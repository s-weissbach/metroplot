"""SVG post-processing: inject a flowing-dash animation layer onto metro tracks.

The animation metaphor is *data flowing through the pipeline* — a shimmer of
dashes that travels along each track.  This is visually distinct from
nf-metro's travelling-ball approach.

The overlay is inserted *before* the station layer so dashes appear behind
station circles.

Usage
-----
    d.save_svg("pipeline.svg", animate=True)

    # or manually:
    from metroplot._svg_animate import inject_flow_animation
    inject_flow_animation("pipeline.svg", [ln.color for ln in d.lines])
"""
from __future__ import annotations

import random
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", _NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

# GID format: metro-track-{line_index}-{route_index}-{segment_index}
_TRACK_RE = re.compile(r"^metro-track-(\d+)-(\d+)-\d+$")


def inject_flow_animation(
    svg_path: str | Path,
    line_colors: list[str],
    *,
    speed: float = 3.0,
    dash_len: float = 6.0,
    gap_len: float = 44.0,
    overlay_opacity: float = 0.42,
    lighten: float = 0.30,
    seed: int | None = None,
) -> None:
    """Add a flowing-dash animation overlay to a metroplot SVG file.

    The file is modified in-place.  Track elements must carry GIDs of the
    form ``metro-track-{line_index}-{route_index}-{segment_index}`` (set by
    ``Diagram.render()``), and station elements must carry GIDs of the form
    ``metro-station-{name}`` so the overlay can be inserted behind them.

    When a line has multiple routes (branches), one route is chosen at random
    for the animation so the dashes don't appear to duplicate at splits.

    Parameters
    ----------
    svg_path:
        Path to the SVG to modify.
    line_colors:
        Hex colours in line order (``[ln.color for ln in d.lines]``).
    speed:
        Seconds for one full animation cycle.
    dash_len / gap_len:
        SVG user-units for the dash pattern.  Larger gap_len = sparser.
    overlay_opacity:
        Overall opacity of the animated overlay (0–1).
    lighten:
        Mix the line colour toward white (0 = exact colour, 1 = white).
    seed:
        Optional RNG seed for reproducible branch selection.
    """
    rng = random.Random(seed)
    path = Path(svg_path)
    content = path.read_text(encoding="utf-8")

    tree = ET.parse(path)
    root = tree.getroot()

    # --- Collect track elements grouped by (line_index, route_index) ------
    tracks_by_line_route: dict[tuple[int, int], list[ET.Element]] = defaultdict(list)
    for elem in root.iter():
        gid = elem.get("id", "")
        m = _TRACK_RE.match(gid)
        if m:
            li, ri = int(m.group(1)), int(m.group(2))
            tracks_by_line_route[(li, ri)].append(elem)

    if not tracks_by_line_route:
        return

    # For each line, collect available route indices then pick one randomly
    routes_per_line: dict[int, list[int]] = defaultdict(list)
    for li, ri in tracks_by_line_route:
        routes_per_line[li].append(ri)

    chosen_route: dict[int, int] = {
        li: rng.choice(sorted(routes))
        for li, routes in routes_per_line.items()
    }

    # Build tracks_by_line using only the chosen route per line
    tracks_by_line: dict[int, list[ET.Element]] = {}
    for (li, ri), elems in tracks_by_line_route.items():
        if ri == chosen_route[li]:
            tracks_by_line.setdefault(li, []).extend(elems)

    # --- Build CSS with per-line phase offsets (so parallel tracks stagger) -
    period = dash_len + gap_len
    css_parts = ["<style>"]

    # Stagger each line by half a period divided across lines so dashes on
    # parallel shared segments are visually offset from each other.
    n_lines = max(tracks_by_line.keys()) + 1 if tracks_by_line else 1
    for li in sorted(tracks_by_line):
        phase = (li * period / max(n_lines, 2)) % period
        css_parts += [
            f"@keyframes metro-flow-{li} {{",
            f"  from {{ stroke-dashoffset: {period + phase:.1f}; }}",
            f"  to   {{ stroke-dashoffset: {phase:.1f}; }}",
            "}",
        ]

    for li in sorted(tracks_by_line):
        color = line_colors[li] if li < len(line_colors) else "#ffffff"
        overlay_color = _lighten_hex(color, lighten)
        css_parts += [
            f".metro-anim-{li} {{",
            "  fill: none;",
            f"  stroke: {overlay_color};",
            f"  opacity: {overlay_opacity};",
            f"  stroke-dasharray: {dash_len:.1f} {gap_len:.1f};",
            "  stroke-linecap: round;",
            f"  animation: metro-flow-{li} {speed:.2f}s linear infinite;",
            "}",
        ]
    css_parts.append("</style>")
    css_block = "\n".join(css_parts)

    # --- Build overlay group of duplicated paths --------------------------
    overlay_parts = ['<g id="metro-animation-overlay">']
    for li, elems in sorted(tracks_by_line.items()):
        for orig in elems:
            for child in _geometry_elements(orig):
                sw = _extract_stroke_width(child.get("style", ""))
                d_attr = child.get("d", "")
                pts = child.get("points", "")
                if d_attr:
                    overlay_parts.append(
                        f'<path class="metro-anim-{li}" '
                        f'stroke-width="{sw}" d="{d_attr}"/>'
                    )
                elif pts:
                    overlay_parts.append(
                        f'<polyline class="metro-anim-{li}" '
                        f'stroke-width="{sw}" points="{pts}"/>'
                    )
    overlay_parts.append("</g>")
    overlay_block = "\n".join(overlay_parts)

    # --- Insert overlay BEFORE the first station group --------------------
    station_marker = re.search(r'<g id="metro-station-', content)
    if station_marker:
        insert_pos = station_marker.start()
        new_content = (
            content[:insert_pos]
            + overlay_block + "\n"
            + css_block + "\n"
            + content[insert_pos:]
        )
    else:
        new_content = content.replace(
            "</svg>",
            f"{overlay_block}\n{css_block}\n</svg>",
            1,
        )

    path.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _geometry_elements(elem: ET.Element) -> list[ET.Element]:
    """Return path/polyline elements that carry geometry for this artist.

    matplotlib wraps GID-tagged artists in <g id="..."> groups; the actual
    <path> or <polyline> is a direct child (sometimes the element itself).
    """
    tag_local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    if tag_local in ("path", "polyline"):
        return [elem]
    results = []
    for child in elem:
        ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if ctag in ("path", "polyline"):
            results.append(child)
    return results


def _extract_stroke_width(style: str) -> str:
    m = re.search(r"stroke-width\s*:\s*([\d.]+)", style)
    return m.group(1) if m else "6"


def _lighten_hex(hex_color: str, amount: float) -> str:
    """Mix hex_color toward white by `amount` (0 = unchanged, 1 = white)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"
