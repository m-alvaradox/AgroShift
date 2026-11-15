"""P3 · Elevación SRTM -> data/processed/srtm_daule.tif

Bandas (contrato): elevacion (m), pendiente (grados), zona_baja (1 = bajo el umbral, 0 = no)

Uso:
    python src/elevacion_srtm.py --desde-locales                      # usa elevacion_daule_utm.tif y pendiente_daule.tif
    python src/elevacion_srtm.py --proyecto TU_PROYECTO_EE            # o descarga de Earth Engine
    python src/elevacion_srtm.py --solo-umbral 14                     # recalcula zona_baja sin internet
    python src/elevacion_srtm.py --mock --solo-umbral 14              # lo mismo sobre data/mock

Ajuste del umbral: abre srtm_daule.tif en QGIS, pinta la banda elevacion con pseudocolor y
compara con el río Daule y los arrozales de una imagen satelital (XYZ de Google o Esri).
Cuando encuentres el valor que separa la zona baja de la loma, corre --solo-umbral con ese valor.
"""
import argparse

import numpy as np

from p3_comun import carpeta, leer_bbox, iniciar_ee, descargar_ee, leer_raster, escribir_raster

NOMBRES = ["elevacion", "pendiente", "zona_baja"]


def resumen_elevacion(elev):
    v = elev[np.isfinite(elev)]
    pct = np.percentile(v, [5, 25, 50, 75, 95])
    print("Elevación (m)  p5={:.1f}  p25={:.1f}  mediana={:.1f}  p75={:.1f}  p95={:.1f}".format(*pct))
    for u in (8, 10, 12, 15, 20):
        print(f"  umbral {u:>2} m -> zona baja = {np.mean(v <= u) * 100:5.1f} % del recuadro")


def descargar(proyecto, umbral, destino):
    ee = iniciar_ee(proyecto)
    o, s, e, n = leer_bbox()
    aoi = ee.Geometry.Rectangle([o, s, e, n], None, False)
    dem = ee.Image("USGS/SRTMGL1_003").select("elevation").rename("elevacion")
    # La pendiente se calcula antes de recortar para no tener bordes falsos
    pendiente = ee.Terrain.slope(dem).rename("pendiente")
    zona_baja = dem.lte(umbral).rename("zona_baja")
    img = dem.addBands(pendiente).addBands(zona_baja).toFloat().clip(aoi)
    descargar_ee(img, aoi, 30, destino)


def desde_locales(destino, umbral, elev_path, pend_path):
    """Arma srtm_daule.tif con los GeoTIFF que el equipo ya tiene (elevacion_daule_utm.tif y
    pendiente_daule.tif, UTM 17S a 30 m), sin volver a descargar de Earth Engine."""
    from p3_comun import a_grilla
    e, perfil = leer_raster(elev_path, ["elevacion"])
    elev = list(e.values())[0]
    p, perfil_p = leer_raster(pend_path, ["pendiente"])
    pend = list(p.values())[0]
    if pend.shape != elev.shape or perfil_p["transform"] != perfil["transform"]:
        pend = list(a_grilla(pend_path, perfil, ["pendiente"]).values())[0]
    baja = np.where(np.isfinite(elev), (elev <= umbral).astype("float32"), np.nan)
    escribir_raster(destino, {"elevacion": elev, "pendiente": pend, "zona_baja": baja}, perfil)


def recalcular_umbral(destino, umbral):
    bandas, perfil = leer_raster(destino, NOMBRES)
    elev = bandas["elevacion"]
    baja = np.where(np.isfinite(elev), (elev <= umbral).astype("float32"), np.nan)
    escribir_raster(destino, {"elevacion": elev, "pendiente": bandas["pendiente"], "zona_baja": baja}, perfil)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proyecto", help="ID del proyecto de Earth Engine")
    ap.add_argument("--umbral", type=float, default=8.0, help="metros; zona baja = elevacion <= umbral")
    ap.add_argument("--solo-umbral", type=float, help="recalcula zona_baja sobre el tif existente")
    ap.add_argument("--desde-locales", action="store_true",
                    help="arma srtm_daule.tif con elevacion_daule_utm.tif y pendiente_daule.tif")
    ap.add_argument("--elev", default=None, help="ruta de la elevación (por defecto data/processed/elevacion_daule_utm.tif)")
    ap.add_argument("--pend", default=None, help="ruta de la pendiente (por defecto data/processed/pendiente_daule.tif)")
    ap.add_argument("--mock", action="store_true", help="trabaja en data/mock")
    a = ap.parse_args()

    base = carpeta(a.mock)
    destino = base / "srtm_daule.tif"
    if a.desde_locales:
        desde_locales(destino, a.umbral,
                      a.elev or base / "elevacion_daule_utm.tif",
                      a.pend or base / "pendiente_daule.tif")
    elif a.solo_umbral is not None:
        recalcular_umbral(destino, a.solo_umbral)
    else:
        descargar(a.proyecto, a.umbral, destino)

    bandas, _ = leer_raster(destino, NOMBRES)
    resumen_elevacion(bandas["elevacion"])


if __name__ == "__main__":
    main()
