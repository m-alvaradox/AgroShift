# Fuentes y criterios del catálogo de cultivos

**Proyecto:** AgroShift  
**Zona piloto:** Daule, Guayas, Ecuador  
**Responsable:** P4 — Agronomía y reglas  
**Fecha de revisión:** 2026-11-14  
**Estado:** valores iniciales para el MVP; requieren validación agronómica local.

## 1. Propósito y alcance

Este documento registra la procedencia y los criterios de los valores de `data/cultivos.csv`. El catálogo incluye arroz, soya y maíz duro amarillo, y proporciona coeficientes de cultivo (`Kc`) y rangos orientativos de evapotranspiración del cultivo (`ETc`) para comparar estrategias.

Los valores no constituyen una recomendación de siembra por parcela. El ciclo real y el consumo de agua dependen de la variedad, fecha de siembra, manejo, suelo y condiciones meteorológicas.

## 2. Separación entre ETc y riego

AgroShift debe mostrar ETc y requerimiento de riego como magnitudes diferentes:

- **ETc (mm):** agua consumida por el cultivo mediante transpiración y evaporación. Para el cálculo por etapa se utiliza `ETc = Kc × ETo`.
- **Riego neto requerido (mm):** aporte que falta después de descontar la precipitación efectiva. Para cultivos no inundados, una aproximación inicial es `IN = max(0, ETc - Pe)`, sujeta al balance de humedad del suelo.
- **Riego bruto aplicado (mm):** volumen que debe entregar el sistema; cuando se estime, debe considerar la eficiencia del método de riego.

El manual FAO distingue expresamente la necesidad de agua del cultivo de la cantidad que debe suministrarse mediante riego. Para arroz bajo inundación, el balance es especial: además de ETc y precipitación efectiva, puede requerir saturar el suelo, compensar percolación y filtración, y establecer la lámina de agua. La formulación orientativa es:

`IN_arroz = ETc + SAT + PERC + WL - Pe`

donde `SAT` es saturación previa del suelo, `PERC` representa percolación/filtración, `WL` es el agua para establecer la lámina y `Pe` es precipitación efectiva.

**Decisión de implementación:** el catálogo conserva rangos de ETc de referencia. No almacena un requerimiento fijo de riego por cultivo. El módulo de agua de P1 debe calcular el riego para cada estrategia y periodo usando clima, lluvia efectiva y, para arroz, los componentes adicionales cuando existan datos. No se debe interpretar `etc_min_mm` o `etc_max_mm` como agua que necesariamente se extraerá de canales o bombas.

## 3. Valores seleccionados

| Cultivo | Ciclo de referencia | Kc ini | Kc med | Kc fin | ETc estacional de referencia | Inundación |
|---|---:|---:|---:|---:|---:|---|
| Arroz | 115 días | 1.05 | 1.20 | 0.75 | 450–700 mm | Sí, en sistema de arroz paddy |
| Soya | 108 días | 0.40 | 1.15 | 0.50 | 450–700 mm | No |
| Maíz duro amarillo | 120 días | 0.30 | 1.20 | 0.35 | 500–800 mm | No |

### Arroz

- **Ciclo (115 días):** valor representativo de la variedad INIAP-14. Una fuente académica ecuatoriana que reproduce características varietales atribuidas a INIAP informa 113–117 días; se utiliza 115 como punto medio. INIAP clasifica varias variedades nacionales, incluida INIAP-14, como precoces, pero el ciclo puede variar con el sistema de siembra y manejo.
- **Kc:** FAO-56 presenta 1.05, 1.20 y un intervalo 0.90–0.60. Se adopta 0.75 para Kc final como punto medio del intervalo, no como valor único prescrito por FAO. El Kc inicial 1.05 corresponde a arroz paddy con una lámina de 0.10–0.20 m bajo condiciones climáticas de referencia; debe revisarse para el clima y manejo reales.
- **ETc estacional (450–700 mm):** rango indicativo FAO para arroz paddy. No incluye automáticamente saturación previa, percolación/filtración ni establecimiento de la lámina de agua; esos componentes se modelan en el cálculo de riego.

### Soya

- **Ciclo (108 días):** punto representativo redondeado dentro del intervalo de 105–110 días que INIAP publica como característica deseable de las variedades de soya liberadas. No equivale al ciclo garantizado de una variedad específica.
- **Kc:** FAO-56 asigna al grupo de leguminosas Kc inicial 0.40 y Kc medio 1.15; para soya indica Kc final 0.50.
- **ETc estacional (450–700 mm):** rango indicativo FAO para soya.
- **Inundación:** se marca `false`. La soya no es un cultivo de arrozal; el exceso de agua y el anegamiento prolongado pueden reducir establecimiento, vigor y rendimiento. La tolerancia varía entre genotipos y con la duración del anegamiento.

### Maíz duro amarillo

- **Ciclo (120 días):** corresponde al ciclo vegetativo reportado por INIAP para el híbrido H-551, recomendado para la zona central del litoral ecuatoriano. Es una referencia varietal, no una duración universal de todo maíz amarillo duro.
- **Kc:** FAO-56 da Kc inicial 0.30 para el grupo de cereales y Kc medio 1.20 para maíz de grano. El Kc final es 0.60 para cosecha con humedad alta del grano y 0.35 cuando el grano se deja secar completamente en el campo; se adopta 0.35 para el supuesto de maíz duro cosechado como grano seco.
- **ETc estacional (500–800 mm):** rango indicativo FAO para maíz.
- **Inundación:** se marca `false`. El maíz no es un cultivo de humedal; el anegamiento provoca falta de oxígeno en la zona radicular y puede afectar crecimiento y rendimiento.

## 4. Semántica de las columnas

- `cultivo`: identificador estable usado por AgroShift.
- `ciclo_dias`: duración de referencia del ciclo completo, en días.
- `kc_ini`, `kc_med`, `kc_fin`: coeficientes Kc inicial, medio y final, adimensionales.
- `etc_min_mm`, `etc_max_mm`: rango orientativo de ETc por ciclo, en milímetros.
- `tolera_inundacion`: indicador simplificado de si el sistema productivo contempla cultivo en condiciones de arrozal inundado. No representa una tolerancia cuantitativa a cualquier duración o profundidad de inundación.
- `agua_min_mm`, `agua_max_mm`: columnas heredadas del contrato inicial. Se conservan temporalmente por compatibilidad y duplican los rangos ETc; **no representan riego aplicado**. El nuevo código debe preferir `etc_min_mm` y `etc_max_mm`. Una vez migrados los consumidores, se podrán retirar mediante una actualización coordinada del contrato.

Conversión útil para reportar volúmenes: **1 mm aplicado sobre 1 ha equivale a 10 m³/ha**.

## 5. Limitaciones y validaciones pendientes

1. Los rangos FAO de ETc son orientativos para el ciclo completo; no sustituyen el cálculo local diario o mensual a partir de ETo y Kc.
2. Los Kc de FAO-56 son valores de referencia y pueden requerir ajuste por humedad relativa mínima, viento, altura del cultivo y frecuencia de humedecimiento.
3. El Kc inicial del arroz supone una lámina de agua y condiciones de referencia específicas. No debe aplicarse sin revisar el sistema de riego usado en el lote.
4. El ciclo de arroz depende de variedad, siembra directa o trasplante y régimen hídrico. La soya también cambia según variedad; el valor 108 es un punto de referencia, no una promesa agronómica.
5. El indicador booleano de inundación no describe drenaje, duración del encharcamiento, textura del suelo ni tolerancia específica del cultivar.
6. Antes de presentar una recomendación a productores, validar los valores con INIAP, un técnico local y/o datos de campo de Daule.

## 6. Coordinación del contrato de datos

El contrato inicial nombraba `agua_min_mm` y `agua_max_mm`. Para evitar que esos nombres se interpreten como volumen de riego, se agregaron `etc_min_mm` y `etc_max_mm` como campos explícitos. Los campos anteriores se conservan temporalmente como alias de compatibilidad, con los mismos valores.

P1 debe calcular y entregar el requerimiento de riego como una salida separada del catálogo. P1 y P5 deben ser notificados de que los consumidores nuevos deben usar los campos `etc_*`, y no asumir que las columnas `agua_*` describen riego aplicado.

## 7. Fuentes

1. **FAO.** *Crop Evapotranspiration — Guidelines for Computing Crop Water Requirements*, Irrigation and Drainage Paper 56, capítulo 6: ETc mediante Kc × ETo; valores tabulados y ajustes de Kc.  
   https://www.fao.org/4/X0490E/x0490e0b.htm

2. **FAO.** *Crop Water Needs*, capítulo 2: definición de necesidad de agua como evapotranspiración y rangos aproximados por ciclo (arroz paddy 450–700 mm; soya 450–700 mm; maíz 500–800 mm).  
   https://www.fao.org/4/s2022e/s2022e02.htm

3. **FAO.** *Irrigation Water Needs*, capítulo 4: distinción entre ET del cultivo y necesidad de riego; componentes adicionales del balance para arroz paddy.  
   https://www.fao.org/4/S2022E/s2022e08.htm

4. **INIAP.** Programa Nacional del Arroz: variedades liberadas y variedades precoces para siembra directa bajo riego. La página no fija un único ciclo para todas las variedades.  
   https://www.iniap.gob.ec/programa-1/

5. **Universidad Laica Vicente Rocafuerte de Guayaquil (fuente académica secundaria).** Tabla de características varietales del arroz; reporta 113–117 días para INIAP-14. Se usa solo como referencia de ciclo, pendiente de confirmar con ficha varietal primaria.  
   https://repositorio.ulvr.edu.ec/bitstream/44000/3918/1/T-ULVR-3277.pdf

6. **INIAP.** Programa de Oleaginosas: publica 105–110 días como característica deseable del ciclo de las variedades de soya liberadas.  
   https://www.iniap.gob.ec/oleaginosas/

7. **INIAP.** *Híbrido INIAP H-551*: ficha técnica; ciclo vegetativo de 120 días y recomendación para la zona central del litoral ecuatoriano.  
   https://tecnologia.iniap.gob.ec/wp-content/uploads/2023/11/h551.pdf

8. **University of Minnesota Extension.** *Flooded soybean*: documenta la sensibilidad general de la soya al exceso de agua y los efectos del anegamiento prolongado. Referencia complementaria, no específica de Daule.  
   https://extension.umn.edu/agriculture/crop-production/soybean/flooded-soybean

9. **Excellence in Breeding.** *Phenotyping for abiotic stress tolerance in maize: Waterlogging stress*: describe la susceptibilidad del maíz al anegamiento y la necesidad de aireación en la zona radicular. Referencia complementaria.  
   https://excellenceinbreeding.org/sites/default/files/manual/57827.pdf
