"""
Datos, filtros y frases del Dashboard (funciones puras: sin Streamlit, faciles de probar).

Todo sale de los archivos reales del equipo que carga utils/carga.py. Las frases de
conclusion se calculan con los datos filtrados; los numeros van con formato de Ecuador
(1.234,5) usando ui.num.
"""
from __future__ import annotations

import pandas as pd

from utils.logica import MESES, MESES_LARGOS

PERIODOS = {"1": "Último año", "2": "Últimos 2 años", "todo": "Todo (2021–2026)"}
TIPOS = {"todos": "Todos", "nino": "🌧️ Muy lluvioso", "normal": "🌤️ Normal", "nina": "☀️ Seco"}
ENSO_DE = {"nino": "nino", "normal": "neutro", "nina": "nina"}      # filtro -> columna enso
ESC_DE_ENSO = {"nino": "nino", "neutro": "normal", "nina": "nina"}  # columna enso -> escenario
ORDEN_ESC = ["nina", "normal", "nino"]


def num(v: float, dec: int = 0) -> str:
    """1234.5 -> '1.234,5' (formato de Ecuador)."""
    texto = f"{v:,.{dec}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def mes_largo(f) -> str:
    f = pd.Timestamp(f)
    return f"{MESES_LARGOS[f.month - 1]} de {f.year}"


def mes_corto(f) -> str:
    f = pd.Timestamp(f)
    return f"{MESES[f.month - 1].lower()} {f.year}"


def capital(texto: str) -> str:
    return texto[:1].upper() + texto[1:]


def rango_meses(meses: list[int]) -> str:
    """[4, 5, ..., 11] (0-11) -> 'mayo a diciembre'."""
    if not meses:
        return ""
    if len(meses) == 1:
        return MESES_LARGOS[meses[0]]
    return f"{MESES_LARGOS[meses[0]]} a {MESES_LARGOS[meses[-1]]}"


# --- Tabla mensual unica (lluvia, balance y satelite) --------------------------------------

def tabla_mensual(imerg: pd.DataFrame | None, power: pd.DataFrame | None,
                  serie: pd.DataFrame | None, clim: pd.DataFrame | None) -> pd.DataFrame:
    """
    Una fila por mes con lo que haya: lluvia IMERG y POWER, agua que se evapora, balance,
    verdor (ndvi), agua en el terreno (ndwi), tipo de año (enso) y lluvia normal del mes.
    """
    partes = []
    if imerg is not None:
        cols = [c for c in ["fecha", "lluvia_mm", "enso", "temporada"] if c in imerg]
        partes.append(imerg[cols].rename(columns={"lluvia_mm": "lluvia_imerg_mm"}))
    if power is not None:
        partes.append(power[["fecha", "lluvia_mm", "et0_mm", "balance_mm"]]
                      .rename(columns={"lluvia_mm": "lluvia_power_mm"}))
    if serie is not None:
        partes.append(serie[["fecha", "ndvi", "ndwi"]])
    if not partes:
        return pd.DataFrame(columns=["fecha"])
    t = partes[0]
    for p in partes[1:]:
        t = t.merge(p, on="fecha", how="outer")
    t["fecha"] = pd.to_datetime(t["fecha"])
    t = t.sort_values("fecha").reset_index(drop=True)
    # Lo normal de cada mes: mediana IMERG de ese mes en toda la serie (si no, la climatologia)
    if "lluvia_imerg_mm" in t:
        normal = t.groupby(t["fecha"].dt.month)["lluvia_imerg_mm"].median()
        t["normal_mm"] = t["fecha"].dt.month.map(normal)
    elif clim is not None:
        t["normal_mm"] = t["fecha"].dt.month.map(dict(zip(clim["mes"], clim["lluvia_mm"])))
    return t


def filtrar(t: pd.DataFrame, periodo: str, tipo: str) -> pd.DataFrame:
    if t.empty:
        return t
    fin = t["fecha"].max()
    if periodo in ("1", "2"):
        desde = fin - pd.DateOffset(months=12 * int(periodo) - 1)
        t = t[t["fecha"] >= desde]
    if tipo != "todos" and "enso" in t:
        t = t[t["enso"] == ENSO_DE[tipo]]
    return t.reset_index(drop=True)


def ticks(fechas: pd.Series) -> tuple[list, list]:
    """
    Marcas del eje de tiempo en español, en dos lineas ('ene' arriba y '2025' abajo) y
    como mucho 6, para que no se monten en la pantalla de un celular (390 px).
    """
    f = pd.Series(pd.to_datetime(fechas)).drop_duplicates().sort_values()
    paso = 2 if len(f) <= 12 else (4 if len(f) <= 24 else 12)
    elegidas = [x for x in f if (x.month - 1) % paso == 0] or list(f)
    return elegidas, [f"{MESES[x.month - 1].lower()}<br>{x.year}" for x in elegidas]


# --- Tarjetas (KPI) -------------------------------------------------------------------------

def kpi_lluvia(t: pd.DataFrame) -> dict | None:
    d = t.dropna(subset=["lluvia_imerg_mm"]) if "lluvia_imerg_mm" in t else None
    if d is None or d.empty:
        return None
    total, normal = d["lluvia_imerg_mm"].sum(), d["normal_mm"].sum()
    pct = (total / normal - 1) * 100 if normal > 0 else 0
    if abs(pct) < 5:
        frase = "parecida a lo normal"
    elif pct > 0:
        frase = f"+{num(pct)} % más que lo normal"
    else:
        frase = f"{num(abs(pct))} % menos que lo normal"
    return {"valor": num(total), "unidad": "mm", "frase": f"{frase} ({len(d)} meses)", "pct": pct}


def kpi_secos(clim: pd.DataFrame) -> dict:
    tipos = clim.sort_values("mes")["tipo_mes"].tolist()
    secos = [i for i, x in enumerate(tipos) if x == "seco"]
    return {"valor": str(len(secos)), "unidad": "de 12",
            "frase": f"de {rango_meses(secos)} llueve menos de la mitad de lo que se evapora"}


def kpi_verdor(t: pd.DataFrame, completa: pd.DataFrame) -> dict | None:
    """Verdor promedio del periodo y su cambio frente a los mismos meses un año antes."""
    d = t.dropna(subset=["ndvi"]) if "ndvi" in t else None
    if d is None or d.empty:
        return None
    media = d["ndvi"].mean()
    previo = completa.set_index("fecha")["ndvi"]
    antes = [previo.get(f - pd.DateOffset(years=1)) for f in d["fecha"]]
    antes = pd.Series(antes, dtype=float).dropna()
    if antes.empty:
        flecha, frase = "", "sin año anterior para comparar"
    else:
        dif = media - antes.mean()
        if dif > 0.02:
            flecha, frase = "↑", f"más verde que el año anterior (+{num(dif, 2)})"
        elif dif < -0.02:
            flecha, frase = "↓", f"menos verde que el año anterior ({num(dif, 2)})"
        else:
            flecha, frase = "→", "parecido al año anterior"
    return {"valor": num(media, 2), "unidad": "", "flecha": flecha,
            "frase": f"{frase}. 0 = suelo pelado, 0,8 = muy verde"}


def kpi_agua(t: pd.DataFrame) -> dict | None:
    d = t.dropna(subset=["ndwi"]) if "ndwi" in t else None
    if d is None or d.empty:
        return None
    n = int((d["ndwi"] > 0).sum())
    frase = (f"de {len(d)} meses con foto del satélite" if n else
             f"en {len(d)} meses con foto el satélite no vio agua acumulada")
    return {"valor": str(n), "unidad": "meses", "frase": frase}


def kpi_hectareas(zonas: pd.DataFrame, zid: int) -> dict:
    total = zonas["area_ha"].sum()
    if zid == 0:
        return {"valor": num(total), "unidad": "ha", "frase": f"las {len(zonas)} zonas de Daule juntas"}
    fila = zonas[zonas["zona_id"] == zid].iloc[0]
    return {"valor": num(fila["area_ha"]), "unidad": "ha",
            "frase": f"el {num(fila['area_ha'] / total * 100)} % de Daule"}


# --- Estrategias ----------------------------------------------------------------------------

NOTAS = ["agua_m3_ha", "nota_agua", "nota_suelo", "nota_plagas", "nota_ingresos"]


def estrategias_zona(est: pd.DataFrame, zonas: pd.DataFrame | None, zid: int) -> pd.DataFrame:
    """Filas de la zona; para 'Todo Daule' (0), promedio de las zonas pesado por su superficie."""
    if zid != 0:
        return est[est["zona_id"] == zid].copy()
    if zonas is None or zonas.empty:
        pesos = est.assign(peso=1.0)
    else:
        pesos = est.merge(zonas[["zona_id", "area_ha"]].rename(columns={"area_ha": "peso"}), on="zona_id")
    filas = []
    for (e, esc), g in pesos.groupby(["estrategia", "escenario"]):
        fila = {"estrategia": e, "zona_id": 0, "escenario": esc}
        for c in NOTAS:
            fila[c] = round(float((g[c] * g["peso"]).sum() / g["peso"].sum()), 1)
        filas.append(fila)
    return pd.DataFrame(filas)


def ahorro_vs_a(est_z: pd.DataFrame, escenario: str, estrategia: str) -> float | None:
    d = est_z[est_z["escenario"] == escenario].set_index("estrategia")["agua_m3_ha"]
    if "A" not in d or estrategia not in d or d["A"] <= 0:
        return None
    return float((1 - d[estrategia] / d["A"]) * 100)


# --- Frases de conclusion -------------------------------------------------------------------

def frase_lluvia(t: pd.DataFrame) -> str:
    col = "lluvia_imerg_mm" if "lluvia_imerg_mm" in t else "lluvia_power_mm"
    d = t.dropna(subset=[col, "normal_mm"]) if col in t and "normal_mm" in t else pd.DataFrame()
    if d.empty:
        return "No hay lluvia para el periodo elegido."
    veces = d[col] / d["normal_mm"].clip(lower=1)
    i = veces.idxmax()
    f, mm, v = d.loc[i, "fecha"], d.loc[i, col], veces[i]
    if v >= 2 and mm > 30:
        return f"{capital(mes_largo(f))} tuvo {num(mm)} mm, unas {num(v)} veces lo normal."
    total, normal = d[col].sum(), d["normal_mm"].sum()
    return (f"En el periodo llovieron {num(total)} mm; lo normal para esos meses es "
            f"{num(normal)} mm.")


def frase_balance(t: pd.DataFrame) -> str:
    d = t.dropna(subset=["balance_mm"]) if "balance_mm" in t else pd.DataFrame()
    if d.empty:
        return "No hay datos de balance para el periodo elegido."
    faltan = d[d["balance_mm"] < 0]
    if faltan.empty:
        return f"En los {len(d)} meses llovió más de lo que se evaporó: no faltó agua."
    peor = faltan.loc[faltan["balance_mm"].idxmin()]
    if len(d) == 1:
        return f"En {mes_largo(peor['fecha'])} faltaron {num(-peor['balance_mm'])} mm de agua."
    return (f"Faltó agua en {len(faltan)} de {len(d)} meses. El peor fue "
            f"{mes_largo(peor['fecha'])}: faltaron {num(-peor['balance_mm'])} mm.")


def frase_verdor(t: pd.DataFrame, completa: pd.DataFrame) -> str:
    d = t.dropna(subset=["ndvi"]) if "ndvi" in t else pd.DataFrame()
    if d.empty:
        return "Las nubes no dejaron ver el campo en el periodo elegido."
    ult = d.iloc[-1]
    tipico = completa[completa["fecha"].dt.month == ult["fecha"].month]["ndvi"].mean()
    nubes = int(t["ndvi"].isna().sum())
    if ult["ndvi"] > tipico + 0.03:
        como = "más verde que otros años"
    elif ult["ndvi"] < tipico - 0.03:
        como = "menos verde que otros años"
    else:
        como = "tan verde como otros años"
    extra = f" {nubes} meses sin foto por nubes." if nubes else ""
    return (f"En {mes_largo(ult['fecha'])} el campo se vio {como} "
            f"({num(ult['ndvi'], 2)} frente a {num(tipico, 2)}).{extra}")


def frase_inundacion(t: pd.DataFrame) -> str:
    d = t.dropna(subset=["ndwi"]) if "ndwi" in t else pd.DataFrame()
    if d.empty:
        return "Las nubes no dejaron ver el agua en el periodo elegido."
    con_agua = d[d["ndwi"] > 0]
    if con_agua.empty:
        mas = d.loc[d["ndwi"].idxmax()]
        return ("En el promedio de todo Daule el satélite no vio agua sobre el terreno. "
                f"El mes más húmedo fue {mes_largo(mas['fecha'])}.")
    meses = con_agua["fecha"].dt.month.value_counts()
    return (f"Se vio agua en el terreno en {len(con_agua)} meses, sobre todo en "
            f"{MESES_LARGOS[meses.index[0] - 1]}.")


def frase_temporadas(temp: pd.DataFrame) -> str:
    if temp.empty:
        return "Todavía no hay temporadas completas."
    mas, menos = temp.loc[temp["lluvia_temporada_mm"].idxmax()], temp.loc[temp["lluvia_temporada_mm"].idxmin()]
    veces = mas["lluvia_temporada_mm"] / menos["lluvia_temporada_mm"]
    return (f"La temporada más lluviosa fue {mas['temporada']} ({num(mas['lluvia_temporada_mm'])} mm), "
            f"{num(veces, 1)} veces la más seca ({menos['temporada']}, "
            f"{num(menos['lluvia_temporada_mm'])} mm).")


def frase_estrategias(est_z: pd.DataFrame, escenario: str, nombre_anio: str) -> str:
    d = est_z[est_z["escenario"] == escenario]
    if d.empty:
        return "No hay datos de agua para este tipo de año."
    mejor = d.loc[d["agua_m3_ha"].idxmin()]
    ahorro = ahorro_vs_a(est_z, escenario, mejor["estrategia"])
    if mejor["estrategia"] == "A" or ahorro is None:
        return f"En un {nombre_anio}, sembrar solo arroz es lo que menos agua pide."
    return (f"En un {nombre_anio}, el plan {mejor['estrategia']} pide {num(ahorro)} % menos agua "
            f"que sembrar solo arroz (A): {num(mejor['agua_m3_ha'])} m³/ha por ciclo.")


def frase_zonas(zonas: pd.DataFrame, zid: int, corto) -> str:
    total = zonas["area_ha"].sum()
    if zid != 0 and (zonas["zona_id"] == zid).any():
        z = zonas[zonas["zona_id"] == zid].iloc[0]
        return (f"Tu zona ({corto(z['nombre_comun']).lower()}) ocupa el "
                f"{num(z['area_ha'] / total * 100)} % de Daule: {num(z['area_ha'])} ha.")
    z = zonas.loc[zonas["area_ha"].idxmax()]
    return (f"La {corto(z['nombre_comun']).lower()} es la más grande: "
            f"{num(z['area_ha'] / total * 100)} % de Daule ({num(z['area_ha'])} ha).")


def frase_relieve(zonas: pd.DataFrame, corto) -> str:
    alta = zonas.loc[zonas["elevacion"].idxmax()]
    empinada = zonas.loc[zonas["pendiente"].idxmax()]
    return (f"La {corto(alta['nombre_comun']).lower()} es la más alta ({num(alta['elevacion'], 1)} m) y "
            f"la {corto(empinada['nombre_comun']).lower()} la de más pendiente "
            f"({num(empinada['pendiente'], 1)}°).")


def csv_ecuador(df: pd.DataFrame) -> bytes:
    """CSV para Excel en español: separador ';', decimales con coma y tildes (UTF-8 con BOM)."""
    salida = df.copy()
    for c in salida.columns:
        if pd.api.types.is_datetime64_any_dtype(salida[c]):
            salida[c] = salida[c].dt.strftime("%Y-%m")
    return salida.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


# --- Infografia: titular, pictogramas, meses especiales y conclusiones ----------------------

PERIODO_TXT = {"1": "Este año", "2": "En los últimos 2 años", "todo": "Entre 2021 y 2026"}
ICONO_TIPO_MES = {"lluvioso": "🌧️", "transicion": "⛅", "seco": "☀️"}


def tipos_mes(clim: pd.DataFrame | None) -> dict:
    """{1: 'transicion', 2: 'lluvioso', ...} segun la climatologia (año tipico)."""
    if clim is None:
        return {}
    return dict(zip(clim["mes"].astype(int), clim["tipo_mes"]))


def especiales(t: pd.DataFrame) -> pd.DataFrame:
    """Meses con muchisima mas lluvia de lo normal (mas de 3 veces y 50 mm por encima)."""
    if "lluvia_imerg_mm" not in t or "normal_mm" not in t:
        return t.iloc[0:0]
    d = t.dropna(subset=["lluvia_imerg_mm", "normal_mm"])
    raro = d["lluvia_imerg_mm"] > (3 * d["normal_mm"]).clip(lower=d["normal_mm"] + 50)
    d = d[raro].assign(veces=lambda x: x["lluvia_imerg_mm"] / x["normal_mm"].clip(lower=1))
    return d.sort_values("veces", ascending=False)


def fuera_de_temporada(t: pd.DataFrame, clim: pd.DataFrame | None) -> pd.DataFrame:
    """Meses especiales que cayeron en la temporada seca del año tipico."""
    tipos = tipos_mes(clim)
    e = especiales(t)
    return e[e["fecha"].dt.month.map(tipos) == "seco"] if tipos else e.iloc[0:0]


def titular(t: pd.DataFrame, clim: pd.DataFrame | None, periodo: str) -> str:
    """Una frase que resume lo mas importante del periodo elegido."""
    cuando = PERIODO_TXT.get(periodo, "En el periodo")
    if 0 < len(t) < 3:
        return (f"{cuando} solo {'hay 1 mes' if len(t) == 1 else f'hay {len(t)} meses'} de ese tipo de año. "
                "Para comparar mejor, elige «Todo (2021–2026)».")
    fuera = fuera_de_temporada(t, clim)
    if not fuera.empty:
        f = fuera.iloc[0]
        return (f"{cuando} llovió fuera de temporada: {mes_largo(f['fecha'])} tuvo "
                f"{num(f['lluvia_imerg_mm'])} mm en plena época seca.")
    k = kpi_lluvia(t)
    if k and k["pct"] > 20:
        return f"{cuando} llovió más de lo normal: {num(k['pct'])}\u00a0% más."
    if k and k["pct"] < -20:
        return f"{cuando} llovió menos de lo normal: {num(-k['pct'])}\u00a0% menos."
    if "balance_mm" in t and t["balance_mm"].notna().any():
        d = t.dropna(subset=["balance_mm"])
        return (f"{cuando} faltó agua en {int((d['balance_mm'] < 0).sum())} de {len(d)} meses: "
                "el riego es clave en la época seca.")
    return f"{cuando} en Daule, según los satélites de la NASA."


def iconos(icono: str, llenos: float, total: int | None = None, vacio: str | None = None,
           medio: bool = True) -> str:
    """
    Pictograma HTML: 'llenos' iconos encendidos (con medio icono si sobra 0,5 o mas) y el
    resto, hasta 'total', apagados. Ej.: iconos('💧', 3.6, 5) -> 💧💧💧💧(tenue)💧(apagado).
    """
    enteros = int(llenos)
    partes = [f"<span>{icono}</span>"] * enteros
    if medio and llenos - enteros >= 0.5:
        partes.append(f'<span class="medio">{icono}</span>')
    if total:
        partes += [f'<span class="off">{vacio or icono}</span>'] * max(0, total - len(partes))
    return f'<span class="iconos">{"".join(partes)}</span>'


def waffle(valores: list[float], n: int = 10) -> list[int]:
    """Reparte n casillas segun la proporcion de cada valor (resto mayor), suma exacta n."""
    total = sum(valores) or 1
    exactos = [v / total * n for v in valores]
    base = [int(x) for x in exactos]
    for i in sorted(range(len(valores)), key=lambda i: exactos[i] - base[i], reverse=True)[:n - sum(base)]:
        base[i] += 1
    return base


def conclusiones(completa: pd.DataFrame, clim: pd.DataFrame | None, est_z: pd.DataFrame | None,
                 zonas: pd.DataFrame | None, escenario: str, nombre_anio: str, zona_txt: str,
                 corto) -> list[dict]:
    """3 a 4 conclusiones en lenguaje simple (se omiten las que no tienen datos)."""
    salida = []
    tipos = tipos_mes(clim)
    if tipos:
        lluvia = [m - 1 for m in sorted(tipos) if tipos[m] != "seco"]
        seco = [m - 1 for m in sorted(tipos) if tipos[m] == "seco"]
        salida.append({"icono": "🌦️", "titulo": "Dos temporadas muy distintas",
                       "texto": f"Llueve de {rango_meses(lluvia)}. De {rango_meses(seco)} casi no "
                                f"llueve: son {len(seco)} meses en los que el cultivo depende del riego.",
                       "fuente": "NASA POWER"})
    fuera = fuera_de_temporada(completa, clim)
    e = fuera if not fuera.empty else especiales(completa)
    if not e.empty:
        f = e.iloc[0]
        lugar = "en plena época seca" if not fuera.empty else "mucho más de lo normal"
        salida.append({"icono": "⚠️", "titulo": "La lluvia puede sorprender",
                       "texto": f"En {mes_largo(f['fecha'])} cayeron {num(f['lluvia_imerg_mm'])} mm, "
                                f"{lugar}: unas {num(f['veces'])} veces lo normal. Conviene tener "
                                "drenajes limpios todo el año.",
                       "fuente": "GPM IMERG"})
    if est_z is not None and not est_z.empty:
        d = est_z[est_z["escenario"] == escenario]
        if not d.empty and "A" in set(d["estrategia"]):
            mejor = d.loc[d["agua_m3_ha"].idxmin()]
            ahorro = ahorro_vs_a(est_z, escenario, mejor["estrategia"])
            if mejor["estrategia"] != "A" and ahorro:
                salida.append({"icono": "🌾", "titulo": "Rotar cultivos ahorra agua",
                               "texto": f"En {zona_txt}, en un {nombre_anio}, el plan {mejor['estrategia']} "
                                        f"usa {num(ahorro)}\u00a0% menos agua de riego que sembrar solo "
                                        "arroz todo el año.",
                               "fuente": "Balance FAO-56 (P1) y reglas de P4"})
    if zonas is not None and not zonas.empty:
        total = zonas["area_ha"].sum()
        grande = zonas.loc[zonas["area_ha"].idxmax()]
        texto = (f"La {corto(grande['nombre_comun']).lower()} es el "
                 f"{num(grande['area_ha'] / total * 100)}\u00a0% de Daule")
        if "elevacion" in zonas:
            alta = zonas.loc[zonas["elevacion"].idxmax()]
            texto += (f"; la {corto(alta['nombre_comun']).lower()}, la parte más alta "
                      f"({num(alta['elevacion'], 1)} m), es el {num(alta['area_ha'] / total * 100)}\u00a0%")
        salida.append({"icono": "🗺️", "titulo": "Un territorio casi plano", "texto": texto + ".",
                       "fuente": "SRTM (P3)"})
    return salida
