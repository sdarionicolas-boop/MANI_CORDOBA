# scripts/7_generar_informe_pdf_mejorado.py
import os, pandas as pd, matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime
from config_mani import RUTAS, LABELS_DICT

print("[INFO] 7. Generando informe PDF - MANÍ Córdoba")

estadisticas_path = RUTAS["estadisticas"]
pdf_path = RUTAS["informes"]
timelapse_path = RUTAS["timelapse"]
os.makedirs(pdf_path, exist_ok=True)

area_csv = os.path.join(estadisticas_path, "area_por_clase.csv")
estadisticas_csv = os.path.join(estadisticas_path, "estadisticas_clases.csv")
evolucion_png = os.path.join(estadisticas_path, "evolucion_area_mejorada.png")
clima_grafico = os.path.join(estadisticas_path, "Evolucion_Vigor_vs_Clima.png")
matriz_correlacion = os.path.join(estadisticas_path, "Matriz_Correlacion.png")
analisis_regresion = os.path.join(estadisticas_path, "Analisis_Regresion.png")
dataset_integrado = os.path.join(estadisticas_path, "Dataset_Integrado_Clima_Vigor.csv")
serie_temporal_png = os.path.join(estadisticas_path, "serie_temporal_mejorada.png")
tendencias_csv = os.path.join(estadisticas_path, "tendencias_indices.csv")
cambios_csv = os.path.join(estadisticas_path, "cambios_abruptos.csv")
fenologia_csv = os.path.join(estadisticas_path, "fenologia.csv")
timelapse_gif = os.path.join(timelapse_path, "timelapse_mani.gif")

class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font("Arial", "B", 16)
            self.cell(0, 10, "INFORME DE MONITOREO AGRÍCOLA - MANÍ (Córdoba)", 0, 1, 'C')
            self.set_font("Arial", "", 10)
            self.cell(0, 8, f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'C')
            self.ln(5)
        else:
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Informe - Página {self.page_no()}", 0, 0, 'R')
            self.ln(15)
    def footer(self):
        self.set_y(-15); self.set_font("Arial","I",8); self.cell(0,10, f"Página {self.page_no()}", 0,0,'C')
    def add_section_title(self, title):
        self.ln(6); self.set_font("Arial","B",12); self.set_fill_color(240,240,240)
        self.cell(0,8,title,0,1,'L',1); self.ln(2)
    def add_image_with_caption(self, path, caption, width=190):
        if os.path.exists(path):
            try:
                self.image(path, x=10, w=width); self.ln(4)
                self.set_font("Arial","I",9); self.cell(0,5,caption,0,1,'C'); self.ln(6)
                return True
            except: pass
        self.set_font("Arial","",10); self.cell(0,6,f"Archivo no encontrado: {os.path.basename(path)}",0,1); return False

pdf = PDF(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()

# Portada
pdf.set_font("Arial","B",18); pdf.cell(0,15,"INFORME TÉCNICO",0,1,'C')
pdf.set_font("Arial","",12)
pdf.cell(0,8, "Zona: EEA Gral. Cabrera - Córdoba", 0,1,'C')
pdf.cell(0,8, "Campaña: 2023-2025 | Satélite: Sentinel-2 | Algoritmo: K-means", 0,1,'C')
pdf.ln(8)

# Índice
pdf.add_section_title("ÍNDICE")
for i, item in enumerate(["1. Introducción","2. Metodología","3. Clases","4. Análisis temporal",
                          "5. Evolución de áreas","6. Estadísticas por clase",
                          "7. Clima vs NDVI","8. Correlaciones","9. Regresiones","10. Timelapse","11. Conclusiones"], start=1):
    pdf.set_font("Arial","",11); pdf.cell(0,7, item, ln=True)

# Introducción
pdf.add_section_title("1. INTRODUCCIÓN")
pdf.set_font("Arial","",11)
pdf.multi_cell(0,6, "Este informe integra teledetección (Sentinel-2) y clima (EEA Manfredi) para monitorear el cultivo de MANÍ en Córdoba. Se utiliza una clasificación K-means consistente en el tiempo y análisis de series para estimar desarrollo, estrés hídrico y productividad relativa.")

# Metodología
pdf.add_section_title("2. METODOLOGÍA")
pdf.multi_cell(0,6, "- Colección S2 SR Harmonized, 10 m.\n- Índices: NDVI, NDRE, NDWI, EVI + derivados.\n- K-means (4 clases) con normalización por NDVI promedio.\n- Integración con clima (promedios 10 días previos por fecha S2).")

# Clases
pdf.add_section_title("3. CLASES IDENTIFICADAS")
for k,v in LABELS_DICT.items():
    pdf.cell(0,6,f"{k}: {v}", ln=True)

# Análisis temporal
pdf.add_section_title("4. ANÁLISIS TEMPORAL DE ÍNDICES")
pdf.add_image_with_caption(serie_temporal_png, "Evolución temporal de índices de vegetación")

# Evolución de áreas
pdf.add_section_title("5. EVOLUCIÓN DE ÁREAS")
pdf.add_image_with_caption(evolucion_png, "Evolución del área por clase a lo largo del tiempo")

# Estadísticas por clase
pdf.add_section_title("6. ESTADÍSTICAS POR CLASE")
if os.path.exists(estadisticas_csv):
    df_stats = pd.read_csv(estadisticas_csv)
    # Mostrar tabla breve
    pdf.set_font("Arial","B",9)
    headers = ["Clase","Promedio(ha)","Mín","Máx","Std"]
    widths = [62,28,25,25,20]
    for w,h in zip(widths,headers): pdf.cell(w,7,h,1,0,'C')
    pdf.ln(7); pdf.set_font("Arial","",8)
    for _,r in df_stats.iterrows():
        pdf.cell(widths[0],6,str(r['Clase']),1)
        pdf.cell(widths[1],6,f"{r['Area_promedio_ha']:.1f}",1,0,'R')
        pdf.cell(widths[2],6,f"{r['Area_min_ha']:.1f}",1,0,'R')
        pdf.cell(widths[3],6,f"{r['Area_max_ha']:.1f}",1,0,'R')
        pdf.cell(widths[4],6,f"{r['Desviacion_std_ha']:.1f}",1,1,'R')
else:
    pdf.cell(0,6,"No hay estadísticas (ejecutá el script 4).", ln=True)

# Clima vs NDVI
pdf.add_section_title("7. CLIMA VS NDVI")
pdf.add_image_with_caption(clima_grafico, "NDVI vs Precipitación y Temperatura mínima (10 días previos)")

# Correlaciones
pdf.add_section_title("8. MATRIZ DE CORRELACIÓN")
pdf.add_image_with_caption(matriz_correlacion, "Matriz de correlación NDVI - Clima")

# Regresiones
pdf.add_section_title("9. ANÁLISIS DE REGRESIÓN")
pdf.add_image_with_caption(analisis_regresion, "Regresiones simples y múltiples")

# Timelapse
pdf.add_section_title("10. TIMELAPSE")
if os.path.exists(timelapse_gif):
    pdf.add_image_with_caption(timelapse_gif, "Vista estática del timelapse (ver GIF/MP4 en carpeta)")
else:
    pdf.cell(0,6, "Timelapse no disponible (ejecutá script 5).", ln=True)

# Conclusiones (básicas)
pdf.add_section_title("11. CONCLUSIONES Y RECOMENDACIONES")
corr_ndvi_t = "N/A"; corr_ndvi_p = "N/A"
if os.path.exists(dataset_integrado):
    df_int = pd.read_csv(dataset_integrado)
    if set(['NDVI','Tmedia','Precip']).issubset(df_int.columns):
        corr_ndvi_t = f"{df_int['NDVI'].corr(df_int['Tmedia']):.3f}"
        corr_ndvi_p = f"{df_int['NDVI'].corr(df_int['Precip']):.3f}"
pdf.set_font("Arial","",11)
pdf.multi_cell(0,6, f"- Correlación NDVI-Temperatura media: {corr_ndvi_t}\n- Correlación NDVI-Precipitación: {corr_ndvi_p}\n- Recomendación: validar con campo y ajustar umbrales por variedad y fecha de siembra.")

nombre_pdf = f"Informe_Monitoreo_Mani_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
ruta_pdf = os.path.join(pdf_path, nombre_pdf)
try:
    pdf.output(ruta_pdf)
    print(f"[OK] Informe generado: {ruta_pdf}")
except Exception as e:
    print("[ERROR] No se pudo guardar el PDF:", e)
