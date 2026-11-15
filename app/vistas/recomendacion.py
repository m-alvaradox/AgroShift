"""Recomendacion: estrategia sugerida con evidencia, beneficios, vacios y riesgos."""
import streamlit as st

from utils import carga, logica, ui

zid, znombre = ui.zona_actual()
esc = ui.escenario_actual()
pesos = ui.pesos_actuales()

st.title("✅ Recomendación")
ui.aviso_datos()

est = carga.estrategias()
info = carga.estrategias_info()
comp = logica.comparar(est, zid, esc, pesos)
mejor = comp.iloc[0]
e = info[mejor["estrategia"]]

st.markdown(f"Para **{znombre}** en un **{ui.NOMBRE_ESC[esc].lower()}**, te sugerimos:")
st.markdown(f"## {mejor['estrategia']} · {e['nombre']}")
st.markdown(f"**{e['secuencia']}** — {e['descripcion']}")

base = comp[comp["estrategia"] == "A"]
c1, c2, c3 = st.columns(3)
c1.metric("Puntaje", f"{ui.num(mejor['puntaje'], 1)} / 10")
c2.metric("Agua por ciclo", f"{ui.num(mejor['agua_m3_ha'])} m³/ha")
if len(base) and mejor["estrategia"] != "A":
    ahorro = base["agua_m3_ha"].iloc[0] - mejor["agua_m3_ha"]
    c3.metric("Ahorro frente a arroz todo el año", f"{ui.num(ahorro)} m³/ha")
else:
    c3.metric("Frente a lo que se hace hoy", "Es la misma práctica")

motivos = logica.razones(mejor, pesos)
if motivos:
    st.info("Sale primera sobre todo por: **" + "** y **".join(motivos).lower() + "**, "
            "según las prioridades que marcaste.", icon="💡")

# --- Ficha -----------------------------------------------------------------------
izq, der = st.columns(2)
bloques = [(izq, "🔎 Evidencia", "evidencia"), (izq, "👍 Beneficios", "beneficios"),
           (der, "❓ Vacíos de información", "vacios"), (der, "⚠️ Riesgos", "riesgos")]
for col, titulo, clave in bloques:
    with col.container(border=True):
        st.markdown(f"**{titulo}**")
        for item in e[clave]:
            st.markdown(f"- {item}")

# --- Reglas para el campo --------------------------------------------------------
st.subheader("Reglas para el campo")
reglas = [r for r in carga.reglas() if r.get("zona_id") in (None, zid)]
for r in reglas:
    with st.container(border=True):
        st.markdown(f"**{r['texto_campo']}**")
        st.caption(f"Por qué: {r['evidencia']}")
if not reglas:
    st.write("No hay reglas específicas para esta zona todavía.")

st.divider()
ui.aviso_tecnico()
