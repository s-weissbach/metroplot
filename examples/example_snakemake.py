"""WGS variant-calling Snakemake workflow → metroplot.

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
    fastqc --> trimmomatic
    trimmomatic --> bwa_mem
    bwa_mem --> samtools_sort
    samtools_sort --> mark_duplicates
    mark_duplicates --> haplotype_caller
    haplotype_caller --> snpeff
"""

d = from_mermaid(
    MERMAID,
    line_name="WGS Variant Calling",
    color="#1f2a44",
    background="#f5f6f8",
    column_spacing=2.5,
    label_overrides={
        "fastqc":           "FastQC",
        "trimmomatic":      "Trimmomatic",
        "bwa_mem":          "BWA MEM",
        "samtools_sort":    "SAMtools",
        "mark_duplicates":  "Picard",
        "haplotype_caller": "GATK",
        "snpeff":           "SnpEff",
    },
    sub_overrides={
        "fastqc":           "QUALITY CONTROL",
        "trimmomatic":      "TRIMMING",
        "bwa_mem":          "ALIGNMENT",
        "samtools_sort":    "SORT & INDEX",
        "mark_duplicates":  "MARK DUPLICATES",
        "haplotype_caller": "VARIANT CALLING",
        "snpeff":           "ANNOTATION",
    },
    legend_loc=None,
)

fig, ax = plt.subplots(figsize=(16, 3))
d.render(ax)
fig.savefig("graphics/snakemake_example.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("wrote graphics/snakemake_example.png")
