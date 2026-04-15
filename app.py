import streamlit as st
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import pandas as pd
from PIL import Image
import os
import datetime
import json

# --- 1. CONFIGURACIÓN Y CONEXIÓN CLOUD ---
st.set_page_config(page_title="Tecnoelec SaaS Pro", layout="wide")

# Conectamos con Google Sheets para que los clientes sean eternos
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_global = conn.read(ttl=0) # ttl=0 para datos siempre frescos
except:
    df_global = pd.DataFrame(columns=['UsuarioID', 'Nombre', 'RUT', 'Direccion', 'Contacto'])

# --- 2. GESTIÓN DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

# --- 3. MOTOR PDF (Diseño Profesional con Celdas) ---
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

# --- 4. INTERFAZ DE ACCESO ---
if not st.session_state['autenticado']:
    st.title("⚡ Generador de Informes Eléctricos Pro")
    tab1, tab2 = st.tabs(["Ingresar", "Solicitar Cuenta"])
    
    with tab1:
        u = st.text_input("Correo Electrónico")
        p = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión"):
            # Validación simple (puedes mejorarla con una tabla de usuarios)
            if u and p:
                st.session_state['autenticado'] = True
                st.session_state['user_email'] = u
                st.rerun()
    with tab2:
        st.write("Si eres un instalador externo, contacta a admin@tecnoelec.cl para habilitar tu espacio de trabajo.")

# --- 5. PANEL DE CONTROL (SaaS) ---
else:
    # Creamos carpeta privada para este usuario si no existe
    # Reemplazamos caracteres raros del email para la carpeta
    safe_email = st.session_state['user_email'].replace("@", "_").replace(".", "_")
    user_folder = f"user_data_{safe_email}"
    if not os.path.exists(user_folder): os.makedirs(user_folder)
    
    logo_path = os.path.join(user_folder, "logo.jpg")
    perfil_path = os.path.join(user_folder, "perfil.json")

    op = st.sidebar.radio(f"Bienvenido {st.session_state['user_email']}", 
                         ["Mi Perfil Empresa", "Mis Clientes", "Nuevo Informe", "Cerrar Sesión"])

    if op == "Cerrar Sesión":
        st.session_state['autenticado'] = False
        st.rerun()

    elif op == "Mi Perfil Empresa":
        st.header("Configuración de Marca Corporativa")
        # Cargar perfil privado
        if os.path.exists(perfil_path):
            with open(perfil_path, "r") as f: p_data = json.load(f)
        else: p_data = {"empresa": "Mi Empresa", "rut": ""}

        nom_emp = st.text_input("Nombre Fantasía Empresa", value=p_data['empresa'])
        rut_emp = st.text_input("RUT Empresa", value=p_data['rut'])
        logo_up = st.file_uploader("Logo para tus Informes", type=["png", "jpg", "jpeg"])
        
        if st.button("Guardar Perfil"):
            with open(perfil_path, "w") as f: 
                json.dump({"empresa": nom_emp, "rut": rut_emp}, f)
            if logo_up:
                Image.open(logo_up).convert("RGB").save(logo_path)
            st.success("Configuración guardada. Tus informes saldrán con esta marca.")

    elif op == "Mis Clientes":
        st.header("Base de Datos en la Nube")
        # Filtrar solo los clientes de este usuario
        mis_clientes = df_global[df_global['UsuarioID'] == st.session_state['user_email']]
        
        with st.form("fc"):
            col1, col2 = st.columns(2)
            with col1: n = st.text_input("Cliente"); r = st.text_input("RUT")
            with col2: d = st.text_input("Dirección"); c = st.text_input("Contacto")
            if st.form_submit_button("Guardar Cliente Permanente"):
                nueva_fila = pd.DataFrame([[st.session_state['user_email'], n, r, d, c]], 
                                         columns=['UsuarioID', 'Nombre', 'RUT', 'Direccion', 'Contacto'])
                # Actualizar Google Sheets
                df_updated = pd.concat([df_global, nueva_fila], ignore_index=True)
                conn.update(data=df_updated)
                st.success("Cliente guardado en tu nube privada.")
                st.rerun()
        
        st.subheader("Tu lista de clientes")
        st.dataframe(mis_clientes[['Nombre', 'RUT', 'Direccion', 'Contacto']], use_container_width=True)

    elif op == "Nuevo Informe":
        st.header("Generar Informe Técnico")
        mis_clientes = df_global[df_global['UsuarioID'] == st.session_state['user_email']]
        
        if mis_clientes.empty:
            st.warning("Primero registra un cliente en la sección 'Mis Clientes'.")
        else:
            c_sel = st.selectbox("Seleccionar Cliente", mis_clientes['Nombre'])
            c_row = mis_clientes[mis_clientes['Nombre'] == c_sel].iloc[0]
            
            # Formulario de informe (igual al anterior pero usando perfil_data)
            # ... (Lógica de fechas, descripción y fotos) ...
            st.info("Al finalizar, el PDF usará tu logo y datos de empresa guardados.")
            if st.button("🚀 Generar"):
                st.write("Procesando...")
    elif op == "Salir":
        st.session_state['conectado'] = False; st.rerun()
