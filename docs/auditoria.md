# Auditoría de AgroShift (rama Develop)

- **Fecha:** 15 de noviembre de 2026
- **Commit auditado:** `0ff7194` (Develop)
- **Base:** lo acordado por el equipo en `README_APP.md`, `docs/metodologia_p1.md`, `docs/INFORME_moduloP1.md`, la documentación de P4 (`docs/reglas_agronomicas.md` y `docs/fuentes_catalogo_cultivos.md` en `origin/p4-reglas`) y la lista de requisitos RF/RNF y del reto.
- **Alcance:** solo revisión, sin cambios de código.

## Resumen

| Sección | ✅ Cumple | 🟡 Parcial | ❌ No cumple |
|---|:-:|:-:|:-:|
| A. Requerimientos funcionales (10) | 6 | 2 | 2 |
| B. Requerimientos no funcionales (8) | 3 | 5 | 0 |
| C. Requisitos del reto (6) | 1 | 4 | 1 |
| D. Datos (6) | 2 | 4 | 0 |
| E. Calidad (3) | 2 | 1 | 0 |
| **Total (33)** | **14** | **16** | **3** |

**En una frase:** la app funciona de punta a punta con datos 100 % reales de la NASA y es reproducible desde el repo. Los tres huecos grandes para el pitch son:
1. No hay series de satélite **por zona**: todo es el promedio de Daule.
2. No hay **imágenes de cada mes**.
3. No se muestran las **características de los cultivos ni del suelo**.

### Cómo se verificó

- **AppTest:** 138 corridas. Son las 10 páginas × zonas 1, 2 y 3 × escenarios normal, muy lluvioso y seco, más las 48 combinaciones de filtros del Dashboard.
- **Navegador real (Chrome):** se midió el tiempo de carga de cada página en computadora (1400 px) y en celular (390 px), dos rondas, y se revisó el scroll horizontal.
- **Reproducción desde cero:** se clonó el repo en una carpeta temporal y se siguió `README_APP.md` con un entorno virtual nuevo.
- **Datos:** se revisaron los 9 archivos de los contratos.
- **Búsqueda en todos los archivos versionados:** credenciales, rutas personales y correos.

---

## A. Requerimientos funcionales

| ID | Requisito | Estado | Evidencia | Qué falta |
|---|---|:-:|---|---|
| RF-01 | Mapa con 2 o 3 zonas y su nombre común | ✅ | `app/vistas/inicio.py:58` dibuja `mapa.construir()` (`app/utils/mapa.py:199`). Las 3 zonas de P3 tienen color por tipo y una ventana al tocarlas con nombre, hectáreas, elevación y pendiente (`mapa.py:237`). | — |
| RF-02 | Lluvia y evaporación de cada mes, clasificado como lluvioso, transición o seco | ✅ | `app/vistas/clima.py:26-31` (barras de lluvia y línea de evaporación). La clasificación sale de `scripts/adaptar_datos.py:93`: lluvioso feb–mar, transición ene y abr, seco may–dic. | Es la **mediana de solo 5 años** (2021–2026), no un promedio histórico (ver C). |
| RF-03 | Series mensuales de 5 años de NDVI, NDWI, NDMI y lluvia **por zona** | ❌ | `app/data/series_zonas.csv` tiene 60 meses (nov 2021 a oct 2026) con los tres índices y lluvia, pero **solo `zona_id = 0`** (todo el recuadro): `scripts/adaptar_datos.py:21`. La app lo avisa en `app/vistas/zonas.py:18`. | P2 debe entregar los índices promediados dentro de cada polígono de P3 (zonas 1, 2 y 3). |
| RF-04 | Mejores meses para sembrar cada cultivo en cada zona | 🟡 | Hay calendario por cultivo en `app/vistas/zonas.py:47` y `app/utils/logica.py:171`. Solo cambia por zona en la loma (aviso de arroz, `logica.py:178`). El riesgo de encharcamiento usa el NDWI de todo Daule (`logica.py:176`), que nunca supera 0. | Que dependa de las series por zona (RF-03) y de un calendario validado por P4 (`app/utils/juego.py:346`, `TODO`). |
| RF-05 | Características de cada cultivo y del suelo local | ❌ | `data/cultivos.csv` (ciclo, Kc, tolerancia) se usa en cálculos (`logica.py:81`, `juego.py:144`), pero **ninguna página lo muestra**. No hay datos de suelo en Develop: el módulo de suelo de P3 (`src/suelo.py`) está solo en su rama. | Una ficha por cultivo (P4) y datos de suelo por zona (P3), más su vista en la app (P5). |
| RF-06 | Comparar las 3 estrategias con su agua en m³/ha por zona | ✅ | `data/processed/estrategias.csv`: 27 filas (3 zonas × 3 tipos de año × A, B, C), entre 2.960 y 13.500 m³/ha. Se muestra en `app/vistas/estrategias.py:34-81` y en el Dashboard. | Validar los supuestos del cálculo (ver D6). |
| RF-07 | Reordenar las estrategias según las prioridades del usuario | ✅ | `st.pills` de prioridades en `app/vistas/comparar.py:19` y `app/vistas/estrategias.py:23`; el puntaje se calcula en `app/utils/logica.py:34`. | — |
| RF-08 | Cada estrategia en año normal, muy lluvioso (El Niño) y seco (La Niña) | 🟡 | Hay tres escenarios (`app/utils/ui.py:22`), pero se definen **por la lluvia IMERG de cada temporada, no por el índice ENSO** (`scripts/adaptar_datos.py:124`). El grupo "muy lluvioso" es solo 2024-2025 y el "seco" solo 2021-2022. | Serie IMERG más larga (P1), para tener varios años por tipo. Acordar si se vuelve a ENSO (RONI de P1) o si se queda la definición por lluvia. |
| RF-09 | Recomendar una estrategia con evidencia, beneficios, vacíos y riesgos | ✅ | `app/vistas/recomendacion.py:48-49` muestra las cuatro partes, desde `data/estrategias_info.json`. | La ficha la redactó P5 a partir de la documentación de P4 y P1; **falta que P4 la valide**. |
| RF-10 | Reglas para el campo, cada una con el dato que la respalda | ✅ | `app/vistas/recomendacion.py:58-61`: cada regla de `data/reglas.json` (P4) trae su evidencia en "Por qué". | Las 5 reglas son generales (`zona_id` null) y su evidencia es bibliográfica (FAO, INIAP), no un dato medido en Daule. |

## B. Requerimientos no funcionales

| ID | Requisito | Estado | Evidencia | Qué falta |
|---|---|:-:|---|---|
| RNF-01 | Se abre en computadora y celular (390 px) | ✅ | En Chrome, las 10 páginas en 1400 px y 390 px **sin scroll horizontal**. Solo la franja de meses y las tablas tienen scroll interno, a propósito. Los 6 botones del menú caben a 390 px. | — |
| RNF-02 | Cada página carga en menos de 5 s | 🟡 | Ver la tabla de tiempos abajo. Promedio de 4,3 s; **7 de 40 mediciones pasan de 5 s**. El peor caso es 7,5 s ("Mi finca" y Dashboard en la primera carga). | Acelerar "Mi finca" (mapa de 2 MB con capas incrustadas) y el Dashboard: guardar el mapa en caché y cargar las capas raster solo cuando se encienden. |
| RNF-03 | Lenguaje simple; cada término técnico explicado | 🟡 | Hay glosario: verdor = NDVI, agua en el terreno = NDWI, agua que se evapora = ET0 (`ui.py:29` y el pie del Dashboard). Pero el productor ve siglas sin explicar: **P1–P4** en las fuentes del Dashboard, **AGR-001…005** en beneficios y riesgos (Comparar y Recomendación), **FAO-56, Hargreaves, K-means, SRTM, IMERG, GPM, CSV**. | Quitar los códigos internos (P1–P4, AGR-0xx) de las vistas del productor o explicarlos; ampliar el glosario. |
| RNF-04 | Solo datos gratuitos y públicos | ✅ | Ver la lista de fuentes abajo: todas son gratuitas. | Notas: Earth Engine pide una cuenta gratuita; las fotos aéreas de fondo de Esri son de uso gratuito con atribución, pero no son datos abiertos. |
| RNF-05 | Solo imágenes recortadas al área; ningún archivo de más de ~50 MB | ✅ | El archivo más grande es `data/processed/pendiente_daule.tif`, con 3,7 MB. Los 96 archivos suman 13,2 MB. Los raster cubren solo el recuadro de Daule (~0,25° × 0,25°). | — |
| RNF-06 | Cada número muestra su fuente y nivel de confianza | 🟡 | La **fuente** sí aparece: pie de cada gráfico, etiqueta "Dato de satélite NASA" y la tabla "De dónde sale cada dato" (`app/utils/carga.py`, `FUENTES`). El **nivel de confianza no aparece en ninguna parte** (`git grep confianza`: 0 resultados). | Agregar una confianza (alta, media o baja) por archivo y mostrarla junto a la fuente. Por ejemplo: IMERG alta; estrategias media, por los supuestos; zonas media, por la unidad de la pendiente sin confirmar. |
| RNF-07 | Aviso de que no reemplaza al técnico local | 🟡 | `ui.aviso_tecnico()` (`ui.py:180`) sale solo en `plan.py:48` y `recomendacion.py:68`. **No aparece** en Mi finca, Dashboard, Asistente ni Comparar. | Mostrarlo en el pie de todas las páginas o al menos en Mi finca y el Dashboard. |
| RNF-08 | Reproducible: funciones, requirements y README para correr todo desde cero | 🟡 | **Lo que funciona:** clonar el repo y seguir `README_APP.md` instala todo en 225 s; `adaptar_datos`, `calcular_estrategias`, `preparar_capas` y `revisar_datos` terminan sin error y **regeneran exactamente los mismos archivos**; la app levanta. **Lo que falla:** `README.md` solo dice "# AgroShift" y **15 de 25 scripts** son código suelto sin funciones (`analizar_datos`, `clasificar_terreno`, `descargar_nasa_power`, `graficar_clima`, `integrar_datos`, `procesar_srtm`, `revisar_datos`, `probar_modulos`, y en `src/`: `analizar_enso`, `balance_estrategias`, `climatologia`, `comparar_fuentes_agua`, `demanda_cultivos`, `enso`, `eto`, `graficar_balance`). Además, no se pueden regenerar los datos crudos: falta el script que extrajo IMERG de Earth Engine, el código de zonificación de P3 no está en Develop y `calcular_estrategias.py` lee `src/reglas.py` de la rama `origin/p4-reglas`. | Un README principal con la cadena completa (descargas → procesamiento → app); los scripts que faltan; pasar los scripts a funciones con `main()`. |

**Tiempo de carga real** (Chrome; segundos hasta que la página terminó y sus gráficos están dibujados; sesión nueva en cada medición):

| Página | PC, 1ª | PC, 2ª | Celular, 1ª | Celular, 2ª |
|---|--:|--:|--:|--:|
| Mi finca | **7,5** | 4,9 | 4,4 | **5,7** |
| Jugar | 4,0 | 4,3 | 3,2 | 4,4 |
| Comparar | 3,1 | **5,3** | 4,4 | 3,3 |
| Mi plan | 4,9 | 4,1 | 3,2 | 3,5 |
| Asistente | 4,0 | **5,1** | 4,1 | 3,4 |
| Clima | 3,2 | 3,7 | **5,2** | 3,6 |
| Satélite | 3,2 | 4,0 | 4,5 | 4,9 |
| Estrategias | 3,2 | 4,1 | 3,4 | 4,3 |
| Recomendación | 4,5 | 4,3 | 3,5 | 3,6 |
| Dashboard | **7,2** | **5,4** | 4,4 | 4,3 |

**Fuentes usadas (RNF-04):**

| Fuente | Qué aporta | Quién la procesó | Gratuita y pública |
|---|---|---|:-:|
| NASA POWER (diario) | Lluvia, temperaturas y evaporación (ET0 por Hargreaves) | P1 | ✅ API abierta |
| NASA GPM IMERG V07 (mensual) | Lluvia y tipos de año | P1 | ✅ (vía Google Earth Engine, cuenta gratuita) |
| Landsat 8 y 9 (USGS y NASA) | NDVI, NDWI, NDMI | P2 | ✅ (Earth Engine) |
| Sentinel-2 (ESA) | Relleno de meses nublados en los compuestos de P2 | P2 | ✅ (no es de la NASA) |
| SRTM (NASA) | Elevación, pendiente y zonas | P3 | ✅ |
| NOAA RONI | Fases de El Niño y La Niña (informe de P1; la app no lo usa) | P1 | ✅ |
| FAO-56, FAO *Irrigation Water Needs*, INIAP | Kc, ciclos y reglas | P4 | ✅ (publicaciones) |
| OpenStreetMap y Esri World Imagery | Mapas de fondo | P5 | ✅ uso gratuito con atribución |

## C. Requisitos del reto (mentor)

| Requisito | Estado | Evidencia | Qué falta |
|---|:-:|---|---|
| Una región y 3 cultivos locales con datos locales | 🟡 | Daule, con arroz, soya y maíz duro (`data/cultivos.csv`). | Los parámetros son de referencia (FAO, INIAP), no medidos en Daule. Faltan rendimientos, precios o suelos locales. |
| Patrones históricos | 🟡 | Solo 5 años (nov 2021 a oct 2026). `scripts/clima_historico_power.py` puede bajar 35 años, pero **no hay salida en el repo** y la app no la usa. | Correr la climatología de 35 años y mostrarla en Clima y el Dashboard. |
| Zonas con K-means usando elevación e índices de Landsat | 🟡 | P3 usó K-means (`origin/p3-feature/zonificacion-terreno:src/zonas.py:71`), pero las zonas salieron **solo con elevación y pendiente**: el código avisa "No hay Landsat de P2 todavía" (`src/zonas.py:177`) y `zonas_resumen.csv` no trae columnas de NDVI. Ese código no está en Develop. | Volver a correr K-means con los índices de P2 e integrar el código de zonas en Develop. |
| Series de tiempo de los últimos 5 años | 🟡 | Hay 60 meses (nov 2021 a oct 2026) de lluvia, evaporación e índices. | No están por zona (RF-03). |
| Imágenes de cada mes para ver qué meses son mejores para cada cultivo | ❌ | La app no muestra imágenes mensuales. `data/processed/landsat/` solo trae `cobertura_landsat.csv`, y la capa "Verdor (último mes)" del mapa queda omitida (`preparar_capas.py`). | P2 exporta los compuestos mensuales recortados (GeoTIFF de NDVI) y P5 los muestra en una galería o con un selector de mes en el mapa. |
| Datos de la NASA usados explícitamente | ✅ | NASA POWER, GPM IMERG, Landsat 8 y 9 y SRTM se nombran en cada gráfico, en la portada del Dashboard y en el pie de todas las páginas. | — |

## D. Datos

### Los 9 contratos de `app/utils/carga.py`

| Archivo | ¿Real? | Se usa la copia de | Viene de | Período | Valores raros |
|---|:-:|---|---|---|---|
| `climatologia_daule.csv` | ✅ | `app/data/` | P1: NASA POWER diario, adaptado por `adaptar_datos.py` | 12 meses, calculados con 5 años | Ninguno. El balance es negativo en 10 meses, lo esperable en la época seca. |
| `clima_mensual_daule.csv` | ✅ | `app/data/` | P1: NASA POWER diario | nov 2021 a oct 2026 (60 meses) | Ninguno. Lluvia de 2,0 a 573,5 mm; temperatura de 25,5 a 29,9 °C. |
| `lluvia_imerg_daule.csv` | ✅ | `app/data/` | P1: IMERG de Mario, adaptado | nov 2021 a oct 2026 (60 meses) | Noviembre de 2021 queda sin tipo de año (temporada incompleta). Octubre de 2026 tiene 585 mm en plena época seca; NASA POWER marca 573,5 mm, así que lo confirman dos fuentes. |
| `series_zonas.csv` | ✅ | `app/data/` | P2: índices Landsat del recuadro | nov 2021 a oct 2026 (60 meses) | Solo `zona_id = 0`. 7 meses sin NDVI por nubes. **El NDWI siempre es negativo (−0,57 a −0,26)**: en el promedio del recuadro nunca se ve agua. |
| `cultivos.csv` | ✅ | `data/` | P4 (Johan) | — | Arroz 450–700 mm: según la documentación de P4, `agua_*` es un alias de la ETc y no el riego. Por eso **ya no contradice** los 1.000–1.500 mm, que incluyen la inundación. |
| `estrategias.csv` | ✅ | `data/processed/` | Calculado por P5 (`scripts/calcular_estrategias.py`) con datos de P1 y reglas de P4 | Temporadas 2021-22 a 2025-26 | Ninguno fuera de rango: agua de 2.960 a 13.500 m³/ha y notas de 2 a 9. **Depende de supuestos sin validar** (ver D6). |
| `zonas_daule.geojson` | ✅ | `data/processed/` | P3 (Austin) | — | 3 zonas que suman 77.137 ha, que es todo el recuadro (unos 773 km²). El "% de Daule" de la app es del recuadro, no del cantón. Pendiente de 2,1 a 5,8°, en grados según el código de P3. |
| `estrategias_info.json` | ✅ | `data/` | Redactado por P5 con la documentación de P4 y P1 | — | Figura a nombre de P4, pero **P4 no lo ha validado**. |
| `reglas.json` | ✅ | `data/` | P4 (Johan) | — | Las 5 reglas tienen `zona_id` null: son generales. |

Otros valores raros en archivos que no son contratos:
- `elevacion_daule_utm.tif` tiene 11.370 píxeles bajo 0 m (mínimo −30,6 m), artefactos típicos de SRTM. La capa del mapa los recorta (percentiles del 2 al 98).

**Corrección de un aviso anterior:** `zonas_daule.geojson` y `zonas_resumen.csv` de P3 **son UTF-8 válidos y "erosión" está bien escrito**. Lo que antes se vio como "erosi�n" era la consola de Windows mostrando mal la "ó". Para estos archivos, el pedido a Austin de "guardar en UTF-8" no aplica. El arreglo de tildes de `carga.py` no hace daño.

### Coherencia y datos inventados

| # | Revisión | Estado | Evidencia | Qué falta |
|---|---|:-:|---|---|
| D1 | Los 9 contratos son reales | ✅ | `scripts/revisar_datos.py`: "Archivos reales que cumplen el contrato: 9 de 9". La app ya no lee `data/mock/`. | — |
| D2 | Mismas zonas (`zona_id`) | 🟡 | El GeoJSON y `estrategias.csv` usan 1, 2 y 3 ✅. `series_zonas.csv` solo tiene 0 ❌. `reglas.json` usa null (generales). | Series por zona (RF-03). |
| D3 | Mismo recuadro de Daule | 🟡 | Hay **tres áreas distintas**. El recuadro grande (lat −1,70 a −1,95; lon −79,85 a −80,10) lo usan las zonas de P3, el SRTM y el IMERG de P1 (`docs/metodologia_p1.md`, §2). Landsat usa `data/aoi_daule.geojson`, más pequeño (lat −1,78 a −1,93; lon −79,93 a −80,08) (`scripts/landsat_gee.py:40`). NASA POWER usa un solo punto (−1,86; −79,98) (`scripts/descargar_nasa_power.py:26`). | Acordar un solo recuadro y volver a exportar Landsat (P2), o recortar las zonas (P3). |
| D4 | Mismos meses | ✅ | POWER, IMERG y Landsat cubren de nov 2021 a oct 2026 (60 meses), sin meses duplicados. | — |
| D5 | Valores raros explicados | 🟡 | Ver la tabla de contratos. La app explica las nubes (☁️) y el NDWI del recuadro, pero no los artefactos del SRTM ni que las hectáreas son del recuadro. | Aclarar en la app que el área es el recuadro de estudio. |
| D6 | La app no muestra datos inventados ni de prueba | 🟡 | **Sí muestra:** el Asistente abre con una alerta fija **inventada**, "⚠️ Se viene una semana muy lluviosa. No siembres en zona baja hasta el lunes." (`app/utils/juego.py:388`, `app/vistas/asistente.py:43`). Abajo dice "Vista previa", pero el mensaje parece un pronóstico real. **Valores fijos, aunque etiquetados:** las barras del juego para combinaciones que no son A, B o C (`juego.py:125-133`, "Estimación del juego"); las acciones del plan mes a mes (`juego.py:331`, "Calendario general"). **Supuestos sin validar en `estrategias.csv`:** agua extra del arroz (saturación 200 mm, lámina 100 mm, percolación 4 mm/día), ajustes por zona y el drenaje deducido del nombre de cada zona; las notas de suelo, plagas e ingresos son reglas simples. | Quitar o reescribir la alerta de ejemplo (P5); que P1 y P4 validen los supuestos; que P4 entregue los ingresos y el efecto en el suelo de cada cultivo para reemplazar los `TODO`. |

## E. Calidad

| # | Revisión | Estado | Evidencia | Qué falta |
|---|---|:-:|---|---|
| E1 | AppTest de todas las páginas, zonas y escenarios | ✅ | 138 corridas, **0 excepciones**. 1 aviso, esperable: "Arroz en la loma: necesita mucha más agua…" (zona 3). Mensajes informativos, también esperables: "Sin meses en el periodo elegido" (combinaciones de filtros del Dashboard sin meses de ese tipo de año) y "Por ahora se muestra todo el recuadro de Daule" (Satélite). Antes se probó también cada archivo faltante: ninguna página se cae y cada una muestra "Falta este dato". | — |
| E2 | Ortografía, palabras en inglés y siglas | 🟡 | No se encontraron faltas de ortografía en los textos que se ven. **En inglés:** "Dashboard" (menú y pestaña) y el botón "Deploy" de la barra de Streamlit, porque `.streamlit/config.toml` no define `client.toolbarMode`. **Siglas sin explicar:** ver RNF-03. | Traducir "Dashboard" (por ejemplo, "Datos" o "Tablero"), ocultar la barra de Streamlit en producción y explicar o quitar las siglas. |
| E3 | Credenciales, rutas personales y datos privados | ✅ | `git grep` en los 96 archivos versionados no encontró claves, tokens, contraseñas, rutas de carpetas personales de Windows, correos ni el ID del proyecto de Earth Engine: este se pasa por línea de comandos (`scripts/landsat_gee.py:234`). `__pycache__` y `.venv` no están en git. | — |

---

## Lo que falta, por importancia para el pitch

| # | Qué falta | Por qué importa en el pitch | Quién |
|---|---|---|---|
| 1 | **Series por zona** (NDVI, NDWI, NDMI y lluvia en cada polígono) | Es RF-03 y requisito del reto. Habilita los meses de siembra por zona (RF-04) y el riesgo de inundación real: hoy el NDWI del recuadro nunca marca agua. | P2 Thomas (con los polígonos de P3) |
| 2 | **Imágenes de cada mes** (compuestos NDVI recortados) | Requisito explícito del mentor ❌. La capa "Verdor" del mapa ya está lista para recibirlas. | P2 Thomas → P5 Andrés las integra |
| 3 | **Ficha de cultivos y datos de suelo** | RF-05 ❌: hoy el productor no ve ciclo, agua ni tolerancia de cada cultivo, ni el suelo de su zona. | P4 Johan (cultivos), P3 Austin (suelo, `src/suelo.py`), P5 Andrés (vista) |
| 4 | **Quitar la alerta inventada del Asistente** | Muestra un pronóstico falso; un jurado lo notaría. | P5 Andrés |
| 5 | **K-means con índices de Landsat** e integrar el código de zonas en Develop | Lo pide el mentor; hoy las zonas usan solo elevación y pendiente. | P3 Austin (con datos de P2) |
| 6 | **Validar los supuestos de `estrategias.csv` y la ficha `estrategias_info.json`** | Los m³/ha y las notas son el corazón de la recomendación. | P1 Mario (agua del arroz, percolación, ajustes por zona), P4 Johan (notas y ficha) |
| 7 | **Más años de lluvia** (IMERG 2001–2025) y su script de extracción | Hoy cada tipo de año es una sola temporada. Además da los patrones históricos. | P1 Mario |
| 8 | **Climatología de 35 años** en la app | "Patrones históricos" del reto. | P1 Mario (datos), P5 Andrés (vista) |
| 9 | **Un solo recuadro de estudio** para Landsat, zonas, IMERG y POWER | Coherencia de datos; el "% de Daule" se refiere al recuadro. | P1 Mario, P2 Thomas y P3 Austin (acordar); P5 Andrés (texto en la app) |
| 10 | **Nivel de confianza** junto a cada fuente | RNF-06: hoy solo se muestra la fuente. | P5 Andrés, con la confianza que defina cada dueño de datos |
| 11 | **Carga en menos de 5 s** en Mi finca y Dashboard | RNF-02: hasta 7,5 s en la primera carga. | P5 Andrés |
| 12 | **README principal** con la cadena completa, scripts como funciones y los scripts que faltan (extracción IMERG, zonas) | RNF-08: hoy la app se reproduce, pero no los datos crudos. | P5 Andrés (README); cada uno sus scripts: P1, P2, P3 |
| 13 | **Lenguaje:** quitar P1–P4 y AGR-0xx de las vistas del productor, explicar FAO-56, K-means, etc., y traducir "Dashboard" | RNF-03 y E2. | P5 Andrés (P4 para reescribir los textos de reglas) |
| 14 | **Aviso del técnico local** en Mi finca y el Dashboard | RNF-07. | P5 Andrés |
| 15 | **Confirmar la unidad de la pendiente** (el código dice grados) y si 17.097 ha de ladera es razonable | Credibilidad del mapa de zonas. | P3 Austin |
| 16 | **Ocultar el botón "Deploy"** de Streamlit (`client.toolbarMode = "viewer"`) | Imagen pulida en la demo. | P5 Andrés |
