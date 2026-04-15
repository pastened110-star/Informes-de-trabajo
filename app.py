import streamlit as st
from fpdf import FPDF
import pandas as pd
from PIL import Image
import io
import datetime
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestor de Informes Técnicos", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; background-color: #004a99; color: white; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar Base de Datos en la sesión
if 'clientes' not in st.session_state:
    # Agregamos la columna 'Contacto'
    st.session_state['clientes'] = pd.DataFrame(columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])
if 'perfil' not in st.session_state:
    st.session_state['perfil'] = {"empresa": "Tecnoelec SpA", "rut": "", "logo": None}
if 'conectado' not in st.session_state:
    st.session_state['conectado'] = False

# --- 2. MOTOR PDF (Se mantiene tu diseño pro) ---
class PDF_Pro(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def crear_recuadro(self, titulo, contenido):
        self.set_fill_color(240, 240, 240)
        self.set_font("Arial", 'B', 10)
        self.cell(0, 8, f" {titulo}", 1, 1, 'L', True)
        self.set_font("Arial", '', 9)
        self.multi_cell(0, 6, contenido, 1)
        self.ln(5)

def generar_pdf_hibrido(titulo_doc, perfil, cliente, proy, datos, fotos):
    pdf = PDF_Pro()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    if perfil['logo']:
        try:
            img = Image.open(perfil['logo'])
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.save("temp_logo.jpg", "JPEG")
            pdf.image("temp_logo.jpg", 10, 10, 35)
        except: pass
    pdf.ln(40)
    pdf.set_font('Arial', 'B', 22); pdf.multi_cell(0, 15, proy.upper(), 0, 'C')
    pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, titulo_doc.upper(), 0, 1, 'C')
    pdf.ln(20)
    # Tabla Control
    pdf.set_fill_color(200, 220, 255); pdf.set_font('Arial', 'B', 8)
    pdf.cell(20, 8, "REV", 1, 0, 'C', True); pdf.cell(30, 8, "FECHA", 1, 0, 'C', True)
    pdf.cell(50, 8, "PREPARA", 1, 0, 'C', True); pdf.cell(50, 8, "REVISA", 1, 0, 'C', True); pdf.cell(40, 8, "APRUEBA", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 8); pdf.cell(20, 8, "01", 1, 0, 'C'); pdf.cell(30, 8, str(datetime.date.today()), 1, 0, 'C')
    pdf.cell(50, 8, datos['encargado'], 1, 0, 'C'); pdf.cell(50, 8, perfil['empresa'], 1, 0, 'C'); pdf.cell(40, 8, "CLIENTE", 1, 1, 'C')
    # Sección Técnica
    pdf.add_page(); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "DESARROLLO DEL INFORME", 0, 1, 'L'); pdf.ln(5)
    info_gen = f"Cliente: {cliente['Nombre']}\nRUT: {cliente['RUT']}\nUbicación: {cliente['Direccion']}\nContacto: {cliente['Contacto']}"
    pdf.crear_recuadro("I. INFORMACION GENERAL", info_gen)
    pdf.crear_recuadro("II. GESTION DE OBRA", f"Responsable: {datos['encargado']}\nInicio: {datos['f_inicio']} | Término: {datos['f_termino']}")
    pdf.crear_recuadro("III. DESCRIPCION DE ACTIVIDADES", datos['detalle'])
    pdf.crear_recuadro("IV. CONCLUSIONES", datos['conclu'])
    # Fotos
    if fotos:
        pdf.add_page(); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "ANEXO FOTOGRAFICO", 0, 1, 'L')
        y_img = 30
        for i, foto in enumerate(fotos):
            if i > 0 and i % 2 == 0: pdf.add_page(); y_img = 30
            img = Image.open(foto); img = img.convert("RGB"); img.save(f"temp_{i}.jpg", "JPEG")
            pdf.image(f"temp_{i}.jpg", 15, y_img, 180, 95)
            pdf.set_xy(15, y_img + 97); pdf.cell(180, 8, f"Imagen {i+1}", 1, 1, 'C'); y_img += 115
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. INTERFAZ ---
if not st.session_state['conectado']:
    st.title("Sistema de Gestión de Informes Técnicos")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Ingresar"):
        if u == "admin" and p == "tecnoelec2026":
            st.session_state['conectado'] = True
            st.rerun()
else:
    st.sidebar.title("Menú")
    op = st.sidebar.radio("", ["Perfil", "Clientes", "Generar Informe", "Salir"])

    if op == "Perfil":
        st.header("Perfil de Empresa")
        st.session_state['perfil']['empresa'] = st.text_input("Nombre Empresa", value=st.session_state['perfil']['empresa'])
        st.session_state['perfil']['logo'] = st.file_uploader("Subir Logo", type=["png", "jpg"])

    elif op == "Clientes":
        st.header("Base de Datos de Clientes")
        
        # Formulario de entrada
        with st.expander("➕ Agregar / Editar Cliente", expanded=True):
            with st.form("form_cliente", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nombre = st.text_input("Nombre del Cliente")
                    rut = st.text_input("RUT")
                with col2:
                    direccion = st.text_input("Dirección")
                    contacto = st.text_input("Persona de Contacto (Enviar a)")
                
                if st.form_submit_button("Guardar Cliente"):
                    if nombre and rut:
                        # Si el cliente ya existe (por nombre), lo actualizamos; si no, lo agregamos
                        if nombre in st.session_state['clientes']['Nombre'].values:
                            st.session_state['clientes'].loc[st.session_state['clientes']['Nombre'] == nombre, ['RUT', 'Direccion', 'Contacto']] = [rut, direccion, contacto]
                            st.success(f"Datos de {nombre} actualizados.")
                        else:
                            nuevo = pd.DataFrame([[nombre, rut, direccion, contacto]], columns=['Nombre', 'RUT', 'Direccion', 'Contacto'])
                            st.session_state['clientes'] = pd.concat([st.session_state['clientes'], nuevo], ignore_index=True)
                            st.success("Cliente guardado correctamente.")
                    else:
                        st.error("Nombre y RUT son obligatorios.")

        # Tabla de gestión
        st.subheader("Clientes Registrados")
        if not st.session_state['clientes'].empty:
            for i, row in st.session_state['clientes'].iterrows():
                with st.container():
                    c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 1, 1])
                    c1.write(f"**{row['Nombre']}**")
                    c2.write(row['RUT'])
                    c3.write(row['Direccion'])
                    
                    # Botón Eliminar
                    if c4.button("Eliminar", key=f"del_{i}"):
                        st.session_state['clientes'] = st.session_state['clientes'].drop(i).reset_index(drop=True)
                        st.rerun()
                    
                    # Botón Cargar para editar
                    if c5.button("Editar", key=f"ed_{i}"):
                        st.info(f"Modifique los datos de arriba para {row['Nombre']} y presione Guardar.")
            
            st.divider()
            st.dataframe(st.session_state['clientes'], use_container_width=True)
        else:
            st.info("No hay clientes registrados aún.")

    elif op == "Generar Informe":
        st.header("Crear Nuevo Documento")
        if st.session_state['clientes'].empty:
            st.warning("Debe registrar un cliente primero."); st.stop()
        
        c_sel = st.selectbox("Seleccionar Cliente", st.session_state['clientes']['Nombre'])
        c_data = st.session_state['clientes'][st.session_state['clientes']['Nombre'] == c_sel].iloc[0]
        
        st.write(f"**Enviado a:** {c_data['Contacto']}") # Muestra el contacto automáticamente
        
        proy = st.text_input("Proyecto (Ej: MANTENCION UPS PISO 5)")
        f_i = st.date_input("Fecha Inicio")
        f_t = st.date_input("Fecha Término")
        enc = st.text_input("Encargado", value="David Alberto Pastene Moyano")
        det = st.text_area("Descripción de actividades")
        con = st.text_area("Conclusiones")
        fotos = st.file_uploader("Fotos", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

        if st.button("🚀 GENERAR INFORME FINAL"):
            d_obra = {"f_inicio": f_i, "f_termino": f_t, "encargado": enc, "detalle": det, "conclu": con}
            pdf_out = generar_pdf_hibrido("Informe de Mantenimiento", st.session_state['perfil'], c_data, proy, d_obra, fotos)
            st.download_button("💾 Descargar PDF", data=pdf_out, file_name=f"Informe_{c_sel}.pdf")

    elif op == "Salir":
        st.session_state['conectado'] = False
        st.rerun()
