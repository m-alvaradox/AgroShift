"""Mi finca: frase resumen, 3 semaforos, el año mes a mes y acceso al juego."""
from datetime import date

import streamlit as st
from streamlit_folium import st_folium

from utils import carga, juego, mapa, ui

zid, znombre = ui.zona_actual()
tipo = ui.tipo_zona(znombre)
esc = ui.escenario_actual()
hoy = date.today().month - 1

clim = carga.climatologia()
serie = ui.serie_zona(zid)
factor = juego.factor_lluvia(carga.lluvia_imerg(), esc)

# Que datos son reales y cuales todavia de prueba
clima_real = not carga.es_mock("climatologia_daule.csv")
anio_real = esc == "normal" or not carga.es_mock("lluvia_imerg_daule.csv")
satelite_real = not carga.es_mock("series_zonas.csv")

st.title(f"{ui.icono_zona(znombre)} Mi finca")
ui.html(f'<div class="resumen">{juego.frase_finca(tipo, esc, clim)}</div>')

izq, der = st.columns(2, gap="large")

with izq:
    st.subheader("¿Cómo está tu finca?")
    ui.html(ui.semaforo("Agua", "💧", juego.semaforo_agua(clim, factor), clima_real and anio_real))
    ui.html(ui.semaforo("Suelo", "🌱", juego.semaforo_suelo(serie), satelite_real))
    ui.html(ui.semaforo("Riesgo de inundación", "🌊", juego.semaforo_inundacion(tipo, esc, serie),
                        satelite_real))

with der:
    st.subheader("Tu año, mes a mes")
    celdas = "".join(
        f'<div class="mes12 {m["tipo"]}{" hoy" if i == hoy else ""}"><span>{m["icono"]}</span>{m["mes"]}</div>'
        for i, m in enumerate(juego.meses_12(clim)))
    ui.html(f'<div class="meses12">{celdas}</div>'
            '<div class="leyenda"><span>🌧️ Llueve fuerte</span><span>🌦️ Algo de lluvia</span>'
            f'<span>☀️ Seco</span></div>{ui.etiqueta_fuente(clima_real)}')

    st.write("")
    with st.container(key="cta_jugar"):
        ui.html('<div class="cta-tit">🎲 Juega tu temporada</div>'
                '<p>Elige qué sembrar en cada temporada y mira cómo te iría en el año.</p>')
        st.page_link("vistas/jugar.py", label="Jugar ahora", icon="▶️", width="stretch")

# --- Mapa de las zonas (siempre visible) -----------------------------------------------------
st.subheader("🗺️ Tu zona en el mapa")
# returned_objects=[]: mover o tocar el mapa no recarga la pagina
st_folium(mapa.construir(zid), height=520, use_container_width=True, returned_objects=[],
          key="mapa_finca")
st.caption(f"Resaltada: {ui.etiqueta_zona(znombre)}. Toca una zona para ver sus datos. Con el "
           "botón de capas (arriba a la derecha) puedes ver la elevación o la pendiente.")

# --- Pie --------------------------------------------------------------------------------------
if carga.archivos_mock():
    st.caption("🧪 Algunos datos todavía son de ejemplo mientras el equipo termina los reales.")
st.page_link("vistas/clima.py", label="Ver datos técnicos", icon="🔬")
