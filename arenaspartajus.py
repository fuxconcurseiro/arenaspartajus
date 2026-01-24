import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime

# -----------------------------------------------------------------------------
# 0. IMPORTAÇÃO SEGURA (Prevenção de Erros)
# -----------------------------------------------------------------------------
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    LIBS_INSTALLED = True
except ImportError:
    LIBS_INSTALLED = False

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
# 3. INTEGRAÇÃO GOOGLE SHEETS (Backend Robusto)
# -----------------------------------------------------------------------------
def connect_db():
    """Tenta conectar à planilha ArenaSpartaJus_DB com tratamento de erros."""
    if not LIBS_INSTALLED:
        return None, "Bibliotecas 'gspread' ou 'oauth2client' não instaladas."

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Tenta acessar secrets com segurança
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open("ArenaSpartaJus_DB").sheet1, None
        else:
            return None, "Secrets não configurados (.streamlit/secrets.toml)."
    except Exception as e:
        return None, f"Erro na conexão: {str(e)}"

def load_data():
    """Carrega dados. Se falhar, usa dados padrão (offline) sem crashar."""
    sheet, error_msg = connect_db()
    
    if sheet:
        try:
            cell = sheet.find(TEST_USER)
            if cell:
                # Pega o JSON da coluna B
                json_data = sheet.cell(cell.row, 2).value
                return json.loads(json_data), cell.row, "Online"
            else:
                # Cria novo usuário se não existir
                sheet.append_row([TEST_USER, json.dumps(DEFAULT_USER_DATA)])
                new_cell = sheet.find(TEST_USER)
                return DEFAULT_USER_DATA, new_cell.row, "Online (Novo Usuário Criado)"
        except Exception as e:
            return DEFAULT_USER_DATA, None, f"Erro ao ler planilha: {str(e)}"
    
    # Retorna offline
    return DEFAULT_USER_DATA, None, f"Modo Offline ({error_msg})"

def save_data(row_idx, data):
    """Salva o progresso na planilha se possível."""
    sheet, _ = connect_db()
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
        "imagem": "🛡️",
        "dificuldade": "Fácil",
        "link_tec": "https://www.tecconcursos.com.br", 
        "max_erros": 3,
        "max_tempo": 20, 
        "xp_reward": 100,
        "max_hp": 50
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
        "xp_reward": 250,
        "max_hp": 80
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
        "xp_reward": 500,
        "max_hp": 120
    }
]

# -----------------------------------------------------------------------------
# 5. LÓGICA DO JOGO
# -----------------------------------------------------------------------------
def process_battle(tempo, acertos, erros, opponent):
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
    # Inicialização Segura
    if 'user_data' not in st.session_state:
        with st.spinner("Carregando Arena..."):
            data, row_idx, status_msg = load_data()
            st.session_state['user_data'] = data
            st.session_state['row_idx'] = row_idx
            st.session_state['connection_status'] = status_msg

    user = st.session_state['user_data']
    status = st.session_state['connection_status']

    # Aviso de Status (Debug amigável)
    if "Offline" in status:
        st.warning(f"⚠️ {status} - O jogo está rodando com dados locais. Seu progresso será perdido ao fechar a aba.")
    
    # --- SIDEBAR (PERFIL) ---
    with st.sidebar:
        st.markdown(f"# {user['avatar']} {TEST_USER}")
        st.caption(f"Status: {status}")
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        c1.metric("Nível", user['nivel'])
        c2.metric("XP", user['xp'])
        
        xp_next = user['nivel'] * 1000
        progresso = min(user['xp'] / xp_next, 1.0)
        st.progress(progresso, text=f"XP: {user['xp']} / {xp_next}")
        
        st.markdown("---")
        st.markdown(f"**⚔️ Vitórias:** {user['vitorias']}")
        st.markdown(f"**💀 Derrotas:** {user['derrotas']}")
        
        if st.button("Resetar Sessão"):
            st.session_state.clear()
            st.rerun()

    # --- MAIN ---
    st.markdown("<h1 class='main-header'>🏟️ ARENA SPARTAJUS</h1>", unsafe_allow_html=True)

    tab_arena, tab_historico = st.tabs(["⚔️ Batalhar", "📜 Histórico"])

    with tab_arena:
        if 'active_battle' not in st.session_state:
            # LOBBY
            st.subheader("Escolha seu desafio:")
            cols = st.columns(3)
            for idx, opp in enumerate(OPONENTS_DB):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="gladiator-card">
                        <div style="font-size: 50px;">{opp['imagem']}</div>
                        <h3>{opp['nome']}</h3>
                        <p style="color: #aaa; font-style: italic; min-height: 45px;">{opp['descricao']}</p>
                        <hr style="border-color: #d4af37;">
                        <p>🔥 <b>{opp['dificuldade']}</b></p>
                        <p>🏆 <b>{opp['xp_reward']} XP</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"DESAFIAR", key=f"btn_{opp['id']}", use_container_width=True):
                        st.session_state['active_battle'] = opp
                        st.session_state['start_time'] = time.time()
                        st.rerun()

        else:
            # BATALHA
            opp = st.session_state['active_battle']
            st.info(f"⚔️ BATALHA EM CURSO VS **{opp['nome'].upper()}**")
            
            c1, c2 = st.columns([1, 1], gap="large")
            
            with c1:
                st.markdown("### 1. Execute a Missão")
                st.link_button("🛡️ ABRIR TEC CONCURSOS", opp['link_tec'], type="primary", use_container_width=True)
                st.markdown(f"""
                **Condições de Vitória:**
                - Tempo Máximo: **{opp['max_tempo']} min**
                - Erros Máximos: **{opp['max_erros']}**
                """)

            with c2:
                st.markdown("### 2. Relatório")
                with st.form("battle_form"):
                    tempo = st.number_input("Tempo (min):", 0, 120)
                    acertos = st.number_input("Acertos:", 0, 50)
                    erros = st.number_input("Erros:", 0, 50)
                    
                    if st.form_submit_button("⚔️ FINALIZAR"):
                        res, det = process_battle(tempo, acertos, erros, opp)
                        
                        if res == "vitoria":
                            user['xp'] += det
                            user['vitorias'] += 1
                            if user['xp'] >= (user['nivel'] * 1000):
                                user['nivel'] += 1
                                st.balloons()
                                st.toast("LEVEL UP!", icon="🆙")
                            st.success(f"VITÓRIA! +{det} XP")
                        else:
                            user['derrotas'] += 1
                            st.error(f"DERROTA: {', '.join(det)}")
                        
                        # Log
                        log = {
                            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "oponente": opp['nome'],
                            "resultado": res,
                            "detalhes": det,
                            "xp_ganho": det if res == "vitoria" else 0
                        }
                        user['historico_batalhas'].append(log)
                        
                        st.session_state['user_data'] = user
                        save_data(st.session_state['row_idx'], user)
                        
                        if st.form_submit_button("Voltar"):
                            del st.session_state['active_battle']
                            st.rerun()

            if st.button("Fugir (Cancelar)"):
                del st.session_state['active_battle']
                st.rerun()

    with tab_historico:
        if user['historico_batalhas']:
            st.dataframe(pd.DataFrame(user['historico_batalhas']))
        else:
            st.info("Sem registros ainda.")

if __name__ == "__main__":
    main()
