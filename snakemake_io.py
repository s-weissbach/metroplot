"""Build a metroplot Diagram from a Snakemake workflow directory.

Best-effort: parses .smk / Snakefile text to extract rule names and their
``input:`` / ``output:`` file path templates, matches outputs to downstream
inputs to build a DAG, then lays the rules out left-to-right with side
branches placed below the longest source-to-sink spine.

Limitations: dynamic rules, checkpoint outputs, and rules where outputs
are computed via complex Python expressions may not be picked up. Pass
``rule_overrides=`` to fix or augment what the parser extracts.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from metroplot import Diagram


_RULE_HEADER_RE = re.compile(r"^rule\s+(\w+)\s*:", re.M)
_PATH_RE = re.compile(r"""f?["']([^"'\n]+)["']""")


def parse_snakefile_text(text: str) -> list[dict]:
    """Return one dict per rule with keys: name, inputs, outputs."""
    # Split on 'rule NAME:' headers; tokens alternate (preamble, header, body, ...).
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
    """Pull every quoted path under a ``section:`` block (input | output)."""
    pattern = re.compile(
        rf"^[ \t]*{section}\s*:\s*\n((?:[ \t]+.*\n)+?)(?=^[ \t]*\w+\s*:|\Z)",
        re.M,
    )
    m = pattern.search(body)
    if not m:
        return []
    return [match.group(1).strip() for match in _PATH_RE.finditer(m.group(1))]


def parse_workflow(workflow_dir: str | Path) -> list[dict]:
    """Read every Snakefile and *.smk under ``workflow_dir`` (and ``rules/``)."""
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
    line_name: str = "Pipeline",
    color: str = "#1f2a44",
    skip_rules: Iterable[str] = ("all",),
    column_spacing: float = 2.0,
    branch_spacing: float = 2.0,
    legend_loc: str | None = "upper right",
) -> Diagram:
    """Parse a Snakemake workflow directory and return a Diagram.

    Each rule becomes a station. Rules on the longest source-to-sink path
    sit on the main row (y=0); branches drop below at ``branch_spacing``.
    """
    rules = [r for r in parse_workflow(workflow_dir) if r["name"] not in skip_rules]
    if not rules:
        raise ValueError(f"no rules found in {workflow_dir}")

    deps = build_dag(rules)
    incoming = _invert(deps, [r["name"] for r in rules])
    levels = _levels(rules, incoming)
    spine = _longest_spine(rules, deps, incoming, levels)

    positions = _layout(rules, levels, spine, column_spacing, branch_spacing)
    routes = _enumerate_paths(rules, deps, incoming)

    d = Diagram(legend_loc=legend_loc)
    for r in rules:
        x, y = positions[r["name"]]
        label = r["name"].replace("_", " ")
        d.station(r["name"], x, y, label, label_pos="above" if y > 0 else "below")
    d.line(line_name, color, routes)
    return d


# ---------- DAG helpers ----------


def _invert(deps: dict[str, set[str]], names: list[str]) -> dict[str, set[str]]:
    incoming: dict[str, set[str]] = {n: set() for n in names}
    for u, ds in deps.items():
        for child in ds:
            incoming[child].add(u)
    return incoming


def _levels(rules, incoming) -> dict[str, int]:
    """Topological depth: longest path from any source."""
    levels: dict[str, int] = {}

    def depth(name: str, stack: frozenset = frozenset()) -> int:
        if name in levels:
            return levels[name]
        if name in stack:
            return 0  # cycle guard; shouldn't happen in valid Snakemake DAG
        parents = incoming.get(name, set())
        levels[name] = 0 if not parents else 1 + max(
            depth(p, stack | {name}) for p in parents
        )
        return levels[name]

    for r in rules:
        depth(r["name"])
    return levels


def _longest_spine(rules, deps, incoming, levels) -> set[str]:
    """Return the names on one longest source-to-sink path. These stay at y=0."""
    sinks = [r["name"] for r in rules if not deps.get(r["name"])]
    sources = [r["name"] for r in rules if not incoming.get(r["name"])]

    best: list[str] = []

    def walk(node: str, path: list[str]) -> None:
        nonlocal best
        path = path + [node]
        children = deps.get(node, set())
        if not children:
            if len(path) > len(best):
                best = path
            return
        for c in children:
            walk(c, path)

    for src in sources:
        walk(src, [])
    return set(best)


def _layout(rules, levels, spine, col_spacing, branch_spacing):
    """Assign (x, y) per rule. Spine at y=0; off-spine rules below."""
    by_level: dict[int, list[str]] = defaultdict(list)
    for r in rules:
        by_level[levels[r["name"]]].append(r["name"])

    positions: dict[str, tuple[float, float]] = {}
    for level, names_at_level in by_level.items():
        x = level * col_spacing
        spine_here = [n for n in names_at_level if n in spine]
        off_here = [n for n in names_at_level if n not in spine]
        for n in spine_here:
            positions[n] = (x, 0.0)
        for i, n in enumerate(off_here, start=1):
            positions[n] = (x, -i * branch_spacing)
    return positions


def _enumerate_paths(rules, deps, incoming) -> list[list[str]]:
    """All distinct source-to-sink paths through the DAG."""
    sources = [r["name"] for r in rules if not incoming.get(r["name"])]
    paths: list[list[str]] = []

    def walk(node: str, path: list[str]) -> None:
        path = path + [node]
        children = deps.get(node, set())
        if not children:
            paths.append(path)
            return
        for c in children:
            walk(c, path)

    for src in sources:
        walk(src, [])
    return paths
