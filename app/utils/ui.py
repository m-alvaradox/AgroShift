"""Estado compartido y piezas HTML que se repiten en varias paginas (el CSS esta en estilo.py)."""
from html import escape

import streamlit as st

from utils import carga, logica

# --- Paleta del campo ----------------------------------------------------------------
VERDE_ARROZAL = "#1F4D2B"   # titulos y textos fuertes
HOJA = "#4E8B3A"            # acciones y estado "bien"
RIO = "#2F6F9F"             # lluvia y agua
SECA = "#C9A227"            # epoca seca y estado "atento"
RIESGO = "#C0392B"          # solo para riesgos
NEUTRO = "#EEF3EA"          # fondos suaves

# Color de cada zona segun su tipo (se reconoce por el nombre, no por el numero)
COLOR_ZONA = {"loma": "#B9863A", "ladera": "#7FA650", "baja": RIO, "transicion": "#8FB8D8"}
COLOR_TIPO = {"lluvioso": RIO, "transicion": "#8FB8D8", "seco": SECA}
COLOR_ESC = {"normal": "#7A869A", "nino": RIO, "nina": SECA}
# Escenarios: las claves nino/nina son las del contrato de datos, pero en la app se
# muestran por la lluvia real de cada temporada (GPM IMERG), no por el indice ENSO.
NOMBRE_ESC = {"normal": "Año normal", "nino": "Año muy lluvioso", "nina": "Año seco"}
ICONO_ESC = {"normal": "🌤️", "nino": "🌧️", "nina": "☀️"}
NOMBRE_TIPO = {"lluvioso": "Lluvias", "transicion": "Transición", "seco": "Seca"}
CORTO_TIPO = {"lluvioso": "Lluvias", "transicion": "Cambio", "seco": "Seca"}
ICONO_CULTIVO = {"Arroz": "🌾", "Soya": "🫘", "Maíz duro": "🌽", "Maíz": "🌽", "Descanso": "🍂"}
ETAPA = {"siembra": "Siembra", "crece": "Crece", "cosecha": "Cosecha", "riesgo": "Riesgo"}

GLOSARIO = {
    "NDVI": "Qué tan verde y sano está el campo. Cerca de 0: suelo pelado. Cerca de 0,8: cultivo muy verde.",
    "NDWI": "Si hay agua sobre el terreno. Mayor que 0: terreno con agua o inundado.",
    "NDMI": "Humedad dentro de las plantas. Bajo: la planta puede estar pasando sed.",
    "ET0": "El agua que se evapora del suelo y las plantas en un mes. Si llueve menos que esto, falta agua.",
}

# --- Estado compartido --------------------------------------------------------------

def zona_inicial(tabla) -> int:
    """La zona con la que abre la app: la zona baja (buscada por nombre), si no la primera."""
    for zid, nombre in zip(tabla["zona_id"], tabla["nombre_comun"]):
        if tipo_zona(nombre) == "baja":
            return int(zid)
    return int(tabla["zona_id"].iloc[0])


ZONA_SIN_MAPA = (0, "Todo Daule")  # si todavia no estan las zonas de P3


def zona_actual() -> tuple[int, str]:
    if not carga.disponible("zonas_daule.geojson"):
        return ZONA_SIN_MAPA
    tabla = carga.tabla_zonas()
    nombres = dict(zip(tabla["zona_id"].astype(int), tabla["nombre_comun"]))
    zid = st.session_state.get("zona_id")
    if zid not in nombres:
        zid = zona_inicial(tabla)
    return zid, nombres[zid]


def escenario_actual() -> str:
    return st.session_state.get("escenario") or "normal"


def pesos_actuales() -> dict:
    elegidas = st.session_state.get("prio_guardadas", [])
    if not elegidas:
        return {c: 3 for c in logica.CRITERIOS}
    return {c: (5 if c in elegidas else 1) for c in logica.CRITERIOS}


# --- Respuestas del Asistente: se guardan una vez y las usan todas las paginas ---------------
# Claves de st.session_state que NO son de widgets (Streamlit no las borra al cambiar de pagina):
#   zona_confirmada  True cuando el productor dijo o ubico su finca (GPS, mapa o a mano)
#   ubicacion        {"fuente": "gps"|"mapa"|"mano", "zona_id", "lat", "lon", ...}
#   objetivo         clave de logica.CRITERIOS (nota_agua, nota_suelo, nota_plagas, nota_ingresos)
#   mes_inicio       0-11, mes desde el que empieza el plan
#   zona_pendiente   zona por aplicar antes de dibujar el selector de la cabecera
OBJETIVOS = logica.CRITERIOS
ICONO_OBJETIVO = {"nota_agua": "💧", "nota_suelo": "🪱", "nota_plagas": "🐛", "nota_ingresos": "💵"}
FUENTE_UBICACION = {"gps": "con el GPS de tu teléfono", "mapa": "tocando el mapa", "mano": "elegida por ti"}


def fijar_zona(zid: int, **ubicacion):
    """Guarda la zona del productor. Se aplica al inicio de la siguiente corrida (streamlit_app.py)."""
    st.session_state["zona_pendiente"] = int(zid)
    st.session_state["zona_confirmada"] = True
    st.session_state["ubicacion"] = {"fuente": "mano", **ubicacion, "zona_id": int(zid)}


def olvidar_zona():
    for k in ("zona_confirmada", "ubicacion"):
        st.session_state.pop(k, None)


def objetivo() -> str | None:
    k = st.session_state.get("objetivo")
    return k if k in OBJETIVOS else None


def guardar_objetivo(k: str):
    st.session_state["objetivo"] = k
    st.session_state["prio_guardadas"] = [k]  # el orden de los planes usa lo que quiere lograr


def mes_inicio() -> int | None:
    m = st.session_state.get("mes_inicio")
    return m if isinstance(m, int) and 0 <= m <= 11 else None


def guardar_mes(m: int):
    st.session_state["mes_inicio"] = int(m)


def anio_de_inicio(mes0: int) -> int:
    """Año del mes de inicio: si el mes ya paso este año, es el del año que viene."""
    from datetime import date
    hoy = date.today()
    return hoy.year + (1 if mes0 < hoy.month - 1 else 0)


def mejores_por_objetivo(zid: int, esc: str) -> dict:
    """{criterio: [letras]} con la(s) estrategia(s) de mejor nota en estrategias.csv para la zona y el año."""
    est = carga.estrategias()
    f = est[(est["zona_id"] == zid) & (est["escenario"] == esc)]
    if f.empty:
        return {}
    return {c: sorted(f.loc[f[c] == f[c].max(), "estrategia"]) for c in OBJETIVOS}


def recomendada_para(zid: int, esc: str, criterio: str | None) -> str | None:
    """La mejor estrategia para lo que quiere lograr; si empatan, la de mejor nota general."""
    est = carga.estrategias()
    f = est[(est["zona_id"] == zid) & (est["escenario"] == esc)].copy()
    if f.empty:
        return None
    f["general"] = f[list(OBJETIVOS)].mean(axis=1)
    orden = [criterio, "general"] if criterio in OBJETIVOS else ["general"]
    return str(f.sort_values(orden, ascending=False)["estrategia"].iloc[0])


def tipo_zona(nombre: str) -> str:
    """
    'loma', 'ladera', 'baja' o 'transicion' segun el nombre_comun de la zona
    (lo que usa utils/juego.py). Asi la app no depende del numero de zona.
    """
    n = str(nombre).lower()
    if "loma" in n:
        return "loma"
    if "ladera" in n or "erosi" in n:
        return "ladera"
    if "baja" in n or "encharca" in n:
        return "baja"
    return "transicion"


CORTO_ZONA = {"loma": "Loma", "ladera": "Ladera", "baja": "Zona baja", "transicion": "Transición"}
ICONO_ZONA = {"loma": "⛰️", "ladera": "🏞️", "baja": "🌊", "transicion": "🌿"}
ETIQUETA_ZONA = {"baja": "Zona baja (se encharca)", "ladera": "Ladera (riesgo de erosión)"}


def corto_zona(nombre: str) -> str:
    return CORTO_ZONA[tipo_zona(nombre)]


def icono_zona(nombre: str) -> str:
    return ICONO_ZONA[tipo_zona(nombre)]


def color_zona(nombre: str) -> str:
    return COLOR_ZONA[tipo_zona(nombre)]


def etiqueta_zona(nombre: str) -> str:
    t = tipo_zona(nombre)
    return f"{ICONO_ZONA[t]} {ETIQUETA_ZONA.get(t, CORTO_ZONA[t])}"


ETIQUETA_ESC = {"normal": "🌤️ Normal", "nino": "🌧️ Muy lluvioso", "nina": "☀️ Seco"}


def serie_vacia():
    """Serie del satelite sin filas (con tipos correctos) para cuando falta series_zonas.csv."""
    import pandas as pd
    return pd.DataFrame({"fecha": pd.Series(dtype="datetime64[ns]"), "zona_id": pd.Series(dtype=int),
                         **{k: pd.Series(dtype=float) for k in ("ndvi", "ndwi", "ndmi")}})


def serie_zona(zid: int):
    """Serie del satelite para la zona; si aun no hay por zona, la de todo Daule (zona 0)."""
    serie = carga.series()
    sz = serie[serie["zona_id"] == zid]
    return sz if not sz.empty else serie[serie["zona_id"] == 0]


def ranking(zid: int, esc: str):
    """Estrategias ordenadas de mejor a peor con las prioridades del usuario."""
    return logica.comparar(carga.estrategias(), zid, esc, pesos_actuales())


def html(texto: str):
    st.markdown(texto, unsafe_allow_html=True)

# --- Avisos ---------------------------------------------------------------------------

def falta(*nombres: str) -> bool:
    """
    True (y muestra un aviso en esa seccion) si falta alguno de los archivos.
    Uso:  if not ui.falta("estrategias.csv"): ...dibujar la seccion...
    """
    ausentes = [n for n in nombres if not carga.disponible(n)]
    for n in ausentes:
        st.warning(str(carga.FaltaArchivo(n)), icon="📭")
    return bool(ausentes)


def tipos_de_anio() -> dict:
    """{'nino': ['2024-2025'], 'normal': [...], 'nina': [...]} segun la lluvia IMERG."""
    if not carga.disponible("lluvia_imerg_daule.csv"):
        return {}
    s = carga.lluvia_imerg()
    if "temporada" not in s:
        return {}
    s = s[s["enso"].isin(["nino", "neutro", "nina"])].drop_duplicates("temporada")
    clave = {"nino": "nino", "neutro": "normal", "nina": "nina"}
    return {clave[e]: sorted(s.loc[s["enso"] == e, "temporada"]) for e in ["nino", "neutro", "nina"]}


def origen_datos(abierto: bool = False):
    """Vista tecnica: de que archivo y de que fuente sale cada dato."""
    faltan = carga.faltan()
    total = len(carga.CONTRATOS)
    titulo = (f"📂 De dónde sale cada dato ({total - len(faltan)} de {total} archivos reales"
              + (f"; faltan {len(faltan)})" if faltan else ")"))
    with st.expander(titulo, expanded=abierto):
        st.dataframe(carga.estado_datos(), hide_index=True, width="stretch",
                     column_config={"fuente": st.column_config.TextColumn(width="large")})
        tipos = tipos_de_anio()
        if tipos:
            st.markdown(
                "**Tipos de año.** Salen de la lluvia **GPM IMERG de la NASA** (serie de Mario, "
                "2021–2026): se suma la lluvia de diciembre a mayo de cada temporada. La más "
                "lluviosa es el *año muy lluvioso*, la más seca el *año seco* y las demás, el "
                "*año normal*.\n\n"
                + "\n".join(f"- {ICONO_ESC[k]} **{NOMBRE_ESC[k]}:** {', '.join(v)}"
                            for k, v in tipos.items()))
        st.caption("Si una copia aparece como rechazada, le faltan columnas del contrato y la app "
                   "busca en la siguiente carpeta (app/data → data/processed → data).")


class FinDePagina(Exception):
    """La pagina termino antes (como st.stop), pero el pie con el aviso tecnico se sigue dibujando."""


def terminar_pagina():
    """Usar en lugar de st.stop(): streamlit_app.py atrapa la excepcion y dibuja el pie."""
    raise FinDePagina


def aviso_tecnico():
    """Se muestra al pie de TODAS las paginas (streamlit_app.py)."""
    html('<div class="aviso-tecnico">👩‍🌾 Agroshift te ayuda a decidir, pero no reemplaza tu experiencia '
         'ni la de un técnico agrícola. Confirma antes de sembrar.</div>')


# --- Nivel de confianza -------------------------------------------------------------------
# Segun la resolucion del dato y los años disponibles. (nivel, por que)
CONFIANZA = {
    "lluvia": ("media", "satélite de lluvia con cuadros de ~10 km y solo 5 años de datos"),
    "agua": ("media", "clima de la NASA con cuadros de ~50 km y 5 años de datos"),
    "verdor": ("alta", "fotos del satélite Landsat de 30 m cada mes; algunos meses sin foto por nubes"),
    "agua_terreno": ("media", "fotos de 30 m, pero en la época de lluvias las nubes tapan varios meses"),
    "inundacion": ("media", "junta el relieve de tu zona (30 m) con el agua que vio el satélite"),
    "recomendacion": ("media", "agua calculada con datos reales de la NASA; algunos valores del arroz "
                               "y del suelo aún deben validarlos técnicos"),
    "anio_tipo": ("baja", "cada tipo de año sale de una sola temporada real: hay solo 5 años de datos"),
    "juego": ("baja", "combinación libre: es una estimación del juego, no un cálculo con tus datos"),
    "zonas": ("media", "relieve del satélite SRTM de 30 m; el suelo de cada finca aún no se ha medido"),
    "calendario": ("media", "meses de lluvia de 5 años y ciclos de referencia de cada cultivo"),
    "plan": ("baja", "calendario general por temporada; todavía no es un calendario de tu zona"),
}
ICONO_CONF = {"alta": "🟢", "media": "🟡", "baja": "🔴"}


def nivel(clave: str, escenario: str | None = None) -> tuple[str, str]:
    """Nivel y razon; en un año muy lluvioso o seco la recomendacion baja a 'baja'."""
    if clave == "recomendacion" and escenario in ("nino", "nina"):
        return CONFIANZA["anio_tipo"]
    return CONFIANZA[clave]


def confianza(clave: str, escenario: str | None = None) -> str:
    """Etiqueta HTML: '🟡 Confianza media · por que'."""
    n, por_que = nivel(clave, escenario)
    return (f'<div class="conf {n}">{ICONO_CONF[n]} <b>Confianza {n}</b> · {escape(por_que)}</div>')


def fuente(texto: str):
    st.caption(f"Fuente: {texto}")


def num(valor: float, decimales: int = 0) -> str:
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


# --- Componentes ---------------------------------------------------------------------

def franja_anual(clim, filas: list[tuple[str, list]], mes_hoy: int | None = None):
    """
    Franja de 12 meses: arriba la temporada de cada mes y debajo una fila por
    cultivo o por anio, con iconos y etapa (siembra, crece, cosecha, riesgo).
    filas = [(etiqueta, [None | {'cultivo','etapa'} | 'etapa'] * 12), ...]
    """
    tipos = clim.sort_values("mes")["tipo_mes"].tolist()
    html = ['<div class="franja-scroll"><div class="franja">', '<div></div>']
    for i, t in enumerate(tipos):
        hoy = " hoy" if mes_hoy == i else ""
        html.append(f'<div class="mes {t}{hoy}">{logica.MESES[i]}<small>{CORTO_TIPO[t]}</small></div>')
    for etiqueta, meses in filas:
        html.append(f'<div class="etq">{escape(etiqueta)}</div>')
        for m in meses:
            if not m:
                html.append('<div class="celda vacio">descansa</div>')
                continue
            if isinstance(m, str):
                html.append(f'<div class="celda {m}">{ETAPA[m]}</div>')
                continue
            ico = ICONO_CULTIVO.get(m["cultivo"], "🌱")
            html.append(f'<div class="celda {m["etapa"]}"><span class="ico">{ico}</span>'
                        f'{ETAPA[m["etapa"]]}</div>')
    html.append("</div></div>")
    html.append(
        '<div class="leyenda">'
        f'<span><i style="background:#DCEAF5"></i>Temporada de lluvias</span>'
        f'<span><i style="background:#F6ECCB"></i>Temporada seca</span>'
        f'<span><i style="background:{HOJA}"></i>Siembra</span>'
        '<span><i style="background:#CFE3C4"></i>Crece</span>'
        '<span><i style="background:#F1D78A"></i>Cosecha</span>'
        '<span><i style="background:#F6D3CE"></i>Riesgo</span>'
        '</div>')
    st.markdown("".join(html), unsafe_allow_html=True)


ICONO_SENAL = {"lluvia": "🌧️", "verdor": "🌱", "agua": "💧"}
QUE_SENAL = {"lluvia": "Lluvia del último mes", "verdor": "Verdor del campo",
             "agua": "Agua sobre el terreno"}


def tarjeta_senal(tipo: str, s: dict):
    st.markdown(
        f'<div class="senal {s["estado"]}"><div class="que">{ICONO_SENAL[tipo]} {QUE_SENAL[tipo]}</div>'
        f'<div class="tit">{escape(s["titulo"])}</div><p>{escape(s["texto"])}</p></div>',
        unsafe_allow_html=True)


def tarjeta_accion(texto: str, mes: int):
    st.markdown(
        f'<div class="accion"><div class="que">¿Qué hago en {logica.MESES_LARGOS[mes]}?</div>'
        f'<div class="txt">{escape(texto)}</div></div>', unsafe_allow_html=True)


# --- Piezas del diseño tipo juego -----------------------------------------------------

def etiqueta_fuente(real: bool, otra: str = "🧮 Estimación de AgroShift") -> str:
    """Etiqueta pequeña junto a los datos: dato de la NASA o calculo propio de la app."""
    if real:
        return '<span class="tag nasa">🛰️ Dato de satélite NASA</span>'
    return f'<span class="tag sim">{escape(otra)}</span>'


def semaforo(titulo: str, icono: str, s: dict, real: bool, conf: str | None = None) -> str:
    return (f'<div class="semaforo {s["color"]}"><div class="luces"><i class="r"></i><i class="a"></i>'
            f'<i class="v"></i></div><div><div class="sem-tit">{icono} {escape(titulo)}'
            f'<b>{escape(s["palabra"])}</b></div><p>{escape(s["texto"])}</p>{etiqueta_fuente(real)}'
            f'{confianza(conf) if conf else ""}</div></div>')


COLOR_SENAL = {"bien": "verde", "atento": "amarillo", "alerta": "rojo", "sin": "gris"}


def semaforo_de_senal(s: dict) -> dict:
    """Convierte una senal de logica.py ({estado, titulo, texto}) al formato de semaforo()."""
    return {"color": COLOR_SENAL.get(s["estado"], "gris"), "palabra": s["titulo"], "texto": s["texto"]}


def barra(nombre: str, icono: str, valor: float, color: str, palabra: str) -> str:
    n = max(0, min(10, int(round(valor))))
    segs = "".join('<i class="on"></i>' if k < n else "<i></i>" for k in range(10))
    return (f'<div class="barra"><div class="barra-top"><span>{icono} {escape(nombre)}</span>'
            f'<span class="palabra {palabra}">{palabra}</span></div>'
            f'<div class="segs {color}" role="img" aria-label="{escape(nombre)}: {palabra}">{segs}</div></div>')


BARRAS = [("agua", "Ahorro de agua", "💧", "azul"), ("suelo", "Salud del suelo", "🪱", "verde"),
          ("cosecha", "Cosecha", "🧺", "amarillo")]


def tres_barras(valores: dict) -> str:
    from utils.juego import palabra
    return "".join(barra(n, i, valores[k], c, palabra(valores[k])) for k, n, i, c in BARRAS)


def mini_cartas(secuencia: list[str]) -> str:
    from utils.juego import CARTAS
    return "".join(f'<span class="mini {CARTAS[c]["slug"]}">{CARTAS[c]["icono"]} {escape(c)}</span>'
                   for c in secuencia)


def carta_html(nombre: str) -> str:
    from utils.juego import CARTAS
    c = CARTAS[nombre]
    return (f'<div class="carta-ico">{c["icono"]}</div><div class="carta-nombre">{escape(nombre)}</div>'
            f'<div class="carta-frase">{escape(c["frase"])}</div>')


_PLANTA = {
    "feliz": {"hoja": "#43A047", "tallo": "M50 90 C50 72 50 58 50 40", "flor": True,
              "hojas": [(36, 58, -35), (64, 58, 35), (40, 74, -20), (60, 74, 20)],
              "boca": "M42 112 Q50 120 58 112", "texto": "¡Tu planta está feliz!"},
    "normal": {"hoja": "#7CB342", "tallo": "M50 90 C50 75 51 62 52 48", "flor": False,
               "hojas": [(38, 60, -10), (64, 62, 10), (42, 76, -5)],
               "boca": "M43 115 L57 115", "texto": "Tu planta está bien, puede mejorar."},
    "cansada": {"hoja": "#A1887F", "tallo": "M50 90 C50 76 56 66 68 62", "flor": False,
                "hojas": [(40, 74, 40), (70, 70, 60)],
                "boca": "M42 118 Q50 110 58 118", "texto": "Tu planta está cansada."},
}


def planta_svg(animo: str) -> str:
    p = _PLANTA.get(animo, _PLANTA["normal"])
    hojas = "".join(f'<ellipse cx="{x}" cy="{y}" rx="13" ry="6.5" fill="{p["hoja"]}" '
                    f'transform="rotate({r} {x} {y})"/>' for x, y, r in p["hojas"])
    flor = ('<circle cx="50" cy="36" r="8" fill="#F9A825"/><circle cx="50" cy="36" r="3.5" fill="#6D4C41"/>'
            if p["flor"] else "")
    svg = (f'<svg viewBox="0 0 100 135" role="img" aria-label="{p["texto"]}">'
           f'<path d="{p["tallo"]}" stroke="#558B2F" stroke-width="4" fill="none" stroke-linecap="round"/>'
           f'{hojas}{flor}'
           '<rect x="20" y="88" width="60" height="11" rx="4" fill="#6D4C41"/>'
           '<path d="M25 99 H75 L68 130 H32 Z" fill="#8D6E63"/>'
           '<circle cx="42" cy="108" r="3" fill="#3E2723"/><circle cx="58" cy="108" r="3" fill="#3E2723"/>'
           f'<path d="{p["boca"]}" stroke="#3E2723" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
           '</svg>')
    return f'<div class="planta">{svg}<div class="planta-txt">{p["texto"]}</div></div>'

# --- Naipes del juego (estilo casino) ----------------------------------------------------------
# Dibujos simples en SVG de cada cultivo para el centro de la carta (sin imagenes externas).
_DIBUJO = {
    "Arroz": ('<path d="M30 76 C30 56 31 38 38 20" stroke="#5E8C31" stroke-width="2.6" fill="none"/>'
              '<path d="M30 70 C22 58 16 50 8 46" stroke="#7CA843" stroke-width="2.4" fill="none"/>'
              '<path d="M31 62 C38 54 46 50 54 50" stroke="#7CA843" stroke-width="2.4" fill="none"/>'
              + "".join(f'<ellipse cx="{x}" cy="{y}" rx="2.6" ry="5" fill="#E2B53E" transform="rotate({r} {x} {y})"/>'
                        for x, y, r in [(38, 18, 20), (42, 24, 35), (35, 25, -10), (45, 31, 45), (37, 32, 5),
                                        (47, 38, 55), (39, 39, 15), (48, 45, 65)])),
    "Soya": ('<path d="M30 76 C30 60 30 44 30 30" stroke="#5E8C31" stroke-width="2.6" fill="none"/>'
             '<path d="M30 44 C20 40 12 32 12 24 C22 26 28 34 30 44Z" fill="#7CA843"/>'
             '<path d="M30 36 C40 32 48 24 48 16 C38 18 32 26 30 36Z" fill="#8DB255"/>'
             '<path d="M18 60 C14 52 22 44 30 50 C38 56 42 66 34 70 C28 72 22 68 18 60Z" fill="#B5C76A"'
             ' stroke="#6E8B2E" stroke-width="1.5"/>'
             '<circle cx="23" cy="56" r="3.4" fill="#DCE6A0"/><circle cx="29" cy="60" r="3.4" fill="#DCE6A0"/>'
             '<circle cx="34" cy="65" r="3.2" fill="#DCE6A0"/>'),
    "Maíz": ('<path d="M30 78 C18 66 14 46 20 30 C24 46 28 58 30 78Z" fill="#7CA843"/>'
             '<path d="M30 78 C42 66 46 46 40 30 C36 46 32 58 30 78Z" fill="#5E8C31"/>'
             '<ellipse cx="30" cy="38" rx="9" ry="22" fill="#F2C230" stroke="#C99A16" stroke-width="1.4"/>'
             + "".join(f'<circle cx="{x}" cy="{y}" r="1.7" fill="#D9A11A"/>'
                       for y in range(22, 58, 6) for x in (26, 30, 34))
             + '<path d="M30 16 C28 10 32 6 30 2" stroke="#C99A16" stroke-width="1.5" fill="none"/>'),
    "Descanso": ('<path d="M10 70 H50" stroke="#8D6E63" stroke-width="3"/>'
                 '<path d="M20 70 C20 58 28 52 36 50 C34 60 28 66 20 70Z" fill="#C59A6B"/>'
                 '<path d="M34 70 C36 62 42 58 48 58 C46 64 42 68 34 70Z" fill="#A1887F"/>'),
}


def dibujo_cultivo(nombre: str, ancho: int = 60) -> str:
    return (f'<svg viewBox="0 0 60 80" width="{ancho}" role="img" aria-label="{escape(nombre)}">'
            f'{_DIBUJO.get(nombre, _DIBUJO["Descanso"])}</svg>')


def naipe_html(letra: str, nombre: str, secuencia: list[str], elegida: bool = False,
               otra_elegida: bool = False) -> str:
    """Carta con proporcion de naipe: letra en las esquinas, dibujo al centro, borde dorado y reverso."""
    unicos = list(dict.fromkeys(secuencia))  # cultivos sin repetir, en orden
    dibujos = "".join(dibujo_cultivo(c, 54 if len(unicos) > 1 else 78) for c in unicos)
    estado = " elegida" if elegida else (" apagada" if otra_elegida else "")
    return (f'<div class="naipe{estado}"><div class="naipe-in">'
            f'<div class="cara frente"><span class="esq sup">{letra}</span>'
            f'<div class="naipe-dib">{dibujos}</div>'
            f'<div class="naipe-nom">{escape(nombre)}</div>'
            f'<div class="naipe-seq">{escape(" · ".join(secuencia))}</div>'
            f'<span class="esq inf">{letra}</span></div>'
            '<div class="cara reverso"><div class="rev-marco"><span>AgroShift</span></div></div>'
            '</div></div>')


def marcador(barras: dict, palabras: dict) -> str:
    """Tablero de resultados tipo marcador: agua, suelo y cosecha de 0 a 10."""
    celdas = "".join(
        f'<div class="marc-celda"><div class="marc-etq">{etq}</div>'
        f'<div class="marc-num">{num(barras[k], 1)}<small>/10</small></div>'
        f'<div class="marc-pal {palabras[k]}">{palabras[k]}</div></div>'
        for k, etq in (("agua", "Ahorro de agua"), ("suelo", "Salud del suelo"), ("cosecha", "Cosecha")))
    return f'<div class="marcador">{celdas}</div>'
