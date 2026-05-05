import streamlit as st
import os
import tempfile
import shutil
from datetime import datetime

def show():
    st.title("📤 Subir Datos")
    st.markdown("Cargue sus imágenes satelitales y datos para procesar")
    
    st.session_state.data_uploaded = False
    st.session_state.processed = False
    
    tab1, tab2 = st.tabs(["🛰️ Imágenes Satelitales", "📊 Datos Tabulares"])
    
    with tab1:
        st.markdown("### Cargar Imágenes TIFF/GeoTIFF")
        
        uploaded_files = st.file_uploader(
            "Seleccione imágenes satelitales",
            type=['tif', 'tiff'],
            accept_multiple_files=True,
            help="Formatos soportados: TIFF, GeoTIFF"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} imagen(es) seleccionada(s)")
            
            with st.expander("Ver nombres de archivos"):
                for f in uploaded_files:
                    st.text(f.name)
            
            if st.button("💾 Confirmar Imágenes", type="primary"):
                with st.spinner("Guardando imágenes..."):
                    save_dir = os.path.join(os.path.dirname(__file__), "..", "..", "datos", "raw", "upload")
                    os.makedirs(save_dir, exist_ok=True)
                    
                    for f in uploaded_files:
                        save_path = os.path.join(save_dir, f.name)
                        with open(save_path, "wb") as dest:
                            dest.write(f.getbuffer())
                    
                    st.session_state.image_dir = save_dir
                    st.success("✅ Imágenes guardadas correctamente")
    
    with tab2:
        st.markdown("### Cargar Datos Tabulares")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_file = st.file_uploader("CSV", type=['csv'])
        with col2:
            xlsx_file = st.file_uploader("Excel", type=['xlsx', 'xls'])
        
        if csv_file or xlsx_file:
            st.success("✅ Archivo(s) cargado(s)")
            
            if st.button("💾 Confirmar Datos Tabulares", type="primary"):
                with st.spinner("Guardando datos..."):
                    save_dir = os.path.join(os.path.dirname(__file__), "..", "..", "datos", "externos", "upload")
                    os.makedirs(save_dir, exist_ok=True)
                    
                    if csv_file:
                        save_path = os.path.join(save_dir, csv_file.name)
                        with open(save_path, "wb") as dest:
                            dest.write(csv_file.getbuffer())
                    
                    if xlsx_file:
                        save_path = os.path.join(save_dir, xlsx_file.name)
                        with open(save_path, "wb") as dest:
                            dest.write(xlsx_file.getbuffer())
                    
                    st.session_state.data_tabular = save_dir
                    st.success("✅ Datos tabulares guardados")
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("📌 **Nota:** Asegúrese de que las imágenes tengan nombres con fecha (ej: MANI_20230708.tif)")
    
    with col2:
        if st.button("🚀 Procesar Datos", type="primary", disabled=not (st.session_state.get('image_dir') or st.session_state.get('data_tabular'))):
            st.session_state.data_uploaded = True
            st.success("✅ Datos listos para procesamiento")
            st.rerun()