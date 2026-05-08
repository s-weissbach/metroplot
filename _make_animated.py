"""Generate graphics/example_animated.svg for the README."""
import sys
sys.path.insert(0, "src")

import matplotlib
matplotlib.use("Agg")

from metroplot import Diagram
from metroplot.themes import PALETTES

RED, BLUE, TEAL, NAVY = PALETTES["default"]

d = Diagram(theme="light", legend_loc="lower right")

(d.station("sra",    0.0,  0.0, "SRA",          "DATA DOWNLOAD",    "above")
  .station("fastqc", 2.0,  0.0, "FastQC",       "QC",               "above")
  .station("trim",   4.0,  0.0, "Trim Galore",  "TRIMMING",         "above")
  .station("star",   6.0,  0.0, "STAR",         "ALIGNMENT",        "above")
  .station("rmats",  9.0,  0.0, "rMATS",        "ALT SPLICING",     "above")
  .station("bam",    8.0, -2.0, "bamCoverage",  "COVERAGE",         "below")
  .station("fc",     6.0, -2.0, "featureCounts","QUANTIFICATION",   "below")
  .station("deseq",  9.0, -2.0, "DESeq2",       "DIFF EXPRESSION",  "below"))

d.line("splicing",   RED,  [
    ["sra", "fastqc", "trim", "star", "rmats"],
    ["rmats", "bam"],
])
d.line("expression", NAVY, [
    ["sra", "fastqc", "trim", "star", "fc", "deseq"],
])

d.section("Pre-processing", stations=["sra", "fastqc", "trim"], padding=0.65)
d.section("Alignment",      stations=["star"],                   padding=0.65)
d.section("Downstream",     stations=["rmats", "bam", "fc", "deseq"], padding=0.65)

d.save_svg("graphics/example_animated.svg", animate=True)
print("wrote graphics/example_animated.svg")
