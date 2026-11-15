"""Mi plan: que hacer cada mes con el plan elegido y 3 consejos practicos."""
from datetime import date

import streamlit as st

from utils import juego, ui

zid, znombre = ui.zona_actual()
tipo = ui.tipo_zona(znombre)
esc = ui.escenario_actual()
hoy = date.today().month - 1

comp = ui.ranking(zid, esc)
recomendada = comp["estrategia"].iloc[0] if not comp.empty else "B"
elegida = st.session_state.get("estrategia_elegida") or recomendada
if elegida not in juego.ATAJOS:
    elegida = recomendada


def elegir(k):
    st.session_state["estrategia_elegida"] = k


atajo = juego.ATAJOS[elegida]
st.title("📅 Mi plan")
ui.html(f'<p><b>{elegida} · {atajo["nombre"]}</b>{" ⭐ recomendado" if elegida == recomendada else ""}'
        f'<br>{ui.mini_cartas(atajo["secuencia"])}</p>')

with st.container(key="cambiar_plan", horizontal=True, gap="small"):
    for k, a in juego.ATAJOS.items():
        st.button(f"{k} · {a['nombre']}", key=f"plan_btn_{k}", on_click=elegir, args=(k,),
                  type="primary" if k == elegida else "secondary", width="stretch")

st.subheader("Mes a mes")
filas = []
for i, m in enumerate(juego.plan_12_meses(atajo["secuencia"])):
    filas.append(f'<div class="plan-mes{" hoy" if i == hoy else ""}"><div class="ico">{m["icono"]}</div>'
                 f'<div class="mes">{m["mes"]}</div><div><div class="etapa">{m["etapa"]} · {m["cultivo"]}'
                 f'{" · este mes" if i == hoy else ""}</div><div class="acc">{m["accion"]}</div></div></div>')
ui.html(f'<div class="plan-lista">{"".join(filas)}</div>{ui.etiqueta_fuente(False)}')

st.subheader("3 consejos para ti")
for c in juego.consejos(tipo, esc, atajo["secuencia"]):
    ui.html(f'<div class="consejo">💡 {c}</div>')

ui.aviso_tecnico()
