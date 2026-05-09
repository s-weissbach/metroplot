"""Build a metroplot Diagram from a Mermaid graph or flowchart definition.

Handles the common subset of Mermaid used for pipeline / DAG diagrams::

    flowchart LR
        FASTQ[Raw Reads] --> QC[FastQC]
        QC --> TRIM[Trim Galore]
        TRIM --> STAR[STAR] & HISAT2[HISAT2]
        STAR & HISAT2 --> COUNTS[featureCounts]

Supported syntax
----------------
- ``graph`` / ``flowchart`` direction headers (direction is ignored; metroplot
  does its own layout)
- Node labels: ``A[text]``, ``A(text)``, ``A((text))``, ``A{text}``
- Arrow edges: ``-->`` and ``---``; labeled variants ``-->|text|`` (label discarded)
- Multi-source / multi-target: ``A & B --> C``, ``A --> B & C``
- Chained arrows: ``A --> B --> C``
- ``%%`` comments

Not supported
-------------
- Subgraphs
- ``classDef`` / ``style`` directives (silently ignored)
- Complex channel operators or dynamic nodes
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Mapping

from metroplot._core import Diagram
from metroplot._pipeline_layout import build_diagram_from_dag

# ── Regex patterns ─────────────────────────────────────────────────────────────

_HEADER_RE = re.compile(r"^\s*(graph|flowchart)\s+\w*\s*$", re.IGNORECASE)
_COMMENT_RE = re.compile(r"%%.*$", re.M)
_SKIP_RE = re.compile(r"^\s*(style|classDef|class|linkStyle|subgraph|end)\b", re.IGNORECASE)

# Splits on --> or --- with an optional |edge-label| in between
_EDGE_SEP_RE = re.compile(r"\s*(?:-->|---)\s*(?:\|[^|]*\|\s*)?")

# Matches a node token: ID followed by optional bracket label
# Groups: (1) id, (2) double-paren label, (3) other bracket label
_NODE_RE = re.compile(
    r"([A-Za-z0-9_]+)"
    r"(?:\s*"
    r"(?:\(\(([^)]+)\)\))"          # ((circle))
    r"|(?:[\[\({>]([^\]\)\}]+)[\]\)}])"  # [rect] (round) {diamond} >asym]
    r")?"
)


# ── Public API ─────────────────────────────────────────────────────────────────

def parse_mermaid_text(
    text: str,
) -> tuple[list[dict], dict[str, set[str]]]:
    """Return ``(rules, deps)`` from a Mermaid source string.

    ``rules`` is a list of ``{"name": id, "label": display_label}`` dicts.
    ``deps``  maps each node id to the set of node ids it feeds into.
    """
    text = _COMMENT_RE.sub("", text)

    labels: dict[str, str] = {}
    deps: dict[str, set[str]] = defaultdict(set)

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or _HEADER_RE.match(line) or _SKIP_RE.match(line):
            continue

        parts = _EDGE_SEP_RE.split(line)

        if len(parts) >= 2:
            # Edge line: parse each segment as a group of nodes (split by &)
            groups = [
                [_parse_node(tok, labels) for tok in _split_amp(seg) if tok]
                for seg in parts
            ]
            for i in range(len(groups) - 1):
                for src in groups[i]:
                    for dst in groups[i + 1]:
                        if src and dst and src != dst:
                            deps[src].add(dst)
        else:
            # Standalone node definition
            _parse_node(line, labels)

    all_ids = (
        set(labels)
        | set(deps)
        | {c for cs in deps.values() for c in cs}
    )
    rules = [{"name": n, "label": labels.get(n, n)} for n in sorted(all_ids)]
    return rules, dict(deps)


def from_mermaid(
    mermaid_text: str,
    *,
    label_overrides: Mapping[str, str] | None = None,
    sub_overrides: Mapping[str, str] | None = None,
    lanes: Mapping[str, Mapping] | None = None,
    line_name: str = "Pipeline",
    color: str = "#1f2a44",
    column_spacing: float = 2.0,
    branch_spacing: float = 2.0,
    legend_loc: str | None = "upper right",
    theme: str = "light",
    background: str | None = None,
) -> Diagram:
    """Parse a Mermaid graph/flowchart string and return a metroplot Diagram.

    Parameters
    ----------
    mermaid_text:
        Raw Mermaid ``graph`` or ``flowchart`` source (as a string).
    label_overrides:
        ``node_id -> display label`` — overrides the in-graph bracket label.
    sub_overrides:
        ``node_id -> sub label`` (small uppercase text under each station).
    lanes:
        ``lane_label -> {"color": "#hex", "rules": [node_id, ...]}``.
        When provided each lane becomes its own metroplot Line.
    line_name, color:
        Default single-line name and colour (used when ``lanes`` is None).
    column_spacing, branch_spacing:
        Grid spacing for the auto-layout.
    legend_loc:
        Matplotlib legend location string, or ``None`` to hide the legend.
    theme:
        Theme name (``"light"``, ``"dark"``, ``"minimal"``) or a Theme object.
    """
    rules, deps = parse_mermaid_text(mermaid_text)
    if not rules:
        raise ValueError("no nodes found in Mermaid graph")

    # Mermaid bracket labels are merged into label_overrides; explicit
    # overrides take priority.
    merged_labels = {r["name"]: r["label"] for r in rules}
    if label_overrides:
        merged_labels.update(label_overrides)

    return build_diagram_from_dag(
        rules, deps,
        line_name=line_name, color=color,
        column_spacing=column_spacing, branch_spacing=branch_spacing,
        legend_loc=legend_loc,
        label_overrides=merged_labels,
        sub_overrides=sub_overrides,
        lanes=lanes,
        theme=theme,
        background=background,
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _split_amp(segment: str) -> list[str]:
    """Split a node-group string on ``&`` and strip whitespace."""
    return [tok.strip() for tok in re.split(r"\s*&\s*", segment.strip())]


def _parse_node(token: str, labels: dict[str, str]) -> str:
    """Extract node id from a Mermaid token; register its display label."""
    m = _NODE_RE.match(token.strip())
    if not m:
        return ""
    node_id = m.group(1)
    raw_label = m.group(2) or m.group(3)  # double-paren or other bracket
    if raw_label is not None:
        labels[node_id] = raw_label.strip()
    elif node_id not in labels:
        labels[node_id] = node_id
    return node_id
