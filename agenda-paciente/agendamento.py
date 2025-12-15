import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time
import re
import os
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build # BIBLIOTECA DO CALENDÁRIO (ESSENCIAL)

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Dra. Thais Milene", page_icon="🦷", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CONFIGURAÇÃO ---
SHEET_ID = "16YOR1odJ11iiUUI_y62FKb7GotQSRZeu64qP6RwZXrU"
CALENDAR_ID = "dra.thaismilene@gmail.com" # E-mail oficial da agenda

# Tabela de Preços (Estimativa para Dashboard)
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

# --- 3. ESTILO VISUAL (ROSE PREMIUM FINAL) ---
st.markdown("""
    <style>
        .stApp { background-color: #F0E4E6; }
        
        /* Esconder Menus Padrão */
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        div[data-testid="stToolbar"] {visibility: hidden; height: 0%; position: fixed;}
        div[data-testid="stDecoration"] {visibility: hidden; height: 0%;}
        div[data-testid="stStatusWidget"] {visibility: hidden;}
        .block-container { padding-top: 2rem !important; }

        /* Botões Nativos */
        .big-button { width: 100%; height: 120px; border-radius: 20px; color: white; font-size: 20px; font-weight: 600; cursor: pointer; margin-bottom: 15px; display: flex; align-items: center; justify-content: center; text-decoration: none; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .big-button:hover { transform: scale(1.02); }
        
        div[data-testid="stButton"] button[kind="primary"] { background-color: #D8A7B1 !important; color: white !important; border: none; border-radius: 12px; height: 60px; font-size: 18px; font-weight: 600; box-shadow: 0 4px 10px rgba(216, 167, 177, 0.3); width: 100%; }
        div[data-testid="stButton"] button[kind="secondary"] { background-color: #FFFFFF !important; color: #2F2F33 !important; border: 1px solid #E6E6E8; border-radius: 12px; height: 60px; font-size: 16px; font-weight: 500; width: 100%; }
        
        /* Links Personalizados (FIX AZUL & ÍCONES) */
        a.custom-link-btn { 
            display: flex !important; align-items: center !important; justify-content: center !important; 
            width: 100% !important; height: 60px !important; 
            background-color: #FFFFFF !important; color: #2F2F33 !important; 
            border: 1px solid #E6E6E8 !important; border-radius: 12px !important; 
            text-decoration: none !important; font-size: 16px !important; font-weight: 500 !important; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important; transition: all 0.3s ease !important; 
            margin-bottom: 15px !important; 
        }
        a.custom-link-btn:hover { 
            transform: translateY(-2px); border-color: #D8A7B1 !important; 
            color: #D8A7B1 !important; box-shadow: 0 4px 12px rgba(216, 167, 177, 0.2) !important; 
        }
        /* Ícone dentro do botão */
        a.custom-link-btn svg {
            width: 24px !important; height: 24px !important; 
            margin-right: 12px !important; fill: currentColor !important; 
            transition: fill 0.3s ease !important;
        }

        /* Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] div, .stDateInput input, .stTextArea textarea { background-color: #FFFFFF !important; border: 1px solid #E6E6E8 !important; border-radius: 10px !important; color: #2F2F33 !important; padding-left: 12px; }
        .stTextInput input:focus, .stSelectbox div:focus, .stDateInput input:focus { border-color: #D8A7B1 !important; box-shadow: 0 0 0 2px rgba(216, 167, 177, 0.2) !important; }
        
        /* Dashboard & Layout */
        .metric-card { background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #D8A7B1; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; margin-bottom: 10px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2F2F33; }
        .metric-label { font-size: 14px; color: #7A7A7C; }
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
        
        /* Rodapé Social */
        .social-footer { display: flex; justify-content: center; gap: 25px; margin-top: 40px; margin-bottom: 20px; }
        .social-icon { width: 24px !important; height: 24px !important; fill: #7A7A7C; transition: all 0.3s ease; cursor: pointer; }
        .social-icon:hover { fill: #D8A7B1; transform: scale(1.1); }
    </style>
""", unsafe_allow_html=True)

# --- 4. CREDENCIAIS UNIFICADAS ---
@st.cache_resource
def get_credentials():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds", 
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/calendar" # Agenda Ativada
        ]
        if "gcp_service_account" not in st.secrets:
            st.error("⚠️ Segredos não encontrados."); return None
        return ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    except: return None

# --- 5. INTEGRAÇÕES ---
def conectar_google_sheets():
    creds = get_credentials()
    if not creds: return None
    try:
        client = gspread.authorize(creds)
        return client.open_by_key(SHEET_ID).sheet1
    except: return None

def adicionar_ao_calendar(nome, tel, data_obj, hora_str, servico):
    """Cria evento no Google Calendar"""
    creds = get_credentials()
    if not creds: return "Erro Credenciais"
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        # Formata data para ISO
        start_time = f"{data_obj.strftime('%Y-%m-%d')}T{hora_str}:00"
        end_time_obj = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=1)
        end_time = end_time_obj.strftime("%Y-%m-%dT%H:%M:%S")
        
        evento = {
            'summary': f"🦷 {nome} - {servico}",
            'location': 'Consultório Dra Thais',
            'description': f"Paciente: {nome}\nTel: {tel}\nServiço: {servico}\nAgendado pelo Site.",
            'start': {'dateTime': start_time, 'timeZone': 'America/Sao_Paulo'},
            'end': {'dateTime': end_time, 'timeZone': 'America/Sao_Paulo'},
            'colorId': '11', # Vermelho/Rosa
        }
        
        service.events().insert(calendarId=CALENDAR_ID, body=evento).execute()
        return "OK"
    except Exception as e:
        return f"Erro: {e}"

def enviar_email(nome, email, data, hora, serv):
    if "email" not in st.secrets: return
    try:
        remetente = st.secrets["email"]["usuario"]
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = email
        msg['Subject'] = f"Confirmação: {serv} com Dra. Thais"
        corpo = f"Olá {nome},\n\nSeu agendamento está confirmado.\n\n📅 Data: {data}\n⏰ Horário: {hora}\n🦷 Procedimento: {serv}\n\nAtenciosamente,\nEquipe Dra. Thais Milene"
        msg.attach(MIMEText(corpo, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, st.secrets["email"]["senha"])
        server.send_message(msg)
        
        # Cópia para Dra
        msg_dra = MIMEMultipart()
        msg_dra['From'] = remetente
        msg_dra['To'] = CALENDAR_ID # Usa o email profissional para receber cópia
        msg_dra['Subject'] = f"🔔 Novo Paciente: {nome}"
        msg_dra.attach(MIMEText(f"Novo agendamento:\n{nome}\n{email}\n{data} - {hora}\n{serv}", 'plain'))
        server.send_message(msg_dra)
        server.quit()
    except: pass

# --- 6. OPERAÇÕES ---
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
    if sheet is None: return "Erro Conexão Planilha"
    try:
        data_br = data.strftime("%d/%m/%Y")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        sheet.append_row([str(nome), str(tel), str(email), str(data_br), str(hora), str(serv), str(anam), str(agora)])
        
        # Integrações
        if email and "@" in email: enviar_email(nome, email, data_br, hora, serv)
        
        # Tenta salvar no Calendar (avisa no console se falhar, mas não trava o usuário)
        res_cal = adicionar_ao_calendar(nome, tel, data, hora, serv)
        if res_cal != "OK": print(f"Aviso Calendar: {res_cal}")
            
        return "OK"
    except Exception as e: return f"Erro Geral: {e}"

def get_horarios_ocupados(data_desejada):
    df = carregar_dados_gs()
    if df.empty: return []
    try:
        df['Data'] = df['Data'].astype(str)
        return df[df['Data'].isin([data_desejada.strftime("%d/%m/%Y"), str(data_desejada)])]['Horario'].tolist()
    except: return []

def buscar_paciente_login(dado_busca):
    df = carregar_dados_gs()
    if df.empty: return None
    limpo = re.sub(r'\D', '', dado_busca)
    if 'Telefone' in df.columns:
        res = df[df['Telefone'].astype(str).apply(lambda x: re.sub(r'\D', '', x)) == limpo]
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

# --- 7. NAVEGAÇÃO ---
if 'pagina' not in st.session_state: st.session_state.pagina = 'home'
def ir_para(p): st.session_state.pagina = p

if 'pre_nome' not in st.session_state: st.session_state.pre_nome = ""
if 'pre_tel' not in st.session_state: st.session_state.pre_tel = ""
if 'pre_email' not in st.session_state: st.session_state.pre_email = ""

# --- ÁREA ADMIN PROTEGIDA ---
with st.sidebar:
    with st.expander("🔐 Acesso Restrito"):
        senha_admin = st.text_input("Senha", type="password", key="admin_pass")
        if senha_admin == "admin123":
            st.success("🔓 Acesso Liberado")
            st.markdown("---")
            if st.button("📊 Painel Financeiro"): ir_para('admin_panel')
            
            st.markdown("**Diagnóstico**")
            if st.button("🔌 Testar Conexões"):
                c = conectar_google_sheets()
                if c: st.success("✅ Planilha OK")
                else: st.error("❌ Erro Planilha")
            
            if st.button("📅 Testar Agenda Google"):
                res = adicionar_ao_calendar("Teste", "00", datetime.now(), "08:00", "Teste Site")
                if res == "OK": st.success("✅ Agenda OK")
                else: 
                    st.error(f"❌ Falha: {res}")
                    if "403" in res: st.info("Dica: Verifique permissão de 'Alterar Eventos' no Google Calendar.")

# --- TELA 1: HOME ---
if st.session_state.pagina == 'home':
    st.write("")
    
    dra_b64 = get_img_as_base64(CAMINHO_DRA)
    logo_b64 = get_img_as_base64(CAMINHO_LOGO)
    if dra_b64 and logo_b64:
        st.markdown(f"""<div class="header-container"><img src="data:image/jpeg;base64,{dra_b64}" class="header-dra"><img src="data:image/jpeg;base64,{logo_b64}" class="header-logo"></div>""", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align:center; color:#2F2F33; margin-top:-10px; margin-bottom:5px'>Dra. Thais Milene</h2>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align:center; color:#7A7A7C; font-weight:normal; margin-bottom: 30px;'>Harmonização Orofacial & Odontologia</h5>", unsafe_allow_html=True)
    
    if st.button("✨ Agende sua Consulta", type="primary", use_container_width=True): ir_para('agendar')
    st.write("") 
    if st.button("📂 Minhas Reservas", type="secondary", use_container_width=True): ir_para('reservas')
    st.write("") 

    st.markdown("""
    <a href="https://wa.me/5512997997515" class="custom-link-btn" target="_blank"><svg class="btn-icon" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>Falar no WhatsApp</a>
    <a href="https://www.google.com/maps/search/?api=1&query=Taubaté+SP" class="custom-link-btn" target="_blank"><svg class="btn-icon" viewBox="0 0 24 24"><path d="M12 0c-4.198 0-8 3.403-8 7.602 0 4.198 3.469 9.21 8 16.398 4.531-7.188 8-12.2 8-16.398 0-4.199-3.801-7.602-8-7.602zm0 11c-1.657 0-3-1.343-3-3s1.343-3 3-3 3 1.343 3 3-1.343 3-3 3z"/></svg>Localização (Maps)</a>
    <a href="https://www.instagram.com/dra_thaism?igsh=MTBkeTVkZTZzMTR6eA==" class="custom-link-btn" target="_blank"><svg class="btn-icon" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>Nosso Instagram</a>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="social-footer">
            <a href="https://www.instagram.com/dra_thaism?igsh=MTBkeTVkZTZzMTR6eA==" target="_blank" title="Instagram"><svg class="social-icon" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg></a>
            <a href="#" title="Site"><svg class="social-icon" viewBox="0 0 24 24"><path d="M12 0c-4.198 0-8 3.403-8 7.602 0 4.198 3.469 9.21 8 16.398 4.531-7.188 8-12.2 8-16.398 0-4.199-3.801-7.602-8-7.602zm0 11c-1.657 0-3-1.343-3-3s1.343-3 3-3 3 1.343 3 3-1.343 3-3 3z"/></svg></a>
            <a href="#" title="YouTube"><svg class="social-icon" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg></a>
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
    st.title("📊 Painel da Dra. Thais")
    df = carregar_dados_gs()
    if not df.empty:
        df['Faturamento'] = df['Servico'].map(PRECOS).fillna(0)
        mes = datetime.now().strftime("%m/%Y")
        try:
            df['DataObj'] = pd.to_datetime(df['Data'], format="%d/%m/%Y", errors='coerce')
            df_mes = df[df['DataObj'].dt.strftime("%m/%Y") == mes]
            fat = df_mes['Faturamento'].sum(); qtd = len(df_mes)
        except: fat=0; qtd=0
        
        m1,m2,m3 = st.columns(3)
        with m1: st.markdown(f"<div class='metric-card'><div class='metric-label'>Total</div><div class='metric-value'>{len(df)}</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-card'><div class='metric-label'>Faturamento ({mes})</div><div class='metric-value'>R$ {fat:,.2f}</div></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-card'><div class='metric-label'>Pacientes Mês</div><div class='metric-value'>{qtd}</div></div>", unsafe_allow_html=True)
        
        st.write(""); st.subheader("📈 Procedimentos")
        st.bar_chart(df['Servico'].value_counts(), color="#D8A7B1")
        with st.expander("📋 Ver Tabela"): st.dataframe(df[['Data','Horario','Nome','Servico']], use_container_width=True)
    else: st.info("Sem dados.")
