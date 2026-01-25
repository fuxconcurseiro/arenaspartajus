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

# Arquivos de Imagem (Certifique-se de que estão no repositório)
# Capa principal (Banner)
HERO_IMG_FILE = "Arena_Spartajus_Logo_3.jpg"
# Avatar do usuário para a barra lateral
USER_AVATAR_FILE = "fux_concurseiro.png"
# Imagem de espera
PREPARE_SE_FILE = "prepare-se.jpg"

# -----------------------------------------------------------------------------
# 2. FUNÇÕES VISUAIS (BASE64 E CSS)
# -----------------------------------------------------------------------------
def get_base64_of_bin_file(bin_file):
    """Lê um arquivo de imagem local e converte para base64 para uso em CSS/HTML."""
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

# ESTILIZAÇÃO GERAL
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
    
    /* CARD DO DOCTORE (SELEÇÃO) */
    .master-card {
        background-color: #FFF; 
        border: 4px double #8B4513; 
        border-radius: 15px; 
        padding: 20px; 
        text-align: center;
        transition: transform 0.2s;
        margin-bottom: 20px;
    }
    .master-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        border-color: #DAA520;
    }
    
    /* ESTATÍSTICAS SIDEBAR */
    .stat-box {
        background-color: #FFFFFF; border: 1px solid #DEB887; border-radius: 8px;
        padding: 10px; text-align: center; margin-bottom: 10px;
    }
    .stat-value { font-size: 1.5em; font-weight: bold; color: #8B4513; }
    .stat-label { font-size: 0.8em; color: #666; text-transform: uppercase; }

    /* DOCTORE QUESTION CARD */
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
# 4. BASE DE DADOS (OPONENTES)
# -----------------------------------------------------------------------------
def get_avatar_image(local_file, fallback_url):
    """Verifica se a imagem local existe, caso contrário usa fallback."""
    if os.path.exists(local_file):
        return local_file
    return fallback_url

OPONENTS_DB = [
    {
        "id": 1,
        "nome": "O Velho Leão",
        "descricao": "Suas garras estão gastas, mas sua experiência é mortal.",
        # Avatar Inicial
        "avatar_url": get_avatar_image("1_leao_velho.png", "https://img.icons8.com/color/96/lion.png"),
        # Imagem de Vitória (Consequência Positiva)
        "img_vitoria": get_avatar_image("vitoria_leao_velho.jpg", "https://img.icons8.com/color/96/laurel-wreath.png"),
        # Imagem de Derrota (Consequência Negativa)
        "img_derrota": get_avatar_image("derrota_leao_velho.jpg", "https://img.icons8.com/color/96/skull.png"),
        "link_tec": "https://www.tecconcursos.com.br/caderno/Q5r1Ng", 
        "dificuldade": "Desafio Inicial",
        "max_tempo": 60, 
        "max_erros": 7 
    },
    {
        "id": 2,
        "nome": "Legionário da Lei Seca",
        "descricao": "A letra da lei é sua espada. Atenção aos detalhes.",
        "avatar_url": "https://img.icons8.com/color/96/centurion.png",
        "img_vitoria": "https://img.icons8.com/color/96/trophy.png",
        "img_derrota": "https://img.icons8.com/color/96/dead-body.png",
        "link_tec": "https://www.tecconcursos.com.br",
        "dificuldade": "Intermediário",
        "max_tempo": 45,
        "max_erros": 5
    },
    {
        "id": 3,
        "nome": "Centurião da Jurisprudência",
        "descricao": "Rápido, letal e cheio de precedentes.",
        "avatar_url": "https://img.icons8.com/color/96/spartan-helmet.png",
        "img_vitoria": "https://img.icons8.com/color/96/crown.png",
        "img_derrota": "https://img.icons8.com/color/96/grave.png",
        "link_tec": "https://www.tecconcursos.com.br",
        "dificuldade": "Avançado",
        "max_tempo": 30,
        "max_erros": 3
    }
]

# -----------------------------------------------------------------------------
# 5. BASE DE DADOS HIERÁRQUICA (DOCTORE)
# -----------------------------------------------------------------------------
DOCTORE_DB = {
    "praetorium": {
        "nome": "Praetorium Legislativus",
        "descricao": "O Guardião das Leis e do Processo Legislativo.",
        "imagem": "praetorium.jpg", 
        "materias": {
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
            "Processo Legislativo": [
                {
                    "id": 301,
                    "texto": "A sanção do projeto de lei não convalida o vício de iniciativa.",
                    "gabarito": "Certo",
                    "origem": "Súmula STF",
                    "explicacao": "O vício de iniciativa é insanável pela sanção presidencial/governador."
                }
            ]
        }
    },
    "enam_criscis": {
        "nome": "Enam Criscis",
        "descricao": "A Sabedoria da Toga. Mestre do Exame Nacional da Magistratura.",
        "imagem": "enam-criscis.png",
        "materias": {
            "Direitos Humanos": [
                {
                    "id": 401,
                    "texto": "A Corte Interamericana de Direitos Humanos admite a possibilidade de controle de convencionalidade das leis internas.",
                    "gabarito": "Certo",
                    "origem": "Jurisprudência Corte IDH",
                    "explicacao": "O controle de convencionalidade é dever do Judiciário nacional."
                }
            ],
            "Direito Administrativo": [
                {
                    "id": 402,
                    "texto": "A responsabilidade civil do Estado por atos omissivos é, em regra, objetiva.",
                    "gabarito": "Errado",
                    "origem": "Doutrina Majoritária",
                    "explicacao": "No caso de omissão, a responsabilidade é subjetiva (teoria da 'faute du service'), salvo em casos de custódia onde o Estado é garante."
                }
            ]
        }
    },
    "parquet_tribunus": {
        "nome": "Parquet Tribunus",
        "descricao": "O Defensor da Sociedade. Mestre das Promotorias de Justiça.",
        "imagem": "parquet.jpg", # Deve estar no repositório
        "materias": {
            "Direito Processual Coletivo": [
                {
                    "id": 501,
                    "texto": "O Ministério Público possui legitimidade para propor Ação Civil Pública visando a defesa de direitos individuais homogêneos, ainda que disponíveis, quando houver relevância social.",
                    "gabarito": "Certo",
                    "origem": "Tema Repetitivo STJ",
                    "explicacao": "A relevância social do bem jurídico tutelado legitima a atuação do MP."
                }
            ],
            "Direito Penal": [
                {
                    "id": 502,
                    "texto": "Na ação penal pública condicionada, a representação do ofendido é condição de procedibilidade, mas pode ser retratada até o oferecimento da denúncia.",
                    "gabarito": "Certo",
                    "origem": "Art. 25 CPP",
                    "explicacao": "A retratação é permitida até o oferecimento da denúncia, não até o recebimento."
                }
            ]
        }
    }
}

# -----------------------------------------------------------------------------
# 6. CONEXÃO GOOGLE SHEETS
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
# 7. APP PRINCIPAL
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

    # --- SIDEBAR ---
    with st.sidebar:
        if os.path.exists(USER_AVATAR_FILE):
            st.image(USER_AVATAR_FILE, caption=TEST_USER, use_container_width=True)
        else:
            st.header(f"🏛️ {TEST_USER}")
            st.warning("Avatar não encontrado (fux_concurseiro.png)")
        
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
        }}
        .full-width-hero img {{
            width: 100%;
            height: auto;
            object-fit: cover;
            display: block;
            border-bottom: 4px solid #DAA520;
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
                render_centered_image(opp['avatar_url'], width=200)
            
            with c_info:
                st.markdown(f"### {opp['nome']}")
                st.markdown(f"*{opp['descricao']}*")
                if is_locked: st.markdown("🔒 **BLOQUEADO**")
                elif is_completed: st.markdown("✅ **CONQUISTADO**")
                else: 
                    st.markdown(f"🔥 **Dificuldade:** {opp['dificuldade']}")
                    st.caption(f"Tempo Máx: {opp['max_tempo']} min | Limite de Erros: {opp['max_erros']}")

            with c_action:
                if is_current:
                    if st.button("⚔️ BATALHAR", key=f"bat_{opp['id']}", type="primary"):
                        st.session_state['active_battle_id'] = opp['id']
                elif is_completed:
                    st.button("Refazer", key=f"redo_{opp['id']}")
            
            # Imagem de Status Centralizada (400px)
            status_img_path = None
            if is_completed: status_img_path = opp['img_vitoria']
            elif is_current and st.session_state.get('last_result') == 'derrota' and st.session_state.get('last_opp_id') == opp['id']: status_img_path = opp['img_derrota']
            else: 
                if os.path.exists(PREPARE_SE_FILE): status_img_path = PREPARE_SE_FILE
                else: status_img_path = "https://img.icons8.com/color/96/shield.png"
            
            if status_img_path:
                render_centered_image(status_img_path, width=400)

            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.get('active_battle_id') == opp['id']:
                with st.expander("⚔️ CAMPO DE BATALHA", expanded=True):
                    st.info(f"Derrote {opp['nome']}. Você deve terminar em até {opp['max_tempo']} minutos e errar no máximo {opp['max_erros']} questões.")
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
                                st.success("VITÓRIA! Oponente derrotado com honra!")
                                st.balloons()
                            else:
                                st.session_state['last_result'] = 'derrota'
                                motivos = []
                                if not passou_erros: motivos.append(f"Errou {erros_q} (Máx: {limit_errors})")
                                if not passou_tempo: motivos.append(f"Levou {tempo_min} min (Máx: {limit_time})")
                                st.error(f"DERROTA. Motivo: {', '.join(motivos)}.")
                            
                            save_data(st.session_state['row_idx'], user_data)
                            time.sleep(2)
                            del st.session_state['active_battle_id']
                            st.rerun()

            # Conector Discreto
            if opp['id'] < len(OPONENTS_DB):
                st.markdown("""
                <div style="display:flex; justify-content:center; align-items:center; margin: 15px 0;">
                    <div style="height: 1px; width: 60px; background-color: #DAA520; opacity: 0.6;"></div>
                    <div style="color: #DAA520; font-size: 14px; margin: 0 10px; opacity: 0.8;">🔗</div>
                    <div style="height: 1px; width: 60px; background-color: #DAA520; opacity: 0.6;"></div>
                </div>
                """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # TAB 2: DOCTORE (O PANTEÃO DOS MESTRES)
    # -------------------------------------------------------------------------
    with tab_doctore:
        if 'doctore_state' not in st.session_state:
            st.session_state['doctore_state'] = 'selection'
        if 'selected_master' not in st.session_state:
            st.session_state['selected_master'] = None

        if st.session_state['doctore_state'] == 'selection':
            st.markdown("### 🏛️ O Panteão dos Mestres")
            st.markdown("Escolha seu mentor e especialize-se em uma carreira.")
            
            cols = st.columns(2)
            
            for idx, (key, master) in enumerate(DOCTORE_DB.items()):
                with cols[idx % 2]:
                    with st.container():
                        st.markdown(f"<div class='master-card'>", unsafe_allow_html=True)
                        
                        img_path = master['imagem']
                        if os.path.exists(img_path):
                            render_centered_image(img_path, width=400)
                        else:
                            if img_path.startswith("http"):
                                st.image(img_path, use_container_width=True)
                            else:
                                st.warning(f"Imagem {img_path} não encontrada.")
                        
                        st.markdown(f"### {master['nome']}")
                        st.markdown(f"*{master['descricao']}*")
                        
                        if st.button(f"Treinar com {master['nome']}", key=f"sel_{key}"):
                            st.session_state['selected_master'] = key
                            st.session_state['doctore_state'] = 'training'
                            st.session_state['doctore_session'] = {"active": False, "questions": [], "idx": 0, "wrong_ids": [], "mode": "normal"}
                            st.rerun()
                            
                        st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state['doctore_state'] == 'training':
            master_key = st.session_state['selected_master']
            master_data = DOCTORE_DB[master_key]
            
            if st.button("🔙 Voltar ao Panteão", type="secondary"):
                st.session_state['doctore_state'] = 'selection'
                st.rerun()
                
            st.markdown(f"## Treinamento: {master_data['nome']}")
            st.markdown("---")

            if 'doctore_session' not in st.session_state:
                st.session_state['doctore_session'] = {"active": False, "questions": [], "idx": 0, "wrong_ids": [], "mode": "normal"}
            ds = st.session_state['doctore_session']

            if not ds['active']:
                materias_disponiveis = list(master_data['materias'].keys())
                nicho = st.selectbox("Escolha a Matéria do Mestre:", materias_disponiveis)
                
                c1, c2 = st.columns(2)
                if c1.button("Iniciar Treino", type="primary", use_container_width=True):
                    qs = master_data['materias'][nicho].copy()
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
                        "detalhe": f"{master_data['nome']} ({ds['mode']})",
                        "resultado": f"{len(q_list)-len(ds['wrong_ids'])}/{len(q_list)} acertos",
                        "tempo": "-"
                    })
                    save_data(st.session_state['row_idx'], user_data)
                    
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
        if user_data['historico_atividades']:
            st.dataframe(pd.DataFrame(user_data['historico_atividades'][::-1]), use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não há registros.")

if __name__ == "__main__":
    main()
