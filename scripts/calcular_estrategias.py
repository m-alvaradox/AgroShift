"""
Agroshift - estrategias.csv con datos reales (balance de agua FAO-56 + reglas de P4).

Lee (sin modificarlos):
    data/processed/clima_diario_daule.csv   P1 (Mario): NASA POWER diario -> ET0 Hargreaves y lluvia
    app/data/lluvia_imerg_daule.csv         tipo de año de cada temporada (scripts/adaptar_datos.py,
                                            a partir de la serie GPM IMERG de Mario)
    app/data/climatologia_daule.csv         meses de lluvias y de seca -> fechas de siembra
    data/cultivos.csv                       P4 (Johan): ciclo y Kc de cada cultivo
    data/processed/zonas_daule.geojson      P3 (Austin): zonas 1, 2 y 3
    origin/p4-reglas:src/reglas.py          P4 (Johan): evaluador de reglas (se lee con git show,
                                            sin hacer merge de su rama)

Escribe data/processed/estrategias.csv con las columnas del contrato:
    estrategia, zona_id, escenario, agua_m3_ha, nota_agua, nota_suelo, nota_plagas, nota_ingresos
y al final columnas de detalle para revisar el calculo.

Metodo del agua (por cada ciclo de cultivo, dia a dia):
    ETc = Kc(dia) x ET0                                   (FAO-56; Kc por etapas, ver ETAPAS)
    lluvia util = min(80 % de la lluvia del dia, ETc)     (mismo supuesto que la metodologia P1)
    riego ETc = suma de (ETc - lluvia util)               (nunca negativo)
    arroz: + saturacion + lamina + percolacion x dias - lluvia sobrante (minimo 0)
    agua_m3_ha = promedio por ciclo de cultivo (1 mm = 10 m3/ha)

Escenarios: cada temporada (año agricola dic-nov) tiene un tipo de año segun su lluvia IMERG
de diciembre a mayo. El escenario usa los años reales de ese tipo (promedio si hay varios).

Uso (desde la raiz del proyecto, despues de scripts/adaptar_datos.py):
    python scripts/calcular_estrategias.py
"""
import math
import subprocess
import sys
import types
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))
from adaptar_datos import latitud_centro, radiacion_extraterrestre  # noqa: E402
from utils.carga import NOMBRE_CULTIVO, leer_json_archivo  # noqa: E402
from utils.logica import MESES_LARGOS, SECUENCIAS, temporadas  # noqa: E402
from utils.ui import tipo_zona  # noqa: E402

PROC = ROOT / "data" / "processed"
APP_DATA = ROOT / "app" / "data"
SALIDA = PROC / "estrategias.csv"

# ======================================================================================
# PARAMETROS VISIBLES (a validar por Johan - P4 y Mario - P1)
# ======================================================================================

# Fraccion de la lluvia diaria que aprovecha el cultivo, limitada por la ETc del dia.
# Fuente: supuesto experimental de la metodologia P1 (docs/metodologia_p1.md, "Deficit hidrico").
APROVECHAMIENTO_LLUVIA = 0.80

# Agua extra del arroz bajo inundacion (mm por ciclo), ademas de la ETc.
# Fuente: FAO, "Irrigation Water Management: Irrigation Water Needs" (Brouwer y Heibloem, 1986),
# capitulo 4 (el mismo que cita Johan en la regla AGR-005 y en docs/fuentes_catalogo_cultivos.md):
# IN_arroz = ETc + SAT + PERC + WL - Pe. Los valores de abajo son los ORIENTATIVOS de ese manual
# (saturar el suelo ~200 mm, establecer una lamina ~100 mm, percolacion y filtracion de varios
# mm por dia segun el suelo). VALIDAR las cifras exactas en la fuente y con datos de Daule.
ARROZ_SATURACION_MM = 200       # mojar el suelo hasta saturarlo antes de sembrar
ARROZ_LAMINA_MM = 100           # establecer la lamina de agua del arrozal
ARROZ_PERCOLACION_MM_DIA = 4.0  # perdidas por percolacion y filtracion (suelo arcilloso)

# Ajustes por tipo de zona (SUPUESTOS a validar con Austin - P3). La zona se reconoce por su nombre.
#   perc  : multiplica la percolacion del arroz
#   lluvia: fraccion de la lluvia que entra al suelo (el resto escurre)
FACTOR_ZONA = {
    "baja":   {"perc": 0.5, "lluvia": 1.00},  # napa alta y suelo pesado: pierde poca agua hacia abajo
    "ladera": {"perc": 1.0, "lluvia": 0.85},  # pendiente: parte de la lluvia escurre
    "loma":   {"perc": 1.5, "lluvia": 1.00},  # suelo mas suelto y alto: drena mas rapido
    "transicion": {"perc": 1.0, "lluvia": 1.00},
}

# Contexto de cada tipo de zona para el evaluador de Johan (drenaje y riesgo de anegamiento).
# Se deduce del nombre de la zona de P3 ("Zona baja que se encharca", "Ladera...", "Loma seca").
CONTEXTO_ZONA = {
    "baja":   {"drenaje": "deficiente", "riesgo_anegamiento": "alto"},
    "ladera": {"drenaje": "bueno", "riesgo_anegamiento": "bajo"},
    "loma":   {"drenaje": "bien_drenado", "riesgo_anegamiento": "bajo"},
    "transicion": {"drenaje": None, "riesgo_anegamiento": None},
}

# Duracion de las etapas como fraccion del ciclo (inicial, desarrollo, media, final).
# Fuente: FAO-56, Tabla 11 (arroz 30/30/60/30; soya tropical 15/15/40/15; maiz grano 20/35/40/30).
ETAPAS = {
    "Arroz": (0.20, 0.20, 0.40, 0.20),
    "Soya": (0.18, 0.18, 0.46, 0.18),
    "Maíz duro": (0.16, 0.28, 0.32, 0.24),
}

# Nombres de la app -> nombres del catalogo de Johan (para su evaluador)
ID_P4 = {v: k for k, v in NOMBRE_CULTIVO.items()}
LEGUMINOSAS = {"Soya"}


# --- Datos ----------------------------------------------------------------------------

def clima_diario() -> pd.DataFrame:
    """ET0 Hargreaves y lluvia diaria de NASA POWER (igual que scripts/adaptar_datos.py)."""
    d = pd.read_csv(PROC / "clima_diario_daule.csv", parse_dates=["fecha"])
    rango = (d["temperatura_maxima"] - d["temperatura_minima"]).clip(lower=0)
    ra = radiacion_extraterrestre(d["fecha"], latitud_centro())
    d["et0"] = 0.0023 * (d["temperatura_media"] + 17.8) * np.sqrt(rango) * 0.408 * ra
    d["lluvia"] = d["precipitacion"].clip(lower=0)
    return d.set_index("fecha")[["et0", "lluvia"]].dropna()


def cultivos() -> dict:
    c = pd.read_csv(ROOT / "data" / "cultivos.csv")
    c["cultivo"] = [NOMBRE_CULTIVO.get(str(x).strip().lower(), str(x).strip()) for x in c["cultivo"]]
    return {f["cultivo"]: f for _, f in c.iterrows()}


def zonas() -> list[dict]:
    geo = leer_json_archivo(PROC / "zonas_daule.geojson")
    salida = []
    for f in geo["features"]:
        p = f["properties"]
        salida.append({"zona_id": int(p["zona_id"]), "nombre": p["nombre_comun"],
                       "tipo": tipo_zona(p["nombre_comun"])})
    return sorted(salida, key=lambda z: z["zona_id"])


def escenarios() -> dict[str, list[str]]:
    """{'nino': ['2024-2025'], 'neutro': [...], 'nina': [...]} desde la serie IMERG adaptada."""
    s = pd.read_csv(APP_DATA / "lluvia_imerg_daule.csv")
    s = s[s["enso"].isin(["nino", "neutro", "nina"])].drop_duplicates("temporada")
    return {e: sorted(s.loc[s["enso"] == e, "temporada"]) for e in ["nino", "neutro", "nina"]}


def reglas_p4():
    """Modulo src/reglas.py de Johan leido desde su rama (sin merge). None si no se puede."""
    try:
        codigo = subprocess.run(["git", "show", "origin/p4-reglas:src/reglas.py"], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8", check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"[aviso] No se pudo leer src/reglas.py de origin/p4-reglas ({e}); notas sin sus alertas.")
        return None
    mod = types.ModuleType("reglas_p4")
    mod.__file__ = str(ROOT / "src" / "reglas.py")  # sus rutas apuntan a data/ de este repo
    exec(compile(codigo, "origin/p4-reglas:src/reglas.py", "exec"), mod.__dict__)
    return mod


# --- Balance de agua ----------------------------------------------------------------------

def kc_diario(cultivo: str, c, dias: int) -> np.ndarray:
    """Curva de Kc de FAO-56: constante, sube, constante y baja."""
    f_ini, f_des, f_med, _ = ETAPAS.get(cultivo, (0.2, 0.25, 0.35, 0.2))
    l_ini, l_des, l_med = round(dias * f_ini), round(dias * f_des), round(dias * f_med)
    l_fin = dias - l_ini - l_des - l_med
    return np.concatenate([
        np.full(l_ini, c["kc_ini"]),
        np.linspace(c["kc_ini"], c["kc_med"], l_des, endpoint=False),
        np.full(l_med, c["kc_med"]),
        np.linspace(c["kc_med"], c["kc_fin"], l_fin),
    ])


def ciclo(cultivo: str, inicio: date, clima: pd.DataFrame, cult: dict, tipo: str) -> dict | None:
    c = cult[cultivo]
    dias = int(c["ciclo_dias"])
    tramo = clima.loc[pd.Timestamp(inicio): pd.Timestamp(inicio + timedelta(days=dias - 1))]
    if len(tramo) < dias:
        return None  # el clima diario no cubre todo el ciclo
    fz = FACTOR_ZONA.get(tipo, FACTOR_ZONA["transicion"])
    etc = kc_diario(cultivo, c, dias) * tramo["et0"].to_numpy()
    lluvia = APROVECHAMIENTO_LLUVIA * fz["lluvia"] * tramo["lluvia"].to_numpy()
    util = np.minimum(lluvia, etc)
    riego_etc = float((etc - util).sum())
    extra = 0.0
    if cultivo == "Arroz":
        sobrante = float(np.clip(lluvia - etc, 0, None).sum())
        bruto = ARROZ_SATURACION_MM + ARROZ_LAMINA_MM + ARROZ_PERCOLACION_MM_DIA * fz["perc"] * dias
        extra = max(0.0, bruto - sobrante)
    return {"cultivo": cultivo, "etc_mm": float(etc.sum()), "lluvia_util_mm": float(util.sum()),
            "riego_etc_mm": riego_etc, "extra_arroz_mm": extra, "riego_mm": riego_etc + extra}


def fechas_siembra(temporada: str, clim: pd.DataFrame) -> tuple[date, date]:
    """Siembra al inicio de las lluvias y al inicio de la seca dentro del año agricola."""
    y = int(temporada.split("-")[1])
    m_lluvia, m_seca = (m + 1 for m in temporadas(clim))  # meses 1-12
    f1 = date(y - 1 if m_lluvia == 12 else y, m_lluvia, 1)
    f2 = date(f1.year, m_seca, 1)
    if f2 <= f1:
        f2 = date(f1.year + 1, m_seca, 1)
    return f1, f2


def agua_estrategia(est: str, temps: list[str], tipo: str, clima, cult, clim) -> dict:
    """Promedio por ciclo y por año de los años reales del escenario."""
    ciclos = []
    for t in temps:
        f1, f2 = fechas_siembra(t, clim)
        for lluvias, seca in SECUENCIAS[est]:
            for cultivo, inicio in ((lluvias, f1), (seca, f2)):
                r = ciclo(cultivo, inicio, clima, cult, tipo)
                if r:
                    ciclos.append(r)
    if not ciclos:
        return {}
    df = pd.DataFrame(ciclos)
    return {"agua_m3_ha": df["riego_mm"].mean() * 10, "agua_anual_m3_ha": df["riego_mm"].mean() * 20,
            "etc_mm": df["etc_mm"].mean(), "lluvia_util_mm": df["lluvia_util_mm"].mean(),
            "riego_etc_mm": df["riego_etc_mm"].mean(), "extra_arroz_mm": df["extra_arroz_mm"].mean(),
            "ciclos": len(df)}


# --- Notas de suelo, plagas e ingresos (0 a 10) ---------------------------------------------
#
# Reglas simples y explicables (a validar con Johan - P4):
#   Suelo   : base 5; + 3 x fraccion de ciclos con leguminosa (soya fija nitrogeno);
#             + 1 si rota 3 cultivos distintos; - 2 si repite siempre el mismo cultivo;
#             - 1 mas si ese monocultivo es en la ladera (suelo suelto expuesto a la erosion).
#   Plagas  : base 8; - 3 por cada advertencia de repeticion del evaluador de Johan (AGR-001:
#             arroz tras arroz mantiene malezas, plagas y enfermedades); + 1 si rota 3 cultivos.
#   Ingresos: base 6; + 1 x fraccion de ciclos de lluvias con arroz en la zona baja (es lo que
#             mejor rinde en tierra que se encharca); + 0,5 por cada cultivo extra (diversifica);
#             - 1,5 por cada alerta de Johan (AGR-003 drenaje y AGR-004 anegamiento: soya o maiz
#             en zona que se encharca); - 1 en un año muy lluvioso si hay soya o maiz en zona baja.
#   Agua    : nota_agua = 10 x (1 - agua / (1,25 x la mayor agua de la tabla)); 10 = casi sin riego
#             y la combinacion que mas agua pide queda en 2.

def notas(est: str, tipo: str, escenario: str, alertas: list[dict]) -> dict:
    pares = SECUENCIAS[est]
    cultivos_seq = [c for par in pares for c in par]
    n = len(cultivos_seq)
    distintos = len(set(cultivos_seq))
    mono = distintos == 1
    frac_leg = sum(c in LEGUMINOSAS for c in cultivos_seq) / n
    advertencias = sum(a["estado"] == "advertencia" for a in alertas)
    alertas_zona = sum(a["estado"] == "alerta" for a in alertas)
    sensibles = any(c in ("Soya", "Maíz duro") for c in cultivos_seq)

    suelo = 5 + 3 * frac_leg + (1 if distintos >= 3 else 0) - (2 if mono else 0) \
        - (1 if mono and tipo == "ladera" else 0)
    plagas = 8 - 3 * advertencias + (1 if distintos >= 3 else 0)
    arroz_lluvias = sum(par[0] == "Arroz" for par in pares) / len(pares)
    ingresos = 6 + (arroz_lluvias if tipo == "baja" else 0) + 0.5 * (distintos - 1) \
        - 1.5 * alertas_zona - (1 if escenario == "nino" and tipo == "baja" and sensibles else 0)
    lim = lambda v: round(max(0.0, min(10.0, v)), 1)  # noqa: E731
    return {"nota_suelo": lim(suelo), "nota_plagas": lim(plagas), "nota_ingresos": lim(ingresos),
            "alertas_p4": "; ".join(f"{a['id']}:{a['estado']}" for a in alertas)}


def alertas_de(mod, est: str, zona: dict) -> list[dict]:
    if mod is None:
        # sin el evaluador: repeticion de arroz y soya/maiz en zona que se encharca
        seq = [c for par in SECUENCIAS[est] for c in par]
        a = [{"id": "AGR-001", "estado": "advertencia"}] if seq.count("Arroz") >= 2 and len(set(seq)) == 1 else []
        if zona["tipo"] == "baja" and any(c in ("Soya", "Maíz duro") for c in seq):
            a += [{"id": "AGR-003", "estado": "alerta"}, {"id": "AGR-004", "estado": "alerta"}]
        return a
    contexto = {"zona_id": str(zona["zona_id"]), **CONTEXTO_ZONA.get(zona["tipo"], {})}
    return mod.evaluar_reglas(est, contexto)


# --- Principal ---------------------------------------------------------------------------------

ESCENARIO_APP = {"nino": "nino", "neutro": "normal", "nina": "nina"}


def main() -> None:
    clima = clima_diario()
    cult = cultivos()
    clim = pd.read_csv(APP_DATA / "climatologia_daule.csv")
    zs = zonas()
    esc = escenarios()
    mod = reglas_p4()

    f1, f2 = fechas_siembra("2024-2025", clim)
    print(f"Siembras: temporada de lluvias el 1 de {MESES_LARGOS[f1.month - 1]}, temporada seca "
          f"el 1 de {MESES_LARGOS[f2.month - 1]} (segun app/data/climatologia_daule.csv)")
    for e, t in esc.items():
        print(f"  escenario {ESCENARIO_APP[e]:<6} <- temporadas {', '.join(t)}")

    filas = []
    for z in zs:
        for e, temps in esc.items():
            for est in SECUENCIAS:
                agua = agua_estrategia(est, temps, z["tipo"], clima, cult, clim)
                if not agua:
                    print(f"[aviso] sin datos para {est} zona {z['zona_id']} escenario {e}")
                    continue
                filas.append({
                    "estrategia": est, "zona_id": z["zona_id"], "escenario": ESCENARIO_APP[e],
                    "agua_m3_ha": round(agua["agua_m3_ha"], -1),
                    **notas(est, z["tipo"], ESCENARIO_APP[e], alertas_de(mod, est, z)),
                    "zona": z["nombre"], "temporadas": " ".join(temps), "ciclos": agua["ciclos"],
                    "etc_mm": round(agua["etc_mm"], 1), "lluvia_util_mm": round(agua["lluvia_util_mm"], 1),
                    "riego_etc_mm": round(agua["riego_etc_mm"], 1),
                    "extra_arroz_mm": round(agua["extra_arroz_mm"], 1),
                    "agua_anual_m3_ha": round(agua["agua_anual_m3_ha"], -1),
                })
    df = pd.DataFrame(filas)
    tope = 1.25 * df["agua_m3_ha"].max()
    df.insert(4, "nota_agua", (10 * (1 - df["agua_m3_ha"] / tope)).clip(0, 10).round(1))
    columnas = ["estrategia", "zona_id", "escenario", "agua_m3_ha", "nota_agua", "nota_suelo",
                "nota_plagas", "nota_ingresos", "zona", "temporadas", "ciclos", "etc_mm",
                "lluvia_util_mm", "riego_etc_mm", "extra_arroz_mm", "agua_anual_m3_ha", "alertas_p4"]
    df = df[columnas]
    df.to_csv(SALIDA, index=False)

    print(f"\n{SALIDA.relative_to(ROOT).as_posix()}: {len(df)} filas "
          f"({df['zona_id'].nunique()} zonas x {df['escenario'].nunique()} escenarios x 3 estrategias)"
          f"{'' if mod else '  [sin evaluador de P4]'}")
    tabla = df.pivot_table(index=["zona_id", "estrategia"], columns="escenario", values="agua_m3_ha")
    print("\nAgua por ciclo (m3/ha):")
    print(tabla[["nina", "normal", "nino"]].round(-1).astype(int).to_string())


if __name__ == "__main__":
    main()
