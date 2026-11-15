"""
Agroshift - app principal (Streamlit).

Correr desde la raiz del proyecto:
    streamlit run app/streamlit_app.py

Este archivo arma el menu de paginas y la barra lateral (zona, escenario y
prioridades). Como la barra lateral se dibuja en cada pagina, lo que elige el
usuario se mantiene al cambiar de pagina.
"""
import streamlit as st

from utils import carga
from utils.ui import NOMBRE_ESC

st.set_page_config(page_title="Agroshift", page_icon="🌱", layout="wide")

paginas = [
    st.Page("vistas/inicio.py", title="Inicio", icon="🗺️", default=True),
    st.Page("vistas/clima.py", title="Clima", icon="🌦️"),
    st.Page("vistas/zonas.py", title="Zonas y series", icon="🛰️"),
    st.Page("vistas/estrategias.py", title="Estrategias", icon="🌱"),
    st.Page("vistas/recomendacion.py", title="Recomendación", icon="✅"),
]
pg = st.navigation(paginas)

# --- Barra lateral compartida ----------------------------------------------------
with st.sidebar:
    st.markdown("## 🌱 Agroshift")
    st.caption("Rotación de cultivos con datos de la NASA · Daule, Guayas")

    tabla = carga.tabla_zonas().sort_values("zona_id")
    nombres = dict(zip(tabla["zona_id"], tabla["nombre_comun"]))
    st.selectbox("Tu zona", options=list(nombres), format_func=nombres.get,
                 key="zona_id", index=len(nombres) - 1)
    st.radio("¿Qué tipo de año esperas?", options=list(NOMBRE_ESC),
             format_func=NOMBRE_ESC.get, key="escenario")

    with st.expander("Tus prioridades", expanded=False):
        st.caption("0 = no me importa · 5 = muy importante")
        st.slider("Ahorrar agua", 0, 5, 3, key="p_agua")
        st.slider("Mejorar el suelo", 0, 5, 3, key="p_suelo")
        st.slider("Cortar plagas", 0, 5, 3, key="p_plagas")
        st.slider("Ingresos", 0, 5, 3, key="p_ingresos")

    st.divider()
    st.caption("NASA Space Apps 2026 · Reto Field Shift")

pg.run()
