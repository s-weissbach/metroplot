"""Example: a multi-omics pipeline (bulk RNA-seq, scRNA-seq, ATAC-seq)
sharing a QC trunk, with a bulk splice branch ending at MASER."""
import matplotlib.pyplot as plt

from metroplot import Diagram

NAVY = "#1f2a44"
CORAL = "#e07a6b"
BLUE = "#457b9d"

d = Diagram(legend_loc="upper right")

# Shared trunk
(d.station("fastq",   0.0,  0.0, "FASTQ",         "RAW READS", "below")
  .station("fastqc",  2.0,  0.0, "FastQC",        "QUALITY CONTROL", "below")
  .station("fastp",   4.0,  0.0, "fastp",         "ADAPTER TRIMMING", "below"))

# Bulk RNA-seq DE lane
(d.station("star",    6.0,  2.0, "STAR",          "ALIGNMENT", "below")
  .station("fcounts", 8.0,  2.0, "featureCounts", "QUANTIFICATION")
  .station("deseq2", 10.0,  2.0, "DESeq2",        "DIFFERENTIAL EXPR"))

# Bulk splice branch (off STAR, going up)
(d.station("rmats",   8.0,  4.0, "rMATS",         "ALT SPLICING")
  .station("maser",  10.0,  4.0, "MASER",         "SPLICING ANALYSIS"))

# scRNA-seq lane
(d.station("cellranger", 6.0,  0.0, "Cellranger",  "ALIGNMENT", "below")
  .station("scanpy_qc",  8.0,  0.0, "Scanpy",      "CELL QC + HVG", "below")
  .station("leiden",    10.0,  0.0, "Leiden",      "CLUSTER + ANNOT", "below"))

# ATAC-seq lane
(d.station("bowtie2",   6.0, -2.0, "Bowtie2",     "ALIGNMENT", "below")
  .station("macs2",     8.0, -2.0, "MACS2",       "PEAK CALLING", "below")
  .station("homer",    10.0, -2.0, "HOMER",       "MOTIF ENRICHMENT", "below"))

# Merge + downstream
(d.station("mofa",     12.0,  0.0, "MOFA+",        "MULTI-OMICS FACTORS", "below")
  .station("enrich",   14.0,  0.0, "enrichR",      "PATHWAY ENRICHMENT", "below")
  .station("report",   16.0,  0.0, "Quarto",       "FIGURE-READY REPORT", "below"))

# Bulk has two routes: the main DE path and a splice branch from STAR up to
# rMATS / MASER. Per-segment bend orientation is chosen automatically so the
# divergence and convergence segments don't visually run through the lanes
# they pass between.
d.line("Bulk RNA-seq", NAVY, [
    ["fastq", "fastqc", "fastp", "star", "fcounts", "deseq2", "mofa", "enrich", "report"],
    ["star", "rmats", "maser"],
])

d.line("scRNA-seq", CORAL, [
    ["fastq", "fastqc", "fastp", "cellranger", "scanpy_qc", "leiden", "mofa", "enrich", "report"],
])
d.line("ATAC-seq", BLUE, [
    ["fastq", "fastqc", "fastp", "bowtie2", "macs2", "homer", "mofa", "enrich", "report"],
])

fig, ax = plt.subplots(figsize=(15, 6))
d.render(ax)
plt.tight_layout()
plt.savefig("example.png", dpi=150, bbox_inches="tight")
print("wrote example.png")
