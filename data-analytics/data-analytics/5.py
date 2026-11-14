
# PHOENIX ORBIT - CODIGO 5
# Clasificacion y comparacion de SAFFIRE-I

from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

base = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

salida = base / "phoenix_data"
db = salida / "phoenix_fire.db"

with sqlite3.connect(db) as conn:
    df = pd.read_sql_query(
        "SELECT * FROM dataset_001",
        conn
    )

# Normalizar nombres
df.columns = df.columns.str.strip()

df = df.rename(columns={
    "Sample Number": "muestra",
    "Material": "material",
    "Sample Thickness (cm)": "espesor_cm",
    "Sample Length (cm)": "longitud_cm",
    "Sample Width (cm)": "ancho_cm",
    "Air Flow (cm/s)": "flujo_cm_s",
    "Percent O2": "oxigeno_pct",
    "Ignition Power (W)": "potencia_w",
    "Ignition Time (s)": "tiempo_ignicion_s",
    "Burn Time (s)": "tiempo_combustion_s",
    "Flow Direction": "direccion_flujo",
    "Camera 1": "camara_1",
    "Camera 2": "camara_2"
})

# Identificar muestras de ensayo S1 y S2
mascara = (
    df["muestra"]
    .astype(str)
    .str.fullmatch(r"S\d+", na=False)
)

ensayos = df.loc[mascara].copy()
auxiliares = df.loc[~mascara].copy()

# Convertir variables numéricas de las muestras
columnas_numericas = [
    "espesor_cm", "longitud_cm", "ancho_cm",
    "flujo_cm_s", "oxigeno_pct",
    "potencia_w", "tiempo_ignicion_s",
    "tiempo_combustion_s"
]

for columna in columnas_numericas:
    ensayos[columna] = pd.to_numeric(
        ensayos[columna], errors="coerce"
    )

# Guardar datos clasificados
ensayos.to_csv(
    salida / "saffire_ensayos.csv",
    index=False,
    encoding="utf-8-sig"
)

auxiliares.to_csv(
    salida / "saffire_registros_auxiliares.csv",
    index=False,
    encoding="utf-8-sig"
)

# Añadir tablas a la base SQLite
with sqlite3.connect(db) as conn:
    ensayos.to_sql(
        "saffire_ensayos",
        conn,
        if_exists="replace",
        index=False
    )
    auxiliares.to_sql(
        "saffire_auxiliares",
        conn,
        if_exists="replace",
        index=False
    )

print("ENSAYOS IDENTIFICADOS:", len(ensayos))
print("REGISTROS AUXILIARES:", len(auxiliares))

print("\nDATOS DE ENSAYOS:")
print(ensayos.to_string(index=False))

print("\nVALORES FALTANTES EN ENSAYOS:")
print(ensayos.isna().sum())

# Comparar duración de combustión
datos = ensayos.dropna(
    subset=["tiempo_combustion_s"]
)

if not datos.empty:
    fig, ax = plt.subplots(figsize=(9, 5))

    etiquetas = (
        datos["muestra"].astype(str)
        + " - "
        + datos["direccion_flujo"].astype(str)
    )

    ax.bar(
        etiquetas,
        datos["tiempo_combustion_s"]
    )

    ax.set_title(
        "SAFFIRE-I: Tiempo de combustion"
    )
    ax.set_ylabel("Tiempo (s)")
    ax.set_xlabel("Muestra y direccion del flujo")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(
        salida / "comparacion_saffire.png",
        dpi=300
    )
    plt.close(fig)

print("\nANALISIS FINALIZADO")
