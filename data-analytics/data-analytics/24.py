
# ==========================================
# PHOENIX ORBIT - CODIGO 24
# INFORME CIENTIFICO CONSOLIDADO
# ==========================================

from pathlib import Path
import sqlite3
import pandas as pd

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

SALIDA = BASE / "phoenix_data"
ENTREGA = SALIDA / "entrega_analisis"
DB = SALIDA / "phoenix_fire.db"

ENTREGA.mkdir(parents=True, exist_ok=True)

# 1. Cargar las tablas que ya construimos
with sqlite3.connect(DB) as conn:

    datos = pd.read_sql_query(
        "SELECT * FROM nasa_unificado_validado",
        conn
    )

    saffire = pd.read_sql_query(
        "SELECT * FROM saffire_clasificado",
        conn
    )

# Cargar informe de validacion
anomalias = pd.read_csv(
    ENTREGA / "validacion_automatica.csv"
)

# 2. Preparar variables
for columna in [
    "oxigeno_pct",
    "presion_kpa",
    "tiempo_combustion_s"
]:
    datos[columna] = pd.to_numeric(
        datos[columna],
        errors="coerce"
    )

# 3. Distribucion de experimentos
distribucion = (
    datos["experimento"]
    .value_counts()
    .rename_axis("experimento")
    .reset_index(name="registros")
)

# 4. Analisis de FLEX
flex = datos[
    datos["experimento"] == "FLEX"
].copy()

resumen_flex = flex.groupby("material").agg(
    registros=("id_ensayo", "count"),
    tiempos_disponibles=(
        "tiempo_combustion_s", "count"
    ),
    tiempo_mediano_s=(
        "tiempo_combustion_s", "median"
    ),
    tiempo_promedio_s=(
        "tiempo_combustion_s", "mean"
    ),
    oxigeno_mediano_pct=(
        "oxigeno_pct", "median"
    )
).reset_index()

# 5. Analisis de SAFFIRE
resumen_saffire = saffire.groupby(
    ["experimento", "comportamiento_reportado"],
    dropna=False
).size().reset_index(name="registros")

# 6. Incidencias por prioridad
resumen_incidencias = anomalias.groupby(
    ["dataset", "prioridad"]
).size().reset_index(name="cantidad")

# 7. Guardar resultados
tablas = {
    "resumen_experimentos": distribucion,
    "resumen_flex": resumen_flex,
    "resumen_saffire": resumen_saffire,
    "resumen_incidencias": resumen_incidencias
}

for nombre, tabla in tablas.items():
    tabla.to_csv(
        ENTREGA / f"{nombre}.csv",
        index=False,
        encoding="utf-8-sig"
    )

# 8. Crear informe Markdown
informe = f"""
# PHOENIX DATA ANALYTICS
## Informe científico preliminar

Proyecto: PHOENIX FIRE INTELLIGENCE

Reto: Flame in Freefall - NASA Space Apps Challenge 2026

### 1. Objetivo
Organizar, validar y analizar información experimental
sobre combustión en microgravedad, conservando
la procedencia y las limitaciones de los datos.

### 2. Base de datos
Registros originales: 293

Registros integrados: {len(datos)}

Experimentos analizados: {datos['experimento'].nunique()}

### 3. Distribución de registros

{distribucion.to_string(index=False)}

### 4. Estadísticas FLEX

{resumen_flex.to_string(index=False)}

### 5. Resultados SAFFIRE

{resumen_saffire.to_string(index=False)}

### 6. Incidencias de calidad

{resumen_incidencias.to_string(index=False)}

Total de incidencias: {len(anomalias)}

### 7. Hallazgos preliminares

- FLEX contiene ensayos de metanol y heptano.
- Se observaron diferencias descriptivas en los
  tiempos de combustión entre ambos combustibles.
- Los análisis anteriores identificaron asociaciones
  entre oxígeno, diámetro y tiempo de combustión.
- SAFFIRE-I permite comparar dos condiciones
  de dirección del flujo.
- SAFFIRE-II contiene resultados cuantitativos
  y cualitativos sobre distintos materiales.

### 8. Limitaciones

- Existen valores faltantes y formatos ambiguos.
- Las condiciones de los experimentos difieren.
- Las correlaciones no prueban causalidad.
- Las duraciones de combustión no representan
  automáticamente niveles de peligro.
- Algunas incidencias requieren revisión manual.
- Las categorías de finalización experimental
  necesitan interpretación según documentación.

### 9. Conclusión

Los datos permiten desarrollar comparaciones
exploratorias y herramientas de visualización
para apoyar la interpretación científica.

Todavía no existe una clasificación validada
de peligrosidad basada en estos resultados.

### 10. Fuentes primarias

- PSI-69_Experimental table_FLEX.csv
- PSI-98_Experimental table_SAFFIRE-1.csv
- PSI-99_Experimental table_SAFFIRE-2.csv

Repositorio NASA PSI:
https://psi.nasa.gov/
"""

ruta_informe = (
    ENTREGA / "informe_cientifico_phoenix.md"
)

ruta_informe.write_text(
    informe,
    encoding="utf-8"
)

# 9. Mostrar resultados
print("=" * 55)
print("PHOENIX - INFORME CIENTIFICO")
print("=" * 55)

print("\nEXPERIMENTOS:")
print(distribucion.to_string(index=False))

print("\nFLEX:")
print(resumen_flex.to_string(index=False))

print("\nSAFFIRE:")
print(resumen_saffire.to_string(index=False))

print("\nINCIDENCIAS:")
print(resumen_incidencias.to_string(index=False))

print("\nInforme creado en:")
print(ruta_informe)

print("\nPROCESO FINALIZADO")
