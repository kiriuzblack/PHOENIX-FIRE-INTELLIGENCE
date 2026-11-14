
# PHOENIX ORBIT - CODIGO 12
# Analisis descriptivo FLEX

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

variables = [
    "oxigeno_pct",
    "presion_kpa",
    "tiempo_combustion_s"
]

for columna in variables:
    df[columna] = pd.to_numeric(
        df[columna], errors="coerce"
    )

print("\nTOTAL FLEX:", len(df))

print("\nCOMBUSTIBLES:")
print(df["material"].value_counts())

print("\nESTADISTICAS:")
print(df[variables].describe().to_string())

print("\nVALORES FALTANTES:")
print(df[variables].isna().sum())

# Resumen por combustible
resumen = df.groupby("material").agg(
    ensayos=("id_ensayo", "count"),
    tiempo_mediano_s=("tiempo_combustion_s", "median"),
    tiempo_disponible=("tiempo_combustion_s", "count"),
    oxigeno_mediano_pct=("oxigeno_pct", "median"),
    presion_mediana_kpa=("presion_kpa", "median")
).reset_index()

print("\nRESUMEN POR COMBUSTIBLE:")
print(resumen.to_string(index=False))

resumen.to_csv(
    SALIDA / "flex_resumen_combustibles.csv",
    index=False,
    encoding="utf-8-sig"
)

# Grafica de numero de ensayos por combustible
fig, ax = plt.subplots(figsize=(10, 5))

df["material"].value_counts().plot(
    kind="bar", ax=ax
)

ax.set_title("FLEX - Ensayos por combustible")
ax.set_xlabel("Combustible")
ax.set_ylabel("Numero de ensayos")

fig.tight_layout()
fig.savefig(
    SALIDA / "flex_combustibles.png",
    dpi=300
)
plt.close(fig)

# Grafica de tiempo de combustion
datos = df.dropna(
    subset=["tiempo_combustion_s"]
)

fig, ax = plt.subplots(figsize=(10, 5))

if not datos.empty:
    ax.hist(
        datos["tiempo_combustion_s"],
        bins=20,
        edgecolor="black"
    )

    ax.set_title(
        "FLEX - Distribucion de tiempos de combustion"
    )
    ax.set_xlabel("Tiempo de combustion (s)")
    ax.set_ylabel("Frecuencia")

    fig.tight_layout()
    fig.savefig(
        SALIDA / "flex_tiempos.png",
        dpi=300
    )

plt.close(fig)

print("\nANALISIS FLEX FINALIZADO")
print("Resultados:", SALIDA)
