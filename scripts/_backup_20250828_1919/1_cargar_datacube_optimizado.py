# scripts/1_cargar_datacube_optimizado.py
import glob, xarray as xr, rioxarray, pandas as pd, numpy as np, os, re
from dask.diagnostics import ProgressBar

from config_mani import RUTAS, BANDAS

print("[INFO] 1. Cargando y creando datacube (OPTIMIZADO) - MANÍ Córdoba")

datos_raw = RUTAS["raw"]
nc_path = RUTAS["datacube"]
os.makedirs(os.path.dirname(nc_path), exist_ok=True)

archivos = sorted(glob.glob(os.path.join(datos_raw, "MANI_*.tif")) + glob.glob(os.path.join(datos_raw, "S2_*.tif")))
if not archivos:
    raise FileNotFoundError(f"[ERROR] No se encontraron GeoTIFF en {datos_raw} (esperado MANI_*.tif o S2_*.tif)")

print(f"[OK] Encontrados {len(archivos)} archivos")

fechas = []
for f in archivos:
    nombre = os.path.basename(f)
    m = re.search(r'(\d{8})', nombre)
    if m: fechas.append(m.group(1))
    else: raise ValueError(f"[ERROR] No se encontró fecha en: {nombre}")
print(f"[OK] Fechas extraídas: {fechas[:5]}... (total: {len(fechas)})")

print("[INFO] Cargando archivos en paralelo...")
data_arrays = []
for i, f in enumerate(archivos):
    print(f"  Cargando {i+1}/{len(archivos)}: {os.path.basename(f)}")
    da = rioxarray.open_rasterio(f, chunks={'x': 1000, 'y': 1000})
    # Si el archivo trae bandas sin nombres, asignamos los esperados
    if len(da.band) == len(BANDAS):
        da = da.assign_coords(band=BANDAS)
    data_arrays.append(da)

with ProgressBar():
    datacube = xr.concat(data_arrays, dim='time', combine_attrs='drop')

fechas_dt = pd.to_datetime(fechas, format='%Y%m%d')
datacube = datacube.assign_coords(time=fechas_dt)
datacube = datacube.to_dataset(dim="band")

if not hasattr(datacube, 'rio') or datacube.rio.crs is None:
    print("[WARN] CRS no encontrado. Asignando EPSG:32720")
    datacube = datacube.rio.write_crs("EPSG:32720")

print("[INFO] Guardando datacube optimizado...")
encoding = {var: {'zlib': True, 'complevel': 1} for var in datacube.data_vars}
datacube.to_netcdf(nc_path, engine='netcdf4', mode='w', encoding=encoding)

print(f"[OK] DataCube guardado: {nc_path}")
print(f"[INFO] Dimensiones: {dict(datacube.sizes)}")
print(f"[INFO] Variables: {list(datacube.data_vars)}")
print(f"[INFO] Rango temporal: {datacube.time[0].item()} a {datacube.time[-1].item()}")
