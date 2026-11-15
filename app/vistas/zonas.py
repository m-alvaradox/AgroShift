"""Zonas y series: como se comporta cada zona mes a mes y calendario de siembra."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import carga, logica, ui

zid, znombre = ui.zona_actual()

st.title("🛰️ Zonas y series de tiempo")
st.markdown(f"Cómo cambió **{znombre}** mes a mes en los últimos 5 años, visto desde el satélite.")
ui.aviso_datos()

serie = carga.series()
sz = serie[serie["zona_id"] == zid].sort_values("fecha")

# --- Indices en el tiempo --------------------------------------------------------
indices = {"ndvi": ("NDVI · verdor", "#2E7D32"), "ndwi": ("NDWI · agua", "#3B82C4"),
           "ndmi": ("NDMI · humedad", "#8E6BBF")}
elegidos = st.multiselect("Índices a mostrar", list(indices), default=["ndvi", "ndwi"],
                          format_func=lambda k: indices[k][0])
fig = go.Figure()
for k in elegidos:
    fig.add_scatter(x=sz["fecha"], y=sz[k], name=indices[k][0], mode="lines",
                    line=dict(color=indices[k][1], width=2))
fig.add_hline(y=0, line=dict(color="#999", dash="dot"))
fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white",
                  legend=dict(orientation="h", y=1.12), yaxis_title="valor del índice")
st.plotly_chart(fig, width="stretch")
ui.fuente("Landsat 8 y 9, compuestos mensuales 2021–2025.")

with st.expander("¿Qué significa cada índice?"):
    for k in ["NDVI", "NDWI", "NDMI"]:
        st.markdown(f"- **{k}:** {ui.GLOSARIO[k]}")

# --- Meses con agua en superficie ------------------------------------------------
st.subheader("¿En qué meses hubo agua en el terreno?")
tabla = (sz.assign(anio=sz["fecha"].dt.year, mes=sz["fecha"].dt.month)
           .pivot_table(index="anio", columns="mes", values="ndwi"))
tabla.columns = [logica.MESES[m - 1] for m in tabla.columns]
fig2 = go.Figure(go.Heatmap(
    z=tabla.values, x=tabla.columns, y=tabla.index.astype(str),
    colorscale=[[0, "#F4E6C8"], [0.5, "#F7F7F7"], [1, "#3B82C4"]], zmid=0,
    colorbar=dict(title="NDWI"), hovertemplate="%{y} %{x}: %{z:.2f}<extra></extra>"))
fig2.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig2, width="stretch")
st.caption("Azul = hubo agua en la superficie (NDWI mayor que 0). Sirve para saber cuándo no sembrar soya o maíz.")

# --- Calendario de siembra -------------------------------------------------------
st.subheader("Calendario sugerido de siembra")
cal, notas = logica.calendario(carga.climatologia(), carga.cultivos(), sz, znombre)
colores = {"Siembra": "#2E7D32", "Crece": "#A5D6A7", "Cosecha": "#F2C14E", "Riesgo": "#E57373"}


def pintar(v):
    if v in colores:
        texto = "white" if v in ("Siembra", "Riesgo") else "black"
        return f"background-color: {colores[v]}; color: {texto}"
    return ""


st.dataframe(cal.style.map(pintar), width="stretch")
for n in notas:
    st.warning(n, icon="⚠️")
st.caption("Lógica de ejemplo: la reemplazarán las reglas de P4 cuando estén listas.")

with st.expander("Ver los datos de esta zona"):
    st.dataframe(sz.reset_index(drop=True), width="stretch", hide_index=True)
