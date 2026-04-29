<p align="center"><img src="graphics/metroplot_logo.png" alt="metroplot" width="400"/></p>

[![tests](https://github.com/s-weissbach/metroplot/actions/workflows/test.yml/badge.svg)](https://github.com/s-weissbach/metroplot/actions/workflows/test.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![code style: matplotlib](https://img.shields.io/badge/built%20on-matplotlib-11557c.svg)](https://matplotlib.org/)

Subway-style pipeline diagrams for matplotlib. Define stations on a grid and lines that connect them; the renderer handles right-angle routing, parallel-track offsets where lines share segments, and station labels.

![example](graphics/example.png)


## Install

No package on PyPI yet — drop `metroplot.py` next to your script. Only dependency is `matplotlib`.

## Usage

```python
import matplotlib.pyplot as plt
from metroplot import Diagram

NAVY, SALMON = "#1f2a44", "#e07a6b"

d = Diagram()
(d.station("sra",    0.0,  0.0, "SRA tool", "DATA DOWNLOAD", "below")
  .station("fastqc", 2.0,  0.0, "fastqc",   "QUALITY CONTROL")
  .station("star",   6.0,  0.0, "STAR",     "ALIGNMENT")
  .station("rmats",  9.0,  0.0, "rMATS",    "ALT SPLICING")
  .station("bam",    8.0, -1.5, "bamCoverage", "COVERAGE", "below")
  .station("fc",     6.0, -2.5, "featureCounts", "QUANTIFICATION", "below"))

# A line is a list of routes. Multiple routes that share a station encode a split.
d.line("splicing", SALMON, [
    ["sra", "fastqc", "star", "rmats"],
    ["rmats", "bam"],          # branch off rmats
])
d.line("quant", NAVY, [
    ["sra", "fastqc", "star", "fc"],
])

d.render()
plt.savefig("pipeline.png", dpi=150, bbox_inches="tight")
```

Run [example.py](example.py) to regenerate the figure at the top.

## Pipeline workflows

metroplot ships with parsers that turn a workflow definition into a Diagram automatically. Two formats are supported:

- **Snakemake** — `from snakemake_io import from_snakemake` parses every `Snakefile` / `*.smk` under a directory, matches each rule's `output:` paths to downstream `input:` paths to derive the DAG.
- **Nextflow (DSL2)** — `from nextflow_io import from_nextflow` parses every `*.nf` file, finds `process NAME { … }` blocks, and extracts edges by reading `workflow { … }` blocks for invocations like `STAR(TRIM.out)`.

Both share the same downstream layout/Diagram-builder ([_pipeline_layout.py](_pipeline_layout.py)): the longest source-to-sink path becomes the `y = 0` spine, off-spine rules drop below at `branch_spacing`, and every parameter (label overrides, sub-labels, lanes, colors, column spacing) is exposed as a kwarg.

```python
from snakemake_io import from_snakemake          # or: from nextflow_io import from_nextflow

d = from_snakemake(
    "path/to/workflow",
    line_name="My pipeline",
    label_overrides={"run_method": "scanpy/Seurat"},     # snake_case rule name → display label
    sub_overrides={"run_method": "ANNOTATION"},          # small uppercase line under each label
    lanes={                                              # optional: split into multiple parallel lines
        "QC":   {"color": "#aaaaaa", "rules": ["FASTQC", "MULTIQC"]},
        "Main": {"color": "#1f2a44", "rules": ["FASTP", "STAR", "FEATURECOUNTS", "DESEQ2"]},
    },
)
d.render()
```

End-to-end demos:

- Snakemake on a real cell-type annotation benchmarking workflow → [example_snakemake.py](example_snakemake.py) → [graphics/snakemake_example.png](graphics/snakemake_example.png)
- Nextflow on an nf-core-style RNA-seq pipeline → [example_nextflow.py](example_nextflow.py) → [graphics/nextflow_example.png](graphics/nextflow_example.png)

Both parsers are best-effort regex-based and do not understand dynamic rules / checkpoint outputs (Snakemake) or subworkflow imports / channel operators like `map`, `branch`, `combine` (Nextflow). For anything they miss, override at the kwarg layer or pass extra rules/edges into [`_pipeline_layout.build_diagram_from_dag`](_pipeline_layout.py) directly.

## Concepts

- **Station** — a node at `(x, y)` on a grid. You control layout fully; there's no auto-layout.
- **Line** — a colored route, owning one or more `routes` (lists of station names). Splits are implicit: two routes that share a station diverge there.
- **Shared segments** — when multiple lines traverse the same `(a, b)` segment, they're auto-offset perpendicular to the segment so they render as parallel tracks.
- **Bends** — non-collinear hops use an L-shape. Per-line `bend="hv"` (horizontal then vertical, default) or `"vh"`.

## Tuning

`Diagram(track_spacing=..., station_radius=..., line_width=..., label_font=..., sub_font=...)` exposes the visual knobs.

## Testing

```sh
pip install matplotlib pytest
pytest
```

CI runs the suite on Python 3.10, 3.11, and 3.12 (see [`.github/workflows/test.yml`](.github/workflows/test.yml)).

## License

[MIT](LICENSE).
