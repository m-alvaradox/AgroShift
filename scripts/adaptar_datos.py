"""
Agroshift - Adaptador: convierte los archivos del equipo al formato de los contratos.

Lee (sin modificarlos) los archivos que ya existen en data/processed/:
    clima_diario_daule.csv                   (P1: NASA POWER diario)
    indices_mensuales_daule_integrados.csv   (P2: indices Landsat por mes)

Y escribe en app/data/ (la carpeta que la app lee primero):
    clima_mensual_daule.csv   fecha, anio, mes, lluvia_mm, et0_mm, balance_mm, t_media_c
    climatologia_daule.csv    mes, nombre_mes, lluvia_mm, et0_mm, balance_mm, tipo_mes, ...
    series_zonas.csv          fecha, zona_id, ndvi, ndwi, ndmi, lluvia_mm, ...

Notas:
  - La ET0 se calcula con Hargreaves (FAO-56) usando la radiacion extraterrestre
    calculada a partir de la latitud y el dia del anio.
  - La climatologia usa la MEDIANA de la lluvia para que un anio extremo
    (por ejemplo, El Nino de 2026) no distorsione el mes "tipico".
  - Mientras P3 no entregue las zonas, la serie de indices es de todo el
    recuadro y se guarda con zona_id = 0.

Uso (desde la raiz del proyecto):
    python scripts/adaptar_datos.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
SALIDA = ROOT / "app" / "data"
AOI = ROOT / "data" / "aoi_daule.geojson"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def latitud_centro() -> float:
    if AOI.exists():
        gj = json.loads(AOI.read_text(encoding="utf-8"))
        lats = [c[1] for c in gj["features"][0]["geometry"]["coordinates"][0]]
        return (min(lats) + max(lats)) / 2
    return -1.86


def radiacion_extraterrestre(fechas: pd.Series, lat_grados: float) -> pd.Series:
    """Ra en MJ/m2/dia (FAO-56, ecuaciones 21 a 25)."""
    j = fechas.dt.day_of_year.to_numpy()
    phi = np.radians(lat_grados)
    dr = 1 + 0.033 * np.cos(2 * np.pi * j / 365)
    delta = 0.409 * np.sin(2 * np.pi * j / 365 - 1.39)
    ws = np.arccos(-np.tan(phi) * np.tan(delta))
    ra = (24 * 60 / np.pi) * 0.0820 * dr * (
        ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))
    return pd.Series(ra, index=fechas.index)


def clima(lat: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = pd.read_csv(PROC / "clima_diario_daule.csv", parse_dates=["fecha"])
    rango = (d["temperatura_maxima"] - d["temperatura_minima"]).clip(lower=0)
    ra = radiacion_extraterrestre(d["fecha"], lat)
    d["et0"] = 0.0023 * (d["temperatura_media"] + 17.8) * np.sqrt(rango) * 0.408 * ra

    m = d.set_index("fecha").resample("MS").agg(
        lluvia_mm=("precipitacion", lambda s: s.sum(min_count=20)),
        et0_mm=("et0", lambda s: s.sum(min_count=20)),
        t_media_c=("temperatura_media", "mean"),
    ).reset_index()
    m["balance_mm"] = m["lluvia_mm"] - m["et0_mm"]
    m["anio"] = m["fecha"].dt.year
    m["mes"] = m["fecha"].dt.month
    m = m[["fecha", "anio", "mes", "lluvia_mm", "et0_mm", "balance_mm", "t_media_c"]]
    num = ["lluvia_mm", "et0_mm", "balance_mm", "t_media_c"]
    m[num] = m[num].round(1)

    c = m.groupby("mes").agg(
        lluvia_mm=("lluvia_mm", "median"),
        et0_mm=("et0_mm", "mean"),
        lluvia_promedio_mm=("lluvia_mm", "mean"),
        lluvia_max_mm=("lluvia_mm", "max"),
        anios=("lluvia_mm", "count"),
    ).reset_index()
    c["balance_mm"] = c["lluvia_mm"] - c["et0_mm"]
    c["tipo_mes"] = np.select(
        [c["lluvia_mm"] >= c["et0_mm"], c["lluvia_mm"] < 0.5 * c["et0_mm"]],
        ["lluvioso", "seco"], default="transicion")
    c.insert(1, "nombre_mes", [MESES[i - 1] for i in c["mes"]])
    c = c[["mes", "nombre_mes", "lluvia_mm", "et0_mm", "balance_mm", "tipo_mes",
           "lluvia_promedio_mm", "lluvia_max_mm", "anios"]].round(1)
    return m, c


def series(mensual: pd.DataFrame) -> pd.DataFrame:
    i = pd.read_csv(PROC / "indices_mensuales_daule_integrados.csv")
    i["fecha"] = pd.to_datetime(i["mes"] + "-01")
    s = i.rename(columns={"NDVI": "ndvi", "NDWI": "ndwi", "NDMI": "ndmi"})
    s["zona_id"] = 0  # todo el recuadro, hasta que P3 entregue las zonas
    s = s.merge(mensual[["fecha", "lluvia_mm"]], on="fecha", how="left")
    cols = ["fecha", "zona_id", "ndvi", "ndwi", "ndmi", "lluvia_mm", "imagenes", "calidad_cobertura"]
    s = s[[c for c in cols if c in s.columns]]
    s[["ndvi", "ndwi", "ndmi"]] = s[["ndvi", "ndwi", "ndmi"]].round(4)
    return s


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    lat = latitud_centro()

    mensual, clim = clima(lat)
    mensual.to_csv(SALIDA / "clima_mensual_daule.csv", index=False)
    clim.to_csv(SALIDA / "climatologia_daule.csv", index=False)
    serie = series(mensual)
    serie.to_csv(SALIDA / "series_zonas.csv", index=False)

    print(f"Archivos adaptados en {SALIDA}:")
    print(f"  clima_mensual_daule.csv  {len(mensual)} meses "
          f"({mensual['fecha'].min():%Y-%m} a {mensual['fecha'].max():%Y-%m})")
    print(f"  climatologia_daule.csv   12 meses (mediana de {int(clim['anios'].min())}-"
          f"{int(clim['anios'].max())} anios por mes)")
    print(f"  series_zonas.csv         {len(serie)} meses, "
          f"{int(serie['ndvi'].isna().sum())} sin imagen por nubes")
    print("\nMeses segun la climatologia:")
    for t in ["lluvioso", "transicion", "seco"]:
        print(f"  {t:<11} {', '.join(clim.loc[clim['tipo_mes'] == t, 'nombre_mes'])}")


if __name__ == "__main__":
    main()
