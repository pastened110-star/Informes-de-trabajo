import streamlit as st
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime
import json
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestor Tecnoelec Pro", layout="wide")

PERFIL_FILE = "perfil_config.json"
CLIENTES_FILE = "clientes_db.json"
BORRADOR_FILE = "borrador_actual.json"
LOGO_PATH = "logo_empresa.png"

def guardar_json(file, datos):
    datos_limpios = {k: v for k, v in datos.items() if isinstance(v, (str, int, float, bool, list, dict))}
    with open(file, "w") as f:
        json.dump(datos_limpios, f)

def cargar_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except: return default
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

# --- 3. MOTOR PDF COMPLETO ---
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
    
    # PORTADA
    pdf.add_page()
    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, 10, 10, 35)
    pdf.ln(40)
    pdf.set_font('Arial', 'B', 22); pdf.multi_cell(0, 15, proy.upper(), 0, 'C')
    pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, titulo.upper(), 0, 1, 'C')
    pdf.ln(20)
    # Tabla Versiones
    pdf.set_fill_color(200, 220, 255); pdf.set_font('Arial', 'B', 8)
    pdf.cell(20, 8, "REV", 1, 0, 'C', True); pdf.cell(30, 8, "FECHA", 1, 0, 'C', True)
    pdf.cell(50, 8, "PREPARA", 1, 0, 'C', True); pdf.cell(50, 8, "REVISA", 1, 0, 'C', True); pdf.cell(40, 8, "APRUEBA", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 8); pdf.cell(20, 8, "01", 1, 0, 'C'); pdf.cell(30, 8, str(datetime.date.today()), 1, 0, 'C')
    pdf.cell(50, 8, datos['encargado'], 1, 0, 'C'); pdf.cell(50, 8, perfil['empresa'], 1, 0, 'C'); pdf.cell(40, 8, "CLIENTE", 1, 1, 'C')
    
    # CONTENIDO TÉCNICO
    pdf.add_page(); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "DESARROLLO TECNICO", 0, 1, 'L'); pdf.ln(5)
    pdf.crear_recuadro("I. INFORMACION GENERAL", f"Cliente: {cliente['Nombre']}\nContacto: {cliente['Contacto']}\nDirección: {cliente['Direccion']}")
    pdf.crear_recuadro("II. GESTION DE OBRA", f"Responsable: {datos['encargado']} ({datos['cargo']})\nInicio: {datos['f_inicio']} | Término: {datos['f_termino']}\nEquipo: {datos['equipo']}")
    pdf.crear_recuadro("III. DESCRIPCION ACTIVIDADES", datos['detalle'])
    pdf.crear_recuadro("IV. CONCLUSIONES", datos['conclu'])
    
    if fotos:
        pdf.add_page()
        for i, foto in enumerate(fotos):
            try:
                img = Image.open(foto).convert("RGB")
                temp = f"temp_{i}.jpg"; img.save(temp, "JPEG")
                pdf.image(temp, 15, pdf.get_y(), 180, 95); pdf.ln(100)
            except: pass
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. INTERFAZ ---
if not st.session_state['conectado']:
    st.title("Acceso Tecnoelec SpA")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        if u == "admin" and p == "tecnoelec2026":
            st.session_state['conectado'] = True; st.rerun()
else:
    op = st.sidebar.radio("Menú", ["Perfil", "Clientes", "Generar Informe", "Salir"])

    if op == "Perfil":
        st.header("Configuración de Perfil (Permanente)")
        st.session_state['perfil']['empresa'] = st.text_input("Empresa", value=st.session_state['perfil']['empresa'])
        logo = st.file_uploader("Actualizar Logo", type=["png", "jpg", "jpeg"])
        if st.button("Guardar Perfil"):
            guardar_json(PERFIL_FILE, st.session_state['perfil'])
            if logo:
                img = Image.open(logo).convert("RGB"); img.save(LOGO_PATH)
            st.success("¡Perfil guardado!")

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
        st.header("Crear Nuevo Informe")
        
        # Recuperar borrador
        if os.path.exists(BORRADOR_FILE) and st.button("📂 Recuperar último borrador"):
            b = cargar_json(BORRADOR_FILE, {})
            st.session_state['tmp_det'] = b.get('detalle', ''); st.session_state['tmp_con'] = b.get('conclu', '')
            st.rerun()

        if st.session_state['clientes'].empty:
            st.warning("Agregue un cliente primero.")
        else:
            c_sel = st.selectbox("Seleccionar Cliente", st.session_state['clientes']['Nombre'])
            proy = st.text_input("Nombre Proyecto (Referencia)", value="QUINCHO VITACURA")
            
            with st.expander("📝 Datos de Gestión y Personal", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    f_ini = st.date_input("Fecha Inicio", value=datetime.date.today())
                    enc = st.text_input("Responsable Técnico", value="David Alberto Pastene Moyano")
                with col2:
                    f_ter = st.date_input("Fecha Término", value=datetime.date.today())
                    car = st.text_input("Cargo", value="Instalador Eléctrico Clase D")
                equ = st.text_area("Equipo de apoyo / Personal", placeholder="Ej: Juan Pérez, Luis Mora")

            st.subheader("Contenido Técnico")
            det = st.text_area("Descripción detallada", value=st.session_state.get('tmp_det', ''), height=200)
            con = st.text_area("Conclusiones técnicas", value=st.session_state.get('tmp_con', ''))
            
            if st.button("💾 Guardar Borrador"):
                guardar_json(BORRADOR_FILE, {"detalle": det, "conclu": con})
                st.toast("Progreso guardado")

            fotos = st.file_uploader("Adjuntar Evidencia Fotográfica", accept_multiple_files=True)
            
            if st.button("🚀 FINALIZAR Y DESCARGAR PDF"):
                c_data = st.session_state['clientes'][st.session_state['clientes']['Nombre'] == c_sel].iloc[0]
                d_obra = {"f_inicio": str(f_ini), "f_termino": str(f_ter), "encargado": enc, "cargo": car, "equipo": equ, "detalle": det, "conclu": con}
                pdf_out = generar_pdf("Informe de Mantenimiento", st.session_state['perfil'], c_data, proy, d_obra, fotos)
                st.download_button("Descargar Informe", data=pdf_out, file_name=f"{proy}.pdf")

    elif op == "Salir":
        st.session_state['conectado'] = False; st.rerun()
