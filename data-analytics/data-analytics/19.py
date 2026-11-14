
# PHOENIX ORBIT - CODIGO 19
# Comparador SAFFIRE-I y SAFFIRE-II

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

def numero_con_unidad(valor, unidad):
    if pd.isna(valor):
        return np.nan

    texto = str(valor).strip().replace(",", ".")

    patron = (
        r"~?\s*(\d+(?:\.\d+)?)\s*"
        + re.escape(unidad)
    )

    encontrado = re.fullmatch(
        patron, texto, flags=re.IGNORECASE
    )

    if not encontrado:
        return np.nan

    numero = encontrado.group(1)

    # Evitar espesores ambiguos como 037 mm
    if re.fullmatch(r"0\d{2,}", numero):
        return np.nan

    return float(numero)


def numero_simple(valor):
    if pd.isna(valor):
        return np.nan
    return pd.to_numeric(valor, errors="coerce")


def oxigeno_representativo(valor):
    if pd.isna(valor):
        return np.nan

    texto = str(valor).strip().replace(",", ".")
    numeros = re.findall(r"\d+(?:\.\d+)?", texto)

    if len(numeros) == 1:
        return float(numeros[0])

    if len(numeros) == 2:
        return (
            float(numeros[0]) + float(numeros[1])
        ) / 2

    return np.nan


with sqlite3.connect(DB) as conn:
    s1 = pd.read_sql_query(
        'SELECT * FROM "dataset_002"', conn
    )
    s2 = pd.read_sql_query(
        'SELECT * FROM "dataset_003"', conn
    )

s1.columns = s1.columns.str.strip()
s2.columns = s2.columns.str.strip()

# SAFFIRE-I: ensayos S1, S2...
s1 = s1[
    s1["Sample Number"].astype(str)
    .str.fullmatch(r"S\d+")
].copy()

# SAFFIRE-II: ensayos 2-1, 2-2...
s2 = s2[
    s2["Sample Number"].astype(str)
    .str.fullmatch(r"2-\d+")
].copy()

registros = []

# Normalizar SAFFIRE-I
for _, fila in s1.iterrows():
    registros.append({
        "experimento": "SAFFIRE-I",
        "muestra": fila["Sample Number"],
        "material": fila["Material"],
        "material_original": fila["Material"],
        "oxigeno_original": fila["Percent O2"],
        "oxigeno_estimado_pct": oxigeno_representativo(
            fila["Percent O2"]
        ),
        "flujo_m_s": (
            numero_simple(fila["Air Flow (cm/s)"])
            / 100
        ),
        "tiempo_combustion_s": numero_simple(
            fila["Burn Time (s)"]
        ),
        "tiempo_original": fila["Burn Time (s)"],
        "direccion_flujo": fila["Flow Direction"],
        "espesor_original": fila["Sample Thickness (cm)"],
        "espesor_mm": (
            numero_simple(fila["Sample Thickness (cm)"])
            * 10
        ),
        "propagacion_original": None,
        "propagacion_mm_s": np.nan,
        "fuente_archivo":
            "PSI-98_Experimental table_SAFFIRE-1.csv"
    })

# Normalizar SAFFIRE-II
for _, fila in s2.iterrows():
    registros.append({
        "experimento": "SAFFIRE-II",
        "muestra": fila["Sample Number"],
        "material": fila["Material"],
        "material_original": fila["Material"],
        "oxigeno_original": fila["Percent O2 (Note 1)"],
        "oxigeno_estimado_pct": oxigeno_representativo(
            fila["Percent O2 (Note 1)"]
        ),
        "flujo_m_s": numero_con_unidad(
            fila["Air Flow (cm/s)"], "cm/s"
        ) / 100,
        "tiempo_combustion_s": numero_con_unidad(
            fila["Burn Time (s)"], "s"
        ),
        "tiempo_original": fila["Burn Time (s)"],
        "direccion_flujo": fila["Flow Direction"],
        "espesor_original": fila["Samle Thickness"],
        "espesor_mm": numero_con_unidad(
            fila["Samle Thickness"], "mm"
        ),
        "propagacion_original": fila["?-g Spread Length"],
        "propagacion_mm_s": numero_con_unidad(
            fila["?-g Spread Length"], "mm/s"
        ),
        "fuente_archivo":
            "PSI-99_Experimental table_SAFFIRE-2.csv"
    })

df = pd.DataFrame(registros)

# Advertencia: la columna del CSV se denomina
# Spread Length, pero algunos valores tienen mm/s.
# No usarla como velocidad validada sin revisar
# el documento científico original.
df["propagacion_validada"] = False

df["requiere_revision"] = (
    df["material"].isna()
    | df["espesor_mm"].isna()
    | df["oxigeno_estimado_pct"].isna()
    | df["flujo_m_s"].isna()
)

# Conservar como texto el resultado experimental
df["nivel_peligro"] = "No determinado"

print("\nENSAYOS POR EXPERIMENTO")
print(df["experimento"].value_counts())

print("\nMATERIALES REGISTRADOS")
print(
    df.groupby(
        ["experimento", "material"],
        dropna=False
    ).size()
)

print("\nCOMPARACION GENERAL")
columnas = [
    "experimento", "muestra", "material",
    "oxigeno_estimado_pct", "flujo_m_s",
    "tiempo_combustion_s",
    "direccion_flujo"
]
print(df[columnas].to_string(index=False))

print("\nREGISTROS QUE REQUIEREN REVISION")
print(
    df.loc[
        df["requiere_revision"],
        ["experimento", "muestra", "material",
         "espesor_original", "oxigeno_original"]
    ].to_string(index=False)
)

# Exportar archivos
df.to_csv(
    SALIDA / "saffire_comparador.csv",
    index=False,
    encoding="utf-8-sig"
)

df.to_json(
    SALIDA / "saffire_comparador.json",
    orient="records",
    indent=2,
    force_ascii=False
)

with sqlite3.connect(DB) as conn:
    df.to_sql(
        "saffire_comparador",
        conn,
        if_exists="replace",
        index=False
    )

print("\nCOMPARADOR SAFFIRE FINALIZADO")
