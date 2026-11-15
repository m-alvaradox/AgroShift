"""
Dashboard ilustrativo: "Daule en datos de la NASA", como una infografia.

De arriba hacia abajo:
  1. Portada: titulo grande, una frase que resume lo mas importante y tarjetas con
     pictogramas (gotas, soles, plantas, zonas, cultivos).
  2. "El año en Daule": franja de 12 meses y lluvia real frente a lo normal, con anotaciones.
  3. Graficos con icono, pregunta, conclusion arriba, fondos por temporada y anotaciones.
  4. "Lo que nos dicen los datos": 3 a 4 conclusiones en tarjetas.
Los filtros (zona, periodo, tipo de año) y las descargas van en el desplegable "Ajustar filtros".
Solo datos reales: si falta un archivo, esa seccion muestra un aviso y el resto sigue.
"""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils import carga, logica, ui
from utils import tablero as tb

ss = st.session_state
FUENTE = dict(family="Nunito, system-ui, sans-serif", size=13, color="#1F2A1F")
CONFIG = {"displayModeBar": False}
# Fondo de cada temporada detras de los graficos de tiempo
FONDO = {"lluvioso": "rgba(30,136,229,.13)", "transicion": "rgba(30,136,229,.06)", "seco": "rgba(249,168,37,.16)"}
ICONO_CULTIVO = {"Arroz": "🌾", "Soya": "🫘", "Maíz duro": "🌽"}
NOMBRE_PLAN = {"A": "Siempre arroz", "B": "Arroz y soya", "C": "Rotación de 2 años"}
ICONO_ANIO = {"nino": "🌧️", "normal": "🌤️", "nina": "☀️"}
descargas: dict[str, pd.DataFrame] = {}


def hay(nombre: str) -> bool:
    return carga.disponible(nombre)


def leer(nombre: str, cargador):
    return cargador() if hay(nombre) else None


# --- Datos reales (cada uno puede faltar) -----------------------------------------------------
imerg = leer("lluvia_imerg_daule.csv", carga.lluvia_imerg)
power = leer("clima_mensual_daule.csv", carga.clima_mensual)
clim = leer("climatologia_daule.csv", carga.climatologia)
serie_todo = leer("series_zonas.csv", carga.series)
zonas = carga.tabla_zonas().sort_values("zona_id").reset_index(drop=True) if hay("zonas_daule.geojson") else None
est = leer("estrategias.csv", carga.estrategias)

# --- Filtros, dentro del desplegable "Ajustar filtros" ------------------------------------------
opciones_zona = [0] + ([int(z) for z in zonas["zona_id"]] if zonas is not None else [])
nombres_zona = dict(zip(zonas["zona_id"].astype(int), zonas["nombre_comun"])) if zonas is not None else {}
if ss.get("dash_zona") not in opciones_zona:
    ss["dash_zona"] = ss.get("zona_id") if ss.get("zona_id") in opciones_zona else 0
if ss.get("dash_periodo") not in tb.PERIODOS:
    ss["dash_periodo"] = "1"
if ss.get("dash_tipo") not in tb.TIPOS:
    ss["dash_tipo"] = "todos"


def _sincronizar_zona():
    if ss["dash_zona"]:  # la zona elegida aqui tambien queda para las otras paginas
        ss["zona_id"] = ss["dash_zona"]


def _sincronizar_tipo():
    if ss.get("dash_tipo") and ss["dash_tipo"] != "todos":
        ss["escenario"] = ss["dash_tipo"]


def nombre_zona(z: int) -> str:
    return "🗺️ Todo Daule" if z == 0 else ui.etiqueta_zona(nombres_zona[z])


panel = st.expander("⚙️ Ajustar filtros y descargar datos")
with panel:
    c1, c2, c3 = st.columns([1.1, 1.4, 1.6])
    c1.selectbox("Zona", opciones_zona, key="dash_zona", on_change=_sincronizar_zona, format_func=nombre_zona)
    c2.segmented_control("Periodo", list(tb.PERIODOS), key="dash_periodo", required=True,
                         format_func=lambda p: tb.PERIODOS[p], width="stretch", wrap=True)
    c3.segmented_control("Tipo de año", list(tb.TIPOS), key="dash_tipo", required=True,
                         on_change=_sincronizar_tipo, format_func=lambda t: tb.TIPOS[t],
                         width="stretch", wrap=True)

zid = ss["dash_zona"] or 0
periodo = ss["dash_periodo"] or "1"
tipo = ss["dash_tipo"] or "todos"
escenario = tipo if tipo != "todos" else "normal"
nombre_anio = ui.NOMBRE_ESC[escenario].lower()
zona_txt = "todo Daule" if zid == 0 else f"la {ui.corto_zona(nombres_zona[zid]).lower()}"

completa = tb.tabla_mensual(imerg, power, serie_todo[serie_todo["zona_id"] == 0] if serie_todo is not None
                            else None, clim)
t = tb.filtrar(completa, periodo, tipo)
est_z = tb.estrategias_zona(est, zonas, zid) if est is not None else None
tipos_mes = tb.tipos_mes(clim)


# --- Piezas comunes ---------------------------------------------------------------------------

def falta(*nombres: str) -> bool:
    ausentes = [n for n in nombres if not hay(n)]
    for n in ausentes:
        st.warning(f"Falta este dato ({n}): lo entrega {carga.FaltaArchivo(n).responsable}.", icon="📭")
    return bool(ausentes)


def seccion(icono: str, pregunta: str, conclusion: str | None = None):
    """Icono y pregunta grandes, y la conclusion bien visible ARRIBA del grafico."""
    ui.html(f'<div class="sec-cab"><span class="sec-ico">{icono}</span><span class="sec-tit">{pregunta}</span></div>')
    if conclusion:
        ui.html(f'<div class="conclusion">💡 {conclusion}</div>')


def fuente(texto: str):
    ui.html(f'<div class="fuente-peq">Fuente: {texto}</div>')


def estilo(fig, alto: int = 280, leyenda: bool = False, arriba: int = 14):
    fig.update_layout(
        height=alto, margin=dict(l=4, r=10, t=(38 if leyenda else arriba), b=4), separators=",.",
        font=FUENTE, plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)", showlegend=leyenda,
        bargap=0.22, legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=12)),
        hoverlabel=dict(font=dict(family=FUENTE["family"], size=13)))
    fig.update_xaxes(showgrid=False, fixedrange=True)
    fig.update_yaxes(gridcolor="#EDF1EA", zerolinecolor="#90A4AE", fixedrange=True)
    return fig


def mostrar(fig):
    st.plotly_chart(fig, width="stretch", config=CONFIG)


def eje_tiempo(fig, fechas):
    vals, textos = tb.ticks(fechas)
    fig.update_xaxes(tickvals=vals, ticktext=textos, tickangle=0)


def sombrear(fig, fechas):
    """Fondo azul claro en la temporada de lluvias y mostaza claro en la seca (año tipico)."""
    if not tipos_mes:
        return
    f = pd.Series(pd.to_datetime(fechas)).drop_duplicates().sort_values().tolist()
    grupos, ini = [], 0
    for i in range(1, len(f) + 1):
        if i == len(f) or tipos_mes.get(f[i].month) != tipos_mes.get(f[ini].month):
            grupos.append((f[ini], f[i - 1], tipos_mes.get(f[ini].month)))
            ini = i
    for a, b, tipo_m in grupos:
        if tipo_m in FONDO:
            fig.add_vrect(x0=a - pd.Timedelta(days=15), x1=b + pd.Timedelta(days=15),
                          fillcolor=FONDO[tipo_m], line_width=0, layer="below")


def ley_temporadas():
    ui.html('<div class="graf-ley"><i style="background:#DCEBFA"></i>Temporada de lluvias'
            '<i style="background:#FDF0D3"></i>Temporada seca</div>')


def anotar(fig, x, y, texto: str, frac: float, color: str, abajo: bool = False, **extra):
    """Flecha con texto que no se sale por los lados: se abre hacia el centro del grafico."""
    if frac > 0.72:
        xanchor, ax = "right", -22
    elif frac < 0.28:
        xanchor, ax = "left", 22
    else:
        xanchor, ax = "center", 0
    fig.add_annotation(x=x, y=y, text=texto, showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.6,
                       arrowcolor=color, ax=ax, ay=34 if abajo else -34, xanchor=xanchor,
                       font=dict(size=12, color=color, family=FUENTE["family"]),
                       bgcolor="rgba(255,255,255,.92)", bordercolor=color, borderwidth=1, borderpad=3, **extra)


def fraccion(fechas: pd.Series, f) -> float:
    a, b = fechas.min(), fechas.max()
    return 0.5 if a == b else (f - a) / (b - a)


# --- 1. Portada --------------------------------------------------------------------------------
frase = tb.titular(t, clim, periodo) if not t.empty else "No hay meses para los filtros elegidos."
chips = [nombre_zona(zid), tb.PERIODOS[periodo],
         "Todos los años" if tipo == "todos" else ui.NOMBRE_ESC[tipo]]
ui.html('<div class="hero"><div class="hero-sat">🛰️ Satélites de la NASA · Equipo AgroShift</div>'
        '<div class="hero-tit">Daule en datos de la NASA</div>'
        f'<div class="hero-frase">{frase}</div>'
        f'<div class="chips">{"".join(f"<span>{c}</span>" for c in chips)}'
        '<span class="chip-ayuda">⚙️ Cámbialo en «Ajustar filtros»</span></div></div>')
if tipo != "todos" and imerg is None:
    st.warning("El filtro de tipo de año necesita lluvia_imerg_daule.csv (lo entrega P1).", icon="📭")
if t.empty and not completa.empty:
    st.info("No hay meses de ese tipo de año en el periodo elegido. Prueba con «Todo (2021–2026)».",
            icon="ℹ️")


def tarjeta(color: str, icono: str, titulo: str, numero: str, cuerpo: str, frase_: str) -> str:
    return (f'<div class="picto {color}"><div class="picto-cab"><span class="picto-ico">{icono}</span>'
            f'<span class="picto-tit">{titulo}</span></div><div class="picto-num">{numero}</div>'
            f'{cuerpo}<div class="picto-frase">{frase_}</div></div>')


def tarjeta_falta(color: str, icono: str, titulo: str, archivo: str) -> str:
    resp = carga.FaltaArchivo(archivo).responsable if not hay(archivo) else None
    texto = f"Falta este dato: lo entrega {resp}." if resp else "Sin datos para los filtros elegidos."
    return tarjeta(color, icono, titulo, "—", "", texto)


def fila(etq: str, contenido: str) -> str:
    return f'<div class="picto-fila"><span class="picto-etq">{etq}</span>{contenido}</div>'


tarjetas = []
# Lluvia: 5 gotas = lo normal; cada gota es un 20 % de lo normal
k = tb.kpi_lluvia(t)
if k:
    gotas = min(12, max(0.0, 5 * (1 + k["pct"] / 100)))
    tarjetas.append(tarjeta("azul", "💧", "Lluvia del periodo", f'{k["valor"]} <small>mm</small>',
                            fila("Lo normal", tb.iconos("💧", 5)) +
                            fila("Real", tb.iconos("💧", gotas) + ("<b>+</b>" if gotas >= 12 else "")),
                            k["frase"].split(" (")[0].capitalize() + ". Cada 💧 = 20 % de lo normal."))
else:
    tarjetas.append(tarjeta_falta("azul", "💧", "Lluvia del periodo", "lluvia_imerg_daule.csv"))
# Meses secos: un sol por cada mes seco del año tipico
if clim is not None:
    s = tb.kpi_secos(clim)
    tarjetas.append(tarjeta("amarillo", "☀️", "Meses secos del año", f'{s["valor"]} <small>de 12</small>',
                            fila("", tb.iconos("☀️", int(s["valor"]), 12, vacio="🌧️")),
                            f'{tb.capital(s["frase"])}.'))
else:
    tarjetas.append(tarjeta_falta("amarillo", "☀️", "Meses secos del año", "climatologia_daule.csv"))
# Verdor: 5 plantas = muy verde (0,8)
v = tb.kpi_verdor(t, completa) if "ndvi" in t else None
if v:
    plantas = max(0.5, min(5.0, float(v["valor"].replace(",", ".")) / 0.8 * 5))
    tarjetas.append(tarjeta("verde", "🌱", "Verdor del campo", f'{v["valor"]} {v.get("flecha", "")}',
                            fila("", tb.iconos("🌱", plantas, 5)),
                            v["frase"].split(". 0 =")[0].capitalize() + ". 5 🌱 = campo muy verde."))
else:
    tarjetas.append(tarjeta_falta("verde", "🌱", "Verdor del campo", "series_zonas.csv"))
# Agua sobre el terreno: una gota por mes con agua
a = tb.kpi_agua(t) if "ndwi" in t else None
if a:
    n_agua = int(a["valor"])
    cuerpo = fila("", tb.iconos("💧", n_agua) if n_agua else '<span class="iconos"><span>🏜️</span></span>')
    tarjetas.append(tarjeta("azul", "🌊", "Meses con agua en el terreno", f'{a["valor"]} <small>meses</small>',
                            cuerpo, tb.capital(a["frase"]) + "."))
else:
    tarjetas.append(tarjeta_falta("azul", "🌊", "Meses con agua en el terreno", "series_zonas.csv"))
# Hectareas: 10 casillas repartidas entre las zonas (cada una con su icono)
if zonas is not None:
    casillas = tb.waffle(list(zonas["area_ha"]))
    waffle = "".join(
        (f'<span>{ui.icono_zona(n)}</span>' if zid in (0, z) else f'<span class="off">{ui.icono_zona(n)}</span>') * c
        for n, z, c in zip(zonas["nombre_comun"], zonas["zona_id"], casillas))
    h = tb.kpi_hectareas(zonas, zid)
    tarjetas.append(tarjeta("marron", "🗺️", "Hectáreas de la zona", f'{h["valor"]} <small>ha</small>',
                            fila("", f'<span class="iconos">{waffle}</span>'),
                            f'{tb.capital(h["frase"])}. Cada icono = 10 % de Daule.'))
else:
    tarjetas.append(tarjeta_falta("marron", "🗺️", "Hectáreas de la zona", "zonas_daule.geojson"))
# Estrategia recomendada: los cultivos del plan y su ahorro de agua
recomendada = None
if est_z is not None and not est_z.empty:
    comp = logica.comparar(est_z, zid, escenario, ui.pesos_actuales())
    if not comp.empty:
        recomendada = comp["estrategia"].iloc[0]
if recomendada:
    cultivos = " · ".join(" → ".join(ICONO_CULTIVO.get(c, "🌱") for c in par)
                          for par in logica.SECUENCIAS[recomendada])
    ahorro = tb.ahorro_vs_a(est_z, escenario, recomendada)
    frase_plan = (f"Ahorra {tb.num(ahorro)} % de agua frente a sembrar solo arroz, en un {nombre_anio}."
                  if recomendada != "A" and ahorro else f"Lo mejor en un {nombre_anio} para lo que te importa.")
    tarjetas.append(tarjeta("verde", "✅", "Plan recomendado", f"Plan {recomendada}",
                            fila(NOMBRE_PLAN[recomendada], f'<span class="iconos cultivos">{cultivos}</span>'), frase_plan))
else:
    tarjetas.append(tarjeta_falta("verde", "✅", "Plan recomendado", "estrategias.csv"))
ui.html(f'<div class="picto-grid">{"".join(tarjetas)}</div>')
fuente("GPM IMERG y NASA POWER (P1, Mario) · Landsat 8 y 9 (P2, Thomas) · SRTM (P3, Austin) · "
       "estrategias FAO-56 (P1 y P4, Johan).")
if zid and serie_todo is not None and not (serie_todo["zona_id"] == zid).any():
    st.caption("🛰️ El verdor y el agua en el terreno todavía son el promedio de todo Daule.")


# --- 2. El año en Daule ------------------------------------------------------------------------
with st.container(key="dash_anio"):
    ui.html('<div class="bloque-tit">📅 El año en Daule</div>')
    if not falta("climatologia_daule.csv"):
        hoy = date.today().month - 1
        celdas = "".join(
            f'<div class="m {tipos_mes.get(i + 1, "")}{" hoy" if i == hoy else ""}">'
            f'<span>{tb.ICONO_TIPO_MES.get(tipos_mes.get(i + 1), "·")}</span>{logica.MESES[i]}'
            f'{"<small>hoy</small>" if i == hoy else ""}</div>' for i in range(12))
        ui.html(f'<div class="anio12">{celdas}</div>'
                '<div class="graf-ley"><span>🌧️ Lluvias</span><span>⛅ Cambio</span><span>☀️ Seca</span>'
                '<span>🟩 Mes actual</span></div>')
    if not falta("lluvia_imerg_daule.csv"):
        d = t.dropna(subset=["lluvia_imerg_mm"]) if "lluvia_imerg_mm" in t else t.iloc[0:0]
        if d.empty:
            st.info("Sin meses en el periodo elegido.", icon="ℹ️")
        else:
            esp = tb.especiales(d)
            seccion("🌧️", "¿Cómo viene lloviendo?", tb.frase_lluvia(d))
            raros = set(esp["fecha"])
            fig = go.Figure()
            sombrear(fig, d["fecha"])
            fig.add_bar(x=d["fecha"], y=d["lluvia_imerg_mm"], name="Lluvia real",
                        marker_color=[ui.RIESGO if f in raros else ui.RIO for f in d["fecha"]],
                        customdata=[tb.mes_corto(f) for f in d["fecha"]],
                        hovertemplate="%{customdata}: llovió %{y:,.0f} mm<extra></extra>")
            fig.add_scatter(x=d["fecha"], y=d["normal_mm"], name="Lo normal", mode="lines+markers",
                            line=dict(color="#263238", dash="dot", width=2), marker=dict(size=5),
                            customdata=[tb.mes_corto(f) for f in d["fecha"]],
                            hovertemplate="%{customdata}: lo normal es %{y:,.0f} mm<extra></extra>")
            # Anotaciones: el mes mas especial y, si esta lejos, el mas lluvioso
            maximo = float(d["lluvia_imerg_mm"].max())
            marcados = []
            if not esp.empty:
                f0 = esp.iloc[0]
                record = f0["lluvia_imerg_mm"] >= completa["lluvia_imerg_mm"].max()
                texto = (f"¡Récord! {tb.num(f0['lluvia_imerg_mm'])} mm" if record
                         else f"¡{tb.num(f0['veces'])} veces lo normal!")
                if tipos_mes.get(f0["fecha"].month) == "seco":
                    texto += "<br>en plena época seca"
                anotar(fig, f0["fecha"], f0["lluvia_imerg_mm"], texto, fraccion(d["fecha"], f0["fecha"]), ui.RIESGO)
                marcados.append(f0["fecha"])
            top = d.loc[d["lluvia_imerg_mm"].idxmax()]
            if all(abs((top["fecha"] - m).days) > 120 for m in marcados) and top["lluvia_imerg_mm"] > 50:
                anotar(fig, top["fecha"], top["lluvia_imerg_mm"],
                       f"El mes más lluvioso:<br>{tb.num(top['lluvia_imerg_mm'])} mm",
                       fraccion(d["fecha"], top["fecha"]), ui.RIO)
            fig.update_yaxes(range=[0, maximo * 1.42], tickformat=",.0f", title="mm de lluvia")
            eje_tiempo(fig, d["fecha"])
            mostrar(estilo(fig, alto=330, leyenda=True))
            ley_temporadas()
            descargas["lluvia_mensual"] = d[[c for c in ("fecha", "lluvia_imerg_mm", "lluvia_power_mm",
                                                         "normal_mm") if c in d]]
    fuente("año típico con NASA POWER; lluvia de cada mes con GPM IMERG V07, procesados por P1 (Mario). "
           "Lo normal = mediana de cada mes entre 2021 y 2026. En rojo, los meses con muchísima más lluvia.")


# --- 3. Graficos ilustrados ----------------------------------------------------------------------

def graf_balance():
    if falta("clima_mensual_daule.csv"):
        return
    d = t.dropna(subset=["balance_mm"]) if "balance_mm" in t else t.iloc[0:0]
    if d.empty:
        seccion("⚖️", "¿Sobra o falta agua?")
        st.info("Sin meses en el periodo elegido.", icon="ℹ️")
        return
    seccion("⚖️", "¿Sobra o falta agua?", tb.frase_balance(d))
    fig = go.Figure()
    sombrear(fig, d["fecha"])
    fig.add_bar(x=d["fecha"], y=d["balance_mm"],
                marker_color=[ui.HOJA if b >= 0 else ui.SECA for b in d["balance_mm"]],
                customdata=[f"{tb.mes_corto(f)}: {'sobran' if b >= 0 else 'faltan'} {tb.num(abs(b))} mm"
                            for f, b in zip(d["fecha"], d["balance_mm"])],
                hovertemplate="%{customdata}<extra></extra>")
    peor = d.loc[d["balance_mm"].idxmin()]
    mejor = d.loc[d["balance_mm"].idxmax()]
    if peor["balance_mm"] < 0:
        anotar(fig, peor["fecha"], peor["balance_mm"], f"Faltaron {tb.num(-peor['balance_mm'])} mm",
               fraccion(d["fecha"], peor["fecha"]), "#8D6E00", abajo=True)
    if mejor["balance_mm"] > 0 and abs((mejor["fecha"] - peor["fecha"]).days) > 60:
        anotar(fig, mejor["fecha"], mejor["balance_mm"], f"Sobraron {tb.num(mejor['balance_mm'])} mm",
               fraccion(d["fecha"], mejor["fecha"]), ui.HOJA)
    lo, hi = float(d["balance_mm"].min()), float(d["balance_mm"].max())
    # espacio arriba y abajo para que las notas no tapen las barras ni las fechas
    fig.update_yaxes(range=[min(lo, 0) * 2.3 - 20, max(hi, 0) * 1.6 + 20], tickformat=",.0f",
                     title="mm (+ sobra · − falta)")
    eje_tiempo(fig, d["fecha"])
    mostrar(estilo(fig, alto=300))
    ui.html(f'<div class="graf-ley"><i style="background:{ui.HOJA}"></i>Sobra agua'
            f'<i style="background:{ui.SECA}"></i>Falta agua · fondo: '
            '<i style="background:#DCEBFA"></i>lluvias<i style="background:#FDF0D3"></i>seca</div>')
    fuente("NASA POWER: lluvia menos el agua que se evapora (Hargreaves, FAO-56), P1 (Mario).")
    descargas["balance_agua"] = d[["fecha", "lluvia_power_mm", "et0_mm", "balance_mm"]].rename(
        columns={"et0_mm": "agua_que_se_evapora_mm"})


def graf_verdor():
    if falta("series_zonas.csv"):
        return
    d = t[["fecha", "ndvi"]] if "ndvi" in t else t.iloc[0:0]
    if d.empty:
        seccion("🌱", "¿Qué tan verde está el campo?")
        st.info("Sin meses en el periodo elegido.", icon="ℹ️")
        return
    seccion("🌱", "¿Qué tan verde está el campo?", tb.frase_verdor(t, completa))
    fig = go.Figure()
    sombrear(fig, d["fecha"])
    fig.add_scatter(x=d["fecha"], y=d["ndvi"], mode="lines+markers", connectgaps=False,
                    line=dict(color="#3E7D2F", width=3.5, shape="spline"), marker=dict(size=7),
                    customdata=[tb.mes_corto(f) for f in d["fecha"]],
                    hovertemplate="%{customdata}: verdor %{y:,.2f}<extra></extra>")
    validos = d.dropna(subset=["ndvi"])
    if not validos.empty:
        lo, hi = float(validos["ndvi"].min()), float(validos["ndvi"].max())
        nubes = d[d["ndvi"].isna()]
        if not nubes.empty:
            fig.add_scatter(x=nubes["fecha"], y=[lo - 0.045] * len(nubes), mode="text", text=["☁️"] * len(nubes),
                            textfont=dict(size=17), customdata=[tb.mes_corto(f) for f in nubes["fecha"]],
                            hovertemplate="%{customdata}: sin foto por nubes<extra></extra>")
        alto_ = validos.loc[validos["ndvi"].idxmax()]
        anotar(fig, alto_["fecha"], alto_["ndvi"], f"🌿 El más verde: {tb.num(alto_['ndvi'], 2)}",
               fraccion(d["fecha"], alto_["fecha"]), "#2E7D32")
        bajo = validos.loc[validos["ndvi"].idxmin()]
        if abs((bajo["fecha"] - alto_["fecha"]).days) > 90:
            anotar(fig, bajo["fecha"], bajo["ndvi"], f"🍂 El menos verde: {tb.num(bajo['ndvi'], 2)}",
                   fraccion(d["fecha"], bajo["fecha"]), "#8D6E63", abajo=True)
        fig.update_yaxes(range=[lo - 0.09, hi + 0.09], tickformat=",.2f", title="verdor")
    eje_tiempo(fig, d["fecha"])
    mostrar(estilo(fig, alto=300))
    ui.html('<div class="graf-ley">0 = suelo pelado · 0,8 = muy verde · ☁️ = sin foto por nubes · fondo: '
            '<i style="background:#DCEBFA"></i>lluvias<i style="background:#FDF0D3"></i>seca</div>')
    fuente("Landsat 8 y 9 (verdor = NDVI), procesado por P2 (Thomas); promedio de todo Daule.")
    descargas["verdor"] = d.rename(columns={"ndvi": "verdor_ndvi"})


def graf_inundacion():
    if falta("series_zonas.csv"):
        return
    d = t.dropna(subset=["ndwi"]) if "ndwi" in t else t.iloc[0:0]
    if d.empty:
        seccion("💧", "¿Cuándo se inunda?")
        st.info("Sin meses con foto en el periodo elegido.", icon="ℹ️")
        return
    seccion("💧", "¿Cuándo se inunda?", tb.frase_inundacion(t))
    base = t[["fecha", "ndwi"]].assign(anio=t["fecha"].dt.year, mes=t["fecha"].dt.month)
    tabla = base.pivot_table(index="anio", columns="mes", values="ndwi", aggfunc="mean", dropna=False)
    tabla = tabla.reindex(columns=range(1, 13))
    meses_con_dato = set(zip(base["anio"], base["mes"]))
    texto = [[(f"{logica.MESES[m - 1].lower()} {a}: " +
               ("sin foto (nubes)" if pd.isna(val) else f"{tb.num(val, 2)} · {'💧 hay agua' if val > 0 else 'seco'}"))
              for m, val in zip(tabla.columns, fila_)] for a, fila_ in zip(tabla.index, tabla.values)]
    lim = max(0.3, float(d["ndwi"].abs().max()))
    anios = [str(a) for a in tabla.index]
    fig = go.Figure(go.Heatmap(
        z=tabla.values, x=logica.MESES, y=anios, customdata=texto, zmin=-lim, zmax=lim, zmid=0,
        xgap=3, ygap=3, showscale=False, hovertemplate="%{customdata}<extra></extra>",
        colorscale=[[0, "#A1887F"], [0.45, "#EFE6DA"], [0.5, "#F7F7F7"], [0.55, "#BBDEFB"], [1, "#1565C0"]]))
    # 💧 donde hubo agua sobre el terreno y ☁️ donde las nubes taparon la foto
    marcas = [(logica.MESES[m - 1], str(a), "💧" if v > 0 else "☁️")
              for a, fila_ in zip(tabla.index, tabla.values) for m, v in zip(tabla.columns, fila_)
              if (a, m) in meses_con_dato and (pd.isna(v) or v > 0)]
    if marcas:
        fig.add_scatter(x=[m[0] for m in marcas], y=[m[1] for m in marcas], text=[m[2] for m in marcas],
                        mode="text", textfont=dict(size=16), hoverinfo="skip")
    fig.update_layout(plot_bgcolor="#FFFFFF")
    fig.update_xaxes(type="category", tickangle=0)
    fig.update_yaxes(autorange="reversed", type="category")
    mostrar(estilo(fig, alto=110 + 42 * len(anios)))
    ui.html('<div class="graf-ley"><i style="background:#A1887F"></i>Seco<i style="background:#F7F7F7"></i>'
            'Húmedo<i style="background:#1565C0"></i>Agua · 💧 = agua en el terreno · ☁️ = nubes</div>')
    fuente("Landsat 8 y 9 (agua en el terreno = NDWI), procesado por P2 (Thomas); promedio de todo Daule.")
    descargas["agua_en_terreno"] = d[["fecha", "ndwi"]].rename(columns={"ndwi": "agua_en_terreno_ndwi"})


def graf_temporadas():
    if falta("lluvia_imerg_daule.csv"):
        return
    if "lluvia_temporada_mm" not in imerg:
        st.info("La serie de lluvia todavía no trae las temporadas.", icon="ℹ️")
        return
    temp = (imerg.dropna(subset=["lluvia_temporada_mm"]).drop_duplicates("temporada")
            .sort_values("temporada")[["temporada", "lluvia_temporada_mm", "enso"]].reset_index(drop=True))
    temp["escenario"] = temp["enso"].map(tb.ESC_DE_ENSO)
    temp["etiqueta"] = [f"{ICONO_ANIO[e]} {t_}" for e, t_ in zip(temp["escenario"], temp["temporada"])]
    seccion("📆", "Cada temporada de lluvias", tb.frase_temporadas(temp))
    elegido = None if tipo == "todos" else tipo
    fig = go.Figure(go.Bar(
        y=temp["etiqueta"], x=temp["lluvia_temporada_mm"], orientation="h",
        marker_color=[ui.COLOR_ESC[e] for e in temp["escenario"]],
        marker_opacity=[1 if elegido in (None, e) else 0.3 for e in temp["escenario"]],
        text=[f"{tb.num(v)} mm" for v in temp["lluvia_temporada_mm"]], textposition="inside",
        insidetextanchor="end", textfont=dict(color="#fff", size=13),
        customdata=[ui.NOMBRE_ESC[e] for e in temp["escenario"]],
        hovertemplate="%{y}: %{x:,.0f} mm de dic a may · %{customdata}<extra></extra>"))
    maximo = temp["lluvia_temporada_mm"].max()
    for fila_, texto in [(temp.loc[temp["lluvia_temporada_mm"].idxmax()], "más lluviosa"),
                         (temp.loc[temp["lluvia_temporada_mm"].idxmin()], "más seca")]:
        fig.add_annotation(x=fila_["lluvia_temporada_mm"], y=fila_["etiqueta"], text=texto, showarrow=True,
                           arrowhead=2, arrowwidth=1.6, ax=20, ay=0, xanchor="left",
                           arrowcolor=ui.COLOR_ESC[fila_["escenario"]],
                           font=dict(size=11, color=ui.COLOR_ESC[fila_["escenario"]], family=FUENTE["family"]))
    # espacio a la derecha para la flecha y su texto, tambien en un celular de 390 px
    fig.update_xaxes(range=[0, maximo * 2.05], tickformat=",.0f", showticklabels=False)
    fig.update_yaxes(categoryorder="array", categoryarray=list(temp["etiqueta"]), autorange="reversed")
    mostrar(estilo(fig, alto=60 + 44 * len(temp)))
    ui.html('<div class="graf-ley">🌧️ Año muy lluvioso · 🌤️ Año normal · ☀️ Año seco</div>')
    fuente("GPM IMERG V07, lluvia de diciembre a mayo de cada año agrícola; procesado por P1 (Mario).")
    descargas["temporadas_lluvia"] = temp[["temporada", "lluvia_temporada_mm"]].assign(
        tipo_de_anio=temp["escenario"].map(ui.NOMBRE_ESC))


def graf_estrategias():
    if falta("estrategias.csv"):
        return
    if est_z is None or est_z.empty:
        st.info("No hay estrategias para esta zona.", icon="ℹ️")
        return
    d = est_z[est_z["escenario"] == escenario].set_index("estrategia")
    seccion("🌾", "¿Cuánta agua necesita cada opción?", tb.frase_estrategias(est_z, escenario, nombre_anio))
    mejor = d["agua_m3_ha"].idxmin() if not d.empty else None
    filas = []
    for k in ["A", "B", "C"]:
        if k not in d.index:
            continue
        agua = float(d.loc[k, "agua_m3_ha"])
        cultivos = " · ".join(" → ".join(ICONO_CULTIVO.get(c, "🌱") for c in par) for par in logica.SECUENCIAS[k])
        otros = est_z[est_z["estrategia"] == k].set_index("escenario")["agua_m3_ha"]
        detalle = " · ".join(f"{ICONO_ANIO[e]} {tb.num(otros[e])}" for e in tb.ORDEN_ESC if e in otros.index)
        filas.append(
            f'<div class="plan-fila{" mejor" if k == mejor else ""}">'
            f'<div class="plan-cab"><span class="plan-letra">{k}</span><b>{NOMBRE_PLAN[k]}</b>'
            f'<span class="plan-cult">{cultivos}</span>{"<span class=plan-badge>⭐ menos agua</span>" if k == mejor else ""}</div>'
            f'<div class="plan-gotas">{tb.iconos("💧", agua / 1000)}<span class="plan-num">{tb.num(agua)} m³/ha</span></div>'
            f'<div class="plan-detalle">Por tipo de año: {detalle}</div></div>')
    zona_ = "promedio de Daule según la superficie de cada zona" if zid == 0 else ui.etiqueta_zona(nombres_zona[zid])
    ui.html(f'<div class="plan-lista-agua">{"".join(filas)}</div>'
            f'<div class="graf-ley">Cada 💧 = 1.000 m³ de agua de riego por hectárea y por ciclo · '
            f'{ICONO_ANIO[escenario]} {ui.NOMBRE_ESC[escenario]} · Zona: {zona_}<br>'
            '🌾 arroz · 🫘 soya · 🌽 maíz</div>')
    fuente("Balance de agua FAO-56 con NASA POWER y los años de GPM IMERG (P1, Mario) y reglas de P4 (Johan).")
    descargas["agua_estrategias"] = est_z[["estrategia", "escenario", "agua_m3_ha", "nota_agua", "nota_suelo",
                                          "nota_plagas", "nota_ingresos"]].assign(
        escenario=lambda x: x["escenario"].map(ui.NOMBRE_ESC))


def graf_zonas():
    if falta("zonas_daule.geojson"):
        return
    seccion("🗺️", "Cómo se reparte Daule", tb.frase_zonas(zonas, zid, ui.corto_zona))
    total = zonas["area_ha"].sum()
    fig = go.Figure(go.Pie(
        labels=[ui.etiqueta_zona(n) for n in zonas["nombre_comun"]], values=zonas["area_ha"], hole=0.5,
        sort=False, direction="clockwise", rotation=90,
        marker=dict(colors=[ui.color_zona(n) for n in zonas["nombre_comun"]], line=dict(color="#fff", width=3)),
        pull=[0.07 if z == zid else 0 for z in zonas["zona_id"]],
        text=[f"{ui.icono_zona(n)}<br>{tb.num(a / total * 100)} %" for n, a in zip(zonas["nombre_comun"], zonas["area_ha"])],
        textinfo="text", textposition="inside", insidetextorientation="horizontal",
        textfont=dict(size=15, color="#fff"), customdata=[tb.num(a) for a in zonas["area_ha"]],
        hovertemplate="%{label}: %{customdata} ha<extra></extra>"))
    fig.update_layout(annotations=[dict(text=f"<b>{tb.num(total)}</b><br>hectáreas", showarrow=False,
                                        font=dict(size=14, family=FUENTE["family"]))])
    mostrar(estilo(fig, alto=300, leyenda=True))
    fuente("Elevación y pendiente de SRTM (NASA) agrupadas con K-means, procesado por P3 (Austin).")
    descargas["zonas_hectareas"] = zonas[["zona_id", "nombre_comun", "area_ha"]]


def graf_relieve():
    if falta("zonas_daule.geojson"):
        return
    if not {"elevacion", "pendiente"} <= set(zonas.columns):
        st.info("Las zonas todavía no traen elevación y pendiente.", icon="ℹ️")
        return
    seccion("⛰️", "Altura y pendiente de cada zona", tb.frase_relieve(zonas, ui.corto_zona))
    # etiquetas cortas y horizontales (en el celular plotly las giraba)
    etiquetas = [f"{ui.icono_zona(n)}<br>{ui.corto_zona(n).replace('Zona baja', 'Baja')}" for n in zonas["nombre_comun"]]
    colores = [ui.color_zona(n) for n in zonas["nombre_comun"]]
    opac = [1 if zid in (0, z) else 0.4 for z in zonas["zona_id"]]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Altura (m sobre el mar)", "Pendiente (°)"),
                        horizontal_spacing=0.12)
    for col, campo, unidad in [(1, "elevacion", " m"), (2, "pendiente", "°")]:
        tope = zonas[campo].idxmax()
        fig.add_bar(x=etiquetas, y=zonas[campo], marker=dict(color=colores, opacity=opac), row=1, col=col,
                    text=[f"{tb.num(v, 1)}{unidad}" + (" ⬆" if i == tope else "") for i, v in enumerate(zonas[campo])],
                    textposition="outside", cliponaxis=False, textfont=dict(size=13),
                    hovertemplate="%{x}: %{y:,.1f}" + unidad + "<extra></extra>")
        fig.update_yaxes(range=[0, zonas[campo].max() * 1.45], showticklabels=False, row=1, col=col)
    fig.update_annotations(font=dict(size=13, family=FUENTE["family"]))
    estilo(fig, alto=320, arriba=34)
    fig.update_xaxes(tickangle=0, tickfont=dict(size=12))
    fig.update_layout(uniformtext=dict(minsize=12, mode="show"))  # que plotly no achique los textos
    mostrar(fig)
    fuente("SRTM (NASA), procesado por P3 (Austin). Pendiente en grados según su código (por confirmar con P3).")
    descargas["altura_pendiente"] = zonas[["zona_id", "nombre_comun", "elevacion", "pendiente"]]


def par(izq, der=None):
    cols = st.columns(2, gap="large") if der else [st.container()]
    for col, graf in zip(cols, [izq, der] if der else [izq]):
        with col, st.container(key=f"graf_{graf.__name__}"):
            graf()


ui.html('<div class="bloque-tit">🔎 Mirando más de cerca</div>')
par(graf_balance, graf_verdor)
par(graf_inundacion, graf_temporadas)
par(graf_estrategias)
par(graf_zonas, graf_relieve)

# --- 4. Lo que nos dicen los datos -----------------------------------------------------------------
ideas = tb.conclusiones(completa, clim, est_z, zonas, escenario, nombre_anio, zona_txt, ui.corto_zona)
ui.html('<div class="bloque-tit">💬 Lo que nos dicen los datos</div>')
if ideas:
    ui.html('<div class="ideas">' + "".join(
        f'<div class="idea"><div class="idea-ico">{i["icono"]}</div><div><div class="idea-tit">{i["titulo"]}</div>'
        f'<p>{i["texto"]}</p><div class="fuente-peq">Fuente: {i["fuente"]}</div></div></div>' for i in ideas)
        + "</div>")
else:
    st.info("Faltan datos para sacar conclusiones.", icon="ℹ️")

ui.html('<div class="dash-pie">Glosario: <b>verdor</b> = NDVI · <b>agua en el terreno</b> = NDWI · '
        '<b>agua que se evapora</b> = ET0. Los números usan coma decimal (1.234,5).</div>')
st.page_link("vistas/clima.py", label="Ver datos técnicos: de dónde sale cada dato", icon="🔬")

# --- Descargas (dentro del desplegable de arriba) ---------------------------------------------------
with panel:
    st.markdown("**⬇️ Descargar los datos que ves** (CSV para Excel, con coma decimal)")
    if descargas:
        with st.container(horizontal=True, gap="small"):
            for nombre, datos in descargas.items():
                if datos is not None and not datos.empty:
                    st.download_button(nombre.replace("_", " ").capitalize(), tb.csv_ecuador(datos),
                                       file_name=f"{nombre}.csv", mime="text/csv", key=f"bajar_{nombre}",
                                       icon="⬇️")
    else:
        st.caption("No hay datos para descargar con estos filtros.")
