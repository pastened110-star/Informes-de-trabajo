import streamlit as st
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime

# --- 1. CONFIGURACIÓN Y ESTILO VISUAL (CSS) ---
st.set_page_config(page_title="Gestión de Informes", layout="wide")

# Pintura y terminaciones (CSS personalizado)
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #004a99;
        color: white;
    }
    .stSidebar {
        background-color: #f0f2f6;
    }
    h1, h2 {
        color: #1c2b46;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialización de bases de datos temporales
if 'clientes' not in st.session_state:
    st.session_state['clientes'] = pd.DataFrame(columns=['Nombre', 'RUT', 'Direccion'])
if 'perfil' not in st.session_state:
    st.session_state['perfil'] = {"empresa": "Mi Empresa", "rut": "", "logo": None}
if 'conectado' not in st.session_state:
    st.session_state['conectado'] = False

# --- 2. MOTOR DEL PDF ---
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
    pdf.cell(0, 8, " I. INFORMACION GENERAL", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 9)
    pdf.cell(95, 7, f" Cliente: {cliente['Nombre']}", 1)
    pdf.cell(95, 7, f" Proyecto: {proyecto}", 1, 1)
    pdf.cell(95, 7, f" RUT Cliente: {cliente['RUT']}", 1)
    pdf.cell(95, 7, f" Ubicacion: {cliente['Direccion']}", 1, 1)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " II. GESTION DE OBRA Y PERSONAL", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 9)
    pdf.cell(63, 7, f" Inicio: {datos_obra['f_inicio']}", 1)
    pdf.cell(63, 7, f" Termino: {datos_obra['f_termino']}", 1)
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
    pdf.cell(0, 6, " Descripcion Detallada:", "LR", 1)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, f" {datos_obra['detalle']}", "LRB")
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " IV. CONCLUSIONES FINALIZACION", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, f" {datos_obra['conclu']}", 1)
    pdf.ln(25)
    y_firma = pdf.get_y()
    pdf.line(30, y_firma, 80, y_firma)
    pdf.line(130, y_firma, 180, y_firma)
    pdf.set_xy(30, y_firma + 2)
    pdf.cell(50, 5, "Firma Encargado", 0, 0, 'C')
    pdf.set_xy(130, y_firma + 2)
    pdf.cell(50, 5, "V.B. Cliente", 0, 0, 'C')
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. LOGICA DE ACCESO ---
if not st.session_state['conectado']:
    st.title("Sistema de Gestión de Informes Técnicos")
    col_login, _ = st.columns([1, 2])
    with col_login:
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión"):
            if u == "admin" and p == "tecnoelec2026":
                st.session_state['conectado'] = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
else:
    # --- 4. PANEL PRINCIPAL ---
    st.sidebar.markdown("### Navegación")
    m = st.sidebar.radio("", ["Mi Perfil", "Mis Clientes", "Crear Informe", "Cerrar Sesión"])

    if m == "Mi Perfil":
        st.header("Configuración de Perfil")
        st.session_state['perfil']['empresa'] = st.text_input("Razón Social / Nombre", value=st.session_state['perfil']['empresa'])
        st.session_state['perfil']['rut'] = st.text_input("RUT / Identificación", value=st.session_state['perfil']['rut'])
        logo = st.file_uploader("Subir Logotipo", type=["png", "jpg"])
        if logo: st.session_state['perfil']['logo'] = logo
        st.info("Estos datos aparecerán en el encabezado de todos tus informes.")

    elif m == "Mis Clientes":
        st.header("Base de Datos de Clientes")
        with st.form("form_cliente", clear_on_submit=True):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                nom = st.text_input("Nombre Cliente")
                rut = st.text_input("RUT Cliente")
            with col_c2:
                dir = st.text_input("Dirección")
            if st.form_submit_button("Guardar Cliente"):
                nuevo = pd.DataFrame([[nom, rut, dir]], columns=['Nombre', 'RUT', 'Direccion'])
                st.session_state['clientes'] = pd.concat([st.session_state['clientes'], nuevo], ignore_index=True)
                st.success("Cliente registrado con éxito.")
        
        if not st.session_state['clientes'].empty:
            st.dataframe(st.session_state['clientes'], use_container_width=True)

    elif m == "Crear Informe":
        st.header("Generar Nuevo Informe")
        
        # Bloque de Selección
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                tit = st.text_input("Tipo de Documento", value="Informe de Trabajo")
                if not st.session_state['clientes'].empty:
                    c_nom = st.selectbox("Seleccionar Cliente", st.session_state['clientes']['Nombre'])
                    c_data = st.session_state['clientes'][st.session_state['clientes']['Nombre'] == c_nom].iloc[0]
                else: 
                    st.warning("Debe registrar un cliente primero.")
                    st.stop()
            with col2:
                proy = st.text_input("Referencia / Proyecto")
                f_ini = st.date_input("Fecha Inicio", value=datetime.date.today())
        
        # Bloque de Gestión
        with st.expander("Detalles de Gestión y Personal", expanded=True):
            col3, col4 = st.columns(2)
            with col3:
                f_ter = st.date_input("Fecha Término", value=datetime.date.today())
                t_aprox = st.text_input("Tiempo de ejecución", placeholder="Ej: 3 días")
            with col4:
                enc = st.text_input("Responsable Técnico")
                car = st.text_input("Cargo")
            equipo = st.text_area("Personal de apoyo")

        # Bloque Técnico
        st.subheader("Desarrollo Técnico")
        resumen = st.text_input("Breve resumen del servicio")
        detalle = st.text_area("Descripción detallada de trabajos realizados", height=150)
        concl = st.text_area("Conclusiones y recomendaciones")

        if st.button("Generar Informe PDF"):
            datos_obra = {
                "f_inicio": f_ini, "f_termino": f_ter, "tiempo": t_aprox,
                "encargado": enc, "cargo": car, "equipo": equipo,
                "resumen": resumen, "detalle": detalle, "conclu": concl
            }
            pdf_bytes = generar_pdf_avanzado(tit, st.session_state['perfil'], c_data, proy, datos_obra, st.session_state['perfil']['logo'])
            st.download_button("Descargar Archivo PDF", data=pdf_bytes, file_name=f"Informe_{c_nom}.pdf")
    
    elif m == "Cerrar Sesión":
        st.session_state['conectado'] = False
        st.rerun()
