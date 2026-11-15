
from pathlib import Path

import numpy as np
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

BASE = Path(__file__).resolve().parent.parent
DATOS = BASE / "data" / "processed"

FACTOR_LLUVIA = 0.80

# ==========================================
# 2. CARGAR DATOS
# ==========================================

balance = pd.read_csv(
    DATOS / "balance_estrategias_diario.csv",
    parse_dates=["fecha"]
)

power = pd.read_csv(
    DATOS / "clima_mensual_daule.csv"
)

imerg = pd.read_csv(
    DATOS / "lluvia_imerg_daule.csv"
)

# Normalizar fechas mensuales
for df in (power, imerg):
    df["mes"] = (
        pd.to_datetime(df["mes"])
        .dt.strftime("%Y-%m")
    )

balance["mes"] = (
    balance["fecha"]
    .dt.strftime("%Y-%m")
)

# ==========================================
# 3. VALIDAR FUENTES
# ==========================================

assert power["mes"].is_unique
assert imerg["mes"].is_unique

assert not balance.duplicated(
    ["estrategia", "fecha"]
).any(), "Existen días duplicados"

# Seleccionar lluvia mensual
power = power[
    ["mes", "precipitacion"]
].rename(
    columns={
        "precipitacion": "power_mensual_mm"
    }
)

columnas_imerg = [
    "mes",
    "precipitacion_imerg_mm"
]

# Conservar control de completitud
if "observaciones" in imerg.columns:
    columnas_imerg.append("observaciones")

if "observaciones_esperadas" in imerg.columns:
    columnas_imerg.append(
        "observaciones_esperadas"
    )

imerg = imerg[columnas_imerg]

# ==========================================
# 4. INTEGRAR FUENTES
# ==========================================

datos = balance.merge(
    power,
    on="mes",
    how="left",
    validate="many_to_one"
).merge(
    imerg,
    on="mes",
    how="left",
    validate="many_to_one"
)

columnas_requeridas = [
    "etc_mm",
    "lluvia_mm",
    "power_mensual_mm",
    "precipitacion_imerg_mm"
]

if datos[columnas_requeridas].isna().any().any():
    raise ValueError(
        "Existen datos faltantes en el balance"
    )

# Días naturales de cada mes
datos["dias_mes"] = datos[
    "fecha"
].dt.days_in_month

# ==========================================
# 5. ESCENARIOS DE PRECIPITACIÓN
# ==========================================

# Escenario 1:
# POWER con lluvia diaria original
datos["lluvia_power_diaria"] = (
    datos["lluvia_mm"].clip(lower=0)
)

# Escenario 2:
# POWER mensual distribuido uniformemente
datos["lluvia_power_uniforme"] = (
    datos["power_mensual_mm"]
    / datos["dias_mes"]
)

# Escenario 3:
# IMERG mensual distribuido uniformemente
datos["lluvia_imerg_uniforme"] = (
    datos["precipitacion_imerg_mm"]
    / datos["dias_mes"]
)

# ==========================================
# 6. CALCULAR DÉFICITS
# ==========================================

escenarios = {
    "POWER diario": "lluvia_power_diaria",
    "POWER mensual uniforme":
        "lluvia_power_uniforme",
    "IMERG mensual uniforme":
        "lluvia_imerg_uniforme"
}

resultados = []

for nombre, columna in escenarios.items():

    lluvia_aprovechable = np.minimum(
        datos[columna].clip(lower=0)
        * FACTOR_LLUVIA,
        datos["etc_mm"]
    )

    deficit = (
        datos["etc_mm"] - lluvia_aprovechable
    ).clip(lower=0)

    temporal = pd.DataFrame({
        "estrategia": datos["estrategia"],
        "escenario": nombre,
        "etc_mm": datos["etc_mm"],
        "lluvia_util_mm": lluvia_aprovechable,
        "deficit_mm": deficit
    })

    resultados.append(temporal)

resultados = pd.concat(
    resultados,
    ignore_index=True
)

# ==========================================
# 7. RESUMEN POR ESTRATEGIA
# ==========================================

resumen = (
    resultados.groupby(
        ["escenario", "estrategia"],
        as_index=False
    )
    .agg(
        demanda_etc_mm=("etc_mm", "sum"),
        lluvia_util_mm=("lluvia_util_mm", "sum"),
        deficit_mm=("deficit_mm", "sum")
    )
)

# 1 mm en una hectárea = 10 m³
resumen["deficit_m3_ha"] = (
    resumen["deficit_mm"] * 10
)

# Comparación relativa frente a A
referencia = (
    resumen[resumen["estrategia"] == "A"]
    [["escenario", "deficit_mm"]]
    .rename(
        columns={"deficit_mm": "deficit_A"}
    )
)

resumen = resumen.merge(
    referencia,
    on="escenario"
)

resumen["reduccion_vs_A_pct"] = (
    100 *
    (
        1 -
        resumen["deficit_mm"]
        / resumen["deficit_A"]
    )
)

resumen = resumen.drop(
    columns=["deficit_A"]
)

# ==========================================
# 8. COMPROBAR CALIDAD DE IMERG
# ==========================================

if (
    "observaciones" in imerg.columns
    and "observaciones_esperadas"
    in imerg.columns
):
    incompletos = imerg[
        imerg["observaciones"]
        < imerg["observaciones_esperadas"]
    ]

    print("\n=== MESES IMERG INCOMPLETOS ===")
    print(incompletos.to_string(index=False))

# ==========================================
# 9. GUARDAR RESULTADOS
# ==========================================

salida = (
    DATOS /
    "comparacion_fuentes_agua.csv"
)

resumen.to_csv(
    salida,
    index=False
)

print("\n=== COMPARACIÓN DE FUENTES ===")

print(
    resumen.round(2).to_string(
        index=False
    )
)

print("\nArchivo generado:")
print(salida)
