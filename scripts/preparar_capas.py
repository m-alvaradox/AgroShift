"""
Agroshift - Capas raster para el mapa de "Mi finca".

Lee (sin modificarlos) los GeoTIFF del equipo, los reproyecta a EPSG:4326,
les aplica una paleta y los guarda como PNG con transparencia en app/data/capas/.
Tambien escribe app/data/capas/capas.json con los limites de cada PNG
(lo que necesita folium.raster_layers.ImageOverlay) y los datos de la leyenda.

    data/processed/elevacion_daule_utm.tif  -> elevacion.png  (verde -> marron)
    data/processed/pendiente_daule.tif      -> pendiente.png  (blanco -> rojo)
    data/processed/landsat/*ndvi*.tif       -> verdor.png     (si existe; el ultimo mes)

Los PNG se guardan con paleta de 256 colores (modo "P"): pesan poco y la app
no necesita rasterio para mostrarlos.

Uso (desde la raiz del proyecto):
    python scripts/preparar_capas.py
"""
import json
from pathlib import Path

import numpy as np
import rasterio
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from rasterio.warp import Resampling, calculate_default_transform, reproject

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
SALIDA = ROOT / "app" / "data" / "capas"      # capas.json (limites y leyenda)
PNG_DIR = ROOT / "app" / "static" / "capas"   # PNG servidos por Streamlit en app/static/capas/
DESTINO = "EPSG:4326"
NIVELES = 64  # colores de la paleta: menos niveles = PNG mas liviano, se ve igual

# nombre: (archivo, titulo, unidad, colores de la paleta, rango fijo o None = percentiles 2-98)
CAPAS = {
    "elevacion": (PROC / "elevacion_daule_utm.tif", "Elevación", "m",
                  ["#1a9850", "#a6d96a", "#fee08b", "#d8a463", "#8c510a", "#543005"], None),
    "pendiente": (PROC / "pendiente_daule.tif", "Pendiente", "°",
                  ["#ffffff", "#fcbba1", "#fb6a4a", "#cb181d", "#67000d"], None),
}
PALETA_VERDOR = ["#8c510a", "#dfc27d", "#f6e8c3", "#a6d96a", "#1a9850", "#00441b"]


def ultimo_ndvi() -> Path | None:
    """GeoTIFF de NDVI mas reciente en data/processed/landsat/ (por nombre de archivo)."""
    carpeta = PROC / "landsat"
    if not carpeta.exists():
        return None
    candidatos = sorted(p for p in carpeta.glob("*.tif") if "ndvi" in p.name.lower())
    return candidatos[-1] if candidatos else None


def reproyectar(ruta: Path) -> tuple[np.ndarray, list]:
    """Banda 1 en EPSG:4326 (NaN = sin dato) y limites [[sur, oeste], [norte, este]]."""
    with rasterio.open(ruta) as src:
        datos = src.read(1).astype("float32")
        if src.nodata is not None:
            datos[datos == src.nodata] = np.nan
        transform, ancho, alto = calculate_default_transform(
            src.crs, DESTINO, src.width, src.height, *src.bounds)
        salida = np.full((alto, ancho), np.nan, dtype="float32")
        reproject(datos, salida, src_transform=src.transform, src_crs=src.crs, src_nodata=np.nan,
                  dst_transform=transform, dst_crs=DESTINO, dst_nodata=np.nan,
                  resampling=Resampling.bilinear)
    oeste, norte = transform * (0, 0)
    este, sur = transform * (ancho, alto)
    return salida, [[round(sur, 6), round(oeste, 6)], [round(norte, 6), round(este, 6)]]


def a_png(datos: np.ndarray, colores: list[str], vmin: float, vmax: float, destino: Path) -> None:
    """Indice 0 = transparente; 1..NIVELES = paleta de colores de vmin a vmax."""
    cmap = LinearSegmentedColormap.from_list("capa", colores, N=NIVELES)
    escala = np.clip((datos - vmin) / (vmax - vmin), 0, 1)
    idx = np.where(np.isfinite(datos), 1 + np.round(np.nan_to_num(escala) * (NIVELES - 1)), 0).astype("uint8")
    paleta = [0, 0, 0] + [int(round(c * 255)) for i in range(NIVELES) for c in cmap(i)[:3]]
    img = Image.fromarray(idx, mode="P")
    img.putpalette(paleta)
    img.save(destino, optimize=True, transparency=0)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    capas = dict(CAPAS)
    ndvi = ultimo_ndvi()
    if ndvi:
        capas["verdor"] = (ndvi, f"Verdor (último mes: {ndvi.stem})", "NDVI", PALETA_VERDOR, (0.0, 0.9))

    info = {}
    for clave, (ruta, titulo, unidad, colores, rango) in capas.items():
        if not ruta.exists():
            print(f"  [ falta ]  {ruta.relative_to(ROOT).as_posix()}")
            continue
        datos, limites = reproyectar(ruta)
        validos = datos[np.isfinite(datos)]
        if validos.size == 0:
            print(f"  [ vacio ]  {ruta.name}: no tiene pixeles validos")
            continue
        vmin, vmax = rango or (float(np.percentile(validos, 2)), float(np.percentile(validos, 98)))
        png = PNG_DIR / f"{clave}.png"
        a_png(datos, colores, vmin, vmax, png)
        info[clave] = {
            "nombre": titulo, "png": png.relative_to(ROOT / "app").as_posix(), "limites": limites, "unidad": unidad,
            "min": round(vmin, 2), "max": round(vmax, 2), "colores": colores,
            "fuente": ruta.relative_to(ROOT).as_posix(),
        }
        print(f"  [  ok   ]  {png.relative_to(ROOT).as_posix():<34} {png.stat().st_size / 1024:7.0f} KB  "
              f"{datos.shape[1]}x{datos.shape[0]} px  rango {vmin:.1f} a {vmax:.1f} {unidad}")
    if not ndvi:
        print("  [ omitida ] Verdor: no hay GeoTIFF de NDVI en data/processed/landsat/")

    (SALIDA / "capas.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Limites guardados en {(SALIDA / 'capas.json').relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
