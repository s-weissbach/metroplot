"""Example: build a metroplot Diagram directly from a Snakemake workflow.

This points at the cell-type annotation benchmarking project's workflow
directory and renders the rule DAG as a subway-style figure.
"""
from pathlib import Path

import matplotlib.pyplot as plt

from snakemake_io import from_snakemake

WORKFLOW = Path.home() / "Desktop" / "benchmarking_project" / "workflow"

d = from_snakemake(
    WORKFLOW,
    line_name="Cell-type annotation benchmark",
    color="#1f2a44",
    column_spacing=2.5,
    branch_spacing=2.5,
)

fig, ax = plt.subplots(figsize=(15, 5))
d.render(ax)
plt.tight_layout()
plt.savefig("graphics/snakemake_example.png", dpi=150, bbox_inches="tight")
print("wrote graphics/snakemake_example.png")
