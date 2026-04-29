"""Example: parse a small nf-core-style Nextflow pipeline and render it.

The pipeline file is generated inline so the example is self-contained.
It mirrors the structure of nf-core/rnaseq: FASTQC + trimming on the
trunk, alignment, then a split into quantification (featureCounts) and
alternative-splicing analysis (rMATS), merging into a multiqc report.
"""
from pathlib import Path
import tempfile

import matplotlib.pyplot as plt

from metroplot.nextflow_io import from_nextflow

PIPELINE = """\
process FASTQC {
    input:  path reads
    output: path "*.html"
    script: "fastqc $reads"
}

process FASTP {
    input:  path reads
    output: path "*.trim.fq.gz", emit: trimmed
    script: "fastp -i $reads -o trim.fq.gz"
}

process STAR {
    input:  path reads
    output: path "*.bam", emit: bam
    script: "STAR --readFilesIn $reads"
}

process FEATURECOUNTS {
    input:  path bam
    output: path "counts.tsv"
    script: "featureCounts -a annotation.gtf -o counts.tsv $bam"
}

process RMATS {
    input:  path bam
    output: path "rmats_out/"
    script: "rmats.py --b1 $bam --gtf annotation.gtf"
}

process DESEQ2 {
    input:  path counts
    output: path "deseq2_results.tsv"
    script: "Rscript deseq2.R $counts"
}

process MULTIQC {
    input:  path reports
    output: path "multiqc_report.html"
    script: "multiqc ."
}

workflow {
    reads_ch = Channel.fromPath(params.reads)
    FASTQC(reads_ch)
    FASTP(reads_ch)
    STAR(FASTP.out)
    FEATURECOUNTS(STAR.out)
    RMATS(STAR.out)
    DESEQ2(FEATURECOUNTS.out)
    MULTIQC(FASTQC.out)
}
"""

with tempfile.TemporaryDirectory() as td:
    nf_dir = Path(td)
    (nf_dir / "main.nf").write_text(PIPELINE)
    d = from_nextflow(
        nf_dir,
        line_name="RNA-seq",
        color="#1f2a44",
        column_spacing=2.5,
        branch_spacing=2.5,
        label_overrides={
            "FASTQC": "FastQC",
            "FASTP": "fastp",
            "STAR": "STAR",
            "FEATURECOUNTS": "featureCounts",
            "RMATS": "rMATS",
            "DESEQ2": "DESeq2",
            "MULTIQC": "MultiQC",
        },
        sub_overrides={
            "FASTQC": "QUALITY CONTROL",
            "FASTP": "ADAPTER TRIMMING",
            "STAR": "ALIGNMENT",
            "FEATURECOUNTS": "QUANTIFICATION",
            "RMATS": "ALT SPLICING",
            "DESEQ2": "DIFFERENTIAL EXPR",
            "MULTIQC": "REPORT",
        },
    )

fig, ax = plt.subplots(figsize=(15, 5))
d.render(ax)
plt.tight_layout()
plt.savefig("graphics/nextflow_example.png", dpi=150, bbox_inches="tight")
print("wrote graphics/nextflow_example.png")
