"""Generate graphics/example_animated.svg for the README."""
import sys, dataclasses
sys.path.insert(0, "src")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metroplot import Diagram
from metroplot.themes import LIGHT, PALETTES, LOGO_ORANGE

_, BLUE, TEAL, NAVY = PALETTES["default"]
ORANGE = LOGO_ORANGE   # #e8614a — matches the logo

# Custom theme: same as light but with a warm off-white background
theme = dataclasses.replace(LIGHT, background="#f5f6f8")

d = Diagram(theme=theme, legend_loc="lower right",
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

# ── Alt splicing branch from STAR (separate line, different colour) ───────────
d.station("rmats",       14,   3.5,   "rMATS",         "ALT SPLICING",  "above")
d.station("gseapy",      17.5, 3.5,   "GSEApy",        "ENRICHMENT",    "above")

# ── Post-processing ───────────────────────────────────────────────────────────
d.station("samtools",    21,   0,     "SAMtools",      "BAM PROCESS",   "above")
d.station("bigtwig",     24.5, 0,     "bigWig",        "TRACKS",        "above")

# ── QC & Reporting ────────────────────────────────────────────────────────────
d.station("rseqc",       28,   1.5,   "RSeQC",         "RNA QC",        "above")
d.station("bedtools",    28,   -1.5,  "BEDTools",      "COVERAGE",      "below")
d.station("multiqc",     31.5, 0,     "MultiQC",       "REPORT",        "above")

# ── Lines ─────────────────────────────────────────────────────────────────────
# Main STAR pipeline — bedtools is on the main track, no branch
d.line("STAR + featureCounts", ORANGE, [
    ["fastqc_raw", "trim", "fastqc_trim", "star",
     "umitools", "fcounts", "samtools", "bigtwig", "bedtools", "multiqc"],
])

# Alt splicing is a separate line with its own colour, branching from STAR
d.line("Alt splicing", TEAL, [
    ["star", "rmats", "gseapy"],
])

# HISAT2 shares the trunk and post-processing, ending at RSeQC then MultiQC
d.line("HISAT2", NAVY, [
    ["fastqc_raw", "trim", "fastqc_trim", "hisat2",
     "umitools", "fcounts", "samtools", "bigtwig", "rseqc", "multiqc"],
])

# ── Sections ──────────────────────────────────────────────────────────────────
d.section("Pre-processing",   stations=["fastqc_raw", "trim", "fastqc_trim"], padding=0.85)
d.section("Genome alignment", stations=["star", "hisat2", "umitools", "fcounts"], padding=0.85)
d.section("Alt splicing",     stations=["rmats", "gseapy"],                     padding=0.75)
d.section("Post-processing",  stations=["samtools", "bigtwig"],                 padding=0.75)
d.section("QC & Reporting",   stations=["rseqc", "bedtools", "multiqc"],        padding=0.85)

fig, ax = plt.subplots(figsize=(22, 8))
d.save_svg("graphics/example_animated.svg", ax=ax, animate=True)
plt.close(fig)
print("wrote graphics/example_animated.svg")
