"""Tests for the Mermaid graph parser."""
import matplotlib
matplotlib.use("Agg")

from metroplot.mermaid_io import from_mermaid, parse_mermaid_text


SIMPLE = """
flowchart LR
    A[Start] --> B[Process]
    B --> C[End]
"""

BRANCH = """
graph LR
    FASTQ --> TRIM
    TRIM --> STAR & HISAT2
    STAR & HISAT2 --> COUNTS
    COUNTS --> DESEQ2
"""

LABELED = """
flowchart LR
    A[Raw] -->|filtered| B[Trimmed]
    B --> C((QC))
    B --> D{Branch}
"""

COMMENTS = """
flowchart LR
    %% this is a comment
    A --> B %% inline comment
    B --> C
"""

CHAINED = """
flowchart LR
    A --> B --> C --> D
"""


def test_simple_linear():
    rules, deps = parse_mermaid_text(SIMPLE)
    names = {r["name"] for r in rules}
    assert names == {"A", "B", "C"}
    assert deps["A"] == {"B"}
    assert deps["B"] == {"C"}
    assert "C" not in deps


def test_labels_extracted():
    rules, _ = parse_mermaid_text(SIMPLE)
    by_id = {r["name"]: r["label"] for r in rules}
    assert by_id["A"] == "Start"
    assert by_id["B"] == "Process"
    assert by_id["C"] == "End"


def test_branch_multi_source_target():
    rules, deps = parse_mermaid_text(BRANCH)
    names = {r["name"] for r in rules}
    assert names == {"FASTQ", "TRIM", "STAR", "HISAT2", "COUNTS", "DESEQ2"}
    assert deps["TRIM"] == {"STAR", "HISAT2"}
    assert deps["STAR"] == {"COUNTS"}
    assert deps["HISAT2"] == {"COUNTS"}


def test_edge_labels_ignored():
    rules, deps = parse_mermaid_text(LABELED)
    assert deps["A"] == {"B"}


def test_bracket_styles():
    rules, _ = parse_mermaid_text(LABELED)
    by_id = {r["name"]: r["label"] for r in rules}
    assert by_id["A"] == "Raw"
    assert by_id["B"] == "Trimmed"
    assert by_id["C"] == "QC"    # (( ))
    assert by_id["D"] == "Branch"  # { }


def test_comments_stripped():
    rules, deps = parse_mermaid_text(COMMENTS)
    names = {r["name"] for r in rules}
    assert names == {"A", "B", "C"}
    assert "this" not in names
    assert deps["A"] == {"B"}
    assert deps["B"] == {"C"}


def test_chained_arrows():
    _, deps = parse_mermaid_text(CHAINED)
    assert deps["A"] == {"B"}
    assert deps["B"] == {"C"}
    assert deps["C"] == {"D"}


def test_from_mermaid_returns_diagram():
    d = from_mermaid(BRANCH, legend_loc=None)
    assert {"FASTQ", "TRIM", "STAR", "HISAT2", "COUNTS", "DESEQ2"} <= set(d.stations)
    assert len(d.lines) == 1


def test_label_overrides_win():
    d = from_mermaid(SIMPLE, label_overrides={"A": "Custom"}, legend_loc=None)
    assert d.stations["A"].label == "Custom"


def test_sub_overrides():
    d = from_mermaid(SIMPLE, sub_overrides={"B": "STEP"}, legend_loc=None)
    assert d.stations["B"].sub == "STEP"
