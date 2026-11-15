"""Mi campo: el terreno visto desde el satelite (por zona), sus fotos de cada mes y cuando sembrar."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import carga, logica, ui

zid, znombre = ui.zona_actual()

st.title("🛰️ Tu campo visto desde el satélite")
ui.origen_datos()

sz = ui.serie_vacia()
serie = None
if not ui.falta("series_zonas.csv"):
    serie = carga.series()
    sz = serie[serie["zona_id"] == zid].sort_values("fecha")
    if sz.empty and (serie["zona_id"] == 0).any():
        sz = serie[serie["zona_id"] == 0].sort_values("fecha")
        st.info("Por ahora se muestra todo el recuadro de Daule. Cuando estén listas las series por "
                "zona, verás solo la tuya.", icon="ℹ️")
    else:
        st.caption(f"Datos de tu zona: {ui.etiqueta_zona(znombre)}.")

    # --- Que mirar --------------------------------------------------------------------------
    hay_pct = "pct_agua" in sz and sz["pct_agua"].notna().any()
    opciones = {
        "ndvi": ("🌱 Verdor", "#3E7D2F", "Más alto = cultivo más verde y sano. Cerca de 0 = suelo pelado."),
        "agua": ("💧 Agua en el terreno", ui.RIO,
                 "Qué parte de tu zona tenía agua encima ese mes (arrozal inundado, charcos o crecidas)."
                 if hay_pct else "Por encima de 0 = hay agua sobre el terreno o está inundado."),
        "ndmi": ("🌿 Humedad", "#7A5FA8", "Más bajo = las plantas pueden estar pasando sed."),
    }
    ver = st.segmented_control("¿Qué quieres ver?", options=list(opciones), default="ndvi",
                               format_func=lambda k: opciones[k][0], key="indice") or "ndvi"
    nombre, color, ayuda = opciones[ver]
    st.markdown(ayuda)

    meses_txt = [f"{logica.MESES[f.month - 1].lower()} {f.year}" for f in sz["fecha"]]
    fig = go.Figure()
    if ver == "agua" and hay_pct:
        con_agua = sz["pct_agua"] >= logica.UMBRAL_AGUA_PCT
        fig.add_bar(x=sz["fecha"], y=sz["pct_agua"], marker_color=[ui.RIO if a else "#B0C4D6" for a in con_agua],
                    customdata=meses_txt, hovertemplate="%{customdata}: %{y:.1f} % de la zona con agua<extra></extra>")
        fig.add_hline(y=logica.UMBRAL_AGUA_PCT, line=dict(color=ui.RIESGO, dash="dot"),
                      annotation_text=f"{ui.num(logica.UMBRAL_AGUA_PCT)} % = mes con agua",
                      annotation_position="top left")
        fig.update_yaxes(title="% de la zona con agua", rangemode="tozero")
    else:
        col = "ndwi" if ver == "agua" else ver
        fig.add_scatter(x=sz["fecha"], y=sz[col], mode="lines+markers", line=dict(color=color, width=3),
                        marker=dict(size=6), customdata=meses_txt,
                        hovertemplate="%{customdata}: %{y:.2f}<extra></extra>")
        if col == "ndwi":
            fig.add_hline(y=0, line=dict(color=ui.RIESGO, dash="dot"),
                          annotation_text="encima = agua", annotation_position="top left")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", separators=",.",
                      showlegend=False, font=dict(family="Nunito, sans-serif", size=14))
    st.plotly_chart(fig, width="stretch")
    if not sz.empty:
        ui.fuente(f"Landsat 8 y 9, una imagen por mes ({sz['fecha'].min():%m/%Y} a "
                  f"{sz['fecha'].max():%m/%Y}). Los cortes en la línea son meses con demasiadas nubes.")
        ui.html(ui.confianza("agua_terreno" if ver == "agua" else "verdor"))

# --- Tu campo mes a mes: fotos del satelite ------------------------------------------------------
st.subheader("📸 Tu campo mes a mes")
ms = carga.meses_satelite()
if ms is None or ms.empty:
    st.info("Todavía no están las fotos de cada mes. Se generan con scripts/series_por_zona.py.", icon="📭")
else:
    etiquetas = [f"{logica.MESES[f.month - 1].lower()} {f.year}" for f in ms["fecha"]]
    # lluvia de cada mes (satelite GPM IMERG) y lo normal para ese mes
    lluvia, normal = {}, {}
    if carga.disponible("lluvia_imerg_daule.csv"):
        im = carga.lluvia_imerg()
        lluvia = dict(zip(im["fecha"], im["lluvia_mm"]))
        normal = im.groupby(im["fecha"].dt.month)["lluvia_mm"].median().to_dict()

    i = st.select_slider("Elige un mes", options=list(range(len(ms))), value=len(ms) - 1,
                         format_func=lambda k: etiquetas[k], key="mes_campo")
    f = ms.iloc[i]
    mes = etiquetas[i]
    if f["estado"] == "sin imagen por nubes" or not f["color"]:
        st.info(f"☁️ {mes.capitalize()}: sin imagen por nubes. El satélite no logró una foto limpia "
                f"(solo el {ui.num(f['cobertura_pct'])} % del área sin nubes).", icon="☁️")
    else:
        c1, c2 = st.columns(2, gap="medium")
        c1.image(str(carga.APP_DIR / f["color"]), caption=f"{mes.capitalize()} · color real (como desde un avión)",
                 width="stretch")
        c2.image(str(carga.APP_DIR / f["ndvi"]), caption=f"{mes.capitalize()} · verdor: café = suelo pelado, "
                 "verde = cultivo sano", width="stretch")
        if f["estado"] == "parcial":
            st.caption(f"Foto parcial: el {ui.num(f['cobertura_pct'])} % del área sin nubes; "
                       "lo que se ve en blanco eran nubes.")
    # Estado de ese mes en tu zona
    partes = []
    if f["fecha"] in lluvia:
        partes.append(f"🌧️ Llovieron <b>{ui.num(lluvia[f['fecha']])} mm</b> "
                      f"(lo normal en ese mes: {ui.num(normal.get(f['fecha'].month, 0))} mm)")
    fila_z = sz[sz["fecha"] == f["fecha"]]
    if not fila_z.empty and pd.notna(fila_z["ndvi"].iloc[0]):
        v = float(fila_z["ndvi"].iloc[0])
        tipico = sz[sz["fecha"].dt.month == f["fecha"].month]["ndvi"].mean()
        como = "más verde que otros años" if v > tipico + 0.03 else (
            "menos verde que otros años" if v < tipico - 0.03 else "como otros años")
        partes.append(f"🌱 Verdor de tu zona: <b>{ui.num(v, 2)}</b> ({como})")
        if "pct_agua" in fila_z and pd.notna(fila_z["pct_agua"].iloc[0]):
            partes.append(f"💧 Agua sobre el terreno: <b>{ui.num(float(fila_z['pct_agua'].iloc[0]), 1)} %</b> de tu zona")
    elif not fila_z.empty:
        partes.append("☁️ Ese mes las nubes no dejaron medir tu zona")
    if partes:
        ui.html('<div class="estado-mes">' + "<br>".join(partes) + "</div>")

    # Galeria del ultimo año
    st.markdown("**Los últimos 12 meses**")
    tipo_g = st.segmented_control("Ver la galería en", ["color", "ndvi"], default="color", key="galeria_tipo",
                                  format_func=lambda k: "🖼️ Color real" if k == "color" else "🌱 Verdor") or "color"
    celdas = []
    for _, g in ms.tail(12).iterrows():
        et = f"{logica.MESES[g['fecha'].month - 1]} {g['fecha'].year}"
        ll = f" · {ui.num(lluvia[g['fecha']])} mm" if g["fecha"] in lluvia else ""
        if g[tipo_g]:
            celdas.append(f'<figure><img src="app/{g[tipo_g]}" alt="{et}" loading="lazy">'
                          f'<figcaption>{et}{ll}</figcaption></figure>')
        else:
            celdas.append(f'<figure><div class="sin-foto">☁️<br>sin imagen<br>por nubes</div>'
                          f'<figcaption>{et}{ll}</figcaption></figure>')
    ui.html(f'<div class="galeria">{"".join(celdas)}</div>')
    ui.fuente("Landsat 8 y 9 de la NASA: mediana de las fotos sin nubes de cada mes, recuadro de las zonas.")

# --- Cuando sembrar cada cultivo -------------------------------------------------------------
st.subheader("¿Cuándo sembrar cada cultivo aquí?")
if not ui.falta("climatologia_daule.csv", "cultivos.csv"):
    cal, notas = logica.calendario(carga.climatologia(), carga.cultivos(), sz, znombre)
    filas = []
    for cultivo, fila in cal.iterrows():
        meses = [({"cultivo": cultivo, "etapa": v} if v and v != "riesgo" else (v or None)) for v in fila]
        filas.append((f"{ui.ICONO_CULTIVO.get(cultivo, '🌱')} {cultivo}", meses))
    ui.franja_anual(carga.climatologia(), filas, mes_hoy=logica.mes_actual())
    ui.html(ui.confianza("calendario"))
    for n in notas:
        st.warning(n, icon="⚠️")

if not sz.empty:
    with st.expander("Ver los números de cada mes"):
        st.dataframe(sz.reset_index(drop=True), width="stretch", hide_index=True)
