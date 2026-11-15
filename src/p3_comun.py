import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")
from pathlib import Path
import json

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]

# Recuadro de Daule según la documentación: (oeste, sur, este, norte)
BBOX_DAULE = (-80.10, -1.95, -79.85, -1.70)

# UTM 17 Sur: metros, sirve para pendiente, áreas y píxeles de 30 m
CRS_UTM = "EPSG:32717"


def carpeta(mock: bool) -> Path:
    p = RAIZ / "data" / ("mock" if mock else "processed")
    p.mkdir(parents=True, exist_ok=True)
    return p


def leer_bbox():
    p = RAIZ / "data" / "aoi_daule.geojson"
    if not p.exists():
        print(f"[aviso] No existe {p.name}; uso el recuadro de la documentación {BBOX_DAULE}")
        return BBOX_DAULE
    gj = json.loads(p.read_text(encoding="utf-8"))
    xs, ys = [], []

    def recorrer(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0]); ys.append(c[1])
        else:
            for k in c:
                recorrer(k)

    feats = gj["features"] if gj.get("type") == "FeatureCollection" else [gj]
    for f in feats:
        geom = f.get("geometry", f)
        recorrer(geom["coordinates"])
    return (min(xs), min(ys), max(xs), max(ys))


# Earth Engine
def iniciar_ee(proyecto=None):
    import ee
    try:
        ee.Initialize(project=proyecto) if proyecto else ee.Initialize()
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=proyecto) if proyecto else ee.Initialize()
    return ee


def descargar_ee(img, region, escala, destino: Path, crs=CRS_UTM):
    import requests
    url = img.getDownloadURL({
        "region": region, "scale": escala, "crs": crs,
        "format": "GEO_TIFF", "filePerBand": False,
    })
    r = requests.get(url, timeout=600)
    r.raise_for_status()
    destino.write_bytes(r.content)
    print(f"[ok] {destino}  ({len(r.content) / 1e6:.1f} MB)")


# rasters
def leer_raster(path: Path, nombres_por_defecto=None):
    import rasterio
    with rasterio.open(path) as src:
        perfil = src.profile.copy()
        nombres = [d.lower() if d else None for d in src.descriptions]
        if any(n is None for n in nombres):
            nombres = list(nombres_por_defecto or [f"b{i + 1}" for i in range(src.count)])
        datos = {}
        for i, n in enumerate(nombres[: src.count], start=1):
            a = src.read(i).astype("float32")
            if src.nodata is not None:
                a[a == src.nodata] = np.nan
            datos[n] = a
    return datos, perfil


def a_grilla(path: Path, perfil_ref, nombres_por_defecto=None, metodo="bilinear"):
    import rasterio
    from rasterio.warp import reproject, Resampling
    rs = getattr(Resampling, metodo)
    with rasterio.open(path) as src:
        nombres = [d.lower() if d else None for d in src.descriptions]
        if any(n is None for n in nombres):
            nombres = list(nombres_por_defecto or [f"b{i + 1}" for i in range(src.count)])
        salida = {}
        for i, n in enumerate(nombres[: src.count], start=1):
            dst = np.full((perfil_ref["height"], perfil_ref["width"]), np.nan, dtype="float32")
            reproject(
                source=rasterio.band(src, i), destination=dst,
                src_nodata=src.nodata, dst_nodata=np.nan,
                dst_transform=perfil_ref["transform"], dst_crs=perfil_ref["crs"],
                resampling=rs,
            )
            salida[n] = dst
    return salida


def escribir_raster(path: Path, bandas: dict, perfil_ref, dtype="float32", nodata=np.nan):
    import rasterio
    perfil = perfil_ref.copy()
    perfil.update(count=len(bandas), dtype=dtype, nodata=nodata, compress="deflate", driver="GTiff")
    with rasterio.open(path, "w", **perfil) as dst:
        for i, (n, a) in enumerate(bandas.items(), start=1):
            dst.write(a.astype(dtype), i)
            dst.set_band_description(i, n)
    print(f"[ok] {path}")


def leer_landsat(path: Path, perfil_ref):
    bandas = a_grilla(path, perfil_ref, ["ndvi", "ndwi", "ndmi"])
    vacio = (bandas["ndvi"] == 0) & (bandas["ndwi"] == 0) & (bandas["ndmi"] == 0)
    for nombre in bandas:
        bandas[nombre][vacio] = np.nan
    return bandas


def avisar_cobertura(cubierto, valido, minimo_pct: float = 80.0) -> None:
    pct = 100 * float(np.mean(cubierto[valido]))
    if pct < minimo_pct:
        print(f"[AVISO] Landsat cubre solo el {pct:.0f} % del mapa de elevación. "
              "Revisa que P2 haya usado el recuadro completo de Daule.")


def archivos_landsat(base: Path):
    out = []
    for p in sorted((base / "landsat").glob("*.tif")):
        try:
            a, m = p.stem.split("_")
            out.append((int(a), int(m), p))
        except ValueError:
            print(f"[aviso] nombre raro, lo salto: {p.name}")
    return out