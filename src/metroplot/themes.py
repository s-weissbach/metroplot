"""Visual themes for metroplot diagrams.

All built-in themes use a transparent background so diagrams embed cleanly
into any document, slide, or web page regardless of its background colour.

Built-in presets:  "light", "dark", "minimal"

City palettes (pass to ``Theme(palette=PALETTES["london"])`` etc.):
    "london"    London Underground (TfL official colours)
    "tokyo"     Tokyo Metro + Toei Subway
    "nyc"       NYC Subway (MTA official colours)
    "paris"     Paris Métro (RATP official colours)
    "berlin"    Berlin U-Bahn + S-Bahn (BVG official colours)
    "hongkong"  Hong Kong MTR

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
    # metroplot logo orange (coral) — use as a highlight or primary accent
    "logo_orange": ["#e8614a", "#457b9d", "#a8dadc", "#1d3557"],

    # London Underground (TfL official colours)
    "london": [
        "#DA291C",  # Central
        "#10069F",  # Piccadilly
        "#007A33",  # District
        "#6950A1",  # Elizabeth
        "#A45A2A",  # Bakerloo
        "#FFCD00",  # Circle
        "#00A3E0",  # Victoria
        "#7C878E",  # Jubilee
        "#840B55",  # Metropolitan
        "#E89CAE",  # Hammersmith & City
        "#000000",  # Northern
        "#6ECEB2",  # Waterloo & City
        "#00A4A7",  # DLR
        "#EE7C0E",  # Overground
    ],

    # Tokyo Metro + Toei Subway (official line colours)
    "tokyo": [
        "#FF9500",  # Ginza (G)
        "#F62E36",  # Marunouchi (M)
        "#009BBF",  # Tozai (T)
        "#00BB85",  # Chiyoda (C)
        "#8F76D6",  # Hanzomon (Z)
        "#EC6E65",  # Asakusa (A)
        "#006CB6",  # Mita (I)
        "#CE045B",  # Oedo (E)
        "#B5B5AC",  # Hibiya (H)
        "#C1A470",  # Yurakucho (Y)
        "#00AC9B",  # Namboku (N)
        "#9C5E31",  # Fukutoshin (F)
        "#B0C124",  # Shinjuku (S)
    ],

    # NYC Subway (MTA official colours)
    "nyc": [
        "#EE352E",  # 1/2/3
        "#00933C",  # 4/5/6
        "#B933AD",  # 7
        "#2850AD",  # A/C/E
        "#FF6319",  # B/D/F/M
        "#6CBE45",  # G
        "#FCCC0A",  # N/Q/R/W
        "#996633",  # J/Z
        "#A7A9AC",  # L
        "#808183",  # S
    ],

    # Paris Métro (RATP official colours)
    "paris": [
        "#FFBE02",  # M1
        "#006CB8",  # M2
        "#A0006E",  # M4
        "#F68F4B",  # M5
        "#ED1B2A",  # RER A
        "#3C91DC",  # RER B
        "#62259D",  # M14
        "#77C695",  # M6
        "#FF82B4",  # M7
        "#9C983A",  # M3
        "#CEC92A",  # M9
        "#00643C",  # M12
        "#82C8E6",  # M13
        "#D282BE",  # M8
        "#5A230A",  # M11
        "#DC9609",  # M10
    ],

    # Berlin U-Bahn + S-Bahn (BVG official colours)
    "berlin": [
        "#DA421E",  # U2
        "#009BD5",  # U7
        "#8C6DAB",  # U6
        "#16683D",  # U3
        "#7DAD4C",  # U1
        "#F3791D",  # U9
        "#224F86",  # U8
        "#F0D722",  # U4
        "#7E5330",  # U5
        "#007734",  # S2/S25
        "#0066AD",  # S3
        "#DA6BA2",  # S1
        "#EB7405",  # S5
        "#816DA6",  # S7
    ],

    # Hong Kong MTR (official line colours)
    "hongkong": [
        "#007DC5",  # Island Line
        "#ED1D24",  # Tsuen Wan Line
        "#00AB4E",  # Kwun Tong Line
        "#F7943E",  # Tung Chung Line
        "#7D499D",  # Tseung Kwan O Line
        "#923011",  # Tuen Ma Line
        "#A3238F",  # West Rail Line
        "#53B7E8",  # East Rail Line
        "#BAC429",  # South Island Line
        "#00888A",  # Airport Express
        "#F173AC",  # Disneyland Resort Line
    ],
}

# Logo orange as a standalone constant
LOGO_ORANGE = "#e8614a"


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
    station_edge="#555555",
    station_edge_width=2.0,
    station_dot=False,
    station_dot_ratio=0.40,
    station_colored_edge=True,
    label_color="#1d3557",
    sub_color="#457b9d",
    glow=False,
    section_fill="#f4f7fa",
    section_edge="#d0dce8",
    section_edge_width=0.8,
    section_label_color="#4a6a85",
    section_label_font=11,
    section_corner_radius=0.40,
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
