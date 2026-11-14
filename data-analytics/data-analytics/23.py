
# PHOENIX ORBIT - CODIGO 23
# VALIDACION AUTOMATIZADA DE DATASETS NASA

from pathlib import Path
import sqlite3
import json
import re
import pandas as pd

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

SALIDA = BASE / "phoenix_data"
ENTREGA = SALIDA / "entrega_analisis"
DB = SALIDA / "phoenix_fire.db"

ENTREGA.mkdir(parents=True, exist_ok=True)

# Obtener mapeo real de archivos y tablas
with open(
    SALIDA / "catalogo_datasets.json",
    encoding="utf-8"
) as f:
    catalogo = json.load(f)

mapa = {
    item["archivo"].lower(): item["tabla"]
    for item in catalogo
}

def buscar_tabla(nombre):
    for archivo, tabla in mapa.items():
        if nombre.lower() in archivo:
            return tabla
    raise ValueError(f"No se encontró: {nombre}")

# Seleccionar tablas por nombre del archivo
tabla_flex = buscar_tabla("PSI-69_Experimental")
tabla_s1 = buscar_tabla("PSI-98_Experimental")
tabla_s2 = buscar_tabla("PSI-99_Experimental")

with sqlite3.connect(DB) as conn:
    def leer(tabla):
        tabla_segura = tabla.replace('"', '""')
        df = pd.read_sql_query(
            f'SELECT * FROM "{tabla_segura}"',
            conn
        )
        df.columns = df.columns.str.strip()
        return df

    flex = leer(tabla_flex)
    s1 = leer(tabla_s1)
    s2 = leer(tabla_s2)

incidencias = []

def registrar(dataset, ensayo, variable,
             original, descripcion, prioridad):
    incidencias.append({
        "dataset": dataset,
        "ensayo": str(ensayo),
        "variable": variable,
        "valor_original": str(original),
        "descripcion": descripcion,
        "prioridad": prioridad,
        "estado": "Pendiente"
    })

# =========================================
# 1. VALIDAR FLEX
# =========================================

for _, fila in flex.iterrows():

    ensayo = fila["FLEX Test #"]

    presion = pd.to_numeric(
        fila["Ambient pressure; mmHg"],
        errors="coerce"
    )

    if pd.isna(presion) or presion <= 0:
        registrar(
            "FLEX", ensayo, "Presión",
            fila["Ambient pressure; mmHg"],
            "Presión ausente o no positiva",
            "Alta"
        )

    oxigeno = pd.to_numeric(
        fila[
            "O initial ambient composition; mole fraction"
        ],
        errors="coerce"
    )

    if pd.notna(oxigeno) and not (
        0 <= oxigeno <= 1
    ):
        registrar(
            "FLEX", ensayo, "Oxígeno",
            oxigeno,
            "Fracción molar fuera de 0 a 1",
            "Alta"
        )

    tiempo = pd.to_numeric(
        fila["Burn time; s"],
        errors="coerce"
    )

    if pd.notna(tiempo) and tiempo < 0:
        registrar(
            "FLEX", ensayo, "Tiempo",
            tiempo,
            "Duración negativa",
            "Alta"
        )

# =========================================
# 2. VALIDAR SAFFIRE-I
# =========================================

s1_ensayos = s1[
    s1["Sample Number"].astype(str)
    .str.fullmatch(r"S\d+")
].copy()

for _, fila in s1_ensayos.iterrows():

    ensayo = fila["Sample Number"]
    oxigeno = str(fila["Percent O2"]).strip()

    if "~" in oxigeno or "-" in oxigeno:
        registrar(
            "SAFFIRE-I", ensayo, "Oxígeno",
            oxigeno,
            "Dato aproximado o intervalo",
            "Media"
        )

    tiempo = pd.to_numeric(
        fila["Burn Time (s)"],
        errors="coerce"
    )

    if pd.notna(tiempo) and tiempo < 0:
        registrar(
            "SAFFIRE-I", ensayo,
            "Tiempo de combustión",
            tiempo,
            "Duración negativa",
            "Alta"
        )

# =========================================
# 3. VALIDAR SAFFIRE-II
# =========================================

s2_ensayos = s2[
    s2["Sample Number"].astype(str)
    .str.fullmatch(r"2-\d+")
].copy()

for _, fila in s2_ensayos.iterrows():

    ensayo = fila["Sample Number"]
    material = fila["Material"]

    if pd.isna(material) or str(material).strip().lower() in (
        "", "none", "nan"
    ):
        registrar(
            "SAFFIRE-II", ensayo,
            "Material", material,
            "Material sin identificar",
            "Alta"
        )

    espesor = str(fila["Samle Thickness"]).strip()

    if re.fullmatch(r"0\d{2,}\s*mm", espesor):
        registrar(
            "SAFFIRE-II", ensayo,
            "Espesor", espesor,
            "Formato numérico ambiguo",
            "Alta"
        )

    tiempo = str(fila["Burn Time (s)"]).strip()

    if tiempo.lower() == "insignificant":
        registrar(
            "SAFFIRE-II", ensayo,
            "Tiempo de combustión",
            tiempo,
            "Resultado cualitativo",
            "Media"
        )

# =========================================
# 4. REPORTE FINAL
# =========================================

reporte = pd.DataFrame(
    incidencias,
    columns=[
        "dataset", "ensayo", "variable",
        "valor_original", "descripcion",
        "prioridad", "estado"
    ]
)

reporte.to_csv(
    ENTREGA / "validacion_automatica.csv",
    index=False,
    encoding="utf-8-sig"
)

reporte.to_json(
    ENTREGA / "validacion_automatica.json",
    orient="records",
    force_ascii=False,
    indent=2
)

print("=" * 55)
print("PHOENIX - VALIDACION AUTOMATIZADA")
print("=" * 55)

print("\nRegistros originales:",
      len(flex) + len(s1) + len(s2))

print("Ensayos FLEX:", len(flex))
print("Ensayos SAFFIRE-I:", len(s1_ensayos))
print("Ensayos SAFFIRE-II:", len(s2_ensayos))

print("\nINCIDENCIAS DETECTADAS:")
print(len(reporte))

print("\nPOR DATASET:")
print(reporte.groupby("dataset").size())

print("\nPOR PRIORIDAD:")
print(reporte["prioridad"].value_counts())

print("\nDETALLE:")
print(reporte.to_string(index=False))

print("\nReportes guardados en:", ENTREGA)
print("\nVALIDACION TERMINADA")
