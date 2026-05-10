# metroplot — Agent Usage Guide

This file is for AI agents. It describes how to generate pipeline diagrams with
metroplot, which layout pattern to choose, and how to configure visuals.

---

## What metroplot does

Renders bioinformatics (or any) pipelines as subway-style diagrams: coloured
lines connect labelled stations on a coordinate grid. Stations are tools/steps;
lines are analysis routes. Shared segments render as parallel offset tracks.

Output: matplotlib figure (PNG, PDF, SVG). Animated SVG via `save_svg(animate=True)`.

---

## Core API

```python
from metroplot import Diagram
from metroplot.themes import PALETTES, LOGO_ORANGE

RED, BLUE, TEAL, NAVY = PALETTES["default"]
CORAL = LOGO_ORANGE

d = Diagram(theme="light", legend_loc="lower right")

# station(key, x, y, label="", sub="", label_pos="above")
d.station("fastq", 0, 0, "FASTQ",   "RAW READS",  "above")
d.station("star",  2, 0, "STAR",    "ALIGNMENT",  "above")
d.station("deseq", 4, 0, "DESeq2",  "DIFF EXPR",  "above")

# line(name, colour, routes, bend="hv", edge_labels=None)
# routes = list of lists of station keys
d.line("RNA-seq", NAVY, [["fastq", "star", "deseq"]])

# Optional: label segments with the data format flowing through them
d.line("RNA-seq", NAVY, [["fastq", "star", "deseq"]], edge_labels={
    ("fastq", "star"):  "FASTQ",
    ("star",  "deseq"): "BAM",
})

# Optional: draw a labelled box behind a cluster of stations
d.section("Alignment", stations=["star"], padding=0.7)

# Render to a matplotlib axis
ax = d.render()

# Save
import matplotlib.pyplot as plt
plt.savefig("pipeline.png", dpi=150, bbox_inches="tight")

# Or save as animated SVG (carts travel along tracks)
d.save_svg("pipeline.svg", animate=True)
```

---

## Diagram parameters

| Parameter | Default | Description |
|---|---|---|
| `line_width` | `4.0` | Track stroke width in points |
| `track_spacing` | `0.09` | Gap between parallel tracks on a shared segment, in data units |
| `station_radius` | `0.21` | Station circle radius in data units |
| `station_linewidth` | `2.5` | Station circle border width in points |
| `corner_radius` | `0.20` | Rounding radius for L-bend corners, in data units |
| `label_font` | `9` | Font size for station main labels, in points |
| `sub_font` | `7` | Font size for station sub-labels, in points |
| `legend_loc` | `None` | Legend position, e.g. `"lower right"` — omit to hide |
| `auto_bend` | `True` | Automatically choose hv/vh bend to avoid overlapping stations |
| `station_interchange_rect` | `True` | Use rounded rectangles at interchange stations |
| `theme` | `"light"` | `"light"`, `"dark"`, `"minimal"`, or a custom `Theme` object |

---

## Layout patterns

Choose one based on pipeline structure. All layouts use hand-placed stations on an integer
grid — metroplot does not auto-arrange.

---

### 1. Linear — single straight pipeline

**When to use:** sequential steps with no branches.

```
A ——— B ——— C ——— D ——— E
```

```python
d = Diagram()
for i, (key, label, sub) in enumerate([
    ("raw",   "FASTQ",         "RAW READS"),
    ("trim",  "Trim Galore",   "TRIMMING"),
    ("star",  "STAR",          "ALIGNMENT"),
    ("quant", "featureCounts", "QUANTIFICATION"),
    ("de",    "DESeq2",        "DIFF EXPR"),
]):
    d.station(key, i * 2, 0, label, sub, "above")
d.line("RNA-seq", CORAL, [[key for key, *_ in [...]]])
```

---

### 2. Parallel lanes — independent pipelines sharing input

**When to use:** multiple assay types (RNA-seq, ATAC-seq, scRNA-seq) with
shared pre-processing. Place each assay on its own y-row; shared stations
appear in every route.

```
              ——— B1 ——— C1 ——— D1
             /
A ——— A2 ———— B2 ——— C2 ——— D2
             \
              ——— B3 ——— C3 ——— D3
```

```python
d = Diagram(legend_loc="lower right")
# Shared trunk at y=0
d.station("fastq", 0, 0, "FASTQ",       "RAW READS", "above")
d.station("fastp", 2, 0, "fastp",       "TRIMMING",  "above")
# Each assay on its own row
d.station("star",  4,  2, "STAR",       "ALIGNMENT", "above")
d.station("cr",    4,  0, "Cellranger", "ALIGNMENT", "above")
d.station("bw",    4, -2, "Bowtie2",   "ALIGNMENT", "below")
# ... downstream stations ...
d.line("Bulk RNA-seq", NAVY,  [["fastq", "fastp", "star",  ...]])
d.line("scRNA-seq",    CORAL, [["fastq", "fastp", "cr",    ...]])
d.line("ATAC-seq",     BLUE,  [["fastq", "fastp", "bw",    ...]])
```

---

### 3. Loop-back — trunk with returning branches

**When to use:** lines travel right on a shared trunk, bend at a common step
(e.g. alignment), and return left on separate rows.

```
A ——— B ——— C ——— D1 ——— E1
                 |
                 D2 ——— E2 ——— F2
```

```python
d = Diagram(legend_loc="lower right")
d.station("raw",   0, 0, "FASTQ",       "RAW READS",  "above")
d.station("trim",  3, 0, "Trim Galore", "TRIMMING",   "above")
d.station("align", 6, 0, "STAR",        "ALIGNMENT",  "above")  # bend point

d.station("rmats", 6, 2, "rMATS",       "ALT SPLICING", "above")
d.station("maser", 3, 2, "MASER",       "SPLICING VIZ", "above")

d.station("quant", 6, 4, "featureCounts","QUANTIFY",  "above")
d.station("de",    3, 4, "DESeq2",      "DIFF EXPR",  "above")
d.station("enrich",0, 4, "clusterProfiler","ENRICHMENT","above")

d.line("Alt Splicing",  TEAL,  [["raw", "trim", "align", "rmats", "maser"]])
d.line("Bulk RNA-seq",  CORAL, [["raw", "trim", "align", "quant", "de", "enrich"]])
```

---

### 4. Wide fan-out — trunk with many outward branches

**When to use:** one shared step fans out to many independent downstream
pipelines. Use `auto_bend=False` and `bend="vh"` so branches first drop to
their target row, then extend horizontally.

```
           ——— B1
          /
A ——— HUB ——— B2
          \
           ——— B3
```

```python
d = Diagram(auto_bend=False)
d.station("input", 0, 0, "FASTQ", "RAW READS", "above")
d.station("hub",   2, 0, "fastp", "TRIMMING",  "left")

branches = [
    ("rna",   "Bulk RNA-seq", "DEG ANALYSIS",  2.5),
    ("scrna", "scRNA-seq",    "CELL ATLAS",    1.5),
    ("atac",  "ATAC-seq",     "CHROMATIN",     0.5),
    ("chip",  "ChIP-seq",     "BINDING SITES",-0.5),
    ("meth",  "RRBS",         "METHYLATION",  -1.5),
    ("hic",   "Hi-C",         "3D GENOME",    -2.5),
]
routes = []
for name, label, sub, y in branches:
    d.station(name, 6, y, label, sub, "right")
    routes.append(["input", "hub", name])

d.line("Multi-omics", CORAL, routes, bend="vh")
```

---

### 5. Serpentine — long pipeline snaking across rows

**When to use:** a long linear pipeline that won't fit on one row. Place
turnaround stations at the same x-coordinate on adjacent rows — metroplot
draws a clean vertical connector automatically.

```
A ——— B ——— C ——— D
               |
E ——— F ——— G ——— D'(same x)
|
H ——— I ——— J ——— K
```

```python
d = Diagram()
# Row 0 — left → right (y=0)
d.station("s00", 0, 0, "FASTQ",        "RAW READS",    "above")
d.station("s01", 3, 0, "Trim Galore",  "TRIMMING",     "above")
d.station("s02", 6, 0, "STAR",         "ALIGNMENT",    "above")
d.station("s03", 9, 0, "UMI-tools",   "DEDUP",        "right")   # right turn-around

# Row 1 — right → left (y=2); s03 and s10 share x=9 → vertical connector
d.station("s10", 9, 2, "featureCounts","QUANTIFY",     "right")
d.station("s11", 6, 2, "DESeq2",       "DIFF EXPR",    "above")
d.station("s12", 3, 2, "fgsea",        "ENRICHMENT",   "above")
d.station("s13", 0, 2, "clusterProfiler","PATHWAYS",   "left")    # left turn-around

# Row 2 — left → right (y=4); s13 and s20 share x=0 → vertical connector
d.station("s20", 0, 4, "MultiQC",      "QC REPORT",    "above")
d.station("s21", 3, 4, "Volcano",      "DE PLOTS",     "above")
d.station("s22", 6, 4, "Heatmap",      "EXPRESSION",   "above")
d.station("s23", 9, 4, "Quarto",       "FINAL REPORT", "above")

d.line("RNA-seq", CORAL, [[
    "s00","s01","s02","s03",
    "s10","s11","s12","s13",
    "s20","s21","s22","s23",
]])
```

---

## Edge labels

Label a segment with the data format flowing through it. The track is
interrupted at the midpoint; the text matches the line colour.

```python
d.line("Bulk RNA-seq", NAVY, [["fastq", "star", "counts", "deseq"]], edge_labels={
    ("fastq",  "star"):   "FASTQ",
    ("star",   "counts"): "BAM",
    ("counts", "deseq"):  "counts",
})
```

Rules:
- Only supported on **straight** (horizontal or vertical) segments. Labels on
  L-bend segments are skipped with a warning.
- If a segment is shared by multiple lines, annotate it on **all** of them or
  on **none**. Mixing looks inconsistent.
- Key tuple order does not matter — `("b", "a")` and `("a", "b")` both work.

---

## Section grouping boxes

Sections draw a labelled rounded rectangle behind a cluster of stations.

```python
d.section("Quality Control", stations=["fastqc", "multiqc"], padding=0.7)
```

- Call `section()` after all stations are defined.
- `padding` controls the gap between station edges and the box border (0.5–1.0 is typical).
- Sections render behind tracks and stations.

---

## Themes

| Name | Best for |
|---|---|
| `"light"` *(default)* | Papers, reports, light-mode web |
| `"dark"` | Dark slides or dark-mode docs — adds coloured station rings and a track glow |
| `"minimal"` | Publications — thinner strokes, no inner dots |

```python
d = Diagram(theme="dark")
```

Custom theme:

```python
from metroplot.themes import Theme, THEMES
THEMES["mylab"] = Theme(
    name="mylab",
    label_color="#2a2a2a",
    sub_color="#666666",
    palette=["#e63946", "#457b9d", "#a8dadc", "#1d3557"],
)
d = Diagram(theme="mylab")
```

---

## Colours

```python
from metroplot.themes import PALETTES, LOGO_ORANGE

RED, BLUE, TEAL, NAVY = PALETTES["default"]
CORAL = LOGO_ORANGE  # metroplot brand orange
```

Any hex code is also valid: `d.line("L", "#e07a6b", [...])`.

---

## Decision guide

| Situation | Pattern |
|---|---|
| Sequential steps, no branches | Linear |
| Multiple assay types sharing input/output | Parallel lanes |
| Lines diverge from a shared step and return | Loop-back |
| One hub fans out to many independent branches | Wide fan-out |
| Long pipeline that won't fit on one row | Serpentine |
| Embedding in a paper | `theme="minimal"`, no animation |
| Embedding in slides / dark-mode | `theme="dark"`, `animate=True` |
| Web / docs | `theme="light"`, `animate=True`, SVG output |
