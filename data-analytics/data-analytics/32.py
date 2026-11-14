
# ==================================================
# PHOENIX ORBIT - CODIGO 32
# PAQUETE TECNICO DE ANALISIS DE DATOS
# ==================================================

from pathlib import Path
from datetime import datetime
import sqlite3
import pandas as pd
import hashlib
import json
import shutil
import zipfile

# 1. RUTAS
BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

PHOENIX = BASE / "phoenix_data"
ENTREGA = PHOENIX / "entrega_analisis"
PAQUETE = PHOENIX / "PHOENIX_DATA_ANALYTICS_V2"

DB = PHOENIX / "phoenix_fire.db"

PAQUETE.mkdir(parents=True, exist_ok=True)

# 2. CARGAR TABLAS DEFINIDAS PARA LA VERSION 2
tablas = {
    "ensayos_integrados": "nasa_unificado_v2",
    "matriz_evidencia": "matriz_evidencia_v2",
    "clasificacion_saffire": "saffire_clasificado"
}

datos = {}

with sqlite3.connect(DB) as conn:
    for nombre_archivo, nombre_tabla in tablas.items():
        datos[nombre_archivo] = pd.read_sql_query(
            f'SELECT * FROM "{nombre_tabla}"',
            conn
        )

# 3. VERIFICAR INTEGRIDAD ANTES DE EXPORTAR
ensayos = datos["ensayos_integrados"]
matriz = datos["matriz_evidencia"]
saffire = datos["clasificacion_saffire"]

assert len(ensayos) == 285
assert len(matriz) == 285
assert len(saffire) == 11

assert ensayos["id_ensayo"].is_unique
assert matriz["id_ensayo"].is_unique

assert set(ensayos["id_ensayo"]) == set(
    matriz["id_ensayo"]
)

assert int(
    pd.to_numeric(
        matriz["total_incidencias"],
        errors="raise"
    ).sum()
) == 12

assert ensayos["experimento"].value_counts().to_dict() == {
    "FLEX": 274,
    "SAFFIRE-II": 9,
    "SAFFIRE-I": 2
}

# 4. DICCIONARIO CON DESCRIPCIONES
descripciones = {
    "id_ensayo": (
        "Identificador normalizado del ensayo", ""
    ),
    "experimento": (
        "Programa experimental de origen", ""
    ),
    "material": (
        "Material o combustible reportado", ""
    ),
    "oxigeno_pct": (
        "Concentracion representativa de oxigeno",
        "%"
    ),
    "oxigeno_texto_original": (
        "Texto del oxigeno en el registro original",
        ""
    ),
    "oxigeno_min_pct": (
        "Limite inferior del intervalo reportado",
        "%"
    ),
    "oxigeno_max_pct": (
        "Limite superior del intervalo reportado",
        "%"
    ),
    "tipo_oxigeno": (
        "Valor reportado, aproximado o intervalo",
        ""
    ),
    "presion_kpa": (
        "Presion normalizada cuando esta disponible",
        "kPa"
    ),
    "flujo_m_s": (
        "Velocidad del flujo de aire normalizada",
        "m/s"
    ),
    "tiempo_combustion_s": (
        "Duracion numerica reportada cuando existe",
        "s"
    ),
    "fuente_archivo": (
        "Nombre del CSV experimental de origen",
        ""
    ),
    "total_incidencias": (
        "Cantidad de observaciones de calidad",
        "conteo"
    ),
    "prioridad_revision": (
        "Prioridad de revision de datos, no peligro",
        ""
    ),
    "cobertura_datos": (
        "Disponibilidad de cinco variables seleccionadas",
        ""
    ),
    "clasificacion_evidencia": (
        "Estado segun reglas de auditoria automatica",
        ""
    ),
    "nivel_peligro": (
        "Peligrosidad no determinada en esta version",
        ""
    ),
    "observaciones": (
        "Observaciones de auditoria asociadas",
        ""
    ),
    "muestra": (
        "Identificador original del ensayo SAFFIRE",
        ""
    ),
    "comportamiento_reportado": (
        "Tipo descriptivo del resultado SAFFIRE",
        ""
    ),
    "estado_calidad": (
        "Etiqueta preliminar de calidad SAFFIRE",
        ""
    )
}

diccionario = []

for nombre_tabla, df in datos.items():

    for columna in df.columns:

        descripcion, unidad = descripciones.get(
            columna,
            ("Pendiente de documentar", "")
        )

        diccionario.append({
            "tabla": nombre_tabla,
            "variable": columna,
            "tipo_dato": str(df[columna].dtype),
            "descripcion": descripcion,
            "unidad": unidad,
            "registros": len(df),
            "valores_disponibles": int(
                df[columna].notna().sum()
            ),
            "valores_faltantes": int(
                df[columna].isna().sum()
            )
        })

df_diccionario = pd.DataFrame(diccionario)

# 5. EXPORTAR TABLAS DE DATOS
for nombre, df in datos.items():

    df.to_csv(
        PAQUETE / f"{nombre}.csv",
        index=False,
        encoding="utf-8-sig"
    )

    df.to_json(
        PAQUETE / f"{nombre}.json",
        orient="records",
        force_ascii=False,
        indent=2
    )

df_diccionario.to_csv(
    PAQUETE / "diccionario_variables.csv",
    index=False,
    encoding="utf-8-sig"
)

# 6. INCLUIR INFORME Y AUDITORIA
archivos_adicionales = [
    "informe_cientifico_phoenix_v2.md",
    "auditoria_final_v2.json",
    "validacion_automatica.csv",
    "inventario_trazable.csv"
]

for nombre in archivos_adicionales:

    origen = ENTREGA / nombre

    if not origen.is_file():
        raise FileNotFoundError(
            f"Falta un archivo de entrega: {origen}"
        )

    shutil.copy2(
        origen,
        PAQUETE / nombre
    )

# 7. INSTRUCCIONES PARA EL EQUIPO
readme = """# PHOENIX DATA ANALYTICS V2

Proyecto: PHOENIX FIRE INTELLIGENCE
Equipo: PHOENIX Orbit

## Contenido

- ensayos_integrados.csv:
  285 ensayos de FLEX, SAFFIRE-I y SAFFIRE-II.

- matriz_evidencia.csv:
  Variables, cobertura e incidencias por ensayo.

- clasificacion_saffire.csv:
  Clasificacion descriptiva de 11 ensayos SAFFIRE.

- diccionario_variables.csv:
  Campos, tipos, unidades y valores faltantes.

- validacion_automatica.csv:
  12 incidencias de auditoria documentadas.

- informe_cientifico_phoenix_v2.md:
  Resultados y limitaciones del analisis.

- inventario_trazable.csv:
  Identificacion de los archivos NASA originales.

## Procedencia

Archivos originales utilizados:

PSI-69_Experimental table_FLEX.csv
PSI-98_Experimental table_SAFFIRE-1.csv
PSI-99_Experimental table_SAFFIRE-2.csv

## Restricciones de interpretacion

1. Los resultados son exploratorios.
2. La prioridad de revision NO es nivel de peligro.
3. Las duraciones no representan por si solas
   severidad ni propagacion del incendio.
4. Los valores aproximados y rangos de oxigeno
   deben conservarse con su texto original.
5. Los registros con ninguna incidencia detectada
   no estan necesariamente validados.
6. Existen espesores, materiales y unidades
   pendientes de verificacion documental.
7. Los datos originales no deben reemplazarse
   por suposiciones.
8. Algunas columnas del diccionario requieren
   documentacion adicional antes de uso cientifico.

## Uso recomendado

Usar id_ensayo para relacionar
ensayos_integrados y matriz_evidencia.

Consultar fuente_archivo y observaciones
antes de generar conclusiones automaticas.

La peligrosidad se considera no determinada
hasta implementar una metodologia validada.
"""

(PAQUETE / "README.md").write_text(
    readme,
    encoding="utf-8"
)

# 8. CREAR MANIFIESTO DE ARCHIVOS
def sha256(ruta):
    h = hashlib.sha256()

    with ruta.open("rb") as f:
        for bloque in iter(
            lambda: f.read(1024 * 1024),
            b""
        ):
            h.update(bloque)

    return h.hexdigest()

archivos = []

for ruta in sorted(PAQUETE.iterdir()):

    if ruta.is_file() and ruta.name != "manifest.json":

        archivos.append({
            "archivo": ruta.name,
            "tamano_bytes": ruta.stat().st_size,
            "sha256": sha256(ruta)
        })

manifest = {
    "proyecto": "PHOENIX FIRE INTELLIGENCE",
    "area": "Analisis de Datos",
    "version": "2",
    "fecha_generacion": datetime.now().isoformat(
        timespec="seconds"
    ),
    "ensayos": 285,
    "incidencias": 12,
    "archivos": archivos
}

(PAQUETE / "manifest.json").write_text(
    json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

# 9. CREAR ARCHIVO ZIP
ruta_zip = (
    PHOENIX / "PHOENIX_DATA_ANALYTICS_V2.zip"
)

with zipfile.ZipFile(
    ruta_zip,
    "w",
    compression=zipfile.ZIP_DEFLATED
) as z:

    for ruta in sorted(PAQUETE.iterdir()):
        if ruta.is_file():
            z.write(
                ruta,
                arcname=f"{PAQUETE.name}/{ruta.name}"
            )

# 10. VERIFICAR INTEGRIDAD DEL ZIP
with zipfile.ZipFile(ruta_zip) as z:
    archivo_danado = z.testzip()

    if archivo_danado is not None:
        raise RuntimeError(
            f"Archivo ZIP dañado: {archivo_danado}"
        )

# 11. RESULTADOS
pendientes_diccionario = int(
    (
        df_diccionario["descripcion"]
        == "Pendiente de documentar"
    ).sum()
)

print("=" * 60)
print("PHOENIX - PAQUETE TECNICO DE DATOS")
print("=" * 60)

print("\nENSAYOS:", len(ensayos))
print("REGISTROS SAFFIRE:", len(saffire))
print("INCIDENCIAS:", int(
    matriz["total_incidencias"].sum()
))

print("\nVARIABLES DOCUMENTADAS:")
print(len(df_diccionario) - pendientes_diccionario)

print("\nVARIABLES POR DOCUMENTAR:")
print(pendientes_diccionario)

print("\nARCHIVOS INCLUIDOS:")
for ruta in sorted(PAQUETE.iterdir()):
    if ruta.is_file():
        print("-", ruta.name)

print("\nCARPETA:")
print(PAQUETE)

print("\nARCHIVO ZIP:")
print(ruta_zip)

print("\nINTEGRIDAD ZIP: CORRECTA")
print("\nPAQUETE GENERADO CORRECTAMENTE")
