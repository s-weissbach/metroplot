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
    track_spacing: float = 0.18
    station_radius: float = 0.13
    line_width: float = 7.0
    label_font: int = 12
    sub_font: int = 9
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

        for li, ln in enumerate(self.lines):
            for route in ln.routes:
                for a, b in zip(route[:-1], route[1:]):
                    cohort = users[tuple(sorted([a, b]))]
                    offset = (cohort.index(li) - (len(cohort) - 1) / 2) * self.track_spacing
                    self._draw_segment(ax, self.stations[a], self.stations[b], ln, offset)

        for s in self.stations.values():
            ax.add_patch(Circle((s.x, s.y), self.station_radius,
                                facecolor="white", edgecolor="black",
                                linewidth=2.0, zorder=10))
            if s.label:
                self._draw_label(ax, s)

        ax.set_aspect("equal")
        ax.axis("off")
        ax.margins(0.12)
        return ax

    def _draw_segment(self, ax, sa, sb, ln, offset):
        x1, y1, x2, y2 = sa.x, sa.y, sb.x, sb.y
        kw = dict(color=ln.color, linewidth=self.line_width,
                  solid_capstyle="round", solid_joinstyle="round", zorder=5)

        if y1 == y2:
            ax.plot([x1, x2], [y1 + offset, y1 + offset], **kw)
        elif x1 == x2:
            ax.plot([x1 + offset, x1 + offset], [y1, y2], **kw)
        elif ln.bend == "hv":
            cx, cy = x2 + offset, y1 + offset
            ax.plot([x1, cx], [cy, cy], **kw)
            ax.plot([cx, cx], [cy, y2], **kw)
        else:
            cx, cy = x1 + offset, y2 + offset
            ax.plot([cx, cx], [y1, cy], **kw)
            ax.plot([cx, x2], [cy, cy], **kw)

    def _draw_label(self, ax, s):
        if s.label_pos == "above":
            dy_main, dy_sub, va = 0.74, 0.42, "bottom"
        else:
            dy_main, dy_sub, va = -0.74, -0.42, "top"
        ax.text(s.x, s.y + dy_main, s.label, ha="center", va=va,
                fontweight="bold", fontsize=self.label_font)
        if s.sub:
            ax.text(s.x, s.y + dy_sub, s.sub, ha="center", va=va,
                    fontsize=self.sub_font, color="#333")
