
# ==========================================
# PHOENIX ORBIT - CODIGO 22
# INVENTARIO Y TRAZABILIDAD DE DATOS NASA
# ==========================================

from pathlib import Path
import sqlite3
import pandas as pd
import json
import hashlib

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

ENTRADA = BASE / "datos_nasa"
SALIDA = BASE / "phoenix_data"
ENTREGA = SALIDA / "entrega_analisis"

DB = SALIDA / "phoenix_fire.db"
CATALOGO = SALIDA / "catalogo_datasets.json"

ENTREGA.mkdir(parents=True, exist_ok=True)

# 1. Comprobar archivos
if not DB.is_file():
    raise FileNotFoundError(
        f"No se encontro la base SQLite: {DB}"
    )

if not CATALOGO.is_file():
    raise FileNotFoundError(
        f"No se encontro el catalogo: {CATALOGO}"
    )

with open(CATALOGO, encoding="utf-8") as f:
    catalogo = json.load(f)

inventario = []
diccionario = []
pendientes = []

# 2. Leer todas las tablas originales
with sqlite3.connect(DB) as conn:

    tablas_existentes = {
        fila[0] for fila in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table'"
        )
    }

    for item in catalogo:

        tabla = item["tabla"]
        archivo = item["archivo"]

        if tabla not in tablas_existentes:
            pendientes.append({
                "tabla": tabla,
                "problema": "Tabla no encontrada"
            })
            continue

        tabla_sql = tabla.replace('"', '""')

        df = pd.read_sql_query(
            f'SELECT * FROM "{tabla_sql}"',
            conn
        )

        # 3. Identificar experimento
        columnas = set(df.columns.str.strip())

        if {
            "FLEX Test #",
            "Fuel",
            "Test end"
        }.issubset(columnas):
            experimento = "FLEX"

        elif {
            "Sample Number",
            "Percent O2"
        }.issubset(columnas):
            experimento = "SAFFIRE-I"

        elif {
            "Sample Number",
            "Percent O2 (Note 1)"
        }.issubset(columnas):
            experimento = "SAFFIRE-II"

        else:
            experimento = "No identificado"

        # 4. Verificar procedencia
        ruta_original = ENTRADA / archivo
        hash_archivo = None

        if ruta_original.is_file():
            contenido = ruta_original.read_bytes()

            hash_archivo = hashlib.sha256(
                contenido
            ).hexdigest()
        else:
            pendientes.append({
                "tabla": tabla,
                "problema": "CSV original no localizado"
            })

        # 5. Inventario general
        inventario.append({
            "experimento": experimento,
            "tabla": tabla,
            "archivo": archivo,
            "registros": len(df),
            "columnas": len(df.columns),
            "valores_faltantes": int(
                df.isna().sum().sum()
            ),
            "filas_duplicadas": int(
                df.duplicated().sum()
            ),
            "archivo_presente":
                ruta_original.is_file(),
            "sha256": hash_archivo
        })

        # 6. Diccionario de variables
        for columna in df.columns:

            diccionario.append({
                "experimento": experimento,
                "tabla": tabla,
                "variable_original": columna,
                "tipo_dato": str(
                    df[columna].dtype
                ),
                "valores_disponibles": int(
                    df[columna].notna().sum()
                ),
                "valores_faltantes": int(
                    df[columna].isna().sum()
                ),
                "porcentaje_faltante": round(
                    df[columna].isna().mean() * 100,
                    2
                ) if len(df) else None
            })

# 7. Exportar informes
df_inventario = pd.DataFrame(inventario)
df_diccionario = pd.DataFrame(diccionario)
df_pendientes = pd.DataFrame(
    pendientes,
    columns=["tabla", "problema"]
)

df_inventario.to_csv(
    ENTREGA / "inventario_trazable.csv",
    index=False,
    encoding="utf-8-sig"
)

df_diccionario.to_csv(
    ENTREGA / "diccionario_variables.csv",
    index=False,
    encoding="utf-8-sig"
)

df_pendientes.to_csv(
    ENTREGA / "pendientes_trazabilidad.csv",
    index=False,
    encoding="utf-8-sig"
)

# 8. Resultados generales
print("=" * 55)
print("PHOENIX - INVENTARIO CIENTIFICO")
print("=" * 55)

print("\nDATASETS IDENTIFICADOS:")
print(
    df_inventario[
        [
            "experimento",
            "registros",
            "columnas",
            "valores_faltantes",
            "filas_duplicadas",
            "archivo_presente"
        ]
    ].to_string(index=False)
)

print("\nTOTAL DE DATASETS:", len(df_inventario))
print(
    "TOTAL DE REGISTROS ORIGINALES:",
    df_inventario["registros"].sum()
)

print("\nPENDIENTES DE TRAZABILIDAD:")
print(df_pendientes.to_string(index=False))

print("\nREPORTES GUARDADOS EN:")
print(ENTREGA)

print("\nPROCESO FINALIZADO")
