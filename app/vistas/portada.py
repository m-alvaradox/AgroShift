"""Portada: el nombre de la app y 6 tarjetas grandes, cada una lleva a su pagina."""
import streamlit as st

from utils import ui

# Iconos simples de trazo (SVG en linea, sin archivos ni emojis)
_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>')
ICONOS = {
    "finca": '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>'
             '<path d="M2 20h20"/>',
    "jugar": '<rect x="3" y="5" width="11" height="15" rx="2" transform="rotate(-10 8.5 12.5)"/>'
             '<rect x="10" y="4" width="11" height="15" rx="2"/><path d="M15.5 9.5l1.5 2-1.5 2-1.5-2z"/>',
    "opciones": '<path d="M12 21v-8"/><path d="M12 13 6 7"/><path d="M12 13l6-6"/>'
                '<path d="M3 4h6v6"/><path d="M21 4h-6v6"/>',
    "plan": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18"/><path d="M8 3v4"/>'
            '<path d="M16 3v4"/><path d="M7 14h2"/><path d="M11 14h2"/><path d="M15 14h2"/><path d="M7 17h2"/>',
    "asistente": '<path d="M21 11.5a8.5 8.5 0 0 1-12.4 7.6L3 21l1.9-5.3A8.5 8.5 0 1 1 21 11.5z"/>'
                 '<path d="M8.5 11.5h.01"/><path d="M12.5 11.5h.01"/><path d="M16.5 11.5h.01"/>',
    "dashboard": '<path d="M3 21h18"/><rect x="5" y="11" width="3" height="7" rx="1"/>'
                 '<rect x="10.5" y="6" width="3" height="12" rx="1"/><rect x="16" y="13" width="3" height="5" rx="1"/>',
}
TARJETAS = [
    ("finca", "vistas/inicio.py", "Mi finca", "Ubica tu finca y mira cómo está tu zona."),
    ("jugar", "vistas/jugar.py", "Jugar", "Elige una carta y mira cómo te iría en la temporada."),
    ("opciones", "vistas/comparar.py", "Mis opciones", "La mejor opción para lo que quieres lograr."),
    ("plan", "vistas/plan.py", "Mi plan", "Qué hacer cada mes, desde el mes que elijas."),
    ("asistente", "vistas/asistente.py", "Asistente", "Responde 3 preguntas y te armamos el plan."),
    ("dashboard", "vistas/dashboard.py", "Dashboard", "Tu zona en gráficos con datos de la NASA."),
]

ui.html('<div class="portada-cab"><h1 class="portada-tit">AGROSHIFT</h1>'
        '<p class="portada-sub">Qué sembrar, cuándo y dónde con datos de la NASA</p></div>')

# Cada tarjeta es un st.container(key="portada_...") y su st.page_link cubre toda la tarjeta
# (estilo.py), asi toda la tarjeta es un boton y la sesion no se pierde al cambiar de pagina.
with st.container(key="portada_grid"):
    for fila in range(0, len(TARJETAS), 2):
        cols = st.columns(2, gap="medium")
        for col, (slug, pagina, nombre, linea) in zip(cols, TARJETAS[fila:fila + 2]):
            with col, st.container(key=f"portada_{slug}"):
                ui.html(f'<div class="ptj"><div class="ptj-ico">{_SVG.format(ICONOS[slug])}</div>'
                        f'<div><div class="ptj-nom">{nombre}</div><div class="ptj-lin">{linea}</div></div>'
                        '<div class="ptj-flecha" aria-hidden="true">›</div></div>')
                st.page_link(pagina, label=nombre)

ui.html('<p class="portada-pie">Daule, Guayas · Datos de NASA POWER, GPM IMERG, Landsat 8 y 9 y SRTM</p>')
st.page_link("vistas/clima.py", label="Vista técnica: clima, mi campo y recomendación",
             icon=":material/science:")
