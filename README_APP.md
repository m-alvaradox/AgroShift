# Agroshift: app base (Streamlit)

## Correr en tu computadora

```powershell
pip install -r requirements-app.txt
python scripts/generar_mock.py        # crea los datos de prueba en data/mock/
streamlit run app/streamlit_app.py
```

## Cómo están organizados los archivos

```
app/
├── streamlit_app.py     # menú de páginas y barra lateral (zona, tipo de año, prioridades)
├── vistas/              # una página por archivo
│   ├── inicio.py        # mapa de zonas y resumen
│   ├── clima.py         # lluvia frente a evaporación y años El Niño/La Niña
│   ├── zonas.py         # series de NDVI/NDWI/NDMI y calendario de siembra
│   ├── estrategias.py   # comparación de las 3 estrategias
│   └── recomendacion.py # ficha recomendada y reglas para el campo
└── utils/
    ├── carga.py         # lee los archivos de los contratos (real primero, prueba después)
    ├── logica.py        # puntaje, recomendación y calendario (lógica de ejemplo)
    └── ui.py            # colores, avisos, glosario y formato de números
scripts/generar_mock.py  # datos de prueba con las columnas de los contratos
```

## De dónde saca los datos

Para cada archivo, la app usa el primero que encuentre:

1. `app/data/`: datos reales que se suben con la app (para Coolify)
2. `data/processed/`: datos reales del equipo
3. `data/`: `cultivos.csv`, `reglas.json` y `estrategias_info.json` de P4
4. `data/mock/`: datos de prueba

Mientras haya archivos de prueba, la app muestra un aviso amarillo.

## Cambios a los contratos (avisar al equipo)

- `estrategias.csv` agrega al final las columnas `nota_agua`, `nota_suelo`, `nota_plagas` y `nota_ingresos` (0 a 10). La app calcula el `puntaje` con las prioridades del usuario. Las entregan P1 (agua) y P4 (las otras tres).
- Archivo nuevo de P4: `data/estrategias_info.json`, con el nombre, la secuencia, la descripción, la evidencia, los beneficios, los vacíos y los riesgos de cada estrategia.

## Desplegar en Coolify

Build Pack: **Dockerfile** · Puerto: **8501**
