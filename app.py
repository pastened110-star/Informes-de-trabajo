import streamlit as st
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime
import os

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Gestor de Informes Técnicos", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #004a99; color: white; font-weight: bold; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

if 'clientes' not in st.session_state:
    st.session_state['clientes'] = pd.DataFrame(columns=['Nombre', 'RUT', 'Direccion'])
if 'perfil' not in st.session_state:
    st.session_state['perfil'] = {"empresa": "Tecnoelec SpA", "rut": "", "logo": None}
if 'conectado' not in st.session_state:
    st.session_state['conectado'] = False

# --- 2. CLASE PDF PERSONALIZADA ---
class PDF_Pro(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def crear_recuadro(self, titulo, contenido):
        self.set_fill_color(240, 240, 240)
        self.set_font("Arial", 'B', 10)
        self.cell(0, 8, f" {titulo}", 1, 1, 'L', True)
        self.set_font("Arial", '', 9)
        self.multi_cell(0, 6, contenido, 1)
        self.ln(5)

def generar_pdf_hibrido(titulo_doc, perfil, cliente, proy, datos, fotos):
    pdf = PDF_Pro()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1: PORTADA TÉCNICA ---
    pdf.add_page()
    if perfil['logo']:
        try:
            img = Image.open(perfil['logo'])
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.save("temp_logo.jpg", "JPEG")
            pdf.image("temp_logo.jpg", 10, 10, 35)
        except: pass

    pdf.ln(40)
    pdf.set_font('Arial', 'B', 22)
    pdf.multi_cell(0, 15, proy.upper(), 0, 'C')
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, titulo_doc.upper(), 0, 1, 'C')
    
    pdf.ln(30)
    # Tabla Control de Versiones (Estilo Word)
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(20, 8, "REV", 1, 0, 'C', True)
    pdf.cell(30, 8, "FECHA", 1, 0, 'C', True)
    pdf.cell(50, 8, "PREPARA", 1, 0, 'C', True)
    pdf.cell(50, 8, "REVISA", 1, 0, 'C', True)
    pdf.cell(40, 8, "APRUEBA", 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 8)
    pdf.cell(20, 8, "01", 1, 0, 'C')
    pdf.cell(30, 8, str(datetime.date.today()), 1, 0, 'C')
    pdf.cell(50, 8, datos['encargado'], 1, 0, 'C')
    pdf.cell(50, 8, perfil['empresa'], 1, 0, 'C')
    pdf.cell(40, 8, "CLIENTE", 1, 1, 'C')

    # --- PÁGINA 2: CONTENIDO TÉCNICO CON RECUADROS ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "DESARROLLO DEL INFORME", 0, 1, 'L')
    pdf.ln(5)

    # I. Información General
    info_gen = f"Cliente: {cliente['Nombre']}\nRUT: {cliente['RUT']}\nUbicación: {cliente['Direccion']}\nReferencia: {proy}"
    pdf.crear_recuadro("I. INFORMACION GENERAL", info_gen)

    # II. Gestión y Personal
    info_gestion = f"Inicio: {datos['f_inicio']} | Término: {datos['f_termino']}\nResponsable: {datos['encargado']} ({datos['cargo']})\nEquipo: {datos['equipo']}"
    pdf.crear_recuadro("II. GESTION DE OBRA Y PERSONAL", info_gestion)

    # III. Detalle de Trabajos
    pdf.crear_recuadro("III. DESCRIPCION DE ACTIVIDADES", datos['detalle'])

    # IV. Conclusiones
    pdf.crear_recuadro("IV. CONCLUSIONES Y RECOMENDACIONES", datos['conclu'])

    # Firmas al final de la sección técnica
    pdf.ln(20)
    yf = pdf.get_y()
    pdf.line(30, yf, 80, yf); pdf.line(130, yf, 180, yf)
    pdf.set_y(yf + 2)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_x(30); pdf.cell(50, 5, "Firma Encargado", 0, 0, 'C')
    pdf.set_x(130); pdf.cell(50, 5, "V.B. Cliente", 0, 1, 'C')

    # --- PÁGINA 3: ANEXO FOTOGRÁFICO ---
    if fotos:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "ANEXO: REGISTRO FOTOGRAFICO", 0, 1, 'L')
        
        y_img = 30
        for i, foto in enumerate(fotos):
            if i > 0 and i % 2 == 0:
                pdf.add_page()
                y_img = 30
            
            try:
                img = Image.open(foto)
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                img_path = f"temp_{i}.jpg"
                img.save(img_path, "JPEG")
                
                pdf.image(img_path, 15, y_img, 180, 95)
                pdf.set_xy(15, y_img + 97)
                pdf.set_font('Arial', 'I', 9)
                pdf.cell(180, 8, f"Imagen {i+1}: Registro de actividad en terreno.", 1, 1, 'C')
                y_img += 115
            except: pass

    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. INTERFAZ STREAMLIT ---
if not st.session_state['conectado']:
    st.title("Sistema de Gestión de Informes Técnicos")
    t1, t2 = st.tabs(["Acceso", "Registro"])
    with t1:
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Ingresar"):
            if u == "admin" and p == "tecnoelec2026":
                st.session_state['conectado'] = True
                st.rerun()
    with t2: st.info("Módulo de registro en mantenimiento.")
else:
    st.sidebar.title("Menú")
    op = st.sidebar.radio("", ["Perfil", "Clientes", "Generar Informe", "Salir"])

    if op == "Perfil":
        st.header("Perfil de Empresa")
        st.session_state['perfil']['empresa'] = st.text_input("Nombre Empresa", value=st.session_state['perfil']['empresa'])
        st.session_state['perfil']['logo'] = st.file_uploader("Subir Logo", type=["png", "jpg"])

    elif op == "Clientes":
        st.header("Base de Datos de Clientes")
        with st.form("c"):
            n = st.text_input("Nombre"); r = st.text_input("RUT"); d = st.text_input("Dirección")
            if st.form_submit_button("Guardar"):
                st.session_state['clientes'] = pd.concat([st.session_state['clientes'], pd.DataFrame([[n,r,d]], columns=['Nombre','RUT','Direccion'])], ignore_index=True)

    elif op == "Generar Informe":
        st.header("Crear Nuevo Documento")
        col1, col2 = st.columns(2)
        with col1:
            tit = st.text_input("Tipo de Informe", value="Informe de Mantenimiento")
            if not st.session_state['clientes'].empty:
                c_sel = st.selectbox("Seleccionar Cliente", st.session_state['clientes']['Nombre'])
                c_data = st.session_state['clientes'][st.session_state['clientes']['Nombre'] == c_sel].iloc[0]
            else: st.warning("Cree un cliente primero"); st.stop()
        with col2:
            proy = st.text_input("Proyecto (Ej: MANTENCION UPS PISO 5)")
            f_i = st.date_input("Fecha Inicio")
        
        with st.expander("Gestión y Personal", expanded=True):
            col3, col4 = st.columns(2)
            with col3: f_t = st.date_input("Fecha Término"); t_a = st.text_input("Tiempo Ejecución")
            with col4: enc = st.text_input("Encargado"); car = st.text_input("Cargo")
            equ = st.text_area("Equipo de apoyo")

        st.subheader("Contenido Técnico")
        res = st.text_input("Resumen ejecutivo")
        det = st.text_area("Descripción detallada de actividades", height=150)
        con = st.text_area("Conclusiones y Recomendaciones")
        fotos = st.file_uploader("Cargar Registro Fotográfico", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

        if st.button("🚀 GENERAR INFORME FINAL"):
            d_obra = {"f_inicio": f_i, "f_termino": f_t, "tiempo": t_a, "encargado": enc, "cargo": car, "equipo": equ, "resumen": res, "detalle": det, "conclu": con}
            pdf_out = generar_pdf_hibrido(tit, st.session_state['perfil'], c_data, proy, d_obra, fotos)
            st.download_button("💾 Descargar PDF", data=pdf_out, file_name=f"Reporte_{c_sel}.pdf")

    elif op == "Salir":
        st.session_state['conectado'] = False
        st.rerun()
