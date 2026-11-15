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


def aviso_tecnico():
    st.caption("Agroshift te ayuda a decidir, pero no reemplaza tu experiencia ni la de un "
               "técnico agrícola. Confirma antes de sembrar.")


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


def semaforo(titulo: str, icono: str, s: dict, real: bool) -> str:
    return (f'<div class="semaforo {s["color"]}"><div class="luces"><i class="r"></i><i class="a"></i>'
            f'<i class="v"></i></div><div><div class="sem-tit">{icono} {escape(titulo)}'
            f'<b>{escape(s["palabra"])}</b></div><p>{escape(s["texto"])}</p>{etiqueta_fuente(real)}</div></div>')


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