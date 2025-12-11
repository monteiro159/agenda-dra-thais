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
# ID da planilha (o código no meio do link)
SHEET_ID = "16YOR1odJ11iiUUI_y62FKb7GotQSRZeu64qP6RwZXrU"

# --- 3. ESTILO VISUAL (NOVA PALETA PREMIUM) ---
st.markdown("""
    <style>
        /* Fundo Rose Neutro / Pó */
        .stApp { background-color: #F0E4E6; }
        
        /* Botões Estilo Card */
        .big-button { 
            width: 100%; height: 120px; border-radius: 15px; 
            color: white; font-size: 20px; font-weight: 600; 
            cursor: pointer; margin-bottom: 15px; display: flex; 
            align-items: center; justify-content: center; text-decoration: none; 
            transition: transform 0.2s, box-shadow 0.2s; 
            box-shadow: 0 4px 20px rgba(216, 167, 177, 0.25); /* Sombra suave Rose */
            background-color: #D8A7B1; /* Rose Principal */
        }
        .big-button:hover { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(216, 167, 177, 0.4); }

        /* Botões Padrão Streamlit */
        div[data-testid="stButton"] button { border-radius: 8px; height: 50px; font-weight: 500; border: none; letter-spacing: 0.5px; }
        
        /* Botão Primário (Rose Principal) */
        div[data-testid="stButton"] button[kind="primary"] { 
            background-color: #D8A7B1; color: white !important; font-size: 16px; 
            box-shadow: 0 4px 10px rgba(216, 167, 177, 0.3);
        }
        div[data-testid="stButton"] button[kind="primary"]:hover { background-color: #C08E98; }
        
        /* Botão Secundário (Clean) */
        div[data-testid="stButton"] button[kind="secondary"] { 
            background-color: #FFFFFF; color: #2F2F33 !important; /* Grafite */
            border: 1px solid #E6E6E8; /* Cinza Clean */
            font-size: 16px; 
        }
        div[data-testid="stButton"] button[kind="secondary"]:hover { border-color: #D8A7B1; color: #D8A7B1 !important; }

        /* Inputs Modernos & Clean */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] div, .stDateInput input, .stTextArea textarea { 
            background-color: #FFFFFF !important; 
            border: 1px solid #E6E6E8 !important; /* Cinza Clean */
            border-radius: 8px !important; 
            color: #2F2F33 !important; /* Grafite */
            padding-left: 12px;
        }
        /* Foco com Dourado Desaturado ou Rose */
        .stTextInput input:focus, .stSelectbox div:focus, .stDateInput input:focus { 
            border-color: #D8A7B1 !important; 
            box-shadow: 0 0 0 1px #D8A7B1 !important; 
        }
        
        /* Tipografia */
        h1, h2, h3 { color: #2F2F33 !important; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 600; }
        p, label, .stMarkdown { color: #2F2F33 !important; font-family: 'Helvetica', sans-serif; }
        .stCaption { color: #7A7A7C !important; } /* Cinza Médio */
        
        /* Abas Elegantes */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { 
            height: 45px; background-color: rgba(255,255,255,0.6); 
            border-radius: 8px 8px 0px 0px; border: none; color: #7A7A7C;
        }
        .stTabs [aria-selected="true"] { 
            background-color: #FFFFFF; 
            border-bottom: 3px solid #D8A7B1; /* Rose Principal */
            color: #2F2F33; font-weight: bold;
        }

        /* Ticket Premium com Dourado */
        .ticket { 
            background-color: white; 
            border: 1px dashed #C9B49A; /* Dourado Desaturado */
            padding: 25px; border-radius: 12px; margin-top: 25px; 
            text-align: center; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.03); 
        }
        
        /* Cabeçalhos de Seção */
        .anamnese-header { 
            color: #2F2F33; /* Grafite */
            font-weight: 600; margin-top: 25px; margin-bottom: 12px; 
            border-left: 4px solid #D8A7B1; /* Rose Principal */
            padding-left: 15px; 
            background: linear-gradient(90deg, rgba(255,255,255,0.5) 0%, rgba(255,255,255,0) 100%);
            padding-top: 5px; padding-bottom: 5px; 
        }
        
        .login-box { 
            background-color: #FFFFFF; padding: 20px; border-radius: 12px; 
            border: 1px solid #E6E6E8; margin-bottom: 25px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        }
        
        /* Checkbox Moderno */
        .stCheckbox label span { color: #2F2F33; }
        
        /* Ajuste link whatsapp */
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
    
    corpo = f"""
    Olá {nome_paciente},
    
    Seu agendamento está confirmado.
    
    📅 Data: {data}
    ⏰ Horário: {hora}
    🦷 Procedimento: {servico}
    📍 Local: Taubaté/SP
    
    Caso precise reagendar, por favor nos avise.
    
    Atenciosamente,
    Equipe Dra. Thais Milene
    """
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
        msg_dra.attach(MIMEText(f"Novo paciente agendado:\nNome: {nome_paciente}\nTel: {email_paciente}\nData: {data} - {hora}", 'plain'))
        server.send_message(msg_dra)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro email: {e}")
        return False

# --- 5. CONEXÃO GOOGLE SHEETS ---

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
        colunas = ['Nome', 'Telefone', 'Email', 'Data', 'Horario', 'Servico', 'Anamnese', 'Timestamp']
        if df.empty: return pd.DataFrame(columns=colunas)
        return df
    except: return pd.DataFrame()

def salvar_agendamento(nome, tel, email, data, hora, serv, anam):
    sheet = conectar_google_sheets()
    if sheet is None: return "Erro de Conexão com Planilha"
    try:
        data_br = data.strftime("%d/%m/%Y")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        sheet.append_row([str(nome), str(tel), str(email), str(data_br), str(hora), str(serv), str(anam), str(agora)])
        
        if email and "@" in email:
            enviar_email_confirmacao(nome, email, data_br, hora, serv)
            
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

def buscar_paciente_login(dado_busca):
    df = carregar_dados_gs()
    if df.empty: return None
    
    dado_limpo = re.sub(r'\D', '', dado_busca)
    
    if 'Telefone' in df.columns:
        df['tel_temp'] = df['Telefone'].astype(str).apply(lambda x: re.sub(r'\D', '', x))
        resultado = df[df['tel_temp'] == dado_limpo]
        if not resultado.empty: return resultado.iloc[-1]
        
    if 'Email' in df.columns:
        resultado = df[df['Email'].astype(str).str.lower() == dado_busca.lower()]
        if not resultado.empty: return resultado.iloc[-1]
        
    return None

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

# --- 6. LÓGICA DO SITE ---
if 'pagina' not in st.session_state: st.session_state.pagina = 'home'
def ir_para(pagina): st.session_state.pagina = pagina

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
            except Exception as e:
                st.error(f"❌ Erro: {e}")
        else: st.error("Erro Secrets")
    st.write("---")
    if st.text_input("Senha", type="password") == "admin123":
        if st.button("Painel"): ir_para('admin_panel')

# HOME
if st.session_state.pagina == 'home':
    st.write(""); c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        try: st.image("logo.jpg", use_container_width=True)
        except: st.markdown("<h1 style='text-align:center; color:#2F2F33'>Dra. Thais</h1>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align:center; color:#7A7A7C; font-weight:normal; margin-top:-15px'>Odontologia Especializada</h5>", unsafe_allow_html=True)
    st.write("---")
    if st.button("✨  NOVO AGENDAMENTO", type="primary", use_container_width=True): ir_para('agendar')
    st.write("")
    if st.button("📂  MINHAS RESERVAS", type="secondary", use_container_width=True): ir_para('reservas')
    st.markdown("<div style='margin-top: 60px; text-align: center; color: #7A7A7C; font-size: 12px;'><p>📍 Taubaté/SP | CRO 12345</p></div>", unsafe_allow_html=True)

# AGENDAR
elif st.session_state.pagina == 'agendar':
    if st.button("⬅ Voltar"): ir_para('home'); st.rerun()
    st.markdown("<h2 style='color:#2F2F33;'>Ficha do Paciente</h2>", unsafe_allow_html=True)
    
    with st.expander("👋 Já possui cadastro? Clique aqui!"):
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        c_login1, c_login2 = st.columns([3, 1])
        with c_login1:
            busca_input = st.text_input("Digite seu Celular ou E-mail:", placeholder="Ex: 12999999999")
        with c_login2:
            st.write("")
            st.write("")
            btn_buscar = st.button("🔍 Buscar")
        
        if btn_buscar:
            paciente_enc = buscar_paciente_login(busca_input)
            if paciente_enc is not None:
                st.session_state.pre_nome = paciente_enc['Nome']
                st.session_state.pre_tel = paciente_enc['Telefone']
                st.session_state.pre_email = paciente_enc.get('Email', '') 
                st.success(f"Bem-vindo(a) de volta, {paciente_enc['Nome']}!")
                time.sleep(1); st.rerun()
            else:
                st.warning("Cadastro não encontrado.")
        st.markdown("</div>", unsafe_allow_html=True)

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
        nome = st.text_input("👤 Nome Completo", value=st.session_state.pre_nome)
        c_contato1, c_contato2 = st.columns(2)
        with c_contato1: tel = st.text_input("📱 WhatsApp (DDD+Número)", value=st.session_state.pre_tel)
        with c_contato2: email = st.text_input("📧 E-mail (Opcional)", value=st.session_state.pre_email)
        
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
                
                res = salvar_agendamento(nome, formatar_telefone(tel_clean), email, data_agend, hora, servico, ficha)
                
                if res == "OK":
                    st.balloons()
                    msg_zap = f"Olá! Agendei {servico} dia {data_agend.strftime('%d/%m')} às {hora}."
                    st.markdown(f'<div class="ticket">✅ Confirmado!<br>{nome}<br>{data_agend.strftime("%d/%m")} - {hora}<br><small>Verifique seu e-mail!</small></div>', unsafe_allow_html=True)
                    st.markdown(f'<a href="https://wa.me/5512987054320?text={msg_zap}" target="_blank" class="big-button" style="background:#25D366; height:60px; font-size:16px;">📲 ENVIAR WHATSAPP</a>', unsafe_allow_html=True)
                    
                    st.session_state.pre_nome = ""
                    st.session_state.pre_tel = ""
                    st.session_state.pre_email = ""
                    
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
