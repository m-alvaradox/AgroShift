"""
Mi plan: el recorrido de la abejita mes a mes desde el mes de inicio, y 3 consejos.

El camino es un grafico de plotly con un punto por mes (12 paradas) sobre el color de la
temporada de cada mes (climatologia de NASA POWER). La abejita avanza con el boton de
reproducir o con el control deslizante (frames de plotly). En cada parada: mes, cultivo,
etapa (siembra, crece, cosecha o descanso) y una accion concreta.
"""
import math
import textwrap
from datetime import date

import plotly.graph_objects as go
import streamlit as st

from utils import carga, juego, ui

zid, znombre = ui.zona_actual()
tipo = ui.tipo_zona(znombre)
esc = ui.escenario_actual()
hoy = date.today().month - 1
ss = st.session_state

st.title("Mi plan")
recomendada = None
if not ui.falta("estrategias.csv"):  # sin estrategias.csv no hay recomendacion, pero si el plan
    recomendada = ui.recomendada_para(zid, esc, ui.objetivo()) if ui.objetivo() else None
    if recomendada is None:
        comp = ui.ranking(zid, esc)
        recomendada = comp["estrategia"].iloc[0] if not comp.empty else None
elegida = ss.get("estrategia_elegida") or recomendada or "A"
if elegida not in juego.ATAJOS:
    elegida = recomendada or "A"


def elegir(k):
    ss["estrategia_elegida"] = k


def mes_cambiado():
    ui.guardar_mes(ss["w_mes_plan"])


atajo = juego.ATAJOS[elegida]
with st.container(key="cambiar_plan", horizontal=True, gap="small"):
    for k, a in juego.ATAJOS.items():
        st.button(f"{k} · {a['nombre']}", key=f"plan_btn_{k}", on_click=elegir, args=(k,),
                  type="primary" if k == elegida else "secondary", width="stretch")
mes0 = ui.mes_inicio()
mes0 = hoy if mes0 is None else mes0
c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
with c1:
    ui.html(f'<p class="plan-elegido"><b>{elegida} · {atajo["nombre"]}</b>'
            f'{" · recomendado para lo que quieres lograr" if elegida == recomendada and ui.objetivo() else ""}'
            f'{" · recomendado" if elegida == recomendada and not ui.objetivo() else ""}'
            f'<br>{ui.mini_cartas(atajo["secuencia"])}</p>')
c2.selectbox("Empezar en", options=list(range(12)), index=mes0, key="w_mes_plan", on_change=mes_cambiado,
             format_func=lambda m: juego.MESES_LARGOS[m].capitalize())

# --- Las 12 paradas, desde el mes de inicio ---------------------------------------------------
anio0 = ui.anio_de_inicio(mes0)
calendario = juego.plan_12_meses(atajo["secuencia"])
paradas = []
for i in range(12):
    m = (mes0 + i) % 12
    p = dict(calendario[m])
    p.update({"i": i, "m": m, "anio": anio0 + (mes0 + i) // 12})
    paradas.append(p)

clim = carga.climatologia() if carga.disponible("climatologia_daule.csv") else None
tipos = clim.sort_values("mes")["tipo_mes"].tolist() if clim is not None else ["sin"] * 12
FONDO = {"lluvioso": "#DCEAF5", "transicion": "#EBF2F7", "seco": "#F6ECCB", "sin": "#F1F3EF"}


def y_de(x: float) -> float:
    return 0.5 * math.sin(x * math.pi / 2)  # camino ondulado: sube y baja cada 2 meses


def detalle(p: dict) -> str:
    accion = "<br>".join(textwrap.wrap(p["accion"], 46))
    return (f"<b>{juego.MESES_LARGOS[p['m']].capitalize()} {p['anio']} · {p['cultivo']}</b>"
            f"<br>{p['etapa']}<br>{accion}")


def caja(p: dict) -> dict:
    return dict(text=detalle(p), x=0.5, y=1.0, xref="paper", yref="paper", xanchor="center", yanchor="bottom",
                showarrow=False, align="left", font=dict(size=14, color="#1F2A1F"), bgcolor="#FFFFFF",
                bordercolor="#2E7D32", borderwidth=2, borderpad=8)


xs = [p["i"] for p in paradas]
ys = [y_de(x) for x in xs]
fino = [k / 10 for k in range(0, 111)]
fig = go.Figure()
# 0: el camino
fig.add_trace(go.Scatter(x=fino, y=[y_de(x) for x in fino], mode="lines", hoverinfo="skip",
                         line=dict(color="#A1887F", width=5, dash="dot"), showlegend=False))
# 1: las paradas (cosecha en dorado, siembra en verde)
COLOR_ETAPA = {"Siembra": "#2E7D32", "Crece": "#9CCC65", "Cosecha": "#F9A825", "Descanso": "#BCAAA4"}
fig.add_trace(go.Scatter(
    x=xs, y=ys, mode="markers+text", text=[juego.MESES[p["m"]] for p in paradas], textposition="bottom center",
    textfont=dict(size=12, color="#3E4E40"), showlegend=False,
    marker=dict(size=[22 if p["m"] == hoy else 16 for p in paradas],
                color=[COLOR_ETAPA[p["etapa"]] for p in paradas],
                line=dict(width=[4 if p["m"] == hoy else 2 for p in paradas], color="#1B4D20")),
    customdata=[[juego.MESES_LARGOS[p["m"]].capitalize(), p["anio"], p["cultivo"], p["etapa"], p["accion"]]
                for p in paradas],
    hovertemplate="<b>%{customdata[0]} %{customdata[1]}</b><br>%{customdata[2]} · %{customdata[3]}"
                  "<br>%{customdata[4]}<extra></extra>"))
# 2: el cultivo de cada parada
fig.add_trace(go.Scatter(x=xs, y=[y + 0.32 for y in ys], mode="text", hoverinfo="skip", showlegend=False,
                         text=[juego.CARTAS[p["cultivo"]]["icono"] for p in paradas], textfont=dict(size=18)))
# 3: la abejita
fig.add_trace(go.Scatter(x=[xs[0]], y=[ys[0] + 0.02], mode="text", text=["🐝"], textfont=dict(size=30),
                         hoverinfo="skip", showlegend=False))
fig.frames = [go.Frame(name=str(p["i"]), traces=[3],
                       data=[go.Scatter(x=[p["i"]], y=[ys[p["i"]] + 0.02])],
                       layout=go.Layout(annotations=[caja(p)])) for p in paradas]
# fondo de cada tramo con el color de su temporada
for p in paradas:
    fig.add_vrect(x0=p["i"] - 0.5, x1=p["i"] + 0.5, fillcolor=FONDO[tipos[p["m"]]], line_width=0, layer="below")
animar = {"frame": {"duration": 900, "redraw": True}, "transition": {"duration": 300}, "fromcurrent": True,
          "mode": "immediate"}
fig.update_layout(
    height=430, margin=dict(l=8, r=8, t=118, b=10), plot_bgcolor="#FFFFFF", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Nunito, sans-serif"), annotations=[caja(paradas[0])], dragmode=False,
    xaxis=dict(visible=False, range=[-0.6, 11.6], fixedrange=True),
    yaxis=dict(visible=False, range=[-0.95, 0.95], fixedrange=True),
    updatemenus=[dict(type="buttons", direction="left", x=0, y=-0.01, xanchor="left", yanchor="top",
                      pad=dict(t=6, r=6), showactive=False, bgcolor="#E8F5E9", bordercolor="#2E7D32",
                      font=dict(size=13, color="#1B4D20"),
                      buttons=[dict(label="▶ Reproducir", method="animate", args=[None, animar]),
                               dict(label="❚❚ Pausa", method="animate",
                                    args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}])])],
    sliders=[dict(active=0, x=0, len=1, y=-0.13, yanchor="top", pad=dict(t=4, b=0, l=8, r=8),
                  currentvalue=dict(visible=False), font=dict(size=10, color="#3E4E40"), tickcolor="#9AA59A",
                  bgcolor="#E8F5E9", bordercolor="#2E7D32", activebgcolor="#2E7D32",
                  steps=[dict(label=juego.MESES[p["m"]], method="animate",
                              args=[[str(p["i"])], {"frame": {"duration": 0, "redraw": True},
                                                    "transition": {"duration": 250}, "mode": "immediate"}])
                         for p in paradas])])
fig.update_layout(height=500, margin=dict(b=118))

st.subheader("El recorrido de la abejita")
with st.container(key="graf_plan"):
    st.plotly_chart(fig, config={"displayModeBar": False, "responsive": True}, width="stretch", key="camino")
    ui.html('<div class="leyenda"><span><i style="background:#DCEAF5"></i>Lluvias</span>'
            '<span><i style="background:#EBF2F7"></i>Cambio de temporada</span>'
            '<span><i style="background:#F6ECCB"></i>Seca</span>'
            + "".join(f'<span><i style="background:{c};border-radius:50%"></i>{e}</span>'
                      for e, c in COLOR_ETAPA.items())
            + '</div><p class="fuente-peq">Toca ▶ Reproducir o mueve el control para avanzar mes a mes. '
              'El punto grande es el mes actual.</p>')
ui.html(ui.etiqueta_fuente(False, "📋 Calendario general por temporada") + ui.confianza("plan"))

st.subheader("Mes a mes")
filas = []
for p in paradas:
    es_hoy = p["m"] == hoy
    filas.append(f'<div class="plan-mes{" hoy" if es_hoy else ""}"><div class="ico">{p["icono"]}</div>'
                 f'<div class="mes">{juego.MESES[p["m"]]}</div><div><div class="etapa">{p["etapa"]} · '
                 f'{p["cultivo"]}{" · este mes" if es_hoy else ""}</div><div class="acc">{p["accion"]}</div></div></div>')
ui.html(f'<div class="plan-lista">{"".join(filas)}</div>')

st.subheader("3 consejos para ti")
for c in juego.consejos(tipo, esc, atajo["secuencia"]):
    ui.html(f'<div class="consejo">{c}</div>')
