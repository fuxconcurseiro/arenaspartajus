import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import random
import os
import base64

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
# 1. CONSTANTES E ARQUIVOS
# -----------------------------------------------------------------------------
TEST_USER = "fux_concurseiro"
LOGO_FILE = "logo_spartajus.jpg"
BG_FILE = "coliseu_bg.jpg"

# -----------------------------------------------------------------------------
# 2. FUNÇÕES VISUAIS (BASE64 E CSS)
# -----------------------------------------------------------------------------
def get_base64_of_bin_file(bin_file):
    """Lê um arquivo de imagem local e converte para base64 para uso em CSS."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# ESTILIZAÇÃO GERAL (Mantendo a identidade do MentorSpartaJus)
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
    
    /* CARDS DA ARENA */
    .battle-card {
        background-color: #FFF8DC; 
        border: 2px solid #DAA520; 
        border-radius: 12px; 
        padding: 20px; 
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: center;
    }
    .battle-card.locked { filter: grayscale(100%); opacity: 0.6; border-color: #555; }
    .battle-card.victory { border-color: #228B22; background-color: #F0FFF0; }
    .battle-card.defeat { border-color: #B22222; background-color: #FFF0F0; }
    
    /* ESTATÍSTICAS SIDEBAR */
    .stat-box {
        background-color: #FFFFFF; border: 1px solid #DEB887; border-radius: 8px;
        padding: 10px; text-align: center; margin-bottom: 10px;
    }
    .stat-value { font-size: 1.5em; font-weight: bold; color: #8B4513; }
    .stat-label { font-size: 0.8em; color: #666; text-transform: uppercase; }

    /* DOCTORE CARD */
    .doctore-card {
        background-color: #FFF; border-left: 5px solid #8B4513; padding: 25px;
        border-radius: 5px; font-family: 'Georgia', serif; font-size: 1.2rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .feedback-box {
        padding: 15px; border-radius: 5px; margin-top: 15px; border: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. CONFIGURAÇÃO DE DADOS
# -----------------------------------------------------------------------------
DEFAULT_USER_DATA = {
    "stats": {
        "total_questoes": 0,
        "total_acertos": 0,
        "total_erros": 0
    },
    "progresso_arena": {
        "fase_maxima_desbloqueada": 1, 
        "fases_vencidas": [] 
    },
    "historico_atividades": []
}

# -----------------------------------------------------------------------------
# 4. BASE DE DADOS (MOCK)
# -----------------------------------------------------------------------------
OPONENTS_DB = [
    {
        "id": 1,
        "nome": "Recruta da Banca",
        "descricao": "O primeiro teste. Não subestime o básico.",
        "avatar_url": "https://img.icons8.com/color/96/roman-soldier.png",
        "img_vitoria": "https://img.icons8.com/color/96/laurel-wreath.png",
        "img_derrota": "https://img.icons8.com/color/96/skull.png",
        "link_tec": "https://www.tecconcursos.com.br", 
        "dificuldade": "Fácil"
    },
    {
        "id": 2,
        "nome": "Legionário da Lei Seca",
        "descricao": "A letra da lei é sua espada. Atenção aos detalhes.",
        "avatar_url": "https://img.icons8.com/color/96/centurion.png",
        "img_vitoria": "https://img.icons8.com/color/96/trophy.png",
        "img_derrota": "https://img.icons8.com/color/96/dead-body.png",
        "link_tec": "https://www.tecconcursos.com.br",
        "dificuldade": "Média"
    },
    {
        "id": 3,
        "nome": "Centurião da Jurisprudência",
        "descricao": "Rápido, letal e cheio de precedentes.",
        "avatar_url": "https://img.icons8.com/color/96/spartan-helmet.png",
        "img_vitoria": "https://img.icons8.com/color/96/crown.png",
        "img_derrota": "https://img.icons8.com/color/96/grave.png",
        "link_tec": "https://www.tecconcursos.com.br",
        "dificuldade": "Difícil"
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
# 5. CONEXÃO GOOGLE SHEETS
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
                if "stats" not in data: data = DEFAULT_USER_DATA.copy()
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
# 6. APP PRINCIPAL
# -----------------------------------------------------------------------------
def main():
    if 'user_data' not in st.session_state:
        with st.spinner("Preparando a Arena..."):
            d, r, s = load_data()
            st.session_state['user_data'] = d
            st.session_state['row_idx'] = r
            st.session_state['status'] = s

    user_data = st.session_state['user_data']
    stats = user_data['stats']

    # --- SIDEBAR (LOGO + STATS) ---
    with st.sidebar:
        # LOGO DA SPARTAJUS
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_column_width=True)
        else:
            st.header(f"🏛️ {TEST_USER}")
        
        st.markdown("---")
        
        st.markdown("### 📊 Desempenho Global")
        c1, c2 = st.columns(2)
        c1.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#006400'>{stats['total_acertos']}</div><div class='stat-label'>Acertos</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#8B0000'>{stats['total_erros']}</div><div class='stat-label'>Erros</div></div>""", unsafe_allow_html=True)
        st.markdown(f"""<div class='stat-box'><div class='stat-value'>{stats['total_questoes']}</div><div class='stat-label'>Total de Questões</div></div>""", unsafe_allow_html=True)
        
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

    # --- HERO HEADER (COLISEU BACKGROUND) ---
    # Verifica se a imagem existe para criar o CSS
    bg_css = ""
    if os.path.exists(BG_FILE):
        img_b64 = get_base64_of_bin_file(BG_FILE)
        bg_css = f"""
        background-image: linear-gradient(rgba(255, 255, 240, 0.4), rgba(255, 255, 240, 0.9)), url("data:image/jpg;base64,{img_b64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        """
    else:
        # Fallback sem imagem (apenas cor)
        bg_css = "background-color: #FFF8DC;"

    st.markdown(f"""
    <style>
    .hero-container {{
        {bg_css}
        padding: 80px 20px;
        text-align: center;
        border-bottom: 4px solid #DAA520;
        margin-bottom: 30px;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
    .hero-title {{
        font-family: 'Helvetica Neue', sans-serif;
        color: #8B4513;
        font-size: 3.5rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 5px;
        text-shadow: 2px 2px 0px #FFF, 4px 4px 0px rgba(0,0,0,0.2);
        margin: 0;
    }}
    .hero-subtitle {{
        font-family: 'Georgia', serif;
        color: #5C4033;
        font-size: 1.2rem;
        font-style: italic;
        margin-top: 10px;
    }}
    </style>
    <div class="hero-container">
        <h1 class="hero-title">Arena SpartaJus</h1>
        <div class="hero-subtitle">"Onde a preparação encontra a glória"</div>
    </div>
    """, unsafe_allow_html=True)

    # --- TABS E CONTEÚDO ---
    tab_batalha, tab_doctore, tab_historico = st.tabs(["🛡️ Linha do Tempo (Desafios)", "🦉 Doctore (Treino)", "📜 Histórico"])

    # -------------------------------------------------------------------------
    # TAB 1: BATALHA
    # -------------------------------------------------------------------------
    with tab_batalha:
        st.markdown("### 🗺️ A Jornada do Gladiador")
        fase_max = user_data['progresso_arena']['fase_maxima_desbloqueada']
        fases_vencidas = user_data['progresso_arena']['fases_vencidas']

        for opp in OPONENTS_DB:
            is_locked = opp['id'] > fase_max
            is_completed = opp['id'] in fases_vencidas
            is_current = (opp['id'] == fase_max) and not is_completed
            
            css_class = "battle-card"
            if is_locked: css_class += " locked"
            elif is_completed: css_class += " victory"
            
            st.markdown(f"<div class='{css_class}'>", unsafe_allow_html=True)
            c_img, c_info, c_action = st.columns([1, 2, 1])
            with c_img:
                if is_completed: st.image(opp['img_vitoria'], width=80)
                elif is_current and st.session_state.get('last_result') == 'derrota' and st.session_state.get('last_opp_id') == opp['id']:
                     st.image(opp['img_derrota'], width=80)
                else: st.image(opp['avatar_url'], width=80)

            with c_info:
                st.markdown(f"### {opp['nome']}")
                st.markdown(f"*{opp['descricao']}*")
                if is_locked: st.markdown("🔒 **BLOQUEADO**")
                elif is_completed: st.markdown("✅ **CONQUISTADO**")
                else: st.markdown(f"🔥 **Dificuldade:** {opp['dificuldade']}")

            with c_action:
                if is_current:
                    if st.button("⚔️ BATALHAR", key=f"bat_{opp['id']}", type="primary"):
                        st.session_state['active_battle_id'] = opp['id']
                elif is_completed:
                    st.button("Refazer", key=f"redo_{opp['id']}")
            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.get('active_battle_id') == opp['id']:
                with st.expander("⚔️ CAMPO DE BATALHA", expanded=True):
                    st.info("Missão ativa. Execute e reporte.")
                    st.link_button("🔗 ABRIR CADERNO TEC", opp['link_tec'], type="primary", use_container_width=True)
                    st.divider()
                    with st.form(f"form_bat_{opp['id']}"):
                        c_t, c_a, c_time = st.columns(3)
                        total_q = c_t.number_input("Total", min_value=1, step=1)
                        acertos_q = c_a.number_input("Acertos", min_value=0, step=1)
                        tempo_min = c_time.number_input("Tempo (min)", min_value=0, step=1)
                        
                        if st.form_submit_button("📜 REPORTAR"):
                            erros_q = max(0, total_q - acertos_q)
                            perc = (acertos_q / total_q) * 100
                            VITORIA = perc >= 70
                            
                            user_data['stats']['total_questoes'] += total_q
                            user_data['stats']['total_acertos'] += acertos_q
                            user_data['stats']['total_erros'] += erros_q
                            user_data['historico_atividades'].append({
                                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "tipo": "Batalha",
                                "detalhe": f"vs {opp['nome']}",
                                "resultado": f"{'Vitória' if VITORIA else 'Derrota'} ({acertos_q}/{total_q})",
                                "tempo": f"{tempo_min} min"
                            })
                            
                            st.session_state['last_opp_id'] = opp['id']
                            if VITORIA:
                                st.session_state['last_result'] = 'vitoria'
                                if opp['id'] not in fases_vencidas:
                                    user_data['progresso_arena']['fases_vencidas'].append(opp['id'])
                                    if opp['id'] == user_data['progresso_arena']['fase_maxima_desbloqueada']:
                                        user_data['progresso_arena']['fase_maxima_desbloqueada'] += 1
                                st.success("VITÓRIA!")
                                st.balloons()
                            else:
                                st.session_state['last_result'] = 'derrota'
                                st.error(f"DERROTA ({perc:.1f}%). Exige-se 70%.")
                            
                            save_data(st.session_state['row_idx'], user_data)
                            time.sleep(2)
                            del st.session_state['active_battle_id']
                            st.rerun()

            if opp['id'] < len(OPONENTS_DB):
                st.markdown("<div style='text-align:center; color:#8B4513; font-size:20px;'>⬇</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # TAB 2: DOCTORE
    # -------------------------------------------------------------------------
    with tab_doctore:
        st.markdown("### 🦉 Treinamento Técnico")
        if 'doctore_session' not in st.session_state:
            st.session_state['doctore_session'] = {"active": False, "questions": [], "idx": 0, "wrong_ids": [], "mode": "normal"}
        ds = st.session_state['doctore_session']

        if not ds['active']:
            nicho = st.selectbox("Escolha a Matéria:", list(DOCTORE_DB.keys()))
            c1, c2 = st.columns(2)
            if c1.button("Iniciar Treino", type="primary", use_container_width=True):
                qs = DOCTORE_DB[nicho].copy()
                random.shuffle(qs)
                ds.update({"questions": qs, "idx": 0, "active": True, "wrong_ids": [], "mode": "normal"})
                st.rerun()
        else:
            q_list = ds['questions']
            idx = ds['idx']
            if idx < len(q_list):
                q = q_list[idx]
                st.markdown(f"**Modo:** {'REVISÃO' if ds['mode']=='retry' else 'TREINO'} | Q {idx+1}/{len(q_list)}")
                st.progress((idx)/len(q_list))
                st.markdown(f"<div class='doctore-card'>{q['texto']}</div>", unsafe_allow_html=True)
                
                if 'doc_revealed' not in st.session_state: st.session_state['doc_revealed'] = False
                if not st.session_state['doc_revealed']:
                    c_c, c_e = st.columns(2)
                    if c_c.button("✅ CERTO", use_container_width=True):
                        st.session_state.update({"doc_choice": "Certo", "doc_revealed": True})
                        st.rerun()
                    if c_e.button("❌ ERRADO", use_container_width=True):
                        st.session_state.update({"doc_choice": "Errado", "doc_revealed": True})
                        st.rerun()
                else:
                    acertou = (st.session_state['doc_choice'] == q['gabarito'])
                    if acertou: 
                        st.success(f"Correto! {q['gabarito']}")
                        user_data['stats']['total_acertos'] += 1
                    else: 
                        st.error(f"Errou! É {q['gabarito']}")
                        user_data['stats']['total_erros'] += 1
                        if q not in ds['wrong_ids']: ds['wrong_ids'].append(q)
                    user_data['stats']['total_questoes'] += 1
                    
                    st.markdown(f"<div class='feedback-box'><b>Justificativa:</b> {q['explicacao']}</div>", unsafe_allow_html=True)
                    if st.button("Próxima ➡️"):
                        st.session_state['doc_revealed'] = False
                        ds['idx'] += 1
                        save_data(st.session_state['row_idx'], user_data)
                        st.rerun()
            else:
                st.success("Treino Finalizado!")
                st.write(f"Erros: {len(ds['wrong_ids'])}")
                user_data['historico_atividades'].append({
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "tipo": "Doctore",
                    "detalhe": f"Sessão {ds['mode']}",
                    "resultado": f"{len(q_list)-len(ds['wrong_ids'])}/{len(q_list)} acertos",
                    "tempo": "-"
                })
                save_data(st.session_state['row_idx'], user_data)
                
                c1, c2 = st.columns(2)
                if c1.button("🏠 Início"):
                    ds['active'] = False
                    st.rerun()
                if len(ds['wrong_ids']) > 0 and c2.button("🔄 Refazer Erradas"):
                    ds.update({"questions": ds['wrong_ids'].copy(), "wrong_ids": [], "idx": 0, "mode": "retry"})
                    st.rerun()

    # -------------------------------------------------------------------------
    # TAB 3: HISTÓRICO
    # -------------------------------------------------------------------------
    with tab_historico:
        st.markdown("### 📜 Pergaminho de Feitos")
        if user_data['historico_atividades']:
            st.dataframe(pd.DataFrame(user_data['historico_atividades'][::-1]), use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não há registros.")

if __name__ == "__main__":
    main()
