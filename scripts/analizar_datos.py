
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent

ruta = (
    BASE_DIR / "data" / "processed"
    / "datos_integrados_daule.csv"
)

datos = pd.read_csv(ruta)

# Preparar fechas
datos["mes"] = pd.to_datetime(datos["mes"])

# Mantener únicamente NDVI con cobertura >= 50 %
datos["NDVI_filtrado"] = datos["NDVI"].where(
    datos["indices_utilizables"]
)

# Crear gráfico con dos ejes
fig, ax1 = plt.subplots(figsize=(13, 6))

# Precipitación
ax1.bar(
    datos["mes"],
    datos["precipitacion"],
    width=20,
    alpha=0.45,
    color="steelblue",
    label="Precipitación"
)

ax1.set_ylabel("Precipitación mensual (mm)")
ax1.set_xlabel("Fecha")

# NDVI
ax2 = ax1.twinx()

ax2.plot(
    datos["mes"],
    datos["NDVI_filtrado"],
    color="forestgreen",
    marker="o",
    markersize=4,
    linewidth=1.8,
    label="NDVI"
)

ax2.set_ylabel("NDVI")
ax2.set_ylim(0, 1)

plt.title(
    "AgroShift: precipitación y NDVI en Daule\n"
    "Noviembre 2021 - Octubre 2026"
)

fig.tight_layout()

# Guardar imagen
salida = (
    BASE_DIR / "data" / "processed"
    / "precipitacion_ndvi_daule.png"
)

plt.savefig(salida, dpi=200)

plt.show()

print("Gráfico generado:")
print(salida)
