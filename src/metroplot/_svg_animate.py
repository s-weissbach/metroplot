"""SVG post-processing: inject a flowing-dash animation layer onto metro tracks.

The animation metaphor is *data flowing through the pipeline* — a shimmer of
dashes that travels along each track.  This is visually distinct from
nf-metro's travelling-ball approach.

Usage
-----
    # 1. Render and save to SVG (GIDs must have been set during render):
    fig, ax = plt.subplots(figsize=(15, 5))
    d.render(ax)
    plt.savefig("pipeline.svg", format="svg", bbox_inches="tight")
    plt.close(fig)

    # 2. Post-process in-place:
    from metroplot._svg_animate import inject_flow_animation
    inject_flow_animation("pipeline.svg", [ln.color for ln in d.lines])

    # Or use the convenience wrapper:
    d.save_svg("pipeline.svg", animate=True)
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", _NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

# IDs injected by _core.py have the form  metro-track-{line_idx}-{seg_idx}
_TRACK_RE = re.compile(r"^metro-track-(\d+)-\d+$")


def inject_flow_animation(
    svg_path: str | Path,
    line_colors: list[str],
    *,
    speed: float = 1.4,
    dash_len: float = 9.0,
    gap_len: float = 15.0,
    overlay_opacity: float = 0.55,
    lighten: float = 0.35,
) -> None:
    """Add a flowing-dash animation overlay to a metroplot SVG file.

    The file is modified in-place.  Track path elements must carry GIDs of
    the form ``metro-track-{line_index}-{segment_index}`` (set automatically
    by ``Diagram.render()``).

    Parameters
    ----------
    svg_path:
        Path to the SVG to modify.
    line_colors:
        Hex colours in line order (e.g. ``[ln.color for ln in d.lines]``).
    speed:
        Seconds for one full animation cycle.
    dash_len / gap_len:
        SVG user-units for the dash pattern.
    overlay_opacity:
        Overall opacity of the animated overlay layer (0–1).
    lighten:
        How much to mix the line colour toward white for the overlay stroke
        (0 = exact line colour, 1 = white).
    """
    path = Path(svg_path)
    content = path.read_text(encoding="utf-8")

    tree = ET.parse(path)
    root = tree.getroot()

    # --- Collect track elements grouped by line index -------------------
    tracks_by_line: dict[int, list[ET.Element]] = {}
    for elem in root.iter():
        gid = elem.get("id", "")
        m = _TRACK_RE.match(gid)
        if m:
            li = int(m.group(1))
            tracks_by_line.setdefault(li, []).append(elem)

    if not tracks_by_line:
        return

    # --- Build CSS -------------------------------------------------------
    period = dash_len + gap_len
    css_parts = [
        "<style>",
        "@keyframes metro-flow {",
        f"  from {{ stroke-dashoffset: {period:.1f}; }}",
        "  to   { stroke-dashoffset: 0; }",
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
            f"  animation: metro-flow {speed:.2f}s linear infinite;",
            "}",
        ]
    css_parts.append("</style>")
    css_block = "\n".join(css_parts)

    # --- Build overlay group of duplicated paths -------------------------
    # matplotlib wraps each GID-tagged artist in a <g id="..."> element;
    # the actual geometry lives on a child <path> or <polyline>.  We walk
    # into the children to find it.

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

    # --- Inject into SVG -------------------------------------------------
    # Insert both blocks just before </svg> so they layer on top.
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
    """Mix hex_color toward white by `amount` (0=unchanged, 1=white)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"
