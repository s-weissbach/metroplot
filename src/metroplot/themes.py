"""Visual themes for metroplot diagrams.

All built-in themes use a transparent background so diagrams embed cleanly
into any document, slide, or web page regardless of its background colour.

Built-in presets:  "light", "dark", "minimal"

The default colour palette is:
    PALETTES["default"] = ["#e63946", "#a8dadc", "#457b9d", "#1d3557"]

Add your own theme:
    from metroplot.themes import Theme, THEMES
    THEMES["myteam"] = Theme(
        name="myteam",
        label_color="#2a2a2a",
        sub_color="#666666",
        palette=["#e63946", "#a8dadc", "#457b9d", "#1d3557"],
    )
Then pass theme="myteam" to Diagram().
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Colour palettes  (line colours for multi-line diagrams)
# ---------------------------------------------------------------------------

PALETTES: dict[str, list[str]] = {
    "default": ["#e63946", "#457b9d", "#a8dadc", "#1d3557"],
}


# ---------------------------------------------------------------------------
# Theme dataclass
# ---------------------------------------------------------------------------

@dataclass
class Theme:
    """All visual knobs for a Diagram.

    background
        Axes and figure fill.  Use ``"none"`` (the default) for a fully
        transparent background that embeds into any document.
    station_dot
        Draw a small filled dot inside each single-line station to show the
        line colour.  Good for light backgrounds.
    station_colored_edge
        Use the line colour for the station ring border instead of
        ``station_edge``.  Good for dark backgrounds.
    glow
        Draw a wider, semi-transparent halo behind each track segment.
    palette
        Ordered list of hex colours for lines.  Referenced via
        ``PALETTES["default"]`` or ``theme.palette[i]``.
    """
    name: str = "custom"

    # Background (transparent by default)
    background: str = "none"

    # Station circles
    station_fill: str = "none"
    station_edge: str = "#111111"
    station_edge_width: float = 2.5
    station_dot: bool = True
    station_dot_ratio: float = 0.42
    station_colored_edge: bool = False

    # Labels
    label_color: str = "#111111"
    sub_color: str = "#555555"

    # Track glow (halo behind each track segment)
    glow: bool = False
    glow_alpha: float = 0.15
    glow_width_multiplier: float = 3.2

    # Section grouping boxes
    section_fill: str = "#f0f4f8"
    section_edge: str = "#cccccc"
    section_edge_width: float = 1.2
    section_label_color: str = "#888888"
    section_label_font: int = 9
    section_corner_radius: float = 0.35

    # Colour palette for multi-line diagrams
    palette: list = field(default_factory=lambda: list(PALETTES["default"]))


# ---------------------------------------------------------------------------
# Built-in presets
# ---------------------------------------------------------------------------

# For use on light backgrounds (white docs, papers, light slides)
LIGHT = Theme(
    name="light",
    background="none",
    station_fill="white",
    station_edge="#222222",
    station_edge_width=2.5,
    station_dot=True,
    station_dot_ratio=0.42,
    station_colored_edge=False,
    label_color="#1d3557",
    sub_color="#457b9d",
    glow=False,
    section_fill="#f0f4f8",
    section_edge="#c8d8e8",
    section_edge_width=1.2,
    section_label_color="#7a9ab5",
    section_label_font=9,
    section_corner_radius=0.35,
    palette=list(PALETTES["default"]),
)

# For use on dark backgrounds (dark slides, dark-mode docs)
DARK = Theme(
    name="dark",
    background="none",
    station_fill="none",        # transparent fill → station reads as a ring
    station_edge="#a8dadc",
    station_edge_width=2.0,
    station_dot=False,
    station_colored_edge=True,  # ring picks up the line colour
    label_color="#f1faee",
    sub_color="#a8dadc",
    glow=True,
    glow_alpha=0.20,
    glow_width_multiplier=3.2,
    section_fill="#1a2a3a",
    section_edge="#2a4a6a",
    section_edge_width=1.0,
    section_label_color="#6a9ab5",
    section_label_font=9,
    section_corner_radius=0.35,
    palette=list(PALETTES["default"]),
)

# For publications: thinner, minimal, no inner dots
MINIMAL = Theme(
    name="minimal",
    background="none",
    station_fill="white",
    station_edge="#555555",
    station_edge_width=1.5,
    station_dot=False,
    station_colored_edge=False,
    label_color="#222222",
    sub_color="#777777",
    glow=False,
    section_fill="#f5f5f5",
    section_edge="#dddddd",
    section_edge_width=0.8,
    section_label_color="#aaaaaa",
    section_label_font=8,
    section_corner_radius=0.25,
    palette=list(PALETTES["default"]),
)

THEMES: dict[str, Theme] = {
    "light":   LIGHT,
    "dark":    DARK,
    "minimal": MINIMAL,
}


def get_theme(name_or_theme: str | Theme) -> Theme:
    """Resolve a theme name or pass a Theme through unchanged."""
    if isinstance(name_or_theme, Theme):
        return name_or_theme
    try:
        return THEMES[name_or_theme]
    except KeyError:
        raise ValueError(
            f"unknown theme {name_or_theme!r}. "
            f"Available: {list(THEMES)}"
        ) from None
