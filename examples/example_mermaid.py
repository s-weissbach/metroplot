"""Mermaid graph → metroplot diagram.

Demonstrates parsing a Mermaid flowchart string directly into a Diagram.
The pipeline below is a compact RNA-seq workflow written in Mermaid syntax.
"""
import sys
sys.path.insert(0, "src")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metroplot.mermaid_io import from_mermaid

MERMAID = """
flowchart LR
    FASTQ[Raw Reads]   --> FASTQC[FastQC]
    FASTQ              --> TRIM[Trim Galore]
    TRIM               --> STAR[STAR]
    TRIM               --> HISAT2[HISAT2]
    STAR               --> RMATS[rMATS]
    STAR & HISAT2      --> COUNTS[featureCounts]
    COUNTS             --> DESEQ2[DESeq2]
    DESEQ2             --> GSEA[fgsea]
    DESEQ2             --> PATHWAY[clusterProfiler]
    HISAT2             --> BIGWIG[bigWig]
"""

d = from_mermaid(
    MERMAID,
    line_name="RNA-seq",
    color="#e8614a",
    background="#f5f6f8",
    sub_overrides={
        "FASTQ":   "INPUT",
        "FASTQC":  "QC",
        "TRIM":    "TRIMMING",
        "STAR":    "ALIGNMENT",
        "HISAT2":  "ALIGNMENT",
        "RMATS":   "ALT SPLICING",
        "COUNTS":  "QUANTIFY",
        "DESEQ2":  "DIFF EXPR",
        "GSEA":    "ENRICHMENT",
        "PATHWAY": "ENRICHMENT",
        "BIGWIG":  "COVERAGE",
    },
    column_spacing=3.0,
    branch_spacing=2.5,
    legend_loc=None,
)

fig, ax = plt.subplots(figsize=(18, 6))
d.render(ax=ax)
fig.savefig("graphics/mermaid_example.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("wrote graphics/mermaid_example.png")
