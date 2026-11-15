"""Mi finca: que hacer este mes, el anio de la finca y las senales del satelite."""
import folium
import streamlit as st
from streamlit_folium import st_folium

from utils import carga, logica, ui

zid, znombre = ui.zona_actual()
esc = ui.escenario_actual()
hoy = logica.mes_actual()

clim = carga.climatologia()
cult = carga.cultivos()
info = carga.estrategias_info()
mejor = logica.comparar(carga.estrategias(), zid, esc, ui.pesos_actuales()).iloc[0]
e = info[mejor["estrategia"]]
plan = logica.plan(mejor["estrategia"], clim, cult)

st.title(f"{ui.icono_zona(znombre)} Tu finca en la {znombre.lower()}")
ui.aviso_datos()

# --- Lo que hay que hacer ahora -----------------------------------------------------------
ui.tarjeta_accion(logica.accion_del_mes(plan[0], hoy), hoy)

# --- El anio de la finca (el elemento principal) -----------------------------------------
st.subheader("El año de tu finca")
st.markdown(f"Con la opción recomendada, **{e['nombre'].lower()}**, tu año se vería así:")
filas = [(f"Año {i + 1}" if len(plan) > 1 else "Tu plan", meses) for i, meses in enumerate(plan)]
ui.franja_anual(clim, filas, mes_hoy=hoy)
st.page_link("vistas/estrategias.py", label="Comparar con otras opciones", icon="🌱")

# --- Senales del satelite -----------------------------------------------------------------
st.subheader("Lo que muestran los satélites")
serie = carga.series()
sz = serie[serie["zona_id"] == zid]
if sz.empty:
    sz = serie[serie["zona_id"] == 0]
c1, c2, c3 = st.columns(3)
with c1:
    ui.tarjeta_senal("lluvia", logica.senal_lluvia(carga.clima_mensual(), clim))
with c2:
    ui.tarjeta_senal("verdor", logica.senal_verdor(sz))
with c3:
    ui.tarjeta_senal("agua", logica.senal_agua(sz))
ui.fuente("lluvia de NASA POWER; verdor y agua de Landsat 8 y 9.")

# --- Mapa ---------------------------------------------------------------------------------
with st.expander("🗺️ Ver las zonas en el mapa"):
    geo = carga.zonas()
    lons = [p[0] for f in geo["features"] for p in f["geometry"]["coordinates"][0]]
    lats = [p[1] for f in geo["features"] for p in f["geometry"]["coordinates"][0]]
    mapa = folium.Map(location=[sum(lats) / len(lats), sum(lons) / len(lons)],
                      zoom_start=12, tiles=None, control_scale=True)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery", name="Satélite").add_to(mapa)
    folium.TileLayer("OpenStreetMap", name="Mapa").add_to(mapa)

    def estilo(feature):
        z = feature["properties"]["zona_id"]
        elegida = z == zid
        return {"fillColor": ui.COLOR_ZONA.get(z, "#888"), "color": "#fff" if elegida else "#333",
                "weight": 4 if elegida else 1, "fillOpacity": 0.5 if elegida else 0.2}

    folium.GeoJson(geo, name="Zonas", style_function=estilo,
                   tooltip=folium.GeoJsonTooltip(fields=["nombre_comun", "area_ha"],
                                                 aliases=["Zona", "Hectáreas"])).add_to(mapa)
    folium.LayerControl(collapsed=True).add_to(mapa)
    mapa.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
    st_folium(mapa, height=420, use_container_width=True, returned_objects=[])
    st.caption("La zona elegida se ve resaltada. Las zonas salen de la altura del terreno "
               "y de cómo se ve el campo desde el satélite.")
