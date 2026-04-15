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

# --- 3. MOTOR PDF MEJORADO (SIN CORTES) ---
class PDF_Pro(FPDF):
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def crear_seccion_titulo(self, titulo):
        # Verificamos si hay espacio suficiente para el título y al menos dos líneas de texto
        if self.get_y() > 250: self.add_page()
        self.set_fill_color(230, 230, 230); self.set_font("Arial", 'B', 10)
        txt = titulo.encode('latin-1', 'replace').decode('latin-1')
        self.cell(0, 8, f" {txt}", 1, 1, 'L', True)

def generar_pdf(titulo, perfil, cliente, proy, datos, fotos, img_portada):
    # Reducimos el margen de salto a 20mm para aprovechar más la hoja
    pdf = PDF_Pro()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    def limpiar(texto):
        if not texto: return ""
        cambios = {'ñ': 'n', 'Ñ': 'N', 'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 
                   'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', '°': ' deg '}
        for original, reemplazo in cambios.items():
            texto = texto.replace(original, reemplazo)
        return texto.encode('latin-1', 'ignore').decode('latin-1')

    # --- PÁGINA 1: PORTADA ---
    pdf.add_page()
    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, 10, 10, 30)
    
    pdf.set_y(45)
    pdf.set_font('Arial', 'B', 22); pdf.multi_cell(0, 12, limpiar(proy).upper(), 0, 'C')
    pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, limpiar(titulo).upper(), 0, 1, 'C')
    
    if img_portada:
        try:
            img_p = Image.open(img_portada).convert("RGB")
            img_p.save("temp_portada.jpg", "JPEG")
            # Ajustamos la imagen para que no empuje la tabla fuera de la primera página
            pdf.image("temp_portada.jpg", x=45, y=85, w=120, h=90) 
        except: pass
    
    # Anclamos la tabla firmemente al pie de la portada
    pdf.set_y(205)
    pdf.set_fill_color(200, 220, 255); pdf.set_font('Arial', 'B', 8)
    pdf.cell(20, 8, "REV", 1, 0, 'C', True); pdf.cell(30, 8, "FECHA", 1, 0, 'C', True)
    pdf.cell(50, 8, "PREPARA", 1, 0, 'C', True); pdf.cell(50, 8, "REVISA", 1, 0, 'C', True); pdf.cell(40, 8, "APRUEBA", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 8); pdf.cell(20, 8, "01", 1, 0, 'C'); pdf.cell(30, 8, str(datetime.date.today()), 1, 0, 'C')
    pdf.cell(50, 8, limpiar(datos['encargado']), 1, 0, 'C'); pdf.cell(50, 8, limpiar(perfil['empresa']), 1, 0, 'C'); pdf.cell(40, 8, "CLIENTE", 1, 1, 'C')
    
    # --- PÁGINA 2 EN ADELANTE ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "DESARROLLO TECNICO", 0, 1, 'L'); pdf.ln(5)
    
    pdf.crear_seccion_titulo("I. INFORMACION GENERAL")
    pdf.set_font("Arial", '', 9)
    pdf.cell(95, 7, f" Cliente: {limpiar(cliente['Nombre'])}", 1); pdf.cell(95, 7, f" Contacto: {limpiar(cliente['Contacto'])}", 1, 1)
    pdf.cell(0, 7, f" Direccion: {limpiar(cliente['Direccion'])}", 1, 1); pdf.ln(5)
    
    pdf.crear_seccion_titulo("II. GESTION DE OBRA")
    pdf.set_font("Arial", 'B', 9); pdf.cell(95, 7, " FECHA DE INICIO", 1, 0); pdf.cell(95, 7, " FECHA DE TERMINO", 1, 1)
    pdf.set_font("Arial", '', 9); pdf.cell(95, 7, f" {datos['f_inicio']}", 1, 0); pdf.cell(95, 7, f" {datos['f_termino']}", 1, 1)
    pdf.set_font("Arial", 'B', 9); pdf.cell(95, 7, " RESPONSABLE TECNICO", 1, 0); pdf.cell(95, 7, " CARGO", 1, 1)
    pdf.set_font("Arial", '', 9); pdf.cell(95, 7, f" {limpiar(datos['encargado'])}", 1, 0); pdf.cell(95, 7, f" {limpiar(datos['cargo'])}", 1, 1)
    pdf.set_font("Arial", 'B', 9); pdf.cell(0, 7, " PERSONAL DE APOYO", 1, 1)
    pdf.set_font("Arial", '', 9); pdf.multi_cell(0, 7, f" {limpiar(datos['equipo'])}", 1); pdf.ln(5)
    
    pdf.crear_seccion_titulo("III. DESCRIPCION ACTIVIDADES")
    # Multi_cell maneja automáticamente los saltos de línea largos
    pdf.multi_cell(0, 6, f" {limpiar(datos['detalle'])}", 1); pdf.ln(5)
    
    pdf.crear_seccion_titulo("IV. CONCLUSIONES")
    pdf.multi_cell(0, 6, f" {limpiar(datos['conclu'])}", 1)
    
    if fotos:
        pdf.add_page(); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "REGISTRO FOTOGRAFICO", 0, 1, 'L')
        for i, foto in enumerate(fotos):
            try:
                img = Image.open(foto).convert("RGB")
                temp = f"temp_{i}.jpg"; img.save(temp, "JPEG")
                # Verificamos espacio antes de poner la foto
                if pdf.get_y() > 180: pdf.add_page()
                pdf.image(temp, 15, pdf.get_y(), 180, 95); pdf.ln(105)
            except: pass
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. INTERFAZ ---
if not st.session_state['conectado']:
    st.title("Acceso Tecnoelec SpA")
    u = st.text_input("Usuario"); p = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        if u == "admin" and p == "tecnoelec2026":
            st.session_state['conectado'] = True; st.rerun()
        else: st.error("Clave incorrecta")
else:
    op = st.sidebar.radio("Menú", ["Perfil", "Clientes", "Generar Informe", "Salir"])

    if op == "Perfil":
        st.header("Perfil Empresa")
        st.session_state['perfil']['empresa'] = st.text_input("Empresa", value=st.session_state['perfil']['empresa'])
        logo = st.file_uploader("Actualizar Logo", type=["png", "jpg", "jpeg"])
        if st.button("Guardar Perfil"):
            guardar_json(PERFIL_FILE, st.session_state['perfil'])
            if logo:
                img = Image.open(logo).convert("RGB"); img.save(LOGO_PATH)
            st.success("Perfil actualizado")

    elif op == "Clientes":
        st.header("Base de Datos de Clientes")
        with st.form("fc", clear_on_submit=True):
            n = st.text_input("Nombre Cliente"); r = st.text_input("RUT"); d = st.text_input("Dirección"); c = st.text_input("Contacto")
            if st.form_submit_button("Guardar"):
                nuevo = pd.DataFrame([[n,r,d,c]], columns=['Nombre','RUT','Direccion','Contacto'])
                st.session_state['clientes'] = pd.concat([st.session_state['clientes'], nuevo], ignore_index=True)
                guardar_json(CLIENTES_FILE, st.session_state['clientes'].values.tolist())
                st.success("Cliente guardado.")
        st.dataframe(st.session_state['clientes'], use_container_width=True)

    elif op == "Generar Informe":
        st.header("Nuevo Informe Técnico")
        if os.path.exists(BORRADOR_FILE) and st.button("📂 Recuperar Borrador"):
            b = cargar_json(BORRADOR_FILE, {})
            st.session_state['tmp_det'] = b.get('detalle', ''); st.session_state['tmp_con'] = b.get('conclu', '')
            st.rerun()

        if st.session_state['clientes'].empty:
            st.warning("Primero agrega un cliente.")
        else:
            c_sel = st.selectbox("Cliente", st.session_state['clientes']['Nombre'])
            proy = st.text_input("Proyecto", value="PROYECTO ELECTRICO")
            img_p = st.file_uploader("🖼️ Imagen de Portada", type=["png", "jpg", "jpeg"])
            
            with st.expander("📝 Gestión y Personal", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    f_ini = st.date_input("Inicio", value=datetime.date.today())
                    enc = st.text_input("Responsable", value="David Alberto Pastene Moyano")
                with col2:
                    f_ter = st.date_input("Término", value=datetime.date.today())
                    car = st.text_input("Cargo", value="Instalador Electrico Clase D")
                equ = st.text_area("Equipo de trabajo")

            det = st.text_area("Descripción Actividades", value=st.session_state.get('tmp_det', ''), height=200)
            con = st.text_area("Conclusiones", value=st.session_state.get('tmp_con', ''))
            
            if st.button("💾 Guardar Borrador"):
                guardar_json(BORRADOR_FILE, {"detalle": det, "conclu": con})
                st.toast("Borrador guardado")

            fotos = st.file_uploader("Anexo Fotográfico", accept_multiple_files=True)
            
            if st.button("🚀 FINALIZAR Y DESCARGAR PDF"):
                c_data = st.session_state['clientes'][st.session_state['clientes']['Nombre'] == c_sel].iloc[0]
                d_obra = {"f_inicio": str(f_ini), "f_termino": str(f_ter), "encargado": enc, "cargo": car, "equipo": equ, "detalle": det, "conclu": con}
                pdf_out = generar_pdf("Informe de Mantenimiento", st.session_state['perfil'], c_data, proy, d_obra, fotos, img_p)
                st.download_button("Descargar Informe", data=pdf_out, file_name=f"{proy}.pdf")

    elif op == "Salir":
        st.session_state['conectado'] = False; st.rerun()
