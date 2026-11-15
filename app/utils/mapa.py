"""
Mapa tipo QGIS para "Mi finca": capas base, zonas de P3, capas raster opcionales,
control de capas, herramientas (pantalla completa, medir, coordenadas) y leyenda.

Las zonas se preparan en memoria (sin tocar data/processed/):
  1. si las coordenadas vienen en metros UTM, se reproyectan a EPSG:4326;
  2. se calculan los limites recorriendo TODAS las coordenadas (tambien MultiPolygon);
  3. se simplifican con shapely para que el mapa cargue rapido.
Los PNG de las capas raster los crea scripts/preparar_capas.py en app/data/capas/.
"""
import math
import re
from html import escape

import folium
import streamlit as st
from branca.element import MacroElement
from folium import plugins
from folium.raster_layers import ImageOverlay
from jinja2 import Template
from shapely import set_precision
from shapely.geometry import mapping, shape

from utils import carga, ui

CAPAS_DIR = carga.APP_DIR / "data" / "capas"
AOI = carga.ROOT / "data" / "aoi_daule.geojson"
TOLERANCIA = 0.0005      # grados (~55 m): suficiente para ver las zonas a zoom 9-14
EPSG_DAULE = 32717       # UTM 17 Sur, el que usa P3 para sus GeoTIFF
ZOOM_INICIAL, ZOOM_MIN, ZOOM_MAX = 11, 9, 18
MARGEN = 0.35            # grados que se puede mover el mapa fuera de Daule

ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"


# --- Geometria ------------------------------------------------------------------------

def puntos(coords):
    """Todos los [x, y] de un Polygon o MultiPolygon (cualquier nivel de anidado)."""
    if len(coords) and isinstance(coords[0], (int, float)):
        yield coords
    else:
        for c in coords:
            yield from puntos(c)


def limites(geo: dict) -> list | None:
    """[[sur, oeste], [norte, este]] de todas las coordenadas, o None si no son validos."""
    try:
        xs, ys = [], []
        for f in geo["features"]:
            for p in puntos(f["geometry"]["coordinates"]):
                xs.append(float(p[0]))
                ys.append(float(p[1]))
        oeste, este, sur, norte = min(xs), max(xs), min(ys), max(ys)
    except (KeyError, TypeError, ValueError, IndexError):
        return None
    validos = (all(math.isfinite(v) for v in (oeste, este, sur, norte))
               and -180 <= oeste < este <= 180 and -90 <= sur < norte <= 90)
    return [[sur, oeste], [norte, este]] if validos else None


def _en_metros(geo: dict) -> bool:
    """True si las coordenadas no caben en grados (p. ej. UTM: x ~ 600000, y ~ 9800000)."""
    for f in geo["features"]:
        for p in puntos(f["geometry"]["coordinates"]):
            return abs(p[0]) > 180 or abs(p[1]) > 90
    return False


def _epsg_origen(geo: dict) -> int:
    """EPSG declarado en el GeoJSON (campo 'crs'); si no hay, UTM 17 Sur."""
    nombre = str(geo.get("crs", {}).get("properties", {}).get("name", ""))
    m = re.search(r"(\d{4,5})\s*$", nombre)
    return int(m.group(1)) if m else EPSG_DAULE


def _a_4326(geo: dict) -> dict:
    from rasterio.warp import transform_geom  # solo hace falta si las zonas vienen en UTM
    origen = f"EPSG:{_epsg_origen(geo)}"
    feats = [{**f, "geometry": transform_geom(origen, "EPSG:4326", f["geometry"])}
             for f in geo["features"]]
    return {"type": "FeatureCollection", "features": feats}


def _texto(valor, decimales: int, unidad: str) -> str:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "sin dato"
    return "sin dato" if math.isnan(v) else f"{ui.num(v, decimales)} {unidad}".strip()


@st.cache_data(show_spinner=False)
def _preparar(ruta: str, mtime: float) -> tuple[dict, list | None, bool]:
    """Zonas en EPSG:4326, simplificadas y con textos para el popup; limites; si se reproyecto."""
    geo = carga.zonas()
    reproyectado = _en_metros(geo)
    if reproyectado:
        geo = _a_4326(geo)
    lim = limites(geo)
    feats = []
    for f in geo["features"]:
        p = dict(f["properties"])
        nombre = str(p.get("nombre_comun", ""))
        p.update({
            "tipo": ui.tipo_zona(nombre),
            "zona_txt": ui.etiqueta_zona(nombre),
            "area_txt": _texto(p.get("area_ha"), 0, "ha"),
            "elev_txt": _texto(p.get("elevacion"), 1, "m"),
            "pend_txt": _texto(p.get("pendiente"), 1, "°"),
        })
        geom = shape(f["geometry"]).simplify(TOLERANCIA, preserve_topology=True)
        geom = set_precision(geom, 1e-5)  # 5 decimales (~1 m): menos texto en el HTML
        feats.append({"type": "Feature", "properties": p, "geometry": mapping(geom)})
    return {"type": "FeatureCollection", "features": feats}, lim, reproyectado


def zonas_mapa() -> tuple[dict, list, str]:
    """
    Zonas listas para el mapa, encuadre [[sur, oeste], [norte, este]] y de donde sale el
    encuadre. Si las zonas reales no estan o sus limites no sirven, usa data/aoi_daule.geojson.
    """
    p = carga.ruta("zonas_daule.geojson")
    geo, lim, _ = _preparar(str(p), p.stat().st_mtime)
    if lim:
        return geo, lim, "zonas"
    aoi = limites(carga.leer_json_archivo(AOI)) if AOI.exists() else None
    return geo, aoi or lim or [[-1.93, -80.08], [-1.78, -79.93]], "aoi"


def capas_raster() -> dict:
    """Capas creadas por scripts/preparar_capas.py (vacio si todavia no se corrio)."""
    indice = CAPAS_DIR / "capas.json"
    if not indice.exists():
        return {}
    capas = carga.leer_json_archivo(indice)
    return {k: c for k, c in capas.items() if (CAPAS_DIR / c["png"]).exists()}


# --- Leyenda --------------------------------------------------------------------------

class Leyenda(MacroElement):
    """Leyenda abajo a la izquierda; muestra la barra de la capa raster que este encendida."""
    _template = Template("""
        {% macro html(this, kwargs) %}{% endmacro %}
        {% macro script(this, kwargs) %}
        (function() {
            var mapa = {{ this._parent.get_name() }};
            var ley = L.control({position: "bottomleft"});
            ley.onAdd = function() {
                var div = L.DomUtil.create("div", "leyenda-mapa");
                div.innerHTML = {{ this.contenido|tojson }};
                L.DomEvent.disableClickPropagation(div);
                return div;
            };
            ley.addTo(mapa);
            function mostrar(nombre, si) {
                document.querySelectorAll(".leyenda-mapa [data-capa]").forEach(function(el) {
                    if (el.getAttribute("data-capa") === nombre) { el.style.display = si ? "block" : "none"; }
                });
            }
            mapa.on("overlayadd", function(e) { mostrar(e.name, true); });
            mapa.on("overlayremove", function(e) { mostrar(e.name, false); });
        })();
        {% endmacro %}
    """)

    def __init__(self, contenido: str):
        super().__init__()
        self._name = "Leyenda"
        self.contenido = contenido


ESTILO_LEYENDA = (
    "<style>.leyenda-mapa{background:rgba(255,255,255,.92);padding:8px 10px;border-radius:8px;"
    "font:13px/1.35 'Atkinson Hyperlegible',sans-serif;color:#1F4D2B;box-shadow:0 1px 4px rgba(0,0,0,.3);"
    "max-width:210px}.leyenda-mapa b{display:block;margin:2px 0 4px}"
    ".leyenda-mapa i{display:inline-block;width:14px;height:14px;border-radius:3px;margin-right:6px;"
    "vertical-align:-2px;border:1px solid #555}.leyenda-mapa .rampa{height:10px;border-radius:3px;"
    "margin:3px 0 1px;border:1px solid #999}.leyenda-mapa .ext{display:flex;justify-content:space-between;"
    "font-size:12px}.leyenda-mapa [data-capa]{display:none;margin-top:8px}</style>")


def _leyenda_html(tipos: list[str], rasters: dict) -> str:
    filas = "".join(f'<div><i style="background:{ui.COLOR_ZONA[t]}"></i>{ui.ICONO_ZONA[t]} '
                    f'{escape(ui.CORTO_ZONA[t])}</div>' for t in tipos)
    barras = "".join(
        f'<div data-capa="{escape(c["nombre"])}"><b>{escape(c["nombre"])}</b>'
        f'<div class="rampa" style="background:linear-gradient(90deg,{",".join(c["colores"])})"></div>'
        f'<div class="ext"><span>{ui.num(c["min"], 1)} {escape(c["unidad"])}</span>'
        f'<span>{ui.num(c["max"], 1)} {escape(c["unidad"])}</span></div></div>'
        for c in rasters.values())
    return f"{ESTILO_LEYENDA}<b>Zonas</b>{filas}{barras}"


# --- Mapa -----------------------------------------------------------------------------

def construir(zid: int) -> folium.Map:
    geo, (sw, ne), _ = zonas_mapa()
    (sur, oeste), (norte, este) = sw, ne
    mapa = folium.Map(
        location=[(sur + norte) / 2, (oeste + este) / 2], zoom_start=ZOOM_INICIAL,
        min_zoom=ZOOM_MIN, max_zoom=ZOOM_MAX, tiles=None, control_scale=True,
        max_bounds=True, min_lat=sur - MARGEN, max_lat=norte + MARGEN,
        min_lon=oeste - MARGEN, max_lon=este + MARGEN,
        **{"minZoom": ZOOM_MIN, "maxBoundsViscosity": 0.8})  # opciones directas de L.map

    # Capas base (solo una a la vez). Con tiles=None, folium no aplica min_zoom al mapa:
    # Leaflet lo toma de las capas base, por eso va tambien aqui.
    folium.TileLayer(ESRI, attr="Esri World Imagery", name="Satélite", min_zoom=ZOOM_MIN,
                     max_zoom=ZOOM_MAX, max_native_zoom=17).add_to(mapa)
    folium.TileLayer("OpenStreetMap", name="Mapa", show=False, min_zoom=ZOOM_MIN,
                     max_zoom=ZOOM_MAX).add_to(mapa)

    # Capas raster (apagadas): en su propio panel, debajo de las zonas (overlayPane = 400)
    rasters = capas_raster()
    if rasters:
        folium.map.CustomPane("rasters", z_index=350).add_to(mapa)
    for c in rasters.values():
        ImageOverlay(str(CAPAS_DIR / c["png"]), bounds=c["limites"], name=c["nombre"], opacity=0.6,
                     show=False, pixelated=False, interactive=False, pane="rasters").add_to(mapa)

    # Zonas, coloreadas por tipo; la elegida, resaltada. Las zonas de P3 son muy fragmentadas
    # (muchos huecos), por eso el borde es fino y el resalte va sobre todo en el relleno.
    def estilo(feature):
        p = feature["properties"]
        elegida = p.get("zona_id") == zid
        color = ui.COLOR_ZONA.get(p.get("tipo"), "#888")
        return {"fillColor": color, "color": "#FFFFFF" if elegida else color,
                "weight": 1.6 if elegida else 0.6, "fillOpacity": 0.6 if elegida else 0.35}

    folium.GeoJson(
        geo, name="Zonas", style_function=estilo,
        highlight_function=lambda f: {"weight": 3, "color": "#F9A825"},
        tooltip=folium.GeoJsonTooltip(fields=["zona_txt"], labels=False),
        popup=folium.GeoJsonPopup(
            fields=["zona_txt", "area_txt", "elev_txt", "pend_txt"],
            aliases=["Zona", "Superficie", "Elevación promedio", "Pendiente promedio"]),
    ).add_to(mapa)

    # Herramientas
    plugins.Fullscreen(position="topleft", title="Pantalla completa",
                       title_cancel="Salir de pantalla completa").add_to(mapa)
    plugins.MeasureControl(position="topleft", primary_length_unit="meters",
                           secondary_length_unit="kilometers", primary_area_unit="hectares",
                           secondary_area_unit="sqmeters").add_to(mapa)
    plugins.MousePosition(position="bottomright", separator="  ·  ", prefix="Lat / Lon:",
                          num_digits=5, empty_string="").add_to(mapa)
    folium.LayerControl(position="topright", collapsed=False).add_to(mapa)

    tipos = [t for t in ("baja", "ladera", "loma", "transicion")
             if any(f["properties"]["tipo"] == t for f in geo["features"])]
    Leyenda(_leyenda_html(tipos, rasters)).add_to(mapa)

    mapa.fit_bounds([sw, ne])
    return mapa


def tamano_html(mapa: folium.Map) -> int:
    """Bytes del HTML del mapa (para revisar que siga liviano)."""
    return len(mapa.get_root().render().encode("utf-8"))
