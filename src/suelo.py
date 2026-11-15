"""P3 · Suelo con SoilGrids (ISRIC, 250 m) -> data/processed/suelo_daule.tif y suelo_daule.csv

Bandas: arcilla_pct, arena_pct, limo_pct, ph, mo_pct (materia orgánica), promedio de 0 a 30 cm.
El resumen por zona (suelo_zonas.csv) lo escribe zonas.py, porque necesita las zonas.

Uso:
    python src/suelo.py --proyecto TU_PROYECTO_EE

Conversiones de SoilGrids (valores guardados como enteros):
    arcilla, arena, limo: g/kg  -> % dividiendo para 10
    phh2o: pH x 10              -> pH dividiendo para 10
    soc: dg/kg                  -> g/kg dividiendo para 10; MO % = SOC (g/kg) / 10 x 1.724 (factor de Van Bemmelen)
"""
import argparse

import numpy as np
import pandas as pd

from p3_comun import carpeta, leer_bbox, iniciar_ee, descargar_ee, leer_raster

NOMBRES = ["arcilla_pct", "arena_pct", "limo_pct", "ph", "mo_pct"]
# Profundidades y su espesor en cm, para un promedio ponderado de 0 a 30 cm
CAPAS = [("0-5cm", 5), ("5-15cm", 10), ("15-30cm", 15)]


def textura_usda(arena, limo, arcilla):
    """Clase textural USDA (triángulo de texturas) a partir de porcentajes."""
    if any(not np.isfinite(x) for x in (arena, limo, arcilla)):
        return "sin dato"
    if limo + 1.5 * arcilla < 15:
        return "arenoso"
    if limo + 2 * arcilla < 30:
        return "arenoso franco"
    if (7 <= arcilla < 20 and arena > 52) or (arcilla < 7 and limo < 50):
        return "franco arenoso"
    if 7 <= arcilla < 27 and 28 <= limo < 50 and arena <= 52:
        return "franco"
    if limo >= 80 and arcilla < 12:
        return "limoso"
    if (limo >= 50 and 12 <= arcilla < 27) or (50 <= limo < 80 and arcilla < 12):
        return "franco limoso"
    if 20 <= arcilla < 35 and limo < 28 and arena > 45:
        return "franco arcillo arenoso"
    if 27 <= arcilla < 40 and 20 < arena <= 45:
        return "franco arcilloso"
    if 27 <= arcilla < 40 and arena <= 20:
        return "franco arcillo limoso"
    if arcilla >= 35 and arena > 45:
        return "arcillo arenoso"
    if arcilla >= 40 and limo >= 40:
        return "arcillo limoso"
    if arcilla >= 40:
        return "arcilloso"
    return "sin clasificar"


def resumir(bandas, mascara=None):
    """Promedio de cada variable (opcionalmente dentro de una máscara) y su textura."""
    fila = {}
    for n in NOMBRES:
        a = bandas[n]
        v = a[mascara] if mascara is not None else a
        v = v[np.isfinite(v)]
        fila[n] = round(float(v.mean()), 2) if v.size else np.nan
    fila["textura"] = textura_usda(fila["arena_pct"], fila["limo_pct"], fila["arcilla_pct"])
    return fila


def descargar(proyecto, destino):
    ee = iniciar_ee(proyecto)
    o, s, e, n = leer_bbox()
    aoi = ee.Geometry.Rectangle([o, s, e, n], None, False)

    def capa_0_30(var):
        img = ee.Image(f"projects/soilgrids-isric/{var}_mean")
        total = sum(esp for _, esp in CAPAS)
        suma = None
        for prof, esp in CAPAS:
            b = img.select(f"{var}_{prof}_mean").multiply(esp)
            suma = b if suma is None else suma.add(b)
        return suma.divide(total)

    arcilla = capa_0_30("clay").divide(10).rename("arcilla_pct")
    arena = capa_0_30("sand").divide(10).rename("arena_pct")
    limo = capa_0_30("silt").divide(10).rename("limo_pct")
    ph = capa_0_30("phh2o").divide(10).rename("ph")
    mo = capa_0_30("soc").divide(10).divide(10).multiply(1.724).rename("mo_pct")
    img = arcilla.addBands([arena, limo, ph, mo]).toFloat().clip(aoi)
    descargar_ee(img, aoi, 250, destino)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proyecto", help="ID del proyecto de Earth Engine")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()

    base = carpeta(a.mock)
    tif = base / "suelo_daule.tif"
    if not a.mock:
        descargar(a.proyecto, tif)
    bandas, _ = leer_raster(tif, NOMBRES)
    fila = resumir(bandas)
    pd.DataFrame([fila]).to_csv(base / "suelo_daule.csv", index=False)
    print("Suelo promedio del recuadro (0-30 cm):", fila)


if __name__ == "__main__":
    main()
