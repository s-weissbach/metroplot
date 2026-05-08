<p align="center"><img src="graphics/metroplot_logo.png" alt="metroplot" width="400"/></p>

[![tests](https://github.com/s-weissbach/metroplot/actions/workflows/test.yml/badge.svg)](https://github.com/s-weissbach/metroplot/actions/workflows/test.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![code style: matplotlib](https://img.shields.io/badge/built%20on-matplotlib-11557c.svg)](https://matplotlib.org/)

Subway-style pipeline diagrams for matplotlib. Define stations on a grid and lines that connect them; the renderer handles right-angle routing, parallel-track offsets where lines share segments, and station labels.

<p align="center">
  <img src="graphics/example_animated.svg" alt="animated metroplot example" width="100%"/>
</p>


## Install

```sh
pip install metroplot
```

Or from source:

```sh
git clone https://github.com/s-weissbach/metroplot.git
cd metroplot
pip install -e .
```

Only hard dependency is `matplotlib`.

## Usage

```python
import dataclasses, matplotlib.pyplot as plt
from metroplot import Diagram
from metroplot.themes import LIGHT, PALETTES, LOGO_ORANGE

_, BLUE, TEAL, NAVY = PALETTES["default"]
ORANGE = LOGO_ORANGE

theme = dataclasses.replace(LIGHT, background="#f5f6f8")

d = Diagram(theme=theme, legend_loc="lower right",
            line_width=5.5, station_radius=0.21, label_font=9, sub_font=7)

# Pre-processing (shared trunk)
d.station("fastq",        0,   0,   "FASTQ",           "RAW READS",       "above")
d.station("fastqc_raw",   3,   0,   "FastQC",          "RAW QC",          "above")
d.station("trim",         6,   0,   "Trim Galore",     "TRIMMING",        "above")
d.station("fastqc_trim",  9,   0,   "FastQC",          "TRIM QC",         "above")

# Alignment fork
d.station("star",        12,   2,   "STAR",            "ALIGNMENT",       "above")
d.station("hisat2",      12,  -2,   "HISAT2",          "ALIGNMENT",       "below")
d.station("umitools",    15,   0,   "UMI-tools",       "DEDUPLICATION",   "above")

# Alt Splicing (TEAL, off STAR)
d.station("rmats",       15,   5,   "rMATS",           "ALT SPLICING",    "above")
d.station("maser",       18,   5,   "MASER",           "SPLICING VIZ",    "above")

# Variant Calling (NAVY, off STAR)
d.station("gatk_split",  15,   3,   "GATK SplitN",     "CIGAR SPLIT",     "above")
d.station("haplotype",   18,   3,   "HaplotypeCaller", "VARIANT CALL",    "above")
d.station("snpeff",      21,   3,   "SnpEff",          "ANNOTATION",      "above")

# Quantification & DE (ORANGE)
d.station("fcounts",     18,   0,   "featureCounts",   "QUANTIFY",        "above")
d.station("deseq2",      21,   0,   "DESeq2",          "DIFF EXPR",       "above")
d.station("gsea",        24,  -2,   "fgsea",           "GENE SET ENRICH", "below")
d.station("clustprof",   24,   0,   "clusterProfiler", "PATHWAY ENRICH",  "above")

# Coverage Tracks (BLUE, off HISAT2)
d.station("samtools",    18,  -4,   "SAMtools",        "BAM SORT/INDEX",  "below")
d.station("bigtwig",     21,  -4,   "bigWig",          "COVERAGE TRACKS", "below")
d.station("deeptools",   24,  -4,   "deepTools",       "PEAK ANALYSIS",   "below")

# Report (all lines converge)
d.station("multiqc",     27,   0,   "MultiQC",         "QC REPORT",       "above")

# Lines
d.line("Bulk RNA-seq", ORANGE, [
    ["fastq", "fastqc_raw", "trim", "fastqc_trim", "star",
     "umitools", "fcounts", "deseq2", "clustprof", "multiqc"],
    ["deseq2", "gsea"],   # GSEA sub-branch
])
d.line("Alt Splicing", TEAL, [
    ["star", "rmats", "maser"],
])
d.line("RNA Variants", NAVY, [
    ["star", "gatk_split", "haplotype", "snpeff", "multiqc"],
])
d.line("QC Tracks", BLUE, [
    ["fastq", "fastqc_raw", "trim", "fastqc_trim", "hisat2",
     "umitools", "samtools", "bigtwig", "deeptools", "multiqc"],
])

# Section grouping boxes
d.section("Pre-processing",  stations=["fastq", "fastqc_raw", "trim", "fastqc_trim"], padding=0.9)
d.section("Alignment",       stations=["star", "hisat2", "umitools"],                 padding=0.9)
d.section("Alt Splicing",    stations=["rmats", "maser"],                             padding=0.75)
d.section("Variant Calling", stations=["gatk_split", "haplotype", "snpeff"],         padding=0.75)
d.section("Quant & DE",      stations=["fcounts", "deseq2", "gsea", "clustprof"],    padding=0.8)
d.section("Coverage Tracks", stations=["samtools", "bigtwig", "deeptools"],          padding=0.75,
          label_pos="bottom-middle")
d.section("Report",          stations=["multiqc"],                                    padding=0.7)

fig, ax = plt.subplots(figsize=(24, 10))
d.save_svg("pipeline.svg", ax=ax, animate=True)
plt.close(fig)
```

## CLI

After `pip install metroplot` the `metroplot` command is available:

```sh
# From a Snakemake workflow directory
metroplot snakemake path/to/workflow -o pipeline.png

# From a Nextflow DSL2 directory
metroplot nextflow path/to/workflow -o pipeline.png

# Common options
metroplot snakemake path/to/workflow \
  --line-name "My pipeline" \
  --color "#1f2a44" \
  --label-overrides '{"star_align":"STAR"}' \
  --sub-overrides '{"star_align":"ALIGNMENT"}' \
  --column-spacing 2.5 \
  --branch-spacing 2.5 \
  --no-legend \
  --dpi 300 \
  --figsize 18 6
```

## Pipeline workflows

metroplot ships with parsers that turn a workflow definition into a Diagram automatically. Two formats are supported:

- **Snakemake** — `from metroplot.snakemake_io import from_snakemake` parses every `Snakefile` / `*.smk` under a directory, matches each rule's `output:` paths to downstream `input:` paths to derive the DAG.
- **Nextflow (DSL2)** — `from metroplot.nextflow_io import from_nextflow` parses every `*.nf` file, finds `process NAME { … }` blocks, and extracts edges by reading `workflow { … }` blocks for invocations like `STAR(TRIM.out)`.

Both share the same downstream layout/Diagram-builder (`metroplot._pipeline_layout`): the longest source-to-sink path becomes the `y = 0` spine, off-spine rules drop below at `branch_spacing`, and every parameter (label overrides, sub-labels, lanes, colors, column spacing) is exposed as a kwarg.

```python
from metroplot.snakemake_io import from_snakemake   # or: from metroplot.nextflow_io import from_nextflow

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

- Snakemake on a real cell-type annotation benchmarking workflow → [examples/example_snakemake.py](examples/example_snakemake.py) → [graphics/snakemake_example.png](graphics/snakemake_example.png)
- Nextflow on an nf-core-style RNA-seq pipeline → [examples/example_nextflow.py](examples/example_nextflow.py) → [graphics/nextflow_example.png](graphics/nextflow_example.png)

Both parsers are best-effort regex-based and do not understand dynamic rules / checkpoint outputs (Snakemake) or subworkflow imports / channel operators like `map`, `branch`, `combine` (Nextflow). For anything they miss, override at the kwarg layer or pass extra rules/edges into `metroplot._pipeline_layout.build_diagram_from_dag` directly.

## Concepts

- **Station** — a node at `(x, y)` on a grid. You control layout fully; there's no auto-layout.
- **Line** — a colored route, owning one or more `routes` (lists of station names). Splits are implicit: two routes that share a station diverge there.
- **Shared segments** — when multiple lines traverse the same `(a, b)` segment, they're auto-offset perpendicular to the segment so they render as parallel tracks.
- **Bends** — non-collinear hops use an L-shape. Per-line `bend="hv"` (horizontal then vertical, default) or `"vh"`.

## Themes

Three built-in themes — all use a **transparent background** so diagrams embed cleanly into any document or slide:

| Name | Use case |
|---|---|
| `"light"` (default) | Light documents, papers, light-mode web |
| `"dark"` | Dark slides, dark-mode docs — coloured station rings + track glow |
| `"minimal"` | Publications — thinner lines, no inner dots |

```python
d = Diagram(theme="dark")
```

A default colour palette is available for multi-line diagrams:

```python
from metroplot.themes import PALETTES

RED, BLUE, TEAL, NAVY = PALETTES["default"]  # #e63946, #457b9d, #a8dadc, #1d3557

d.line("RNA-seq",  RED,  routes1)
d.line("ChIP-seq", NAVY, routes2)
```

Add your own theme:

```python
from metroplot.themes import Theme, THEMES

THEMES["myteam"] = Theme(
    name="myteam",
    label_color="#2a2a2a",
    sub_color="#666666",
    palette=["#e63946", "#457b9d", "#a8dadc", "#1d3557"],
)
```

### Animated SVG

Pass `animate=True` to `save_svg` to inject flowing-dash animation (data moving through the pipeline):

```python
d.save_svg("pipeline.svg", animate=True)
```

Or from the CLI:

```sh
metroplot nextflow path/to/workflow --theme dark --animate -o pipeline.svg
```

## Tuning

`Diagram(track_spacing=..., station_radius=..., line_width=..., label_font=..., sub_font=...)` exposes the visual knobs.

## Testing

```sh
pip install -e ".[dev]"
pytest
```

CI runs the suite on Python 3.10, 3.11, and 3.12 (see [`.github/workflows/test.yml`](.github/workflows/test.yml)).

## License

[MIT](LICENSE).
