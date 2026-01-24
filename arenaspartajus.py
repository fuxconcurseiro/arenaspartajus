import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E TEMA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Arena SpartaJus",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS (Tema Gladiador Escuro/Dourado)
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
        text-shadow: 2px 2px 4px #000000;
    }
    .gladiator-card {
        background-color: #1e2130;
        border: 2px solid #d4af37;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        transition: transform 0.2s;
    }
    .gladiator-card:hover {
        transform: scale(1.02);
        border-color: #ff4b4b;
    }
    .victory-text { color: #00ff00; font-weight: bold; font-size: 2rem; text-align: center; }
    .defeat-text { color: #ff0000; font-weight: bold; font-size: 2rem; text-align: center; }
    
    /* Input fields dark theme */
    div[data-baseweb="input"] > div {
        background-color: #262730;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CONFIGURAÇÃO DO USUÁRIO TESTE (HARDCODED)
# -----------------------------------------------------------------------------
TEST_USER = "fux_concurseiro"
DEFAULT_USER_DATA = {
    "nivel": 1, 
    "xp": 0, 
    "avatar": "🧑‍🚀", 
    "vitorias": 0, 
    "derrotas": 0, 
    "historico_batalhas": []
}

# -----------------------------------------------------------------------------
# 3. INTEGRAÇÃO GOOGLE SHEETS (Backend)
# -----------------------------------------------------------------------------
def connect_db():
    """Tenta conectar à planilha ArenaSpartaJus_DB."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Verifica se existem secrets configurados
    if "gcp_service_account" in st.secrets:
        try:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open("ArenaSpartaJus_DB").sheet1
        except Exception as e:
            st.warning(f"Erro de conexão com Google Sheets: {e}")
            return None
    return None

def load_data():
    """Carrega dados do usuário teste. Se falhar, usa dados padrão (offline)."""
    sheet = connect_db()
    if sheet:
        try:
            cell = sheet.find(TEST_USER)
            if cell:
                # Pega o JSON da coluna B
                json_data = sheet.cell(cell.row, 2).value
                return json.loads(json_data), cell.row
            else:
                # Usuário não existe na planilha, cria novo
                st.toast("Usuário novo detectado. Criando registro...")
                sheet.append_row([TEST_USER, json.dumps(DEFAULT_USER_DATA)])
                new_cell = sheet.find(TEST_USER)
                return DEFAULT_USER_DATA, new_cell.row
        except Exception as e:
            st.error(f"Erro ao ler dados: {e}")
    
    # Fallback para modo offline
    st.toast("⚠️ Modo Offline (Sem conexão com Planilha)", icon="🔌")
    return DEFAULT_USER_DATA, None

def save_data(row_idx, data):
    """Salva o progresso na planilha."""
    sheet = connect_db()
    if sheet and row_idx:
        try:
            sheet.update_cell(row_idx, 2, json.dumps(data))
            st.toast("Progresso salvo na nuvem!", icon="☁️")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
    else:
        st.toast("Dados salvos apenas localmente (Sessão)", icon="💾")

# -----------------------------------------------------------------------------
# 4. BASE DE DADOS DE OPONENTES
# -----------------------------------------------------------------------------
OPONENTS_DB = [
    {
        "id": 1,
        "nome": "Recruta da Banca",
        "descricao": "Um oponente fraco. Ideal para aquecimento diário.",
        "imagem": "🛡️", # Substituir por URL de imagem depois
        "dificuldade": "Fácil",
        "link_tec": "https://www.tecconcursos.com.br", # Colocar link específico do caderno aqui
        "max_erros": 3,
        "max_tempo": 20, # minutos
        "xp_reward": 100
    },
    {
        "id": 2,
        "nome": "Legionário da Lei Seca",
        "descricao": "Exige atenção aos detalhes da letra da lei.",
        "imagem": "⚔️",
        "dificuldade": "Média",
        "link_tec": "https://www.tecconcursos.com.br",
        "max_erros": 2,
        "max_tempo": 15,
        "xp_reward": 250
    },
    {
        "id": 3,
        "nome": "Centurião da Jurisprudência",
        "descricao": "Rápido, letal e cheio de pegadinhas.",
        "imagem": "👹",
        "dificuldade": "Difícil",
        "link_tec": "https://www.tecconcursos.com.br",
        "max_erros": 1,
        "max_tempo": 12,
        "xp_reward": 500
    }
]

# -----------------------------------------------------------------------------
# 5. LÓGICA DO JOGO
# -----------------------------------------------------------------------------
def process_battle(tempo, acertos, erros, opponent):
    """Calcula vitória ou derrota baseado nas regras do oponente."""
    derrota_tempo = tempo > opponent['max_tempo']
    derrota_erros = erros > opponent['max_erros']
    total_questoes = acertos + erros
    
    if total_questoes == 0:
        return "invalido", 0
        
    if derrota_tempo or derrota_erros:
        motivos = []
        if derrota_tempo: motivos.append(f"Tempo esgotado (> {opponent['max_tempo']} min)")
        if derrota_erros: motivos.append(f"Erros excessivos (> {opponent['max_erros']})")
        return "derrota", motivos
    else:
        return "vitoria", opponent['xp_reward']

# -----------------------------------------------------------------------------
# 6. APP PRINCIPAL
# -----------------------------------------------------------------------------
def main():
    # Inicialização do Estado (Carrega dados na primeira execução)
    if 'user_data' not in st.session_state:
        data, row_idx = load_data()
        st.session_state['user_data'] = data
        st.session_state['row_idx'] = row_idx

    user = st.session_state['user_data']
    
    # --- SIDEBAR (PERFIL) ---
    with st.sidebar:
        st.markdown(f"# {user['avatar']} {TEST_USER}")
        st.caption("Gladiador Iniciante")
        st.markdown("---")
        
        # Stats
        c1, c2 = st.columns(2)
        c1.metric("Nível", user['nivel'])
        c2.metric("XP", user['xp'])
        
        # Barra de XP (Simulada: Nível * 1000 para subir)
        xp_next = user['nivel'] * 1000
        progresso = min(user['xp'] / xp_next, 1.0)
        st.progress(progresso, text=f"XP: {user['xp']} / {xp_next}")
        
        st.markdown("---")
        st.markdown(f"**⚔️ Vitórias:** {user['vitorias']}")
        st.markdown(f"**💀 Derrotas:** {user['derrotas']}")
        
        if st.button("Recarregar Dados"):
            st.session_state.clear()
            st.rerun()

    # --- CABEÇALHO ---
    st.markdown("<h1 class='main-header'>🏟️ ARENA SPARTAJUS</h1>", unsafe_allow_html=True)

    # --- NAVEGAÇÃO ---
    tab_arena, tab_historico = st.tabs(["⚔️ Batalhar", "📜 Pergaminho de Histórico"])

    with tab_arena:
        # Se NÃO estiver em batalha, mostra a seleção
        if 'active_battle' not in st.session_state:
            st.subheader("Escolha seu desafio, Spartano:")
            
            # Grid Responsivo
            cols = st.columns(3)
            for idx, opp in enumerate(OPONENTS_DB):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="gladiator-card">
                        <div style="font-size: 50px;">{opp['imagem']}</div>
                        <h3>{opp['nome']}</h3>
                        <p style="color: #aaa; font-style: italic; min-height: 40px;">{opp['descricao']}</p>
                        <hr style="border-color: #d4af37;">
                        <div style="display: flex; justify-content: space-between;">
                            <span>🔥 {opp['dificuldade']}</span>
                            <span>🏆 {opp['xp_reward']} XP</span>
                        </div>
                        <div style="margin-top: 10px; font-size: 0.9em;">
                            <p>⏳ Máx: {opp['max_tempo']} min | ❤️ Erros: {opp['max_erros']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"DESAFIAR", key=f"btn_{opp['id']}", use_container_width=True):
                        st.session_state['active_battle'] = opp
                        st.session_state['start_time'] = time.time()
                        st.rerun()

        # Se ESTIVER em batalha
        else:
            opp = st.session_state['active_battle']
            
            # Header da Batalha
            st.info(f"⚔️ BATALHA EM CURSO VS **{opp['nome'].upper()}**")
            
            col_action, col_report = st.columns([1, 1], gap="large")
            
            with col_action:
                st.markdown("### 1. Execute a Missão")
                st.markdown("Clique abaixo para abrir o caderno de questões.")
                st.link_button(
                    "🛡️ ABRIR TEC CONCURSOS", 
                    opp['link_tec'], 
                    type="primary", 
                    use_container_width=True
                )
                
                st.markdown("---")
                st.markdown("**Regras de Combate:**")
                st.markdown(f"- **Tempo Limite:** {opp['max_tempo']} minutos")
                st.markdown(f"- **Limite de Erros:** {opp['max_erros']} erros")
                st.markdown("*(Seja honesto, honra é tudo para um gladiador)*")

            with col_report:
                st.markdown("### 2. Relatório de Combate")
                with st.form("battle_form"):
                    tempo = st.number_input("Tempo Gasto (minutos):", min_value=0, step=1)
                    acertos = st.number_input("Questões Certas:", min_value=0, step=1)
                    erros = st.number_input("Questões Erradas:", min_value=0, step=1)
                    
                    submitted = st.form_submit_button("⚔️ ENCERRAR BATALHA")
                    
                    if submitted:
                        resultado, detalhes = process_battle(tempo, acertos, erros, opp)
                        
                        # Processamento
                        if resultado == "vitoria":
                            user['xp'] += detalhes
                            user['vitorias'] += 1
                            # Verifica Level Up
                            if user['xp'] >= (user['nivel'] * 1000):
                                user['nivel'] += 1
                                st.balloons()
                                st.toast(f"LEVEL UP! Nível {user['nivel']} alcançado!", icon="🆙")
                            else:
                                st.toast("Vitória registrada!", icon="🏆")
                                
                            st.markdown(f"""
                                <div class="gladiator-card" style="background-color: rgba(0, 255, 0, 0.1); border-color: #00ff00;">
                                    <h2 class="victory-text">VITÓRIA!</h2>
                                    <p>Você ganhou <b>{detalhes} XP</b>.</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                        elif resultado == "derrota":
                            user['derrotas'] += 1
                            st.markdown(f"""
                                <div class="gladiator-card" style="background-color: rgba(255, 0, 0, 0.1); border-color: #ff0000;">
                                    <h2 class="defeat-text">DERROTA</h2>
                                    <p>Motivo: {', '.join(detalhes)}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        # Salvar Log
                        log_entry = {
                            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "oponente": opp['nome'],
                            "resultado": resultado,
                            "detalhes": detalhes,
                            "xp_ganho": detalhes if resultado == "vitoria" else 0
                        }
                        user['historico_batalhas'].append(log_entry)
                        
                        # Atualiza Session State e DB
                        st.session_state['user_data'] = user
                        save_data(st.session_state['row_idx'], user)
                        
                        # Botão de Retorno
                        if st.form_submit_button("Voltar ao Lobby"):
                            del st.session_state['active_battle']
                            st.rerun()

            if st.button("Fugir da Batalha (Cancelar)"):
                del st.session_state['active_battle']
                st.rerun()

    with tab_historico:
        st.subheader("📜 Seu Histórico de Batalhas")
        if user['historico_batalhas']:
            # Cria DataFrame para exibição bonita
            df = pd.DataFrame(user['historico_batalhas'])
            # Reordena colunas para ficar legível
            df = df[['data', 'oponente', 'resultado', 'xp_ganho', 'detalhes']]
            st.dataframe(
                df, 
                use_container_width=True,
                column_config={
                    "xp_ganho": st.column_config.NumberColumn("XP", format="%d XP"),
                    "resultado": st.column_config.TextColumn("Resultado", help="Vitória ou Derrota"),
                }
            )
        else:
            st.info("Nenhuma batalha registrada ainda. Vá para a arena!")

# Executar App
if __name__ == "__main__":
    main()
