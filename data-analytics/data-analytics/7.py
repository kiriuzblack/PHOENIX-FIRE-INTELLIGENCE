
# PHOENIX ORBIT - CODIGO 7
# Validacion de datos estandarizados

from pathlib import Path
import sqlite3
import pandas as pd

base = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

carpeta = base / "phoenix_data"
db = carpeta / "phoenix_fire.db"

with sqlite3.connect(db) as conexion:
    df = pd.read_sql_query(
        "SELECT * FROM ensayos_estandarizados",
        conexion
    )

print("=" * 50)
print("PHOENIX - VALIDACION DE DATOS")
print("=" * 50)

# Identificadores duplicados
duplicados = df["id_ensayo"].duplicated().sum()

print("\nIdentificadores duplicados:", duplicados)

# Convertir a numerico para comprobar valores
columnas = [
    "espesor_m",
    "longitud_m",
    "ancho_m",
    "flujo_m_s",
    "oxigeno_pct",
    "potencia_w",
    "tiempo_ignicion_s",
    "tiempo_combustion_s"
]

for columna in columnas:
    df[columna] = pd.to_numeric(
        df[columna], errors="coerce"
    )

# Verificar valores negativos
for columna in columnas:
    negativos = (df[columna] < 0).sum()
    print(f"{columna}: {negativos} negativos")

# Verificar rango fisico del oxigeno
oxigeno_invalido = (
    (df["oxigeno_pct"] < 0) |
    (df["oxigeno_pct"] > 100)
).sum()

print("\nOxigeno fuera de rango:", oxigeno_invalido)

# Resumen de integridad
reporte = pd.DataFrame({
    "variable": df.columns,
    "faltantes": df.isna().sum().values
})

reporte.to_csv(
    carpeta / "validacion_saffire.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nREPORTE DE FALTANTES")
print(reporte.to_string(index=False))

print("\nVALIDACION FINALIZADA")
