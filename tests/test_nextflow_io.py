"""Tests for the Nextflow parser + DAG extraction."""
import textwrap

import matplotlib
matplotlib.use("Agg")

from metroplot.nextflow_io import from_nextflow, parse_nextflow_text


SAMPLE = textwrap.dedent('''
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

    process COUNT {
        input:  path bam
        output: path "counts.tsv"
    }

    workflow {
        ch = Channel.fromPath(params.reads)
        FASTQC(ch)
        TRIM(ch)
        ALIGN(TRIM.out)
        COUNT(ALIGN.out)
    }
''')


def test_parse_finds_all_processes():
    rules, _ = parse_nextflow_text(SAMPLE)
    assert sorted(r["name"] for r in rules) == ["ALIGN", "COUNT", "FASTQC", "TRIM"]


def test_parse_extracts_workflow_edges():
    _, deps = parse_nextflow_text(SAMPLE)
    assert deps.get("TRIM") == {"ALIGN"}
    assert deps.get("ALIGN") == {"COUNT"}
    assert "COUNT" not in deps          # leaf
    assert "FASTQC" not in deps         # leaf — only consumes raw channel


def test_from_nextflow_builds_diagram(tmp_path):
    (tmp_path / "main.nf").write_text(SAMPLE)
    d = from_nextflow(tmp_path, line_name="rnaseq", legend_loc=None)
    assert {"FASTQC", "TRIM", "ALIGN", "COUNT"} <= set(d.stations)
    # spine should put TRIM->ALIGN->COUNT on y=0; FASTQC is off-spine.
    assert d.stations["TRIM"].y == 0
    assert d.stations["ALIGN"].y == 0
    assert d.stations["COUNT"].y == 0
    # FASTQC is at the same depth as TRIM but not on the longest path.
    assert d.stations["FASTQC"].y < 0


def test_lanes_create_separate_lines(tmp_path):
    """When lanes are passed, each lane becomes its own metroplot Line."""
    (tmp_path / "main.nf").write_text(SAMPLE)
    d = from_nextflow(
        tmp_path,
        lanes={
            "qc": {"color": "#aaaaaa", "rules": ["FASTQC"]},
            "main": {"color": "#1f2a44", "rules": ["TRIM", "ALIGN", "COUNT"]},
        },
        legend_loc=None,
    )
    names = [ln.name for ln in d.lines]
    assert "main" in names
    # qc lane only has one rule -> no segments -> not added.
    assert "qc" not in names
