
from pathlib import Path

import numpy as np
import rasterio
import matplotlib.pyplot as plt

from rasterio.warp import (
    calculate_default_transform,
    reproject,
    Resampling
)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

input_path = RAW_DIR / "elevacion_daule.tif"
output_path = OUTPUT_DIR / "elevacion_daule_utm.tif"
slope_path = OUTPUT_DIR / "pendiente_daule.tif"

# 1. Reproyectar elevación a UTM 17S
with rasterio.open(input_path) as src:
    transform, width, height = calculate_default_transform(
        src.crs,
        "EPSG:32717",
        src.width,
        src.height,
        *src.bounds,
        resolution=30
    )

    profile = src.profile.copy()
    profile.update(
        crs="EPSG:32717",
        transform=transform,
        width=width,
        height=height,
        dtype="float32",
        nodata=-9999.0
    )

    with rasterio.open(output_path, "w", **profile) as dst:
        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(dst, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=transform,
            dst_crs="EPSG:32717",
            dst_nodata=-9999.0,
            resampling=Resampling.bilinear
        )

# 2. Leer elevación reproyectada
with rasterio.open(output_path) as src:
    elevation = src.read(1, masked=True)
    transform = src.transform
    profile = src.profile.copy()

    dx = abs(transform.a)
    dy = abs(transform.e)

# 3. Calcular pendientes
z = elevation.filled(np.nan).astype(float)

dz_dy, dz_dx = np.gradient(z, dy, dx)

slope_degrees = np.degrees(
    np.arctan(
        np.sqrt(dz_dx**2 + dz_dy**2)
    )
)

slope_degrees = np.where(
    np.isfinite(slope_degrees),
    slope_degrees,
    -9999.0
).astype("float32")

# 4. Guardar mapa de pendientes
profile.update(
    dtype="float32",
    nodata=-9999.0
)

with rasterio.open(slope_path, "w", **profile) as dst:
    dst.write(slope_degrees, 1)

# 5. Estadísticas
valid_slope = slope_degrees[
    slope_degrees != -9999.0
]

print("\nPENDIENTES DEL TERRENO")
print("Pendiente mínima:", np.min(valid_slope))
print("Pendiente máxima:", np.max(valid_slope))
print("Pendiente promedio:", np.mean(valid_slope))

# 6. Visualización
fig, ax = plt.subplots(figsize=(10, 7))

img = ax.imshow(
    np.ma.masked_equal(slope_degrees, -9999.0),
    cmap="YlOrRd",
    vmin=0,
    vmax=15
)

fig.colorbar(
    img,
    ax=ax,
    label="Pendiente (grados)"
)

ax.set_title("AgroShift - Pendientes de Daule")
plt.tight_layout()
plt.show()

print("\nArchivos generados:")
print(output_path)
print(slope_path)
