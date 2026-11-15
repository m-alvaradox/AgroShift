"""Recomendacion: la opcion sugerida, por que, que cuidar y reglas para el campo."""
import streamlit as st

from utils import carga, logica, ui

zid, znombre = ui.zona_actual()
esc = ui.escenario_actual()
pesos = ui.pesos_actuales()

est = carga.estrategias()
info = carga.estrategias_info()
comp = logica.comparar(est, zid, esc, pesos)
mejor = comp.iloc[0]
e = info[mejor["estrategia"]]
clim = carga.climatologia()
plan = logica.plan(mejor["estrategia"], clim, carga.cultivos())

st.title("✅ Te recomendamos")
ui.aviso_datos()
st.markdown(f"## {e['nombre']}")
st.markdown(f"Para la **{znombre.lower()}** en un **{ui.NOMBRE_ESC[esc].lower()}**. {e['descripcion']}")

hoy = logica.mes_actual()
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
reglas = [r for r in carga.reglas() if r.get("zona_id") in (None, zid)]
for r in reglas:
    st.checkbox(r["texto_campo"], key=f"regla_{r.get('id', r['texto_campo'][:20])}",
                help=f"Por qué: {r['evidencia']}")
if reglas:
    st.caption("Marca las que ya tienes en cuenta. Toca el ícono ⓘ para ver de dónde sale cada regla.")
else:
    st.write("Todavía no hay reglas para esta zona.")

st.divider()
ui.aviso_tecnico()
