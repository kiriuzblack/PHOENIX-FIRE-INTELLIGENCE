
# ==============================================
# PHOENIX ORBIT - CODIGO 25
# MATRIZ DE EVIDENCIA CIENTIFICA
# ==============================================

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

# 1. Cargar datos normalizados
with sqlite3.connect(DB) as conn:
    df = pd.read_sql_query(
        "SELECT * FROM nasa_unificado_validado",
        conn
    )

# 2. Leer incidencias documentadas
incidencias = pd.read_csv(
    ENTREGA / "validacion_automatica.csv",
    dtype={"ensayo": str}
)

# 3. Vincular cada incidencia con su ensayo
def construir_id(fila):
    experimento = str(fila["dataset"])
    ensayo = str(fila["ensayo"]).strip()

    if experimento == "FLEX":
        return f"FLEX-{ensayo}"

    return f"{experimento}-{ensayo}"

incidencias["id_ensayo"] = incidencias.apply(
    construir_id,
    axis=1
)

# 4. Resumir incidencias por ensayo
resumen_inc = incidencias.groupby("id_ensayo").agg(
    total_incidencias=("prioridad", "count"),
    incidencias_altas=(
        "prioridad",
        lambda x: (x == "Alta").sum()
    ),
    incidencias_medias=(
        "prioridad",
        lambda x: (x == "Media").sum()
    ),
    observaciones=(
        "descripcion",
        lambda x: "; ".join(x.astype(str))
    )
).reset_index()

# 5. Integrar evidencia e incidencias
matriz = df.merge(
    resumen_inc,
    on="id_ensayo",
    how="left",
    validate="one_to_one"
)

for columna in [
    "total_incidencias",
    "incidencias_altas",
    "incidencias_medias"
]:
    matriz[columna] = (
        matriz[columna].fillna(0).astype(int)
    )

matriz["observaciones"] = (
    matriz["observaciones"]
    .fillna("Sin incidencias detectadas por las reglas")
)

# 6. Calcular disponibilidad de variables
variables = [
    "material",
    "oxigeno_pct",
    "presion_kpa",
    "flujo_m_s",
    "tiempo_combustion_s"
]

matriz["variables_disponibles"] = (
    matriz[variables].notna().sum(axis=1)
)

# 7. Clasificar cobertura de datos
def cobertura(fila):
    cantidad = fila["variables_disponibles"]

    if cantidad >= 4:
        return "Amplia"
    elif cantidad >= 3:
        return "Intermedia"
    else:
        return "Limitada"

matriz["cobertura_datos"] = matriz.apply(
    cobertura,
    axis=1
)

# 8. Prioridad de revision
def prioridad(fila):

    if fila["incidencias_altas"] > 0:
        return "Alta"

    if fila["incidencias_medias"] > 0:
        return "Media"

    return "Ordinaria"

matriz["prioridad_revision"] = matriz.apply(
    prioridad,
    axis=1
)

# 9. Clasificacion de evidencia
def estado_evidencia(fila):

    if fila["incidencias_altas"] > 0:
        return "Requiere revision prioritaria"

    if fila["total_incidencias"] > 0:
        return "Requiere interpretacion"

    return "Sin incidencias detectadas"

matriz["clasificacion_evidencia"] = (
    matriz.apply(estado_evidencia, axis=1)
)

# No inferir peligro mediante estas reglas
matriz["nivel_peligro"] = "No determinado"

# 10. Campos del reporte
columnas_finales = [
    "id_ensayo",
    "experimento",
    "material",
    "oxigeno_pct",
    "presion_kpa",
    "flujo_m_s",
    "tiempo_combustion_s",
    "variables_disponibles",
    "cobertura_datos",
    "total_incidencias",
    "prioridad_revision",
    "clasificacion_evidencia",
    "observaciones",
    "nivel_peligro",
    "fuente_archivo"
]

resultado = matriz[columnas_finales].copy()

# 11. Guardar CSV y JSON
resultado.to_csv(
    ENTREGA / "matriz_evidencia.csv",
    index=False,
    encoding="utf-8-sig"
)

resultado.to_json(
    ENTREGA / "matriz_evidencia.json",
    orient="records",
    force_ascii=False,
    indent=2
)

# 12. Guardar SQLite sin alterar originales
with sqlite3.connect(DB) as conn:
    resultado.to_sql(
        "matriz_evidencia",
        conn,
        if_exists="replace",
        index=False
    )

# 13. Resumen de resultados
print("=" * 55)
print("PHOENIX - MATRIZ DE EVIDENCIA")
print("=" * 55)

print("\nTOTAL REGISTROS:", len(resultado))

print("\nCOBERTURA DE DATOS:")
print(
    resultado["cobertura_datos"].value_counts()
)

print("\nPRIORIDAD DE REVISION:")
print(
    resultado["prioridad_revision"].value_counts()
)

print("\nCLASIFICACION DE EVIDENCIA:")
print(
    resultado["clasificacion_evidencia"]
    .value_counts()
)

print("\nREGISTROS CON INCIDENCIAS:")
print(
    resultado[
        resultado["total_incidencias"] > 0
    ][
        ["id_ensayo", "total_incidencias",
         "prioridad_revision"]
    ].to_string(index=False)
)

print("\nMATRIZ GENERADA CORRECTAMENTE")
print("Carpeta:", ENTREGA)
