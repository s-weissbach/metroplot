"""Generate theme and city-palette showcase images for the README."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from metroplot import Diagram
from metroplot.themes import PALETTES, THEMES


def make_showcase(theme_name, filename, line_width=5, corner_radius=0.20,
                  figsize=(9, 3.2)):
    """Three-line parallel pipeline rendered with the given theme."""
    theme = THEMES[theme_name]
    colors = theme.palette
    c1, c2, c3 = colors[0], colors[1], colors[2]

    d = Diagram(line_width=line_width, corner_radius=corner_radius,
                label_font=9, sub_font=7, theme=theme_name,
                legend_loc="lower left")

    d.station("fastq",  0, 0,  "FASTQ",         "RAW READS",    "above")
    d.station("trim",   2, 0,  "Trim Galore",   "TRIMMING",     "above")
    d.station("star",   4,  1, "STAR",          "ALIGNMENT",    "above")
    d.station("fc",     6,  1, "featureCounts", "QUANTIFY",     "above")
    d.station("de",     8,  1, "DESeq2",        "DIFF EXPR",    "above")
    d.station("cr",     4,  0, "Cellranger",    "ALIGNMENT",    "above")
    d.station("sc",     6,  0, "Scanpy",        "CLUSTERING",   "above")
    d.station("mk",     8,  0, "Markers",       "ANNOTATION",   "above")
    d.station("bw",     4, -1, "Bowtie2",       "ALIGNMENT",    "below")
    d.station("mc",     6, -1, "MACS2",         "PEAK CALL",    "below")
    d.station("hm",     8, -1, "HOMER",         "MOTIF ENRICH", "below")

    d.line("Bulk RNA-seq", c1, [["fastq", "trim", "star", "fc", "de"]])
    d.line("scRNA-seq",    c2, [["fastq", "trim", "cr",   "sc", "mk"]])
    d.line("ATAC-seq",     c3, [["fastq", "trim", "bw",   "mc", "hm"]])

    fig, ax = plt.subplots(figsize=figsize)
    d.render(ax)

    # Apply a solid background — render() may set it to transparent for some themes.
    # Dark theme has background="none" but needs a dark canvas for the showcase.
    _dark_bg = "#1a1a2e"
    bg = (_dark_bg if theme_name == "dark"
          else theme.background if theme.background not in ("none", "transparent")
          else "white")
    fig.patch.set_facecolor(bg)
    fig.patch.set_alpha(1.0)
    ax.set_facecolor(bg)
    ax.patch.set_alpha(1.0)

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches="tight", facecolor=bg)
    plt.close(fig)
    print(f"wrote {filename}")


# Built-in themes
make_showcase("light",   "graphics/theme_light.png")
make_showcase("dark",    "graphics/theme_dark.png")
make_showcase("minimal", "graphics/theme_minimal.png")

# City themes — line_width and corner_radius tuned per system
make_showcase("london",   "graphics/theme_london.png",   line_width=6, corner_radius=0.25)
make_showcase("nyc",      "graphics/theme_nyc.png",      line_width=7, corner_radius=0.12)
make_showcase("paris",    "graphics/theme_paris.png",    line_width=5, corner_radius=0.22)
make_showcase("berlin",   "graphics/theme_berlin.png",   line_width=5, corner_radius=0.18)
