# Agroshift: app base (Streamlit)

## Correr en tu computadora

```powershell
pip install -r requirements.txt
python scripts/generar_mock.py        # crea los datos de prueba en data/mock/
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
│   ├── clima.py         # Vista técnica: lluvia, evaporación y El Niño/La Niña
│   ├── zonas.py         # Vista técnica: series de satélite y calendario
│   ├── estrategias.py   # Vista técnica: comparación detallada
│   └── recomendacion.py # Vista técnica: ficha, evidencia y reglas
└── utils/
    ├── carga.py         # lee los archivos de los contratos (real primero, prueba después)
    ├── logica.py        # puntaje, recomendación y calendario (lógica de ejemplo)
    ├── juego.py         # reglas del juego, semáforos, plan y asistente (funciones puras)
    ├── estilo.py        # todo el CSS (colores, Nunito, celular y pantalla ancha)
    └── ui.py            # estado compartido y piezas HTML (semáforo, barras, cartas, plantita)
scripts/generar_mock.py  # datos de prueba con las columnas de los contratos
```

La "Vista técnica" no sale en el menú: se abre con el enlace **Ver datos técnicos** al pie de Mi finca.
Lo que todavía no sale de los datos está marcado con `# TODO: reemplazar con datos reales` en
`utils/juego.py` y en pantalla dice **Simulación de ejemplo**.

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
