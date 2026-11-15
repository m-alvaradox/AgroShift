"""
Revisa los archivos que el equipo dejo en data/processed/:
  - muestra las columnas de cada CSV (para saber que trae cada uno)
  - dice si los archivos de los contratos cumplen las columnas que la app necesita

Uso (desde la raiz del proyecto):
    python scripts/revisar_datos.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from utils.carga import CONTRATOS, faltantes  # noqa: E402

PROC = ROOT / "data" / "processed"

print(f"\nArchivos en {PROC}:\n")
for p in sorted(PROC.glob("*")):
    if p.suffix == ".csv":
        df = pd.read_csv(p, nrows=3)
        print(f"- {p.name}  ({len(pd.read_csv(p, usecols=[0]))} filas)")
        print(f"    columnas: {', '.join(df.columns)}")
    else:
        print(f"- {p.name}")

print("\nContratos que usa la app:\n")
for nombre, cols in CONTRATOS.items():
    p = PROC / nombre
    if not p.exists():
        print(f"  [ falta ]  {nombre}")
        continue
    falta = faltantes(p, nombre)
    estado = "[  ok   ]" if not falta else "[ no ok ]"
    detalle = "" if not falta else f"  -> le faltan: {', '.join(falta)}"
    print(f"  {estado}  {nombre}{detalle}")
print()
