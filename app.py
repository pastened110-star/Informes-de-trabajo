import streamlit as st
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime
import json
import os

# --- 1. CONFIGURACIÓN, PERSISTENCIA Y ESTILO ---
st.set_page_config(page_title="Gestión de Informes Técnicos", layout="wide")

USER_DB = "usuarios.json"

def cargar_usuarios():
    if os.path.exists(USER_DB):
        try:
            with open(USER_DB, "r") as f:
                return json.load(f)
        except:
            return {"admin": "tecnoelec2026"}
    return {"admin": "tecnoelec2026"}

def guardar_usuario(usuario, clave):
    usuarios = cargar_usuarios()
    usuarios[usuario] = clave
    with open(USER_DB, "w") as f:
        json.dump(usuarios, f)

# CSS para mejorar la estética
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #004a99; color: white; font-weight: bold; }
    .stSidebar { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    h1, h2, h3 { color: #1c2b46; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar estados de sesión
if 'conectado' not in st.session_state:
    st.session_state['conectado'] = False
if 'clientes' not in st.session_state:
    st.session_state['clientes'] = pd.DataFrame(columns=['Nombre', 'RUT', 'Direccion'])
if 'perfil' not in st.session_state:
    st.session_state['perfil'] = {"empresa": "Mi Empresa", "rut": "", "logo": None}

# --- 2. MOTOR DEL PDF (CORREGIDO PARA LOGOS) ---
def generar_pdf_avanzado(titulo_doc, perfil, cliente, proyecto, datos_obra, logo_img):
    pdf = FPDF()
    pdf.add_page()
    
    # Manejo del Logo con puente de memoria
    if logo_img:
        try:
            img = Image.open(logo_img)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            temp_path = "temp_logo.jpg"
            img.save(temp_path, "JPEG")
            pdf.image(temp_path, 10, 10, 30)
        except:
            pass
    
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(0, 10, titulo_doc.upper(), 0, 1, 'R')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"Empresa: {perfil['empresa']}", 0, 1, 'R')
    pdf.ln(10)

    # I. INFORMACIÓN GENERAL
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " I. INFORMACION GENERAL", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 9)
    pdf.cell(95, 7, f" Cliente: {cliente['Nombre']}", 1)
    pdf.cell(95, 7, f" Proyecto: {proyecto}", 1, 1)
    pdf.cell(95, 7, f" RUT Cliente: {cliente['RUT']}", 1)
    pdf.cell(95, 7, f" Ubicacion: {cliente['Direccion']}", 1, 1)
    pdf.ln(5)

    # II. GESTIÓN DE OBRA
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " II. GESTION DE OBRA Y PERSONAL", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 9)
    pdf.cell(63, 7, f" Inicio: {datos_obra['f_inicio']}", 1)
    pdf.cell(63, 7, f" Termino: {datos_obra['f_termino']}", 1)
    pdf.cell(64, 7, f" Tiempo: {datos_obra['tiempo']}", 1, 1)
    pdf.cell(95, 7, f" Responsable: {datos_obra['encargado']}", 1)
    pdf.cell(95, 7, f" Cargo: {datos_obra['cargo']}", 1, 1)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 6, " Equipo de Trabajo:", "LR", 1)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, f" {datos_obra['equipo']}", "LRB")
    pdf.ln(5)

    # III. DETALLE TÉCNICO
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " III. DETALLE DE LOS TRABAJOS", 1, 1, 'L', True)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 6, " Resumen:", "LR", 1)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, f" {datos_obra['resumen']}", "LRB")
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 6, " Detalle Paso a Paso:", "LR", 1)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, f" {datos_obra['detalle']}", "LRB")
    pdf.ln(5)

    # IV. CONCLUSIONES
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " IV. CONCLUSIONES Y RECOMENDACIONES", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, f" {datos_obra['conclu']}", 1)

    # FIRMAS
    pdf.ln(25)
    y_f = pdf.get_y()
    pdf.line(30, y_f, 80, y_f)
    pdf.line(130, y_f, 180, y_f)
    pdf.set_xy(30, y_f + 2)
    pdf.cell(50, 5, "Firma Encargado", 0, 0, 'C')
    pdf.set_xy(130, y_f + 2)
    pdf.cell(50, 5, "V.B. Cliente", 0, 0, 'C')

    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. ACCESO Y REGISTRO ---
if not st.session_state['conectado']:
    st.title("Sistema de Gestión de Informes Técnicos")
    t1, t2 = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
    
    with t1:
        u_l = st.text_input("Usuario", key="l_u")
        p_l = st.text_input("Contraseña", type="password", key="l_p")
        if st.button("Entrar", key="btn_l"):
            users = cargar_usuarios()
            if u_l in users and users[u_l] == p_l:
                st.session_state['conectado'] = True
                st.rerun()
            else: st.error("Datos incorrectos")
            
    with t2:
        u_r = st.text_input("Nuevo Usuario", key="r_u")
        p_r = st.text_input("Nueva Contraseña", type="password", key="r_p")
        p_c = st.text_input("Confirmar Contraseña", type="password", key="r_c")
        if st.button("Registrar Cuenta", key="btn_r"):
            if p_r == p_c and len(p_r) > 3:
                guardar_usuario(u_r, p_r)
                st.success("Cuenta creada. Ya puedes iniciar sesión.")
            else: st.error("Las contraseñas no coinciden o son muy cortas.")

# --- 4. PANEL DE CONTROL ---
else:
    st.sidebar.title("Navegación")
    m = st.sidebar.radio("", ["Mi Perfil", "Mis Clientes", "Crear Informe", "Cerrar Sesión"])

    if m == "Mi Perfil":
        st.header("Configuración de Perfil")
        st.session_state['perfil']['empresa'] = st.text_input("Nombre Empresa", value=st.session_state['perfil']['empresa'])
        st.session_state['perfil']['rut'] = st.text_input("RUT Empresa", value=st.session_state['perfil']['rut'])
        logo = st.file_uploader("Subir Logo", type=["png", "jpg", "jpeg"])
        if logo: st.session_state['perfil']['logo'] = logo
        st.info("Configura tu logo y datos una vez para que aparezcan en tus informes.")

    elif m == "Mis Clientes":
        st.header("Base de Datos de Clientes")
        with st.form("fc"):
            c1, c2 = st.columns(2)
            with c1: n = st.text_input("Nombre Cliente"); r = st.text_input("RUT")
            with c2: d = st.text_input("Dirección")
            if st.form_submit_button("Guardar Cliente"):
                st.session_state['clientes'] = pd.concat([st.session_state['clientes'], pd.DataFrame([[n,r,d]], columns=['Nombre','RUT','Direccion'])], ignore_index=True)
                st.success("Cliente guardado.")
        st.dataframe(st.session_state['clientes'], use_container_width=True)

    elif m == "Crear Informe":
        st.header("Generar Nuevo Informe")
        col1, col2 = st.columns(2)
        with col1:
            tit = st.text_input("Tipo de Documento", value="Informe de Trabajo")
            if not st.session_state['clientes'].empty:
                c_sel = st.selectbox("Cliente", st.session_state['clientes']['Nombre'])
                c_data = st.session_state['clientes'][st.session_state['clientes']['Nombre'] == c_sel].iloc[0]
            else: st.warning("Crea un cliente primero"); st.stop()
        with col2:
            proy = st.text_input("Proyecto / OT"); f_i = st.date_input("Inicio")
            
        with st.expander("Gestión de Obra", expanded=True):
            col3, col4 = st.columns(2)
            with col3: f_t = st.date_input("Término"); t_a = st.text_input("Tiempo aprox.")
            with col4: enc = st.text_input("Encargado"); car = st.text_input("Cargo")
            equ = st.text_area("Equipo de trabajo")
            
        res = st.text_input("Resumen breve")
        det = st.text_area("Detalle de trabajos", height=150)
        con = st.text_area("Conclusiones")

        if st.button("Generar PDF"):
            dat = {"f_inicio":f_i,"f_termino":f_t,"tiempo":t_a,"encargado":enc,"cargo":car,"equipo":equ,"resumen":res,"detalle":det,"conclu":con}
            pdf_bytes = generar_pdf_avanzado(tit, st.session_state['perfil'], c_data, proy, dat, st.session_state['perfil']['logo'])
            st.download_button("Descargar Informe", data=pdf_bytes, file_name=f"Informe_{c_sel}.pdf")

    elif m == "Cerrar Sesión":
        st.session_state['conectado'] = False
        st.rerun()
