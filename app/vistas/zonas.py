"""Mi campo: como se ve el terreno desde el satelite y cuando conviene sembrar cada cultivo."""
import plotly.graph_objects as go
import streamlit as st

from utils import carga, logica, ui

zid, znombre = ui.zona_actual()

st.title("🛰️ Tu campo visto desde el satélite")
ui.aviso_datos()

serie = carga.series()
sz = serie[serie["zona_id"] == zid].sort_values("fecha")
if sz.empty and (serie["zona_id"] == 0).any():
    sz = serie[serie["zona_id"] == 0].sort_values("fecha")
    st.info("Por ahora se muestra todo el recuadro de Daule. Cuando estén listas las zonas, "
            "verás solo la tuya.", icon="ℹ️")

# --- Que mirar ------------------------------------------------------------------------------
opciones = {
    "ndvi": ("🌱 Verdor", "#3E7D2F", "Más alto = cultivo más verde y sano. Cerca de 0 = suelo pelado."),
    "ndwi": ("💧 Agua", ui.RIO, "Por encima de 0 = hay agua sobre el terreno o está inundado."),
    "ndmi": ("🌿 Humedad", "#7A5FA8", "Más bajo = las plantas pueden estar pasando sed."),
}
ver = st.segmented_control("¿Qué quieres ver?", options=list(opciones), default="ndvi",
                           format_func=lambda k: opciones[k][0], key="indice") or "ndvi"
nombre, color, ayuda = opciones[ver]
st.markdown(ayuda)

fig = go.Figure()
fig.add_scatter(x=sz["fecha"], y=sz[ver], mode="lines+markers", name=nombre,
                line=dict(color=color, width=3), marker=dict(size=6),
                hovertemplate="%{x|%b %Y}: %{y:.2f}<extra></extra>")
if ver == "ndwi":
    fig.add_hline(y=0, line=dict(color=ui.RIESGO, dash="dot"),
                  annotation_text="encima = agua", annotation_position="top left")
fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white",
                  showlegend=False, font=dict(family="Atkinson Hyperlegible, sans-serif", size=14))
st.plotly_chart(fig, width="stretch")
ui.fuente(f"Landsat 8 y 9, una imagen por mes ({sz['fecha'].min():%m/%Y} a {sz['fecha'].max():%m/%Y}). "
          "Los cortes en la línea son meses con demasiadas nubes.")

# --- Cuando sembrar cada cultivo -------------------------------------------------------------
st.subheader("¿Cuándo sembrar cada cultivo aquí?")
cal, notas = logica.calendario(carga.climatologia(), carga.cultivos(), sz, znombre)
filas = []
for cultivo, fila in cal.iterrows():
    meses = [({"cultivo": cultivo, "etapa": v} if v and v != "riesgo" else (v or None)) for v in fila]
    filas.append((f"{ui.ICONO_CULTIVO.get(cultivo, '🌱')} {cultivo}", meses))
ui.franja_anual(carga.climatologia(), filas, mes_hoy=logica.mes_actual())
for n in notas:
    st.warning(n, icon="⚠️")

with st.expander("Ver los números de cada mes"):
    st.dataframe(sz.reset_index(drop=True), width="stretch", hide_index=True)
