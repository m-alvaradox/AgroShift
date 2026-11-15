"""
Asistente: vista previa de como funcionara por WhatsApp (simulado, sin conexion real).

Primero hace 3 preguntas, en orden, con botones de respuesta:
  a) ¿Donde esta tu finca?        -> GPS ("Ubicar mi finca") o la zona a mano
  b) ¿Que quieres lograr?         -> ahorrar agua, mejorar el suelo, menos plagas o ganar mas
  c) ¿Desde que mes empiezas?     -> el mes actual u otro
Las respuestas quedan en st.session_state (ver ui.py) y las usan Mi finca, Mis opciones,
Mi plan y Jugar. Si una ya se respondio en otra pagina, no se vuelve a preguntar.
Al final responde con un resumen hecho con los datos reales (estrategias.csv y el plan).
"""
from datetime import date, datetime
from html import escape

import streamlit as st

from utils import carga, juego, ubicacion, ui

ss = st.session_state
hoy = date.today().month - 1
st.title("Asistente")
if ui.falta("climatologia_daule.csv"):  # sin clima el asistente no puede responder
    ui.terminar_pagina()
clim = carga.climatologia()
imerg = carga.lluvia_imerg() if carga.disponible("lluvia_imerg_daule.csv") else None
mensual = carga.clima_mensual() if carga.disponible("clima_mensual_daule.csv") else None
hay_zonas = carga.disponible("zonas_daule.geojson")
hay_estrategias = carga.disponible("estrategias.csv")

zid, znombre = ui.zona_actual()
tipo = ui.tipo_zona(znombre)
esc = ui.escenario_actual()
nombres = {}
if hay_zonas:
    tabla = carga.tabla_zonas().sort_values("zona_id")
    nombres = dict(zip(tabla["zona_id"].astype(int), tabla["nombre_comun"]))

ss.setdefault("asis_horas", {})
ss.setdefault("chat", [])  # preguntas libres despues del resumen


def ahora() -> str:
    return datetime.now().strftime("%H:%M")


def hora(paso: str) -> str:
    return ss["asis_horas"].setdefault(paso, ahora())


# --- En que paso va la conversacion -----------------------------------------------------------
objetivo = ui.objetivo()
mes0 = ui.mes_inicio()
if not ss.get("zona_confirmada") and hay_zonas:
    paso = "zona"
elif objetivo is None:
    paso = "objetivo"
elif mes0 is None:
    paso = "mes"
else:
    paso = "listo"


# --- Acciones (callbacks) -------------------------------------------------------------------
def zona_a_mano(z):
    ui.fijar_zona(z)
    ss.pop("gps_asis", None)
    ss.pop("gps_asis_res", None)
    ss["asis_horas"]["zona_r"] = ahora()


def elegir_objetivo(k):
    ui.guardar_objetivo(k)
    if hay_estrategias:  # Mi plan y Jugar arrancan con la opcion recomendada para lo que quiere
        ss["estrategia_elegida"] = ui.recomendada_para(zid, esc, k)
    ss["asis_horas"]["objetivo_r"] = ahora()


def elegir_mes(m):
    ui.guardar_mes(m)
    ss.pop("asis_otro_mes", None)
    ss["asis_horas"]["mes_r"] = ahora()


def mes_de_lista():
    elegir_mes(ss["w_mes_asis"])


def otro_mes():
    ss["asis_otro_mes"] = True


def preguntar(clave):
    ss["chat"].append({"de": "yo", "texto": juego.PREGUNTAS[clave], "hora": ahora()})
    ss["chat"].append({"de": "bot", "texto": respuesta_libre(clave), "hora": ahora()})


def empezar_de_nuevo():
    for k in ("objetivo", "mes_inicio", "chat", "asis_horas", "asis_otro_mes", "gps_asis", "gps_asis_res"):
        ss.pop(k, None)
    ui.olvidar_zona()


# --- Textos de la conversacion ---------------------------------------------------------------
def texto_zona() -> str:
    u = ss.get("ubicacion") or {}
    como = ui.FUENTE_UBICACION.get(u.get("fuente"), "elegida por ti")
    return f"Mi finca está en la {ui.corto_zona(znombre).lower()} ({como})."


def resumen() -> str:
    """Respuesta final: zona, opcion recomendada para lo que quiere lograr y que hacer ese mes."""
    partes = [f"Listo. Tu finca está en la {znombre.lower()}."]
    k = ui.recomendada_para(zid, esc, objetivo) if hay_estrategias else None
    if k:
        atajo = juego.ATAJOS[k]
        fila = juego.notas_estrategia(carga.estrategias(), k, zid, esc)
        nota = f" (nota {ui.num(fila[objetivo], 1)} de 10)" if fila else ""
        partes.append(f"Para {ui.OBJETIVOS[objetivo].lower()} en un {juego.NOMBRE_ANIO[esc]}, tu mejor "
                      f"opción es la {k} · {atajo['nombre']}: {' → '.join(atajo['secuencia'])}{nota}.")
        mes = juego.plan_12_meses(atajo["secuencia"])[mes0]
        partes.append(f"En {mes['mes_largo']} de {ui.anio_de_inicio(mes0)}: {mes['accion']}")
    else:
        partes.append("Todavía no hay planes calculados para tu zona.")
    return " ".join(partes)


def respuesta_libre(clave: str) -> str:
    k = ss.get("estrategia_elegida") or (ui.recomendada_para(zid, esc, objetivo) if hay_estrategias else None) or "A"
    atajo = juego.ATAJOS.get(k, juego.ATAJOS["A"])
    mes = juego.plan_12_meses(atajo["secuencia"])[mes0 if mes0 is not None else hoy]
    factor = juego.factor_lluvia(imerg, esc)
    ctx = {"zona": ui.corto_zona(znombre), "zona_tipo": tipo, "escenario": esc,
           "plan_nombre": atajo["nombre"], "secuencia": atajo["secuencia"],
           "lluvias": juego.lluvias_texto(clim), "agua": juego.semaforo_agua(clim, factor),
           "factor": factor, "factor_nino": juego.factor_lluvia(imerg, "nino"),
           "mes": mes["mes_largo"], "accion": mes["accion"]}
    texto = juego.respuesta(clave, ctx)
    if clave == "lluvia":  # un hecho real del ultimo mes (no un pronostico)
        texto += " " + juego.dato_del_mes(mensual, clim, hoy)
    return texto


# --- Armar las burbujas ------------------------------------------------------------------------
burbujas = [("bot", "¡Hola! Soy el asistente de AgroShift. Te hago 3 preguntas y te armo tu plan.", hora("hola"))]
gps = None
if hay_zonas:
    burbujas.append(("bot", "1. ¿Dónde está tu finca?", hora("zona")))
    if paso == "zona":
        gps = ubicacion.resultado_gps("asis")
        if gps and gps["estado"] == "esperando":
            burbujas.append(("bot", "Buscando tu ubicación… Si el teléfono te pide permiso, toca «Permitir».", ahora()))
        elif gps and ubicacion.mensaje(gps, con_mapa=False):
            burbujas.append(("bot", ubicacion.mensaje(gps, con_mapa=False), ahora()))
    else:
        burbujas.append(("yo", texto_zona(), hora("zona_r")))
if paso != "zona":
    burbujas.append(("bot", "2. ¿Qué quieres lograr?", hora("objetivo")))
    if objetivo:
        burbujas.append(("yo", ui.OBJETIVOS[objetivo], hora("objetivo_r")))
if paso in ("mes", "listo"):
    burbujas.append(("bot", "3. ¿Desde qué mes quieres empezar tu plan?", hora("mes")))
    if mes0 is not None:
        burbujas.append(("yo", f"Desde {juego.MESES_LARGOS[mes0]}.", hora("mes_r")))
if paso == "listo":
    burbujas.append(("bot", resumen(), hora("resumen")))
    burbujas += [(m["de"], m["texto"], m["hora"]) for m in ss["chat"][-8:]]

ui.html('<div class="wa"><div class="wa-top"><div class="wa-avatar">🌱</div>'
        '<div><b>AgroShift</b><small>en línea</small></div></div><div class="wa-body">'
        + "".join(f'<div class="burbuja {de}">{escape(t)}<span class="hora">{h}</span></div>'
                  for de, t, h in burbujas)
        + "</div></div>")

# --- Botones de respuesta -------------------------------------------------------------------
with st.container(key="rapidas"):
    if paso == "zona":
        st.button("Ubicar mi finca", key="asis_gps", icon=":material/my_location:", type="primary",
                  on_click=ubicacion.pedir_gps, args=("asis",), width="stretch")
        with st.container(key="rapidas_zonas", horizontal=True, gap="small"):
            for z, n in nombres.items():
                st.button(ui.etiqueta_zona(n), key=f"asis_zona_{z}", on_click=zona_a_mano, args=(z,),
                          width="stretch")
        st.caption("En el celular la ubicación funciona cuando la app se abre con https.")
    elif paso == "objetivo":
        with st.container(key="rapidas_obj", horizontal=True, gap="small"):
            for k, n in ui.OBJETIVOS.items():
                st.button(f"{ui.ICONO_OBJETIVO[k]} {n}", key=f"asis_obj_{k}", on_click=elegir_objetivo,
                          args=(k,), width="stretch")
    elif paso == "mes":
        with st.container(key="rapidas_mes", horizontal=True, gap="small"):
            st.button(f"Este mes ({juego.MESES_LARGOS[hoy]})", key="asis_mes_hoy", type="primary",
                      on_click=elegir_mes, args=(hoy,), width="stretch")
            st.button("Elegir otro mes", key="asis_mes_otro", on_click=otro_mes, width="stretch")
        if ss.get("asis_otro_mes"):
            st.pills("Elige el mes:", options=list(range(12)), key="w_mes_asis", on_change=mes_de_lista,
                     format_func=lambda m: juego.MESES_LARGOS[m].capitalize())
    else:
        with st.container(key="rapidas_libres", horizontal=True, gap="small"):
            for clave, texto in juego.PREGUNTAS.items():
                st.button(texto, key=f"rapida_{clave}", on_click=preguntar, args=(clave,), width="stretch")
        with st.container(key="rapidas_ir", horizontal=True, gap="small"):
            st.page_link("vistas/plan.py", label="Ver mi plan", icon=":material/calendar_month:", width="stretch")
            st.page_link("vistas/comparar.py", label="Ver mis opciones", icon=":material/alt_route:",
                         width="stretch")
        st.button("Cambiar mis respuestas", key="asis_reset", icon=":material/restart_alt:",
                  on_click=empezar_de_nuevo, width="stretch")

ui.html('<div class="wa-nota">Vista previa: así funcionará por WhatsApp. Las respuestas salen de los datos '
        'reales de la app.</div>' + (f'<div class="wa-nota">{ui.confianza("recomendacion", esc)}</div>'
                                     if paso == "listo" else ""))
