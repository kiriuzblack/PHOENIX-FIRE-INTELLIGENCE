
# PHOENIX ORBIT - CODIGO 13
# Auditoria de calidad cientifica

from pathlib import Path
import sqlite3
import pandas as pd

BASE = Path(r"C:\Users\Yesid\Documents\Machine\guia2")
SALIDA = BASE / "phoenix_data"
DB = SALIDA / "phoenix_fire.db"

with sqlite3.connect(DB) as conn:
    flex = pd.read_sql_query(
        'SELECT * FROM "dataset_001"', conn
    )
    saffire2 = pd.read_sql_query(
        'SELECT * FROM "dataset_003"', conn
    )

# Normalizar nombres de columnas
flex.columns = flex.columns.str.strip()
saffire2.columns = saffire2.columns.str.strip()

print("=" * 55)
print("PHOENIX - AUDITORIA CIENTIFICA")
print("=" * 55)

# 1. Presiones reportadas
presion = pd.to_numeric(
    flex["Ambient pressure; mmHg"],
    errors="coerce"
)

anomalias = flex.loc[
    presion.isna() | (presion <= 0)
].copy()

print("\nREGISTROS CON PRESION NULA O INVALIDA:")
print("Cantidad:", len(anomalias))

columnas_auditoria = [
    "FLEX Test #",
    "FLEX Identifier",
    "Fuel",
    "Ambient pressure; mmHg",
    "Burn time; s",
    "Test end"
]

print(
    anomalias[columnas_auditoria].to_string(
        index=False
    )
)

anomalias.to_csv(
    SALIDA / "flex_presiones_revisar.csv",
    index=False,
    encoding="utf-8-sig"
)

# 2. Motivos de terminacion
print("\nRESULTADOS DE FINALIZACION FLEX:")
resultados = (
    flex["Test end"]
    .fillna("No documentado")
    .value_counts(dropna=False)
)

print(resultados.to_string())

resultados.rename_axis(
    "resultado"
).reset_index(
    name="cantidad"
).to_csv(
    SALIDA / "flex_tipos_finalizacion.csv",
    index=False,
    encoding="utf-8-sig"
)

# 3. Variables problematicas SAFFIRE-II
print("\nREVISION DE SAFFIRE-II:")

columnas = [
    "Sample Number",
    "Material",
    "Samle Thickness",
    "Percent O2 (Note 1)",
    "Burn Time (s)",
    "?-g Spread Length",
    "1-g Spread Rate"
]

print(
    saffire2[columnas].to_string(index=False)
)

saffire2[columnas].to_csv(
    SALIDA / "saffire2_revision_manual.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nAUDITORIA FINALIZADA")
print("Reportes guardados en:", SALIDA)
