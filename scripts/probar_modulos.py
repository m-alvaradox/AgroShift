
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.clima_power import consultar_mes as consultar_power
from src.lluvia_imerg import consultar_mes as consultar_imerg

mes = "2025-03"

clima = consultar_power(mes)
lluvia = consultar_imerg(mes)

print(f"\nAGROSHIFT - DATOS DE {mes}")

print(
    f"Temperatura media: "
    f"{clima['temperatura_media']:.2f} °C"
)

print(
    f"Precipitación POWER: "
    f"{clima['precipitacion']:.2f} mm"
)

print(
    f"Precipitación IMERG: "
    f"{lluvia['precipitacion_imerg_mm']:.2f} mm"
)
