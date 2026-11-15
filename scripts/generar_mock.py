"""
Agroshift - Datos de prueba (mock) para construir la app sin esperar al equipo.

Crea en data/mock/ los mismos archivos de los contratos de datos, con las
mismas columnas, pero con valores SIMULADOS. La app los usa solo cuando
todavia no existe el archivo real en data/processed/ (o en app/data/).

Uso (desde la raiz del proyecto):
    python scripts/generar_mock.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MOCK = ROOT / "data" / "mock"
RNG = np.random.default_rng(42)

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
# Lluvia y ET0 tipicas de la costa (mm/mes). SIMULADAS, solo para probar la app.
LLUVIA_BASE = [190, 260, 280, 200, 60, 15, 5, 3, 4, 6, 8, 45]
ET0_BASE = [120, 110, 125, 120, 115, 100, 100, 110, 115, 120, 120, 125]

# Recuadro de Daule y 3 zonas de ejemplo (franjas de oeste a este).
# Misma numeracion y nombres que las zonas reales de P3 (data/processed/zonas_resumen.csv).
# "tipo" solo se usa aqui para simular valores; la app reconoce la zona por su nombre.
OESTE, ESTE, SUR, NORTE = -80.08, -79.93, -1.93, -1.78
ZONAS = [
    {"zona_id": 1, "nombre_comun": "Zona baja que se encharca", "tipo": "baja", "x0": -80.02, "x1": -79.93},
    {"zona_id": 2, "nombre_comun": "Ladera con riesgo de erosión", "tipo": "ladera", "x0": -80.05, "x1": -80.02},
    {"zona_id": 3, "nombre_comun": "Loma seca", "tipo": "loma", "x0": -80.08, "x1": -80.05},
]
ID_DE = {z["tipo"]: z["zona_id"] for z in ZONAS}

# Anios ENSO aproximados, solo para el ejemplo (P1 debe confirmarlos)
NINO = {2002, 2009, 2015, 2023}
NINA = {2007, 2010, 2011, 2020, 2021, 2022}


def tipo_mes(lluvia, et0):
    if lluvia >= et0:
        return "lluvioso"
    if lluvia < 0.5 * et0:
        return "seco"
    return "transicion"


def enso(anio):
    return "nino" if anio in NINO else "nina" if anio in NINA else "neutro"


def climatologia():
    filas = []
    for i in range(12):
        ll, et = LLUVIA_BASE[i], ET0_BASE[i]
        filas.append({"mes": i + 1, "nombre_mes": MESES[i], "lluvia_mm": ll,
                      "et0_mm": et, "balance_mm": ll - et, "tipo_mes": tipo_mes(ll, et)})
    return pd.DataFrame(filas)


def clima_mensual():
    filas = []
    for fecha in pd.date_range("1991-01-01", "2025-12-01", freq="MS"):
        m = fecha.month - 1
        factor = {"nino": 1.8, "nina": 0.75, "neutro": 1.0}[enso(fecha.year)]
        ll = max(0, LLUVIA_BASE[m] * factor * RNG.normal(1, 0.25))
        et = ET0_BASE[m] * RNG.normal(1, 0.05)
        filas.append({"fecha": fecha.date(), "anio": fecha.year, "mes": fecha.month,
                      "lluvia_mm": round(ll, 1), "et0_mm": round(et, 1),
                      "balance_mm": round(ll - et, 1),
                      "t_media_c": round(26 + (1 if m < 5 else -0.5) + RNG.normal(0, 0.4), 1)})
    return pd.DataFrame(filas)


def lluvia_imerg():
    filas = []
    for fecha in pd.date_range("2001-01-01", "2025-12-01", freq="MS"):
        m = fecha.month - 1
        e = enso(fecha.year)
        factor = {"nino": 1.8, "nina": 0.75, "neutro": 1.0}[e]
        ll = max(0, LLUVIA_BASE[m] * factor * RNG.normal(1, 0.3))
        filas.append({"fecha": fecha.date(), "lluvia_mm": round(ll, 1), "enso": e})
    return pd.DataFrame(filas)


def zonas_geojson():
    features = []
    for z in ZONAS:
        coords = [[z["x0"], SUR], [z["x1"], SUR], [z["x1"], NORTE], [z["x0"], NORTE], [z["x0"], SUR]]
        # area aproximada en ha (1 grado ~ 111 km cerca del ecuador)
        area = abs(z["x1"] - z["x0"]) * 111 * abs(NORTE - SUR) * 111 * 100
        features.append({
            "type": "Feature",
            "properties": {"zona_id": z["zona_id"], "nombre_comun": z["nombre_comun"],
                           "area_ha": round(area)},
            "geometry": {"type": "Polygon", "coordinates": [coords]},
        })
    return {"type": "FeatureCollection", "features": features}


def series_zonas(clima):
    filas = []
    fechas = pd.date_range("2021-01-01", "2025-12-01", freq="MS")
    for z in ZONAS:
        zid = z["zona_id"]
        for fecha in fechas:
            m = fecha.month - 1
            ll = clima.loc[(clima["anio"] == fecha.year) & (clima["mes"] == fecha.month),
                           "lluvia_mm"].iloc[0]
            lluvioso = m in (0, 1, 2, 3)
            if z["tipo"] == "baja":   # arroz en zona baja: dos picos de verdor al anio
                ndvi = 0.35 + 0.35 * np.sin(np.pi * ((m % 6) / 5))
                ndwi = 0.15 if lluvioso else -0.20
            elif z["tipo"] == "ladera":
                ndvi = 0.40 + 0.25 * np.sin(np.pi * ((m % 6) / 5))
                ndwi = 0.02 if m in (1, 2) else -0.25
            else:          # loma: maiz en invierno y suelo mas seco en verano
                ndvi = 0.30 + (0.35 if lluvioso else 0.05)
                ndwi = -0.30
            ndmi = ndvi * 0.6 - 0.1 + (0.1 if lluvioso else -0.05)
            filas.append({
                "fecha": fecha.date(), "zona_id": zid,
                "ndvi": round(float(np.clip(ndvi + RNG.normal(0, 0.04), -1, 1)), 3),
                "ndwi": round(float(np.clip(ndwi + RNG.normal(0, 0.04), -1, 1)), 3),
                "ndmi": round(float(np.clip(ndmi + RNG.normal(0, 0.04), -1, 1)), 3),
                "lluvia_mm": ll,
            })
    return pd.DataFrame(filas)


def cultivos():
    # Kc tomados de FAO-56 (valores tipicos); ciclos y agua del documento. Confirmar con INIAP.
    return pd.DataFrame([
        {"cultivo": "Arroz", "ciclo_dias": 120, "kc_ini": 1.05, "kc_med": 1.20, "kc_fin": 0.90,
         "agua_min_mm": 1000, "agua_max_mm": 1500, "tolera_inundacion": True},
        {"cultivo": "Soya", "ciclo_dias": 100, "kc_ini": 0.40, "kc_med": 1.15, "kc_fin": 0.50,
         "agua_min_mm": 450, "agua_max_mm": 650, "tolera_inundacion": False},
        {"cultivo": "Maíz duro", "ciclo_dias": 120, "kc_ini": 0.30, "kc_med": 1.20, "kc_fin": 0.35,
         "agua_min_mm": 500, "agua_max_mm": 800, "tolera_inundacion": False},
    ])


def estrategias():
    # Notas de 0 a 10 por criterio (columnas agregadas al final del contrato).
    base = {
        "A": {"agua": 12000, "suelo": 3, "plagas": 2, "ingresos": 7},
        "B": {"agua": 7500, "suelo": 8, "plagas": 8, "ingresos": 7},
        "C": {"agua": 6800, "suelo": 9, "plagas": 9, "ingresos": 6},
    }
    ajuste_zona = {"loma": {"A": 1.25, "B": 0.95, "C": 0.85},   # loma: arroz necesita mas riego
                   "ladera": {"A": 1.05, "B": 1.0, "C": 0.95},
                   "baja": {"A": 0.95, "B": 1.05, "C": 1.0}}
    ajuste_esc = {"normal": 1.0, "nino": 0.8, "nina": 1.2}
    filas = []
    for z in ZONAS:
        zid, tipo = z["zona_id"], z["tipo"]
        for esc, fe in ajuste_esc.items():
            for est, v in base.items():
                agua = v["agua"] * ajuste_zona[tipo][est] * fe
                nota_agua = round(10 - (agua - 5000) / 1000, 1)
                riesgo_inund = tipo == "baja" and esc == "nino" and est in ("B", "C")
                # En la zona baja el maiz (estrategia C) sufre con el encharcamiento
                maiz_en_baja = tipo == "baja" and est == "C"
                # En la ladera, dejar el suelo pelado entre ciclos favorece la erosion
                erosion = tipo == "ladera" and est == "A"
                filas.append({
                    "estrategia": est, "zona_id": zid, "escenario": esc,
                    "agua_m3_ha": round(agua, -1),
                    "puntaje": None,  # lo calcula la app segun las prioridades
                    "nota_agua": max(0, min(10, nota_agua)),
                    "nota_suelo": v["suelo"] - (2 if maiz_en_baja else 0) - (1 if erosion else 0),
                    "nota_plagas": v["plagas"],
                    "nota_ingresos": v["ingresos"] - (2 if riesgo_inund else 0) - (2 if maiz_en_baja else 0),
                })
    return pd.DataFrame(filas)


def estrategias_info():
    return [
        {"estrategia": "A", "nombre": "Base: arroz todo el año",
         "secuencia": "Arroz → Arroz",
         "descripcion": "Lo que se hace hoy: dos o tres ciclos de arroz seguidos.",
         "evidencia": ["Mercado seguro y práctica conocida en Daule"],
         "beneficios": ["Ingreso conocido", "No requiere semilla nueva"],
         "vacios": ["Costo real del riego en verano en cada finca"],
         "riesgos": ["Más agua en verano", "Plagas del arroz se mantienen", "Suelo se desgasta"]},
        {"estrategia": "B", "nombre": "Rotación simple: arroz y soya",
         "secuencia": "Arroz (invierno) → Soya (verano)",
         "descripcion": "Arroz con las lluvias y soya aprovechando la humedad que queda.",
         "evidencia": ["Meses secos de junio a noviembre (NASA POWER)",
                       "Humedad que queda tras la cosecha (NDMI)",
                       "Rotación arroz–soya documentada por el INIAP"],
         "beneficios": ["Menos agua en verano", "Aporta nitrógeno al suelo",
                        "Corta el ciclo de plagas del arroz", "Ingreso adicional"],
         "vacios": ["Datos de suelo a nivel de finca", "Precio local de la soya"],
         "riesgos": ["La soya no tolera el encharcamiento",
                     "Conseguir semilla y comprador de soya"]},
        {"estrategia": "C", "nombre": "Rotación de 2 años",
         "secuencia": "Año 1: Arroz → Soya | Año 2: Maíz → Soya",
         "descripcion": "Alterna arroz y maíz en invierno, con soya en cada verano.",
         "evidencia": ["Elevación SRTM: la loma no se inunda",
                       "Balance de agua con NASA POWER"],
         "beneficios": ["La mayor mejora del suelo", "Diversifica ingresos"],
         "vacios": ["Rendimientos locales de maíz después de soya"],
         "riesgos": ["Más manejo y planificación", "El maíz no tolera inundación en zona baja"]},
    ]


def reglas():
    return [
        {"id": "R1", "texto_campo": "No siembres soya en zonas que se inundaron en ese mes en 2 o más de los últimos 5 años.",
         "condicion": "ndwi > 0 en el mes de siembra en >= 2 de 5 años",
         "evidencia": "NDWI de Landsat 8 y 9, 2021-2025", "zona_id": ID_DE["baja"]},
        {"id": "R2", "texto_campo": "Siembra soya apenas cosechas el arroz de invierno, mientras el suelo aún guarda humedad.",
         "condicion": "NDMI alto en mayo-junio después de la cosecha",
         "evidencia": "Serie de NDMI por zona", "zona_id": None},
        {"id": "R3", "texto_campo": "En la loma, prefiere maíz en invierno y soya en verano; el arroz necesita mucha más agua.",
         "condicion": "elevación > umbral y balance de agua negativo",
         "evidencia": "SRTM y balance de agua con NASA POWER", "zona_id": ID_DE["loma"]},
        {"id": "R4", "texto_campo": "Si se anuncia El Niño, evita sembrar en la zona baja al inicio del invierno.",
         "condicion": "año El Niño y zona baja",
         "evidencia": "Lluvia de IMERG en años El Niño", "zona_id": ID_DE["baja"]},
        {"id": "R5", "texto_campo": "En la ladera, siembra siguiendo las curvas de nivel y deja rastrojo sobre el suelo para que la lluvia no lo arrastre.",
         "condicion": "pendiente alta y lluvias fuertes",
         "evidencia": "Pendiente del SRTM", "zona_id": ID_DE["ladera"]},
    ]


def main():
    MOCK.mkdir(parents=True, exist_ok=True)
    clim = climatologia()
    mensual = clima_mensual()
    clim.to_csv(MOCK / "climatologia_daule.csv", index=False)
    mensual.to_csv(MOCK / "clima_mensual_daule.csv", index=False)
    lluvia_imerg().to_csv(MOCK / "lluvia_imerg_daule.csv", index=False)
    (MOCK / "zonas_daule.geojson").write_text(json.dumps(zonas_geojson(), indent=2), encoding="utf-8")
    series_zonas(mensual).to_csv(MOCK / "series_zonas.csv", index=False)
    cultivos().to_csv(MOCK / "cultivos.csv", index=False)
    estrategias().to_csv(MOCK / "estrategias.csv", index=False)
    (MOCK / "estrategias_info.json").write_text(
        json.dumps(estrategias_info(), indent=2, ensure_ascii=False), encoding="utf-8")
    (MOCK / "reglas.json").write_text(json.dumps(reglas(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Datos de prueba creados en {MOCK}")
    for f in sorted(MOCK.iterdir()):
        print("  -", f.name)


if __name__ == "__main__":
    main()
