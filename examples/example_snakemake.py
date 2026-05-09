"""Example: build a metroplot Diagram from a Snakemake workflow.

The pipeline is written inline so the example is fully self-contained.
It mirrors a typical bulk RNA-seq Snakemake workflow: quality control,
trimming, alignment, quantification, and differential expression.
"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, "src")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metroplot.snakemake_io import from_snakemake

SNAKEFILE = """\
rule fastqc_raw:
    input:  "data/{sample}.fastq.gz"
    output: "qc/raw/{sample}_fastqc.html"
    shell:  "fastqc {input} -o qc/raw/"

rule trim_galore:
    input:  "data/{sample}.fastq.gz"
    output: "trimmed/{sample}_trimmed.fq.gz"
    shell:  "trim_galore {input} -o trimmed/"

rule fastqc_trim:
    input:  "trimmed/{sample}_trimmed.fq.gz"
    output: "qc/trim/{sample}_fastqc.html"
    shell:  "fastqc {input} -o qc/trim/"

rule star_align:
    input:  "trimmed/{sample}_trimmed.fq.gz"
    output: "aligned/{sample}.bam"
    shell:  "STAR --readFilesIn {input} --outSAMtype BAM"

rule samtools_sort:
    input:  "aligned/{sample}.bam"
    output: "aligned/{sample}.sorted.bam"
    shell:  "samtools sort {input} -o {output}"

rule featurecounts:
    input:  "aligned/{sample}.sorted.bam"
    output: "counts/{sample}_counts.tsv"
    shell:  "featureCounts -a genes.gtf -o {output} {input}"

rule deseq2:
    input:  expand("counts/{sample}_counts.tsv", sample=config["samples"])
    output: "results/de_results.tsv"
    script: "scripts/deseq2.R"

rule multiqc:
    input:
        expand("qc/raw/{sample}_fastqc.html",  sample=config["samples"]),
        expand("qc/trim/{sample}_fastqc.html", sample=config["samples"]),
        "results/de_results.tsv"
    output: "multiqc_report.html"
    shell:  "multiqc ."
"""

with tempfile.TemporaryDirectory() as td:
    (Path(td) / "Snakefile").write_text(SNAKEFILE)
    d = from_snakemake(
        td,
        line_name="Bulk RNA-seq",
        color="#1f2a44",
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
    )

fig, ax = plt.subplots(figsize=(18, 5))
d.render(ax)
fig.savefig("graphics/snakemake_example.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("wrote graphics/snakemake_example.png")
