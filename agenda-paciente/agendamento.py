import streamlit as st
import pandas as pd
from datetime import datetime, date
import time
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(
    page_title="Dra. Thais Milene",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. ESTILO VISUAL ---
st.markdown("""
    <style>
        .stApp { background-color: #FCEEF5; }
        
        /* Botões Iniciais */
        .big-button {
            width: 100%; height: 120px; border-radius: 20px; border: none;
            color: white; font-size: 20px; font-weight: bold; cursor: pointer;
            margin-bottom: 15px; display: flex; align-items: center; justify-content: center;
            text-decoration: none; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .big-button:hover { transform: scale(1.02); }

        div[data-testid="stButton"] button { border-radius: 12px; height: 50px; font-weight: 600; border: none; }
        
        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #9A2A5A; color: white !important; font-size: 16px;
            box-shadow: 0 4px 10px rgba(154, 42, 90, 0.2);
        }
        
        div[data-testid="stButton"] button[kind="secondary"] {
            background-color: #FFFFFF; color: #9A2A5A !important; font-size: 16px; border: 1px solid #F3D0DE;
        }

        /* Inputs Modernos */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] div, .stDateInput input, .stTextArea textarea {
            background-color: #FFFFFF !important; border: 1px solid #E3CWD8 !important;
            border-radius: 12px !important; color: #495057 !important; padding-left: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
        }
        
        .stTextInput input:focus, .stSelectbox div:focus, .stDateInput input:focus {
            border-color: #9A2A5A !important; box-shadow: 0 0 0 1px #9A2A5A !important;
        }
        
        /* Textos */
        h1, h2, h3, p, label, .stMarkdown { color: #5D4050 !important; font-family: 'Helvetica', sans-serif; }
        
        /* Abas */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            height: 40px; white-space: pre-wrap; background-color: rgba(255,255,255,0.5);
            border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF; border-bottom: 2px solid #9A2A5A; color: #9A2A5A; }

        .anamnese-header {
            color: #9A2A5A; font-weight: 700; font-size: 1.1em;
            margin-top: 20px; margin-bottom: 8px; border-left: 5px solid #9A2A5A; padding-left: 10px;
            background-color: rgba(255,255,255,0.5); padding-top: 5px; padding-bottom: 5px; border-radius: 0 10px 10px 0;
        }
        
        /* Ticket Visual de Confirmação */
        .ticket {
            background-color: white; border: 1px dashed #9A2A5A; padding: 20px;
            border-radius: 10px; margin-top: 20px; text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); position: relative;
        }
        .ticket-title { color: #9A2A5A; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
        .ticket-info { color: #555; font-size: 14px; margin: 5px 0; }
        .ticket-check { font-size: 40px; margin-bottom: 10px; }

    </style>
""", unsafe_allow_html=True)

# --- 3. CONEXÃO GOOGLE SHEETS (COM CACHE PARA NÃO TRAVAR) ---

# MELHORIA 1: Cache Resource impede que o site reconecte toda hora que muda a data
@st.cache_resource
def conectar_google_sheets():
    """Conecta ao Google Sheets usando st.secrets"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("Agenda Dra Thais").sheet1 

# Não usamos cache aqui pois os dados mudam (alguém pode ter agendado agora)
def carregar_dados_gs():
    """Baixa todos os dados da planilha"""
    try:
        sheet = conectar_google_sheets()
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        return pd.DataFrame()

def salvar_agendamento(nome, tel, data, hora, serv, anam):
    """Salva uma nova linha na planilha"""
    try:
        sheet = conectar_google_sheets()
        sheet.append_row([nome, tel, str(data), hora, serv, anam, str(datetime.now())])
        return True
    except Exception as e:
        st.error(f"Erro de conexão. Tente novamente: {e}")
        return False

def get_horarios_ocupados(data_desejada):
    """Verifica na planilha quais horários já estão tomados"""
    df = carregar_dados_gs()
    if df.empty:
        return []
    
    # Garante que estamos comparando texto com texto
    df['Data'] = df['Data'].astype(str)
    data_str = str(data_desejada) # Formato YYYY-MM-DD padrão do Python
    
    # Se a planilha salvou como DD/MM/YYYY, precisamos converter ou padronizar
    # Assumindo padrão YYYY-MM-DD do date_input
    agendamentos_dia = df[df['Data'] == data_str]
    return agendamentos_dia['Horario'].tolist()

def buscar_agendamentos_cliente(telefone):
    df = carregar_dados_gs()
    if df.empty: return pd.DataFrame()
    
    telefone_usuario = re.sub(r'\D', '', telefone)
    # Evita erro se a coluna Telefone estiver vazia ou com números
    df['tel_limpo'] = df['Telefone'].astype(str).apply(lambda x: re.sub(r'\D', '', x))
    
    resultado = df[df['tel_limpo'].str.contains(telefone_usuario, na=False)]
    return resultado[['Data', 'Horario', 'Servico']]

def formatar_telefone(tel):
    nums = re.sub(r'\D', '', tel)
    if len(nums) == 11: return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"
    if len(nums) == 10: return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    return tel

# --- 4. NAVEGAÇÃO ---
if 'pagina' not in st.session_state: st.session_state.pagina = 'home'
def ir_para(pagina): st.session_state.pagina = pagina

# --- 5. TELA: HOME ---
if st.session_state.pagina == 'home':
    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try: st.image("logo.jpg", use_container_width=True)
        except: 
            try: st.image("logo.png", use_container_width=True)
            except: st.markdown("<h1 style='text-align:center; color:#9A2A5A'>Dra. Thais</h1>", unsafe_allow_html=True)
    
    st.markdown("<h5 style='text-align:center; color:#8C6B7A; font-weight:normal; margin-top:-15px'>Odontologia Especializada</h5>", unsafe_allow_html=True)
    st.write("---")
    
    if st.button("✨  NOVO AGENDAMENTO", type="primary", use_container_width=True): ir_para('agendar')
    st.write("")
    if st.button("📂  MINHAS RESERVAS", type="secondary", use_container_width=True): ir_para('reservas')

    st.markdown("<div style='margin-top: 60px; text-align: center; color: #999; font-size: 12px;'><p>📍 Av. Itália, 123 - Taubaté/SP<br>CRO 12345</p></div>", unsafe_allow_html=True)

    # MELHORIA 3: Admin na Sidebar para limpar a Home
    with st.sidebar:
        st.header("🔐 Acesso Profissional")
        senha = st.text_input("Senha Admin", type="password")
        if senha == "admin123":
            st.success("Logado")
            if st.button("Ir para Painel"):
                ir_para('admin_panel')

# --- 6. TELA: AGENDAR ---
elif st.session_state.pagina == 'agendar':
    if st.button("⬅ Voltar"): ir_para('home'); st.rerun()

    st.markdown("<h2 style='color:#9A2A5A; margin-bottom:0px'>Ficha do Paciente</h2>", unsafe_allow_html=True)
    st.caption("Preencha seus dados para agilizarmos seu atendimento.")

    with st.form("form_anamnese"):
        st.markdown("<div class='anamnese-header'>1. Agendamento</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1], gap="small")
        
        # CORREÇÃO DATA: format="DD/MM/YYYY" apenas visual. O valor interno é YYYY-MM-DD
        with c1: 
            data_agend = st.date_input("📅 Data Desejada", min_value=datetime.today(), format="DD/MM/YYYY")
        
        with c2: 
            servico = st.selectbox("🦷 Procedimento", ["Avaliação (1ª Vez)", "Limpeza", "Restauração", "Clareamento", "Harmonização", "Dor/Urgência"])

        # MELHORIA 2: Spinner visual enquanto carrega os horários
        with st.spinner("Verificando agenda da Dra..."):
            try:
                horarios = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
                ocupados = get_horarios_ocupados(data_agend)
                livres = [h for h in horarios if h not in ocupados] if data_agend.weekday() < 5 else []
            except:
                livres = [] # Falha silenciosa segura
        
        if data_agend.weekday() >= 5: 
            st.warning("⚠️ Atendimentos apenas de Segunda a Sexta.")
            hora = "Indisponível"
        else:
            if not livres:
                st.error("Sem horários vagos para este dia.")
                hora = "Indisponível"
            else:
                # Placeholder simulado (index=None se fosse Streamlit mais novo, aqui usamos logica)
                hora = st.selectbox("⏰ Horário Disponível", livres)

        st.markdown("<div class='anamnese-header'>2. Seus Dados</div>", unsafe_allow_html=True)
        nome = st.text_input("👤 Nome Completo")
        tel_input = st.text_input("📱 WhatsApp (DDD + Número)", placeholder="Ex: 12 99999-9999")
        
        st.markdown("**🎂 Data de Nascimento**")
        dn_col1, dn_col2, dn_col3 = st.columns([3, 5, 4], gap="small")
        with dn_col1: dia_nasc = st.selectbox("Dia", list(range(1, 32)))
        with dn_col2:
            meses = {1:"Janeiro", 2:"Fevereiro", 3:"Março", 4:"Abril", 5:"Maio", 6:"Junho", 7:"Julho", 8:"Agosto", 9:"Setembro", 10:"Outubro", 11:"Novembro", 12:"Dezembro"}
            mes_nasc_nome = st.selectbox("Mês", list(meses.values()))
            mes_nasc = [k for k, v in meses.items() if v == mes_nasc_nome][0]
        with dn_col3:
            ano_atual = datetime.now().year
            ano_nasc = st.selectbox("Ano", list(range(ano_atual, 1920, -1)), index=30)
        try: data_nasc = date(ano_nasc, mes_nasc, dia_nasc)
        except: data_nasc = date(1990, 1, 1)

        genero = st.radio("Gênero", ["Feminino", "Masculino"], horizontal=True)

        st.markdown("<div class='anamnese-header'>3. Saúde (Anamnese)</div>", unsafe_allow_html=True)
        tab_geral, tab_bucal, tab_habitos = st.tabs(["🏥 Geral", "🦷 Bucal", "🚬 Hábitos"])

        with tab_geral:
            col_g1, col_g2 = st.columns(2, gap="small")
            with col_g1:
                diabetes = st.checkbox("Diabetes")
                hipertensao = st.checkbox("Pressão Alta")
                cardiaco = st.checkbox("Doença Cardíaca")
                respiratorio = st.checkbox("Asma / Bronquite")
            with col_g2:
                renal = st.checkbox("Problema Renal")
                hepatite = st.checkbox("Hepatite")
                anemia = st.checkbox("Anemia")
                gestante = st.checkbox("Gestante")
            st.divider()
            alergia_tem = st.radio("Tem Alergias?", ["Não", "Sim"], horizontal=True)
            alergia_desc = st.text_input("Quais?") if alergia_tem == "Sim" else "Nenhuma"
            
            # CORREÇÃO SOLICITADA: Texto do remédio
            medicamentos = st.text_area("Toma algum remédio de uso contínuo?", placeholder="Ex: Losartana...")

        with tab_bucal:
            queixa = st.text_area("O que te incomoda hoje?", placeholder="Ex: Dor no dente de trás...")
            c_bucal1, c_bucal2 = st.columns(2, gap="small")
            with c_bucal1:
                sangramento = st.checkbox("Gengiva Sangra")
                sensibilidade = st.checkbox("Dente Sensível")
            with c_bucal2:
                bruxismo = st.checkbox("Range dentes")
                implantado = st.checkbox("Usa Prótese/Implante")

        with tab_habitos:
            fumante = st.radio("Fuma?", ["Não", "Sim, às vezes", "Sim, todo dia"])
            bebe = st.checkbox("Bebe álcool?")

        st.write("")
        submit = st.form_submit_button("✅  CONFIRMAR AGENDAMENTO", type="primary", use_container_width=True)

        if submit:
            tel_limpo = re.sub(r'\D', '', tel_input)
            
            if not nome or len(nome) < 3: st.error("Por favor, preencha seu Nome Completo.")
            elif len(tel_limpo) < 10: st.error("Número de WhatsApp inválido.")
            elif hora == "Indisponível": st.error("Selecione um horário válido.")
            else:
                idade = (date.today() - data_nasc).days // 365
                lista_saude = []
                if diabetes: lista_saude.append("Diabetes")
                if hipertensao: lista_saude.append("Hipertensão")
                if cardiaco: lista_saude.append("Cardíaco")
                if respiratorio: lista_saude.append("Respiratório")
                if renal: lista_saude.append("Renal")
                if hepatite: lista_saude.append("Hepatite")
                if anemia: lista_saude.append("Anemia")
                if gestante: lista_saude.append("Gestante")
                str_saude = ", ".join(lista_saude) if lista_saude else "Nenhuma"

                ficha_completa = (
                    f"[PERFIL] {idade} anos | {genero} | Nasc: {data_nasc.strftime('%d/%m/%Y')}\n"
                    f"[QUEIXA] {queixa}\n"
                    f"[SAÚDE] {str_saude} | Alergia: {alergia_desc}\n"
                    f"[BUCAL] Sangra: {'Sim' if sangramento else 'Não'} | Sensível: {'Sim' if sensibilidade else 'Não'}\n"
                    f"[HÁBITOS] Fuma: {fumante}"
                )
                tel_formatado = formatar_telefone(tel_limpo)
                
                with st.spinner("Registrando no sistema..."):
                    sucesso = salvar_agendamento(nome, tel_formatado, data_agend, hora, servico, ficha_completa)
                
                if sucesso:
                    # MELHORIA 4: Ticket Visual em vez de texto simples
                    st.balloons()
                    st.markdown(f"""
                        <div class="ticket">
                            <div class="ticket-check">✅</div>
                            <div class="ticket-title">Agendamento Confirmado!</div>
                            <p class="ticket-info">Paciente: <b>{nome}</b></p>
                            <p class="ticket-info">Dia: <b>{data_agend.strftime('%d/%m/%Y')}</b> às <b>{hora}</b></p>
                            <p class="ticket-info">Procedimento: <b>{servico}</b></p>
                            <hr style="border-top: 1px dashed #9A2A5A;">
                            <p style="font-size:12px; color:#888;">Aguarde a confirmação final pelo WhatsApp.</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    msg = f"Olá Dra. Thais! Sou *{nome}*. Agendei *{servico}* para dia *{data_agend.strftime('%d/%m/%Y')}* às *{hora}*."
                    st.markdown(f'''
                        <a href="https://wa.me/5512987054320?text={msg}" target="_blank" style="text-decoration:none;">
                            <div style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold; margin-top:10px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                                📲 ENVIAR COMPROVANTE AGORA
                            </div>
                        </a>
                    ''', unsafe_allow_html=True)
                    
                    # Aguarda 15s para dar tempo de clicar no botão antes de resetar
                    time.sleep(15)
                    ir_para('home')
                    st.rerun()

# --- 7. TELA: RESERVAS (PACIENTE) ---
elif st.session_state.pagina == 'reservas':
    if st.button("⬅ Voltar"): ir_para('home'); st.rerun()
    st.markdown("<h3 style='color:#9A2A5A'>Minhas Reservas</h3>", unsafe_allow_html=True)
    
    st.write("Digite seu número para consultar:")
    c_busca1, c_busca2 = st.columns([3,1])
    with c_busca1: tel_busca = st.text_input("Seu WhatsApp", label_visibility="collapsed", placeholder="Ex: 12999999999")
    with c_busca2: btn_buscar = st.button("🔎", type="primary")
    
    if btn_buscar and tel_busca:
        with st.spinner("Buscando no sistema..."):
            df = buscar_agendamentos_cliente(tel_busca)
        if not df.empty:
            st.dataframe(df, hide_index=True, use_container_width=True)
        else: st.warning("Nenhum agendamento encontrado.")

# --- 8. TELA: ADMIN PAINEL (NOVA, SEPARADA) ---
elif st.session_state.pagina == 'admin_panel':
    if st.button("⬅ Sair"): ir_para('home'); st.rerun()
    st.title("Painel da Dra. Thais")
    
    df_geral = carregar_dados_gs()
    if not df_geral.empty:
        st.dataframe(df_geral[['Data', 'Horario', 'Nome', 'Servico']], use_container_width=True)
        st.write("---")
        st.markdown("#### 📋 Detalhes do Paciente")
        if 'Nome' in df_geral.columns:
            opcoes = df_geral.index.astype(str) + " - " + df_geral['Nome']
            escolha = st.selectbox("Escolha o paciente:", options=opcoes)
            if escolha:
                idx_selecionado = int(escolha.split(" - ")[0])
                paciente = df_geral.iloc[idx_selecionado]
                st.info(f"Ficha de {paciente['Nome']}")
                st.text(paciente['Anamnese'])
    else:
        st.info("Planilha vazia.")
