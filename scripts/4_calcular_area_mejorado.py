# === BOOTSTRAP MANI_CORDOBA (AUTO) ===
import sys, os
BASE_DIR = r"C:\Users\sdari\Desktop\Pruebas e Investigaciones\MANI_CORDOBA"
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
import config_mani as CFG
from utils_agro import (
    cargar_datacube, calcular_indices_avanzados,
    analizar_tendencias, detectar_cambios_abruptos,
    calcular_fenologia, exportar_geotiff
)
# === FIN BOOTSTRAP ===

# scripts/4_calcular_area_mejorado.py
import os, rasterio, pandas as pd, numpy as np, matplotlib.pyplot as plt
from config_mani import RUTAS, LABELS_DICT, PIXEL_AREA_HA

print("[INFO] 4. Calculando áreas por clase (MEJORADO) - MANÍ Córdoba")

mapas_path = RUTAS["mapas"]
resultados_path = RUTAS["estadisticas"]
os.makedirs(resultados_path, exist_ok=True)

resultados_csv = os.path.join(resultados_path, "area_por_clase.csv")
estadisticas_csv = os.path.join(resultados_path, "estadisticas_clases.csv")

resultados = []
estadisticas_por_clase = {c: {'areas': [], 'fechas': []} for c in LABELS_DICT}

print("[INFO] Procesando archivos de clasificación...")
archivos_procesados = 0
for archivo in sorted(os.listdir(mapas_path)):
    if archivo.startswith("clasificacion_") and archivo.endswith(".tif"):
        fecha_str = archivo.split("_")[1].replace(".tif","")
        fecha = f"{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:8]}"
        ruta = os.path.join(mapas_path, archivo)
        try:
            with rasterio.open(ruta) as src:
                mapa = src.read(1)
                nodata = src.nodata
            mapa_valido = np.where((mapa>=0)&(mapa<=3), mapa, np.nan)
            total_pix = np.sum(~np.isnan(mapa_valido))
            if total_pix == 0: continue
            for clase in LABELS_DICT:
                pix = np.sum(mapa_valido == clase)
                area_ha = pix * PIXEL_AREA_HA
                porc = (pix / total_pix * 100)
                resultados.append({
                    'Fecha': fecha, 'Clase': LABELS_DICT[clase], 'Clase_ID': clase,
                    'Area_ha': round(area_ha,2), 'Area_pixeles': int(pix), 'Porcentaje': round(porc,2)
                })
                estadisticas_por_clase[clase]['areas'].append(area_ha)
                estadisticas_por_clase[clase]['fechas'].append(fecha)
            archivos_procesados += 1
        except Exception as e:
            print(f"[ERROR] {ruta}: {e}")

df_res = pd.DataFrame(resultados)
df_res.to_csv(resultados_csv, index=False)
print(f"[OK] Resultados: {resultados_csv}")

stats = []
for clase, data in estadisticas_por_clase.items():
    if data['areas']:
        a = np.array(data['areas'])
        stats.append({
            'Clase': LABELS_DICT[clase], 'Clase_ID': clase,
            'Area_min_ha': round(np.min(a),2),
            'Area_max_ha': round(np.max(a),2),
            'Area_promedio_ha': round(np.mean(a),2),
            'Area_mediana_ha': round(np.median(a),2),
            'Desviacion_std_ha': round(np.std(a),2),
            'Coeficiente_variacion': round(np.std(a)/np.mean(a)*100,2) if np.mean(a)>0 else 0,
            'Numero_fechas': int(len(a))
        })
df_stats = pd.DataFrame(stats)
df_stats.to_csv(estadisticas_csv, index=False)
print(f"[OK] Estadísticas: {estadisticas_csv}")

# Gráficos
if not df_res.empty:
    df_res['Fecha'] = pd.to_datetime(df_res['Fecha'])
    df_res = df_res.sort_values('Fecha').reset_index(drop=True)
    fig, axes = plt.subplots(2,2, figsize=(24,16), constrained_layout=True)
    fig.suptitle("MANÍ (Córdoba) - Análisis Temporal de Clasificación", fontsize=18, fontweight='bold')
    # 1 área apilada
    df_p = df_res.pivot(index='Fecha', columns='Clase', values='Area_ha').fillna(0)
    df_p.plot(kind='area', stacked=True, alpha=0.85, ax=axes[0,0])
    axes[0,0].set_title("Evolución del Área por Clase"); axes[0,0].set_xlabel("Fecha"); axes[0,0].set_ylabel("Área (ha)"); axes[0,0].grid(alpha=0.3)
    # 2 porcentajes
    df_pct = df_res.pivot(index='Fecha', columns='Clase', values='Porcentaje').fillna(0)
    df_pct.plot(kind='line', linewidth=2, alpha=0.9, ax=axes[0,1])
    axes[0,1].set_title("Porcentajes por Clase"); axes[0,1].set_xlabel("Fecha"); axes[0,1].set_ylabel("%"); axes[0,1].grid(alpha=0.3); axes[0,1].set_ylim(0,100)
    # 3 individual
    for clase in df_res['Clase'].unique():
        df_c = df_res[df_res['Clase']==clase]
        axes[1,0].plot(df_c['Fecha'], df_c['Area_ha'], marker='o', label=clase, linewidth=2)
    axes[1,0].set_title("Evolución Individual por Clase"); axes[1,0].set_xlabel("Fecha"); axes[1,0].set_ylabel("Área (ha)"); axes[1,0].legend(); axes[1,0].grid(alpha=0.3)
    # 4 promedio
    areas_prom = [s['Area_promedio_ha'] for s in stats]
    clases_names = [s['Clase'] for s in stats]
    bars = axes[1,1].bar(clases_names, areas_prom, alpha=0.85)
    axes[1,1].set_title("Área Promedio por Clase"); axes[1,1].set_ylabel("Área (ha)"); axes[1,1].grid(alpha=0.3, axis='y')
    for bar in bars:
        h = bar.get_height(); axes[1,1].text(bar.get_x()+bar.get_width()/2, h*1.01, f'{h:.1f}', ha='center', va='bottom')
    out_png = os.path.join(resultados_path, "evolucion_area_mejorada.png")
    out_pdf = os.path.join(resultados_path, "evolucion_area_mejorada.pdf")
    plt.savefig(out_png, dpi=200, bbox_inches='tight'); plt.savefig(out_pdf, bbox_inches='tight')
    print(f"[OK] Gráficos: {out_png}")
print(f"\n[OK] Procesamiento completado. {archivos_procesados} archivos.")
