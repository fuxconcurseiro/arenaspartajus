import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import random
import os
import base64
import re

# -----------------------------------------------------------------------------
# 0. IMPORTAÇÃO SEGURA
# -----------------------------------------------------------------------------
try:
    import gspread
    from google.oauth2.service_account import Credentials
    LIBS_INSTALLED = True
    IMPORT_ERROR = ""
except ImportError as e:
    LIBS_INSTALLED = False
    IMPORT_ERROR = str(e)

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
SHEET_NAME = "SpartaJus_DB"
QUESTOES_FILE = "questoes.json"

# Arquivos de Imagem
HERO_IMG_FILE = "Arena_Spartajus_Logo_3.jpg"
USER_AVATAR_FILE = "fux_concurseiro.png"
PREPARE_SE_FILE = "prepare-se.jpg"

# -----------------------------------------------------------------------------
# 2. FUNÇÕES VISUAIS & UTILITÁRIOS
# -----------------------------------------------------------------------------
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

def render_centered_image(img_path, width=200):
    """Renderiza uma imagem centralizada usando HTML/CSS."""
    src = img_path
    if os.path.exists(img_path):
        ext = img_path.split('.')[-1]
        b64 = get_base64_of_bin_file(img_path)
        if b64:
            src = f"data:image/{ext};base64,{b64}"
    
    st.markdown(f"""
    <div style="display: flex; justify-content: center; margin-top: 15px; margin-bottom: 15px;">
        <img src="{src}" style="width: {width}px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
    </div>
    """, unsafe_allow_html=True)

def calculate_daily_stats(history, target_date):
    """Filtra o histórico pela data selecionada e soma acertos/erros."""
    stats = {"total": 0, "acertos": 0, "erros": 0}
    target_str = target_date.strftime("%d/%m/%Y")
    for activity in history:
        try:
            act_date_str = activity.get('data', '').split(' ')[0]
            if act_date_str == target_str:
                result_str = activity.get('resultado', '')
                match = re.search(r'(\d+)/(\d+)', result_str)
                if match:
                    acertos = int(match.group(1))
                    total = int(match.group(2))
                    erros = max(0, total - acertos)
                    stats['total'] += total
                    stats['acertos'] += acertos
                    stats['erros'] += erros
        except:
            continue
    return stats

# ESTILIZAÇÃO GERAL (Clean Design - Leitura Otimizada)
st.markdown("""
    <style>
    /* 1. RESET E FUNDO GLOBAL */
    .stApp {
        background-color: #F5F4EF;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* 2. HIERARQUIA TIPOGRÁFICA */
    
    /* Títulos e Negritos: Vermelho Espartano (#9E0000) */
    h1, h2, h3, h4, h5, h6, strong, b {
        color: #9E0000 !important;
    }
    
    /* Corpo do Texto: Chumbo/Grafite (#2e2c2b) */
    p, label, li, span, .stMarkdown, .stText, div[data-testid="stMarkdownContainer"] p {
        color: #2e2c2b !important;
    }
    
    /* Legendas */
    .stcaption {
        color: #2e2c2b !important;
        opacity: 0.8;
    }

    /* 3. SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #E3DFD3;
        border-right: 1px solid #dcd8cc;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #9E0000 !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #2e2c2b !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #9E0000;
        opacity: 0.2;
    }

    /* 4. BOTÕES */
    .stButton > button {
        background-color: #E3DFD3;
        color: #9E0000;
        border: 1px solid #E3DFD3;
        border-radius: 6px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        padding: 0.6rem 1.2rem;
    }
    
    .stButton > button:hover {
        background-color: #E3DFD3 !important;
        color: #9E0000 !important;
        border: 1px solid #9E0000 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(158, 0, 0, 0.1);
    }
    
    .stButton > button:active {
        background-color: #dcd8cc;
        transform: translateY(0px);
    }

    /* 5. INPUTS */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stDateInput > div > div > input {
        background-color: #FFFFFF;
        color: #2e2c2b;
        border: 1px solid #E3DFD3;
        border-radius: 4px;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        border-color: #9E0000;
        box-shadow: 0 0 0 1px #9E0000;
    }

    /* 6. CARDS GERAIS */
    .battle-card, .master-card {
        background-color: #FFFFFF;
        border: 1px solid #E3DFD3;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .master-card:hover {
        border-color: #9E0000;
        transform: translateY(-3px);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.05);
    }
    
    .battle-card.locked { opacity: 0.6; filter: grayscale(100%); background-color: #F0F0F0; }
    .battle-card.victory { border-left: 4px solid #2E8B57; background-color: #FAFCFA; }
    .battle-card.defeat { border-left: 4px solid #B22222; background-color: #FCFAFA; }

    /* 7. DOCTORE CARD (Ergonomia de Leitura) */
    .doctore-card {
        background-color: #FFFFFF;
        border: 1px solid #E3DFD3;
        border-left: 5px solid #9E0000;
        border-radius: 6px;
        padding: 40px; 
        margin-bottom: 30px;
        
        display: block;
        width: 50% !important;           
        min-width: 600px !important;     
        max-width: 95vw !important;      
        margin-left: auto !important;    
        margin-right: auto !important;   
        
        text-align: left !important;
        font-size: 22px !important;      
        font-weight: 500;
        line-height: 1.6;
        color: #2e2c2b !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }

    /* 8. ESTATÍSTICAS */
    .stat-box {
        background-color: #FFFFFF;
        border: 1px solid #E3DFD3;
        border-radius: 6px;
        padding: 12px;
        text-align: center;
        margin-bottom: 10px;
    }
    .stat-value {
        font-size: 1.5em;
        font-weight: 800;
        color: #9E0000;
    }
    .stat-label {
        font-size: 0.8em;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stat-header {
        font-size: 1.1em;
        font-weight: bold;
        color: #9E0000;
        margin-top: 20px;
        margin-bottom: 15px;
        border-bottom: 1px solid #E3DFD3;
        padding-bottom: 5px;
    }

    /* 9. EXTRAS */
    .feedback-box {
        background-color: #Fdfdfd;
        padding: 20px;
        border-radius: 4px;
        margin-top: 20px;
        border: 1px solid #E3DFD3;
        text-align: left;
        font-size: 16px;
        color: #2e2c2b !important;
    }
    
    .stTabs [data-baseweb="tab-list"] { border-bottom-color: #E3DFD3; }
    .stTabs [data-baseweb="tab"] { color: #555; }
    .stTabs [aria-selected="true"] { color: #9E0000; border-bottom-color: #9E0000; font-weight: bold;}
    
    .full-width-hero {
        background-color: #F5F4EF !important;
        border-bottom: 1px solid #E3DFD3 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. CONFIGURAÇÃO DE DADOS (MERGE SEGURO)
# -----------------------------------------------------------------------------
DEFAULT_ARENA_DATA = {
    "stats": {"total_questoes": 0, "total_acertos": 0, "total_erros": 0},
    "progresso_arena": {"fase_maxima_desbloqueada": 1, "fases_vencidas": []},
    "historico_atividades": []
}

# --- DADOS ORIGINAIS PARA BACKUP (FALLBACK) ---
DEFAULT_DOCTORE_DB = {
    "praetorium": {
        "nome": "Praetorium Legislativus", "descricao": "O Guardião das Leis e do Processo Legislativo.", "imagem": "praetorium.jpg", 
        "materias": {
            "Direito Constitucional": {
                "Organização Político-Administrativa": [
                     {"id": 21, "texto": "Nos termos da Constituição da República, a câmara de vereadores não é competente para apreciar matéria eleitoral nem matéria criminal.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE (CESPE) / 2002 / AL (CAM DEP)"}
                ]
            }
        }
    }
}

# -----------------------------------------------------------------------------
# 4. BASE DE DADOS (OPONENTES) - LISTA FINAL E BALANCEADA
# -----------------------------------------------------------------------------
def get_avatar_image(local_file, fallback_url):
    if os.path.exists(local_file): return local_file
    return fallback_url

OPONENTS_DB = [
    {
        "id": 1, "nome": "O Velho Leão", "descricao": "Suas garras estão gastas, mas sua experiência é mortal.",
        "avatar_url": get_avatar_image("1_leao_velho.png", "https://img.icons8.com/color/96/lion.png"),
        "img_vitoria": get_avatar_image("vitoria_leao_velho.jpg", "https://img.icons8.com/color/96/laurel-wreath.png"),
        "img_derrota": get_avatar_image("derrota_leao_velho.jpg", "https://img.icons8.com/color/96/skull.png"),
        "link_tec": "https://www.tecconcursos.com.br/caderno/Q5r1Ng", 
        "dificuldade": "Desafio Inicial", "max_tempo": 60, "max_erros": 7 
    },
    {
        "id": 2, "nome": "Beuzebu", "descricao": "A fúria incontrolável. Supere a pressão ou seja chifrado.",
        "avatar_url": get_avatar_image("touro.jpg", "https://img.icons8.com/color/96/bull.png"),
        "img_vitoria": get_avatar_image("vitoria_touro.jpg", "https://img.icons8.com/color/96/trophy.png"),
        "img_derrota": get_avatar_image("derrota_touro.jpg", "https://img.icons8.com/color/96/dead-body.png"),
        "link_tec": "https://www.tecconcursos.com.br/caderno/Q5rIKB",
        "dificuldade": "Desafio Inicial", "max_tempo": 40, "max_erros": 6 
    },
    {
        "id": 3, "nome": "Leproso", "descricao": "A doença que corrói a alma. Vença ou seja consumido.",
        "avatar_url": get_avatar_image("leproso.jpg", "https://img.icons8.com/color/96/zombie.png"),
        "img_vitoria": get_avatar_image("vitoria_leproso.jpg", "https://img.icons8.com/color/96/clean-hands.png"),
        "img_derrota": get_avatar_image("derrota_leproso.jpg", "https://img.icons8.com/color/96/hospital.png"),
        "link_tec": "https://www.tecconcursos.com.br/caderno/Q5rIWI",
        "dificuldade": "Desafio Inicial", "max_tempo": 40, "max_erros": 6
    },
    {
        "id": 4, "nome": "Autanax, o domador canino", "descricao": "Ele comanda as feras com um olhar gelado. Quebre seu controle.",
        "avatar_url": get_avatar_image("autanax.png", "https://img.icons8.com/color/96/wolf.png"),
        "img_vitoria": get_avatar_image("vitoria_autanax.png", "https://img.icons8.com/color/96/medal.png"),
        "img_derrota": get_avatar_image("derrota_autanax.png", "https://img.icons8.com/color/96/sad.png"),
        "link_tec": "", 
        "dificuldade": "Intermediário", "max_tempo": 30, "max_erros": 5 
    },
    {
        "id": 5, "nome": "Tanara, a infiel", "descricao": "Sua lealdade é comprada com sangue. Não confie em ninguém.",
        "avatar_url": get_avatar_image("tanara.png", "https://img.icons8.com/color/96/witch.png"),
        "img_vitoria": get_avatar_image("vitoria_tanara.png", "https://img.icons8.com/color/96/crown.png"),
        "img_derrota": get_avatar_image("derrota_tanara.png", "https://img.icons8.com/color/96/ghost.png"),
        "link_tec": "", 
        "dificuldade": "Difícil", "max_tempo": 30, "max_erros": 5 
    },
    {
        "id": 6, "nome": "Afezio, o renegado", "descricao": "Expulso do panteão, ele busca vingança contra os justos.",
        "avatar_url": get_avatar_image("afezio.png", "https://img.icons8.com/color/96/demon.png"),
        "img_vitoria": get_avatar_image("vitoria_afezio.png", "https://img.icons8.com/color/96/throne.png"),
        "img_derrota": get_avatar_image("derrota_afezio.png", "https://img.icons8.com/color/96/fire.png"),
        "link_tec": "", 
        "dificuldade": "Pesadelo", "max_tempo": 30, "max_erros": 5 
    }
]

# -----------------------------------------------------------------------------
# 5. BASE DE DADOS HIERÁRQUICA (DOCTORE) - CARGA HÍBRIDA
# -----------------------------------------------------------------------------
@st.cache_data
def load_doctore_data():
    """Tenta carregar JSON. Se falhar, usa o backup hardcoded (DEFAULT_DOCTORE_DB)."""
    if not os.path.exists(QUESTOES_FILE):
        return DEFAULT_DOCTORE_DB 
    
    try:
        with open(QUESTOES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return DEFAULT_DOCTORE_DB

DOCTORE_DB = load_doctore_data()

# -----------------------------------------------------------------------------
# 6. CONEXÃO GOOGLE SHEETS (BLINDADA)
# -----------------------------------------------------------------------------
def connect_db():
    if not LIBS_INSTALLED:
        return None, f"Erro Crítico: Bibliotecas não instaladas. Detalhe: {IMPORT_ERROR}"

    if "gcp_service_account" not in st.secrets:
        return None, "Erro: 'gcp_service_account' não encontrado em st.secrets."

    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(credentials)
        sheet = client.open(SHEET_NAME).sheet1
        return sheet, None

    except Exception as e:
        return None, f"Erro de Conexão: {str(e)}"

def load_data():
    sheet, error_msg = connect_db()
    
    if not sheet:
        data = DEFAULT_ARENA_DATA.copy()
        return data, None, f"🟠 Offline ({error_msg})"

    try:
        cell = sheet.find(TEST_USER)
        if cell:
            raw_data = sheet.cell(cell.row, 2).value
            try:
                full_user_data = json.loads(raw_data)
            except:
                full_user_data = {} 
            
            if "arena_v1_data" not in full_user_data:
                full_user_data["arena_v1_data"] = DEFAULT_ARENA_DATA.copy()

            return full_user_data, cell.row, "🟢 Online (Sincronizado)"
            
        else:
            return DEFAULT_ARENA_DATA.copy(), None, "🟠 Offline (Usuário não encontrado)"
            
    except Exception as e:
        return DEFAULT_ARENA_DATA.copy(), None, f"🔴 Erro Leitura: {str(e)}"

def save_data(row_idx, full_data):
    sheet, _ = connect_db()
    if sheet and row_idx:
        try:
            sheet.update_cell(row_idx, 2, json.dumps(full_data))
        except Exception:
            pass

# -----------------------------------------------------------------------------
# 7. APP PRINCIPAL
# -----------------------------------------------------------------------------
def main():
    if 'full_data' not in st.session_state:
        with st.spinner("Sincronizando com o Templo..."):
            d, r, s = load_data()
            st.session_state['full_data'] = d
            st.session_state['row_idx'] = r
            st.session_state['status'] = s

    full_data = st.session_state['full_data']
    
    arena_data = full_data.get('arena_v1_data', DEFAULT_ARENA_DATA.copy())
    
    if not isinstance(arena_data, dict): arena_data = DEFAULT_ARENA_DATA.copy()
    if "stats" not in arena_data: arena_data["stats"] = DEFAULT_ARENA_DATA["stats"].copy()
    if "progresso_arena" not in arena_data: arena_data["progresso_arena"] = DEFAULT_ARENA_DATA["progresso_arena"].copy()
    if "historico_atividades" not in arena_data: arena_data["historico_atividades"] = DEFAULT_ARENA_DATA["historico_atividades"].copy()

    full_data['arena_v1_data'] = arena_data
    stats = arena_data['stats']
    hist = arena_data['historico_atividades']

    # --- SIDEBAR ---
    with st.sidebar:
        if os.path.exists(USER_AVATAR_FILE):
            st.image(USER_AVATAR_FILE, caption=TEST_USER, use_container_width=True)
        else:
            st.header(f"🏛️ {TEST_USER}")
            st.warning("Avatar não encontrado")
        
        if "Online" in st.session_state['status']:
            st.success(st.session_state['status'])
        else:
            st.error(st.session_state['status'])

        st.markdown("<div class='stat-header'>📊 Desempenho Global</div>", unsafe_allow_html=True)
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

        st.markdown("<div class='stat-header'>📅 Desempenho Diário</div>", unsafe_allow_html=True)
        selected_date = st.date_input("Data:", datetime.now(), format="DD/MM/YYYY")
        daily_stats = calculate_daily_stats(hist, selected_date)
        
        d1, d2 = st.columns(2)
        d1.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#006400'>{daily_stats['acertos']}</div><div class='stat-label'>Acertos</div></div>""", unsafe_allow_html=True)
        d2.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#8B0000'>{daily_stats['erros']}</div><div class='stat-label'>Erros</div></div>""", unsafe_allow_html=True)
        st.markdown(f"""<div class='stat-box'><div class='stat-value'>{daily_stats['total']}</div><div class='stat-label'>Total do Dia</div></div>""", unsafe_allow_html=True)
        
        if daily_stats['total'] > 0:
            d_perc = (daily_stats['acertos'] / daily_stats['total']) * 100
        else:
            d_perc = 0.0
        st.markdown(f"**Eficiência:** {d_perc:.1f}%")
        st.progress(d_perc / 100)
        
        st.markdown("---")
        if st.button("Sair"):
            st.session_state.clear()
            st.rerun()

    # --- HERO HEADER ---
    if os.path.exists(HERO_IMG_FILE):
        img_b64 = get_base64_of_bin_file(HERO_IMG_FILE)
        st.markdown(f"""
        <style>
        .full-width-hero {{
            position: relative;
            width: 100vw;
            left: 50%;
            right: 50%;
            margin-left: -50vw;
            margin-right: -50vw;
            margin-bottom: 20px;
            overflow: hidden;
            background-color: #FFF8DC;
            height: 250px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-bottom: 4px solid #DAA520;
        }}
        .full-width-hero img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            object-position: center;
            display: block;
        }}
        </style>
        <div class="full-width-hero">
            <img src="data:image/jpg;base64,{img_b64}" alt="Arena SpartaJus">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 40px; background-color: #FFF8DC; border-bottom: 4px solid #DAA520; margin-bottom: 30px;">
            <h1 style="color: #8B4513; font-family: 'Helvetica Neue', sans-serif;">ARENA SPARTAJUS</h1>
            <p style="color: #5C4033;">(Imagem 'Arena_Spartajus_Logo_3.jpg' não encontrada)</p>
        </div>
        """, unsafe_allow_html=True)

    # --- TABS ---
    tab_batalha, tab_doctore, tab_historico = st.tabs(["Combates no Coliseum", "🦉 Doctore (treinos no Ludus)", "📜 Histórico"])

    # -------------------------------------------------------------------------
    # TAB 1: BATALHA (PAGINAÇÃO + LÓGICA DE BLOQUEIO)
    # -------------------------------------------------------------------------
    with tab_batalha:
        st.markdown("### 🗺️ A Jornada do Gladiador")
        fase_max = arena_data['progresso_arena']['fase_maxima_desbloqueada']
        fases_vencidas = arena_data['progresso_arena']['fases_vencidas']

        # Paginação
        ITEMS_PER_PAGE = 3
        if 'coliseum_page' not in st.session_state:
            st.session_state['coliseum_page'] = 0

        total_pages = (len(OPONENTS_DB) - 1) // ITEMS_PER_PAGE + 1
        
        # Validação do índice da página
        current_page = st.session_state['coliseum_page']
        if current_page >= total_pages:
             current_page = total_pages - 1
             st.session_state['coliseum_page'] = current_page
        if current_page < 0:
             current_page = 0
             st.session_state['coliseum_page'] = current_page

        start_idx = current_page * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_opponents = OPONENTS_DB[start_idx:end_idx]

        st.markdown(f"*Página {current_page + 1} de {total_pages}*")

        for opp in page_opponents:
            is_locked = opp['id'] > fase_max
            is_completed = opp['id'] in fases_vencidas
            is_current = (opp['id'] == fase_max) and not is_completed
            
            # CSS: Aplica classe .locked para estilo cinza/transparente
            css_class = "battle-card"
            if is_locked: css_class += " locked"
            elif is_completed: css_class += " victory"
            
            st.markdown(f"<div class='{css_class}'>", unsafe_allow_html=True)
            c_img, c_info, c_action = st.columns([1, 2, 1])
            with c_img:
                render_centered_image(opp['avatar_url'], width=200)
            
            with c_info:
                st.markdown(f"### {opp['nome']}")
                st.markdown(f"*{opp['descricao']}*")
                
                # Lógica de Exibição de Info
                if is_locked:
                    st.markdown("### 🔒 BLOQUEADO")
                else:
                    if is_completed: st.markdown("✅ **CONQUISTADO**")
                    st.markdown(f"🔥 **Dificuldade:** {opp['dificuldade']}")
                    st.caption(f"Tempo Máx: {opp['max_tempo']} min | Limite de Erros: {opp['max_erros']}")

            with c_action:
                # Botões de Ação
                if not is_locked:
                    if is_current:
                        if st.button("⚔️ BATALHAR", key=f"bat_{opp['id']}", type="primary"):
                            st.session_state['active_battle_id'] = opp['id']
                    elif is_completed:
                        st.button("Refazer", key=f"redo_{opp['id']}")
            
            # Imagem de Status (V/D) - Apenas se não estiver bloqueado ou se já tiver interagido
            status_img_path = None
            if is_completed: status_img_path = opp['img_vitoria']
            elif is_current and st.session_state.get('last_result') == 'derrota' and st.session_state.get('last_opp_id') == opp['id']: status_img_path = opp['img_derrota']
            elif not is_locked: 
                if os.path.exists(PREPARE_SE_FILE): status_img_path = PREPARE_SE_FILE
                else: status_img_path = "https://img.icons8.com/color/96/shield.png"
            
            if status_img_path:
                render_centered_image(status_img_path, width=400)

            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.get('active_battle_id') == opp['id']:
                with st.expander("⚔️ CAMPO DE BATALHA", expanded=True):
                    st.info(f"Derrote {opp['nome']}. Você deve terminar em até {opp['max_tempo']} minutos e errar no máximo {opp['max_erros']} questões.")
                    if opp['link_tec']:
                        st.link_button("🔗 ABRIR CADERNO TEC CONCURSOS", opp['link_tec'], type="primary", use_container_width=True)
                    st.divider()
                    
                    with st.form(f"form_bat_{opp['id']}"):
                        c_t, c_a, c_time = st.columns(3)
                        total_q = c_t.number_input("Total de Questões Realizadas", min_value=1, step=1)
                        acertos_q = c_a.number_input("Questões Acertadas", min_value=0, step=1)
                        tempo_min = c_time.number_input("Tempo Gasto (minutos)", min_value=0, step=1)
                        
                        if st.form_submit_button("📜 REPORTAR RESULTADO"):
                            erros_q = max(0, total_q - acertos_q)
                            limit_errors = opp.get('max_erros', 5)
                            limit_time = opp.get('max_tempo', 60)
                            
                            passou_erros = erros_q <= limit_errors
                            passou_tempo = tempo_min <= limit_time
                            
                            VITORIA = passou_erros and passou_tempo
                            
                            stats['total_questoes'] += total_q
                            stats['total_acertos'] += acertos_q
                            stats['total_erros'] += erros_q
                            
                            hist.append({
                                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "tipo": "Batalha",
                                "detalhe": f"vs {opp['nome']}",
                                "resultado": f"{'Vitória' if VITORIA else 'Derrota'} ({acertos_q}/{total_q})",
                                "tempo": f"{tempo_min} min"
                            })
                            
                            st.session_state['last_opp_id'] = opp['id']
                            if VITORIA:
                                st.session_state['last_result'] = 'vitoria'
                                if opp['id'] not in arena_data['progresso_arena']['fases_vencidas']:
                                    arena_data['progresso_arena']['fases_vencidas'].append(opp['id'])
                                    if opp['id'] == arena_data['progresso_arena']['fase_maxima_desbloqueada']:
                                        arena_data['progresso_arena']['fase_maxima_desbloqueada'] += 1
                                st.success("VITÓRIA! Oponente derrotado com honra!")
                                st.balloons()
                            else:
                                st.session_state['last_result'] = 'derrota'
                                motivos = []
                                if not passou_erros: motivos.append(f"Errou {erros_q} (Máx: {limit_errors})")
                                if not passou_tempo: motivos.append(f"Levou {tempo_min} min (Máx: {limit_time})")
                                st.error(f"DERROTA. Motivo: {', '.join(motivos)}.")
                            
                            arena_data['stats'] = stats
                            arena_data['historico_atividades'] = hist
                            full_data['arena_v1_data'] = arena_data
                            
                            save_data(st.session_state['row_idx'], full_data)
                            time.sleep(2)
                            del st.session_state['active_battle_id']
                            st.rerun()

            # Divisor visual
            if opp != page_opponents[-1]:
                st.markdown("""
                <div style="display:flex; justify-content:center; align-items:center; margin: 15px 0;">
                    <div style="height: 1px; width: 60px; background-color: #DAA520; opacity: 0.6;"></div>
                </div>
                """, unsafe_allow_html=True)

        # Navegação no Rodapé
        st.divider()
        c_prev, c_page, c_next = st.columns([1, 2, 1])
        with c_prev:
            if current_page > 0:
                if st.button("⬅️ Anterior"):
                    st.session_state['coliseum_page'] -= 1
                    st.rerun()
        with c_next:
            if current_page < total_pages - 1:
                if st.button("Próximo ➡️"):
                    st.session_state['coliseum_page'] += 1
                    st.rerun()

    # -------------------------------------------------------------------------
    # TAB 2: DOCTORE (REFATORADA)
    # -------------------------------------------------------------------------
    with tab_doctore:
        if 'doctore_state' not in st.session_state:
            st.session_state['doctore_state'] = 'selection'
        if 'selected_master' not in st.session_state:
            st.session_state['selected_master'] = None

        # --- TELA DE SELEÇÃO ---
        if st.session_state['doctore_state'] == 'selection':
            st.markdown("### 🏛️ O Panteão dos Mestres")
            st.markdown("Escolha seu mentor e especialize-se em uma carreira.")
            
            cols = st.columns(2)
            
            # Itera sobre o DOCTORE_DB
            for idx, (key, master) in enumerate(DOCTORE_DB.items()):
                with cols[idx % 2]:
                    with st.container():
                        st.markdown(f"<div class='master-card'>", unsafe_allow_html=True)
                        
                        img_path = master.get('imagem', '')
                        if os.path.exists(img_path):
                            render_centered_image(img_path, width=400)
                        else:
                            if img_path.startswith("http"):
                                st.image(img_path, use_container_width=True)
                            else:
                                st.warning(f"Mestre {master['nome']}")
                        
                        st.markdown(f"### {master['nome']}")
                        st.markdown(f"*{master['descricao']}*")
                        
                        if st.button(f"Treinar com {master['nome']}", key=f"sel_{key}"):
                            st.session_state['selected_master'] = key
                            st.session_state['doctore_state'] = 'training'
                            st.session_state['doctore_session'] = {"active": False, "questions": [], "idx": 0, "wrong_ids": [], "mode": "normal"}
                            st.rerun()
                            
                        st.markdown("</div>", unsafe_allow_html=True)

        # --- TELA DE TREINAMENTO ---
        elif st.session_state['doctore_state'] == 'training':
            master_key = st.session_state['selected_master']
            master_data = DOCTORE_DB.get(master_key)
            
            if not master_data:
                st.error("Mestre não encontrado. Retornando ao panteão.")
                st.session_state['doctore_state'] = 'selection'
                st.rerun()
            
            if st.button("🔙 Voltar ao Panteão", type="secondary"):
                st.session_state['doctore_state'] = 'selection'
                st.rerun()
                
            st.markdown(f"## Treinamento: {master_data['nome']}")
            st.markdown("---")

            if 'doctore_session' not in st.session_state:
                st.session_state['doctore_session'] = {"active": False, "questions": [], "idx": 0, "wrong_ids": [], "mode": "normal"}
            ds = st.session_state['doctore_session']

            # Configuração do Treino (Filtros)
            if not ds['active']:
                materias_disponiveis = list(master_data['materias'].keys())
                
                if not materias_disponiveis:
                     st.warning("Este mestre ainda não possui matérias cadastradas.")
                else:
                    nicho = st.selectbox("1. Escolha a Matéria:", materias_disponiveis)
                    
                    # SELETOR DE ASSUNTO (Dependente da Matéria)
                    assuntos_disponiveis = list(master_data['materias'][nicho].keys())
                    sub_nicho = st.selectbox("2. Escolha o Assunto:", assuntos_disponiveis)
                    
                    c1, c2 = st.columns(2)
                    if c1.button("Iniciar Treino", type="primary", use_container_width=True):
                        # Carrega as questões do Assunto específico
                        qs = master_data['materias'][nicho][sub_nicho].copy()
                        random.shuffle(qs)
                        ds.update({"questions": qs, "idx": 0, "active": True, "wrong_ids": [], "mode": "normal"})
                        st.rerun()
            
            # Execução do Treino (Quiz)
            else:
                q_list = ds['questions']
                idx = ds['idx']
                
                if idx < len(q_list):
                    q = q_list[idx]
                    st.markdown(f"**Modo:** {'REVISÃO' if ds['mode']=='retry' else 'TREINO'} | Q {idx+1}/{len(q_list)}")
                    st.progress((idx)/len(q_list))
                    st.markdown(f"<div class='doctore-card'>{q['texto']}</div>", unsafe_allow_html=True)
                    
                    if 'doc_revealed' not in st.session_state: st.session_state['doc_revealed'] = False
                    
                    # --- ÁREA DE INTERAÇÃO ---
                    if not st.session_state['doc_revealed']:
                        c_c, c_e = st.columns(2)
                        
                        # Função auxiliar para processar a resposta e salvar IMEDIATAMENTE
                        def process_answer(choice_text):
                            st.session_state['doc_choice'] = choice_text
                            st.session_state['doc_revealed'] = True
                            
                            is_correct = (choice_text == q['gabarito'])
                            
                            # Atualiza Stats Locais
                            stats['total_questoes'] += 1
                            if is_correct:
                                stats['total_acertos'] += 1
                            else:
                                stats['total_erros'] += 1
                                if q not in ds['wrong_ids']: ds['wrong_ids'].append(q)
                            
                            # Atualiza Sessão Global e Persiste no Google Sheets
                            arena_data['stats'] = stats
                            full_data['arena_v1_data'] = arena_data
                            
                            # Salva imediatamente para não perder dados se o usuário sair
                            save_data(st.session_state['row_idx'], full_data)

                        if c_c.button("✅ CERTO", use_container_width=True):
                            process_answer("Certo")
                            st.rerun()

                        if c_e.button("❌ ERRADO", use_container_width=True):
                            process_answer("Errado")
                            st.rerun()
                            
                    else:
                        # Exibição do Gabarito e Explicação
                        acertou = (st.session_state['doc_choice'] == q['gabarito'])
                        if acertou: 
                            st.success(f"Correto! O gabarito é {q['gabarito']}.")
                        else: 
                            st.error(f"Errou! O gabarito é {q['gabarito']}.")
                        
                        st.markdown(f"<div class='feedback-box'>{q['explicacao']}</div>", unsafe_allow_html=True)
                        
                        if st.button("Próxima ➡️"):
                            st.session_state['doc_revealed'] = False
                            ds['idx'] += 1
                            st.rerun()
                else:
                    # Fim do Treino
                    st.success("Treino Finalizado!")
                    st.write(f"Erros na rodada: {len(ds['wrong_ids'])}")
                    
                    hist.append({
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "tipo": "Doctore",
                        "detalhe": f"{master_data['nome']} ({ds['mode']})",
                        "resultado": f"{len(q_list)-len(ds['wrong_ids'])}/{len(q_list)} acertos",
                        "tempo": "-"
                    })
                    
                    arena_data['historico_atividades'] = hist
                    full_data['arena_v1_data'] = arena_data
                    save_data(st.session_state['row_idx'], full_data)
                    
                    c1, c2 = st.columns(2)
                    if c1.button("🏠 Novo Treino"):
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
        if arena_data.get('historico_atividades'):
            st.dataframe(pd.DataFrame(arena_data['historico_atividades'][::-1]), use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não há registros.")

if __name__ == "__main__":
    main()
