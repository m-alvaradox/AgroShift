"""
AgroShift - app principal (Streamlit).

Correr desde la raiz del proyecto:
    streamlit run app/streamlit_app.py

Arma el menu de 6 botones (Mi finca, Dashboard, Jugar, Comparar, Mi plan, Asistente),
la eleccion de zona y tipo de año (se guarda en st.session_state) y la
seccion "Vista tecnica" con las paginas de datos para los jueces.
"""
import streamlit as st

from utils import carga, estilo, ui

st.set_page_config(page_title="AgroShift", page_icon="🌱", layout="wide",
                   initial_sidebar_state="collapsed")
estilo.aplicar()

PRINCIPALES = [
    st.Page("vistas/inicio.py", title="Mi finca", icon="🏡", default=True),
    st.Page("vistas/dashboard.py", title="Dashboard", icon="📊"),
    st.Page("vistas/jugar.py", title="Jugar", icon="🎲"),
    st.Page("vistas/comparar.py", title="Comparar", icon="⚖️"),
    st.Page("vistas/plan.py", title="Mi plan", icon="📅"),
    st.Page("vistas/asistente.py", title="Asistente", icon="💬"),
]
# Vista tecnica: graficos y datos reales (no salen en el menu principal)
TECNICAS = [
    st.Page("vistas/clima.py", title="Clima", icon="🌦️"),
    st.Page("vistas/zonas.py", title="Satélite", icon="🛰️"),
    st.Page("vistas/estrategias.py", title="Estrategias", icon="🌱"),
    st.Page("vistas/recomendacion.py", title="Recomendación", icon="✅"),
]
pg = st.navigation(PRINCIPALES + TECNICAS, position="hidden")
es_tecnica = pg.title in {p.title for p in TECNICAS}
es_dashboard = pg.title == "Dashboard"  # tiene sus propios filtros

# --- Cabecera ------------------------------------------------------------------------------
ui.html('<div class="marca"><b>🌱 AgroShift</b><span>Qué sembrar, cuándo y dónde · Daule</span></div>')

with st.container(key="nav", horizontal=True, wrap=False, gap="small"):
    for p in PRINCIPALES:
        estado = "on" if p.title == pg.title else "off"
        with st.container(key=f"nav_{estado}_{p.url_path or 'inicio'}", width="stretch"):
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

if es_dashboard:
    # El selector no se dibuja aqui: se reasigna el estado para que Streamlit no lo borre
    # y la zona y el tipo de año sigan iguales al volver a las otras paginas.
    for clave in ("zona_id", "escenario"):
        if clave in st.session_state:
            st.session_state[clave] = st.session_state[clave]
else:
    with st.container(key="selector"):
        col_zona, col_anio = st.columns([3, 2])
        if hay_zonas:
            col_zona.segmented_control(
                "¿Dónde está tu terreno?", options=list(nombres), key="zona_id", required=True,
                format_func=lambda z: ui.etiqueta_zona(nombres[z]), width="stretch", wrap=True)
        else:
            with col_zona:
                ui.falta("zonas_daule.geojson")
        col_anio.segmented_control(
            "¿Cómo viene el año?", options=list(ui.ETIQUETA_ESC), key="escenario", required=True,
            format_func=lambda e: ui.ETIQUETA_ESC[e], width="stretch", wrap=True)

if es_tecnica:
    with st.container(key="nav_tecnica", horizontal=True, gap="small", vertical_alignment="center"):
        st.markdown("**🔬 Vista técnica:**", width="content")
        for p in TECNICAS:
            st.page_link(p, label=p.title, icon=p.icon, width="content")
        st.page_link(PRINCIPALES[0], label="Volver a Mi finca", icon="↩️", width="content")

pg.run()

st.divider()
st.caption("NASA Space Apps 2026 · Reto Field Shift · Datos de NASA POWER, Landsat, SRTM y GPM")
