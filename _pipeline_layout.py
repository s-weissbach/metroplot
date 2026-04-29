"""Shared layout + Diagram-building for parsed pipeline DAGs.

Pipeline-format parsers (snakemake_io, nextflow_io, ...) produce two things:

1. ``rules``: list of ``{"name": str}`` dicts (one per process / rule).
2. ``deps``: ``dict[str, set[str]]`` mapping each rule to the rules that
   consume its outputs.

Everything past that point — layout, station creation, lane assignment,
label overrides — lives here and is shared across formats.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

from metroplot import Diagram


def build_diagram_from_dag(
    rules: list[dict],
    deps: dict[str, set[str]],
    *,
    line_name: str = "Pipeline",
    color: str = "#1f2a44",
    column_spacing: float = 2.0,
    branch_spacing: float = 2.0,
    legend_loc: str | None = "upper right",
    label_overrides: Mapping[str, str] | None = None,
    sub_overrides: Mapping[str, str] | None = None,
    lanes: Mapping[str, Mapping] | None = None,
) -> Diagram:
    """Build a Diagram from a parsed DAG.

    Parameters
    ----------
    rules, deps
        Output of a format-specific parser (see ``snakemake_io``, ``nextflow_io``).
    line_name, color
        Default line for the entire DAG. Ignored when ``lanes`` is provided.
    label_overrides
        ``rule_name -> display label`` (replaces the snake_case rule name).
    sub_overrides
        ``rule_name -> sub label`` (small uppercase line under the bold name).
    lanes
        ``lane_label -> {"color": "#hex", "rules": [...]}``. Each lane becomes
        its own metroplot Line; rules listed in multiple lanes appear as
        parallel tracks on shared segments.
    """
    label_overrides = dict(label_overrides or {})
    sub_overrides = dict(sub_overrides or {})

    incoming = _invert(deps, [r["name"] for r in rules])
    levels = _levels(rules, incoming)
    spine = _longest_spine(rules, deps, incoming)
    positions = _layout(rules, levels, spine, column_spacing, branch_spacing)
    paths = _enumerate_paths(rules, deps, incoming)

    d = Diagram(legend_loc=legend_loc)
    for r in rules:
        x, y = positions[r["name"]]
        label = label_overrides.get(r["name"], r["name"].replace("_", " "))
        sub = sub_overrides.get(r["name"], "")
        d.station(r["name"], x, y, label, sub,
                  label_pos="above" if y > 0 else "below")

    if lanes:
        for lane_label, lane_def in lanes.items():
            lane_rules = set(lane_def["rules"])
            lane_paths = _restrict_paths(paths, lane_rules)
            if lane_paths:
                d.line(lane_label, lane_def["color"], lane_paths)
    else:
        d.line(line_name, color, paths)

    return d


# ---------- DAG helpers ----------


def _invert(deps: dict[str, set[str]], names: Iterable[str]) -> dict[str, set[str]]:
    incoming: dict[str, set[str]] = {n: set() for n in names}
    for u, ds in deps.items():
        for child in ds:
            if child in incoming:
                incoming[child].add(u)
    return incoming


def _levels(rules, incoming) -> dict[str, int]:
    levels: dict[str, int] = {}

    def depth(name: str, stack: frozenset = frozenset()) -> int:
        if name in levels:
            return levels[name]
        if name in stack:
            return 0
        parents = incoming.get(name, set())
        levels[name] = 0 if not parents else 1 + max(
            depth(p, stack | {name}) for p in parents
        )
        return levels[name]

    for r in rules:
        depth(r["name"])
    return levels


def _longest_spine(rules, deps, incoming) -> set[str]:
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
    by_level: dict[int, list[str]] = defaultdict(list)
    for r in rules:
        by_level[levels[r["name"]]].append(r["name"])
    positions: dict[str, tuple[float, float]] = {}
    for level, names in by_level.items():
        x = level * col_spacing
        on_spine = [n for n in names if n in spine]
        off_spine = [n for n in names if n not in spine]
        for n in on_spine:
            positions[n] = (x, 0.0)
        for i, n in enumerate(off_spine, start=1):
            positions[n] = (x, -i * branch_spacing)
    return positions


def _enumerate_paths(rules, deps, incoming) -> list[list[str]]:
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


def _restrict_paths(paths: list[list[str]], allowed: set[str]) -> list[list[str]]:
    """Slice each path to its longest contiguous run of rules in ``allowed``."""
    out: list[list[str]] = []
    for p in paths:
        run: list[str] = []
        for node in p:
            if node in allowed:
                run.append(node)
            else:
                if len(run) >= 2:
                    out.append(run)
                run = []
        if len(run) >= 2:
            out.append(run)
    # de-duplicate identical runs
    seen: set[tuple[str, ...]] = set()
    unique: list[list[str]] = []
    for r in out:
        t = tuple(r)
        if t not in seen:
            seen.add(t)
            unique.append(r)
    return unique
