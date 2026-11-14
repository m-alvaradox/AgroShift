"""
P2 · Imágenes satelitales — Landsat 8 y 9 en Google Earth Engine.

Qué hace:
  1. Filtra Landsat 8 y 9 (Collection 2, Level 2, reflectancia de superficie)
     por el recuadro del área de estudio y los últimos 5 años.
  2. Quita nubes, sombras, cirros y nieve con la banda QA_PIXEL.
  3. Arma un compuesto por mes con la mediana.
  4. Calcula NDVI, NDWI y NDMI y exporta un GeoTIFF por mes (AAAA_MM.tif)
     con las bandas ndvi, ndwi, ndmi a 30 m, recortado al recuadro.
  5. Anota en un CSV cuántas imágenes y qué porcentaje del recuadro quedó
     cubierto cada mes (los meses con huecos por nubes).

Contrato de datos (plan del equipo):
  data/processed/landsat/AAAA_MM.tif  -> bandas ndvi, ndwi, ndmi, 30 m  (lo usa P3)
  data/processed/landsat/cobertura_landsat.csv -> registro de huecos por nubes

Uso:
  python src/landsat_gee.py --proyecto MI-PROYECTO-GEE                # descarga local
  python src/landsat_gee.py --proyecto MI-PROYECTO-GEE --destino drive
  python src/landsat_gee.py --proyecto MI-PROYECTO-GEE --solo-cobertura

Requiere: earthengine-api, requests (y haber corrido `earthengine authenticate`).
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

import ee
import requests

RAIZ = Path(__file__).resolve().parents[1]
AOI_GEOJSON = RAIZ / "data" / "aoi_daule.geojson"
SALIDA = RAIZ / "data" / "processed" / "landsat"
CARPETA_DRIVE = "agroshift_landsat"

# Recuadro de respaldo mientras P1 entrega data/aoi_daule.geojson.
# Centrado en el punto que usa descargar_nasa_power.py (-1.86, -79.98), ~10 x 10 km.
# [oeste, sur, este, norte]
BBOX_RESPALDO = [-80.03, -1.91, -79.93, -1.81]

ESCALA_M = 30
ANIOS = 5


# --------------------------------------------------------------------------- #
# Área de estudio
# --------------------------------------------------------------------------- #
def cargar_aoi() -> ee.Geometry:
    if AOI_GEOJSON.exists():
        gj = json.loads(AOI_GEOJSON.read_text(encoding="utf-8"))
        geom = gj["features"][0]["geometry"] if gj.get("type") == "FeatureCollection" else gj.get("geometry", gj)
        print(f"AOI: {AOI_GEOJSON.relative_to(RAIZ)}")
        return ee.Geometry(geom)
    print(f"AVISO: no existe {AOI_GEOJSON.relative_to(RAIZ)}; uso el recuadro de respaldo {BBOX_RESPALDO}")
    return ee.Geometry.Rectangle(BBOX_RESPALDO)


# --------------------------------------------------------------------------- #
# Landsat: máscara de nubes, factores de escala e índices
# --------------------------------------------------------------------------- #
def enmascarar_y_escalar(img: ee.Image) -> ee.Image:
    qa = img.select("QA_PIXEL")
    # Bits QA_PIXEL: 1 nube dilatada, 2 cirro, 3 nube, 4 sombra de nube, 5 nieve
    malos = (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5)
    limpio = qa.bitwiseAnd(malos).eq(0)
    # Píxeles saturados
    limpio = limpio.And(img.select("QA_RADSAT").eq(0))

    # Factores de escala de Collection 2 Level 2
    sr = img.select("SR_B.").multiply(0.0000275).add(-0.2)
    return img.addBands(sr, None, True).updateMask(limpio)


def agregar_indices(img: ee.Image) -> ee.Image:
    # Landsat 8/9 OLI: B3 verde, B4 rojo, B5 NIR, B6 SWIR1
    ndvi = img.normalizedDifference(["SR_B5", "SR_B4"]).rename("ndvi")
    ndwi = img.normalizedDifference(["SR_B3", "SR_B5"]).rename("ndwi")  # McFeeters (agua abierta)
    ndmi = img.normalizedDifference(["SR_B5", "SR_B6"]).rename("ndmi")  # humedad de la vegetación
    return ndvi.addBands([ndwi, ndmi])


def coleccion(aoi: ee.Geometry, inicio: str, fin: str) -> ee.ImageCollection:
    l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
    return (
        l8.merge(l9)
        .filterBounds(aoi)
        .filterDate(inicio, fin)
        .map(enmascarar_y_escalar)
    )


# --------------------------------------------------------------------------- #
# Meses
# --------------------------------------------------------------------------- #
def lista_meses(anios: int) -> list[tuple[int, int]]:
    hoy = date.today()
    # Último mes completo
    anio_fin, mes_fin = (hoy.year, hoy.month - 1) if hoy.month > 1 else (hoy.year - 1, 12)
    meses = []
    a, m = anio_fin, mes_fin
    for _ in range(anios * 12):
        meses.append((a, m))
        a, m = (a, m - 1) if m > 1 else (a - 1, 12)
    return sorted(meses)


def rango_mes(anio: int, mes: int) -> tuple[str, str]:
    sig = (anio + 1, 1) if mes == 12 else (anio, mes + 1)
    return f"{anio}-{mes:02d}-01", f"{sig[0]}-{sig[1]:02d}-01"


def compuesto_mensual(aoi: ee.Geometry, anio: int, mes: int) -> tuple[ee.Image, ee.Number]:
    inicio, fin = rango_mes(anio, mes)
    col = coleccion(aoi, inicio, fin)
    n = col.size()
    # Si no hay imágenes, devolvemos una imagen enmascarada con las 3 bandas
    vacia = ee.Image.constant([0, 0, 0]).rename(["ndvi", "ndwi", "ndmi"]).float().updateMask(0)
    comp = ee.Image(
        ee.Algorithms.If(n.gt(0), agregar_indices(col.median()), vacia)
    ).toFloat().clip(aoi)
    return comp, n


def porcentaje_cubierto(img: ee.Image, aoi: ee.Geometry) -> ee.Number:
    valido = img.select("ndvi").mask().gt(0).unmask(0)
    media = valido.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=aoi, scale=ESCALA_M, maxPixels=1e9
    ).get("ndvi")
    return ee.Number(ee.Algorithms.If(media, media, 0)).multiply(100)


def calidad(pct: float) -> str:
    if pct >= 80:
        return "alta"
    if pct >= 40:
        return "intermedia"
    return "baja"


# --------------------------------------------------------------------------- #
# Exportación
# --------------------------------------------------------------------------- #
def descargar_local(img: ee.Image, aoi: ee.Geometry, destino: Path) -> None:
    url = img.getDownloadURL(
        {
            "bands": ["ndvi", "ndwi", "ndmi"],
            "region": aoi,
            "scale": ESCALA_M,
            "crs": "EPSG:4326",
            "format": "GEO_TIFF",
        }
    )
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    destino.write_bytes(r.content)


def exportar_drive(img: ee.Image, aoi: ee.Geometry, nombre: str) -> None:
    tarea = ee.batch.Export.image.toDrive(
        image=img.select(["ndvi", "ndwi", "ndmi"]),
        description=f"landsat_{nombre}",
        folder=CARPETA_DRIVE,
        fileNamePrefix=nombre,
        region=aoi,
        scale=ESCALA_M,
        crs="EPSG:4326",
        maxPixels=1e10,
    )
    tarea.start()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--proyecto", required=True, help="ID del proyecto de Google Cloud con Earth Engine")
    p.add_argument("--destino", choices=["local", "drive"], default="local")
    p.add_argument("--anios", type=int, default=ANIOS)
    p.add_argument("--solo-cobertura", action="store_true", help="Solo calcula el registro de huecos, sin exportar")
    p.add_argument("--sobrescribir", action="store_true", help="Vuelve a descargar meses que ya existen")
    args = p.parse_args()

    ee.Initialize(project=args.proyecto)
    aoi = cargar_aoi()
    SALIDA.mkdir(parents=True, exist_ok=True)

    filas = []
    meses = lista_meses(args.anios)
    print(f"Procesando {len(meses)} meses: {meses[0][0]}-{meses[0][1]:02d} a {meses[-1][0]}-{meses[-1][1]:02d}")

    for anio, mes in meses:
        nombre = f"{anio}_{mes:02d}"
        comp, n = compuesto_mensual(aoi, anio, mes)
        n_img = int(n.getInfo())
        pct = float(porcentaje_cubierto(comp, aoi).getInfo()) if n_img else 0.0
        filas.append(
            {"mes": f"{anio}-{mes:02d}", "imagenes": n_img,
             "cobertura_pct": round(pct, 2), "calidad_cobertura": calidad(pct)}
        )
        estado = f"{nombre}: {n_img} imágenes, {pct:5.1f}% cubierto ({calidad(pct)})"

        if args.solo_cobertura or n_img == 0:
            print(estado + ("  -> sin imágenes, no se exporta" if n_img == 0 else ""))
            continue

        if args.destino == "drive":
            exportar_drive(comp, aoi, nombre)
            print(estado + f"  -> tarea enviada a Drive/{CARPETA_DRIVE}")
        else:
            archivo = SALIDA / f"{nombre}.tif"
            if archivo.exists() and not args.sobrescribir:
                print(estado + "  -> ya existe, se omite")
                continue
            descargar_local(comp, aoi, archivo)
            print(estado + f"  -> {archivo.relative_to(RAIZ)}")

    registro = SALIDA / "cobertura_landsat.csv"
    with registro.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["mes", "imagenes", "cobertura_pct", "calidad_cobertura"])
        w.writeheader()
        w.writerows(filas)

    huecos = [r["mes"] for r in filas if r["calidad_cobertura"] != "alta"]
    print(f"\nRegistro: {registro.relative_to(RAIZ)}")
    print(f"Meses con huecos por nubes ({len(huecos)}): {', '.join(huecos) or 'ninguno'}")


if __name__ == "__main__":
    main()
