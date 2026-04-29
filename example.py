"""Example: a multi-omics pipeline (bulk RNA-seq, scRNA-seq, ATAC-seq)
sharing an upstream QC trunk and a downstream integration trunk."""
import matplotlib.pyplot as plt

from metroplot import Diagram

NAVY  = "#1f2a44"
ORANGE = "#e07a6b"
GREEN = "#5d9c8a"

d = Diagram()

# Shared trunk
(d.station("fastq",   0.0,  0.0, "FASTQ",          "RAW READS", "below")
  .station("fastqc",  2.0,  0.0, "FastQC",         "QUALITY CONTROL", "below")
  .station("fastp",   4.0,  0.0, "fastp",          "ADAPTER TRIMMING", "below"))

# Bulk RNA-seq lane (top)
(d.station("star",     6.0,  2.0, "STAR",           "ALIGNMENT")
  .station("fcounts",  8.0,  2.0, "featureCounts",  "QUANTIFICATION")
  .station("deseq2",  10.0,  2.0, "DESeq2",         "DIFFERENTIAL EXPR"))

# scRNA-seq lane (middle)
(d.station("cellranger", 6.0,  0.0, "Cellranger",   "ALIGNMENT", "below")
  .station("scanpy_qc",  8.0,  0.0, "Scanpy",       "CELL QC + HVG", "below")
  .station("leiden",    10.0,  0.0, "Leiden",       "CLUSTER + ANNOT", "below"))

# ATAC-seq lane (bottom)
(d.station("bowtie2",   6.0, -2.0, "Bowtie2",       "ALIGNMENT", "below")
  .station("macs2",     8.0, -2.0, "MACS2",         "PEAK CALLING", "below")
  .station("homer",    10.0, -2.0, "HOMER",         "MOTIF ENRICHMENT", "below"))

# Merge + downstream
(d.station("mofa",     12.0,  0.0, "MOFA+",         "MULTI-OMICS FACTORS", "below")
  .station("enrich",   14.0,  0.0, "enrichR",       "PATHWAY ENRICHMENT", "below")
  .station("report",   16.0,  0.0, "Quarto",        "FIGURE-READY REPORT", "below"))

# Lines
d.line("bulk", NAVY, [
    ["fastq", "fastqc", "fastp", "star", "fcounts", "deseq2", "mofa", "enrich", "report"],
])
d.line("scrna", ORANGE, [
    ["fastq", "fastqc", "fastp", "cellranger", "scanpy_qc", "leiden", "mofa", "enrich", "report"],
])
d.line("atac", GREEN, [
    ["fastq", "fastqc", "fastp", "bowtie2", "macs2", "homer", "mofa", "enrich", "report"],
])

fig, ax = plt.subplots(figsize=(15, 5))
d.render(ax)
plt.tight_layout()
plt.savefig("example.png", dpi=150, bbox_inches="tight")
print("wrote example.png")
