
# PHOENIX ORBIT - CODIGO 27
# REPARACION CONTROLADA DE SAFFIRE-II

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

with sqlite3.connect(DB) as conn:
    unificado = pd.read_sql_query(
        "SELECT * FROM nasa_unificado_validado", conn
    )
    comparador = pd.read_sql_query(
        "SELECT * FROM saffire_comparador", conn
    )

incidencias = pd.read_csv(
    ENTREGA / "validacion_automatica.csv",
    dtype={"ensayo": str}
)

# Verificar estructura minima
for nombre in ["id_ensayo", "experimento"]:
    if nombre not in unificado.columns:
        raise ValueError(f"Falta columna: {nombre}")

for nombre in ["experimento", "muestra"]:
    if nombre not in comparador.columns:
        raise ValueError(
            f"Falta columna en comparador: {nombre}"
        )

# Identificar las filas auxiliares incorrectamente incluidas
auxiliares = unificado[
    (unificado["experimento"] == "SAFFIRE-II")
    & ~unificado["id_ensayo"].astype(str).str.fullmatch(
        r"SAFFIRE-II-2-[1-9]"
    )
].copy()

print("REGISTROS AUXILIARES A EXCLUIR:")
print(auxiliares["id_ensayo"].to_string(index=False))

# Mantener FLEX, SAFFIRE-I y solo los ensayos reales de II
conservar = (
    (unificado["experimento"] != "SAFFIRE-II")
    | unificado["id_ensayo"].astype(str).str.fullmatch(
        r"SAFFIRE-II-2-[1-9]"
    )
)

corregido = unificado.loc[conservar].copy()

# Buscar los ensayos en el comparador independiente
comparador_ii = comparador[
    comparador["experimento"] == "SAFFIRE-II"
].copy()

comparador_ii["muestra"] = (
    comparador_ii["muestra"].astype(str).str.strip()
)

esperados = {f"SAFFIRE-II-2-{i}" for i in range(1, 10)}
actuales = set(corregido["id_ensayo"].astype(str))
faltantes = sorted(esperados - actuales)

print("\nENSAYOS FALTANTES:")
print(faltantes)

# Recuperar datos ya procesados desde el comparador
nuevas_filas = []

for identificador in faltantes:
    muestra = identificador.replace("SAFFIRE-II-", "")

    coincidencias = comparador_ii[
        comparador_ii["muestra"] == muestra
    ]

    if len(coincidencias) != 1:
        raise ValueError(
            f"Se esperaba una fila para {muestra}; "
            f"se encontraron {len(coincidencias)}"
        )

    origen = coincidencias.iloc[0]

    # La fila conserva el mismo esquema del unificado.
    nueva = {col: None for col in unificado.columns}

    nueva["id_ensayo"] = identificador
    nueva["experimento"] = "SAFFIRE-II"

    # Copiar los campos disponibles con el mismo nombre
    # en ambas tablas, evitando campos de identificación.
    protegidos = {"id_ensayo", "experimento"}

    for col in unificado.columns:
        if col in comparador.columns and col not in protegidos:
            nueva[col] = origen[col]

    # Identificar material y duración explícitamente
    for col in ["material", "tiempo_combustion_s"]:
        if col not in comparador.columns:
            raise ValueError(
                f"Falta {col} en saffire_comparador"
            )
        if col not in unificado.columns:
            raise ValueError(
                f"Falta {col} en unificado"
            )
        nueva[col] = origen[col]

    # Referencia al CSV original; no atribuir
    # valores no disponibles.
    if "fuente_archivo" in unificado.columns:
        nueva["fuente_archivo"] = (
            "PSI-99_Experimental table_SAFFIRE-2.csv"
        )

    nuevas_filas.append(nueva)

if nuevas_filas:
    corregido = pd.concat(
        [corregido, pd.DataFrame(nuevas_filas)],
        ignore_index=True
    )

# Validaciones estrictas antes de guardar
ids = corregido["id_ensayo"].astype(str)

if len(corregido) != 285:
    raise ValueError(
        f"Cantidad inesperada: {len(corregido)}"
    )

if ids.duplicated().any():
    raise ValueError("Existen identificadores duplicados")

ids_ii = set(
    corregido.loc[
        corregido["experimento"] == "SAFFIRE-II",
        "id_ensayo"
    ].astype(str)
)

if ids_ii != esperados:
    raise ValueError(
        f"Los ensayos SAFFIRE-II no coinciden: {ids_ii}"
    )

# Reconstruir relaciones de incidencias
incidencias["id_ensayo"] = (
    incidencias["dataset"].astype(str).str.strip()
    + "-"
    + incidencias["ensayo"].astype(str).str.strip()
)

sin_vincular = incidencias[
    ~incidencias["id_ensayo"].isin(ids)
]

if not sin_vincular.empty:
    raise ValueError(
        "Persisten incidencias sin vincular:\n"
        + sin_vincular.to_string(index=False)
    )

resumen = incidencias.groupby("id_ensayo").agg(
    total_incidencias=("prioridad", "size"),
    incidencias_altas=(
        "prioridad", lambda x: (x == "Alta").sum()
    ),
    incidencias_medias=(
        "prioridad", lambda x: (x == "Media").sum()
    ),
    observaciones=(
        "descripcion",
        lambda x: "; ".join(x.astype(str))
    )
).reset_index()

matriz = corregido.merge(
    resumen,
    on="id_ensayo",
    how="left",
    validate="one_to_one"
)

for col in [
    "total_incidencias",
    "incidencias_altas",
    "incidencias_medias"
]:
    matriz[col] = matriz[col].fillna(0).astype(int)

matriz["observaciones"] = matriz[
    "observaciones"
].fillna("Sin incidencias detectadas por las reglas")

variables = [
    "material",
    "oxigeno_pct",
    "presion_kpa",
    "flujo_m_s",
    "tiempo_combustion_s"
]

for col in variables:
    if col not in matriz.columns:
        raise ValueError(f"Variable ausente: {col}")

matriz["variables_disponibles"] = (
    matriz[variables].notna().sum(axis=1)
)

matriz["cobertura_datos"] = pd.cut(
    matriz["variables_disponibles"],
    bins=[-1, 2, 3, 5],
    labels=["Limitada", "Intermedia", "Amplia"]
).astype(str)

def prioridad(f):
    if f["incidencias_altas"] > 0:
        return "Alta"
    if f["incidencias_medias"] > 0:
        return "Media"
    return "Ordinaria"

matriz["prioridad_revision"] = matriz.apply(
    prioridad, axis=1
)

matriz["clasificacion_evidencia"] = matriz[
    "prioridad_revision"
].map({
    "Alta": "Requiere revision prioritaria",
    "Media": "Requiere interpretacion",
    "Ordinaria": "Sin incidencias detectadas"
})

matriz["nivel_peligro"] = "No determinado"

# Comprobacion final de integridad
if int(matriz["total_incidencias"].sum()) != 12:
    raise ValueError(
        "La matriz no contiene las 12 incidencias"
    )

# Guardar nuevas tablas; conservar anteriores
with sqlite3.connect(DB) as conn:
    corregido.to_sql(
        "nasa_unificado_corregido",
        conn, if_exists="replace", index=False
    )
    matriz.to_sql(
        "matriz_evidencia_corregida",
        conn, if_exists="replace", index=False
    )

corregido.to_csv(
    ENTREGA / "nasa_unificado_corregido.csv",
    index=False, encoding="utf-8-sig"
)

matriz.to_csv(
    ENTREGA / "matriz_evidencia_corregida.csv",
    index=False, encoding="utf-8-sig"
)

matriz.to_json(
    ENTREGA / "matriz_evidencia_corregida.json",
    orient="records",
    force_ascii=False,
    indent=2
)

print("\n" + "=" * 55)
print("PHOENIX - INTEGRIDAD CORREGIDA")
print("=" * 55)

print("\nREGISTROS:", len(corregido))
print("\nENSAYOS POR EXPERIMENTO:")
print(corregido["experimento"].value_counts())

print("\nINCIDENCIAS VINCULADAS:")
print(int(matriz["total_incidencias"].sum()))

print("\nENSAYOS CON INCIDENCIAS:")
print(int((matriz["total_incidencias"] > 0).sum()))

print("\nPRIORIDAD DE REVISION:")
print(matriz["prioridad_revision"].value_counts())

print("\nENSAYOS RECUPERADOS:")
print(
    corregido[
        corregido["id_ensayo"].isin(faltantes)
    ][
        ["id_ensayo", "material", "tiempo_combustion_s"]
    ].to_string(index=False)
)

print("\nCORRECCION FINALIZADA")
