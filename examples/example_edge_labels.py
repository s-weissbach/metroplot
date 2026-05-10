"""Example: edge text labels on track segments.

Labels are placed at the midpoint of a segment, interrupting the track.
Text height matches the line width and uses the line colour. Key rule:
annotate a segment on every line that carries it, or on none.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metroplot import Diagram
from metroplot.themes import PALETTES, LOGO_ORANGE

NAVY, BLUE, TEAL  = "#1f2a44", "#457b9d", "#a8dadc"
CORAL = LOGO_ORANGE

d = Diagram(line_width=6, legend_loc="lower left")

# Shared input — all three lines start here
d.station("fastq",  0, 0, "FASTQ",  "RAW READS",         "above")
d.station("fastp",  2, 0, "fastp",  "TRIMMING",           "above")

# Bulk RNA-seq (top lane)
d.station("star",    4,  2, "STAR",          "ALIGNMENT",        "above")
d.station("fcounts", 6,  2, "featureCounts", "QUANTIFICATION")
d.station("deseq2",  8,  2, "DESeq2",        "DIFF EXPR")

# scRNA-seq (middle lane)
d.station("cellranger", 4,  0, "Cellranger", "ALIGNMENT", "above")
d.station("scanpy",     6,  0, "Scanpy",     "CLUSTERING", "above")
d.station("markers",    8,  0, "Markers",    "ANNOTATION", "above")

# ATAC-seq (bottom lane)
d.station("bowtie2", 4, -2, "Bowtie2", "ALIGNMENT",    "below")
d.station("macs2",   6, -2, "MACS2",   "PEAK CALLING", "below")
d.station("homer",   8, -2, "HOMER",   "MOTIF ENRICH", "below")

# Annotate every segment of every line — consistently
d.line("Bulk RNA-seq", NAVY, [
    ["fastq", "fastp", "star", "fcounts", "deseq2"],
], edge_labels={
    ("fastq",   "fastp"):   "fastq",
    ("star",    "fcounts"): "BAM",
    ("fcounts", "deseq2"):  "counts",
})

d.line("scRNA-seq", CORAL, [
    ["fastq", "fastp", "cellranger", "scanpy", "markers"],
], edge_labels={
    ("fastq",      "fastp"):    "fastq",
    ("cellranger", "scanpy"):   "countmatrix",
    ("scanpy",     "markers"):  "AnnData",
})

d.line("ATAC-seq", BLUE, [
    ["fastq", "fastp", "bowtie2", "macs2", "homer"],
], edge_labels={
    ("fastq",   "fastp"):  "fastq",
    ("bowtie2", "macs2"):  "BAM",
    ("macs2",   "homer"):  "peaks",
})

fig, ax = plt.subplots(figsize=(13, 5))
d.render(ax)
plt.tight_layout()
plt.savefig("graphics/example_edge_labels.png", dpi=150, bbox_inches="tight")
print("wrote graphics/example_edge_labels.png")
plt.close(fig)

# Animated SVG
d.save_svg("graphics/example_edge_labels_animated.svg", animate=True)
print("wrote graphics/example_edge_labels_animated.svg")
