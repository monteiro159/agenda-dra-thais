import streamlit as st
import pandas as pd
from datetime import datetime, date
import time
import re
import os
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Dra. Thais Milene", page_icon="🦷", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CONFIGURAÇÃO DA PLANILHA ---
SHEET_ID = "16YOR1odJ11iiUUI_y62FKb7GotQSRZeu64qP6RwZXrU"

# Tabela de Preços
PRECOS = {
    "Avaliação (1ª Vez)": 0,
    "Limpeza": 250,
    "Restauração": 350,
    "Clareamento": 800,
    "Harmonização": 1500,
    "Dor/Urgência": 200
}

# --- GPS DE ARQUIVOS ---
PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_LOGO = os.path.join(PASTA_ATUAL, "logo.jpg")
CAMINHO_DRA = os.path.join(PASTA_ATUAL, "dra.jpg")

def get_img_as_base64(path):
    try:
        with open(path, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return None

# --- 3. ESTILO VISUAL (ROSE PREMIUM + ÍCONES DO RODAPÉ) ---
st.markdown("""
    <style>
        /* Fundo Geral */
        .stApp { background-color: #F0E4E6; }
        
        /* --- ESCONDER BARRA DO STREAMLIT --- */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        div[data-testid="stToolbar"] {visibility: hidden; height: 0%; position: fixed;}
        div[data-testid="stDecoration"] {visibility: hidden; height: 0%;}
        div[data-testid="stStatusWidget"] {visibility: hidden;}
        .block-container { padding-top: 2rem !important; }

        /* --- BOTÕES --- */
        .big-button { width: 100%; height: 120px; border-radius: 20px; color: white; font-size: 20px; font-weight: 600; cursor: pointer; margin-bottom: 15px; display: flex; align-items: center; justify-content: center; text-decoration: none; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .big-button:hover { transform: scale(1.02); }
        
        div[data-testid="stButton"] button[kind="primary"] { background-color: #D8A7B1 !important; color: white !important; border: none; border-radius: 12px; height: 60px; font-size: 18px; font-weight: 600; box-shadow: 0 4px 10px rgba(216, 167, 177, 0.3); width: 100%; }
        div[data-testid="stButton"] button[kind="secondary"] { background-color: #FFFFFF !important; color: #2F2F33 !important; border: 1px solid #E6E6E8; border-radius: 12px; height: 60px; font-size: 16px; font-weight: 500; width: 100%; }
        
        /* Links Personalizados */
        .custom-link-btn { display: flex; align-items: center; justify-content: center; width: 100%; height: 60px; background-color: #FFFFFF; color: #2F2F33; border: 1px solid #E6E6E8; border-radius: 12px; text-decoration: none; font-size: 16px; font-weight: 500; box-shadow: 0 2px 5px rgba(0,0,0,0.02); transition: all 0.3s ease; margin-bottom: 15px; }
        .custom-link-btn:hover { transform: translateY(-2px); border-color: #D8A7B1; color: #D8A7B1; box-shadow: 0 4px 12px rgba(216, 167, 177, 0.2); }
        .btn-icon { width: 24px; height: 24px; margin-right: 12px; fill: currentColor; }

        /* Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] div, .stDateInput input, .stTextArea textarea { background-color: #FFFFFF !important; border: 1px solid #E6E6E8 !important; border-radius: 10px !important; color: #2F2F33 !important; padding-left: 12px; }
        .stTextInput input:focus, .stSelectbox div:focus, .stDateInput input:focus { border-color: #D8A7B1 !important; box-shadow: 0 0 0 2px rgba(216, 167, 177, 0.2) !important; }
        
        /* Dashboard Cards */
        .metric-card { background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #D8A7B1; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; margin-bottom: 10px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2F2F33; }
        .metric-label { font-size: 14px; color: #7A7A7C; }

        /* Typography & Layout */
        h1, h2, h3, p, label, .stMarkdown { color: #2F2F33 !important; font-family: 'Helvetica', sans-serif; }
        .section-header { color: #2F2F33; font-size: 1.1em; font-weight: 600; margin-top: 25px; margin-bottom: 15px; border-left: 4px solid #D8A7B1; padding-left: 15px; background: linear-gradient(90deg, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0) 100%); padding-top: 8px; padding-bottom: 8px; border-radius: 0 8px 8px 0; }
        .login-box { background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid #E6E6E8; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.02); }
        .ticket { background-color: white; border: 1px solid #C9B49A; padding: 30px; border-radius: 12px; margin-top: 20px; text-align: center; position: relative; box-shadow: 0 10px 30px rgba(0,0,0,0.03); }
        .ticket::before { content: "✦"; color: #C9B49A; font-size: 20px; position: absolute; top: 10px; left: 50%; transform: translateX(-50%); }
        
        .header-container { display: flex; justify-content: center; align-items: center; gap: 20px; margin-bottom: 20px; margin-top: 10px; }
        .header-dra { width: 120px; height: 120px; border-radius: 50%; border: 3px solid #D8A7B1; object-fit: cover; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .header-logo { width: 120px; height: auto; object-fit: contain; }
        a { text-decoration: none; }
        [data-testid="stImage"] { margin: 0 auto; }

        /* --- RODAPÉ SOCIAL COM ÍCONES SVG --- */
        .social-footer { 
            display: flex; 
            justify-content: center; 
            gap: 25px; 
            margin-top: 40px; 
            margin-bottom: 20px;
        }
        .social-icon { 
            width: 28px; 
            height: 28px; 
            fill: #7A7A7C; /* Cor Cinza Original */
            transition: all 0.3s ease; 
            cursor: pointer;
        }
        .social-icon:hover { 
            fill: #D8A7B1; /* Cor Rose ao passar o mouse */
            transform: scale(1.2); 
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNÇÕES DE EMAIL ---
def enviar_email_confirmacao(nome_paciente, email_paciente, data, hora, servico):
    if "email" not in st.secrets: return
    try:
        remetente = st.secrets["email"]["usuario"]
        senha = st.secrets["email"]["senha"]
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = email_paciente
        msg['Subject'] = f"Confirmação: {servico} com Dra. Thais"
        corpo = f"Olá {nome_paciente},\n\nSeu agendamento está confirmado.\n\n📅 Data: {data}\n⏰ Horário: {hora}\n🦷 Procedimento: {servico}\n📍 Local: Taubaté/SP\n\nAtenciosamente,\nEquipe Dra. Thais Milene"
        msg.attach(MIMEText(corpo, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)
        
        # Copia para Dra
        msg_dra = MIMEMultipart()
        msg_dra['From'] = remetente
        msg_dra['To'] = remetente
        msg_dra['Subject'] = f"🔔 Novo Agendamento: {nome_paciente}"
        msg_dra.attach(MIMEText(f"Novo agendamento:\n{nome_paciente}\n{email_paciente}\n{data} - {hora}\n{serv}", 'plain'))
        server.send_message(msg_dra)
        server.quit()
        return True
    except: return False

# --- 5. CONEXÃO GOOGLE SHEETS ---
@st.cache_resource
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" not in st.secrets:
            st.error("⚠️ Segredo 'gcp_service_account' não encontrado."); return None
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds)
    except Exception as e: st.error(f"❌ Erro Técnico: {e}"); return None

def conectar_google_sheets():
    client = get_gspread_client()
    if client is None: return None
    try: return client.open_by_key(SHEET_ID).sheet1
    except Exception as e: st.sidebar.error(f"❌ Erro Planilha: {e}"); return None

def carregar_dados_gs():
    sheet = conectar_google_sheets()
    if sheet is None: return pd.DataFrame()
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        colunas = ['Nome', 'Telefone', 'Email', 'Data', 'Horario', 'Servico', 'Anamnese', 'Timestamp']
        if df.empty: return pd.DataFrame(columns=colunas)
        return df
    except: return pd.DataFrame()

def salvar_agendamento(nome, tel, email, data, hora, serv, anam):
    sheet = conectar_google_sheets()
    if sheet is None: return "Erro Conexão"
    try:
        data_br = data.strftime("%d/%m/%Y")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        sheet.append_row([str(nome), str(tel), str(email), str(data_br), str(hora), str(serv), str(anam), str(agora)])
        if email and "@" in email: enviar_email_confirmacao(nome, email, data_br, hora, serv)
        return "OK"
    except Exception as e: return f"Erro: {e}"

def get_horarios_ocupados(data_desejada):
    df = carregar_dados_gs()
    if df.empty: return []
    try:
        df['Data'] = df['Data'].astype(str)
        data_br = data_desejada.strftime("%d/%m/%Y")
        data_iso = str(data_desejada)
        return df[(df['Data'] == data_br) | (df['Data'] == data_iso)]['Horario'].tolist()
    except: return []

def buscar_paciente_login(dado_busca):
    df = carregar_dados_gs()
    if df.empty: return None
    dado_limpo = re.sub(r'\D', '', dado_busca)
    if 'Telefone' in df.columns:
        df['tel_temp'] = df['Telefone'].astype(str).apply(lambda x: re.sub(r'\D', '', x))
        res = df[df['tel_temp'] == dado_limpo]
        if not res.empty: return res.iloc[-1]
    if 'Email' in df.columns:
        res = df[df['Email'].astype(str).str.lower() == dado_busca.lower()]
        if not res.empty: return res.iloc[-1]
    return None

def buscar_agendamentos_cliente(t):
    df = carregar_dados_gs()
    if df.empty: return pd.DataFrame()
    l = re.sub(r'\D', '', t)
    if 'Telefone' not in df.columns: return pd.DataFrame()
    return df[df['Telefone'].astype(str).apply(lambda x: re.sub(r'\D', '', x)).str.contains(l, na=False)][['Data', 'Horario', 'Servico']]

def format_tel(t):
    n = re.sub(r'\D', '', t)
    return f"({n[:2]}) {n[2:7]}-{n[7:]}" if len(n) == 11 else t

# --- 6. LÓGICA DO SITE ---
if 'pagina' not in st.session_state: st.session_state.pagina = 'home'
def ir_para(p): st.session_state.pagina = p

if 'pre_nome' not in st.session_state: st.session_state.pre_nome = ""
if 'pre_tel' not in st.session_state: st.session_state.pre_tel = ""
if 'pre_email' not in st.session_state: st.session_state.pre_email = ""

# SIDEBAR
with st.sidebar:
    st.header("🔧 Admin")
    if st.button("Testar Conexão"):
        client = get_gspread_client()
        if client:
            try:
                sheet = client.open_by_key(SHEET_ID).sheet1
                st.success(f"✅ Conectado: {sheet.title}")
            except Exception as e: st.error(f"❌ Erro: {e}")
        else: st.error("Erro Secrets")
    st.write("---")
    if st.text_input("Senha", type="password") == "admin123":
        if st.button("Painel"): ir_para('admin_panel')

# --- TELA 1: HOME ---
if st.session_state.pagina == 'home':
    st.write("")
    
    dra_b64 = get_img_as_base64(CAMINHO_DRA)
    logo_b64 = get_img_as_base64(CAMINHO_LOGO)
    if dra_b64 and logo_b64:
        st.markdown(f"""
            <div class="header-container">
                <img src="data:image/jpeg;base64,{dra_b64}" class="header-dra">
                <img src="data:image/jpeg;base64,{logo_b64}" class="header-logo">
            </div>
        """, unsafe_allow_html=True)
    else: st.warning("Imagens não encontradas.")

    st.markdown("<h2 style='text-align:center; color:#2F2F33; margin-top:-10px; margin-bottom:5px'>Dra. Thais Milene</h2>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align:center; color:#7A7A7C; font-weight:normal; margin-bottom: 30px;'>Harmonização Orofacial & Odontologia</h5>", unsafe_allow_html=True)
    
    # BOTÕES PRINCIPAIS
    if st.button("✨ Agende sua Consulta", type="primary", use_container_width=True): 
        ir_para('agendar')
    
    st.write("") 
    
    if st.button("📂 Minhas Reservas", type="secondary", use_container_width=True): 
        ir_para('reservas')
        
    st.write("") 

    # BOTÕES DE LINK COM ÍCONES
    st.markdown("""
    <a href="https://wa.me/5512997997515" class="custom-link-btn" target="_blank">
        <svg class="btn-icon" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>
        Falar no WhatsApp
    </a>
    <a href="https://www.instagram.com/dra_thaism?igsh=MTBkeTVkZTZzMTR6eA==" class="custom-link-btn" target="_blank">
        <svg class="btn-icon" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
        Nosso Instagram
    </a>
    """, unsafe_allow_html=True)

    # --- RODAPÉ COM ÍCONES NOVOS ---
    st.markdown("""
        <div class="social-footer">
            <a href="https://www.instagram.com/dra_thaism?igsh=MTBkeTVkZTZzMTR6eA==" target="_blank" title="Instagram">
                <svg class="social-icon" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
            </a>
            <a href="https://wa.me/5512997997515" target="_blank" title="WhatsApp">
                <svg class="social-icon" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>
            </a>
            <a href="#" title="Site da Clínica (Em breve)">
                <svg class="social-icon" viewBox="0 0 24 24"><path d="M12 0c-4.198 0-8 3.403-8 7.602 0 4.198 3.469 9.21 8 16.398 4.531-7.188 8-12.2 8-16.398 0-4.199-3.801-7.602-8-7.602zm0 11c-1.657 0-3-1.343-3-3s1.343-3 3-3 3 1.343 3 3-1.343 3-3 3z"/></svg>
            </a>
            <a href="#" title="YouTube (Em breve)">
                <svg class="social-icon" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
            </a>
        </div>
        <div style='margin-top: 20px; text-align: center; color: #7A7A7C; font-size: 12px;'>
            <p>Taubaté/SP | CRO 12345<br>© 2025 Dra. Thais Milene</p>
        </div>
    """, unsafe_allow_html=True)

# TELA 2: AGENDAR
elif st.session_state.pagina == 'agendar':
    if st.button("⬅ Voltar"): ir_para('home'); st.rerun()
    st.markdown("<h2 style='color:#2F2F33;'>Ficha do Paciente</h2>", unsafe_allow_html=True)
    
    with st.expander("👋 Já possui cadastro? Clique aqui!"):
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1: busca = st.text_input("Celular ou E-mail:", placeholder="Ex: 12999999999")
        with c2: 
            st.write(""); st.write("")
            if st.button("🔍 Buscar"):
                p = buscar_paciente_login(busca)
                if p:
                    st.session_state.pre_nome = p['Nome']; st.session_state.pre_tel = p['Telefone']
                    st.session_state.pre_email = p.get('Email', '')
                    st.success(f"Olá, {p['Nome']}!"); time.sleep(1); st.rerun()
                else: st.warning("Não encontrado.")
        st.markdown("</div>", unsafe_allow_html=True)

    msg = st.container()
    with st.form("main"):
        st.markdown("<div class='section-header'>1. Agendamento</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1], gap="small")
        with c1: dt = st.date_input("📅 Data", min_value=datetime.today(), format="DD/MM/YYYY")
        with c2: serv = st.selectbox("🦷 Procedimento", list(PRECOS.keys()))
        
        try: occ = get_horarios_ocupados(dt)
        except: occ = []
        livres = [h for h in ["08:00","09:00","10:00","11:00","14:00","15:00","16:00","17:00"] if h not in occ] if dt.weekday() < 5 else []
        if dt.weekday() >= 5: st.warning("⚠️ Seg-Sex."); hr="Indisponível"
        else: hr = st.selectbox("⏰ Horário", livres) if livres else "Indisponível"
        if not livres and dt.weekday() < 5: st.warning("Lotado.")

        st.markdown("<div class='section-header'>2. Seus Dados</div>", unsafe_allow_html=True)
        nome = st.text_input("👤 Nome Completo", value=st.session_state.pre_nome)
        c3, c4 = st.columns(2)
        with c3: tel = st.text_input("📱 WhatsApp", value=st.session_state.pre_tel)
        with c4: email = st.text_input("📧 E-mail", value=st.session_state.pre_email)
        
        st.markdown("**🎂 Data de Nascimento**")
        d1,d2,d3 = st.columns([3,5,4], gap="small")
        with d1: dia = st.selectbox("Dia", range(1,32))
        with d2: mes = st.selectbox("Mês", ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"])
        with d3: ano = st.selectbox("Ano", range(datetime.now().year,1920,-1), index=30)
        try: nasc = date(ano, {"Janeiro":1,"Fevereiro":2,"Março":3,"Abril":4,"Maio":5,"Junho":6,"Julho":7,"Agosto":8,"Setembro":9,"Outubro":10,"Novembro":11,"Dezembro":12}[mes], dia)
        except: nasc = date(1990, 1, 1)
        gen = st.radio("Gênero", ["Feminino", "Masculino"], horizontal=True)

        st.markdown("<div class='section-header'>3. Sobre o Atendimento</div>", unsafe_allow_html=True)
        queixa = st.text_area("Queixa Principal", placeholder="O que te incomoda?")
        infos = st.text_area("Informações Importantes", placeholder="Alergias, remédios, medo...")

        if st.form_submit_button("✅ CONFIRMAR AGENDAMENTO", type="primary", use_container_width=True):
            tc = re.sub(r'\D','',tel)
            if len(nome)<3: msg.error("Nome inválido")
            elif len(tc)<10: msg.error("Zap inválido")
            elif hr=="Indisponível": msg.error("Horário inválido")
            else:
                ficha = f"[PERFIL] {datetime.now().year-ano}a|{gen}\n[QUEIXA] {queixa}\n[OBS] {infos}"
                res = salvar_agendamento(nome, format_tel(tc), email, dt, hr, serv, ficha)
                if res=="OK":
                    st.balloons()
                    msg_zap = f"Olá! Agendei {serv} dia {dt.strftime('%d/%m')} às {hr}."
                    st.markdown(f'<div class="ticket">✅ Confirmado!<br><b>{nome}</b><br>{dt.strftime("%d/%m")} - {hr}<br><small>Verifique seu e-mail!</small></div>', unsafe_allow_html=True)
                    st.markdown(f'<a href="https://wa.me/5512997997515?text={msg_zap}" target="_blank" class="big-button" style="background:#25D366;height:60px;font-size:16px;margin-top:10px;">📲 ENVIAR WHATSAPP</a>', unsafe_allow_html=True)
                    st.session_state.pre_nome="";st.session_state.pre_tel="";st.session_state.pre_email=""
                    time.sleep(10); ir_para('home'); st.rerun()
                else: msg.error(res)

# TELA 3: RESERVAS
elif st.session_state.pagina == 'reservas':
    if st.button("⬅ Voltar"): ir_para('home'); st.rerun()
    st.markdown("<h3 style='color:#2F2F33'>Minhas Reservas</h3>", unsafe_allow_html=True)
    t_busca = st.text_input("Seu WhatsApp")
    if st.button("🔎 Buscar"):
        df = buscar_agendamentos_cliente(t_busca)
        if not df.empty: st.dataframe(df, hide_index=True, use_container_width=True)
        else: st.warning("Nada encontrado.")

# TELA 4: ADMIN
elif st.session_state.pagina == 'admin_panel':
    if st.button("⬅ Sair"): ir_para('home'); st.rerun()
    df = carregar_dados_gs()
    if not df.empty: st.dataframe(df, use_container_width=True)
    else: st.info("Vazio.")
