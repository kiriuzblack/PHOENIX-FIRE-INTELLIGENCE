
# PHOENIX ORBIT - CODIGO 10
# Integracion cientifica de tres datasets NASA

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

SALIDA.mkdir(parents=True, exist_ok=True)

def numero(valor, unidad=None):
    """
    Extrae solo numeros interpretables.
    Acepta unidades explicitas y aproximaciones.
    No convierte intervalos en valores exactos.
    """
    if pd.isna(valor):
        return np.nan

    texto = str(valor).strip().replace(",", ".")

    if texto.lower() in ["none", "nan", "", "n/a"]:
        return np.nan

    patron = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"

    numeros = re.findall(patron, texto)

    if len(numeros) != 1:
        return np.nan

    # Conservar textos ambiguos como 037 mm
    if re.search(r"\b0\d{2,}\b", texto):
        return np.nan

    # Rechazar textos cualitativos
    if re.search(r"[a-zA-Z]", texto):
        if unidad is None:
            return np.nan

        limpio = re.sub(
            re.escape(unidad), "", texto,
            flags=re.IGNORECASE
        ).strip()

        if not re.fullmatch(
            r"[~≈]?\s*" + patron, limpio
        ):
            return np.nan

    return float(numeros[0])


def oxigeno_saffire(valor):
    """
    Devuelve:
    minimo, maximo, estimacion, calificador.
    """
    if pd.isna(valor):
        return np.nan, np.nan, np.nan, "faltante"

    texto = str(valor).strip().replace(",", ".")

    numeros = re.findall(r"\d+(?:\.\d+)?", texto)
    numeros = [float(x) for x in numeros]

    if len(numeros) == 2 and "-" in texto:
        menor, mayor = sorted(numeros)
        return (
            menor, mayor, (menor + mayor) / 2,
            "intervalo; punto medio calculado"
        )

    if len(numeros) == 1:
        tipo = (
            "aproximado" if "~" in texto or "≈" in texto
            else "reportado"
        )
        return (
            numeros[0], numeros[0],
            numeros[0], tipo
        )

    return np.nan, np.nan, np.nan, "no interpretable"


with sqlite3.connect(DB) as conn:
    flex = pd.read_sql_query(
        "SELECT * FROM dataset_001", conn
    )
    s1 = pd.read_sql_query(
        "SELECT * FROM dataset_002", conn
    )
    s2 = pd.read_sql_query(
        "SELECT * FROM dataset_003", conn
    )

# ==========================================
# FLEX
# ==========================================

flex.columns = flex.columns.str.strip()

tabla_flex = pd.DataFrame()

tabla_flex["id_ensayo"] = (
    "FLEX-" + flex["FLEX Test #"].astype(str)
)
tabla_flex["experimento"] = "FLEX"
tabla_flex["tipo_registro"] = "Ensayo experimental"
tabla_flex["material"] = flex["Fuel"]

tabla_flex["oxigeno_pct"] = (
    pd.to_numeric(
        flex[
            "O initial ambient composition; mole fraction"
        ],
        errors="coerce"
    ) * 100
)

tabla_flex["presion_kpa"] = (
    pd.to_numeric(
        flex["Ambient pressure; mmHg"],
        errors="coerce"
    ) * 0.133322368
)

tabla_flex["tiempo_combustion_s"] = (
    flex["Burn time; s"]
    .apply(lambda x: numero(x, "s"))
)

tabla_flex["flujo_m_s"] = np.nan

tabla_flex["resultado_original"] = flex["Test end"]
tabla_flex["fuente_archivo"] = (
    "PSI-69_Experimental table_FLEX.csv"
)

# ==========================================
# SAFFIRE-I
# ==========================================

s1.columns = s1.columns.str.strip()

s1 = s1[
    s1["Sample Number"]
    .astype(str)
    .str.fullmatch(r"S\d+")
].copy()

tabla_s1 = pd.DataFrame(index=s1.index)

tabla_s1["id_ensayo"] = (
    "SAFFIRE-I-" + s1["Sample Number"].astype(str)
)
tabla_s1["experimento"] = "SAFFIRE-I"
tabla_s1["tipo_registro"] = "Ensayo experimental"
tabla_s1["material"] = s1["Material"]

ox = s1["Percent O2"].apply(oxigeno_saffire)
ox = pd.DataFrame(
    ox.tolist(),
    index=s1.index,
    columns=[
        "oxigeno_min",
        "oxigeno_max",
        "oxigeno_pct",
        "calificador_oxigeno"
    ]
)

tabla_s1["oxigeno_pct"] = ox["oxigeno_pct"]
tabla_s1["oxigeno_min"] = ox["oxigeno_min"]
tabla_s1["oxigeno_max"] = ox["oxigeno_max"]
tabla_s1["calificador_oxigeno"] = (
    ox["calificador_oxigeno"]
)
tabla_s1["oxigeno_original"] = s1["Percent O2"]

tabla_s1["presion_kpa"] = np.nan

tabla_s1["flujo_m_s"] = (
    pd.to_numeric(
        s1["Air Flow (cm/s)"], errors="coerce"
    ) / 100
)

tabla_s1["tiempo_combustion_s"] = pd.to_numeric(
    s1["Burn Time (s)"], errors="coerce"
)

tabla_s1["resultado_original"] = s1["Flow Direction"]
tabla_s1["fuente_archivo"] = (
    "PSI-98_Experimental table_SAFFIRE-1.csv"
)

# ==========================================
# SAFFIRE-II
# ==========================================

s2.columns = s2.columns.str.strip()

# Registrar filas con información de ensayo
s2_validos = s2[
    s2["Material"].notna()
    & s2["Sample Number"].notna()
].copy()

tabla_s2 = pd.DataFrame(index=s2_validos.index)

tabla_s2["id_ensayo"] = (
    "SAFFIRE-II-"
    + s2_validos["Sample Number"].astype(str)
)

tabla_s2["experimento"] = "SAFFIRE-II"
tabla_s2["tipo_registro"] = "Ensayo experimental"
tabla_s2["material"] = s2_validos["Material"]

ox2 = s2_validos[
    "Percent O2 (Note 1)"
].apply(oxigeno_saffire)

ox2 = pd.DataFrame(
    ox2.tolist(),
    index=s2_validos.index,
    columns=[
        "oxigeno_min",
        "oxigeno_max",
        "oxigeno_pct",
        "calificador_oxigeno"
    ]
)

tabla_s2["oxigeno_pct"] = ox2["oxigeno_pct"]
tabla_s2["oxigeno_min"] = ox2["oxigeno_min"]
tabla_s2["oxigeno_max"] = ox2["oxigeno_max"]
tabla_s2["calificador_oxigeno"] = (
    ox2["calificador_oxigeno"]
)

tabla_s2["oxigeno_original"] = (
    s2_validos["Percent O2 (Note 1)"]
)

tabla_s2["presion_kpa"] = np.nan

tabla_s2["flujo_m_s"] = (
    s2_validos["Air Flow (cm/s)"]
    .apply(lambda x: numero(x, "cm/s")) / 100
)

tabla_s2["tiempo_combustion_s"] = (
    s2_validos["Burn Time (s)"]
    .apply(lambda x: numero(x, "s"))
)

tabla_s2["resultado_original"] = (
    s2_validos["1-g Spread Rate"]
)

tabla_s2["fuente_archivo"] = (
    "PSI-99_Experimental table_SAFFIRE-2.csv"
)

# ==========================================
# UNIFICACION
# ==========================================

unificado = pd.concat(
    [tabla_flex, tabla_s1, tabla_s2],
    ignore_index=True,
    sort=False
)

# Conservar solo datos fisicamente admisibles
# Los originales siguen intactos en SQLite.
for col in ["oxigeno_pct", "oxigeno_min", "oxigeno_max"]:
    invalido = (
        (unificado[col] < 0) |
        (unificado[col] > 100)
    )
    unificado.loc[invalido, col] = np.nan

# Registrar disponibilidad
unificado["nivel_peligro"] = "No determinado"
unificado["estado_evidencia"] = (
    "Dato derivado de tabla experimental"
)

# Guardar datos estructurados
unificado.to_csv(
    SALIDA / "nasa_unificado.csv",
    index=False,
    encoding="utf-8-sig"
)

unificado.to_json(
    SALIDA / "nasa_unificado.json",
    orient="records",
    indent=2,
    force_ascii=False
)

with sqlite3.connect(DB) as conn:
    unificado.to_sql(
        "nasa_unificado",
        conn,
        if_exists="replace",
        index=False
    )

print("\nPHOENIX - INTEGRACION COMPLETADA")
print("\nRegistros por experimento:")
print(unificado["experimento"].value_counts())

print("\nVariables disponibles:")
print(unificado.notna().sum())

print("\nDuplicados:")
print(unificado["id_ensayo"].duplicated().sum())

print("\nArchivos guardados en:", SALIDA)
