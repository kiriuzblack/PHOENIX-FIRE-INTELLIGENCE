
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Conectar a nuestra base de datos
conexion = sqlite3.connect(
    "phoenix_data/phoenix_fire.db"
)

# Leer experimentos
df = pd.read_sql_query(
    "SELECT * FROM experimentos",
    conexion
)

conexion.close()

# Total de registros
print("TOTAL DE EXPERIMENTOS:", len(df))

# Calcular valores faltantes
faltantes = df.isna().sum()

porcentaje = (
    faltantes / len(df) * 100
).round(2)

reporte = pd.DataFrame({
    "Valores faltantes": faltantes,
    "Porcentaje faltante (%)": porcentaje
})

print("\nREPORTE DE CALIDAD:")
print(reporte)

# Visualización
plt.figure(figsize=(11, 5))

porcentaje.plot(kind="bar")

plt.title(
    "PHOENIX Orbit - Calidad de datos NASA"
)

plt.ylabel("Datos faltantes (%)")
plt.xlabel("Variables")
plt.ylim(0, 105)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig(
    "phoenix_data/calidad_datos.png",
    dpi=300
)

plt.show()

# Guardar reporte CSV
reporte.to_csv(
    "phoenix_data/reporte_calidad.csv",
    encoding="utf-8-sig"
)

print("\nReporte generado correctamente.")
