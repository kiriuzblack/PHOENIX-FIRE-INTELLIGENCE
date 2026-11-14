# PHOENIX DATA ANALYTICS

## Preliminary Scientific Report

**Project:** PHOENIX FIRE INTELLIGENCE  
**Team:** PHOENIX Orbit  
**Challenge:** NASA Space Apps Challenge 2026 — Flame in Freefall

### Objective

To organize, standardize, audit, and explore NASA
experimental combustion data collected under
microgravity-related research conditions.

### Dataset Overview

The source tables contain 293 original records,
including auxiliary records and explanatory notes.

The integrated analytical dataset contains 285 tests:

| Experiment | Tests |
|---|---:|
| FLEX | 274 |
| SAFFIRE-I | 2 |
| SAFFIRE-II | 9 |
| **Total** | **285** |

### FLEX: Descriptive Statistics

| material   |   tests |   durations_available |   median_duration_s |   mean_duration_s |
|:-----------|--------:|----------------------:|--------------------:|------------------:|
| Heptane    |     117 |                   112 |                 7.5 |             7.938 |
| Methanol   |     157 |                   156 |                11.9 |            13.51  |

FLEX includes methanol and heptane droplet combustion
tests. Differences in observed burn duration are
descriptive and must be interpreted in relation to
oxygen concentration, pressure, initial droplet size,
and experimental outcomes.

### SAFFIRE: Reported Outcomes

| experiment   | reported_behavior                 |   tests |
|:-------------|:----------------------------------|--------:|
| SAFFIRE-I    | Quantified duration               |       2 |
| SAFFIRE-II   | Insignificant combustion reported |       4 |
| SAFFIRE-II   | Quantified duration               |       5 |

Qualitative observations, including "Insignificant",
are not treated as numeric zero-duration measurements.

### Data Quality

| priority   |   tests |
|:-----------|--------:|
| Routine    |     275 |
| High       |       5 |
| Medium     |       5 |

The dataset contains **12 documented quality flags**
associated with **10 experimental tests**.

Review priority describes data quality or interpretation
needs. It is not a fire hazard rating.

### Oxygen Data and Uncertainty

For SAFFIRE-II, seven oxygen entries are reported
approximately and two as ranges.

Representative midpoints are used for descriptive
analysis where appropriate. Original reported values
and interval boundaries are retained.

### Scientific Limitations

- These analyses are exploratory.
- Correlation does not establish causation.
- Combustion duration alone is not a measure of
  fire hazard or severity.
- FLEX and SAFFIRE involve different physical systems
  and should not be directly compared without a
  justified methodology.
- Certain SAFFIRE-II sample materials are unidentified.
- Several sample-thickness values require verification.
- Propagation-related column names and units
  require documentary confirmation.
- The FLEX test 114 non-positive pressure entry
  remains flagged.
- Automated integrity checks do not replace
  independent scientific validation.

### Conclusion

PHOENIX DATA ANALYTICS provides an integrated
experimental dataset, a traceable quality-flag matrix,
and an interactive dashboard supporting exploratory
analysis of combustion research.

Fire hazard levels remain **Not determined**.

### Sources

Primary experimental data source:
[NASA Physical Sciences Informatics](https://psi.nasa.gov/physci/repo/search?q=combustion)

Additional references:
[Official NASA Resources](../references/README.md)

### Disclaimer

PHOENIX FIRE INTELLIGENCE is an independent student
project and is not an official NASA product.
