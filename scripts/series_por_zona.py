"""
Agroshift - Series de satelite POR ZONA e imagenes de cada mes (Google Earth Engine).

Que hace (noviembre 2021 a octubre 2026):
  1. Compuesto mensual de Landsat 8 y 9 (Collection 2 Level 2): nubes, sombras y
     cirros quitados con QA_PIXEL y mediana del mes. Usa las MISMAS funciones de
     scripts/landsat_gee.py (P2, Thomas): enmascarar_y_escalar, agregar_indices,
     coleccion y rango_mes. Solo Landsat del mes, sin relleno con Sentinel-2.
  2. NDVI, NDWI y NDMI y su promedio en cada zona de data/processed/zonas_daule.geojson
     (P3, Austin) con reduceRegions a 30 m. Tambien:
       pct_agua      % de pixeles con foto de la zona con NDWI > 0 (agua sobre el terreno)
       cobertura_pct % de la zona con foto sin nubes ese mes
     La zona 0 es todo el recuadro de data/aoi_daule.geojson (el mismo de la serie de P2).
  3. Una miniatura PNG por mes del recuadro de las zonas (~400 px): color verdadero y
     verdor (NDVI). Si el mes casi no tiene foto limpia, se marca "sin imagen por nubes".

Escribe:
  data/processed/indices_por_zona.csv   fecha, zona_id, ndvi, ndwi, ndmi, pct_agua, cobertura_pct
  app/static/meses/AAAA_MM_color.png y AAAA_MM_ndvi.png
  app/data/meses_satelite.csv           fecha, cobertura_pct, estado, color, ndvi
  y vuelve a armar app/data/series_zonas.csv con scripts/adaptar_datos.py
  (zona 0 = serie de P2 + pct_agua; zonas 1, 2 y 3 = esta serie; lluvia de NASA POWER).

Las geometrias de las zonas se simplifican (~55 m) solo para enviarlas a Earth Engine.

Uso (desde la raiz del proyecto; requiere `earthengine authenticate`):
    python scripts/series_por_zona.py
    python scripts/series_por_zona.py --proyecto OTRO-PROYECTO --sin-imagenes
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import ee
import pandas as pd
import requests
from PIL import Image
from shapely import set_precision
from shapely.geometry import mapping, shape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "app"))
from landsat_gee import agregar_indices, coleccion, rango_mes  # noqa: E402  (P2, Thomas)
from utils.carga import leer_json_archivo  # noqa: E402

PROYECTO = os.environ.get("EE_PROYECTO", "unique-rarity-514718-n5")
ZONAS = ROOT / "data" / "processed" / "zonas_daule.geojson"
AOI = ROOT / "data" / "aoi_daule.geojson"
SALIDA_CSV = ROOT / "data" / "processed" / "indices_por_zona.csv"
CARPETA_IMG = ROOT / "app" / "static" / "meses"
MESES_CSV = ROOT / "app" / "data" / "meses_satelite.csv"
INICIO, FIN = (2021, 11), (2026, 10)
ESCALA_M = 30
TOLERANCIA = 0.0005          # grados (~55 m), solo para enviar las zonas a Earth Engine
ANCHO_PX = 400
MIN_COBERTURA_IMG = 15.0     # % del recuadro con foto limpia para guardar la miniatura
VIS_COLOR = {"bands": ["SR_B4", "SR_B3", "SR_B2"], "min": 0.0, "max": 0.25, "gamma": 1.25}
VIS_NDVI = {"min": 0.0, "max": 0.8, "palette": ["8c510a", "dfc27d", "f6e8c3", "a6d96a", "1a9850", "00441b"]}


def meses() -> list[tuple[int, int]]:
    a, m, salida = *INICIO, []
    while (a, m) <= FIN:
        salida.append((a, m))
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return salida


def zonas_ee() -> tuple[ee.FeatureCollection, ee.Geometry]:
    """Zonas 1-3 (simplificadas) + zona 0 (recuadro de P2) y el recuadro de las imagenes."""
    feats = []
    for f in leer_json_archivo(ZONAS)["features"]:
        geom = set_precision(shape(f["geometry"]).simplify(TOLERANCIA, preserve_topology=True), 1e-5)
        feats.append(ee.Feature(ee.Geometry(mapping(geom)), {"zona_id": int(f["properties"]["zona_id"])}))
    aoi = json.loads(AOI.read_text(encoding="utf-8"))["features"][0]["geometry"]
    feats.append(ee.Feature(ee.Geometry(aoi), {"zona_id": 0}))
    fc = ee.FeatureCollection(feats)
    recuadro = fc.filter(ee.Filter.neq("zona_id", 0)).geometry().bounds(1)
    return fc, recuadro


def compuesto(anio: int, mes: int, region: ee.Geometry) -> ee.Image:
    """Mediana del mes de Landsat 8/9 (reflectancia escalada y sin nubes) con sus indices."""
    ini, fin = rango_mes(anio, mes)
    col = coleccion(region, ini, fin)
    vacia = ee.Image.constant([0] * 9).rename(
        ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "ndvi", "ndwi", "ndmi", "n"]).float().updateMask(0)
    def armar():
        med = col.median()
        return med.select(["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6"]).addBands(agregar_indices(med)) \
            .addBands(ee.Image.constant(1).rename("n")).toFloat()
    return ee.Image(ee.Algorithms.If(col.size().gt(0), armar(), vacia)), col.size()


def estadisticas(img: ee.Image, fc: ee.FeatureCollection) -> list[dict]:
    """Promedio por zona de los indices, % de agua (NDWI > 0) y % con foto."""
    ind = img.select(["ndvi", "ndwi", "ndmi"])
    agua = ind.select("ndwi").gt(0).rename("agua")            # enmascarada donde no hay foto
    cubre = ind.select("ndvi").mask().gt(0).unmask(0).rename("cubre")
    tabla = ind.addBands(agua).addBands(cubre).reduceRegions(
        collection=fc, reducer=ee.Reducer.mean(), scale=ESCALA_M, tileScale=4).getInfo()
    return [f["properties"] for f in tabla["features"]]


def miniatura(img: ee.Image, vis: dict, region: ee.Geometry, destino: Path) -> None:
    url = img.visualize(**vis).getThumbURL({"region": region, "dimensions": ANCHO_PX, "format": "png"})
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    destino.write_bytes(r.content)
    optimizar_png(destino)


def optimizar_png(ruta: Path, colores: int = 128) -> None:
    """Sigue siendo PNG con transparencia, pero con paleta de 128 colores: pesa ~3 veces menos."""
    img = Image.open(ruta).convert("RGBA")
    img.quantize(colors=colores, method=Image.Quantize.FASTOCTREE).save(ruta, optimize=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--proyecto", default=PROYECTO, help="proyecto de Google Cloud con Earth Engine")
    ap.add_argument("--sin-imagenes", action="store_true", help="solo las series, sin miniaturas")
    ap.add_argument("--sobrescribir", action="store_true", help="vuelve a bajar miniaturas que ya existen")
    a = ap.parse_args()

    ee.Initialize(project=a.proyecto)
    fc, recuadro = zonas_ee()
    CARPETA_IMG.mkdir(parents=True, exist_ok=True)
    filas, imagenes = [], []
    for anio, mes in meses():
        etiqueta = f"{anio}_{mes:02d}"
        img, n = compuesto(anio, mes, recuadro)
        n = int(n.getInfo())
        stats = estadisticas(img, fc) if n else []
        for s in stats:
            filas.append({"fecha": f"{anio}-{mes:02d}-01", "zona_id": int(s["zona_id"]),
                          "ndvi": s.get("ndvi"), "ndwi": s.get("ndwi"), "ndmi": s.get("ndmi"),
                          "pct_agua": None if s.get("agua") is None else round(100 * s["agua"], 2),
                          "cobertura_pct": round(100 * (s.get("cubre") or 0), 1), "imagenes": n})
        # cobertura del recuadro de las imagenes: promedio de las 3 zonas pesado por su superficie
        cub = [s for s in stats if s["zona_id"] != 0]
        cobertura = round(sum(100 * (s.get("cubre") or 0) for s in cub) / len(cub), 1) if cub else 0.0
        fila_img = {"fecha": f"{anio}-{mes:02d}-01", "imagenes": n, "cobertura_pct": cobertura,
                    "estado": "sin imagen por nubes", "color": "", "ndvi": ""}
        if cobertura >= MIN_COBERTURA_IMG:
            fila_img["estado"] = "limpia" if cobertura >= 80 else "parcial"
            if not a.sin_imagenes:
                for tipo, vis in (("color", VIS_COLOR), ("ndvi", VIS_NDVI)):
                    destino = CARPETA_IMG / f"{etiqueta}_{tipo}.png"
                    if a.sobrescribir or not destino.exists():
                        fuente = img.select(vis["bands"]) if tipo == "color" else img.select("ndvi")
                        miniatura(fuente, {k: v for k, v in vis.items() if k != "bands"} if tipo == "ndvi"
                                  else vis, recuadro, destino)
                    fila_img[tipo] = destino.relative_to(ROOT / "app").as_posix()
        imagenes.append(fila_img)
        zona1 = next((s for s in stats if s["zona_id"] == 1), {})
        print(f"{etiqueta}: {n} img | cobertura {cobertura:5.1f}% | {fila_img['estado']:<20} | "
              f"zona baja agua {100 * (zona1.get('agua') or 0):5.2f}%")

    df = pd.DataFrame(filas).sort_values(["fecha", "zona_id"])
    for c in ("ndvi", "ndwi", "ndmi"):
        df[c] = df[c].astype(float).round(4)
    df.to_csv(SALIDA_CSV, index=False)
    pd.DataFrame(imagenes).to_csv(MESES_CSV, index=False)
    print(f"\n{SALIDA_CSV.relative_to(ROOT).as_posix()}: {len(df)} filas; "
          f"{MESES_CSV.relative_to(ROOT).as_posix()}: {len(imagenes)} meses")

    # Volver a armar app/data/series_zonas.csv (zona 0 de P2 + zonas 1, 2 y 3)
    import adaptar_datos
    mensual, _ = adaptar_datos.clima(adaptar_datos.latitud_centro())
    serie = adaptar_datos.series(mensual)
    serie.to_csv(adaptar_datos.SALIDA / "series_zonas.csv", index=False)
    print(f"app/data/series_zonas.csv: zonas {sorted(serie['zona_id'].unique())}, {len(serie)} filas")


if __name__ == "__main__":
    main()
