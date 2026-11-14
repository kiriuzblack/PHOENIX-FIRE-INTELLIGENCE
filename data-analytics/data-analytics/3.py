
from pathlib import Path
import pandas as pd
import sqlite3
import json

# ==========================================
# PHOENIX ORBIT - IMPORTACION DE DATOS NASA
# ==========================================

# 1. RUTA PRINCIPAL DEL PROYECTO
base = Path(r"C:\Users\Yesid\Documents\Machine\guia2")

# 2. CARPETAS DEL PROYECTO
entrada = base / "datos_nasa"
salida = base / "phoenix_data"

# Crear carpetas si no existen
entrada.mkdir(parents=True, exist_ok=True)
salida.mkdir(parents=True, exist_ok=True)

# 3. BASE DE DATOS SQLITE
db = salida / "phoenix_fire.db"

print("=" * 50)
print("PHOENIX ORBIT - NASA DATA ANALYTICS")
print("=" * 50)

print("\nCarpeta de entrada:", entrada)
print("Carpeta de salida:", salida)
print("Base de datos:", db)

# 4. BUSCAR ARCHIVOS CSV
archivos = sorted(
    archivo for archivo in entrada.rglob("*")
    if archivo.is_file()
    and archivo.suffix.lower() == ".csv"
)

if not archivos:
    print("\nNo se encontraron archivos CSV.")
    print("Coloca tus datasets NASA en:")
    print(entrada)
else:
    catalogo = []

    # 5. CONECTAR CON SQLITE
    with sqlite3.connect(db) as conexion:

        for i, archivo in enumerate(archivos, 1):

            print("\n" + "-" * 50)
            print("Procesando:", archivo.name)

            # 6. LEER DATASET
            try:
                df = pd.read_csv(archivo)

            except UnicodeDecodeError:
                df = pd.read_csv(
                    archivo,
                    encoding="latin-1"
                )

            except Exception as error:
                print("Error al leer:", error)
                continue

            # 7. CREAR TABLA
            tabla = f"dataset_{i:03d}"

            df.to_sql(
                tabla,
                conexion,
                if_exists="replace",
                index=False
            )

            # 8. ANALIZAR CALIDAD
            faltantes = df.isna().sum().to_dict()

            catalogo.append({
                "archivo": str(archivo.relative_to(entrada)),
                "tabla": tabla,
                "filas": len(df),
                "columnas": len(df.columns),
                "variables": df.columns.tolist(),
                "faltantes": faltantes
            })

            print("Tabla SQLite:", tabla)
            print("Registros:", len(df))
            print("Columnas:", len(df.columns))
            print("Variables:")
            print(df.columns.tolist())

    # 9. EXPORTAR CATALOGO JSON
    ruta_json = salida / "catalogo_datasets.json"

    with open(
        ruta_json,
        "w",
        encoding="utf-8"
    ) as archivo_json:

        json.dump(
            catalogo,
            archivo_json,
            ensure_ascii=False,
            indent=4
        )

    # 10. GENERAR REPORTE CSV
    reporte = pd.DataFrame([
        {
            "archivo": dato["archivo"],
            "tabla": dato["tabla"],
            "filas": dato["filas"],
            "columnas": dato["columnas"],
            "total_faltantes": sum(
                dato["faltantes"].values()
            )
        }
        for dato in catalogo
    ])

    reporte.to_csv(
        salida / "reporte_datasets.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 50)
    print("IMPORTACION FINALIZADA")
    print("Datasets importados:", len(catalogo))
    print("Resultados guardados en:", salida)
    print("=" * 50)
