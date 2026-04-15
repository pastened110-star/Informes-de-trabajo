import streamlit as st
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="Tecnoelec - Generador Pro", layout="wide")

if 'clientes' not in st.session_state:
    st.session_state['clientes'] = pd.DataFrame(columns=['Nombre', 'RUT', 'Direccion'])
if 'perfil' not in st.session_state:
    st.session_state['perfil'] = {"empresa": "Tecnoelec SpA", "rut": "", "logo": None}
if 'conectado' not in st.session_state:
    st.session_state['conectado'] = False

# --- 2. EL MOTOR DEL PDF (Lo que me pasaste) ---
def generar_pdf_avanzado(titulo_doc, perfil, cliente, proyecto, datos_obra, logo_img):
    pdf = FPDF()
    pdf.add_page()
    if logo_img:
        img = Image.open(logo_img)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        pdf.image(img_byte_arr, 10, 10, 30)
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(0, 10, titulo_doc.upper(), 0, 1, 'R')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"Empresa: {perfil['empresa']}", 0, 1, 'R')
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " I. INFORMACIÓN GENERAL", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 9)
    col_width = 95
    pdf.cell(col_width, 7, f" Cliente: {cliente['Nombre']}", 1)
    pdf.cell(col_width, 7, f" Proyecto: {proyecto}", 1, 1)
    pdf.cell(col_width, 7, f" RUT Cliente: {cliente['RUT']}", 1)
    pdf.cell(col_width, 7, f" Ubicación: {cliente['Direccion']}", 1, 1)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " II. GESTIÓN DE OBRA Y PERSONAL", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 9)
    pdf.cell(63, 7, f" Inicio: {datos_obra['f_inicio']}", 1)
    pdf.cell(63, 7, f" Término: {datos_obra['f_termino']}", 1)
    pdf.cell(64, 7, f" Tiempo Total: {datos_obra['tiempo']}", 1, 1)
    pdf.cell(95, 7, f" Responsable: {datos_obra['encargado']}", 1)
    pdf.cell(95, 7, f" Cargo: {datos_obra['cargo']}", 1, 1)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 6, " Equipo de Trabajo:", "LR", 1)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, f" {datos_obra['equipo']}", "LRB")
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " III. DETALLE DE LOS TRABAJOS", 1, 1, 'L', True)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 6, " Resumen del Servicio:", "LR", 1)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, f" {datos_obra['resumen']}", "LRB")
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 6, " Descripción Detallada:", "LR", 1)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, f" {datos_obra['detalle']}", "LRB")
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " IV. CONCLUSIONES FINALIZACIÓN", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, f" {datos_obra['conclu']}", 1)
    pdf.ln(25)
    y_firma = pdf.get_y()
    pdf.line(30, y_firma, 80, y_firma)
    pdf.line(130, y_firma, 180, y_firma)
    pdf.set_xy(30, y_firma + 2)
    pdf.cell(50, 5, "Firma Encargado", 0, 0, 'C')
    pdf.set_xy(130, y_firma + 2)
    pdf.cell(50, 5, "V°B° Cliente", 0, 0, 'C')
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. INTERFAZ Y LOGIC ---
if not st.session_state['conectado']:
    st.title("🔐 Tecnoelec - Acceso")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if u == "admin" and p == "tecnoelec2026":
            st.session_state['conectado'] = True
            st.rerun()
        else: st.error("Error")
else:
    st.sidebar.title("Panel de Control")
    m = st.sidebar.radio("Ir a:", ["🏢 Mi Perfil", "👥 Mis Clientes", "📝 Crear Informe", "🚪 Salir"])

    if m == "🏢 Mi Perfil":
        st.header("Configura tu Empresa")
        st.session_state['perfil']['empresa'] = st.text_input("Razón Social", value=st.session_state['perfil']['empresa'])
        st.session_state['perfil']['rut'] = st.text_input("RUT Empresa", value=st.session_state['perfil']['rut'])
        logo = st.file_uploader("Sube tu Logo", type=["png", "jpg"])
        if logo: st.session_state['perfil']['logo'] = logo
        
    elif m == "👥 Mis Clientes":
        st.header("Base de Datos de Clientes")
        with st.form("c"):
            nom = st.text_input("Nombre Cliente")
            rut = st.text_input("RUT")
            dir = st.text_input("Dirección")
            if st.form_submit_button("Guardar"):
                nuevo = pd.DataFrame([[nom, rut, dir]], columns=['Nombre', 'RUT', 'Direccion'])
                st.session_state['clientes'] = pd.concat([st.session_state['clientes'], nuevo], ignore_index=True)

    elif m == "📝 Crear Informe":
        st.header("Generar Nuevo Documento")
        col1, col2 = st.columns(2)
        with col1:
            tit = st.text_input("Tipo de Informe", value="Informe de mantenimiento")
            if not st.session_state['clientes'].empty:
                c_nom = st.selectbox("Selecciona el Cliente", st.session_state['clientes']['Nombre'])
                c_data = st.session_state['clientes'][st.session_state['clientes']['Nombre'] == c_nom].iloc[0]
            else: st.warning("Crea un cliente primero"); st.stop()
        with col2:
            proy = st.text_input("Proyecto")
            f_ini = st.date_input("Fecha Inicio")
        
        c3, c4 = st.columns(2)
        with c3:
            f_ter = st.date_input("Fecha Término")
            t_aprox = st.text_input("Tiempo de trabajo")
        with c4:
            enc = st.text_input("Encargado")
            car = st.text_input("Cargo")
        
        equipo = st.text_area("Equipo de trabajo")
        resumen = st.text_input("Breve descripción (Resumen)")
        detalle = st.text_area("Trabajo Realizado (Paso a paso)")
        concl = st.text_area("Conclusiones")

        if st.button("🔥 Generar Informe Completo"):
            datos_obra = {
                "f_inicio": f_ini, "f_termino": f_ter, "tiempo": t_aprox,
                "encargado": enc, "cargo": car, "equipo": equipo,
                "resumen": resumen, "detalle": detalle, "conclu": concl
            }
            pdf_bytes = generar_pdf_avanzado(tit, st.session_state['perfil'], c_data, proy, datos_obra, st.session_state['perfil']['logo'])
            st.download_button("💾 Descargar PDF", data=pdf_bytes, file_name=f"Informe_{c_nom}.pdf")
    
    elif m == "🚪 Salir":
        st.session_state['conectado'] = False
        st.rerun()
