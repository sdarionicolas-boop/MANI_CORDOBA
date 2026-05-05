# scripts/1_cargar_datacube_optimizado.py
import os, sys, glob, re
import numpy as np
import pandas as pd
import xarray as xr

# asegurar rioxarray
try:
    import rioxarray  # noqa: F401
except Exception as e:
    print("[WARN] No se pudo importar rioxarray. Instalar con: pip install rioxarray rasterio")
    raise

# === BOOTSTRAP MANI_CORDOBA ===
BASE_DIR = r"C:\Users\sdari\Desktop\Pruebas e Investigaciones\MANI_CORDOBA"
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
import config_mani as CFG

print("[INFO] 1. Cargando y creando datacube (OPTIMIZADO - MANI_CORDOBA)")
print(f"[INFO] RAW_DIR: {CFG.RAW_DIR}")

os.makedirs(CFG.PROCESSED_DIR, exist_ok=True)

bandas_objetivo = CFG.BANDAS_S2  # ['B2','B3','B4','B5','B8','NDVI','NDRE','NDWI','EVI']
nc_path = CFG.DATACUBE_PATH

# ------------------------------------------------------------------
# 1) Descubrir archivos
# ------------------------------------------------------------------
archivos = sorted(glob.glob(os.path.join(CFG.RAW_DIR, "S2_*.tif")))
if not archivos:
    print("[ERROR] No se encontraron archivos S2_*.tif en datos\\raw.")
    try:
        listado = os.listdir(CFG.RAW_DIR)
        print("[INFO] Contenido de datos\\raw:")
        for nm in listado:
            print("  -", nm)
    except Exception as e:
        print("[WARN] No se pudo listar datos\\raw:", e)
    sys.exit(1)

print(f"[OK] Encontrados {len(archivos)} TIFF")

# ------------------------------------------------------------------
# 2) Extraer fechas de los nombres
# ------------------------------------------------------------------
fechas = []
for f in archivos:
    nombre = os.path.basename(f)
    m = re.search(r'(\d{8})', nombre)
    if not m:
        print(f"[ERROR] No se encontró fecha YYYYMMDD en {nombre}. Renombrar a S2_YYYYMMDD.tif")
        sys.exit(1)
    fechas.append(m.group(1))
print(f"[OK] Ejemplo fechas: {fechas[:5]} ... total {len(fechas)}")

# ------------------------------------------------------------------
# 3) Cargar cada TIFF y asegurar 9 bandas
#    - Si trae 9 bandas: renombramos a bandas_objetivo
#    - Si trae 5 bandas: calculamos NDVI, NDRE, NDWI, EVI
# ------------------------------------------------------------------
da_list = []
for i, f in enumerate(archivos):
    nombre = os.path.basename(f)
    print(f"[INFO] Cargando {i+1}/{len(archivos)}: {nombre}")
    da = rioxarray.open_rasterio(f, chunks={'x': 1000, 'y': 1000})  # DataArray dims: (band, y, x)
    # Número de bandas reales
    nband = da.sizes.get("band", 1)

    if nband == 9:
        # asumimos orden correcto ya exportado por GEE
        da = da.assign_coords(band=bandas_objetivo)
    elif nband == 5:
        # asumimos orden: B2,B3,B4,B5,B8  -> agregamos NDVI, NDRE, NDWI, EVI
        base_names = ['B2','B3','B4','B5','B8']
        da = da.assign_coords(band=base_names)
        # convertir a Dataset temporal para cálculos
        dsb = da.to_dataset(dim="band")  # vars: B2,B3,B4,B5,B8
        eps = 1e-10
        NDVI = (dsb['B8'] - dsb['B4']) / (dsb['B8'] + dsb['B4'] + eps)
        NDRE = (dsb['B8'] - dsb['B5']) / (dsb['B8'] + dsb['B5'] + eps)
        NDWI = (dsb['B3'] - dsb['B8']) / (dsb['B3'] + dsb['B8'] + eps)
        EVI  = 2.5 * ((dsb['B8'] - dsb['B4']) / (dsb['B8'] + 6*dsb['B4'] - 7.5*dsb['B2'] + 1 + eps))

        # volver a apilar en orden objetivo
        da = xr.concat(
            [dsb['B2'], dsb['B3'], dsb['B4'], dsb['B5'], dsb['B8'], NDVI, NDRE, NDWI, EVI],
            dim="band"
        ).assign_coords(band=bandas_objetivo)
    else:
        print(f"[ERROR] {nombre} tiene {nband} bandas. Se esperan 9 o 5. Revise exportación de GEE.")
        sys.exit(1)

    # aseguramos dtype float32 para todo
    da = da.astype("float32")

    # agregar a lista
    da_list.append(da)

# ------------------------------------------------------------------
# 4) Concatenar temporalmente y a Dataset
# ------------------------------------------------------------------
print("[INFO] Concatenando imágenes...")
datacube = xr.concat(da_list, dim="time", combine_attrs="drop")

# asignar coordenadas de tiempo desde 'fechas'
fechas_dt = pd.to_datetime(fechas, format="%Y%m%d")
datacube = datacube.assign_coords(time=fechas_dt)

# pasar a Dataset por banda
datacube = datacube.to_dataset(dim="band")  # variables: B2, B3, ..., EVI

# CRS
try:
    if getattr(datacube, "rio", None) is not None and datacube.rio.crs is None:
        datacube = datacube.rio.write_crs(CFG.CRS_EPSG)
except Exception as e:
    print("[WARN] No se pudo escribir CRS al dataset:", e)

print("[OK] DataCube armado")
print("[INFO] Dimensiones:", dict(datacube.sizes))
print("[INFO] Variables:", list(datacube.data_vars))

# ------------------------------------------------------------------
# 5) Guardar NetCDF (con fallback de engine)
# ------------------------------------------------------------------
os.makedirs(CFG.PROCESSED_DIR, exist_ok=True)
encoding = {var: {'zlib': True, 'complevel': 1} for var in datacube.data_vars}

def guardar_nc(path, ds):
    try:
        ds.to_netcdf(path, engine='netcdf4', mode='w', encoding=encoding)
        return True, "netcdf4"
    except Exception as e:
        print("[WARN] Falló engine netcdf4:", e)
        try:
            ds.to_netcdf(path, engine='scipy', mode='w')  # sin compresión con scipy
            return True, "scipy"
        except Exception as e2:
            print("[ERROR] También falló engine scipy:", e2)
            return False, str(e2)

print(f"[INFO] Guardando datacube en: {nc_path}")
ok, engine_usado = guardar_nc(nc_path, datacube)
if not ok:
    print("[ERROR] No se pudo guardar el NetCDF. Verifique dependencias: pip install netCDF4")
    sys.exit(1)
else:
    print(f"[OK] DataCube guardado con engine: {engine_usado}")
    print(f"[INFO] Rango temporal: {str(datacube.time.values[0])} a {str(datacube.time.values[-1])}")
    # imprimir tamaño aproximado en disco
    try:
        sz = os.path.getsize(nc_path) / (1024**2)
        print(f"[INFO] Tamaño de archivo: {sz:.1f} MB")
    except Exception:
        pass

print("[DONE] Paso 1 finalizado correctamente")
