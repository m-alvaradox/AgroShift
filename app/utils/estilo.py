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
html, body, .stApp, [class*="st-"]:not([data-testid="stIconMaterial"]), button, input, textarea {{
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
.st-key-nav [data-testid="stPageLink-NavLink"] {{ justify-content: center; border-radius: 14px; padding: .35rem .5rem; }}
.st-key-nav [data-testid="stPageLink-NavLink"] p {{ font-size: 1.02rem; font-weight: 700; color: #3E4E40; }}
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

/* ---------- Pantalla ancha: 2 columnas ---------- */
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
  /* menu: 5 botones en una fila, icono arriba y nombre abajo */
  .st-key-nav [data-testid="stPageLink-NavLink"] {{ flex-direction: column; gap: 0; padding: .3rem .1rem; }}
  .st-key-nav [data-testid="stPageLink-NavLink"] p {{ font-size: .78rem !important; }}
  /* temporadas: 1 por fila (Streamlit apila las columnas); cartas: 2 por fila */
  .st-key-fila_temporadas [data-testid="stHorizontalBlock"] {{ flex-direction: column !important; }}
  .st-key-fila_temporadas [data-testid="stColumn"] {{ width: 100% !important; min-width: 100% !important; flex: 1 1 auto !important; }}
  .st-key-fila_cartas [data-testid="stHorizontalBlock"] {{ flex-direction: row !important; flex-wrap: wrap !important; }}
  .st-key-fila_cartas [data-testid="stColumn"] {{ min-width: calc(50% - 8px) !important; width: calc(50% - 8px) !important;
                                                 max-width: calc(50% - 8px) !important; flex: 1 1 calc(50% - 8px) !important; }}
  .carta-ico {{ font-size: 2rem; }}
}}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>
"""


def aplicar():
    st.markdown(CSS, unsafe_allow_html=True)
