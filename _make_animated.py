"""Generate graphics/example_animated.svg for the README.

U-turn layout: pre-processing goes right along y=0, the alignment hub is at
x=12, and each analysis track returns left at its own y-level.  Every line
runs the full journey from FASTQ to its terminus so the data flow is clear.
"""
import sys, dataclasses
sys.path.insert(0, "src")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metroplot import Diagram
from metroplot.themes import LIGHT, PALETTES, LOGO_ORANGE

_, BLUE, TEAL, NAVY = PALETTES["default"]
ORANGE = LOGO_ORANGE

# nf-metro style: white ring, colored edge for single-line, no inner dot
theme = dataclasses.replace(
    LIGHT,
    background="#f5f6f8",
    station_dot=False,
    station_colored_edge=True,
    station_edge="#555555",
    station_edge_width=2.0,
)

d = Diagram(theme=theme, legend_loc="lower right",
            line_width=3.5, track_spacing=0.09, station_radius=0.21,
            station_interchange_rect=True,
            label_font=9, sub_font=7)

# ── Pre-processing (shared trunk, going RIGHT) ────────────────────────────────
d.station("fastq",       0,  0,  "FASTQ",           "RAW READS",      "above")
d.station("fastqc_raw",  3,  0,  "FastQC",          "RAW QC",         "above")
d.station("trim",        6,  0,  "Trim Galore",     "TRIMMING",       "above")
d.station("fastqc_trim", 9,  0,  "FastQC",          "TRIM QC",        "above")

# ── Alignment fork (the "corner" of the U) ────────────────────────────────────
d.station("star",       12,  1.5, "STAR",            "ALIGNMENT",      "right")
d.station("hisat2",     12, -1.5, "HISAT2",          "ALIGNMENT",      "right")

# ── Alt Splicing (y=6, returning LEFT from STAR) ─────────────────────────────
d.station("rmats",       9,  6,  "rMATS",            "ALT SPLICING",   "above")
d.station("maser",       6,  6,  "MASER",            "SPLICING VIZ",   "above")

# ── Variant Calling (y=4, returning LEFT from STAR) ──────────────────────────
d.station("gatk_split",  9,  4,  "GATK SplitN",     "CIGAR SPLIT",    "above")
d.station("haplotype",   6,  4,  "HaplotypeCaller",  "VARIANT CALL",   "above")
d.station("snpeff",      3,  4,  "SnpEff",           "ANNOTATION",     "above")

# ── Quantification & DE (y=2, returning LEFT from STAR) ──────────────────────
d.station("umitools",    9,  2,  "UMI-tools",        "DEDUPLICATION",  "above")
d.station("fcounts",     6,  2,  "featureCounts",    "QUANTIFY",       "above")
d.station("deseq2",      3,  2,  "DESeq2",           "DIFF EXPR",      "above")
d.station("clustprof",   0,  2,  "clusterProfiler",  "PATHWAY ENRICH", "above")

# ── Coverage Tracks (y=-2, returning LEFT from HISAT2) ───────────────────────
d.station("samtools",    9, -2,  "SAMtools",         "BAM SORT/INDEX", "below")
d.station("bigtwig",     6, -2,  "bigWig",           "COVERAGE",       "below")
d.station("deeptools",   3, -2,  "deepTools",        "PEAK ANALYSIS",  "below")

# ── Lines — each track runs the full journey from FASTQ ──────────────────────
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

# ── Section grouping boxes ────────────────────────────────────────────────────
d.section("Pre-processing",  stations=["fastq", "fastqc_raw", "trim", "fastqc_trim"], padding=0.9)
d.section("Alignment",       stations=["star", "hisat2"],                              padding=0.9,
          label_pos="right")
d.section("Alt Splicing",    stations=["rmats", "maser"],                              padding=0.75)
d.section("Variant Calling", stations=["gatk_split", "haplotype", "snpeff"],          padding=0.75)
d.section("Quant & DE",      stations=["umitools", "fcounts", "deseq2", "clustprof"], padding=0.8)
d.section("Coverage Tracks", stations=["samtools", "bigtwig", "deeptools"],            padding=0.75,
          label_pos="bottom-middle")

fig, ax = plt.subplots(figsize=(16, 10))
d.save_svg("graphics/example_animated.svg", ax=ax, animate=True)
plt.close(fig)
print("wrote graphics/example_animated.svg")
