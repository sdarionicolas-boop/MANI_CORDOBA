import streamlit as st
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def show():
    st.title("📊 Resultados")
    st.markdown("Visualización de clasificaciones y áreas detectadas")
    
    stats_dir = os.path.join(BASE_DIR, "resultados", "estadisticas")
    mapas_dir = os.path.join(BASE_DIR, "resultados", "mapas")
    
    if not os.path.exists(stats_dir):
        st.warning("⚠️ No hay resultados disponibles. Ejecute primero el procesamiento.")
        return
    
    csv_files = [f for f in os.listdir(stats_dir) if f.endswith('.csv')]
    
    if csv_files:
        st.success(f"✅ {len(csv_files)} archivo(s) de resultados encontrado(s)")
        
        selected_file = st.selectbox("Seleccionar archivo", csv_files)
        
        if selected_file:
            df = pd.read_csv(os.path.join(stats_dir, selected_file))
            
            st.subheader("📈 Tabla de Resultados")
            st.dataframe(df, use_container_width=True)
            
            st.subheader("📊 Resumen Estadístico")
            if 'area_ha' in df.columns or 'Area' in df.columns:
                col1, col2, col3 = st.columns(3)
                
                area_col = 'area_ha' if 'area_ha' in df.columns else 'Area'
                
                with col1:
                    st.metric("Área Total", f"{df[area_col].sum():.2f} ha")
                with col2:
                    st.metric("Media", f"{df[area_col].mean():.2f} ha")
                with col3:
                    st.metric("Máximo", f"{df[area_col].max():.2f} ha")
            
            if 'clase' in df.columns or 'Class' in df.columns:
                st.subheader("🏷️ Distribución por Clase")
                class_col = 'clase' if 'clase' in df.columns else 'Class'
                st.bar_chart(df[class_col].value_counts())
    else:
        st.info("ℹ️ No hay archivos de estadísticas. Ejecute el procesamiento de datos.")
    
    st.markdown("---")
    st.caption("Los resultados se generan automáticamente al procesar las imágenes satelitales.")