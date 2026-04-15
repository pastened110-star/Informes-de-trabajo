import streamlit as st
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import pandas as pd
from PIL import Image
import os
import datetime
import json

# --- 1. CONFIGURACIÓN Y DISEÑO DE FONDO ---
st.set_page_config(page_title="Tecnoelec Pro Cloud", layout="wide")

# CSS para fondo con degradado y estilo moderno
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .main-box {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0px 10px 25px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #004a99;
        color: white;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #003366;
        border: 1px solid #004a99;
    }
    </style>
    """, unsafe_allow_html=True)

# Conexión persistente a la nube
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_global = conn.read(ttl=0)
except:
    df_global = pd.DataFrame(columns=['UsuarioID', 'Nombre', 'RUT', 'Direccion', 'Contacto'])

# --- 2. GESTIÓN DE SESIÓN ---
if 'conectado' not in st.session_state:
    st.session_state['conectado'] = False

# --- 3. MOTOR PDF PROFESIONAL ---
class PDF_Pro(FPDF):
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')
    def crear_seccion_titulo(self, titulo):
        if self.get_y() > 250: self.add_page()
        self.set_fill_color(230, 230, 230); self.set_font("Arial", 'B', 10)
        txt = titulo.encode('latin-1', 'replace').decode('latin-1')
        self.cell(0, 8, f" {txt}", 1, 1, 'L', True)

def limpiar(t):
    if not t: return ""
    cambios = {'ñ':'n','Ñ':'N','á':'a','é':'e','í':'i','ó':'o','ú':'u','°':' deg '}
    for o, r in cambios.items(): t = t.replace(o, r)
    return t.encode('latin-1', 'ignore').decode('latin-1')

def generar_pdf(titulo, perfil, cliente, proy, datos, fotos, img_portada, logo_p):
    pdf = PDF_Pro()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    if os.path.exists(logo_p): pdf.image(logo_p, 10, 10, 30)
    pdf.set_y(45); pdf.set_font('Arial', 'B', 22); pdf.multi_cell(0, 12, limpiar(proy).upper(), 0, 'C')
    pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, limpiar(titulo).upper(), 0, 1, 'C')
    if img_portada:
        try:
            img_p = Image.open(img_portada).convert("RGB"); img_p.save("temp_p.jpg", "JPEG")
            pdf.image("temp_p.jpg", x=45, y=85, w=120, h=90) 
        except: pass
    pdf.set_y(205)
    pdf.set_fill_color(200, 220, 255); pdf.set_font('Arial', 'B', 8)
    pdf.cell(20, 8, "REV", 1, 0, 'C', True); pdf.cell(30, 8, "FECHA", 1, 0, 'C', True)
    pdf.cell(50, 8, "PREPARA", 1, 0, 'C', True); pdf.cell(50, 8, "REVISA", 1, 0, 'C', True); pdf.cell(40, 8, "APRUEBA", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 8); pdf.cell(20, 8, "01", 1, 0, 'C'); pdf.cell(30, 8, str(datetime.date.today()), 1, 0, 'C')
    pdf.cell(50, 8, limpiar(datos['encargado']), 1, 0, 'C'); pdf.cell(50, 8, limpiar(perfil['empresa']), 1, 0, 'C'); pdf.cell(40, 8, "CLIENTE", 1, 1, 'C')
    pdf.add_page(); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "DESARROLLO TECNICO", 0, 1, 'L'); pdf.ln(5)
    pdf.crear_seccion_titulo("I. INFORMACION GENERAL")
    pdf.set_font("Arial", '', 9); pdf.cell(95, 7, f" Cliente: {limpiar(cliente['Nombre'])}", 1); pdf.cell(95, 7, f" Contacto: {limpiar(cliente['Contacto'])}", 1, 1)
    pdf.cell(0, 7, f" Direccion: {limpiar(cliente['Direccion'])}", 1, 1); pdf.ln(5)
    pdf.crear_seccion_titulo("II. GESTION DE OBRA")
    pdf.set_font("Arial", 'B', 9); pdf.cell(95, 7, " FECHA DE INICIO", 1, 0); pdf.cell(95, 7, " FECHA DE TERMINO", 1, 1)
    pdf.set_font("Arial", '', 9); pdf.cell(95, 7, f" {datos['f_inicio']}", 1, 0); pdf.cell(95, 7, f" {datos['f_termino']}", 1, 1)
    pdf.set_font("Arial", 'B', 9); pdf.cell(95, 7, " RESPONSABLE TECNICO", 1, 0); pdf.cell(95, 7, " CARGO", 1, 1)
    pdf.set_font("Arial", '', 9); pdf.cell(95, 7, f" {limpiar(datos['encargado'])}", 1, 0); pdf.cell(95, 7, f" {limpiar(datos['cargo'])}", 1, 1)
    pdf.set_font("Arial", 'B', 9); pdf.cell(0, 7, " PERSONAL DE APOYO (EQUIPO TRABAJO)", 1, 1)
    pdf.set_font("Arial", '', 9); pdf.multi_cell(0, 7, f" {limpiar(datos['equipo'])}", 1); pdf.ln(5)
    pdf.crear_seccion_titulo("III. DESCRIPCION ACTIVIDADES"); pdf.multi_cell(0, 6, f" {limpiar(datos['detalle'])}", 1); pdf.ln(5)
    pdf.crear_seccion_titulo("IV. CONCLUSIONES"); pdf.multi_cell(0, 6, f" {limpiar(datos['conclu'])}", 1)
    if fotos:
        pdf.add_page(); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "REGISTRO FOTOGRAFICO", 0, 1, 'L')
        for i, f in enumerate(fotos):
            try:
                img = Image.open(f).convert("RGB"); img.save(f"t{i}.jpg", "JPEG")
                if pdf.get_y() > 180: pdf.add_page()
                pdf.image(f"t{i}.jpg", 15, pdf.get_y(), 180, 95); pdf.ln(105)
            except: pass
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. INTERFAZ DE ACCESO ---
if not st.session_state['conectado']:
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    st.title(" Informes de trabajo")
    st.subheader("Acceso al Sistema")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Ingresar al Tablero"):
        if u == "admin" and p == "tecnoelec2026":
            st.session_state['conectado'] = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Definimos carpetas base (Para Tecnoelec)
    user_folder = "data_admin"
    if not os.path.exists(user_folder): os.makedirs(user_folder)
    logo_p = os.path.join(user_folder, "logo.jpg")
    perf_p = os.path.join(user_folder, "perfil.json")

    st.sidebar.title("Menú de Navegación")
    op = st.sidebar.radio("", ["Perfil Empresa", "Clientes Cloud", "Nuevo Informe", "Salir"])

    if op == "Salir":
        st.session_state['conectado'] = False; st.rerun()

    elif op == "Perfil Empresa":
        st.header("Marca Corporativa")
        # Carga automática de datos guardados
        if os.path.exists(perf_p):
            with open(perf_p, "r") as f: p_data = json.load(f)
        else: p_data = {"empresa": "TECNOELEC SpA", "rut": ""}
        
        emp = st.text_input("Empresa", value=p_data['empresa'])
        rut = st.text_input("RUT", value=p_data['rut'])
        log = st.file_uploader("Logo", type=["png","jpg"])
        if st.button("Guardar Cambios"):
            with open(perf_p, "w") as f: json.dump({"empresa": emp, "rut": rut}, f)
            if log: Image.open(log).convert("RGB").save(logo_p)
            st.success("Perfil Guardado")

    elif op == "Clientes Cloud":
        st.header("Base de Datos en Google Sheets")
        with st.form("fc"):
            n = st.text_input("Nombre"); r = st.text_input("RUT"); d = st.text_input("Dirección"); c = st.text_input("Contacto")
            if st.form_submit_button("Guardar en la Nube"):
                nf = pd.DataFrame([[n, r, d, c]], columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])
                conn.update(data=pd.concat([df_global, nf], ignore_index=True))
                st.success("Guardado permanente"); st.rerun()
        st.dataframe(df_global, use_container_width=True)

    elif op == "Nuevo Informe":
        st.header("Generar Documento Técnico")
        if df_global.empty: st.warning("Agrega un cliente primero"); st.stop()
        
        c_sel = st.selectbox("Cliente", df_global['Nombre'])
        c_dat = df_global[df_global['Nombre'] == c_sel].iloc[0]
        proy = st.text_input("Nombre Proyecto", value="PROYECTO ELECTRICO")
        img_p = st.file_uploader("Imagen Portada", type=["jpg","png"])
        
        with st.expander("Gestión de Obra", expanded=True):
            col1, col2 = st.columns(2)
            with col1: f_i = st.date_input("Inicio"); enc = st.text_input("Responsable", value="David Alberto Pastene Moyano")
            with col2: f_t = st.date_input("Termino"); car = st.text_input("Cargo", value="Instalador Electrico Clase D")
            equ = st.text_area("Equipo de apoyo")
            
        det = st.text_area("Descripción Actividades", height=200)
        con = st.text_area("Conclusiones")
        fotos = st.file_uploader("Anexo Fotos", accept_multiple_files=True)
        
        if st.button("🚀 GENERAR PDF"):
            if os.path.exists(perf_p):
                with open(perf_p, "r") as f: p_data = json.load(f)
            else: p_data = {"empresa": "TECNOELEC SpA", "rut": ""}
            d_obra = {"f_inicio": str(f_i), "f_termino": str(f_ter), "encargado": enc, "cargo": car, "equipo": equ, "detalle": det, "conclu": con}
            pdf_out = generar_pdf("Informe de Mantenimiento", p_data, c_dat, proy, d_obra, fotos, img_p, logo_p)
            st.download_button("Descargar", data=pdf_out, file_name=f"{proy}.pdf")
