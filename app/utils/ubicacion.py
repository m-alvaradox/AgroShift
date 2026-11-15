"""
Ubicar la finca: GPS del navegador o un toque en el mapa -> zona de zonas_daule.geojson (P3).

  buscar_zona(lat, lon)   punto dentro de un poligono (shapely). Si cae en un hueco entre
                          poligonos (rio, camino, pueblo) y hay una zona a menos de 550 m,
                          se usa esa. Si no, el punto esta fuera de las zonas de Daule.
  pedir_gps(prefijo)      callback del boton "Ubicar mi finca".
  resultado_gps(prefijo)  dibuja el componente (invisible) que pide la ubicacion al navegador
                          (streamlit_js_eval + navigator.geolocation) y devuelve el resultado.

En el celular el navegador solo da la ubicacion si la app se abre con https (o en localhost).
La ubicacion no se guarda en ningun archivo: solo vive en la sesion del navegador.
"""
from __future__ import annotations

import streamlit as st
from shapely.geometry import Point, shape
from shapely.ops import unary_union
from shapely.prepared import prep

from utils import carga, mapa, ui

CERCA_M = 550            # si el punto cae en un hueco, zona mas cercana hasta esta distancia
M_POR_GRADO = 111_320    # metros por grado cerca del ecuador

ERRORES_GPS = {
    1: ("sin_permiso", "No diste permiso para ver tu ubicación."),
    2: ("sin_gps", "El teléfono no pudo encontrar tu ubicación (sin señal de GPS)."),
    3: ("sin_gps", "La ubicación tardó demasiado en llegar."),
    0: ("sin_gps", "Este navegador no puede dar tu ubicación."),
}


@st.cache_resource(show_spinner=False)
def _zonas(ruta: str, mtime: float):
    """Zonas en grados (sin simplificar) listas para buscar puntos, y los limites de todas."""
    geo = carga.zonas()
    if mapa._en_metros(geo):
        geo = mapa._a_4326(geo)
    zonas = []
    for f in geo["features"]:
        g = shape(f["geometry"])
        if not g.is_valid:
            g = g.buffer(0)
        zonas.append((int(f["properties"]["zona_id"]), g, prep(g)))
    return zonas, unary_union([g for _, g, _ in zonas]).bounds


def buscar_zona(lat: float, lon: float) -> dict:
    """{'estado': 'dentro'|'cerca'|'fuera', 'zona_id', 'distancia_m', 'lat', 'lon'}"""
    p = carga.ruta("zonas_daule.geojson")
    zonas, _ = _zonas(str(p), p.stat().st_mtime)
    punto = Point(float(lon), float(lat))
    base = {"lat": float(lat), "lon": float(lon)}
    for zid, _, preparada in zonas:
        if preparada.covers(punto):
            return {**base, "estado": "dentro", "zona_id": zid, "distancia_m": 0}
    zid, dist = min(((z, g.distance(punto)) for z, g, _ in zonas), key=lambda t: t[1])
    metros = round(dist * M_POR_GRADO)
    if metros <= CERCA_M:
        return {**base, "estado": "cerca", "zona_id": zid, "distancia_m": metros}
    return {**base, "estado": "fuera", "zona_id": None, "distancia_m": metros}


def interpretar_gps(valor: dict) -> dict:
    """Respuesta del navegador -> resultado de buscar_zona o un error con su mensaje."""
    if not isinstance(valor, dict) or "error" in valor or "coords" not in valor:
        codigo = (valor or {}).get("error", {}).get("code", 0) if isinstance(valor, dict) else 0
        estado, mensaje = ERRORES_GPS.get(codigo, ERRORES_GPS[0])
        return {"estado": estado, "mensaje": mensaje}
    c = valor["coords"]
    res = buscar_zona(c["latitude"], c["longitude"])
    res["precision_m"] = round(float(c.get("accuracy") or 0))
    return res


def mensaje(res: dict, con_mapa: bool = True) -> str | None:
    """Texto para el productor cuando el punto no sirve (None si se encontro la zona)."""
    otra = ("Toca tu finca en el mapa o elige tu zona a mano." if con_mapa
            else "Elige tu zona con los botones de abajo.")
    if res["estado"] in ("sin_permiso", "sin_gps"):
        return f"{res['mensaje']} {otra}"
    if res["estado"] == "fuera":
        km = res["distancia_m"] / 1000
        return (f"Ese punto queda fuera de las zonas de Daule (a {ui.num(km, 1)} km de la más cercana). "
                f"Si tu finca está en Daule: {otra[0].lower()}{otra[1:]}")
    return None


def aplicar(res: dict, fuente: str) -> bool:
    """Si el resultado tiene zona, la guarda para toda la app. True si se guardo."""
    if res.get("zona_id") is None:
        return False
    ui.fijar_zona(res["zona_id"], fuente=fuente, lat=res["lat"], lon=res["lon"],
                  estado=res["estado"], distancia_m=res.get("distancia_m", 0))
    return True


# --- GPS del navegador -----------------------------------------------------------------------

def pedir_gps(prefijo: str):
    """Callback del boton: cada intento usa un componente nuevo (si no, repetiria la respuesta)."""
    ss = st.session_state
    ss[f"gps_{prefijo}"] = ss.get(f"gps_{prefijo}", 0) + 1
    ss.pop(f"gps_{prefijo}_res", None)


def resultado_gps(prefijo: str) -> dict | None:
    """
    None si no se pidio la ubicacion; {'estado': 'esperando'} mientras el navegador responde;
    si no, el resultado (con zona o con error). Con zona, la guarda y vuelve a correr la pagina.
    """
    ss = st.session_state
    intento = ss.get(f"gps_{prefijo}")
    if not intento:
        return None
    if f"gps_{prefijo}_res" in ss:
        return ss[f"gps_{prefijo}_res"]
    from streamlit_js_eval import get_geolocation
    with st.container(key=f"gpscomp_{prefijo}"):  # el iframe del componente no se ve (estilo.py)
        valor = get_geolocation(component_key=f"gps_{prefijo}_{intento}")
    if not valor:
        return {"estado": "esperando"}
    res = interpretar_gps(valor)
    ss[f"gps_{prefijo}_res"] = res
    if aplicar(res, "gps"):
        st.rerun()  # la zona nueva se aplica antes de dibujar la cabecera
    return res
