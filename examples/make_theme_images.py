"""Generate theme and city-palette showcase images for the README."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from metroplot import Diagram
from metroplot.themes import PALETTES, Theme, THEMES


def make_showcase(colors, theme, filename, figsize=(9, 3.2), bg=None):
    """Three-line parallel pipeline using the first three colours of a palette."""
    c1, c2, c3 = colors[0], colors[1], colors[2]
    d = Diagram(line_width=5, label_font=9, sub_font=7, theme=theme,
                legend_loc="lower right")

    d.station("fastq",  0, 0,  "FASTQ",         "RAW READS",   "above")
    d.station("trim",   2, 0,  "Trim Galore",   "TRIMMING",    "above")

    d.station("star",   4,  1, "STAR",          "ALIGNMENT",   "above")
    d.station("fc",     6,  1, "featureCounts", "QUANTIFY",    "above")
    d.station("de",     8,  1, "DESeq2",        "DIFF EXPR",   "above")

    d.station("cr",     4,  0, "Cellranger",    "ALIGNMENT",   "above")
    d.station("sc",     6,  0, "Scanpy",        "CLUSTERING",  "above")
    d.station("mk",     8,  0, "Markers",       "ANNOTATION",  "above")

    d.station("bw",     4, -1, "Bowtie2",       "ALIGNMENT",   "below")
    d.station("mc",     6, -1, "MACS2",         "PEAK CALL",   "below")
    d.station("hm",     8, -1, "HOMER",         "MOTIF ENRICH","below")

    d.line("Bulk RNA-seq", c1, [["fastq", "trim", "star", "fc", "de"]])
    d.line("scRNA-seq",    c2, [["fastq", "trim", "cr",   "sc", "mk"]])
    d.line("ATAC-seq",     c3, [["fastq", "trim", "bw",   "mc", "hm"]])

    fig, ax = plt.subplots(figsize=figsize)
    d.render(ax)
    if bg:
        fig.patch.set_facecolor(bg)
        fig.patch.set_alpha(1.0)
        ax.set_facecolor(bg)
        ax.patch.set_alpha(1.0)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches="tight",
                facecolor=bg if bg else "white")
    plt.close(fig)
    print(f"wrote {filename}")


# ── Built-in themes (default palette) ────────────────────────────────────────
default_colors = PALETTES["default"]

make_showcase(default_colors, "light",   "graphics/theme_light.png")
make_showcase(default_colors, "dark",    "graphics/theme_dark.png",   bg="#1a1a2e")
make_showcase(default_colors, "minimal", "graphics/theme_minimal.png")

# ── City palettes (light theme) ───────────────────────────────────────────────
for city in ("london", "tokyo", "nyc", "paris", "berlin", "hongkong"):
    colors = PALETTES[city]
    theme = Theme(
        name=city,
        background="none",
        station_fill="white",
        station_edge="#555555",
        station_edge_width=2.0,
        station_dot=False,
        station_colored_edge=True,
        label_color="#1d3557",
        sub_color="#457b9d",
        glow=False,
        palette=colors,
    )
    make_showcase(colors, theme, f"graphics/theme_{city}.png")
