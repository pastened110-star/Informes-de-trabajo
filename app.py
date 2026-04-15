import streamlit as st
from fpdf import FPDF
from datetime import datetime
import pandas as pd
from PIL import Image
import io

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Generador de Informes Pro", layout="wide")

# Inicializar bases de datos temporales (Session State)
if 'clientes' not in st.session_state:
    st.session_state['clientes'] = pd.DataFrame(columns=['Nombre', 'RUT', 'Direccion'])
if 'perfil' not in st.session_state:
    st.session_state['perfil'] = {"empresa": "Mi Empresa", "rut": "", "logo": None}

# --- FUNCIÓN PDF ---
def generar_pdf(titulo_doc, perfil, cliente, proyecto, fecha, hallazgos, conclusiones, logo_img):
    pdf = FPDF()
    pdf.add_page()
    
    # Logo si existe
    if logo_img:
        # Guardar imagen temporalmente para el PDF
        img = Image.open(logo_img)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        pdf.image(img_byte_arr, 10, 8, 33)
        pdf.ln(20)

    # Título Dinámico
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, titulo_doc.upper(), 0, 1, 'C')
    pdf.ln(5)

    # Datos Emisor
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 7, f"EMISOR: {perfil['empresa']} | RUT: {perfil['rut']}", ln=True)
    pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
    pdf.ln(10)

    # Datos Cliente Seleccionado
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "INFORMACIÓN DEL CLIENTE", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 7, f"Cliente: {cliente['Nombre']}", ln=True)
    pdf.cell(0, 7, f"RUT: {cliente['RUT']}", ln=True)
    pdf.cell(0, 7, f"Dirección: {cliente['Direccion']}", ln=True)
    pdf.ln(5)

    # Contenido
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "DETALLES DEL TRABAJO", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 7, hallazgos)
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- INTERFAZ DE USUARIO ---
st.sidebar.title("🛠️ Panel de Control")
menu = st.sidebar.radio("Ir a:", ["🏢 Mi Perfil", "👥 Mis Clientes", "📝 Crear Informe"])

# SECCIÓN: MI PERFIL
if menu == "🏢 Mi Perfil":
    st.header("Configura tu Identidad Visual")
    st.session_state['perfil']['empresa'] = st.text_input("Nombre de tu Empresa", value=st.session_state['perfil']['empresa'])
    st.session_state['perfil']['rut'] = st.text_input("Tu RUT comercial", value=st.session_state['perfil']['rut'])
    archivo_logo = st.file_uploader("Sube tu Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if archivo_logo:
        st.session_state['perfil']['logo'] = archivo_logo
        st.image(archivo_logo, width=150)
    st.success("Los datos se aplicarán a todos tus informes.")

# SECCIÓN: MIS CLIENTES
elif menu == "👥 Mis Clientes":
    st.header("Administración de Clientes")
    with st.form("nuevo_cliente"):
        n = st.text_input("Nombre del Cliente (ej: Clínica Bradford Hill)")
        r = st.text_input("RUT del Cliente")
        d = st.text_input("Dirección")
        if st.form_submit_button("Guardar Cliente"):
            nuevo = pd.DataFrame([[n, r, d]], columns=['Nombre', 'RUT', 'Direccion'])
            st.session_state['clientes'] = pd.concat([st.session_state['clientes'], nuevo], ignore_index=True)
            st.success("Cliente guardado en la lista.")
    
    st.write("Tu lista de clientes actual:")
    st.table(st.session_state['clientes'])

# SECCIÓN: CREAR INFORME
elif menu == "📝 Crear Informe":
    st.header("Generar Nuevo Documento")
    
    col1, col2 = st.columns(2)
    with col1:
        titulo_personalizado = st.text_input("Título del Informe", value="Informe de Obra")
        # Selector de cliente desde la base de datos interna
        if not st.session_state['clientes'].empty:
            cliente_nom = st.selectbox("Selecciona el Cliente", st.session_state['clientes']['Nombre'])
            cliente_data = st.session_state['clientes'][st.session_state['clientes']['Nombre'] == cliente_nom].iloc[0]
        else:
            st.warning("Primero debes agregar un cliente en la sección 'Mis Clientes'.")
            st.stop()
    
    with col2:
        fecha = st.date_input("Fecha del servicio")
        proyecto_nom = st.text_input("Nombre del Proyecto/Referencia")

    hallazgos = st.text_area("Descripción de los trabajos realizados")
    
    if st.button("🚀 Previsualizar y Descargar PDF"):
        pdf_bytes = generar_pdf(
            titulo_personalizado, 
            st.session_state['perfil'], 
            cliente_data, 
            proyecto_nom, 
            fecha, 
            hallazgos, 
            "", 
            st.session_state['perfil']['logo']
        )
        st.download_button("⬇️ Descargar Informe", data=pdf_bytes, file_name=f"{titulo_personalizado}.pdf")
