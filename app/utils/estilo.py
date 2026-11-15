"""
Todo el estilo visual de la app en un solo lugar.

Se inyecta una vez desde streamlit_app.py con estilo.aplicar().
Mobile-first: una columna en celular y dos en pantalla ancha.
Los contenedores con key="..." de Streamlit reciben la clase "st-key-...",
que es la que se usa aqui para dar color a cartas, casillas y menu.
"""
import streamlit as st

# --- Paleta ---------------------------------------------------------------------------
VERDE, VERDE_FONDO = "#2E7D32", "#E8F5E9"
AMARILLO, AMARILLO_FONDO, AMARILLO_TEXTO = "#F9A825", "#FFF8E1", "#7A5600"
MARRON, MARRON_FONDO = "#6D4C41", "#EFEBE9"
AZUL, AZUL_FONDO = "#1E88E5", "#E3F2FD"
ROJO, ROJO_FONDO = "#C62828", "#FFEBEE"
FONDO_APP = "#FAFAF5"
TEXTO = "#1F2A1F"

# Color de cada carta: (borde, fondo, texto)
COLOR_CARTA = {
    "arroz": (AZUL, AZUL_FONDO, "#0D47A1"),
    "maiz": (AMARILLO, AMARILLO_FONDO, AMARILLO_TEXTO),
    "soya": (VERDE, VERDE_FONDO, "#1B5E20"),
    "descanso": (MARRON, MARRON_FONDO, "#4E342E"),
}


def _css_cartas() -> str:
    reglas = []
    for slug, (borde, fondo, texto) in COLOR_CARTA.items():
        reglas.append(f"""
.st-key-naipe_no_{slug}, .st-key-naipe_sel_{slug}, [class*="st-key-temp_llena_"][class*="_{slug}"] {{
  background: {fondo}; border-color: {borde}; }}
.st-key-naipe_no_{slug} .carta-nombre, .st-key-naipe_sel_{slug} .carta-nombre,
[class*="st-key-temp_llena_"][class*="_{slug}"] .carta-nombre {{ color: {texto}; }}
.mini.{slug} {{ background: {fondo}; border-color: {borde}; color: {texto}; }}""")
    return "\n".join(reglas)


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
:root {{
  --verde: {VERDE}; --verde-fondo: {VERDE_FONDO};
  --amarillo: {AMARILLO}; --amarillo-fondo: {AMARILLO_FONDO}; --amarillo-texto: {AMARILLO_TEXTO};
  --marron: {MARRON}; --marron-fondo: {MARRON_FONDO};
  --azul: {AZUL}; --azul-fondo: {AZUL_FONDO};
  --rojo: {ROJO}; --rojo-fondo: {ROJO_FONDO};
  --fondo: {FONDO_APP}; --texto: {TEXTO};
  --sombra: 0 2px 10px rgba(46, 60, 40, .10);
  --radio: 20px;
}}

/* ---------- Base ---------- */
html, body, .stApp, [class*="st-"]:not([data-testid="stIconMaterial"]):not([data-testid="stAlertDynamicIcon"]),
button, input, textarea {{
  font-family: 'Nunito', system-ui, sans-serif !important;
}}
.stApp {{ background: var(--fondo); color: var(--texto); }}
[data-testid="stMainBlockContainer"], .block-container {{
  padding-top: 3.2rem; padding-bottom: 3rem; max-width: 1100px;
}}
h1, h2, h3, h4 {{ font-weight: 800 !important; color: #1B4D20; letter-spacing: -.01em; }}
h1 {{ font-size: 2rem !important; line-height: 1.15 !important; }}
h3 {{ font-size: 1.35rem !important; }}
p, li, label, .stMarkdown {{ font-size: 1.05rem; line-height: 1.5; }}
[data-testid="stCaptionContainer"] p {{ font-size: .95rem; }}

/* Botones grandes (48 px o mas) */
.stButton button, [data-testid="stPageLink-NavLink"], button[data-variant="segmented_control"],
button[data-variant="pills"] {{
  min-height: 48px; font-size: 1.05rem !important; font-weight: 700 !important; border-radius: 14px !important;
}}
.stButton button p, button[data-variant="segmented_control"] p, button[data-variant="pills"] p {{
  font-size: 1.05rem !important; font-weight: 700 !important;
}}
.stButton button[kind="primary"], [data-testid="stBaseButton-primary"] {{
  background: var(--verde); border-color: var(--verde); color: #fff;
}}
.stButton button:disabled {{ opacity: .45; }}
button[data-variant="segmented_control"][aria-checked="true"], button[data-variant="pills"][aria-checked="true"],
button[data-variant="pills"][aria-pressed="true"] {{
  background: var(--verde) !important; border-color: var(--verde) !important; color: #fff !important;
}}
button[data-variant="segmented_control"][aria-checked="true"] p, button[data-variant="pills"][aria-checked="true"] p,
button[data-variant="pills"][aria-pressed="true"] p {{ color: #fff !important; }}

/* Tarjeta blanca generica */
.tarjeta, [class*="st-key-tarjeta"] {{
  background: #fff; border-radius: var(--radio); box-shadow: var(--sombra); padding: 1rem 1.1rem;
}}

/* ---------- Cabecera y menu ---------- */
.marca {{ display: flex; flex-wrap: wrap; align-items: baseline; column-gap: .6rem; margin-bottom: .3rem; }}
.marca b {{ font-size: 1.6rem; font-weight: 900; color: var(--verde); }}
.marca span {{ color: #5B6B5E; font-size: 1rem; }}
.st-key-nav {{ background: #fff; border-radius: var(--radio); box-shadow: var(--sombra); padding: .35rem; }}
.st-key-nav [data-testid="stPageLink-NavLink"] {{ justify-content: center; border-radius: 14px; padding: .35rem .25rem; }}
.st-key-nav [data-testid="stPageLink-NavLink"] p {{ font-size: .9rem; font-weight: 700; color: #3E4E40; }}
[class*="st-key-nav_on_"] [data-testid="stPageLink-NavLink"] {{ background: var(--verde-fondo); }}
[class*="st-key-nav_on_"] [data-testid="stPageLink-NavLink"] p {{ color: var(--verde); font-weight: 900; }}
.st-key-selector {{ background: #fff; border-radius: var(--radio); box-shadow: var(--sombra); padding: .6rem .9rem .8rem; }}
.st-key-selector label p {{ font-weight: 800; font-size: 1.05rem; color: #1B4D20; }}
.st-key-nav_tecnica {{ background: var(--marron-fondo); border-radius: 14px; padding: .4rem .7rem; }}

/* ---------- Etiquetas de fuente ---------- */
.tag {{ display: inline-block; font-size: .8rem; font-weight: 700; border-radius: 999px;
       padding: .1rem .55rem; margin-top: .35rem; }}
.tag.nasa {{ background: var(--azul-fondo); color: #0D47A1; }}
.tag.sim {{ background: var(--amarillo-fondo); color: var(--amarillo-texto); }}

/* ---------- Mi finca ---------- */
.resumen {{ background: var(--verde); color: #fff; border-radius: var(--radio); padding: 1.1rem 1.3rem;
           font-size: 1.35rem; font-weight: 800; line-height: 1.3; box-shadow: var(--sombra); margin-bottom: .6rem; }}
.semaforo {{ display: flex; gap: .9rem; align-items: center; background: #fff; border-radius: var(--radio);
            box-shadow: var(--sombra); padding: .8rem 1rem; margin-bottom: .7rem; border-left: 8px solid #B0BEC5; }}
.semaforo.verde {{ border-left-color: var(--verde); }}
.semaforo.amarillo {{ border-left-color: var(--amarillo); }}
.semaforo.rojo {{ border-left-color: var(--rojo); background: var(--rojo-fondo); }}
.luces {{ display: flex; flex-direction: column; gap: 4px; background: #37474F; padding: 5px; border-radius: 12px; }}
.luces i {{ width: 18px; height: 18px; border-radius: 50%; background: #607D8B; opacity: .35; display: block; }}
.semaforo.rojo .luces i.r {{ background: #EF5350; opacity: 1; box-shadow: 0 0 8px #EF5350; }}
.semaforo.amarillo .luces i.a {{ background: #FFCA28; opacity: 1; box-shadow: 0 0 8px #FFCA28; }}
.semaforo.verde .luces i.v {{ background: #66BB6A; opacity: 1; box-shadow: 0 0 8px #66BB6A; }}
.sem-tit {{ font-size: 1.15rem; font-weight: 800; }}
.sem-tit b {{ font-weight: 900; margin-left: .3rem; }}
.semaforo.verde .sem-tit b {{ color: var(--verde); }}
.semaforo.amarillo .sem-tit b {{ color: var(--amarillo-texto); }}
.semaforo.rojo .sem-tit b {{ color: var(--rojo); }}
.semaforo p {{ margin: .1rem 0 0; font-size: 1rem; }}

.meses12 {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; }}
.mes12 {{ border-radius: 14px; text-align: center; padding: .45rem 0 .35rem; font-weight: 800; font-size: 1rem; }}
.mes12 span {{ display: block; font-size: 1.6rem; line-height: 1.2; }}
.mes12.lluvioso {{ background: var(--azul-fondo); color: #0D47A1; }}
.mes12.transicion {{ background: #EEF5FB; color: #2C5D86; }}
.mes12.seco {{ background: var(--amarillo-fondo); color: var(--amarillo-texto); }}
.mes12.hoy {{ outline: 3px solid var(--verde); outline-offset: 1px; }}
.leyenda {{ display: flex; flex-wrap: wrap; gap: .4rem 1rem; font-size: .95rem; color: #4A5A4D; margin-top: .5rem; }}
.leyenda i {{ display: inline-block; width: .9rem; height: .9rem; border-radius: 3px; vertical-align: -2px; margin-right: .3rem; }}

.st-key-cta_jugar {{ background: var(--amarillo-fondo); border: 3px solid var(--amarillo); border-radius: var(--radio);
                    padding: 1rem 1.1rem; box-shadow: var(--sombra); }}
.st-key-cta_jugar .cta-tit {{ font-size: 1.3rem; font-weight: 900; color: var(--amarillo-texto); }}
.st-key-cta_jugar [data-testid="stPageLink-NavLink"] {{ background: var(--verde); justify-content: center; }}
.st-key-cta_jugar [data-testid="stPageLink-NavLink"] p {{ color: #fff; font-weight: 800; font-size: 1.1rem; }}

/* ---------- Jugar: temporadas y cartas ----------
   Cada tarjeta es un st.container(key="temp_..." o "naipe_...").
   Todo va en flujo normal: sin posiciones absolutas, margenes negativos ni alturas fijas. */

/* Secciones: 16px de gap de Streamlit + 16px de margen = 32px entre secciones */
.st-key-sec_cartas, .st-key-sec_atajos, .st-key-sec_jugar {{ margin-top: 16px; }}
[class*="st-key-sec_"] h3 {{ padding: 0 0 4px !important; margin: 0 !important; }}

/* Filas: 16px entre tarjetas y todas de la misma altura */
.st-key-fila_temporadas [data-testid="stHorizontalBlock"],
.st-key-fila_cartas [data-testid="stHorizontalBlock"] {{ gap: 16px !important; align-items: stretch !important; }}
.st-key-fila_temporadas [data-testid="stColumn"],
.st-key-fila_cartas [data-testid="stColumn"] {{ display: flex !important; flex-direction: column; }}
.st-key-fila_temporadas [data-testid="stColumn"] > div,
.st-key-fila_cartas [data-testid="stColumn"] > div {{ flex: 1 1 auto; display: flex; flex-direction: column; }}
/* Streamlit envuelve cada contenedor en un stLayoutWrapper que no crece: se le deja crecer */
.st-key-fila_temporadas [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"],
.st-key-fila_cartas [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] {{
  flex: 1 1 auto; display: flex; flex-direction: column; }}

/* La tarjeta */
[class*="st-key-temp_"], [class*="st-key-naipe_"] {{
  flex: 1 1 auto; display: flex; flex-direction: column; gap: 16px !important;
  padding: 20px; border-radius: 20px; border: 3px solid transparent; background: #fff;
  box-shadow: var(--sombra); box-sizing: border-box;
}}
/* Streamlit pone margin-bottom:-16px al texto: se anula para que no se coma el espacio del boton */
[class*="st-key-temp_"] [data-testid="stMarkdownContainer"],
[class*="st-key-naipe_"] [data-testid="stMarkdownContainer"],
[class*="st-key-tarjplan_"] [data-testid="stMarkdownContainer"] {{ margin-bottom: 0 !important; }}
/* el boton va abajo, a todo el ancho */
[class*="st-key-temp_"] > :last-child, [class*="st-key-naipe_"] > :last-child {{ margin-top: auto; }}
[class*="st-key-temp_"] .stButton, [class*="st-key-naipe_"] .stButton,
[class*="st-key-temp_"] .stButton button, [class*="st-key-naipe_"] .stButton button {{ width: 100%; min-height: 48px; }}

/* Contenido: 8px entre icono, nombre y frase */
.cuerpo {{ display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center; }}
.temp-tit {{ font-weight: 900; font-size: 1.1rem; }}
.temp-sub {{ font-size: .95rem; color: #5B6B5E; }}
.carta-ico {{ font-size: 2.4rem; line-height: 1.1; }}
.carta-nombre {{ font-weight: 900; font-size: 1.2rem; line-height: 1.2; }}
.carta-frase {{ font-size: 1rem; line-height: 1.3; color: #37474F; min-height: 2.6em; }}

/* Temporada vacia: borde punteado gris y "+" al centro */
[class*="st-key-temp_vacia_"] {{ border: 3px dashed #B0BAB0; background: #FBFCFA; box-shadow: none; }}
.hueco {{ font-size: 2.4rem; font-weight: 900; line-height: 1.1; color: #9AA59A; }}
.hueco-txt {{ font-size: 1rem; color: #8A978C; min-height: 2.6em; }}
/* Temporada llena: color del cultivo y borde solido (ver _css_cartas) */
[class*="st-key-temp_llena_"] {{ border-style: solid; }}

/* Carta elegida: borde mas oscuro y anillo interior (no cambia el tamaño) */
[class*="st-key-naipe_sel_"] {{ border-color: #1B4D20 !important; box-shadow: inset 0 0 0 3px #1B4D20, var(--sombra); }}
{_css_cartas()}
.mini {{ display: inline-flex; align-items: center; gap: .25rem; border: 2px solid; border-radius: 12px;
        padding: .15rem .5rem; font-weight: 800; font-size: .98rem; margin: .15rem .2rem .15rem 0; }}

/* ---------- Resultado ---------- */
.barra {{ margin: .2rem 0 .8rem; }}
.barra-top {{ display: flex; justify-content: space-between; font-weight: 800; font-size: 1.05rem; margin-bottom: .25rem; }}
.palabra {{ border-radius: 999px; padding: 0 .6rem; font-size: .95rem; }}
.palabra.Bien {{ background: var(--verde-fondo); color: var(--verde); }}
.palabra.Regular {{ background: var(--amarillo-fondo); color: var(--amarillo-texto); }}
.palabra.Bajo {{ background: var(--rojo-fondo); color: var(--rojo); }}
.segs {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 4px; }}
.segs i {{ height: 18px; border-radius: 5px; background: #E0E4DD; display: block; }}
.segs.azul i.on {{ background: var(--azul); }}
.segs.verde i.on {{ background: var(--verde); }}
.segs.amarillo i.on {{ background: var(--amarillo); }}
.planta {{ text-align: center; }}
.planta svg {{ width: 150px; height: auto; }}
.planta-txt {{ font-weight: 800; font-size: 1.05rem; color: #3E4E40; }}
.frase-res {{ font-size: 1.25rem; font-weight: 800; line-height: 1.35; margin: .3rem 0 .6rem; }}
.evento {{ border-radius: 16px; padding: .7rem .9rem; margin-bottom: .55rem; font-size: 1.05rem; border-left: 6px solid; }}
.evento.malo {{ background: var(--rojo-fondo); border-color: var(--rojo); }}
.evento.bueno {{ background: var(--verde-fondo); border-color: var(--verde); }}
.evento.info {{ background: var(--azul-fondo); border-color: var(--azul); }}
.logro {{ background: var(--amarillo-fondo); border: 2px solid var(--amarillo); color: var(--amarillo-texto);
         border-radius: 16px; padding: .6rem .9rem; font-weight: 900; font-size: 1.1rem; text-align: center; margin: .4rem 0; }}

/* ---------- Comparar ---------- */
[class*="st-key-tarjplan_"] {{ background: #fff; border-radius: var(--radio); box-shadow: var(--sombra);
                              padding: 20px; border: 3px solid transparent; }}
[class*="st-key-tarjplan_top_"] {{ border-color: var(--verde); }}
.cinta {{ background: var(--verde); color: #fff; font-weight: 900; border-radius: 999px; padding: .2rem .8rem;
         display: inline-block; font-size: .95rem; }}
.plan-nombre {{ font-weight: 900; font-size: 1.25rem; margin: .3rem 0 .2rem; }}
.pro, .contra {{ font-size: 1rem; margin: .2rem 0; }}

/* ---------- Mi plan ---------- */
.plan-lista {{ display: grid; grid-template-columns: 1fr; gap: 8px; }}
.plan-mes {{ display: flex; align-items: center; gap: .8rem; background: #fff; border-radius: 16px;
            box-shadow: var(--sombra); padding: .6rem .9rem; }}
.plan-mes .ico {{ font-size: 1.8rem; width: 2.2rem; text-align: center; }}
.plan-mes .mes {{ font-weight: 900; width: 2.8rem; color: #1B4D20; }}
.plan-mes .etapa {{ font-size: .85rem; font-weight: 800; color: #5B6B5E; text-transform: uppercase; }}
.plan-mes .acc {{ font-size: 1.02rem; }}
.plan-mes.hoy {{ outline: 3px solid var(--verde); background: var(--verde-fondo); }}
.consejo {{ background: var(--amarillo-fondo); border-radius: 16px; padding: .8rem 1rem; margin-bottom: .6rem;
           font-size: 1.05rem; border-left: 6px solid var(--amarillo); }}

/* ---------- Asistente (estilo WhatsApp) ---------- */
.wa {{ max-width: 560px; margin: 0 auto; border-radius: var(--radio); overflow: hidden; box-shadow: var(--sombra); }}
.wa-top {{ background: #0B6E4F; color: #fff; padding: .7rem 1rem; display: flex; align-items: center; gap: .7rem; }}
.wa-avatar {{ width: 42px; height: 42px; border-radius: 50%; background: #E8F5E9; display: flex;
             align-items: center; justify-content: center; font-size: 1.4rem; }}
.wa-top b {{ font-size: 1.1rem; }}
.wa-top small {{ display: block; opacity: .85; font-size: .85rem; }}
.wa-body {{ background: #EFE7DC; padding: .9rem; display: flex; flex-direction: column; gap: .5rem; min-height: 260px; }}
.burbuja {{ max-width: 85%; padding: .55rem .8rem .35rem; border-radius: 14px; font-size: 1.02rem; line-height: 1.4;
           box-shadow: 0 1px 1px rgba(0,0,0,.12); }}
.burbuja.bot {{ background: #fff; align-self: flex-start; border-top-left-radius: 3px; }}
.burbuja.yo {{ background: #D9FDD3; align-self: flex-end; border-top-right-radius: 3px; }}
.burbuja.alerta {{ background: var(--rojo-fondo); border-left: 5px solid var(--rojo); }}
.burbuja .hora {{ display: block; text-align: right; font-size: .75rem; color: #667781; margin-top: .1rem; }}
.st-key-rapidas {{ max-width: 560px; margin: 0 auto; }}
.wa-nota {{ max-width: 560px; margin: .4rem auto 0; font-size: .9rem; color: #5B6B5E; text-align: center; }}

/* ---------- Vista tecnica (paginas anteriores) ---------- */
.franja-scroll {{ overflow-x: auto; padding-bottom: .4rem; }}
.franja {{ display: grid; grid-template-columns: 7.2rem repeat(12, minmax(3.1rem, 1fr)); gap: 4px; min-width: 760px; }}
.franja .etq {{ display: flex; align-items: center; font-weight: 700; color: #1B4D20; font-size: .95rem; }}
.franja .mes {{ text-align: center; border-radius: 6px; padding: .35rem 0 .3rem; font-weight: 700; font-size: .9rem; position: relative; }}
.franja .mes small {{ display: block; font-weight: 400; font-size: .72rem; white-space: nowrap; }}
.mes.lluvioso {{ background: #DCEAF5; color: #1D4F75; }}
.mes.transicion {{ background: #EBF2F7; color: #3B5E78; }}
.mes.seco {{ background: #F6ECCB; color: #6E5200; }}
.franja .hoy {{ outline: 3px solid #1B4D20; outline-offset: 1px; }}
.franja .hoy::after {{ content: "hoy"; position: absolute; top: -1.15rem; left: 50%; transform: translateX(-50%);
                      font-size: .72rem; color: #1B4D20; font-weight: 700; }}
.franja .celda {{ min-height: 3.3rem; border-radius: 8px; display: flex; flex-direction: column; align-items: center;
                 justify-content: center; font-size: .72rem; line-height: 1.1; text-align: center; }}
.celda .ico {{ font-size: 1.35rem; }}
.celda.siembra {{ background: #4E8B3A; color: #fff; }}
.celda.crece {{ background: #CFE3C4; color: #1B4D20; }}
.celda.cosecha {{ background: #F1D78A; color: #5A4300; }}
.celda.riesgo {{ background: #F6D3CE; color: #7E1F14; }}
.celda.vacio {{ border: 1px dashed #C9D3C6; color: #8A978C; }}
.senal {{ border-left: 6px solid #9AA5A0; background: #fff; border-radius: 4px 14px 14px 4px; padding: .8rem 1rem; height: 100%; }}
.senal .tit {{ font-weight: 800; font-size: 1.12rem; color: #1B4D20; margin: .1rem 0 .25rem; }}
.senal .que {{ font-size: .85rem; color: #5B6B5E; }}
.senal p {{ font-size: .98rem; margin: 0; }}
.senal.bien {{ border-color: #4E8B3A; }}
.senal.atento {{ border-color: #C9A227; }}
.senal.alerta {{ border-color: #C0392B; background: #FDF4F2; }}
.accion {{ background: #1B4D20; color: #F3F8EF; border-radius: 14px; padding: 1rem 1.2rem; margin: .6rem 0 1rem; }}
.accion .que {{ font-size: .9rem; opacity: .85; }}
.accion .txt {{ font-size: 1.35rem; font-weight: 700; line-height: 1.3; margin-top: .2rem; }}
.opcion-top {{ font-weight: 700; color: #4E8B3A; font-size: .95rem; }}
.estrellas {{ color: #C9A227; font-size: 1.35rem; letter-spacing: .08em; }}
.gotas {{ font-size: 1.1rem; letter-spacing: .05em; }}

/* ---------- Mi campo: fotos de cada mes ---------- */
.estado-mes {{ background: #fff; border-radius: 14px; box-shadow: var(--sombra); padding: .7rem .9rem;
              line-height: 1.7; margin: .4rem 0 1rem; }}
.galeria {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .6rem; margin: .4rem 0; }}
.galeria figure {{ margin: 0; background: #fff; border-radius: 12px; box-shadow: var(--sombra); padding: .35rem; }}
.galeria img {{ width: 100%; aspect-ratio: 1 / 1; object-fit: cover; border-radius: 8px; background: #ECEFF1; display: block; }}
.galeria .sin-foto {{ aspect-ratio: 1 / 1; border-radius: 8px; background: #ECEFF1; color: #607D8B; display: flex;
                     flex-direction: column; justify-content: center; align-items: center; text-align: center;
                     font-size: .8rem; line-height: 1.3; }}
.galeria figcaption {{ font-size: .8rem; text-align: center; color: #3E4E40; padding-top: .25rem; font-weight: 700; }}
@media (max-width: 640px) {{ .galeria {{ grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .4rem; }} }}

/* ---------- Confianza y aviso tecnico ---------- */
.conf {{ display: inline-block; font-size: .85rem; line-height: 1.35; border-radius: 10px; padding: .25rem .6rem;
        margin: .35rem 0 .1rem; color: #3E4E40; background: #F1F3EF; }}
.conf.alta {{ background: #E8F5E9; }}
.conf.media {{ background: #FFF8E1; }}
.conf.baja {{ background: #FFEBEE; }}
.aviso-tecnico {{ background: #fff; border: 2px dashed #C5D3C0; border-radius: 14px; padding: .6rem .9rem;
                 font-size: .95rem; color: #3E4E40; margin: 1.2rem 0 .2rem; }}
/* ---------- Dashboard ilustrativo ---------- */
.hero {{ background: linear-gradient(135deg, #1B4D20 0%, #2E7D32 55%, #4E8B3A 100%); color: #fff;
        border-radius: 26px; padding: 1.6rem 1.7rem 1.3rem; margin: .3rem 0 1.2rem; box-shadow: var(--sombra); }}
.hero-sat {{ font-size: .95rem; font-weight: 700; opacity: .85; }}
.hero-tit {{ font-size: 2.5rem; font-weight: 900; line-height: 1.08; letter-spacing: -.02em; margin: .2rem 0 .5rem; }}
.hero-frase {{ font-size: 1.3rem; font-weight: 700; line-height: 1.35; color: #FFF8E1; max-width: 46rem; }}
.chips {{ display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .9rem; }}
.chips span {{ background: rgba(255,255,255,.16); border-radius: 999px; padding: .2rem .7rem; font-size: .9rem; font-weight: 700; }}
.chips .chip-ayuda {{ background: transparent; opacity: .8; font-weight: 600; }}
.picto-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin: .2rem 0 .5rem; }}
.picto {{ background: #fff; border-radius: var(--radio); box-shadow: var(--sombra); padding: 1.1rem 1.15rem 1rem;
         border-top: 6px solid var(--verde); min-width: 0; display: flex; flex-direction: column; gap: .35rem; }}
.picto.azul {{ border-top-color: var(--azul); }}
.picto.amarillo {{ border-top-color: var(--amarillo); }}
.picto.marron {{ border-top-color: var(--marron); }}
.picto-cab {{ display: flex; align-items: center; gap: .55rem; }}
.picto-ico {{ font-size: 2.2rem; line-height: 1; }}
.picto-tit {{ font-size: 1rem; font-weight: 800; color: #5B6B5E; line-height: 1.2; }}
.picto-num {{ font-size: 2.3rem; font-weight: 900; color: #1B4D20; line-height: 1.05; }}
.picto-num small {{ font-size: 1.05rem; font-weight: 700; color: #5B6B5E; }}
.picto-fila {{ display: flex; flex-wrap: wrap; align-items: center; gap: .2rem .5rem; min-height: 1.9rem; }}
.iconos.cultivos {{ white-space: nowrap; }}
.picto-etq {{ font-size: .85rem; font-weight: 800; color: #5B6B5E; min-width: 4.4rem; }}
.picto-etq:empty {{ display: none; }}
.iconos {{ font-size: 1.35rem; line-height: 1.25; letter-spacing: .03em; overflow-wrap: anywhere; }}
.iconos .off {{ opacity: .16; filter: grayscale(1); }}
.iconos .medio {{ opacity: .45; }}
.picto-frase {{ font-size: .95rem; line-height: 1.35; color: #3E4E40; margin-top: auto; padding-top: .2rem; }}
.fuente-peq {{ font-size: .82rem; color: #7A867C; line-height: 1.4; margin: .35rem 0 .2rem; }}
.bloque-tit {{ font-size: 1.6rem; font-weight: 900; color: #1B4D20; margin: 2rem 0 .7rem; letter-spacing: -.01em; }}
.st-key-dash_anio, [class*="st-key-graf_"] {{ background: #fff; border-radius: var(--radio); box-shadow: var(--sombra);
                                              padding: 1.1rem 1.2rem .9rem; }}
[class*="st-key-graf_"] {{ height: 100%; }}
.anio12 {{ display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 6px; margin: .2rem 0 .3rem; }}
.anio12 .m {{ border-radius: 14px; text-align: center; padding: .5rem 0 .4rem; font-weight: 800; font-size: .95rem;
             background: #F1F3EF; color: #3E4E40; }}
.anio12 .m span {{ display: block; font-size: 1.7rem; line-height: 1.25; }}
.anio12 .m small {{ display: block; font-size: .7rem; font-weight: 900; color: var(--verde); }}
.anio12 .lluvioso {{ background: var(--azul-fondo); color: #0D47A1; }}
.anio12 .transicion {{ background: #EEF5FB; color: #2C5D86; }}
.anio12 .seco {{ background: var(--amarillo-fondo); color: var(--amarillo-texto); }}
.anio12 .hoy {{ outline: 3px solid var(--verde); outline-offset: 1px; }}
.sec-cab {{ display: flex; align-items: center; gap: .6rem; margin: .7rem 0 .4rem; }}
.sec-ico {{ font-size: 2rem; line-height: 1; }}
.sec-tit {{ font-size: 1.28rem; font-weight: 900; color: #1B4D20; line-height: 1.2; }}
.graf-ley {{ font-size: .85rem; color: #3E4E40; display: flex; flex-wrap: wrap; align-items: center; gap: .25rem .55rem; }}
.graf-ley i {{ display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-left: .2rem; }}
.conclusion {{ background: var(--amarillo-fondo); border-left: 6px solid var(--amarillo); border-radius: 12px;
              padding: .6rem .85rem; font-weight: 800; font-size: 1.05rem; line-height: 1.35; color: #3E2F00;
              margin: .1rem 0 .5rem; }}
.plan-lista-agua {{ display: flex; flex-direction: column; gap: .7rem; margin: .3rem 0 .5rem; }}
.plan-fila {{ border: 2px solid #E3E9E0; border-radius: 16px; padding: .7rem .9rem; }}
.plan-fila.mejor {{ border-color: var(--verde); background: var(--verde-fondo); }}
.plan-cab {{ display: flex; flex-wrap: wrap; align-items: center; gap: .3rem .6rem; }}
.plan-letra {{ background: #1B4D20; color: #fff; border-radius: 8px; padding: 0 .5rem; font-weight: 900; }}
.plan-cult {{ font-size: 1.25rem; }}
.plan-badge {{ background: var(--verde); color: #fff; border-radius: 999px; padding: .05rem .6rem; font-size: .8rem; font-weight: 800; }}
.plan-gotas {{ display: flex; flex-wrap: wrap; align-items: center; gap: .2rem .7rem; margin-top: .3rem; }}
.plan-num {{ font-weight: 900; color: #0D47A1; font-size: 1.1rem; }}
.plan-detalle {{ font-size: .85rem; color: #5B6B5E; margin-top: .15rem; }}
.ideas {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }}
.idea {{ display: flex; gap: .9rem; background: #fff; border-radius: var(--radio); box-shadow: var(--sombra); padding: 1.1rem 1.2rem; }}
.idea-ico {{ font-size: 2.4rem; line-height: 1; }}
.idea-tit {{ font-weight: 900; color: #1B4D20; font-size: 1.12rem; margin-bottom: .2rem; }}
.idea p {{ margin: 0; font-size: 1rem; line-height: 1.45; }}
.dash-pie {{ font-size: .88rem; color: #5B6B5E; margin: 1.4rem 0 .4rem; }}

/* ---------- Portada: el menu principal ---------- */
.portada-cab {{ text-align: center; margin: .2rem 0 1.8rem; }}
.portada-cab h1.portada-tit {{ font-size: 3.8rem !important; font-weight: 900 !important; letter-spacing: .14em;
  color: var(--verde) !important; margin: 0 !important; padding: 0 0 0 .14em !important; line-height: 1.05 !important; }}
.portada-sub {{ font-size: 1.3rem !important; color: #4A5A4D; margin: .5rem 0 0; font-weight: 700; }}
.portada-cab::after {{ content: ""; display: block; width: 72px; height: 5px; border-radius: 3px;
  background: var(--amarillo); margin: 1rem auto 0; }}
.st-key-portada_grid [data-testid="stHorizontalBlock"] {{ gap: 1.1rem !important; }}
[class*="st-key-portada_"]:not(.st-key-portada_grid) {{
  position: relative; background: #fff; border-radius: 24px; box-shadow: var(--sombra); padding: 1.4rem 1.3rem;
  border: 2px solid #E6ECE2; min-height: 132px; justify-content: center;
  transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease; }}
[class*="st-key-portada_"]:not(.st-key-portada_grid):hover {{
  transform: translateY(-4px); box-shadow: 0 12px 28px rgba(46, 60, 40, .18); border-color: var(--verde); }}
[class*="st-key-portada_"]:not(.st-key-portada_grid):has(a:focus-visible) {{ outline: 3px solid var(--amarillo); outline-offset: 2px; }}
/* el st.page_link cubre toda la tarjeta: toda la tarjeta es el boton */
[class*="st-key-portada_"]:not(.st-key-portada_grid) > [data-testid="stElementContainer"]:has([data-testid="stPageLink"]) {{
  position: absolute !important; inset: 0; z-index: 3; margin: 0 !important; width: 100% !important; }}
[class*="st-key-portada_"] [data-testid="stPageLink"], [class*="st-key-portada_"] [data-testid="stPageLink"] > div {{ height: 100%; }}
[class*="st-key-portada_"] [data-testid="stPageLink-NavLink"] {{ width: 100%; height: 100%; opacity: 0; margin: 0; }}
.ptj {{ display: flex; align-items: center; gap: 1.1rem; }}
.ptj-ico {{ width: 68px; height: 68px; border-radius: 20px; flex: none; display: flex; align-items: center;
  justify-content: center; background: var(--verde-fondo); color: var(--verde); }}
.ptj-ico svg {{ width: 36px; height: 36px; }}
.st-key-portada_jugar .ptj-ico {{ background: #FFF3CD; color: #9A6B00; }}
.st-key-portada_opciones .ptj-ico {{ background: var(--azul-fondo); color: #1565C0; }}
.st-key-portada_plan .ptj-ico {{ background: #F3E5D8; color: #8D5524; }}
.st-key-portada_asistente .ptj-ico {{ background: #DDF3E8; color: #0B6E4F; }}
.st-key-portada_dashboard .ptj-ico {{ background: #EDE7F6; color: #5E35B1; }}
.ptj-nom {{ font-size: 1.5rem; font-weight: 900; color: #1B4D20; line-height: 1.15; }}
.ptj-lin {{ font-size: 1.02rem; color: #4A5A4D; line-height: 1.35; margin-top: .15rem; }}
.ptj-flecha {{ margin-left: auto; font-size: 2.2rem; line-height: 1; color: #B5C0B2; transition: color .15s, transform .15s; }}
[class*="st-key-portada_"]:hover .ptj-flecha {{ color: var(--verde); transform: translateX(3px); }}
.portada-pie {{ text-align: center; color: #6B786D; font-size: .95rem !important; margin: 1.6rem 0 0; }}

/* ---------- Mi finca: ubicar la finca ---------- */
.st-key-paso_ubicar {{ background: #fff; border-radius: var(--radio); box-shadow: var(--sombra); padding: 1.3rem 1.3rem 1.1rem;
  border-top: 6px solid var(--verde); }}
.ubicar-tit {{ font-size: 1.9rem; font-weight: 900; color: #1B4D20; line-height: 1.15; }}
.ubicar-txt {{ margin: .3rem 0 0; color: #3E4E40; }}
.st-key-btn_gps button, .st-key-asis_gps button {{ min-height: 60px; font-size: 1.2rem !important; }}
.ubicar-o {{ display: flex; align-items: center; gap: .8rem; color: #5B6B5E; font-weight: 800; margin: .2rem 0 0; }}
.ubicar-o::before, .ubicar-o::after {{ content: ""; flex: 1; height: 2px; background: #E3E9E0; }}
/* el componente que pide la ubicacion no ocupa lugar (fuera del flujo, pero sigue cargado) */
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-gpscomp_"]), [class*="st-key-gpscomp_"] {{
  position: absolute !important; width: 1px !important; height: 1px !important; overflow: hidden; opacity: 0; pointer-events: none; }}
[class*="st-key-zona_grande_"] {{ border-radius: var(--radio); padding: 1.1rem 1.3rem; box-shadow: var(--sombra);
  background: var(--azul-fondo); border-left: 10px solid var(--azul); margin-bottom: .4rem; }}
.st-key-zona_grande_ladera {{ background: #EEF5E6; border-left-color: #7FA650; }}
.st-key-zona_grande_loma {{ background: #F6EEDF; border-left-color: #B9863A; }}
.zg {{ display: flex; align-items: center; gap: 1rem; }}
.zg-ico {{ font-size: 3rem; line-height: 1; }}
.zg-tit {{ font-size: 1.85rem; font-weight: 900; color: #1B4D20; line-height: 1.15; }}
.zg-sub {{ font-size: 1rem; color: #3E4E40; margin-top: .2rem; }}
.semaforo.gris {{ border-left-color: #B0BEC5; }}

/* ---------- Jugar: mesa de casino ---------- */
.st-key-mesa, .st-key-mesa_res {{
  background: radial-gradient(ellipse at 50% 30%, #1F7A4D 0%, #11573A 55%, #0B3F2A 100%);
  border: 6px solid #6B4A1E; outline: 2px solid #D4AF37; outline-offset: -10px; border-radius: 28px;
  padding: 1.6rem 1.4rem 1.4rem; box-shadow: 0 10px 26px rgba(0, 0, 0, .25), inset 0 0 40px rgba(0, 0, 0, .35); }}
.mesa-sub {{ color: #F3EBD2; font-size: 1.1rem; text-align: center; margin-bottom: .4rem; }}
.mesa-tit {{ color: #FFD54F; font-weight: 900; font-size: 1.6rem; text-align: center; letter-spacing: .02em; }}
.st-key-mesa label p, .st-key-mesa [data-testid="stCaptionContainer"] p, .st-key-mesa_res [data-testid="stCaptionContainer"] p {{ color: #F3EBD2 !important; }}
.st-key-mesa_res .frase-res {{ color: #FFFFFF; }}
.st-key-mesa_res .planta-txt {{ color: #F3EBD2; }}
.st-key-mesa_res .mini {{ background: #FFFDF5; }}
.mesa-mes {{ color: #F3EBD2; font-size: 1.1rem; }}
.mesa-mes b {{ color: #FFD54F; }}
.st-key-mesa button[kind="secondary"], .st-key-mesa_res button[kind="secondary"] {{
  background: #FFF8E1; color: #4A3700; border: 2px solid #D4AF37; }}
.st-key-mesa button[kind="primary"] {{ background: #D4AF37; border-color: #FFE082; color: #2A1F00; }}
.st-key-mesa button[kind="primary"] p {{ color: #2A1F00 !important; }}
.st-key-btn_jugar button {{ min-height: 66px !important; font-size: 1.35rem !important; border: none !important;
  background: linear-gradient(180deg, #F7DC6F 0%, #D4AF37 100%) !important; color: #2A1F00 !important;
  box-shadow: 0 6px 0 #8C6D1F, 0 10px 18px rgba(0, 0, 0, .35); }}
.st-key-btn_jugar button p {{ font-size: 1.35rem !important; font-weight: 900 !important; color: #2A1F00 !important; }}
.st-key-btn_jugar button:disabled {{ opacity: .55; box-shadow: none; }}
.st-key-mesa_res [data-testid="stPageLink-NavLink"] {{ background: #FFF8E1; border: 2px solid #D4AF37; justify-content: center; }}
.honesto {{ background: rgba(255, 253, 245, .97); border-left: 6px solid #D4AF37; border-radius: 12px; padding: .65rem .9rem;
  color: #2A2A1F; font-size: 1.02rem; line-height: 1.4; margin: .2rem 0 .3rem; }}
.st-key-fila_naipes [data-testid="stHorizontalBlock"] {{ gap: 14px !important; }}
.naipe {{ perspective: 900px; width: 100%; max-width: 210px; margin: 0 auto; aspect-ratio: 5 / 7; }}
.naipe-in {{ position: relative; width: 100%; height: 100%; transform-style: preserve-3d; }}
.naipe .cara {{ position: absolute; inset: 0; border-radius: 14px; backface-visibility: hidden; -webkit-backface-visibility: hidden; }}
.naipe .frente {{ background: #FFFDF5; border: 3px solid #D4AF37;
  box-shadow: inset 0 0 0 5px #FFFDF5, inset 0 0 0 6px #E6CB72, 0 6px 16px rgba(0, 0, 0, .35);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: .25rem; padding: 14% 9%; text-align: center; }}
.naipe .reverso {{ transform: rotateY(180deg); border: 3px solid #D4AF37; display: flex; align-items: center; justify-content: center;
  background: repeating-linear-gradient(45deg, #7E1F24 0 7px, #962A30 7px 14px); box-shadow: 0 6px 16px rgba(0, 0, 0, .35); }}
.rev-marco {{ width: 78%; height: 84%; border: 2px solid #D4AF37; border-radius: 10px; display: flex; align-items: center;
  justify-content: center; background: radial-gradient(circle, rgba(0,0,0,.25), transparent 70%); }}
.rev-marco span {{ color: #F4D774; font-weight: 900; letter-spacing: .08em; transform: rotate(-35deg); font-size: 1rem; }}
.esq {{ position: absolute; font-family: Georgia, 'Times New Roman', serif; font-weight: 900; font-size: 1.7rem; line-height: 1; color: #8E1B1F; }}
.esq.sup {{ top: 9px; left: 11px; }}
.esq.inf {{ bottom: 9px; right: 11px; transform: rotate(180deg); }}
.naipe-dib {{ display: flex; justify-content: center; align-items: flex-end; gap: 2px; width: 100%; }}
.naipe-dib svg {{ height: 4.6rem; width: auto; flex: 0 1 auto; min-width: 0; }}
.naipe-dib svg:only-child {{ height: 6.4rem; }}
.naipe-nom {{ font-weight: 900; font-size: 1.15rem; color: #1B4D20; line-height: 1.15; margin-top: .35rem; }}
.naipe-seq {{ font-size: .8rem; color: #5B6B5E; line-height: 1.25; }}
.naipe.elegida .naipe-in {{ animation: voltear .7s ease-out both; }}
.naipe.elegida .frente {{ border-color: #FFD54F; box-shadow: inset 0 0 0 5px #FFFDF5, inset 0 0 0 6px #E6CB72,
  0 0 0 4px rgba(255, 213, 79, .6), 0 12px 24px rgba(0, 0, 0, .45); }}
.naipe.apagada {{ opacity: .62; filter: saturate(.55); }}
@keyframes voltear {{ 0% {{ transform: rotateY(180deg) scale(.96); }} 100% {{ transform: rotateY(0) scale(1); }} }}
.marcador {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; background: #0B1A12; border: 3px solid #D4AF37;
  border-radius: 16px; padding: 10px; box-shadow: inset 0 0 18px rgba(0, 0, 0, .7); margin: .4rem 0 .8rem; }}
.marc-celda {{ background: #13261B; border-radius: 10px; text-align: center; padding: .55rem .3rem .5rem; }}
.marc-etq {{ color: #E8D9A8; font-size: .82rem; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; }}
.marc-num {{ font-variant-numeric: tabular-nums; color: #FFD54F; font-size: 2.6rem; font-weight: 900; line-height: 1.1;
  text-shadow: 0 0 10px rgba(255, 213, 79, .5); }}
.marc-num small {{ font-size: 1rem; color: #C9B26A; text-shadow: none; }}
.marc-pal {{ display: inline-block; font-size: .82rem; font-weight: 800; border-radius: 999px; padding: 0 .55rem; }}
.marc-pal.Bien {{ background: #2E7D32; color: #fff; }}
.marc-pal.Regular {{ background: #F9A825; color: #2A1F00; }}
.marc-pal.Bajo {{ background: #C62828; color: #fff; }}

/* ---------- Mis opciones ---------- */
.opc-tit {{ font-size: 2.7rem; font-weight: 900; color: #1B4D20; letter-spacing: .05em; line-height: 1.1; margin: .3rem 0 1rem; }}
.opc-lista {{ display: flex; flex-direction: column; gap: .8rem; }}
.opc {{ position: relative; display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: center;
  gap: .3rem 1rem; background: #fff; border-radius: 18px; box-shadow: var(--sombra); padding: .95rem 1.2rem; border: 3px solid transparent; }}
.opc.tuya {{ border-color: var(--verde); background: var(--verde-fondo); }}
.opc-si {{ font-size: 1.2rem; }}
.opc-si b {{ font-weight: 900; color: #1B4D20; letter-spacing: .02em; }}
.opc-flecha {{ font-size: 1.9rem; font-weight: 900; color: var(--amarillo); line-height: 1; }}
.opc-plan {{ font-size: 1.22rem; font-weight: 700; color: #1F2A1F; }}
.opc-plan b {{ background: #1B4D20; color: #fff; border-radius: 8px; padding: 0 .45rem; }}
.opc-plan small {{ display: block; font-size: .88rem; font-weight: 600; color: #5B6B5E; margin-top: .1rem; }}
.opc-tuya {{ position: absolute; top: -.75rem; right: 1rem; background: var(--verde); color: #fff; font-size: .8rem; font-weight: 900;
  border-radius: 999px; padding: .05rem .65rem; }}
.opc-pie {{ font-size: .98rem !important; color: #4A5A4D; margin: .7rem 0 .4rem; }}

/* ---------- Mi plan ---------- */
.plan-elegido {{ margin: .2rem 0 0; }}

/* ---------- Pantalla ancha: 2 columnas ---------- */
@media (max-width: 899px) and (min-width: 641px) {{
  .picto-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}
@media (min-width: 900px) {{
  .plan-lista {{ grid-template-columns: 1fr 1fr; }}
}}

/* ---------- Celular ---------- */
@media (max-width: 640px) {{
  [data-testid="stMainBlockContainer"], .block-container {{ padding-left: 1rem; padding-right: 1rem; padding-top: 2.8rem; }}
  h1 {{ font-size: 1.55rem !important; }}
  .marca b {{ font-size: 1.3rem; }}
  .marca span {{ font-size: .9rem; }}
  .resumen {{ font-size: 1.15rem; }}
  /* menu: 6 botones en una fila, icono arriba y nombre abajo */
  .st-key-nav {{ padding: .3rem .1rem; gap: 0 !important; }}
  .st-key-nav [data-testid="stPageLink-NavLink"] {{ flex-direction: column; gap: 0; padding: .3rem 0; }}
  .st-key-nav [data-testid="stPageLink-NavLink"] p, .st-key-nav [data-testid="stPageLink-NavLink"] span {{
    font-size: .64rem !important; letter-spacing: -.02em; white-space: normal !important; line-height: 1.05; text-align: center; }}
  .st-key-nav [data-testid="stPageLink-NavLink"] span {{ overflow: visible; }}
  .st-key-nav [data-testid="stPageLink-NavLink"] {{ min-height: 52px; }}
  /* temporadas: 1 por fila (Streamlit apila las columnas); cartas: 2 por fila */
  .st-key-fila_temporadas [data-testid="stHorizontalBlock"] {{ flex-direction: column !important; }}
  .st-key-fila_temporadas [data-testid="stColumn"] {{ width: 100% !important; min-width: 100% !important; flex: 1 1 auto !important; }}
  .st-key-fila_cartas [data-testid="stHorizontalBlock"] {{ flex-direction: row !important; flex-wrap: wrap !important; }}
  .st-key-fila_cartas [data-testid="stColumn"] {{ min-width: calc(50% - 8px) !important; width: calc(50% - 8px) !important;
                                                 max-width: calc(50% - 8px) !important; flex: 1 1 calc(50% - 8px) !important; }}
  .carta-ico {{ font-size: 2rem; }}
  /* dashboard: todo en una columna */
  .hero {{ padding: 1.2rem 1.1rem 1rem; border-radius: 20px; }}
  .hero-tit {{ font-size: 1.85rem; }}
  .hero-frase {{ font-size: 1.08rem; }}
  .picto-grid, .ideas {{ grid-template-columns: 1fr; gap: .8rem; }}
  .picto-num {{ font-size: 2rem; }}
  .anio12 {{ grid-template-columns: repeat(6, minmax(0, 1fr)); }}
  .anio12 .m span {{ font-size: 1.45rem; }}
  .st-key-dash_anio, [class*="st-key-graf_"] {{ padding: .85rem .75rem .7rem; }}
  .bloque-tit {{ font-size: 1.35rem; margin-top: 1.5rem; }}
  .sec-tit {{ font-size: 1.12rem; }}
  .conclusion {{ font-size: .98rem; }}
  /* portada */
  .portada-cab h1.portada-tit {{ font-size: 2.6rem !important; letter-spacing: .1em; padding-left: .1em !important; }}
  .portada-sub {{ font-size: 1.08rem !important; }}
  [class*="st-key-portada_"]:not(.st-key-portada_grid) {{ min-height: 104px; padding: 1rem 1rem; border-radius: 20px; }}
  .ptj-ico {{ width: 56px; height: 56px; border-radius: 16px; }}
  .ptj-ico svg {{ width: 30px; height: 30px; }}
  .ptj-nom {{ font-size: 1.28rem; }}
  .ptj-lin {{ font-size: .95rem; }}
  /* ubicar */
  .ubicar-tit {{ font-size: 1.5rem; }}
  .zg-tit {{ font-size: 1.4rem; }}
  .zg-ico {{ font-size: 2.4rem; }}
  /* casino: las 3 cartas siguen en una fila */
  .st-key-mesa, .st-key-mesa_res {{ padding: 1.1rem .7rem 1rem; border-width: 4px; outline-offset: -8px; border-radius: 22px; }}
  .st-key-fila_naipes [data-testid="stHorizontalBlock"] {{ flex-direction: row !important; flex-wrap: nowrap !important; gap: 8px !important; }}
  .st-key-fila_naipes [data-testid="stColumn"] {{ min-width: 0 !important; width: calc(33.3% - 6px) !important; flex: 1 1 0 !important; }}
  .st-key-fila_naipes .stButton button {{ min-height: 44px; padding: 0 .3rem; }}
  .naipe .frente {{ padding: 18% 6% 14%; }}
  .esq {{ font-size: 1.15rem; }}
  .esq.sup {{ top: 6px; left: 7px; }}
  .esq.inf {{ bottom: 6px; right: 7px; }}
  .naipe-dib svg {{ height: 2.2rem; }}
  .naipe-dib svg:only-child {{ height: 3rem; }}
  .naipe-nom {{ font-size: .82rem; }}
  .naipe-seq {{ display: none; }}
  .st-key-mesa_res .planta svg {{ width: 105px; }}
  .rev-marco span {{ font-size: .7rem; }}
  .mesa-tit {{ font-size: 1.3rem; }}
  .marc-num {{ font-size: 1.8rem; }}
  .marc-etq {{ font-size: .68rem; letter-spacing: .02em; }}
  .st-key-btn_jugar button p {{ font-size: 1.2rem !important; }}
  /* mis opciones: una columna */
  .opc-tit {{ font-size: 2rem; }}
  .opc {{ grid-template-columns: 1fr; padding: .85rem 1rem; }}
  .opc-flecha {{ display: none; }}
  .opc-si {{ font-size: 1.08rem; }}
  .opc-plan {{ font-size: 1.12rem; }}
}}
@media (prefers-reduced-motion: reduce) {{
  * {{ transition: none !important; }}
  .naipe.elegida .naipe-in {{ animation: none; }}
}}
</style>
"""


def aplicar():
    st.markdown(CSS, unsafe_allow_html=True)
