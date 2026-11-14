
# =================================================
# PHOENIX ORBIT - CODIGO 29
# RECUPERACION DE OXIGENO EN SAFFIRE-II
# =================================================

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

# 1. Identificar el dataset original por archivo
with open(
    SALIDA / "catalogo_datasets.json",
    encoding="utf-8"
) as archivo:
    catalogo = json.load(archivo)

tablas = [
    item["tabla"]
    for item in catalogo
    if "PSI-99_Experimental" in item["archivo"]
]

if len(tablas) != 1:
    raise ValueError(
        "No se identifico un unico dataset SAFFIRE-II"
    )

tabla_segura = tablas[0].replace('"', '""')

with sqlite3.connect(DB) as conn:
    original = pd.read_sql_query(
        f'SELECT * FROM "{tabla_segura}"',
        conn
    )
    corregido = pd.read_sql_query(
        "SELECT * FROM nasa_unificado_corregido",
        conn
    )
    matriz = pd.read_sql_query(
        "SELECT * FROM matriz_evidencia_corregida",
        conn
    )

original.columns = original.columns.str.strip()

# 2. Seleccionar los nueve ensayos reales
original["muestra"] = (
    original["Sample Number"]
    .astype(str)
    .str.strip()
)

ensayos = original[
    original["muestra"].str.fullmatch(r"2-[1-9]")
].copy()

if len(ensayos) != 9:
    raise ValueError(
        "Se esperaban exactamente 9 ensayos originales"
    )

# 3. Analizar concentraciones de oxigeno
# Formatos admitidos:
#  ~ 22.1
#  22.0 to 21.9
#  21.5 - 21.7
#  22.1

NUM = r"\d+(?:[.,]\d+)?"

def analizar_oxigeno(valor):

    texto = str(valor).strip()
    limpio = texto.replace(",", ".")

    numeros = re.findall(NUM, limpio)

    resultado = {
        "oxigeno_texto_original": texto,
        "oxigeno_pct": None,
        "oxigeno_min_pct": None,
        "oxigeno_max_pct": None,
        "tipo_oxigeno": "No interpretable"
    }

    if pd.isna(valor) or texto.lower() in (
        "", "nan", "none"
    ):
        resultado["tipo_oxigeno"] = "Faltante"
        return resultado

    # Un intervalo debe tener exactamente dos valores
    if (
        len(numeros) == 2
        and re.search(r"\bto\b|[-–]", limpio)
    ):
        a, b = [float(x) for x in numeros]

        resultado.update({
            "oxigeno_pct": (a + b) / 2,
            "oxigeno_min_pct": min(a, b),
            "oxigeno_max_pct": max(a, b),
            "tipo_oxigeno": "Intervalo reportado"
        })

    elif len(numeros) == 1:
        valor_num = float(numeros[0])

        resultado.update({
            "oxigeno_pct": valor_num,
            "tipo_oxigeno": (
                "Aproximado"
                if "~" in limpio or "≈" in limpio
                else "Valor reportado"
            )
        })

    # No aceptar porcentajes fuera del rango fisico
    x = resultado["oxigeno_pct"]

    if x is not None and not (0 <= x <= 100):
        resultado.update({
            "oxigeno_pct": None,
            "oxigeno_min_pct": None,
            "oxigeno_max_pct": None,
            "tipo_oxigeno": "Fuera de rango"
        })

    return resultado

registros = []

for _, fila in ensayos.iterrows():

    muestra = fila["muestra"]

    registro = analizar_oxigeno(
        fila["Percent O2 (Note 1)"]
    )

    registro["id_ensayo"] = (
        f"SAFFIRE-II-{muestra}"
    )

    registros.append(registro)

oxigeno = pd.DataFrame(registros)

# 4. Exigir identificadores unicos
if oxigeno["id_ensayo"].duplicated().any():
    raise ValueError(
        "Identificadores duplicados en oxigeno"
    )

if (oxigeno["tipo_oxigeno"].isin(
    ["No interpretable", "Fuera de rango"]
)).any():
    raise ValueError(
        "Existen valores que requieren interpretacion manual"
    )

# 5. Construir nueva version de tablas
campos_nuevos = [
    "oxigeno_texto_original",
    "oxigeno_min_pct",
    "oxigeno_max_pct",
    "tipo_oxigeno"
]

for nombre, df in [
    ("unificado", corregido),
    ("matriz", matriz)
]:
    if df["id_ensayo"].duplicated().any():
        raise ValueError(
            f"IDs duplicados en {nombre}"
        )

def actualizar_tabla(df):

    # Evitar conflictos con campos anteriores
    base = df.drop(
        columns=campos_nuevos,
        errors="ignore"
    ).copy()

    base = base.merge(
        oxigeno,
        on="id_ensayo",
        how="left",
        validate="one_to_one",
        suffixes=("", "_original_nasa")
    )

    # Mantener oxigeno existente en FLEX/SAFFIRE-I
    # y usar el original para los 9 de SAFFIRE-II.
    es_ii = base["experimento"].eq("SAFFIRE-II")

    valores_recuperados = pd.to_numeric(
        base["oxigeno_pct_original_nasa"],
        errors="coerce"
    )

    base.loc[es_ii, "oxigeno_pct"] = (
        valores_recuperados.loc[es_ii].to_numpy()
    )

    base = base.drop(
        columns=["oxigeno_pct_original_nasa"]
    )

    return base

unificado_v2 = actualizar_tabla(corregido)
matriz_v2 = actualizar_tabla(matriz)

# 6. Recalcular cobertura en la matriz
variables = [
    "material",
    "oxigeno_pct",
    "presion_kpa",
    "flujo_m_s",
    "tiempo_combustion_s"
]

matriz_v2["variables_disponibles"] = (
    matriz_v2[variables]
    .notna()
    .sum(axis=1)
)

def cobertura(n):
    if n >= 4:
        return "Amplia"
    if n >= 3:
        return "Intermedia"
    return "Limitada"

matriz_v2["cobertura_datos"] = (
    matriz_v2["variables_disponibles"]
    .apply(cobertura)
)

# 7. Comprobaciones antes de escribir
esperados = {
    f"SAFFIRE-II-2-{i}"
    for i in range(1, 10)
}

for nombre, df in [
    ("unificado", unificado_v2),
    ("matriz", matriz_v2)
]:
    if len(df) != 285:
        raise ValueError(
            f"{nombre}: cantidad inesperada"
        )

    ids_ii = set(
        df.loc[
            df["experimento"] == "SAFFIRE-II",
            "id_ensayo"
        ]
    )

    if ids_ii != esperados:
        raise ValueError(
            f"{nombre}: ensayos incorrectos"
        )

    faltantes = df.loc[
        df["experimento"] == "SAFFIRE-II",
        "oxigeno_pct"
    ].isna().sum()

    if faltantes:
        raise ValueError(
            f"{nombre}: {faltantes} valores de oxigeno "
            "siguen sin interpretar"
        )

if matriz_v2["total_incidencias"].sum() != 12:
    raise ValueError(
        "Se perdieron incidencias de calidad"
    )

# 8. Guardar versiones nuevas
with sqlite3.connect(DB) as conn:

    unificado_v2.to_sql(
        "nasa_unificado_v2",
        conn,
        if_exists="replace",
        index=False
    )

    matriz_v2.to_sql(
        "matriz_evidencia_v2",
        conn,
        if_exists="replace",
        index=False
    )

oxigeno.to_csv(
    ENTREGA / "oxigeno_saffire_ii_validacion.csv",
    index=False,
    encoding="utf-8-sig"
)

matriz_v2.to_csv(
    ENTREGA / "matriz_evidencia_v2.csv",
    index=False,
    encoding="utf-8-sig"
)

# 9. Mostrar resumen
print("=" * 60)
print("PHOENIX - OXIGENO SAFFIRE-II")
print("=" * 60)

print("\nVALORES RECUPERADOS:")
print(
    oxigeno[
        [
            "id_ensayo",
            "oxigeno_texto_original",
            "oxigeno_pct",
            "oxigeno_min_pct",
            "oxigeno_max_pct",
            "tipo_oxigeno"
        ]
    ].to_string(index=False)
)

print("\nTIPOS DE MEDICION:")
print(oxigeno["tipo_oxigeno"].value_counts())

print("\nCOBERTURA ACTUALIZADA:")
print(matriz_v2["cobertura_datos"].value_counts())

print("\nINCIDENCIAS CONSERVADAS:")
print(int(matriz_v2["total_incidencias"].sum()))

print("\nTOTAL ENSAYOS:")
print(len(matriz_v2))

print("\nNORMALIZACION FINALIZADA")
