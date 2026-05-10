"""Example: edge text labels on track segments.

Labels are placed at the midpoint of a segment, interrupting the track.
The text height matches the line width and uses the line colour.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metroplot import Diagram

NAVY  = "#1f2a44"
CORAL = "#e07a6b"
BLUE  = "#457b9d"

d = Diagram(line_width=6, legend_loc="upper right")

# Shared input
d.station("fastq",  0, 0, "FASTQ",   "RAW READS",        "below")
d.station("fastp",  2, 0, "fastp",   "ADAPTER TRIMMING",  "below")

# Bulk RNA-seq lane (top)
d.station("star",    4,  2, "STAR",          "ALIGNMENT",        "below")
d.station("fcounts", 6,  2, "featureCounts", "QUANTIFICATION")
d.station("deseq2",  8,  2, "DESeq2",        "DIFF EXPR")

# scRNA-seq lane (middle)
d.station("cellranger", 4,  0, "Cellranger",  "ALIGNMENT", "below")
d.station("scanpy",     6,  0, "Scanpy",      "CLUSTERING", "below")
d.station("markers",    8,  0, "Markers",     "ANNOTATION", "below")

# ATAC-seq lane (bottom)
d.station("bowtie2", 4, -2, "Bowtie2", "ALIGNMENT",    "below")
d.station("macs2",   6, -2, "MACS2",   "PEAK CALLING", "below")
d.station("homer",   8, -2, "HOMER",   "MOTIF ENRICH", "below")

d.line("Bulk RNA-seq", NAVY, [
    ["fastq", "fastp", "star", "fcounts", "deseq2"],
], edge_labels={
    ("fastq",  "fastp"):   "reads",
    ("star",   "fcounts"): "BAM",
    ("fcounts","deseq2"):  "counts",
})

d.line("scRNA-seq", CORAL, [
    ["fastq", "fastp", "cellranger", "scanpy", "markers"],
], edge_labels={
    ("cellranger", "scanpy"):  "matrix",
    ("scanpy",     "markers"): "AnnData",
})

d.line("ATAC-seq", BLUE, [
    ["fastq", "fastp", "bowtie2", "macs2", "homer"],
], edge_labels={
    ("bowtie2", "macs2"): "BAM",
    ("macs2",   "homer"): "peaks",
})

fig, ax = plt.subplots(figsize=(13, 5))
d.render(ax)
plt.tight_layout()
plt.savefig("graphics/example_edge_labels.png", dpi=150, bbox_inches="tight")
print("wrote graphics/example_edge_labels.png")
