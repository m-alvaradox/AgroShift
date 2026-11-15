"""Comparar: los 3 planes (A, B, C) ordenados segun lo que le importa al productor."""
import streamlit as st

from utils import carga, juego, logica, ui

zid, znombre = ui.zona_actual()
esc = ui.escenario_actual()

st.title("⚖️ Compara los planes")

ICONO_CRIT = {"nota_agua": "💧", "nota_suelo": "🪱", "nota_plagas": "🐛", "nota_ingresos": "💵"}


def guardar_prioridades():
    # mismo estado que usa la vista tecnica de estrategias
    st.session_state["prio_guardadas"] = st.session_state.get("w_prio") or []


st.pills("Me importa más:", options=list(logica.CRITERIOS), selection_mode="multi", key="w_prio",
         default=st.session_state.get("prio_guardadas", []), on_change=guardar_prioridades,
         format_func=lambda c: f"{ICONO_CRIT[c]} {logica.CRITERIOS[c]}")

if ui.falta("estrategias.csv"):
    st.stop()
comp = ui.ranking(zid, esc)
info = {} if ui.falta("estrategias_info.json") else carga.estrategias_info()
real = True
if comp.empty:
    st.info("Todavía no hay planes para esta zona y este año.", icon="ℹ️")
    st.stop()

st.markdown(f"Para tu **{ui.corto_zona(znombre).lower()}** en un "
            f"**{juego.NOMBRE_ANIO[esc]}**. El primero es el que más te conviene.")

cols = st.columns(len(comp), gap="medium")
for i, (col, (_, fila)) in enumerate(zip(cols, comp.iterrows())):
    k = fila["estrategia"]
    e = info.get(k, {})
    atajo = juego.ATAJOS.get(k, {"nombre": k, "secuencia": []})
    with col, st.container(key=f"tarjplan_{'top' if i == 0 else 'otro'}_{k}"):
        if i == 0:
            ui.html('<span class="cinta">⭐ Recomendada para ti</span>')
        ui.html(f'<div class="plan-nombre">{k} · {atajo["nombre"]}</div>'
                f'<p>{ui.mini_cartas(atajo["secuencia"])}</p>')
        ui.html(ui.tres_barras(juego.barras_desde_notas(fila)))
        if e.get("beneficios"):
            ui.html(f'<p class="pro">👍 {e["beneficios"][0]}</p>')
        if e.get("riesgos"):
            ui.html(f'<p class="contra">⚠️ {e["riesgos"][0]}</p>')
        if st.button("Elegir este plan", key=f"elegir_{k}", type="primary" if i == 0 else "secondary",
                     width="stretch"):
            st.session_state["estrategia_elegida"] = k
            st.switch_page("vistas/plan.py")

ui.html(ui.etiqueta_fuente(real))
