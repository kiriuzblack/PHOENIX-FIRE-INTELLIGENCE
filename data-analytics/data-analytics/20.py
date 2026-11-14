
# PHOENIX ORBIT - CODIGO 20
# Clasificacion del comportamiento de combustion

from pathlib import Path
import sqlite3
import pandas as pd

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

SALIDA = BASE / "phoenix_data"
DB = SALIDA / "phoenix_fire.db"

with sqlite3.connect(DB) as conn:
    df = pd.read_sql_query(
        "SELECT * FROM saffire_comparador",
        conn
    )

# Convertir duración numérica
df["tiempo_combustion_s"] = pd.to_numeric(
    df["tiempo_combustion_s"],
    errors="coerce"
)

# Clasificar disponibilidad del resultado
def clasificar_resultado(fila):
    valor = fila["tiempo_combustion_s"]
    texto = str(fila["tiempo_original"]).strip()

    if pd.notna(valor):
        return "Duracion cuantificada"

    if texto.lower() == "insignificant":
        return "Combustion insignificante reportada"

    return "Resultado sin clasificar"

df["comportamiento_reportado"] = df.apply(
    clasificar_resultado,
    axis=1
)

# Estado de confiabilidad para uso analítico
def evaluar_calidad(fila):
    if pd.isna(fila["material"]):
        return "Requiere verificar material"

    if pd.isna(fila["espesor_mm"]):
        return "Requiere verificar espesor"

    return "Variables basicas disponibles"

df["estado_calidad"] = df.apply(
    evaluar_calidad,
    axis=1
)

# Prioridad de revisión, no nivel de peligro
df["prioridad_revision"] = df[
    "estado_calidad"
].apply(
    lambda x: (
        "Alta" if x != "Variables basicas disponibles"
        else "Ordinaria"
    )
)

df["nivel_peligro"] = "No determinado"

# Información de procedencia
df["tipo_evidencia"] = "Tabla experimental NASA PSI"

# Guardar resultados
df.to_csv(
    SALIDA / "saffire_clasificado.csv",
    index=False,
    encoding="utf-8-sig"
)

df.to_json(
    SALIDA / "saffire_clasificado.json",
    orient="records",
    indent=2,
    force_ascii=False
)

with sqlite3.connect(DB) as conn:
    df.to_sql(
        "saffire_clasificado",
        conn,
        if_exists="replace",
        index=False
    )

print("\nPHOENIX - CLASIFICACION DE SAFFIRE")

print("\nCOMPORTAMIENTO REPORTADO:")
print(df["comportamiento_reportado"].value_counts())

print("\nCALIDAD DE LOS REGISTROS:")
print(df["estado_calidad"].value_counts())

print("\nRESULTADOS POR ENSAYO:")
print(
    df[
        [
            "experimento",
            "muestra",
            "material",
            "tiempo_combustion_s",
            "comportamiento_reportado",
            "estado_calidad",
            "nivel_peligro"
        ]
    ].to_string(index=False)
)

print("\nCLASIFICACION FINALIZADA")
