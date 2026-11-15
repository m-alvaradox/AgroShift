"""Recomendacion: la opcion sugerida, por que, que cuidar y reglas para el campo."""
import streamlit as st

from utils import carga, logica, ui

zid, znombre = ui.zona_actual()
esc = ui.escenario_actual()
pesos = ui.pesos_actuales()

st.title("✅ Te recomendamos")
ui.origen_datos()
if ui.falta("estrategias.csv", "estrategias_info.json"):
    ui.terminar_pagina()

est = carga.estrategias()
info = carga.estrategias_info()
comp = logica.comparar(est, zid, esc, pesos)
if comp.empty:
    st.info("Todavía no hay planes para esta zona y este año.", icon="ℹ️")
    ui.terminar_pagina()
mejor = comp.iloc[0]
e = info[mejor["estrategia"]]
st.markdown(f"## {e['nombre']}")
st.markdown(f"Para la **{znombre.lower()}** en un **{ui.NOMBRE_ESC[esc].lower()}**. {e['descripcion']}")
ui.html(ui.confianza("recomendacion", esc))

hoy = logica.mes_actual()
if not ui.falta("climatologia_daule.csv", "cultivos.csv"):
    clim = carga.climatologia()
    plan = logica.plan(mejor["estrategia"], clim, carga.cultivos())
    ui.tarjeta_accion(logica.accion_del_mes(plan[0], hoy), hoy)
    ui.franja_anual(clim, [(f"Año {k + 1}" if len(plan) > 1 else "Tu plan", m)
                           for k, m in enumerate(plan)], mes_hoy=hoy)

base = comp[comp["estrategia"] == "A"]
if len(base) and mejor["estrategia"] != "A":
    ahorro = base["agua_m3_ha"].iloc[0] - mejor["agua_m3_ha"]
    if ahorro > 0:
        st.success(f"Ahorras unos **{ui.num(ahorro)} m³ de agua por hectárea** en cada ciclo "
                   "frente a sembrar solo arroz.", icon="💧")

motivos = logica.razones(mejor, pesos)
if motivos:
    st.markdown("Sale primera porque es la que mejor cumple con: **"
                + "** y **".join(m.lower() for m in motivos) + "**.")

# --- Ficha en cuatro partes -----------------------------------------------------------------
izq, der = st.columns(2)
bloques = [(izq, "👍 Lo bueno", "beneficios"), (der, "⚠️ Ten cuidado con", "riesgos"),
           (izq, "🔎 En qué nos basamos", "evidencia"), (der, "❓ Lo que todavía no sabemos", "vacios")]
for col, titulo, clave in bloques:
    with col.container(border=True):
        st.markdown(f"**{titulo}**")
        for item in e[clave]:
            st.markdown(f"- {item}")

# --- Reglas para el campo ----------------------------------------------------------------------
st.subheader("Reglas para tu campo")
reglas = [] if ui.falta("reglas.json") else carga.reglas_zona(zid)  # de esta zona + generales
for r in reglas:
    st.checkbox(r["texto_campo"], key=f"regla_{r.get('id', r['texto_campo'][:20])}",
                help=f"Por qué: {r['evidencia']}")
if reglas:
    st.caption("Marca las que ya tienes en cuenta. Toca el ícono ⓘ para ver de dónde sale cada regla.")
else:
    st.write("Todavía no hay reglas para esta zona.")

