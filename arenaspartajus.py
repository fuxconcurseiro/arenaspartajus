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

# Arquivos de Imagem
HERO_IMG_FILE = "Arena_Spartajus_Logo_3.jpg"
USER_AVATAR_FILE = "fux_concurseiro.png"
LOGO_FILE = "logo_spartajus.jpg"  # Adicionado de volta
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

# ESTILIZAÇÃO GERAL
st.markdown("""
    <style>
    .stApp { background-color: #FFFFF0; color: #333333; }
    .stMarkdown, .stText, p, label, .stDataFrame, .stExpander { color: #4A4A4A !important; }
    h1, h2, h3 { color: #8B4513 !important; font-family: 'Georgia', serif; text-shadow: none; }
    [data-testid="stSidebar"] { background-color: #FFDEAD; border-right: 2px solid #DEB887; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #5C4033 !important; }
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div, .stDateInput > div > div > input { background-color: #FFFFFF; color: #333333; border: 1px solid #DEB887; }
    .stButton>button { background-color: #FFDEAD; color: #5C4033; border: 1px solid #8B4513; border-radius: 6px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: all 0.3s; }
    .stButton>button:hover { background-color: #FFE4C4; color: #000000; border-color: #A0522D; transform: scale(1.02); }
    .battle-card { background-color: #FFF8DC; border: 2px solid #DAA520; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); text-align: center; }
    .battle-card.locked { filter: grayscale(100%); opacity: 0.6; border-color: #555; }
    .battle-card.victory { border-color: #228B22; background-color: #F0FFF0; }
    .battle-card.defeat { border-color: #B22222; background-color: #FFF0F0; }
    .stat-box { background-color: #FFFFFF; border: 1px solid #DEB887; border-radius: 8px; padding: 8px; text-align: center; margin-bottom: 8px; }
    .stat-value { font-size: 1.3em; font-weight: bold; color: #8B4513; }
    .stat-label { font-size: 0.75em; color: #666; text-transform: uppercase; }
    .stat-header { font-size: 1.1em; font-weight: bold; color: #5C4033; margin-top: 15px; margin-bottom: 10px; border-bottom: 1px dashed #8B4513; }
    .doctore-card, .master-card { background-color: #FFF; border: 4px double #8B4513; border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px; }
    .master-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.15); border-color: #DAA520; }
    .feedback-box { padding: 15px; border-radius: 5px; margin-top: 15px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. CONFIGURAÇÃO DE DADOS (MERGE SEGURO)
# -----------------------------------------------------------------------------
DEFAULT_ARENA_DATA = {
    "arena_stats": {"total_questoes": 0, "total_acertos": 0, "total_erros": 0},
    "progresso_arena": {"fase_maxima_desbloqueada": 1, "fases_vencidas": []},
    "historico_atividades": []
}

# -----------------------------------------------------------------------------
# 4. BASE DE DADOS (OPONENTES)
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
        "dificuldade": "Desafio Inicial", "max_tempo": 30, "max_erros": 5
    },
    {
        "id": 3, "nome": "Leproso", "descricao": "A doença que corrói a alma. Vença ou seja consumido.",
        "avatar_url": get_avatar_image("leproso.jpg", "https://img.icons8.com/color/96/zombie.png"),
        "img_vitoria": get_avatar_image("vitoria_leproso.jpg", "https://img.icons8.com/color/96/clean-hands.png"),
        "img_derrota": get_avatar_image("derrota_leproso.jpg", "https://img.icons8.com/color/96/hospital.png"),
        "link_tec": "https://www.tecconcursos.com.br/caderno/Q5rIWI",
        "dificuldade": "Desafio Inicial", "max_tempo": 30, "max_erros": 5
    }
]

# -----------------------------------------------------------------------------
# 5. BASE DE DADOS HIERÁRQUICA (DOCTORE)
# -----------------------------------------------------------------------------
DOCTORE_DB = {
    "praetorium": {
        "nome": "Praetorium Legislativus", "descricao": "O Guardião das Leis e do Processo Legislativo.", "imagem": "praetorium.jpg", 
        "materias": {
            "Direito Constitucional": {
                "Conceito e Fontes": [
                     {"id": 1, "texto": "Alguns doutrinadores não fazem distinção entre estado de direito e estado de direito democrático. Outros, porém, afirmam que essa expressão representaria até mesmo uma contradição, já que haveria estados de direito não necessariamente democráticos.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE (CESPE) / 2006 / CL DF"},
                     {"id": 2, "texto": "O DF já figurou como capital da União em constituições anteriores, porém, na atualidade, a capital federal é o Distrito Federal.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE (CESPE) / 2006 / CL DF<br><br><strong>Texto Original Correto:</strong> ...a capital federal é Brasília.<br><br><strong>Análise:</strong> Confusão entre o ente federativo (DF) e a capital (Brasília)."}
                ],
                "Histórico das Constituições no Brasil": [
                    {"id": 3, "texto": "A Constituição de 1934 foi a primeira Constituição brasileira a prever a existência dos direitos sociais.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE (CESPE) / 2021 / ALECE"},
                    {"id": 4, "texto": "A Constituição de 1937 tratou expressamente da função social da propriedade...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF<br><br><strong>Texto Original:</strong> A Constituição de 1937 não tratou da função social da propriedade.<br><br><strong>Análise:</strong> A Carta de 1937 omitiu este princípio."},
                    {"id": 5, "texto": "A limitação das tarifas segundo o critério da justa remuneração do capital foi princípio constitucional inscrito nas constituições de 1934, 1937, 1946 e 1969...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 6, "texto": "A Constituição de 1988 alterou profundamente o domínio das águas no Brasil, que passou a ser público dos estados e da União...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN<br><br><strong>Análise:</strong> As águas superficiais que não atravessam fronteiras pertencem aos Estados."},
                    {"id": 7, "texto": "A escassez de recursos externos provocada pela Segunda Guerra Mundial impediu a implantação de modelos alternativos...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"}
                ],
                "Constituição: Conceito, Estrutura, Supremacia e Classificação": [
                    {"id": 8, "texto": "No que concerne a conteúdo, a constituição que estabelece preceitos cuja matéria não é constitucional classifica-se como material.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2021 / ALECE<br><br><strong>Análise:</strong> Classifica-se como formal."},
                    {"id": 9, "texto": "A constituição promulgada resulta do trabalho de uma assembleia nacional constituinte eleita pelo povo...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2021 / ALECE"},
                    {"id": 10, "texto": "Adotando-se a nomenclatura utilizada por Alexandre de Moraes, é correto afirmar que a Constituição brasileira é... sintética quanto à extensão.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF<br><br><strong>Análise:</strong> A CF/88 é analítica."},
                    {"id": 11, "texto": "A Constituição, lei que contém todas as normas fundamentais do Estado, sobrepõe-se a todas as demais normas jurídicas...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF"},
                    {"id": 12, "texto": "No sistema jurídico brasileiro, os tratados ou convenções internacionais estão hierarquicamente superiores à autoridade normativa da Constituição...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Tratados são subordinados à Constituição (salvo DH com quórum qualificado)."},
                    {"id": 13, "texto": "Em determinado conflito entre uma norma constitucional e outra norma infraconstitucional... pode-se optar tanto pela tese da simples revogação...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 14, "texto": "Como na própria Constituição da República estão previstas as formas pelas quais ela pode ser validamente alterada, é juridicamente correto classificá-la como constituição de tipo flexível.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> A CF/88 é rígida devido ao processo dificultoso de emenda."}
                ],
                "Dos Princípios Fundamentais da Constituição": [
                    {"id": 15, "texto": "A Constituição Federal de 1988 define o Brasil como Estado democrático de direito...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2024 / CM Maceió"},
                    {"id": 16, "texto": "Segundo o STF, a livre iniciativa é um fim em si mesmo...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2024 / CM Maceió<br><br><strong>Análise:</strong> A livre iniciativa deve conviver com outros valores constitucionais."},
                    {"id": 17, "texto": "A República Federativa do Brasil, constituída como Estado democrático de direito, visa garantir o pleno exercício dos direitos e garantias fundamentais...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)"},
                    {"id": 18, "texto": "O princípio jurídico da dignidade da pessoa humana não orienta os objetivos dos sistemas de direito considerados humanizados.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> A dignidade é o núcleo axiológico central."},
                    {"id": 19, "texto": "As relações internacionais da República Federativa do Brasil regem-se pelo princípio da autodeterminação dos povos.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2012 / TL (CAM DEP)"},
                    {"id": 20, "texto": "Os princípios que regem o Brasil nas suas relações internacionais incluem a cooperação entre os povos para o progresso da humanidade e a vedação de asilo político.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2012 / AL (CAM DEP)<br><br><strong>Análise:</strong> O Brasil rege-se pela CONCESSÃO de asilo político."},
                    {"id": 21, "texto": "Entre os fundamentos do Estado Democrático de Direito consagrados pela Carta de 1988 estão a soberania, a dignidade da pessoa humana e o pluralismo político.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 22, "texto": "A mitigação dos direitos humanos é um dos componentes essenciais na ação do Brasil...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> O Brasil busca a prevalência dos direitos humanos."},
                    {"id": 23, "texto": "Em suas relações internacionais, o Brasil deve orientar-se por princípios que fortaleçam os direitos humanos...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN"}
                ],
                "Dos Direitos e Deveres Individuais e Coletivos": [
                    {"id": 501, "texto": "O texto constitucional garante o livre exercício de todo e qualquer trabalho, não havendo óbice para que a lei estabeleça requisitos...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2024 / CM Maceió"},
                    {"id": 502, "texto": "Se um servidor público federal incorporar ao seu patrimônio, de forma lícita, certa vantagem pessoal... tal lei, nesse caso, será considerada constitucional...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / TL (CAM DEP)<br><br><strong>Análise:</strong> Viola o direito adquirido."},
                    {"id": 503, "texto": "No âmbito judicial e administrativo, a todos são assegurados a razoável duração do processo...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)"},
                    {"id": 504, "texto": "Na esfera judicial, é imprescindível a prévia oitiva do investigado para que seja quebrado seu sigilo bancário...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2011 / ALES<br><br><strong>Análise:</strong> O contraditório é diferido; a oitiva prévia é dispensável."},
                    {"id": 505, "texto": "Um deputado distrital propôs projeto de lei... O projeto em tela poderia ser considerado materialmente inconstitucional, já que obriga a filiação a uma associação.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF"},
                    {"id": 506, "texto": "A inviolabilidade do domicílio foi elevada ao patamar de direito fundamental... mesmo à noite, desde que munida de mandado judicial, admite-se o ingresso...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF<br><br><strong>Análise:</strong> Mandado judicial somente durante o dia."},
                    {"id": 507, "texto": "Qualquer pessoa pode exigir dos órgãos públicos informações que sejam do seu interesse particular...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF"},
                    {"id": 508, "texto": "O registro civil de nascimento e a certidão de óbito... são de obtenção gratuita a todos os brasileiros...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF<br><br><strong>Análise:</strong> Gratuidade constitucional para os reconhecidamente pobres."},
                    {"id": 509, "texto": "Além da indenização por dano material, moral ou à imagem, é assegurado o direito de resposta, proporcional ao agravo.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 510, "texto": "Consoante dispositivos constitucionais expressos, a pena deve ser cumprida em estabelecimentos distintos... independentemente do valor do patrimônio transferido.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> A obrigação limita-se ao valor do patrimônio transferido."},
                    {"id": 511, "texto": "O direito adquirido compõe o rol das cláusulas pétreas, não podendo, portanto, ser prejudicado ou violado.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 512, "texto": "O princípio constitucional segundo o qual todos são iguais perante a lei... veda, de forma absoluta, a possibilidade de qualquer tratamento diferenciado...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> A isonomia material permite distinções."},
                    {"id": 513, "texto": "O direito constitucional de livre manifestação do pensamento não exclui a punição penal... para divulgação pornográfica ou obscena...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 514, "texto": "Sob a vigência da Constituição... O juízo competente condenou o soldado à morte... Nessa situação, foi ilícita a condenação, dado que a Constituição veda a pena de morte em qualquer hipótese.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> A CF admite pena de morte em caso de guerra declarada."},
                    {"id": 515, "texto": "A chamada cláusula de reserva jurisdicional consiste na possibilidade de que um dos poderes pratique ato de invasão domiciliar.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 516, "texto": "Tratamento desumano e tortura não são admitidos, salvo em situações de extrema comoção interna ou estado de sítio.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Tortura não é admitida em hipótese alguma."},
                    {"id": 517, "texto": "O direito à vida diz respeito a um projeto de continuidade, dignidade e subsistência.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 518, "texto": "A cidadania brasileira crescentemente tem demandado novas formas de representação, sendo, contudo, vedada a implementação de quotas...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN<br><br><strong>Análise:</strong> Ações afirmativas (quotas) são constitucionais."},
                    {"id": 519, "texto": "Apesar de toda a ação dos movimentos brasileiros... a constituinte de 1988 não incluiu, na Constituição da República, a expressa proibição de discriminação por orientação sexual.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN"},
                    {"id": 520, "texto": "O preso será informado de seus direitos e poderá permanecer calado, exceto se a prisão acontecer em flagrante delito...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN<br><br><strong>Análise:</strong> O direito ao silêncio aplica-se também ao flagrante."},
                    {"id": 521, "texto": "A obtenção de certidões em repartições públicas... não depende do pagamento de taxas.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN"},
                    {"id": 522, "texto": "Consoante dispositivos constitucionais expressos... podendo a pena passar da pessoa do condenado nos casos de multa pecuniária.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Princípio da intranscendência da pena aplica-se à multa."}
                ],
                "Direitos Sociais e dos Trabalhadores": [
                    {"id": 601, "texto": "A jornada de seis horas para o trabalho realizado em turnos ininterruptos de revezamento é absoluta, não podendo ser aumentada ou reduzida...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> Pode ser alterada por negociação coletiva."},
                    {"id": 602, "texto": "A CF assegura expressamente a igualdade de direitos entre o trabalhador com vínculo empregatício permanente e o trabalhador avulso.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2012 / AL (CAM DEP)"},
                    {"id": 603, "texto": "Os direitos sociais, diferentemente das liberdades negativas, correspondem a uma prestação positiva do Estado...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF"},
                    {"id": 604, "texto": "Seria constitucional uma lei que determinasse que, no serviço público, a remuneração do serviço extraordinário fosse apenas 30% superior...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2003 / AL (CAM DEP)<br><br><strong>Análise:</strong> O adicional deve ser de no mínimo 50%."},
                    {"id": 605, "texto": "Tendo como fundamentos a dignidade da pessoa humana e os valores sociais do trabalho... cabe ao Estado brasileiro... definir os patamares mínimos de proteção...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 606, "texto": "Os brasileiros que trabalham como empregados domésticos na embaixada do país X... têm seus contratos de trabalho regidos pela legislação do país representado...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Aplica-se a legislação brasileira (Lex Loci Executionis)."},
                    {"id": 607, "texto": "A ação, quanto aos créditos resultantes das relações de trabalho, tem prazo prescricional de cinco anos...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"}
                ],
                "Direitos Coletivos dos Trabalhadores": [
                    {"id": 608, "texto": "A criação de sindicatos independe de autorização estatal... sendo permitido ao sindicato que represente a mesma categoria profissional abranger a mesma base territorial de outro...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> O Brasil adota a unicidade sindical."},
                    {"id": 609, "texto": "As negociações coletivas de trabalho devem contar obrigatoriamente com a participação dos sindicatos.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2012 / AL (CAM DEP)"},
                    {"id": 610, "texto": "A flexibilização da legislação do trabalho... tem, entre seus fundamentos, a prevalência do acordo individual sobre o coletivo, dispensando a legitimidade da representação sindical...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Exige-se participação sindical para flexibilização."},
                    {"id": 611, "texto": "O direito de greve é coletivo, tem como titular um grupo organizado de trabalhadores e pode ser caracterizado como instrumento de defesa.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"}
                ],
                "Nacionalidade": [
                    {"id": 701, "texto": "Se um casal formado por um cidadão argentino e uma cidadã canadense for contratado pela República do Uruguai para prestar serviços em representação consular desse país no Brasil... tal filho será considerado estrangeiro...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / TL (CAM DEP)<br><br><strong>Análise:</strong> Os pais não estão a serviço de seus países de origem, logo o filho é brasileiro nato (jus soli)."},
                    {"id": 702, "texto": "O indivíduo que, nascido no estrangeiro, de pai brasileiro ou mãe brasileira, venha a residir no Brasil, ainda menor, passa a ser considerado brasileiro nato...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2011 / ALECE"},
                    {"id": 703, "texto": "A vigente Constituição brasileira garante aos portugueses com residência permanente no país... os direitos inerentes ao brasileiro nato...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Garante direitos de brasileiro naturalizado."},
                    {"id": 704, "texto": "Nacionalidade é um conceito mais amplo que o de cidadania. Por conseguinte, pressupõe-se que todo cidadão brasileiro é titular da nacionalidade brasileira...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN"},
                    {"id": 705, "texto": "A Constituição assegura a igualdade de direitos entre brasileiros natos e naturalizados, não havendo impedimento para que um brasileiro naturalizado ocupe o cargo de Ministro do Tribunal Superior Eleitoral (TSE), mesmo que na vaga destinada a Ministro oriundo do Supremo Tribunal Federal (STF).", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> Cargo de Ministro do STF é privativo de nato."},
                    {"id": 706, "texto": "O cargo de tenente do Exército somente pode ser ocupado por brasileiro nato.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2012 / AL (CAM DEP)"},
                    {"id": 707, "texto": "O brasileiro naturalizado pode ser eleito deputado federal, mas não poderá ser eleito senador, pois o cargo de senador da República é privativo de brasileiro nato.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2011 / ALECE<br><br><strong>Análise:</strong> Pode ser Senador, só não pode ser Presidente do Senado."},
                    {"id": 708, "texto": "A CF exige que determinados cargos eletivos sejam ocupados por brasileiro nato... Nesse contexto, um brasileiro naturalizado ou português equiparado poderá concorrer a cargo de deputado federal ou senador...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2021 / ALECE"},
                    {"id": 709, "texto": "A atual Constituição da República veda expressamente que o brasileiro nato perca a nacionalidade brasileira...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> O nato pode perder a nacionalidade em caso de aquisição voluntária de outra."}
                ],
                "Extradição, Deportação, Expulsão e Banimento": [
                    {"id": 801, "texto": "João, brasileiro nato, durante viagem a determinado país estrangeiro, cometeu um crime... João não poderá ser extraditado pelo Brasil.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)"},
                    {"id": 802, "texto": "Em nenhuma hipótese, o Brasil concede a extradição de brasileiros natos, salvo se comprovado seu envolvimento em tráfico ilícito...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> A exceção do tráfico aplica-se apenas aos naturalizados."},
                    {"id": 803, "texto": "Há proibição, no Brasil, de extradição de estrangeiro por crime político ou de opinião.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 804, "texto": "A extradição de cidadão brasileiro naturalizado somente pode ser concedida em caso de crime comum praticado antes da naturalização; se o crime for de tráfico ilícito... a prática também deve ser anterior...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> Tráfico de drogas permite extradição a qualquer tempo."}
                ],
                "União: Bens e Competências": [
                     {"id": 901, "texto": "É competência comum da União, dos estados, do Distrito Federal e dos municípios fomentar a produção agropecuária.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2021 / ALECE"},
                     {"id": 902, "texto": "O estado pode legislar sobre navegação lacustre e fluvial, desde que lei ordinária federal específica o autorize.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2021 / ALECE<br><br><strong>Análise:</strong> Exige Lei Complementar."},
                     {"id": 903, "texto": "No que concerne à distribuição de competências... o chamado critério do predominante interesse dispõe que se o assunto for de predominante interesse regional ou estadual, a competência é do estado federado...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2021 / ALECE"},
                     {"id": 904, "texto": "Apesar de se verificar significativa atuação da União, por meio do IPHAN... tal atividade é atribuição exclusiva da União...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> É competência comum."},
                     {"id": 905, "texto": "O serviço postal está inserido no rol constitucional de competência legislativa privativa da União...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)"},
                     {"id": 906, "texto": "Fere o pacto federativo a edição de lei complementar, pelo Congresso Nacional, que autorize os estados a legislar sobre questões específicas...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> A CF autoriza expressamente essa delegação."},
                     {"id": 907, "texto": "Se um estado da Federação editar norma que proíba revista íntima... tal norma... será inconstitucional, pois tratará de matéria de competência privativa da União.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)"},
                     {"id": 908, "texto": "Na hipótese de lei estadual que disponha sobre a comercialização de produtos por meio de embalagens reutilizáveis, entende o STF haver inconstitucionalidade formal...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> O STF entende ser competência concorrente (defesa do consumidor/meio ambiente)."},
                     {"id": 909, "texto": "A legislação sobre a proteção e defesa da saúde é... de competência tanto federal como estadual...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)"},
                     {"id": 910, "texto": "Conforme dispositivo da CF, as terras ocupadas, em passado remoto, por população indígena são bens de propriedade da comunidade indígena.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / TL (CAM DEP)<br><br><strong>Análise:</strong> São bens da União."},
                     {"id": 911, "texto": "Lei distrital que submeta as desapropriações, no âmbito do Distrito Federal, à aprovação prévia da Câmara Legislativa será inconstitucional...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / TL (CAM DEP)"},
                     {"id": 912, "texto": "É da União a competência privativa para legislar sobre previdência social, sendo vedada a competência concorrente dos estados para instituir regime próprio.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2011 / ALECE<br><br><strong>Análise:</strong> Competência concorrente."},
                     {"id": 913, "texto": "No âmbito da competência legislativa concorrente, sobrevindo lei federal que contenha normas gerais, ficará suspensa a eficácia de lei estadual preexistente...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2011 / ALES"},
                     {"id": 914, "texto": "Seria constitucional lei distrital que fixasse em 70 km/h a velocidade máxima permitida nas vias urbanas do DF...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF<br><br><strong>Análise:</strong> Trânsito é competência privativa da União."},
                     {"id": 915, "texto": "Compete à União organizar e manter a Polícia Civil, a Polícia Militar e o Corpo de Bombeiros Militar do DF...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF"},
                     {"id": 916, "texto": "A Constituição da República determina que, no âmbito da legislação sobre proteção à infância, a competência da União é ampla e irrestrita...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF<br><br><strong>Análise:</strong> Limita-se a normas gerais."},
                     {"id": 917, "texto": "É competência comum entre União, estados, DF e municípios a proteção e garantia das pessoas portadoras de necessidades especiais.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF"},
                     {"id": 918, "texto": "A competência para legislar sobre licitação é da União... cabendo a cada ente editar suas próprias normas gerais sobre licitação de forma autônoma.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Normas gerais são competência da União."},
                     {"id": 919, "texto": "Considerando um prefeito que submeteu projeto de lei prevendo a condição de crime eleitoral para candidato analfabeto: Compete privativamente à União legislar sobre o direito eleitoral.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                     {"id": 920, "texto": "A Constituição da República estabelece que é competência privativa da União estabelecer e implantar política de educação para a segurança do trânsito.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Competência comum."},
                     {"id": 921, "texto": "Os estados e o Distrito Federal (DF) podem legislar concorrentemente sobre direito tributário, financeiro, penitenciário, econômico e urbanístico.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN"},
                     {"id": 922, "texto": "Em uma determinada fazenda, localizada em rio que banha mais de um estado-membro... a União dispôs irregularmente dos bens públicos, pois tais terrenos pertencem aos Estados.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN<br><br><strong>Análise:</strong> Rios interestaduais e seus terrenos marginais são da União."},
                     {"id": 923, "texto": "A faixa de fronteira é considerada área indispensável à segurança nacional e corresponde à faixa interna de 150 km de largura...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN"},
                     {"id": 924, "texto": "Compete concorrentemente à União e aos estados legislar sobre o regime dos portos e a navegação...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN<br><br><strong>Análise:</strong> Competência privativa da União."},
                     {"id": 925, "texto": "Tratando-se de áreas urbanas ou urbanizáveis, as construções e atividades civis realizadas nos terrenos de marinha ficam sujeitas à regulamentação e à tributação municipais...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN"}
                ],
                "Estados Federados - Organização, Competências, Bens": [
                    {"id": 950, "texto": "Não afrontaria a CF dispositivo de Constituição estadual que previsse que a ausência do país do governador... por qualquer prazo, dependeria de prévia licença...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / TL (CAM DEP)<br><br><strong>Análise:</strong> Afrontaria a simetria. Licença só para ausências superiores a 15 dias."},
                    {"id": 951, "texto": "Incorreria em inconstitucionalidade lei distrital que reservasse para mulheres metade das vagas abertas nos concursos públicos para oficial do Corpo de Bombeiros Militar do DF.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2006 / CL DF"},
                    {"id": 952, "texto": "Um estado-membro da Federação editou... medida provisória tornando obrigatório o uso de cinto de segurança... A lei não padece de vício de inconstitucionalidade...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Trânsito é competência privativa da União."},
                    {"id": 953, "texto": "A União, os estados e o DF podem... estabelecer normas sobre a organização das polícias civis, cabendo à União... a primazia no que concerne à fixação das normas gerais...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 954, "texto": "Alterações constitucionais empreendidas... mantiveram no texto da Constituição da República as disposições que tornam defeso ao Estado conceder a empresas privadas a exploração dos serviços de gás canalizado...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN<br><br><strong>Análise:</strong> A concessão foi permitida pela EC 5/95."},
                    {"id": 955, "texto": "Caso fosse criado um novo estado federado, a partir da fusão dos estados de São Paulo, Minas Gerais e Rio de Janeiro... a sua assembleia legislativa não poderia ser formada por mais de cem deputados estaduais.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN"}
                ],
                "Municípios - Organização e Competências": [
                    {"id": 1001, "texto": "Além da competência para legislar sobre temas de interesse local, os municípios exercem competência suplementar nos casos em que possuem competência concorrente...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2024 / CM Maceió"},
                    {"id": 1002, "texto": "Cabe aos municípios prestar os serviços de coleta de resíduos sólidos... desde que haja expressa autorização em lei estadual...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2024 / CM Maceió<br><br><strong>Análise:</strong> A competência independe de autorização estadual."},
                    {"id": 1003, "texto": "A inviolabilidade do vereador por suas opiniões... possui abrangência restrita a seu respectivo município.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2021 / ALECE"},
                    {"id": 1004, "texto": "A autonomia municipal sempre foi plena na história constitucional brasileira...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> Até 1946 a autonomia era apenas nominal."},
                    {"id": 1005, "texto": "Será constitucional lei municipal que dispuser sobre a organização dos serviços funerários locais...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)"},
                    {"id": 1006, "texto": "As prescrições na Constituição Federal referentes à perda do mandato de governador não se aplicam ao prefeito...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> Aplicam-se por simetria."},
                    {"id": 1007, "texto": "A fixação do subsídio dos vereadores cabe à câmara municipal...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)"},
                    {"id": 1008, "texto": "Empregado remunerado em empresa pública estadual eleito vice-prefeito de determinado município poderá acumular a remuneração...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> Vice-prefeito não pode acumular."},
                    {"id": 1009, "texto": "A vocação sucessória dos cargos de prefeito e vice-prefeito põe-se no âmbito da autonomia política local...", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)"},
                    {"id": 1010, "texto": "Se um prefeito municipal cometer um crime comum... ele será julgado originalmente pelo juiz de direito da comarca local...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2014 / AL (CAM DEP)<br><br><strong>Análise:</strong> Julgado pelo TJ (2ª instância)."},
                    {"id": 1011, "texto": "O serviço de proteção do patrimônio histórico-cultural local é exemplo de serviço público explorado pelos municípios e pelo DF.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2011 / ALECE"},
                    {"id": 1012, "texto": "Lúcio, prefeito... O referido município possui 150 mil eleitores. A exemplo da eleição presidencial, a eleição referida... deverá ser realizada em dois turnos.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Exige-se mais de 200 mil eleitores para 2º turno."},
                    {"id": 1013, "texto": "A Constituição da República permite que os municípios instituam e arrecadem tributos de sua competência.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 1014, "texto": "Caso haja dois turnos para a eleição (de Prefeito), um será no primeiro domingo e o outro no segundo domingo de novembro...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> O segundo turno é no último domingo de outubro."},
                    {"id": 1015, "texto": "O município pode legislar sobre parcelamento do solo urbano.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 1016, "texto": "O município tem competência para legislar sobre quaisquer assuntos de interesse regional, desde que haja concordância dos municípios vizinhos.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Competência restrita ao interesse local."},
                    {"id": 1017, "texto": "Martins, vereador municipal do município Alfa... apresentou proposta legislativa de proteção de patrimônio histórico-cultural situado no município Beta. O tema... é de competência municipal.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 1018, "texto": "Compete aos municípios promover a proteção do patrimônio histórico-cultural local, sendo vedada, contudo, qualquer ação fiscalizadora federal e estadual...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> A fiscalização é concorrente."},
                    {"id": 1019, "texto": "A câmara municipal compõe-se de vereadores, cujo número é fixado proporcionalmente à população do respectivo município.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 1020, "texto": "A autonomia municipal na Constituição da República fundamenta-se na soberania dos municípios...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Municípios possuem autonomia, não soberania."},
                    {"id": 1021, "texto": "Nos termos da Constituição da República, a câmara de vereadores não é competente para apreciar matéria eleitoral nem matéria criminal.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)"},
                    {"id": 1022, "texto": "A posse do prefeito e do vice-prefeito ocorre no dia 1.º de fevereiro...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / AL (CAM DEP)<br><br><strong>Análise:</strong> Posse em 1º de janeiro."},
                    {"id": 1023, "texto": "No serviço público de interesse local, o serviço de transporte coletivo é competência exclusiva do Estado...", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> CEBRASPE / 2002 / SEN<br><br><strong>Análise:</strong> É competência municipal."}
                ],
                "Do Distrito Federal e dos Territórios": [],
                "Intervenção Federal e Estadual": [],
                "Disposições Gerais (Administração Pública)": [],
                "Dos Servidores Públicos": [],
                "Do Congresso Nacional": [],
                "Das Atribuições do Congresso Nacional": [],
                "Da Câmara dos Deputados": [],
                "Do Senado Federal": [],
                "Dos Deputados e Senadores": [],
                "Das Reuniões": [],
                "Das Comissões Parlamentares": [],
                "Da Emenda à Constituição": [],
                "Leis Ordinárias e Complementares": [],
                "Medidas Provisórias": [],
                "Leis Delegadas": [],
                "Fases do Processo Legislativo": [],
                "Questões Mescladas de Processo Legislativo": [],
                "Forças Armadas": [],
                "Segurança Pública": []
            }
        }
    },
    "enam_criscis": {
        "nome": "Enam Criscis", "descricao": "A Sabedoria da Toga. Mestre do Exame Nacional da Magistratura.", "imagem": "enam-criscis.png",
        "materias": {
            "Direitos Humanos": [{"id": 401, "texto": "A Corte Interamericana de Direitos Humanos admite a possibilidade de controle de convencionalidade das leis internas.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> Jurisprudência Corte IDH"}],
            "Direito Administrativo": [{"id": 402, "texto": "A responsabilidade civil do Estado por atos omissivos é, em regra, objetiva.", "gabarito": "Errado", "explicacao": "<strong>Metadados:</strong> Doutrina Majoritária<br><br><strong>Análise:</strong> Omissão gera responsabilidade subjetiva."}]
        }
    },
    "parquet_tribunus": {
        "nome": "Parquet Tribunus", "descricao": "O Defensor da Sociedade. Mestre das Promotorias de Justiça.", "imagem": "parquet.jpg",
        "materias": {
            "Direito Processual Coletivo": [{"id": 501, "texto": "O Ministério Público possui legitimidade para propor Ação Civil Pública visando a defesa de direitos individuais homogêneos, ainda que disponíveis, quando houver relevância social.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> Tema Repetitivo STJ"}],
            "Direito Penal": [{"id": 502, "texto": "Na ação penal pública condicionada, a representação do ofendido é condição de procedibilidade, mas pode ser retratada até o oferecimento da denúncia.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> Art. 25 CPP"}]
        }
    },
    "noel_autarquicus": {
        "nome": "Noel Autarquicus", "descricao": "O Guardião dos Municípios e Conselhos. Mestre da Administração Local.", "imagem": "noel.png",
        "materias": {
            "Direito Administrativo": [{"id": 601, "texto": "É constitucional a exigência de inscrição em conselho de fiscalização profissional para o exercício de cargos públicos cujas funções exijam qualificação técnica específica.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> Tema 999 STF"}],
            "Legislação Municipal": [{"id": 602, "texto": "Compete aos Municípios legislar sobre assuntos de interesse local, inclusive horário de funcionamento de estabelecimento comercial.", "gabarito": "Certo", "explicacao": "<strong>Metadados:</strong> Súmula Vinculante 38"}]
        }
    }
}

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
            
            # Garante que arena_v1_data existe
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

    # Atalhos e Proteção de Dados
    full_data = st.session_state['full_data']
    
    # Recupera ou inicializa a parte da Arena
    arena_data = full_data.get('arena_v1_data', DEFAULT_ARENA_DATA.copy())
    
    # Garante integridade das chaves
    if not isinstance(arena_data, dict): arena_data = DEFAULT_ARENA_DATA.copy()
    if "stats" not in arena_data: arena_data["stats"] = DEFAULT_ARENA_DATA["stats"].copy()
    if "progresso_arena" not in arena_data: arena_data["progresso_arena"] = DEFAULT_ARENA_DATA["progresso_arena"].copy()
    if "historico_atividades" not in arena_data: arena_data["historico_atividades"] = DEFAULT_ARENA_DATA["historico_atividades"].copy()

    full_data['arena_v1_data'] = arena_data
    stats = arena_data['stats']
    hist = arena_data['historico_atividades']

    # --- SIDEBAR ---
    with st.sidebar:
        # LOGO
        if os.path.exists(LOGO_FILE):
             st.image(LOGO_FILE, use_container_width=True)
        # AVATAR
        if os.path.exists(USER_AVATAR_FILE):
            st.image(USER_AVATAR_FILE, caption=TEST_USER, use_container_width=True)
        else:
            st.header(f"🏛️ {TEST_USER}")
            st.warning("Avatar não encontrado")
        
        if "Online" in st.session_state['status']:
            st.success(st.session_state['status'])
        else:
            st.error(st.session_state['status'])

        # --- DESEMPENHO GLOBAL ---
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

        # --- DESEMPENHO DIÁRIO ---
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
    # TAB 1: BATALHA
    # -------------------------------------------------------------------------
    with tab_batalha:
        st.markdown("### 🗺️ A Jornada do Gladiador")
        fase_max = arena_data['progresso_arena']['fase_maxima_desbloqueada']
        fases_vencidas = arena_data['progresso_arena']['fases_vencidas']

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
                            
                            # Atualiza a estrutura Arena com a chave correta
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
                            
                            # Salva e reatribui para garantir persistência
                            full_data['arena_v1_data'] = arena_data
                            
                            save_data(st.session_state['row_idx'], full_data)
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
                nicho = st.selectbox("1. Escolha a Matéria:", materias_disponiveis)
                
                # SELETOR DE ASSUNTO
                assuntos_disponiveis = list(master_data['materias'][nicho].keys())
                sub_nicho = st.selectbox("2. Escolha o Assunto:", assuntos_disponiveis)
                
                c1, c2 = st.columns(2)
                if c1.button("Iniciar Treino", type="primary", use_container_width=True):
                    # CARREGA QUESTÕES DO ASSUNTO ESPECÍFICO
                    qs = master_data['materias'][nicho][sub_nicho].copy()
                    if not qs:
                         st.warning("Ainda não há questões cadastradas para este tópico.")
                    else:
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
                        
                        # Lógica de Clique com Atualização Imediata
                        if c_c.button("✅ CERTO", use_container_width=True):
                            st.session_state.update({"doc_choice": "Certo", "doc_revealed": True})
                            
                            if q['gabarito'] == "Certo":
                                stats['total_acertos'] += 1
                                st.toast("Resposta Correta!", icon="✅")
                            else:
                                stats['total_erros'] += 1
                                if q not in ds['wrong_ids']: ds['wrong_ids'].append(q)
                                st.toast("Resposta Incorreta!", icon="❌")
                                
                            stats['total_questoes'] += 1
                            
                            full_data['arena_v1_data'] = arena_data
                            save_data(st.session_state['row_idx'], full_data)
                            st.rerun()

                        if c_e.button("❌ ERRADO", use_container_width=True):
                            st.session_state.update({"doc_choice": "Errado", "doc_revealed": True})
                            
                            if q['gabarito'] == "Errado":
                                stats['total_acertos'] += 1
                                st.toast("Resposta Correta!", icon="✅")
                            else:
                                stats['total_erros'] += 1
                                if q not in ds['wrong_ids']: ds['wrong_ids'].append(q)
                                st.toast("Resposta Incorreta!", icon="❌")
                                
                            stats['total_questoes'] += 1
                            full_data['arena_v1_data'] = arena_data
                            save_data(st.session_state['row_idx'], full_data)
                            st.rerun()
                    else:
                        acertou = (st.session_state['doc_choice'] == q['gabarito'])
                        if acertou: 
                            st.success(f"Correto! O gabarito é {q['gabarito']}.")
                        else: 
                            st.error(f"Errou! O gabarito é {q['gabarito']}.")
                        
                        st.markdown(f"<div class='feedback-box'><b>Justificativa:</b> {q['explicacao']}</div>", unsafe_allow_html=True)
                        if st.button("Próxima ➡️"):
                            st.session_state['doc_revealed'] = False
                            ds['idx'] += 1
                            st.rerun()
                else:
                    st.success("Treino Finalizado!")
                    st.write(f"Erros na rodada: {len(ds['wrong_ids'])}")
                    
                    hist.append({
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "tipo": "Doctore",
                        "detalhe": f"{master_data['nome']} ({ds['mode']})",
                        "resultado": f"{len(q_list)-len(ds['wrong_ids'])}/{len(q_list)} acertos",
                        "tempo": "-"
                    })
                    
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
