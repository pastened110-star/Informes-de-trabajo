import streamlit as st
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime
import json
import os

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Gestor Tecnoelec Pro", layout="wide")

PERFIL_FILE = "perfil_config.json"
CLIENTES_FILE = "clientes_db.json"
BORRADOR_FILE = "borrador_actual.json"
LOGO_PATH = "logo_empresa.png"

def guardar_json(file, datos):
    with open(file, "w") as f:
        json.dump(datos, f)

def cargar_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except:
            return default
    return default

# --- 2. CARGA INICIAL ---
if 'perfil' not in st.session_state:
    st.session_state['perfil'] = cargar_json(PERFIL_FILE, {"empresa": "TECNOELEC SpA", "rut": ""})
if 'clientes' not in st.session_state:
    saved_clients = cargar_json(CLIENTES_FILE, [])
    st.session_state['clientes'] = pd.DataFrame(saved_clients, columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])
if 'conectado' not in st.session_state:
    st.session_state['conectado'] = False

st.markdown("""<style>.stButton>button { width: 100%; border-radius: 5px; background-color: #004a99; color: white; }</style>""", unsafe_allow_html=True)

# --- 3. MOTOR PDF (Diseño Híbrido Word/Recuadros) ---
class PDF_Pro(FPDF):
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
    def crear_recuadro(self, titulo, contenido):
        self.set_fill_color(240, 240, 240); self.set_font("Arial", 'B', 10)
        self.cell(0, 8, f" {titulo}", 1, 1, 'L', True)
        self.set_font("Arial", '', 9); self.multi_cell(0, 6, contenido, 1); self.ln(5)

def generar_pdf(titulo, perfil, cliente, proy, datos, fotos):
    pdf = PDF_Pro()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, 10, 10, 35)
    pdf.ln(40)
    pdf.set_font('Arial', 'B', 22); pdf.multi_cell(0, 15, proy.upper(), 0, 'C')
    pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, titulo.upper(), 0, 1, 'C')
    pdf.ln(20)
    # Tabla Control
    pdf.set_fill_color(200, 220, 255); pdf.set_font('Arial', 'B', 8)
    pdf.cell(20, 8, "REV", 1, 0, 'C', True); pdf.cell(30, 8, "FECHA", 1, 0, 'C', True)
    pdf.cell(50, 8, "PREPARA", 1, 0, 'C', True); pdf.cell(50, 8, "REVISA", 1, 0, 'C', True); pdf.cell(40, 8, "APRUEBA", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 8); pdf.cell(20, 8, "01", 1, 0, 'C'); pdf.cell(30, 8, str(datetime.date.today()), 1, 0, 'C')
    pdf.cell(50, 8, datos['encargado'], 1, 0, 'C'); pdf.cell(50, 8, perfil['empresa'], 1, 0, 'C'); pdf.cell(40, 8, "CLIENTE", 1, 1, 'C')
    
    pdf.add_page(); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "DESARROLLO TECNICO", 0, 1, 'L'); pdf.ln(5)
    pdf.crear_recuadro("I. INFORMACION GENERAL", f"Cliente: {cliente['Nombre']}\nContacto: {cliente['Contacto']}\nDirección: {cliente['Direccion']}")
    pdf.crear_recuadro("II. DETALLE ACTIVIDADES", datos['detalle'])
    pdf.crear_recuadro("III. CONCLUSIONES", datos['conclu'])
    
    if fotos:
        pdf.add_page()
        for i, foto in enumerate(fotos):
            img = Image.open(foto).convert("RGB")
            temp_name = f"temp_img_{i}.jpg"
            img.save(temp_name, "JPEG")
            pdf.image(temp_name, 15, pdf.get_y(), 180, 95); pdf.ln(100)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. INTERFAZ ---
if not st.session_state['conectado']:
    st.title("Acceso Tecnoelec SpA")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        if u == "admin" and p == "tecnoelec2026":
            st.session_state['conectado'] = True
            st.rerun()
        else: st.error("Clave incorrecta")
else:
    op = st.sidebar.radio("Menú", ["Perfil", "Clientes", "Generar Informe", "Salir"])

    if op == "Perfil":
        st.header("Configuración de Perfil (Permanente)")
        st.session_state['perfil']['empresa'] = st.text_input("Empresa", value=st.session_state['perfil']['empresa'])
        logo_subido = st.file_uploader("Actualizar Logo", type=["png", "jpg", "jpeg"])
        
        if st.button("Guardar Perfil"):
            # Guardamos el texto en el JSON
            guardar_json(PERFIL_FILE, st.session_state['perfil'])
            # Guardamos la imagen por separado si se subió una nueva
            if logo_subido:
                img = Image.open(logo_subido)
                img = img.convert("RGB")
                img.save(LOGO_PATH)
            st.success("¡Perfil guardado! El logo y el nombre se mantendrán.")

    elif op == "Clientes":
        st.header("Gestión de Clientes")
        with st.form("fc", clear_on_submit=True):
            n = st.text_input("Nombre"); r = st.text_input("RUT"); d = st.text_input("Dirección"); c = st.text_input("Contacto")
            if st.form_submit_button("Guardar"):
                nuevo = pd.DataFrame([[n,r,d,c]], columns=['Nombre','RUT','Direccion','Contacto'])
                st.session_state['clientes'] = pd.concat([st.session_state['clientes'], nuevo], ignore_index=True)
                guardar_json(CLIENTES_FILE, st.session_state['clientes'].values.tolist())
                st.success("Cliente guardado.")
        st.dataframe(st.session_state['clientes'], use_container_width=True)

    elif op == "Generar Informe":
        st.header("Redacción de Informe")
        
        if os.path.exists(BORRADOR_FILE) and st.button("📂 Recuperar último borrador"):
            borrador = cargar_json(BORRADOR_FILE, {})
            st.session_state['tmp_det'] = borrador.get('detalle', '')
            st.session_state['tmp_con'] = borrador.get('conclu', '')
            st.rerun()

        if st.session_state['clientes'].empty:
            st.warning("Primero agrega un cliente.")
        else:
            c_sel = st.selectbox("Cliente", st.session_state['clientes']['Nombre'])
            proy = st.text_input("Nombre Proyecto")
            det = st.text_area("Descripción de actividades", value=st.session_state.get('tmp_det', ''), height=200)
            con = st.text_area("Conclusiones", value=st.session_state.get('tmp_con', ''))
            
            if st.button("💾 Guardar Borrador"):
                guardar_json(BORRADOR_FILE, {"detalle": det, "conclu": con})
                st.toast("Progreso guardado")

            fotos = st.file_uploader("Fotos", accept_multiple_files=True)
            
            if st.button("🚀 FINALIZAR Y DESCARGAR"):
                c_data = st.session_state['clientes'][st.session_state['clientes']['Nombre'] == c_sel].iloc[0]
                d_obra = {"f_inicio": "Hoy", "encargado": "David Pastene", "detalle": det, "conclu": con}
                pdf_out = generar_pdf("Informe de Mantenimiento", st.session_state['perfil'], c_data, proy, d_obra, fotos)
                st.download_button("Descargar PDF", data=pdf_out, file_name=f"{proy}.pdf")

    elif op == "Salir":
        st.session_state['conectado'] = False
        st.rerun()
