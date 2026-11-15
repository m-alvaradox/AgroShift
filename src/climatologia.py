
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from clima_power import obtener_clima
from lluvia_imerg import obtener_lluvia

BASE = Path(__file__).resolve().parent.parent
DATOS = BASE / "data" / "processed"

# 1. Obtener datos desde los módulos P1
power = obtener_clima()
imerg = obtener_lluvia()

# 2. Integrar fuentes
df = power.merge(
    imerg[["mes", "precipitacion_imerg_mm"]],
    on="mes",
    how="inner",
    validate="one_to_one"
)

assert len(df) == 60, "Se esperaban 60 meses"

# 3. Extraer mes del año
df["numero_mes"] = pd.to_datetime(
    df["mes"]
).dt.month

# 4. Caracterización mensual multianual
climatologia = df.groupby(
    "numero_mes",
    as_index=False
).agg(
    temperatura_media=(
        "temperatura_media", "mean"
    ),
    precipitacion_power=(
        "precipitacion", "mean"
    ),
    precipitacion_imerg=(
        "precipitacion_imerg_mm", "mean"
    ),
    humedad_relativa=(
        "humedad_relativa", "mean"
    )
)

# 5. Guardar CSV
salida_csv = DATOS / "climatologia_daule.csv"

climatologia.to_csv(
    salida_csv,
    index=False
)

print("\n=== CLIMATOLOGÍA DE DAULE ===")
print(climatologia.round(2).to_string(index=False))

# 6. Gráfico de precipitación
meses = [
    "Ene", "Feb", "Mar", "Abr",
    "May", "Jun", "Jul", "Ago",
    "Sep", "Oct", "Nov", "Dic"
]

posiciones = range(12)
ancho = 0.38

fig, ax = plt.subplots(figsize=(12, 6))

ax.bar(
    [x - ancho / 2 for x in posiciones],
    climatologia["precipitacion_power"],
    width=ancho,
    label="NASA POWER",
    color="#5D95CA"
)

ax.bar(
    [x + ancho / 2 for x in posiciones],
    climatologia["precipitacion_imerg"],
    width=ancho,
    label="GPM IMERG",
    color="#4A9C70"
)

ax.set_xticks(list(posiciones))
ax.set_xticklabels(meses)

ax.set_ylabel("Precipitación promedio mensual (mm)")
ax.set_title(
    "AgroShift - Caracterización de lluvias en Daule\n"
    "Noviembre 2021 - Octubre 2026"
)

ax.legend()
ax.grid(axis="y", alpha=0.2)
ax.set_axisbelow(True)

plt.tight_layout()

salida_png = DATOS / "climatologia_lluvia_daule.png"

plt.savefig(
    salida_png,
    dpi=200,
    bbox_inches="tight"
)

plt.show()

print("\nArchivos generados:")
print(salida_csv)
print(salida_png)
