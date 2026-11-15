"""Opciones: comparar las 3 rotaciones segun lo que le importa al productor."""
import plotly.graph_objects as go
import streamlit as st

from utils import carga, logica, ui

zid, znombre = ui.zona_actual()
esc = ui.escenario_actual()

st.title("🌱 Compara tus opciones")
ui.origen_datos()
if ui.falta("estrategias.csv", "estrategias_info.json"):
    ui.terminar_pagina()

# --- Prioridades (se guardan para las otras paginas) --------------------------------------
ICONO_CRIT = {"nota_agua": "💧", "nota_suelo": "🪱", "nota_plagas": "🐛", "nota_ingresos": "💵"}


def guardar_prioridades():
    st.session_state["prio_guardadas"] = st.session_state.get("w_prio") or []


st.pills("¿Qué es lo más importante para ti? Puedes elegir varias.",
         options=list(logica.CRITERIOS), selection_mode="multi", key="w_prio",
         default=st.session_state.get("prio_guardadas", []), on_change=guardar_prioridades,
         format_func=lambda c: f"{ICONO_CRIT[c]} {logica.CRITERIOS[c]}")
pesos = ui.pesos_actuales()

est = carga.estrategias()
info = carga.estrategias_info()
clim = carga.climatologia() if carga.disponible("climatologia_daule.csv") else None
cult = carga.cultivos() if carga.disponible("cultivos.csv") else None
comp = logica.comparar(est, zid, esc, pesos)
agua_max = float(comp["agua_m3_ha"].max())
base = comp[comp["estrategia"] == "A"]
agua_base = float(base["agua_m3_ha"].iloc[0]) if len(base) else None

st.markdown(f"Para la **{znombre.lower()}** en un **{ui.NOMBRE_ESC[esc].lower()}**, "
            "de la mejor a la menos recomendada:")

# --- Una tarjeta por opcion, de mejor a peor ------------------------------------------------
for i, fila in comp.iterrows():
    e = info[fila["estrategia"]]
    with st.container(border=True):
        if i == 0:
            st.markdown('<div class="opcion-top">⭐ La mejor para lo que te importa</div>',
                        unsafe_allow_html=True)
        izq, der = st.columns([3, 2])
        with izq:
            st.markdown(f"### {e['nombre']}")
            st.markdown(e["descripcion"])
        with der:
            st.markdown(f'<div class="estrellas">{logica.estrellas(fila["puntaje"])}</div>',
                        unsafe_allow_html=True)
            gotas = max(1, round(5 * fila["agua_m3_ha"] / agua_max))
            texto_agua = f"{ui.num(fila['agua_m3_ha'])} m³ de agua por hectárea"
            if agua_base and fila["estrategia"] != "A":
                dif = (1 - fila["agua_m3_ha"] / agua_base) * 100
                texto_agua += f" · {dif:.0f} % menos que arroz todo el año" if dif > 0 else ""
            st.markdown(f'<div class="gotas">{"💧" * gotas}</div>{texto_agua}', unsafe_allow_html=True)

        if clim is not None and cult is not None:
            plan = logica.plan(fila["estrategia"], clim, cult)
            filas = [(f"Año {k + 1}" if len(plan) > 1 else "Su año", m) for k, m in enumerate(plan)]
            ui.franja_anual(clim, filas)
        else:
            ui.falta("climatologia_daule.csv", "cultivos.csv")

        cols = st.columns(4)
        for col, (c, nombre) in zip(cols, logica.CRITERIOS.items()):
            col.progress(min(1.0, fila[c] / 10), text=f"{ICONO_CRIT[c]} {nombre}")

# --- Agua segun el tipo de anio ---------------------------------------------------------------
st.subheader("¿Cuánta agua necesita cada opción según el año?")
dz = est[est["zona_id"] == zid]
fig = go.Figure()
for esc_k in ["nina", "normal", "nino"]:
    d = dz[dz["escenario"] == esc_k].sort_values("estrategia")
    fig.add_bar(y=d["estrategia"].map(lambda s: info[s]["nombre"]), x=d["agua_m3_ha"], orientation="h",
                name=f"{ui.ICONO_ESC[esc_k]} {ui.NOMBRE_ESC[esc_k]}", marker_color=ui.COLOR_ESC[esc_k],
                hovertemplate="%{y}: %{x:,.0f} m³/ha<extra></extra>")
fig.update_layout(barmode="group", height=360, margin=dict(l=10, r=10, t=10, b=10),
                  xaxis_title="m³ de agua por hectárea", plot_bgcolor="white",
                  legend=dict(orientation="h", y=-0.25),
                  font=dict(family="Atkinson Hyperlegible, sans-serif", size=14))
st.plotly_chart(fig, width="stretch")
st.caption("En un año muy lluvioso hace falta menos riego, pero la zona baja se puede inundar.")
ui.fuente("agua de riego con el método FAO-56 (NASA POWER y los años de GPM IMERG); notas de "
          "suelo, plagas e ingresos con las reglas de P4 (scripts/calcular_estrategias.py).")

st.page_link("vistas/recomendacion.py", label="Ver por qué te recomendamos la primera", icon="✅")

# --- Conoce los cultivos (data/cultivos.csv de P4, en lenguaje simple) --------------------------
st.subheader("🌾 Conoce los cultivos")
ICONO_C = {"Arroz": "🌾", "Soya": "🫘", "Maíz duro": "🌽"}
if not ui.falta("cultivos.csv"):
    tabla_z = carga.tabla_zonas() if carga.disponible("zonas_daule.geojson") else None
    zonas_por_tipo = {}
    if tabla_z is not None:
        for n in tabla_z["nombre_comun"]:
            zonas_por_tipo.setdefault(ui.tipo_zona(n), []).append(ui.etiqueta_zona(n))
    tarjetas_c = []
    for _, c in carga.cultivos().iterrows():
        nombre = c["cultivo"]
        dias = int(c["ciclo_dias"])
        tolera = bool(c["tolera_inundacion"])
        agua_min = c.get("etc_min_mm", c.get("agua_min_mm"))
        agua_max = c.get("etc_max_mm", c.get("agua_max_mm"))
        # Donde conviene: si aguanta el agua, la zona baja; si no, las zonas que drenan
        if tolera:
            donde = zonas_por_tipo.get("baja", ["la zona baja"])
            por_que = "aguanta el terreno inundado"
        else:
            donde = zonas_por_tipo.get("loma", []) + zonas_por_tipo.get("ladera", [])
            por_que = "necesita que el agua drene: en la zona que se encharca se ahoga"
        extra_arroz = (" Además necesita agua para mantener el terreno inundado." if nombre == "Arroz" else "")
        tarjetas_c.append(
            f'<div class="idea"><div class="idea-ico">{ICONO_C.get(nombre, "🌱")}</div><div>'
            f'<div class="idea-tit">{nombre}</div>'
            f'<p>⏱️ <b>{dias} días</b> de siembra a cosecha (unos {round(dias / 30)} meses).</p>'
            f'<p>💧 Usa entre <b>{ui.num(agua_min)} y {ui.num(agua_max)} mm</b> de agua por ciclo (lo que la '
            f'planta toma y evapora); pide más a mitad del ciclo.{extra_arroz}</p>'
            f'<p>🌊 ¿Aguanta el encharcamiento? <b>{"Sí ✅" if tolera else "No ❌"}</b></p>'
            f'<p>📍 Conviene en: <b>{", ".join(donde) or "—"}</b>, porque {por_que}.</p></div></div>')
    ui.html(f'<div class="ideas">{"".join(tarjetas_c)}</div>')
    ui.html(ui.confianza("calendario"))
    ui.fuente("ciclos del INIAP y agua de referencia de la FAO (agencia de la ONU para la agricultura), "
              "catálogo de cultivos del equipo; zonas según el relieve del satélite SRTM.")

# --- El suelo de cada zona -----------------------------------------------------------------------
st.subheader("🪨 El terreno de cada zona")
if not ui.falta("zonas_daule.geojson"):
    tz = carga.tabla_zonas().sort_values("zona_id")
    filas_s = []
    for _, z in tz.iterrows():
        n = z["nombre_comun"]
        pend = z.get("pendiente")
        elev = z.get("elevacion")
        desc_p = ("casi plano" if pend < 3 else "con algo de pendiente" if pend < 5 else "con pendiente")
        filas_s.append(
            f'<div class="idea"><div class="idea-ico">{ui.icono_zona(n)}</div><div>'
            f'<div class="idea-tit">{ui.etiqueta_zona(n)}</div>'
            f'<p>⛰️ Altura promedio: <b>{ui.num(elev, 1)} m</b> sobre el mar.</p>'
            f'<p>📐 Pendiente promedio: <b>{ui.num(pend, 1)}°</b> ({desc_p}).</p></div></div>')
    ui.html(f'<div class="ideas">{"".join(filas_s)}</div>')
    st.info("Todavía no tenemos datos de suelo de cada finca (textura, drenaje, fertilidad). "
            "Por ahora usamos la altura y la pendiente de cada zona.", icon="🪨")
    ui.html(ui.confianza("zonas"))
    ui.fuente("relieve del satélite SRTM de la NASA, zonas del equipo.")
