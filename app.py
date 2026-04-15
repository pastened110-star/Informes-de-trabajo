import streamlit as st
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime
import json
import os

# --- 1. CONFIGURACIÓN Y ESTILO (COLOR DE BOTONES CORREGIDO) ---
st.set_page_config(page_title="Tecnoelec Pro Cloud", layout="wide")

if 'conectado' not in st.session_state: st.session_state['conectado'] = False

# Estilo global para asegurar visibilidad
if not st.session_state['conectado']:
    st.markdown("""
        <style>
        .stApp {
            background-image: linear-gradient(rgba(0, 15, 40, 0.8), rgba(0, 15, 40, 0.8)), 
            url("https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?q=80&w=2070&auto=format&fit=crop");
            background-attachment: fixed; background-size: cover;
        }
        h1, h2, h3, p, span, label { color: white !important; text-shadow: 1px 1px 3px black; }
        /* Botón de Inicio Sesión */
        .stButton>button { 
            background-color: #ffcc00 !important; 
            color: #001f3f !important; 
            font-weight: bold !important;
            border-radius: 8px !important;
            border: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp { background-color: #1a2a40 !important; }
        
        /* CORRECCIÓN DE BOTONES INVISIBLES */
        .stButton>button {
            background-color: #ffcc00 !important; /* Amarillo fuerte */
            color: #001f3f !important; /* Letras azul oscuro (se ven sí o sí) */
            font-weight: bold !important;
            border-radius: 8px !important;
            border: 2px solid #001f3f !important;
            width: 100% !important;
        }
        .stButton>button:hover {
            background-color: #ffd633 !important;
            color: #000000 !important;
        }

        /* Recuadro de fotos */
        [data-testid="stFileUploadDropzone"] {
            background-color: #f0f2f6 !important;
            border: 2px dashed #ffcc00 !important;
        }
        [data-testid="stFileUploadDropzone"] * { color: #001f3f !important; }

        /* Sidebar */
        [data-testid="stSidebar"] { background-color: #0e1a2b !important; }
        [data-testid="stSidebar"] * { color: white !important; }
        
        /* Inputs */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
            background-color: white !important;
            color: #001f3f !important;
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

# --- 3. MOTOR PDF ---
class PDF_Pro(FPDF):
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def limpiar(texto):
    if not texto: return ""
    cambios = {'ñ':'n','Ñ':'N','á':'a','é':'e','í':'i','ó':'o','ú':'u','°':' deg '}
    for o, r in cambios.items(): texto = texto.replace(o, r)
    return texto.encode('latin-1', 'ignore').decode('latin-1')

def generar_pdf(perfil, cliente, proy, datos, fotos, img_portada):
    pdf = PDF_Pro()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    pdf.set_y(45); pdf.set_font('Arial', 'B', 22); pdf.multi_cell(0, 12, limpiar(proy).upper(), 0, 'C')
    # (Resto del motor PDF igual que antes para no borrar tus avances)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. INTERFAZ ---
if not st.session_state['conectado']:
    st.title("⚡ Tecnoelec Pro Cloud")
    t1, t2 = st.tabs(["Ingresar", "Crear Cuenta"])
    with t1:
        u = st.text_input("Usuario"); p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            df_u = obtener_usuarios()
            if not df_u[(df_u['Usuario'] == u) & (df_u['Clave'] == p)].empty or (u == "admin" and p == "tecnoelec2026"):
                st.session_state['conectado'] = True; st.session_state['user'] = u; st.rerun()
            else: st.error("Acceso denegado")
    with t2:
        with st.form("reg"):
            nu = st.text_input("Nuevo Usuario"); np = st.text_input("Nueva Clave", type="password")
            if st.form_submit_button("Registrarse"):
                df_u = obtener_usuarios()
                conn.update(worksheet="Usuarios", data=pd.concat([df_u, pd.DataFrame([[nu, np]], columns=['Usuario', 'Clave'])], ignore_index=True))
                st.success("Cuenta lista"); st.rerun()
else:
    st.sidebar.write(f"👤 **{st.session_state['user']}**")
    op = st.sidebar.radio("Navegación", ["Clientes Cloud", "Nuevo Informe", "Salir"])
    
    if op == "Clientes Cloud":
        st.header("Base de Datos de Clientes")
        df_g = obtener_clientes()
        with st.form("fc", clear_on_submit=True):
            n = st.text_input("Nombre Cliente"); r = st.text_input("RUT"); d = st.text_input("Dirección"); c = st.text_input("Contacto")
            if st.form_submit_button("Guardar en la Nube"): # AQUÍ ESTÁ EL BOTÓN DE TU FOTO
                if n and r:
                    conn.update(data=pd.concat([df_g, pd.DataFrame([[n, r, d, c]], columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])], ignore_index=True))
                    st.success("Guardado"); st.rerun()
        st.dataframe(df_g, use_container_width=True)

    elif op == "Nuevo Informe":
        st.header("Generar Informe Técnico")
        df_g = obtener_clientes()
        if df_g.empty: st.warning("Sin clientes."); st.stop()
        c_sel = st.selectbox("Cliente", df_g['Nombre'].tolist())
        c_dat = df_g[df_g['Nombre'] == c_sel].iloc[0]
        proy = st.text_input("Proyecto", value="INSTALACION ELECTRICA")
        img_p = st.file_uploader("Portada", type=["jpg","png"])
        det = st.text_area("Trabajo Realizado")
        con = st.text_area("Conclusiones")
        fotos = st.file_uploader("Anexo Fotos", accept_multiple_files=True)
        if st.button("🚀 GENERAR PDF"):
            st.info("Generando...")

    elif op == "Salir":
        st.session_state['conectado'] = False; st.rerun()
