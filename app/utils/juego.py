"""
Logica del juego "Arma tu año" y de las senales simples de Mi finca y el Asistente.

Todo son funciones puras: reciben datos (DataFrames, listas, dicts) y devuelven
datos. No usan Streamlit, asi se pueden probar solas:

    from utils import juego
    juego.jugar(["Arroz", "Soya", "Arroz"], "baja", "nino", clim=clim)

Los valores que todavia no salen de los datos del equipo estan marcados con
"# TODO: reemplazar con datos reales" y la app muestra "Simulacion de ejemplo".
"""
from __future__ import annotations

import pandas as pd

from utils.logica import SECUENCIAS

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# --- Temporadas y cartas -------------------------------------------------------------

TEMPORADAS = [
    {"nombre": "Temporada 1", "meses": "Ene–Abr", "detalle": "Lluvias", "icono": "🌧️", "idx": [0, 1, 2, 3]},
    {"nombre": "Temporada 2", "meses": "May–Ago", "detalle": "Empieza la seca", "icono": "⛅", "idx": [4, 5, 6, 7]},
    {"nombre": "Temporada 3", "meses": "Sep–Dic", "detalle": "Seca", "icono": "☀️", "idx": [8, 9, 10, 11]},
]

# Mazo: los cultivos de cultivos.csv (Maíz duro se muestra como "Maíz") y el descanso.
CARTAS = {
    "Arroz": {"icono": "🌾", "frase": "Aguanta el agua", "slug": "arroz"},
    "Maíz": {"icono": "🌽", "frase": "Buen precio", "slug": "maiz"},
    "Soya": {"icono": "🫘", "frase": "Da fuerza al suelo", "slug": "soya"},
    "Descanso": {"icono": "🍂", "frase": "La tierra respira", "slug": "descanso"},
}


def carta(cultivo: str) -> str:
    """Nombre de carta para un cultivo de los datos ('Maíz duro' -> 'Maíz')."""
    return "Maíz" if cultivo.lower().startswith("ma") else cultivo


def secuencia_3t(pares: list[tuple[str, str]]) -> list[str]:
    """
    Adapta una secuencia de estrategias (pares lluvias -> seca) a las 3 temporadas:
    T1 = cultivo de lluvias, T2 = cultivo de la seca, T3 = el siguiente de la rotacion.
      A [(Arroz, Arroz)]                 -> Arroz, Arroz, Arroz
      B [(Arroz, Soya)]                  -> Arroz, Soya, Arroz
      C [(Arroz, Soya), (Maíz, Soya)]    -> Arroz, Soya, Maíz
    """
    # TODO: reemplazar con datos reales (calendario de 3 temporadas validado por P4)
    plano = [c for par in pares for c in par]
    return [carta(plano[i % len(plano)]) for i in range(3)]


NOMBRE_ATAJO = {"A": "Siempre arroz", "B": "Con soya", "C": "Rotación"}
ATAJOS = {k: {"nombre": NOMBRE_ATAJO.get(k, k), "secuencia": secuencia_3t(v)}
          for k, v in SECUENCIAS.items()}


def atajo_de(casillas: list) -> str | None:
    """Letra de la estrategia si las casillas son exactamente una de A, B o C."""
    for k, a in ATAJOS.items():
        if list(casillas) == a["secuencia"]:
            return k
    return None


# --- Datos que salen de los archivos ------------------------------------------------

def factor_lluvia(imerg: pd.DataFrame, escenario: str) -> float:
    """Cuanto llueve en un año El Niño o La Niña frente a uno normal (1 = igual)."""
    if escenario == "normal" or imerg is None or imerg.empty:
        return 1.0
    anual = (imerg.assign(anio=pd.to_datetime(imerg["fecha"]).dt.year)
             .groupby(["anio", "enso"], as_index=False)["lluvia_mm"].sum())
    prom = anual.groupby("enso")["lluvia_mm"].mean()
    if escenario not in prom.index or "neutro" not in prom.index or prom["neutro"] <= 0:
        return 1.0
    return float(prom[escenario] / prom["neutro"])


def falta_agua(clim: pd.DataFrame, factor: float = 1.0) -> list[float]:
    """Por temporada, que parte del agua que piden las plantas NO cubre la lluvia (0 a 1)."""
    c = clim.sort_values("mes").reset_index(drop=True)
    salida = []
    for t in TEMPORADAS:
        lluvia = float(c.loc[t["idx"], "lluvia_mm"].sum()) * factor
        evapora = float(c.loc[t["idx"], "et0_mm"].sum())
        salida.append(0.0 if evapora <= 0 else max(0.0, 1 - lluvia / evapora))
    return salida


def notas_estrategia(est: pd.DataFrame, estrategia: str, zona_id: int, escenario: str) -> dict | None:
    """Fila de estrategias.csv para esa estrategia, zona y año (o None si no existe)."""
    f = est[(est["estrategia"] == estrategia) & (est["zona_id"] == zona_id) & (est["escenario"] == escenario)]
    return None if f.empty else f.iloc[0].to_dict()


def barras_desde_notas(notas: dict) -> dict:
    """Las 3 barras del juego a partir de las notas reales (0 a 10)."""
    return {
        "agua": float(notas["nota_agua"]),
        "suelo": float(notas["nota_suelo"]),
        # la cosecha junta lo que se gana y lo que se pierde por plagas
        "cosecha": (float(notas["nota_ingresos"]) + float(notas["nota_plagas"])) / 2,
    }


# --- Simulacion del año --------------------------------------------------------------

# TODO: reemplazar con datos reales (ingresos y efecto en el suelo de cada cultivo, P4)
SIM_CULTIVO = {
    "Arroz": {"ingreso": 7.0, "suelo": 0.0},
    "Maíz": {"ingreso": 7.0, "suelo": -0.5},
    "Soya": {"ingreso": 6.0, "suelo": 2.5},
    "Descanso": {"ingreso": 0.0, "suelo": 1.0},
}
# TODO: reemplazar con datos reales (se usan solo si cultivos.csv no trae el dato)
AGUA_MM = {"Arroz": 1250.0, "Maíz": 650.0, "Soya": 550.0, "Descanso": 0.0}
TOLERA = {"Arroz": True, "Maíz": False, "Soya": False, "Descanso": True}
SUELO_INICIAL = 5.0


def _datos_cultivos(cult: pd.DataFrame | None) -> tuple[dict, dict]:
    agua, tolera = dict(AGUA_MM), dict(TOLERA)
    if cult is not None and not cult.empty:
        for _, c in cult.iterrows():
            k = carta(str(c["cultivo"]))
            if {"agua_min_mm", "agua_max_mm"} <= set(c.index):
                agua[k] = (float(c["agua_min_mm"]) + float(c["agua_max_mm"])) / 2
            tolera[k] = bool(c["tolera_inundacion"])
    return agua, tolera


def palabra(valor: float) -> str:
    return "Bien" if valor >= 7 else ("Regular" if valor >= 4 else "Bajo")


def _limitar(v: float) -> float:
    return round(max(0.0, min(10.0, v)), 1)


def simular(casillas: list[str], zona_tipo: str, escenario: str, *, clim: pd.DataFrame,
            cult: pd.DataFrame | None = None, factor: float = 1.0) -> tuple[dict, list[dict]]:
    """Barras simuladas (0 a 10) y eventos del año para cualquier combinacion de cartas."""
    agua_mm, tolera = _datos_cultivos(cult)
    falta = falta_agua(clim, factor)
    exito = [1.0, 1.0, 1.0]
    eventos = []

    def evento(i, tipo, texto, prioridad):
        eventos.append({"temporada": i, "meses": TEMPORADAS[i]["meses"], "tipo": tipo,
                        "texto": texto, "prioridad": prioridad})

    for i, c in enumerate(casillas):
        if c == "Descanso":
            evento(i, "bueno", "la tierra descansó y recuperó fuerza.", 3)
            continue
        if i == 0 and zona_tipo == "baja" and escenario == "nino" and c != "Arroz":
            exito[0] = 0.0
            evento(0, "malo", f"llegó El Niño y se inundó tu {c.lower()}.", 1)
        elif i == 0 and zona_tipo == "baja" and not tolera.get(c, False):
            exito[0] = 0.6
            evento(0, "malo", f"el terreno se encharcó y tu {c.lower()} sufrió.", 1)
        elif i == 0 and escenario == "nino" and c == "Arroz":
            evento(0, "info", "llegó El Niño con mucha lluvia y tu arroz aguantó el agua.", 2)
        if i > 0 and c == "Arroz" and escenario == "nina" and zona_tipo != "baja":
            exito[i] = 0.7
            evento(i, "malo", "llovió poco y el arroz pidió mucho riego.", 1)
        if c == "Soya":
            evento(i, "bueno", "la soya le dio fuerza al suelo.", 2)

    repetido = len(set(casillas)) == 1 and casillas[0] != "Descanso"
    suelo = SUELO_INICIAL + sum(SIM_CULTIVO[c]["suelo"] for c in casillas)
    cosecha = sum(SIM_CULTIVO[c]["ingreso"] * exito[i] for i, c in enumerate(casillas)) / 3
    if repetido:
        suelo -= 2
        cosecha -= 2.5
        evento(2, "malo", f"todo el año {casillas[0].lower()}: llegaron más plagas y el suelo se cansó.", 1)

    pide = sum(agua_mm.get(c, 0) * falta[i] for i, c in enumerate(casillas))
    pide_arroz = sum(agua_mm["Arroz"] * f for f in falta)
    agua = 10.0 if pide_arroz <= 0 else 10 * (1 - pide / pide_arroz)

    if not eventos:
        evento(0, "info", "llovió como siempre y sembraste tranquilo.", 3)
    return {"agua": _limitar(agua), "suelo": _limitar(suelo), "cosecha": _limitar(cosecha)}, eventos


def frase_resultado(barras: dict) -> str:
    nombres = {"agua": "el agua", "suelo": "el suelo", "cosecha": "la cosecha"}
    buenos = [nombres[k] for k, v in barras.items() if v >= 7]
    bajos = [nombres[k] for k, v in barras.items() if v < 4]
    if len(buenos) == 3:
        return "¡Año redondo! Cuidaste el agua, el suelo y tu cosecha."
    if buenos and bajos:
        return f"Te fue bien con {buenos[0]}, pero te faltó cuidar {bajos[0]}."
    if bajos:
        return f"Año difícil: te faltó cuidar {' y '.join(bajos)}. Prueba otra combinación."
    if buenos:
        return f"Buen año para {' y '.join(buenos)}. Lo demás se puede mejorar."
    return "Año regular. Prueba otra combinación para mejorar."


def jugar(casillas: list[str], zona_tipo: str, escenario: str, *, clim: pd.DataFrame,
          cult: pd.DataFrame | None = None, factor: float = 1.0, notas: dict | None = None) -> dict:
    """
    Juega el año. Si 'notas' viene (la combinacion es A, B o C y hay fila en
    estrategias.csv) las barras salen de las notas reales; si no, se simulan.
    Los eventos siempre salen de las reglas.
    """
    if len(casillas) != 3 or any(c not in CARTAS for c in casillas):
        raise ValueError("Hacen falta 3 cartas validas")
    barras, eventos = simular(casillas, zona_tipo, escenario, clim=clim, cult=cult, factor=factor)
    if notas is not None:
        barras = {k: _limitar(v) for k, v in barras_desde_notas(notas).items()}
    elegidos = sorted(eventos, key=lambda e: e["prioridad"])[:3]
    elegidos.sort(key=lambda e: e["temporada"])
    promedio = sum(barras.values()) / 3
    return {
        "barras": barras,
        "palabras": {k: palabra(v) for k, v in barras.items()},
        "eventos": elegidos,
        "logro": "Cuidador del suelo" if barras["suelo"] > SUELO_INICIAL else None,
        "animo": "feliz" if promedio >= 7 else ("normal" if promedio >= 4 else "cansada"),
        "frase": frase_resultado(barras),
        "con_notas": notas is not None,
    }


# --- Mi finca: frase y semaforos ------------------------------------------------------

def _rango(meses: list[int]) -> str:
    if not meses:
        return ""
    if len(meses) == 1:
        return MESES_LARGOS[meses[0]]
    return f"{MESES_LARGOS[meses[0]]} a {MESES_LARGOS[meses[-1]]}"


def meses_por_tipo(clim: pd.DataFrame) -> dict:
    tipos = clim.sort_values("mes")["tipo_mes"].tolist()
    return {
        "lluvioso": [i for i, t in enumerate(tipos) if t == "lluvioso"],
        "agua": [i for i, t in enumerate(tipos) if t != "seco"],
        "seco": [i for i, t in enumerate(tipos) if t == "seco"],
    }


def frase_finca(zona_tipo: str, escenario: str, clim: pd.DataFrame) -> str:
    m = meses_por_tipo(clim)
    if zona_tipo == "baja":
        frase = f"Tu terreno se encharca de {_rango(m['lluvioso'] or m['agua'])}."
    elif zona_tipo == "loma":
        frase = f"Tu terreno es alto y no se inunda, pero le falta agua de {_rango(m['seco'])}."
    elif zona_tipo == "ladera":
        frase = (f"Tu terreno tiene pendiente: de {_rango(m['lluvioso'] or m['agua'])} las lluvias "
                 "fuertes pueden arrastrar el suelo.")
    else:
        frase = f"Tu terreno recibe agua de {_rango(m['agua'])} y se seca de {_rango(m['seco'])}."
    extra = {"nino": " Este año puede llover más de lo normal.",
             "nina": " Este año puede llover menos de lo normal."}
    return frase + extra.get(escenario, "")


def lluvias_texto(clim: pd.DataFrame) -> str:
    return _rango(meses_por_tipo(clim)["agua"])


def meses_12(clim: pd.DataFrame) -> list[dict]:
    icono = {"lluvioso": "🌧️", "transicion": "🌦️", "seco": "☀️"}
    return [{"mes": MESES[i], "tipo": t, "icono": icono.get(t, "☀️")}
            for i, t in enumerate(clim.sort_values("mes")["tipo_mes"].tolist())]


def semaforo_agua(clim: pd.DataFrame, factor: float = 1.0) -> dict:
    lluvia = float(clim["lluvia_mm"].sum()) * factor
    evapora = float(clim["et0_mm"].sum()) or 1.0
    r = lluvia / evapora
    if r >= 0.7:
        return {"color": "verde", "palabra": "Bien", "texto": "Llueve lo suficiente casi todo el año."}
    if r >= 0.45:
        return {"color": "amarillo", "palabra": "Regular", "texto": "Alcanza en lluvias. En la seca hay que regar."}
    return {"color": "rojo", "palabra": "Bajo", "texto": "Va a faltar agua. Guárdala y riega con cuidado."}


def semaforo_suelo(serie: pd.DataFrame) -> dict:
    """Usa el verdor del satelite: comparado con el mismo mes de otros años."""
    s = serie.dropna(subset=["ndvi"]).sort_values("fecha") if not serie.empty else serie
    if s.empty:
        return {"color": "gris", "palabra": "Sin dato", "texto": "Las nubes taparon el campo. Mira otra vez el próximo mes."}
    ult = s.iloc[-1]
    mes = pd.to_datetime(ult["fecha"]).month
    tipico = s[pd.to_datetime(s["fecha"]).dt.month == mes]["ndvi"].mean()
    if ult["ndvi"] < tipico - 0.08:
        return {"color": "amarillo", "palabra": "Regular", "texto": "El campo se ve menos verde que otros años. Revisa agua y plagas."}
    if ult["ndvi"] < 0.2:
        return {"color": "rojo", "palabra": "Bajo", "texto": "Casi no hay plantas verdes. El suelo está pelado."}
    return {"color": "verde", "palabra": "Bien", "texto": "Las plantas se ven sanas, como en otros años."}


def semaforo_inundacion(zona_tipo: str, escenario: str, serie: pd.DataFrame) -> dict:
    # la ladera escurre el agua (su riesgo es la erosion), pero esta casi tan baja como la zona baja
    puntos = {"loma": 0, "ladera": 1, "transicion": 1, "baja": 2}.get(zona_tipo, 1)
    puntos += {"nina": -1, "normal": 0, "nino": 1}.get(escenario, 0)
    s = serie.dropna(subset=["ndwi"]).sort_values("fecha") if not serie.empty else serie
    if not s.empty and float(s.iloc[-1]["ndwi"]) > 0:
        puntos += 1
    if puntos >= 3:
        return {"color": "rojo", "palabra": "Alto", "texto": "Tu terreno se puede inundar. En lluvias siembra solo arroz."}
    if puntos == 2:
        return {"color": "amarillo", "palabra": "Medio", "texto": "Puede encharcarse si llueve fuerte varios días."}
    return {"color": "verde", "palabra": "Bajo", "texto": "Es difícil que tu terreno se inunde."}


# --- Mi plan -----------------------------------------------------------------------------

ACCIONES = {
    "Arroz": ["Prepara el terreno y siembra el arroz.", "Mantén el agua en el arrozal.",
              "Revisa si hay plagas en las hojas.", "Cosecha el arroz y deja la paja en el suelo."],
    "Maíz": ["Siembra el maíz en surcos.", "Quita la maleza alrededor de las plantas.",
             "Riega si pasa una semana sin lluvia.", "Cosecha el maíz cuando la mazorca esté seca."],
    "Soya": ["Siembra la soya con la humedad que quedó.", "Riega poco: la soya no quiere charcos.",
             "Revisa las hojas por gusanos.", "Cosecha la soya y deja los restos: abonan el suelo."],
    "Descanso": ["Limpia el terreno y deja los restos encima.", "La tierra descansa.",
                 "La tierra descansa.", "Prepara la semilla para la próxima siembra."],
}
ETAPAS = ["Siembra", "Crece", "Crece", "Cosecha"]


def plan_12_meses(secuencia: list[str]) -> list[dict]:
    """Una accion corta por mes a partir de las 3 cartas de la temporada."""
    # TODO: reemplazar con datos reales (calendario de siembra por zona, P4)
    filas = []
    for t, c in zip(TEMPORADAS, secuencia):
        for k, i in enumerate(t["idx"]):
            filas.append({"mes": MESES[i], "mes_largo": MESES_LARGOS[i], "temporada": t["nombre"],
                          "cultivo": c, "icono": CARTAS[c]["icono"],
                          "etapa": "Descanso" if c == "Descanso" else ETAPAS[k],
                          "accion": ACCIONES[c][k]})
    return filas


def consejos(zona_tipo: str, escenario: str, secuencia: list[str]) -> list[str]:
    # TODO: reemplazar con datos reales (reglas de campo de P4)
    por_zona = {
        "baja": "En lluvias siembra solo arroz en la parte baja: es el que aguanta el agua.",
        "loma": "En la loma no guardes el arroz para la seca: pide mucha agua.",
        "ladera": "En la ladera siembra siguiendo las curvas de nivel y deja rastrojo encima "
                  "para que la lluvia no se lleve el suelo.",
        "transicion": "Haz zanjas para sacar el agua cuando llueva fuerte varios días.",
    }
    por_anio = {
        "nino": "Año de El Niño: limpia canales y zanjas antes de enero.",
        "nina": "Año de La Niña: llueve poco, prefiere cultivos que piden poca agua como la soya.",
        "normal": "Compra semilla buena antes de cada siembra y guarda el recibo.",
    }
    if "Soya" in secuencia:
        tercero = "Después de la soya el suelo queda con más fuerza: puedes usar menos abono."
    elif len(set(secuencia)) == 1:
        tercero = "Cambia de cultivo alguna temporada: repetir lo mismo trae más plagas."
    else:
        tercero = "Deja los restos de la cosecha sobre el suelo: lo protegen del sol."
    return [por_zona.get(zona_tipo, por_zona["transicion"]), por_anio.get(escenario, por_anio["normal"]), tercero]


# --- Asistente (simulado) ------------------------------------------------------------------

PREGUNTAS = {
    "siembro": "¿Qué siembro?",
    "lluvia": "¿Cómo viene la lluvia?",
    "nino": "Alerta El Niño",
    "plan": "Mi plan",
}
ALERTA_EJEMPLO = "⚠️ Se viene una semana muy lluviosa. No siembres en zona baja hasta el lunes."
NOMBRE_ANIO = {"normal": "año normal", "nino": "año de El Niño", "nina": "año de La Niña"}


def respuesta(clave: str, ctx: dict) -> str:
    """
    Texto corto del asistente. ctx necesita: zona (texto), zona_tipo, escenario,
    plan_nombre, secuencia (3 cartas), lluvias (texto), agua (semaforo), mes (texto), accion.
    """
    anio = NOMBRE_ANIO.get(ctx["escenario"], "año normal")
    if clave == "siembro":
        seq = " → ".join(ctx["secuencia"])
        return f"Para tu {ctx['zona'].lower()} en un {anio} te conviene: {seq}. Es el plan «{ctx['plan_nombre']}»."
    if clave == "lluvia":
        extra = {"nino": " Este año puede llover más de lo normal.",
                 "nina": " Este año puede llover menos de lo normal."}.get(ctx["escenario"], "")
        return f"Llueve sobre todo de {ctx['lluvias']}.{extra} Agua para tu finca: {ctx['agua']['palabra']}."
    if clave == "nino":
        if ctx["zona_tipo"] == "baja":
            consejo = "Tu zona se puede inundar: en lluvias siembra solo arroz y limpia los canales."
        else:
            consejo = "Tu zona no suele inundarse, pero limpia las zanjas antes de enero."
        aviso = "Elegiste año de El Niño." if ctx["escenario"] == "nino" else "Si llega El Niño, lloverá mucho de enero a abril."
        return f"{aviso} {consejo}"
    if clave == "plan":
        return f"En {ctx['mes']}: {ctx['accion']} Mira el plan completo en «Mi plan»."
    return "No entendí. Toca uno de los botones de abajo."
