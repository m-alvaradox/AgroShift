"""Piezas visuales que se repiten en varias paginas."""
import streamlit as st

from utils import carga

COLOR_ZONA = {1: "#C8963E", 2: "#7FA650", 3: "#3B82C4"}   # loma, transicion, baja
COLOR_TIPO = {"lluvioso": "#3B82C4", "transicion": "#9CC3E6", "seco": "#E0B05C"}
COLOR_ESC = {"normal": "#7A869A", "nino": "#3B82C4", "nina": "#E0B05C"}
NOMBRE_ESC = {"normal": "Año normal", "nino": "Año El Niño", "nina": "Año La Niña"}
NOMBRE_TIPO = {"lluvioso": "Lluvioso", "transicion": "Transición", "seco": "Seco"}

GLOSARIO = {
    "NDVI": "Qué tan verde y sano está el cultivo. Cerca de 0: suelo desnudo. Cerca de 0,8: cultivo muy verde.",
    "NDWI": "Si hay agua en la superficie. Mayor que 0: terreno con agua o inundado.",
    "NDMI": "Humedad dentro de las plantas. Bajo: la planta puede estar pasando sed.",
    "ET0": "El agua que se evapora del suelo y las plantas en un mes. Si llueve menos que esto, falta agua.",
}


def aviso_datos():
    mock = carga.archivos_mock()
    if mock:
        st.warning(
            f"Datos de prueba: {len(mock)} de {len(carga.CONTRATOS)} archivos todavía son "
            "simulados. Los resultados sirven para ver cómo funciona la app, no para decidir.",
            icon="🧪",
        )
        with st.expander("Ver qué datos son reales y cuáles de prueba"):
            st.dataframe(carga.estado_datos(), hide_index=True, width="stretch")
            st.caption("Si un archivo real aparece como rechazado, le faltan columnas del "
                       "contrato. Mientras tanto, la app usa el de prueba.")


def aviso_tecnico():
    st.caption(
        "Agroshift apoya la decisión, pero no reemplaza el criterio del agricultor "
        "ni de un técnico agrícola local. Confirma la recomendación antes de sembrar."
    )


def fuente(texto: str):
    st.caption(f"Fuente: {texto}")


def zona_actual() -> tuple[int, str]:
    zid = st.session_state.get("zona_id", 3)
    tabla = carga.tabla_zonas().set_index("zona_id")
    return zid, tabla.loc[zid, "nombre_comun"]


def escenario_actual() -> str:
    return st.session_state.get("escenario", "normal")


def pesos_actuales() -> dict:
    return {
        "nota_agua": st.session_state.get("p_agua", 3),
        "nota_suelo": st.session_state.get("p_suelo", 3),
        "nota_plagas": st.session_state.get("p_plagas", 3),
        "nota_ingresos": st.session_state.get("p_ingresos", 3),
    }


def num(valor: float, decimales: int = 0) -> str:
    """Numero con formato de Ecuador: punto para miles y coma para decimales."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
