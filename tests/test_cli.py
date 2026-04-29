"""Tests for the CLI entry point."""
import textwrap

import matplotlib
matplotlib.use("Agg")

import pytest
from metroplot.cli import main


SNAKEFILE = textwrap.dedent("""\
    rule download:
        output: "raw.fastq"

    rule fastqc:
        input:  "raw.fastq"
        output: "qc.html"

    rule align:
        input:  "raw.fastq"
        output: "aligned.bam"

    rule count:
        input:  "aligned.bam"
        output: "counts.tsv"
""")

NF_PIPELINE = textwrap.dedent("""\
    process FASTQC {
        input:  path reads
        output: path "*.html"
    }
    process TRIM {
        input:  path reads
        output: path "*.trim.fq", emit: trimmed
    }
    process ALIGN {
        input:  path reads
        output: path "*.bam", emit: bam
    }
    workflow {
        ch = Channel.fromPath(params.reads)
        FASTQC(ch)
        TRIM(ch)
        ALIGN(TRIM.out)
    }
""")


def test_snakemake_subcommand(tmp_path):
    (tmp_path / "Snakefile").write_text(SNAKEFILE)
    out = tmp_path / "out.png"
    main(["snakemake", str(tmp_path), "-o", str(out), "--no-legend"])
    assert out.exists()


def test_nextflow_subcommand(tmp_path):
    (tmp_path / "main.nf").write_text(NF_PIPELINE)
    out = tmp_path / "out.png"
    main(["nextflow", str(tmp_path), "-o", str(out), "--no-legend"])
    assert out.exists()


def test_snakemake_label_overrides(tmp_path):
    (tmp_path / "Snakefile").write_text(SNAKEFILE)
    out = tmp_path / "out.png"
    main([
        "snakemake", str(tmp_path), "-o", str(out),
        "--label-overrides", '{"align": "STAR"}',
        "--no-legend",
    ])
    assert out.exists()


def test_missing_workflow_dir_exits(tmp_path):
    with pytest.raises(SystemExit):
        main(["snakemake", str(tmp_path / "nonexistent")])
