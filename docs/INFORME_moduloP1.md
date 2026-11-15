
# AgroShift — Informe técnico del módulo P1

## Coordinación, clima y agua

**Proyecto:** AgroShift
**Equipo:** Semilla Cósmica
**Desafío:** Field Shift: Adapting Farms with NASA Data
**Área piloto:** Daule, Guayas, Ecuador
**Período de análisis climático:** Noviembre de 2021 – octubre de 2026
**Estado:** Primera versión funcional, pendiente de validación agronómica.

---

## 1. Resumen ejecutivo

El módulo P1 de AgroShift tiene como objetivo analizar las condiciones climáticas y la disponibilidad potencial de agua en el área piloto de Daule, utilizando información de NASA POWER, NASA GPM IMERG y el índice climático RONI de NOAA.

Se desarrolló un sistema de procesamiento de datos en Python que permite analizar cinco años de información climática, identificar patrones estacionales de precipitación, estimar la demanda de evapotranspiración de diferentes cultivos y comparar tres estrategias de rotación agrícola.

Los resultados muestran una temporada lluviosa concentrada principalmente entre febrero y abril, mientras que los meses de julio a septiembre presentan condiciones generalmente más secas.

En la simulación hídrica de 2025–2026, la estrategia C, que combina arroz, soya y maíz duro, presentó el menor déficit de evapotranspiración no cubierto por la lluvia aprovechable estimada.

Estos resultados son preliminares y permiten comparar escenarios bajo condiciones definidas, pero no constituyen recomendaciones definitivas de riego o selección de cultivos.

## 2. Objetivo del módulo

Desarrollar un componente de análisis climático e hídrico basado en datos de la NASA para apoyar la evaluación de estrategias de rotación de cultivos en Daule, Ecuador.

### Objetivos específicos

- Procesar información histórica de temperatura, precipitación, humedad relativa y radiación solar mediante NASA POWER.
- Obtener estimaciones satelitales de precipitación mediante NASA GPM IMERG.
- Identificar condiciones asociadas con El Niño y La Niña utilizando información de NOAA.
- Estimar la evapotranspiración de referencia y la demanda hídrica de arroz, soya y maíz duro.
- Comparar el déficit hídrico estimado de tres estrategias agrícolas.
- Proporcionar datos procesados y funciones reutilizables para el dashboard y simulador de AgroShift.

## 3. Fuentes de información

| Fuente             | Variables principales                                            | Aplicación                                        |
| ------------------ | ---------------------------------------------------------------- | -------------------------------------------------- |
| NASA POWER         | Temperatura, precipitación, humedad relativa y radiación solar | Caracterización climática y cálculo de ETo      |
| NASA GPM IMERG V07 | Precipitación estimada por satélite                            | Comparación de lluvia y análisis de sensibilidad |
| NOAA RONI          | Anomalías relativas de temperatura oceánica                    | Clasificación descriptiva de condiciones ENSO     |

Los datos climáticos y de precipitación comprenden 60 meses, desde noviembre de 2021 hasta octubre de 2026. La serie RONI utilizada dispone de 59 registros, hasta septiembre de 2026.

## 4. Metodología

### 4.1. Procesamiento climático

Se descargaron y organizaron los datos diarios de NASA POWER, obteniendo 1.826 registros correspondientes al período de estudio.

A partir de ellos se generaron tablas mensuales con temperatura, precipitación, humedad relativa y radiación solar.

### 4.2. Precipitación satelital

Se utilizó NASA GPM IMERG V07 mediante Google Earth Engine.

Las estimaciones de intensidad de precipitación, expresadas en mm/h, se convirtieron en acumulados por intervalos de 30 minutos y posteriormente en acumulados mensuales.

Se procesaron los 60 meses de estudio. De ellos, 58 presentaron la cantidad esperada de observaciones y dos mostraron pequeñas diferencias de completitud.

### 4.3. Análisis ENSO

Se procesó el índice RONI de NOAA para clasificar los meses según condiciones El Niño, La Niña o neutrales.

Se integraron estas clasificaciones con las precipitaciones mensuales de NASA POWER e IMERG.

El análisis se considera descriptivo, debido a que no controla completamente la estacionalidad ni permite atribuir causalidad climática.

### 4.4. Evapotranspiración de referencia

Se estimó la ETo mediante el método Hargreaves–Samani, utilizando temperaturas diarias de NASA POWER y radiación extraterrestre calculada para la latitud del área piloto.

La ETo media estimada fue de **5,26 mm/día**.

### 4.5. Demanda de los cultivos

Se estimó la evapotranspiración de cultivo mediante:

**ETc = Kc × ETo**

Se utilizaron coeficientes Kc preliminares que varían según las etapas de desarrollo.

Para una simulación inicial de 120 días, desde enero de 2025, se obtuvieron las siguientes demandas:

| Cultivo    | ETc estimada |
| ---------- | -----------: |
| Arroz      |    602,80 mm |
| Soya       |    401,26 mm |
| Maíz duro |    430,06 mm |

Los calendarios y coeficientes utilizados son parámetros de simulación y requieren validación agronómica local.

### 4.6. Balance hídrico de estrategias

Se evaluaron tres estrategias durante 2025–2026, utilizando cuatro ciclos de 120 días con fechas hipotéticas de inicio en enero y julio.

| Estrategia | Año 2025      | Año 2026          |
| ---------- | -------------- | ------------------ |
| A          | Arroz → arroz | Arroz → arroz     |
| B          | Arroz → soya  | Arroz → soya      |
| C          | Arroz → soya  | Maíz duro → soya |

El balance preliminar estimó la fracción de ETc no cubierta por la precipitación diaria aprovechable.

Se utilizó un supuesto experimental del 80 % de aprovechamiento de lluvia, limitado por la demanda diaria de cada cultivo.

Además, se evaluaron escenarios mensuales con NASA POWER e IMERG para analizar la sensibilidad a la fuente y distribución temporal de la precipitación.

## 5. Resultados

### 5.1. Caracterización climática de Daule

A partir de los cinco años analizados, se identificaron los siguientes patrones:

- **Temporada de mayor precipitación:** febrero, marzo y abril.
- **Período generalmente más seco:** julio, agosto y septiembre.
- **Mes con mayor precipitación promedio:** febrero.
- **Mes con menor precipitación promedio:** agosto.
- **Temperatura media más alta por mes del año:** septiembre, con 28,43 °C.
- **Temperatura media más baja por mes del año:** marzo, con 26,33 °C.

La temperatura presenta variaciones estacionales relativamente pequeñas en comparación con las diferencias observadas en precipitación.

### 5.2. Comparación NASA POWER e IMERG

| Indicador                             |  NASA POWER |   GPM IMERG |
| ------------------------------------- | ----------: | ----------: |
| Precipitación media mensual          |    92,07 mm |   114,14 mm |
| Precipitación acumulada del período | 5.523,98 mm | 6.848,46 mm |

IMERG estimó acumulados superiores a NASA POWER para el período estudiado.

Ambas fuentes presentan patrones estacionales similares, con una correlación mensual de Pearson de aproximadamente 0,961.

La diferencia entre productos no permite establecer automáticamente cuál de ellos es más preciso; para ello se requieren mediciones meteorológicas de referencia.

### 5.3. Condiciones ENSO

El análisis RONI identificó:

| Condición | Meses |
| ---------- | ----: |
| El Niño   |    12 |
| La Niña   |    33 |
| Neutral    |    14 |

La precipitación mensual media estimada por IMERG fue de 83,17 mm durante meses clasificados como El Niño, 119,19 mm durante La Niña y 95,14 mm durante condiciones neutrales.

Estos resultados reflejan diferencias observadas dentro del período, pero no demuestran que una determinada fase ENSO cause mayores precipitaciones en Daule.

### 5.4. Comparación del déficit hídrico

Se obtuvieron los siguientes resultados para los tres escenarios de precipitación:

| Escenario              |  Estrategia A |  Estrategia B |  Estrategia C |
| ---------------------- | ------------: | ------------: | ------------: |
| POWER diario           | 19.613 m³/ha | 15.188 m³/ha | 13.925 m³/ha |
| POWER mensual uniforme | 16.462 m³/ha | 12.042 m³/ha | 10.905 m³/ha |
| IMERG mensual uniforme | 14.327 m³/ha |  9.907 m³/ha |  9.271 m³/ha |

En los tres escenarios evaluados, la estrategia C presentó el menor déficit estimado.

En el escenario POWER diario, la reducción del déficit fue aproximadamente:
