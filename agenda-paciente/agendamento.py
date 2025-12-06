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

# --- 2. ESTILO VISUAL (MANTIDO IGUAL) ---
st.markdown("""
    <style>
        .stApp { background-color: #FCEEF5; }
        #MainMenu, footer, header {visibility: hidden;}
        .stElementContainer { margin-bottom: 0.3rem !important; }
        
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

        .stTextInput input, .stSelectbox div[data-baseweb="select"] div, .stDateInput input, .stTextArea textarea {
            background-color: #FFFFFF !important; border: 1px solid #E3CWD8 !important;
            border-radius: 12px !important; color: #495057 !important; padding-left: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
        }
        
        .stTextInput input:focus, .stSelectbox div:focus, .stDateInput input:focus {
            border-color: #9A2A5A !important; box-shadow: 0 0 0 1px #9A2A5A !important;
        }
        
        h1, h2, h3, p, label, .stMarkdown { color: #5D4050 !important; font-family: 'Helvetica', sans-serif; }
        
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
        .stCheckbox label { color: #5D4050 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CONEXÃO GOOGLE SHEETS (NOVO BACKEND) ---

def conectar_google_sheets():
    """Conecta ao Google Sheets usando st.secrets"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Pega as credenciais do secrets.toml
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # Abre a planilha (O nome deve ser EXATAMENTE igual ao do Google Drive)
    return client.open("Agenda Dra Thais").sheet1 

def carregar_dados_gs():
    """Baixa todos os dados da planilha para um DataFrame"""
    try:
        sheet = conectar_google_sheets()
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        # st.error(f"Erro ao carregar dados: {e}") # Descomente para debug
        return pd.DataFrame()

def salvar_agendamento(nome, tel, data, hora, serv, anam):
    """Salva uma nova linha na planilha"""
    try:
        sheet = conectar_google_sheets()
        # Adiciona linha: Nome, Telefone, Data, Horario, Servico, Anamnese, Registro(Timestamp)
        sheet.append_row([nome, tel, str(data), hora, serv, anam, str(datetime.now())])
        return True
    except Exception as e:
        st.error(f"Erro ao salvar no sistema: {e}")
        return False

def get_horarios_ocupados(data_desejada):
    """Verifica na planilha quais horários já estão tomados naquele dia"""
    df = carregar_dados_gs()
    if df.empty:
        return []
    
    # Converte a coluna Data para string para garantir a comparação
    df['Data'] = df['Data'].astype(str)
    data_str = str(data_desejada)
    
    # Filtra os agendamentos daquele dia
    agendamentos_dia = df[df['Data'] == data_str]
    return agendamentos_dia['Horario'].tolist()

def buscar_agendamentos_cliente(telefone):
    """Busca agendamentos baseados no telefone (limpando formatação)"""
    df = carregar_dados_gs()
    if df.empty:
        return pd.DataFrame()
    
    # Limpa o telefone digitado pelo usuário
    telefone_usuario = re.sub(r'\D', '', telefone)
    
    # Cria uma coluna temporária com telefones limpos da planilha para comparar
    # Converte para string primeiro para evitar erro se o excel leu como numero
    df['tel_limpo'] = df['Telefone'].astype(str).apply(lambda x: re.sub(r'\D', '', x))
    
    # Filtra onde contém o número
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

# --- 6. TELA: AGENDAR ---
elif st.session_state.pagina == 'agendar':
    if st.button("⬅ Voltar"): ir_para('home'); st.rerun()

    st.markdown("<h2 style='color:#9A2A5A; margin-bottom:0px'>Ficha do Paciente</h2>", unsafe_allow_html=True)
    st.caption("Preencha seus dados para agilizarmos seu atendimento.")

    with st.form("form_anamnese"):
        # --- BLOCO 1: AGENDAMENTO ---
        st.markdown("<div class='anamnese-header'>1. Agendamento</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1], gap="small")
        with c1: data_agend = st.date_input("📅 Data Desejada", min_value=datetime.today(), format="DD/MM/YYYY")
        with c2: servico = st.selectbox("🦷 Procedimento", ["Avaliação (1ª Vez)", "Limpeza", "Restauração", "Clareamento", "Harmonização", "Dor/Urgência"])

        horarios = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        
        # Busca horários ocupados no Google Sheets
        try:
            ocupados = get_horarios_ocupados(data_agend)
        except:
            ocupados = [] # Se der erro na conexão, assume livre (ou poderia bloquear)
            
        livres = [h for h in horarios if h not in ocupados] if data_agend.weekday() < 5 else []
        
        if data_agend.weekday() >= 5: st.warning("⚠️ Atendimentos apenas de Segunda a Sexta.")
        hora = st.selectbox("⏰ Horário", livres if livres else ["Indisponível"])

        # --- BLOCO 2: DADOS PESSOAIS ---
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

        # --- BLOCO 3: ANAMNESE ---
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
            medicamentos = st.text_area("Toma algum remédio?", placeholder="Ex: Losartana...")

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
            elif not livres: st.error("Horário indisponível.")
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
                
                # --- AQUI MUDA O SALVAMENTO PARA O SHEETS ---
                sucesso = salvar_agendamento(nome, tel_formatado, data_agend, hora, servico, ficha_completa)
                
                if sucesso:
                    st.success("Agendamento realizado e salvo na Nuvem! ☁️👏")
                    st.balloons()
                    
                    msg = f"Olá Dra. Thais! Sou *{nome}*. Agendei *{servico}* para dia *{data_agend.strftime('%d/%m/%Y')}* às *{hora}*."
                    st.markdown(f'''
                        <a href="https://wa.me/5512987054320?text={msg}" target="_blank" style="text-decoration:none;">
                            <div style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold; margin-top:10px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                                📲 ENVIAR COMPROVANTE NO WHATSAPP
                            </div>
                        </a>
                    ''', unsafe_allow_html=True)
                    
                    time.sleep(10)
                    ir_para('home')
                    st.rerun()

# --- 7. TELA: RESERVAS ---
elif st.session_state.pagina == 'reservas':
    if st.button("⬅ Voltar"): ir_para('home'); st.rerun()
    st.markdown("<h3 style='color:#9A2A5A'>Minhas Reservas</h3>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Sou Paciente", "Área da Dra. Thais"])
    
    with tab1:
        st.write("Digite seu número para consultar:")
        c_busca1, c_busca2 = st.columns([3,1])
        with c_busca1: tel_busca = st.text_input("Seu WhatsApp", label_visibility="collapsed", placeholder="Ex: 12999999999")
        with c_busca2: btn_buscar = st.button("🔎", type="primary")
        
        if btn_buscar and tel_busca:
            df = buscar_agendamentos_cliente(tel_busca)
            if not df.empty:
                st.dataframe(df, hide_index=True, use_container_width=True)
            else: st.warning("Nenhum agendamento encontrado.")
    
    with tab2:
        senha = st.text_input("Senha Admin", type="password")
        if senha == "admin123":
            st.success("Acesso Admin (Google Sheets)")
            
            df_geral = carregar_dados_gs()
            
            if not df_geral.empty:
                # Mostra tabela simplificada
                df_view = df_geral[['Data', 'Horario', 'Nome', 'Servico']].copy()
                st.dataframe(df_view, use_container_width=True)
                
                st.write("---")
                st.markdown("#### 📋 Ficha Completa")
                
                # Cria lista de opções
                if 'Nome' in df_geral.columns:
                    # Adiciona indice para garantir unicidade
                    opcoes = df_geral.index.astype(str) + " - " + df_geral['Nome']
                    escolha = st.selectbox("Escolha o paciente:", options=opcoes)
                    
                    if escolha:
                        idx_selecionado = int(escolha.split(" - ")[0])
                        paciente = df_geral.iloc[idx_selecionado]
                        
                        with st.container():
                            st.markdown(f"""
                            <div style="background-color:#FFFFFF; padding:15px; border-radius:10px; border:1px solid #E3CWD8; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                                <h3 style="color:#9A2A5A; margin:0">{paciente['Nome']}</h3>
                                <p style="color:#666; margin-bottom:10px">📞 {paciente['Telefone']}</p>
                                <hr style="margin:10px 0; border-top:1px dashed #ccc;">
                                <pre style="white-space: pre-wrap; font-family:inherit; color:#333;">{paciente['Anamnese']}</pre>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("A planilha ainda está vazia.")
