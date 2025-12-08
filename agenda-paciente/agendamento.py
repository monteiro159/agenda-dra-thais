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
        
        /* Botões */
        .big-button {
            width: 100%; height: 120px; border-radius: 20px; border: none;
            color: white; font-size: 20px; font-weight: bold; cursor: pointer;
            margin-bottom: 15px; display: flex; align-items: center; justify-content: center;
            text-decoration: none; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .big-button:hover { transform: scale(1.02); }
        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #9A2A5A; color: white !important; font-size: 16px;
            box-shadow: 0 4px 10px rgba(154, 42, 90, 0.2); border: none; border-radius: 12px; height: 50px;
        }
        div[data-testid="stButton"] button[kind="secondary"] {
            background-color: #FFFFFF; color: #9A2A5A !important; font-size: 16px; border: 1px solid #F3D0DE; border-radius: 12px; height: 50px;
        }

        /* Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] div, .stDateInput input, .stTextArea textarea {
            background-color: #FFFFFF !important; border: 1px solid #E3CWD8 !important;
            border-radius: 12px !important; color: #495057 !important; padding-left: 10px;
        }
        .stTextInput input:focus, .stSelectbox div:focus, .stDateInput input:focus {
            border-color: #9A2A5A !important; box-shadow: 0 0 0 1px #9A2A5A !important;
        }

        /* Textos e Abas */
        h1, h2, h3, p, label, .stMarkdown { color: #5D4050 !important; font-family: 'Helvetica', sans-serif; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            height: 40px; background-color: rgba(255,255,255,0.5); border-radius: 4px 4px 0px 0px;
        }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF; border-bottom: 2px solid #9A2A5A; color: #9A2A5A; }
        
        /* Ticket Visual */
        .ticket {
            background-color: white; border: 1px dashed #9A2A5A; padding: 20px;
            border-radius: 10px; margin-top: 20px; text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }
        .anamnese-header {
            color: #9A2A5A; font-weight: 700; margin-top: 20px; margin-bottom: 8px; 
            border-left: 5px solid #9A2A5A; padding-left: 10px; background-color: rgba(255,255,255,0.5);
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. CONEXÃO GOOGLE SHEETS ROBUSTA ---

@st.cache_resource
def conectar_google_sheets():
    """Conecta e retorna a planilha com tratamento de erro"""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # Tenta abrir a planilha
        sheet = client.open("Agenda Dra Thais").sheet1
        return sheet
    except Exception as e:
        return None

def carregar_dados_gs():
    """Baixa dados e garante que o DataFrame tenha colunas mesmo se vazio"""
    sheet = conectar_google_sheets()
    if sheet is None:
        return pd.DataFrame() # Retorna vazio se não conectar
        
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Se a planilha estiver vazia ou nova, cria as colunas manualmente para não dar erro
        colunas_esperadas = ['Nome', 'Telefone', 'Data', 'Horario', 'Servico', 'Anamnese', 'Timestamp']
        if df.empty or not set(colunas_esperadas).issubset(df.columns):
            return pd.DataFrame(columns=colunas_esperadas)
            
        return df
    except Exception:
        return pd.DataFrame()

def salvar_agendamento(nome, tel, data, hora, serv, anam):
    """Salva no Sheets com tratamento de erro explícito"""
    sheet = conectar_google_sheets()
    if sheet is None:
        return "Erro: Falha na conexão com Google Sheets. Verifique os Segredos."
        
    try:
        # Converte tudo para string para garantir que o Sheets aceite
        linha = [
            str(nome), 
            str(tel), 
            str(data),  # Salva como YYYY-MM-DD
            str(hora), 
            str(serv), 
            str(anam), 
            str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ]
        sheet.append_row(linha)
        return "OK"
    except Exception as e:
        return f"Erro ao gravar: {e}"

def get_horarios_ocupados(data_desejada):
    """Verifica horários ocupados"""
    df = carregar_dados_gs()
    if df.empty:
        return []
    
    # Normalização de dados para comparação
    if 'Data' not in df.columns or 'Horario' not in df.columns:
        return []
        
    df['Data'] = df['Data'].astype(str)
    data_str = str(data_desejada)
    
    # Filtra
    ocupados = df[df['Data'] == data_str]['Horario'].tolist()
    return ocupados

def buscar_agendamentos_cliente(telefone):
    df = carregar_dados_gs()
    if df.empty: return pd.DataFrame()
    
    telefone_usuario = re.sub(r'\D', '', telefone)
    
    # Garante que as colunas existam
    if 'Telefone' not in df.columns: return pd.DataFrame()

    df['tel_limpo'] = df['Telefone'].astype(str).apply(lambda x: re.sub(r'\D', '', x))
    resultado = df[df['tel_limpo'].str.contains(telefone_usuario, na=False)]
    
    return resultado[['Data', 'Horario', 'Servico']] if not resultado.empty else pd.DataFrame()

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

    st.markdown("<div style='margin-top: 60px; text-align: center; color: #999; font-size: 12px;'><p>📍 Taubaté/SP | CRO 12345</p></div>", unsafe_allow_html=True)

    # Diagnóstico de Conexão na Home (apenas para teste)
    if st.sidebar.checkbox("Verificar Conexão Google"):
        sheet = conectar_google_sheets()
        if sheet:
            st.sidebar.success(f"Conectado à planilha: {sheet.title}")
        else:
            st.sidebar.error("Falha na conexão. Verifique se compartilhou a planilha com o email do service account.")

    # Acesso Admin
    with st.sidebar:
        st.write("---")
        if st.text_input("Senha Admin", type="password") == "admin123":
            if st.button("Acessar Painel"): ir_para('admin_panel')

# --- 6. TELA: AGENDAR ---
elif st.session_state.pagina == 'agendar':
    if st.button("⬅ Voltar"): ir_para('home'); st.rerun()

    st.markdown("<h2 style='color:#9A2A5A; margin-bottom:0px'>Ficha do Paciente</h2>", unsafe_allow_html=True)
    
    with st.form("form_anamnese"):
        st.markdown("<div class='anamnese-header'>1. Agendamento</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1], gap="small")
        with c1: 
            # Data mínima hoje
            data_agend = st.date_input("📅 Data Desejada", min_value=datetime.today(), format="DD/MM/YYYY")
        with c2: 
            servico = st.selectbox("🦷 Procedimento", ["Avaliação (1ª Vez)", "Limpeza", "Restauração", "Clareamento", "Harmonização", "Dor/Urgência"])

        # Lógica de horários com tratamento de erro
        horarios = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        try:
            ocupados = get_horarios_ocupados(data_agend)
        except:
            ocupados = [] 
            
        livres = [h for h in horarios if h not in ocupados] if data_agend.weekday() < 5 else []
        
        if data_agend.weekday() >= 5: 
            st.warning("⚠️ Atendimentos apenas de Segunda a Sexta.")
            hora = "Indisponível"
        else:
            if not livres:
                st.warning("📅 Dia lotado. Tente outra data.")
                hora = "Indisponível"
            else:
                hora = st.selectbox("⏰ Horário Disponível", livres)

        st.markdown("<div class='anamnese-header'>2. Seus Dados</div>", unsafe_allow_html=True)
        nome = st.text_input("👤 Nome Completo")
        tel_input = st.text_input("📱 WhatsApp (DDD + Número)", placeholder="Ex: 12 99999-9999")
        
        # Nascimento Simplificado
        st.markdown("**🎂 Data de Nascimento**")
        dn_col1, dn_col2, dn_col3 = st.columns([3, 5, 4], gap="small")
        with dn_col1: dia_nasc = st.selectbox("Dia", list(range(1, 32)))
        with dn_col2:
            meses = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}
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
            # CORRIGIDO TEXTO
            medicamentos = st.text_area("Toma algum remédio de uso contínuo?", placeholder="Ex: Losartana...")

        with tab_bucal:
            queixa = st.text_area("Queixa Principal", placeholder="O que te incomoda?")
            c_bucal1, c_bucal2 = st.columns(2, gap="small")
            with c_bucal1:
                sangramento = st.checkbox("Gengiva Sangra")
                sensibilidade = st.checkbox("Dente Sensível")
            with c_bucal2:
                bruxismo = st.checkbox("Range dentes")
                implantado = st.checkbox("Prótese/Implante")

        with tab_habitos:
            fumante = st.radio("Fuma?", ["Não", "Sim, às vezes", "Sim, todo dia"])
            bebe = st.checkbox("Consome álcool?")

        st.write("")
        submit = st.form_submit_button("✅  CONFIRMAR AGENDAMENTO", type="primary", use_container_width=True)

        if submit:
            tel_limpo = re.sub(r'\D', '', tel_input)
            
            if not nome or len(nome) < 3: st.error("⚠️ Preencha seu Nome Completo.")
            elif len(tel_limpo) < 10: st.error("⚠️ WhatsApp inválido.")
            elif hora == "Indisponível": st.error("⚠️ Horário indisponível.")
            else:
                idade = (date.today() - data_nasc).days // 365
                lista_saude = []
                if diabetes: lista_saude.append("Diabetes")
                if hipertensao: lista_saude.append("Hipertensão")
                if cardiaco: lista_saude.append("Cardíaco")
                if gestante: lista_saude.append("Gestante")
                str_saude = ", ".join(lista_saude) if lista_saude else "Nenhuma"

                ficha_completa = (
                    f"[PERFIL] {idade} anos | {genero} | Nasc: {data_nasc.strftime('%d/%m/%Y')}\n"
                    f"[QUEIXA] {queixa}\n"
                    f"[SAÚDE] {str_saude} | Alergia: {alergia_desc}\n"
                    f"[BUCAL] Sangra: {'Sim' if sangramento else 'Não'}\n"
                    f"[HÁBITOS] Fuma: {fumante}"
                )
                tel_formatado = formatar_telefone(tel_limpo)
                
                with st.spinner("Salvando na agenda..."):
                    resultado = salvar_agendamento(nome, tel_formatado, data_agend, hora, servico, ficha_completa)
                
                if resultado == "OK":
                    st.balloons()
                    st.markdown(f"""
                        <div class="ticket">
                            <div class="ticket-title">✅ Agendamento Confirmado!</div>
                            <p><b>{nome}</b></p>
                            <p>{data_agend.strftime('%d/%m/%Y')} às {hora}</p>
                            <p>{servico}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    msg = f"Olá! Sou *{nome}*. Agendei *{servico}* para dia *{data_agend.strftime('%d/%m')}* às *{hora}*."
                    st.markdown(f'''
                        <a href="https://wa.me/5512987054320?text={msg}" target="_blank" style="text-decoration:none;">
                            <div style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold; margin-top:10px;">
                                📲 ENVIAR NO WHATSAPP
                            </div>
                        </a>
                    ''', unsafe_allow_html=True)
                    time.sleep(10)
                    ir_para('home')
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar: {resultado}")
                    st.info("Verifique se o e-mail do robô foi adicionado como Editor na planilha.")

# --- 7. TELA: RESERVAS ---
elif st.session_state.pagina == 'reservas':
    if st.button("⬅ Voltar"): ir_para('home'); st.rerun()
    st.markdown("<h3 style='color:#9A2A5A'>Minhas Reservas</h3>", unsafe_allow_html=True)
    
    tel_busca = st.text_input("Seu WhatsApp", placeholder="Ex: 12999999999")
    if st.button("🔎 Buscar"):
        df = buscar_agendamentos_cliente(tel_busca)
        if not df.empty: st.dataframe(df, hide_index=True)
        else: st.warning("Nada encontrado.")

# --- 8. TELA: ADMIN ---
elif st.session_state.pagina == 'admin_panel':
    if st.button("⬅ Sair"): ir_para('home'); st.rerun()
    st.title("Painel da Dra. Thais")
    
    df_geral = carregar_dados_gs()
    if not df_geral.empty:
        st.dataframe(df_geral[['Data', 'Horario', 'Nome', 'Servico']], use_container_width=True)
        if 'Nome' in df_geral.columns:
            opcoes = df_geral.index.astype(str) + " - " + df_geral['Nome']
            escolha = st.selectbox("Ver Ficha:", options=opcoes)
            if escolha:
                idx = int(escolha.split(" - ")[0])
                paciente = df_geral.iloc[idx]
                st.info(f"Ficha: {paciente['Nome']}")
                st.text(paciente['Anamnese'])
    else:
        st.info("Agenda vazia ou erro de conexão.")
