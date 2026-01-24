import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import random

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
    
    /* Estilo do Cartão de Treinamento (Doctore) */
    .training-card {
        background-color: #262730;
        border-left: 5px solid #d4af37;
        padding: 30px;
        border-radius: 5px;
        font-size: 1.3rem;
        font-family: 'Georgia', serif;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }
    .justificativa-box {
        background-color: #1c2e24; /* Verde escuro sutil */
        border: 1px solid #4caf50;
        padding: 15px;
        border-radius: 5px;
        margin-top: 15px;
    }
    .origem-tag {
        font-size: 0.8rem;
        color: #aaa;
        font-style: italic;
        margin-top: 5px;
        display: block;
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
# 2. CONFIGURAÇÃO DO USUÁRIO TESTE
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
# 3. BASE DE DADOS DOCTORE (TREINAMENTO)
# -----------------------------------------------------------------------------
# AQUI VOCÊ VAI ADICIONAR SUAS QUESTÕES
DOCTORE_DB = {
    "Direito Constitucional": [
        {
            "id": 101,
            "texto": "Segundo o STF, é inconstitucional a lei estadual que determina que as empresas de telecomunicações forneçam dados cadastrais de usuários diretamente ao Ministério Público e às polícias, sem prévia autorização judicial.",
            "gabarito": "Certo",
            "origem": "ADI 7777/DF, Rel. Min. Gilmar Mendes, j. 15.08.2023",
            "explicacao": "A proteção de dados pessoais e o sigilo das comunicações são cláusulas de reserva de jurisdição."
        },
        {
            "id": 102,
            "texto": "Normas constitucionais de eficácia limitada são aquelas que, desde a promulgação da Constituição, possuem aplicabilidade imediata, direta e integral.",
            "gabarito": "Errado",
            "origem": "Cobrado em: MPE/GO 2022 - Promotor de Justiça",
            "explicacao": "Essas são as normas de eficácia plena. As de eficácia limitada dependem de regulamentação posterior para produzirem todos os seus efeitos."
        }
    ],
    "Direito Penal": [
        {
            "id": 201,
            "texto": "O princípio da insignificância é aplicável aos crimes contra a administração pública, desde que o prejuízo seja ínfimo.",
            "gabarito": "Errado",
            "origem": "Súmula 599 do STJ",
            "explicacao": "O princípio da insignificância é inaplicável aos crimes contra a administração pública."
        }
    ],
    "Processo Civil": [
        {
            "id": 301,
            "texto": "A contagem dos prazos processuais em dias úteis, prevista no CPC/2015, aplica-se também aos Juizados Especiais Cíveis.",
            "gabarito": "Certo",
            "origem": "Lei 13.728/2018",
            "explicacao": "A Lei 13.728/2018 alterou a Lei 9.099/95 para estabelecer que, na contagem de prazo em dias, computar-se-ão somente os dias úteis."
        }
    ]
}

# -----------------------------------------------------------------------------
# 4. INTEGRAÇÃO GOOGLE SHEETS
# -----------------------------------------------------------------------------
def connect_db():
    if not LIBS_INSTALLED:
        return None, "Bibliotecas ausentes."

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open("ArenaSpartaJus_DB").sheet1, None
        else:
            return None, "Secrets não configurados."
    except Exception as e:
        return None, f"Erro na conexão: {str(e)}"

def load_data():
    sheet, error_msg = connect_db()
    if sheet:
        try:
            cell = sheet.find(TEST_USER)
            if cell:
                json_data = sheet.cell(cell.row, 2).value
                return json.loads(json_data), cell.row, "Online"
            else:
                sheet.append_row([TEST_USER, json.dumps(DEFAULT_USER_DATA)])
                new_cell = sheet.find(TEST_USER)
                return DEFAULT_USER_DATA, new_cell.row, "Online (Novo)"
        except Exception as e:
            return DEFAULT_USER_DATA, None, f"Erro: {str(e)}"
    return DEFAULT_USER_DATA, None, f"Modo Offline ({error_msg})"

def save_data(row_idx, data):
    sheet, _ = connect_db()
    if sheet and row_idx:
        try:
            sheet.update_cell(row_idx, 2, json.dumps(data))
        except Exception:
            pass # Silencioso para não travar UX

# -----------------------------------------------------------------------------
# 5. DADOS DOS OPONENTES
# -----------------------------------------------------------------------------
OPONENTS_DB = [
    {
        "id": 1,
        "nome": "Recruta da Banca",
        "descricao": "Um oponente fraco. Ideal para aquecimento.",
        "imagem": "🛡️",
        "dificuldade": "Fácil",
        "link_tec": "https://www.tecconcursos.com.br", 
        "max_erros": 3, "max_tempo": 20, "xp_reward": 100
    },
    {
        "id": 2,
        "nome": "Legionário da Lei Seca",
        "descricao": "Exige atenção aos detalhes da lei.",
        "imagem": "⚔️",
        "dificuldade": "Média",
        "link_tec": "https://www.tecconcursos.com.br",
        "max_erros": 2, "max_tempo": 15, "xp_reward": 250
    },
    {
        "id": 3,
        "nome": "Centurião da Jurisprudência",
        "descricao": "Rápido e letal.",
        "imagem": "👹",
        "dificuldade": "Difícil",
        "link_tec": "https://www.tecconcursos.com.br",
        "max_erros": 1, "max_tempo": 12, "xp_reward": 500
    }
]

# -----------------------------------------------------------------------------
# 6. LÓGICA DO JOGO (BATALHA E DOCTORE)
# -----------------------------------------------------------------------------
def process_battle(tempo, acertos, erros, opponent):
    derrota_tempo = tempo > opponent['max_tempo']
    derrota_erros = erros > opponent['max_erros']
    if (acertos + erros) == 0: return "invalido", 0
    
    if derrota_tempo or derrota_erros:
        motivos = []
        if derrota_tempo: motivos.append("Tempo esgotado")
        if derrota_erros: motivos.append("Muitos erros")
        return "derrota", motivos
    return "vitoria", opponent['xp_reward']

def initialize_doctore_session(niche):
    """Inicializa ou reinicia a sessão de treino para um nicho."""
    st.session_state['doctore_questions'] = DOCTORE_DB[niche].copy()
    random.shuffle(st.session_state['doctore_questions']) # Embaralha
    st.session_state['doctore_idx'] = 0
    st.session_state['doctore_revealed'] = False
    st.session_state['doctore_result'] = None # "correto" ou "errado"

# -----------------------------------------------------------------------------
# 7. APP PRINCIPAL
# -----------------------------------------------------------------------------
def main():
    if 'user_data' not in st.session_state:
        with st.spinner("Entrando na Arena..."):
            data, row_idx, status = load_data()
            st.session_state['user_data'] = data
            st.session_state['row_idx'] = row_idx
            st.session_state['connection_status'] = status

    user = st.session_state['user_data']
    status = st.session_state['connection_status']

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"# {user['avatar']} {TEST_USER}")
        if "Offline" in status:
            st.warning("Modo Offline")
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("Nível", user['nivel'])
        c2.metric("XP", user['xp'])
        st.progress(min(user['xp'] / (user['nivel']*1000), 1.0))
        st.markdown("---")
        st.write(f"Vitórias: {user['vitorias']}")
        if st.button("Resetar App"):
            st.session_state.clear()
            st.rerun()

    # --- MAIN ---
    st.markdown("<h1 class='main-header'>🏟️ ARENA SPARTAJUS</h1>", unsafe_allow_html=True)

    # Abas atualizadas
    tab_arena, tab_doctore, tab_historico = st.tabs(["⚔️ Batalhar", "🦉 Doctore (Treino)", "📜 Histórico"])

    # -------------------------------------------------------------------------
    # ABA 1: BATALHA (Lógica Mantida)
    # -------------------------------------------------------------------------
    with tab_arena:
        if 'active_battle' not in st.session_state:
            st.subheader("Escolha seu desafio:")
            cols = st.columns(3)
            for idx, opp in enumerate(OPONENTS_DB):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="gladiator-card">
                        <div style="font-size: 40px;">{opp['imagem']}</div>
                        <h4>{opp['nome']}</h4>
                        <p style="font-size:0.8rem; color:#aaa;">{opp['descricao']}</p>
                        <hr style="border-color:#d4af37;">
                        <p>🔥 <b>{opp['dificuldade']}</b> | 🏆 <b>{opp['xp_reward']} XP</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("LUTAR", key=f"btn_{opp['id']}", use_container_width=True):
                        st.session_state['active_battle'] = opp
                        st.rerun()
        else:
            opp = st.session_state['active_battle']
            st.info(f"⚔️ COMBATE: {opp['nome'].upper()}")
            c1, c2 = st.columns(2)
            with c1:
                st.link_button("🛡️ ABRIR TEC CONCURSOS", opp['link_tec'], type="primary", use_container_width=True)
                st.markdown(f"*Tempo: {opp['max_tempo']} min | Erros: {opp['max_erros']}*")
            with c2:
                with st.form("battle_form"):
                    t = st.number_input("Minutos:", 0)
                    a = st.number_input("Acertos:", 0)
                    e = st.number_input("Erros:", 0)
                    if st.form_submit_button("FINALIZAR"):
                        res, det = process_battle(t, a, e, opp)
                        if res == "vitoria":
                            user['xp'] += det
                            user['vitorias'] += 1
                            if user['xp'] >= (user['nivel']*1000):
                                user['nivel'] += 1
                                st.balloons()
                            st.success(f"VITÓRIA! +{det} XP")
                        else:
                            user['derrotas'] += 1
                            st.error("DERROTA")
                        
                        user['historico_batalhas'].append({
                            "data": datetime.now().strftime("%Y-%m-%d"),
                            "oponente": opp['nome'], "resultado": res, "xp_ganho": det if res=="vitoria" else 0
                        })
                        save_data(st.session_state['row_idx'], user)
                        del st.session_state['active_battle']
                        st.rerun()
            if st.button("Fugir"):
                del st.session_state['active_battle']
                st.rerun()

    # -------------------------------------------------------------------------
    # ABA 2: DOCTORE (NOVA FUNCIONALIDADE)
    # -------------------------------------------------------------------------
    with tab_doctore:
        st.markdown("### 🦉 Treinamento com o Doctore")
        st.markdown("O Doctore apresenta uma assertiva. Você deve julgar se está **Certa** ou **Errada**.")
        
        # 1. Seleção de Nicho
        nichos_disponiveis = list(DOCTORE_DB.keys())
        nicho_selecionado = st.selectbox("Escolha o Nicho de Treinamento:", nichos_disponiveis)
        
        # Inicializa se mudou o nicho ou se não existe
        if 'current_niche' not in st.session_state or st.session_state['current_niche'] != nicho_selecionado:
            st.session_state['current_niche'] = nicho_selecionado
            initialize_doctore_session(nicho_selecionado)
        
        # 2. Mostra Questão Atual
        questions = st.session_state['doctore_questions']
        idx = st.session_state['doctore_idx']
        
        if idx < len(questions):
            q_atual = questions[idx]
            
            # Barra de Progresso do Treino
            st.progress((idx) / len(questions), text=f"Questão {idx + 1} de {len(questions)}")
            
            # O Cartão da Questão
            st.markdown(f"""
            <div class="training-card">
                {q_atual['texto']}
            </div>
            """, unsafe_allow_html=True)
            
            # Área de Interação
            if not st.session_state['doctore_revealed']:
                col_c, col_e = st.columns(2)
                with col_c:
                    if st.button("✅ CERTO", use_container_width=True):
                        st.session_state['doctore_revealed'] = True
                        st.session_state['doctore_choice'] = "Certo"
                        st.rerun()
                with col_e:
                    if st.button("❌ ERRADO", use_container_width=True):
                        st.session_state['doctore_revealed'] = True
                        st.session_state['doctore_choice'] = "Errado"
                        st.rerun()
            
            else:
                # 3. Resultado e Justificativa
                escolha = st.session_state['doctore_choice']
                gabarito = q_atual['gabarito']
                acertou = escolha == gabarito
                
                if acertou:
                    st.success(f"🎯 GOLPE CERTEIRO! O gabarito é **{gabarito.upper()}**.")
                    # Pequeno bônus de XP por treino (opcional)
                    # user['xp'] += 10 
                else:
                    st.error(f"💀 GUARDA BAIXA! Você marcou {escolha}, mas é **{gabarito.upper()}**.")
                
                # Exibição da Justificativa
                st.markdown(f"""
                <div class="justificativa-box">
                    <h4>⚖️ Justificativa do Doctore:</h4>
                    <p>{q_atual['explicacao']}</p>
                    <span class="origem-tag">📌 Origem: {q_atual['origem']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("")
                if st.button("Próximo Desafio ➡️", type="primary"):
                    st.session_state['doctore_idx'] += 1
                    st.session_state['doctore_revealed'] = False
                    st.rerun()
        
        else:
            st.markdown("### 🎉 Treino Concluído!")
            st.write(f"Você finalizou todas as questões de {nicho_selecionado}.")
            if st.button("Reiniciar Treino"):
                initialize_doctore_session(nicho_selecionado)
                st.rerun()

    # -------------------------------------------------------------------------
    # ABA 3: HISTÓRICO
    # -------------------------------------------------------------------------
    with tab_historico:
        if user['historico_batalhas']:
            st.dataframe(pd.DataFrame(user['historico_batalhas']))
        else:
            st.info("Sem registros.")

if __name__ == "__main__":
    main()
```

### Como Alimentar o Doctore

Para adicionar suas questões extraídas, basta editar a variável `DOCTORE_DB` no topo do código. Use este formato:

```python
    "Nome da Matéria": [
        {
            "id": 1, # Número único
            "texto": "Coloque a assertiva aqui...",
            "gabarito": "Certo", # ou "Errado"
            "origem": "Cobrado em: MPE/SP 2024",
            "explicacao": "A justificativa técnica aqui."
        },
        # ... próxima questão ...
    ],
