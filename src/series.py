import os
# Evita "OpenBLAS error: Memory allocation still failed" en Windows (limita hilos antes de importar numpy)
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")
import argparse

import numpy as np
import pandas as pd

from p3_comun import carpeta, leer_raster, archivos_landsat, leer_landsat, avisar_cobertura

INDICES = ["ndvi", "ndwi", "ndmi"]
MIN_PCT_VALIDO = 30.0


def promedios_por_zona(zonas, bandas, k):
    filas = []
    total = np.bincount(zonas.ravel(), minlength=k + 1)
    for z in range(1, k + 1):
        filas.append({"zona_id": z})
    ref = None
    for i in INDICES:
        a = bandas[i].ravel()
        ok = np.isfinite(a) & (zonas.ravel() > 0)
        n = np.bincount(zonas.ravel()[ok], minlength=k + 1)
        s = np.bincount(zonas.ravel()[ok], weights=a[ok], minlength=k + 1)
        if ref is None:
            ref = n
        for z in range(1, k + 1):
            filas[z - 1][i] = s[z] / n[z] if n[z] else np.nan
    for z in range(1, k + 1):
        pct = 100 * ref[z] / total[z] if total[z] else 0.0
        filas[z - 1]["pct_valido"] = round(float(pct), 1)
        if pct < MIN_PCT_VALIDO:
            for i in INDICES:
                filas[z - 1][i] = np.nan
    return filas


def leer_lluvia(base):
    p = base / "clima_mensual_daule.csv"
    if not p.exists():
        print(f"[aviso] No existe {p.name} (P1); lluvia_mm queda vacía")
        return None
    c = pd.read_csv(p)
    # Acepta el contrato (fecha, anio, mes, lluvia_mm) y el formato que subió P1
    # (mes = AAAA-MM-01, precipitacion en mm del mes)
    if "lluvia_mm" not in c.columns and "precipitacion" in c.columns:
        c = c.rename(columns={"precipitacion": "lluvia_mm"})
    if "anio" not in c.columns:
        f = pd.to_datetime(c["fecha"] if "fecha" in c.columns else c["mes"])
        c["anio"], c["mes"] = f.dt.year, f.dt.month
    return c.groupby(["anio", "mes"], as_index=False)["lluvia_mm"].sum()


def armar_serie(registros, lluvia, k):
    df = pd.DataFrame(registros)
    inicio = pd.Timestamp(int(df.anio.min()), int(df[df.anio == df.anio.min()].mes.min()), 1)
    fin = pd.Timestamp(int(df.anio.max()), int(df[df.anio == df.anio.max()].mes.max()), 1)
    meses = pd.date_range(inicio, fin, freq="MS")
    base = pd.MultiIndex.from_product([meses, range(1, k + 1)], names=["f", "zona_id"]).to_frame(index=False)
    base["anio"], base["mes"] = base.f.dt.year, base.f.dt.month
    df = base.merge(df, on=["anio", "mes", "zona_id"], how="left")
    df["pct_valido"] = df["pct_valido"].fillna(0.0)
    if lluvia is not None:
        df = df.merge(lluvia, on=["anio", "mes"], how="left")
    else:
        df["lluvia_mm"] = np.nan
    df["fecha"] = df.f.dt.strftime("%Y-%m-01")
    df = df[["fecha", "zona_id", "ndvi", "ndwi", "ndmi", "lluvia_mm", "pct_valido"]]
    return df.round({"ndvi": 4, "ndwi": 4, "ndmi": 4, "lluvia_mm": 1})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    base = carpeta(a.mock)

    z, perfil = leer_raster(base / "zonas_daule.tif", ["zona_id"])
    zonas = np.nan_to_num(z["zona_id"], nan=0).astype(int)
    k = int(zonas.max())

    archivos = archivos_landsat(base)
    if not archivos:
        raise SystemExit("No hay archivos en landsat/. Espera a P2 o corre mock_p3.py y usa --mock")
    registros = []
    cubierto = np.zeros(zonas.shape, dtype=bool)
    for anio, mes, p in archivos:
        bandas = leer_landsat(p, perfil)
        cubierto |= np.isfinite(bandas["ndvi"])
        for fila in promedios_por_zona(zonas, bandas, k):
            registros.append({"anio": anio, "mes": mes, **fila})

    avisar_cobertura(cubierto, zonas > 0)
    df = armar_serie(registros, leer_lluvia(base), k)
    destino = base / "series_zonas.csv"
    df.to_csv(destino, index=False)
    huecos = df.groupby("zona_id")["ndvi"].apply(lambda s: s.isna().sum())
    print(f"[ok] {destino}: {df.fecha.nunique()} meses x {k} zonas")
    print("Meses sin dato de NDVI por zona (nubes o sin imagen):", huecos.to_dict())


if __name__ == "__main__":
    main()