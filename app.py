import streamlit as st
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime
import json
import os

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Tecnoelec Pro Cloud", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #004a99; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN SEGURA ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_raw = conn.read(ttl=0)
    if not df_raw.empty:
        df_global = df_raw.iloc[:, :4].dropna(subset=[df_raw.columns[0]])
        df_global.columns = ['Nombre', 'RUT', 'Direccion', 'Contacto']
    else:
        df_global = pd.DataFrame(columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])
except Exception as e:
    st.error(f"Error de Conexión Cloud: {e}")
    df_global = pd.DataFrame(columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])

PERFIL_FILE = "perfil_config.json"
LOGO_PATH = "logo_empresa.png"

def cargar_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

def guardar_json(file, datos):
    with open(file, "w") as f: json.dump(datos, f)

# --- 3. MOTOR PDF PROFESIONAL ---
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
    
    # PORTADA
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
    
    # DESARROLLO
    pdf.add_page(); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "DESARROLLO TECNICO", 0, 1, 'L'); pdf.ln(5)
    pdf.crear_seccion_titulo("I. INFORMACION GENERAL")
    pdf.set_font("Arial", '', 9); pdf.cell(95, 7, f" Cliente: {limpiar(cliente['Nombre'])}", 1); pdf.cell(95, 7, f" Contacto: {limpiar(cliente['Contacto'])}", 1, 1)
    pdf.cell(0, 7, f" Direccion: {limpiar(cliente['Direccion'])}", 1, 1); pdf.ln(5)
    
    pdf.crear_seccion_titulo("II. GESTION DE OBRA - PERSONAL")
    pdf.set_font("Arial", 'B', 9); pdf.cell(110, 7, " NOMBRE", 1, 0, 'C', True); pdf.cell(80, 7, " CARGO / FUNCION", 1, 1, 'C', True)
    pdf.set_font("Arial", '', 9)
    # Listamos al responsable y al equipo
    pdf.cell(110, 7, f" {limpiar(datos['encargado'])}", 1); pdf.cell(80, 7, f" {limpiar(datos['cargo'])}", 1, 1)
    for p in datos['equipo_lista']:
        if p['nombre']:
            pdf.cell(110, 7, f" {limpiar(p['nombre'])}", 1)
            pdf.cell(80, 7, f" {limpiar(p['cargo'])}", 1, 1)
    pdf.ln(5)
    
    pdf.crear_seccion_titulo("III. TRABAJO REALIZADO")
    pdf.set_font("Arial", '', 9); pdf.multi_cell(0, 6, f" {limpiar(datos['detalle'])}", 1); pdf.ln(5)
    
    pdf.crear_seccion_titulo("IV. CONCLUSIONES")
    pdf.set_font("Arial", '', 9); pdf.multi_cell(0, 6, f" {limpiar(datos['conclu'])}", 1)
    
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

if not st.session_state['conectado']:
    st.title(" Informes de trabajo")
    u = st.text_input("Usuario"); p = st.text_input("Clave", type="password")
    if st.button("Ingresar"):
        if u == "admin" and p == "tecnoelec2026":
            st.session_state['conectado'] = True; st.rerun()
        else: st.error("Acceso denegado")
else:
    op = st.sidebar.radio("Navegación", ["Perfil Empresa", "Clientes Cloud", "Nuevo Informe", "Salir"])

    if op == "Clientes Cloud":
        st.header("Gestión de Clientes")
        with st.form("fc", clear_on_submit=True):
            n = st.text_input("Nombre Cliente"); r = st.text_input("RUT")
            d = st.text_input("Dirección"); c = st.text_input("Contacto")
            if st.form_submit_button("Guardar"):
                if n and r:
                    try:
                        df_actual = conn.read(ttl=0).iloc[:, :4]
                        df_actual.columns = ['Nombre', 'RUT', 'Direccion', 'Contacto']
                        nuevo = pd.DataFrame([[n, r, d, c]], columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])
                        conn.update(data=pd.concat([df_actual, nuevo], ignore_index=True))
                        st.success(f"¡{n} guardado!"); st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
        st.dataframe(df_global, use_container_width=True)

    elif op == "Nuevo Informe":
        st.header("Generar Informe Técnico ")
        if df_global.empty: st.warning("Registre un cliente primero."); st.stop()
        
        c_sel = st.selectbox("Seleccionar Cliente", df_global['Nombre'].tolist())
        c_dat = df_global[df_global['Nombre'] == c_sel].iloc[0]
        proy = st.text_input("Nombre del Proyecto", value="MANTENCION ELECTRICA")
        img_p = st.file_uploader("Portada", type=["jpg","png"])
        
        with st.expander(" Gestión de Obra y Personal", expanded=True):
            st.subheader("Responsable ")
            col1, col2 = st.columns(2)
            with col1: enc = st.text_input("Nombre", value="David Pastene")
            with col2: car = st.text_input("Cargo", value="Oficina Técnica / Instalador Autorizado SEC")
            
            st.subheader("Equipo de Trabajo")
            # --- NUEVA SECCIÓN DE EQUIPO CON NOMBRE Y CARGO ---
            equipo_lista = []
            for i in range(1, 3): # Permite agregar hasta 2 personas más
                c_eq1, c_eq2 = st.columns(2)
                with c_eq1: nom_e = st.text_input(f"Nombre Personal {i}", key=f"n{i}", placeholder="Ej: Hernán Riquelme")
                with c_eq2: car_e = st.text_input(f"Cargo Personal {i}", key=f"c{i}", placeholder="Ej: Ayudante Eléctrico")
                equipo_lista.append({"nombre": nom_e, "cargo": car_e})
            
        det = st.text_area("Trabajo Realizado", height=150)
        con = st.text_area("Conclusiones")
        fotos = st.file_uploader("Anexo Fotos", accept_multiple_files=True)
        
        if st.button("🚀 GENERAR PDF"):
            p_data = cargar_json(PERFIL_FILE, {"empresa": "TECNOELEC SpA"})
            pdf_out = generar_pdf("Informe Técnico", p_data, c_dat, proy, {"encargado":enc, "cargo":car, "equipo_lista": equipo_lista, "detalle":det, "conclu":con}, fotos, img_p, LOGO_PATH)
            st.download_button("Descargar Informe", data=pdf_out, file_name=f"{proy}.pdf")

    elif op == "Salir":
        st.session_state['conectado'] = False; st.rerun()
