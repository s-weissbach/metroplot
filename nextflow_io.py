"""Build a metroplot Diagram from a Nextflow (DSL2) pipeline.

Parses ``process NAME { ... }`` blocks to find process names, then scans
``workflow [name] { ... }`` blocks for process invocations to extract the
DAG. A call like ``STAR(TRIM.out)`` registers a ``TRIM → STAR`` edge;
``ALIGN(ch1, ch2)`` where ``ch1`` is bound to a process's output is also
picked up. Channel-only sources (``Channel.fromPath(...)``) are ignored.

Limitations: this is a regex-based parser, not a Groovy parser. It handles
the common nf-core layout (one process per file, explicit workflow block
with chained process invocations) but does not understand subworkflow
imports, complex operators (``map``, ``branch``, ``combine``), or processes
called from inside Groovy closures.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping

from _pipeline_layout import build_diagram_from_dag
from metroplot import Diagram

_PROCESS_RE = re.compile(r"^\s*process\s+(\w+)\s*\{", re.M)
_WORKFLOW_RE = re.compile(r"workflow(?:\s+\w+)?\s*\{", re.M)
_CALL_RE = re.compile(r"(\b[A-Z][A-Z0-9_]*)\s*\(([^()]*)\)")
_REF_RE = re.compile(r"\b([A-Z][A-Z0-9_]*)\b")


def parse_nextflow_text(text: str) -> tuple[list[dict], dict[str, set[str]]]:
    """Return (rules, deps) for a Nextflow source string."""
    process_names = {m.group(1) for m in _PROCESS_RE.finditer(text)}
    rules = [{"name": n} for n in sorted(process_names)]

    deps: dict[str, set[str]] = defaultdict(set)
    # channel_owner: channel_name (lowercase identifier) -> producer process
    # E.g., "trim_ch = TRIM(reads)" => channel_owner["trim_ch"] = "TRIM"
    channel_owner: dict[str, str] = {}

    for body in _iter_workflow_bodies(text):
        # Pass 1: discover channel assignments mapping channel names back to processes.
        for line in body.splitlines():
            assign = re.match(r"\s*(\w+)\s*=\s*(\w[\w.]*)\s*\(", line)
            if assign:
                ch_name, callee = assign.group(1), assign.group(2).split(".")[0]
                if callee in process_names:
                    channel_owner[ch_name] = callee
        # Pass 2: register call → arg edges.
        for call in _CALL_RE.finditer(body):
            callee = call.group(1)
            args = call.group(2)
            if callee not in process_names:
                continue
            for ref in _REF_RE.finditer(args):
                producer = ref.group(1).split(".")[0]
                if producer in process_names and producer != callee:
                    deps[producer].add(callee)
            for word in re.finditer(r"\b(\w+)(?:\.out)?\b", args):
                ch = word.group(1)
                if ch in channel_owner and channel_owner[ch] != callee:
                    deps[channel_owner[ch]].add(callee)

    return rules, dict(deps)


def _iter_workflow_bodies(text: str) -> Iterable[str]:
    """Yield the body string of every ``workflow { ... }`` block."""
    for header in _WORKFLOW_RE.finditer(text):
        start = header.end()
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            i += 1
        yield text[start:i - 1]


def parse_pipeline(workflow_dir: str | Path) -> tuple[list[dict], dict[str, set[str]]]:
    """Read every ``main.nf`` / ``*.nf`` under ``workflow_dir``."""
    root = Path(workflow_dir)
    files: list[Path] = []
    for p in [root / "main.nf", *root.glob("*.nf"), *root.glob("modules/**/*.nf"),
              *root.glob("subworkflows/**/*.nf")]:
        if p.is_file() and p not in files:
            files.append(p)
    if not files:
        raise FileNotFoundError(f"no .nf files found under {workflow_dir}")
    full_text = "\n".join(f.read_text() for f in files)
    return parse_nextflow_text(full_text)


def from_nextflow(
    workflow_dir: str | Path,
    *,
    skip_processes: Iterable[str] = (),
    label_overrides: Mapping[str, str] | None = None,
    sub_overrides: Mapping[str, str] | None = None,
    lanes: Mapping[str, Mapping] | None = None,
    line_name: str = "Pipeline",
    color: str = "#1f2a44",
    column_spacing: float = 2.0,
    branch_spacing: float = 2.0,
    legend_loc: str | None = "upper right",
) -> Diagram:
    """Parse a Nextflow pipeline directory and return a Diagram."""
    rules, deps = parse_pipeline(workflow_dir)
    skip = set(skip_processes)
    rules = [r for r in rules if r["name"] not in skip]
    deps = {u: {c for c in cs if c not in skip}
            for u, cs in deps.items() if u not in skip}
    if not rules:
        raise ValueError(f"no processes found in {workflow_dir}")
    return build_diagram_from_dag(
        rules, deps,
        line_name=line_name, color=color,
        column_spacing=column_spacing, branch_spacing=branch_spacing,
        legend_loc=legend_loc,
        label_overrides=label_overrides, sub_overrides=sub_overrides,
        lanes=lanes,
    )
