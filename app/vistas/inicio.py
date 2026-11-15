"""Mi finca: frase resumen, 3 semaforos, el año mes a mes, el mapa y acceso al juego."""
from datetime import date

import streamlit as st
from streamlit_folium import st_folium

from utils import carga, juego, mapa, ui

zid, znombre = ui.zona_actual()
tipo = ui.tipo_zona(znombre)
esc = ui.escenario_actual()
hoy = date.today().month - 1

hay_clima = carga.disponible("climatologia_daule.csv")
hay_satelite = carga.disponible("series_zonas.csv")
clim = carga.climatologia() if hay_clima else None
serie = ui.serie_zona(zid) if hay_satelite else ui.serie_vacia()
imerg = carga.lluvia_imerg() if carga.disponible("lluvia_imerg_daule.csv") else None
factor = juego.factor_lluvia(imerg, esc)

st.title(f"{ui.icono_zona(znombre)} Mi finca")
if clim is not None:
    ui.html(f'<div class="resumen">{juego.frase_finca(tipo, esc, clim)}</div>')

izq, der = st.columns(2, gap="large")

with izq:
    st.subheader("¿Cómo está tu finca?")
    if not ui.falta("climatologia_daule.csv"):
        if esc != "normal" and imerg is None:
            ui.falta("lluvia_imerg_daule.csv")
        ui.html(ui.semaforo("Agua", "💧", juego.semaforo_agua(clim, factor), True))
    if not ui.falta("series_zonas.csv"):
        ui.html(ui.semaforo("Suelo", "🌱", juego.semaforo_suelo(serie), True))
    ui.html(ui.semaforo("Riesgo de inundación", "🌊", juego.semaforo_inundacion(tipo, esc, serie),
                        hay_satelite))

with der:
    st.subheader("Tu año, mes a mes")
    if not ui.falta("climatologia_daule.csv"):
        celdas = "".join(
            f'<div class="mes12 {m["tipo"]}{" hoy" if i == hoy else ""}"><span>{m["icono"]}</span>{m["mes"]}</div>'
            for i, m in enumerate(juego.meses_12(clim)))
        ui.html(f'<div class="meses12">{celdas}</div>'
                '<div class="leyenda"><span>🌧️ Llueve fuerte</span><span>🌦️ Algo de lluvia</span>'
                f'<span>☀️ Seco</span></div>{ui.etiqueta_fuente(True)}')

    st.write("")
    with st.container(key="cta_jugar"):
        ui.html('<div class="cta-tit">🎲 Juega tu temporada</div>'
                '<p>Elige qué sembrar en cada temporada y mira cómo te iría en el año.</p>')
        st.page_link("vistas/jugar.py", label="Jugar ahora", icon="▶️", width="stretch")

# --- Mapa de las zonas (siempre visible) -----------------------------------------------------
st.subheader("🗺️ Tu zona en el mapa")
if not ui.falta("zonas_daule.geojson"):
    # returned_objects=[]: mover o tocar el mapa no recarga la pagina
    st_folium(mapa.construir(zid), height=520, use_container_width=True, returned_objects=[],
              key="mapa_finca")
    st.caption(f"Resaltada: {ui.etiqueta_zona(znombre)}. Toca una zona para ver sus datos. Con el "
               "botón de capas (arriba a la derecha) puedes ver la elevación o la pendiente.")

# --- Pie --------------------------------------------------------------------------------------
st.page_link("vistas/clima.py", label="Ver datos técnicos: de dónde sale cada dato", icon="🔬")
