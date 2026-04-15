import streamlit as st
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime
import json
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Generador de Informes Técnicos", layout="wide")

# Estilo CSS para botones y visualización
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #004a99; color: white; font-weight: bold; }
    h1, h2 { color: #1c2b46; }
    </style>
    """, unsafe_allow_html=True)

if 'clientes' not in st.session_state:
    st.session_state['clientes'] = pd.DataFrame(columns=['Nombre', 'RUT', 'Direccion'])
if 'perfil' not in st.session_state:
    st.session_state['perfil'] = {"empresa": "Mi Empresa", "rut": "", "logo": None}
if 'conectado' not in st.session_state:
    st.session_state['conectado'] = False

# --- MOTOR DEL PDF AVANZADO ---
class PDF(FPDF):
    def header(self):
        if hasattr(self, 'perfil_data') and self.perfil_data['logo']:
            try:
                img = Image.open(self.perfil_data['logo'])
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                img.save("temp_logo.jpg", "JPEG")
                self.image("temp_logo.jpg", 10, 8, 25)
            except: pass
        self.set_font('Arial', 'B', 8)
        self.cell(0, 5, f"{self.perfil_data['empresa']}", 0, 1, 'R')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf_pro(titulo, perfil, cliente, proyecto, datos, fotos):
    pdf = PDF()
    pdf.perfil_data = perfil
    
    # --- PÁGINA 1: PORTADA ESTILO BRADFORD HILL ---
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font('Arial', 'B', 22)
    pdf.multi_cell(0, 15, proyecto.upper(), 0, 'C')
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 20, titulo.upper(), 0, 1, 'C')
    
    pdf.ln(30)
    # Cuadro de Control de Versiones
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(30, 8, "VERSION", 1, 0, 'C', True)
    pdf.cell(40, 8, "FECHA", 1, 0, 'C', True)
    pdf.cell(40, 8, "PREPARA", 1, 0, 'C', True)
    pdf.cell(40, 8, "REVISA", 1, 0, 'C', True)
    pdf.cell(40, 8, "APRUEBA", 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 9)
    pdf.cell(30, 8, "01", 1, 0, 'C')
    pdf.cell(40, 8, str(datetime.date.today()), 1, 0, 'C')
    pdf.cell(40, 8, datos['encargado'], 1, 0, 'C')
    pdf.cell(40, 8, perfil['empresa'], 1, 0, 'C')
    pdf.cell(40, 8, "CLIENTE", 1, 1, 'C')

    # --- PÁGINA 2: CONTENIDO TÉCNICO ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "1. DESCRIPCION GENERAL", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, f"Cliente: {cliente['Nombre']}\nRUT: {cliente['RUT']}\nUbicación: {cliente['Direccion']}\nResumen: {datos['resumen']}")
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "2. DETALLE DE ACTIVIDADES", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, datos['detalle'])
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "3. CONCLUSIONES", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, datos['conclu'])

    # --- PÁGINA 3+: INFORME FOTOGRÁFICO ---
    if fotos:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "4. REGISTRO FOTOGRAFICO", 0, 1, 'L')
        
        col = 0
        x_start = 10
        y_start = 30
        for i, foto in enumerate(fotos):
            try:
                img = Image.open(foto)
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                temp_f = f"temp_foto_{i}.jpg"
                img.save(temp_f, "JPEG")
                
                # Acomodar 2 fotos por página
                if i > 0 and i % 2 == 0:
                    pdf.add_page()
                    y_start = 30
                
                pdf.image(temp_f, x_start, y_start, 180, 90) # Foto grande
                pdf.set_xy(x_start, y_start + 92)
                pdf.set_font('Arial', 'I', 9)
                pdf.cell(0, 10, f"Imagen {i+1}: Registro de actividad en terreno.", 0, 1, 'C')
                y_start += 110
            except: pass

    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- LÓGICA DE INTERFAZ ---
if not st.session_state['conectado']:
    st.title("Sistema de Gestión de Informes Técnicos")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if u == "admin" and p == "tecnoelec2026":
            st.session_state['conectado'] = True
            st.rerun()
else:
    st.sidebar.title("Menú")
    m = st.sidebar.radio("", ["Mi Perfil", "Mis Clientes", "Crear Informe", "Cerrar Sesión"])

    if m == "Mi Perfil":
        st.header("Configuración de Perfil")
        st.session_state['perfil']['empresa'] = st.text_input("Empresa", value=st.session_state['perfil']['empresa'])
        st.session_state['perfil']['logo'] = st.file_uploader("Logo PNG/JPG", type=["png", "jpg", "jpeg"])

    elif m == "Mis Clientes":
        st.header("Base de Clientes")
        with st.form("c"):
            n = st.text_input("Nombre"); r = st.text_input("RUT"); d = st.text_input("Dirección")
            if st.form_submit_button("Guardar"):
                st.session_state['clientes'] = pd.concat([st.session_state['clientes'], pd.DataFrame([[n,r,d]], columns=['Nombre','RUT','Direccion'])], ignore_index=True)

    elif m == "Crear Informe":
        st.header("Nuevo Informe Estilo Profesional")
        c_sel = st.selectbox("Cliente", st.session_state['clientes']['Nombre']) if not st.session_state['clientes'].empty else st.error("Sin clientes")
        proy = st.text_input("Nombre del Proyecto (Ej: MANTENCION BRADFORD HILL)")
        
        with st.expander("Datos del Trabajo"):
            enc = st.text_input("Encargado Técnico")
            res = st.text_input("Resumen")
            det = st.text_area("Detalle de Actividades")
            con = st.text_area("Conclusiones")
        
        st.subheader("Evidencia Fotográfica")
        fotos_subidas = st.file_uploader("Sube una o más fotos", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

        if st.button("Generar Informe con Fotos"):
            c_data = st.session_state['clientes'][st.session_state['clientes']['Nombre'] == c_sel].iloc[0]
            datos = {"encargado": enc, "resumen": res, "detalle": det, "conclu": con}
            pdf_b = generar_pdf_pro("Informe de Mantenimiento", st.session_state['perfil'], c_data, proy, datos, fotos_subidas)
            st.download_button("💾 Descargar Informe Final", data=pdf_b, file_name=f"Informe_{proy}.pdf")

    elif m == "Cerrar Sesión":
        st.session_state['conectado'] = False
        st.rerun()
