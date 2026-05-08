"""Generate graphics/example_animated.svg for the README.

Pipeline: nf-core RNA-seq inspired
  Pre-processing  → Genome alignment (STAR / HISAT2) → Post-processing → QC
  Alt splicing branch (rMATS → GSEApy) off STAR
"""
import sys
sys.path.insert(0, "src")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metroplot import Diagram
from metroplot.themes import PALETTES

RED, BLUE, TEAL, NAVY = PALETTES["default"]

d = Diagram(theme="light", legend_loc="lower right",
            line_width=5.5, station_radius=0.20, label_font=10, sub_font=7)

# ── Pre-processing ────────────────────────────────────────────────────────────
d.station("fastqc_raw",  0,    0,     "FastQC",        "RAW QC",        "above")
d.station("trim",        3.5,  0,     "Trim Galore",   "TRIMMING",      "above")
d.station("fastqc_trim", 7,    0,     "FastQC",        "TRIM QC",       "above")

# ── Genome alignment ──────────────────────────────────────────────────────────
d.station("star",        10.5, 1.5,   "STAR",          "ALIGNMENT",     "above")
d.station("hisat2",      10.5, -1.5,  "HISAT2",        "ALIGNMENT",     "below")
d.station("umitools",    14,   0,     "UMI-tools",     "DEDUP",         "above")
d.station("fcounts",     17.5, 0,     "featureCounts", "QUANTIFY",      "above")

# ── Alt splicing (branch from STAR) ───────────────────────────────────────────
d.station("rmats",       14,   3.5,   "rMATS",         "ALT SPLICING",  "above")
d.station("gseapy",      17.5, 3.5,   "GSEApy",        "ENRICHMENT",    "above")

# ── Post-processing ───────────────────────────────────────────────────────────
d.station("samtools",    21,   0,     "SAMtools",      "BAM PROCESS",   "above")
d.station("bigtwig",     24.5, 0,     "bigWig",        "TRACKS",        "above")

# ── QC & Reporting (fan-out) ──────────────────────────────────────────────────
d.station("rseqc",       28,   1.5,   "RSeQC",         "RNA QC",        "above")
d.station("bedtools",    28,   -1.5,  "BEDTools",      "COVERAGE",      "below")
d.station("multiqc",     31.5, 0,     "MultiQC",       "REPORT",        "above")

# ── Lines ─────────────────────────────────────────────────────────────────────
d.line("STAR + featureCounts", NAVY, [
    ["fastqc_raw", "trim", "fastqc_trim", "star",
     "umitools", "fcounts", "samtools", "bigtwig", "rseqc", "multiqc"],
    ["bigtwig", "bedtools"],
    ["star", "rmats", "gseapy"],
])
d.line("HISAT2", TEAL, [
    ["fastqc_raw", "trim", "fastqc_trim", "hisat2", "umitools"],
])

# ── Sections ──────────────────────────────────────────────────────────────────
d.section("Pre-processing",
          stations=["fastqc_raw", "trim", "fastqc_trim"], padding=0.85)
d.section("Genome alignment",
          stations=["star", "hisat2", "umitools", "fcounts"], padding=0.85)
d.section("Alt splicing",
          stations=["rmats", "gseapy"], padding=0.75)
d.section("Post-processing",
          stations=["samtools", "bigtwig"], padding=0.75)
d.section("QC & Reporting",
          stations=["rseqc", "bedtools", "multiqc"], padding=0.85)

fig, ax = plt.subplots(figsize=(22, 7))
d.save_svg("graphics/example_animated.svg", ax=ax, animate=True)
plt.close(fig)
print("wrote graphics/example_animated.svg")
