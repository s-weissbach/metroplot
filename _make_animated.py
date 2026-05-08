"""Generate graphics/example_animated.svg for the README.

An elaborate RNA-seq workflow showcasing:
  - Shared pre-processing trunk
  - STAR / HISAT2 alignment fork
  - Three independent downstream branches (splicing, variants, coverage)
  - GSEA sub-branch inside the main DE line
  - Seven section grouping boxes
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

theme = dataclasses.replace(LIGHT, background="#f5f6f8")

d = Diagram(theme=theme, legend_loc="lower right",
            line_width=5.5, station_radius=0.21, label_font=9, sub_font=7)

# ── Pre-processing (shared trunk) ─────────────────────────────────────────────
d.station("fastq",        0,   0,   "FASTQ",           "RAW READS",       "above")
d.station("fastqc_raw",   3,   0,   "FastQC",          "RAW QC",          "above")
d.station("trim",         6,   0,   "Trim Galore",     "TRIMMING",        "above")
d.station("fastqc_trim",  9,   0,   "FastQC",          "TRIM QC",         "above")

# ── Alignment fork ────────────────────────────────────────────────────────────
d.station("star",        12,   2,   "STAR",            "ALIGNMENT",       "above")
d.station("hisat2",      12,  -2,   "HISAT2",          "ALIGNMENT",       "below")
d.station("umitools",    15,   0,   "UMI-tools",       "DEDUPLICATION",   "above")

# ── Alt Splicing branch (TEAL, off STAR) ──────────────────────────────────────
d.station("rmats",       15,   5,   "rMATS",           "ALT SPLICING",    "above")
d.station("maser",       18,   5,   "MASER",           "SPLICING VIZ",    "above")

# ── Variant Calling branch (NAVY, off STAR) ───────────────────────────────────
d.station("gatk_split",  15,   3,   "GATK SplitN",     "CIGAR SPLIT",     "above")
d.station("haplotype",   18,   3,   "HaplotypeCaller", "VARIANT CALL",    "above")
d.station("snpeff",      21,   3,   "SnpEff",          "ANNOTATION",      "above")

# ── Quantification & Differential Expression (ORANGE) ─────────────────────────
d.station("fcounts",     18,   0,   "featureCounts",   "QUANTIFY",        "above")
d.station("deseq2",      21,   0,   "DESeq2",          "DIFF EXPR",       "above")
d.station("gsea",        24,  -2,   "fgsea",           "GENE SET ENRICH", "below")
d.station("clustprof",   24,   0,   "clusterProfiler", "PATHWAY ENRICH",  "above")

# ── Coverage & Genome Tracks (BLUE, off HISAT2) ───────────────────────────────
d.station("samtools",    18,  -4,   "SAMtools",        "BAM SORT/INDEX",  "below")
d.station("bigtwig",     21,  -4,   "bigWig",          "COVERAGE TRACKS", "below")
d.station("deeptools",   24,  -4,   "deepTools",       "PEAK ANALYSIS",   "below")

# ── Report (all lines converge) ───────────────────────────────────────────────
d.station("multiqc",     27,   0,   "MultiQC",         "QC REPORT",       "above")

# ── Lines ─────────────────────────────────────────────────────────────────────
# Main Bulk RNA-seq line — has a GSEA sub-branch off DESeq2
d.line("Bulk RNA-seq", ORANGE, [
    ["fastq", "fastqc_raw", "trim", "fastqc_trim", "star",
     "umitools", "fcounts", "deseq2", "clustprof", "multiqc"],
    ["deseq2", "gsea"],
])

# Alt Splicing — separate line with its own colour, terminates at MASER
d.line("Alt Splicing", TEAL, [
    ["star", "rmats", "maser"],
])

# RNA Variant Calling — from STAR through GATK to MultiQC
d.line("RNA Variants", NAVY, [
    ["star", "gatk_split", "haplotype", "snpeff", "multiqc"],
])

# QC & Genome Tracks — HISAT2 path through coverage tools to MultiQC
d.line("QC Tracks", BLUE, [
    ["fastq", "fastqc_raw", "trim", "fastqc_trim", "hisat2",
     "umitools", "samtools", "bigtwig", "deeptools", "multiqc"],
])

# ── Section grouping boxes ────────────────────────────────────────────────────
d.section("Pre-processing",  stations=["fastq", "fastqc_raw", "trim", "fastqc_trim"], padding=0.9)
d.section("Alignment",       stations=["star", "hisat2", "umitools"],                 padding=0.9)
d.section("Alt Splicing",    stations=["rmats", "maser"],                             padding=0.75)
d.section("Variant Calling", stations=["gatk_split", "haplotype", "snpeff"],         padding=0.75)
d.section("Quant & DE",      stations=["fcounts", "deseq2", "gsea", "clustprof"],    padding=0.8)
d.section("Coverage Tracks", stations=["samtools", "bigtwig", "deeptools"],          padding=0.75,
          label_pos="bottom-middle")
d.section("Report",          stations=["multiqc"],                                    padding=0.7)

fig, ax = plt.subplots(figsize=(24, 10))
d.save_svg("graphics/example_animated.svg", ax=ax, animate=True)
plt.close(fig)
print("wrote graphics/example_animated.svg")
