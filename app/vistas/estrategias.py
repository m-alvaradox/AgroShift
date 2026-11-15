"""Estrategias: comparar las 3 rotaciones segun zona, escenario y prioridades."""
import plotly.graph_objects as go
import streamlit as st

from utils import carga, logica, ui

zid, znombre = ui.zona_actual()
esc = ui.escenario_actual()
pesos = ui.pesos_actuales()

st.title("🌱 Comparar estrategias")
st.markdown(f"**{znombre}** · {ui.NOMBRE_ESC[esc]}. Cambia la zona, el tipo de año o tus "
            "prioridades en la barra lateral y mira cómo cambia el orden.")
ui.aviso_datos()

est = carga.estrategias()
info = carga.estrategias_info()
comp = logica.comparar(est, zid, esc, pesos)
base = est[(est["zona_id"] == zid) & (est["escenario"] == esc) & (est["estrategia"] == "A")]
agua_base = float(base["agua_m3_ha"].iloc[0]) if len(base) else None

# --- Tarjetas --------------------------------------------------------------------
cols = st.columns(3)
for i, (col, (_, fila)) in enumerate(zip(cols, comp.iterrows())):
    e = info[fila["estrategia"]]
    with col.container(border=True):
        if i == 0:
            st.success("Mejor para tus prioridades", icon="⭐")
        st.markdown(f"### {fila['estrategia']} · {e['nombre']}")
        st.caption(e["secuencia"])
        delta = None
        if agua_base and fila["estrategia"] != "A":
            delta = f"{(fila['agua_m3_ha'] / agua_base - 1) * 100:+.0f} % frente a A"
        st.metric("Agua por ciclo", f"{ui.num(fila['agua_m3_ha'])} m³/ha", delta=delta,
                  delta_color="inverse")
        st.metric("Puntaje", f"{ui.num(fila['puntaje'], 1)} / 10")
        for c, nombre in logica.CRITERIOS.items():
            st.progress(min(1.0, fila[c] / 10), text=f"{nombre}: {fila[c]:.0f}/10")

ui.fuente("agua con el balance FAO-56 y NASA POWER; notas de suelo, plagas e ingresos del catálogo de P4.")

# --- Agua segun el tipo de anio --------------------------------------------------
st.subheader("Agua necesaria según el tipo de año")
dz = est[est["zona_id"] == zid]
fig = go.Figure()
for e in ["normal", "nino", "nina"]:
    d = dz[dz["escenario"] == e].sort_values("estrategia")
    fig.add_bar(x=d["estrategia"].map(lambda s: f"{s} · {info[s]['nombre']}"), y=d["agua_m3_ha"],
                name=ui.NOMBRE_ESC[e], marker_color=ui.COLOR_ESC[e],
                hovertemplate="%{x}: %{y:,.0f} m³/ha<extra></extra>")
fig.update_layout(barmode="group", height=360, margin=dict(l=10, r=10, t=30, b=10),
                  yaxis_title="m³ por hectárea", plot_bgcolor="white",
                  legend=dict(orientation="h", y=1.12))
st.plotly_chart(fig, width="stretch")
st.caption("En años El Niño llueve más, así que se necesita menos riego, pero sube el riesgo de inundación.")

st.page_link("vistas/recomendacion.py", label="Ver la recomendación y sus razones", icon="✅")
