<p align="center"><img src="graphics/metroplot_logo.png" alt="metroplot" width="400"/></p>

[![tests](https://github.com/s-weissbach/metroplot/actions/workflows/test.yml/badge.svg)](https://github.com/s-weissbach/metroplot/actions/workflows/test.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![code style: matplotlib](https://img.shields.io/badge/built%20on-matplotlib-11557c.svg)](https://matplotlib.org/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/metroplot.svg)](https://pypi.org/project/metroplot/)

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
            line_width=5.5, station_radius=0.45, label_font=9, sub_font=7)

# Pre-processing (shared trunk, going right)
d.station("fastq",       0,  0,  "FASTQ",           "RAW READS",      "above")
d.station("fastqc_raw",  3,  0,  "FastQC",          "RAW QC",         "above")
d.station("trim",        6,  0,  "Trim Galore",     "TRIMMING",       "above")
d.station("fastqc_trim", 9,  0,  "FastQC",          "TRIM QC",        "above")

# Alignment fork — the corner of the U
d.station("star",       12,  1.5, "STAR",            "ALIGNMENT",      "right")
d.station("hisat2",     12, -1.5, "HISAT2",          "ALIGNMENT",      "right")

# Alt Splicing (returning left at y=6)
d.station("rmats",       9,  6,  "rMATS",            "ALT SPLICING",   "above")
d.station("maser",       6,  6,  "MASER",            "SPLICING VIZ",   "above")

# Variant Calling (returning left at y=4)
d.station("gatk_split",  9,  4,  "GATK SplitN",     "CIGAR SPLIT",    "above")
d.station("haplotype",   6,  4,  "HaplotypeCaller",  "VARIANT CALL",   "above")
d.station("snpeff",      3,  4,  "SnpEff",           "ANNOTATION",     "above")

# Quantification & DE (returning left at y=2)
d.station("umitools",    9,  2,  "UMI-tools",        "DEDUPLICATION",  "above")
d.station("fcounts",     6,  2,  "featureCounts",    "QUANTIFY",       "above")
d.station("deseq2",      3,  2,  "DESeq2",           "DIFF EXPR",      "above")
d.station("clustprof",   0,  2,  "clusterProfiler",  "PATHWAY ENRICH", "above")

# Coverage Tracks (returning left at y=-2)
d.station("samtools",    9, -2,  "SAMtools",         "BAM SORT/INDEX", "below")
d.station("bigtwig",     6, -2,  "bigWig",           "COVERAGE",       "below")
d.station("deeptools",   3, -2,  "deepTools",        "PEAK ANALYSIS",  "below")

# Lines — every track runs the full journey from FASTQ
d.line("Bulk RNA-seq", ORANGE, [
    ["fastq", "fastqc_raw", "trim", "fastqc_trim", "star",
     "umitools", "fcounts", "deseq2", "clustprof"],
])
d.line("Alt Splicing", TEAL, [
    ["fastq", "fastqc_raw", "trim", "fastqc_trim", "star", "rmats", "maser"],
])
d.line("RNA Variants", NAVY, [
    ["fastq", "fastqc_raw", "trim", "fastqc_trim", "star",
     "gatk_split", "haplotype", "snpeff"],
])
d.line("QC Tracks", BLUE, [
    ["fastq", "fastqc_raw", "trim", "fastqc_trim", "hisat2",
     "samtools", "bigtwig", "deeptools"],
])

# Section grouping boxes
d.section("Pre-processing",  stations=["fastq", "fastqc_raw", "trim", "fastqc_trim"], padding=0.9)
d.section("Alignment",       stations=["star", "hisat2"],    padding=0.9, label_pos="right")
d.section("Alt Splicing",    stations=["rmats", "maser"],    padding=0.75)
d.section("Variant Calling", stations=["gatk_split", "haplotype", "snpeff"], padding=0.75)
d.section("Quant & DE",      stations=["umitools", "fcounts", "deseq2", "clustprof"], padding=0.8)
d.section("Coverage Tracks", stations=["samtools", "bigtwig", "deeptools"], padding=0.75,
          label_pos="bottom-middle")

fig, ax = plt.subplots(figsize=(16, 10))
d.save_svg("pipeline.svg", ax=ax, animate=True)
plt.close(fig)
```

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

Pass `animate=True` to `save_svg` to inject animated metro carts travelling along each line:

```python
d.save_svg("pipeline.svg", animate=True)
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
