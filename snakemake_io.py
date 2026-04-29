"""Build a metroplot Diagram from a Snakemake workflow directory.

Best-effort: parses .smk / Snakefile text to extract rule names and their
``input:`` / ``output:`` file path templates, matches outputs to downstream
inputs to build a DAG, then defers to ``_pipeline_layout`` for layout.

Limitations: dynamic rules, checkpoint outputs, and rules where outputs
are computed via complex Python expressions may not be picked up.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping

from _pipeline_layout import build_diagram_from_dag
from metroplot import Diagram

_PATH_RE = re.compile(r"""f?["']([^"'\n]+)["']""")


def parse_snakefile_text(text: str) -> list[dict]:
    """Return one dict per rule with keys: name, inputs, outputs."""
    tokens = re.split(r"^(rule\s+\w+\s*:)", text, flags=re.M)
    rules = []
    for i in range(1, len(tokens), 2):
        name = re.match(r"rule\s+(\w+)\s*:", tokens[i]).group(1)
        body = tokens[i + 1] if i + 1 < len(tokens) else ""
        rules.append({
            "name": name,
            "inputs": _extract_paths(body, "input"),
            "outputs": _extract_paths(body, "output"),
        })
    return rules


def _extract_paths(body: str, section: str) -> list[str]:
    pattern = re.compile(
        rf"^[ \t]*{section}\s*:\s*\n((?:[ \t]+.*\n)+?)(?=^[ \t]*\w+\s*:|\Z)",
        re.M,
    )
    m = pattern.search(body)
    if not m:
        return []
    return [match.group(1).strip() for match in _PATH_RE.finditer(m.group(1))]


def parse_workflow(workflow_dir: str | Path) -> list[dict]:
    root = Path(workflow_dir)
    files: list[Path] = []
    for p in [root / "Snakefile", *root.glob("*.smk"), *root.glob("rules/*.smk")]:
        if p.is_file() and p not in files:
            files.append(p)
    rules: list[dict] = []
    for f in files:
        rules.extend(parse_snakefile_text(f.read_text()))
    return rules


def build_dag(rules: list[dict]) -> dict[str, set[str]]:
    """Map each rule name to the set of rules that consume its outputs."""
    producer: dict[str, str] = {}
    for r in rules:
        for path in r["outputs"]:
            producer[path] = r["name"]
    deps: dict[str, set[str]] = defaultdict(set)
    for r in rules:
        for path in r["inputs"]:
            if path in producer and producer[path] != r["name"]:
                deps[producer[path]].add(r["name"])
    return deps


def from_snakemake(
    workflow_dir: str | Path,
    *,
    skip_rules: Iterable[str] = ("all",),
    label_overrides: Mapping[str, str] | None = None,
    sub_overrides: Mapping[str, str] | None = None,
    lanes: Mapping[str, Mapping] | None = None,
    line_name: str = "Pipeline",
    color: str = "#1f2a44",
    column_spacing: float = 2.0,
    branch_spacing: float = 2.0,
    legend_loc: str | None = "upper right",
) -> Diagram:
    """Parse a Snakemake workflow directory and return a Diagram."""
    rules = [r for r in parse_workflow(workflow_dir) if r["name"] not in set(skip_rules)]
    if not rules:
        raise ValueError(f"no rules found in {workflow_dir}")
    deps = build_dag(rules)
    return build_diagram_from_dag(
        rules, deps,
        line_name=line_name, color=color,
        column_spacing=column_spacing, branch_spacing=branch_spacing,
        legend_loc=legend_loc,
        label_overrides=label_overrides, sub_overrides=sub_overrides,
        lanes=lanes,
    )
