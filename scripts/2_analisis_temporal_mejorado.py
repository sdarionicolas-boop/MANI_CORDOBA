# scripts/2_analisis_temporal_mejorado.py
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os, sys
from scipy import stats
from scipy.ndimage import gaussian_filter1d
import warnings
warnings.filterwarnings('ignore')

# === BOOTSTRAP MANI_CORDOBA ===
BASE_DIR = r"C:\Users\sdari\Desktop\Pruebas e Investigaciones\MANI_CORDOBA"
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import config_mani as CFG
from utils_agro import (
    cargar_datacube, calcular_indices_avanzados,
    analizar_tendencias, detectar_cambios_abruptos, calcular_fenologia
)

print("[INFO] 2. Analizando series temporales (MEJORADO) - MANÍ Córdoba")

# Rutas centralizadas
estadisticas_path = CFG.ESTAD_DIR
os.makedirs(estadisticas_path, exist_ok=True)

# Carga optimizada
print("[INFO] Cargando datacube...")
datacube = cargar_datacube()
datacube = calcular_indices_avanzados(datacube)

# Calcular promedios espaciales
print("[INFO] Calculando promedios espaciales...")
indices = ['NDVI', 'NDRE', 'EVI', 'GNDVI', 'OSAVI', 'BIOMASA', 'ESTRES_HIDRICO', 'PRODUCTIVIDAD']
series_temporales = {}

for idx in indices:
    try:
        if idx in datacube.data_vars:
            serie = datacube[idx].mean(dim=['x', 'y'])
            series_temporales[idx] = serie
            print(f"  ✓ {idx}: {len(serie)} puntos temporales")
        else:
            print(f"  ✗ {idx}: No disponible")
    except Exception as e:
        print(f"  ✗ {idx}: Error - {e}")

# Análisis de tendencias
print("[INFO] Analizando tendencias...")
tendencias = {}
for idx, serie in series_temporales.items():
    slope, p_value, r2 = analizar_tendencias(serie.values)
    tendencias[idx] = {
        'pendiente': slope,
        'p_value': p_value,
        'r_cuadrado': r2,
        'tendencia': '↑ Creciente' if (not np.isnan(slope) and slope > 0.001) else
                     '↓ Decreciente' if (not np.isnan(slope) and slope < -0.001) else '↔ Estable',
        'significativo': (p_value < 0.05) if not np.isnan(p_value) else False
    }

# Detección de cambios abruptos
print("[INFO] Detectando cambios abruptos...")
cambios_abruptos = {}
for idx, serie in series_temporales.items():
    cambios = detectar_cambios_abruptos(serie.values, umbral=0.25)
    cambios_abruptos[idx] = {
        'total_cambios': int(np.sum(cambios)),
        'fechas_cambios': serie.time.values[cambios] if np.any(cambios) else [],
        'magnitud_promedio': float(np.mean(np.abs(np.diff(serie.values)[cambios[1:]]))) if np.any(cambios) else 0.0
    }

# Análisis fenológico (solo NDVI)
print("[INFO] Analizando fenología...")
fenologia = {}
if 'NDVI' in series_temporales:
    ndvi_series = series_temporales['NDVI']
    inicio, pico, fin = calcular_fenologia(ndvi_series.values, ndvi_series.time.values)
    fenologia['NDVI'] = {
        'inicio_estacion': inicio,
        'pico_vegetacion': pico,
        'fin_estacion': fin,
        'duracion_estacion': (pd.to_datetime(fin) - pd.to_datetime(inicio)).days
                              if (not np.isnan(inicio) and not np.isnan(fin)) else np.nan
    }

# Guardar CSVs
tendencias_df = pd.DataFrame(tendencias).T
tendencias_df.to_csv(os.path.join(estadisticas_path, "tendencias_indices.csv"))
print(f"[OK] Tendencias guardadas: {os.path.join(estadisticas_path, 'tendencias_indices.csv')}")

cambios_df = pd.DataFrame(cambios_abruptos).T
cambios_df.to_csv(os.path.join(estadisticas_path, "cambios_abruptos.csv"))
print(f"[OK] Cambios abruptos guardados: {os.path.join(estadisticas_path, 'cambios_abruptos.csv')}")

if fenologia:
    fenologia_df = pd.DataFrame(fenologia).T
    fenologia_df.to_csv(os.path.join(estadisticas_path, "fenologia.csv"))
    print(f"[OK] Fenología guardada: {os.path.join(estadisticas_path, 'fenologia.csv')}")

# Gráfico de series temporales
print("[INFO] Generando gráficos...")
plt.figure(figsize=(18, 14))

# Subplot 1: Índices principales
plt.subplot(3, 2, 1)
for idx in ['NDVI', 'NDRE', 'EVI']:
    if idx in series_temporales:
        serie = series_temporales[idx]
        plt.plot(serie.time, serie, marker='o', label=idx, linewidth=2, markersize=4)
plt.axhline(y=0.3, color='r', linestyle='--', alpha=0.5, label='Umbral suelo (0.3)')
plt.axhline(y=0.6, color='g', linestyle='--', alpha=0.5, label='Umbral cultivo (0.6)')
plt.title("Índices de Vegetación Principales", fontsize=14, fontweight='bold')
plt.xlabel("Fecha"); plt.ylabel("Valor del Índice")
plt.legend(); plt.grid(alpha=0.3); plt.xticks(rotation=45)

# Subplot 2: Índices avanzados
plt.subplot(3, 2, 2)
for idx in ['GNDVI', 'OSAVI']:
    if idx in series_temporales:
        serie = series_temporales[idx]
        plt.plot(serie.time, serie, marker='s', label=idx, linewidth=2, markersize=4)
plt.title("Índices de Vegetación Avanzados", fontsize=14, fontweight='bold')
plt.xlabel("Fecha"); plt.ylabel("Valor del Índice")
plt.legend(); plt.grid(alpha=0.3); plt.xticks(rotation=45)

# Subplot 3: Biomasa y Productividad
plt.subplot(3, 2, 3)
if 'BIOMASA' in series_temporales:
    plt.plot(series_temporales['BIOMASA'].time, series_temporales['BIOMASA'],
             marker='^', label='Biomasa (kg/ha)', linewidth=2)
    plt.ylabel("Biomasa Estimada (kg/ha)")
    plt.legend(loc='upper left')
ax2 = plt.gca().twinx()
if 'PRODUCTIVIDAD' in series_temporales:
    ax2.plot(series_temporales['PRODUCTIVIDAD'].time, series_temporales['PRODUCTIVIDAD'],
             marker='v', label='Productividad', linewidth=2, alpha=0.7)
    ax2.set_ylabel("Productividad")
    ax2.legend(loc='upper right')
plt.title("Biomasa y Productividad", fontsize=14, fontweight='bold')
plt.xlabel("Fecha"); plt.grid(alpha=0.3); plt.xticks(rotation=45)

# Subplot 4: Estrés hídrico
plt.subplot(3, 2, 4)
if 'ESTRES_HIDRICO' in series_temporales:
    plt.plot(series_temporales['ESTRES_HIDRICO'].time, series_temporales['ESTRES_HIDRICO'],
             marker='D', label='Estrés hídrico', linewidth=2)
    plt.axhline(y=1.0, color='orange', linestyle='--', alpha=0.7, label='Umbral estrés (1.0)')
    plt.title("Estrés Hídrico", fontsize=14, fontweight='bold')
    plt.xlabel("Fecha"); plt.ylabel("Índice de Estrés")
    plt.legend(); plt.grid(alpha=0.3); plt.xticks(rotation=45)

# Subplot 5: Resumen de tendencias
plt.subplot(3, 2, 5)
indices_tendencia = [idx for idx in ['NDVI','NDRE','EVI','GNDVI','OSAVI'] if idx in tendencias]
pendientes = [tendencias[idx]['pendiente'] * 1000 for idx in indices_tendencia]
colors = ['green' if p > 0 else 'red' for p in pendientes]
bars = plt.bar(indices_tendencia, pendientes, alpha=0.7, color=colors)
plt.axhline(y=0, color='black', linestyle='-', alpha=0.8)
for i, (bar, p_val) in enumerate(zip(bars, [tendencias[idx]['p_value'] for idx in indices_tendencia])):
    height = bar.get_height()
    signo = '*' if (not np.isnan(p_val) and p_val < 0.05) else ''
    plt.text(bar.get_x() + bar.get_width()/2., height/2, f'{height:.2f}{signo}',
             ha='center', va='center', fontweight='bold')
plt.title("Tendencia Anual (x1000) *p<0.05", fontsize=14, fontweight='bold')
plt.ylabel("Cambio anual"); plt.grid(alpha=0.3, axis='y')

# Subplot 6: Fenología
plt.subplot(3, 2, 6)
if 'NDVI' in series_temporales and not np.isnan(fenologia.get('NDVI', {}).get('inicio_estacion', np.nan)):
    ndvi_series = series_temporales['NDVI']
    plt.plot(ndvi_series.time, ndvi_series, marker='o', linewidth=2, label='NDVI')
    inicio = fenologia['NDVI']['inicio_estacion']
    pico   = fenologia['NDVI']['pico_vegetacion']
    fin    = fenologia['NDVI']['fin_estacion']
    if not np.isnan(inicio): plt.axvline(x=inicio, color='blue', linestyle='--', alpha=0.7, label='Inicio estación')
    if not np.isnan(pico):   plt.axvline(x=pico,   color='red',  linestyle='--', alpha=0.7, label='Pico vegetación')
    if not np.isnan(fin):    plt.axvline(x=fin,    color='orange',linestyle='--', alpha=0.7, label='Fin estación')
    plt.title("Fenología del Cultivo", fontsize=14, fontweight='bold')
    plt.xlabel("Fecha"); plt.ylabel("NDVI")
    plt.legend(); plt.grid(alpha=0.3); plt.xticks(rotation=45)
else:
    plt.text(0.5, 0.5, 'Datos insuficientes\npara análisis fenológico',
             ha='center', va='center', transform=plt.gca().transAxes, fontsize=12)
    plt.title("Fenología del Cultivo", fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(estadisticas_path, "serie_temporal_mejorada.png"), dpi=300, bbox_inches='tight')
plt.savefig(os.path.join(estadisticas_path, "serie_temporal_mejorada.pdf"), bbox_inches='tight')
plt.show()

# Reporte final
print("\n" + "="*60)
print("REPORTE DE ANÁLISIS TEMPORAL")
print("="*60)

print("\n📈 TENDENCIAS SIGNIFICATIVAS:")
for idx, stats_ in tendencias.items():
    if stats_['significativo']:
        print(f"  {idx}: {stats_['tendencia']} (p={stats_['p_value']:.3f}, R²={stats_['r_cuadrado']:.2f})")

print("\n⚠️  CAMBIOS ABRUPTOS DETECTADOS:")
for idx, cambios in cambios_abruptos.items():
    if cambios['total_cambios'] > 0:
        print(f"  {idx}: {cambios['total_cambios']} cambios (magnitud avg: {cambios['magnitud_promedio']:.3f})")

if fenologia and 'NDVI' in fenologia:
    fen = fenologia['NDVI']
    if not np.isnan(fen['inicio_estacion']):
        print("\n🌾 FENOLOGÍA DEL CULTIVO:")
        print(f"  Inicio estación: {pd.to_datetime(fen['inicio_estacion']).strftime('%Y-%m-%d')}")
        print(f"  Pico vegetación: {pd.to_datetime(fen['pico_vegetacion']).strftime('%Y-%m-%d')}")
        print(f"  Fin estación: {pd.to_datetime(fen['fin_estacion']).strftime('%Y-%m-%d')}")
        print(f"  Duración: {fen['duracion_estacion']} días")

print("\n[OK] Análisis temporal mejorado completado")
