"""
Agroshift - Paso 2: clima historico de NASA POWER para Daule.

Que hace:
  1. Lee el centro del recuadro desde data/aoi_daule.geojson
  2. Descarga datos DIARIOS de NASA POWER (1991-2025): lluvia, temperatura,
     humedad y radiacion.
  3. Calcula la evapotranspiracion de referencia (ET0) con Hargreaves.
  4. Agrupa por mes y saca la climatologia: que meses son lluviosos,
     de transicion o secos.

Uso (desde la carpeta raiz del proyecto, con el venv activado):
    python src/clima_power.py

Salidas:
    data/raw/power_diario_daule.csv          datos diarios tal como llegan
    data/processed/clima_mensual_daule.csv   un registro por mes y anio
    data/processed/climatologia_daule.csv    promedio de cada mes (ene..dic)
    data/processed/climatologia_daule.html   grafico interactivo (abrir en el navegador)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests

# --- Rutas -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
AOI = ROOT / "data" / "aoi_daule.geojson"
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"

# --- Configuracion -----------------------------------------------------------
INICIO, FIN = "19910101", "20251231"  # 35 anios completos
PARAMETROS = [
    "PRECTOTCORR",        # lluvia corregida (mm/dia)
    "T2M",                # temperatura media a 2 m (C)
    "T2M_MAX",            # temperatura maxima (C)
    "T2M_MIN",            # temperatura minima (C)
    "RH2M",               # humedad relativa (%)
    "ALLSKY_SFC_SW_DWN",  # radiacion solar en superficie (MJ/m2/dia)
    "TOA_SW_DWN",         # radiacion en el tope de la atmosfera (MJ/m2/dia), para ET0
]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def centro_aoi(ruta: Path) -> tuple[float, float]:
    """Devuelve (lat, lon) del centro del recuadro."""
    gj = json.loads(ruta.read_text(encoding="utf-8"))
    coords = gj["features"][0]["geometry"]["coordinates"][0]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return (min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2


def descargar_power(lat: float, lon: float) -> pd.DataFrame:
    """Descarga datos diarios de NASA POWER para un punto."""
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    consulta = {
        "parameters": ",".join(PARAMETROS),
        "community": "AG",  # comunidad agricola: radiacion en MJ/m2/dia
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "start": INICIO,
        "end": FIN,
        "format": "JSON",
    }
    print(f"Descargando NASA POWER para lat={lat:.4f}, lon={lon:.4f} ...")
    r = requests.get(url, params=consulta, timeout=300)
    r.raise_for_status()
    datos = r.json()["properties"]["parameter"]

    df = pd.DataFrame(datos)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df.index.name = "fecha"
    return df.replace(-999.0, np.nan)  # -999 = dato faltante en POWER


def et0_hargreaves(df: pd.DataFrame) -> pd.Series:
    """ET0 diaria (mm/dia) con Hargreaves-Samani (FAO-56, ec. 52)."""
    rango = (df["T2M_MAX"] - df["T2M_MIN"]).clip(lower=0)
    ra_mm = df["TOA_SW_DWN"] * 0.408  # MJ/m2/dia -> mm/dia equivalentes
    return 0.0023 * ra_mm * (df["T2M"] + 17.8) * np.sqrt(rango)


def resumen_mensual(df: pd.DataFrame) -> pd.DataFrame:
    """Un registro por mes y anio. Pide al menos 20 dias validos por mes."""
    m = pd.DataFrame({
        "lluvia_mm": df["PRECTOTCORR"].resample("MS").sum(min_count=20),
        "et0_mm": df["ET0"].resample("MS").sum(min_count=20),
        "t_media_c": df["T2M"].resample("MS").mean(),
        "t_max_c": df["T2M_MAX"].resample("MS").mean(),
        "t_min_c": df["T2M_MIN"].resample("MS").mean(),
        "humedad_pct": df["RH2M"].resample("MS").mean(),
        "radiacion_mj": df["ALLSKY_SFC_SW_DWN"].resample("MS").mean(),
    })
    m["balance_mm"] = m["lluvia_mm"] - m["et0_mm"]  # + sobra agua, - falta agua
    m["anio"] = m.index.year
    m["mes"] = m.index.month
    return m.round(1)


def climatologia(m: pd.DataFrame) -> pd.DataFrame:
    """Promedio de cada mes del anio y clasificacion simple."""
    c = m.groupby("mes").agg(
        lluvia_mm=("lluvia_mm", "mean"),
        lluvia_anio_seco_mm=("lluvia_mm", lambda s: s.quantile(0.2)),
        lluvia_anio_lluvioso_mm=("lluvia_mm", lambda s: s.quantile(0.8)),
        et0_mm=("et0_mm", "mean"),
        balance_mm=("balance_mm", "mean"),
        t_media_c=("t_media_c", "mean"),
        t_max_c=("t_max_c", "mean"),
        humedad_pct=("humedad_pct", "mean"),
    )
    # Regla simple y explicable:
    #   lluvioso   -> llueve igual o mas de lo que se evapora
    #   seco       -> llueve menos de la mitad de lo que se evapora
    #   transicion -> el resto
    c["tipo_mes"] = np.select(
        [c["lluvia_mm"] >= c["et0_mm"], c["lluvia_mm"] < 0.5 * c["et0_mm"]],
        ["lluvioso", "seco"],
        default="transicion",
    )
    c.insert(0, "nombre_mes", MESES)
    return c.round(1)


def grafico(c: pd.DataFrame, ruta: Path) -> None:
    """Barras de lluvia (con rango de anios secos a lluviosos) y linea de ET0."""
    colores = {"lluvioso": "#2a7fd4", "transicion": "#9bbbe0", "seco": "#d9a441"}
    fig = go.Figure()
    fig.add_bar(
        x=c["nombre_mes"], y=c["lluvia_mm"], name="Lluvia promedio (mm)",
        marker_color=[colores[t] for t in c["tipo_mes"]],
        error_y=dict(
            type="data", symmetric=False,
            array=c["lluvia_anio_lluvioso_mm"] - c["lluvia_mm"],
            arrayminus=c["lluvia_mm"] - c["lluvia_anio_seco_mm"],
        ),
        hovertext=c["tipo_mes"],
    )
    fig.add_scatter(x=c["nombre_mes"], y=c["et0_mm"], name="ET0: agua que se evapora (mm)",
                    mode="lines+markers", line=dict(color="#333"))
    fig.update_layout(
        title="Daule: lluvia frente a evaporacion por mes (NASA POWER, 1991-2025)",
        yaxis_title="mm por mes", template="simple_white",
        legend=dict(orientation="h", y=-0.15),
    )
    fig.write_html(ruta)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROC.mkdir(parents=True, exist_ok=True)

    lat, lon = centro_aoi(AOI)
    diario = descargar_power(lat, lon)
    diario["ET0"] = et0_hargreaves(diario)
    diario.round(2).to_csv(RAW / "power_diario_daule.csv")

    mensual = resumen_mensual(diario)
    mensual.to_csv(PROC / "clima_mensual_daule.csv")

    clim = climatologia(mensual)
    clim.to_csv(PROC / "climatologia_daule.csv")
    grafico(clim, PROC / "climatologia_daule.html")

    print("\nClimatologia de Daule (promedio 1991-2025):")
    print(clim[["nombre_mes", "lluvia_mm", "et0_mm", "balance_mm", "tipo_mes"]]
          .to_string(index=False))
    print(f"\nLluvia anual promedio: {clim['lluvia_mm'].sum():.0f} mm")
    for tipo in ["lluvioso", "transicion", "seco"]:
        meses = ", ".join(clim.loc[clim["tipo_mes"] == tipo, "nombre_mes"])
        print(f"Meses {tipo}: {meses or '-'}")
    print(f"\nArchivos guardados en {PROC}")


if __name__ == "__main__":
    main()
