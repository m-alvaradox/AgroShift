"""
Logica de la app: puntajes, recomendacion, plan de cultivos por mes y senales.

IMPORTANTE: es una logica de EJEMPLO para que la app funcione desde ya.
Cuando P1 y P4 entreguen su version, se reemplazan estas funciones
manteniendo los mismos nombres.
"""
import math
from datetime import date

import pandas as pd

# Un mes "con agua sobre el terreno" si al menos este % de la zona tiene NDWI > 0
# (columna pct_agua de scripts/series_por_zona.py). Si no hay pct_agua, se usa NDWI medio > 0.
UMBRAL_AGUA_PCT = 5.0


def meses_con_agua(serie: pd.DataFrame) -> pd.DataFrame:
    """Filas de la serie con agua sobre el terreno."""
    if "pct_agua" in serie and serie["pct_agua"].notna().any():
        return serie[serie["pct_agua"] >= UMBRAL_AGUA_PCT]
    return serie[serie["ndwi"] > 0]


CRITERIOS = {
    "nota_agua": "Ahorrar agua",
    "nota_suelo": "Cuidar el suelo",
    "nota_plagas": "Menos plagas",
    "nota_ingresos": "Ganar más",
}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Secuencia de cultivos de cada estrategia: (temporada de lluvias, temporada seca)
SECUENCIAS = {
    "A": [("Arroz", "Arroz")],
    "B": [("Arroz", "Soya")],
    "C": [("Arroz", "Soya"), ("Maíz duro", "Soya")],
}


# --- Puntaje y recomendacion -------------------------------------------------------

def puntajes(est: pd.DataFrame, pesos: dict) -> pd.DataFrame:
    total = sum(pesos.values()) or 1
    df = est.copy()
    df["puntaje"] = (sum(df[c] * pesos[c] for c in CRITERIOS) / total).round(1)
    return df


def comparar(est: pd.DataFrame, zona_id: int, escenario: str, pesos: dict) -> pd.DataFrame:
    df = est[(est["zona_id"] == zona_id) & (est["escenario"] == escenario)]
    return puntajes(df, pesos).sort_values("puntaje", ascending=False).reset_index(drop=True)


def razones(fila: pd.Series, pesos: dict, n: int = 2) -> list[str]:
    aportes = {CRITERIOS[c]: fila[c] * pesos[c] for c in CRITERIOS if pesos[c] > 0}
    return [k for k, _ in sorted(aportes.items(), key=lambda kv: -kv[1])[:n]]


def estrellas(puntaje: float) -> str:
    llenas = int(round(puntaje / 2))
    return "★" * llenas + "☆" * (5 - llenas)


# --- Plan de cultivos mes a mes ----------------------------------------------------

def temporadas(clim: pd.DataFrame) -> tuple[int, int]:
    """Mes (0-11) en que empiezan las lluvias y mes en que empieza la epoca seca."""
    tipos = clim.sort_values("mes")["tipo_mes"].tolist()
    no_seco = [i for i, t in enumerate(tipos) if t != "seco"]
    if not no_seco:
        return 0, 4
    inicio = no_seco[0]
    # buscar el primer mes no seco despues de una racha seca (inicio real de lluvias)
    for i in range(12):
        if tipos[i] != "seco" and tipos[i - 1] == "seco":
            inicio = i
            break
    fin = inicio
    while tipos[(fin + 1) % 12] != "seco" and fin - inicio < 11:
        fin += 1
    return inicio, (fin + 1) % 12


def plan(estrategia: str, clim: pd.DataFrame, cult: pd.DataFrame) -> list[list[dict | None]]:
    """
    Para cada anio de la estrategia, una lista de 12 meses con
    {'cultivo', 'etapa'} o None si el terreno descansa.
    """
    ciclo = dict(zip(cult["cultivo"], cult["ciclo_dias"]))
    inicio, seca = temporadas(clim)
    anios = []
    for lluvias, verano in SECUENCIAS.get(estrategia, [("Arroz", "Soya")]):
        meses: list[dict | None] = [None] * 12
        for cultivo, arranque in ((lluvias, inicio), (verano, seca)):
            n = max(1, math.ceil(ciclo.get(cultivo, 120) / 30))
            for k in range(n):
                m = (arranque + k) % 12
                if meses[m] is None:
                    etapa = "siembra" if k == 0 else ("cosecha" if k == n - 1 else "crece")
                    meses[m] = {"cultivo": cultivo, "etapa": etapa}
        anios.append(meses)
    return anios


def accion_del_mes(plan_anio: list, mes: int) -> str:
    """Una frase simple sobre que hacer en el mes indicado (0-11)."""
    hoy = plan_anio[mes]
    if hoy:
        c = hoy["cultivo"].lower()
        if hoy["etapa"] == "siembra":
            return f"Es momento de sembrar {c}."
        if hoy["etapa"] == "cosecha":
            return f"Prepárate para cosechar el {c}."
        return f"Tu {c} está creciendo: cuida el agua y revisa plagas."
    for k in range(1, 12):
        sig = plan_anio[(mes + k) % 12]
        if sig and sig["etapa"] == "siembra":
            cuando = "el próximo mes" if k == 1 else f"en {MESES_LARGOS[(mes + k) % 12]}"
            return f"El terreno descansa. Prepáralo: {cuando} toca sembrar {sig['cultivo'].lower()}."
    return "El terreno descansa."


# --- Senales del ultimo mes ----------------------------------------------------------

def senal_lluvia(mensual: pd.DataFrame, clim: pd.DataFrame) -> dict:
    ult = mensual.sort_values("fecha").dropna(subset=["lluvia_mm"]).iloc[-1]
    tipica = float(clim.set_index("mes").loc[int(ult["mes"]), "lluvia_mm"])
    real = float(ult["lluvia_mm"])
    mes = MESES_LARGOS[int(ult["mes"]) - 1]
    if real > max(3 * tipica, tipica + 50):
        veces = real / tipica if tipica > 1 else None
        detalle = f"unas {veces:.0f} veces lo normal" if veces and veces >= 3 else "mucho más de lo normal"
        return {"estado": "alerta", "titulo": "Llovió muchísimo",
                "texto": f"En {mes} cayeron {real:.0f} mm, {detalle}. Hay riesgo de inundación en la zona baja."}
    if real > 1.3 * tipica + 10:
        return {"estado": "atento", "titulo": "Llovió más de lo normal",
                "texto": f"En {mes} cayeron {real:.0f} mm; lo típico es {tipica:.0f} mm."}
    if real < 0.5 * tipica - 10:
        return {"estado": "atento", "titulo": "Llovió menos de lo normal",
                "texto": f"En {mes} cayeron {real:.0f} mm; lo típico es {tipica:.0f} mm. Cuida el agua."}
    return {"estado": "bien", "titulo": "Lluvia normal",
            "texto": f"En {mes} cayeron {real:.0f} mm, parecido a lo típico ({tipica:.0f} mm)."}


def senal_verdor(serie: pd.DataFrame) -> dict:
    s = serie.dropna(subset=["ndvi"]).sort_values("fecha")
    if s.empty:
        return {"estado": "sin", "titulo": "Sin imagen reciente", "texto": "Las nubes no dejaron ver el campo."}
    ult = s.iloc[-1]
    mismo_mes = s[s["fecha"].dt.month == ult["fecha"].month]["ndvi"].mean()
    mes = MESES_LARGOS[ult["fecha"].month - 1]
    if ult["ndvi"] < mismo_mes - 0.08:
        return {"estado": "atento", "titulo": "Campo menos verde",
                "texto": f"En {mes} el campo se vio menos verde que en otros años. Puede faltar agua o haber plagas."}
    if ult["ndvi"] > mismo_mes + 0.08:
        return {"estado": "bien", "titulo": "Campo más verde",
                "texto": f"En {mes} el campo se vio más verde que en otros años."}
    return {"estado": "bien", "titulo": "Campo como siempre",
            "texto": f"En {mes} el verdor fue parecido al de otros años."}


def senal_agua(serie: pd.DataFrame) -> dict:
    s = serie.dropna(subset=["ndwi"]).sort_values("fecha")
    if s.empty:
        return {"estado": "sin", "titulo": "Sin imagen reciente", "texto": "Las nubes no dejaron ver el campo."}
    ult = s.iloc[-1]
    mes = MESES_LARGOS[ult["fecha"].month - 1]
    if ult["ndwi"] > 0:
        return {"estado": "alerta", "titulo": "Agua sobre el terreno",
                "texto": f"En {mes} el satélite vio agua en la superficie. No siembres soya ni maíz ahí."}
    return {"estado": "bien", "titulo": "Sin agua encharcada",
            "texto": f"En {mes} el satélite no vio agua acumulada en el terreno."}


def mes_actual() -> int:
    return date.today().month - 1


def calendario(clim: pd.DataFrame, cult: pd.DataFrame, serie_zona: pd.DataFrame,
               zona_nombre: str) -> tuple[pd.DataFrame, list[str]]:
    """Calendario por cultivo con riesgo de encharcamiento (se usa en Mi campo)."""
    inicio, seca = temporadas(clim)
    s = serie_zona.dropna(subset=["ndwi"]).assign(mes=lambda d: d["fecha"].dt.month - 1)
    anios_agua = meses_con_agua(s).groupby("mes")["fecha"].apply(lambda f: f.dt.year.nunique())
    filas, notas = {}, []
    loma = "loma" in zona_nombre.lower()
    for _, c in cult.iterrows():
        nombre = c["cultivo"]
        n = max(1, math.ceil(c["ciclo_dias"] / 30))
        arranque = seca if nombre.lower().startswith("soya") else inicio
        fila = [""] * 12
        for k in range(n):
            fila[(arranque + k) % 12] = "siembra" if k == 0 else ("cosecha" if k == n - 1 else "crece")
        n_agua = int(anios_agua.get(arranque, 0))
        if not bool(c["tolera_inundacion"]) and n_agua >= 2:
            notas.append(f"{nombre}: en {MESES_LARGOS[arranque]} hubo agua en el terreno en "
                         f"{n_agua} de los últimos años.")
            fila = ["riesgo" if v else "" for v in fila]
        if loma and nombre.lower().startswith("arroz"):
            notas.append("Arroz en la loma: necesita mucha más agua que el maíz o la soya.")
            fila = ["riesgo" if v else "" for v in fila]
        filas[nombre] = fila
    return pd.DataFrame.from_dict(filas, orient="index", columns=MESES), notas
