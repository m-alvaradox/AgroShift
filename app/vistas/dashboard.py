"""
Dashboard: toda la data real del equipo en tarjetas y graficos simples.

Filtros (zona, periodo y tipo de año) arriba; tarjetas grandes; graficos en 2 columnas
(1 en celular). Cada grafico: titulo en forma de pregunta, frase de conclusion calculada,
fuente y boton para descargar los datos filtrados. Si falta un archivo, ese grafico
muestra un aviso y el resto sigue.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils import carga, logica, ui
from utils import tablero as tb

ss = st.session_state
FUENTE = dict(family="Nunito, system-ui, sans-serif", size=13, color="#1F2A1F")
CONFIG = {"displayModeBar": False, "locale": "es"}
COLOR_PLAN = {"A": ui.RIO, "B": ui.HOJA, "C": ui.SECA}
NOMBRE_PLAN = {"A": "A · Siempre arroz", "B": "B · Con soya", "C": "C · Rotación"}


def hay(nombre: str) -> bool:
    return carga.disponible(nombre)


def leer(nombre: str, cargador):
    return cargador() if hay(nombre) else None


# --- Datos reales (cada uno puede faltar) -----------------------------------------------------
imerg = leer("lluvia_imerg_daule.csv", carga.lluvia_imerg)
power = leer("clima_mensual_daule.csv", carga.clima_mensual)
clim = leer("climatologia_daule.csv", carga.climatologia)
serie_todo = leer("series_zonas.csv", carga.series)
zonas = carga.tabla_zonas().sort_values("zona_id") if hay("zonas_daule.geojson") else None
est = leer("estrategias.csv", carga.estrategias)

# --- Filtros (afectan a todo el dashboard) ------------------------------------------------------
opciones_zona = [0] + ([int(z) for z in zonas["zona_id"]] if zonas is not None else [])
nombres_zona = dict(zip(zonas["zona_id"].astype(int), zonas["nombre_comun"])) if zonas is not None else {}
if ss.get("dash_zona") not in opciones_zona:
    ss["dash_zona"] = ss.get("zona_id") if ss.get("zona_id") in opciones_zona else 0
ss.setdefault("dash_periodo", "1")
if ss.get("dash_tipo") not in tb.TIPOS:
    ss["dash_tipo"] = "todos"


def _sincronizar_zona():
    # la zona elegida aqui tambien queda para las otras paginas
    if ss["dash_zona"]:
        ss["zona_id"] = ss["dash_zona"]


def _sincronizar_tipo():
    if ss.get("dash_tipo") and ss["dash_tipo"] != "todos":
        ss["escenario"] = ss["dash_tipo"]


st.title("📊 Dashboard")
st.markdown("Todo lo que miden los satélites y el equipo sobre Daule, en un vistazo.")
with st.container(key="filtros_dash"):
    c1, c2, c3 = st.columns([1.1, 1.4, 1.6])
    c1.selectbox("Zona", opciones_zona, key="dash_zona", on_change=_sincronizar_zona,
                 format_func=lambda z: "🗺️ Todo Daule" if z == 0 else ui.etiqueta_zona(nombres_zona[z]))
    c2.segmented_control("Periodo", list(tb.PERIODOS), key="dash_periodo", required=True,
                         format_func=lambda p: tb.PERIODOS[p], width="stretch", wrap=True)
    c3.segmented_control("Tipo de año", list(tb.TIPOS), key="dash_tipo", required=True,
                         on_change=_sincronizar_tipo, format_func=lambda t: tb.TIPOS[t], width="stretch",
                         wrap=True)
zid = ss["dash_zona"] or 0
periodo = ss["dash_periodo"] or "1"
tipo = ss["dash_tipo"] or "todos"
escenario = tipo if tipo != "todos" else "normal"
nombre_anio = ui.NOMBRE_ESC[escenario].lower()

completa = tb.tabla_mensual(imerg, power, serie_todo[serie_todo["zona_id"] == 0] if serie_todo is not None
                            else None, clim)
t = tb.filtrar(completa, periodo, tipo)
est_z = tb.estrategias_zona(est, zonas, zid) if est is not None else None

if tipo != "todos" and imerg is None:
    st.warning("El filtro de tipo de año necesita lluvia_imerg_daule.csv (lo entrega P1).", icon="📭")
if t.empty and not completa.empty:
    st.info("No hay meses de ese tipo de año en el periodo elegido. Prueba con «Todo (2021–2026)».",
            icon="ℹ️")


# --- Piezas comunes ---------------------------------------------------------------------------

def falta(*nombres: str) -> bool:
    ausentes = [n for n in nombres if not hay(n)]
    for n in ausentes:
        st.warning(f"Falta este dato ({n}): lo entrega {carga.FaltaArchivo(n).responsable}.", icon="📭")
    return bool(ausentes)


def estilo(fig, alto: int = 300, leyenda: bool = True):
    # Leyenda arriba del grafico: abajo chocaba con las fechas de dos lineas en el celular
    fig.update_layout(
        height=alto, margin=dict(l=6, r=6, t=40 if leyenda else 8, b=6), separators=",.", font=FUENTE,
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)", showlegend=leyenda, bargap=0.18,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=12)),
        hoverlabel=dict(font=dict(family=FUENTE["family"], size=13)))
    fig.update_xaxes(showgrid=False, fixedrange=True)
    fig.update_yaxes(gridcolor="#E8EDE6", zerolinecolor="#90A4AE", fixedrange=True)
    return fig


def mostrar(fig):
    st.plotly_chart(fig, width="stretch", config=CONFIG)


def cierre(frase: str, fuente: str, datos: pd.DataFrame | None, archivo: str):
    ui.html(f'<div class="conclusion">💡 {frase}</div>')
    st.caption(f"Fuente: {fuente}")
    if datos is not None and not datos.empty:
        st.download_button("⬇️ Descargar datos", tb.csv_ecuador(datos), file_name=f"{archivo}.csv",
                           mime="text/csv", key=f"bajar_{archivo}")


def titulo(pregunta: str, ayuda: str | None = None):
    ui.html(f'<div class="graf-tit">{pregunta}</div>' + (f'<div class="graf-sub">{ayuda}</div>' if ayuda else ""))


def eje_tiempo(fig, fechas):
    vals, textos = tb.ticks(fechas)
    fig.update_xaxes(tickvals=vals, ticktext=textos, tickangle=0)


def kpi(icono: str, tit: str, dato: dict | None, color: str, falta_de: str | None = None) -> str:
    if dato is None:
        resp = carga.FaltaArchivo(falta_de).responsable if falta_de and not hay(falta_de) else None
        frase = f"Falta este dato: lo entrega {resp}." if resp else "Sin datos en el periodo elegido."
        return (f'<div class="kpi {color}"><div class="kpi-ico">{icono}</div><div class="kpi-tit">{tit}</div>'
                f'<div class="kpi-num">—</div><div class="kpi-frase">{frase}</div></div>')
    flecha = dato.get("flecha", "")
    clase = {"↑": "sube", "↓": "baja"}.get(flecha, "")
    flecha_html = f' <span class="flecha {clase}">{flecha}</span>' if flecha else ""
    unidad = f' <small>{dato["unidad"]}</small>' if dato.get("unidad") else ""
    return (f'<div class="kpi {color}"><div class="kpi-ico">{icono}</div><div class="kpi-tit">{tit}</div>'
            f'<div class="kpi-num">{dato["valor"]}{unidad}{flecha_html}</div>'
            f'<div class="kpi-frase">{dato["frase"]}</div></div>')


# --- Tarjetas grandes ---------------------------------------------------------------------------
recomendada = None
if est_z is not None and not est_z.empty:
    comp = logica.comparar(est_z, zid, escenario, ui.pesos_actuales())
    if not comp.empty:
        k = comp["estrategia"].iloc[0]
        ahorro = tb.ahorro_vs_a(est_z, escenario, k)
        frase = (f"ahorra {tb.num(ahorro)} % de agua frente a arroz todo el año (A)"
                 if k != "A" and ahorro is not None else "es sembrar arroz todo el año")
        recomendada = {"valor": f"Plan {k}", "unidad": "", "frase": f"{frase}, en un {nombre_anio}"}

tarjetas = [
    kpi("🌧️", "Lluvia del periodo", tb.kpi_lluvia(t), "azul", "lluvia_imerg_daule.csv"),
    kpi("☀️", "Meses secos del año típico", tb.kpi_secos(clim) if clim is not None else None,
        "amarillo", "climatologia_daule.csv"),
    kpi("🌱", "Verdor promedio del campo", tb.kpi_verdor(t, completa) if "ndvi" in t else None,
        "verde", "series_zonas.csv"),
    kpi("💧", "Meses con agua en el terreno", tb.kpi_agua(t) if "ndwi" in t else None,
        "azul", "series_zonas.csv"),
    kpi("🌾", "Hectáreas de la zona", tb.kpi_hectareas(zonas, zid) if zonas is not None else None,
        "marron", "zonas_daule.geojson"),
    kpi("✅", "Estrategia recomendada", recomendada, "verde", "estrategias.csv"),
]
ui.html(f'<div class="kpis">{"".join(tarjetas)}</div>')
if zid and serie_todo is not None and not (serie_todo["zona_id"] == zid).any():
    st.caption("🛰️ El verdor y el agua en el terreno todavía son el promedio de todo Daule: "
               "el satélite aún no se procesa por zona.")


# --- Graficos -------------------------------------------------------------------------------------

def graf_lluvia():
    titulo("🌧️ ¿Cómo viene lloviendo?", "Lluvia de cada mes medida por dos satélites de la NASA.")
    falta("lluvia_imerg_daule.csv", "clima_mensual_daule.csv")  # avisa; dibuja con lo que haya
    if imerg is None and power is None:
        return
    d = t.dropna(subset=[c for c in ("lluvia_imerg_mm", "lluvia_power_mm") if c in t], how="all")
    if d.empty:
        st.info("Sin meses en el periodo elegido.", icon="ℹ️")
        return
    meses = [tb.mes_corto(f) for f in d["fecha"]]
    fig = go.Figure()
    if "lluvia_imerg_mm" in d:
        raro = d["lluvia_imerg_mm"] > (3 * d["normal_mm"]).clip(lower=d["normal_mm"] + 50)
        fig.add_bar(x=d["fecha"], y=d["lluvia_imerg_mm"], name="GPM IMERG",
                    marker_color=[ui.RIESGO if r else ui.RIO for r in raro], customdata=meses,
                    hovertemplate="%{customdata}: %{y:,.0f} mm (GPM IMERG)<extra></extra>")
    if "lluvia_power_mm" in d:
        fig.add_bar(x=d["fecha"], y=d["lluvia_power_mm"], name="NASA POWER", marker_color="#A9C4DB",
                    customdata=meses, hovertemplate="%{customdata}: %{y:,.0f} mm (NASA POWER)<extra></extra>")
    if "normal_mm" in d:
        fig.add_scatter(x=d["fecha"], y=d["normal_mm"], name="Lo normal para ese mes", mode="lines",
                        line=dict(color="#263238", dash="dot", width=2), customdata=meses,
                        hovertemplate="%{customdata}: lo normal es %{y:,.0f} mm<extra></extra>")
    fig.update_layout(barmode="group", yaxis_title="mm de lluvia")
    fig.update_yaxes(tickformat=",.0f")
    eje_tiempo(fig, d["fecha"])
    mostrar(estilo(fig))
    ui.html('<div class="graf-ley"><i style="background:#C0392B"></i>Mes con muchísima más lluvia de lo normal</div>')
    cols = [c for c in ("fecha", "lluvia_imerg_mm", "lluvia_power_mm", "normal_mm") if c in d]
    cierre(tb.frase_lluvia(d), "GPM IMERG V07 y NASA POWER, procesados por P1 (Mario). Lo normal: "
           "mediana de IMERG de cada mes, 2021–2026.", d[cols], "lluvia_mensual")


def graf_balance():
    titulo("⚖️ ¿Sobra o falta agua?", "Lluvia menos el agua que se evapora del suelo y las plantas.")
    if falta("clima_mensual_daule.csv"):
        return
    d = t.dropna(subset=["balance_mm"]) if "balance_mm" in t else t.iloc[0:0]
    if d.empty:
        st.info("Sin meses en el periodo elegido.", icon="ℹ️")
        return
    texto = [f"{tb.mes_corto(f)}: {'sobran' if b >= 0 else 'faltan'} {tb.num(abs(b))} mm"
             for f, b in zip(d["fecha"], d["balance_mm"])]
    fig = go.Figure(go.Bar(x=d["fecha"], y=d["balance_mm"], customdata=texto,
                           marker_color=[ui.HOJA if b >= 0 else ui.SECA for b in d["balance_mm"]],
                           hovertemplate="%{customdata}<extra></extra>"))
    fig.update_layout(yaxis_title="mm (+ sobra, − falta)")
    eje_tiempo(fig, d["fecha"])
    mostrar(estilo(fig, leyenda=False))
    ui.html(f'<div class="graf-ley"><i style="background:{ui.HOJA}"></i>Sobra agua'
            f'<i style="background:{ui.SECA}"></i>Falta agua</div>')
    cierre(tb.frase_balance(d), "NASA POWER: lluvia y temperaturas; agua que se evapora con Hargreaves "
           "(FAO-56). Procesado por P1 (Mario).",
           d[["fecha", "lluvia_power_mm", "et0_mm", "balance_mm"]].rename(
               columns={"et0_mm": "agua_que_se_evapora_mm"}), "balance_agua")


def graf_verdor():
    titulo("🌱 ¿Qué tan verde está el campo?", "Verdor medido por el satélite: 0 = suelo pelado, 0,8 = muy verde.")
    if falta("series_zonas.csv"):
        return
    d = t[["fecha", "ndvi"]] if "ndvi" in t else t.iloc[0:0]
    if d.empty:
        st.info("Sin meses en el periodo elegido.", icon="ℹ️")
        return
    meses = [tb.mes_corto(f) for f in d["fecha"]]
    fig = go.Figure()
    fig.add_scatter(x=d["fecha"], y=d["ndvi"], mode="lines+markers", name="Verdor", connectgaps=False,
                    line=dict(color="#3E7D2F", width=3), marker=dict(size=6), customdata=meses,
                    hovertemplate="%{customdata}: verdor %{y:,.2f}<extra></extra>")
    nubes = d[d["ndvi"].isna()]
    if not nubes.empty:
        base = float(d["ndvi"].min()) - 0.03 if d["ndvi"].notna().any() else 0
        fig.add_scatter(x=nubes["fecha"], y=[base] * len(nubes), mode="text", text=["☁️"] * len(nubes),
                        name="Sin foto por nubes", textfont=dict(size=16),
                        customdata=[tb.mes_corto(f) for f in nubes["fecha"]],
                        hovertemplate="%{customdata}: sin foto (nubes)<extra></extra>")
    fig.update_layout(yaxis_title="verdor")
    eje_tiempo(fig, d["fecha"])
    mostrar(estilo(fig))
    cierre(tb.frase_verdor(t, completa), "Landsat 8 y 9, procesado por P2 (Thomas); promedio de todo Daule.",
           d.rename(columns={"ndvi": "verdor_ndvi"}), "verdor")


def graf_inundacion():
    titulo("💧 ¿Cuándo se inunda?", "Agua en el terreno según el satélite: azul = hay agua, café = seco.")
    if falta("series_zonas.csv"):
        return
    d = t.dropna(subset=["ndwi"]) if "ndwi" in t else t.iloc[0:0]
    if d.empty:
        st.info("Sin meses con foto en el periodo elegido.", icon="ℹ️")
        return
    base = t[["fecha", "ndwi"]].assign(anio=t["fecha"].dt.year, mes=t["fecha"].dt.month)
    tabla = base.pivot_table(index="anio", columns="mes", values="ndwi", aggfunc="mean", dropna=False)
    tabla = tabla.reindex(columns=range(1, 13))
    texto = [[(f"{logica.MESES[m - 1].lower()} {a}: " +
               ("sin foto (nubes o sin dato)" if pd.isna(v) else
                f"{tb.num(v, 2)} · {'hay agua' if v > 0 else 'seco'}"))
              for m, v in zip(tabla.columns, fila)] for a, fila in zip(tabla.index, tabla.values)]
    lim = max(0.3, float(d["ndwi"].abs().max()))
    fig = go.Figure(go.Heatmap(
        z=tabla.values, x=logica.MESES, y=[str(a) for a in tabla.index], customdata=texto,
        zmin=-lim, zmax=lim, zmid=0, xgap=2, ygap=2,
        colorscale=[[0, "#8D6E63"], [0.45, "#EFE6DA"], [0.5, "#F5F5F5"], [0.55, "#BBDEFB"], [1, "#1565C0"]],
        hovertemplate="%{customdata}<extra></extra>",
        colorbar=dict(title="", tickvals=[-lim, 0, lim], ticktext=["seco", "0", "agua"], len=0.8, thickness=10)))
    fig.update_layout(plot_bgcolor="#CFD8DC")
    fig.update_yaxes(autorange="reversed", type="category")
    mostrar(estilo(fig, alto=260, leyenda=False))
    ui.html('<div class="graf-ley"><i style="background:#CFD8DC"></i>Gris = sin foto por nubes</div>')
    cierre(tb.frase_inundacion(t), "Landsat 8 y 9, procesado por P2 (Thomas); promedio de todo Daule.",
           d[["fecha", "ndwi"]].rename(columns={"ndwi": "agua_en_terreno_ndwi"}), "agua_en_terreno")


def graf_temporadas():
    titulo("📆 Cada temporada de lluvias", "Lluvia de diciembre a mayo de cada año agrícola.")
    if falta("lluvia_imerg_daule.csv"):
        return
    if "lluvia_temporada_mm" not in imerg:
        st.info("La serie de lluvia todavía no trae las temporadas.", icon="ℹ️")
        return
    temp = (imerg.dropna(subset=["lluvia_temporada_mm"]).drop_duplicates("temporada")
            .sort_values("temporada")[["temporada", "lluvia_temporada_mm", "enso"]].reset_index(drop=True))
    temp["tipo_de_anio"] = [ui.NOMBRE_ESC[tb.ESC_DE_ENSO[e]] for e in temp["enso"]]
    elegido = None if tipo == "todos" else tb.ENSO_DE[tipo]
    fig = go.Figure()
    for enso in ["nino", "neutro", "nina"]:
        g = temp[temp["enso"] == enso]
        if g.empty:
            continue
        esc = tb.ESC_DE_ENSO[enso]
        fig.add_bar(y=g["temporada"], x=g["lluvia_temporada_mm"], orientation="h", name=ui.NOMBRE_ESC[esc],
                    marker_color=ui.COLOR_ESC[esc], opacity=1 if elegido in (None, enso) else 0.3,
                    customdata=g["tipo_de_anio"], text=[f"{tb.num(v)} mm" for v in g["lluvia_temporada_mm"]],
                    textposition="auto", hovertemplate="%{y}: %{x:,.0f} mm · %{customdata}<extra></extra>")
    # sin titulo en el eje X: cada barra ya dice sus mm y asi la leyenda no lo tapa
    fig.update_xaxes(tickformat=",.0f")  # 1.500 (punto de miles)
    fig.update_yaxes(categoryorder="array", categoryarray=list(temp["temporada"]), autorange="reversed")
    mostrar(estilo(fig, alto=280))
    cierre(tb.frase_temporadas(temp), "GPM IMERG V07, procesado por P1 (Mario). La más lluviosa es el "
           "año muy lluvioso y la más seca, el año seco.",
           temp[["temporada", "lluvia_temporada_mm", "tipo_de_anio"]], "temporadas_lluvia")


def graf_estrategias():
    titulo("🌾 ¿Cuánta agua necesita cada opción?", "Agua de riego por ciclo de cultivo, en m³ por hectárea.")
    if falta("estrategias.csv"):
        return
    if est_z is None or est_z.empty:
        st.info("No hay estrategias para esta zona.", icon="ℹ️")
        return
    ORDEN = [e for e in tb.ORDEN_ESC if tipo in ("todos", e)]
    d = est_z[est_z["escenario"].isin(ORDEN)]
    # etiquetas en dos lineas para que no se peguen en el celular
    etiquetas = {"nina": "Año<br>seco", "normal": "Año<br>normal", "nino": "Año muy<br>lluvioso"}
    fig = go.Figure()
    for k in ["A", "B", "C"]:
        g = d[d["estrategia"] == k].set_index("escenario").reindex(ORDEN)
        fig.add_bar(x=[etiquetas[e] for e in ORDEN], y=g["agua_m3_ha"], name=NOMBRE_PLAN[k],
                    marker_color=COLOR_PLAN[k],
                    customdata=[f"{NOMBRE_PLAN[k]} · {ui.NOMBRE_ESC[e]}" for e in ORDEN],
                    hovertemplate="%{customdata}: %{y:,.0f} m³/ha por ciclo<extra></extra>")
    fig.update_layout(barmode="group", yaxis_title="m³ por hectárea")
    fig.update_yaxes(tickformat=",.0f")  # 8.000 (punto de miles)
    mostrar(estilo(fig))
    zona_txt = "promedio de Daule según la superficie de cada zona" if zid == 0 else \
        ui.etiqueta_zona(nombres_zona[zid])
    st.caption(f"Zona: {zona_txt}.")
    salida = d[["estrategia", "escenario", "agua_m3_ha", "nota_agua", "nota_suelo", "nota_plagas",
                "nota_ingresos"]].assign(escenario=lambda x: x["escenario"].map(ui.NOMBRE_ESC))
    cierre(tb.frase_estrategias(est_z, escenario, nombre_anio),
           "Balance de agua FAO-56 con NASA POWER y los años de GPM IMERG (P1, Mario) y reglas de "
           "P4 (Johan); calculado con scripts/calcular_estrategias.py.", salida, "agua_estrategias")


def graf_zonas():
    titulo("🗺️ Cómo se reparte Daule", "Hectáreas de cada zona de terreno.")
    if falta("zonas_daule.geojson"):
        return
    nombres = [ui.etiqueta_zona(n) for n in zonas["nombre_comun"]]
    fig = go.Figure(go.Pie(
        labels=nombres, values=zonas["area_ha"], hole=0.55, sort=False, direction="clockwise",
        marker=dict(colors=[ui.color_zona(n) for n in zonas["nombre_comun"]], line=dict(color="#fff", width=2)),
        pull=[0.08 if z == zid else 0 for z in zonas["zona_id"]], textinfo="percent",
        customdata=[tb.num(a) for a in zonas["area_ha"]],
        hovertemplate="%{label}: %{customdata} ha (%{percent})<extra></extra>"))
    total = tb.num(zonas["area_ha"].sum())
    fig.update_layout(annotations=[dict(text=f"<b>{total}</b><br>ha", showarrow=False, font=dict(size=15))])
    mostrar(estilo(fig, alto=290))
    cierre(tb.frase_zonas(zonas, zid, ui.corto_zona), "Elevación y pendiente de SRTM (NASA) agrupadas "
           "con K-means, procesado por P3 (Austin).",
           zonas[["zona_id", "nombre_comun", "area_ha"]], "zonas_hectareas")


def graf_relieve():
    titulo("⛰️ Altura y pendiente de cada zona", "Promedio de cada zona según el satélite SRTM.")
    if falta("zonas_daule.geojson"):
        return
    if not {"elevacion", "pendiente"} <= set(zonas.columns):
        st.info("Las zonas todavía no traen elevación y pendiente.", icon="ℹ️")
        return
    cortos = [ui.corto_zona(n) for n in zonas["nombre_comun"]]
    colores = [ui.color_zona(n) for n in zonas["nombre_comun"]]
    opac = [1 if zid in (0, z) else 0.4 for z in zonas["zona_id"]]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Altura (m sobre el mar)", "Pendiente (°)"),
                        horizontal_spacing=0.14)
    for col, campo, unidad in [(1, "elevacion", "m"), (2, "pendiente", "°")]:
        fig.add_bar(x=cortos, y=zonas[campo], marker=dict(color=colores, opacity=opac), row=1, col=col,
                    text=[f"{tb.num(v, 1)} {unidad}".strip() for v in zonas[campo]], textposition="outside",
                    cliponaxis=False, hovertemplate="%{x}: %{y:,.1f} " + unidad + "<extra></extra>")
    fig.update_annotations(font=dict(size=13, family=FUENTE["family"]))
    fig.update_yaxes(rangemode="tozero")
    estilo(fig, alto=300, leyenda=False)
    fig.update_layout(margin=dict(t=34))  # espacio para los titulos de los dos paneles
    mostrar(fig)
    cierre(tb.frase_relieve(zonas, ui.corto_zona), "SRTM (NASA), procesado por P3 (Austin). La pendiente "
           "está en grados según su código (por confirmar con P3).",
           zonas[["zona_id", "nombre_comun", "elevacion", "pendiente"]], "altura_pendiente")


GRAFICOS = [graf_lluvia, graf_balance, graf_verdor, graf_inundacion,
            graf_temporadas, graf_estrategias, graf_zonas, graf_relieve]

for i in range(0, len(GRAFICOS), 2):
    columnas = st.columns(2, gap="medium")
    for col, graf in zip(columnas, GRAFICOS[i:i + 2]):
        with col, st.container(key=f"graf_{graf.__name__}"):
            graf()

ui.html('<div class="dash-pie">Glosario: <b>verdor</b> = NDVI · <b>agua en el terreno</b> = NDWI · '
        '<b>agua que se evapora</b> = ET0. Los números usan coma decimal (1.234,5).</div>')
st.page_link("vistas/clima.py", label="Ver datos técnicos: de dónde sale cada dato", icon="🔬")
