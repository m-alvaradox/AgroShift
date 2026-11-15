import os
# Evita "OpenBLAS error: Memory allocation still failed" en Windows (limita hilos antes de importar numpy)
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")
import argparse
import json

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from p3_comun import (carpeta, leer_raster, a_grilla, escribir_raster, archivos_landsat,
                       leer_landsat, avisar_cobertura)

INDICES = ["ndvi", "ndwi", "ndmi"]
UMBRAL_ZONA_BAJA_M = 8.0    
UMBRAL_FREC_AGUA = 0.20     # zona "que se encharca" si NDWI > 0 en 20 % o más de los meses
PENDIENTE_LADERA = 5.0      # grados


# variables por píxel
def estadisticas_landsat(base, perfil):
    """Media de cada índice, variación (desv. estándar) del NDVI y frecuencia de agua (NDWI > 0),
    acumuladas mes a mes para no cargar los 60 meses en memoria."""
    archivos = archivos_landsat(base)
    if not archivos:
        return None
    h, w = perfil["height"], perfil["width"]
    suma = {i: np.zeros((h, w)) for i in INDICES}
    cuenta = {i: np.zeros((h, w)) for i in INDICES}
    suma2_ndvi = np.zeros((h, w))
    agua = np.zeros((h, w))
    for anio, mes, p in archivos:
        b = leer_landsat(p, perfil)
        for i in INDICES:
            ok = np.isfinite(b[i])
            suma[i][ok] += b[i][ok]
            cuenta[i][ok] += 1
        ok = np.isfinite(b["ndvi"])
        suma2_ndvi[ok] += b["ndvi"][ok] ** 2
        ok = np.isfinite(b["ndwi"])
        agua[ok] += b["ndwi"][ok] > 0
    with np.errstate(invalid="ignore", divide="ignore"):
        out = {f"{i}_medio": (suma[i] / cuenta[i]).astype("float32") for i in INDICES}
        var = suma2_ndvi / cuenta["ndvi"] - out["ndvi_medio"] ** 2
        out["ndvi_variacion"] = np.sqrt(np.clip(var, 0, None)).astype("float32")
        out["frec_agua"] = (agua / cuenta["ndwi"]).astype("float32")
    print(f"[ok] Landsat: {len(archivos)} meses usados para las zonas")
    return out


# agrupación
def agrupar(variables: dict, valido, k="3", muestra=50_000, semilla=42):
    nombres = list(variables)
    X = np.column_stack([variables[n][valido] for n in nombres]).astype("float64")
    # Huecos (nubes) en una variable: se rellenan con la mediana de esa variable
    med = np.nanmedian(X, axis=0)
    filas, cols = np.where(~np.isfinite(X))
    X[filas, cols] = med[cols]
    Xs = StandardScaler().fit_transform(X)

    rng = np.random.default_rng(semilla)
    idx = rng.choice(len(Xs), size=min(muestra, len(Xs)), replace=False)

    if str(k) == "auto":
        mejor, mejor_s = 2, -1
        sub = idx[:5000]
        for kk in (2, 3):
            km = KMeans(kk, n_init=10, random_state=semilla).fit(Xs[idx])
            s = silhouette_score(Xs[sub], km.predict(Xs[sub]))
            print(f"  k={kk}: silueta = {s:.3f}")
            if s > mejor_s:
                mejor, mejor_s = kk, s
        k = mejor
    k = int(k)
    km = KMeans(k, n_init=10, random_state=semilla).fit(Xs[idx])
    crudo = km.predict(Xs)

    # Reordenar: zona 1 = la de menor elevación media
    elev = variables["elevacion"][valido]
    orden = np.argsort([np.nanmean(elev[crudo == c]) for c in range(k)])
    mapa = np.empty(k, dtype=int)
    mapa[orden] = np.arange(1, k + 1)
    etiquetas = np.zeros(valido.shape, dtype="uint8")
    etiquetas[valido] = mapa[crudo]
    print(f"[ok] K-means con k={k} y variables: {', '.join(nombres)}")
    return etiquetas, k


def resumen_por_zona(etiquetas, variables, area_pixel_ha):
    filas = []
    for z in range(1, int(etiquetas.max()) + 1):
        m = etiquetas == z
        fila = {"zona_id": z, "area_ha": round(float(m.sum() * area_pixel_ha), 1)}
        for n, a in variables.items():
            v = a[m]
            v = v[np.isfinite(v)]
            fila[n] = float(v.mean()) if v.size else np.nan
        filas.append(fila)
    return pd.DataFrame(filas)


def nombrar(df, umbral_baja=UMBRAL_ZONA_BAJA_M):
    nombres = []
    k = len(df)
    for _, r in df.iterrows():
        z = int(r["zona_id"])
        encharca = r.get("frec_agua", np.nan) >= UMBRAL_FREC_AGUA or r["elevacion"] <= umbral_baja
        ladera = r.get("pendiente", 0) >= PENDIENTE_LADERA
        if z == 1:
            n = "Zona baja que se encharca" if encharca else "Zona baja"
        elif z == k:
            n = "Loma con pendiente" if ladera else "Loma seca"
        elif ladera:
            n = "Ladera con riesgo de erosión"
        else:
            n = "Zona de transición que se encharca" if encharca else "Zona de transición"
        nombres.append(n)
    df.insert(1, "nombre_comun", nombres)
    return df


# polígonos
def a_geojson(etiquetas, perfil, df, destino, sieve_px=50):
    import rasterio.features
    from rasterio.warp import transform_geom
    lab = rasterio.features.sieve(etiquetas, size=sieve_px)  # quita manchas < ~4.5 ha
    lab[etiquetas == 0] = 0
    poligonos = {}
    for geom, val in rasterio.features.shapes(lab, mask=lab > 0, transform=perfil["transform"]):
        poligonos.setdefault(int(val), []).append(geom["coordinates"])
    feats = []
    for _, r in df.iterrows():
        z = int(r["zona_id"])
        g = {"type": "MultiPolygon", "coordinates": poligonos.get(z, [])}
        g = transform_geom(perfil["crs"], "EPSG:4326", g, precision=6)
        props = {"zona_id": z, "nombre_comun": r["nombre_comun"], "area_ha": float(r["area_ha"])}
        for c in df.columns:
            if c not in props:
                v = r[c]
                props[c] = None if pd.isna(v) else round(float(v), 4)
        feats.append({"type": "Feature", "properties": props, "geometry": g})
    destino.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False),
                       encoding="utf-8")
    print(f"[ok] {destino}")
    return lab


def suelo_por_zona(base, perfil, etiquetas):
    p = base / "suelo_daule.tif"
    if not p.exists():
        print("[aviso] No hay suelo_daule.tif; corre suelo.py para tener suelo por zona")
        return
    from suelo import NOMBRES, resumir
    bandas = a_grilla(p, perfil, NOMBRES, metodo="nearest")
    filas = [{"zona_id": z, **resumir(bandas, etiquetas == z)} for z in range(1, int(etiquetas.max()) + 1)]
    pd.DataFrame(filas).to_csv(base / "suelo_zonas.csv", index=False)
    print(f"[ok] {base / 'suelo_zonas.csv'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", default="3", help="2, 3 o auto")
    ap.add_argument("--solo-terreno", action="store_true", help="no usar Landsat")
    ap.add_argument("--umbral", type=float, default=UMBRAL_ZONA_BAJA_M)
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    base = carpeta(a.mock)

    srtm, perfil = leer_raster(base / "srtm_daule.tif", ["elevacion", "pendiente", "zona_baja"])
    variables = {"elevacion": srtm["elevacion"], "pendiente": srtm["pendiente"]}
    if not a.solo_terreno:
        ls = estadisticas_landsat(base, perfil)
        if ls is None:
            print("[aviso] No hay Landsat de P2 todavía; zonas solo con elevación y pendiente")
        else:
            avisar_cobertura(np.isfinite(ls["ndvi_medio"]), np.isfinite(srtm["elevacion"]))
            variables.update(ls)
    valido = np.isfinite(srtm["elevacion"])

    etiquetas, k = agrupar(variables, valido, a.k)
    area_pixel_ha = abs(perfil["transform"].a * perfil["transform"].e) / 10_000
    df = nombrar(resumen_por_zona(etiquetas, variables, area_pixel_ha), a.umbral)

    lab = a_geojson(etiquetas, perfil, df, base / "zonas_daule.geojson")
    escribir_raster(base / "zonas_daule.tif", {"zona_id": lab}, perfil, dtype="uint8", nodata=0)
    df.to_csv(base / "zonas_resumen.csv", index=False)
    print(df.round(3).to_string(index=False))
    suelo_por_zona(base, perfil, lab)

    # Validación con el umbral de elevación
    baja = srtm["zona_baja"] == 1
    if baja.any():
        coincide = np.mean((lab == 1)[valido] == baja[valido]) * 100
        print(f"Coincidencia zona 1 vs. umbral de elevación: {coincide:.1f} % de los píxeles")


if __name__ == "__main__":
    main()