"""Bulk RNA-seq Snakemake workflow → metroplot.

Recommended workflow
--------------------
Generate the Mermaid DAG from your actual Snakemake workflow, then pass
it to from_mermaid / from_mermaid_file:

    # Snakemake 9.0+ native Mermaid output:
    snakemake --dag > dag.mmd

    # Older Snakemake (requires: pip install dot2mermaid):
    snakemake --dag | dot2mermaid > dag.mmd

Then in Python:

    from metroplot import from_mermaid_file
    d = from_mermaid_file("dag.mmd", label_overrides=..., sub_overrides=...)

The inline MERMAID string below is what those commands produce for this
pipeline and is used here so the example is self-contained.
"""
import sys
sys.path.insert(0, "src")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metroplot import from_mermaid

# Equivalent of: snakemake --dag | dot2mermaid
# (or: from metroplot import from_mermaid_file; d = from_mermaid_file("dag.mmd", ...))
MERMAID = """
flowchart LR
    trim_galore --> fastqc_trim
    trim_galore --> star_align
    star_align --> samtools_sort
    samtools_sort --> featurecounts
    featurecounts --> deseq2
    fastqc_raw --> multiqc
    fastqc_trim --> multiqc
    deseq2 --> multiqc
"""

d = from_mermaid(
    MERMAID,
    line_name="Bulk RNA-seq",
    color="#1f2a44",
    background="#f5f6f8",
    column_spacing=2.5,
    branch_spacing=2.5,
    label_overrides={
        "fastqc_raw":    "FastQC",
        "trim_galore":   "Trim Galore",
        "fastqc_trim":   "FastQC",
        "star_align":    "STAR",
        "samtools_sort": "SAMtools",
        "featurecounts": "featureCounts",
        "deseq2":        "DESeq2",
        "multiqc":       "MultiQC",
    },
    sub_overrides={
        "fastqc_raw":    "RAW QC",
        "trim_galore":   "TRIMMING",
        "fastqc_trim":   "TRIM QC",
        "star_align":    "ALIGNMENT",
        "samtools_sort": "SORT/INDEX",
        "featurecounts": "QUANTIFY",
        "deseq2":        "DIFF EXPR",
        "multiqc":       "REPORT",
    },
    legend_loc=None,
)

fig, ax = plt.subplots(figsize=(18, 5))
d.render(ax)
fig.savefig("graphics/snakemake_example.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("wrote graphics/snakemake_example.png")
