
# ==========================================
# PHOENIX ORBIT - CODIGO 26
# AUDITORIA DE INTEGRIDAD DE LA MATRIZ
# ==========================================

from pathlib import Path
import sqlite3
import pandas as pd

BASE = Path(
    r"C:\Users\Yesid\Documents\Machine\guia2"
)

ENTREGA = BASE / "phoenix_data" / "entrega_analisis"
DB = BASE / "phoenix_data" / "phoenix_fire.db"

# 1. Cargar tablas
with sqlite3.connect(DB) as conn:
    originales = pd.read_sql_query(
        "SELECT * FROM nasa_unificado_validado",
        conn
    )

    matriz = pd.read_sql_query(
        "SELECT * FROM matriz_evidencia",
        conn
    )

incidencias = pd.read_csv(
    ENTREGA / "validacion_automatica.csv",
    dtype={"ensayo": str}
)

# 2. Construir identificadores esperados
incidencias["id_esperado"] = (
    incidencias["dataset"].astype(str)
    + "-"
    + incidencias["ensayo"].astype(str).str.strip()
)

# 3. Comparar con identificadores existentes
ids_matriz = set(
    matriz["id_ensayo"].dropna().astype(str).str.strip()
)

incidencias["en_matriz"] = (
    incidencias["id_esperado"].isin(ids_matriz)
)

sin_vincular = incidencias[
    ~incidencias["en_matriz"]
].copy()

# 4. Buscar ensayos SAFFIRE-II en tabla integrada
detalle_saffire = originales[
    originales["experimento"] == "SAFFIRE-II"
].copy()

# 5. Verificar integridad de identificadores
duplicados = originales[
    originales["id_ensayo"].duplicated(keep=False)
]

nulos = originales[
    originales["id_ensayo"].isna()
]

# 6. Comparar cantidades
total_reportadas = len(incidencias)

total_vinculadas = int(
    incidencias["en_matriz"].sum()
)

total_matriz = int(
    pd.to_numeric(
        matriz["total_incidencias"],
        errors="coerce"
    ).fillna(0).sum()
)

print("=" * 60)
print("PHOENIX - AUDITORIA DE INTEGRIDAD")
print("=" * 60)

print("\nREGISTROS:")
print("Integrados:", len(originales))
print("Matriz:", len(matriz))

print("\nINCIDENCIAS:")
print("Reporte original:", total_reportadas)
print("Identificadores encontrados:", total_vinculadas)
print("Total registrado en matriz:", total_matriz)
print("Sin vincular:", len(sin_vincular))

print("\nINCIDENCIAS SIN VINCULAR:")
if sin_vincular.empty:
    print("Ninguna")
else:
    print(
        sin_vincular[
            [
                "dataset",
                "ensayo",
                "id_esperado",
                "variable",
                "valor_original"
            ]
        ].to_string(index=False)
    )

print("\nIDENTIFICADORES SAFFIRE-II EN BASE:")
print(
    detalle_saffire[
        [
            "id_ensayo",
            "experimento",
            "material",
            "tiempo_combustion_s"
        ]
    ].to_string(index=False)
)

print("\nIDENTIFICADORES DUPLICADOS:")
print(len(duplicados))

print("\nIDENTIFICADORES NULOS:")
print(len(nulos))

# 7. Exportar diagnóstico
sin_vincular.to_csv(
    ENTREGA / "incidencias_sin_vincular.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nDIAGNOSTICO FINALIZADO")
