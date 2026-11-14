
# PHOENIX ORBIT - CODIGO 18
# OXIGENO, DIAMETRO Y DURACION DE COMBUSTION

from pathlib import Path
import sqlite3
import pandas as pd

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

SALIDA = BASE / "phoenix_data"
DB = SALIDA / "phoenix_fire.db"

with sqlite3.connect(DB) as conn:
    datos = pd.read_sql_query(
        """
        SELECT id_ensayo, material, oxigeno_pct,
               presion_kpa, tiempo_combustion_s
        FROM nasa_unificado_validado
        WHERE experimento = 'FLEX'
        """,
        conn
    )

    original = pd.read_sql_query(
        'SELECT * FROM "dataset_001"',
        conn
    )

original.columns = original.columns.str.strip()

original["id_ensayo"] = (
    "FLEX-" + original["FLEX Test #"].astype(str)
)

# Vincular diámetro y resultado original
datos = datos.merge(
    original[
        [
            "id_ensayo",
            "Droplet initial diameter; mm",
            "Test end"
        ]
    ],
    on="id_ensayo",
    how="left",
    validate="one_to_one"
)

datos["diametro_mm"] = pd.to_numeric(
    original.set_index("id_ensayo")
    .reindex(datos["id_ensayo"])[
        "Droplet initial diameter; mm"
    ].to_numpy(),
    errors="coerce"
)

for columna in [
    "oxigeno_pct",
    "presion_kpa",
    "tiempo_combustion_s"
]:
    datos[columna] = pd.to_numeric(
        datos[columna], errors="coerce"
    )

# Seleccionar presión de 95 a 105 kPa
datos = datos[
    datos["presion_kpa"].between(95, 105)
].copy()

# Conservar observaciones con variables disponibles
datos = datos.dropna(
    subset=[
        "diametro_mm",
        "oxigeno_pct",
        "tiempo_combustion_s"
    ]
)

# Rangos de diámetro EXPLORATORIOS
datos["grupo_diametro"] = pd.cut(
    datos["diametro_mm"],
    bins=[0, 1.5, 2.0, 2.5, float("inf")],
    labels=[
        "0-1.5 mm",
        ">1.5-2.0 mm",
        ">2.0-2.5 mm",
        ">2.5 mm"
    ],
    include_lowest=True
)

datos["grupo_oxigeno"] = pd.cut(
    datos["oxigeno_pct"],
    bins=[0, 15, 20, 25, 35, 100],
    labels=[
        "0-15%",
        ">15-20%",
        ">20-25%",
        ">25-35%",
        ">35-100%"
    ],
    include_lowest=True
)

# Resumen por combustible, oxígeno y diámetro
resumen = datos.groupby(
    ["material", "grupo_oxigeno", "grupo_diametro"],
    observed=True
).agg(
    ensayos=("id_ensayo", "count"),
    mediana_tiempo_s=(
        "tiempo_combustion_s", "median"
    ),
    diametro_mediano_mm=("diametro_mm", "median")
).reset_index()

resumen["analisis_exploratorio"] = (
    resumen["ensayos"] >= 5
)

print("\nTOTAL DE ENSAYOS ANALIZABLES:", len(datos))

print("\nCOMPARACION POR OXIGENO Y DIAMETRO:")
print(resumen.to_string(index=False))

print("\nGRUPOS CON AL MENOS 5 ENSAYOS:")
print(
    resumen[
        resumen["analisis_exploratorio"]
    ].to_string(index=False)
)

resumen.to_csv(
    SALIDA / "flex_oxigeno_diametro.csv",
    index=False,
    encoding="utf-8-sig"
)

datos.to_csv(
    SALIDA / "flex_datos_comparables.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nANALISIS FINALIZADO")
