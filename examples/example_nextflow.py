"""ChIP-seq Nextflow pipeline → metroplot.

Recommended workflow
--------------------
Generate the Mermaid DAG with Nextflow's built-in support (22.04+),
then pass it to from_mermaid / from_mermaid_file:

    nextflow run pipeline.nf -with-dag dag.mmd

Then in Python:

    from metroplot import from_mermaid_file
    d = from_mermaid_file(
        "dag.mmd",
        skip_nodes=["p0"],          # drop Channel.fromPath source node
        label_overrides=...,
        sub_overrides=...,
    )

Nextflow uses sequential IDs (p0, p1, …) with bracket labels for each
node.  Channel source nodes (((Channel.fromPath))) can be dropped with
skip_nodes.

The inline MERMAID string below is representative of what
``nextflow run -with-dag dag.mmd`` produces and is used here so the
example is self-contained.
"""
import sys
sys.path.insert(0, "src")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metroplot import from_mermaid

# Equivalent of: nextflow run pipeline.nf -with-dag dag.mmd
# (or: from metroplot import from_mermaid_file; d = from_mermaid_file("dag.mmd", ...))
MERMAID = """
flowchart TD
    p0((Channel.fromPath))
    p1[FASTQC]
    p2[TRIM_GALORE]
    p3[BOWTIE2]
    p4[SAMTOOLS_SORT]
    p5[PICARD_DEDUP]
    p6[MACS2]
    p7[DEEPTOOLS]
    p0 --> p1
    p1 --> p2
    p2 --> p3
    p3 --> p4
    p4 --> p5
    p5 --> p6
    p6 --> p7
"""

d = from_mermaid(
    MERMAID,
    skip_nodes=["p0"],          # drop the Channel.fromPath source node
    line_name="ChIP-seq",
    color="#1f2a44",
    background="#f5f6f8",
    column_spacing=2.5,
    # Bracket labels (FASTQC, TRIM_GALORE, …) become display names automatically.
    # label_overrides uses the p1/p2/... IDs to further rename if needed:
    label_overrides={
        "p2": "Trim Galore",
        "p3": "Bowtie2",
        "p4": "SAMtools",
        "p5": "Picard",
        "p7": "deepTools",
    },
    sub_overrides={
        "p1": "QUALITY CONTROL",
        "p2": "TRIMMING",
        "p3": "ALIGNMENT",
        "p4": "SORT & INDEX",
        "p5": "DEDUPLICATION",
        "p6": "PEAK CALLING",
        "p7": "COVERAGE",
    },
    legend_loc=None,
)

fig, ax = plt.subplots(figsize=(16, 3))
d.render(ax)
fig.savefig("graphics/nextflow_example.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("wrote graphics/nextflow_example.png")
