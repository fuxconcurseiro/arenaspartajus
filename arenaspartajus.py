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
# 0. IMPORTAÇÃO SEGURA DAS LIBS DO GOOGLE
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
SHEET_NAME = "SpartaJus_DB"
QUESTOES_FILE = "questoes.json"

# Arquivos de Imagem
HERO_IMG_FILE = "Arena_Spartajus_Logo_3.jpg"
USER_AVATAR_FILE = "fux_concurseiro.png"
PREPARE_SE_FILE = "prepare-se.jpg"

# ÁUDIO PLACEHOLDER (Para quando o arquivo oficial não existir)
AUDIO_PLACEHOLDER = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

# MAPA DE ESPECIALIDADES (Para injetar nos dados carregados)
SPECIALTIES_MAP = {
    "praetorium": "Constitucional, Administrativo, Penal e Processo Penal",
    "enam_criscis": "Constitucional, Civil, Processo Civil e Empresarial",
    "parquet_tribunus": "Penal, Processo Penal e Direitos Difusos",
    "noel_autarquicus": "Administrativo e Leis Específicas",
    "sara_oracula": "Jurisprudência do STF e STJ",
    "primus_revisao": "Todas as disciplinas possíveis"
}

# MAPA DE ÁUDIO (Mapeamento Exato Solicitado)
# Arquivos locais na pasta 'audios/' ou Placeholder
AUDIO_MAP = {
    "praetorium": "audios/praetorium.m4a",
    "parquet_tribunus": "audios/parquet.m4a",
    "noel_autarquicus": "audios/noel.m4a",
    "sara_oracula": "audios/sara.m4a",
    "primus_revisao": "audios/primus.m4a",
    "enam_criscis": AUDIO_PLACEHOLDER  # Placeholder conforme solicitado
}

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

def render_centered_image(img_path, width=None):
    src = img_path
    if os.path.exists(img_path):
        ext = img_path.split('.')[-1]
        b64 = get_base64_of_bin_file(img_path)
        if b64:
            src = f"data:image/{ext};base64,{b64}"
    
    if width:
        style_attr = f"width: {width}px;"
    else:
        style_attr = "width: 100%; max-width: 400px;"

    st.markdown(f"""
    <div style="display: flex; justify-content: center; margin-top: 5px; margin-bottom: 15px;">
        <img src="{src}" style="{style_attr} border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
    </div>
    """, unsafe_allow_html=True)

def render_red_header(text):
    """
    Usa HTML H3 com estilo inline para garantir a cor vermelha #9E0000.
    """
    st.markdown(f"<h3 style='color: #9E0000 !important; font-weight: 700; margin-top: 5px; margin-bottom: 5px;'>{text}</h3>", unsafe_allow_html=True)

def calculate_daily_stats(history, target_date):
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

# ESTILIZAÇÃO GERAL
st.markdown("""
    <style>
    .stApp { background-color: #F5F4EF; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    
    /* CAMUFLAGEM DE SEGURANÇA */
    .stTextInput > div > div {
        background-color: #F5F4EF !important;
        border-color: #F5F4EF !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        background-color: transparent !important;
    }

    /* Títulos Globais em Vermelho */
    h1, h2, h3, h4, h5, h6, strong, b { color: #9E0000 !important; }
    
    /* Texto do Corpo em Grafite */
    p, label, li, span, .stMarkdown, .stText, div[data-testid="stMarkdownContainer"] p { color: #2e2c2b !important; }
    .stcaption { color: #2e2c2b !important; opacity: 0.8; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #E3DFD3; border-right: 1px solid #dcd8cc; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #9E0000 !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #2e2c2b !important; }
    
    /* Botões e Links */
    .stButton > button, .stLinkButton > a {
        background-color: #E3DFD3 !important;
        color: #9E0000 !important;
        border: 1px solid #E3DFD3 !important;
        border-radius: 6px; 
        font-weight: 700; 
        text-transform: uppercase;
        transition: all 0.3s ease; 
        padding: 0.6rem 1.2rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        text-decoration: none;
        display: inline-flex;
        justify-content: center;
        align-items: center;
    }
    
    .stButton > button:hover, .stLinkButton > a:hover {
        background-color: #E3DFD3 !important; 
        color: #9E0000 !important;            
        border: 1px solid #9E0000 !important; 
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(158, 0, 0, 0.1);
    }
    
    .stButton > button:active, .stLinkButton > a:active {
        background-color: #dcd8cc !important;
        transform: translateY(0px);
    }

    /* Botão de Login */
    [data-testid="stForm"] button {
        height: 60px;
        font-size: 20px !important;
        background-color: #E3DFD3 !important; 
        color: #9E0000 !important;
        border: 1px solid #E3DFD3 !important;
    }
    
    [data-testid="stForm"] button:hover {
        background-color: #E3DFD3 !important;
        border: 1px solid #9E0000 !important;
        color: #9E0000 !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #FFFFFF; color: #2e2c2b; border: 1px solid #E3DFD3;
    }
    
    /* Cards */
    .battle-card, .master-card {
        background-color: #FFFFFF; 
        border: 1px solid #E3DFD3; 
        border-radius: 8px;
        padding: 20px; 
        margin-bottom: 20px; 
        margin-top: 10px;
        text-align: center; 
        transition: all 0.3s ease;
    }
    .battle-card.locked { opacity: 0.6; filter: grayscale(100%); background-color: #F0F0F0; }
    .battle-card.victory { border-left: 4px solid #2E8B57; background-color: #FAFCFA; }
    .master-card:hover { border-color: #9E0000; transform: translateY(-3px); }

    /* Doctore Card (Questão) */
    .doctore-card {
        background-color: #FFFFFF; border: 1px solid #E3DFD3; border-left: 5px solid #9E0000;
        border-radius: 6px; padding: 40px; margin-bottom: 30px;
        display: block; width: 50% !important; min-width: 600px !important;
        margin-left: auto !important; margin-right: auto !important;
        text-align: left !important; font-size: 22px !important; color: #2e2c2b !important;
    }
    
    /* Stats */
    .stat-box { background-color: #FFFFFF; border: 1px solid #E3DFD3; border-radius: 6px; padding: 12px; text-align: center; margin-bottom: 10px; }
    .stat-value { font-size: 1.5em; font-weight: 800; color: #9E0000; }
    .stat-header { font-size: 1.1em; font-weight: bold; color: #9E0000; margin-top: 20px; border-bottom: 1px solid #E3DFD3; }
    .feedback-box { background-color: #Fdfdfd; padding: 20px; border-radius: 4px; margin-top: 20px; border: 1px solid #E3DFD3; text-align: left; }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. CONFIGURAÇÃO DE DADOS & OPONENTES
# -----------------------------------------------------------------------------
DEFAULT_ARENA_DATA = {
    "stats": {"total_questoes": 0, "total_acertos": 0, "total_erros": 0},
    "progresso_arena": {"fase_maxima_desbloqueada": 1, "fases_vencidas": []},
    "historico_atividades": []
}

# BACKUP ATUALIZADO
DEFAULT_DOCTORE_DB = {
    "praetorium": {
        "nome": "Praetorium Lex", 
        "especialidades": "Constitucional, Administrativo, Penal e Processo Penal", 
        "imagem": "praetorium.jpg", 
        "audio": "audios/praetorium.m4a",
        "materias": {}
    }
}

def get_avatar_image(local_file, fallback_url):
    if os.path.exists(local_file): return local_file
    return fallback_url

# LISTA DE OPONENTES COM CAMPO AUDIO
OPONENTS_DB = [
    {
        "id": 1, 
        "nome": "Velho Leão", 
        "descricao": "Suas garras estão gastas, mas sua experiência é mortal.", 
        "avatar_url": get_avatar_image("1_leao_velho.png", ""), 
        "img_vitoria": get_avatar_image("vitoria_leao_velho.jpg", ""), 
        "img_derrota": get_avatar_image("derrota_leao_velho.jpg", ""), 
        "link_tec": "https://www.tecconcursos.com.br/caderno/Q5r1Ng", 
        "dificuldade": "Desafio Inicial", "max_tempo": 60, "max_erros": 7,
        "audio": "audios/velho_leao.m4a" # Arquivo local
    },
    {
        "id": 2, 
        "nome": "Beuzebu", 
        "descricao": "A fúria incontrolável.", 
        "avatar_url": get_avatar_image("touro.jpg", ""), 
        "img_vitoria": get_avatar_image("vitoria_touro.jpg", ""), 
        "img_derrota": get_avatar_image("derrota_touro.jpg", ""), 
        "link_tec": "https://www.tecconcursos.com.br/caderno/Q5rIKB", 
        "dificuldade": "Desafio Inicial", "max_tempo": 40, "max_erros": 6,
        "audio": AUDIO_PLACEHOLDER # Placeholder
    },
    {
        "id": 3, 
        "nome": "Leproso", 
        "descricao": "A doença que corrói a alma.", 
        "avatar_url": get_avatar_image("leproso.jpg", ""), 
        "img_vitoria": get_avatar_image("vitoria_leproso.jpg", ""), 
        "img_derrota": get_avatar_image("derrota_leproso.jpg", ""), 
        "link_tec": "https://www.tecconcursos.com.br/caderno/Q5rIWI", 
        "dificuldade": "Desafio Inicial", "max_tempo": 40, "max_erros": 6,
        "audio": AUDIO_PLACEHOLDER # Placeholder
    },
    {
        "id": 4, 
        "nome": "Autanax, o domador canino", 
        "descricao": "Ele comanda as feras com um olhar gelado.", 
        "avatar_url": get_avatar_image("autanax.png", ""), 
        "img_vitoria": get_avatar_image("vitoria_autanax.png", ""), 
        "img_derrota": get_avatar_image("derrota_autanax.png", ""), 
        "link_tec": "", 
        "dificuldade": "Intermediário", "max_tempo": 30, "max_erros": 5,
        "audio": AUDIO_PLACEHOLDER # Placeholder
    },
    {
        "id": 5, 
        "nome": "Tanara, a infiel", 
        "descricao": "Sua lealdade é comprada com sangue.", 
        "avatar_url": get_avatar_image("tanara.png", ""), 
        "img_vitoria": get_avatar_image("vitoria_tanara.png", ""), 
        "img_derrota": get_avatar_image("derrota_tanara.png", ""), 
        "link_tec": "", 
        "dificuldade": "Difícil", "max_tempo": 30, "max_erros": 5,
        "audio": AUDIO_PLACEHOLDER # Placeholder
    },
    {
        "id": 6, 
        "nome": "Afezio, o renegado", 
        "descricao": "Expulso do panteão, busca vingança.", 
        "avatar_url": get_avatar_image("afezio.png", ""), 
        "img_vitoria": get_avatar_image("vitoria_afezio.png", ""), 
        "img_derrota": get_avatar_image("derrota_afezio.png", ""), 
        "link_tec": "", 
        "dificuldade": "Pesadelo", "max_tempo": 30, "max_erros": 5,
        "audio": AUDIO_PLACEHOLDER # Placeholder
    }
]

# -----------------------------------------------------------------------------
# 4. CARGA DE DADOS DOCTORE (COM INJEÇÃO DE ESPECIALIDADES E ÁUDIO)
# -----------------------------------------------------------------------------
@st.cache_data
def load_doctore_data():
    """Carrega JSON e injeta especialidades e áudio."""
    data = DEFAULT_DOCTORE_DB
    if os.path.exists(QUESTOES_FILE):
        try:
            with open(QUESTOES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
            
    # INJEÇÃO DE METADADOS
    for key, master_info in data.items():
        if key in SPECIALTIES_MAP:
            data[key]['especialidades'] = SPECIALTIES_MAP[key]
            
        if key in AUDIO_MAP:
            data[key]['audio'] = AUDIO_MAP[key]
        else:
            data[key]['audio'] = None
        
        # Garante nomes corretos
        nome_atual = master_info.get('nome', '')
        if "Praetorium" in nome_atual or key == "praetorium":
            data[key]['nome'] = "Praetorium Lex"
        elif "Sara" in nome_atual or key == "sara" or key == "sara_oracula":
            data[key]['nome'] = "Sara Orácula"
        elif "Primus" in nome_atual or key == "primus" or key == "primus_revisao":
            data[key]['nome'] = "Primus Savage"
            
    return data

DOCTORE_DB = load_doctore_data()

# -----------------------------------------------------------------------------
# 5. SISTEMA DE LOGIN E BANCO DE DADOS
# -----------------------------------------------------------------------------
def get_gsheets_client():
    if not LIBS_INSTALLED: return None
    if "gcp_service_account" not in st.secrets: return None
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(credentials)

def check_login(username, password):
    client = get_gsheets_client()
    if not client: return False, "Erro de Biblioteca (ver logs)"
    try:
        sheet = client.open(SHEET_NAME).worksheet("Usuarios")
        records = sheet.get_all_records()
        for record in records:
            if str(record.get('Login', '')).strip() == username and str(record.get('Senha', '')).strip() == password:
                return True, record.get('Nome', 'Gladiador')
        return False, "Usuário ou senha incorretos."
    except Exception as e:
        return False, f"Erro ao acessar base de usuários: {str(e)}"

def load_user_data(username):
    client = get_gsheets_client()
    if not client: return DEFAULT_ARENA_DATA.copy(), None, "Erro libs"
    try:
        sheet = client.open(SHEET_NAME).sheet1
        cell = sheet.find(username, in_column=1)
        if cell:
            raw_data = sheet.cell(cell.row, 3).value 
            if not raw_data: return DEFAULT_ARENA_DATA.copy(), cell.row, "Novo Registro"
            try:
                data = json.loads(raw_data)
                return data, cell.row, "Dados Carregados"
            except:
                return DEFAULT_ARENA_DATA.copy(), cell.row, "Erro no JSON"
        else:
            new_row = [username, "", json.dumps(DEFAULT_ARENA_DATA)]
            sheet.append_row(new_row)
            return DEFAULT_ARENA_DATA.copy(), len(sheet.get_all_values()), "Novo Usuário Criado"
    except Exception as e:
        return DEFAULT_ARENA_DATA.copy(), None, f"Erro Sheets: {str(e)}"

def save_data(row_idx, full_data):
    client = get_gsheets_client()
    if client and row_idx:
        try:
            sheet = client.open(SHEET_NAME).sheet1
            sheet.update_cell(row_idx, 3, json.dumps(full_data))
        except Exception as e:
            print(f"Erro ao salvar: {e}")

# -----------------------------------------------------------------------------
# 6. TELA DE LOGIN
# -----------------------------------------------------------------------------
def login_screen():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists(HERO_IMG_FILE):
            img_b64 = get_base64_of_bin_file(HERO_IMG_FILE)
            st.markdown(f'<img src="data:image/jpg;base64,{img_b64}" style="width:100%; border-radius:10px; margin-bottom:20px;">', unsafe_allow_html=True)
        
        # Título Vermelho Hard-coded
        st.markdown("<h3 style='color: #9E0000;'>🛡️ Portão da Arena</h3>", unsafe_allow_html=True)
        st.info("Utilize suas credenciais para acessar.")
        
        with st.form("login_form"):
            user = st.text_input("Usuário (Login)")
            pwd = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("ENTRAR NA ARENA", type="primary", use_container_width=True)
            
            if submitted:
                if not user or not pwd:
                    st.error("Preencha todos os campos.")
                else:
                    with st.spinner("Validando credenciais..."):
                        success, result = check_login(user, pwd)
                        if success:
                            st.session_state['logged_in'] = True
                            st.session_state['user_id'] = user
                            st.session_state['user_name'] = result
                            st.rerun()
                        else:
                            st.error(result)

# -----------------------------------------------------------------------------
# 7. APP PRINCIPAL
# -----------------------------------------------------------------------------
def main():
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        login_screen()
        return

    current_user = st.session_state['user_id']
    user_name = st.session_state['user_name']

    if 'arena_data' not in st.session_state:
        with st.spinner(f"Carregando dados de {user_name}..."):
            data, row, status = load_user_data(current_user)
            st.session_state['arena_data'] = data
            st.session_state['row_idx'] = row
            st.session_state['status'] = status

    arena_data = st.session_state['arena_data']
    if "stats" not in arena_data: arena_data["stats"] = DEFAULT_ARENA_DATA["stats"].copy()
    if "progresso_arena" not in arena_data: arena_data["progresso_arena"] = DEFAULT_ARENA_DATA["progresso_arena"].copy()
    if "historico_atividades" not in arena_data: arena_data["historico_atividades"] = DEFAULT_ARENA_DATA["historico_atividades"].copy()
    
    stats = arena_data['stats']
    hist = arena_data['historico_atividades']

    # --- SIDEBAR ---
    with st.sidebar:
        if os.path.exists(USER_AVATAR_FILE):
            st.image(USER_AVATAR_FILE, use_container_width=True)
        
        # Nome do usuário Vermelho Hard-coded
        st.markdown(f"<h3 style='color: #9E0000;'>Olá, {user_name}</h3>", unsafe_allow_html=True)
        st.caption(f"ID: {current_user}")
        
        st.divider()
        st.markdown("<div class='stat-header'>📊 Desempenho Global</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#006400'>{stats['total_acertos']}</div><div class='stat-label'>Acertos</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#8B0000'>{stats['total_erros']}</div><div class='stat-label'>Erros</div></div>""", unsafe_allow_html=True)
        
        # TOTAL GLOBAL
        st.markdown(f"""<div class='stat-box'><div class='stat-value'>{stats['total_questoes']}</div><div class='stat-label'>Total de Questões</div></div>""", unsafe_allow_html=True)
        
        st.markdown("<div class='stat-header'>📅 Desempenho Diário</div>", unsafe_allow_html=True)
        selected_date = st.date_input("Data:", datetime.now(), format="DD/MM/YYYY")
        daily_stats = calculate_daily_stats(hist, selected_date)
        
        d1, d2 = st.columns(2)
        d1.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#006400'>{daily_stats['acertos']}</div><div class='stat-label'>Acertos</div></div>""", unsafe_allow_html=True)
        d2.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#8B0000'>{daily_stats['erros']}</div><div class='stat-label'>Erros</div></div>""", unsafe_allow_html=True)
        st.markdown(f"""<div class='stat-box'><div class='stat-value'>{daily_stats['total']}</div><div class='stat-label'>Total do Dia</div></div>""", unsafe_allow_html=True)
        
        if daily_stats['total'] > 0: d_perc = (daily_stats['acertos'] / daily_stats['total']) * 100
        else: d_perc = 0.0
        st.markdown(f"**Eficiência:** {d_perc:.1f}%")
        st.progress(d_perc / 100)

        st.divider()
        if st.button("🔄 Recarregar Dados"):
            st.cache_data.clear()
            del st.session_state['arena_data']
            st.rerun()
        if st.button("🚪 SAIR (Logout)"):
            st.session_state.clear()
            st.rerun()

    # HERO HEADER
    if os.path.exists(HERO_IMG_FILE):
        img_b64 = get_base64_of_bin_file(HERO_IMG_FILE)
        st.markdown(f"""<div style="background-color: #F5F4EF; border-bottom: 4px solid #DAA520; display:flex; justify-content:center; height:250px; overflow:hidden;"><img src="data:image/jpg;base64,{img_b64}" style="height:100%; width:auto;"></div>""", unsafe_allow_html=True)

    tab_batalha, tab_doctore, tab_historico = st.tabs(["🏛️ Coliseum", "🦉 Doctore", "📜 Histórico"])

    # -------------------------------------------------------------------------
    # TAB 1: BATALHA
    # -------------------------------------------------------------------------
    with tab_batalha:
        # Título Hard-Coded
        st.markdown("<h3 style='color: #9E0000;'>🗺️ A Jornada do Gladiador</h3>", unsafe_allow_html=True)
        
        fase_max = arena_data['progresso_arena']['fase_maxima_desbloqueada']
        fases_vencidas = arena_data['progresso_arena']['fases_vencidas']

        ITEMS_PER_PAGE = 3
        if 'coliseum_page' not in st.session_state: st.session_state['coliseum_page'] = 0
        total_pages = (len(OPONENTS_DB) - 1) // ITEMS_PER_PAGE + 1
        
        # ZERO ESPAÇO, ZERO COLUNAS AQUI. INÍCIO DIRETO DO LOOP.
        start_idx = st.session_state['coliseum_page'] * ITEMS_PER_PAGE
        page_opponents = OPONENTS_DB[start_idx : start_idx + ITEMS_PER_PAGE]

        for opp in page_opponents:
            is_locked = opp['id'] > fase_max
            is_completed = opp['id'] in fases_vencidas
            is_current = (opp['id'] == fase_max) and not is_completed
            
            css_class = "battle-card"
            if is_locked: css_class += " locked"
            elif is_completed: css_class += " victory"
            
            st.markdown(f"<div class='{css_class}'>", unsafe_allow_html=True)
            c_img, c_info, c_action = st.columns([1, 2, 1])
            with c_img: 
                render_centered_image(opp['avatar_url'])
                
                # PLAYER HÍBRIDO (Coliseum)
                audio_path = opp.get('audio')
                if audio_path:
                    # 1. Verifica se é link externo
                    if audio_path.startswith('http'):
                        st.audio(audio_path)
                    # 2. Verifica se é arquivo local
                    elif os.path.exists(audio_path):
                        _, ext = os.path.splitext(audio_path)
                        # Define MIME type para m4a ou mp3
                        mime_type = 'audio/mp4' if 'm4a' in ext.lower() else 'audio/mp3'
                        st.audio(audio_path, format=mime_type)
            
            with c_info:
                # NOME OPONENTE HARD-CODED
                st.markdown(f"<h3 style='color: #9E0000;'>{opp['nome']}</h3>", unsafe_allow_html=True)
                st.markdown(f"*{opp['descricao']}*")
                
                if is_locked:
                    st.markdown("<h3 style='color: #9E0000;'>🔒 BLOQUEADO</h3>", unsafe_allow_html=True)
                    st.caption("Vença os desafios anteriores para liberar.")
                else:
                    if is_completed: st.markdown("✅ **CONQUISTADO**")
                    st.markdown(f"🔥 **Dificuldade:** {opp['dificuldade']}")
                    st.caption(f"Tempo: {opp['max_tempo']} min | Erros Máx: {opp['max_erros']}")

            with c_action:
                if not is_locked:
                    if is_current:
                        if st.button("⚔️ BATALHAR", key=f"bat_{opp['id']}", type="primary"):
                            st.session_state['active_battle_id'] = opp['id']
                    elif is_completed:
                        st.button("Refazer", key=f"redo_{opp['id']}")
            
            status_img = None
            if is_completed: status_img = opp['img_vitoria']
            elif is_current and st.session_state.get('last_result') == 'derrota' and st.session_state.get('last_opp_id') == opp['id']:
                status_img = opp['img_derrota']
            elif not is_locked:
                if os.path.exists(PREPARE_SE_FILE): status_img = PREPARE_SE_FILE
            
            if status_img: render_centered_image(status_img, width=400)
            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.get('active_battle_id') == opp['id']:
                with st.expander("⚔️ CAMPO DE BATALHA", expanded=True):
                    st.info(f"Objetivo: {opp['max_tempo']} min | Máx {opp['max_erros']} erros.")
                    if opp['link_tec']:
                        st.link_button("🔗 ABRIR CADERNO TEC", opp['link_tec'], type="primary", use_container_width=True)
                    
                    with st.form(f"battle_form_{opp['id']}"):
                        c1, c2, c3 = st.columns(3)
                        total = c1.number_input("Total Questões", min_value=1)
                        acertos = c2.number_input("Acertos", min_value=0)
                        tempo = c3.number_input("Tempo (min)", min_value=0)
                        
                        if st.form_submit_button("REPORTAR RESULTADO"):
                            erros = max(0, total - acertos)
                            win = (erros <= opp['max_erros']) and (tempo <= opp['max_tempo'])
                            
                            stats['total_questoes'] += total
                            stats['total_acertos'] += acertos
                            stats['total_erros'] += erros
                            hist.append({
                                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "tipo": "Batalha",
                                "detalhe": f"vs {opp['nome']}",
                                "resultado": f"{'Vitória' if win else 'Derrota'} ({acertos}/{total})",
                                "tempo": f"{tempo} min"
                            })
                            
                            st.session_state['last_opp_id'] = opp['id']
                            if win:
                                st.session_state['last_result'] = 'vitoria'
                                if opp['id'] not in fases_vencidas:
                                    fases_vencidas.append(opp['id'])
                                    if opp['id'] == fase_max:
                                        arena_data['progresso_arena']['fase_maxima_desbloqueada'] += 1
                                st.balloons()
                                st.success("VITÓRIA!")
                            else:
                                st.session_state['last_result'] = 'derrota'
                                st.error("DERROTA. Tente novamente!")
                            
                            save_data(st.session_state['row_idx'], arena_data)
                            time.sleep(1.5)
                            del st.session_state['active_battle_id']
                            st.rerun()

        # Navegação no Rodapé (MANTIDA)
        c_prev, c_info, c_next = st.columns([1, 4, 1])
        with c_prev:
            if st.session_state['coliseum_page'] > 0:
                if st.button("⬅️ Anterior"): st.session_state['coliseum_page'] -= 1; st.rerun()
        with c_next:
            if st.session_state['coliseum_page'] < total_pages - 1:
                if st.button("Próximo ➡️"): st.session_state['coliseum_page'] += 1; st.rerun()

    # -------------------------------------------------------------------------
    # TAB 2: DOCTORE
    # -------------------------------------------------------------------------
    with tab_doctore:
        if 'doctore_state' not in st.session_state: st.session_state['doctore_state'] = 'selection'
        
        if st.session_state['doctore_state'] == 'selection':
            # Título Hard-Coded
            st.markdown("<h3 style='color: #9E0000;'>🏛️ O Panteão dos Mestres</h3>", unsafe_allow_html=True)
            st.markdown("Escolha seu mentor e especialize-se em uma carreira.")
            cols = st.columns(2)
            for idx, (key, master) in enumerate(DOCTORE_DB.items()):
                with cols[idx % 2]:
                    with st.container():
                        st.markdown("<div class='master-card'>", unsafe_allow_html=True)
                        
                        # INSERÇÃO DAS ESPECIALIDADES
                        if 'especialidades' in master:
                            st.markdown(f"""
                            <div style="
                                background-color: #E3DFD3;
                                color: #5D4037;
                                padding: 6px 10px;
                                border-radius: 6px;
                                text-align: center;
                                font-size: 0.8rem;
                                font-weight: 600;
                                margin-bottom: 8px;
                                border: 1px solid #D7CCC8;
                                box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
                            ">
                                📚 {master['especialidades']}
                            </div>
                            """, unsafe_allow_html=True)

                        if master.get('imagem'): render_centered_image(master['imagem'], width=400)
                        
                        # PLAYER HÍBRIDO (Doctore)
                        audio_path = master.get('audio')
                        if audio_path:
                            # 1. Verifica se é link externo
                            if audio_path.startswith('http'):
                                st.audio(audio_path)
                            # 2. Verifica se é arquivo local
                            elif os.path.exists(audio_path):
                                _, ext = os.path.splitext(audio_path)
                                # Define MIME type para m4a ou mp3
                                mime_type = 'audio/mp4' if 'm4a' in ext.lower() else 'audio/mp3'
                                st.audio(audio_path, format=mime_type)

                        # NOME MESTRE HARD-CODED
                        st.markdown(f"<h3 style='color: #9E0000;'>{master['nome']}</h3>", unsafe_allow_html=True)
                        
                        st.markdown(f"*{master['descricao']}*")
                        if st.button(f"Treinar", key=f"sel_{key}"):
                            st.session_state['selected_master'] = key
                            st.session_state['doctore_state'] = 'training'
                            st.session_state['doctore_session'] = {"active": False, "questions": [], "idx": 0, "wrong_ids": [], "mode": "normal"}
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
        
        elif st.session_state['doctore_state'] == 'training':
             if st.button("🔙 Voltar ao Panteão"):
                 st.session_state['doctore_state'] = 'selection'
                 st.rerun()
             
             master_key = st.session_state['selected_master']
             master = DOCTORE_DB.get(master_key)
             if not master: st.rerun()
             
             # NOME MESTRE TREINO HARD-CODED
             st.markdown(f"<h3 style='color: #9E0000;'>{master['nome']}</h3>", unsafe_allow_html=True)
             st.markdown("---")
             
             if 'doctore_session' not in st.session_state:
                 st.session_state['doctore_session'] = {"active": False, "questions": [], "idx": 0}
             ds = st.session_state['doctore_session']
             
             if not ds['active']:
                 materias = list(master['materias'].keys())
                 if not materias:
                     st.warning("Sem matérias cadastradas.")
                 else:
                     nicho = st.selectbox("Escolha a Matéria:", materias)
                     assuntos = list(master['materias'][nicho].keys())
                     sub_nicho = st.selectbox("Escolha o Assunto:", assuntos)
                     
                     if st.button("Iniciar Treino", type="primary"):
                         qs = master['materias'][nicho][sub_nicho].copy()
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
                         c1, c2 = st.columns(2)
                         
                         def process_answer(ans):
                             st.session_state['doc_choice'] = ans
                             st.session_state['doc_revealed'] = True
                             is_correct = (ans == q['gabarito'])
                             
                             stats['total_questoes'] += 1 # Correção: Incremento unitário
                             if is_correct: stats['total_acertos'] += 1
                             else:
                                 stats['total_erros'] += 1
                                 if q not in ds['wrong_ids']: ds['wrong_ids'].append(q)
                             
                             save_data(st.session_state['row_idx'], arena_data)

                         if c1.button("✅ CERTO", use_container_width=True): process_answer("Certo"); st.rerun()
                         if c2.button("❌ ERRADO", use_container_width=True): process_answer("Errado"); st.rerun()
                     
                     else:
                         acertou = (st.session_state['doc_choice'] == q['gabarito'])
                         if acertou: st.success(f"Correto! Gabarito: {q['gabarito']}")
                         else: st.error(f"Errou! Gabarito: {q['gabarito']}")
                         
                         st.markdown(f"<div class='feedback-box'>{q['explicacao']}</div>", unsafe_allow_html=True)
                         
                         if st.button("Próxima ➡️"):
                             st.session_state['doc_revealed'] = False
                             ds['idx'] += 1
                             st.rerun()
                 else:
                     st.success("Treino Finalizado!")
                     st.write(f"Erros: {len(ds['wrong_ids'])}")
                     
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
        if hist:
            st.dataframe(pd.DataFrame(hist[::-1]), use_container_width=True, hide_index=True)
        else:
            st.info("Sem histórico.")

if __name__ == "__main__":
    main()
