
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
DATOS = BASE / "data" / "processed"

# 1. Cargar fuentes
enso = pd.read_csv(DATOS / "enso_roni_daule.csv")
power = pd.read_csv(DATOS / "clima_mensual_daule.csv")
imerg = pd.read_csv(DATOS / "lluvia_imerg_daule.csv")

# 2. Normalizar fechas
for df in (enso, power, imerg):
    df["mes"] = (
        pd.to_datetime(df["mes"])
        .dt.strftime("%Y-%m")
    )
    assert df["mes"].is_unique, "Meses duplicados"

# 3. Seleccionar columnas
power = power[["mes", "precipitacion"]].rename(
    columns={"precipitacion": "power_mm"}
)

imerg = imerg[
    ["mes", "precipitacion_imerg_mm"]
].rename(
    columns={"precipitacion_imerg_mm": "imerg_mm"}
)

# 4. Integrar, conservando los 60 meses
datos = power.merge(
    imerg, on="mes", how="left", validate="one_to_one"
).merge(
    enso[["mes", "roni", "fase_enso"]],
    on="mes",
    how="left",
    validate="one_to_one"
)

datos = datos.sort_values("mes").reset_index(drop=True)
datos["fecha"] = pd.to_datetime(datos["mes"])

assert len(datos) == 60, "Se esperaban 60 meses"

# 5. Resumen según condiciones ENSO
resumen = (
    datos.dropna(subset=["fase_enso"])
    .groupby("fase_enso")
    .agg(
        meses=("mes", "count"),
        power_promedio_mm=("power_mm", "mean"),
        imerg_promedio_mm=("imerg_mm", "mean")
    )
    .round(2)
)

print("\n=== ENSO Y PRECIPITACIÓN EN DAULE ===")
print("Meses integrados:", len(datos))
print("Meses con RONI:", datos["roni"].notna().sum())

print("\nPrecipitación mensual por fase:")
print(resumen.to_string())

print("\nMeses sin RONI:")
print(
    datos.loc[datos["roni"].isna(), "mes"].tolist()
)

# 6. Guardar información
datos.drop(columns="fecha").to_csv(
    DATOS / "enso_lluvia_daule.csv",
    index=False
)

resumen.to_csv(
    DATOS / "resumen_enso_lluvia.csv"
)

# 7. Gráfico histórico
fig, ax1 = plt.subplots(figsize=(14, 6))

ax1.bar(
    datos["fecha"],
    datos["imerg_mm"],
    width=23,
    color="steelblue",
    alpha=0.65,
    label="Precipitación IMERG"
)

ax1.set_ylabel("Precipitación mensual (mm)")
ax1.set_xlabel("Fecha")

ax2 = ax1.twinx()

ax2.plot(
    datos["fecha"],
    datos["roni"],
    color="darkorange",
    linewidth=2,
    marker="o",
    markersize=3,
    label="RONI"
)

ax2.axhline(0.5, color="red", linestyle="--",
            alpha=0.6)
ax2.axhline(-0.5, color="blue", linestyle="--",
            alpha=0.6)
ax2.axhline(0, color="gray", linewidth=0.7)

ax2.set_ylabel("RONI (°C)")

ax1.set_title(
    "AgroShift - ENSO y precipitación en Daule\n"
    "Noviembre 2021 - Octubre 2026"
)

fig.tight_layout()

salida = DATOS / "enso_lluvia_daule.png"
plt.savefig(salida, dpi=200)
plt.show()

print("\nGráfico generado:", salida)
