"""Subway-style pipeline diagrams on a matplotlib axes.

Define stations on an (x, y) grid and lines as one or more routes through them.
Lines that share a segment are auto-offset so they render as parallel tracks.
A line with multiple routes that share a station encodes a split at that station.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Sequence

import matplotlib.pyplot as plt
from matplotlib.patches import Circle


@dataclass
class Station:
    name: str
    x: float
    y: float
    label: str = ""
    sub: str = ""
    label_pos: str = "above"  # "above" | "below"


@dataclass
class Line:
    name: str
    color: str
    routes: Sequence[Sequence[str]]
    bend: str = "hv"  # "hv" = horizontal then vertical; "vh" = vertical then horizontal


@dataclass
class Diagram:
    track_spacing: float = 0.13
    station_radius: float = 0.22
    line_width: float = 6.0
    label_font: int = 11
    sub_font: int = 8
    label_dy_main: float = 0.50
    label_dy_sub: float = 0.25
    stations: dict = field(default_factory=dict)
    lines: list = field(default_factory=list)

    def station(self, name, x, y, label="", sub="", label_pos="above"):
        self.stations[name] = Station(name, x, y, label, sub, label_pos)
        return self

    def line(self, name, color, routes, bend="hv"):
        self.lines.append(Line(name, color, [list(r) for r in routes], bend))
        return self

    def render(self, ax=None):
        if ax is None:
            _, ax = plt.subplots(figsize=(13, 5))

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

        for li, ln in enumerate(self.lines):
            for route in ln.routes:
                for a, b in zip(route[:-1], route[1:]):
                    self._draw_segment(ax, self.stations[a], self.stations[b], ln, line_offset[li])

        for s in self.stations.values():
            cy = s.y + station_dy.get(s.name, 0.0)
            ax.add_patch(Circle((s.x, cy), self.station_radius,
                                facecolor="white", edgecolor="black",
                                linewidth=2.0, zorder=10))
            if s.label:
                self._draw_label(ax, s, cy)

        ax.set_aspect("equal")
        ax.axis("off")
        ax.margins(0.10)
        return ax

    def _draw_segment(self, ax, sa, sb, ln, offset):
        x1, y1, x2, y2 = sa.x, sa.y, sb.x, sb.y
        kw = dict(color=ln.color, linewidth=self.line_width,
                  solid_capstyle="round", solid_joinstyle="round", zorder=5)

        # L-bends are drawn as a single Line2D so solid_joinstyle="round"
        # rounds the corner. Both endpoints carry the line's offset so that
        # consecutive segments meet on the same track without a kink.
        if y1 == y2:
            ax.plot([x1, x2], [y1 + offset, y1 + offset], **kw)
        elif x1 == x2:
            ax.plot([x1 + offset, x1 + offset], [y1, y2], **kw)
        elif ln.bend == "hv":
            cx, cy = x2 + offset, y1 + offset
            ax.plot([x1, cx, cx], [cy, cy, y2 + offset], **kw)
        else:
            cx, cy = x1 + offset, y2 + offset
            ax.plot([cx, cx, x2], [y1 + offset, cy, cy], **kw)

    def _draw_label(self, ax, s, cy):
        if s.label_pos == "above":
            dy_main, dy_sub, va = self.label_dy_main, self.label_dy_sub, "bottom"
        else:
            dy_main, dy_sub, va = -self.label_dy_main, -self.label_dy_sub, "top"
        ax.text(s.x, cy + dy_main, s.label, ha="center", va=va,
                fontweight="bold", fontsize=self.label_font, zorder=15)
        if s.sub:
            ax.text(s.x, cy + dy_sub, s.sub, ha="center", va=va,
                    fontsize=self.sub_font, color="#333", zorder=15)
