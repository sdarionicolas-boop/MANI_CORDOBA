import streamlit as st

if 'data_uploaded' not in st.session_state:
    st.session_state.data_uploaded = False
if 'processed' not in st.session_state:
    st.session_state.processed = False

def show():
    st.title("🌱 Monitor de Cultivos de Maní")
    st.markdown("### Córdoba, Argentina")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📤")
        st.markdown("**Subir Datos**")
        st.caption("Cargue sus imágenes satelitales y datos de cultivos")
    
    with col2:
        st.success("📊")
        st.markdown("**Resultados**")
        st.caption("Vea áreas cultivadas y clasificaciones")
    
    with col3:
        st.warning("📋")
        st.markdown("**Informe**")
        st.caption("Genere reportes PDF personalizados")
    
    st.markdown("---")
    
    st.subheader("📋 Estado del Proyecto")
    
    if st.session_state.get('data_uploaded'):
        st.success("✅ Datos subidos correctamente")
    else:
        st.warning("⚠️ No hay datos subidos")
    
    st.markdown("""
    ---
    **Comenzar:** Vaya a **Subir Datos** en el menú lateral para cargar sus archivos.
    """)