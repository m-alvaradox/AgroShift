"""Catálogo, estrategias de rotación y reglas agronómicas de AgroShift.

El módulo es independiente de Streamlit y de los módulos de clima/agua. Los
consumidores reciben estructuras Python simples para integrarlas en la interfaz
o en los cálculos de otros componentes.
"""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
RUTA_CATALOGO = BASE_DIR / "data" / "cultivos.csv"
RUTA_REGLAS = BASE_DIR / "data" / "reglas.json"

# Las temporadas son etiquetas del piloto de Daule, no fechas fijas de siembra.
_DEFINICIONES_ESTRATEGIAS: tuple[dict[str, Any], ...] = (
    {
        "id": "A",
        "nombre": "Continuidad de arroz",
        "descripcion": (
            "Arroz en la época lluviosa seguido de arroz en la época seca. "
            "Representa la práctica de referencia arroz-arroz."
        ),
        "horizonte_anios": 1,
        "secuencia": (
            {"anio": 1, "temporada": "lluviosa", "cultivo": "arroz"},
            {"anio": 1, "temporada": "seca", "cultivo": "arroz"},
        ),
    },
    {
        "id": "B",
        "nombre": "Rotación arroz-soya",
        "descripcion": (
            "Arroz en la época lluviosa seguido de soya en la época seca. "
            "La opción depende de disponer de drenaje adecuado."
        ),
        "horizonte_anios": 1,
        "secuencia": (
            {"anio": 1, "temporada": "lluviosa", "cultivo": "arroz"},
            {"anio": 1, "temporada": "seca", "cultivo": "soya"},
        ),
    },
    {
        "id": "C",
        "nombre": "Rotación diversificada de dos años",
        "descripcion": (
            "Año 1: arroz en época lluviosa y soya en época seca. "
            "Año 2: maíz duro amarillo en época lluviosa y soya en época seca."
        ),
        "horizonte_anios": 2,
        "secuencia": (
            {"anio": 1, "temporada": "lluviosa", "cultivo": "arroz"},
            {"anio": 1, "temporada": "seca", "cultivo": "soya"},
            {"anio": 2, "temporada": "lluviosa", "cultivo": "maiz_duro_amarillo"},
            {"anio": 2, "temporada": "seca", "cultivo": "soya"},
        ),
    },
)

_TIPOS_CONDICION = {
    "cultivo_incluido",
    "repeticion_consecutiva",
    "drenaje",
    "anegamiento",
}


def _parsear_bool(valor: Any, *, campo: str, fila: int) -> bool:
    """Convierte valores booleanos habituales del CSV o produce un error explícito."""
    texto = str(valor).strip().lower()
    if texto in {"true", "1", "si", "sí", "yes"}:
        return True
    if texto in {"false", "0", "no"}:
        return False
    raise ValueError(
        f"Valor booleano inválido en fila {fila}, campo '{campo}': {valor!r}"
    )


def _parsear_numero(
    valor: Any,
    *,
    campo: str,
    fila: int,
    entero: bool = False,
) -> int | float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Valor numérico inválido en fila {fila}, campo '{campo}': {valor!r}"
        ) from exc

    if not math.isfinite(numero):
        raise ValueError(
            f"El campo '{campo}' debe ser un número finito en la fila {fila}."
        )
    if entero:
        if not numero.is_integer():
            raise ValueError(
                f"El campo '{campo}' debe ser entero en la fila {fila}."
            )
        return int(numero)
    return numero


def cargar_catalogo(ruta: str | Path = RUTA_CATALOGO) -> dict[str, dict[str, Any]]:
    """Carga y valida el catálogo CSV; devuelve un diccionario indexado por cultivo.

    Se prefieren etc_min_mm y etc_max_mm. Si un CSV antiguo todavía no los contiene,
    agua_min_mm y agua_max_mm se leen como alias temporales. Si ambos pares existen,
    deben coincidir para evitar ambigüedad.
    """
    ruta = Path(ruta)
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el catálogo de cultivos: {ruta}")

    with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        encabezados = set(lector.fieldnames or [])

        campos_base = {
            "cultivo",
            "ciclo_dias",
            "kc_ini",
            "kc_med",
            "kc_fin",
            "tolera_inundacion",
        }
        faltantes = campos_base - encabezados
        if faltantes:
            raise ValueError(
                "Faltan columnas obligatorias en data/cultivos.csv: "
                + ", ".join(sorted(faltantes))
            )

        tiene_etc = {"etc_min_mm", "etc_max_mm"}.issubset(encabezados)
        tiene_alias = {"agua_min_mm", "agua_max_mm"}.issubset(encabezados)
        if not tiene_etc and not tiene_alias:
            raise ValueError(
                "El catálogo debe incluir etc_min_mm/etc_max_mm o, temporalmente, "
                "agua_min_mm/agua_max_mm."
            )

        catalogo: dict[str, dict[str, Any]] = {}
        for fila, registro in enumerate(lector, start=2):
            cultivo = (registro.get("cultivo") or "").strip()
            if not cultivo:
                raise ValueError(f"Identificador de cultivo vacío en la fila {fila}.")
            if cultivo in catalogo:
                raise ValueError(
                    f"Identificador de cultivo duplicado en la fila {fila}: {cultivo}"
                )

            ciclo = _parsear_numero(
                registro.get("ciclo_dias"),
                campo="ciclo_dias",
                fila=fila,
                entero=True,
            )
            if ciclo <= 0:
                raise ValueError(f"ciclo_dias debe ser positivo en la fila {fila}.")

            kc = {
                campo: _parsear_numero(
                    registro.get(campo), campo=campo, fila=fila
                )
                for campo in ("kc_ini", "kc_med", "kc_fin")
            }
            if any(valor < 0 for valor in kc.values()):
                raise ValueError(
                    f"Los coeficientes Kc no pueden ser negativos (fila {fila})."
                )

            min_campo = "etc_min_mm" if tiene_etc else "agua_min_mm"
            max_campo = "etc_max_mm" if tiene_etc else "agua_max_mm"
            etc_min = _parsear_numero(
                registro.get(min_campo), campo=min_campo, fila=fila
            )
            etc_max = _parsear_numero(
                registro.get(max_campo), campo=max_campo, fila=fila
            )
            if etc_min < 0 or etc_max < 0 or etc_min > etc_max:
                raise ValueError(
                    f"Rango ETc inválido en la fila {fila}: {etc_min}–{etc_max} mm."
                )

            # Los nombres antiguos se conservan como alias, no como requerimiento
            # de riego. Mientras coexistan, deben duplicar el rango ETc.
            if tiene_etc and tiene_alias:
                agua_min = _parsear_numero(
                    registro.get("agua_min_mm"), campo="agua_min_mm", fila=fila
                )
                agua_max = _parsear_numero(
                    registro.get("agua_max_mm"), campo="agua_max_mm", fila=fila
                )
                if agua_min != etc_min or agua_max != etc_max:
                    raise ValueError(
                        f"Las columnas agua_* deben coincidir con etc_* "
                        f"mientras sean alias (fila {fila})."
                    )

            catalogo[cultivo] = {
                "cultivo": cultivo,
                "ciclo_dias": ciclo,
                **kc,
                "tolera_inundacion": _parsear_bool(
                    registro.get("tolera_inundacion"),
                    campo="tolera_inundacion",
                    fila=fila,
                ),
                "etc_min_mm": etc_min,
                "etc_max_mm": etc_max,
            }

            if tiene_alias:
                catalogo[cultivo]["agua_min_mm"] = _parsear_numero(
                    registro.get("agua_min_mm"),
                    campo="agua_min_mm",
                    fila=fila,
                )
                catalogo[cultivo]["agua_max_mm"] = _parsear_numero(
                    registro.get("agua_max_mm"),
                    campo="agua_max_mm",
                    fila=fila,
                )

    if not catalogo:
        raise ValueError("El catálogo no contiene cultivos.")
    return catalogo


def cargar_reglas(ruta: str | Path = RUTA_REGLAS) -> list[dict[str, Any]]:
    """Carga reglas JSON y verifica su estructura mínima."""
    ruta = Path(ruta)
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo de reglas: {ruta}")

    with ruta.open("r", encoding="utf-8") as archivo:
        reglas = json.load(archivo)

    if not isinstance(reglas, list):
        raise ValueError("data/reglas.json debe contener una lista de reglas.")

    ids: set[str] = set()
    for indice, regla in enumerate(reglas, start=1):
        if not isinstance(regla, dict):
            raise ValueError(f"La regla #{indice} debe ser un objeto JSON.")

        faltantes = {
            "id", "texto_campo", "condicion", "evidencia", "zona_id"
        } - set(regla)
        if faltantes:
            raise ValueError(
                f"Faltan claves en la regla #{indice}: "
                + ", ".join(sorted(faltantes))
            )

        regla_id = str(regla["id"]).strip()
        if not regla_id or regla_id in ids:
            raise ValueError(f"ID de regla vacío o duplicado: {regla_id!r}")
        ids.add(regla_id)

        if not str(regla["texto_campo"]).strip():
            raise ValueError(f"texto_campo vacío en la regla {regla_id}.")
        if not isinstance(regla["condicion"], dict):
            raise ValueError(f"condicion debe ser un objeto en la regla {regla_id}.")
        tipo = regla["condicion"].get("tipo")
        if tipo not in _TIPOS_CONDICION:
            raise ValueError(
                f"Tipo de condición no soportado en {regla_id}: {tipo!r}"
            )
        if not str(regla["evidencia"]).strip():
            raise ValueError(f"evidencia vacía en la regla {regla_id}.")

    return reglas


def obtener_estrategias(
    catalogo: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Devuelve las tres estrategias con secuencia y resúmenes de referencia.

    Los totales ETc suman los rangos de cada ciclo incluido en el horizonte de la
    estrategia. Son acumulados de consumo de cultivo, no volúmenes de riego.
    """
    catalogo = catalogo or cargar_catalogo()
    estrategias: list[dict[str, Any]] = []

    for definicion in _DEFINICIONES_ESTRATEGIAS:
        secuencia: list[dict[str, Any]] = []
        dias_totales = 0
        etc_min_total = 0.0
        etc_max_total = 0.0

        for paso in definicion["secuencia"]:
            cultivo_id = paso["cultivo"]
            if cultivo_id not in catalogo:
                raise ValueError(
                    f"La estrategia {definicion['id']} requiere el cultivo "
                    f"'{cultivo_id}', ausente del catálogo."
                )
            datos_cultivo = catalogo[cultivo_id]
            secuencia.append(
                {
                    **paso,
                    "nombre_cultivo": cultivo_id.replace("_", " ").title(),
                    "ciclo_dias": datos_cultivo["ciclo_dias"],
                    "etc_min_mm": datos_cultivo["etc_min_mm"],
                    "etc_max_mm": datos_cultivo["etc_max_mm"],
                }
            )
            dias_totales += datos_cultivo["ciclo_dias"]
            etc_min_total += datos_cultivo["etc_min_mm"]
            etc_max_total += datos_cultivo["etc_max_mm"]

        estrategias.append(
            {
                "id": definicion["id"],
                "nombre": definicion["nombre"],
                "descripcion": definicion["descripcion"],
                "horizonte_anios": definicion["horizonte_anios"],
                "secuencia": secuencia,
                "dias_totales_referencia": dias_totales,
                "etc_acumulada_referencia_mm": {
                    "min": round(etc_min_total, 2),
                    "max": round(etc_max_total, 2),
                },
            }
        )

    return estrategias


def _normalizar_etiqueta(valor: Any) -> str:
    return str(valor).strip().lower().replace(" ", "_") if valor is not None else ""


def _evaluar_condicion(
    condicion: Mapping[str, Any],
    secuencia: Sequence[Mapping[str, Any]],
    contexto: Mapping[str, Any],
) -> str | None:
    """Evalúa uno de los tipos de condición documentados en data/reglas.json."""
    cultivos = [paso["cultivo"] for paso in secuencia]
    tipo = condicion["tipo"]

    if tipo == "cultivo_incluido":
        afectados = set(condicion.get("cultivos", []))
        return (
            condicion.get("estado", "informacion")
            if afectados.intersection(cultivos)
            else None
        )

    if tipo == "repeticion_consecutiva":
        cultivo_objetivo = condicion["cultivo"]
        minimo = int(condicion.get("min_repeticiones", 2))
        repeticiones = 1
        mayor_repeticion = 1
        anterior: str | None = None
        for cultivo in cultivos:
            if cultivo == anterior == cultivo_objetivo:
                repeticiones += 1
            else:
                repeticiones = 1
            mayor_repeticion = max(mayor_repeticion, repeticiones)
            anterior = cultivo
        return (
            condicion.get("estado", "advertencia")
            if mayor_repeticion >= minimo
            else None
        )

    if tipo == "drenaje":
        afectados = set(condicion.get("cultivos", []))
        if not afectados.intersection(cultivos):
            return None

        campo = condicion.get("campo", "drenaje")
        drenaje = _normalizar_etiqueta(contexto.get(campo))
        if not drenaje:
            return "pendiente_validacion"

        valores_no_aptos = {
            _normalizar_etiqueta(valor)
            for valor in condicion.get("valores_no_aptos", [])
        }
        if drenaje in valores_no_aptos:
            return "alerta"
        valores_aptos = {
            _normalizar_etiqueta(valor)
            for valor in condicion.get("valores_aptos", [])
        }
        if drenaje in valores_aptos:
            return "condicion_favorable"
        return "pendiente_validacion"

    if tipo == "anegamiento":
        afectados = set(condicion.get("cultivos", []))
        if not afectados.intersection(cultivos):
            return None

        campo = condicion.get("campo", "riesgo_anegamiento")
        riesgo = contexto.get(campo)
        if riesgo is None or str(riesgo).strip() == "":
            return "pendiente_validacion"

        if isinstance(riesgo, str):
            riesgo_normalizado = _normalizar_etiqueta(riesgo)
            if riesgo_normalizado in {"true", "1", "si", "sí", "alto", "muy_alto"}:
                riesgo = True
            elif riesgo_normalizado in {"false", "0", "no", "bajo", "sin_riesgo"}:
                riesgo = False
            else:
                return "pendiente_validacion"
        return "alerta" if bool(riesgo) else "condicion_favorable"

    raise ValueError(f"Tipo de condición no soportado: {tipo!r}")


def evaluar_reglas(
    estrategia_id: str,
    contexto: Mapping[str, Any] | None = None,
    *,
    catalogo: Mapping[str, Mapping[str, Any]] | None = None,
    reglas: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Evalúa reglas para una estrategia y un contexto opcional de zona.

    Contexto reconocido:
    - zona_id: identificador de la zona (si la regla se restringe a una zona).
    - drenaje: etiqueta como bueno, moderado o deficiente.
    - riesgo_anegamiento: booleano o etiqueta equivalente (alto/bajo).

    Si falta un dato de drenaje/anegamiento, se devuelve pendiente_validacion. La
    ausencia de información no se interpreta como una condición favorable.
    """
    contexto = contexto or {}
    catalogo = catalogo or cargar_catalogo()
    estrategias = obtener_estrategias(catalogo)
    estrategia = next(
        (item for item in estrategias if item["id"] == estrategia_id),
        None,
    )
    if estrategia is None:
        ids = ", ".join(item["id"] for item in estrategias)
        raise ValueError(
            f"Estrategia desconocida: {estrategia_id!r}. Opciones: {ids}."
        )

    reglas_activas = list(reglas) if reglas is not None else cargar_reglas()
    resultados: list[dict[str, Any]] = []

    for regla in reglas_activas:
        zona_regla = regla["zona_id"]
        zona_contexto = contexto.get("zona_id")
        if zona_regla is not None and zona_contexto != zona_regla:
            continue

        estado = _evaluar_condicion(
            regla["condicion"],
            estrategia["secuencia"],
            contexto,
        )
        if estado is None:
            continue

        resultados.append(
            {
                "id": regla["id"],
                "texto_campo": regla["texto_campo"],
                "estado": estado,
                "evidencia": regla["evidencia"],
                "zona_id": zona_regla,
            }
        )

    return resultados


if __name__ == "__main__":
    catalogo = cargar_catalogo()
    print(f"Catálogo cargado: {len(catalogo)} cultivos")
    for estrategia in obtener_estrategias(catalogo):
        etc = estrategia["etc_acumulada_referencia_mm"]
        print(
            f"{estrategia['id']} — {estrategia['nombre']}: "
            f"{estrategia['dias_totales_referencia']} días de ciclo acumulado; "
            f"ETc acumulada de referencia {etc['min']:.0f}–{etc['max']:.0f} mm"
        )
