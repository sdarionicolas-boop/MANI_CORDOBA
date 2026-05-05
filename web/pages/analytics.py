import streamlit as st
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def show():
    st.title("📈 Análisis")
    st.markdown("Análisis temporal y gráfico de la evolución del cultivo")
    
    st.subheader("📉 Series de Tiempo NDVI")
    
    stats_dir = os.path.join(BASE_DIR, "resultados", "estadisticas")
    
    if os.path.exists(stats_dir):
        csv_files = [f for f in os.listdir(stats_dir) if f.endswith('.csv')]
        
        if csv_files:
            selected = st.selectbox("Seleccionar serie", csv_files)
            df = pd.read_csv(os.path.join(stats_dir, selected))
            
            numeric_cols = df.select_dtypes(include=['float', 'int']).columns.tolist()
            
            if numeric_cols:
                col = st.selectbox("Seleccionar variable", numeric_cols)
                
                if 'fecha' in df.columns or 'date' in df.columns or 'time' in df.columns:
                    date_col = [c for c in df.columns if 'fecha' in c.lower() or 'date' in c.lower() or 'time' in c.lower()][0]
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    df = df.sort_values(date_col)
                    st.line_chart(df.set_index(date_col)[col])
                else:
                    st.line_chart(df[col])
            else:
                st.warning("No hay columnas numéricas para graficar")
        else:
            st.info("No hay datos disponibles")
    else:
        st.warning("No se encontró directorio de estadísticas")
    
    st.markdown("---")
    
    st.subheader("🛰️ Análisis de Imágenes")
    
    timelapse_dir = os.path.join(BASE_DIR, "resultados", "timelapse")
    if os.path.exists(timelapse_dir):
        images = [f for f in os.listdir(timelapse_dir) if f.endswith(('.png', '.jpg'))]
        
        if images:
            st.success(f"✅ {len(images)} imágenes disponibles")
            
            selected_img = st.selectbox("Seleccionar imagen", images)
            
            img_path = os.path.join(timelapse_dir, selected_img)
            st.image(img_path, caption=selected_img, use_container_width=True)
        else:
            st.info("No hay imágenes de timelapse")
    else:
        st.info("No hay timelapse disponible")