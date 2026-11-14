
# ==============================================
# PHOENIX ORBIT - CODIGO 17
# ANALISIS CONTROLANDO LA PRESION
# ==============================================

from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)
SALIDA = BASE / "phoenix_data"
DB = SALIDA / "phoenix_fire.db"

with sqlite3.connect(DB) as conn:
    df = pd.read_sql_query(
        """
        SELECT *
        FROM nasa_unificado_validado
        WHERE experimento = 'FLEX'
        """,
        conn
    )

    original = pd.read_sql_query(
        'SELECT * FROM "dataset_001"', conn
    )

# Vincular resultado original del ensayo
original.columns = original.columns.str.strip()
original["id_ensayo"] = (
    "FLEX-" + original["FLEX Test #"].astype(str)
)

df = df.merge(
    original[["id_ensayo", "Test end"]],
    on="id_ensayo",
    how="left",
    validate="one_to_one"
)

# Convertir variables
for columna in [
    "oxigeno_pct",
    "presion_kpa",
    "tiempo_combustion_s"
]:
    df[columna] = pd.to_numeric(
        df[columna], errors="coerce"
    )

# Seleccionar presiones comparables
datos = df[
    df["presion_kpa"].between(95, 105)
].copy()

print("=" * 55)
print("PHOENIX - ANALISIS CON PRESION CONTROLADA")
print("=" * 55)

print("Ensayos FLEX originales:", len(df))
print("Ensayos seleccionados:", len(datos))

# Clasificar oxigeno
limites = [0, 15, 20, 25, 35, 100]
etiquetas = [
    "0-15%",
    ">15-20%",
    ">20-25%",
    ">25-35%",
    ">35-100%"
]

datos["rango_oxigeno"] = pd.cut(
    datos["oxigeno_pct"],
    bins=limites,
    labels=etiquetas,
    include_lowest=True
)

# Resumen descriptivo
resumen = datos.groupby(
    ["material", "rango_oxigeno"],
    observed=True
).agg(
    ensayos=("id_ensayo", "count"),
    tiempos_disponibles=(
        "tiempo_combustion_s", "count"
    ),
    tiempo_mediano_s=(
        "tiempo_combustion_s", "median"
    ),
    presion_mediana_kpa=(
        "presion_kpa", "median"
    )
).reset_index()

resumen["muestra_suficiente"] = (
    resumen["ensayos"] >= 5
)

print("\nCOMPARACION BAJO PRESIONES SIMILARES")
print(resumen.to_string(index=False))

# Resultados de finalizacion
finalizacion = pd.crosstab(
    [
        datos["material"],
        datos["rango_oxigeno"]
    ],
    datos["Test end"],
    dropna=False
)

print("\nFINALIZACION DE ENSAYOS")
print(finalizacion.to_string())

# Guardar resultados
resumen.to_csv(
    SALIDA / "flex_presion_controlada.csv",
    index=False,
    encoding="utf-8-sig"
)

finalizacion.to_csv(
    SALIDA / "flex_finalizacion_presion_controlada.csv",
    encoding="utf-8-sig"
)

# Grafica: solo grupos con 5 o mas ensayos
grafica = resumen[
    resumen["muestra_suficiente"]
].copy()

if not grafica.empty:

    tabla = grafica.pivot(
        index="rango_oxigeno",
        columns="material",
        values="tiempo_mediano_s"
    )

    ax = tabla.plot(
        kind="bar",
        figsize=(10, 6)
    )

    ax.set_title(
        "FLEX - Oxigeno y combustion\n"
        "Presion entre 95 y 105 kPa"
    )

    ax.set_xlabel("Concentracion de oxigeno")
    ax.set_ylabel("Tiempo mediano (s)")
    ax.grid(axis="y", alpha=0.3)

    plt.xticks(rotation=30)
    plt.tight_layout()

    plt.savefig(
        SALIDA / "flex_presion_controlada.png",
        dpi=300
    )

    plt.close()

print("\nANALISIS FINALIZADO")
print("Resultados guardados en:", SALIDA)
