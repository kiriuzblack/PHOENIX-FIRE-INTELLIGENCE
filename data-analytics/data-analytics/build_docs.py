
# ============================================================
# PHOENIX FIRE INTELLIGENCE
# DATA ANALYTICS - GITHUB DOCUMENTATION BUILDER
# ============================================================

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
REFERENCES = ROOT / "references"

REPORTS.mkdir(parents=True, exist_ok=True)
REFERENCES.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# 1. LOAD EXPORTED DATA
# ------------------------------------------------------------

experiments = pd.read_csv(
    DATA / "integrated_experiments.csv"
)

evidence = pd.read_csv(
    DATA / "evidence_matrix.csv"
)

saffire = pd.read_csv(
    DATA / "saffire_classification.csv"
)

flags = pd.read_csv(
    DATA / "quality_flags.csv"
)

mapping = pd.read_csv(
    REPORTS / "column_mapping.csv"
)

assert len(experiments) == 285
assert len(evidence) == 285
assert len(saffire) == 11
assert len(flags) == 12
assert len(mapping) == 70
assert not mapping["translation_status"].eq(
    "Requires review"
).any()

# ------------------------------------------------------------
# 2. ENGLISH DATA DICTIONARY
# ------------------------------------------------------------

# Define fields whose meanings are supported
# by the current processing methodology.

DEFINITIONS = {
    "test_id": (
        "Normalized experimental test identifier", ""
    ),
    "experiment": (
        "Source experimental program", ""
    ),
    "sample_id": (
        "Experimental sample identifier", ""
    ),
    "material": (
        "Reported fuel or sample material", ""
    ),
    "original_material": (
        "Material text preserved from the source", ""
    ),
    "oxygen_percent": (
        "Representative oxygen concentration", "%"
    ),
    "oxygen_original_text": (
        "Original reported oxygen text", ""
    ),
    "original_oxygen_value": (
        "Original oxygen value preserved as reported", ""
    ),
    "oxygen_min_percent": (
        "Lower bound of a reported oxygen interval", "%"
    ),
    "oxygen_max_percent": (
        "Upper bound of a reported oxygen interval", "%"
    ),
    "oxygen_min_original": (
        "Previously extracted oxygen lower bound; "
        "verify interpretation against the source", ""
    ),
    "oxygen_max_original": (
        "Previously extracted oxygen upper bound; "
        "verify interpretation against the source", ""
    ),
    "oxygen_value_type": (
        "Oxygen value representation category", ""
    ),
    "oxygen_qualifier": (
        "Qualifier associated with reported oxygen", ""
    ),
    "estimated_oxygen_percent": (
        "Derived representative oxygen concentration",
        "%"
    ),
    "pressure_kpa": (
        "Normalized ambient pressure", "kPa"
    ),
    "airflow_m_s": (
        "Normalized airflow speed", "m/s"
    ),
    "burn_time_s": (
        "Numerically reported combustion duration", "s"
    ),
    "original_burn_time": (
        "Original combustion duration or qualitative text",
        ""
    ),
    "source_file": (
        "Original NASA CSV filename", ""
    ),
    "record_type": (
        "Classification of record content", ""
    ),
    "original_result": (
        "Original experimental outcome text", ""
    ),
    "flow_direction": (
        "Reported airflow direction relative to flame",
        ""
    ),
    "original_thickness": (
        "Original sample thickness as reported", ""
    ),
    "thickness_mm": (
        "Parsed thickness; verify ambiguous source values",
        "mm"
    ),
    "original_spread_value": (
        "Original propagation-related source text", ""
    ),
    "reported_spread_mm_s_unverified": (
        "Parsed propagation-related value; source "
        "heading and units require verification",
        "mm/s"
    ),
    "spread_measurement_validated": (
        "Whether the propagation measurement was validated",
        ""
    ),
    "requires_review": (
        "Whether a record is flagged for review", ""
    ),
    "quality_flag_count": (
        "Number of documented data-quality flags",
        "count"
    ),
    "high_priority_flags": (
        "Number of high-priority review flags",
        "count"
    ),
    "medium_priority_flags": (
        "Number of medium-priority review flags",
        "count"
    ),
    "review_priority": (
        "Data review priority; not a fire hazard rating",
        ""
    ),
    "data_coverage": (
        "Availability category for five selected fields",
        ""
    ),
    "available_variables": (
        "Number of available selected variables",
        "count"
    ),
    "evidence_status": (
        "Automated evidence-review status", ""
    ),
    "evidence_state": (
        "Previously assigned evidence status", ""
    ),
    "evidence_type": (
        "Type of experimental evidence", ""
    ),
    "hazard_level": (
        "Fire hazard level; not determined in this dataset",
        ""
    ),
    "quality_notes": (
        "Documented review observations", ""
    ),
    "reported_behavior": (
        "Descriptive combustion outcome category", ""
    ),
    "quality_status": (
        "Preliminary SAFFIRE data-quality category",
        ""
    ),
}

dictionary_rows = []

for _, item in mapping.iterrows():

    table = item["table"]
    column = item["exported_column"]

    description, unit = DEFINITIONS.get(
        column,
        (
            "Definition requires source review",
            ""
        )
    )

    # Read the actual exported table.
    frame = {
        "integrated_experiments": experiments,
        "evidence_matrix": evidence,
        "saffire_classification": saffire,
    }[table]

    dictionary_rows.append({
        "table": table,
        "column_name": column,
        "original_column": item["original_column"],
        "description": description,
        "unit": unit,
        "data_type": str(frame[column].dtype),
        "non_null_records": int(
            frame[column].notna().sum()
        ),
        "missing_records": int(
            frame[column].isna().sum()
        ),
        "definition_status": (
            "Documented"
            if column in DEFINITIONS
            else "Requires source review"
        )
    })

dictionary = pd.DataFrame(dictionary_rows)

dictionary.to_csv(
    REPORTS / "data_dictionary.csv",
    index=False,
    encoding="utf-8-sig"
)

# ------------------------------------------------------------
# 3. CALCULATE SCIENTIFIC SUMMARY
# ------------------------------------------------------------

flex = experiments[
    experiments["experiment"] == "FLEX"
].copy()

flex["burn_time_s"] = pd.to_numeric(
    flex["burn_time_s"],
    errors="coerce"
)

flex_summary = flex.groupby("material").agg(
    tests=("test_id", "count"),
    durations_available=("burn_time_s", "count"),
    median_duration_s=("burn_time_s", "median"),
    mean_duration_s=("burn_time_s", "mean"),
).reset_index()

saffire_summary = (
    saffire.groupby(
        ["experiment", "reported_behavior"]
    )
    .size()
    .reset_index(name="tests")
)

priority_summary = (
    evidence["review_priority"]
    .value_counts()
    .rename_axis("priority")
    .reset_index(name="tests")
)

# ------------------------------------------------------------
# 4. SCIENTIFIC REPORT IN ENGLISH
# ------------------------------------------------------------

report = f"""# PHOENIX DATA ANALYTICS

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

{flex_summary.round(3).to_markdown(index=False)}

FLEX includes methanol and heptane droplet combustion
tests. Differences in observed burn duration are
descriptive and must be interpreted in relation to
oxygen concentration, pressure, initial droplet size,
and experimental outcomes.

### SAFFIRE: Reported Outcomes

{saffire_summary.to_markdown(index=False)}

Qualitative observations, including "Insignificant",
are not treated as numeric zero-duration measurements.

### Data Quality

{priority_summary.to_markdown(index=False)}

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
"""

(REPORTS / "scientific_report.md").write_text(
    report,
    encoding="utf-8"
)

# ------------------------------------------------------------
# 5. OFFICIAL NASA REFERENCE LINKS
# ------------------------------------------------------------

resources = [
    (
        "NASA PSI Combustion Data",
        "https://psi.nasa.gov/physci/repo/search?q=combustion"
    ),
    (
        "NASA Combustion Science",
        "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/"
    ),
    (
        "NASA ScienceCasts: Combustion on the ISS",
        "https://www.youtube.com/watch?v=W1oXykoz9zg"
    ),
    (
        "ISS Combustion Science Researcher's Guide",
        "https://www.nasa.gov/missions/station/a-researchers-guide-to-combustion-science/"
    ),
    (
        "Apollo 1",
        "https://sma.nasa.gov/sma-disciplines/accllp/apollo-1"
    ),
    (
        "Apollo 13",
        "https://sma.nasa.gov/sma-disciplines/accllp/apollo-13"
    ),
    (
        "1997 Mir Space Station Fire",
        "https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/"
    ),
    (
        "Fireman's Air Tanks",
        "https://spinoff.nasa.gov/node/9582"
    ),
    (
        "Fire Detector",
        "https://spinoff.nasa.gov/node/9407"
    ),
    (
        "New Technology for the Fire Attire",
        "https://spinoff.nasa.gov/node/9918"
    ),
]

references_text = (
    "# NASA Scientific Resources\n\n"
    "These NASA resources provide experimental data, "
    "scientific background, historical safety cases, "
    "and technology-transfer examples.\n\n"
)

for label, url in resources:
    references_text += f"- [{label}]({url})\n"

references_text += (
    "\n## Evidence Categories\n\n"
    "- **Experimental evidence:** PSI FLEX and SAFFIRE data.\n"
    "- **Historical cases:** Apollo 1, Apollo 13, and Mir.\n"
    "- **Context and technology:** NASA research guides, "
    "videos, and Spinoff projects.\n\n"
    "Historical cases and technology examples are not "
    "included in the 285 experimental tests.\n\n"
    "These references do not imply NASA endorsement.\n"
)

(REFERENCES / "README.md").write_text(
    references_text,
    encoding="utf-8"
)

# ------------------------------------------------------------
# 6. GITHUB README
# ------------------------------------------------------------

readme = """# PHOENIX FIRE INTELLIGENCE

**NASA Space Apps Challenge 2026 — Flame in Freefall**

**Team:** PHOENIX Orbit  
**Module:** Data Analytics

## Project Overview

PHOENIX FIRE INTELLIGENCE is an exploratory
data analytics application for investigating
NASA combustion experiments under microgravity
research conditions.

## Experimental Data

- 274 FLEX tests
- 2 SAFFIRE-I tests
- 9 SAFFIRE-II tests
- 285 integrated experimental tests
- 12 documented quality flags

## Features

- Experimental data exploration
- FLEX fuel comparisons
- SAFFIRE material and combustion analysis
- Oxygen measurement interpretation
- Data quality auditing
- Interactive Streamlit visualizations
- CSV exports
- Links to official NASA resources

## Installation

```bash
pip install -r requirements.txt
```

## Run the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard reads the CSV files in `data/`.

## Data Documentation

- [Scientific Report](reports/scientific_report.md)
- [Data Dictionary](reports/data_dictionary.csv)
- [NASA Scientific Resources](references/README.md)

## Scientific Integrity

The results are exploratory. Data review priorities
are not fire hazard ratings.

Fire hazard levels are not determined by this module.

Some experimental variables and source units
require additional documentary verification.

## Source Attribution

Experimental datasets originate from the NASA
Physical Sciences Informatics repository.

This project is developed independently by
PHOENIX Orbit and is not an official NASA product.
"""

(ROOT / "README.md").write_text(
    readme,
    encoding="utf-8"
)

# ------------------------------------------------------------
# 7. FINAL STATUS
# ------------------------------------------------------------

pending = int(
    dictionary["definition_status"]
    .eq("Requires source review")
    .sum()
)

print("=" * 60)
print("PHOENIX - GITHUB DOCUMENTATION")
print("=" * 60)

print("Integrated tests:", len(experiments))
print("Dictionary entries:", len(dictionary))
print("Definitions requiring source review:", pending)

print("\nGenerated files:")
print("- README.md")
print("- reports/scientific_report.md")
print("- reports/data_dictionary.csv")
print("- references/README.md")

print("\nDOCUMENTATION GENERATED")
