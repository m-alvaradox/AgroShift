
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATOS = BASE / "data" / "processed"

# Fecha de prueba, no calendario agrícola validado
FECHA_SIEMBRA = "2025-01-01"

# Parámetros preliminares.
# Kc orientativos basados en referencias FAO.
# Duraciones ilustrativas: 120 días por cultivo.
CULTIVOS = {
    "Arroz": {
        "etapas": [25, 30, 40, 25],
        "kc_ini": 1.10,
        "kc_mid": 1.20,
        "kc_fin": 1.00,
    },
    "Soya": {
        "etapas": [25, 30, 40, 25],
        "kc_ini": 0.35,
        "kc_mid": 1.10,
        "kc_fin": 0.60,
    },
    "Maiz duro": {
        "etapas": [25, 30, 40, 25],
        "kc_ini": 0.40,
        "kc_mid": 1.15,
        "kc_fin": 0.70,
    },
}

def obtener_kc(dia, cultivo):
    ini, desarrollo, medio, final = cultivo["etapas"]
    kc_ini = cultivo["kc_ini"]
    kc_mid = cultivo["kc_mid"]
    kc_fin = cultivo["kc_fin"]

    if dia < ini:
        return kc_ini

    dia -= ini
    if dia < desarrollo:
        return kc_ini + (
            (kc_mid - kc_ini)
            * dia / desarrollo
        )

    dia -= desarrollo
    if dia < medio:
        return kc_mid

    dia -= medio
    return kc_mid + (
        (kc_fin - kc_mid)
        * min(dia / final, 1)
    )

# Cargar ETo diaria
eto = pd.read_csv(
    DATOS / "eto_diaria_daule.csv",
    parse_dates=["fecha"]
)

eto = eto.set_index("fecha")

resultados = []
inicio = pd.Timestamp(FECHA_SIEMBRA)

for nombre, parametros in CULTIVOS.items():

    duracion = sum(parametros["etapas"])

    for dia in range(duracion):
        fecha = inicio + pd.Timedelta(days=dia)

        if fecha not in eto.index:
            raise ValueError(
                f"No existe ETo para {fecha.date()}"
            )

        eto_dia = eto.loc[fecha, "eto_mm_dia"]
        kc = obtener_kc(dia, parametros)

        resultados.append({
            "cultivo": nombre,
            "fecha": fecha,
            "dia_cultivo": dia + 1,
            "eto_mm": eto_dia,
            "kc": kc,
            "etc_mm": eto_dia * kc,
        })

df = pd.DataFrame(resultados)

resumen = df.groupby("cultivo").agg(
    duracion_dias=("etc_mm", "count"),
    demanda_etc_mm=("etc_mm", "sum")
).round(2)

print("\n=== DEMANDA HÍDRICA DE CULTIVOS ===")
print(resumen.to_string())

# Guardar resultados
df.to_csv(
    DATOS / "demanda_cultivos_diaria.csv",
    index=False
)

resumen.to_csv(
    DATOS / "demanda_cultivos_resumen.csv"
)

print("\nArchivos generados correctamente.")
