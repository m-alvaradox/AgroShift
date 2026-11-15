"""Inicio: mapa de zonas y resumen rapido."""
import folium
import streamlit as st
from streamlit_folium import st_folium

from utils import carga, logica, ui

zid, znombre = ui.zona_actual()
esc = ui.escenario_actual()

st.title("Agroshift")
st.markdown("¿Qué sembrar, cuándo y dónde? Recomendaciones de rotación con datos satelitales de la NASA.")
ui.aviso_datos()

# --- Resumen en tarjetas -----------------------------------------------------------
clim = carga.climatologia()
tabla = carga.tabla_zonas().set_index("zona_id")
mejor = logica.comparar(carga.estrategias(), zid, esc, ui.pesos_actuales()).iloc[0]
info = carga.estrategias_info()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Lluvia al año", f"{ui.num(clim['lluvia_mm'].sum())} mm")
c2.metric("Meses secos", int((clim["tipo_mes"] == "seco").sum()))
c3.metric("Tu zona", f"{ui.num(tabla.loc[zid, 'area_ha'])} ha", help=znombre)
c4.metric("Recomendada", f"Estrategia {mejor['estrategia']}",
          help=info[mejor["estrategia"]]["nombre"])

# --- Mapa ----------------------------------------------------------------------------
st.subheader(f"Zonas de Daule · seleccionada: {znombre}")
geo = carga.zonas()
lons = [p[0] for f in geo["features"] for p in f["geometry"]["coordinates"][0]]
lats = [p[1] for f in geo["features"] for p in f["geometry"]["coordinates"][0]]

mapa = folium.Map(location=[sum(lats) / len(lats), sum(lons) / len(lons)],
                  zoom_start=12, tiles=None, control_scale=True)
folium.TileLayer("OpenStreetMap", name="Mapa").add_to(mapa)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Imagery", name="Satélite",
).add_to(mapa)


def estilo(feature):
    z = feature["properties"]["zona_id"]
    elegida = z == zid
    return {"fillColor": ui.COLOR_ZONA.get(z, "#888"), "color": "#222" if elegida else "#555",
            "weight": 3 if elegida else 1, "fillOpacity": 0.45 if elegida else 0.25}


folium.GeoJson(
    geo, name="Zonas", style_function=estilo,
    tooltip=folium.GeoJsonTooltip(fields=["nombre_comun", "area_ha"],
                                  aliases=["Zona", "Área (ha)"]),
).add_to(mapa)
folium.LayerControl(collapsed=True).add_to(mapa)
mapa.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

st_folium(mapa, height=460, use_container_width=True, returned_objects=[])
ui.fuente("zonas a partir de elevación SRTM e índices Landsat (K-means).")

with st.expander("¿Cómo leer este mapa?"):
    st.markdown(
        "- Cada color es una zona con un comportamiento parecido del terreno.\n"
        "- **Zona baja que se encharca:** junto al río; buena para arroz en invierno.\n"
        "- **Loma seca:** no se inunda; mejor para maíz en invierno y soya en verano.\n"
        "- Elige tu zona en la barra lateral para ver su información en las otras páginas."
    )

st.markdown("#### Sigue explorando")
a, b, c = st.columns(3)
a.page_link("vistas/clima.py", label="Ver el clima de Daule", icon="🌦️")
b.page_link("vistas/estrategias.py", label="Comparar estrategias", icon="🌱")
c.page_link("vistas/recomendacion.py", label="Ver la recomendación", icon="✅")
