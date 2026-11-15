"""
AgroShift - app principal (Streamlit).

Correr desde la raiz del proyecto:
    streamlit run app/streamlit_app.py

Arma la portada (6 tarjetas), el menu (Inicio + Mi finca, Jugar, Mis opciones, Mi plan,
Asistente y Dashboard), la eleccion de zona y tipo de año (se guarda en st.session_state)
y la seccion "Vista tecnica" con las paginas de datos para los jueces.
"""
import streamlit as st

from utils import carga, estilo, ui

st.set_page_config(page_title="AgroShift", page_icon="🌱", layout="wide",
                   initial_sidebar_state="collapsed")
estilo.aplicar()

PORTADA = st.Page("vistas/portada.py", title="Inicio", icon=":material/home:", default=True)
PRINCIPALES = [
    st.Page("vistas/inicio.py", title="Mi finca", icon=":material/agriculture:"),
    st.Page("vistas/jugar.py", title="Jugar", icon=":material/playing_cards:"),
    st.Page("vistas/comparar.py", title="Mis opciones", icon=":material/alt_route:"),
    st.Page("vistas/plan.py", title="Mi plan", icon=":material/calendar_month:"),
    st.Page("vistas/asistente.py", title="Asistente", icon=":material/chat:"),
]
# Vista tecnica: graficos y datos reales (no salen en la portada)
TECNICAS = [
    st.Page("vistas/clima.py", title="Clima", icon=":material/partly_cloudy_day:"),
    st.Page("vistas/zonas.py", title="Mi campo", icon=":material/satellite_alt:"),
    st.Page("vistas/estrategias.py", title="Estrategias", icon=":material/eco:"),
    st.Page("vistas/recomendacion.py", title="Recomendación", icon=":material/task_alt:"),
]
# Dashboard: al final de la navegacion (despues de Recomendacion) y ultimo boton del menu
DASHBOARD = st.Page("vistas/dashboard.py", title="Dashboard", icon=":material/bar_chart:")
MENU = [PORTADA] + PRINCIPALES + [DASHBOARD]
pg = st.navigation([PORTADA] + PRINCIPALES + TECNICAS + [DASHBOARD], position="hidden")
ss = st.session_state
es_portada = pg.title == "Inicio"
es_tecnica = pg.title in {p.title for p in TECNICAS}
es_dashboard = pg.title == "Dashboard"  # tiene sus propios filtros
# Mientras Mi finca o el Asistente preguntan "¿Dónde está tu finca?", la cabecera no muestra el
# selector de zona (seria la misma pregunta dos veces)
es_ubicar = pg.title in ("Mi finca", "Asistente") and not ss.get("zona_confirmada")

# Zona elegida en el Asistente, con el GPS o en el mapa: se aplica ANTES de dibujar el selector
if "zona_pendiente" in ss:
    ss["zona_id"] = ss.pop("zona_pendiente")

# --- Cabecera ------------------------------------------------------------------------------
if not es_portada:  # la portada es el menu principal: no lleva cabecera
    ui.html('<div class="marca"><b>AgroShift</b><span>Qué sembrar, cuándo y dónde · Daule</span></div>')
    with st.container(key="nav", horizontal=True, wrap=False, gap="small"):
        for p in MENU:
            estado = "on" if p.title == pg.title else "off"
            with st.container(key=f"nav_{estado}_{p.url_path or 'portada'}", width="stretch"):
                st.page_link(p, label=p.title, icon=p.icon, width="stretch")

# --- Zona y tipo de año (persisten entre paginas) -------------------------------------------
hay_zonas = carga.disponible("zonas_daule.geojson")
nombres = {}
if hay_zonas:
    tabla = carga.tabla_zonas().sort_values("zona_id")
    nombres = dict(zip(tabla["zona_id"].astype(int), tabla["nombre_comun"]))
    if st.session_state.get("zona_id") not in nombres:
        st.session_state["zona_id"] = ui.zona_inicial(tabla)  # la zona baja, buscada por nombre
if st.session_state.get("escenario") not in ui.ETIQUETA_ESC:
    st.session_state["escenario"] = "normal"



def zona_cambiada():
    """Elegir la zona en la cabecera tambien cuenta como respuesta (no se vuelve a preguntar)."""
    ui.fijar_zona(ss["zona_id"])
    ss.pop("zona_pendiente", None)


def conservar(*claves):
    # El selector no se dibuja: se reasigna el estado para que Streamlit no lo borre
    # y la zona y el tipo de año sigan iguales al volver a las otras paginas.
    for clave in claves:
        if clave in ss:
            ss[clave] = ss[clave]


if es_portada or es_dashboard:
    conservar("zona_id", "escenario")
else:
    with st.container(key="selector"):
        if es_ubicar:
            conservar("zona_id")
            st.segmented_control(
                "¿Cómo viene el año?", options=list(ui.ETIQUETA_ESC), key="escenario", required=True,
                format_func=lambda e: ui.ETIQUETA_ESC[e], width="stretch", wrap=True)
        else:
            col_zona, col_anio = st.columns([3, 2])
            if hay_zonas:
                col_zona.segmented_control(
                    "¿Dónde está tu terreno?", options=list(nombres), key="zona_id", required=True,
                    format_func=lambda z: ui.etiqueta_zona(nombres[z]), width="stretch", wrap=True,
                    on_change=zona_cambiada)
            else:
                with col_zona:
                    ui.falta("zonas_daule.geojson")
            col_anio.segmented_control(
                "¿Cómo viene el año?", options=list(ui.ETIQUETA_ESC), key="escenario", required=True,
                format_func=lambda e: ui.ETIQUETA_ESC[e], width="stretch", wrap=True)

if es_tecnica:
    with st.container(key="nav_tecnica", horizontal=True, gap="small", vertical_alignment="center"):
        st.markdown("**Vista técnica:**", width="content")
        for p in TECNICAS + [DASHBOARD]:
            st.page_link(p, label=p.title, icon=p.icon, width="content")
        st.page_link(PORTADA, label="Volver al inicio", icon=":material/undo:", width="content")

# Las paginas que terminan antes usan ui.terminar_pagina() (no st.stop) para que el pie,
# con el aviso de que la app no reemplaza al tecnico, salga en TODAS las paginas.
try:
    pg.run()
except ui.FinDePagina:
    pass
ui.aviso_tecnico()
st.divider()
st.caption("NASA Space Apps 2026 · Reto Field Shift · Datos de NASA POWER, GPM IMERG, Landsat 8 y 9 y SRTM")
