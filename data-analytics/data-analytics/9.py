
# ==========================================
# PHOENIX ORBIT - CODIGO 9
# DIAGNOSTICO DE MULTIPLES DATASETS NASA
# ==========================================

from pathlib import Path
import sqlite3
import pandas as pd
import json

base = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

salida = base / "phoenix_data"

db = salida / "phoenix_fire.db"

# Leer catalogo de archivos originales
ruta_catalogo = salida / "catalogo_datasets.json"

with open(ruta_catalogo, "r", encoding="utf-8") as f:
    catalogo = json.load(f)

mapa_archivos = {
    item["tabla"]: item["archivo"]
    for item in catalogo
}

resultados = []

with sqlite3.connect(db) as conexion:

    for tabla in sorted(mapa_archivos):

        df = pd.read_sql_query(
            f'SELECT * FROM "{tabla}"',
            conexion
        )

        print("\n" + "=" * 65)
        print("DATASET:", tabla)
        print("ARCHIVO:", mapa_archivos[tabla])
        print("=" * 65)

        print("\nDIMENSIONES:")
        print("Filas:", len(df))
        print("Columnas:", len(df.columns))

        print("\nVARIABLES:")
        for columna in df.columns:
            print("-", columna)

        print("\nTIPOS DE DATOS:")
        print(df.dtypes.to_string())

        print("\nVALORES FALTANTES:")
        print(df.isna().sum().to_string())

        print("\nREGISTROS DUPLICADOS:")
        print(df.duplicated().sum())

        print("\nPRIMERAS 5 FILAS:")
        print(df.head(5).to_string(index=False))

        # Guardar resumen de cada dataset
        for columna in df.columns:
            resultados.append({
                "dataset": tabla,
                "archivo": mapa_archivos[tabla],
                "variable": columna,
                "tipo": str(df[columna].dtype),
                "filas": len(df),
                "faltantes": int(df[columna].isna().sum()),
                "porcentaje_faltante": round(
                    df[columna].isna().mean() * 100, 2
                ) if len(df) else 0
            })

# Generar informe consolidado
reporte = pd.DataFrame(resultados)

reporte.to_csv(
    salida / "diagnostico_general_nasa.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n" + "=" * 65)
print("DIAGNOSTICO GENERAL FINALIZADO")
print("Informe guardado en:")
print(salida / "diagnostico_general_nasa.csv")
print("=" * 65)
