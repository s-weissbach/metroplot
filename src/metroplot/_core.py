"""Subway-style pipeline diagrams on a matplotlib axes.

Define stations on an (x, y) grid and lines as one or more routes through them.
Lines that share a segment are auto-offset so they render as parallel tracks.
A line with multiple routes that share a station encodes a split at that station.
"""
from __future__ import annotations

import math
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.path import Path as MPath
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch

from metroplot.themes import Theme, get_theme


@dataclass
class Station:
    name: str
    x: float
    y: float
    label: str = ""
    sub: str = ""
    label_pos: str = "above"  # "above" | "below" | "left" | "right"
    label_dx: float = 0.0
    label_dy: float = 0.0


@dataclass
class Line:
    name: str
    color: str
    routes: Sequence[Sequence[str]]
    bends: Sequence[str] = ()  # one bend per route ("hv" | "vh")
    edge_labels: dict = field(default_factory=dict)  # {(a, b) -> str}


@dataclass
class _SectionSpec:
    """Internal spec; resolved to pixel bounds during render()."""
    label: str
    sub: str
    station_names: list | None  # if set, bounds computed from these stations
    x: float | None             # manual lower-left x (when station_names is None)
    y: float | None
    width: float | None
    height: float | None
    padding: float
    label_pos: str = "top-middle"   # top-left|top-middle|top-right|bottom-*|left|right
    label_rotation: float = 0.0


@dataclass
class Diagram:
    track_spacing: float = 0.09
    station_radius: float = 0.21
    station_linewidth: float = 2.5
    line_width: float = 4.0
    corner_radius: float = 0.20
    label_font: int = 9
    sub_font: int = 7
    label_dy_main: float = 0.50
    label_dy_sub: float = 0.32
    legend_loc: str | None = None
    legend_font: int = 10
    auto_bend: bool = True
    station_interchange_rect: bool = True
    theme: str | Theme = "light"
    stations: dict = field(default_factory=dict)
    lines: list = field(default_factory=list)
    _sections: list = field(default_factory=list, repr=False)

    def station(self, name, x, y, label="", sub="", label_pos="above",
                label_dx=0.0, label_dy=0.0):
        """Add a station (node) to the diagram.

        Args:
            name: Unique identifier used to reference this station in ``line()``.
            x: Grid column (integer or float, increasing left-to-right).
            y: Grid row (integer or float, increasing bottom-to-top).
            label: Primary label rendered in bold above/beside the station.
            sub: Secondary label rendered in a smaller font below ``label``.
            label_pos: Label placement — ``"above"``, ``"below"``, ``"left"``, or ``"right"``.
            label_dx: Horizontal nudge applied to the label in data units.
            label_dy: Vertical nudge applied to the label in data units.

        Returns:
            ``self``, so calls can be chained.
        """
        self.stations[name] = Station(name, x, y, label, sub, label_pos,
                                      label_dx, label_dy)
        return self

    def section(self, label, *, stations=None, x=None, y=None,
                width=None, height=None, sub="", padding=0.65,
                label_pos="top-middle", label_rotation=0.0):
        """Add a labelled grouping box around a set of stations.

        Provide either ``stations=[...]`` to auto-compute bounds, or explicit
        ``x, y, width, height`` to place the box manually.

        Args:
            label: Primary text displayed on the box border.
            stations: List of station names whose bounding box defines the section.
            x: Manual left edge in data units (required when ``stations`` is omitted).
            y: Manual bottom edge in data units (required when ``stations`` is omitted).
            width: Box width in data units (required when ``stations`` is omitted).
            height: Box height in data units (required when ``stations`` is omitted).
            sub: Secondary label rendered below ``label`` in a smaller font.
            padding: Extra space added around the station bounding box in data units.
            label_pos: Position of the label on the box edge — ``"top-left"``,
                ``"top-middle"``, ``"top-right"``, ``"bottom-*"``, ``"left"``, or ``"right"``.
            label_rotation: Rotation angle of the label in degrees.

        Returns:
            ``self``, so calls can be chained.
        """
        if stations is None and any(v is None for v in (x, y, width, height)):
            raise ValueError(
                "section() requires either stations= or all of x, y, width, height"
            )
        self._sections.append(_SectionSpec(
            label=label, sub=sub,
            station_names=list(stations) if stations is not None else None,
            x=x, y=y, width=width, height=height,
            padding=padding,
            label_pos=label_pos,
            label_rotation=label_rotation,
        ))
        return self

    def line(self, name, color, routes, bend="hv", edge_labels=None):
        """Add a metro line connecting an ordered sequence of stations.

        Args:
            name: Display name shown in the legend.
            color: Matplotlib color string (hex, named, etc.) for the track and legend swatch.
            routes: A list of routes, where each route is a list of station names in
                traversal order.  A single route may be passed as a plain list —
                e.g. ``[["a", "b", "c"]]``.  Multiple routes share the line color and
                encode a split/merge at the station where they diverge or meet.
            bend: Corner style — ``"hv"`` (horizontal then vertical) or ``"vh"``
                (vertical then horizontal) for diagonal segments.  Pass a list to set a
                different style per route.
            edge_labels: Optional dict mapping ``(station_a, station_b)`` pairs to label
                strings rendered alongside that segment.  Only supported on straight
                (axis-aligned) segments.

        Returns:
            ``self``, so calls can be chained.
        """
        rl = [list(r) for r in routes]
        if isinstance(bend, str):
            bends = [bend] * len(rl)
        else:
            bends = list(bend) + ["hv"] * (len(rl) - len(bend))
        labels = {tuple(sorted(k)): v for k, v in (edge_labels or {}).items()}
        self.lines.append(Line(name, color, rl, bends, labels))
        return self

    def render(self, ax=None):
        """Draw the diagram onto a matplotlib axes.

        Args:
            ax: An existing ``matplotlib.axes.Axes`` to draw on.  If ``None``,
                a new figure and axes are created automatically.

        Returns:
            The ``Axes`` instance that was drawn on.
        """
        th = get_theme(self.theme)

        if ax is None:
            _, ax = plt.subplots(figsize=(13, 5))

        ax.set_facecolor(th.background)
        fig = ax.get_figure()
        if fig is not None:
            fig.patch.set_facecolor(th.background)
            if th.background == "none":
                fig.patch.set_alpha(0.0)
                ax.patch.set_alpha(0.0)

        users: dict[tuple, list[int]] = defaultdict(list)
        for li, ln in enumerate(self.lines):
            for route in ln.routes:
                for a, b in zip(route[:-1], route[1:]):
                    key = tuple(sorted([a, b]))
                    if li not in users[key]:
                        users[key].append(li)

        line_offset: dict[int, float] = {}
        for li in range(len(self.lines)):
            cohorts = [c for c in users.values() if li in c]
            if not cohorts:
                line_offset[li] = 0.0
                continue
            best = max(cohorts, key=lambda c: (len(c), -c.index(li)))
            spacing = th.track_spacing if th.track_spacing is not None else self.track_spacing
            line_offset[li] = (best.index(li) - (len(best) - 1) / 2) * spacing

        station_lines: dict[str, list[int]] = defaultdict(list)
        for li, ln in enumerate(self.lines):
            for route in ln.routes:
                for name in route:
                    if li not in station_lines[name]:
                        station_lines[name].append(li)
        station_dy: dict[str, float] = {
            name: sum(line_offset[li] for li in lis) / len(lis)
            for name, lis in station_lines.items()
        }

        max_offset = max((abs(o) for o in line_offset.values()), default=0.0)
        radius = max(self.station_radius, math.sqrt(2) * max_offset * 1.05)

        self._validate_layout(station_dy, radius)

        for spec in self._sections:
            self._draw_section(ax, spec, station_dy, th)

        # --- Pre-compute bends; tally spread direction per station ------
        # line_offset is applied in Y for horizontal segments, in X for
        # vertical segments, and diagonally for L-bends.  For the
        # interchange pill to orient correctly we vote per station:
        #   HV bend source → y-spread (horizontal departure)
        #   HV bend dest   → x-spread (vertical arrival)
        #   VH bend source → x-spread (vertical departure)
        #   VH bend dest   → y-spread (horizontal arrival)
        x_votes: dict[str, int] = defaultdict(int)
        y_votes: dict[str, int] = defaultdict(int)
        pre_bends: dict[tuple[int, int, int], str] = {}

        for li, ln in enumerate(self.lines):
            for ri, route in enumerate(ln.routes):
                user_bend = ln.bends[ri] if ri < len(ln.bends) else "hv"
                for si, (a, b) in enumerate(zip(route[:-1], route[1:])):
                    sa, sb = self.stations[a], self.stations[b]
                    if sa.y == sb.y:
                        bend = user_bend
                        y_votes[a] += 1; y_votes[b] += 1
                    elif sa.x == sb.x:
                        bend = user_bend
                        x_votes[a] += 1; x_votes[b] += 1
                    else:
                        bend = (self._pick_bend(sa, sb, line_offset[li],
                                                user_bend, station_dy, radius)
                                if self.auto_bend else user_bend)
                        if bend == "hv":
                            y_votes[a] += 1   # horizontal departure
                            x_votes[b] += 1   # vertical arrival
                        else:
                            x_votes[a] += 1   # vertical departure
                            y_votes[b] += 1   # horizontal arrival
                    pre_bends[(li, ri, si)] = bend

        station_spread: dict[str, str] = {
            name: "x" if x_votes[name] > y_votes[name] else "y"
            for name in self.stations
        }

        # --- Draw tracks ------------------------------------------------
        _deferred_labels = []
        for li, ln in enumerate(self.lines):
            for ri, route in enumerate(ln.routes):
                for si, (a, b) in enumerate(zip(route[:-1], route[1:])):
                    sa, sb = self.stations[a], self.stations[b]
                    bend = pre_bends[(li, ri, si)]
                    gid = f"metro-track-{li}-{ri}-{si}"
                    key = tuple(sorted([a, b]))
                    edge_label = ln.edge_labels.get(key)
                    if edge_label is not None and (sa.x == sb.x or sa.y == sb.y):
                        _deferred_labels.append((
                            sa.x, sa.y, sb.x, sb.y,
                            line_offset[li], sa.y == sb.y,
                            ln.color, edge_label, gid, th,
                        ))
                    else:
                        if edge_label is not None:
                            warnings.warn(
                                f"edge_labels only supported on straight segments; "
                                f"label {edge_label!r} on ({a!r}, {b!r}) will be skipped.",
                                stacklevel=2,
                            )
                        self._draw_segment(ax, sa, sb, ln, line_offset[li], bend,
                                           gid=gid, theme=th)

        for s in self.stations.values():
            cy = s.y + station_dy.get(s.name, 0.0)
            slines = station_lines.get(s.name, [])
            self._draw_station(ax, s, cy, radius, slines, th,
                               line_offset, station_spread)
            if s.label:
                self._draw_label(ax, s, cy, th)

        if self.legend_loc and self.lines:
            handles = [Line2D([0], [0], color=ln.color,
                              linewidth=self.line_width, solid_capstyle="round",
                              label=ln.name) for ln in self.lines]
            legend = ax.legend(
                handles=handles, loc=self.legend_loc, frameon=True,
                fontsize=self.legend_font,
                borderpad=0.6, handlelength=1.6, handletextpad=0.7,
            )
            legend.set_zorder(20)
            legend.get_frame().set_facecolor(th.background)
            legend.get_frame().set_edgecolor(th.station_edge)
            for text in legend.get_texts():
                text.set_color(th.label_color)

        ax.set_aspect("equal")
        ax.axis("off")
        ax.margins(0.10)

        if _deferred_labels:
            try:
                ax.get_figure().canvas.draw()
            except Exception:
                pass
            for x1, y1, x2, y2, off, is_horiz, color, label, gid, th_item in _deferred_labels:
                self._draw_edge_label(ax, x1, y1, x2, y2, off, is_horiz,
                                      color, label, gid, th_item)

        return ax

    def save_svg(
        self,
        path: str | Path,
        ax=None,
        *,
        animate: bool = False,
        dpi: int = 150,
        bbox_inches: str = "tight",
    ) -> Path:
        """Render to SVG and optionally inject flowing-dash animation.

        If ``ax`` is omitted, this method creates and closes a temporary figure.
        Returns the output path as a ``Path`` object.
        """
        out = Path(path)
        created_fig = ax is None
        if created_fig:
            fig, ax = plt.subplots(figsize=(13, 5))
        self.render(ax)
        plt.tight_layout()
        ax.get_figure().savefig(out, format="svg", dpi=dpi,
                                bbox_inches=bbox_inches)
        if created_fig:
            plt.close(ax.get_figure())

        if animate:
            from metroplot._svg_animate import inject_cart_animation
            line_routes = [(ln.color, list(ln.routes[0])) for ln in self.lines if ln.routes]
            inject_cart_animation(out, line_routes)

        return out

    # ------------------------------------------------------------------
    # Internal drawing helpers
    # ------------------------------------------------------------------

    def _draw_section(self, ax, spec: _SectionSpec,
                      station_dy: dict, th: Theme) -> None:
        if spec.station_names is not None:
            found = [s for s in spec.station_names if s in self.stations]
            if not found:
                return
            xs = [self.stations[s].x for s in found]
            ys = [self.stations[s].y + station_dy.get(s, 0.0) for s in found]
            lx = min(xs) - spec.padding
            ly = min(ys) - spec.padding
            w  = max(xs) - min(xs) + 2 * spec.padding
            h  = max(ys) - min(ys) + 2 * spec.padding
        else:
            lx, ly, w, h = spec.x, spec.y, spec.width, spec.height

        r = th.section_corner_radius
        patch = FancyBboxPatch(
            (lx + r, ly + r),
            max(w - 2 * r, 1e-3),
            max(h - 2 * r, 1e-3),
            boxstyle=f"round,pad={r}",
            facecolor=th.section_fill,
            edgecolor=th.section_edge,
            linewidth=th.section_edge_width,
            zorder=1,
        )
        ax.add_patch(patch)

        cx = lx + w / 2
        cy_box = ly + h / 2
        top = ly + h
        gap = 0.12

        _pos_map = {
            "top-left":      (lx,       top + gap, "left",   "bottom"),
            "top-middle":    (cx,       top + gap, "center", "bottom"),
            "top-right":     (lx + w,   top + gap, "right",  "bottom"),
            "bottom-left":   (lx,       ly  - gap, "left",   "top"),
            "bottom-middle": (cx,       ly  - gap, "center", "top"),
            "bottom-right":  (lx + w,   ly  - gap, "right",  "top"),
            "left":          (lx - gap, cy_box,    "right",  "center"),
            "right":         (lx+w+gap, cy_box,    "left",   "center"),
        }
        tx, ty, ha, va = _pos_map.get(spec.label_pos, _pos_map["top-middle"])
        rot = spec.label_rotation

        ax.text(tx, ty, spec.label,
                ha=ha, va=va, rotation=rot,
                fontsize=th.section_label_font,
                color=th.section_label_color,
                fontweight="bold",
                zorder=12)
        if spec.sub:
            sub_gap = th.section_label_font * 0.016
            ax.text(tx, ty + sub_gap, spec.sub,
                    ha=ha, va=va, rotation=rot,
                    fontsize=max(th.section_label_font - 2, 6),
                    color=th.section_label_color,
                    zorder=12)

    def _draw_station(self, ax, s: Station, cy: float, radius: float,
                      slines: list[int], th: Theme,
                      line_offset: dict[int, float],
                      station_spread: dict[str, str] | None = None) -> None:
        is_interchange = len(slines) > 1
        spread = (station_spread or {}).get(s.name, "y")
        r = radius * th.station_radius_factor   # effective draw radius
        gid = f"metro-station-{s.name}"

        ic_fill = th.station_interchange_fill if th.station_interchange_fill is not None else th.station_fill
        ic_edge = th.station_interchange_edge if th.station_interchange_edge is not None else th.station_edge
        ic_lw   = th.station_edge_width * 1.25

        # ── Interchange station ──────────────────────────────────────────────────
        if is_interchange and self.station_interchange_rect:
            sdy_here = sum(line_offset[li] for li in slines) / len(slines)
            pairs = sorted((line_offset[li] - sdy_here, li) for li in slines)
            rel = [p[0] for p in pairs]

            style = th.station_interchange_style
            if style == "hk_pill":
                self._draw_hk_pill(ax, s, cy, rel, spread, th, gid)
            elif style == "berlin_pill":
                self._draw_berlin_pill(ax, s, cy, rel, spread, gid)
            elif style == "paris_pill":
                self._draw_paris_pill(ax, s, cy, rel, spread, gid)
            elif style == "dot_letter":
                if spread == "y":
                    for o in rel:
                        self._draw_dot_letter(ax, s.x, cy + o, s.label, gid)
                else:
                    for o in rel:
                        self._draw_dot_letter(ax, s.x + o, cy, s.label, gid)
            elif style == "circle":
                # Single centered circle — same as a single-line station
                p = Circle((s.x, cy), r, facecolor=ic_fill,
                            edgecolor=ic_edge, linewidth=ic_lw, zorder=10)
                p.set_gid(gid)
                ax.add_patch(p)
            elif style == "circles":
                self._draw_station_circles(ax, s, cy, r, rel, spread,
                                           ic_fill, ic_edge, ic_lw, gid)
            elif style == "connected":
                self._draw_station_connected(ax, s, cy, r, rel, spread,
                                             ic_fill, ic_edge, ic_lw, gid)
            elif style == "grouped":
                self._draw_station_grouped(ax, s, cy, r, rel, spread,
                                           ic_fill, ic_edge, th, gid, fill_outer=True)
            elif style == "grouped_no_fill":
                self._draw_station_grouped(ax, s, cy, r, rel, spread,
                                           ic_fill, ic_edge, th, gid, fill_outer=False)
            elif style == "merged":
                self._draw_station_merged(ax, s, cy, r, rel, spread,
                                          th, ic_edge, ic_lw, gid)
            elif style == "pill_count":
                self._draw_station_pill_count(ax, s, cy, r, rel, spread,
                                              ic_fill, ic_edge, ic_lw, len(slines), gid)
            else:  # "pill" (default)
                pad = r * 0.45
                if spread == "x":
                    cx_pill = s.x + (min(rel) + max(rel)) / 2
                    w = max(max(rel) - min(rel) + 2 * pad, 2 * r)
                    h = 2 * r
                    r_box = min(w / 2, h / 2) * 0.98
                    patch = FancyBboxPatch(
                        (cx_pill - w / 2 + r_box, cy - h / 2 + r_box),
                        max(w - 2 * r_box, 1e-3), max(h - 2 * r_box, 1e-3),
                        boxstyle=f"round,pad={r_box}",
                        facecolor=ic_fill, edgecolor=ic_edge,
                        linewidth=ic_lw, zorder=10,
                    )
                else:
                    cy_pill = cy + (min(rel) + max(rel)) / 2
                    h = max(max(rel) - min(rel) + 2 * pad, 2 * r)
                    w = 2 * r
                    r_box = min(w / 2, h / 2) * 0.98
                    patch = FancyBboxPatch(
                        (s.x - w / 2 + r_box, cy_pill - h / 2 + r_box),
                        max(w - 2 * r_box, 1e-3), max(h - 2 * r_box, 1e-3),
                        boxstyle=f"round,pad={r_box}",
                        facecolor=ic_fill, edgecolor=ic_edge,
                        linewidth=ic_lw, zorder=10,
                    )
                patch.set_gid(gid)
                ax.add_patch(patch)
            return

        # ── Single-line station ──────────────────────────────────────────────────
        line_color = self.lines[slines[0]].color if slines else th.station_edge
        edge_color = line_color if th.station_colored_edge else th.station_edge

        style = th.station_style
        if style == "hk_dot":
            self._draw_hk_dot(ax, s.x, cy, th, gid)

        elif style == "berlin_dot":
            self._draw_berlin_dot(ax, s.x, cy, gid)

        elif style == "paris_dot":
            self._draw_paris_dot(ax, s.x, cy, line_color, gid)

        elif style == "dot_letter":
            self._draw_dot_letter(ax, s.x, cy, s.label, gid)

        elif style == "colored_dot":
            p = Circle((s.x, cy), r, facecolor=line_color, edgecolor="none", zorder=10)
            p.set_gid(gid)
            ax.add_patch(p)

        elif style == "solid":
            p = Circle((s.x, cy), r, facecolor=th.station_fill,
                       edgecolor="none", zorder=10)
            p.set_gid(gid)
            ax.add_patch(p)

        elif style == "rect":
            if spread == "y":
                w_r, h_r = 1.3 * r, 2.2 * r
            else:
                w_r, h_r = 2.2 * r, 1.3 * r
            r_box = min(w_r, h_r) / 2 * 0.92
            p = FancyBboxPatch(
                (s.x - w_r / 2 + r_box, cy - h_r / 2 + r_box),
                max(w_r - 2 * r_box, 1e-3), max(h_r - 2 * r_box, 1e-3),
                boxstyle=f"round,pad={r_box}",
                facecolor=th.station_fill, edgecolor=edge_color,
                linewidth=th.station_edge_width, zorder=10,
            )
            p.set_gid(gid)
            ax.add_patch(p)

        else:  # "circle"
            outer = Circle((s.x, cy), r, facecolor=th.station_fill,
                           edgecolor=edge_color,
                           linewidth=th.station_edge_width, zorder=10)
            outer.set_gid(gid)
            ax.add_patch(outer)
            if th.station_dot:
                primary_color = self.lines[slines[0]].color
                ax.add_patch(Circle((s.x, cy), r * th.station_dot_ratio,
                                    facecolor=primary_color, edgecolor="none", zorder=11))

    def _draw_hk_dot(self, ax, x, y, th, gid):
        """HK single: white circle touching adjacent circles, thin dark outline."""
        r = (th.track_spacing / 2) if th.track_spacing else 0.09
        p = Circle((x, y), r, facecolor='white', edgecolor='#1a2a3a',
                   linewidth=1.5, zorder=10)
        p.set_gid(gid)
        ax.add_patch(p)

    def _draw_hk_pill(self, ax, s, cy, rel, spread, th, gid):
        """HK interchange: individual circles stacked and touching, dark outline.

        Circle radius = half the inter-track spacing so adjacent circles meet
        exactly at their edges with no gap.
        """
        if len(rel) > 1:
            circle_r = (max(rel) - min(rel)) / (len(rel) - 1) / 2
        else:
            circle_r = (th.track_spacing / 2) if th.track_spacing else 0.09
        edge = '#1a2a3a'
        lw = 1.5
        if spread == "y":
            for i, o in enumerate(rel):
                p = Circle((s.x, cy + o), circle_r, facecolor='white',
                            edgecolor=edge, linewidth=lw, zorder=10)
                if i == len(rel) - 1:
                    p.set_gid(gid)
                ax.add_patch(p)
        else:
            for i, o in enumerate(rel):
                p = Circle((s.x + o, cy), circle_r, facecolor='white',
                            edgecolor=edge, linewidth=lw, zorder=10)
                if i == len(rel) - 1:
                    p.set_gid(gid)
                ax.add_patch(p)

    def _draw_berlin_dot(self, ax, x, y, gid):
        """Berlin single station: white circle, diameter = line_width pts, no outline."""
        artists = ax.plot(x, y, 'o', markersize=self.line_width,
                          color='white', markeredgecolor='none', zorder=10)
        if gid and artists:
            artists[0].set_gid(gid)

    def _draw_berlin_pill(self, ax, s, cy, rel, spread, gid):
        """Berlin interchange: white rounded-rect, width = 1.2× line_width, thin black outline."""
        pill_lw = self.line_width * 1.2
        outline_lw = pill_lw + 1.5
        kw = dict(solid_capstyle='round', zorder=10)
        if spread == "y":
            y0, y1 = cy + min(rel), cy + max(rel)
            ax.plot([s.x, s.x], [y0, y1], color='black', linewidth=outline_lw, **kw)
            artists = ax.plot([s.x, s.x], [y0, y1], color='white', linewidth=pill_lw, **kw)
        else:
            x0, x1 = s.x + min(rel), s.x + max(rel)
            ax.plot([x0, x1], [cy, cy], color='black', linewidth=outline_lw, **kw)
            artists = ax.plot([x0, x1], [cy, cy], color='white', linewidth=pill_lw, **kw)
        if gid and artists:
            artists[0].set_gid(gid)

    def _draw_paris_dot(self, ax, x, y, line_color, gid):
        """Paris single station: colored circle, diameter = 2 × line_width pts."""
        artists = ax.plot(x, y, 'o', markersize=self.line_width * 2.0,
                          color=line_color, markeredgecolor='none', zorder=10)
        if gid and artists:
            artists[0].set_gid(gid)

    def _draw_paris_pill(self, ax, s, cy, rel, spread, gid):
        """Paris interchange: thick rounded-cap line spanning all tracks.

        Width = 2 × line_width pts; round caps add the overhang automatically.
        Drawn as a black outline beneath a white fill.
        """
        pill_lw = self.line_width * 2.0
        outline_lw = pill_lw + 2.0
        kw = dict(solid_capstyle='round', zorder=10)
        if spread == "y":
            y0, y1 = cy + min(rel), cy + max(rel)
            ax.plot([s.x, s.x], [y0, y1], color='black', linewidth=outline_lw, **kw)
            artists = ax.plot([s.x, s.x], [y0, y1], color='white', linewidth=pill_lw, **kw)
        else:
            x0, x1 = s.x + min(rel), s.x + max(rel)
            ax.plot([x0, x1], [cy, cy], color='black', linewidth=outline_lw, **kw)
            artists = ax.plot([x0, x1], [cy, cy], color='white', linewidth=pill_lw, **kw)
        if gid and artists:
            artists[0].set_gid(gid)

    def _draw_dot_letter(self, ax, x, y, label, gid):
        """Black circle (diameter = line_width pts) with white first-letter inside."""
        ms = self.line_width
        artists = ax.plot(x, y, 'o', markersize=ms, color='black',
                          markeredgecolor='none', zorder=10)
        if gid and artists:
            artists[0].set_gid(gid)
        letter = label[0].upper() if label else ""
        if letter:
            ax.text(x, y, letter, ha='center', va='center',
                    color='white', fontsize=ms * 0.55, fontweight='bold', zorder=11)

    def _draw_station_circles(self, ax, s, cy, r, rel, spread,
                              fill, edge, lw, gid):
        """One plain circle per track position, no connecting bar."""
        if spread == "y":
            for o in rel:
                ax.add_patch(Circle((s.x, cy + o), r,
                                    facecolor=fill, edgecolor=edge,
                                    linewidth=lw, zorder=10))
        else:
            for o in rel:
                ax.add_patch(Circle((s.x + o, cy), r,
                                    facecolor=fill, edgecolor=edge,
                                    linewidth=lw, zorder=10))
        ax.patches[-1].set_gid(gid)

    def _draw_station_connected(self, ax, s, cy, r, rel, spread,
                                fill, edge, lw, gid):
        """Circles at each track + thin connecting bar."""
        bar_half = r * 0.28
        if spread == "y":
            ycs = [cy + o for o in rel]
            bar_lo, bar_hi = min(ycs), max(ycs)
            if bar_hi > bar_lo + 1e-3:
                ax.add_patch(FancyBboxPatch(
                    (s.x - bar_half, bar_lo),
                    2 * bar_half, bar_hi - bar_lo,
                    boxstyle="round,pad=0",
                    facecolor=fill, edgecolor=edge, linewidth=lw, zorder=9,
                ))
            for yc in ycs:
                ax.add_patch(Circle((s.x, yc), r, facecolor=fill,
                                    edgecolor=edge, linewidth=lw, zorder=10))
        else:
            xcs = [s.x + o for o in rel]
            bar_lo, bar_hi = min(xcs), max(xcs)
            if bar_hi > bar_lo + 1e-3:
                ax.add_patch(FancyBboxPatch(
                    (bar_lo, cy - bar_half),
                    bar_hi - bar_lo, 2 * bar_half,
                    boxstyle="round,pad=0",
                    facecolor=fill, edgecolor=edge, linewidth=lw, zorder=9,
                ))
            for xc in xcs:
                ax.add_patch(Circle((xc, cy), r, facecolor=fill,
                                    edgecolor=edge, linewidth=lw, zorder=10))
        ax.patches[-1].set_gid(gid)

    def _draw_station_grouped(self, ax, s, cy, r, rel, spread,
                              ic_fill, ic_edge, th, gid, *, fill_outer):
        """NYC/Tokyo: outer rounded rect enclosing individual station markers."""
        pad = r * 0.35
        lw  = th.station_edge_width
        outer_fill = ic_fill if fill_outer else "none"
        if spread == "y":
            ycs = [cy + o for o in rel]
            y_lo = min(ycs) - r - pad
            h_outer = (max(ycs) + r + pad) - y_lo
            w_outer = 2 * r + 2 * pad
            r_box = min(w_outer, h_outer) / 2 * 0.45
            ax.add_patch(FancyBboxPatch(
                (s.x - w_outer / 2 + r_box, y_lo + r_box),
                max(w_outer - 2 * r_box, 1e-3), max(h_outer - 2 * r_box, 1e-3),
                boxstyle=f"round,pad={r_box}",
                facecolor=outer_fill, edgecolor=ic_edge, linewidth=lw, zorder=9,
            ))
            for yc in ycs:
                self._draw_grouped_inner(ax, s.x, yc, r, th, spread)
        else:
            xcs = [s.x + o for o in rel]
            x_lo = min(xcs) - r - pad
            w_outer = (max(xcs) + r + pad) - x_lo
            h_outer = 2 * r + 2 * pad
            r_box = min(w_outer, h_outer) / 2 * 0.45
            ax.add_patch(FancyBboxPatch(
                (x_lo + r_box, cy - h_outer / 2 + r_box),
                max(w_outer - 2 * r_box, 1e-3), max(h_outer - 2 * r_box, 1e-3),
                boxstyle=f"round,pad={r_box}",
                facecolor=outer_fill, edgecolor=ic_edge, linewidth=lw, zorder=9,
            ))
            for xc in xcs:
                self._draw_grouped_inner(ax, xc, cy, r, th, spread)
        ax.patches[-1].set_gid(gid)

    def _draw_grouped_inner(self, ax, x, y, r, th, spread):
        """Draw one station marker inside a grouped interchange."""
        style = th.station_style
        if style == "rect":
            if spread == "y":
                w_r, h_r = 1.3 * r, 2.2 * r
            else:
                w_r, h_r = 2.2 * r, 1.3 * r
            r_box = min(w_r, h_r) / 2 * 0.92
            ax.add_patch(FancyBboxPatch(
                (x - w_r / 2 + r_box, y - h_r / 2 + r_box),
                max(w_r - 2 * r_box, 1e-3), max(h_r - 2 * r_box, 1e-3),
                boxstyle=f"round,pad={r_box}",
                facecolor=th.station_fill, edgecolor=th.station_interchange_edge or th.station_edge,
                linewidth=th.station_edge_width, zorder=10,
            ))
        else:  # solid / circle
            ax.add_patch(Circle((x, y), r, facecolor=th.station_fill,
                                edgecolor="none", zorder=10))

    def _draw_station_merged(self, ax, s, cy, r, rel, spread,
                             th, ic_edge, ic_lw, gid):
        """Hong Kong: overlapping circles at each track, spaced 1.5 r apart."""
        n = len(rel)
        spacing = r * 1.5
        if spread == "y":
            offsets = [(i - (n - 1) / 2) * spacing for i in range(n)]
            for yo in offsets:
                ax.add_patch(Circle((s.x, cy + yo), r,
                                    facecolor=th.station_interchange_fill or th.station_fill,
                                    edgecolor=ic_edge, linewidth=ic_lw, zorder=10))
        else:
            offsets = [(i - (n - 1) / 2) * spacing for i in range(n)]
            for xo in offsets:
                ax.add_patch(Circle((s.x + xo, cy), r,
                                    facecolor=th.station_interchange_fill or th.station_fill,
                                    edgecolor=ic_edge, linewidth=ic_lw, zorder=10))
        ax.patches[-1].set_gid(gid)

    def _draw_station_pill_count(self, ax, s, cy, r, rel, spread,
                                 ic_fill, ic_edge, ic_lw, n_lines, gid):
        """Paris: pill sized exactly as n_lines × circle diameter."""
        mid = (min(rel) + max(rel)) / 2
        if spread == "x":
            w = n_lines * 2 * r
            h = 2 * r
            cx = s.x + mid
            r_box = h / 2 * 0.98
            patch = FancyBboxPatch(
                (cx - w / 2 + r_box, cy - h / 2 + r_box),
                max(w - 2 * r_box, 1e-3), max(h - 2 * r_box, 1e-3),
                boxstyle=f"round,pad={r_box}",
                facecolor=ic_fill, edgecolor=ic_edge, linewidth=ic_lw, zorder=10,
            )
        else:
            h = n_lines * 2 * r
            w = 2 * r
            cy_pill = cy + mid
            r_box = w / 2 * 0.98
            patch = FancyBboxPatch(
                (s.x - w / 2 + r_box, cy_pill - h / 2 + r_box),
                max(w - 2 * r_box, 1e-3), max(h - 2 * r_box, 1e-3),
                boxstyle=f"round,pad={r_box}",
                facecolor=ic_fill, edgecolor=ic_edge, linewidth=ic_lw, zorder=10,
            )
        patch.set_gid(gid)
        ax.add_patch(patch)

    def _draw_segment(self, ax, sa: Station, sb: Station, ln: Line,
                      offset: float, bend: str, *, gid: str, theme: Theme) -> None:
        x1, y1, x2, y2 = sa.x, sa.y, sb.x, sb.y

        if theme.glow:
            glow_lw = self.line_width * theme.glow_width_multiplier
            self._draw_raw_segment(
                ax, x1, y1, x2, y2, offset, bend, ln.color,
                lw=glow_lw, alpha=theme.glow_alpha, zorder=4, gid=None,
            )

        self._draw_raw_segment(
            ax, x1, y1, x2, y2, offset, bend, ln.color,
            lw=self.line_width, alpha=1.0, zorder=5, gid=gid,
        )

    def _draw_raw_segment(self, ax, x1, y1, x2, y2, offset, bend, color,
                          *, lw, alpha, zorder, gid) -> None:
        kw = dict(color=color, linewidth=lw, alpha=alpha,
                  solid_capstyle="round", solid_joinstyle="round",
                  zorder=zorder)

        if y1 == y2:
            artists = ax.plot([x1, x2], [y1 + offset, y1 + offset], **kw)
            if gid and artists:
                artists[0].set_gid(gid)
            return

        if x1 == x2:
            artists = ax.plot([x1 + offset, x1 + offset], [y1, y2], **kw)
            if gid and artists:
                artists[0].set_gid(gid)
            return

        if bend == "hv":
            cx, cy = x2 + offset, y1 + offset
            verts, codes = self._rounded_l((x1, cy), (cx, cy), (cx, y2 + offset))
        else:
            cx, cy = x1 + offset, y2 + offset
            verts, codes = self._rounded_l((cx, y1 + offset), (cx, cy), (x2, cy))

        pp = PathPatch(MPath(verts, codes), fill=False,
                       edgecolor=color, linewidth=lw,
                       alpha=alpha, capstyle="round", joinstyle="round",
                       zorder=zorder)
        if gid:
            pp.set_gid(gid)
        ax.add_patch(pp)

    def _pick_bend(self, sa, sb, offset, user_bend, station_dy, radius):
        """Choose hv or vh so the L-bend's vertical leg doesn't pass through
        another station's circle.

        If both candidates are equally valid/blocked, prefers ``user_bend``
        (with additional direction-aware behavior for default ``"hv"``).
        """
        x1, y1 = sa.x, sa.y
        x2, y2 = sb.x, sb.y
        if x1 == x2 or y1 == y2:
            return user_bend
        y_lo = min(y1 + offset, y2 + offset)
        y_hi = max(y1 + offset, y2 + offset)

        def blocks(leg_x):
            for s in self.stations.values():
                if s.name in (sa.name, sb.name):
                    continue
                sy = s.y + station_dy.get(s.name, 0.0)
                if abs(s.x - leg_x) <= radius and y_lo - radius < sy < y_hi + radius:
                    return True
            return False

        hv_blocked = blocks(x2 + offset)
        vh_blocked = blocks(x1 + offset)
        if hv_blocked and not vh_blocked:
            return "vh"
        if vh_blocked and not hv_blocked:
            return "hv"
        # Both options clear.  Respect an explicit "vh" from the caller;
        # for the default "hv" apply direction-aware logic: going left
        # (return legs) → VH so the source bends immediately and the
        # return run is a clean horizontal.  Going right (forward) → HV.
        if user_bend == "vh":
            return "vh"
        return "vh" if x2 < x1 else "hv"

    def _validate_layout(self, station_dy, radius):
        items = list(self.stations.values())
        for i, sa in enumerate(items):
            ax_, ay = sa.x, sa.y + station_dy.get(sa.name, 0.0)
            for sb in items[i + 1:]:
                bx, by = sb.x, sb.y + station_dy.get(sb.name, 0.0)
                if ax_ == bx and ay == by:
                    raise ValueError(
                        f"stations {sa.name!r} and {sb.name!r} share coordinates "
                        f"({ax_}, {ay})"
                    )
                dist = math.hypot(ax_ - bx, ay - by)
                if dist < 2 * radius:
                    warnings.warn(
                        f"stations {sa.name!r} and {sb.name!r} are closer than "
                        f"2 * station_radius (distance {dist:.3f}, threshold {2 * radius:.3f})",
                        stacklevel=2,
                    )

    def _rounded_l(self, start, corner, end):
        sx, sy = start
        cx, cy = corner
        ex, ey = end
        leg1 = abs(sx - cx) + abs(sy - cy)
        leg2 = abs(ex - cx) + abs(ey - cy)
        r = min(self.corner_radius, leg1, leg2)
        if r <= 0:
            return [start, corner, end], [MPath.MOVETO, MPath.LINETO, MPath.LINETO]
        approach = (cx - r if sx < cx else cx + r, cy) if sx != cx else \
                   (cx, cy - r if sy < cy else cy + r)
        depart = (cx - r if ex < cx else cx + r, cy) if ex != cx else \
                 (cx, cy - r if ey < cy else cy + r)
        return ([start, approach, corner, depart, end],
                [MPath.MOVETO, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO])

    def _draw_edge_label(self, ax, x1, y1, x2, y2, offset, is_horizontal,
                         color, label, gid, theme) -> None:
        """Draw a text label interrupting a straight track segment."""
        if is_horizontal:
            mx, my = (x1 + x2) / 2, y1 + offset
            rotation = 0
        else:
            mx, my = x1 + offset, (y1 + y2) / 2
            rotation = 90

        t = ax.text(mx, my, label,
                    fontsize=self.line_width, color=color,
                    ha="center", va="center", rotation=rotation,
                    zorder=7)

        half_gap = self._measure_label_half_gap(ax, t, is_horizontal)

        def _draw_halves(lw, alpha, zorder):
            kw = dict(color=color, linewidth=lw, alpha=alpha,
                      solid_capstyle="round", solid_joinstyle="round",
                      zorder=zorder)
            if is_horizontal:
                lo, hi = min(x1, x2), max(x1, x2)
                if lo < mx - half_gap:
                    ax.plot([lo, mx - half_gap], [my, my], **kw)
                if mx + half_gap < hi:
                    ax.plot([mx + half_gap, hi], [my, my], **kw)
            else:
                lo, hi = min(y1, y2), max(y1, y2)
                if lo < my - half_gap:
                    ax.plot([mx, mx], [lo, my - half_gap], **kw)
                if my + half_gap < hi:
                    ax.plot([mx, mx], [my + half_gap, hi], **kw)

        if theme.glow:
            _draw_halves(self.line_width * theme.glow_width_multiplier,
                         theme.glow_alpha, 4)
        _draw_halves(self.line_width, 1.0, 5)

        # Invisible full-length line carries the GID so SVG animation can
        # extract a complete path for this segment. The cart follows this ghost
        # and glides smoothly across the label gap instead of jumping off-track.
        ghost_kw = dict(color=color, linewidth=self.line_width, alpha=0.0,
                        solid_capstyle="round", zorder=5)
        if is_horizontal:
            ghost = ax.plot([min(x1, x2), max(x1, x2)], [my, my], **ghost_kw)
        else:
            ghost = ax.plot([mx, mx], [min(y1, y2), max(y1, y2)], **ghost_kw)
        if gid and ghost:
            ghost[0].set_gid(gid)

    def _measure_label_half_gap(self, ax, text_artist, is_horizontal) -> float:
        """Return half the gap (data units) needed to clear the text label."""
        PAD = 1.2
        try:
            renderer = ax.get_figure().canvas.get_renderer()
            bbox_disp = text_artist.get_window_extent(renderer=renderer)
            inv = ax.transData.inverted()
            c0 = inv.transform((bbox_disp.x0, bbox_disp.y0))
            c1 = inv.transform((bbox_disp.x1, bbox_disp.y1))
            if is_horizontal:
                return abs(c1[0] - c0[0]) / 2 * PAD
            else:
                return abs(c1[1] - c0[1]) / 2 * PAD
        except Exception:
            # Fallback: estimate from axes limits and font size
            n = max(len(text_artist.get_text()), 1)
            try:
                fig = ax.get_figure()
                ax_pos = ax.get_position()
                if is_horizontal:
                    ax_pts = ax_pos.width * fig.get_figwidth() * 72
                    data_range = max(ax.get_xlim()[1] - ax.get_xlim()[0], 1e-6)
                else:
                    ax_pts = ax_pos.height * fig.get_figheight() * 72
                    data_range = max(ax.get_ylim()[1] - ax.get_ylim()[0], 1e-6)
                pts_per_data = ax_pts / data_range
                return n * self.line_width * 0.55 / pts_per_data / 2 * PAD
            except Exception:
                return n * 0.03

    def _draw_label(self, ax, s: Station, cy: float, th: Theme) -> None:
        dy_main = th.label_dy_main if th.label_dy_main is not None else self.label_dy_main
        dy_sub  = th.label_dy_sub  if th.label_dy_sub  is not None else self.label_dy_sub
        if s.label_pos == "above":
            main = (0,  dy_main, "center", "bottom")
            sub  = (0,  dy_sub,  "center", "bottom")
        elif s.label_pos == "below":
            main = (0, -dy_main, "center", "top")
            sub  = (0, -dy_sub,  "center", "top")
        elif s.label_pos == "left":
            main = (-dy_main, 0, "right", "bottom")
            sub  = (-dy_main, 0, "right", "top")
        elif s.label_pos == "right":
            main = ( dy_main, 0, "left", "bottom")
            sub  = ( dy_sub,  0, "left", "top")
        else:
            raise ValueError(f"unknown label_pos: {s.label_pos!r}")

        dx_m, dy_m, ha_m, va_m = main
        dx_s, dy_s, ha_s, va_s = sub
        ax.text(s.x + dx_m + s.label_dx, cy + dy_m + s.label_dy,
                s.label, ha=ha_m, va=va_m,
                fontweight="bold", fontsize=self.label_font,
                color=th.label_color, zorder=15)
        if s.sub:
            ax.text(s.x + dx_s + s.label_dx, cy + dy_s + s.label_dy,
                    s.sub, ha=ha_s, va=va_s,
                    fontsize=self.sub_font, color=th.sub_color, zorder=15)
