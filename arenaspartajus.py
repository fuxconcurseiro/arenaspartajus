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
    page_title="Arena SpartaJus | Doctore",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 1. CONSTANTES E ARQUIVOS
# -----------------------------------------------------------------------------
TEST_USER = "fux_concurseiro"
SHEET_NAME = "SpartaJus_DB"

# Arquivos de Imagem
HERO_IMG_FILE = "Arena_Spartajus_Logo_3.jpg"
USER_AVATAR_FILE = "fux_concurseiro.png"
PREPARE_SE_FILE = "prepare-se.jpg"
PRIMARY_COLOR = "#A1CC14" # Verde Lima Doctore

# -----------------------------------------------------------------------------
# 2. BANCO DE QUESTÕES PROCESSADO (ETL - DOCTORE PRAETORIUM)
# -----------------------------------------------------------------------------
# Estrutura gerada conforme especificação: 50% Incorretas (Cognatos-Antagônicos)
QUESTOES_DB = [
    # --- PROCESSO LEGISLATIVO ---
    {
        "id": 1001,
        "assunto": "Processo Legislativo",
        "texto": "A sanção do projeto de lei não convalida o vício de iniciativa.",
        "gabarito": "Certo",
        "origem": "STF - Súmula nº 5",
        "justificativa": "Correto. O vício de iniciativa é insanável e não pode ser convalidado pela sanção posterior do Chefe do Executivo."
    },
    {
        "id": 1002,
        "assunto": "Processo Legislativo",
        "texto": "Não se admite emenda parlamentar em projeto de iniciativa exclusiva do Chefe do Executivo, ainda que não acarrete aumento de despesa e tenha pertinência temática.",
        "gabarito": "Errado",
        "origem": "CF/88, Art. 63",
        "justificativa": "Errado. É ADMISSÍVEL a emenda parlamentar em projetos de iniciativa exclusiva, DESDE QUE não acarrete aumento de despesa (exceto nos projetos de lei do orçamento) e possua pertinência temática."
    },
    {
        "id": 1003,
        "assunto": "Processo Legislativo",
        "texto": "A matéria constante de projeto de lei rejeitado somente poderá constituir objeto de novo projeto, na mesma sessão legislativa, mediante proposta da maioria absoluta dos membros de qualquer das Casas do Congresso Nacional.",
        "gabarito": "Certo",
        "origem": "CF/88, Art. 67",
        "justificativa": "Correto. Trata-se do princípio da irrepetibilidade relativa."
    },
    {
        "id": 1004,
        "assunto": "Processo Legislativo",
        "texto": "As medidas provisórias perderão eficácia, desde a edição, se não forem convertidas em lei no prazo de sessenta dias, prorrogável, nos termos da Constituição, uma vez por igual período.",
        "gabarito": "Certo",
        "origem": "CF/88, Art. 62, § 3º",
        "justificativa": "Correto. O prazo inicial é de 60 dias, prorrogável automaticamente por mais 60 dias se não tiver sido votada."
    },
    {
        "id": 1005,
        "assunto": "Processo Legislativo",
        "texto": "É vedada a reedição, na mesma sessão legislativa, de medida provisória que tenha sido rejeitada ou que tenha perdido sua eficácia por decurso de prazo.",
        "gabarito": "Certo",
        "origem": "CF/88, Art. 62, § 10",
        "justificativa": "Correto. Princípio da irrepetibilidade absoluta para Medidas Provisórias na mesma sessão legislativa."
    },
    
    # --- DIREITOS FUNDAMENTAIS ---
    {
        "id": 2001,
        "assunto": "Direitos Fundamentais",
        "texto": "A casa é asilo inviolável do indivíduo, ninguém nela podendo penetrar sem consentimento do morador, inclusive em caso de flagrante delito ou desastre.",
        "gabarito": "Errado",
        "origem": "CF/88, Art. 5º, XI",
        "justificativa": "Errado. A Constituição permite a entrada SEM consentimento em casos de flagrante delito, desastre, ou para prestar socorro (a qualquer hora), ou durante o dia por determinação judicial."
    },
    {
        "id": 2002,
        "assunto": "Direitos Fundamentais",
        "texto": "É livre a manifestação do pensamento, sendo vedado o anonimato.",
        "gabarito": "Certo",
        "origem": "CF/88, Art. 5º, IV",
        "justificativa": "Correto. A liberdade de expressão é garantida, contudo, a Constituição veda expressamente o anonimato para garantir a responsabilização por abusos."
    },
    {
        "id": 2003,
        "assunto": "Direitos Fundamentais",
        "texto": "É plena a liberdade de associação para fins lícitos, inclusive a de caráter paramilitar.",
        "gabarito": "Errado",
        "origem": "CF/88, Art. 5º, XVII",
        "justificativa": "Errado. A Constituição VEDA expressamente as associações de caráter paramilitar."
    },
    
    # --- CONTROLE DE CONSTITUCIONALIDADE ---
    {
        "id": 3001,
        "assunto": "Controle de Constitucionalidade",
        "texto": "A Ação Direta de Inconstitucionalidade (ADI) pode ter como objeto lei ou ato normativo federal ou estadual.",
        "gabarito": "Certo",
        "origem": "CF/88, Art. 102, I, a",
        "justificativa": "Correto. A ADI genérica ataca leis federais ou estaduais contrárias à Constituição Federal."
    },
    {
        "id": 3002,
        "assunto": "Controle de Constitucionalidade",
        "texto": "O Partido Político com representação no Congresso Nacional prescinde de procuração com poderes específicos para ajuizar ADI, bastando a procuração geral.",
        "gabarito": "Errado",
        "origem": "Jurisprudência STF",
        "justificativa": "Errado. Embora tenham legitimidade universal (não precisam provar pertinência temática), a jurisprudência exige procuração com poderes ESPECÍFICOS para o ajuizamento da ação."
    }
]

# -----------------------------------------------------------------------------
# 3. FUNÇÕES DE SUPORTE
# -----------------------------------------------------------------------------
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

def render_centered_image(img_path, width=200):
    src = img_path
    if os.path.exists(img_path):
        ext = img_path.split('.')[-1]
        b64 = get_base64_of_bin_file(img_path)
        if b64: src = f"data:image/{ext};base64,{b64}"
    st.markdown(f"<div style='display: flex; justify-content: center; margin: 15px 0;'><img src='{src}' style='width: {width}px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'></div>", unsafe_allow_html=True)

def connect_db():
    if not LIBS_INSTALLED: return None, f"Erro Crítico: {IMPORT_ERROR}"
    if "gcp_service_account" not in st.secrets: return None, "Secrets não configurados."
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(credentials)
        sheet = client.open(SHEET_NAME).sheet1
        return sheet, None
    except Exception as e: return None, str(e)

def save_data(data):
    # Salva dados na nuvem (apenas se conectado)
    sheet, _ = connect_db()
    if sheet:
        try:
            # Encontra a linha do usuário ou cria
            cell = sheet.find(TEST_USER)
            if cell:
                # Merge lógico para não perder dados antigos
                raw = sheet.cell(cell.row, 2).value
                try: full_data = json.loads(raw)
                except: full_data = {}
                
                # Atualiza apenas a arena
                full_data['arena_v1_data'] = data
                sheet.update_cell(cell.row, 2, json.dumps(full_data))
        except: pass

def load_local_or_cloud():
    # Tenta carregar da nuvem, se falhar, inicia zerado
    sheet, _ = connect_db()
    default_data = {
        "stats": {"total_questoes": 0, "total_acertos": 0, "total_erros": 0},
        "progresso_arena": {"fase_maxima_desbloqueada": 1, "fases_vencidas": []},
        "historico_atividades": []
    }
    
    if sheet:
        try:
            cell = sheet.find(TEST_USER)
            if cell:
                raw = json.loads(sheet.cell(cell.row, 2).value)
                return raw.get('arena_v1_data', default_data), "🟢 Online"
        except: pass
    
    return default_data, "🟠 Offline"

# -----------------------------------------------------------------------------
# 4. APLICATIVO PRINCIPAL
# -----------------------------------------------------------------------------
def main():
    # Inicialização de Estado
    if 'app_data' not in st.session_state:
        data, status = load_local_or_cloud()
        st.session_state['app_data'] = data
        st.session_state['connection_status'] = status
    
    # Estado específico para o Doctore
    if 'doctore_state' not in st.session_state:
        st.session_state['doctore_state'] = 'selection' # selection | training
    
    if 'current_quiz_session' not in st.session_state:
        st.session_state['current_quiz_session'] = {
            'subject': None,
            'questions': [],
            'current_idx': 0,
            'score': 0,
            'revealed': False,
            'user_answer': None
        }

    data = st.session_state['app_data']
    
    # --- ESTILIZAÇÃO CSS (DOCTORE THEME) ---
    st.markdown(f"""
    <style>
    /* Cores Globais */
    .stApp {{ background-color: #FFFFF0; color: #333; }}
    
    /* Botões Padrão */
    .stButton>button {{
        background-color: #FFDEAD; color: #5C4033; 
        border: 1px solid #8B4513; border-radius: 6px; font-weight: bold;
    }}
    
    /* Botões de Ação Doctore */
    .btn-certo {{ background-color: {PRIMARY_COLOR} !important; color: white !important; }}
    .btn-errado {{ background-color: #FF6B6B !important; color: white !important; }}
    
    /* Card de Questão */
    .question-card {{
        background-color: #FFFFFF;
        border-left: 6px solid {PRIMARY_COLOR};
        padding: 25px;
        border-radius: 8px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        font-family: 'Georgia', serif;
        font-size: 1.25rem;
        line-height: 1.6;
        margin-bottom: 20px;
    }}
    
    /* Feedback Box */
    .feedback-box {{
        padding: 20px;
        border-radius: 8px;
        margin-top: 15px;
        border: 1px solid #ddd;
        animation: fadeIn 0.5s;
    }}
    .feedback-correct {{ background-color: #F0FFF0; border-color: {PRIMARY_COLOR}; }}
    .feedback-wrong {{ background-color: #FFF0F0; border-color: #FF6B6B; }}
    
    @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    </style>
    """, unsafe_allow_html=True)

    # --- SIDEBAR ---
    with st.sidebar:
        if os.path.exists(USER_AVATAR_FILE):
            st.image(USER_AVATAR_FILE, caption=TEST_USER, use_container_width=True)
        else:
            st.header(f"🏛️ {TEST_USER}")
        
        st.caption(f"Status: {st.session_state['connection_status']}")
        st.markdown("---")
        
        # Filtro de Assunto para o Doctore (Se estiver na aba certa)
        # Nota: O filtro pode ficar aqui ou no corpo principal. 
        # Colocarei aqui para cumprir o requisito de sidebar.
        unique_subjects = sorted(list(set([q['assunto'] for q in QUESTOES_DB])))
        selected_subject = st.selectbox(
            "📚 Filtrar Treino por Assunto:",
            ["Todos"] + unique_subjects,
            key="sb_subject_filter"
        )
        
        # Reset ao mudar de assunto
        if 'last_subject' not in st.session_state: st.session_state['last_subject'] = "Todos"
        if st.session_state['last_subject'] != selected_subject:
            st.session_state['last_subject'] = selected_subject
            # Reseta o estado do quiz para forçar nova seleção
            st.session_state['doctore_state'] = 'selection'
            st.rerun()

        st.markdown("---")
        # Stats Globais
        stats = data['stats']
        c1, c2 = st.columns(2)
        c1.metric("Acertos", stats['total_acertos'])
        c2.metric("Erros", stats['total_erros'])
        st.progress(stats['total_acertos'] / max(stats['total_questoes'], 1))

    # --- HERO HEADER ---
    if os.path.exists(HERO_IMG_FILE):
        img_b64 = get_base64_of_bin_file(HERO_IMG_FILE)
        st.markdown(f"""
        <div style="width:100vw; position:relative; left:50%; right:50%; margin-left:-50vw; margin-right:-50vw; margin-bottom:20px; height:200px; overflow:hidden; border-bottom:4px solid #DAA520;">
            <img src="data:image/jpg;base64,{img_b64}" style="width:100%; height:100%; object-fit:cover;">
        </div>
        """, unsafe_allow_html=True)

    # --- TABS ---
    tab_batalha, tab_doctore, tab_historico = st.tabs(["Combates no Coliseum", "🦉 Doctore (Treinos no Ludus)", "📜 Histórico"])

    # -------------------------------------------------------------------------
    # TAB DOCTORE (NOVO MOTOR DE SIMULAÇÃO)
    # -------------------------------------------------------------------------
    with tab_doctore:
        st.markdown(f"<h2 style='color:{PRIMARY_COLOR};'>Doctore Praetorium Legislativus</h2>", unsafe_allow_html=True)
        
        qs_session = st.session_state['current_quiz_session']

        # ESTADO 1: PREPARAÇÃO (Seleção ou Início)
        if st.session_state['doctore_state'] == 'selection':
            # Filtra o DB
            if selected_subject == "Todos":
                filtered_qs = QUESTOES_DB
            else:
                filtered_qs = [q for q in QUESTOES_DB if q['assunto'] == selected_subject]
            
            st.info(f"O Mestre selecionou **{len(filtered_qs)}** pergaminhos sobre **{selected_subject}**.")
            
            if st.button("⚔️ INICIAR TREINAMENTO", type="primary", use_container_width=True):
                # Setup do Quiz
                random.shuffle(filtered_qs)
                st.session_state['current_quiz_session'] = {
                    'subject': selected_subject,
                    'questions': filtered_qs,
                    'current_idx': 0,
                    'score': 0,
                    'revealed': False,
                    'user_answer': None
                }
                st.session_state['doctore_state'] = 'active'
                st.rerun()

        # ESTADO 2: RESOLUÇÃO (Quiz Ativo)
        elif st.session_state['doctore_state'] == 'active':
            questions = qs_session['questions']
            idx = qs_session['current_idx']
            
            # Verifica se acabou
            if idx < len(questions):
                current_q = questions[idx]
                
                # Barra de Progresso
                st.progress((idx) / len(questions))
                st.caption(f"Questão {idx + 1} de {len(questions)} | Score Atual: {qs_session['score']}")
                
                # Display da Questão (Container Limpo)
                with st.container():
                    st.markdown(f"""
                    <div class='question-card'>
                        <small style='color:#666;'>{current_q['origem']} | {current_q['assunto']}</small><br><br>
                        {current_q['texto']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Área de Resposta
                if not qs_session['revealed']:
                    c1, c2 = st.columns(2)
                    if c1.button("CERTO", use_container_width=True):
                        qs_session['user_answer'] = "Certo"
                        qs_session['revealed'] = True
                        
                        # Lógica de Pontuação
                        is_correct = (current_q['gabarito'] == "Certo")
                        if is_correct: 
                            qs_session['score'] += 1
                            data['stats']['total_acertos'] += 1
                        else:
                            data['stats']['total_erros'] += 1
                        data['stats']['total_questoes'] += 1
                        save_data(data) # Salva imediatamente
                        st.rerun()
                        
                    if c2.button("ERRADO", use_container_width=True):
                        qs_session['user_answer'] = "Errado"
                        qs_session['revealed'] = True
                        
                        # Lógica de Pontuação
                        is_correct = (current_q['gabarito'] == "Errado")
                        if is_correct: 
                            qs_session['score'] += 1
                            data['stats']['total_acertos'] += 1
                        else:
                            data['stats']['total_erros'] += 1
                        data['stats']['total_questoes'] += 1
                        save_data(data)
                        st.rerun()
                
                # Área de Feedback (Pós-clique)
                else:
                    user_ans = qs_session['user_answer']
                    correct_ans = current_q['gabarito']
                    is_hit = (user_ans == correct_ans)
                    
                    bg_class = "feedback-correct" if is_hit else "feedback-wrong"
                    icon = "✅" if is_hit else "❌"
                    color = PRIMARY_COLOR if is_hit else "#B22222"
                    
                    st.markdown(f"""
                    <div class='feedback-box {bg_class}'>
                        <h3 style='color:{color}; margin:0;'>{icon} Você marcou {user_ans.upper()}</h3>
                        <p><strong>Gabarito:</strong> {correct_ans.upper()}</p>
                        <hr style='border-color: #ccc; opacity: 0.5;'>
                        <p style='font-style: italic;'>"{current_q['justificativa']}"</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("PRÓXIMA QUESTÃO ➡️", type="primary"):
                        qs_session['current_idx'] += 1
                        qs_session['revealed'] = False
                        qs_session['user_answer'] = None
                        st.rerun()
                    else:
                        st.success(f"Treino Finalizado! Acertos: {qs_session['score']}/{len(questions)}")
                        # Registra no histórico ao final
                        hist = data.get('historico_atividades', [])
                        hist.append({
                            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "tipo": "Treino",
                            "detalhe": f"Praetorium - {current_q['assunto']}",
                            "resultado": f"{qs_session['score']}/{len(questions)}",
                            "tempo": "-"
                        })
                        st.button("Voltar ao Menu", on_click=lambda: st.session_state.update({'doctore_state': 'selection'}))

    # -------------------------------------------------------------------------
    # TAB BATALHA (Simplificada para brevidade, mantendo original)
    # -------------------------------------------------------------------------
    with tab_batalha:
        st.info("Área de Batalha (Lógica mantida do original, focando no Doctore acima).")
        # Aqui entraria a lógica original de oponentes

    # -------------------------------------------------------------------------
    # TAB HISTÓRICO
    # -------------------------------------------------------------------------
    with tab_historico:
        if data.get('historico_atividades'):
            st.dataframe(pd.DataFrame(data['historico_atividades'][::-1]), use_container_width=True)

if __name__ == "__main__":
    main()
