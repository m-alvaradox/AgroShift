"""
P2 · Imágenes satelitales — Landsat 8 y 9 en Google Earth Engine.

Qué hace:
  1. Filtra Landsat 8 y 9 (Collection 2, Level 2, reflectancia de superficie)
     por el recuadro del área de estudio y los últimos 5 años.
  2. Quita nubes, sombras, cirros y nieve con la banda QA_PIXEL.
  3. Arma un compuesto por mes con la mediana. Los huecos por nubes se rellenan
     (salvo con --sin-relleno) primero con Sentinel-2 del mismo mes y luego con
     Landsat de una ventana de 3 meses centrada en el mes.
  4. Calcula NDVI, NDWI y NDMI y exporta un GeoTIFF por mes (AAAA_MM.tif)
     con las bandas ndvi, ndwi, ndmi a 30 m, recortado al recuadro.
  5. Anota en un CSV cuántas imágenes y qué porcentaje del recuadro quedó
     cubierto cada mes, solo con Landsat, con Sentinel-2 y al final.

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


def _indices_o_vacia(col: ee.ImageCollection, fn_indices) -> ee.Image:
    """Mediana de la colección con sus índices; imagen enmascarada si está vacía."""
    vacia = ee.Image.constant([0, 0, 0]).rename(["ndvi", "ndwi", "ndmi"]).float().updateMask(0)
    return ee.Image(ee.Algorithms.If(col.size().gt(0), fn_indices(col.median()), vacia)).toFloat()


# --- Sentinel-2 (relleno del mismo mes) ------------------------------------ #
def coleccion_s2(aoi: ee.Geometry, inicio: str, fin: str) -> ee.ImageCollection:
    cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(aoi)
        .filterDate(inicio, fin)
        .linkCollection(cs, ["cs_cdf"])
    )
    # Cloud Score+: 1 = despejado, 0 = nube. 0.6 es el umbral recomendado por Google.
    return s2.map(
        lambda img: img.updateMask(img.select("cs_cdf").gte(0.6))
        .select(["B3", "B4", "B8", "B11"])
        .divide(10000)
    )


def indices_s2(img: ee.Image) -> ee.Image:
    # Sentinel-2: B3 verde, B4 rojo, B8 NIR, B11 SWIR1 (equivalentes a OLI B3, B4, B5, B6)
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("ndvi")
    ndwi = img.normalizedDifference(["B3", "B8"]).rename("ndwi")
    ndmi = img.normalizedDifference(["B8", "B11"]).rename("ndmi")
    return ndvi.addBands([ndwi, ndmi])


def compuesto_mensual(aoi: ee.Geometry, anio: int, mes: int, rellenar: bool = True) -> dict:
    """
    Compuesto del mes en 3 pasos (cada paso solo llena los píxeles que siguen vacíos):
      1. Landsat 8/9 del mes (dato principal).
      2. Sentinel-2 del mismo mes (misma fecha, otro satélite).
      3. Landsat de una ventana de 3 meses (mes anterior, el mes y el siguiente).
    """
    inicio, fin = rango_mes(anio, mes)
    col_ls = coleccion(aoi, inicio, fin)
    ls = _indices_o_vacia(col_ls, agregar_indices)

    if not rellenar:
        return {"imagen": ls.clip(aoi), "pasos": [ls], "n_ls": col_ls.size(), "n_s2": ee.Number(0)}

    col_s2 = coleccion_s2(aoi, inicio, fin)
    s2 = _indices_o_vacia(col_s2, indices_s2)

    ini_v = ee.Date(inicio).advance(-1, "month")
    fin_v = ee.Date(fin).advance(1, "month")
    ventana = _indices_o_vacia(coleccion(aoi, ini_v, fin_v), agregar_indices)

    paso2 = ls.unmask(s2)
    paso3 = paso2.unmask(ventana)
    return {
        "imagen": paso3.clip(aoi),
        "pasos": [ls, paso2, paso3],
        "n_ls": col_ls.size(),
        "n_s2": col_s2.size(),
    }


def porcentajes_cubiertos(imagenes: list[ee.Image], aoi: ee.Geometry) -> list[float]:
    """% del recuadro con dato válido en cada imagen (una sola consulta a Earth Engine)."""
    bandas = [img.select("ndvi").mask().gt(0).unmask(0).rename(f"p{i}") for i, img in enumerate(imagenes)]
    medias = ee.Image.cat(bandas).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=aoi, scale=ESCALA_M, maxPixels=1e9
    ).getInfo()
    return [round(100 * float(medias.get(f"p{i}") or 0), 2) for i in range(len(imagenes))]


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
    p.add_argument("--sin-relleno", action="store_true",
                   help="Solo Landsat del mes, sin rellenar huecos con Sentinel-2 ni con la ventana de 3 meses")
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
        c = compuesto_mensual(aoi, anio, mes, rellenar=not args.sin_relleno)
        n_ls, n_s2 = int(c["n_ls"].getInfo()), int(c["n_s2"].getInfo())
        pcts = porcentajes_cubiertos(c["pasos"], aoi)
        pct_ls, pct_final = pcts[0], pcts[-1]
        pct_s2 = pcts[1] if len(pcts) > 1 else pct_ls

        filas.append(
            {"mes": f"{anio}-{mes:02d}", "imagenes": n_ls,
             "cobertura_pct": pct_final, "calidad_cobertura": calidad(pct_final),
             "imagenes_s2": n_s2, "cobertura_landsat_pct": pct_ls,
             "cobertura_con_s2_pct": pct_s2}
        )
        estado = (f"{nombre}: L {n_ls} img {pct_ls:5.1f}% | +S2 {n_s2} img {pct_s2:5.1f}% "
                  f"| final {pct_final:5.1f}% ({calidad(pct_final)})")

        if args.solo_cobertura or pct_final == 0:
            print(estado + ("  -> sin datos, no se exporta" if pct_final == 0 else ""))
            continue

        if args.destino == "drive":
            exportar_drive(c["imagen"], aoi, nombre)
            print(estado + f"  -> tarea enviada a Drive/{CARPETA_DRIVE}")
        else:
            archivo = SALIDA / f"{nombre}.tif"
            if archivo.exists() and not args.sobrescribir:
                print(estado + "  -> ya existe, se omite")
                continue
            descargar_local(c["imagen"], aoi, archivo)
            print(estado + f"  -> {archivo.relative_to(RAIZ)}")

    registro = SALIDA / "cobertura_landsat.csv"
    with registro.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["mes", "imagenes", "cobertura_pct", "calidad_cobertura",
                                          "imagenes_s2", "cobertura_landsat_pct", "cobertura_con_s2_pct"])
        w.writeheader()
        w.writerows(filas)

    huecos = [r["mes"] for r in filas if r["calidad_cobertura"] != "alta"]
    print(f"\nRegistro: {registro.relative_to(RAIZ)}")
    print(f"Meses con huecos por nubes ({len(huecos)}): {', '.join(huecos) or 'ninguno'}")


if __name__ == "__main__":
    main()
