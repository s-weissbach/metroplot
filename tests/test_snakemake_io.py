"""Tests for the Snakemake parser / DAG / layout helpers."""
import textwrap

import matplotlib
matplotlib.use("Agg")

from snakemake_io import (
    build_dag,
    from_snakemake,
    parse_snakefile_text,
)


SAMPLE = textwrap.dedent('''
    rule download:
        output:
            ref="data/ref.h5ad",
            query="data/query.h5ad",
        script:
            "scripts/download.py"


    rule prep:
        input:
            "data/query.h5ad",
        output:
            "data/prepped.h5ad",
        script:
            "scripts/prep.py"


    rule analyze:
        input:
            prepped="data/prepped.h5ad",
            ref="data/ref.h5ad",
        output:
            "results/out.json",
        script:
            "scripts/analyze.py"
''')


def test_parse_extracts_rules_inputs_outputs():
    rules = parse_snakefile_text(SAMPLE)
    assert [r["name"] for r in rules] == ["download", "prep", "analyze"]
    assert rules[0]["outputs"] == ["data/ref.h5ad", "data/query.h5ad"]
    assert rules[1]["inputs"] == ["data/query.h5ad"]
    assert rules[1]["outputs"] == ["data/prepped.h5ad"]
    assert sorted(rules[2]["inputs"]) == ["data/prepped.h5ad", "data/ref.h5ad"]


def test_build_dag_resolves_path_matches():
    rules = parse_snakefile_text(SAMPLE)
    deps = build_dag(rules)
    assert deps["download"] == {"prep", "analyze"}
    assert deps["prep"] == {"analyze"}
    assert "analyze" not in deps  # leaf


def test_from_snakemake_on_workflow_dir(tmp_path):
    """End-to-end: write a small workflow to a tmp dir, build a Diagram."""
    (tmp_path / "Snakefile").write_text(SAMPLE)
    d = from_snakemake(tmp_path, line_name="Test", legend_loc=None)
    assert set(d.stations) == {"download", "prep", "analyze"}
    assert len(d.lines) == 1
    # x positions follow topological depth: download=0, prep=1, analyze=2
    xs = {n: s.x for n, s in d.stations.items()}
    assert xs["download"] < xs["prep"] < xs["analyze"]
    # all on the spine -> y=0
    assert all(s.y == 0 for s in d.stations.values())
