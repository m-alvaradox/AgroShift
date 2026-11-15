
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATOS = BASE / "data" / "processed"

# Parámetros preliminares
CULTIVOS = {
    "Arroz": {
        "etapas": [25, 30, 40, 25],
        "kc": [1.10, 1.20, 1.00]
    },
    "Soya": {
        "etapas": [25, 30, 40, 25],
        "kc": [0.35, 1.10, 0.60]
    },
    "Maiz duro": {
        "etapas": [25, 30, 40, 25],
        "kc": [0.40, 1.15, 0.70]
    }
}

# Escenarios para el mismo horizonte temporal
ESTRATEGIAS = {
    "A": [
        ("2025-01-01", "Arroz"),
        ("2025-07-01", "Arroz"),
        ("2026-01-01", "Arroz"),
        ("2026-07-01", "Arroz")
    ],
    "B": [
        ("2025-01-01", "Arroz"),
        ("2025-07-01", "Soya"),
        ("2026-01-01", "Arroz"),
        ("2026-07-01", "Soya")
    ],
    "C": [
        ("2025-01-01", "Arroz"),
        ("2025-07-01", "Soya"),
        ("2026-01-01", "Maiz duro"),
        ("2026-07-01", "Soya")
    ]
}

def obtener_kc(dia, config):
    inicial, desarrollo, medio, final = config["etapas"]
    kc_ini, kc_mid, kc_fin = config["kc"]

    if dia < inicial:
        return kc_ini

    dia -= inicial

    if dia < desarrollo:
        return kc_ini + (
            (kc_mid - kc_ini) * dia / desarrollo
        )

    dia -= desarrollo

    if dia < medio:
        return kc_mid

    dia -= medio

    return kc_mid + (
        (kc_fin - kc_mid)
        * min(dia / final, 1)
    )

# Cargar clima diario con ETo
datos = pd.read_csv(
    DATOS / "eto_diaria_daule.csv",
    parse_dates=["fecha"]
).set_index("fecha")

resultados = []

for estrategia, ciclos in ESTRATEGIAS.items():

    for fecha_inicio, cultivo in ciclos:

        config = CULTIVOS[cultivo]
        inicio = pd.Timestamp(fecha_inicio)
        duracion = sum(config["etapas"])

        for dia in range(duracion):

            fecha = inicio + pd.Timedelta(days=dia)

            if fecha not in datos.index:
                raise ValueError(
                    f"Fecha sin datos: {fecha.date()}"
                )

            fila = datos.loc[fecha]

            eto = float(fila["eto_mm_dia"])
            lluvia = float(fila["precipitacion"])

            kc = obtener_kc(dia, config)
            etc = eto * kc

            # Supuesto ilustrativo:
            # 80 % de lluvia diaria aprovechable,
            # limitada a la demanda ETc del día.
            #
            # No representa un modelo validado
            # de almacenamiento de agua en el suelo.
            lluvia_util = min(
                max(lluvia, 0) * 0.8,
                etc
            )

            deficit = max(
                etc - lluvia_util,
                0
            )

            resultados.append({
                "estrategia": estrategia,
                "cultivo": cultivo,
                "fecha_inicio": fecha_inicio,
                "fecha": fecha,
                "eto_mm": eto,
                "kc": kc,
                "etc_mm": etc,
                "lluvia_mm": lluvia,
                "lluvia_util_mm": lluvia_util,
                "deficit_etc_mm": deficit
            })

df = pd.DataFrame(resultados)

# Resumen por cultivo y ciclo
por_ciclo = df.groupby(
    ["estrategia", "fecha_inicio", "cultivo"],
    as_index=False
).agg(
    etc_mm=("etc_mm", "sum"),
    lluvia_mm=("lluvia_mm", "sum"),
    lluvia_util_mm=("lluvia_util_mm", "sum"),
    deficit_etc_mm=("deficit_etc_mm", "sum")
)

# Resumen de las estrategias
resumen = df.groupby(
    "estrategia", as_index=False
).agg(
    demanda_etc_mm=("etc_mm", "sum"),
    lluvia_total_mm=("lluvia_mm", "sum"),
    lluvia_util_mm=("lluvia_util_mm", "sum"),
    deficit_etc_mm=("deficit_etc_mm", "sum")
)

resumen["deficit_m3_ha"] = (
    resumen["deficit_etc_mm"] * 10
)

# Guardar resultados
df.to_csv(
    DATOS / "balance_estrategias_diario.csv",
    index=False
)

por_ciclo.to_csv(
    DATOS / "balance_estrategias_ciclos.csv",
    index=False
)

resumen.to_csv(
    DATOS / "balance_agua_estrategias.csv",
    index=False
)

print("\n=== BALANCE HÍDRICO POR ESTRATEGIA ===")
print(resumen.round(2).to_string(index=False))

print("\n=== RESULTADOS POR CICLO ===")
print(por_ciclo.round(2).to_string(index=False))

print("\nArchivos generados correctamente.")
