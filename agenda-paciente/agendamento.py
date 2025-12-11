import streamlit as st
import pandas as pd
from datetime import datetime, date
import time
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Dra. Thais Milene", page_icon="🦷", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CONFIGURAÇÃO DA PLANILHA ---
SHEET_ID = "16YOR1odJ11iiUUI_y62FKb7GotQSRZeu64qP6RwZXrU"

# --- 3. ESTILO VISUAL (ROSE PREMIUM + LINKTREE) ---
st.markdown("""
    <style>
        /* Fundo Geral */
        .stApp { background-color: #F0E4E6; }
        
        /* -- ESTILIZAÇÃO DOS BOTÕES (PADRÃO UNIFICADO) -- */
        
        /* Botão Primário (Destaque Sólido) */
        div[data-testid="stButton"] button[kind="primary"], 
        div[data-testid="stLinkButton"] a[kind="primary"] { 
            background-color: #D8A7B1 !important; 
            color: white !important; 
            border: none !important;
            border-radius: 12px !important; 
            height: 60px !important; 
            font-size: 18px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 10px rgba(216, 167, 177, 0.3) !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            display: flex !important; align-items: center !important; justify-content: center !important;
        }
        
        /* Botão Secundário (Fundo Branco - Estilo Card) */
        div[data-testid="stButton"] button[kind="secondary"], 
        div[data-testid="stLinkButton"] a[kind="secondary"] { 
            background-color: #FFFFFF !important; 
            color: #2F2F33 !important; /* Grafite */
            border: 1px solid #E6E6E8 !important; /* Borda sutil */
            border-radius: 12px !important; 
            height: 60px !important; 
            font-size: 16px !important;
            font-weight: 500 !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            display: flex !important; align-items: center !important; justify-content: center !important;
        }
        
        /* Efeito Hover (Passar o mouse) */
        div[data-testid="stButton"] button:hover, div[data-testid="stLinkButton"] a:hover { 
            transform: translateY(-2px); 
            border-color: #D8A7B1 !important; 
            color: #D8A7B1 !important;
            box-shadow: 0 4px 12px rgba(216, 167, 177, 0.2) !important;
        }

        /* Inputs Clean */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] div, .stDateInput input, .stTextArea textarea { 
            background-color: #FFFFFF !important; 
            border: 1px solid #E6E6E8 !important; 
            border-radius: 10px !important; 
            color: #2F2F33 !important; padding-left: 12px;
        }
        .stTextInput input:focus, .stSelectbox div:focus, .stDateInput input:focus { 
            border-color: #D8A7B1 !important; 
            box-shadow: 0 0 0 2px rgba(216, 167, 177, 0.2) !important; 
        }
        
        /* Tipografia */
        h1, h2, h3 { color: #2F2F33 !important; font-family: 'Helvetica Neue', sans-serif; font-weight: 600; }
        p, label, .stMarkdown { color: #2F2F33 !important; font-family: 'Helvetica', sans-serif; }
        .stCaption { color: #7A7A7C !important; }
        
        /* Abas */
        .stTabs [data-baseweb="tab-list"] { gap: 5px; }
        .stTabs [data-baseweb="tab"] { height: 45px; background-color: rgba(255,255,255,0.5); border-radius: 8px 8px 0px 0px; }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF; border-bottom: 3px solid #D8A7B1; color: #2F2F33; font-weight: bold; }

        /* Ticket */
        .ticket { background-color: white; border: 1px solid #C9B49A; padding: 30px; border-radius: 12px; margin-top: 20px; text-align: center; position: relative; box-shadow: 0 10px 30px rgba(0,0,0,0.03); }
        .ticket::before { content: "✦"; color: #C9B49A; font-size: 20px; position: absolute; top: 10px; left: 50%; transform: translateX(-50%); }
        
        /* Cabeçalhos */
        .section-header { color: #2F2F33; font-size: 1.1em; font-weight: 600; margin-top: 25px; margin-bottom: 15px; border-left: 4px solid #D8A7B1; padding-left: 15px; background: linear-gradient(90deg, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0) 100%); padding-top: 8px; padding-bottom: 8px; border-radius: 0 8px 8px 0; }
        .login-box { background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid #E6E6E8; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.02); }
        
        /* Social Icons Footer */
        .social-footer { text-align: center; margin-top: 40px; }
        .social-footer a { margin: 0 10px; text-decoration: none; font-size: 24px; color: #7A7A7C; transition: color 0.3s; }
        .social-footer a:hover { color: #D8A7B1; }
        
        a { text-decoration: none; }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNÇÕES DE EMAIL ---
def enviar_email_confirmacao(nome_paciente, email_paciente, data, hora, servico):
    if "email" not in st.secrets: return
    remetente = st.secrets["email"]["usuario"]
    senha = st.secrets["email"]["senha"]
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = email_paciente
    msg['Subject'] = f"Confirmação: {servico} com Dra. Thais"
    corpo = f"Olá {nome_paciente},\n\nSeu agendamento está confirmado.\n\n📅 Data: {data}\n⏰ Horário: {hora}\n🦷 Procedimento: {servico}\n📍 Local: Taubaté/SP\n\nAtenciosamente,\nEquipe Dra. Thais Milene"
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)
        msg_dra = MIMEMultipart()
        msg_dra['From'] = remetente
        msg_dra['To'] = remetente
        msg_dra['Subject'] = f"🔔 Novo Agendamento: {nome_paciente}"
        msg_dra.attach(MIMEText(f"Novo paciente:\n{nome_paciente}\n{email_paciente}\n{data} - {hora}", 'plain'))
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

def buscar_agendamentos_cliente(telefone):
    df = carregar_dados_gs()
    if df.empty: return pd.DataFrame()
    tel_limpo = re.sub(r'\D', '', telefone)
    if 'Telefone' not in df.columns: return pd.DataFrame()
    df['tel_limpo'] = df['Telefone'].astype(str).apply(lambda x: re.sub(r'\D', '', x))
    return df[df['tel_limpo'].str.contains(tel_limpo, na=False)][['Data', 'Horario', 'Servico']]

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

# --- TELA 1: HOME (LINKTREE STYLE) ---
if st.session_state.pagina == 'home':
    st.write(""); c1, c2, c3 = st.columns([1, 2, 1])
    with c2: 
        try: st.image("logo.jpg", use_container_width=True)
        except: st.markdown("<h1 style='text-align:center; color:#D8A7B1'>Dra. Thais</h1>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align:center; color:#7A7A7C; font-weight:normal; margin-top:-10px; margin-bottom: 30px;'>Odontologia Especializada</h5>", unsafe_allow_html=True)
    
    # LISTA DE BOTÕES (MENU)
    # 1. Agendar (Destaque Rose)
    if st.button("✨ Agende sua Consulta", type="primary", use_container_width=True): 
        ir_para('agendar')
    
    st.write("") # Espaçamento
    
    # 2. Reservas (Branco Clean)
    if st.button("📂 Minhas Reservas", type="secondary", use_container_width=True): 
        ir_para('reservas')
        
    st.write("") 

    # 3. WhatsApp (Link Externo)
    st.link_button("💬 Falar no WhatsApp", "https://wa.me/5512997997515", type="secondary", use_container_width=True)
    
    st.write("")

    # 4. Localização
    st.link_button("📍 Localização (Maps)", "https://www.google.com/maps/search/?api=1&query=Taubaté+SP", type="secondary", use_container_width=True)
    
    st.write("")

    # 5. Instagram (Atualizado com link real)
    st.link_button("📷 Nosso Instagram", "https://www.instagram.com/dra_thaism?igsh=MTBkeTVkZTZzMTR6eA==", type="secondary", use_container_width=True)

    # Rodapé Social (Atualizado)
    st.markdown("""
        <div class="social-footer">
            <a href="https://www.instagram.com/dra_thaism?igsh=MTBkeTVkZTZzMTR6eA==" target="_blank">📷</a>
            <a href="https://wa.me/5512997997515" target="_blank">💬</a>
            <a href="mailto:contato@drathais.com" target="_blank">✉️</a>
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
        c_login1, c_login2 = st.columns([3, 1])
        with c_login1: busca_input = st.text_input("Celular ou E-mail:", placeholder="Ex: 12999999999")
        with c_login2: 
            st.write(""); st.write("")
            if st.button("🔍 Buscar"):
                p = buscar_paciente_login(busca_input)
                if p is not None:
                    st.session_state.pre_nome = p['Nome']; st.session_state.pre_tel = p['Telefone']
                    st.session_state.pre_email = p.get('Email', '')
                    st.success(f"Olá, {p['Nome']}!"); time.sleep(1); st.rerun()
                else: st.warning("Não encontrado.")
        st.markdown("</div>", unsafe_allow_html=True)

    msg = st.container()
    with st.form("form_anamnese"):
        st.markdown("<div class='section-header'>1. Agendamento</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1], gap="small")
        with c1: dt = st.date_input("📅 Data", min_value=datetime.today(), format="DD/MM/YYYY")
        with c2: serv = st.selectbox("🦷 Procedimento", ["Avaliação (1ª Vez)", "Limpeza", "Restauração", "Clareamento", "Harmonização", "Dor/Urgência"])
        
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

        st.markdown("<div class='section-header'>3. Saúde</div>", unsafe_allow_html=True)
        t1,t2,t3 = st.tabs(["🏥 Geral","🦷 Bucal","🚬 Hábitos"])
        with t1: diab=st.checkbox("Diabetes"); hip=st.checkbox("Pressão Alta"); alg=st.text_input("Alergias?"); rem=st.text_area("Remédios?")
        with t2: qx=st.text_area("Queixa"); sgr=st.checkbox("Sangramento")
        with t3: fum=st.radio("Fuma?", ["Não","Sim"])

        if st.form_submit_button("✅ CONFIRMAR AGENDAMENTO", type="primary", use_container_width=True):
            tc = re.sub(r'\D','',tel)
            if len(nome)<3: msg.error("Nome inválido")
            elif len(tc)<10: msg.error("Zap inválido")
            elif hr=="Indisponível": msg.error("Horário inválido")
            else:
                ficha = f"[PERFIL] {2025-ano}a|{gen}\n[QUEIXA] {qx}\n[SAUDE] Diab:{diab} Hip:{hip} Alg:{alg}\n[REM] {rem}"
                res = salvar_agendamento(nome, format_tel(tc), email, dt, hr, serv, ficha)
                if res=="OK":
                    st.balloons()
                    msg_zap = f"Olá! Agendei {serv} dia {dt.strftime('%d/%m')} às {hr}."
                    st.markdown(f'<div class="ticket">✅ Confirmado!<br><b>{nome}</b><br>{dt.strftime("%d/%m")} - {hr}</div>', unsafe_allow_html=True)
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
