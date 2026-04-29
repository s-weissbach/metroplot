"""Example: an RNA-seq pipeline rendered as a subway map."""
import matplotlib.pyplot as plt

from metroplot import Diagram

NAVY = "#1f2a44"
SALMON = "#e07a6b"

d = Diagram()
(d.station("sra",           0.0,  0.0, "SRA tool",      "DATA DOWNLOAD", "below")
  .station("fastqc",        2.0,  0.0, "fastqc",        "QUALITY CONTROL")
  .station("bbduk",         4.0,  0.0, "bbduk",         "ADAPTER TRIMMING")
  .station("star",          6.0,  0.0, "STAR",          "ALIGNMENT")
  .station("rmats",         9.0,  0.0, "rMATS",         "ALT SPLICING ANALYSIS")
  .station("bamcoverage",   8.0, -1.5, "bamCoverage",   "COVERAGE FOR SASHIMI", "below")
  .station("featurecounts", 6.0, -2.5, "featureCounts", "GENE QUANTIFICATION", "below")
  .station("multiqc",       4.0, -2.5, "multiqc",       "QUALITY CONTROL", "below")
  .station("tpm",           2.0, -2.5, "TPM",           "NORMALIZATION", "below"))

d.line("splicing", SALMON, [
    ["sra", "fastqc", "bbduk", "star", "rmats"],
    ["rmats", "bamcoverage"],
])
d.line("quant", NAVY, [
    ["sra", "fastqc", "bbduk", "star", "featurecounts", "multiqc", "tpm"],
])

d.render()
plt.tight_layout()
plt.savefig("example.png", dpi=150, bbox_inches="tight")
print("wrote example.png")
