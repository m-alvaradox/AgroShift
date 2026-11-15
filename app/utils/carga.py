"""
Carga de datos para la app.

Busca cada archivo de los contratos en este orden y usa el primero que exista
y tenga las columnas del contrato:
  1. app/data/          -> datos adaptados para la app (scripts/adaptar_datos.py, capas del mapa)
  2. data/processed/    -> datos reales generados por el equipo
  3. data/              -> cultivos.csv, reglas.json y estrategias_info.json de P4

Solo hay datos reales: si falta un archivo, ruta() lanza FaltaArchivo y la
pagina muestra un aviso en esa seccion (ui.falta) y sigue con el resto.
data/mock/ (scripts/generar_mock.py) queda solo para pruebas automaticas.

Los archivos originales del equipo NO se modifican: las correcciones
(nombres de cultivos, textos con tildes danadas, zona_id de las reglas)
se hacen en memoria al cargarlos.
"""
import json
import math
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
ROOT = APP_DIR.parent
CARPETAS = [APP_DIR / "data", ROOT / "data" / "processed", ROOT / "data"]

# Columnas minimas que la app necesita de cada archivo (los contratos de datos).
# Si una copia no las tiene, la app la salta y busca en la siguiente carpeta.
CONTRATOS = {
    "climatologia_daule.csv": ["mes", "nombre_mes", "lluvia_mm", "et0_mm", "tipo_mes"],
    "clima_mensual_daule.csv": ["fecha", "anio", "mes", "lluvia_mm", "et0_mm"],
    "lluvia_imerg_daule.csv": ["fecha", "lluvia_mm", "enso"],
    "series_zonas.csv": ["fecha", "zona_id", "ndvi", "ndwi", "ndmi"],
    "cultivos.csv": ["cultivo", "ciclo_dias", "tolera_inundacion"],
    "estrategias.csv": ["estrategia", "zona_id", "escenario", "agua_m3_ha",
                        "nota_agua", "nota_suelo", "nota_plagas", "nota_ingresos"],
    "zonas_daule.geojson": ["zona_id", "nombre_comun", "area_ha"],
    "estrategias_info.json": ["estrategia", "nombre", "secuencia", "evidencia",
                              "beneficios", "vacios", "riesgos"],
    "reglas.json": ["texto_campo", "evidencia"],
}

# Quien entrega cada archivo y de que fuente sale (se muestra en "Ver datos tecnicos").
FUENTES = {
    "climatologia_daule.csv": (
        "P1 (Mario)", "NASA POWER diario 2021–2026: lluvia típica (mediana) y ET0 Hargreaves "
        "(FAO-56) de cada mes. Adaptado con scripts/adaptar_datos.py."),
    "clima_mensual_daule.csv": (
        "P1 (Mario)", "NASA POWER diario 2021–2026 sumado por mes (lluvia, ET0, temperatura). "
        "Adaptado con scripts/adaptar_datos.py."),
    "lluvia_imerg_daule.csv": (
        "P1 (Mario)", "NASA GPM IMERG V07 mensual, serie de Mario 2021–2026. Tipo de año según la "
        "lluvia de diciembre a mayo de cada temporada. Adaptado con scripts/adaptar_datos.py."),
    "series_zonas.csv": (
        "P2 (Thomas)", "Landsat 8 y 9: NDVI, NDWI y NDMI mensuales de todo el recuadro de Daule. "
        "Adaptado con scripts/adaptar_datos.py."),
    "cultivos.csv": (
        "P4 (Johan)", "Ciclos de INIAP y coeficientes Kc de FAO-56 para arroz, soya y maíz duro."),
    "estrategias.csv": (
        "P1 y P4", "Balance de agua FAO-56 con NASA POWER y los años de IMERG; notas de suelo, "
        "plagas e ingresos con las reglas de P4. Calculado con scripts/calcular_estrategias.py."),
    "zonas_daule.geojson": (
        "P3 (Austin)", "Elevación y pendiente de SRTM agrupadas con K-means en 3 zonas."),
    "estrategias_info.json": (
        "P4 (Johan)", "Ficha de cada estrategia según la documentación de P4 (reglas y fuentes) "
        "y el informe de P1."),
    "reglas.json": (
        "P4 (Johan)", "Reglas de campo con su evidencia (FAO, INIAP y extensión universitaria)."),
}


class FaltaArchivo(FileNotFoundError):
    """Falta un archivo real del contrato (la pagina muestra un aviso y sigue)."""

    def __init__(self, nombre: str):
        self.nombre = nombre
        self.responsable = FUENTES.get(nombre, ("el equipo", ""))[0]
        super().__init__(f"Falta {nombre}: lo entrega {self.responsable}.")

# Nombres de cultivos de P4 (cultivos.csv) -> nombres que usa la app
# (iconos de ui.py y SECUENCIAS de logica.py).
NOMBRE_CULTIVO = {"arroz": "Arroz", "soya": "Soya", "maiz_duro_amarillo": "Maíz duro"}

# Palabras que llegan con la tilde perdida (caracter de reemplazo U+FFFD).
REPARAR = {"erosi�n": "erosión", "Erosi�n": "Erosión", "transici�n": "transición"}


# --- Lectura de texto con tildes ----------------------------------------------------

def _reparar_texto(s: str) -> str:
    """Corrige tildes danadas: 'erosi�n' -> 'erosión' y 'erosiÃ³n' -> 'erosión'."""
    if "Ã" in s or "Â" in s:  # UTF-8 leido como latin-1 (mojibake)
        try:
            s = s.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    for malo, bueno in REPARAR.items():
        s = s.replace(malo, bueno)
    return s


def _reparar(datos):
    """Aplica _reparar_texto a todos los textos de un JSON (listas y dicts anidados)."""
    if isinstance(datos, str):
        return _reparar_texto(datos)
    if isinstance(datos, list):
        return [_reparar(d) for d in datos]
    if isinstance(datos, dict):
        return {k: _reparar(v) for k, v in datos.items()}
    return datos


def leer_json_archivo(p: Path):
    """Lee JSON o GeoJSON en UTF-8 (con o sin BOM); si no es UTF-8 valido, en latin-1."""
    crudo = Path(p).read_bytes()
    try:
        texto = crudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = crudo.decode("latin-1")
    return _reparar(json.loads(texto))


def faltantes(p: Path, nombre: str) -> list[str]:
    """Columnas del contrato que le faltan al archivo (lista vacia = cumple)."""
    requeridas = CONTRATOS.get(nombre, [])
    try:
        if p.suffix == ".csv":
            columnas = set(pd.read_csv(p, nrows=0).columns)
        else:
            datos = leer_json_archivo(p)
            if p.suffix == ".geojson":
                datos = [f.get("properties", {}) for f in datos.get("features", [])]
            columnas = set(datos[0].keys()) if datos else set()
    except Exception:
        return ["(no se pudo leer el archivo)"]
    return [c for c in requeridas if c not in columnas]


@st.cache_data(show_spinner=False)
def _buscar(nombre: str, firma: tuple) -> tuple[str | None, list]:
    """Ruta a usar (None si no hay ninguna copia valida) y las copias rechazadas."""
    rechazados = []
    for carpeta in CARPETAS:
        p = carpeta / nombre
        if not p.exists():
            continue
        falta = faltantes(p, nombre)
        if falta:
            rechazados.append((p.relative_to(ROOT).as_posix(), falta))
            continue
        return str(p), rechazados
    return None, rechazados


def _firma(nombre: str) -> tuple:
    """Fechas de modificacion de las copias del archivo, para renovar la cache."""
    return tuple((c / nombre).stat().st_mtime if (c / nombre).exists() else 0 for c in CARPETAS)


def disponible(nombre: str) -> bool:
    return _buscar(nombre, _firma(nombre))[0] is not None


def ruta(nombre: str) -> Path:
    encontrado = _buscar(nombre, _firma(nombre))[0]
    if encontrado is None:
        raise FaltaArchivo(nombre)
    return Path(encontrado)


def rechazados(nombre: str) -> list:
    return _buscar(nombre, _firma(nombre))[1]


def faltan() -> list[str]:
    """Archivos del contrato que todavia no estan (lista vacia = todo real)."""
    return [n for n in CONTRATOS if not disponible(n)]


def estado_datos() -> pd.DataFrame:
    """Tabla para 'Ver datos tecnicos': archivo, de donde sale, quien lo entrega y su fuente."""
    filas = []
    for n in CONTRATOS:
        encontrado = _buscar(n, _firma(n))[0]
        responsable, fuente = FUENTES.get(n, ("", ""))
        filas.append({
            "archivo": n,
            "estado": "✅ real" if encontrado else f"❌ falta (lo entrega {responsable})",
            "usando": Path(encontrado).relative_to(ROOT).as_posix() if encontrado else "—",
            "responsable": responsable,
            "fuente": fuente,
            "copias rechazadas (faltan columnas)": "; ".join(
                f"{r}: {', '.join(f)}" for r, f in rechazados(n)),
        })
    return pd.DataFrame(filas)


# --- Lectura con cache ---------------------------------------------------------
# Se pasa la fecha de modificacion para que la cache se renueve si el archivo cambia.

@st.cache_data(show_spinner=False)
def _csv(path: str, mtime: float, fechas: tuple = ()) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=list(fechas))


@st.cache_data(show_spinner=False)
def _json(path: str, mtime: float):
    return leer_json_archivo(Path(path))


def leer_csv(nombre: str, fechas: tuple = ()) -> pd.DataFrame:
    p = ruta(nombre)
    return _csv(str(p), p.stat().st_mtime, fechas).copy()


def leer_json(nombre: str):
    p = ruta(nombre)
    return _json(str(p), p.stat().st_mtime)


# --- Un cargador por contrato --------------------------------------------------

def climatologia() -> pd.DataFrame:
    return leer_csv("climatologia_daule.csv")


def clima_mensual() -> pd.DataFrame:
    return leer_csv("clima_mensual_daule.csv", ("fecha",))


def lluvia_imerg() -> pd.DataFrame:
    return leer_csv("lluvia_imerg_daule.csv", ("fecha",))


def _a_entero(v):
    """zona_id como int; None si viene vacio, null, NaN o no es un numero."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def zonas() -> dict:
    geo = leer_json("zonas_daule.geojson")
    for f in geo["features"]:
        f["properties"]["zona_id"] = _a_entero(f["properties"].get("zona_id"))
    return geo


def tabla_zonas() -> pd.DataFrame:
    return pd.DataFrame([f["properties"] for f in zonas()["features"]])


def series() -> pd.DataFrame:
    return leer_csv("series_zonas.csv", ("fecha",))


def cultivos() -> pd.DataFrame:
    """cultivos.csv con los nombres que usa la app ('maiz_duro_amarillo' -> 'Maíz duro')."""
    df = leer_csv("cultivos.csv")
    df["cultivo"] = [NOMBRE_CULTIVO.get(str(c).strip().lower(), str(c).strip()) for c in df["cultivo"]]
    if df["tolera_inundacion"].dtype == object:
        df["tolera_inundacion"] = df["tolera_inundacion"].astype(str).str.strip().str.lower().isin(
            ["true", "1", "si", "sí", "yes"])
    return df


def estrategias() -> pd.DataFrame:
    return leer_csv("estrategias.csv")


def estrategias_info() -> dict:
    return {e["estrategia"]: e for e in leer_json("estrategias_info.json")}


def reglas() -> list[dict]:
    """Reglas con zona_id normalizado (int o None = regla general)."""
    return [{**r, "zona_id": _a_entero(r.get("zona_id"))} for r in leer_json("reglas.json")]


def reglas_zona(zona_id: int) -> list[dict]:
    """
    Reglas de una zona mas las generales. Se tratan como generales las que
    tienen zona_id null y las que apuntan a una zona que no existe en el mapa
    (por ejemplo, si la numeracion de reglas.json no coincide con la de P3).
    """
    validas = (set(tabla_zonas()["zona_id"].dropna().astype(int))
               if disponible("zonas_daule.geojson") else set())
    return [r for r in reglas()
            if r["zona_id"] is None or r["zona_id"] == zona_id or r["zona_id"] not in validas]
