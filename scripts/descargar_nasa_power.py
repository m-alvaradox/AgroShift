
from pathlib import Path

import pandas as pd
import requests

# ==========================================
# CONFIGURACIÓN AGROSHIFT
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

PARAMS = {
    "parameters": (
        "T2M,T2M_MAX,T2M_MIN,"
        "PRECTOTCORR,RH2M,ALLSKY_SFC_SW_DWN"
    ),
    "community": "AG",
    "latitude": -1.86,
    "longitude": -79.98,
    "start": "20211101",
    "end": "20261031",
    "format": "JSON",
    "time-standard": "LST",
}

# ==========================================
# 1. DESCARGAR INFORMACIÓN DE NASA
# ==========================================

print("Consultando NASA POWER para Daule...")

response = requests.get(
    URL,
    params=PARAMS,
    timeout=120
)
response.raise_for_status()

data = response.json()

# Conservamos el archivo original
raw_path = RAW_DIR / "nasa_power_daule.json"

raw_path.write_text(
    response.text,
    encoding="utf-8"
)

print("Datos originales descargados.")

# ==========================================
# 2. TRANSFORMAR A DATAFRAME
# ==========================================

variables = data["properties"]["parameter"]

df = pd.DataFrame(variables)

df.index = pd.to_datetime(
    df.index,
    format="%Y%m%d"
)

df.index.name = "fecha"
df = df.sort_index()

# NASA utiliza -999 para datos faltantes
df = df.replace(-999, float("nan"))

df = df.rename(columns={
    "T2M": "temperatura_media",
    "T2M_MAX": "temperatura_maxima",
    "T2M_MIN": "temperatura_minima",
    "PRECTOTCORR": "precipitacion",
    "RH2M": "humedad_relativa",
    "ALLSKY_SFC_SW_DWN": "radiacion_solar",
})

# ==========================================
# 3. VALIDAR DATOS
# ==========================================

print("\nRegistros recibidos:", len(df))

print("\nDatos faltantes por variable:")
print(df.isna().sum())

print("\nPrimeros registros:")
print(df.head())

# ==========================================
# 4. GUARDAR DATOS DIARIOS
# ==========================================

daily_path = PROCESSED_DIR / "clima_diario_daule.csv"
df.to_csv(daily_path)

# ==========================================
# 5. GENERAR INDICADORES MENSUALES
# ==========================================

mensual = df.resample("MS").agg({
    "temperatura_media": "mean",
    "temperatura_maxima": "max",
    "temperatura_minima": "min",
    "precipitacion": lambda s: s.sum(min_count=1),
    "humedad_relativa": "mean",
    "radiacion_solar": "mean",
})

mensual.index.name = "mes"

monthly_path = (
    PROCESSED_DIR / "clima_mensual_daule.csv"
)

mensual.to_csv(monthly_path)

# ==========================================
# 6. MOSTRAR RESULTADOS
# ==========================================

print("\nResumen mensual:")
print(mensual.head())

print("\nArchivos generados:")
print(raw_path)
print(daily_path)
print(monthly_path)

print("\nProcesamiento finalizado.")
