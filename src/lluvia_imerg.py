
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RUTA = BASE / "data" / "processed" / "lluvia_imerg_daule.csv"


def obtener_lluvia():
    """Devuelve la serie mensual de GPM IMERG."""
    df = pd.read_csv(RUTA)

    df["mes"] = pd.to_datetime(df["mes"]).dt.strftime("%Y-%m")

    if df["mes"].duplicated().any():
        raise ValueError("Existen meses duplicados en IMERG")

    if df["precipitacion_imerg_mm"].isna().any():
        raise ValueError("Existen meses sin precipitación IMERG")

    return df.sort_values("mes").reset_index(drop=True)


def consultar_mes(mes):
    """Consulta la precipitación de un mes."""
    df = obtener_lluvia()
    resultado = df[df["mes"] == mes]

    if resultado.empty:
        raise ValueError(f"No hay datos IMERG para {mes}")

    return resultado.iloc[0].to_dict()


def obtener_resumen():
    """Resume la precipitación y calidad temporal."""
    df = obtener_lluvia()

    resumen = {
        "meses": len(df),
        "precipitacion_total_mm":
            df["precipitacion_imerg_mm"].sum(),
        "precipitacion_media_mensual_mm":
            df["precipitacion_imerg_mm"].mean()
    }

    if {
        "observaciones",
        "observaciones_esperadas"
    }.issubset(df.columns):

        incompletos = df[
            df["observaciones"]
            < df["observaciones_esperadas"]
        ]

        resumen["meses_incompletos"] = (
            incompletos["mes"].tolist()
        )

    return resumen


if __name__ == "__main__":
    print("=== NASA GPM IMERG - AGROSHIFT ===")

    print("\nEjemplo: marzo de 2025")
    print(consultar_mes("2025-03"))

    print("\nResumen de precipitación:")
    print(obtener_resumen())
