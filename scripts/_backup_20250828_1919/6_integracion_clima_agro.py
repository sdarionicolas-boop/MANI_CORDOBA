# scripts/6_integracion_clima_agro.py
# Integración: Clima (EEA Manfredi CSV) + NDVI real
# Fecha: Agosto 2025

import pandas as pd, numpy as np, matplotlib.pyplot as plt, os, xarray as xr, warnings
warnings.filterwarnings('ignore')
from datetime import timedelta

from config_mani import RUTAS

print("🚀 Integración: Clima (EEA Manfredi) + NDVI (Sentinel-2)")

ruta_clima = RUTAS["clima"]
ruta_datacube = RUTAS["datacube"]
ruta_out_dir = RUTAS["estadisticas"]
os.makedirs(ruta_out_dir, exist_ok=True)

ruta_salida_csv = os.path.join(ruta_out_dir, "Dataset_Integrado_Clima_Vigor.csv")
ruta_salida_png = os.path.join(ruta_out_dir, "Evolucion_Vigor_vs_Clima.png")
ruta_corr_png = os.path.join(ruta_out_dir, "Matriz_Correlacion.png")
ruta_reg_png = os.path.join(ruta_out_dir, "Analisis_Regresion.png")

def cargar_y_limpiar_clima(path_csv):
    print("🔍 Cargando clima:", path_csv)
    df = pd.read_csv(path_csv)
    # Estándar de nombres
    df.columns = [str(c).strip() for c in df.columns]
    # Intentar detectar columnas típicas
    col_map_posibles = [
        {'Fecha':'Fecha','Tmedia':'Tmedia','Tmax':'Tmax','Tmin':'Tmin','Precip':'Precip'},
        {'Fecha':'fecha','Tmedia':'tmedia','Tmax':'tmax','Tmin':'tmin','Precip':'precip'},
        {'Fecha':'Date','Tmedia':'Temp_mean','Tmax':'Temp_max','Tmin':'Temp_min','Precip':'Precip'}
    ]
    mapeo = None
    for mp in col_map_posibles:
        if all(v in df.columns for v in mp.values()):
            # invertimos: clave estándar -> realidad
            inv = {k: mp[k] for k in mp}
            mapeo = inv; break
    if mapeo is None:
        raise ValueError("No se encontraron columnas estándar. Revisá encabezados del CSV.")
    df = df.rename(columns={mapeo['Fecha']:'Fecha', mapeo['Tmedia']:'Tmedia', mapeo['Tmax']:'Tmax', mapeo['Tmin']:'Tmin', mapeo['Precip']:'Precip'})
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df = df.dropna(subset=['Fecha']).sort_values('Fecha')
    for c in ['Tmedia','Tmax','Tmin']:
        df[c] = pd.to_numeric(df[c], errors='coerce').interpolate().bfill().ffill()
    df['Precip'] = pd.to_numeric(df['Precip'], errors='coerce').fillna(0)
    return df.set_index('Fecha')

def cargar_ndvi_desde_datacube(path_nc):
    print("🔍 Cargando NDVI desde datacube:", path_nc)
    ds = xr.open_dataset(path_nc)
    if 'NDVI' not in ds.data_vars: raise ValueError("'NDVI' no está en el datacube")
    registros = []
    for t in range(len(ds.time)):
        fecha_dt = ds.time[t].values
        ndvi = ds['NDVI'].isel(time=t)
        ndvi_val = ndvi.where(ndvi.notnull()).mean().values.item()
        if ndvi_val == ndvi_val:  # no NaN
            registros.append({'Fecha': pd.to_datetime(fecha_dt), 'NDVI': float(ndvi_val)})
    return pd.DataFrame(registros)

def extraer_clima_promedio(df_clima, fecha, dias_previos=10):
    datos = df_clima.loc[fecha - timedelta(days=dias_previos): fecha]
    if datos.empty: return np.nan, np.nan, np.nan, np.nan
    return datos['Tmedia'].mean(), datos['Tmax'].max(), datos['Tmin'].min(), datos['Precip'].sum()

def integrar_datos(df_clima, df_ndvi):
    out = []
    for _, row in df_ndvi.iterrows():
        fecha = row['Fecha']
        tm, tx, tn, pp = extraer_clima_promedio(df_clima, fecha, dias_previos=10)
        out.append({'Fecha': fecha, 'NDVI': row['NDVI'], 'Tmedia': tm, 'Tmax': tx, 'Tmin': tn, 'Precip': pp})
    df = pd.DataFrame(out).dropna().sort_values('Fecha').reset_index(drop=True)
    print(f"✅ Integrado {len(df)} fechas")
    return df

def matriz_correlacion(df):
    import seaborn as sns
    vars = ['NDVI','Tmedia','Tmax','Tmin','Precip']
    v = [c for c in vars if c in df.columns]
    corr = df[v].corr()
    plt.figure(figsize=(8,6))
    sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, square=True, fmt='.3f')
    plt.title('Matriz de Correlación'); plt.tight_layout(); plt.savefig(ruta_corr_png, dpi=300)
    return corr

def analisis_regresion(df):
    import numpy as np
    import statsmodels.api as sm
    plt.figure(figsize=(12,10))
    # NDVI vs Tmedia
    x = df['Tmedia']; y = df['NDVI']
    z = np.polyfit(x, y, 1); p = np.poly1d(z); r2 = np.corrcoef(x,y)[0,1]**2
    plt.subplot(2,2,1); plt.scatter(x,y, alpha=0.6); plt.plot(x, p(x), "r--"); plt.title(f'NDVI vs Tmedia (R²={r2:.3f})'); plt.xlabel('Tmedia'); plt.ylabel('NDVI'); plt.grid(alpha=0.3)
    # NDVI vs Precip
    x2 = df['Precip']; z2 = np.polyfit(x2, y, 1); p2 = np.poly1d(z2); r22 = np.corrcoef(x2,y)[0,1]**2
    plt.subplot(2,2,2); plt.scatter(x2,y, alpha=0.6, color='green'); plt.plot(x2, p2(x2), "r--"); plt.title(f'NDVI vs Precip (R²={r22:.3f})'); plt.xlabel('Precip (mm)'); plt.ylabel('NDVI'); plt.grid(alpha=0.3)
    # Múltiple
    X = sm.add_constant(df[['Tmedia','Precip']]); model = sm.OLS(y, X).fit(); y_pred = model.predict(X)
    plt.subplot(2,2,3); plt.scatter(y, y_pred, alpha=0.6, color='purple'); m1, m2 = min(y.min(), y_pred.min()), max(y.max(), y_pred.max())
    plt.plot([m1,m2],[m1,m2],'r--'); plt.xlabel('NDVI Real'); plt.ylabel('NDVI Predicho'); plt.title(f'Regresión Múltiple (R²={model.rsquared:.3f})'); plt.grid(alpha=0.3)
    # Residuos
    resid = y - y_pred; plt.subplot(2,2,4); plt.scatter(y_pred, resid, alpha=0.6, color='orange'); plt.axhline(0,color='r',linestyle='--'); plt.xlabel('NDVI Predicho'); plt.ylabel('Residuos'); plt.title('Residuos'); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(ruta_reg_png, dpi=300)
    return model

def grafico_integrado(df):
    plt.figure(figsize=(14,7))
    ax1 = plt.gca()
    ax1.plot(df['Fecha'], df['NDVI'], 'go-', label='NDVI', markersize=5)
    ax1.set_ylabel('NDVI', color='g'); ax1.tick_params(axis='y', labelcolor='g'); ax1.set_ylim(0,1)
    ax2 = ax1.twinx()
    ax2.bar(df['Fecha'], df['Precip'], alpha=0.3, label='Precip 10d', width=5)
    ax2.plot(df['Fecha'], df['Tmin'], 'c--', label='Tmin 10d avg', alpha=0.8)
    ax2.set_ylabel('Precip (mm) / Tmin (°C)')
    plt.title('NDVI vs Clima (10 días previos)'); lines1, labels1 = ax1.get_legend_handles_labels(); lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1+lines2, labels1+labels2, loc='upper left'); plt.xticks(rotation=45); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(ruta_salida_png, dpi=300)

if __name__ == "__main__":
    df_clima = cargar_y_limpiar_clima(ruta_clima)
    df_ndvi = cargar_ndvi_desde_datacube(ruta_datacube)
    if df_clima is None or df_ndvi is None or df_clima.empty or df_ndvi.empty:
        print("❌ No se puede continuar sin datos.")
    else:
        df_final = integrar_datos(df_clima, df_ndvi)
        if len(df_final)>0:
            df_final.to_csv(ruta_salida_csv, index=False); print("💾 Guardado:", ruta_salida_csv)
            corr = matriz_correlacion(df_final)
            model = analisis_regresion(df_final)
            grafico_integrado(df_final)
            print("✅ Integración completa.")
        else:
            print("❌ Datos insuficientes para análisis.")
