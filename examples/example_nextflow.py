"""nf-core-style Nextflow pipeline → metroplot.

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
    p2[FASTP]
    p3[STAR]
    p4[FEATURECOUNTS]
    p5[RMATS]
    p6[DESEQ2]
    p7[MULTIQC]
    p0 --> p1
    p0 --> p2
    p2 --> p3
    p3 --> p4
    p3 --> p5
    p4 --> p6
    p1 --> p7
    p6 --> p7
    p5 --> p7
"""

d = from_mermaid(
    MERMAID,
    skip_nodes=["p0"],          # drop the Channel.fromPath source node
    line_name="RNA-seq",
    color="#1f2a44",
    background="#f5f6f8",
    column_spacing=2.5,
    branch_spacing=2.5,
    # Nextflow bracket labels (FASTQC, FASTP, …) are used automatically;
    # sub_overrides reference the p1/p2/… IDs from the Mermaid.
    sub_overrides={
        "p1": "QUALITY CONTROL",
        "p2": "ADAPTER TRIMMING",
        "p3": "ALIGNMENT",
        "p4": "QUANTIFICATION",
        "p5": "ALT SPLICING",
        "p6": "DIFFERENTIAL EXPR",
        "p7": "REPORT",
    },
    legend_loc=None,
)

fig, ax = plt.subplots(figsize=(15, 5))
d.render(ax)
plt.tight_layout()
plt.savefig("graphics/nextflow_example.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("wrote graphics/nextflow_example.png")
