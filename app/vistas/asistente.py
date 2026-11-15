"""Asistente: vista previa de como funcionara por WhatsApp (simulado, sin conexion real)."""
from datetime import date, datetime
from html import escape

import streamlit as st

from utils import carga, juego, ui

zid, znombre = ui.zona_actual()
tipo = ui.tipo_zona(znombre)
esc = ui.escenario_actual()
hoy = date.today().month - 1
clim = carga.climatologia()

comp = ui.ranking(zid, esc)
k = st.session_state.get("estrategia_elegida") or (comp["estrategia"].iloc[0] if not comp.empty else "B")
atajo = juego.ATAJOS.get(k, juego.ATAJOS["B"])
mes_plan = juego.plan_12_meses(atajo["secuencia"])[hoy]
ctx = {
    "zona": ui.corto_zona(znombre), "zona_tipo": tipo, "escenario": esc,
    "plan_nombre": atajo["nombre"], "secuencia": atajo["secuencia"],
    "lluvias": juego.lluvias_texto(clim),
    "agua": juego.semaforo_agua(clim, juego.factor_lluvia(carga.lluvia_imerg(), esc)),
    "mes": mes_plan["mes_largo"], "accion": mes_plan["accion"],
}


def ahora() -> str:
    return datetime.now().strftime("%H:%M")


ss = st.session_state
if "chat" not in ss:
    ss["chat"] = [
        {"de": "bot", "texto": "¡Hola! Soy el asistente de AgroShift 🌱. Toca una pregunta de abajo.", "hora": ahora()},
        {"de": "bot", "texto": juego.ALERTA_EJEMPLO, "hora": ahora(), "alerta": True},
    ]


def preguntar(clave):
    ss["chat"].append({"de": "yo", "texto": juego.PREGUNTAS[clave], "hora": ahora()})
    ss["chat"].append({"de": "bot", "texto": juego.respuesta(clave, ctx), "hora": ahora()})


def borrar():
    del ss["chat"]


st.title("💬 Asistente")

burbujas = "".join(
    f'<div class="burbuja {m["de"]}{" alerta" if m.get("alerta") else ""}">{escape(m["texto"])}'
    f'<span class="hora">{m["hora"]}</span></div>' for m in ss["chat"][-12:])
ui.html('<div class="wa"><div class="wa-top"><div class="wa-avatar">🌱</div>'
        '<div><b>AgroShift</b><small>en línea</small></div></div>'
        f'<div class="wa-body">{burbujas}</div></div>')

with st.container(key="rapidas", horizontal=True, gap="small"):
    for clave, texto in juego.PREGUNTAS.items():
        st.button(texto, key=f"rapida_{clave}", on_click=preguntar, args=(clave,), width="stretch")
    st.button("🧹 Borrar chat", key="rapida_borrar", on_click=borrar, width="stretch")

ui.html('<div class="wa-nota">📱 Vista previa: así funcionará por WhatsApp.</div>')
