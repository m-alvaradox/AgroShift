"""Clima: patrones historicos y anios El Nino / La Nina."""
import plotly.graph_objects as go
import streamlit as st

from utils import carga, ui

st.title("🌦️ Clima de Daule")
st.markdown("Qué meses llueve más de lo que se evapora (sobra agua) y cuáles son secos (falta agua).")
ui.aviso_datos()

clim = carga.climatologia().sort_values("mes")

# --- Lluvia frente a evaporacion -------------------------------------------------
fig = go.Figure()
fig.add_bar(x=clim["nombre_mes"], y=clim["lluvia_mm"], name="Lluvia",
            marker_color=[ui.COLOR_TIPO[t] for t in clim["tipo_mes"]],
            customdata=[ui.NOMBRE_TIPO[t] for t in clim["tipo_mes"]],
            hovertemplate="%{x}: %{y:.0f} mm · %{customdata}<extra></extra>")
fig.add_scatter(x=clim["nombre_mes"], y=clim["et0_mm"], name="Agua que se evapora (ET0)",
                mode="lines+markers", line=dict(color="#333", width=2),
                hovertemplate="%{x}: %{y:.0f} mm<extra></extra>")
fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="mm por mes",
                  legend=dict(orientation="h", y=1.12), plot_bgcolor="white")
st.plotly_chart(fig, width="stretch")
ui.fuente("NASA POWER, promedio 1991–2025.")

cols = st.columns(3)
for col, tipo in zip(cols, ["lluvioso", "transicion", "seco"]):
    meses = clim.loc[clim["tipo_mes"] == tipo, "nombre_mes"].tolist()
    col.markdown(f"**{ui.NOMBRE_TIPO[tipo]}**")
    col.write(", ".join(meses) if meses else "—")

with st.expander("¿Cómo se clasifica cada mes?"):
    st.markdown(
        "- **Lluvioso:** llueve igual o más de lo que se evapora.\n"
        "- **Seco:** llueve menos de la mitad de lo que se evapora.\n"
        "- **Transición:** todo lo demás.\n\n"
        f"**ET0:** {ui.GLOSARIO['ET0']}"
    )

# --- Anios El Nino y La Nina -----------------------------------------------------
st.subheader("¿Cuánto cambia la lluvia en años El Niño y La Niña?")
imerg = carga.lluvia_imerg()
anual = imerg.assign(anio=imerg["fecha"].dt.year).groupby(["anio", "enso"], as_index=False)["lluvia_mm"].sum()

fig2 = go.Figure()
for e in ["normal", "nino", "nina"]:
    clave = "neutro" if e == "normal" else e
    d = anual[anual["enso"] == clave]
    fig2.add_bar(x=d["anio"], y=d["lluvia_mm"], name=ui.NOMBRE_ESC[e], marker_color=ui.COLOR_ESC[e],
                 hovertemplate="%{x}: %{y:,.0f} mm<extra></extra>")
fig2.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="mm por año",
                   legend=dict(orientation="h", y=1.15), plot_bgcolor="white", bargap=0.15)
st.plotly_chart(fig2, width="stretch")
ui.fuente("GPM IMERG, lluvia mensual sumada por año.")

prom = anual.groupby("enso")["lluvia_mm"].mean()
if {"nino", "neutro"} <= set(prom.index):
    extra = (prom["nino"] / prom["neutro"] - 1) * 100
    st.info(f"En años El Niño llueve en promedio **{extra:.0f} % más** que en un año normal. "
            "Esto aumenta el riesgo de inundación en la zona baja.", icon="🌧️")
