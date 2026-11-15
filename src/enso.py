
from pathlib import Path
from io import StringIO

import pandas as pd
import requests

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

URL_RONI = (
    "https://www.cpc.ncep.noaa.gov/"
    "data/indices/RONI.ascii.txt"
)

RUTA_RAW = (
    BASE_DIR / "data" / "raw" / "roni_noaa.txt"
)

RUTA_SALIDA = (
    BASE_DIR / "data" / "processed"
    / "enso_roni_daule.csv"
)

RUTA_RAW.parent.mkdir(
    parents=True, exist_ok=True
)

RUTA_SALIDA.parent.mkdir(
    parents=True, exist_ok=True
)

# ==========================================
# 2. DESCARGAR DATOS OFICIALES NOAA
# ==========================================

print("Descargando RONI desde NOAA...")

respuesta = requests.get(
    URL_RONI,
    timeout=30
)

respuesta.raise_for_status()

RUTA_RAW.write_text(
    respuesta.text,
    encoding="utf-8"
)

# ==========================================
# 3. LEER DATOS RONI
# ==========================================

roni = pd.read_csv(
    StringIO(respuesta.text),
    sep=r"\s+"
)

print("\nColumnas originales:")
print(roni.columns.tolist())

# NOAA utiliza:
# SEAS = temporada trimestral
# YR = año del mes central
# ANOM = valor RONI en grados Celsius

roni = roni.rename(columns={
    "SEAS": "temporada",
    "YR": "anio",
    "ANOM": "roni"
})

# ==========================================
# 4. IDENTIFICAR MES CENTRAL
# ==========================================

meses = {
    "DJF": 1,
    "JFM": 2,
    "FMA": 3,
    "MAM": 4,
    "AMJ": 5,
    "MJJ": 6,
    "JJA": 7,
    "JAS": 8,
    "ASO": 9,
    "SON": 10,
    "OND": 11,
    "NDJ": 12
}

roni["numero_mes"] = (
    roni["temporada"].map(meses)
)

roni["fecha"] = pd.to_datetime(
    dict(
        year=roni["anio"],
        month=roni["numero_mes"],
        day=1
    )
)

roni["mes"] = (
    roni["fecha"].dt.strftime("%Y-%m")
)

# ==========================================
# 5. CLASIFICAR CONDICIONES ENSO
# ==========================================

def clasificar_enso(valor):
    if pd.isna(valor):
        return "Sin datos"
    if valor >= 0.5:
        return "El Niño"
    if valor <= -0.5:
        return "La Niña"
    return "Neutral"

roni["fase_enso"] = (
    roni["roni"].apply(clasificar_enso)
)

# ==========================================
# 6. FILTRAR LOS CINCO AÑOS
# ==========================================

inicio = "2021-11"
fin = "2026-10"

roni = roni[
    (roni["mes"] >= inicio)
    & (roni["mes"] <= fin)
].copy()

roni = roni.sort_values("mes")

# ==========================================
# 7. EXPORTAR CSV
# ==========================================

columnas = [
    "mes",
    "temporada",
    "roni",
    "fase_enso"
]

resultado = roni[columnas]

resultado.to_csv(
    RUTA_SALIDA,
    index=False
)

# ==========================================
# 8. MOSTRAR RESULTADOS
# ==========================================

print("\n=== ANÁLISIS ENSO AGROSHIFT ===")

print(
    "Meses disponibles:",
    len(resultado)
)

print("\nMeses por condición ENSO:")
print(resultado["fase_enso"].value_counts())

print("\nÚltimos registros:")
print(resultado.tail(12).to_string(index=False))

print("\nArchivo generado:")
print(RUTA_SALIDA)
