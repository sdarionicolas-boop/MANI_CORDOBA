# utils_agro.py — Utilidades comunes para el pipeline MANI_CORDOBA

import os
import numpy as np
import pandas as pd
import xarray as xr
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# .rio (GeoTIFF/CRS) — opcional pero recomendado
try:
    import rioxarray  # noqa: F401
except Exception as e:
    print("[WARN] rioxarray/rasterio no disponible. Instalar: pip install rioxarray rasterio")

# Config centralizada
try:
    import config_mani as CFG
except ImportError as e:
    raise ImportError(
        "No se encontró config_mani.py en el PYTHONPATH. "
        "Agregá la carpeta base al sys.path antes de importar utils_agro."
    ) from e


def _ensure_dirs():
    """Crea carpetas clave si faltan (según config_mani)."""
    for d in [
        CFG.PROCESSED_DIR, CFG.RESULTADOS_DIR, CFG.MAPAS_DIR,
        CFG.ESTAD_DIR, CFG.TIMELAPSE_DIR, CFG.INFORMES_DIR,
        CFG.IMAGENES_DIR, CFG.LOGS_DIR
    ]:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            print(f"[WARN] No se pudo crear {d}: {e}")


def cargar_datacube(base_dir=None, path_override=None):
    """
    Carga el datacube NetCDF como xarray.Dataset con chunks.
    Args:
        base_dir: si querés forzar base; si None usa rutas de CFG.
        path_override: ruta directa a .nc (si se pasa, ignora lo demás).
    """
    _ensure_dirs()
    if path_override is not None:
        datacube_path = path_override
    elif base_dir is not None:
        datacube_path = os.path.join(base_dir, "datos", "processed", "datacube_s2.nc")
    else:
        datacube_path = CFG.DATACUBE_PATH

    if not os.path.exists(datacube_path):
        raise FileNotFoundError(f"DataCube no encontrado: {datacube_path}")

    ds = xr.open_dataset(datacube_path, chunks={'time': 10, 'x': 1000, 'y': 1000})

    # Asegurar CRS si es posible
    try:
        if getattr(ds, "rio", None) is not None and ds.rio.crs is None:
            ds = ds.rio.write_crs(CFG.CRS_EPSG)
    except Exception:
        pass

    print(f"[OK] Dataset cargado desde: {datacube_path}")
    print(f"[INFO] Variables: {list(ds.data_vars.keys())}")
    print(f"[INFO] Dimensiones: {dict(ds.dims)}")
    return ds


def entrenar_modelo_global(ds, bandas_clasif=None, n_muestras=10000, n_clusters=None, random_state=42):
    """
    Entrena KMeans global con muestras estratificadas en el tiempo.
    Devuelve: (kmeans, scaler, X_muestras)
    """
    if bandas_clasif is None:
        bandas_clasif = ['NDVI', 'NDRE', 'NDWI']
    if n_clusters is None:
        n_clusters = getattr(CFG, "KMEANS_CLUSTERS", 4)

    print("[INFO] Entrenando modelo global de clasificación...")

    time_step = max(1, len(ds.time) // 10)
    muestras = ds[bandas_clasif].isel(time=slice(0, None, time_step))

    X_list = []
    for t in range(len(muestras.time)):
        band_data_list = []
        for band in bandas_clasif:
            band_data = muestras[band].isel(time=t).values.flatten()
            band_data_list.append(band_data)
        X_date = np.column_stack(band_data_list)  # (n_pix, n_bandas)
        X_list.append(X_date)

    X = np.vstack(X_list)
    valid_mask = ~np.isnan(X).any(axis=1)
    X_valid = X[valid_mask]

    if len(X_valid) > n_muestras:
        np.random.seed(42)
        idx = np.random.choice(len(X_valid), n_muestras, replace=False)
        X_valid = X_valid[idx]

    if len(X_valid) == 0:
        raise ValueError("No hay datos válidos para entrenar el modelo")

    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_valid)

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    kmeans.fit(X_scaled)

    print("[OK] Modelo global entrenado")
    return kmeans, scaler, X_valid


def calcular_indices_avanzados(ds):
    """
    Calcula índices avanzados (GNDVI, OSAVI, BIOMASA, ESTRES_HIDRICO, PRODUCTIVIDAD)
    a partir de bandas existentes en el Dataset.
    Requiere: B2, B3, B4, B5, B8, NDVI, NDRE, NDWI, EVI.
    """
    print("[INFO] Calculando índices avanzados...")

    requeridas = ['B2', 'B3', 'B4', 'B5', 'B8', 'NDVI', 'NDRE', 'NDWI', 'EVI']
    faltan = [b for b in requeridas if b not in ds.data_vars]
    if faltan:
        raise ValueError(f"Bandas faltantes para índices avanzados: {faltan}")

    ds2 = ds.copy()
    eps = 1e-10

    try:
        ds2['GNDVI'] = (ds['B8'] - ds['B3']) / (ds['B8'] + ds['B3'] + eps)
    except Exception as e:
        print(f"[WARN] GNDVI: {e}")

    try:
        ds2['OSAVI'] = 1.16 * (ds['B8'] - ds['B4']) / (ds['B8'] + ds['B4'] + 0.16)
    except Exception as e:
        print(f"[WARN] OSAVI: {e}")

    try:
        ds2['BIOMASA'] = (ds['NDRE'] * 0.8 + ds['EVI'] * 0.5) * 1000.0
    except Exception as e:
        print(f"[WARN] BIOMASA: {e}")

    try:
        ds2['ESTRES_HIDRICO'] = ds['NDVI'] / (ds['NDWI'] + eps)
    except Exception as e:
        print(f"[WARN] ESTRES_HIDRICO: {e}")

    try:
        ds2['PRODUCTIVIDAD'] = ds['NDVI'] * ds['EVI'] * 100.0
    except Exception as e:
        print(f"[WARN] PRODUCTIVIDAD: {e}")

    print("[OK] Índices avanzados calculados")
    return ds2


def detectar_cambios_abruptos(serie_temporal, umbral=0.3, ventana=3):
    """
    Detecta cambios abruptos en series temporales:
      1) Suaviza con media móvil centrada
      2) Diferencia absoluta entre pasos
      3) Marca True donde supera umbral
    """
    if len(serie_temporal) < ventana + 1:
        return np.array([False] * len(serie_temporal))
    serie_suave = pd.Series(serie_temporal).rolling(ventana, center=True).mean().values
    dif = np.abs(np.diff(serie_suave, prepend=serie_suave[0]))
    return dif > umbral


def analizar_tendencias(serie_temporal):
    """
    Tendencia lineal simple con stats.linregress.
    Devuelve: slope, p_value, r2
    """
    if len(serie_temporal) < 3 or np.all(np.isnan(serie_temporal)):
        return np.nan, np.nan, np.nan
    x = np.arange(len(serie_temporal))
    mask = ~np.isnan(serie_temporal)
    if np.sum(mask) < 3:
        return np.nan, np.nan, np.nan
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            x[mask], np.array(serie_temporal)[mask]
        )
        return slope, p_value, r_value**2
    except Exception:
        return np.nan, np.nan, np.nan


def calcular_fenologia(serie_ndvi, fechas):
    """
    Inicio, pico y fin de campaña usando umbrales/param de config:
      - CFG.GAUSS_SMOOTH_SIGMA
      - CFG.NDVI_START_THRESHOLD
      - CFG.NDVI_END_THRESHOLD
    Devuelve: (inicio_fecha, pico_fecha, fin_fecha)
    """
    if len(serie_ndvi) < 10 or np.all(np.isnan(serie_ndvi)):
        return np.nan, np.nan, np.nan
    try:
        from scipy.ndimage import gaussian_filter1d
        ndvi_suave = gaussian_filter1d(serie_ndvi, sigma=CFG.GAUSS_SMOOTH_SIGMA)

        inicio_mask = ndvi_suave > CFG.NDVI_START_THRESHOLD
        inicio_idx = np.argmax(inicio_mask) if np.any(inicio_mask) else np.nan

        pico_idx = int(np.nanargmax(ndvi_suave)) if not np.all(np.isnan(ndvi_suave)) else np.nan

        if not np.isnan(pico_idx) and pico_idx < len(ndvi_suave) - 1:
            fin_mask = ndvi_suave[pico_idx:] < CFG.NDVI_END_THRESHOLD
            fin_idx = pico_idx + np.argmax(fin_mask) if np.any(fin_mask) else len(ndvi_suave) - 1
        else:
            fin_idx = np.nan

        inicio_fecha = fechas[int(inicio_idx)] if not np.isnan(inicio_idx) else np.nan
        pico_fecha   = fechas[int(pico_idx)]   if not np.isnan(pico_idx)   else np.nan
        fin_fecha    = fechas[int(fin_idx)]    if not np.isnan(fin_idx)    else np.nan
        return inicio_fecha, pico_fecha, fin_fecha
    except Exception as e:
        print(f"[WARN] Fenología: {e}")
        return np.nan, np.nan, np.nan


def exportar_geotiff(ds, variable, fecha, carpeta_salida):
    """
    Exporta una variable (DataArray) a GeoTIFF con CRS de configuración.
    Requisitos: rioxarray y CRS válido en config.
    """
    os.makedirs(carpeta_salida, exist_ok=True)
    fecha_str = pd.to_datetime(fecha).strftime('%Y%m%d')
    nombre = f"{variable}_{fecha_str}.tif"
    ruta = os.path.join(carpeta_salida, nombre)
    try:
        da = ds[variable].sel(time=fecha, method='nearest')
        try:
            if getattr(da, "rio", None) is not None and da.rio.crs is None:
                da = da.rio.write_crs(CFG.CRS_EPSG)
        except Exception:
            pass
        da.rio.to_raster(ruta)
        print(f"[OK] Exportado {variable} -> {ruta}")
        return ruta
    except Exception as e:
        print(f"[ERROR] Exportando {variable}: {e}")
        return None
