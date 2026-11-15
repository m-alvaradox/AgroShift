"""
Mis opciones: arriba, la opcion que mejor cumple cada objetivo (estrategias.csv para la zona y
el tipo de año), resaltando lo que el productor eligio en el Asistente. Debajo, las 3 opciones.
"""
import streamlit as st

from utils import carga, juego, logica, ui

zid, znombre = ui.zona_actual()
esc = ui.escenario_actual()
objetivo = ui.objetivo()

ICONO_CRIT = ui.ICONO_OBJETIVO
TEXTO_OBJ = {"nota_agua": "AHORRAR AGUA", "nota_suelo": "MEJORAR EL SUELO", "nota_plagas": "MENOS PLAGAS",
             "nota_ingresos": "GANAR MÁS"}


def guardar_prioridades():
    # mismo estado que usa la vista tecnica de estrategias
    st.session_state["prio_guardadas"] = st.session_state.get("w_prio") or []


def elegir_objetivo(k):
    ui.guardar_objetivo(k)


ui.html('<div class="opc-tit">TUS OPCIONES SON</div>')
if ui.falta("estrategias.csv"):
    ui.terminar_pagina()
mejores = ui.mejores_por_objetivo(zid, esc)
if not mejores:
    st.info("Todavía no hay opciones calculadas para esta zona y este año.", icon=":material/info:")
    ui.terminar_pagina()

est = carga.estrategias()
filas_zona = est[(est["zona_id"] == zid) & (est["escenario"] == esc)].set_index("estrategia")


def detalle(crit: str, letras: list[str]) -> str:
    f = filas_zona.loc[letras[0]]
    if crit == "nota_agua" and "agua_anual_m3_ha" in f:
        return f"usa {ui.num(f['agua_anual_m3_ha'])} m³ de agua por hectárea al año"
    return f"nota {ui.num(f[crit], 1)} de 10"


lineas = []
for crit, letras in mejores.items():
    nombres = " o ".join(f"<b>{k}</b> · {juego.ATAJOS[k]['nombre']}" for k in letras)
    tuya = crit == objetivo
    lineas.append(
        f'<div class="opc{" tuya" if tuya else ""}"><div class="opc-si">Si quieres <b>{TEXTO_OBJ[crit]}</b></div>'
        f'<div class="opc-flecha" aria-hidden="true">→</div><div class="opc-plan">{nombres}'
        f'<small>{detalle(crit, letras)}</small></div>'
        + ('<span class="opc-tuya">Lo que elegiste</span>' if tuya else "") + "</div>")
ui.html(f'<div class="opc-lista">{"".join(lineas)}</div>'
        f'<p class="opc-pie">Para tu <b>{ui.corto_zona(znombre).lower()}</b> en un '
        f'<b>{juego.NOMBRE_ANIO[esc]}</b>, con el cálculo de agua de la NASA y las reglas de campo.</p>')
if objetivo is None:
    st.markdown("¿Qué quieres lograr? Toca uno y lo recordamos en toda la app:")
    with st.container(key="opc_elegir", horizontal=True, gap="small"):
        for k, n in ui.OBJETIVOS.items():
            st.button(f"{ICONO_CRIT[k]} {n}", key=f"opc_obj_{k}", on_click=elegir_objetivo, args=(k,),
                      width="stretch")

st.subheader("Las 3 opciones en detalle")
st.pills("Ordenar según lo que más me importa:", options=list(logica.CRITERIOS), selection_mode="multi",
         key="w_prio", default=st.session_state.get("prio_guardadas", []), on_change=guardar_prioridades,
         format_func=lambda c: f"{ICONO_CRIT[c]} {logica.CRITERIOS[c]}")
comp = ui.ranking(zid, esc)
info = {} if ui.falta("estrategias_info.json") else carga.estrategias_info()
real = True
st.markdown("La primera es la que más te conviene según lo que más te importa.")
ui.html(ui.confianza("recomendacion", esc))

cols = st.columns(len(comp), gap="medium")
for i, (col, (_, fila)) in enumerate(zip(cols, comp.iterrows())):
    k = fila["estrategia"]
    e = info.get(k, {})
    atajo = juego.ATAJOS.get(k, {"nombre": k, "secuencia": []})
    with col, st.container(key=f"tarjplan_{'top' if i == 0 else 'otro'}_{k}"):
        if i == 0:
            ui.html('<span class="cinta">Recomendada para ti</span>')
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
