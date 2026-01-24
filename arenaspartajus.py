import streamlit as st
import pandas as pd
from datetime import datetime
import time
import random

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E TEMA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Arena SpartaJus",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada (Tema Gladiador)
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: #d4af37; /* Dourado */
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 30px;
    }
    .gladiator-card {
        background-color: #1e2130;
        border: 2px solid #d4af37;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
    }
    .battle-stat {
        font-size: 1.2rem;
        font-weight: bold;
        color: #ff4b4b;
    }
    .victory-text {
        color: #00ff00;
        font-weight: bold;
        font-size: 2rem;
        text-align: center;
    }
    .defeat-text {
        color: #ff0000;
        font-weight: bold;
        font-size: 2rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DADOS MOCKADOS (Substituir por Google Sheets depois)
# -----------------------------------------------------------------------------

# Simulação do Banco de Dados de Usuários (Vindo do MentorSpartajus)
USERS_DB = {
    "aluno@spartajus.com": {"nome": "Spartano 01", "nivel": 1, "xp": 0, "avatar": "🧑‍🚀", "vitorias": 0},
    "admin": {"nome": "Mestre Sparta", "nivel": 99, "xp": 10000, "avatar": "👑", "vitorias": 50}
}

# Simulação dos Oponentes (Níveis de Dificuldade)
OPONENTS_DB = [
    {
        "id": 1,
        "nome": "Recruta da Banca",
        "descricao": "Um oponente fraco, ideal para aquecimento.",
        "imagem": "🛡️", # Substituir por URL da imagem depois
        "dificuldade": "Fácil",
        "link_tec": "https://www.tecconcursos.com.br", # Exemplo
        "max_erros": 3,
        "max_tempo": 20, # minutos para 10 questões
        "xp_reward": 100,
        "hp": 50
    },
    {
        "id": 2,
        "nome": "Legionário da Lei Seca",
        "descricao": "Exige atenção aos detalhes. Não tolere erros.",
        "imagem": "⚔️",
        "dificuldade": "Média",
        "link_tec": "https://www.tecconcursos.com.br",
        "max_erros": 2,
        "max_tempo": 15,
        "xp_reward": 250,
        "hp": 80
    },
    {
        "id": 3,
        "nome": "Centurião da Jurisprudência",
        "descricao": "Rápido e letal. Apenas para os preparados.",
        "imagem": "👹",
        "dificuldade": "Difícil",
        "link_tec": "https://www.tecconcursos.com.br",
        "max_erros": 1,
        "max_tempo": 12,
        "xp_reward": 500,
        "hp": 120
    }
]

# -----------------------------------------------------------------------------
# FUNÇÕES DE LÓGICA
# -----------------------------------------------------------------------------

def check_login(email):
    """Verifica se o usuário existe no banco de dados simulado."""
    # FUTURO: Substituir por verificação no Google Sheets (Planilha de Alunos)
    if email in USERS_DB:
        return USERS_DB[email]
    return None

def process_battle(user_input_tempo, user_input_acertos, user_input_erros, opponent):
    """Lógica que define vitória ou derrota."""
    
    # Critérios de Derrota
    derrota_tempo = user_input_tempo > opponent['max_tempo']
    derrota_erros = user_input_erros > opponent['max_erros']
    
    # Total de questões (assumindo 10 por padrão, mas pode ser calculado)
    total_questoes = user_input_acertos + user_input_erros
    if total_questoes == 0:
        return "invalido", 0
        
    if derrota_tempo or derrota_erros:
        motivo = []
        if derrota_tempo: motivo.append("Estourou o tempo limite")
        if derrota_erros: motivo.append("Errou mais que o permitido")
        return "derrota", motivo
    else:
        return "vitoria", opponent['xp_reward']

def update_user_stats(email, xp_gain, win=False):
    """Atualiza XP e Nível do usuário."""
    # FUTURO: Gravar no Google Sheets
    user = st.session_state['user_data']
    user['xp'] += xp_gain
    if win:
        user['vitorias'] += 1
    
    # Lógica simples de Level Up (a cada 1000 xp)
    novo_nivel = 1 + (user['xp'] // 1000)
    if novo_nivel > user['nivel']:
        st.toast(f"🎉 PARABÉNS! Você subiu para o Nível {novo_nivel}!", icon="🆙")
        user['nivel'] = novo_nivel
    
    st.session_state['user_data'] = user

# -----------------------------------------------------------------------------
# INTERFACE DO USUÁRIO
# -----------------------------------------------------------------------------

def login_screen():
    st.markdown("<h1 style='text-align: center; color: #d4af37;'>⚔️ ARENA SPARTAJUS ⚔️</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Identifique-se, Gladiador.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email = st.text_input("E-mail de Cadastro (MentorSpartajus)")
        if st.button("ENTRAR NA ARENA", use_container_width=True):
            user = check_login(email)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user_email'] = email
                st.session_state['user_data'] = user
                st.rerun()
            else:
                st.error("Gladiador não encontrado. Verifique seu e-mail.")

def main_app():
    user = st.session_state['user_data']
    
    # --- SIDEBAR (PERFIL DO GLADIADOR) ---
    with st.sidebar:
        st.markdown(f"# {user['avatar']} {user['nome']}")
        st.markdown("---")
        st.metric("Nível", user['nivel'])
        st.metric("XP Total", user['xp'])
        st.metric("Vitórias em Batalha", user['vitorias'])
        st.markdown("---")
        if st.button("Sair"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- CABEÇALHO ---
    st.markdown("<h1 class='main-header'>🏟️ ARENA DE BATALHA</h1>", unsafe_allow_html=True)

    # Tabs para navegação
    tab1, tab2 = st.tabs(["⚔️ Escolher Oponente", "📜 Histórico de Batalhas"])

    with tab1:
        # Se não estiver em batalha, mostra lista de oponentes
        if 'active_battle' not in st.session_state:
            st.subheader("Escolha seu desafio de hoje:")
            
            # Grid de oponentes
            cols = st.columns(3)
            for idx, opp in enumerate(OPONENTS_DB):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="gladiator-card">
                        <div style="font-size: 50px;">{opp['imagem']}</div>
                        <h3>{opp['nome']}</h3>
                        <p style="color: #aaa; font-style: italic;">{opp['descricao']}</p>
                        <hr style="border-color: #d4af37;">
                        <p><b>Dificuldade:</b> {opp['dificuldade']}</p>
                        <p>❤️ <b>Máx. Erros:</b> {opp['max_erros']}</p>
                        <p>⏳ <b>Máx. Tempo:</b> {opp['max_tempo']} min</p>
                        <p>🏆 <b>Recompensa:</b> {opp['xp_reward']} XP</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"DESAFIAR", key=f"btn_{opp['id']}", use_container_width=True):
                        st.session_state['active_battle'] = opp
                        st.session_state['battle_start_time'] = time.time()
                        st.rerun()

        # Se estiver em batalha (Tela de Resolução)
        else:
            opponent = st.session_state['active_battle']
            
            st.info(f"⚡ BATALHA INICIADA CONTRA: **{opponent['nome'].upper()}**")
            
            col_l, col_r = st.columns([1, 1])
            
            with col_l:
                st.markdown("### 1. A Luta")
                st.markdown("Clique no botão abaixo para abrir o caderno de questões no TEC Concursos.")
                st.link_button(f"🛡️ IR PARA O CAMPO DE BATALHA (TEC)", opponent['link_tec'], type="primary", use_container_width=True)
                
                st.markdown("---")
                st.image("https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcjJ5ZHRxbDM1Zm55eGZ5eGZ5eGZ5eGZ5eGZ5eGZ5eGZ5eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l0HlCqV35hdEg2GMU/giphy.gif", caption="Concentre-se, Gladiador!", use_column_width=True)

            with col_r:
                st.markdown("### 2. O Relatório")
                st.warning("Só preencha após terminar as questões!")
                
                with st.form("battle_report"):
                    tempo_gasto = st.number_input("Tempo gasto (minutos):", min_value=0, max_value=120, step=1)
                    acertos = st.number_input("Questões CERTAS:", min_value=0, max_value=50, step=1)
                    erros = st.number_input("Questões ERRADAS:", min_value=0, max_value=50, step=1)
                    
                    submitted = st.form_submit_button("⚔️ ENCERRAR BATALHA")
                    
                    if submitted:
                        resultado, dados = process_battle(tempo_gasto, acertos, erros, opponent)
                        
                        if resultado == "vitoria":
                            st.balloons()
                            update_user_stats(st.session_state['user_email'], dados, win=True)
                            st.markdown(f"""
                                <div class="gladiator-card" style="background-color: rgba(0, 255, 0, 0.1);">
                                    <h2 class="victory-text">VITÓRIA!</h2>
                                    <p>Você aniquilou seu oponente!</p>
                                    <p><b>XP Ganho:</b> +{dados}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        elif resultado == "derrota":
                            st.markdown(f"""
                                <div class="gladiator-card" style="background-color: rgba(255, 0, 0, 0.1);">
                                    <h2 class="defeat-text">DERROTA...</h2>
                                    <p>O oponente foi superior hoje.</p>
                                    <p><b>Motivo:</b> {', '.join(dados)}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error("Dados inválidos.")
                            
                        # Botão para voltar ao lobby
                        if st.form_submit_button("Voltar ao Lobby"): # Hack para resetar state
                            del st.session_state['active_battle']
                            st.rerun()
            
            if st.button("Cancelar Batalha (Fugir)"):
                del st.session_state['active_battle']
                st.rerun()

    with tab2:
        st.write("Em breve: Gráfico de evolução e histórico completo das suas lutas.")

# -----------------------------------------------------------------------------
# FLUXO PRINCIPAL
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_screen()
else:
    main_app()