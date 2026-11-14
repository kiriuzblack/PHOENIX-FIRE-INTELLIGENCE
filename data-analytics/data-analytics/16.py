
# PHOENIX ORBIT - CODIGO 16
# Comparacion de FLEX por oxigeno y combustible

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
        'SELECT * FROM "dataset_001"',
        conn
    )

original.columns = original.columns.str.strip()
original["id_ensayo"] = (
    "FLEX-" + original["FLEX Test #"].astype(str)
)

# Incorporar resultado del ensayo
df = df.merge(
    original[["id_ensayo", "Test end"]],
    on="id_ensayo",
    how="left",
    validate="one_to_one"
)

# Normalizar variables numéricas
for columna in [
    "oxigeno_pct",
    "presion_kpa",
    "tiempo_combustion_s"
]:
    df[columna] = pd.to_numeric(
        df[columna], errors="coerce"
    )

# Marcar presión anómala sin borrar la original
df["presion_valida"] = df["presion_kpa"].where(
    df["presion_kpa"] > 0
)

# Rangos descriptivos propuestos
limites = [0, 15, 20, 25, 35, 100]
etiquetas = [
    "0-15%",
    ">15-20%",
    ">20-25%",
    ">25-35%",
    ">35-100%"
]

df["rango_oxigeno"] = pd.cut(
    df["oxigeno_pct"],
    bins=limites,
    labels=etiquetas,
    include_lowest=True
)

# Resumen por combustible y oxígeno
resumen = df.groupby(
    ["material", "rango_oxigeno"],
    observed=True
).agg(
    ensayos=("id_ensayo", "count"),
    tiempos_disponibles=("tiempo_combustion_s", "count"),
    tiempo_mediano_s=("tiempo_combustion_s", "median"),
    presion_mediana_kpa=("presion_valida", "median")
).reset_index()

print("\nRESUMEN POR COMBUSTIBLE Y OXIGENO")
print(resumen.to_string(index=False))

# Contar resultados finales por grupo
finalizacion = pd.crosstab(
    [
        df["material"],
        df["rango_oxigeno"]
    ],
    df["Test end"],
    dropna=False
)

print("\nFINALIZACION POR RANGO DE OXIGENO")
print(finalizacion.to_string())

# Guardar reportes
resumen.to_csv(
    SALIDA / "flex_oxigeno_grupos.csv",
    index=False,
    encoding="utf-8-sig"
)

finalizacion.to_csv(
    SALIDA / "flex_oxigeno_finalizacion.csv",
    encoding="utf-8-sig"
)

# Gráfica descriptiva
datos_grafica = resumen.pivot(
    index="rango_oxigeno",
    columns="material",
    values="tiempo_mediano_s"
)

ax = datos_grafica.plot(
    kind="bar",
    figsize=(11, 6)
)

ax.set_title(
    "FLEX: mediana de combustion por oxigeno"
)
ax.set_ylabel("Tiempo mediano (s)")
ax.set_xlabel("Concentracion inicial de oxigeno")
ax.grid(axis="y", alpha=0.3)

plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(
    SALIDA / "flex_oxigeno_comparacion.png",
    dpi=300
)
plt.close()

print("\nANALISIS FINALIZADO")
print("Resultados guardados en:", SALIDA)
