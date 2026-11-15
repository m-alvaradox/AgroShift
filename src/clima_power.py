
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RUTA = BASE / "data" / "processed" / "clima_mensual_daule.csv"

COLUMNAS = [
    "temperatura_media",
    "temperatura_maxima",
    "temperatura_minima",
    "precipitacion",
    "humedad_relativa",
    "radiacion_solar"
]


def obtener_clima():
    """Devuelve los datos climáticos mensuales."""
    df = pd.read_csv(RUTA)
    df["mes"] = pd.to_datetime(df["mes"]).dt.strftime("%Y-%m")

    if df["mes"].duplicated().any():
        raise ValueError("Existen meses duplicados en NASA POWER")

    return df.sort_values("mes").reset_index(drop=True)


def consultar_mes(mes):
    """Consulta un mes con formato YYYY-MM."""
    df = obtener_clima()
    resultado = df[df["mes"] == mes]

    if resultado.empty:
        raise ValueError(f"No hay datos climáticos para {mes}")

    return resultado.iloc[0].to_dict()


def obtener_resumen():
    """Calcula estadísticas del período disponible."""
    df = obtener_clima()

    return {
        "meses": len(df),
        "temperatura_media_c": df["temperatura_media"].mean(),
        "precipitacion_total_mm": df["precipitacion"].sum(),
        "precipitacion_media_mensual_mm": df["precipitacion"].mean(),
        "humedad_relativa_media_pct": df["humedad_relativa"].mean()
    }


if __name__ == "__main__":
    print("=== NASA POWER - AGROSHIFT ===")

    print("\nEjemplo: marzo de 2025")
    print(consultar_mes("2025-03"))

    print("\nResumen climático:")
    print(obtener_resumen())
