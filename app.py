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
    st.header("📄 Generar Nuevo Documento Técnico")
    
    # FILA 1: TÍTULO Y CLIENTE
    col1, col2 = st.columns(2)
    with col1:
        titulo_personalizado = st.text_input("Tipo de Documento", value="Informe de Obra")
        if not st.session_state['clientes'].empty:
            cliente_nom = st.selectbox("Seleccionar Cliente", st.session_state['clientes']['Nombre'])
            cliente_data = st.session_state['clientes'][st.session_state['clientes']['Nombre'] == cliente_nom].iloc[0]
        else:
            st.warning("⚠️ Agrega un cliente en 'Mis Clientes' primero.")
            st.stop()
    with col2:
        proyecto_nom = st.text_input("Nombre del Proyecto / OT")

    # FILA 2: FECHAS Y TIEMPOS
    st.subheader("🗓️ Plazos y Tiempos")
    c1, c2, c3 = st.columns(3)
    with c1:
        f_inicio = st.date_input("Fecha de Inicio")
    with c2:
        f_termino = st.date_input("Fecha de Término")
    with c3:
        tiempo_aprox = st.text_input("Tiempo aprox. de trabajo", placeholder="Ej: 5 días / 40 horas")

    # FILA 3: PERSONAL CARGO
    st.subheader("👷 Personal Responsable")
    p1, p2 = st.columns(2)
    with p1:
        encargado = st.text_input("Persona Encargada")
    with p2:
        cargo_encargado = st.text_input("Cargo del Encargado")
    
    equipo_trabajo = st.text_area("Equipo de Trabajo", placeholder="Ej: Juan Pérez (Eléctrico), Luis Mora (Ayudante)...")

    # FILA 4: CONTENIDO TÉCNICO
    st.subheader("🖋️ Desarrollo del Trabajo")
    descripcion_breve = st.text_input("Breve descripción del trabajo (Resumen)")
    trabajo_realizado = st.text_area("Trabajo Realizado (Detalle paso a paso)", height=150)
    conclusiones = st.text_area("Conclusiones Finales")

    # BOTÓN DE GENERACIÓN
    st.divider()
    if st.button("🔥 Generar Informe Completo"):
        # Aquí llamaremos a la función PDF con todos estos nuevos datos
        datos_obra = {
            "f_inicio": f_inicio, "f_termino": f_termino, "tiempo": tiempo_aprox,
            "encargado": encargado, "cargo": cargo_encargado, "equipo": equipo_trabajo,
            "resumen": descripcion_breve, "detalle": trabajo_realizado, "conclu": conclusiones
        }
        pdf_bytes = generar_pdf_avanzado(titulo_personalizado, st.session_state['perfil'], cliente_data, proyecto_nom, datos_obra, st.session_state['perfil']['logo'])
        st.download_button("💾 Descargar PDF", data=pdf_bytes, file_name=f"Informe_{cliente_nom}.pdf")
