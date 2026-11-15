"""Estilo visual y piezas que se repiten en varias paginas."""
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

COLOR_ZONA = {1: "#B9863A", 2: "#7FA650", 3: RIO}
COLOR_TIPO = {"lluvioso": RIO, "transicion": "#8FB8D8", "seco": SECA}
COLOR_ESC = {"normal": "#7A869A", "nino": RIO, "nina": SECA}
NOMBRE_ESC = {"normal": "Año normal", "nino": "Año El Niño", "nina": "Año La Niña"}
ICONO_ESC = {"normal": "🌤️", "nino": "🌧️", "nina": "☀️"}
NOMBRE_TIPO = {"lluvioso": "Lluvias", "transicion": "Transición", "seco": "Seca"}
CORTO_TIPO = {"lluvioso": "Lluvias", "transicion": "Cambio", "seco": "Seca"}
ICONO_CULTIVO = {"Arroz": "🌾", "Soya": "🫘", "Maíz duro": "🌽"}
ETAPA = {"siembra": "Siembra", "crece": "Crece", "cosecha": "Cosecha", "riesgo": "Riesgo"}

GLOSARIO = {
    "NDVI": "Qué tan verde y sano está el campo. Cerca de 0: suelo pelado. Cerca de 0,8: cultivo muy verde.",
    "NDWI": "Si hay agua sobre el terreno. Mayor que 0: terreno con agua o inundado.",
    "NDMI": "Humedad dentro de las plantas. Bajo: la planta puede estar pasando sed.",
    "ET0": "El agua que se evapora del suelo y las plantas en un mes. Si llueve menos que esto, falta agua.",
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap');
html, body, [class*="st-"]:not([data-testid="stIconMaterial"]), .stMarkdown, button, input, textarea, select {{
  font-family: 'Atkinson Hyperlegible', system-ui, sans-serif !important;
}}
h1, h2, h3 {{ color: {VERDE_ARROZAL}; letter-spacing: -0.01em; }}
h1 {{ font-size: 2.1rem !important; line-height: 1.15 !important; }}
.block-container {{ padding-top: 4.2rem; max-width: 1100px; }}
p, li {{ font-size: 1.05rem; line-height: 1.55; }}

/* Cabecera */
.marca {{ display: flex; flex-wrap: wrap; align-items: baseline; column-gap: .6rem; margin-bottom: .2rem; }}
.marca b {{ font-size: 1.5rem; color: {VERDE_ARROZAL}; }}
.marca span {{ color: #5B6B5E; font-size: .95rem; }}

/* Franja del anio */
.franja-scroll {{ overflow-x: auto; padding-bottom: .4rem; }}
.franja {{ display: grid; grid-template-columns: 7.2rem repeat(12, minmax(3.1rem, 1fr));
           gap: 4px; min-width: 760px; }}
.franja .etq {{ display: flex; align-items: center; font-weight: 700; color: {VERDE_ARROZAL};
               font-size: .95rem; }}
.franja .mes {{ text-align: center; border-radius: 6px; padding: .35rem 0 .3rem;
               font-weight: 700; font-size: .9rem; position: relative; }}
.franja .mes small {{ display: block; font-weight: 400; font-size: .72rem; white-space: nowrap; }}
.mes.lluvioso {{ background: #DCEAF5; color: #1D4F75; }}
.mes.transicion {{ background: #EBF2F7; color: #3B5E78; }}
.mes.seco {{ background: #F6ECCB; color: #6E5200; }}
.franja .hoy {{ outline: 3px solid {VERDE_ARROZAL}; outline-offset: 1px; }}
.franja .hoy::after {{ content: "hoy"; position: absolute; top: -1.15rem; left: 50%;
                      transform: translateX(-50%); font-size: .72rem; color: {VERDE_ARROZAL};
                      font-weight: 700; }}
.franja .celda {{ min-height: 3.3rem; border-radius: 8px; display: flex; flex-direction: column;
                 align-items: center; justify-content: center; font-size: .72rem;
                 line-height: 1.1; text-align: center; }}
.celda .ico {{ font-size: 1.35rem; }}
.celda.siembra {{ background: {HOJA}; color: #fff; }}
.celda.crece {{ background: #CFE3C4; color: {VERDE_ARROZAL}; }}
.celda.cosecha {{ background: #F1D78A; color: #5A4300; }}
.celda.riesgo {{ background: #F6D3CE; color: #7E1F14; }}
.celda.vacio {{ border: 1px dashed #C9D3C6; color: #8A978C; }}
.leyenda {{ display: flex; flex-wrap: wrap; gap: .9rem; font-size: .85rem; color: #4A5A4D;
           margin-top: .4rem; }}
.leyenda i {{ display: inline-block; width: .9rem; height: .9rem; border-radius: 3px;
             vertical-align: -2px; margin-right: .3rem; }}

/* Senales */
.senal {{ border-left: 6px solid #9AA5A0; background: #FAFBF9; border-radius: 4px 10px 10px 4px;
         padding: .8rem 1rem; height: 100%; }}
.senal .tit {{ font-weight: 700; font-size: 1.12rem; color: {VERDE_ARROZAL}; margin: .1rem 0 .25rem; }}
.senal .que {{ font-size: .85rem; color: #5B6B5E; }}
.senal p {{ font-size: .98rem; margin: 0; }}
.senal.bien {{ border-color: {HOJA}; }}
.senal.atento {{ border-color: {SECA}; }}
.senal.alerta {{ border-color: {RIESGO}; background: #FDF4F2; }}

/* Accion del mes */
.accion {{ background: {VERDE_ARROZAL}; color: #F3F8EF; border-radius: 12px;
          padding: 1rem 1.2rem; margin: .6rem 0 1rem; }}
.accion .que {{ font-size: .9rem; opacity: .85; }}
.accion .txt {{ font-size: 1.35rem; font-weight: 700; line-height: 1.3; margin-top: .2rem; }}

/* Opciones (estrategias) */
.opcion-top {{ font-weight: 700; color: {HOJA}; font-size: .95rem; }}
.estrellas {{ color: {SECA}; font-size: 1.35rem; letter-spacing: .08em; }}
.gotas {{ font-size: 1.1rem; letter-spacing: .05em; }}

@media (max-width: 640px) {{
  h1 {{ font-size: 1.6rem !important; }}
  .marca b {{ font-size: 1.25rem; }}
  .marca span {{ font-size: .82rem; }}
  .franja {{ grid-template-columns: 4.6rem repeat(12, minmax(3rem, 1fr)); min-width: 680px; }}
  .accion .txt {{ font-size: 1.15rem; }}
}}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>
"""


def estilos():
    st.markdown(CSS, unsafe_allow_html=True)


# --- Estado compartido --------------------------------------------------------------

def zona_actual() -> tuple[int, str]:
    zid = st.session_state.get("zona_id") or 3
    tabla = carga.tabla_zonas().set_index("zona_id")
    if zid not in tabla.index:
        zid = int(tabla.index[-1])
    return zid, tabla.loc[zid, "nombre_comun"]


def escenario_actual() -> str:
    return st.session_state.get("escenario") or "normal"


def pesos_actuales() -> dict:
    elegidas = st.session_state.get("prio_guardadas", [])
    if not elegidas:
        return {c: 3 for c in logica.CRITERIOS}
    return {c: (5 if c in elegidas else 1) for c in logica.CRITERIOS}


def corto_zona(nombre: str) -> str:
    n = nombre.lower()
    return "Loma" if "loma" in n else ("Zona baja" if "baja" in n or "encharca" in n else "Transición")


def icono_zona(nombre: str) -> str:
    n = nombre.lower()
    return "⛰️" if "loma" in n else ("🌊" if "baja" in n or "encharca" in n else "🌿")


# --- Avisos ---------------------------------------------------------------------------

def aviso_datos():
    mock = carga.archivos_mock()
    if mock:
        with st.expander(f"🧪 Datos de prueba: {len(mock)} de {len(carga.CONTRATOS)} archivos "
                         "todavía son simulados. Toca para ver cuáles."):
            st.dataframe(carga.estado_datos(), hide_index=True, width="stretch")
            st.caption("Si un archivo real aparece como rechazado, le faltan columnas del "
                       "contrato. Mientras tanto, la app usa el de prueba.")


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
