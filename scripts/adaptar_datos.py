"""
Agroshift - Adaptador: convierte los archivos del equipo al formato de los contratos.

Lee (sin modificarlos) los archivos que ya existen en data/processed/:
    clima_diario_daule.csv                   (P1: NASA POWER diario)
    indices_mensuales_daule_integrados.csv   (P2: indices Landsat por mes)
    lluvia_imerg_daule.csv                   (P1: GPM IMERG mensual de Mario)

Y escribe en app/data/ (la carpeta que la app lee primero):
    clima_mensual_daule.csv   fecha, anio, mes, lluvia_mm, et0_mm, balance_mm, t_media_c
    climatologia_daule.csv    mes, nombre_mes, lluvia_mm, et0_mm, balance_mm, tipo_mes, ...
    series_zonas.csv          fecha, zona_id, ndvi, ndwi, ndmi, lluvia_mm, ...
    lluvia_imerg_daule.csv    fecha, lluvia_mm, enso, temporada, lluvia_temporada_mm

Notas:
  - La ET0 se calcula con Hargreaves (FAO-56) usando la radiacion extraterrestre
    calculada a partir de la latitud y el dia del anio.
  - La climatologia usa la MEDIANA de la lluvia para que un anio extremo
    (por ejemplo, El Nino de 2026) no distorsione el mes "tipico".
  - Mientras P3 no entregue las zonas, la serie de indices es de todo el
    recuadro y se guarda con zona_id = 0.
  - Tipo de año (columna enso) con SOLO la lluvia IMERG de Mario: se suma la lluvia
    de cada temporada de lluvias (diciembre a mayo) y se ordenan las temporadas.
    La mas lluviosa = "nino" (Año muy lluvioso), la mas seca = "nina" (Año seco) y
    las demas = "neutro" (Año normal). Cada mes pertenece al año agricola de
    diciembre a noviembre ("2022-2023" = dic 2022 a nov 2023). Los meses de una
    temporada incompleta quedan como "sin_dato". No se usa ningun indice ENSO
    externo: los nombres nino/nina se mantienen solo por el contrato de datos.

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


INDICES_ZONA = PROC / "indices_por_zona.csv"   # lo escribe scripts/series_por_zona.py
COBERTURA_MIN_ZONA = 10.0                      # % de la zona sin nubes para usar el promedio del mes


def series(mensual: pd.DataFrame) -> pd.DataFrame:
    """
    zona_id 0 = todo el recuadro (serie de P2, sin cambios en ndvi, ndwi y ndmi).
    Si existe data/processed/indices_por_zona.csv (scripts/series_por_zona.py), se agregan
    las zonas 1, 2 y 3 de P3 y la columna pct_agua (% de la zona con NDWI > 0).
    """
    i = pd.read_csv(PROC / "indices_mensuales_daule_integrados.csv")
    i["fecha"] = pd.to_datetime(i["mes"] + "-01")
    s = i.rename(columns={"NDVI": "ndvi", "NDWI": "ndwi", "NDMI": "ndmi"})
    s["zona_id"] = 0
    if INDICES_ZONA.exists():
        z = pd.read_csv(INDICES_ZONA, parse_dates=["fecha"])
        s = s.merge(z.loc[z["zona_id"] == 0, ["fecha", "pct_agua"]], on="fecha", how="left")
        zonas = z[z["zona_id"] != 0].rename(columns={"cobertura_pct": "cobertura_zona_pct"})
        # Con menos del 10 % de la zona sin nubes el promedio no es confiable: se trata como sin foto
        poca = zonas["cobertura_zona_pct"] < COBERTURA_MIN_ZONA
        zonas.loc[poca, ["ndvi", "ndwi", "ndmi", "pct_agua"]] = float("nan")
        s = pd.concat([s, zonas], ignore_index=True)
    s = s.merge(mensual[["fecha", "lluvia_mm"]], on="fecha", how="left")
    cols = ["fecha", "zona_id", "ndvi", "ndwi", "ndmi", "lluvia_mm", "pct_agua", "imagenes",
            "calidad_cobertura", "cobertura_zona_pct"]
    s = s[[c for c in cols if c in s.columns]].sort_values(["zona_id", "fecha"]).reset_index(drop=True)
    s[["ndvi", "ndwi", "ndmi"]] = s[["ndvi", "ndwi", "ndmi"]].round(4)
    return s


MESES_LLUVIA = [12, 1, 2, 3, 4, 5]   # temporada de lluvias: diciembre a mayo
NOMBRE_TIPO_ANIO = {"nino": "Año muy lluvioso", "neutro": "Año normal", "nina": "Año seco"}


def temporada_de(fecha: pd.Timestamp) -> str:
    """Año agricola de diciembre a noviembre: dic 2022 a nov 2023 -> '2022-2023'."""
    inicio = fecha.year if fecha.month == 12 else fecha.year - 1
    return f"{inicio}-{inicio + 1}"


def imerg() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Serie IMERG de Mario en el formato del contrato y el resumen por temporada."""
    m = pd.read_csv(PROC / "lluvia_imerg_daule.csv")
    m["fecha"] = pd.to_datetime(m["mes"] + "-01")
    m["lluvia_mm"] = m["precipitacion_imerg_mm"].round(1)
    completa = (m["serie_completa"].astype(str).str.lower() == "true"
                if "serie_completa" in m else pd.Series(True, index=m.index))
    m["temporada"] = m["fecha"].map(temporada_de)

    lluvias = m[m["fecha"].dt.month.isin(MESES_LLUVIA)]
    t = lluvias.assign(completo=completa[lluvias.index]).groupby("temporada").agg(
        lluvia_temporada_mm=("precipitacion_imerg_mm", "sum"),
        meses=("fecha", "count"), completos=("completo", "all")).reset_index()
    t = t[(t["meses"] == len(MESES_LLUVIA)) & t["completos"]].copy()
    t["lluvia_temporada_mm"] = t["lluvia_temporada_mm"].round(1)
    t = t.sort_values("lluvia_temporada_mm", ascending=False).reset_index(drop=True)
    t["enso"] = "neutro"
    if len(t) >= 2:
        t.loc[0, "enso"] = "nino"
        t.loc[len(t) - 1, "enso"] = "nina"

    m = m.merge(t[["temporada", "enso", "lluvia_temporada_mm"]], on="temporada", how="left")
    m["enso"] = m["enso"].fillna("sin_dato")
    return m[["fecha", "lluvia_mm", "enso", "temporada", "lluvia_temporada_mm"]], t


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    lat = latitud_centro()

    mensual, clim = clima(lat)
    mensual.to_csv(SALIDA / "clima_mensual_daule.csv", index=False)
    clim.to_csv(SALIDA / "climatologia_daule.csv", index=False)
    serie = series(mensual)
    serie.to_csv(SALIDA / "series_zonas.csv", index=False)
    lluvia, temporadas = imerg()
    lluvia.to_csv(SALIDA / "lluvia_imerg_daule.csv", index=False)

    print(f"Archivos adaptados en {SALIDA}:")
    print(f"  clima_mensual_daule.csv  {len(mensual)} meses "
          f"({mensual['fecha'].min():%Y-%m} a {mensual['fecha'].max():%Y-%m})")
    print(f"  climatologia_daule.csv   12 meses (mediana de {int(clim['anios'].min())}-"
          f"{int(clim['anios'].max())} anios por mes)")
    print(f"  series_zonas.csv         {len(serie)} meses, "
          f"{int(serie['ndvi'].isna().sum())} sin imagen por nubes")
    print(f"  lluvia_imerg_daule.csv   {len(lluvia)} meses "
          f"({lluvia['fecha'].min():%Y-%m} a {lluvia['fecha'].max():%Y-%m}), "
          f"{int((lluvia['enso'] == 'sin_dato').sum())} sin temporada completa")
    print("\nMeses segun la climatologia:")
    for t in ["lluvioso", "transicion", "seco"]:
        print(f"  {t:<11} {', '.join(clim.loc[clim['tipo_mes'] == t, 'nombre_mes'])}")
    print("\nTipo de año segun la lluvia IMERG de diciembre a mayo:")
    for _, f in temporadas.iterrows():
        print(f"  {f['temporada']}  {f['lluvia_temporada_mm']:7.1f} mm  -> {f['enso']:<6} "
              f"({NOMBRE_TIPO_ANIO[f['enso']]})")


if __name__ == "__main__":
    main()
