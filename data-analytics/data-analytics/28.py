
# =============================================
# PHOENIX ORBIT - CODIGO 28
# AUDITORIA DE ENSAYOS SAFFIRE-II RECUPERADOS
# =============================================

from pathlib import Path
import sqlite3
import json
import pandas as pd

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

SALIDA = BASE / "phoenix_data"
ENTREGA = SALIDA / "entrega_analisis"
DB = SALIDA / "phoenix_fire.db"

ENTREGA.mkdir(parents=True, exist_ok=True)

# 1. Localizar tabla original desde el catalogo
with open(
    SALIDA / "catalogo_datasets.json",
    encoding="utf-8"
) as f:
    catalogo = json.load(f)

coincidencias = [
    item["tabla"]
    for item in catalogo
    if "PSI-99_Experimental" in item["archivo"]
]

if len(coincidencias) != 1:
    raise ValueError(
        "No se pudo identificar de forma unica "
        "la tabla original de SAFFIRE-II."
    )

tabla_original = coincidencias[0]

# 2. Cargar datos originales y corregidos
with sqlite3.connect(DB) as conn:

    nombre_seguro = tabla_original.replace('"', '""')

    original = pd.read_sql_query(
        f'SELECT * FROM "{nombre_seguro}"',
        conn
    )

    corregido = pd.read_sql_query(
        "SELECT * FROM nasa_unificado_corregido",
        conn
    )

original.columns = original.columns.str.strip()

# 3. Seleccionar los nueve ensayos reales
if "Sample Number" not in original.columns:
    raise ValueError(
        "No se encontro la columna Sample Number"
    )

original["muestra"] = (
    original["Sample Number"]
    .astype(str)
    .str.strip()
)

ensayos = original[
    original["muestra"].str.fullmatch(r"2-[1-9]")
].copy()

# 4. Extraer ensayos de la tabla corregida
corregido_ii = corregido[
    corregido["experimento"] == "SAFFIRE-II"
].copy()

corregido_ii["muestra"] = (
    corregido_ii["id_ensayo"]
    .astype(str)
    .str.replace(
        "SAFFIRE-II-",
        "",
        regex=False
    )
)

# 5. Verificar correspondencia
originales_ids = set(ensayos["muestra"])
corregidos_ids = set(corregido_ii["muestra"])

print("=" * 60)
print("PHOENIX - AUDITORIA SAFFIRE-II")
print("=" * 60)

print("\nEnsayos originales:", len(ensayos))
print("Ensayos corregidos:", len(corregido_ii))

print("\nFALTANTES EN TABLA CORREGIDA:")
print(sorted(originales_ids - corregidos_ids))

print("\nSOBRANTES EN TABLA CORREGIDA:")
print(sorted(corregidos_ids - originales_ids))

# 6. Mostrar columnas de la fuente original
print("\nCOLUMNAS ORIGINALES:")
for columna in original.columns:
    if columna != "muestra":
        print("-", columna)

# 7. Revisar dos ensayos recuperados
for muestra in ["2-6", "2-9"]:

    print("\n" + "=" * 60)
    print("ENSAYO:", muestra)
    print("=" * 60)

    fila_original = ensayos[
        ensayos["muestra"] == muestra
    ]

    fila_corregida = corregido_ii[
        corregido_ii["muestra"] == muestra
    ]

    if len(fila_original) != 1:
        print("ERROR: fila original no unica")
        continue

    if len(fila_corregida) != 1:
        print("ERROR: fila corregida no unica")
        continue

    print("\nDATOS ORIGINALES NASA:")
    for columna, valor in (
        fila_original.iloc[0].items()
    ):
        if columna != "muestra":
            print(f"{columna}: {valor}")

    print("\nDATOS NORMALIZADOS:")
    for columna in [
        "id_ensayo",
        "material",
        "oxigeno_pct",
        "presion_kpa",
        "flujo_m_s",
        "tiempo_combustion_s",
        "fuente_archivo"
    ]:
        if columna in fila_corregida.columns:
            print(
                f"{columna}: "
                f"{fila_corregida.iloc[0][columna]}"
            )

# 8. Exportar comparacion completa
comparacion = ensayos.merge(
    corregido_ii,
    on="muestra",
    how="outer",
    indicator=True,
    validate="one_to_one",
    suffixes=("_original", "_normalizado")
)

comparacion.to_csv(
    ENTREGA / "auditoria_saffire_ii.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nESTADO DE CORRESPONDENCIA:")
print(comparacion["_merge"].value_counts())

print("\nArchivo generado:")
print(ENTREGA / "auditoria_saffire_ii.csv")

print("\nAUDITORIA FINALIZADA")
