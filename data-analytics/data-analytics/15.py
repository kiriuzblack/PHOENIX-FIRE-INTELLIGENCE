
# PHOENIX ORBIT - CODIGO 15
# ANALISIS ESTADISTICO FLEX

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

SALIDA = BASE / "phoenix_data"
DB = SALIDA / "phoenix_fire.db"

SALIDA.mkdir(parents=True, exist_ok=True)

# 1. Recuperar los datos normalizados y originales
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

# 2. Vincular las variables mediante ID de ensayo
original["id_ensayo"] = (
    "FLEX-" + original["FLEX Test #"].astype(str)
)

extra = original[
    [
        "id_ensayo",
        "Droplet initial diameter; mm",
        "Visible flame extinction diameter; mm",
        "Test end"
    ]
].copy()

df = df.merge(
    extra,
    on="id_ensayo",
    how="left",
    validate="one_to_one"
)

# 3. Convertir datos numéricos
def convertir_numero(serie):
    return pd.to_numeric(
        serie.astype("string").str.strip(),
        errors="coerce"
    )

df["diametro_inicial_mm"] = convertir_numero(
    df["Droplet initial diameter; mm"]
)

df["diametro_extincion_mm"] = convertir_numero(
    df["Visible flame extinction diameter; mm"]
)

for columna in [
    "oxigeno_pct",
    "presion_kpa",
    "tiempo_combustion_s"
]:
    df[columna] = pd.to_numeric(
        df[columna],
        errors="coerce"
    )

# 4. Marcar la anomalía de presión
df["presion_sospechosa"] = (
    df["presion_kpa"].notna()
    & (df["presion_kpa"] <= 0)
)

# Solo para análisis de presión
df["presion_analisis_kpa"] = (
    df["presion_kpa"].mask(
        df["presion_sospechosa"]
    )
)

# 5. Resumen estadístico por combustible
resumen = df.groupby("material").agg(
    total_ensayos=("id_ensayo", "count"),
    tiempos_validos=("tiempo_combustion_s", "count"),
    tiempo_mediano_s=("tiempo_combustion_s", "median"),
    tiempo_promedio_s=("tiempo_combustion_s", "mean"),
    oxigeno_mediano_pct=("oxigeno_pct", "median"),
    presion_mediana_kpa=("presion_analisis_kpa", "median"),
    diametros_validos=("diametro_inicial_mm", "count")
).reset_index()

print("\nRESUMEN FLEX POR COMBUSTIBLE")
print(resumen.to_string(index=False))

resumen.to_csv(
    SALIDA / "flex_estadisticas_avanzadas.csv",
    index=False,
    encoding="utf-8-sig"
)

# 6. Resultados de finalización
tabla_resultados = pd.crosstab(
    df["material"],
    df["Test end"]
)

print("\nFINALIZACION POR COMBUSTIBLE")
print(tabla_resultados.to_string())

tabla_resultados.to_csv(
    SALIDA / "flex_finalizacion_combustible.csv",
    encoding="utf-8-sig"
)

# 7. Gráfica: oxígeno y duración
datos = df.dropna(
    subset=["oxigeno_pct", "tiempo_combustion_s"]
)

fig, ax = plt.subplots(figsize=(9, 6))

for combustible, grupo in datos.groupby("material"):
    ax.scatter(
        grupo["oxigeno_pct"],
        grupo["tiempo_combustion_s"],
        label=combustible,
        alpha=0.65
    )

ax.set_xlabel("Oxígeno inicial (%)")
ax.set_ylabel("Tiempo de combustión (s)")
ax.set_title("FLEX: oxígeno y tiempo de combustión")
ax.legend()
ax.grid(alpha=0.25)

fig.tight_layout()
fig.savefig(
    SALIDA / "flex_oxigeno_tiempo.png",
    dpi=300
)
plt.close(fig)

# 8. Gráfica: diámetro inicial y duración
datos = df.dropna(
    subset=["diametro_inicial_mm", "tiempo_combustion_s"]
)

fig, ax = plt.subplots(figsize=(9, 6))

for combustible, grupo in datos.groupby("material"):
    ax.scatter(
        grupo["diametro_inicial_mm"],
        grupo["tiempo_combustion_s"],
        label=combustible,
        alpha=0.65
    )

ax.set_xlabel("Diámetro inicial (mm)")
ax.set_ylabel("Tiempo de combustión (s)")
ax.set_title("FLEX: diámetro inicial y duración")
ax.legend()
ax.grid(alpha=0.25)

fig.tight_layout()
fig.savefig(
    SALIDA / "flex_diametro_tiempo.png",
    dpi=300
)
plt.close(fig)

# 9. Correlaciones descriptivas por combustible
variables = [
    "oxigeno_pct",
    "presion_analisis_kpa",
    "diametro_inicial_mm",
    "tiempo_combustion_s"
]

print("\nCORRELACIONES POR COMBUSTIBLE")

for combustible, grupo in df.groupby("material"):
    print("\n", combustible)

    for x in variables[:-1]:
        pares = grupo[
            [x, "tiempo_combustion_s"]
        ].dropna()

        if (
            len(pares) >= 5
            and pares[x].nunique() > 1
            and pares["tiempo_combustion_s"].nunique() > 1
        ):
            r = pares[x].corr(
                pares["tiempo_combustion_s"],
                method="spearman"
            )

            print(
                f"{x}: n={len(pares)}, "
                f"Spearman={r:.3f}"
            )
        else:
            print(
                f"{x}: datos insuficientes "
                "o sin variabilidad"
            )

# 10. Guardar tabla analítica
df.to_csv(
    SALIDA / "flex_analisis_completo.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nANALISIS ESTADISTICO FINALIZADO")
print("Resultados:", SALIDA)
