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
├── streamlit_app.py     # menú de 5 botones, zona y tipo de año (arriba) y "Vista técnica"
├── vistas/              # una página por archivo
│   ├── inicio.py        # Mi finca: frase resumen, 3 semáforos y el año mes a mes
│   ├── jugar.py         # Jugar: "Arma tu año" con cartas y 3 temporadas
│   ├── comparar.py      # Comparar: planes A, B y C según lo que te importa
│   ├── plan.py          # Mi plan: una acción por mes y 3 consejos
│   ├── asistente.py     # Asistente: vista previa tipo WhatsApp (simulado)
│   ├── clima.py         # Vista técnica: de dónde sale cada dato, lluvia y tipos de año
│   ├── zonas.py         # Vista técnica: series de satélite y calendario
│   ├── estrategias.py   # Vista técnica: comparación detallada
│   └── recomendacion.py # Vista técnica: ficha, evidencia y reglas
└── utils/
    ├── carga.py         # lee los archivos de los contratos (solo datos reales)
    ├── mapa.py          # mapa tipo QGIS de Mi finca
    ├── logica.py        # puntaje, recomendación y calendario (lógica de ejemplo)
    ├── juego.py         # reglas del juego, semáforos, plan y asistente (funciones puras)
    ├── estilo.py        # todo el CSS (colores, Nunito, celular y pantalla ancha)
    └── ui.py            # estado compartido y piezas HTML (semáforo, barras, cartas, plantita)
scripts/generar_mock.py  # datos simulados SOLO para pruebas automáticas (la app no los usa)
```

La "Vista técnica" no sale en el menú: se abre con el enlace **Ver datos técnicos** al pie de Mi finca.
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
