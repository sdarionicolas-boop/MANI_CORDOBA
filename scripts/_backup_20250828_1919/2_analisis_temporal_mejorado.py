# scripts/2_analisis_temporal_mejorado.py
import matplotlib.pyplot as plt, pandas as pd, numpy as np, os
from config_mani import RUTAS
from utils_agro import cargar_datacube, calcular_indices_avanzados, analizar_tendencias, detectar_cambios_abruptos, calcular_fenologia

print("[INFO] 2. Analizando series temporales (MEJORADO) - MANÍ Córdoba")

resultados_path = RUTAS["estadisticas"]
os.makedirs(resultados_path, exist_ok=True)

print("[INFO] Cargando datacube...")
datacube = cargar_datacube(RUTAS["processed"].replace("\\\\processed",""))
datacube = calcular_indices_avanzados(datacube)

print("[INFO] Calculando promedios espaciales...")
indices = ['NDVI','NDRE','EVI','GNDVI','OSAVI','BIOMASA','ESTRES_HIDRICO','PRODUCTIVIDAD']
series_temporales = {}
for idx in indices:
    if idx in datacube.data_vars:
        serie = datacube[idx].mean(dim=['x','y'])
        series_temporales[idx] = serie
        print(f"  ✓ {idx}: {len(serie)} puntos temporales")

print("[INFO] Analizando tendencias...")
tendencias = {}
for idx, serie in series_temporales.items():
    slope, p_value, r2 = analizar_tendencias(serie.values)
    tendencias[idx] = {
        'pendiente': slope, 'p_value': p_value, 'r_cuadrado': r2,
        'tendencia': '↑ Creciente' if slope > 0.001 else '↓ Decreciente' if slope < -0.001 else '↔ Estable',
        'significativo': p_value < 0.05 if not np.isnan(p_value) else False
    }

print("[INFO] Detectando cambios abruptos...")
cambios_abruptos = {}
for idx, serie in series_temporales.items():
    cambios = detectar_cambios_abruptos(serie.values, umbral=0.25)
    cambios_abruptos[idx] = {
        'total_cambios': int(np.sum(cambios)),
        'fechas_cambios': list(map(str, pd.to_datetime(serie.time.values[cambios])) if np.any(cambios) else []),
        'magnitud_promedio': float(np.nanmean(np.abs(np.diff(serie.values)[1:][cambios[1:]]))) if np.any(cambios) else 0.0
    }

print("[INFO] Analizando fenología...")
fenologia = {}
if 'NDVI' in series_temporales:
    ndvi_series = series_temporales['NDVI']
    inicio, pico, fin = calcular_fenologia(ndvi_series.values, ndvi_series.time.values)
    fenologia['NDVI'] = {
        'inicio_estacion': inicio, 'pico_vegetacion': pico, 'fin_estacion': fin,
        'duracion_estacion': (pd.to_datetime(fin) - pd.to_datetime(inicio)).days if str(inicio)!='nan' and str(fin)!='nan' else np.nan
    }

pd.DataFrame(tendencias).T.to_csv(os.path.join(resultados_path,"tendencias_indices.csv"))
pd.DataFrame(cambios_abruptos).T.to_csv(os.path.join(resultados_path,"cambios_abruptos.csv"))
if fenologia:
    pd.DataFrame(fenologia).T.to_csv(os.path.join(resultados_path,"fenologia.csv"))

print("[INFO] Generando gráficos...")
plt.figure(figsize=(18,14))
# 1
plt.subplot(3,2,1)
for idx in ['NDVI','NDRE','EVI']:
    if idx in series_temporales:
        s = series_temporales[idx]
        plt.plot(s.time, s, marker='o', label=idx, linewidth=2, markersize=4)
plt.axhline(y=0.3, color='r', linestyle='--', alpha=0.5, label='Umbral suelo (0.3)')
plt.axhline(y=0.6, color='g', linestyle='--', alpha=0.5, label='Umbral cultivo (0.6)')
plt.title("Índices de Vegetación Principales")
plt.xlabel("Fecha"); plt.ylabel("Índice"); plt.legend(); plt.grid(alpha=0.3); plt.xticks(rotation=45)

# 2
plt.subplot(3,2,2)
for idx in ['GNDVI','OSAVI']:
    if idx in series_temporales:
        s = series_temporales[idx]; plt.plot(s.time, s, marker='s', label=idx, linewidth=2, markersize=4)
plt.title("Índices Avanzados"); plt.xlabel("Fecha"); plt.ylabel("Índice"); plt.legend(); plt.grid(alpha=0.3); plt.xticks(rotation=45)

# 3
plt.subplot(3,2,3)
if 'BIOMASA' in series_temporales:
    s = series_temporales['BIOMASA']; plt.plot(s.time, s, marker='^', label='Biomasa (kg/ha)', linewidth=2)
    plt.ylabel("Biomasa Estimada (kg/ha)"); plt.legend(loc='upper left')
ax2 = plt.gca().twinx()
if 'PRODUCTIVIDAD' in series_temporales:
    s2 = series_temporales['PRODUCTIVIDAD']; ax2.plot(s2.time, s2, marker='v', label='Productividad', linewidth=2, alpha=0.7)
    ax2.set_ylabel("Productividad"); ax2.legend(loc='upper right')
plt.title("Biomasa y Productividad"); plt.xlabel("Fecha"); plt.grid(alpha=0.3); plt.xticks(rotation=45)

# 4
plt.subplot(3,2,4)
if 'ESTRES_HIDRICO' in series_temporales:
    s = series_temporales['ESTRES_HIDRICO']; plt.plot(s.time, s, marker='D', label='Estrés hídrico', linewidth=2)
    plt.axhline(y=1.0, color='orange', linestyle='--', alpha=0.7, label='Umbral estrés (1.0)')
    plt.title("Estrés Hídrico"); plt.xlabel("Fecha"); plt.ylabel("Índice"); plt.legend(); plt.grid(alpha=0.3); plt.xticks(rotation=45)

# 5
plt.subplot(3,2,5)
indices_t = [idx for idx in ['NDVI','NDRE','EVI','GNDVI','OSAVI'] if idx in series_temporales]
pendientes = [pd.read_csv(os.path.join(resultados_path,"tendencias_indices.csv"), index_col=0).loc[idx,'pendiente']*1000 for idx in indices_t]
colors = ['green' if p>0 else 'red' for p in pendientes]
bars = plt.bar(indices_t, pendientes, alpha=0.7, color=colors)
plt.axhline(y=0, color='black', linestyle='-', alpha=0.8)
plt.title("Tendencia Anual (x1000) *p<0.05"); plt.ylabel("Cambio anual"); plt.grid(alpha=0.3, axis='y')

# 6
plt.subplot(3,2,6)
if 'NDVI' in series_temporales and str(fenologia.get('NDVI',{}).get('inicio_estacion','nan'))!='nan':
    s = series_temporales['NDVI']; plt.plot(s.time, s, marker='o', linewidth=2, label='NDVI')
    f = fenologia['NDVI']
    if str(f['inicio_estacion'])!='nan': plt.axvline(x=f['inicio_estacion'], color='blue', linestyle='--', alpha=0.7, label='Inicio')
    if str(f['pico_vegetacion'])!='nan': plt.axvline(x=f['pico_vegetacion'], color='red', linestyle='--', alpha=0.7, label='Pico')
    if str(f['fin_estacion'])!='nan': plt.axvline(x=f['fin_estacion'], color='orange', linestyle='--', alpha=0.7, label='Fin')
    plt.title("Fenología del Cultivo"); plt.xlabel("Fecha"); plt.ylabel("NDVI"); plt.legend(); plt.grid(alpha=0.3); plt.xticks(rotation=45)
else:
    plt.text(0.5,0.5,'Datos insuficientes para fenología', ha='center', va='center', transform=plt.gca().transAxes)

plt.tight_layout()
out_png = os.path.join(resultados_path, "serie_temporal_mejorada.png")
out_pdf = os.path.join(resultados_path, "serie_temporal_mejorada.pdf")
plt.savefig(out_png, dpi=300, bbox_inches='tight')
plt.savefig(out_pdf, bbox_inches='tight')
print(f"[OK] Guardados gráficos en: {out_png}")
