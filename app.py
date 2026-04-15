import streamlit as st
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime
import json
import os

# --- 1. CONFIGURACIÓN Y ESTILO (MEJORADO PARA MÓVIL) ---
st.set_page_config(page_title="Tecnoelec Pro Cloud", layout="wide")

# CSS para fondo de obra y letras legibles
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(0, 20, 50, 0.85), rgba(0, 20, 50, 0.85)), 
        url("https://www.transparenttextures.com/patterns/blueprint.png");
        background-attachment: fixed;
        background-size: cover;
    }
    h1, h2, h3, p, span, label {
        color: white !important;
        text-shadow: 1px 1px 2px black;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #002b5c !important;
        border-radius: 5px !important;
    }
    .stTab {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px 10px 0 0;
        color: white !important;
    }
    [data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
    }
    .stButton>button {
        background-color: #ffcc00 !important;
        color: #002b5c !important;
        border: none !important;
        font-weight: bold !important;
        height: 3em !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def obtener_usuarios():
    try: return conn.read(worksheet="Usuarios", ttl=0)
    except: return pd.DataFrame(columns=['Usuario', 'Clave'])

def obtener_clientes():
    try:
        df_raw = conn.read(ttl=0)
        df = df_raw.iloc[:, :4].dropna(subset=[df_raw.columns[0]])
        df.columns = ['Nombre', 'RUT', 'Direccion', 'Contacto']
        return df
    except: return pd.DataFrame(columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])

PERFIL_FILE = "perfil_config.json"
LOGO_PATH = "logo_empresa.png"

def cargar_perfil():
    if os.path.exists(PERFIL_FILE):
        with open(PERFIL_FILE, "r") as f: return json.load(f)
    return {"empresa": "TECNOELEC SpA"}

# --- 3. MOTOR PDF ---
class PDF_Pro(FPDF):
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')
    def crear_seccion_titulo(self, titulo):
        if self.get_y() > 245: self.add_page()
        self.set_fill_color(230, 230, 230); self.set_font("Arial", 'B', 10)
        txt = titulo.encode('latin-1', 'replace').decode('latin-1')
        self.cell(0, 8, f" {txt}", 1, 1, 'L', True)

def limpiar(texto):
    if not texto: return ""
    cambios = {'ñ':'n','Ñ':'N','á':'a','é':'e','í':'i','ó':'o','ú':'u','°':' deg '}
    for o, r in cambios.items(): texto = texto.replace(o, r)
    return texto.encode('latin-1', 'ignore').decode('latin-1')

def generar_pdf(titulo, perfil, cliente, proy, datos, fotos, img_portada, logo_p):
    pdf = PDF_Pro()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    if os.path.exists(logo_p): pdf.image(logo_p, 10, 10, 30)
    pdf.set_y(45); pdf.set_font('Arial', 'B', 22); pdf.multi_cell(0, 12, limpiar(proy).upper(), 0, 'C')
    pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, limpiar(titulo).upper(), 0, 1, 'C')
    if img_portada:
        try:
            img_p = Image.open(img_portada).convert("RGB"); img_p.save("temp_p.jpg", "JPEG")
            pdf.image("temp_p.jpg", x=45, y=85, w=120, h=95) 
        except: pass
    pdf.set_y(210); pdf.set_fill_color(200, 220, 255); pdf.set_font('Arial', 'B', 8)
    pdf.cell(20, 8, "REV", 1, 0, 'C', True); pdf.cell(30, 8, "FECHA", 1, 0, 'C', True)
    pdf.cell(50, 8, "PREPARA", 1, 0, 'C', True); pdf.cell(50, 8, "REVISA", 1, 0, 'C', True); pdf.cell(40, 8, "APRUEBA", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 8); pdf.cell(20, 8, "01", 1, 0, 'C'); pdf.cell(30, 8, str(datetime.date.today()), 1, 0, 'C')
    pdf.cell(50, 8, limpiar(datos['encargado']), 1, 0, 'C'); pdf.cell(50, 8, limpiar(perfil['empresa']), 1, 0, 'C'); pdf.cell(40, 8, "CLIENTE", 1, 1, 'C')
    pdf.add_page(); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "DESARROLLO TECNICO", 0, 1, 'L'); pdf.ln(5)
    pdf.crear_seccion_titulo("I. INFORMACION GENERAL")
    pdf.set_font("Arial", '', 9); pdf.cell(95, 7, f" Cliente: {limpiar(cliente['Nombre'])}", 1); pdf.cell(95, 7, f" Contacto: {limpiar(cliente['Contacto'])}", 1, 1)
    pdf.cell(0, 7, f" Direccion: {limpiar(cliente['Direccion'])}", 1, 1); pdf.ln(5)
    pdf.crear_seccion_titulo("II. GESTION DE OBRA - PERSONAL")
    pdf.set_font("Arial", 'B', 9); pdf.cell(110, 7, " NOMBRE", 1, 0, 'C', True); pdf.cell(80, 7, " CARGO / FUNCION", 1, 1, 'C', True)
    pdf.set_font("Arial", '', 9); pdf.cell(110, 7, f" {limpiar(datos['encargado'])}", 1); pdf.cell(80, 7, f" {limpiar(datos['cargo'])}", 1, 1)
    for p in datos['equipo_lista']:
        if p['nombre']: pdf.cell(110, 7, f" {limpiar(p['nombre'])}", 1); pdf.cell(80, 7, f" {limpiar(p['cargo'])}", 1, 1)
    pdf.ln(5); pdf.crear_seccion_titulo("III. TRABAJO REALIZADO"); pdf.multi_cell(0, 6, f" {limpiar(datos['detalle'])}", 1); pdf.ln(5)
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

# --- 4. INTERFAZ ---
if 'conectado' not in st.session_state: st.session_state['conectado'] = False
if 'user' not in st.session_state: st.session_state['user'] = None

if not st.session_state['conectado']:
    st.title("⚡ Tecnoelec Pro Cloud")
    tab1, tab2 = st.tabs(["Ingresar", "Crear Cuenta"])
    with tab1:
        u = st.text_input("Usuario"); p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            df_u = obtener_usuarios()
            if not df_u[(df_u['Usuario'] == u) & (df_u['Clave'] == p)].empty or (u == "admin" and p == "tecnoelec2026"):
                st.session_state['conectado'] = True; st.session_state['user'] = u; st.rerun()
            else: st.error("Acceso incorrecto")
    with tab2:
        with st.form("reg"):
            nu = st.text_input("Nuevo Usuario"); np = st.text_input("Nueva Clave", type="password")
            if st.form_submit_button("Registrarse"):
                df_u = obtener_usuarios()
                if nu and np and nu not in df_u['Usuario'].values:
                    conn.update(worksheet="Usuarios", data=pd.concat([df_u, pd.DataFrame([[nu, np]], columns=['Usuario', 'Clave'])], ignore_index=True))
                    st.success("Cuenta creada."); st.rerun()
                else: st.warning("Error en el registro.")
else:
    st.sidebar.write(f"👤 Bienvenido: **{st.session_state['user']}**")
    op = st.sidebar.radio("Navegación", ["Perfil Empresa", "Clientes Cloud", "Nuevo Informe", "Salir"])
    
    if op == "Perfil Empresa":
        st.header("Identidad Corporativa")
        p_data = cargar_perfil()
        emp_n = st.text_input("Nombre de la Empresa", value=p_data['empresa'])
        logo_f = st.file_uploader("Subir Logo (PNG/JPG)", type=["png","jpg","jpeg"])
        if st.button("Guardar Perfil"):
            with open(PERFIL_FILE, "w") as f: json.dump({"empresa": emp_n}, f)
            if logo_f: Image.open(logo_f).convert("RGB").save(LOGO_PATH)
            st.success("Datos actualizados.")
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=200)

    elif op == "Clientes Cloud":
        st.header("Base de Datos de Clientes")
        df_g = obtener_clientes()
        with st.form("fc", clear_on_submit=True):
            n = st.text_input("Nombre Cliente"); r = st.text_input("RUT"); d = st.text_input("Dirección"); c = st.text_input("Contacto")
            if st.form_submit_button("Guardar"):
                if n and r:
                    conn.update(data=pd.concat([df_g, pd.DataFrame([[n, r, d, c]], columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])], ignore_index=True))
                    st.success("Guardado"); st.rerun()
        st.dataframe(df_g, use_container_width=True)

    elif op == "Nuevo Informe":
        st.header("Generar Informe Técnico RIC")
        df_g = obtener_clientes()
        if df_g.empty: st.warning("Sin clientes."); st.stop()
        c_sel = st.selectbox("Cliente", df_g['Nombre'].tolist())
        c_dat = df_g[df_g['Nombre'] == c_sel].iloc[0]
        proy = st.text_input("Proyecto", value="INFORME TECNICO")
        img_p = st.file_uploader("Portada", type=["jpg","png"])
        with st.expander("📝 Gestión de Obra", expanded=True):
            col1, col2 = st.columns(2)
            with col1: enc = st.text_input("Responsable", value=st.session_state['user'])
            with col2: car = st.text_input("Cargo", value="Instalador Eléctrico")
            equipo = []
            for i in range(1, 3):
                c1, c2 = st.columns(2)
                with c1: ne = st.text_input(f"Personal {i}", key=f"n{i}"); ce = st.text_input(f"Cargo {i}", key=f"c{i}")
                equipo.append({"nombre": ne, "cargo": ce})
        det = st.text_area("Trabajo Realizado"); con = st.text_area("Conclusiones")
        fotos = st.file_uploader("Anexo Fotos", accept_multiple_files=True)
        if st.button("🚀 GENERAR PDF"):
            p_conf = cargar_perfil()
            pdf_out = generar_pdf("Informe Técnico", p_conf, c_dat, proy, {"encargado":enc, "cargo":car, "equipo_lista": equipo, "detalle":det, "conclu":con}, fotos, img_p, LOGO_PATH)
            st.download_button("Descargar PDF", data=pdf_out, file_name=f"{proy}.pdf")

    elif op == "Salir":
        st.session_state['conectado'] = False; st.rerun()
