import streamlit as st
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dra. Thais Milene - Odontologia",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS (Design Profissional) ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        .main-title {
            font-size: 2.2em;
            font-weight: bold;
            color: #C75B7A; /* Rosa elegante */
            text-align: center;
            margin-bottom: 5px;
        }
        .sub-title {
            font-size: 1.0em;
            color: #666;
            text-align: center;
            margin-bottom: 30px;
        }
        .big-button {
            display: block;
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            font-weight: bold;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 12px;
            text-decoration: none !important;
            cursor: pointer;
        }
        /* Botão Secundário (WhatsApp) */
        .btn-secondary {
            background-color: #F8F9FA;
            color: #C75B7A !important;
            border: 2px solid #C75B7A;
        }
        .btn-secondary:hover {
            background-color: #F0F0F0;
        }
    </style>
""", unsafe_allow_html=True)

# --- BACKEND (Banco de Dados) ---
def init_db():
    conn = sqlite3.connect('consultorio.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nome TEXT NOT NULL,
            cliente_telefone TEXT,
            data_agendamento DATE NOT NULL,
            horario TEXT NOT NULL,
            servico TEXT
        )
    ''')
    conn.commit()
    conn.close()

def salvar_agendamento(nome, telefone, data, horario, servico):
    conn = sqlite3.connect('consultorio.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO agendamentos (cliente_nome, cliente_telefone, data_agendamento, horario, servico)
        VALUES (?, ?, ?, ?, ?)
    ''', (nome, telefone, data, horario, servico))
    conn.commit()
    conn.close()

def get_horarios_ocupados(data):
    conn = sqlite3.connect('consultorio.db')
    c = conn.cursor()
    c.execute('SELECT horario FROM agendamentos WHERE data_agendamento = ?', (data,))
    horarios = [row[0] for row in c.fetchall()]
    conn.close()
    return horarios

init_db()

# --- INTERFACE (FRONTEND) ---

# 1. Cabeçalho Personalizado
st.markdown('<div class="main-title">🦷 Dra. Thais Milene</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Odontologia Especializada e Humanizada</div>', unsafe_allow_html=True)

# 2. Botões de Ação (Estilo App)
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    # Botão 1: Novo Agendamento (Controlado pelo Streamlit)
    mostrar_agenda = st.button("📅 Novo Agendamento Online", type="primary", use_container_width=True)
    
    # Botão 2: WhatsApp (Link Externo)
    # Número formatado para API do Whats (apenas dígitos)
    fone_whats = "5512987054320" 
    msg_ola = "Olá Dra. Thais! Gostaria de tirar uma dúvida sobre os atendimentos."
    link_zap = f"https://wa.me/{fone_whats}?text={msg_ola.replace(' ', '%20')}"
    
    st.markdown(f"""
        <a href="{link_zap}" target="_blank" style="text-decoration:none;">
            <div class="big-button btn-secondary">💬 Falar no WhatsApp</div>
        </a>
    """, unsafe_allow_html=True)

# Lógica para manter o formulário aberto se clicar no botão
if 'mostrar_form' not in st.session_state:
    st.session_state['mostrar_form'] = False
if mostrar_agenda:
    st.session_state['mostrar_form'] = True

st.divider()

# 3. Formulário de Agendamento (Abre ao clicar)
if st.session_state['mostrar_form']:
    
    with st.container():
        # Perfil com os dados novos
        col_foto, col_texto = st.columns([1, 4])
        with col_foto:
            st.markdown("# 👩‍⚕️") 
        with col_texto:
            st.write("**Dra. Thais Milene dos Santos**")
            st.caption("Cirurgiã Dentista | CRO/SP Em Breve")

    st.subheader("🗓️ Escolha seu horário")
    
    # Input de Data
    data_escolhida = st.date_input("Data da Consulta", min_value=datetime.today())

    # Bloqueio de Fim de Semana
    if data_escolhida.weekday() >= 5:
        st.warning("⚠️ Atendimentos apenas de Segunda a Sexta-feira.")
    else:
        # Lógica de Vagas
        horarios_padrao = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        horarios_ocupados = get_horarios_ocupados(data_escolhida)
        horarios_livres = [h for h in horarios_padrao if h not in horarios_ocupados]

        if not horarios_livres:
            st.error("Agenda cheia para este dia. Por favor, escolha outra data.")
        else:
            with st.form("form_agendamento", clear_on_submit=True):
                st.write(f"Vagas para **{data_escolhida.strftime('%d/%m/%Y')}**:")
                hora_escolhida = st.selectbox("Selecione o horário", horarios_livres)
                
                st.markdown("---")
                nome = st.text_input("Seu Nome Completo")
                telefone = st.text_input("Seu WhatsApp (com DDD)")
                
                servicos = [
                    "🔍 Avaliação (Primeira vez)",
                    "✨ Limpeza / Profilaxia",
                    "🦷 Restauração",
                    "😁 Clareamento"
                ]
                servico = st.selectbox("Procedimento", servicos)
                
                # Botão de Enviar
                submitted = st.form_submit_button("✅ Confirmar Agendamento", type="primary")
                
                if submitted:
                    if nome and telefone:
                        salvar_agendamento(nome, telefone, data_escolhida, hora_escolhida, servico)
                        
                        st.success(f"Agendado! Te esperamos dia {data_escolhida.strftime('%d/%m')} às {hora_escolhida}.")
                        st.balloons()
                        
                        # Botão de Enviar Comprovante no Whats da Dra
                        msg_confirm = f"Olá! Agendei *{servico}* com a Dra. Thais para dia *{data_escolhida.strftime('%d/%m')}* às *{hora_escolhida}*."
                        link_confirm = f"https://wa.me/{fone_whats}?text={msg_confirm.replace(' ', '%20')}"
                        
                        st.markdown(f"""
                            <a href="{link_confirm}" target="_blank">
                                <button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; width:100%; font-weight:bold; cursor:pointer; margin-top:10px;">
                                    📲 Enviar confirmação no WhatsApp
                                </button>
                            </a>
                        """, unsafe_allow_html=True)
                        
                    else:
                        st.error("Preencha nome e telefone para continuar.")

# 4. Rodapé Atualizado
st.write(""); st.write("")
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    📍 <b>Atendimento em Taubaté</b> (Endereço disponível em breve)<br>
    📞 +55 12 98705-4320<br>
    © 2025 Dra. Thais Milene dos Santos
</div>
""", unsafe_allow_html=True)

# Área Admin (Sempre escondida no final)
with st.expander("🔐 Área da Dra. (Acesso Restrito)"):
    senha = st.text_input("Senha", type="password")
    if senha == "admin123":
        import pandas as pd
        conn = sqlite3.connect('consultorio.db')
        df = pd.read_sql_query("SELECT * FROM agendamentos ORDER BY data_agendamento DESC", conn)
        # Formatar a tabela para ficar mais bonita
        st.dataframe(df, use_container_width=True)
        conn.close()