"""
Agroshift - app principal (Streamlit).

Correr desde la raiz del proyecto:
    streamlit run app/streamlit_app.py

Este archivo arma el menu de arriba y la cabecera con la zona y el tipo de
anio. Como se dibuja en cada pagina, lo que elige el usuario se mantiene.
"""
import streamlit as st

from utils import carga, ui

st.set_page_config(page_title="Agroshift", page_icon="🌱", layout="wide",
                   initial_sidebar_state="collapsed")
ui.estilos()

paginas = [
    st.Page("vistas/inicio.py", title="Mi finca", icon="🏡", default=True),
    st.Page("vistas/clima.py", title="Clima", icon="🌦️"),
    st.Page("vistas/zonas.py", title="Mi campo", icon="🛰️"),
    st.Page("vistas/estrategias.py", title="Opciones", icon="🌱"),
    st.Page("vistas/recomendacion.py", title="Recomendación", icon="✅"),
]
pg = st.navigation(paginas, position="top")

# --- Cabecera con los controles a la vista ---------------------------------------------
st.markdown('<div class="marca"><b>🌱 Agroshift</b>'
            '<span>Qué sembrar, cuándo y dónde · Daule, Guayas</span></div>',
            unsafe_allow_html=True)

tabla = carga.tabla_zonas().sort_values("zona_id")
nombres = dict(zip(tabla["zona_id"], tabla["nombre_comun"]))
if "zona_id" not in st.session_state:
    st.session_state["zona_id"] = int(tabla["zona_id"].iloc[-1])
if "escenario" not in st.session_state:
    st.session_state["escenario"] = "normal"

col_zona, col_anio = st.columns([3, 2])
col_zona.segmented_control(
    "¿Dónde está tu terreno?", options=list(nombres), key="zona_id",
    format_func=lambda z: f"{ui.icono_zona(nombres[z])} {ui.corto_zona(nombres[z])}")
col_anio.segmented_control(
    "¿Cómo viene el año?", options=list(ui.NOMBRE_ESC), key="escenario",
    format_func=lambda e: f"{ui.ICONO_ESC[e]} {ui.NOMBRE_ESC[e].replace('Año ', '').capitalize().replace('El niño', 'El Niño').replace('La niña', 'La Niña')}")

pg.run()

st.divider()
st.caption("NASA Space Apps 2026 · Reto Field Shift · Datos de NASA POWER, Landsat, SRTM y GPM")
