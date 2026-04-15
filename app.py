import streamlit as st
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime
import os

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Tecnoelec Pro Cloud", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #004a99; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def obtener_usuarios():
    try:
        return conn.read(worksheet="Usuarios", ttl=0)
    except:
        return pd.DataFrame(columns=['Usuario', 'Clave'])

def obtener_clientes():
    try:
        df_raw = conn.read(ttl=0) # Lee la primera hoja (Clientes)
        df = df_raw.iloc[:, :4].dropna(subset=[df_raw.columns[0]])
        df.columns = ['Nombre', 'RUT', 'Direccion', 'Contacto']
        return df
    except:
        return pd.DataFrame(columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])

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

def generar_pdf(titulo, cliente, proy, datos, fotos, img_portada, logo_p):
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
    pdf.cell(50, 8, limpiar(datos['encargado']), 1, 0, 'C'); pdf.cell(50, 8, "TECNOELEC SpA", 1, 0, 'C'); pdf.cell(40, 8, "CLIENTE", 1, 1, 'C')
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

# --- 4. INTERFAZ DE ACCESO ---
if 'conectado' not in st.session_state: st.session_state['conectado'] = False
if 'user' not in st.session_state: st.session_state['user'] = None

if not st.session_state['conectado']:
    st.title("⚡ Tecnoelec Pro Cloud")
    tab1, tab2 = st.tabs(["Ingresar", "Crear Cuenta"])
    
    with tab1:
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            df_u = obtener_usuarios()
            user_row = df_u[(df_u['Usuario'] == u) & (df_u['Clave'] == p)]
            if not user_row.empty or (u == "admin" and p == "tecnoelec2026"):
                st.session_state['conectado'] = True
                st.session_state['user'] = u
                st.rerun()
            else: st.error("Usuario o clave incorrectos")

    with tab2:
        with st.form("registro"):
            new_u = st.text_input("Nuevo Usuario")
            new_p = st.text_input("Nueva Clave", type="password")
            if st.form_submit_button("Registrarse"):
                df_u = obtener_usuarios()
                if new_u in df_u['Usuario'].values:
                    st.error("El usuario ya existe")
                elif new_u and new_p:
                    nuevo_u = pd.DataFrame([[new_u, new_p]], columns=['Usuario', 'Clave'])
                    conn.update(worksheet="Usuarios", data=pd.concat([df_u, nuevo_u], ignore_index=True))
                    st.success("Cuenta creada. Ya puedes ingresar.")
                else: st.warning("Completa los campos.")

else:
    # --- INTERFAZ PRINCIPAL ---
    st.sidebar.write(f"👤 Bienvenido: **{st.session_state['user']}**")
    op = st.sidebar.radio("Navegación", ["Clientes Cloud", "Nuevo Informe", "Salir"])
    df_global = obtener_clientes()

    if op == "Clientes Cloud":
        st.header("Base de Datos de Clientes")
        with st.form("fc", clear_on_submit=True):
            n = st.text_input("Nombre Cliente"); r = st.text_input("RUT"); d = st.text_input("Dirección"); c = st.text_input("Contacto")
            if st.form_submit_button("Guardar Cliente"):
                if n and r:
                    try:
                        df_actual = obtener_clientes()
                        nuevo = pd.DataFrame([[n, r, d, c]], columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])
                        conn.update(data=pd.concat([df_actual, nuevo], ignore_index=True))
                        st.success("Cliente guardado"); st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
        st.dataframe(df_global, use_container_width=True)

    elif op == "Nuevo Informe":
        st.header("Generar Informe Técnico RIC")
        if df_global.empty: st.warning("Registre un cliente primero."); st.stop()
        c_sel = st.selectbox("Seleccionar Cliente", df_global['Nombre'].tolist())
        c_dat = df_global[df_global['Nombre'] == c_sel].iloc[0]
        proy = st.text_input("Proyecto", value="INFORME TECNICO")
        img_p = st.file_uploader("Portada", type=["jpg","png"])
        with st.expander("📝 Gestión de Obra", expanded=True):
            col1, col2 = st.columns(2)
            with col1: enc = st.text_input("Responsable", value=st.session_state['user'])
            with col2: car = st.text_input("Cargo", value="Instalador Eléctrico")
            equipo = []
            for i in range(1, 3):
                c1, c2 = st.columns(2)
                with c1: ne = st.text_input(f"Personal {i}", key=f"n{i}")
                with c2: ce = st.text_input(f"Cargo {i}", key=f"c{i}")
                equipo.append({"nombre": ne, "cargo": ce})
        det = st.text_area("Trabajo Realizado")
        con = st.text_area("Conclusiones")
        fotos = st.file_uploader("Fotos", accept_multiple_files=True)
        if st.button("🚀 GENERAR PDF"):
            pdf_out = generar_pdf("Informe Técnico", c_dat, proy, {"encargado":enc, "cargo":car, "equipo_lista": equipo, "detalle":det, "conclu":con}, fotos, img_p, "logo_empresa.png")
            st.download_button("Descargar PDF", data=pdf_out, file_name=f"{proy}.pdf")

    elif op == "Salir":
        st.session_state['conectado'] = False; st.session_state['user'] = None; st.rerun()
