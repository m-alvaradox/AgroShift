
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent

ruta = BASE_DIR / "data" / "processed" / "clima_mensual_daule.csv"

df = pd.read_csv(
    ruta,
    parse_dates=["mes"]
)

plt.figure(figsize=(12, 5))

plt.bar(
    df["mes"],
    df["precipitacion"],
    width=22
)

plt.title("Precipitación mensual - Daule")
plt.xlabel("Fecha")
plt.ylabel("Precipitación (mm)")

plt.xticks(rotation=45)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.show()
