# Módulo de reglas agronómicas — P4

**Zona piloto:** Daule, Guayas  
**Responsable:** P4 — Agronomía y reglas  
**Estado:** implementación inicial del MVP; las reglas y valores requieren validación local.

## Archivos

- `data/cultivos.csv`: catálogo de referencia de arroz, soya y maíz duro amarillo.
- `data/reglas.json`: reglas en formato JSON, con condición evaluable y evidencia.
- `src/reglas.py`: carga/validación del catálogo, definición de estrategias y evaluación de reglas.
- `tests/test_reglas.py`: pruebas unitarias del contrato y la lógica P4.

## Estrategias definidas

| ID | Horizonte | Época lluviosa | Época seca |
|---|---:|---|---|
| A | 1 año | Arroz | Arroz |
| B | 1 año | Arroz | Soya |
| C | 2 años | Año 1: arroz; año 2: maíz duro amarillo | Soya en ambos años |

Las temporadas indican el orden conceptual del piloto. No son fechas exactas ni sustituyen un calendario de siembra para cada parcela.

## API pública

Desde la raíz del repositorio:

```python
from src.reglas import cargar_catalogo, obtener_estrategias, evaluar_reglas

catalogo = cargar_catalogo()
estrategias = obtener_estrategias(catalogo)

# Contexto de zona ilustrativo; los valores reales deben proceder de P3.
contexto = {
    "zona_id": "Z-01",
    "drenaje": "bueno",
    "riesgo_anegamiento": False,
}
alertas = evaluar_reglas("B", contexto, catalogo=catalogo)
```

### `cargar_catalogo(ruta=None)`

Lee el CSV y devuelve un diccionario indexado por ID de cultivo. Convierte ciclo a entero, Kc y ETc a números, y la tolerancia a inundación a booleano. Rechaza columnas obligatorias ausentes, filas duplicadas, números inválidos y rangos ETc inconsistentes.

El módulo prefiere `etc_min_mm`/`etc_max_mm`. Si coexisten las columnas antiguas `agua_min_mm`/`agua_max_mm`, exige que sean idénticas porque se conservan solamente como alias temporales de ETc. No interpreta esos campos como riego.

### `obtener_estrategias(catalogo=None)`

Devuelve A, B y C, cada una con su secuencia ordenada, ciclo de referencia de cada cultivo, suma de días de ciclo y rango ETc acumulado.

Los días son sumas de ciclos de cultivo, no días calendario entre cosechas. El rango ETc acumulado suma referencias de los ciclos incluidos; para comparar estrategias con distinto horizonte (C es de dos años), debe normalizarse por año o presentarse por ciclo. Ningún total ETc equivale a requerimiento de riego.

### `evaluar_reglas(estrategia_id, contexto=None, catalogo=None, reglas=None)`

Evalúa las reglas aplicables a la secuencia. Devuelve una lista con `id`, `texto_campo`, `estado`, `evidencia` y `zona_id`.

Estados actuales:

- `informacion`: contexto agronómico que debe mostrarse al usuario.
- `nota_tecnica`: consideración específica de manejo.
- `advertencia`: característica que diferencia o limita la estrategia.
- `pendiente_validacion`: falta un dato o se recibió una categoría desconocida.
- `alerta`: condición de zona clasificada como no apta para los cultivos afectados.
- `condicion_favorable`: el contexto recibido está dentro de las categorías consideradas aptas; no significa garantía de rendimiento.

La ausencia de información de drenaje/anegamiento no se trata como condición favorable.

## Contrato de contexto con zonificación (P3)

El evaluador reconoce estos campos:

| Campo | Tipo esperado | Valores reconocidos |
|---|---|---|
| `zona_id` | string | ID de zona; las reglas generales usan `null`. |
| `drenaje` | string | Apto: `bueno`, `adecuado`, `bien_drenado`. No apto: `deficiente`, `muy_deficiente`, `malo`, `muy_malo`. |
| `riesgo_anegamiento` | boolean o string | Alto: `true`, `alto`, `muy_alto`. Bajo: `false`, `bajo`, `sin_riesgo`. |

P3 debe mapear las clases de zonificación a estos valores antes de invocar el evaluador. Categorías como "moderado", valores nulos o etiquetas no reconocidas quedan como `pendiente_validacion`; no deben convertirse silenciosamente en aptas.

## Estructura de una regla JSON

Cada elemento de `data/reglas.json` conserva las claves del contrato del equipo:

```json
{
  "id": "AGR-003",
  "texto_campo": "Texto que se presentará en la ficha de campo.",
  "condicion": {
    "tipo": "drenaje",
    "campo": "drenaje",
    "cultivos": ["soya", "maiz_duro_amarillo"],
    "valores_no_aptos": ["deficiente", "muy_deficiente"],
    "valores_aptos": ["bueno", "adecuado", "bien_drenado"]
  },
  "evidencia": "Fuente y criterio que respaldan la regla.",
  "zona_id": null
}
```

Tipos de condición implementados:

- `cultivo_incluido`: activa una nota cuando la secuencia contiene uno de los cultivos indicados.
- `repeticion_consecutiva`: detecta repeticiones consecutivas del cultivo indicado.
- `drenaje`: evalúa las categorías aptas/no aptas de drenaje para los cultivos indicados.
- `anegamiento`: evalúa si el contexto declara riesgo de anegamiento para los cultivos indicados.

Las reglas con `zona_id: null` son generales. Una regla con una zona específica solo se evalúa cuando el `zona_id` de contexto coincide exactamente.

## Separación de ETc y riego

El catálogo entrega rangos orientativos de ETc por ciclo. La estimación basada en clima debe calcularse como ETc = Kc × ETo; el requerimiento de riego se obtiene mediante un balance separado.

Para arroz paddy, el cálculo de riego puede incluir saturación del suelo, percolación/filtración y establecimiento de la lámina de agua, además de ETc y precipitación efectiva. Estos componentes corresponden al módulo de agua de P1 y no se calculan en este módulo.

## Ejecución de pruebas

Desde la raíz del repositorio:

```bash
python -m unittest discover -v
```

Para imprimir un resumen del catálogo y las estrategias:

```bash
python -m src.reglas
```

Las pruebas no validan rendimientos ni sustituyen la revisión de un agrónomo. El MVP presenta criterios y advertencias trazables, no una garantía de resultados por parcela.
