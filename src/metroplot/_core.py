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
from matplotlib.patches import Circle, PathPatch

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


@dataclass
class Diagram:
    track_spacing: float = 0.13
    station_radius: float = 0.22
    station_linewidth: float = 2.5
    line_width: float = 6.0
    corner_radius: float = 0.20
    label_font: int = 11
    sub_font: int = 8
    label_dy_main: float = 0.50
    label_dy_sub: float = 0.25
    legend_loc: str | None = None
    legend_font: int = 10
    auto_bend: bool = True
    theme: str | Theme = "light"
    stations: dict = field(default_factory=dict)
    lines: list = field(default_factory=list)

    def station(self, name, x, y, label="", sub="", label_pos="above",
                label_dx=0.0, label_dy=0.0):
        self.stations[name] = Station(name, x, y, label, sub, label_pos,
                                      label_dx, label_dy)
        return self

    def line(self, name, color, routes, bend="hv"):
        rl = [list(r) for r in routes]
        if isinstance(bend, str):
            bends = [bend] * len(rl)
        else:
            bends = list(bend) + ["hv"] * (len(rl) - len(bend))
        self.lines.append(Line(name, color, rl, bends))
        return self

    def render(self, ax=None):
        th = get_theme(self.theme)

        if ax is None:
            _, ax = plt.subplots(figsize=(13, 5))

        # Apply background colour ("none" = transparent)
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

        # Each line gets a single offset across its whole route so that
        # tracks stay continuous when they leave a shared trunk. Offset is
        # taken from the largest cohort the line participates in.
        line_offset: dict[int, float] = {}
        for li in range(len(self.lines)):
            cohorts = [c for c in users.values() if li in c]
            if not cohorts:
                line_offset[li] = 0.0
                continue
            best = max(cohorts, key=lambda c: (len(c), -c.index(li)))
            line_offset[li] = (best.index(li) - (len(best) - 1) / 2) * self.track_spacing

        # Each station shifts to the mean offset of the lines passing through
        # it: a single-line station sits exactly on its line's track, a multi-
        # line station sits at the centroid (lines fan out around it).
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

        # Auto-grow the station radius if needed: line endpoints sit at
        # offset distance in both x and y from a station's center, so we
        # need radius >= sqrt(2) * max_offset for them to stay hidden.
        max_offset = max((abs(o) for o in line_offset.values()), default=0.0)
        radius = max(self.station_radius, math.sqrt(2) * max_offset * 1.05)

        self._validate_layout(station_dy, radius)

        # --- Draw tracks ------------------------------------------------
        seg_counters: dict[int, int] = defaultdict(int)
        for li, ln in enumerate(self.lines):
            for ri, route in enumerate(ln.routes):
                user_bend = ln.bends[ri] if ri < len(ln.bends) else "hv"
                for a, b in zip(route[:-1], route[1:]):
                    sa, sb = self.stations[a], self.stations[b]
                    bend = self._pick_bend(sa, sb, line_offset[li], user_bend,
                                           station_dy, radius) if self.auto_bend else user_bend
                    gid = f"metro-track-{li}-{seg_counters[li]}"
                    seg_counters[li] += 1
                    self._draw_segment(ax, sa, sb, ln, line_offset[li], bend,
                                       gid=gid, theme=th)

        # --- Draw stations ----------------------------------------------
        for s in self.stations.values():
            cy = s.y + station_dy.get(s.name, 0.0)
            slines = station_lines.get(s.name, [])
            self._draw_station(ax, s, cy, radius, slines, th)
            if s.label:
                self._draw_label(ax, s, cy, th)

        # --- Legend -----------------------------------------------------
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

        Creates a figure internally if ax is None.  Returns the resolved path.
        """
        out = Path(path)
        created_fig = ax is None
        if created_fig:
            fig, ax = plt.subplots(figsize=(13, 5))
        self.render(ax)
        if created_fig:
            plt.tight_layout()
        ax.get_figure().savefig(out, format="svg", dpi=dpi,
                                bbox_inches=bbox_inches)
        if created_fig:
            plt.close(ax.get_figure())

        if animate:
            from metroplot._svg_animate import inject_flow_animation
            inject_flow_animation(out, [ln.color for ln in self.lines])

        return out

    # ------------------------------------------------------------------
    # Internal drawing helpers
    # ------------------------------------------------------------------

    def _draw_station(self, ax, s: Station, cy: float, radius: float,
                      slines: list[int], th: Theme) -> None:
        is_interchange = len(slines) > 1

        # Edge colour: use line colour for single-line stations on dark-style
        # themes; use theme default otherwise.
        if th.station_colored_edge and len(slines) == 1:
            edge_color = self.lines[slines[0]].color
        else:
            edge_color = th.station_edge

        edge_lw = th.station_edge_width * (1.25 if is_interchange else 1.0)

        ax.add_patch(Circle(
            (s.x, cy), radius,
            facecolor=th.station_fill,
            edgecolor=edge_color,
            linewidth=edge_lw,
            zorder=10,
        ))

        # Inner coloured dot for themes that use it (light, paper)
        if th.station_dot and len(slines) == 1:
            primary_color = self.lines[slines[0]].color
            ax.add_patch(Circle(
                (s.x, cy), radius * th.station_dot_ratio,
                facecolor=primary_color,
                edgecolor="none",
                zorder=11,
            ))
        elif th.station_dot and is_interchange:
            # Interchange: muted inner fill to signal multi-line
            muted = "#888888" if th.background in ("white", "#fafaf8") else "#666666"
            ax.add_patch(Circle(
                (s.x, cy), radius * th.station_dot_ratio,
                facecolor=muted,
                edgecolor="none",
                zorder=11,
            ))

    def _draw_segment(self, ax, sa: Station, sb: Station, ln: Line,
                      offset: float, bend: str, *, gid: str, theme: Theme) -> None:
        x1, y1, x2, y2 = sa.x, sa.y, sb.x, sb.y

        # Optional glow pass (wider semi-transparent halo)
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

        # L-bend with rounded corner via quadratic Bezier
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
        another station's circle. Returns user_bend when both options are
        clear (or both blocked)."""
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
        return user_bend

    def _validate_layout(self, station_dy, radius):
        """Raise on stations sharing exact coordinates; warn when stations
        sit closer than 2 * radius (their circles would overlap)."""
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
        """Three vertices defining an axis-aligned L. Insert a quadratic Bezier
        at the corner with control point at the corner itself."""
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

    def _draw_label(self, ax, s: Station, cy: float, th: Theme) -> None:
        # Each label_pos defines an offset and alignment for both the main
        # bold label and the smaller sub label. label_dx / label_dy on the
        # station add a free-form tweak on top.
        if s.label_pos == "above":
            main = (0,  self.label_dy_main, "center", "bottom")
            sub  = (0,  self.label_dy_sub,  "center", "bottom")
        elif s.label_pos == "below":
            main = (0, -self.label_dy_main, "center", "top")
            sub  = (0, -self.label_dy_sub,  "center", "top")
        elif s.label_pos == "left":
            main = (-self.label_dy_main, 0, "right", "bottom")
            sub  = (-self.label_dy_main, 0, "right", "top")
        elif s.label_pos == "right":
            main = ( self.label_dy_main, 0, "left", "bottom")
            sub  = ( self.label_dy_main, 0, "left", "top")
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
