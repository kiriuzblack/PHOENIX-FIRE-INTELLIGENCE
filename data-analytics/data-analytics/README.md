# PHOENIX FIRE INTELLIGENCE

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
