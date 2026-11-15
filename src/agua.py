
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent
PROYECTO = BASE.parent

PROCESOS = [
    ("Evapotranspiración de referencia", "eto.py"),
    ("Demanda de cultivos", "demanda_cultivos.py"),
    ("Balance de estrategias", "balance_estrategias.py"),
    ("Comparación POWER e IMERG", "comparar_fuentes_agua.py"),
    ("Gráfico comparativo", "graficar_balance.py"),
]


def ejecutar_proceso(nombre, archivo):
    ruta = BASE / archivo

    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta}"
        )

    print(f"\n{'=' * 50}", flush=True)
    print(f"AGROSHIFT: {nombre}", flush=True)
    print(f"{'=' * 50}", flush=True)

    # Ejecutar con el mismo entorno virtual
    subprocess.run(
        [sys.executable, str(ruta)],
        cwd=PROYECTO,
        check=True
    )


def main():
    print("\nAGROSHIFT - MÓDULO P1")
    print("Procesamiento del balance hídrico")

    for nombre, archivo in PROCESOS:
        ejecutar_proceso(nombre, archivo)

    print("\n" + "=" * 50)
    print("PROCESAMIENTO COMPLETADO")
    print("=" * 50)

    print("\nResultados en:")
    print(PROYECTO / "data" / "processed")


if __name__ == "__main__":
    main()
