
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
DATOS = BASE / "data" / "processed"

ruta = DATOS / "balance_agua_estrategias.csv"
df = pd.read_csv(ruta)

# Asegurar el orden de las estrategias
df = df.set_index("estrategia").loc[
    ["A", "B", "C"]
].reset_index()

etiquetas = [
    "A: Arroz continuo",
    "B: Arroz y soya",
    "C: Rotación diversificada"
]

fig, ax = plt.subplots(figsize=(11, 6))

barras = ax.bar(
    etiquetas,
    df["deficit_m3_ha"],
    color=["#C88A51", "#5D95CA", "#4A9C70"],
    width=0.55
)

ax.bar_label(
    barras,
    fmt="%.0f",
    padding=5
)

ax.set_title(
    "AgroShift - Comparación de estrategias agrícolas\n"
    "Déficit hídrico estimado (2025-2026)"
)

ax.set_ylabel("Déficit equivalente (m³/ha)")
ax.set_ylim(0, df["deficit_m3_ha"].max() * 1.18)

ax.grid(axis="y", alpha=0.2)
ax.set_axisbelow(True)

fig.text(
    0.5, 0.01,
    "Modelo preliminar: ETc menos lluvia diaria "
    "aprovechable; no equivale al riego real.",
    ha="center",
    fontsize=9
)

plt.tight_layout(rect=[0, 0.04, 1, 1])

salida = DATOS / "comparacion_estrategias_agua.png"

plt.savefig(
    salida,
    dpi=200,
    bbox_inches="tight"
)

plt.show()

print("Gráfico generado:", salida)
