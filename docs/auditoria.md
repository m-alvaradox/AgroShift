# Auditoría de AgroShift (rama Develop)

- **Primera auditoría:** 15 de noviembre de 2026, commit `0ff7194`: 14 ✅ · 16 🟡 · 3 ❌.
- **Esta actualización:** 15 de noviembre de 2026, después de las correcciones (series por zona, imágenes mensuales, cultivos, confianza y aviso técnico).
- **Base:** lo acordado por el equipo en `README_APP.md`, `docs/metodologia_p1.md`, `docs/INFORME_moduloP1.md`, la documentación de P4 (`docs/reglas_agronomicas.md` y `docs/fuentes_catalogo_cultivos.md` en `origin/p4-reglas`) y la lista de requisitos RF/RNF y del reto.

## Resumen

| Sección | ✅ Cumple | 🟡 Parcial | ❌ No cumple |
|---|:-:|:-:|:-:|
| A. Requerimientos funcionales (10) | 8 | 2 | 0 |
| B. Requerimientos no funcionales (8) | 5 | 3 | 0 |
| C. Requisitos del reto (6) | 3 | 3 | 0 |
| D. Datos (6) | 4 | 2 | 0 |
| E. Calidad (3) | 2 | 1 | 0 |
| **Total (33)** | **22** | **11** | **0** |

Antes eran 14 ✅ · 16 🟡 · 3 ❌. **Ya no queda ningún ❌.** Los tres huecos grandes quedaron resueltos:
- **Series de satélite por zona**, con `pct_agua`. La zona baja muestra 8 meses con agua; la loma, ninguno.
- **Fotos de cada mes** en color real y verdor, con galería.
- **Ficha de cultivos** y terreno por zona.

Lo que sigue en 🟡 depende sobre todo de datos del equipo: suelo, más años de lluvia, K-means con Landsat y validar los supuestos.

### Cambios en esta corrección

1. **Alerta inventada eliminada.** El Asistente ya no muestra "Se viene una semana muy lluviosa…". Ahora abre con un hecho real: "En octubre de 2026 llovieron 574 mm; lo normal para ese mes es 17 mm. En noviembre normalmente llueven 7 mm" (`app/utils/juego.py:402`, `dato_del_mes`). También se cambiaron otras frases que sonaban a pronóstico:
   - "Este año puede llover más/menos de lo normal" ahora dice cuánto más o menos llovió de verdad en ese tipo de año (`juego.py:263`, `comparacion_anio`);
   - "Va a faltar agua" ahora es "Llueve menos de la mitad de lo que se evapora: falta agua";
   - "Si viene un año muy lluvioso, lloverá mucho…" ahora cita el dato IMERG.
2. **Series por zona** con el nuevo `scripts/series_por_zona.py`:
   - Usa Earth Engine y las mismas funciones de Landsat de P2 (`landsat_gee.py`): Collection 2 Level 2, nubes por QA_PIXEL y mediana mensual.
   - Calcula NDVI, NDWI y NDMI de noviembre 2021 a octubre 2026 en cada polígono de P3 (`reduceRegions`, 30 m).
   - Agrega `pct_agua` (% de la zona con NDWI > 0) y `cobertura_pct` (% de la zona sin nubes).
   - `app/data/series_zonas.csv` trae las zonas 0, 1, 2 y 3. La zona 0 es la serie de P2 sin cambios, más su `pct_agua`.
   - Los meses con menos del 10 % de la zona sin nubes se tratan como "sin foto" (`scripts/adaptar_datos.py:103`).
3. **Fotos de cada mes** en `app/static/meses/AAAA_MM_color.png` y `AAAA_MM_ndvi.png`:
   - 47 meses con foto y 13 "sin imagen por nubes", entre ellos enero de 2024.
   - Las 94 miniaturas pesan 6,2 MB (PNG con paleta de 128 colores).
   - "Mi campo" tiene "Tu campo mes a mes" (selector de mes, color y verdor lado a lado, y lluvia, verdor y agua de ese mes) y una galería de los últimos 12 meses (`app/vistas/zonas.py:65-140`).
4. **Cultivos y suelo:** "Conoce los cultivos" y "El terreno de cada zona" en "Opciones" (`app/vistas/estrategias.py:93` y `:131`), enlazados desde "Mi finca".
5. **Aviso del técnico** al pie de todas las páginas (`app/streamlit_app.py:91-93`). Las páginas que terminan antes ya no usan `st.stop()`, sino `ui.terminar_pagina()` (`app/utils/ui.py:180`), para que el pie siempre salga.
6. **Lenguaje:** las vistas del productor ya no muestran P1–P4, AGR-0xx, FAO-56, Hargreaves ni K-means; `data/estrategias_info.json` se reescribió en lenguaje simple. Las referencias técnicas siguen en "Ver datos técnicos".
7. **Confianza** alta, media o baja con su porqué (`app/utils/ui.py:197-225`) en:
   - los 3 semáforos de "Mi finca";
   - el plan recomendado (Comparar, Mi plan, Recomendación, Jugar y Asistente);
   - las 6 tarjetas del Dashboard;
   - los gráficos de "Mi campo", el calendario y las fichas.
   - En un año muy lluvioso o seco, la recomendación baja a "baja", porque cada tipo de año sale de una sola temporada.
8. **README.md principal** (106 líneas): qué es, cómo instalar, scripts en orden y fuentes de la NASA.
9. **Velocidad:**
   - Las capas raster del mapa se sirven desde `app/static/capas/`: el HTML del mapa bajó de 2,0 MB a 0,49 MB (`app/utils/mapa.py:226`, `.streamlit/config.toml:18`).
   - Las zonas preparadas quedan en caché en disco (`persist="disk"`).

---

## A. Requerimientos funcionales

| ID | Requisito | Estado | Evidencia | Qué falta |
|---|---|:-:|---|---|
| RF-01 | Mapa con 2 o 3 zonas y su nombre común | ✅ | `app/vistas/inicio.py` y `app/utils/mapa.py`: 3 zonas de P3 con color, nombre y ventana al tocarlas. | — |
| RF-02 | Lluvia y evaporación de cada mes, clasificado como lluvioso, transición o seco | ✅ | `app/vistas/clima.py:26-31`; la clasificación sale de `scripts/adaptar_datos.py`. | Es la mediana de 5 años (ver C, patrones históricos). |
| RF-03 | Series mensuales de 5 años de NDVI, NDWI, NDMI y lluvia **por zona** | ✅ | `app/data/series_zonas.csv`: zonas 1, 2 y 3 (56 meses con al menos una imagen Landsat cada una) más la zona 0. Hecho con `scripts/series_por_zona.py`. "Mi campo" y el Dashboard muestran la serie de la zona elegida. | La lluvia es la misma en las 3 zonas (un solo dato de NASA POWER para Daule). |
| RF-04 | Mejores meses para sembrar cada cultivo en cada zona | ✅ | El calendario (`app/utils/logica.py`, `calendario`) marca riesgo con el agua **medida en cada zona** (`meses_con_agua`, umbral del 5 %, `logica.py:15`). En la zona baja avisa "Soya: en mayo hubo agua en el terreno en 2 de los últimos años"; en la loma marca el riesgo del arroz. | Los meses de siembra salen del clima, igual en las 3 zonas; un calendario validado por zona sería de P4. |
| RF-05 | Características de cada cultivo y del suelo local | 🟡 | Hay ficha por cultivo en lenguaje simple: días del ciclo, agua por ciclo, si aguanta el encharcamiento y en qué zona conviene (`app/vistas/estrategias.py:93`). Del terreno se muestra la altura y la pendiente de cada zona, con la línea "Todavía no tenemos datos de suelo de cada finca" (`:131`). | **Datos de suelo** (textura, drenaje, fertilidad) por zona: el módulo `src/suelo.py` de P3 no está en Develop. |
| RF-06 | Comparar las 3 estrategias con su agua en m³/ha por zona | ✅ | `data/processed/estrategias.csv` (27 filas); `app/vistas/estrategias.py` y el Dashboard. | Validar los supuestos (D6). |
| RF-07 | Reordenar las estrategias según las prioridades | ✅ | `st.pills` en `comparar.py:19` y `estrategias.py:23`; puntaje en `logica.py` (`puntajes`). | — |
| RF-08 | Cada estrategia en año normal, muy lluvioso y seco | 🟡 | Hay tres escenarios, definidos por la lluvia IMERG de cada temporada. Muy lluvioso es solo 2024-2025 y seco solo 2021-2022. La app ahora lo dice con "Confianza baja · cada tipo de año sale de una sola temporada real". | Más años de IMERG (P1) para tener varios años por tipo. |
| RF-09 | Recomendar con evidencia, beneficios, vacíos y riesgos | ✅ | `app/vistas/recomendacion.py`, con la confianza junto a la recomendación. | P4 debe validar la ficha `data/estrategias_info.json`. |
| RF-10 | Reglas para el campo con el dato que las respalda | ✅ | `app/vistas/recomendacion.py`: cada regla de P4 trae su evidencia. | Las reglas son generales y su evidencia es bibliográfica. |

## B. Requerimientos no funcionales

| ID | Requisito | Estado | Evidencia | Qué falta |
|---|---|:-:|---|---|
| RNF-01 | Se abre en computadora y celular (390 px) | ✅ | En Chrome, las 10 páginas a 1400 px y 390 px **sin scroll horizontal**. Fotos y galería en 3 columnas en celular. | — |
| RNF-02 | Cada página carga en menos de 5 s | 🟡 | Ver la tabla de abajo. Con el servidor ya en marcha, todas las páginas cargan en 3 a 5,3 s (promedio 4,2 s). La **primera visita después de arrancar el servidor** tarda 8,6 s: 2,3 s son la importación de librerías y cerca de 1 s la lectura de las zonas, una sola vez por arranque. El mapa pasó de 2,0 a 0,49 MB. | Bajar el arranque en frío (precalentar la caché al desplegar) y los casos de 5,1–5,3 s (Comparar, Mi finca). |
| RNF-03 | Lenguaje simple; términos explicados | ✅ | Revisión automática de los textos que ve el productor (Mi finca, Jugar, Comparar, Mi plan, Asistente y Dashboard): **0** apariciones de P1–P5, AGR-0xx, FAO-56, Hargreaves, K-means ni de las claves "nino"/"nina". NDVI, NDWI y ET0 se explican como "verdor", "agua en el terreno" y "agua que se evapora". | Las páginas de "Ver datos técnicos" conservan las siglas a propósito. |
| RNF-04 | Solo datos gratuitos y públicos | ✅ | NASA POWER, GPM IMERG, Landsat 8 y 9, SRTM, NOAA RONI y publicaciones de FAO e INIAP; mapas de OpenStreetMap y Esri. | Earth Engine pide una cuenta gratuita. |
| RNF-05 | Imágenes recortadas; ningún archivo de más de ~50 MB | ✅ | El archivo más grande sigue siendo `pendiente_daule.tif` (3,7 MB). Las miniaturas mensuales pesan 96 KB como máximo, 6,2 MB en total, y cubren solo el recuadro de las zonas. `app/static` suma 7,2 MB. | — |
| RNF-06 | Cada número muestra su fuente y nivel de confianza | 🟡 | Confianza (🟢 alta, 🟡 media, 🔴 baja) con su porqué en las señales y recomendaciones (ver "Cambios", punto 7). La fuente se muestra en todos los gráficos. | Falta la confianza en cada gráfico de la vista técnica (Clima, Estrategias) y en los gráficos del Dashboard. Hoy está en sus tarjetas y en las señales. |
| RNF-07 | Aviso de que no reemplaza al técnico | ✅ | Pie de todas las páginas (`app/streamlit_app.py:91-93`). AppTest lo encontró en el 100 % de las corridas, también en el resultado del juego y con archivos faltantes. | — |
| RNF-08 | Reproducible (funciones, requirements, README) | 🟡 | **Lo que mejoró:** hay `README.md` principal con la cadena completa, y `series_por_zona.py` tiene funciones y `main()`. Antes ya se comprobó que, al clonar el repo, `README_APP.md` levanta la app y regenera exactamente los mismos archivos. **Lo que falta:** 15 scripts del equipo siguen siendo código suelto; falta el script que extrajo IMERG de Earth Engine; el código de zonificación de P3 no está en Develop. | Los scripts que faltan (P1, P3) y pasar los scripts a funciones (cada dueño). |

**Tiempo de carga real** (Chrome; segundos hasta que la página terminó y sus gráficos están dibujados; sesión nueva en cada medición):

| Página | PC, 1ª | PC, 2ª | Celular, 1ª | Celular, 2ª |
|---|--:|--:|--:|--:|
| Mi finca | **8,6** (arranque en frío) | **5,1** | 3,7 | 4,0 |
| Jugar | 3,3 | 3,4 | 3,4 | 4,2 |
| Comparar | 4,1 | **5,2** | 4,3 | **5,3** |
| Mi plan | 4,1 | 4,2 | 4,5 | 4,2 |
| Asistente | 3,1 | 4,1 | 3,2 | 4,2 |
| Clima | 3,5 | 4,7 | 4,3 | 4,6 |
| Mi campo | 4,2 | 4,1 | 4,6 | 4,0 |
| Estrategias | 4,9 | 4,4 | 3,6 | 4,6 |
| Recomendación | 3,2 | 3,4 | 3,5 | 4,3 |
| Dashboard | **5,5** | 4,6 | 4,4 | 4,4 |

## C. Requisitos del reto (mentor)

| Requisito | Estado | Evidencia | Qué falta |
|---|:-:|---|---|
| Una región y 3 cultivos locales con datos locales | 🟡 | Daule, con arroz, soya y maíz duro; ficha de cada cultivo en la app. | Los parámetros son de referencia (FAO, INIAP); faltan rendimientos, precios y suelos locales. |
| Patrones históricos | 🟡 | 5 años (noviembre 2021 a octubre 2026). | Correr la climatología de 35 años (`scripts/clima_historico_power.py`) y mostrarla. |
| Zonas con K-means usando elevación e índices de Landsat | 🟡 | P3 usó K-means solo con elevación y pendiente. Ahora hay índices Landsat por zona, que se pueden usar para volver a agrupar. | Que P3 vuelva a correr K-means agregando NDVI y NDWI e integre su código en Develop. |
| Series de tiempo de los últimos 5 años | ✅ | 60 meses de lluvia y evaporación; verdor, agua y humedad por zona en los 56 meses con al menos una imagen Landsat. | — |
| Imágenes de cada mes para ver qué meses son mejores para cada cultivo | ✅ | "Tu campo mes a mes": selector de los 60 meses con color real y verdor lado a lado, más la lluvia, el verdor y el agua de la zona ese mes. Galería de los últimos 12 meses. | — |
| Datos de la NASA usados explícitamente | ✅ | NASA POWER, GPM IMERG, Landsat 8 y 9 y SRTM se nombran en las fuentes, en la portada del Dashboard y en el pie. | — |

## D. Datos

### Los contratos de `app/utils/carga.py`

| Archivo | ¿Real? | Viene de | Período | Valores raros |
|---|:-:|---|---|---|
| `climatologia_daule.csv` | ✅ | P1, NASA POWER (adaptado) | 12 meses, calculados con 5 años | Ninguno. |
| `clima_mensual_daule.csv` | ✅ | P1, NASA POWER | nov 2021 a oct 2026 | Ninguno. |
| `lluvia_imerg_daule.csv` | ✅ | P1, IMERG de Mario (adaptado) | nov 2021 a oct 2026 | Noviembre de 2021 sin tipo de año. Octubre de 2026 con 585 mm, confirmado por NASA POWER (574 mm). |
| `series_zonas.csv` | ✅ | P2 (zona 0) y `series_por_zona.py` (zonas 1–3), con Landsat 8 y 9 | nov 2021 a oct 2026 | **Ahora con zonas.** `pct_agua` máximo: zona baja 15,7 %, ladera 9,3 %, loma 1,2 %. Meses sin foto por nubes: 11 a 14 de 60 por zona. El NDWI promedio sigue negativo, por eso se usa `pct_agua`. |
| `cultivos.csv` | ✅ | P4 | — | `agua_*` es un alias de la ETc (ver la auditoría anterior). |
| `estrategias.csv` | ✅ | P5, con datos de P1 y reglas de P4 | temporadas 2021-22 a 2025-26 | Depende de supuestos sin validar (D6). |
| `zonas_daule.geojson` | ✅ | P3 | — | **Nuevo:** las hectáreas de la tabla de P3 no coinciden con sus polígonos. La ladera tiene 17.097 ha en la tabla y 6.816 ha en el mapa; la zona baja, 45.302 y 56.089 ha. Las hectáreas se calcularon antes de unir los parches chicos (`sieve_px=50`). |
| `estrategias_info.json` | ✅ | P5, con la documentación de P4 y P1 | — | Reescrita en lenguaje simple; falta que P4 la valide. |
| `reglas.json` | ✅ | P4 | — | 5 reglas generales. |

Archivos nuevos que no son contratos:
- `data/processed/indices_por_zona.csv`: 224 filas, sin datos para los 4 meses sin ninguna imagen Landsat.
- `app/data/meses_satelite.csv`: 60 meses (estado de cada foto).
- `app/static/meses/`: 94 PNG.

### Coherencia y datos inventados

| # | Revisión | Estado | Evidencia | Qué falta |
|---|---|:-:|---|---|
| D1 | Los contratos son reales | ✅ | `scripts/revisar_datos.py`: 9 de 9. | — |
| D2 | Mismas zonas (`zona_id`) | ✅ | El GeoJSON, `estrategias.csv` y ahora `series_zonas.csv` usan 1, 2 y 3. La zona 0 de las series es todo el recuadro, solo para el Dashboard. | — |
| D3 | Mismo recuadro de Daule | 🟡 | Las zonas 1–3 y las fotos usan los polígonos de P3 (recuadro grande, igual que IMERG). La zona 0 sigue usando `aoi_daule.geojson` (más pequeño) y NASA POWER un solo punto. | Acordar un solo recuadro (P1, P2, P3). |
| D4 | Mismos meses | ✅ | Todo cubre de noviembre 2021 a octubre 2026. | — |
| D5 | Valores raros explicados | 🟡 | Los meses nublados se marcan como "sin foto" y en la galería como "sin imagen por nubes". Sigue sin explicarse en la app que las hectáreas son del recuadro, ni la diferencia entre la tabla y los polígonos de P3. | P3 debe recalcular `area_ha` con los polígonos finales. |
| D6 | Ningún dato inventado ni de prueba | ✅ | Se eliminó la alerta inventada del Asistente; ya no hay frases sobre el futuro sin dato (revisión automática: 0). Lo que no sale de datos está **etiquetado** con confianza 🔴 baja: las barras del juego para combinaciones libres ("Estimación del juego") y el plan mes a mes ("Calendario general"). | Que P1 y P4 validen los supuestos de `estrategias.csv` (agua extra del arroz, ajustes por zona). |

## E. Calidad

| # | Revisión | Estado | Evidencia | Qué falta |
|---|---|:-:|---|---|
| E1 | AppTest | ✅ | Sin excepciones en ninguna corrida: 90 de páginas (10 × 3 zonas × 3 escenarios, con jugar A, B y C, las 4 preguntas del Asistente y mover el selector de mes de "Mi campo"), 48 de filtros del Dashboard y 90 con cada archivo faltante. Avisos esperables en "Mi campo": "Soya: en mayo hubo agua en el terreno…" (zona baja) y "Arroz en la loma…" (loma). | — |
| E2 | Ortografía, inglés y siglas | 🟡 | Siglas resueltas (RNF-03). Siguen en inglés "Dashboard" (menú) y el botón "Deploy" de Streamlit. | Traducir "Dashboard" y poner `client.toolbarMode = "viewer"` al desplegar. |
| E3 | Credenciales, rutas personales y datos privados | ✅ | Sin claves, tokens, contraseñas, rutas personales ni correos en los archivos versionados. **Nota:** `scripts/series_por_zona.py:51` trae como valor por defecto el ID del proyecto de Google Cloud, a pedido del equipo. No es una credencial (hace falta autenticarse), pero se puede cambiar con `--proyecto` o la variable `EE_PROYECTO`. | Si el repo será público, considerar dejar solo la variable de entorno. |

---

## Lo que falta, por importancia para el pitch

| # | Qué falta | Por qué importa | Quién |
|---|---|---|---|
| 1 | **Validar los supuestos de `estrategias.csv` y la ficha `estrategias_info.json`** | Son el corazón de la recomendación; hoy llevan confianza "media". | P1 Mario (agua del arroz, percolación, ajustes por zona), P4 Johan (notas y ficha) |
| 2 | **Más años de lluvia** (IMERG 2001–2025) y su script de extracción | Cada tipo de año es una sola temporada, por eso la confianza es "baja" fuera del año normal. Además da los patrones históricos. | P1 Mario |
| 3 | **K-means con índices de Landsat**, recalcular `area_ha` con los polígonos finales e integrar el código de zonas | Lo pide el mentor; hoy la ladera mide 17.097 ha en la tabla y 6.816 ha en el mapa. | P3 Austin (las series por zona ya están en `data/processed/indices_por_zona.csv`) |
| 4 | **Datos de suelo** por zona | RF-05: la app dice con honestidad que aún no los tiene. | P3 Austin (`src/suelo.py`) |
| 5 | **Climatología de 35 años** en la app | "Patrones históricos" del reto. | P1 Mario (datos), P5 Andrés (vista) |
| 6 | **Un solo recuadro de estudio** | Coherencia; la zona 0 usa otro recuadro. | P1, P2 y P3 (acordar); P5 (volver a correr `series_por_zona.py`) |
| 7 | **Confianza también en los gráficos** de la vista técnica y del Dashboard | RNF-06 completo. | P5 Andrés |
| 8 | **Arranque en frío menor a 5 s** y casos de 5,1–5,3 s | RNF-02. | P5 Andrés |
| 9 | **Scripts como funciones** y los que faltan (IMERG, zonas) | RNF-08. | P1, P2 y P3, cada uno los suyos |
| 10 | **Traducir "Dashboard"** y ocultar "Deploy" | Detalle visual en la demo. | P5 Andrés |
