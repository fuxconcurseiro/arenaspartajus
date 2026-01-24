import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import random

# -----------------------------------------------------------------------------
# 0. IMPORTAÇÃO SEGURA & SETUP
# -----------------------------------------------------------------------------
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    LIBS_INSTALLED = True
except ImportError:
    LIBS_INSTALLED = False

st.set_page_config(
    page_title="Arena SpartaJus",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 1. IDENTIDADE VISUAL (Estilo MentorSpartaJus)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    /* CORES GERAIS - IVORY (#FFFFF0) */
    .stApp { background-color: #FFFFF0; color: #333333; }
    .stMarkdown, .stText, p, label, .stDataFrame, .stExpander { color: #4A4A4A !important; }
    
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #8B4513 !important; font-family: 'Georgia', serif; text-shadow: none;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #FFDEAD; border-right: 2px solid #DEB887; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { 
        color: #5C4033 !important; 
    }

    /* INPUTS */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #FFFFFF; color: #333333; border: 1px solid #DEB887;
    }

    /* BUTTONS */
    .stButton>button {
        background-color: #FFDEAD; color: #5C4033; border: 1px solid #8B4513; 
        border-radius: 6px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #FFE4C4; color: #000000; border-color: #A0522D; transform: scale(1.02);
    }
    
    /* CARDS ESPECÍFICOS DA ARENA */
    .battle-card {
        background-color: #FFF8DC; 
        border: 2px solid #DAA520; 
        border-radius: 12px; 
        padding: 20px; 
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: center;
    }
    .battle-card.locked {
        filter: grayscale(100%);
        opacity: 0.6;
        border-color: #555;
    }
    .battle-card.victory {
        border-color: #228B22;
        background-color: #F0FFF0;
    }
    .battle-card.defeat {
        border-color: #B22222;
        background-color: #FFF0F0;
    }
    
    .stat-box {
        background-color: #FFFFFF;
        border: 1px solid #DEB887;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .stat-value { font-size: 1.5em; font-weight: bold; color: #8B4513; }
    .stat-label { font-size: 0.8em; color: #666; text-transform: uppercase; }

    /* DOCTORE CARD */
    .doctore-card {
        background-color: #FFF;
        border-left: 5px solid #8B4513;
        padding: 25px;
        border-radius: 5px;
        font-family: 'Georgia', serif;
        font-size: 1.2rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .feedback-box {
        padding: 15px; border-radius: 5px; margin-top: 15px; border: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CONFIGURAÇÃO DE DADOS
# -----------------------------------------------------------------------------
TEST_USER = "fux_concurseiro"

# Nova estrutura de dados (sem XP/Nível)
DEFAULT_USER_DATA = {
    "stats": {
        "total_questoes": 0,
        "total_acertos": 0,
        "total_erros": 0
    },
    "progresso_arena": {
        "fase_maxima_desbloqueada": 1, # Começa na fase 1
        "fases_vencidas": [] # Lista de IDs
    },
    "historico_atividades": []
}

# -----------------------------------------------------------------------------
# 3. BASE DE DADOS (OPONENTES E DOCTORE)
# -----------------------------------------------------------------------------
OPONENTS_DB = [
    {
        "id": 1,
        "nome": "Recruta da Banca",
        "descricao": "O primeiro teste. Não subestime o básico.",
        "avatar_url": "https://img.icons8.com/color/96/roman-soldier.png", # Placeholder
        "img_vitoria": "https://img.icons8.com/color/96/laurel-wreath.png",
        "img_derrota": "https://img.icons8.com/color/96/skull.png",
        "link_tec": "https://www.tecconcursos.com.br", 
        "dificuldade": "Fácil",
        "xp_reward": 100 # Mantido interno para lógica futura se quiser
    },
    {
        "id": 2,
        "nome": "Legionário da Lei Seca",
        "descricao": "A letra da lei é sua espada. Atenção aos detalhes.",
        "avatar_url": "https://img.icons8.com/color/96/centurion.png",
        "img_vitoria": "https://img.icons8.com/color/96/trophy.png",
        "img_derrota": "https://img.icons8.com/color/96/dead-body.png",
        "link_tec": "https://www.tecconcursos.com.br",
        "dificuldade": "Média",
        "xp_reward": 200
    },
    {
        "id": 3,
        "nome": "Centurião da Jurisprudência",
        "descricao": "Rápido, letal e cheio de precedentes.",
        "avatar_url": "https://img.icons8.com/color/96/spartan-helmet.png",
        "img_vitoria": "https://img.icons8.com/color/96/crown.png",
        "img_derrota": "https://img.icons8.com/color/96/grave.png",
        "link_tec": "https://www.tecconcursos.com.br",
        "dificuldade": "Difícil",
        "xp_reward": 500
    }
]

DOCTORE_DB = {
    "Direito Constitucional": [
        {
            "id": 101,
            "texto": "Segundo o STF, é inconstitucional lei estadual que determina fornecimento de dados cadastrais sem autorização judicial.",
            "gabarito": "Certo",
            "origem": "ADI 7777/DF",
            "explicacao": "Viola a cláusula de reserva de jurisdição."
        },
        {
            "id": 102,
            "texto": "Normas de eficácia limitada possuem aplicabilidade imediata e integral.",
            "gabarito": "Errado",
            "origem": "MPE/GO 2022",
            "explicacao": "Possuem aplicabilidade mediata e reduzida."
        }
    ],
    "Direito Penal": [
        {
            "id": 201,
            "texto": "Aplica-se o princípio da insignificância aos crimes contra a administração pública.",
            "gabarito": "Errado",
            "origem": "Súmula 599 STJ",
            "explicacao": "É inaplicável aos crimes contra a administração pública."
        }
    ]
}

# -----------------------------------------------------------------------------
# 4. BACKEND (GOOGLE SHEETS)
# -----------------------------------------------------------------------------
def connect_db():
    if not LIBS_INSTALLED: return None, "Libs ausentes"
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
            client = gspread.authorize(creds)
            return client.open("ArenaSpartaJus_DB").sheet1, None
        return None, "Secrets off"
    except Exception as e: return None, str(e)

def load_data():
    sheet, msg = connect_db()
    if sheet:
        try:
            cell = sheet.find(TEST_USER)
            if cell:
                data = json.loads(sheet.cell(cell.row, 2).value)
                # Migração de estrutura (se for usuário antigo)
                if "stats" not in data:
                    data = DEFAULT_USER_DATA.copy()
                return data, cell.row, "Online"
            else:
                sheet.append_row([TEST_USER, json.dumps(DEFAULT_USER_DATA)])
                return DEFAULT_USER_DATA, sheet.find(TEST_USER).row, "Online (Novo)"
        except: pass
    return DEFAULT_USER_DATA, None, "Offline"

def save_data(row_idx, data):
    sheet, _ = connect_db()
    if sheet and row_idx:
        try: sheet.update_cell(row_idx, 2, json.dumps(data))
        except: pass

# -----------------------------------------------------------------------------
# 5. APP PRINCIPAL
# -----------------------------------------------------------------------------
def main():
    if 'user_data' not in st.session_state:
        with st.spinner("Carregando Pergaminhos..."):
            d, r, s = load_data()
            st.session_state['user_data'] = d
            st.session_state['row_idx'] = r
            st.session_state['status'] = s

    user_data = st.session_state['user_data']
    stats = user_data['stats']

    # --- SIDEBAR (Estilo MentorSpartaJus) ---
    with st.sidebar:
        st.header(f"🏛️ {TEST_USER}")
        st.markdown("---")
        
        # Estatísticas Gerais (Total, Erros, Acertos)
        st.markdown("### 📊 Desempenho Global")
        
        c1, c2 = st.columns(2)
        c1.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#006400'>{stats['total_acertos']}</div><div class='stat-label'>Acertos</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#8B0000'>{stats['total_erros']}</div><div class='stat-label'>Erros</div></div>""", unsafe_allow_html=True)
        
        st.markdown(f"""<div class='stat-box'><div class='stat-value'>{stats['total_questoes']}</div><div class='stat-label'>Total de Questões</div></div>""", unsafe_allow_html=True)
        
        # Cálculo de %
        if stats['total_questoes'] > 0:
            perc = (stats['total_acertos'] / stats['total_questoes']) * 100
        else:
            perc = 0
        st.markdown(f"**Aproveitamento:** {perc:.1f}%")
        st.progress(perc / 100)
        
        st.markdown("---")
        if st.button("Sair"):
            st.session_state.clear()
            st.rerun()

    # --- MAIN CONTENT ---
    st.markdown("<h1 style='text-align: center;'>⚔️ ARENA SPARTAJUS ⚔️</h1>", unsafe_allow_html=True)

    tab_batalha, tab_doctore, tab_historico = st.tabs(["🛡️ Linha do Tempo (Desafios)", "🦉 Doctore (Treino)", "📜 Histórico"])

    # -------------------------------------------------------------------------
    # TAB 1: BATALHA (LINHA DO TEMPO)
    # -------------------------------------------------------------------------
    with tab_batalha:
        st.markdown("### 🗺️ A Jornada do Gladiador")
        
        fase_max = user_data['progresso_arena']['fase_maxima_desbloqueada']
        fases_vencidas = user_data['progresso_arena']['fases_vencidas']

        for opp in OPONENTS_DB:
            # Lógica de Estado
            is_locked = opp['id'] > fase_max
            is_completed = opp['id'] in fases_vencidas
            is_current = (opp['id'] == fase_max) and not is_completed
            
            # CSS Class
            css_class = "battle-card"
            if is_locked: css_class += " locked"
            elif is_completed: css_class += " victory"
            
            # Renderização do Cartão da Fase
            container = st.container()
            with container:
                st.markdown(f"<div class='{css_class}'>", unsafe_allow_html=True)
                
                c_img, c_info, c_action = st.columns([1, 2, 1])
                
                with c_img:
                    if is_completed:
                        st.image(opp['img_vitoria'], width=80)
                    elif is_current and 'last_result' in st.session_state and st.session_state['last_result'] == 'derrota' and st.session_state.get('last_opp_id') == opp['id']:
                         st.image(opp['img_derrota'], width=80)
                    else:
                        st.image(opp['avatar_url'], width=80)

                with c_info:
                    st.markdown(f"### {opp['nome']}")
                    st.markdown(f"*{opp['descricao']}*")
                    if is_locked:
                        st.markdown("🔒 **BLOQUEADO** (Vença o anterior)")
                    elif is_completed:
                        st.markdown("✅ **CONQUISTADO**")
                    else:
                        st.markdown(f"🔥 **Dificuldade:** {opp['dificuldade']}")

                with c_action:
                    if is_current:
                        if st.button("⚔️ BATALHAR", key=f"bat_{opp['id']}", type="primary"):
                            st.session_state['active_battle_id'] = opp['id']
                    elif is_completed:
                        st.button("Refazer", key=f"redo_{opp['id']}") # Apenas visual por enquanto

                st.markdown("</div>", unsafe_allow_html=True)

                # --- ÁREA DE BATALHA ATIVA (EXPANDIDA) ---
                if st.session_state.get('active_battle_id') == opp['id']:
                    with st.expander("⚔️ CAMPO DE BATALHA", expanded=True):
                        st.info("Sua missão foi dada. Cumpra-a e reporte o resultado.")
                        
                        # 1. Botão do Link
                        st.link_button("🔗 ABRIR CADERNO TEC CONCURSOS", opp['link_tec'], type="primary", use_container_width=True)
                        
                        st.divider()
                        
                        # 2. Formulário de Resultados
                        with st.form(f"form_bat_{opp['id']}"):
                            c_t, c_a, c_time = st.columns(3)
                            total_q = c_t.number_input("Total de Questões", min_value=1, step=1)
                            acertos_q = c_a.number_input("Questões Acertadas", min_value=0, step=1)
                            tempo_min = c_time.number_input("Tempo (minutos)", min_value=0, step=1)
                            
                            if st.form_submit_button("📜 REPORTAR RESULTADO AO MENTOR"):
                                erros_q = max(0, total_q - acertos_q)
                                perc = (acertos_q / total_q) * 100
                                
                                # Regra de Vitória (Ex: 70% de acerto para passar)
                                # Você pode customizar isso por oponente se quiser
                                VITORIA = perc >= 70 
                                
                                # Atualiza Stats
                                user_data['stats']['total_questoes'] += total_q
                                user_data['stats']['total_acertos'] += acertos_q
                                user_data['stats']['total_erros'] += erros_q
                                
                                # Atualiza Histórico
                                resultado_str = "Vitória" if VITORIA else "Derrota"
                                user_data['historico_atividades'].append({
                                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                    "tipo": "Batalha",
                                    "detalhe": f"vs {opp['nome']}",
                                    "resultado": f"{resultado_str} ({acertos_q}/{total_q})",
                                    "tempo": f"{tempo_min} min"
                                })

                                # Lógica de Progressão
                                st.session_state['last_opp_id'] = opp['id']
                                if VITORIA:
                                    st.session_state['last_result'] = 'vitoria'
                                    if opp['id'] not in user_data['progresso_arena']['fases_vencidas']:
                                        user_data['progresso_arena']['fases_vencidas'].append(opp['id'])
                                        # Desbloqueia próximo
                                        if opp['id'] == user_data['progresso_arena']['fase_maxima_desbloqueada']:
                                            user_data['progresso_arena']['fase_maxima_desbloqueada'] += 1
                                    st.success("VITÓRIA! Oponente derrotado.")
                                    st.balloons()
                                else:
                                    st.session_state['last_result'] = 'derrota'
                                    st.error(f"DERROTA. Você precisava de 70% (Fez {perc:.1f}%). Tente novamente.")

                                save_data(st.session_state['row_idx'], user_data)
                                time.sleep(2)
                                del st.session_state['active_battle_id']
                                st.rerun()

            # Conector visual (Linha vertical) entre cards
            if opp['id'] < len(OPONENTS_DB):
                st.markdown("<div style='text-align:center; color:#8B4513; font-size:20px;'>⬇</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # TAB 2: DOCTORE (TREINO + REFAZER)
    # -------------------------------------------------------------------------
    with tab_doctore:
        st.markdown("### 🦉 Treinamento Técnico")
        
        # Inicialização da Sessão Doctore
        if 'doctore_session' not in st.session_state:
            st.session_state['doctore_session'] = {
                "active": False,
                "questions": [],
                "idx": 0,
                "wrong_ids": [], # IDs das questões erradas para refazer
                "mode": "normal" # 'normal' ou 'retry'
            }
        
        ds = st.session_state['doctore_session']

        # SELEÇÃO DE NICHO (Se não ativo)
        if not ds['active']:
            nicho = st.selectbox("Escolha a Matéria:", list(DOCTORE_DB.keys()))
            c1, c2 = st.columns(2)
            
            if c1.button("Iniciar Treino Normal", type="primary", use_container_width=True):
                qs = DOCTORE_DB[nicho].copy()
                random.shuffle(qs)
                ds['questions'] = qs
                ds['idx'] = 0
                ds['active'] = True
                ds['wrong_ids'] = []
                ds['mode'] = "normal"
                st.rerun()
            
            # Botão Refazer Erradas (Lógica Mockada para demonstração ou persistência futura)
            # Para persistência real de erros entre sessões, precisaríamos salvar 'erros_pendentes' no DB
            st.caption("O modo 'Refazer' aparece automaticamente ao final se você errar algo.")

        # MODO ATIVO (QUESTÕES)
        else:
            q_list = ds['questions']
            idx = ds['idx']
            
            if idx < len(q_list):
                q = q_list[idx]
                modo_txt = "REVISÃO DE ERROS" if ds['mode'] == 'retry' else "TREINO NORMAL"
                st.markdown(f"**Modo:** {modo_txt} | Questão {idx+1}/{len(q_list)}")
                st.progress((idx)/len(q_list))

                # Cartão da Questão
                st.markdown(f"<div class='doctore-card'>{q['texto']}</div>", unsafe_allow_html=True)

                if 'doc_revealed' not in st.session_state: st.session_state['doc_revealed'] = False

                if not st.session_state['doc_revealed']:
                    c_c, c_e = st.columns(2)
                    if c_c.button("✅ CERTO", use_container_width=True):
                        st.session_state['doc_choice'] = "Certo"
                        st.session_state['doc_revealed'] = True
                        st.rerun()
                    if c_e.button("❌ ERRADO", use_container_width=True):
                        st.session_state['doc_choice'] = "Errado"
                        st.session_state['doc_revealed'] = True
                        st.rerun()
                else:
                    # Feedback
                    escolha = st.session_state['doc_choice']
                    gabarito = q['gabarito']
                    acertou = (escolha == gabarito)

                    if acertou:
                        st.success(f"Correto! Gabarito: {gabarito}")
                        user_data['stats']['total_acertos'] += 1
                    else:
                        st.error(f"Errou! Você marcou {escolha}, mas é {gabarito}.")
                        user_data['stats']['total_erros'] += 1
                        # Adiciona à lista de erros se ainda não estiver lá
                        if q not in ds['wrong_ids']:
                            ds['wrong_ids'].append(q)

                    user_data['stats']['total_questoes'] += 1
                    
                    st.markdown(f"""
                    <div class='feedback-box' style='background-color: {"#F0FFF0" if acertou else "#FFF0F0"}'>
                        <b>Justificativa:</b> {q['explicacao']}<br>
                        <small>Fonte: {q['origem']}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("Próxima ➡️"):
                        st.session_state['doc_revealed'] = False
                        ds['idx'] += 1
                        save_data(st.session_state['row_idx'], user_data)
                        st.rerun()

            else:
                # FIM DO TREINO
                st.success("Treino Finalizado!")
                st.write(f"Você errou {len(ds['wrong_ids'])} questões nesta rodada.")
                
                # Registra no histórico
                user_data['historico_atividades'].append({
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "tipo": "Doctore",
                    "detalhe": f"Sessão {ds['mode']}",
                    "resultado": f"{len(q_list) - len(ds['wrong_ids'])} acertos / {len(q_list)} total",
                    "tempo": "-"
                })
                save_data(st.session_state['row_idx'], user_data)

                c_new, c_retry = st.columns(2)
                
                if c_new.button("🏠 Voltar ao Início"):
                    ds['active'] = False
                    st.rerun()
                
                # BOTÃO MÁGICO: REFAZER ERRADAS
                if len(ds['wrong_ids']) > 0:
                    if c_retry.button("🔄 Refazer Somente as Erradas"):
                        # Reinicia sessão apenas com as erradas
                        ds['questions'] = ds['wrong_ids'].copy()
                        ds['wrong_ids'] = [] # Limpa para nova rodada
                        ds['idx'] = 0
                        ds['mode'] = "retry"
                        ds['active'] = True
                        st.rerun()

    # -------------------------------------------------------------------------
    # TAB 3: HISTÓRICO
    # -------------------------------------------------------------------------
    with tab_historico:
        st.markdown("### 📜 Pergaminho de Feitos")
        if user_data['historico_atividades']:
            # Inverte para mostrar mais recente primeiro
            hist_rev = user_data['historico_atividades'][::-1]
            df = pd.DataFrame(hist_rev)
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "data": "Data",
                    "tipo": "Atividade",
                    "detalhe": "Detalhes",
                    "resultado": "Performance",
                    "tempo": "Tempo"
                }
            )
        else:
            st.info("Ainda não há registros de glória.")

if __name__ == "__main__":
    main()
