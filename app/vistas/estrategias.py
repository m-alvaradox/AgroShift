"""Opciones: comparar las 3 rotaciones segun lo que le importa al productor."""
import plotly.graph_objects as go
import streamlit as st

from utils import carga, logica, ui

zid, znombre = ui.zona_actual()
esc = ui.escenario_actual()

st.title("🌱 Compara tus opciones")
ui.origen_datos()
if ui.falta("estrategias.csv", "estrategias_info.json"):
    st.stop()

# --- Prioridades (se guardan para las otras paginas) --------------------------------------
ICONO_CRIT = {"nota_agua": "💧", "nota_suelo": "🪱", "nota_plagas": "🐛", "nota_ingresos": "💵"}


def guardar_prioridades():
    st.session_state["prio_guardadas"] = st.session_state.get("w_prio") or []


st.pills("¿Qué es lo más importante para ti? Puedes elegir varias.",
         options=list(logica.CRITERIOS), selection_mode="multi", key="w_prio",
         default=st.session_state.get("prio_guardadas", []), on_change=guardar_prioridades,
         format_func=lambda c: f"{ICONO_CRIT[c]} {logica.CRITERIOS[c]}")
pesos = ui.pesos_actuales()

est = carga.estrategias()
info = carga.estrategias_info()
clim = carga.climatologia() if carga.disponible("climatologia_daule.csv") else None
cult = carga.cultivos() if carga.disponible("cultivos.csv") else None
comp = logica.comparar(est, zid, esc, pesos)
agua_max = float(comp["agua_m3_ha"].max())
base = comp[comp["estrategia"] == "A"]
agua_base = float(base["agua_m3_ha"].iloc[0]) if len(base) else None

st.markdown(f"Para la **{znombre.lower()}** en un **{ui.NOMBRE_ESC[esc].lower()}**, "
            "de la mejor a la menos recomendada:")

# --- Una tarjeta por opcion, de mejor a peor ------------------------------------------------
for i, fila in comp.iterrows():
    e = info[fila["estrategia"]]
    with st.container(border=True):
        if i == 0:
            st.markdown('<div class="opcion-top">⭐ La mejor para lo que te importa</div>',
                        unsafe_allow_html=True)
        izq, der = st.columns([3, 2])
        with izq:
            st.markdown(f"### {e['nombre']}")
            st.markdown(e["descripcion"])
        with der:
            st.markdown(f'<div class="estrellas">{logica.estrellas(fila["puntaje"])}</div>',
                        unsafe_allow_html=True)
            gotas = max(1, round(5 * fila["agua_m3_ha"] / agua_max))
            texto_agua = f"{ui.num(fila['agua_m3_ha'])} m³ de agua por hectárea"
            if agua_base and fila["estrategia"] != "A":
                dif = (1 - fila["agua_m3_ha"] / agua_base) * 100
                texto_agua += f" · {dif:.0f} % menos que arroz todo el año" if dif > 0 else ""
            st.markdown(f'<div class="gotas">{"💧" * gotas}</div>{texto_agua}', unsafe_allow_html=True)

        if clim is not None and cult is not None:
            plan = logica.plan(fila["estrategia"], clim, cult)
            filas = [(f"Año {k + 1}" if len(plan) > 1 else "Su año", m) for k, m in enumerate(plan)]
            ui.franja_anual(clim, filas)
        else:
            ui.falta("climatologia_daule.csv", "cultivos.csv")

        cols = st.columns(4)
        for col, (c, nombre) in zip(cols, logica.CRITERIOS.items()):
            col.progress(min(1.0, fila[c] / 10), text=f"{ICONO_CRIT[c]} {nombre}")

# --- Agua segun el tipo de anio ---------------------------------------------------------------
st.subheader("¿Cuánta agua necesita cada opción según el año?")
dz = est[est["zona_id"] == zid]
fig = go.Figure()
for esc_k in ["nina", "normal", "nino"]:
    d = dz[dz["escenario"] == esc_k].sort_values("estrategia")
    fig.add_bar(y=d["estrategia"].map(lambda s: info[s]["nombre"]), x=d["agua_m3_ha"], orientation="h",
                name=f"{ui.ICONO_ESC[esc_k]} {ui.NOMBRE_ESC[esc_k]}", marker_color=ui.COLOR_ESC[esc_k],
                hovertemplate="%{y}: %{x:,.0f} m³/ha<extra></extra>")
fig.update_layout(barmode="group", height=360, margin=dict(l=10, r=10, t=10, b=10),
                  xaxis_title="m³ de agua por hectárea", plot_bgcolor="white",
                  legend=dict(orientation="h", y=-0.25),
                  font=dict(family="Atkinson Hyperlegible, sans-serif", size=14))
st.plotly_chart(fig, width="stretch")
st.caption("En un año muy lluvioso hace falta menos riego, pero la zona baja se puede inundar.")
ui.fuente("agua de riego con el método FAO-56 (NASA POWER y los años de GPM IMERG); notas de "
          "suelo, plagas e ingresos con las reglas de P4 (scripts/calcular_estrategias.py).")

st.page_link("vistas/recomendacion.py", label="Ver por qué te recomendamos la primera", icon="✅")
