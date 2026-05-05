# scripts/3_clasificar_fecha_global.py
import numpy as np, pandas as pd, rioxarray, os, importlib, xarray as xr
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from config_mani import RUTAS, LABELS_DICT

from utils_agro import cargar_datacube

print("[INFO] 3. Clasificando con modelo GLOBAL - MANÍ Córdoba")

mapas_path = RUTAS["mapas"]
os.makedirs(mapas_path, exist_ok=True)

datacube = cargar_datacube(RUTAS["processed"].replace("\\\\processed",""))
bandas_clasif = ['NDVI','NDRE','NDWI']

print("[INFO] Muestreo estratificado en el tiempo...")
muestras_por_fecha = min(10, len(datacube.time))
fechas_muestreo = np.linspace(0, len(datacube.time)-1, muestras_por_fecha, dtype=int)

X_train_list = []
for t in fechas_muestreo:
    fecha_str = pd.to_datetime(datacube.time[t].values).strftime('%Y%m%d')
    img = datacube.isel(time=t)
    X_stack = [img[band].values.flatten() for band in bandas_clasif]
    X_date = np.column_stack(X_stack)
    valid = ~np.isnan(X_date).any(axis=1)
    X_valid = X_date[valid]
    if len(X_valid) > 1000:
        np.random.seed(42 + int(t))
        idx = np.random.choice(len(X_valid), 1000, replace=False)
        X_valid = X_valid[idx]
    X_train_list.append(X_valid)

X_train = np.vstack(X_train_list)
print(f"[OK] {X_train.shape[0]} muestras entrenamiento")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10).fit(X_scaled)

print("[INFO] Lookup table por NDVI promedio...")
ndvi_prom = {}
for c in range(4):
    m = kmeans.labels_ == c
    if np.any(m):
        ndvi_prom[c] = float(np.mean(X_train[m][:,0]))
clases_ordenadas = sorted(ndvi_prom.keys(), key=lambda c: ndvi_prom[c])
lookup_table = {orig: new for new, orig in enumerate(clases_ordenadas)}
print(f"[OK] Lookup table: {lookup_table}")

print("\n[INFO] Clasificando todas las fechas...")
for t in range(len(datacube.time)):
    fecha_dt = datacube.time[t].values
    fecha_str = pd.to_datetime(fecha_dt).strftime('%Y%m%d')
    img = datacube.isel(time=t)
    X = np.stack([img[b].values for b in bandas_clasif], axis=2)
    shape = X.shape[:2]
    X_flat = X.reshape(-1, len(bandas_clasif))
    valid = ~np.isnan(X_flat).any(axis=1)
    X_valid = X_flat[valid]
    if X_valid.size == 0:
        print(f"  [WARN] {fecha_str}: sin datos válidos")
        continue
    Xs = scaler.transform(X_valid)
    labels = kmeans.predict(Xs)
    labels_cons = np.array([lookup_table.get(l, l) for l in labels])
    mapa = np.full(X_flat.shape[0], np.nan, dtype=np.float32)
    mapa[valid] = labels_cons.astype(np.float32)
    mapa = mapa.reshape(shape)
    da = xr.DataArray(mapa, coords={'y': img.y.values, 'x': img.x.values}, dims=['y','x'], 
                      attrs={'classes': str(LABELS_DICT), 'date': fecha_str, 'model':'kmeans_global'})
    da.rio.write_crs("EPSG:32720", inplace=True)
    da.rio.write_nodata(np.nan, encoded=True, inplace=True)
    ruta = os.path.join(mapas_path, f"clasificacion_{fecha_str}.tif")
    da.rio.to_raster(ruta)
    print(f"  [OK] Guardado: {os.path.basename(ruta)}")
print("\n[OK] Clasificación completa")
