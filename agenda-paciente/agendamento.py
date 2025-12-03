import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dra. Thais Milene",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS DE CORREÇÃO (FORÇA TEXTO ESCURO) ---
st.markdown("""
    <style>
        /* 1. Forçar Fundo Rosa Claro */
        .stApp {
            background-color: #FCEEF5;
        }

        /* 2. CORREÇÃO DAS LETRAS BRANCAS */
        /* Isso obriga todos os textos e etiquetas a serem cinza escuro, mesmo se estiver em Dark Mode */
        .stMarkdown, .stText, h1, h2, h3, p, label, .stRadio label, .stCheckbox label {
            color: #444444 !important;
        }
        
        /* Ajuste dos Inputs (Caixinhas de texto) para fundo branco e borda rosa */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input {
            background-color: #FFFFFF !important;
            color: #333333 !important;
            border: 1px solid #F8E1EA !important;
        }

        /* 3. LOGO CENTRALIZADA */
        div[data-testid="stImage"] {
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
        div[data-testid="stImage"] img {
            max-width: 300px;
            filter: drop-shadow(0px 5px 10px rgba(199, 91, 122, 0.2)); 
        }

        /* 4. FORMULÁRIO (CARTÃO BRANCO) */
        div[data-testid="stForm"] {
            background-color: #FFFFFF;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 8px 24px rgba(199, 91, 122, 0.12);
            border: 1px solid #F8E1EA;
        }

        /* Títulos Coloridos */
        .section-header {
            color: #C75B7A !important; /* Rosa Escuro */
            font-weight: 700;
            font-size: 1.15em;
            margin-top: 20px;
            margin-bottom: 15px;
            border-left: 5px solid #C75B7A;
            padding-left: 15px;
            background: linear-gradient(90deg, #FFF0F5 0%, rgba(255,255,255,0) 100%);
            padding-top: 8px;
            padding-bottom: 8px;
            border-radius: 4px;
        }

        /* Botão Primário */
        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #C75B7A;
            color: white !important;
            border: none;
            height: 50px;
            font-size: 16px;
            border-radius: 10px;
        }
        
        .btn-whatsapp {
            display: block; width: 100%; padding: 12px;
            background-color: #FFFFFF; color: #25D366 !important;
            border: 2px solid #25D366; border-radius: 10px;
            text-align: center; text-decoration: none; font-weight: bold;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. BANCO DE DADOS (CORRIGIDO) ---
DB_NAME = 'consultorio_v3.db' # Mudei para v3 para garantir que crie a tabela certa do zero

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Atenção: Voltei o nome da coluna para 'horario' para evitar o erro do sqlite
    c.execute('''CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_nome TEXT, cliente_telefone TEXT,
        data_agendamento DATE, horario TEXT, servico TEXT, anamnese TEXT)''')
    conn.commit(); conn.close()

def salvar_agendamento(nome, tel, data, hora, serv, anam):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('INSERT INTO agendamentos VALUES (NULL,?,?,?,?,?,?)', (nome, tel, data, hora, serv, anam))
    conn.commit(); conn.close()

def get_horarios_ocupados(data):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    # Correção aqui também: buscando 'horario'
    c.execute('SELECT horario FROM agendamentos WHERE data_agendamento = ?', (data,))
    r = [i[0] for i in c.fetchall()]; conn.close(); return r

def carregar_dados():
    conn = sqlite3.connect(DB_NAME)
    try: df = pd.read_sql_query("SELECT * FROM agendamentos", conn)
    except: df = pd.DataFrame()
    conn.close(); return df

init_db()

# --- 4. INTERFACE ---

# Logo
col_vazia1, col_logo, col_vazia2 = st.columns([1, 2, 1])
with col_logo:
    try:
        st.image("logo.png", use_container_width=True) 
    except:
        st.markdown("<h1 style='text-align:center; color:#C75B7A'>Dra. Thais Milene</h1>", unsafe_allow_html=True)

st.markdown('<div style="text-align:center; color:#7f8c8d; margin-bottom:30px;">Odontologia Especializada • Taubaté/SP</div>', unsafe_allow_html=True)

# Botões Iniciais
col_b1, col_b2, col_b3 = st.columns([1, 6, 1])
with col_b2:
    if st.button("📅 NOVO AGENDAMENTO", type="primary", use_container_width=True):
        st.session_state['mostrar_form'] = True
    
    st.markdown(f'<a href="https://wa.me/5512987054320" target="_blank" class="btn-whatsapp">💬 Falar no WhatsApp</a>', unsafe_allow_html=True)

if 'mostrar_form' not in st.session_state: st.session_state['mostrar_form'] = False

if st.session_state['mostrar_form']:
    st.write("")
    
    # IMPORTANTE: O botão de submit TEM que estar indentado dentro do 'with st.form'
    with st.form("form_agendamento"):
        st.markdown('<div class="section-header">1. Dados da Consulta</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: data = st.date_input("Data", min_value=datetime.today())
        with c2: servico = st.selectbox("Procedimento", ["Avaliação (1ª Vez)", "Limpeza", "Restauração", "Clareamento", "Harmonização"])

        horarios = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        ocupados = get_horarios_ocupados(data)
        
        livres = []
        if data.weekday() >= 5:
            st.warning("Atendimentos apenas de Segunda a Sexta.")
        else:
            livres = [h for h in horarios if h not in ocupados]
        
        hora = st.selectbox("Horário", livres if livres else ["Indisponível"])

        st.markdown('<div class="section-header">2. Ficha de Saúde</div>', unsafe_allow_html=True)
        # Agora as letras vão aparecer escuras por causa do CSS lá em cima
        c3, c4 = st.columns(2)
        with c3:
            alergia = st.radio("Tem Alergia?", ["Não", "Sim"], horizontal=True)
            obs_alergia = st.text_input("Qual alergia?") if alergia == "Sim" else ""
        with c4:
            st.write("Histórico:") # Isso agora será cinza escuro
            cardiaco = st.checkbox("Problema Cardíaco / Pressão")
            gestante = st.checkbox("Gestante")
            
        st.markdown('<div class="section-header">3. Finalização</div>', unsafe_allow_html=True)
        nome = st.text_input("Nome Completo")
        tel = st.text_input("WhatsApp (DDD + Número)")

        st.write("")
        
        # O botão DEVE ficar aqui dentro
        submit = st.form_submit_button("✅ CONFIRMAR AGENDAMENTO", type="primary", use_container_width=True)

        if submit:
            if not nome or not tel:
                st.error("Preencha Nome e Telefone.")
            elif not livres:
                st.error("Horário indisponível.")
            else:
                anamnese_text = f"Alergia: {alergia} ({obs_alergia}) | Cardíaco: {cardiaco} | Gestante: {gestante}"
                salvar_agendamento(nome, tel, data, hora, servico, anamnese_text)
                st.success("Agendamento realizado com sucesso!")
                st.balloons()
                msg = f"Olá! Agendei {servico} para dia {data.strftime('%d/%m')} às {hora}."
                st.markdown(f'<a href="https://wa.me/5512987054320?text={msg}" target="_blank" class="btn-whatsapp" style="background:#25D366; color:white; border:none;">📲 Enviar Comprovante</a>', unsafe_allow_html=True)

# Rodapé
st.write(""); st.write("")
st.markdown("---")
st.caption("📍 Dra. Thais Milene | Taubaté - SP | © 2025")

# Admin
with st.expander("🔐 Área da Dra. Thais"):
    if st.text_input("Senha", type="password") == "admin123":
        st.dataframe(carregar_dados(), use_container_width=True)