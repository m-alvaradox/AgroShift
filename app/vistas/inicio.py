"""
Mi finca.

La primera vez: el paso "¿Donde esta tu finca?" (GPS del navegador, tocar el mapa o elegir
la zona a mano). Despues: la zona en grande, el mapa centrado en la finca, los 3 semaforos
de la zona (lluvia, verdor y agua en el terreno), el año mes a mes y el acceso al juego.
"""
from datetime import date

import streamlit as st
from streamlit_folium import st_folium

from utils import carga, juego, logica, mapa, ubicacion, ui

ss = st.session_state
hoy = date.today().month - 1
hay_zonas = carga.disponible("zonas_daule.geojson")


def zona_a_mano(z):
    ui.fijar_zona(z)


def cambiar_ubicacion():
    ui.olvidar_zona()
    for k in ("gps_finca", "gps_finca_res", "clic_finca", "clic_finca_res"):
        ss.pop(k, None)


# --- Paso 1: ubicar la finca (hasta que el productor lo responda) -------------------------------
if hay_zonas and not ss.get("zona_confirmada"):
    st.title("Mi finca")
    nombres = dict(zip(carga.tabla_zonas()["zona_id"].astype(int), carga.tabla_zonas()["nombre_comun"]))
    with st.container(key="paso_ubicar"):
        ui.html('<div class="ubicar-tit">¿Dónde está tu finca?</div>'
                '<p class="ubicar-txt">Con tu ubicación vemos en qué zona de Daule está tu finca: zona baja, '
                'ladera o loma. Solo se usa para eso y no se guarda.</p>')
        st.button("Ubicar mi finca", key="btn_gps", icon=":material/my_location:", type="primary",
                  on_click=ubicacion.pedir_gps, args=("finca",), width="stretch")
        gps = ubicacion.resultado_gps("finca")
        if gps and gps["estado"] == "esperando":
            st.info("Buscando tu ubicación… Si el navegador te pide permiso, toca «Permitir».",
                    icon=":material/my_location:")
        elif gps and ubicacion.mensaje(gps):
            st.warning(ubicacion.mensaje(gps), icon=":material/location_off:")
        st.caption("En el celular la ubicación funciona cuando la app se abre con https.")

        ui.html('<div class="ubicar-o">o elige tu zona a mano</div>')
        with st.container(key="ubicar_zonas", horizontal=True, gap="small"):
            for z, n in nombres.items():
                st.button(ui.etiqueta_zona(n), key=f"finca_zona_{z}", on_click=zona_a_mano, args=(z,),
                          width="stretch")

    st.subheader("O toca tu finca en el mapa")
    clic = st_folium(mapa.construir(ui.zona_actual()[0]), height=430, use_container_width=True,
                     returned_objects=["last_clicked", "last_object_clicked"], key="mapa_ubicar")
    # un toque sobre una zona llega en last_object_clicked; uno fuera de las zonas, en last_clicked
    nuevos = [c for c in ((clic or {}).get("last_object_clicked"), (clic or {}).get("last_clicked"))
              if c and c != ss.get("clic_finca")]
    punto = nuevos[0] if nuevos else None
    if punto:
        ss["clic_finca"] = punto
        res = ubicacion.buscar_zona(punto["lat"], punto["lng"])
        ss["clic_finca_res"] = res
        if ubicacion.aplicar(res, "mapa"):
            st.rerun()
    if ss.get("clic_finca_res") and ubicacion.mensaje(ss["clic_finca_res"]):
        st.warning(ubicacion.mensaje(ss["clic_finca_res"]), icon=":material/location_off:")
    st.caption("Los colores son las zonas de Daule. Acerca el mapa con los dedos y toca donde está tu finca.")
    ui.terminar_pagina()

# --- Paso 2: la finca ubicada ------------------------------------------------------------------
zid, znombre = ui.zona_actual()
tipo = ui.tipo_zona(znombre)
esc = ui.escenario_actual()
u = ss.get("ubicacion") or {}
punto = (u["lat"], u["lon"]) if u.get("lat") is not None and u.get("zona_id") == zid else None

hay_clima = carga.disponible("climatologia_daule.csv")
hay_satelite = carga.disponible("series_zonas.csv")
clim = carga.climatologia() if hay_clima else None
mensual = carga.clima_mensual() if carga.disponible("clima_mensual_daule.csv") else None
serie = ui.serie_zona(zid) if hay_satelite else ui.serie_vacia()
imerg = carga.lluvia_imerg() if carga.disponible("lluvia_imerg_daule.csv") else None
factor = juego.factor_lluvia(imerg, esc)

st.title("Mi finca")
if hay_zonas:
    como = ui.FUENTE_UBICACION.get(u.get("fuente"), "elegida por ti")
    cerca = (f" · a {u['distancia_m']} m del borde de la zona" if u.get("estado") == "cerca" else "")
    with st.container(key=f"zona_grande_{tipo}"):
        ui.html(f'<div class="zg"><div class="zg-ico">{ui.icono_zona(znombre)}</div><div>'
                f'<div class="zg-tit">Tu finca está en la {znombre.lower()}</div>'
                f'<div class="zg-sub">Ubicada {como}{cerca}</div></div></div>')
        st.button("Cambiar ubicación", key="btn_cambiar_ubicacion", icon=":material/edit_location_alt:",
                  on_click=cambiar_ubicacion)

izq, der = st.columns([3, 2], gap="large")
with izq:
    if not ui.falta("zonas_daule.geojson"):
        # returned_objects=[]: mover o tocar el mapa no recarga la pagina
        st_folium(mapa.construir(zid, punto), height=460, use_container_width=True, returned_objects=[],
                  key="mapa_finca")
        st.caption(("El punto rojo es tu finca. " if punto else "")
                   + f"Resaltada: {ui.etiqueta_zona(znombre)}. Con el botón de capas (arriba a la "
                   "derecha) puedes ver la elevación o la pendiente.")

with der:
    st.subheader("Cómo está tu zona")
    if mensual is not None and clim is not None:
        ui.html(ui.semaforo("Lluvia", "🌧️", ui.semaforo_de_senal(logica.senal_lluvia(mensual, clim)),
                            True, conf="agua"))
    else:
        ui.falta("clima_mensual_daule.csv", "climatologia_daule.csv")
    if not ui.falta("series_zonas.csv"):
        ui.html(ui.semaforo("Verdor", "🌱", ui.semaforo_de_senal(logica.senal_verdor(serie)), True,
                            conf="verdor"))
        ui.html(ui.semaforo("Agua en el terreno", "💧", ui.semaforo_de_senal(logica.senal_agua_zona(serie)),
                            True, conf="agua_terreno"))

if clim is not None:
    ui.html(f'<div class="resumen">{juego.frase_finca(tipo, esc, clim, factor)}</div>')

c1, c2 = st.columns(2, gap="large")
with c1:
    st.subheader("Tu año, mes a mes")
    if not ui.falta("climatologia_daule.csv"):
        celdas = "".join(
            f'<div class="mes12 {m["tipo"]}{" hoy" if i == hoy else ""}"><span>{m["icono"]}</span>{m["mes"]}</div>'
            for i, m in enumerate(juego.meses_12(clim)))
        ui.html(f'<div class="meses12">{celdas}</div>'
                '<div class="leyenda"><span>🌧️ Llueve fuerte</span><span>🌦️ Algo de lluvia</span>'
                f'<span>☀️ Seco</span></div>{ui.etiqueta_fuente(True)}')
with c2:
    st.write("")
    with st.container(key="cta_jugar"):
        ui.html('<div class="cta-tit">Juega tu temporada</div>'
                '<p>Elige una carta y mira cómo te iría en el año.</p>')
        st.page_link("vistas/jugar.py", label="Jugar ahora", icon=":material/playing_cards:", width="stretch")

# --- Pie --------------------------------------------------------------------------------------
st.page_link("vistas/estrategias.py", label="Conoce los cultivos y el terreno de cada zona", icon=":material/eco:")
st.page_link("vistas/clima.py", label="Ver datos técnicos: de dónde sale cada dato", icon=":material/science:")
