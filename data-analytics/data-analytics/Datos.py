
# PHOENIX DATA ANALYTICS v1.0
# Requisitos: pip install pandas matplotlib

from pathlib import Path
import json
import sqlite3
import pandas as pd

BASE = Path("phoenix_data")
BASE.mkdir(exist_ok=True)

# 1. Catálogo inicial de fuentes
fuentes = [
    {
        "id": "F001",
        "nombre": "NASA PSI",
        "tipo": "Repositorio científico",
        "url": "https://psi.nasa.gov/",
        "estado": "Consultar archivos individuales"
    },
    {
        "id": "F002",
        "nombre": "NASA Glenn - Combustion Science",
        "tipo": "Información científica",
        "url": "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/",
        "estado": "Página consultada"
    },
    {
        "id": "F003",
        "nombre": "Apollo 1",
        "tipo": "Investigación de accidente",
        "url": "https://sma.nasa.gov/sma-disciplines/accllp/apollo-1",
        "estado": "Página consultada"
    },
    {
        "id": "F004",
        "nombre": "Apollo 13",
        "tipo": "Investigación de incidente",
        "url": "https://sma.nasa.gov/sma-disciplines/accllp/apollo-13",
        "estado": "Página consultada"
    },
    {
        "id": "F005",
        "nombre": "Incendio de Mir",
        "tipo": "Incidente histórico",
        "url": "https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/",
        "estado": "Página consultada"
    },
    {
        "id": "F006",
        "nombre": "Researcher's Guide to Combustion",
        "tipo": "Guía científica",
        "url": "https://www.nasa.gov/missions/station/a-researchers-guide-to-combustion-science/",
        "estado": "Página consultada"
    },
    {
        "id": "F007",
        "nombre": "NASA Spinoff - Fireman's Air Tanks",
        "tipo": "Tecnología de protección",
        "url": "https://spinoff.nasa.gov/node/9582",
        "estado": "Página consultada"
    },
    {
        "id": "F008",
        "nombre": "Video NASA proporcionado",
        "tipo": "Material audiovisual",
        "url": "https://www.youtube.com/watch?v=W1oXykoz9zg",
        "estado": "Contenido pendiente de verificar"
    }
]

# 2. Catálogo de programas experimentales
# Las condiciones numéricas aún no se han extraído.
experimentos = [
    {
        "id": "EXP001",
        "programa": "BASS",
        "tipo_combustible": "Sólidos",
        "objetivo": "Combustión y extinción de sólidos",
        "oxigeno_pct": None,
        "presion_kpa": None,
        "flujo_m_s": None,
        "propagacion_mm_s": None,
        "nivel_peligro": "No determinado",
        "origen": "F002"
    },
    {
        "id": "EXP002",
        "programa": "FLEX",
        "tipo_combustible": "Líquidos",
        "objetivo": "Extinción de llamas de gotas",
        "oxigeno_pct": None,
        "presion_kpa": None,
        "flujo_m_s": None,
        "propagacion_mm_s": None,
        "nivel_peligro": "No determinado",
        "origen": "F002"
    },
    {
        "id": "EXP003",
        "programa": "SAFFIRE",
        "tipo_combustible": None,
        "objetivo": "Seguridad contra incendios espaciales",
        "oxigeno_pct": None,
        "presion_kpa": None,
        "flujo_m_s": None,
        "propagacion_mm_s": None,
        "nivel_peligro": "No determinado",
        "origen": "F002"
    }
]

# 3. Catálogo de incidentes reales
# Gravedad: clasificación retrospectiva propuesta
incidentes = [
    {
        "id": "INC001",
        "evento": "Apollo 1",
        "anio": 1967,
        "tipo": "Incendio de cabina en tierra",
        "fallecidos": 3,
        "danos": "Pérdida de la tripulación durante el incendio",
        "gravedad_propuesta": "Crítica",
        "origen": "F003"
    },
    {
        "id": "INC002",
        "evento": "Apollo 13",
        "anio": 1970,
        "tipo": "Explosión de tanque de oxígeno",
        "fallecidos": 0,
        "danos": "Pérdida de sistemas esenciales",
        "gravedad_propuesta": "Alta",
        "origen": "F004"
    },
    {
        "id": "INC003",
        "evento": "Mir",
        "anio": 1997,
        "tipo": "Incendio en sistema generador de oxígeno",
        "fallecidos": 0,
        "danos": "Humo y bloqueo temporal de una ruta de evacuación; sin daños estructurales",
        "gravedad_propuesta": "Alta",
        "origen": "F005"
    }
]

# 4. Crear tablas con Pandas
df_fuentes = pd.DataFrame(fuentes)
df_exp = pd.DataFrame(experimentos)
df_inc = pd.DataFrame(incidentes)

# 5. Crear SQLite
db_path = BASE / "phoenix_fire.db"

with sqlite3.connect(db_path) as conn:
    df_fuentes.to_sql(
        "fuentes", conn,
        if_exists="replace", index=False
    )
    df_exp.to_sql(
        "experimentos", conn,
        if_exists="replace", index=False
    )
    df_inc.to_sql(
        "incidentes", conn,
        if_exists="replace", index=False
    )

# 6. Exportar CSV y JSON
tablas = {
    "fuentes": df_fuentes,
    "experimentos": df_exp,
    "incidentes": df_inc
}

for nombre, df in tablas.items():
    df.to_csv(
        BASE / f"{nombre}.csv",
        index=False,
        encoding="utf-8-sig"
    )

    df.to_json(
        BASE / f"{nombre}.json",
        orient="records",
        force_ascii=False,
        indent=2
    )

# 7. Reporte de calidad
reporte = {
    "total_fuentes": len(df_fuentes),
    "programas_catalogados": len(df_exp),
    "incidentes_catalogados": len(df_inc),
    "faltantes_experimentos": (
        df_exp.isna().sum().to_dict()
    ),
    "nota": (
        "Los programas no contienen todavía "
        "mediciones numéricas verificadas."
    )
}

with open(
    BASE / "reporte_calidad.json",
    "w",
    encoding="utf-8"
) as archivo:
    json.dump(
        reporte, archivo,
        ensure_ascii=False,
        indent=2
    )

print("PHOENIX DATA ANALYTICS creado.")
print("Archivos en:", BASE.resolve())
print("\nValores faltantes:")
print(df_exp.isna().sum())
