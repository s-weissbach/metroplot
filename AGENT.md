# metroplot — Agent Usage Guide

This file is for AI agents. It describes how to generate pipeline diagrams with
metroplot, which layout pattern to choose, and how to configure visuals.

---

## What metroplot does

Renders bioinformatics (or any) pipelines as subway-style diagrams: coloured
lines connect labelled stations on a coordinate grid. Stations are tools/steps;
lines are analysis routes. Shared segments render as parallel tracks.

Output: matplotlib figure (PNG, PDF, SVG). Animated SVG via `save_svg(animate=True)`.

---

## Core API

```python
from metroplot import Diagram
from metroplot.themes import PALETTES

RED, BLUE, TEAL, NAVY = PALETTES["default"]

d = Diagram(theme="light", legend_loc="upper right")

# Add stations: name, x, y, label, sub-label, label_position
d.station("fastqc", 0.0, 0.0, "FastQC", "QC", "above")
d.station("star",   2.0, 0.0, "STAR",   "ALIGNMENT", "above")

# Add a line: name, colour, list-of-routes
# Each route is a list of station names in order.
# Multiple routes = branching (they share stations where they meet).
d.line("RNA-seq", NAVY, [["fastqc", "star"]])

# Optional: group stations visually inside a labelled box
d.section("Alignment", stations=["star"], padding=0.7)

# Render
ax = d.render()

# Save
import matplotlib.pyplot as plt
plt.savefig("pipeline.png", dpi=150, bbox_inches="tight")
# or animated SVG:
d.save_svg("pipeline.svg", animate=True)
```

---

## Layout patterns

Choose one based on pipeline structure.  All use `column_spacing=2.0` (default)
unless noted.  Coordinates follow a left-to-right, y=0 spine convention.

---

### 1. `linear` — single straight pipeline

**When to use:** ≤ 8 sequential steps, no branches.

```
A ——— B ——— C ——— D ——— E
```

```python
d = Diagram(theme="light")
tools = ["trim", "align", "quantify", "deseq2", "report"]
for i, name in enumerate(tools):
    d.station(name, i * 2.0, 0.0, name.title(), "STEP", "above")
d.line("Pipeline", NAVY, [tools])
```

---

### 2. `branched` — main spine with side processes

**When to use:** one dominant analysis path plus optional/secondary outputs
(e.g. coverage tracks, QC reports) that branch off at a single point.

```
A ——— B ——— C ——— D
              |
              E ——— F
```

Spine on `y=0`, branch drops to `y=-branch_spacing` (default `-2.0`).

```python
d = Diagram(theme="light")
d.station("trim",   0.0,  0.0, "Trim",    "TRIMMING",       "above")
d.station("star",   2.0,  0.0, "STAR",    "ALIGNMENT",      "above")
d.station("counts", 4.0,  0.0, "Counts",  "QUANTIFICATION", "above")
d.station("deseq",  6.0,  0.0, "DESeq2",  "DIFF EXPR",      "above")
d.station("bam",    4.0, -2.0, "bamCov",  "COVERAGE",       "below")  # branch

d.line("main", NAVY, [
    ["trim", "star", "counts", "deseq"],
    ["star", "bam"],                      # branch: diverges at "star"
])
```

---

### 3. `parallel_lanes` — independent pipelines sharing input/output

**When to use:** multiple assay types (RNA-seq, ATAC-seq, ChIP-seq) with
shared pre-processing and/or a shared downstream integration step.

```
A ——— B ———       ——— G ——— H
      |    \   /
      C ——— D ——— E
            |
            F
```

Use `y = +lane_spacing` / `0` / `-lane_spacing` for each lane.
Shared stations (same name) sit at the centroid of all passing lines.

```python
LANE_SEP = 2.5
d = Diagram(theme="light", legend_loc="lower right")

# Shared upstream
d.station("fastq",  0.0,  0.0, "FASTQ",  "INPUT",     "above")
d.station("fastqc", 2.0,  0.0, "FastQC", "QC",        "above")
d.station("fastp",  4.0,  0.0, "fastp",  "TRIMMING",  "above")

# RNA-seq lane
d.station("star",   6.0,  LANE_SEP, "STAR",      "ALIGNMENT",    "above")
d.station("counts", 8.0,  LANE_SEP, "Counts",    "QUANTIFICATION","above")
d.station("deseq",  10.0, LANE_SEP, "DESeq2",    "DIFF EXPR",    "above")

# ATAC-seq lane
d.station("bow",    6.0, -LANE_SEP, "Bowtie2",   "ALIGNMENT",    "below")
d.station("macs2",  8.0, -LANE_SEP, "MACS2",     "PEAKS",        "below")
d.station("homer",  10.0,-LANE_SEP, "HOMER",     "MOTIFS",       "below")

# Shared downstream
d.station("mofa",   12.0, 0.0, "MOFA+",  "INTEGRATION", "above")
d.station("report", 14.0, 0.0, "Report", "OUTPUT",      "above")

d.line("RNA-seq",  RED,  [["fastq","fastqc","fastp","star","counts","deseq","mofa","report"]])
d.line("ATAC-seq", NAVY, [["fastq","fastqc","fastp","bow","macs2","homer","mofa","report"]])

d.section("Pre-processing", stations=["fastqc","fastp"])
d.section("RNA-seq",  stations=["star","counts","deseq"])
d.section("ATAC-seq", stations=["bow","macs2","homer"])
d.section("Integration", stations=["mofa","report"])
```

---

### 4. `fork_join` — one step forks into alternatives that merge back

**When to use:** alternative parameter choices (two aligners, two trimming
tools) tested in parallel before merging into a shared downstream step.

```
      B ———
     /     \
A ———       ——— D ——— E
     \     /
      C ———
```

Fork point and merge point on `y=0`; upper branch `y=+branch_spacing`,
lower branch `y=-branch_spacing`.

```python
d = Diagram(theme="light")
d.station("input",  0.0,  0.0, "Input",    "RAW READS",  "above")
d.station("star",   3.0,  1.5, "STAR",     "ALIGNMENT",  "above")   # upper branch
d.station("hisat",  3.0, -1.5, "HISAT2",   "ALIGNMENT",  "below")   # lower branch
d.station("counts", 6.0,  0.0, "Counts",   "QUANTIFY",   "above")   # merge
d.station("deseq",  8.0,  0.0, "DESeq2",   "DIFF EXPR",  "above")

d.line("comparison", RED, [
    ["input", "star",  "counts", "deseq"],
    ["input", "hisat", "counts"],
])
```

---

### 5. `wide` — same pipeline but more spread out

**When to use:** many stations, long tool names, or crowded labels.
Increase `column_spacing` (and optionally `line_width` / `station_radius`).

```python
d = Diagram(
    theme="light",
    line_width=5.0,
    station_radius=0.20,
    label_font=10,
    column_spacing=3.0,    # wider than default 2.0
    branch_spacing=3.0,
)
```

Pass `column_spacing` / `branch_spacing` to `from_snakemake` / `from_nextflow`
when auto-parsing:

```python
d = from_snakemake("workflow/", column_spacing=3.0, branch_spacing=3.0)
```

---

## Section grouping boxes

Sections draw a labelled rounded rectangle behind a cluster of stations,
creating visual "stages" within the diagram.

```python
# Auto-bounds from station list (recommended)
d.section("Quality Control",
          stations=["fastqc", "multiqc"],
          sub="PRE-ALIGNMENT",
          padding=0.7)

# Manual bounds (lower-left corner + size)
d.section("Custom box", x=1.0, y=-1.2, width=4.5, height=3.0)
```

Rules:
- Call `section()` **after** all stations are defined (bounds are resolved
  at render time using actual layout positions).
- `padding` controls the gap between station edges and the box border.
  Use `0.5`–`1.0` for most cases.
- Section labels are drawn inside the box near the top edge.
- Sections are rendered behind tracks and stations (z-order 1).

---

## Themes

| Name | Best for | Labels | Stations | Glow |
|---|---|---|---|---|
| `"light"` | light docs, papers | dark navy | white + coloured dot | no |
| `"dark"` | dark slides, dark-mode | off-white | coloured ring | yes |
| `"minimal"` | publications, b/w | dark grey | white, no dot | no |

```python
d = Diagram(theme="dark")
```

Custom theme — only override what you need:

```python
from metroplot.themes import Theme, THEMES
THEMES["mylab"] = Theme(
    name="mylab",
    label_color="#1a1a2e",
    sub_color="#555555",
    section_fill="#eef2f7",
    section_edge="#b0c4d8",
    section_label_color="#6a8fa8",
    palette=["#e63946", "#457b9d", "#a8dadc", "#1d3557"],
)
```

---

## Colours

Default palette (`PALETTES["default"]`):

| Variable | Hex | Notes |
|---|---|---|
| RED | `#e63946` | attention, key outputs |
| BLUE | `#457b9d` | primary analysis track |
| TEAL | `#a8dadc` | secondary track |
| NAVY | `#1d3557` | integration, downstream |

```python
from metroplot.themes import PALETTES
RED, BLUE, TEAL, NAVY = PALETTES["default"]
```

---

## Auto-parsing from workflow files

For Snakemake or Nextflow pipelines, skip manual station placement entirely:

```python
from metroplot.snakemake_io import from_snakemake
from metroplot.nextflow_io import from_nextflow

d = from_snakemake("path/to/workflow/", theme="light", column_spacing=2.5)
d = from_nextflow("path/to/pipeline/",  theme="dark",  branch_spacing=2.0)
```

Supports: `label_overrides`, `sub_overrides`, `lanes` (multi-line), `skip_rules`.

---

## Animated SVG output

```python
# Save static PNG
plt.savefig("pipeline.png", dpi=150, bbox_inches="tight")

# Save animated SVG (flowing dashes show data movement)
d.save_svg("pipeline.svg", animate=True)
```

From the CLI:
```sh
metroplot snakemake workflow/ --theme light --animate -o pipeline.svg
metroplot nextflow  pipeline/ --theme dark  --animate -o pipeline.svg
```

---

## Decision guide

| Situation | Choice |
|---|---|
| Simple linear pipeline | `linear` layout, `"light"` theme |
| Pipeline with one branch | `branched` layout |
| Multi-assay (RNA + ATAC etc.) | `parallel_lanes` layout, sections per assay |
| Comparing two tools/params | `fork_join` layout |
| Long labels / many steps | `wide` layout (`column_spacing=3.0`) |
| Embedding in a paper | `"minimal"` theme, no animation |
| Embedding in slides | `"dark"` theme, `animate=True` |
| Web/docs | `"light"` theme, `animate=True`, SVG output |
| Auto-parse workflow file | `from_snakemake()` / `from_nextflow()` |
