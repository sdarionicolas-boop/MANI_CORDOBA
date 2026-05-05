# config_mani.py — Configuración principal para el proyecto MANI_CORDOBA

import os

BASE_DIR = r"C:\Users\sdari\Desktop\Pruebas e Investigaciones\MANI_CORDOBA"

RAW_DIR        = os.path.join(BASE_DIR, "datos", "raw")
PROCESSED_DIR  = os.path.join(BASE_DIR, "datos", "processed")
EXTERNOS_DIR   = os.path.join(BASE_DIR, "datos", "externos")
RESULTADOS_DIR = os.path.join(BASE_DIR, "resultados")
MAPAS_DIR      = os.path.join(RESULTADOS_DIR, "mapas")
ESTAD_DIR      = os.path.join(RESULTADOS_DIR, "estadisticas")
TIMELAPSE_DIR  = os.path.join(RESULTADOS_DIR, "timelapse")
INFORMES_DIR   = os.path.join(RESULTADOS_DIR, "informes")
IMAGENES_DIR   = os.path.join(RESULTADOS_DIR, "imagenes")
LOGS_DIR       = os.path.join(RESULTADOS_DIR, "logs")
DATACUBE_PATH  = os.path.join(PROCESSED_DIR, "datacube_s2.nc")

CRS_EPSG       = "EPSG:32720"
S2_SCALE_M     = 10
PIXEL_AREA_HA  = 0.01

BANDAS_S2 = ['B2','B3','B4','B5','B8','NDVI','NDRE','NDWI','EVI']
KMEANS_CLUSTERS = 4
CLASS_LABELS = {
    0: "Suelo desnudo / seco",
    1: "Cultivo en desarrollo",
    2: "Cultivo maduro",
    3: "Zona húmeda / vegetación densa"
}

NDVI_START_THRESHOLD = 0.30
NDVI_END_THRESHOLD   = 0.40
GAUSS_SMOOTH_SIGMA   = 2

RUTAS = {
    "base": BASE_DIR, "raw": RAW_DIR, "processed": PROCESSED_DIR, "externos": EXTERNOS_DIR,
    "resultados": RESULTADOS_DIR, "mapas": MAPAS_DIR, "estadisticas": ESTAD_DIR,
    "timelapse": TIMELAPSE_DIR, "informes": INFORMES_DIR, "imagenes": IMAGENES_DIR, "logs": LOGS_DIR,
}

BANDAS = BANDAS_S2
LABELS_DICT = CLASS_LABELS
