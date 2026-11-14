
# PHOENIX ORBIT - CODIGO 8
# Inventario de multiples datasets NASA

from pathlib import Path
import sqlite3
import pandas as pd

base = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

salida = base / "phoenix_data"
db = salida / "phoenix_fire.db"

with sqlite3.connect(db) as conn:

    tablas = pd.read_sql_query(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """,
        conn
    )

    inventario = []

    for tabla in tablas["name"]:

        if not tabla.startswith("dataset_"):
            continue

        df = pd.read_sql_query(
            f'SELECT * FROM "{tabla}"',
            conn
        )

        inventario.append({
            "tabla": tabla,
            "registros": len(df),
            "columnas": len(df.columns),
            "variables": ", ".join(df.columns),
            "faltantes": int(df.isna().sum().sum())
        })

reporte = pd.DataFrame(inventario)

if reporte.empty:
    print("No hay datasets experimentales importados.")
else:
    print("\nINVENTARIO DE DATASETS NASA")
    print(
        reporte[
            ["tabla", "registros", "columnas", "faltantes"]
        ].to_string(index=False)
    )

    reporte.to_csv(
        salida / "inventario_datasets.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\nInventario guardado correctamente.")
