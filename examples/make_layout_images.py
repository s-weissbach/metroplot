"""Generate layout-pattern reference images for the README."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from metroplot import Diagram
from metroplot.themes import PALETTES, LOGO_ORANGE

RED, BLUE, TEAL, NAVY = PALETTES["default"]
CORAL = LOGO_ORANGE


# ── 1. Linear ────────────────────────────────────────────────────────────────
d = Diagram(line_width=5, label_font=9, sub_font=7)
for name, x, label, sub in [
    ("raw",   0, "FASTQ",         "RAW READS"),
    ("qc",    2, "FastQC",        "QUALITY CTRL"),
    ("trim",  4, "Trim Galore",   "TRIMMING"),
    ("align", 6, "STAR",          "ALIGNMENT"),
    ("quant", 8, "featureCounts", "QUANTIFICATION"),
    ("de",   10, "DESeq2",        "DIFF EXPR"),
]:
    d.station(name, x, 0, label, sub, "above")
d.line("RNA-seq", CORAL, [["raw", "qc", "trim", "align", "quant", "de"]])
fig, ax = plt.subplots(figsize=(12, 2.6))
d.render(ax)
plt.tight_layout()
plt.savefig("graphics/layout_linear.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("wrote graphics/layout_linear.png")


# ── 2. Parallel lanes ────────────────────────────────────────────────────────
d = Diagram(line_width=5, label_font=9, sub_font=7)
# Shared trunk
d.station("fastq", 0, 0, "FASTQ",      "RAW READS",   "above")
d.station("trim",  2, 0, "Trim Galore","TRIMMING",     "above")
# Bulk lane
d.station("star",  4,  2, "STAR",       "ALIGNMENT",   "above")
d.station("fc",    6,  2, "featureCounts","QUANTIFY")
d.station("de",    8,  2, "DESeq2",     "DIFF EXPR")
# scRNA lane
d.station("cr",    4,  0, "Cellranger", "ALIGNMENT",   "above")
d.station("sc",    6,  0, "Scanpy",     "CLUSTERING",  "above")
d.station("mk",    8,  0, "Markers",    "ANNOTATION",  "above")
# ATAC lane
d.station("bw",    4, -2, "Bowtie2",   "ALIGNMENT",   "below")
d.station("mc",    6, -2, "MACS2",     "PEAK CALLING","below")
d.station("hm",    8, -2, "HOMER",     "MOTIF ENRICH","below")

d.line("Bulk RNA-seq", NAVY,  [["fastq", "trim", "star", "fc", "de"]])
d.line("scRNA-seq",    CORAL, [["fastq", "trim", "cr",   "sc", "mk"]])
d.line("ATAC-seq",     BLUE,  [["fastq", "trim", "bw",   "mc", "hm"]])

fig, ax = plt.subplots(figsize=(12, 5))
d.render(ax)
plt.tight_layout()
plt.savefig("graphics/layout_parallel.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("wrote graphics/layout_parallel.png")


# ── 3. Loop-back ─────────────────────────────────────────────────────────────
d = Diagram(line_width=5, label_font=9, sub_font=7, legend_loc="lower right")
# Forward trunk (y=0, left → right)
d.station("raw",    0, 0, "FASTQ",         "RAW READS",      "above")
d.station("trim",   3, 0, "Trim Galore",   "TRIMMING",       "above")
d.station("align",  6, 0, "STAR",          "ALIGNMENT",      "above")
# Upper return (y=2, right → left)
d.station("rmats",  6, 2, "rMATS",         "ALT SPLICING",   "above")
d.station("maser",  3, 2, "MASER",         "SPLICING VIZ",   "above")
# Middle return (y=4, right → left)
d.station("quant",  6, 4, "featureCounts", "QUANTIFICATION", "above")
d.station("de",     3, 4, "DESeq2",        "DIFF EXPR",      "above")
d.station("enrich", 0, 4, "clusterProfiler","ENRICHMENT",    "above")

d.line("Alt Splicing",  TEAL,  [["raw", "trim", "align", "rmats", "maser"]])
d.line("Bulk RNA-seq",  CORAL, [["raw", "trim", "align", "quant", "de", "enrich"]])

fig, ax = plt.subplots(figsize=(10, 5))
d.render(ax)
plt.tight_layout()
plt.savefig("graphics/layout_return.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("wrote graphics/layout_return.png")
