
from pathlib import Path

import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

BASE_DIR = Path(__file__).resolve().parent.parent

ruta = BASE_DIR / "data" / "processed" / "pendiente_daule.tif"

with rasterio.open(ruta) as src:
    pendiente = src.read(1, masked=True)
    perfil = src.profile.copy()

# Clasificar pendientes
clasificacion = np.zeros(pendiente.shape, dtype=np.uint8)

valido = ~np.ma.getmaskarray(pendiente)
p = pendiente.data

clasificacion[valido & (p <= 2)] = 1
clasificacion[valido & (p > 2) & (p <= 5)] = 2
clasificacion[valido & (p > 5) & (p <= 15)] = 3
clasificacion[valido & (p > 15)] = 4

# Calcular porcentajes
print("\nCLASIFICACIÓN DEL RELIEVE DE DAULE")

categorias = {
    1: "Plano",
    2: "Suave",
    3: "Moderado",
    4: "Pronunciado"
}

total = np.count_nonzero(valido)

for codigo, nombre in categorias.items():
    cantidad = np.count_nonzero(clasificacion == codigo)
    porcentaje = cantidad / total * 100
    print(f"{nombre}: {porcentaje:.2f}%")

# Guardar GeoTIFF clasificado
perfil.update(dtype="uint8", nodata=0)

salida = (
    BASE_DIR / "data" / "processed"
    / "clasificacion_terreno_daule.tif"
)

with rasterio.open(salida, "w", **perfil) as dst:
    dst.write(clasificacion, 1)

# Visualización
colores = [
    "#66bb6a",
    "#d4e157",
    "#ffb74d",
    "#e57373"
]

cmap = ListedColormap(colores)
norm = BoundaryNorm([0.5, 1.5, 2.5, 3.5, 4.5], cmap.N)

imagen = np.ma.masked_equal(clasificacion, 0)

fig, ax = plt.subplots(figsize=(10, 7))
im = ax.imshow(imagen, cmap=cmap, norm=norm)

cbar = fig.colorbar(im, ax=ax, ticks=[1, 2, 3, 4])
cbar.ax.set_yticklabels(list(categorias.values()))

ax.set_title("AgroShift - Clasificación del relieve de Daule")
ax.set_xlabel("Columnas")
ax.set_ylabel("Filas")

plt.tight_layout()
plt.show()

print("\nArchivo generado:", salida)
