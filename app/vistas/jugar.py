"""
Jugar (estilo casino): elige una carta (plan A, B o C) y juega la temporada.

No es una prediccion: antes del resultado se dice desde que mes y con que tipo de año
(registrado por la NASA entre 2021 y 2026) se hace la simulacion. El mes sale del Asistente;
si no se respondio, se pregunta aqui con el mes actual por defecto.
Las barras de A, B y C salen de estrategias.csv; una jugada libre (cultivo por temporada) es
una estimacion del juego.
"""
from datetime import date

import streamlit as st

from utils import carga, juego, ui

zid, znombre = ui.zona_actual()
tipo = ui.tipo_zona(znombre)
esc = ui.escenario_actual()
hoy = date.today().month - 1

ss = st.session_state
ss.setdefault("casillas", [None, None, None])
ss.setdefault("carta_sel", None)
ss.setdefault("jugado", False)


def mes_simulacion() -> int:
    m = ui.mes_inicio()
    return m if m is not None else ss.get("w_mes_jugar", ss.get("mes_jugar_def", hoy))


def honestidad() -> str:
    m = mes_simulacion()
    return (f'<div class="honesto"><b>Simulación, no predicción.</b> Desde {juego.MESES_LARGOS[m]} de '
            f'{ui.anio_de_inicio(m)}, si el año fuera {ui.NOMBRE_ESC[esc].replace("Año ", "").lower()} '
            'como los registrados por la NASA entre 2021 y 2026.</div>')


# --- Acciones (callbacks) ----------------------------------------------------------------------
def tomar(nombre):
    ss["carta_sel"] = None if ss["carta_sel"] == nombre else nombre


def tocar_casilla(i):
    casillas = list(ss["casillas"])
    if casillas[i]:
        casillas[i] = None
    elif ss["carta_sel"]:
        casillas[i] = ss["carta_sel"]
    else:
        ss["aviso_jugar"] = "Primero toca un cultivo."
    ss["casillas"] = casillas


def usar_atajo(k):
    ss["casillas"] = list(juego.ATAJOS[k]["secuencia"])
    ss["carta_sel"] = None
    ss["estrategia_elegida"] = k


def jugar():
    if ui.mes_inicio() is None:  # el mes que dejo en la pregunta queda guardado para toda la app
        ui.guardar_mes(mes_simulacion())
    ss["jugado"] = True


def volver():
    ss["jugado"] = False


def cambiar_mes():
    ss["mes_jugar_def"] = ui.mes_inicio()  # la pregunta vuelve a salir con ese mes elegido
    ss.pop("mes_inicio", None)


st.title("Comienza el juego: ¡elige tu sembrío!")

# --- Resultado ---------------------------------------------------------------------------------
if ss["jugado"] and None not in ss["casillas"]:
    casillas = ss["casillas"]
    if ui.falta("climatologia_daule.csv"):
        st.button("Volver a la mesa", on_click=volver, key="btn_rearmar", width="stretch")
        ui.terminar_pagina()
    atajo = juego.atajo_de(casillas)
    hay_notas = atajo and carga.disponible("estrategias.csv")
    notas = juego.notas_estrategia(carga.estrategias(), atajo, zid, esc) if hay_notas else None
    cult = carga.cultivos() if carga.disponible("cultivos.csv") else None
    imerg = carga.lluvia_imerg() if carga.disponible("lluvia_imerg_daule.csv") else None
    res = juego.jugar(casillas, tipo, esc, clim=carga.climatologia(), cult=cult,
                      factor=juego.factor_lluvia(imerg, esc), notas=notas)
    real = res["con_notas"]
    # los eventos empiezan en la temporada del mes de inicio
    t0 = mes_simulacion() // 4
    eventos = sorted(res["eventos"], key=lambda e: (e["temporada"] - t0) % 3)

    with st.container(key="mesa_res"):
        ui.html(honestidad())
        nombre = f"{atajo} · {juego.ATAJOS[atajo]['nombre']}" if atajo else "Tu jugada"
        ui.html(f'<div class="mesa-tit">Así te iría · {nombre}</div><p>{ui.mini_cartas(casillas)}</p>')
        ui.html(ui.marcador(res["barras"], res["palabras"]))
        izq, der = st.columns([2, 3], gap="large")
        with izq:
            ui.html(ui.planta_svg(res["animo"]))
        with der:
            ui.html(f'<div class="frase-res">{res["frase"]}</div>')
            if res["logro"]:
                ui.html(f'<div class="logro">Logro: {res["logro"]}</div>')
            for e in eventos:
                ui.html(f'<div class="evento {e["tipo"]}"><b>{e["meses"]}:</b> {e["texto"]}</div>')
        ui.html(ui.etiqueta_fuente(real, "🧮 Estimación del juego")
                + ui.confianza("recomendacion" if real else "juego", esc))
        if real:
            st.caption("El marcador sale del cálculo de agua con datos de la NASA y de las reglas de campo "
                       "para tu zona y tu tipo de año.")
        else:
            st.caption("Esta jugada no es una de las cartas A, B o C: el marcador es una estimación del "
                       "juego con la lluvia y los cultivos reales.")
        c1, c2 = st.columns(2)
        c1.button("Volver a la mesa", on_click=volver, key="btn_rearmar", icon=":material/replay:",
                  width="stretch")
        with c2:
            st.page_link("vistas/comparar.py", label="Ver mis opciones", icon=":material/alt_route:",
                         width="stretch")
    ui.terminar_pagina()

# --- Mesa de juego ---------------------------------------------------------------------------------
if ss.pop("aviso_jugar", None):
    st.toast("Primero toca un cultivo")
elegida = juego.atajo_de(ss["casillas"]) if None not in ss["casillas"] else None

with st.container(key="mesa"):
    ui.html(f'<div class="mesa-sub">Cada carta es una forma de sembrar tu {ui.corto_zona(znombre).lower()} '
            'durante el año. Elige una y juega la temporada.</div>')
    with st.container(key="fila_naipes"):
        cols = st.columns(len(juego.ATAJOS), gap="small")
        for col, (k, a) in zip(cols, juego.ATAJOS.items()):
            with col, st.container(key=f"carta_{k}"):
                ui.html(ui.naipe_html(k, a["nombre"], a["secuencia"], elegida == k,
                                      elegida is not None and elegida != k))
                st.button("Elegida" if elegida == k else "Elegir", key=f"atajo_{k}", on_click=usar_atajo,
                          args=(k,), type="primary" if elegida == k else "secondary", width="stretch")

    if ui.mes_inicio() is None:
        st.selectbox("¿Desde qué mes empiezas?", options=list(range(12)), index=ss.get("mes_jugar_def", hoy), key="w_mes_jugar",
                     format_func=lambda m: juego.MESES_LARGOS[m].capitalize())
    else:
        with st.container(key="mesa_mes", horizontal=True, vertical_alignment="center", gap="small"):
            ui.html(f'<div class="mesa-mes">Empiezas en <b>{juego.MESES_LARGOS[ui.mes_inicio()]}</b></div>')
            st.button("Cambiar mes", key="btn_cambiar_mes", on_click=cambiar_mes, width="content")
    ui.html(honestidad())
    faltan = sum(c is None for c in ss["casillas"])
    st.button("Jugar la temporada", key="btn_jugar", type="primary", on_click=jugar, icon=":material/casino:",
              disabled=faltan > 0, width="stretch")
    if faltan:
        st.caption("Elige una carta para jugar.")

# --- Jugada libre: un cultivo por temporada ----------------------------------------------------------
with st.expander("Arma tu propia jugada (un cultivo por temporada)"):
    st.markdown("Toca un cultivo y luego una temporada. Toca una temporada llena para vaciarla.")
    with st.container(key="sec_temporadas"):
        with st.container(key="fila_temporadas"):
            cols = st.columns(3, gap="small")
            for i, (col, t) in enumerate(zip(cols, juego.TEMPORADAS)):
                c = ss["casillas"][i]
                clave = f"temp_llena_{i}_{juego.CARTAS[c]['slug']}" if c else f"temp_vacia_{i}"
                contenido = ui.carta_html(c) if c else '<div class="hueco">+</div><div class="hueco-txt">Vacía</div>'
                with col, st.container(key=clave):
                    ui.html(f'<div class="cuerpo"><div class="temp-tit">{t["nombre"]}</div>'
                            f'<div class="temp-sub">{t["meses"]} · {t["detalle"]}</div>{contenido}</div>')
                    st.button("Vaciar" if c else "Poner aquí", key=f"casilla_{i}", on_click=tocar_casilla,
                              args=(i,), width="stretch")
    with st.container(key="sec_cartas"):
        with st.container(key="fila_cartas"):
            cols = st.columns(len(juego.CARTAS), gap="small")
            for col, (nombre, info) in zip(cols, juego.CARTAS.items()):
                sel = ss["carta_sel"] == nombre
                with col, st.container(key=f"naipe_{'sel' if sel else 'no'}_{info['slug']}"):
                    ui.html(f'<div class="cuerpo">{ui.carta_html(nombre)}</div>')
                    st.button("✓ Elegido" if sel else "Elegir", key=f"tomar_{info['slug']}",
                              on_click=tomar, args=(nombre,), type="primary" if sel else "secondary",
                              width="stretch")
