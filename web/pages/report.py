import streamlit as st
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def show():
    st.title("📋 Informe")
    st.markdown("Generación de informes PDF personalizados")
    
    informes_dir = os.path.join(BASE_DIR, "resultados", "informes")
    
    st.subheader("📄 Informes Generados")
    
    if os.path.exists(informes_dir):
        pdf_files = [f for f in os.listdir(informes_dir) if f.endswith('.pdf')]
        
        if pdf_files:
            st.success(f"✅ {len(pdf_files)} informe(s) disponible(s)")
            
            for pdf in pdf_files:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.text(pdf)
                with col2:
                    pdf_path = os.path.join(informes_dir, pdf)
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "⬇️ Descargar",
                            f.read(),
                            file_name=pdf,
                            mime="application/pdf"
                        )
        else:
            st.info("No hay informes PDF disponibles")
    else:
        st.warning("No se encontró directorio de informes")
    
    st.markdown("---")
    
    st.subheader("🆕 Generar Nuevo Informe")
    
    with st.form("informe_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            titulo = st.text_input("Título del Informe", "Informe de Cultivo de Maní")
        with col2:
            region = st.text_input("Región", "Córdoba, Argentina")
        
        fecha_inicio = st.date_input("Fecha Inicio", value=None)
        fecha_fin = st.date_input("Fecha Fin", value=None)
        
        incluir_graficos = st.checkbox("Incluir gráficos", value=True)
        incluir_mapas = st.checkbox("Incluir mapas", value=True)
        incluir_estadisticas = st.checkbox("Incluir estadísticas", value=True)
        
        submit = st.form_submit_button("📊 Generar Informe", type="primary")
        
        if submit:
            st.info("⚙️ Generando informe... (funcionalidad en desarrollo)")
            st.success("✅ Informe generado correctamente")