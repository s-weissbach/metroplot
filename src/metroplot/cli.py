"""Command-line interface for metroplot.

Usage:
    metroplot snakemake <workflow_dir> [options]
    metroplot nextflow  <workflow_dir> [options]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("workflow_dir", help="path to the workflow directory")
    p.add_argument("-o", "--output", default="pipeline.png",
                   help="output image path (default: pipeline.png)")
    p.add_argument("--line-name", default="Pipeline",
                   help="label shown in the legend")
    p.add_argument("--color", default="#1f2a44",
                   help="hex color for the default line")
    p.add_argument("--label-overrides", type=json.loads, default={},
                   metavar="JSON",
                   help='JSON object mapping rule names to display labels, e.g. \'{"STAR":"STAR aligner"}\'')
    p.add_argument("--sub-overrides", type=json.loads, default={},
                   metavar="JSON",
                   help='JSON object mapping rule names to sub-labels')
    p.add_argument("--column-spacing", type=float, default=2.0,
                   metavar="FLOAT")
    p.add_argument("--branch-spacing", type=float, default=2.0,
                   metavar="FLOAT")
    p.add_argument("--no-legend", action="store_true",
                   help="omit the legend")
    p.add_argument("--theme", default="light",
                   help='visual theme: "light" (default), "dark", "paper", or a custom '
                        'name registered in metroplot.themes.THEMES')
    p.add_argument("--animate", action="store_true",
                   help="inject flowing-dash animation (SVG output only)")
    p.add_argument("--dpi", type=int, default=150)
    p.add_argument("--figsize", nargs=2, type=float, default=[15, 5],
                   metavar=("W", "H"))


def cmd_snakemake(args: argparse.Namespace) -> None:
    from metroplot.snakemake_io import from_snakemake

    skip = list(args.skip_rules) if args.skip_rules else ["all"]
    d = from_snakemake(
        args.workflow_dir,
        skip_rules=skip,
        line_name=args.line_name,
        color=args.color,
        label_overrides=args.label_overrides or None,
        sub_overrides=args.sub_overrides or None,
        column_spacing=args.column_spacing,
        branch_spacing=args.branch_spacing,
        legend_loc=None if args.no_legend else "upper right",
        theme=args.theme,
    )
    _save(d, args)


def _save(d, args: argparse.Namespace) -> None:
    out = Path(args.output)
    animate = getattr(args, "animate", False)
    if out.suffix.lower() == ".svg" or animate:
        if out.suffix.lower() != ".svg":
            out = out.with_suffix(".svg")
            print(f"note: --animate requires SVG output; writing to {out}")
        d.save_svg(out, dpi=args.dpi, animate=animate)
    else:
        fig, ax = plt.subplots(figsize=args.figsize)
        d.render(ax)
        plt.tight_layout()
        plt.savefig(out, dpi=args.dpi, bbox_inches="tight")
        plt.close(fig)
    print(f"wrote {out}")


def cmd_nextflow(args: argparse.Namespace) -> None:
    from metroplot.nextflow_io import from_nextflow

    skip = list(args.skip_processes) if args.skip_processes else []
    d = from_nextflow(
        args.workflow_dir,
        skip_processes=skip,
        line_name=args.line_name,
        color=args.color,
        label_overrides=args.label_overrides or None,
        sub_overrides=args.sub_overrides or None,
        column_spacing=args.column_spacing,
        branch_spacing=args.branch_spacing,
        legend_loc=None if args.no_legend else "upper right",
        theme=args.theme,
    )
    _save(d, args)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="metroplot",
        description="Generate subway-style pipeline diagrams from Snakemake or Nextflow workflows.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sm = sub.add_parser("snakemake", help="render a Snakemake workflow")
    _add_common_args(sm)
    sm.add_argument("--skip-rules", nargs="*", default=["all"],
                    metavar="RULE",
                    help="rule names to exclude (default: all)")

    nf = sub.add_parser("nextflow", help="render a Nextflow DSL2 workflow")
    _add_common_args(nf)
    nf.add_argument("--skip-processes", nargs="*", default=[],
                    metavar="PROCESS",
                    help="process names to exclude")

    args = parser.parse_args(argv)
    try:
        if args.command == "snakemake":
            cmd_snakemake(args)
        elif args.command == "nextflow":
            cmd_nextflow(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
