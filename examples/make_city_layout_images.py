"""Generate city-themed layout-pattern images for the README."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from metroplot import Diagram
from metroplot.themes import PALETTES, THEMES

# Per-city Diagram kwargs that match the recommended settings in the README
CITY_OPTS = {
    "london": dict(line_width=6, corner_radius=0.25),
    "nyc":    dict(line_width=7, corner_radius=0.12),
    "paris":  dict(line_width=5, corner_radius=0.22),
    "berlin": dict(line_width=5, corner_radius=0.18),
}


def _save(fig, theme_name, pattern_name):
    th = THEMES[theme_name]
    bg = th.background if th.background not in ("none", "transparent") else "white"
    fig.patch.set_facecolor(bg)
    fig.patch.set_alpha(1.0)
    for ax in fig.axes:
        ax.set_facecolor(bg)
        ax.patch.set_alpha(1.0)
    path = f"graphics/layout_{theme_name}_{pattern_name}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=bg)
    plt.close(fig)
    print(f"wrote {path}")


for city, opts in CITY_OPTS.items():
    pal = THEMES[city].palette
    c1, c2, c3 = pal[0], pal[1], pal[2]

    # ── 1. Linear ────────────────────────────────────────────────────────────
    d = Diagram(theme=city, label_font=9, sub_font=7, **opts)
    for name, x, label, sub in [
        ("raw",   0, "FASTQ",         "RAW READS"),
        ("qc",    2, "FastQC",        "QUALITY CTRL"),
        ("trim",  4, "Trim Galore",   "TRIMMING"),
        ("align", 6, "STAR",          "ALIGNMENT"),
        ("quant", 8, "featureCounts", "QUANTIFICATION"),
        ("de",   10, "DESeq2",        "DIFF EXPR"),
    ]:
        d.station(name, x, 0, label, sub, "above")
    d.line("RNA-seq", c1, [["raw", "qc", "trim", "align", "quant", "de"]])
    fig, ax = plt.subplots(figsize=(12, 2.6))
    d.render(ax)
    plt.tight_layout()
    _save(fig, city, "linear")

    # ── 2. Parallel lanes ────────────────────────────────────────────────────
    d = Diagram(theme=city, label_font=9, sub_font=7, legend_loc="lower left", **opts)
    d.station("fastq", 0,  0, "FASTQ",        "RAW READS",    "above")
    d.station("trim",  2,  0, "Trim Galore",  "TRIMMING",     "above")
    d.station("star",  4,  2, "STAR",         "ALIGNMENT",    "above")
    d.station("fc",    6,  2, "featureCounts","QUANTIFY")
    d.station("de",    8,  2, "DESeq2",       "DIFF EXPR")
    d.station("cr",    4,  0, "Cellranger",   "ALIGNMENT",    "above")
    d.station("sc",    6,  0, "Scanpy",       "CLUSTERING",   "above")
    d.station("mk",    8,  0, "Markers",      "ANNOTATION",   "above")
    d.station("bw",    4, -2, "Bowtie2",      "ALIGNMENT",    "below")
    d.station("mc",    6, -2, "MACS2",        "PEAK CALLING", "below")
    d.station("hm",    8, -2, "HOMER",        "MOTIF ENRICH", "below")
    d.line("Bulk RNA-seq", c1, [["fastq", "trim", "star", "fc", "de"]])
    d.line("scRNA-seq",    c2, [["fastq", "trim", "cr",   "sc", "mk"]])
    d.line("ATAC-seq",     c3, [["fastq", "trim", "bw",   "mc", "hm"]])
    fig, ax = plt.subplots(figsize=(12, 5))
    d.render(ax)
    plt.tight_layout()
    _save(fig, city, "parallel")

    # ── 3. Loop-back ─────────────────────────────────────────────────────────
    d = Diagram(theme=city, label_font=9, sub_font=7, legend_loc="lower right", **opts)
    d.station("raw",    0, 0, "FASTQ",          "RAW READS",      "above")
    d.station("trim",   3, 0, "Trim Galore",    "TRIMMING",       "above")
    d.station("align",  6, 0, "STAR",           "ALIGNMENT",      "above")
    d.station("rmats",  6, 2, "rMATS",          "ALT SPLICING",   "above")
    d.station("maser",  3, 2, "MASER",          "SPLICING VIZ",   "above")
    d.station("quant",  6, 4, "featureCounts",  "QUANTIFICATION", "above")
    d.station("de",     3, 4, "DESeq2",         "DIFF EXPR",      "above")
    d.station("enrich", 0, 4, "clusterProfiler","ENRICHMENT",     "above")
    d.line("Alt Splicing", c2, [["raw", "trim", "align", "rmats", "maser"]])
    d.line("Bulk RNA-seq", c1, [["raw", "trim", "align", "quant", "de", "enrich"]])
    fig, ax = plt.subplots(figsize=(10, 5))
    d.render(ax)
    plt.tight_layout()
    _save(fig, city, "return")

    # ── 4. Wide fan-out ──────────────────────────────────────────────────────
    d = Diagram(theme=city, label_font=9, sub_font=7, auto_bend=False, **opts)
    d.station("input", 0, 0, "FASTQ", "RAW READS", "above")
    d.station("hub",   2, 0, "fastp", "TRIMMING",  "left")
    branches = [
        ("rna",   "Bulk RNA-seq", "DEG ANALYSIS",  2.5),
        ("scrna", "scRNA-seq",    "CELL ATLAS",    1.5),
        ("atac",  "ATAC-seq",     "CHROMATIN",     0.5),
        ("chip",  "ChIP-seq",     "BINDING SITES",-0.5),
        ("meth",  "RRBS",         "METHYLATION",  -1.5),
        ("hic",   "Hi-C",         "3D GENOME",    -2.5),
    ]
    routes = []
    for name, label, sub, y in branches:
        d.station(name, 6, y, label, sub, "right")
        routes.append(["input", "hub", name])
    d.line("Multi-omics", c1, routes, bend="vh")
    fig, ax = plt.subplots(figsize=(9, 7))
    d.render(ax)
    plt.tight_layout()
    _save(fig, city, "fanout")

    # ── 5. Serpentine ────────────────────────────────────────────────────────
    d = Diagram(theme=city, label_font=9, sub_font=7, **opts)
    d.station("s00", 0, 0, "FASTQ",         "RAW READS",    "above")
    d.station("s01", 3, 0, "Trim Galore",   "TRIMMING",     "above")
    d.station("s02", 6, 0, "STAR",          "ALIGNMENT",    "above")
    d.station("s03", 9, 0, "UMI-tools",     "DEDUP",        "right")
    d.station("s10", 9, 2, "featureCounts", "QUANTIFY",     "right")
    d.station("s11", 6, 2, "DESeq2",        "DIFF EXPR",    "above")
    d.station("s12", 3, 2, "fgsea",         "ENRICHMENT",   "above")
    d.station("s13", 0, 2, "clusterProfiler","PATHWAYS",    "left")
    d.station("s20", 0, 4, "MultiQC",       "QC REPORT",    "above")
    d.station("s21", 3, 4, "Volcano",       "DE PLOTS",     "above")
    d.station("s22", 6, 4, "Heatmap",       "EXPRESSION",   "above")
    d.station("s23", 9, 4, "Quarto",        "FINAL REPORT", "above")
    d.line("RNA-seq", c1, [[
        "s00","s01","s02","s03",
        "s10","s11","s12","s13",
        "s20","s21","s22","s23",
    ]])
    fig, ax = plt.subplots(figsize=(12, 6))
    d.render(ax)
    plt.tight_layout()
    _save(fig, city, "serpentine")
