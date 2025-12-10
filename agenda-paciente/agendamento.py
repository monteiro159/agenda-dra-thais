import streamlit as st
import pandas as pd
from datetime import datetime, date
import time
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Dra. Thais Milene", page_icon="🦷", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CONFIGURAÇÃO DA PLANILHA ---
SHEET_ID = "16YOR1odJ11iiUUI_y62FKb7GotQSRZeu64qP6RwZXrU"

# --- 3. ESTILO VISUAL ---
st.markdown("""
    <style>
        .stApp { background-color: #FCEEF5; }
        .big-button { width: 100%; height: 120px; border-radius: 20px; color: white; font-size: 20px; font-weight: bold; cursor: pointer; margin-bottom: 15px; display: flex; align-items: center; justify-content: center; text-decoration: none; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .big-button:hover { transform: scale(1.02); }
        div[data-testid="stButton"] button[kind="primary"] { background-color: #9A2A5A; color: white !important; border: none; border-radius: 12px; height: 50px; font-size: 16px; }
        div[data-testid="stButton"] button[kind="secondary"] { background-color: #FFFFFF; color: #9A2A5A !important; border: 1px solid #F3D0DE; border-radius: 12px; height: 50px; font-size: 16px; }
        .stTextInput input, .stSelectbox div[data-baseweb="select"] div, .stDateInput input, .stTextArea textarea { background-color: #FFFFFF !important; border: 1px solid #E3CWD8 !important; border-radius: 12px !important; color: #495057 !important; padding-left: 10px; }
        .stTextInput input:focus, .stSelectbox div:focus, .stDateInput input:focus { border-color: #9A2A5A !important; box-shadow: 0 0 0 1px #9A2A5A !important; }
        h1, h2, h3, p, label, .stMarkdown { color: #5D4050 !important; font-family: 'Helvetica', sans-serif; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { height: 40px; background-color: rgba(255,255,255,0.5); border-radius: 4px 4px 0px 0px; }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF; border-bottom: 2px solid #9A2A5A; color: #9A2A5A; }
        .ticket { background-color: white; border: 1px dashed #9A2A5A; padding: 20px; border-radius: 10px; margin-top: 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .anamnese-header { color: #9A2A5A; font-weight: 700; margin-top: 20px; margin-bottom: 8px; border-left: 5px solid #9A2A5A; padding-left: 10px; background-color: rgba(255,255,255,0.5); }
    </style>
""", unsafe_allow_html=True)

# --- 4. CONEXÃO GOOGLE SHEETS ---

@st.cache_resource
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" not in st.secrets:
            st.error("⚠️ Segredo 'gcp_service_account' não encontrado.")
            return None
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Erro Técnico na Autenticação: {e}")
        return None

def conectar_google_sheets():
    client = get_gspread_client()
    if client is None: return None
    try:
        return client.open_by_key(SHEET_ID).sheet1
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao abrir planilha: {e}")
        return None

def carregar_dados_gs():
    sheet = conectar_google_sheets()
    if sheet is None: return pd.DataFrame()
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        colunas = ['Nome', 'Telefone', 'Data', 'Horario', 'Servico', 'Anamnese', 'Timestamp']
        if df.empty: return pd.DataFrame(columns=colunas)
        return df
    except: return pd.DataFrame()

def salvar_agendamento(nome, tel, data, hora, serv, anam):
    sheet = conectar_google_sheets()
    if sheet is None: return "Erro de Conexão com Planilha"
    try:
        data_br = data.strftime("%d/%m/%Y")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        sheet.append_row([str(nome), str(tel), str(data_br), str(hora), str(serv), str(anam), str(agora)])
        return "OK"
    except Exception as e: return f"Erro ao gravar: {e}"

def get_horarios_ocupados(data_desejada):
    df = carregar_dados_gs()
    if df.empty: return []
    try:
        df['Data'] = df['Data'].astype(str)
        data_br = data_desejada.strftime("%d/%m/%Y")
        data_iso = str(data_desejada)
        return df[(df['Data'] == data_br) | (df['Data'] == data_iso)]['Horario'].tolist()
    except: return []

def buscar_agendamentos_cliente(telefone):
    df = carregar_dados_gs()
    if df.empty: return pd.DataFrame()
    tel_limpo_busca = re.sub(r'\D', '', telefone)
    if 'Telefone' not in df.columns: return pd.DataFrame()
    df['tel_limpo'] = df['Telefone'].astype(str).apply(lambda x: re.sub(r'\D', '', x))
    res = df[df['tel_limpo'].str.contains(tel_limpo_busca, na=False)]
    return res[['Data', 'Horario', 'Servico']] if not res.empty else pd.DataFrame()

def formatar_telefone(tel):
    nums = re.sub(r'\D', '', tel)
    if len(nums) == 11: return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"
    if len(nums) == 10: return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    return tel

# --- 5. LÓGICA DO SITE ---
if 'pagina' not in st.session_state: st.session_state.pagina = 'home'
def ir_para(pagina): st.session_state.pagina = pagina

# SIDEBAR: Diagnóstico e Admin
with st.sidebar:
    st.header("🔧 Admin")
    
    if st.button("Testar Conexão"):
        client = get_gspread_client()
        if client:
            # MOSTRA O EMAIL QUE ESTÁ SENDO USADO
            email_robo = st.secrets["gcp_service_account"]["client_email"]
            st.info(f"🤖 Email do Robô:")
            st.code(email_robo)
            st.warning("⚠️ Copie o email acima e garanta que ele está no botão 'Compartilhar' da planilha como Editor.")
            
            try:
                sheet = client.open_by_key(SHEET_ID).sheet1
                st.success(f"✅ Conectado: {sheet.title}")
            except Exception as e:
                st.error(f"❌ Erro: {type(e).__name__}")
                st.error(f"Detalhe: {e}")
                if "Permission" in str(e):
                    st.error("Dica: Ative a 'Google Drive API' no console do Google Cloud.")
        else:
            st.error("Erro nos Segredos")
    
    st.write("---")
    if st.text_input("Senha", type="password") == "admin123":
        if st.button("Painel"): ir_para('admin_panel')

# HOME
if st.session_state.pagina == 'home':
    st.write(""); c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        try: st.image("logo.jpg", use_container_width=True)
        except: st.markdown("<h1 style='text-align:center; color:#9A2A5A'>Dra. Thais</h1>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align:center; color:#8C6B7A; font-weight:normal; margin-top:-15px'>Odontologia Especializada</h5>", unsafe_allow_html=True)
    st.write("---")
    if st.button("✨  NOVO AGENDAMENTO", type="primary", use_container_width=True): ir_para('agendar')
    st.write("")
    if st.button("📂  MINHAS RESERVAS", type="secondary", use_container_width=True): ir_para('reservas')
    st.markdown("<div style='margin-top: 60px; text-align: center; color: #999; font-size: 12px;'><p>📍 Taubaté/SP | CRO 12345</p></div>", unsafe_allow_html=True)

# AGENDAR
elif st.session_state.pagina == 'agendar':
    if st.button("⬅ Voltar"): ir_para('home'); st.rerun()
    st.markdown("<h2 style='color:#9A2A5A;'>Ficha do Paciente</h2>", unsafe_allow_html=True)
    msg = st.container()
    
    with st.form("form_anamnese"):
        st.markdown("<div class='anamnese-header'>1. Agendamento</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1], gap="small")
        with c1: data_agend = st.date_input("📅 Data", min_value=datetime.today(), format="DD/MM/YYYY")
        with c2: servico = st.selectbox("🦷 Procedimento", ["Avaliação (1ª Vez)", "Limpeza", "Restauração", "Clareamento", "Harmonização", "Dor/Urgência"])
        
        try: ocupados = get_horarios_ocupados(data_agend)
        except: ocupados = []
        horarios = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        livres = [h for h in horarios if h not in ocupados] if data_agend.weekday() < 5 else []
        
        if data_agend.weekday() >= 5: st.warning("⚠️ Apenas Seg-Sex."); hora="Indisponível"
        else: hora = st.selectbox("⏰ Horário", livres) if livres else "Indisponível"
        if not livres and data_agend.weekday() < 5: st.warning("Dia lotado.")

        st.markdown("<div class='anamnese-header'>2. Seus Dados</div>", unsafe_allow_html=True)
        nome = st.text_input("👤 Nome Completo")
        tel = st.text_input("📱 WhatsApp (DDD+Número)")
        
        st.markdown("**🎂 Data de Nascimento**")
        d1, d2, d3 = st.columns([3, 5, 4], gap="small")
        with d1: dia = st.selectbox("Dia", list(range(1, 32)))
        with d2: mes_nome = st.selectbox("Mês", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
        with d3: ano = st.selectbox("Ano", list(range(datetime.now().year, 1920, -1)), index=30)
        
        meses = {"Janeiro":1, "Fevereiro":2, "Março":3, "Abril":4, "Maio":5, "Junho":6, "Julho":7, "Agosto":8, "Setembro":9, "Outubro":10, "Novembro":11, "Dezembro":12}
        try: nasc = date(ano, meses[mes_nome], dia)
        except: nasc = date(1990, 1, 1)
        genero = st.radio("Gênero", ["Feminino", "Masculino"], horizontal=True)

        st.markdown("<div class='anamnese-header'>3. Saúde</div>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["🏥 Geral", "🦷 Bucal", "🚬 Hábitos"])
        with t1:
            diabetes = st.checkbox("Diabetes"); hiper = st.checkbox("Pressão Alta")
            cardiaco = st.checkbox("Cardíaco"); resp = st.checkbox("Respiratório")
            renal = st.checkbox("Renal"); gest = st.checkbox("Gestante")
            st.divider()
            alergia = st.text_input("Tem Alergias? Quais?")
            remedio = st.text_area("Toma algum remédio de uso contínuo?")
        with t2:
            queixa = st.text_area("Queixa Principal")
            sangra = st.checkbox("Gengiva Sangra"); sensivel = st.checkbox("Dente Sensível")
        with t3:
            fuma = st.radio("Fuma?", ["Não", "Sim"]); bebe = st.checkbox("Bebe álcool?")

        if st.form_submit_button("✅ CONFIRMAR", type="primary", use_container_width=True):
            tel_clean = re.sub(r'\D', '', tel)
            if len(nome) < 3: msg.error("Nome inválido")
            elif len(tel_clean) < 10: msg.error("WhatsApp inválido")
            elif hora == "Indisponível": msg.error("Horário indisponível")
            else:
                idade = (date.today() - nasc).days // 365
                saude = f"Diabetes:{diabetes}, Hiper:{hiper}, Card:{cardiaco}, Gest:{gest}, Alergia:{alergia}"
                ficha = f"[PERFIL] {idade}a | {genero}\n[QUEIXA] {queixa}\n[SAUDE] {saude}\n[REMEDIO] {remedio}"
                
                res = salvar_agendamento(nome, formatar_telefone(tel_clean), data_agend, hora, servico, ficha)
                if res == "OK":
                    st.balloons()
                    msg_zap = f"Olá! Agendei {servico} dia {data_agend.strftime('%d/%m')} às {hora}."
                    st.markdown(f'<div class="ticket">✅ Confirmado!<br>{nome}<br>{data_agend.strftime("%d/%m")} - {hora}</div>', unsafe_allow_html=True)
                    st.markdown(f'<a href="https://wa.me/5512987054320?text={msg_zap}" target="_blank" class="big-button" style="background:#25D366; height:60px; font-size:16px;">📲 ENVIAR WHATSAPP</a>', unsafe_allow_html=True)
                    time.sleep(10); ir_para('home'); st.rerun()
                else: msg.error(res)

# RESERVAS
elif st.session_state.pagina == 'reservas':
    if st.button("⬅ Voltar"): ir_para('home'); st.rerun()
    tel_busca = st.text_input("Seu WhatsApp")
    if st.button("🔎 Buscar"):
        df = buscar_agendamentos_cliente(tel_busca)
        if not df.empty: st.dataframe(df, hide_index=True, use_container_width=True)
        else: st.warning("Nada encontrado.")

# ADMIN
elif st.session_state.pagina == 'admin_panel':
    if st.button("⬅ Sair"): ir_para('home'); st.rerun()
    df = carregar_dados_gs()
    if not df.empty: st.dataframe(df, use_container_width=True)
    else: st.info("Vazio.")
