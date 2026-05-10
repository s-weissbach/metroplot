<p align="center"><img src="graphics/metroplot_logo.png" alt="metroplot" width="400"/></p>

[![tests](https://github.com/s-weissbach/metroplot/actions/workflows/test.yml/badge.svg)](https://github.com/s-weissbach/metroplot/actions/workflows/test.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![code style: matplotlib](https://img.shields.io/badge/built%20on-matplotlib-11557c.svg)](https://matplotlib.org/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/metroplot.svg)](https://pypi.org/project/metroplot/)

Subway-style pipeline diagrams for matplotlib. Define stations on a grid and lines that connect them; the renderer handles right-angle routing, parallel-track offsets where lines share segments, and station labels.

<p align="center">
  <img src="graphics/example_edge_labels_animated.svg" alt="metroplot example with edge labels" width="100%"/>
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

## Edge labels

Label individual segments with the data format flowing through them. The track is interrupted at the midpoint, the text matches the line colour, and its height equals the line width.

```python
d.line("Bulk RNA-seq", NAVY, [["fastq", "fastp", "star", "fcounts", "deseq2"]], edge_labels={
    ("fastq",   "fastp"):   "fastq",
    ("star",    "fcounts"): "BAM",
    ("fcounts", "deseq2"):  "counts",
})
```

Annotate a segment on **every line that carries it, or on none** — keep labels consistent across parallel tracks.

## Layout patterns

### Linear

The simplest layout — a single line of stations left to right.

<p align="center">
  <img src="graphics/layout_linear.png" alt="linear layout" width="100%"/>
</p>

```python
d = Diagram()
d.station("raw",   0, 0, "FASTQ",         "RAW READS")
d.station("qc",    2, 0, "FastQC",        "QUALITY CTRL")
d.station("trim",  4, 0, "Trim Galore",   "TRIMMING")
d.station("align", 6, 0, "STAR",          "ALIGNMENT")
d.station("quant", 8, 0, "featureCounts", "QUANTIFICATION")
d.station("de",   10, 0, "DESeq2",        "DIFF EXPR")
d.line("RNA-seq", "#e8614a", [["raw", "qc", "trim", "align", "quant", "de"]])
```

---

### Parallel lanes

A shared trunk forks into independent assay-specific lanes at different y-coordinates.

<p align="center">
  <img src="graphics/layout_parallel.png" alt="parallel lanes layout" width="100%"/>
</p>

```python
# Shared input stations at y=0
d.station("fastq", 0, 0, ...)
d.station("trim",  2, 0, ...)

# Assay-specific stations — one y-level per assay
d.station("star", 4,  2, ...)   # Bulk RNA-seq lane (top)
d.station("cr",   4,  0, ...)   # scRNA-seq lane (middle)
d.station("bw",   4, -2, ...)   # ATAC-seq lane (bottom)

# One line per assay; shared stations appear on all lines
d.line("Bulk RNA-seq", NAVY,  [["fastq", "trim", "star", ...]])
d.line("scRNA-seq",    CORAL, [["fastq", "trim", "cr",   ...]])
d.line("ATAC-seq",     BLUE,  [["fastq", "trim", "bw",   ...]])
```

---

### Loop-back

Lines travel right along the bottom row, bend at a shared alignment step, then return left on separate upper rows — one row per downstream branch.

<p align="center">
  <img src="graphics/layout_return.png" alt="loop-back layout" width="100%"/>
</p>

```python
# Forward trunk at y=0
d.station("raw",   0, 0, "FASTQ",       "RAW READS")
d.station("trim",  3, 0, "Trim Galore", "TRIMMING")
d.station("star",  6, 0, "STAR",        "ALIGNMENT")   # bend point

# Return rows — each branch at its own y, going right → left
d.station("rmats", 6, 2, "rMATS",  "ALT SPLICING")    # y=2 branch
d.station("maser", 3, 2, "MASER",  "SPLICING VIZ")

d.station("quant", 6, 4, "featureCounts", "QUANTIFY")  # y=4 branch
d.station("de",    3, 4, "DESeq2",        "DIFF EXPR")
d.station("enrich",0, 4, "clusterProfiler","ENRICHMENT")

d.line("Alt Splicing", TEAL,  [["raw", "trim", "star", "rmats", "maser"]])
d.line("Bulk RNA-seq", CORAL, [["raw", "trim", "star", "quant", "de", "enrich"]])
```

---

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
