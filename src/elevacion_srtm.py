"""
Agroshift - Paso 3: elevacion y pendiente con SRTM (Earth Engine) para Daule.

Que hace:
  1. Lee el recuadro desde data/aoi_daule.geojson
  2. Toma la elevacion SRTM de 30 m y calcula la pendiente, recortadas al recuadro.
  3. Imprime estadisticas: que tan alto es el terreno y que parte queda por
     debajo de distintos umbrales (para elegir el limite zona baja / loma).
  4. Descarga un GeoTIFF pequeno con 3 bandas: elevacion, pendiente y zona_baja.

Uso (desde la carpeta raiz del proyecto, con el venv activado):
    python src/elevacion_srtm.py

Salida:
    data/processed/srtm_daule.tif   (abrir en QGIS)
"""
import json
from pathlib import Path

import ee
import requests

# --- Configuracion -----------------------------------------------------------
PROYECTO = "unique-rarity-514718-n5"   # ID de tu proyecto de Google Cloud
UMBRAL_M = 15                          # por debajo = zona baja; ajustalo viendo el mapa
UMBRALES_PRUEBA = [10, 15, 20, 30]     # para comparar que parte queda "baja"

ROOT = Path(__file__).resolve().parents[1]
AOI = ROOT / "data" / "aoi_daule.geojson"
PROC = ROOT / "data" / "processed"


def cargar_aoi() -> ee.Geometry:
    gj = json.loads(AOI.read_text(encoding="utf-8"))
    return ee.Geometry(gj["features"][0]["geometry"])


def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    ee.Initialize(project=PROYECTO)
    aoi = cargar_aoi()

    srtm = ee.Image("USGS/SRTMGL1_003").select("elevation")
    # La pendiente se calcula ANTES de recortar para evitar errores en los bordes
    pendiente = ee.Terrain.slope(srtm).clip(aoi)
    elevacion = srtm.clip(aoi)

    # --- Estadisticas de elevacion --------------------------------------------
    reductor = ee.Reducer.percentile([5, 25, 50, 75, 95]).combine(
        ee.Reducer.minMax(), sharedInputs=True
    )
    est = elevacion.reduceRegion(
        reducer=reductor, geometry=aoi, scale=30, maxPixels=1e9
    ).getInfo()

    print("\nElevacion del recuadro (metros sobre el nivel del mar):")
    print(f"  minima: {est['elevation_min']}   maxima: {est['elevation_max']}")
    print(f"  5% del area esta por debajo de   {est['elevation_p5']} m")
    print(f"  25% del area esta por debajo de  {est['elevation_p25']} m")
    print(f"  mediana:                          {est['elevation_p50']} m")
    print(f"  75% del area esta por debajo de  {est['elevation_p75']} m")
    print(f"  95% del area esta por debajo de  {est['elevation_p95']} m")

    print("\nQue parte del recuadro quedaria como 'zona baja' segun el umbral:")
    for u in UMBRALES_PRUEBA:
        frac = elevacion.lt(u).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=30, maxPixels=1e9
        ).get("elevation").getInfo()
        print(f"  por debajo de {u:>3} m: {frac * 100:5.1f} %")

    est_pend = pendiente.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.percentile([90]), sharedInputs=True),
        geometry=aoi, scale=30, maxPixels=1e9,
    ).getInfo()
    print(f"\nPendiente media: {est_pend['slope_mean']:.1f} grados "
          f"(el 10% mas inclinado supera {est_pend['slope_p90']:.1f} grados)")

    # --- Descarga del GeoTIFF -------------------------------------------------
    zona_baja = elevacion.lt(UMBRAL_M).rename("zona_baja")
    imagen = (
        elevacion.rename("elevacion")
        .addBands(pendiente.rename("pendiente"))
        .addBands(zona_baja)
        .toFloat()
    )
    url = imagen.getDownloadURL({
        "name": "srtm_daule",
        "scale": 30,
        "region": aoi,
        "crs": "EPSG:4326",
        "format": "GEO_TIFF",
    })
    print("\nDescargando GeoTIFF recortado ...")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    salida = PROC / "srtm_daule.tif"
    salida.write_bytes(r.content)
    print(f"Guardado: {salida} ({len(r.content) / 1e6:.1f} MB)")
    print(f"Banda 3 'zona_baja' usa el umbral de {UMBRAL_M} m (1 = baja, 0 = loma).")


if __name__ == "__main__":
    main()
