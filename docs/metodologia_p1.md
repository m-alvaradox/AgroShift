
# AgroShift — Metodología del módulo P1

## 1. Objetivo

Analizar las condiciones climáticas e hídricas
del área piloto de Daule, Guayas, Ecuador,
utilizando datos satelitales y meteorológicos
para comparar tres estrategias de rotación agrícola.

## 2. Área de estudio

Región: Daule, Guayas, Ecuador.

Coordenadas aproximadas:
- Latitud: -1.70 a -1.95
- Longitud: -79.85 a -80.10

## 3. Fuentes de información

### NASA POWER
Período: noviembre 2021 - octubre 2026.

Variables:
- Temperatura media, máxima y mínima
- Precipitación
- Humedad relativa
- Radiación solar

### NASA GPM IMERG V07
Período: noviembre 2021 - octubre 2026.

Variable:
- Precipitación acumulada mensual (mm)

Resolución temporal original:
30 minutos.

### NOAA RONI
Período disponible:
noviembre 2021 - septiembre 2026.

Uso:
Caracterización de condiciones El Niño,
La Niña y neutrales.

## 4. Metodología hídrica

### Evapotranspiración de referencia

Se estimó la ETo mediante
Hargreaves-Samani, utilizando temperaturas
diarias y radiación extraterrestre calculada.

### Evapotranspiración de cultivos

ETc = Kc × ETo

Los coeficientes Kc cambian según la
etapa de desarrollo de cada cultivo.

Los parámetros actuales son preliminares
y requieren validación agronómica local.

### Déficit hídrico

Se calculó como la diferencia positiva
entre ETc y lluvia diaria aprovechable.

Supuesto experimental:
80 % de la precipitación diaria,
limitada por la demanda ETc.

Este enfoque no representa un balance
completo de humedad almacenada en el suelo.

## 5. Estrategias comparadas

Horizonte: 2025-2026.

A: Arroz continuo.

B: Alternancia arroz-soya.

C: Arroz-soya durante 2025,
   maíz duro-soya durante 2026.

Se simularon cuatro ciclos de 120 días,
con fechas hipotéticas de siembra
en enero y julio.

## 6. Resultados preliminares

Déficit equivalente con NASA POWER diario:

- Estrategia A: 19.613 m³/ha
- Estrategia B: 15.188 m³/ha
- Estrategia C: 13.925 m³/ha

La estrategia C obtuvo el menor déficit
de evapotranspiración no cubierto por lluvia
en todos los escenarios evaluados.

## 7. Limitaciones

- Las fechas de siembra son hipotéticas.
- Los coeficientes Kc requieren validación local.
- No se modela almacenamiento de agua en el suelo.
- No se incluyen pérdidas específicas del arroz
  inundado ni eficiencias del sistema de riego.
- Los escenarios mensuales distribuyen
  uniformemente la lluvia, como simplificación.
- La relación ENSO-precipitación es descriptiva
  y no establece causalidad.
- Las estimaciones deben validarse con
  información agrícola y meteorológica local.

## 8. Ejecución

Desde la raíz del proyecto:

python src/agua.py

Los resultados se almacenan en:

data/processed/

## 9. Alcance

Los resultados son estimaciones exploratorias
para comparar estrategias.

No constituyen recomendaciones definitivas
de riego ni garantizan rendimientos agrícolas.
