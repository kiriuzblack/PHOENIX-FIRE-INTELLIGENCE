
# ==================================================
# PHOENIX ORBIT - CODIGO 31
# AUDITORIA FINAL E INFORME CIENTIFICO V2
# ==================================================

from pathlib import Path
from collections import Counter
from datetime import datetime
import sqlite3
import json
import pandas as pd

# --------------------------------------------------
# 1. RUTAS
# --------------------------------------------------

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

SALIDA = BASE / "phoenix_data"
ENTREGA = SALIDA / "entrega_analisis"
DB = SALIDA / "phoenix_fire.db"

CSV_INCIDENCIAS = (
    ENTREGA / "validacion_automatica.csv"
)

ENTREGA.mkdir(parents=True, exist_ok=True)

if not DB.is_file():
    raise FileNotFoundError(DB)

if not CSV_INCIDENCIAS.is_file():
    raise FileNotFoundError(CSV_INCIDENCIAS)

# --------------------------------------------------
# 2. CARGAR TABLAS CORREGIDAS
# --------------------------------------------------

with sqlite3.connect(DB) as conn:

    datos = pd.read_sql_query(
        "SELECT * FROM nasa_unificado_v2",
        conn
    )

    matriz = pd.read_sql_query(
        "SELECT * FROM matriz_evidencia_v2",
        conn
    )

    saffire = pd.read_sql_query(
        "SELECT * FROM saffire_clasificado",
        conn
    )

incidencias = pd.read_csv(
    CSV_INCIDENCIAS,
    dtype={"ensayo": str}
)

# --------------------------------------------------
# 3. VERIFICACIONES DE INTEGRIDAD
# --------------------------------------------------

errores = []

def verificar(condicion, mensaje):
    if not condicion:
        errores.append(mensaje)

verificar(
    len(datos) == 285,
    "La tabla integrada no contiene 285 registros"
)

verificar(
    len(matriz) == 285,
    "La matriz no contiene 285 registros"
)

verificar(
    datos["id_ensayo"].notna().all()
    and datos["id_ensayo"].is_unique,
    "IDs nulos o duplicados en datos"
)

verificar(
    matriz["id_ensayo"].notna().all()
    and matriz["id_ensayo"].is_unique,
    "IDs nulos o duplicados en matriz"
)

verificar(
    set(datos["id_ensayo"]) ==
    set(matriz["id_ensayo"]),
    "Los identificadores no coinciden"
)

conteo = datos["experimento"].value_counts()

esperados = {
    "FLEX": 274,
    "SAFFIRE-I": 2,
    "SAFFIRE-II": 9
}

verificar(
    conteo.to_dict() == esperados,
    "Distribucion de experimentos incorrecta"
)

ids_saffire_ii = {
    f"SAFFIRE-II-2-{i}" for i in range(1, 10)
}

ids_ii_reales = set(
    datos.loc[
        datos["experimento"] == "SAFFIRE-II",
        "id_ensayo"
    ]
)

verificar(
    ids_ii_reales == ids_saffire_ii,
    "Ensayos SAFFIRE-II incompletos o incorrectos"
)

# Verificar correspondencia con clasificacion
saffire_ids = (
    saffire["experimento"].astype(str)
    + "-"
    + saffire["muestra"].astype(str).str.strip()
)

verificar(
    len(saffire) == 11
    and saffire_ids.is_unique,
    "Clasificacion SAFFIRE incompleta o duplicada"
)

ids_saffire_datos = set(
    datos.loc[
        datos["experimento"].isin(
            ["SAFFIRE-I", "SAFFIRE-II"]
        ),
        "id_ensayo"
    ]
)

verificar(
    set(saffire_ids) == ids_saffire_datos,
    "Clasificacion SAFFIRE y tabla integrada difieren"
)

# --------------------------------------------------
# 4. VERIFICAR INCIDENCIAS UNA POR UNA
# --------------------------------------------------

incidencias["id_ensayo"] = (
    incidencias["dataset"].astype(str).str.strip()
    + "-"
    + incidencias["ensayo"].astype(str).str.strip()
)

recuento_original = Counter(
    incidencias["id_ensayo"]
)

recuento_matriz = {
    str(fila["id_ensayo"]): int(
        fila["total_incidencias"]
    )
    for _, fila in matriz.iterrows()
}

verificar(
    len(incidencias) == 12,
    "El reporte original no tiene 12 incidencias"
)

verificar(
    int(matriz["total_incidencias"].sum()) == 12,
    "La matriz no conserva 12 incidencias"
)

verificar(
    all(
        recuento_matriz.get(id_, -1) == cantidad
        for id_, cantidad in recuento_original.items()
    ),
    "Hay incidencias mal vinculadas"
)

verificar(
    sum(
        valor > 0
        for valor in recuento_matriz.values()
    ) == 10,
    "Numero inesperado de ensayos con incidencias"
)

# --------------------------------------------------
# 5. VERIFICAR VALORES DE OXIGENO SAFFIRE-II
# --------------------------------------------------

ii = datos.loc[
    datos["experimento"] == "SAFFIRE-II"
].copy()

ii["oxigeno_pct"] = pd.to_numeric(
    ii["oxigeno_pct"],
    errors="coerce"
)

verificar(
    ii["oxigeno_pct"].notna().sum() == 9,
    "Faltan valores de oxigeno SAFFIRE-II"
)

esperado_oxigeno = {
    "SAFFIRE-II-2-6": 22.10,
    "SAFFIRE-II-2-8": 22.05,
    "SAFFIRE-II-2-9": 21.95
}

for identificador, esperado in esperado_oxigeno.items():

    coincidencia = ii.loc[
        ii["id_ensayo"] == identificador,
        "oxigeno_pct"
    ]

    verificar(
        len(coincidencia) == 1
        and pd.notna(coincidencia.iloc[0])
        and abs(coincidencia.iloc[0] - esperado)
        < 0.000001,
        f"Oxigeno incorrecto: {identificador}"
    )

for identificador, minimo, maximo in [
    ("SAFFIRE-II-2-8", 22.0, 22.1),
    ("SAFFIRE-II-2-9", 21.9, 22.0)
]:

    fila = ii.loc[
        ii["id_ensayo"] == identificador
    ]

    if len(fila) == 1:
        f = fila.iloc[0]

        verificar(
            pd.notna(f["oxigeno_min_pct"])
            and pd.notna(f["oxigeno_max_pct"])
            and abs(f["oxigeno_min_pct"] - minimo)
            < 0.000001
            and abs(f["oxigeno_max_pct"] - maximo)
            < 0.000001,
            f"Intervalo incorrecto: {identificador}"
        )

# --------------------------------------------------
# 6. COMPROBAR CONSISTENCIA ENTRE TABLAS
# --------------------------------------------------

comparar = datos[
    [
        "id_ensayo",
        "oxigeno_pct",
        "tiempo_combustion_s"
    ]
].merge(
    matriz[
        [
            "id_ensayo",
            "oxigeno_pct",
            "tiempo_combustion_s"
        ]
    ],
    on="id_ensayo",
    how="outer",
    validate="one_to_one",
    indicator=True,
    suffixes=("_datos", "_matriz")
)

verificar(
    comparar["_merge"].eq("both").all(),
    "Existen registros presentes solo en una tabla"
)

for variable in [
    "oxigeno_pct",
    "tiempo_combustion_s"
]:
    a = pd.to_numeric(
        comparar[f"{variable}_datos"],
        errors="coerce"
    )
    b = pd.to_numeric(
        comparar[f"{variable}_matriz"],
        errors="coerce"
    )

    iguales = (
        (a.isna() & b.isna())
        | (
            a.notna()
            & b.notna()
            & ((a - b).abs() < 0.000001)
        )
    )

    verificar(
        iguales.all(),
        f"Inconsistencia entre tablas: {variable}"
    )

# --------------------------------------------------
# 7. DETENERSE SI HAY ERRORES
# --------------------------------------------------

print("=" * 60)
print("PHOENIX - AUDITORIA CIENTIFICA FINAL")
print("=" * 60)

if errores:

    print("\nESTADO: REQUIERE CORRECCION")

    for error in errores:
        print("ERROR:", error)

    print(
        "\nNo se reemplazo el informe cientifico."
    )
    raise SystemExit(1)

print("\nESTADO: COMPROBACIONES SUPERADAS")
print("Ensayos integrados:", len(datos))
print("Incidencias vinculadas:", len(incidencias))
print("Ensayos con incidencias:", len(recuento_original))

# --------------------------------------------------
# 8. RESUMEN CIENTIFICO FLEX
# --------------------------------------------------

flex = datos.loc[
    datos["experimento"] == "FLEX"
].copy()

for variable in [
    "tiempo_combustion_s",
    "oxigeno_pct",
    "presion_kpa"
]:
    flex[variable] = pd.to_numeric(
        flex[variable],
        errors="coerce"
    )

resumen_flex = (
    flex.groupby("material", dropna=False)
    .agg(
        ensayos=("id_ensayo", "count"),
        duraciones_disponibles=(
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
    )
    .reset_index()
)

# --------------------------------------------------
# 9. RESUMEN CIENTIFICO SAFFIRE
# --------------------------------------------------

resumen_saffire = (
    saffire.groupby(
        ["experimento", "comportamiento_reportado"],
        dropna=False
    )
    .size()
    .reset_index(name="ensayos")
)

# --------------------------------------------------
# 10. ESTADO DE CALIDAD
# --------------------------------------------------

resumen_calidad = (
    matriz.groupby("prioridad_revision")
    .size()
    .reset_index(name="ensayos")
)

resumen_incidencias = (
    incidencias.groupby(
        ["dataset", "prioridad"]
    )
    .size()
    .reset_index(name="incidencias")
)

# --------------------------------------------------
# 11. GUARDAR TABLAS ACTUALIZADAS
# --------------------------------------------------

tablas = {
    "resumen_flex_v2": resumen_flex,
    "resumen_saffire_v2": resumen_saffire,
    "resumen_calidad_v2": resumen_calidad,
    "resumen_incidencias_v2": resumen_incidencias
}

for nombre, df in tablas.items():

    df.to_csv(
        ENTREGA / f"{nombre}.csv",
        index=False,
        encoding="utf-8-sig"
    )

# --------------------------------------------------
# 12. INFORME CIENTIFICO ACTUALIZADO
# --------------------------------------------------

fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

informe = f"""
# PHOENIX DATA ANALYTICS
## Informe científico preliminar — versión 2

**Proyecto:** PHOENIX FIRE INTELLIGENCE

**Equipo:** PHOENIX Orbit

**Reto:** Flame in Freefall

**Fecha de generación:** {fecha}

### 1. Objetivo

Organizar y analizar datos experimentales de combustión
en microgravedad para facilitar su exploración y uso
en una plataforma de inteligencia científica.

### 2. Procedencia de datos

Archivos de trabajo:

- PSI-69_Experimental table_FLEX.csv
- PSI-98_Experimental table_SAFFIRE-1.csv
- PSI-99_Experimental table_SAFFIRE-2.csv

Se procesaron 293 filas originales, incluyendo
registros auxiliares y notas.

La selección experimental contiene 285 ensayos:

- FLEX: 274
- SAFFIRE-I: 2
- SAFFIRE-II: 9

Las tablas de referencia de esta versión son
`nasa_unificado_v2` y `matriz_evidencia_v2`.

### 3. Resultados descriptivos FLEX

{resumen_flex.round(3).to_string(index=False)}

Las duraciones de combustión observadas difieren
entre metanol y heptano.

Estas diferencias son descriptivas: no implican
que un material sea universalmente más peligroso.

### 4. Resultados descriptivos SAFFIRE

{resumen_saffire.to_string(index=False)}

Los resultados cualitativos como
"Insignificant" se preservan como tales.

La duración no debe confundirse con la velocidad
de propagación del fuego ni con la peligrosidad.

### 5. Oxígeno SAFFIRE-II

Los nueve ensayos tienen un valor representativo
de oxígeno procedente de la fuente original.

Siete se reportan de forma aproximada y dos
como intervalos.

En los intervalos, el valor representativo
es el punto medio y no una medición exacta.

### 6. Auditoría de calidad

{resumen_calidad.to_string(index=False)}

Incidencias documentadas:

{resumen_incidencias.to_string(index=False)}

Se conservaron 12 incidencias vinculadas
a 10 ensayos.

Las prioridades identifican necesidad de revisión
de datos, no niveles de peligro.

### 7. Limitaciones científicas

- La matriz utiliza reglas preliminares de calidad.
- Existen materiales no identificados en SAFFIRE-II.
- Algunos espesores presentan formato ambiguo.
- Las columnas de propagación requieren comprobar
  sus unidades en la documentación original.
- FLEX y SAFFIRE estudian sistemas físicos distintos.
- Las asociaciones estadísticas no demuestran causalidad.
- Los datos sin incidencias detectadas no equivalen
  a datos científicamente validados.
- La clasificación de peligrosidad sigue pendiente.

### 8. Conclusión

El proyecto dispone de 285 ensayos integrados,
una matriz trazable de incidencias y un dashboard
para exploración de datos.

Las comprobaciones automáticas de integridad de
esta versión se superaron.

Los resultados constituyen un análisis exploratorio.
Su interpretación debe conservar las condiciones
experimentales, incertidumbres y limitaciones.

### 9. Pendientes para validación documental

1. Verificar espesores ambiguos de SAFFIRE-II.
2. Investigar los materiales no identificados.
3. Revisar las unidades de propagación reportadas.
4. Documentar los criterios de comparación
   entre ensayos y experimentos.
5. Revisar la presión no positiva del ensayo
   FLEX 114 sin sustituir el dato original.

### 10. Referencia institucional

NASA Physical Sciences Informatics (PSI)

https://psi.nasa.gov/
"""

archivo_informe = (
    ENTREGA / "informe_cientifico_phoenix_v2.md"
)

archivo_informe.write_text(
    informe.strip() + "\n",
    encoding="utf-8"
)

# --------------------------------------------------
# 13. CREAR REPORTE AUTOMATICO JSON
# --------------------------------------------------

reporte = {
    "proyecto": "PHOENIX FIRE INTELLIGENCE",
    "version": "2",
    "fecha": fecha,
    "ensayos": len(datos),
    "distribucion": {
        k: int(v)
        for k, v in conteo.items()
    },
    "incidencias": len(incidencias),
    "ensayos_con_incidencias": len(recuento_original),
    "controles_automaticos": "Superados",
    "peligrosidad": "No determinada",
    "validacion_documental": "Pendiente"
}

with open(
    ENTREGA / "auditoria_final_v2.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        reporte,
        f,
        indent=2,
        ensure_ascii=False
    )

# --------------------------------------------------
# 14. RESULTADOS
# --------------------------------------------------

print("\nRESULTADOS FLEX:")
print(resumen_flex.round(3).to_string(index=False))

print("\nRESULTADOS SAFFIRE:")
print(resumen_saffire.to_string(index=False))

print("\nESTADO DE CALIDAD:")
print(resumen_calidad.to_string(index=False))

print("\nINCIDENCIAS POR EXPERIMENTO:")
print(resumen_incidencias.to_string(index=False))

print("\nINFORME ACTUALIZADO:")
print(archivo_informe)

print("\nAUDITORIA CIENTIFICA FINALIZADA")
