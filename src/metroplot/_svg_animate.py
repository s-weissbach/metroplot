"""SVG post-processing: inject animated metro-cart overlay.

White rectangles with black outlines travel along each line's route,
visualising data flowing through the pipeline.  Carts are randomly
distributed so they appear to arrive at roughly one per second.

Usage
-----
    d.save_svg("pipeline.svg", animate=True)

    # or manually:
    from metroplot._svg_animate import inject_cart_animation
    line_routes = [(ln.color, list(ln.routes[0])) for ln in d.lines if ln.routes]
    inject_cart_animation("pipeline.svg", line_routes)
"""
from __future__ import annotations

import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", _NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

_NUM_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_TRACK_RE = re.compile(r"^metro-track-\d+-\d+-\d+$")


def inject_cart_animation(
    svg_path: str | Path,
    line_routes: list[tuple[str, list[str]]],
    *,
    dur: float = 12.0,
    carts_per_line: int = 12,
    seed: int | None = None,
) -> None:
    """Add animated metro-cart overlay to a metroplot SVG (modified in-place).

    Parameters
    ----------
    svg_path:
        Path to the SVG to modify.
    line_routes:
        List of ``(hex_color, [station_name, ...])`` in line order.
    dur:
        Seconds for one cart to traverse the full route.
    carts_per_line:
        Number of cart instances per line (~1/s with default dur=12, carts=12).
    seed:
        Optional RNG seed for reproducible begin-time distribution.
    """
    rng = random.Random(seed)
    path = Path(svg_path)
    content = path.read_text(encoding="utf-8")

    tree = ET.parse(path)
    root = tree.getroot()

    station_centers = _extract_station_centers(root)
    if not station_centers:
        return

    sw = _extract_track_stroke_width(root)
    cart_w = sw * 2.8
    cart_h = sw * 1.5
    cart_rx = sw * 0.35
    hw, hh = cart_w / 2, cart_h / 2

    defs_parts: list[str] = []
    cart_parts: list[str] = ['<g id="metro-carts">']

    for li, (_, station_names) in enumerate(line_routes):
        centers = [station_centers[n] for n in station_names if n in station_centers]
        if len(centers) < 2:
            continue

        route_id = f"metro-route-{li}"
        defs_parts.append(
            f'<path id="{route_id}" d="{_build_route_path(centers)}"'
            f' fill="none" stroke="none"/>'
        )

        for _ in range(carts_per_line):
            begin = -rng.uniform(0.0, dur)
            cart_parts.append(
                f'<rect width="{cart_w:.1f}" height="{cart_h:.1f}"'
                f' x="{-hw:.1f}" y="{-hh:.1f}" rx="{cart_rx:.1f}"'
                f' fill="#ffffff" stroke="#222222" stroke-width="1.2" opacity="0.90">'
                f'<animateMotion dur="{dur:.1f}s" begin="{begin:.2f}s"'
                f' repeatCount="indefinite" rotate="auto" calcMode="paced">'
                f'<mpath xlink:href="#{route_id}"/>'
                f'</animateMotion>'
                f'</rect>'
            )

    cart_parts.append("</g>")

    if not defs_parts:
        return

    defs_block = "<defs>\n" + "\n".join(defs_parts) + "\n</defs>"
    cart_block = "\n".join(cart_parts)

    station_marker = re.search(r'<g id="metro-station-', content)
    if station_marker:
        ins = station_marker.start()
        new_content = content[:ins] + defs_block + "\n" + cart_block + "\n" + content[ins:]
    else:
        new_content = content.replace(
            "</svg>", defs_block + "\n" + cart_block + "\n</svg>", 1
        )

    path.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_station_centers(root: ET.Element) -> dict[str, tuple[float, float]]:
    """Return SVG pixel centers keyed by station name from metro-station-* groups."""
    centers: dict[str, tuple[float, float]] = {}
    for elem in root.iter():
        gid = elem.get("id", "")
        if not gid.startswith("metro-station-"):
            continue
        name = gid[len("metro-station-"):]
        for child in _walk_paths(elem):
            d = child.get("d", "")
            nums = [float(x) for x in _NUM_RE.findall(d)]
            if len(nums) >= 4:
                xs = nums[0::2]
                ys = nums[1::2]
                centers[name] = (
                    (min(xs) + max(xs)) / 2,
                    (min(ys) + max(ys)) / 2,
                )
                break
    return centers


def _extract_track_stroke_width(root: ET.Element) -> float:
    """Return stroke-width (px) from the first metro-track-* path element."""
    for elem in root.iter():
        if not _TRACK_RE.match(elem.get("id", "")):
            continue
        for child in _walk_paths(elem):
            m = re.search(r"stroke-width\s*:\s*([\d.]+)", child.get("style", ""))
            if m:
                return float(m.group(1))
    return 8.0


def _walk_paths(elem: ET.Element):
    """Yield <path> and <polyline> descendants depth-first."""
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    if tag in ("path", "polyline"):
        yield elem
    for child in elem:
        yield from _walk_paths(child)


def _build_route_path(centers: list[tuple[float, float]]) -> str:
    """Build an SVG path through SVG-pixel station centers with L-bends.

    Uses VH (vertical-first) when the move is at least 70 % as tall as it is
    wide — this matches the auto_bend collision-avoidance logic in the renderer
    for typical U-turn layouts where tall branches hang off a horizontal spine.
    """
    if len(centers) < 2:
        return ""
    x_prev, y_prev = centers[0]
    parts = [f"M {x_prev:.1f} {y_prev:.1f}"]
    for x_cur, y_cur in centers[1:]:
        dx = abs(x_cur - x_prev)
        dy = abs(y_cur - y_prev)
        if dy < 2.0 or dx < 2.0:
            parts.append(f"L {x_cur:.1f} {y_cur:.1f}")
        elif dy > 0.7 * dx:
            # VH: go vertical first, then horizontal
            parts.append(f"L {x_prev:.1f} {y_cur:.1f}")
            parts.append(f"L {x_cur:.1f} {y_cur:.1f}")
        else:
            # HV: go horizontal first, then vertical
            parts.append(f"L {x_cur:.1f} {y_prev:.1f}")
            parts.append(f"L {x_cur:.1f} {y_cur:.1f}")
        x_prev, y_prev = x_cur, y_cur
    return " ".join(parts)
