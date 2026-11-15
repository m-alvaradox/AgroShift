
from pathlib import Path

import numpy as np
import pandas as pd

# =========================================
# 1. CONFIGURACIÓN
# =========================================

BASE = Path(__file__).resolve().parent.parent
DATOS = BASE / "data" / "processed"

ARCHIVO = DATOS / "clima_diario_daule.csv"
SALIDA_DIARIA = DATOS / "eto_diaria_daule.csv"
SALIDA_MENSUAL = DATOS / "eto_mensual_daule.csv"

LATITUD = -1.86

# =========================================
# 2. CARGAR NASA POWER
# =========================================

df = pd.read_csv(ARCHIVO)

print("Columnas disponibles:")
print(df.columns.tolist())

# Aceptar nombres usados en el proyecto
aliases = {
    "T2M": "temperatura_media",
    "T2M_MAX": "temperatura_maxima",
    "T2M_MIN": "temperatura_minima",
    "fecha": "fecha",
    "date": "fecha"
}

df = df.rename(columns={
    k: v for k, v in aliases.items()
    if k in df.columns
})

if "fecha" not in df.columns:
    alternativas = [
        c for c in df.columns
        if c.startswith("Unnamed:")
    ]

    if alternativas:
        df = df.rename(
            columns={alternativas[0]: "fecha"}
        )

requeridas = [
    "fecha",
    "temperatura_media",
    "temperatura_maxima",
    "temperatura_minima"
]

faltantes = [
    c for c in requeridas if c not in df.columns
]

if faltantes:
    raise ValueError(
        "Faltan columnas: "
        + ", ".join(faltantes)
    )

df["fecha"] = pd.to_datetime(
    df["fecha"].astype(str),
    format="mixed"
)

df = df.sort_values("fecha").reset_index(drop=True)

for columna in requeridas[1:]:
    df[columna] = pd.to_numeric(
        df[columna], errors="coerce"
    )

    # NASA POWER usa valores negativos especiales
    # como -999 para indicar ausencia de datos.
    df.loc[df[columna] <= -900, columna] = np.nan

# =========================================
# 3. RADIACIÓN EXTRATERRESTRE (Ra)
# =========================================

# Día del año
J = df["fecha"].dt.day_of_year.to_numpy()

# Latitud en radianes
phi = np.radians(LATITUD)

# Constante solar: MJ/(m² min)
GSC = 0.0820

# Distancia relativa Tierra-Sol
dr = 1 + 0.033 * np.cos(2 * np.pi * J / 365)

# Declinación solar
delta = 0.409 * np.sin(
    2 * np.pi * J / 365 - 1.39
)

# Ángulo horario de puesta del sol
argumento = -np.tan(phi) * np.tan(delta)

ws = np.arccos(
    np.clip(argumento, -1, 1)
)

# Radiación extraterrestre MJ/(m² día)
Ra = (
    (24 * 60 / np.pi)
    * GSC
    * dr
    * (
        ws * np.sin(phi) * np.sin(delta)
        + np.cos(phi)
        * np.cos(delta)
        * np.sin(ws)
    )
)

df["Ra_MJ_m2_dia"] = Ra

# =========================================
# 4. ETo HARGREAVES-SAMANI
# =========================================

Tmedia = df["temperatura_media"]
Tmax = df["temperatura_maxima"]
Tmin = df["temperatura_minima"]

amplitud = Tmax - Tmin

# Si los datos son inconsistentes,
# no generamos una ETo artificial.
amplitud = amplitud.where(amplitud >= 0)

df["eto_mm_dia"] = (
    0.0023
    * 0.408
    * df["Ra_MJ_m2_dia"]
    * (Tmedia + 17.8)
    * np.sqrt(amplitud)
)

df["eto_mm_dia"] = df["eto_mm_dia"].clip(lower=0)

# =========================================
# 5. RESUMEN MENSUAL
# =========================================

df["mes"] = df["fecha"].dt.strftime("%Y-%m")

mensual = df.groupby("mes").agg(
    eto_total_mm=("eto_mm_dia", "sum"),
    eto_media_mm_dia=("eto_mm_dia", "mean"),
    dias_validos=("eto_mm_dia", "count")
).reset_index()

mensual["dias_mes"] = pd.to_datetime(
    mensual["mes"] + "-01"
).dt.days_in_month

mensual["cobertura_pct"] = (
    100
    * mensual["dias_validos"]
    / mensual["dias_mes"]
)

# No presentar un acumulado parcial como mensual
mensual.loc[
    mensual["dias_validos"] < mensual["dias_mes"],
    "eto_total_mm"
] = np.nan

# =========================================
# 6. GUARDAR RESULTADOS
# =========================================

df.to_csv(SALIDA_DIARIA, index=False)
mensual.to_csv(SALIDA_MENSUAL, index=False)

print("\n=== ETo DAULE ===")
print("Días procesados:", len(df))
print("Días con ETo válida:", df["eto_mm_dia"].count())
print("Meses procesados:", len(mensual))

print("\nPrimeros resultados:")
print(mensual.head().to_string(index=False))

print("\nEstadísticas diarias:")
print(df["eto_mm_dia"].describe())

print("\nArchivos generados:")
print(SALIDA_DIARIA)
print(SALIDA_MENSUAL)
