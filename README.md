# AgroShift

**Qué sembrar, cuándo y dónde en Daule (Guayas, Ecuador), con datos de la NASA.**

AgroShift es una app web para productores de arroz de Daule. Compara tres formas de usar el terreno durante el año y ayuda a decidir cuál conviene en cada zona y en cada tipo de año:

| Plan | Lluvias | Seca |
|---|---|---|
| A · Siempre arroz | Arroz | Arroz |
| B · Arroz y soya | Arroz | Soya |
| C · Rotación de 2 años | Arroz (año 1) · Maíz duro (año 2) | Soya |

Para cada zona (baja que se encharca, ladera y loma) y cada tipo de año (seco, normal o muy lluvioso), la app muestra:
- cuánta agua de riego pide cada plan;
- cómo afecta al suelo, a las plagas y a los ingresos;
- cuándo sembrar;
- qué dice el satélite sobre el campo mes a mes.

Proyecto del NASA Space Apps Challenge 2026, reto *Field Shift*.

## Datos de la NASA que usa

| Fuente | Para qué | Resolución | Script |
|---|---|---|---|
| **NASA POWER** (diario) | Lluvia, temperatura y agua que se evapora (ET0) | ~50 km | `scripts/descargar_nasa_power.py`, `scripts/clima_historico_power.py` |
| **GPM IMERG V07** (mensual) | Lluvia de cada mes y tipo de año | ~10 km | extracción en Google Earth Engine (P1) |
| **Landsat 8 y 9** (Collection 2 Level 2) | Verdor (NDVI), agua en el terreno (NDWI), humedad (NDMI) y fotos de cada mes | 30 m | `scripts/landsat_gee.py`, `scripts/series_por_zona.py` |
| **SRTM** | Altura, pendiente y zonas de terreno | 30 m | `scripts/procesar_srtm.py` y zonificación de P3 |

Otras fuentes gratuitas:
- coeficientes de cultivo de la FAO (FAO-56) y ciclos del INIAP;
- Sentinel-2 de la ESA, solo como relleno en los compuestos de P2;
- mapas de fondo de OpenStreetMap y Esri.

Período de los datos: noviembre 2021 a octubre 2026.

## Instalar

Requiere Python 3.11 o 3.12.

```bash
git clone <url-del-repo> AgroShift
cd AgroShift
python -m venv .venv
# Windows: .venv\Scripts\activate    ·    Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## Correr todo, en orden

**1. Datos crudos.** Este paso es opcional: los resultados ya están en el repo. Necesita internet y, para Earth Engine, haber corrido `earthengine authenticate`.

```bash
python scripts/descargar_nasa_power.py          # P1: clima diario de NASA POWER
python scripts/landsat_gee.py --proyecto TU-PROYECTO-GEE   # P2: índices Landsat del recuadro
python scripts/procesar_srtm.py                 # P3: altura y pendiente (SRTM)
python scripts/series_por_zona.py               # Landsat por zona y fotos de cada mes
                                                 #   (proyecto: --proyecto o variable EE_PROYECTO)
```

**2. Preparar los datos de la app** (rápido y sin internet):

```bash
python scripts/adaptar_datos.py          # clima, satélite e IMERG -> app/data/
python scripts/calcular_estrategias.py   # agua de cada plan (FAO-56) y notas con las reglas de P4
python scripts/preparar_capas.py         # capas de elevación y pendiente del mapa
python scripts/revisar_datos.py          # revisa que los 9 archivos de la app estén y cumplan su formato
```

**3. Abrir la app:**

```bash
streamlit run app/streamlit_app.py
```

Se abre en `http://localhost:8501`. Funciona en computadora y en celular.

## Cómo está organizado

```
app/                 la app (Streamlit)
  streamlit_app.py   menú, zona y tipo de año, pie con el aviso técnico
  vistas/            una página por archivo (portada, Mi finca, Jugar, Mis opciones, Mi plan,
                     Asistente, Dashboard y la vista técnica: Clima, Mi campo, Estrategias,
                     Recomendación)
  utils/             carga de datos, lógica, mapa, estilo y piezas de la interfaz
  data/              datos adaptados para la app
  static/meses/      fotos del satélite de cada mes (color real y verdor)
data/                datos del equipo (cultivos, reglas, zonas, clima, satélite)
scripts/             scripts para descargar y procesar los datos
src/                 módulo de clima y agua de P1
docs/                metodología, informe de P1 y auditoría
```

La app solo usa datos reales. Si falta un archivo, la sección que lo usa avisa ("Falta X: lo entrega P1") y el resto de la página sigue funcionando. Los detalles de la app están en [README_APP.md](README_APP.md) y el estado de cada requisito en [docs/auditoria.md](docs/auditoria.md).

## Equipo

| Rol | Responsable | Entrega |
|---|---|---|
| P1 | Mario | Clima y agua: NASA POWER, IMERG y balance hídrico |
| P2 | Thomas | Imágenes Landsat |
| P3 | Austin | Terreno y zonas (SRTM, K-means) |
| P4 | Johan | Cultivos y reglas agronómicas |
| P5 | Andrés | App e integración |

> AgroShift ayuda a decidir, pero no reemplaza la experiencia del productor ni la de un técnico agrícola.
