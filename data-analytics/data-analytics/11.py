
# PHOENIX ORBIT - CODIGO 11
# Verificacion y correccion de SAFFIRE-I

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
import re

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

SALIDA = BASE / "phoenix_data"
DB = SALIDA / "phoenix_fire.db"

def procesar_oxigeno(valor):
    if pd.isna(valor):
        return np.nan, np.nan, np.nan, "faltante"

    texto = str(valor).replace(",", ".").strip()
    nums = re.findall(r"\d+(?:\.\d+)?", texto)
    nums = [float(x) for x in nums]

    if len(nums) == 2 and "-" in texto:
        bajo, alto = sorted(nums)
        return bajo, alto, (bajo + alto) / 2, "intervalo"

    if len(nums) == 1:
        tipo = "aproximado" if "~" in texto else "reportado"
        return nums[0], nums[0], nums[0], tipo

    return np.nan, np.nan, np.nan, "ambiguo"

with sqlite3.connect(DB) as conn:
    original = pd.read_sql_query(
        "SELECT * FROM dataset_002", conn
    )
    unificado = pd.read_sql_query(
        "SELECT * FROM nasa_unificado", conn
    )

original.columns = original.columns.str.strip()

original = original[
    original["Sample Number"]
    .astype(str)
    .str.fullmatch(r"S\d+")
].copy()

# Evitar problemas de indices
original = original.reset_index(drop=True)

for _, fila in original.iterrows():

    id_ensayo = "SAFFIRE-I-" + str(
        fila["Sample Number"]
    )

    mascara = unificado["id_ensayo"] == id_ensayo

    if mascara.sum() != 1:
        raise ValueError(
            f"Identificador ausente o duplicado: {id_ensayo}"
        )

    minimo, maximo, central, calidad = procesar_oxigeno(
        fila["Percent O2"]
    )

    unificado.loc[mascara, "oxigeno_min"] = minimo
    unificado.loc[mascara, "oxigeno_max"] = maximo
    unificado.loc[mascara, "oxigeno_pct"] = central

    unificado.loc[
        mascara, "calificador_oxigeno"
    ] = calidad

    unificado.loc[
        mascara, "oxigeno_original"
    ] = str(fila["Percent O2"])

    flujo = pd.to_numeric(
        fila["Air Flow (cm/s)"],
        errors="coerce"
    )

    unificado.loc[
        mascara, "flujo_m_s"
    ] = flujo / 100

# Revisar duplicados
if unificado["id_ensayo"].duplicated().any():
    raise ValueError("Existen identificadores duplicados")

# Resumen por experimento
resumen = unificado.groupby("experimento").agg(
    registros=("id_ensayo", "count"),
    oxigeno_disponible=("oxigeno_pct", "count"),
    presion_disponible=("presion_kpa", "count"),
    flujo_disponible=("flujo_m_s", "count"),
    combustion_disponible=("tiempo_combustion_s", "count")
)

print("\nPHOENIX - CALIDAD POR EXPERIMENTO")
print(resumen.to_string())

print("\nSAFFIRE-I CORREGIDO:")
columnas = [
    "id_ensayo",
    "oxigeno_original",
    "oxigeno_pct",
    "oxigeno_min",
    "oxigeno_max",
    "flujo_m_s"
]

print(
    unificado.loc[
        unificado["experimento"] == "SAFFIRE-I",
        columnas
    ].to_string(index=False)
)

# Exportar reporte
resumen.to_csv(
    SALIDA / "calidad_por_experimento.csv",
    encoding="utf-8-sig"
)

unificado.to_csv(
    SALIDA / "nasa_unificado_corregido.csv",
    index=False,
    encoding="utf-8-sig"
)

unificado.to_json(
    SALIDA / "nasa_unificado_corregido.json",
    orient="records",
    force_ascii=False,
    indent=2
)

# Guardar en nueva tabla; no borrar la anterior
with sqlite3.connect(DB) as conn:
    unificado.to_sql(
        "nasa_unificado_validado",
        conn,
        if_exists="replace",
        index=False
    )

print("\nVALIDACION COMPLETADA")
print("Nueva tabla: nasa_unificado_validado")
