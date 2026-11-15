"""Jugar: "Arma tu año". Toca una carta y luego una temporada; despues juega el año."""
import streamlit as st

from utils import carga, juego, ui

zid, znombre = ui.zona_actual()
tipo = ui.tipo_zona(znombre)
esc = ui.escenario_actual()

ss = st.session_state
ss.setdefault("casillas", [None, None, None])
ss.setdefault("carta_sel", None)
ss.setdefault("jugado", False)


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
        ss["aviso_jugar"] = "Primero toca una carta."
    ss["casillas"] = casillas


def usar_atajo(k):
    ss["casillas"] = list(juego.ATAJOS[k]["secuencia"])
    ss["carta_sel"] = None


def jugar():
    ss["jugado"] = True


def volver():
    ss["jugado"] = False


# --- Resultado ---------------------------------------------------------------------------------
if ss["jugado"] and None not in ss["casillas"]:
    casillas = ss["casillas"]
    st.title("🌾 Así te fue en el año")
    if ui.falta("climatologia_daule.csv"):
        st.button("🔁 Volver a armar", on_click=volver, key="btn_rearmar", width="stretch")
        ui.terminar_pagina()
    atajo = juego.atajo_de(casillas)
    hay_notas = atajo and carga.disponible("estrategias.csv")
    notas = juego.notas_estrategia(carga.estrategias(), atajo, zid, esc) if hay_notas else None
    cult = carga.cultivos() if carga.disponible("cultivos.csv") else None
    imerg = carga.lluvia_imerg() if carga.disponible("lluvia_imerg_daule.csv") else None
    res = juego.jugar(casillas, tipo, esc, clim=carga.climatologia(), cult=cult,
                      factor=juego.factor_lluvia(imerg, esc), notas=notas)
    real = res["con_notas"]

    ui.html(f'<p>{ui.mini_cartas(casillas)}</p>')
    izq, der = st.columns(2, gap="large")
    with izq:
        ui.html(ui.planta_svg(res["animo"]))
        ui.html(f'<div class="frase-res">{res["frase"]}</div>')
        if res["logro"]:
            ui.html(f'<div class="logro">🏅 Logro: {res["logro"]}</div>')
    with der:
        ui.html(ui.tres_barras(res["barras"]) + ui.etiqueta_fuente(real, "🧮 Estimación del juego")
                + ui.confianza("recomendacion" if real else "juego", esc))
    st.subheader("Lo que pasó en el año")
    for e in res["eventos"]:
        ui.html(f'<div class="evento {e["tipo"]}"><b>{e["meses"]}:</b> {e["texto"]}</div>')
    if real:
        st.caption("Las barras salen del cálculo de agua con datos de la NASA y de las reglas de campo "
                   "para tu zona y tu tipo de año.")
    else:
        st.caption("Esta combinación no es uno de los planes A, B o C: las barras son una "
                   "estimación del juego con la lluvia y los cultivos reales.")

    c1, c2 = st.columns(2)
    c1.button("🔁 Volver a armar", on_click=volver, key="btn_rearmar", width="stretch")
    with c2:
        st.page_link("vistas/comparar.py", label="Comparar planes", icon="⚖️", width="stretch")
    ui.terminar_pagina()

# --- Tablero -----------------------------------------------------------------------------------
st.title("🎲 Arma tu año")
st.markdown("Toca una carta y luego una temporada. Toca una temporada llena para vaciarla.")
if ss.pop("aviso_jugar", None):
    st.toast("Primero toca una carta 👇", icon="🃏")

# Cada tarjeta es un st.container(key=...) que se estiliza en estilo.py con .st-key-<clave>.
# Prefijos: "temp_" (temporadas) y "naipe_" (cartas). Los botones usan otras claves
# ("casilla_N", "tomar_X") para que el estilo de la tarjeta no se aplique al boton.
with st.container(key="sec_temporadas"):
    st.subheader("Tu terreno, temporada por temporada")
    with st.container(key="fila_temporadas"):
        cols = st.columns(3, gap="small")
        for i, (col, t) in enumerate(zip(cols, juego.TEMPORADAS)):
            c = ss["casillas"][i]
            clave = f"temp_llena_{i}_{juego.CARTAS[c]['slug']}" if c else f"temp_vacia_{i}"
            contenido = ui.carta_html(c) if c else '<div class="hueco">+</div><div class="hueco-txt">Vacía</div>'
            with col, st.container(key=clave):
                ui.html(f'<div class="cuerpo"><div class="temp-tit">{t["icono"]} {t["nombre"]}</div>'
                        f'<div class="temp-sub">{t["meses"]} · {t["detalle"]}</div>{contenido}</div>')
                st.button("Vaciar" if c else "Poner aquí", key=f"casilla_{i}", on_click=tocar_casilla,
                          args=(i,), width="stretch")

with st.container(key="sec_cartas"):
    st.subheader("Tus cartas")
    with st.container(key="fila_cartas"):
        cols = st.columns(len(juego.CARTAS), gap="small")
        for col, (nombre, info) in zip(cols, juego.CARTAS.items()):
            elegida = ss["carta_sel"] == nombre
            with col, st.container(key=f"naipe_{'sel' if elegida else 'no'}_{info['slug']}"):
                ui.html(f'<div class="cuerpo">{ui.carta_html(nombre)}</div>')
                st.button("✓ Elegida" if elegida else "Elegir", key=f"tomar_{info['slug']}",
                          on_click=tomar, args=(nombre,), type="primary" if elegida else "secondary",
                          width="stretch")

with st.container(key="sec_atajos"):
    st.subheader("O usa un atajo")
    with st.container(key="atajos", horizontal=True, gap="small"):
        for k, a in juego.ATAJOS.items():
            st.button(f"{k} · {a['nombre']}", key=f"atajo_{k}", on_click=usar_atajo, args=(k,),
                      help=" → ".join(a["secuencia"]), width="stretch")

with st.container(key="sec_jugar"):
    faltan = sum(c is None for c in ss["casillas"])
    st.button("▶️ Jugar el año", key="btn_jugar", type="primary", on_click=jugar,
              disabled=faltan > 0, width="stretch")
    if faltan:
        st.caption(f"Te falta 1 temporada por llenar." if faltan == 1
                   else f"Te faltan {faltan} temporadas por llenar.")
