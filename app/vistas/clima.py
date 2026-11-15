"""Clima: cuando llueve, cuando falta agua y como cambia en anios El Nino y La Nina."""
import plotly.graph_objects as go
import streamlit as st

from utils import carga, logica, ui

st.title("🌦️ Cuándo llueve en Daule")
ui.aviso_datos()

clim = carga.climatologia().sort_values("mes")
mensual = carga.clima_mensual().sort_values("fecha")


def rango(tipo: str) -> str:
    meses = [logica.MESES_LARGOS[m - 1] for m in clim.loc[clim["tipo_mes"] == tipo, "mes"]]
    if not meses:
        return ""
    return meses[0] if len(meses) == 1 else f"{meses[0]} a {meses[-1]}"


st.markdown(f"Llueve sobre todo de **{rango('lluvioso')}**. De **{rango('seco')}** falta agua: "
            "se evapora más de lo que llueve, así que los cultivos necesitan riego o la humedad "
            "que queda en el suelo.")

# --- Lluvia frente a evaporacion en un anio tipico --------------------------------------------
fig = go.Figure()
fig.add_bar(x=clim["nombre_mes"], y=clim["lluvia_mm"], name="Lluvia de un año típico",
            marker_color=[ui.COLOR_TIPO[t] for t in clim["tipo_mes"]],
            customdata=[ui.NOMBRE_TIPO[t] for t in clim["tipo_mes"]],
            hovertemplate="%{x}: llueven %{y:.0f} mm · %{customdata}<extra></extra>")
fig.add_scatter(x=clim["nombre_mes"], y=clim["et0_mm"], name="Agua que se evapora",
                mode="lines+markers", line=dict(color=ui.VERDE_ARROZAL, width=3),
                hovertemplate="%{x}: se evaporan %{y:.0f} mm<extra></extra>")
fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="milímetros por mes",
                  legend=dict(orientation="h", y=-0.15), plot_bgcolor="white",
                  font=dict(family="Atkinson Hyperlegible, sans-serif", size=14))
st.plotly_chart(fig, width="stretch")
st.caption("Cuando la barra pasa la línea, sobra agua. Cuando queda por debajo, falta.")
ui.fuente(f"NASA POWER, {mensual['anio'].min()}–{mensual['anio'].max()}.")

# --- Este anio frente a lo normal ----------------------------------------------------------
st.subheader("¿Cómo viene lloviendo?")
ult = mensual.tail(24).copy()
ult["tipico"] = ult["mes"].map(dict(zip(clim["mes"], clim["lluvia_mm"])))
raro = (ult["lluvia_mm"] > 3 * ult["tipico"] + 50)
fig2 = go.Figure()
fig2.add_bar(x=ult["fecha"], y=ult["lluvia_mm"], name="Lo que llovió",
             marker_color=[ui.RIESGO if r else ui.RIO for r in raro],
             hovertemplate="%{x|%b %Y}: %{y:.0f} mm<extra></extra>")
fig2.add_scatter(x=ult["fecha"], y=ult["tipico"], name="Lo normal para ese mes", mode="lines",
                 line=dict(color="#333", dash="dot"))
fig2.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="milímetros",
                   legend=dict(orientation="h", y=-0.2), plot_bgcolor="white",
                   font=dict(family="Atkinson Hyperlegible, sans-serif", size=14))
st.plotly_chart(fig2, width="stretch")
if raro.any():
    meses_raros = ", ".join(f"{logica.MESES_LARGOS[f.month - 1]} {f.year}" for f in ult.loc[raro, "fecha"])
    st.error(f"Llovió muchísimo más de lo normal en: {meses_raros}. "
             "En la zona baja eso significa riesgo de inundación.", icon="🌧️")

# --- Anios El Nino y La Nina ---------------------------------------------------------------
st.subheader("¿Y en años de El Niño o La Niña?")
imerg = carga.lluvia_imerg()
anual = imerg.assign(anio=imerg["fecha"].dt.year).groupby(["anio", "enso"], as_index=False)["lluvia_mm"].sum()
prom = anual.groupby("enso")["lluvia_mm"].mean()
c1, c2, c3 = st.columns(3)
for col, clave, esc in [(c1, "neutro", "normal"), (c2, "nino", "nino"), (c3, "nina", "nina")]:
    if clave in prom.index:
        delta = None
        if clave != "neutro" and "neutro" in prom.index:
            delta = f"{(prom[clave] / prom['neutro'] - 1) * 100:+.0f} % que un año normal"
        col.metric(f"{ui.ICONO_ESC[esc]} {ui.NOMBRE_ESC[esc]}", f"{ui.num(prom[clave])} mm",
                   delta=delta, delta_color="off")
st.caption("Lluvia promedio en un año completo.")
ui.fuente("GPM IMERG.")

with st.expander("¿Cómo se decide si un mes es de lluvias o seco?"):
    st.markdown(
        "- **Lluvias:** llueve igual o más de lo que se evapora.\n"
        "- **Seca:** llueve menos de la mitad de lo que se evapora.\n"
        "- **Transición:** todo lo demás.\n\n"
        f"{ui.GLOSARIO['ET0']}")
