# Agroshift: app base (Streamlit)

## Correr en tu computadora

```powershell
pip install -r requirements.txt
python scripts/adaptar_datos.py         # clima, satélite e IMERG del equipo -> app/data/
python scripts/calcular_estrategias.py  # estrategias.csv (FAO-56 + reglas de P4)
python scripts/preparar_capas.py        # capas del mapa (elevación y pendiente)
streamlit run app/streamlit_app.py
```

## Cómo están organizados los archivos

```
app/
├── streamlit_app.py     # menú (Inicio + 6 botones), zona y tipo de año (arriba) y "Vista técnica"
├── vistas/              # una página por archivo
│   ├── portada.py       # Inicio: AGROSHIFT y 6 tarjetas grandes (cada tarjeta lleva a su página)
│   ├── inicio.py        # Mi finca: "¿Dónde está tu finca?" (GPS, mapa o a mano), zona, mapa y semáforos
│   ├── jugar.py         # Jugar: mesa de casino, cartas A, B y C y marcador "Así te iría"
│   ├── comparar.py      # Mis opciones: "TUS OPCIONES SON" por objetivo y las 3 opciones en detalle
│   ├── plan.py          # Mi plan: recorrido de la abejita mes a mes y 3 consejos
│   ├── asistente.py     # Asistente: 3 preguntas tipo WhatsApp y un resumen (simulado)
│   ├── dashboard.py     # Dashboard: tu zona en gráficos
│   ├── clima.py         # Vista técnica: de dónde sale cada dato, lluvia y tipos de año
│   ├── zonas.py         # Vista técnica (Mi campo): series de satélite, fotos de cada mes y calendario
│   ├── estrategias.py   # Vista técnica: comparación detallada, cultivos y terreno
│   └── recomendacion.py # Vista técnica: ficha, evidencia y reglas
└── utils/
    ├── carga.py         # lee los archivos de los contratos (solo datos reales)
    ├── mapa.py          # mapa tipo QGIS de Mi finca (con el punto de la finca)
    ├── ubicacion.py     # "Ubicar mi finca": GPS del navegador o toque en el mapa -> zona (shapely)
    ├── logica.py        # puntaje, recomendación y calendario (lógica de ejemplo)
    ├── juego.py         # reglas del juego, semáforos, plan y asistente (funciones puras)
    ├── estilo.py        # todo el CSS (colores, Nunito, celular y pantalla ancha)
    └── ui.py            # estado compartido y piezas HTML (semáforo, barras, cartas, plantita)
scripts/generar_mock.py  # datos simulados SOLO para pruebas automáticas (la app no los usa)
```

Las respuestas del Asistente (zona, qué quiere lograr y mes de inicio) se guardan en
`st.session_state` y las usan Mi finca, Mis opciones, Mi plan y Jugar, así no se vuelve a preguntar.
"Ubicar mi finca" pide la ubicación al navegador (`streamlit_js_eval`); en el celular solo funciona si
la app se abre con **https** (o en localhost). La ubicación no se guarda en ningún archivo.

La "Vista técnica" no sale en el menú: se abre con el enlace **Ver datos técnicos** al pie de Mi finca
o desde la portada.
Ahí está la tabla **De dónde sale cada dato** (archivo, responsable y fuente).
Lo que todavía no sale de los datos está marcado con `# TODO: reemplazar con datos reales` en
`utils/juego.py` y en pantalla dice **Estimación de AgroShift**.

## De dónde saca los datos

Solo datos reales. Para cada archivo, la app usa el primero que encuentre con las columnas del contrato:

1. `app/data/`: datos adaptados que se suben con la app (para Coolify)
2. `data/processed/`: datos reales del equipo
3. `data/`: `cultivos.csv`, `reglas.json` y `estrategias_info.json` de P4

Si falta un archivo, la sección que lo usa muestra un aviso ("Falta X: lo entrega P1") y el
resto de la página sigue funcionando.

Los escenarios **Año muy lluvioso / normal / seco** salen de la lluvia GPM IMERG (serie de P1,
2021–2026): la temporada de diciembre a mayo más lluviosa, la más seca y las demás.

## Cambios a los contratos (avisar al equipo)

- `estrategias.csv` agrega al final las columnas `nota_agua`, `nota_suelo`, `nota_plagas` y `nota_ingresos` (0 a 10). La app calcula el `puntaje` con las prioridades del usuario. Las entregan P1 (agua) y P4 (las otras tres).
- Archivo nuevo de P4: `data/estrategias_info.json`, con el nombre, la secuencia, la descripción, la evidencia, los beneficios, los vacíos y los riesgos de cada estrategia.

## Desplegar en Coolify

Build Pack: **Dockerfile** · Puerto: **8501**
