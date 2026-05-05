# scripts/5_timelapse.py
import os, rasterio, numpy as np, matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import imageio.v2 as imageio
from config_mani import RUTAS, LABELS_DICT

print("[INFO] 5. Generando timelapse - MANÍ Córdoba")

mapas_path = RUTAS["mapas"]
timelapse_path = RUTAS["timelapse"]
os.makedirs(timelapse_path, exist_ok=True)

cols = ["#d2b48c","#f4d03f","#2ecc71","#1a5276"]
labels = [LABELS_DICT[i] for i in range(4)]
custom_cmap = ListedColormap(cols)

archivos = sorted([f for f in os.listdir(mapas_path) if f.startswith("clasificacion_")])
archivos = [os.path.join(mapas_path, f) for f in archivos]

fechas = []
for f in archivos:
    fecha_str = os.path.basename(f).split("_")[1].replace(".tif","")
    fecha = f"{fecha_str[6:8]}/{fecha_str[4:6]}/{fecha_str[0:4]}"
    fechas.append(fecha)

frames = []
for i, archivo in enumerate(archivos):
    with rasterio.open(archivo) as src:
        mapa = src.read(1)
        mapa = np.where(mapa==255, np.nan, mapa)
        bounds = src.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
    fig, ax = plt.subplots(figsize=(14,10), facecolor='#f0f0f0')
    im = ax.imshow(mapa, cmap=custom_cmap, vmin=0, vmax=3, extent=extent, alpha=0.95)
    title = ax.set_title(f"Evolución de Cobertura - EEA Gral. Cabrera (Córdoba)\n{fechas[i]}", fontsize=18, fontweight='bold', pad=20)
    cbar = plt.colorbar(im, ticks=[0.375,1.125,1.875,2.625], shrink=0.7)
    cbar.ax.set_yticklabels(labels)
    cbar.set_label('Clasificación', rotation=270, labelpad=25)
    ax.grid(True, linestyle='--', alpha=0.2, color='gray')
    ax.text(0.02,0.98,"EEA Gral. Cabrera, Córdoba", transform=ax.transAxes, fontsize=11, fontweight='bold', va='top',
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor='gray'))
    total = np.sum(~np.isnan(mapa))
    if total>0:
        stats_text = "Distribución:\n"
        for cid in range(4):
            p = np.sum(mapa==cid)/total*100
            stats_text += f"{labels[cid][:18]}: {p:.1f}%\n"
        ax.text(0.02, 0.15, stats_text, transform=ax.transAxes, fontsize=10, va='top',
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))
    plt.tight_layout()
    frame_path = os.path.join(timelapse_path, f"frame_{i:03d}.png")
    plt.savefig(frame_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    frames.append(imageio.imread(frame_path))

mp4_path = os.path.join(timelapse_path, "timelapse_mani.mp4")
gif_path = os.path.join(timelapse_path, "timelapse_mani.gif")
if frames:
    imageio.mimwrite(mp4_path, frames, fps=2, format='FFMPEG', codec='libx264', quality=8, pixelformat='yuv420p')
    imageio.mimwrite(gif_path, frames, format='GIF', duration=500, loop=0)
    print(f"[OK] MP4: {mp4_path}")
    print(f"[OK] GIF: {gif_path}")
else:
    print("[WARN] No hay frames (¿faltan GeoTIFF en resultados/mapas?)")
