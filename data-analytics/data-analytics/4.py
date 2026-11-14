
# PHOENIX ORBIT - CODIGO 4
# Analisis experimental SAFFIRE-I

from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

base = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

carpeta = base / "phoenix_data"
db = carpeta / "phoenix_fire.db"

# 1. LEER DATOS REALES
with sqlite3.connect(db) as conexion:
    df = pd.read_sql_query(
        "SELECT * FROM dataset_001",
        conexion
    )

# 2. NORMALIZAR NOMBRES
columnas = {
    "Sample Number ": "muestra",
    "Material": "material",
    "Sample Thickness (cm)": "espesor_cm",
    "Sample Length (cm)": "longitud_cm",
    "Sample Width (cm)": "ancho_cm",
    "Air Flow (cm/s)": "flujo_cm_s",
    "Percent O2": "oxigeno_pct",
    "Ignition Power (W)": "potencia_w",
    "Ignition Time (s)": "tiempo_ignicion_s",
    "Burn Time (s)": "tiempo_combustion_s",
    "Flow Direction ": "direccion_flujo",
    "Camera 1": "camara_1",
    "Camera 2": "camara_2"
}

df = df.rename(columns=columnas)

# 3. CONVERTIR VARIABLES NUMERICAS
numericas = [
    "espesor_cm",
    "longitud_cm",
    "ancho_cm",
    "flujo_cm_s",
    "oxigeno_pct",
    "potencia_w",
    "tiempo_ignicion_s",
    "tiempo_combustion_s"
]

for columna in numericas:
    df[columna] = pd.to_numeric(
        df[columna],
        errors="coerce"
    )

# 4. MOSTRAR DATOS
print("\nDATOS SAFFIRE-I")
print(df.to_string(index=False))

# 5. ESTADISTICAS DESCRIPTIVAS
print("\nESTADISTICAS")
print(df[numericas].describe().to_string())

# 6. DETECTAR VALORES FALTANTES
print("\nVALORES FALTANTES")
print(df.isna().sum())

# 7. GUARDAR DATOS LIMPIOS
df.to_csv(
    carpeta / "saffire_1_limpio.csv",
    index=False,
    encoding="utf-8-sig"
)

# 8. GRAFICA DE OXIGENO Y COMBUSTION
datos = df.dropna(
    subset=["oxigeno_pct", "tiempo_combustion_s"]
)

if not datos.empty:

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.scatter(
        datos["oxigeno_pct"],
        datos["tiempo_combustion_s"],
        s=90
    )

    ax.set_xlabel("Oxigeno (%)")
    ax.set_ylabel("Tiempo de combustion (s)")
    ax.set_title(
        "SAFFIRE-I: Oxigeno vs tiempo de combustion"
    )

    ax.grid(alpha=0.3)

    fig.tight_layout()

    fig.savefig(
        carpeta / "saffire_oxigeno_combustion.png",
        dpi=300
    )

    plt.close(fig)

# 9. GRAFICA DE FLUJO Y COMBUSTION
datos = df.dropna(
    subset=["flujo_cm_s", "tiempo_combustion_s"]
)

if not datos.empty:

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.scatter(
        datos["flujo_cm_s"],
        datos["tiempo_combustion_s"],
        s=90
    )

    ax.set_xlabel("Flujo de aire (cm/s)")
    ax.set_ylabel("Tiempo de combustion (s)")
    ax.set_title(
        "SAFFIRE-I: Flujo vs tiempo de combustion"
    )

    ax.grid(alpha=0.3)
    fig.tight_layout()

    fig.savefig(
        carpeta / "saffire_flujo_combustion.png",
        dpi=300
    )

    plt.close(fig)

print("\nANALISIS TERMINADO")
print("Resultados guardados en:", carpeta)
