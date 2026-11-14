
# PHOENIX ORBIT - CODIGO 14
# Auditoria de anomalías y calidad

from pathlib import Path
import sqlite3
import pandas as pd

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

SALIDA = BASE / "phoenix_data"
DB = SALIDA / "phoenix_fire.db"

incidencias = []

def registrar(dataset, ensayo, variable,
             valor, motivo, prioridad):
    incidencias.append({
        "dataset": dataset,
        "ensayo": str(ensayo),
        "variable": variable,
        "valor_original": str(valor),
        "motivo": motivo,
        "prioridad_revision": prioridad,
        "estado": "Pendiente de verificar"
    })

with sqlite3.connect(DB) as conn:
    flex = pd.read_sql_query(
        'SELECT * FROM "dataset_001"', conn
    )
    s1 = pd.read_sql_query(
        'SELECT * FROM "dataset_002"', conn
    )
    s2 = pd.read_sql_query(
        'SELECT * FROM "dataset_003"', conn
    )

# FLEX: presión nula o negativa
for _, fila in flex.iterrows():
    presion = pd.to_numeric(
        fila["Ambient pressure; mmHg"],
        errors="coerce"
    )

    if pd.isna(presion) or presion <= 0:
        registrar(
            "FLEX",
            fila["FLEX Test #"],
            "Presion ambiental",
            fila["Ambient pressure; mmHg"],
            "Presion faltante, nula o no positiva",
            "Alta"
        )

# SAFFIRE-I: oxígeno con intervalo o aproximación
for _, fila in s1.iterrows():
    muestra = str(fila["Sample Number "]).strip()

    if not muestra.startswith("S"):
        continue

    oxigeno = str(fila["Percent O2"])

    if "~" in oxigeno or "-" in oxigeno:
        registrar(
            "SAFFIRE-I",
            muestra,
            "Oxigeno",
            oxigeno,
            "Valor aproximado o intervalo",
            "Media"
        )

# SAFFIRE-II: revisar datos especiales
for _, fila in s2.iterrows():
    ensayo = str(fila["Sample Number"]).strip()

    # Solo códigos de ensayos 2-1, 2-2, etc.
    if not ensayo.startswith("2-"):
        continue

    material = fila["Material"]

    if (
        pd.isna(material)
        or str(material).strip().lower()
        in ["", "none", "nan"]
    ):
        registrar(
            "SAFFIRE-II",
            ensayo,
            "Material",
            material,
            "Material no identificado",
            "Alta"
        )

    espesor = str(fila["Samle Thickness "]).strip()

    if espesor == "037 mm":
        registrar(
            "SAFFIRE-II",
            ensayo,
            "Espesor",
            espesor,
            "Formato numerico ambiguo",
            "Alta"
        )

    tiempo = str(fila["Burn Time (s)"]).strip()

    if tiempo.lower() == "insignificant":
        registrar(
            "SAFFIRE-II",
            ensayo,
            "Tiempo de combustion",
            tiempo,
            "Resultado cualitativo; no es una duracion",
            "Media"
        )

# Crear reporte
reporte = pd.DataFrame(incidencias)

reporte.to_csv(
    SALIDA / "anomalias_nasa.csv",
    index=False,
    encoding="utf-8-sig"
)

reporte.to_json(
    SALIDA / "anomalias_nasa.json",
    orient="records",
    indent=2,
    force_ascii=False
)

with sqlite3.connect(DB) as conn:
    reporte.to_sql(
        "anomalias_nasa",
        conn,
        if_exists="replace",
        index=False
    )

print("\nPHOENIX - AUDITORIA DE ANOMALIAS")
print("Incidencias identificadas:", len(reporte))
print("\nResumen por experimento:")
print(reporte.groupby("dataset").size())

print("\nReporte detallado:")
print(reporte.to_string(index=False))

print("\nArchivos generados correctamente.")
