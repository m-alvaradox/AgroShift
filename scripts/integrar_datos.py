
from pathlib import Path
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

ruta_clima = (
    BASE_DIR / "data" / "processed"
    / "clima_mensual_daule.csv"
)

ruta_indices = (
    BASE_DIR / "data" / "processed"
    / "indices_mensuales_daule_integrados.csv"
)

ruta_salida = (
    BASE_DIR / "data" / "processed"
    / "datos_integrados_daule.csv"
)

# ==========================================
# 2. CARGAR ARCHIVOS
# ==========================================

clima = pd.read_csv(ruta_clima)
indices = pd.read_csv(ruta_indices)

print("NASA POWER:", clima.shape)
print("LANDSAT:", indices.shape)

# ==========================================
# 3. NORMALIZAR FECHAS
# ==========================================

clima["mes"] = (
    pd.to_datetime(clima["mes"])
    .dt.strftime("%Y-%m")
)

indices["mes"] = (
    pd.to_datetime(indices["mes"])
    .dt.strftime("%Y-%m")
)

# ==========================================
# 4. VALIDAR LOS REGISTROS
# ==========================================

assert not clima["mes"].duplicated().any(), (
    "NASA POWER contiene meses duplicados"
)

assert not indices["mes"].duplicated().any(), (
    "Landsat contiene meses duplicados"
)

# ==========================================
# 5. INTEGRAR INFORMACIÓN
# ==========================================

datos = pd.merge(
    clima,
    indices,
    on="mes",
    how="inner",
    validate="one_to_one"
)

datos = (
    datos.sort_values("mes")
    .reset_index(drop=True)
)

assert len(datos) == 60, (
    f"Se esperaban 60 meses, "
    f"pero se encontraron {len(datos)}"
)

# ==========================================
# 6. IDENTIFICAR MESES UTILIZABLES
# ==========================================

# Umbral exploratorio: al menos 50 %
# de cobertura espacial válida.

datos["indices_utilizables"] = (
    datos["cobertura_pct"].ge(50)
    & datos[["NDVI", "NDWI", "NDMI"]]
      .notna().all(axis=1)
)

# ==========================================
# 7. VERIFICAR DATOS FALTANTES
# ==========================================

print("\n=== DATOS INTEGRADOS ===")

print("Dimensiones:", datos.shape)

print("\nColumnas:")
print(datos.columns.tolist())

print("\nPrimeros registros:")
print(datos.head(5).to_string(index=False))

print("\nValores faltantes:")
print(datos.isna().sum())

print("\nMeses con índices utilizables:")
print(datos["indices_utilizables"].sum())

print("\nMeses con cobertura insuficiente:")
print((~datos["indices_utilizables"]).sum())

# ==========================================
# 8. GUARDAR RESULTADOS
# ==========================================

ruta_salida.parent.mkdir(
    parents=True,
    exist_ok=True
)

datos.to_csv(
    ruta_salida,
    index=False
)

print("\nArchivo generado:")
print(ruta_salida)
