"""
Logica de la app: puntaje de estrategias, recomendacion y calendario de siembra.

IMPORTANTE: esta es una logica de EJEMPLO para que la app funcione desde ya.
Cuando P1 y P4 entreguen su version (src/agua.py y src/reglas.py), se
reemplazan estas funciones por las suyas, manteniendo los mismos nombres.
"""
import math

import pandas as pd

CRITERIOS = {
    "nota_agua": "Ahorrar agua",
    "nota_suelo": "Mejorar el suelo",
    "nota_plagas": "Cortar plagas",
    "nota_ingresos": "Ingresos",
}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def puntajes(est: pd.DataFrame, pesos: dict) -> pd.DataFrame:
    """Agrega la columna 'puntaje' (0 a 10) como promedio ponderado de las notas."""
    total = sum(pesos.values()) or 1
    df = est.copy()
    df["puntaje"] = sum(df[c] * pesos[c] for c in CRITERIOS) / total
    df["puntaje"] = df["puntaje"].round(1)
    return df


def comparar(est: pd.DataFrame, zona_id: int, escenario: str, pesos: dict) -> pd.DataFrame:
    """Las 3 estrategias de una zona y escenario, ordenadas de mejor a peor."""
    df = est[(est["zona_id"] == zona_id) & (est["escenario"] == escenario)]
    return puntajes(df, pesos).sort_values("puntaje", ascending=False).reset_index(drop=True)


def razones(fila: pd.Series, pesos: dict, n: int = 2) -> list[str]:
    """Los criterios que mas aportan al puntaje de una estrategia."""
    aportes = {CRITERIOS[c]: fila[c] * pesos[c] for c in CRITERIOS if pesos[c] > 0}
    return [k for k, _ in sorted(aportes.items(), key=lambda kv: -kv[1])[:n]]


def calendario(clim: pd.DataFrame, cult: pd.DataFrame, serie_zona: pd.DataFrame,
               zona_nombre: str) -> tuple[pd.DataFrame, list[str]]:
    """
    Calendario sugerido por cultivo (filas) y mes (columnas).
    Reglas de ejemplo:
      - Arroz y maiz se siembran al inicio de las lluvias.
      - La soya se siembra al terminar las lluvias, con la humedad que queda.
      - Si en la zona el mes de siembra tuvo agua en superficie (NDWI > 0) en
        2 o mas anios, se marca el riesgo de encharcamiento.
    """
    tipos = clim.sort_values("mes")["tipo_mes"].tolist()
    lluviosos = [i for i, t in enumerate(tipos) if t == "lluvioso"]
    inicio = lluviosos[0] if lluviosos else 0
    fin = lluviosos[-1] if lluviosos else 3

    # anios con agua en superficie por mes, en esta zona
    s = serie_zona.assign(mes=serie_zona["fecha"].dt.month - 1)
    anios_agua = s[s["ndwi"] > 0].groupby("mes")["fecha"].apply(lambda f: f.dt.year.nunique())

    filas, notas = {}, []
    loma = "loma" in zona_nombre.lower()
    for _, c in cult.iterrows():
        nombre = c["cultivo"]
        meses = max(1, math.ceil(c["ciclo_dias"] / 30))
        siembra = (fin + 1) % 12 if nombre.lower().startswith("soya") else inicio
        fila = [""] * 12
        for k in range(meses):
            m = (siembra + k) % 12
            fila[m] = "Siembra" if k == 0 else ("Cosecha" if k == meses - 1 else "Crece")

        n_agua = int(anios_agua.get(siembra, 0))
        if not bool(c["tolera_inundacion"]) and n_agua >= 2:
            notas.append(f"{nombre}: en {MESES[siembra]} hubo agua en superficie en "
                         f"{n_agua} de los últimos años. Riesgo de encharcamiento.")
            fila = ["Riesgo" if v else "" for v in fila]
        if loma and nombre.lower().startswith("arroz"):
            notas.append("Arroz en la loma: necesita mucha más agua que el maíz o la soya.")
            fila = ["Riesgo" if v else "" for v in fila]
        filas[nombre] = fila

    return pd.DataFrame.from_dict(filas, orient="index", columns=MESES), notas
