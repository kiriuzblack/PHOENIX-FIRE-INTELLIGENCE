
# ============================================================
# PHOENIX FIRE INTELLIGENCE
# PHOENIX ORBIT - NASA SPACE APPS CHALLENGE 2026
# DATA ANALYTICS - GITHUB DATA EXPORT
# ============================================================

from pathlib import Path
import sqlite3
import os
import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent

# Local database used to generate the exported datasets.
# Set PHOENIX_DB to use a different database location.

DEFAULT_DB = (
    Path.home()
    / "Documents"
    / "Machine"
    / "guia2"
    / "phoenix_data"
    / "phoenix_fire.db"
)

DB = Path(
    os.environ.get(
        "PHOENIX_DB",
        str(DEFAULT_DB)
    )
)

DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

if not DB.is_file():
    raise FileNotFoundError(
        f"NASA database not found: {DB}"
    )


# ============================================================
# 2. SOURCE TABLES
# ============================================================

TABLES = {
    "integrated_experiments": "nasa_unificado_v2",
    "evidence_matrix": "matriz_evidencia_v2",
    "saffire_classification": "saffire_clasificado",
}


# ============================================================
# 3. COLUMN NAME TRANSLATIONS
# ============================================================

COLUMN_NAMES = {

    # Basic experiment identification
    "id_ensayo": "test_id",
    "experimento": "experiment",
    "muestra": "sample_id",
    "material": "material",

    # Oxygen measurements
    "oxigeno_pct": "oxygen_percent",
    "oxigeno_texto_original": "oxygen_original_text",
    "oxigeno_min_pct": "oxygen_min_percent",
    "oxigeno_max_pct": "oxygen_max_percent",
    "tipo_oxigeno": "oxygen_value_type",

    # Experimental conditions
    "presion_kpa": "pressure_kpa",
    "flujo_m_s": "airflow_m_s",
    "tiempo_combustion_s": "burn_time_s",

    # Data source
    "fuente_archivo": "source_file",

    # Quality indicators
    "total_incidencias": "quality_flag_count",
    "incidencias_altas": "high_priority_flags",
    "incidencias_medias": "medium_priority_flags",
    "prioridad_revision": "review_priority",
    "cobertura_datos": "data_coverage",
    "clasificacion_evidencia": "evidence_status",
    "nivel_peligro": "hazard_level",
    "observaciones": "quality_notes",
    "variables_disponibles": "available_variables",

    # SAFFIRE classification
    "comportamiento_reportado": "reported_behavior",
    "estado_calidad": "quality_status",

    # Additional scientific fields
    "tipo_registro": "record_type",
    "resultado_original": "original_result",
    "oxigeno_min": "oxygen_min_original",
    "oxigeno_max": "oxygen_max_original",
    "calificador_oxigeno": "oxygen_qualifier",
    "oxigeno_original": "original_oxygen_value",
    "estado_evidencia": "evidence_state",

    # Additional SAFFIRE fields
    "material_original": "original_material",
    "oxigeno_estimado_pct": "estimated_oxygen_percent",
    "tiempo_original": "original_burn_time",
    "direccion_flujo": "flow_direction",
    "espesor_original": "original_thickness",
    "espesor_mm": "thickness_mm",
    "propagacion_original": "original_spread_value",
    "propagacion_mm_s": "reported_spread_mm_s_unverified",
    "propagacion_validada": "spread_measurement_validated",
    "requiere_revision": "requires_review",
    "tipo_evidencia": "evidence_type",
}


# ============================================================
# 4. CATEGORICAL VALUE TRANSLATIONS
# ============================================================

VALUE_NAMES = {

    # Review priority
    "Alta": "High",
    "Media": "Medium",
    "Ordinaria": "Routine",

    # Data coverage
    "Amplia": "Broad",
    "Intermedia": "Intermediate",
    "Limitada": "Limited",

    # Oxygen measurement type
    "Aproximado": "Approximate",
    "Intervalo reportado": "Reported range",
    "Valor reportado": "Reported value",
    "Faltante": "Missing",
    "No interpretable": "Not interpretable",
    "Fuera de rango": "Out of range",

    # Hazard classification
    "No determinado": "Not determined",

    # Combustion behavior
    "Duracion cuantificada": "Quantified duration",
    "Combustion insignificante reportada":
        "Insignificant combustion reported",

    # Evidence status
    "Requiere revision prioritaria":
        "Priority review required",

    "Requiere interpretacion":
        "Interpretation required",

    "Sin incidencias detectadas":
        "No flags detected",

    "Sin incidencias detectadas por las reglas":
        "No flags detected by current rules",

    # Quality status
    "Variables basicas disponibles":
        "Basic variables available",

    "Requiere verificar espesor":
        "Thickness verification required",

    "Requiere verificar material":
        "Material verification required",

    # Flow direction
    "Concurrent": "Concurrent",
    "Opposed": "Opposed",

    # Review status
    "Pendiente": "Pending",
}


# ============================================================
# 5. QUALITY DESCRIPTION TRANSLATIONS
# ============================================================

QUALITY_DESCRIPTIONS = {

    "Presión ausente o no positiva":
        "Missing or non-positive pressure",

    "Dato aproximado o intervalo":
        "Approximate value or reported range",

    "Resultado cualitativo":
        "Qualitative experimental result",

    "Formato numérico ambiguo":
        "Ambiguous numeric format",

    "Material sin identificar":
        "Unidentified material",

    # Alternative descriptions from prior audits
    "Presion faltante, nula o no positiva":
        "Missing, zero, or non-positive pressure",

    "Valor aproximado o intervalo":
        "Approximate value or reported range",

    "Resultado cualitativo; no es una duracion":
        "Qualitative result; not a numeric duration",

    "Formato numerico ambiguo":
        "Ambiguous numeric format",

    "Material no identificado":
        "Unidentified material",
}


# ============================================================
# 6. TRANSLATION FUNCTION
# ============================================================

def translate_dataframe(frame):

    # Translate column names without changing measurements.
    result = frame.rename(
        columns=COLUMN_NAMES
    ).copy()

    # Only translate categorical fields.
    # Original NASA values remain unchanged.

    categorical_columns = [
        "review_priority",
        "data_coverage",
        "evidence_status",
        "evidence_state",
        "hazard_level",
        "reported_behavior",
        "quality_status",
        "oxygen_value_type",
        "oxygen_qualifier",
        "record_type",
        "evidence_type",
        "flow_direction",
    ]

    for column in categorical_columns:

        if column in result.columns:

            result[column] = (
                result[column].replace(
                    VALUE_NAMES
                )
            )

    # Translate known audit notes.
    if "quality_notes" in result.columns:

        def translate_notes(value):

            if pd.isna(value):
                return value

            parts = [
                part.strip()
                for part in str(value).split(";")
            ]

            translated_parts = [
                QUALITY_DESCRIPTIONS.get(
                    part,
                    VALUE_NAMES.get(part, part)
                )
                for part in parts
            ]

            return "; ".join(translated_parts)

        result["quality_notes"] = (
            result["quality_notes"].apply(
                translate_notes
            )
        )

    return result


# ============================================================
# 7. EXPORT SCIENTIFIC TABLES
# ============================================================

exported = {}
mapping_records = []

with sqlite3.connect(DB) as conn:

    for output_name, source_table in TABLES.items():

        original = pd.read_sql_query(
            f'SELECT * FROM "{source_table}"',
            conn
        )

        translated = translate_dataframe(
            original
        )

        # Record every original-to-English column mapping.
        for old_column in original.columns:

            mapping_records.append({

                "table": output_name,

                "original_column": old_column,

                "exported_column": COLUMN_NAMES.get(
                    old_column,
                    old_column
                ),

                "translation_status": (
                    "Mapped"
                    if old_column in COLUMN_NAMES
                    else "Requires review"
                ),
            })

        exported[output_name] = translated


# ============================================================
# 8. READ AND TRANSLATE QUALITY FLAGS
# ============================================================

QUALITY_SOURCE = (
    DB.parent
    / "entrega_analisis"
    / "validacion_automatica.csv"
)

if not QUALITY_SOURCE.is_file():

    raise FileNotFoundError(
        f"Quality audit file not found: {QUALITY_SOURCE}"
    )

quality = pd.read_csv(
    QUALITY_SOURCE,
    dtype={"ensayo": str}
)

quality = quality.rename(
    columns={
        "dataset": "experiment",
        "ensayo": "sample_id",
        "variable": "flagged_variable",
        "valor_original": "original_value",
        "descripcion": "description",
        "prioridad": "review_priority",
        "estado": "review_status",
    }
)

# Translate review priority.
quality["review_priority"] = (
    quality["review_priority"].replace(
        VALUE_NAMES
    )
)

# Translate quality descriptions.
quality["description"] = (
    quality["description"].replace(
        QUALITY_DESCRIPTIONS
    )
)

# Translate review status.
quality["review_status"] = (
    quality["review_status"].replace(
        VALUE_NAMES
    )
)

# Translate names of flagged variables.
FLAGGED_VARIABLES = {
    "Presión": "Pressure",
    "Presion": "Pressure",
    "Oxígeno": "Oxygen",
    "Oxigeno": "Oxygen",
    "Tiempo": "Time",
    "Tiempo de combustión": "Burn time",
    "Tiempo de combustion": "Burn time",
    "Espesor": "Thickness",
    "Material": "Material",
}

quality["flagged_variable"] = (
    quality["flagged_variable"].replace(
        FLAGGED_VARIABLES
    )
)


# ============================================================
# 9. INTEGRITY VALIDATION
# ============================================================

experiments = exported["integrated_experiments"]
evidence = exported["evidence_matrix"]
saffire = exported["saffire_classification"]

expected_counts = {
    "FLEX": 274,
    "SAFFIRE-I": 2,
    "SAFFIRE-II": 9,
}

assert len(experiments) == 285, (
    "Expected 285 integrated experiments"
)

assert len(evidence) == 285, (
    "Expected 285 evidence records"
)

assert len(saffire) == 11, (
    "Expected 11 SAFFIRE tests"
)

assert len(quality) == 12, (
    "Expected 12 documented quality flags"
)

assert experiments["test_id"].notna().all()

assert evidence["test_id"].notna().all()

assert experiments["test_id"].is_unique

assert evidence["test_id"].is_unique

assert set(experiments["test_id"]) == set(
    evidence["test_id"]
)

assert (
    experiments["experiment"]
    .value_counts()
    .to_dict()
) == expected_counts

assert int(
    pd.to_numeric(
        evidence["quality_flag_count"],
        errors="raise"
    ).sum()
) == 12

expected_saffire_ii = {
    f"SAFFIRE-II-2-{i}"
    for i in range(1, 10)
}

actual_saffire_ii = set(
    experiments.loc[
        experiments["experiment"] == "SAFFIRE-II",
        "test_id"
    ]
)

assert actual_saffire_ii == expected_saffire_ii, (
    "SAFFIRE-II test identifiers do not match"
)

# Ensure all quality flags refer to an integrated test.
quality["test_id"] = (
    quality["experiment"].astype(str)
    + "-"
    + quality["sample_id"].astype(str).str.strip()
)

assert set(quality["test_id"]).issubset(
    set(experiments["test_id"])
), "Some quality flags cannot be linked to tests"

# Verify flag counts per experiment.
flag_counts = (
    quality.groupby("test_id")
    .size()
    .to_dict()
)

matrix_counts = (
    evidence.set_index("test_id")[
        "quality_flag_count"
    ].to_dict()
)

for test_id, count in flag_counts.items():

    assert int(matrix_counts[test_id]) == count, (
        f"Incorrect flag count: {test_id}"
    )


# ============================================================
# 10. EXPORT CSV FILES
# ============================================================

for output_name, frame in exported.items():

    destination = (
        DATA_DIR / f"{output_name}.csv"
    )

    frame.to_csv(
        destination,
        index=False,
        encoding="utf-8-sig"
    )

quality.to_csv(
    DATA_DIR / "quality_flags.csv",
    index=False,
    encoding="utf-8-sig"
)

mapping = pd.DataFrame(
    mapping_records
)

mapping.to_csv(
    REPORTS_DIR / "column_mapping.csv",
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 11. CHECK COLUMN TRANSLATION COVERAGE
# ============================================================

pending = mapping[
    mapping["translation_status"] == "Requires review"
]

print("=" * 60)
print("PHOENIX - GITHUB DATA EXPORT")
print("=" * 60)

print("\nIntegrated experiments:", len(experiments))
print("SAFFIRE tests:", len(saffire))
print("Documented quality flags:", len(quality))

print("\nColumn mapping entries:", len(mapping))
print("Columns requiring review:", len(pending))

if not pending.empty:

    print("\nColumns requiring translation:")

    print(
        pending[
            [
                "table",
                "original_column"
            ]
        ].to_string(index=False)
    )

print("\nExport directory:")
print(DATA_DIR)

print("\nColumn mapping report:")
print(
    REPORTS_DIR / "column_mapping.csv"
)

print("\nEXPORT COMPLETED")
