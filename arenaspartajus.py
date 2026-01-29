# -----------------------------------------------------------------------------
# 8. APP PRINCIPAL (MAIN LOOP) - COM SIDEBAR COMPLETA RESTAURADA
# -----------------------------------------------------------------------------
def main():
    # Inicializa estado de login
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    # --- FLUXO 1: NÃO LOGADO (Mostra Login) ---
    if not st.session_state['logged_in']:
        login_screen()
        return

    # --- FLUXO 2: LOGADO (Carrega Dados e Mostra App) ---
    current_user = st.session_state['user_id']
    user_name = st.session_state['user_name']

    # Carrega dados se ainda não carregou nesta sessão
    if 'arena_data' not in st.session_state:
        with st.spinner(f"Carregando dados de {user_name}..."):
            data, row, status = load_user_data(current_user)
            st.session_state['arena_data'] = data
            st.session_state['row_idx'] = row
            st.session_state['status'] = status

    arena_data = st.session_state['arena_data']
    
    # Garante estrutura mínima do JSON
    if "stats" not in arena_data: arena_data["stats"] = DEFAULT_ARENA_DATA["stats"].copy()
    if "progresso_arena" not in arena_data: arena_data["progresso_arena"] = DEFAULT_ARENA_DATA["progresso_arena"].copy()
    if "historico_atividades" not in arena_data: arena_data["historico_atividades"] = DEFAULT_ARENA_DATA["historico_atividades"].copy()
    
    stats = arena_data['stats']
    hist = arena_data['historico_atividades']

    # --- SIDEBAR (RESTAURADA COM CALENDÁRIO E CORES) ---
    with st.sidebar:
        if os.path.exists(USER_AVATAR_FILE):
            st.image(USER_AVATAR_FILE, width=100)
        else:
            st.header(f"🏛️ {user_name}")

        st.markdown(f"### Olá, {user_name}")
        st.caption(f"ID: {current_user}")
        
        # Botões de Controle
        c_refresh, c_logout = st.columns(2)
        if c_refresh.button("🔄"):
            st.cache_data.clear()
            del st.session_state['arena_data']
            st.rerun()
        if c_logout.button("🚪 Sair"):
            st.session_state.clear()
            st.rerun()
            
        st.divider()
        
        # --- 1. DESEMPENHO GLOBAL (ESTILO MENTOR) ---
        st.markdown("<div class='stat-header'>📊 Desempenho Global</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#006400'>{stats['total_acertos']}</div><div class='stat-label'>Acertos</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#8B0000'>{stats['total_erros']}</div><div class='stat-label'>Erros</div></div>""", unsafe_allow_html=True)
        
        st.markdown(f"""<div class='stat-box'><div class='stat-value'>{stats['total_questoes']}</div><div class='stat-label'>Total Geral</div></div>""", unsafe_allow_html=True)
        
        if stats['total_questoes'] > 0:
            perc = (stats['total_acertos'] / stats['total_questoes']) * 100
        else:
            perc = 0
        st.markdown(f"**Aproveitamento Geral:** {perc:.1f}%")
        st.progress(perc / 100)

        # --- 2. DESEMPENHO DIÁRIO (RESTAURADO) ---
        st.markdown("<div class='stat-header'>📅 Desempenho Diário</div>", unsafe_allow_html=True)
        
        # Seletor de Data
        selected_date = st.date_input("Filtrar Data:", datetime.now(), format="DD/MM/YYYY")
        
        # Cálculo Dinâmico
        daily_stats = calculate_daily_stats(hist, selected_date)
        
        d1, d2 = st.columns(2)
        d1.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#006400'>{daily_stats['acertos']}</div><div class='stat-label'>Acertos</div></div>""", unsafe_allow_html=True)
        d2.markdown(f"""<div class='stat-box'><div class='stat-value' style='color:#8B0000'>{daily_stats['erros']}</div><div class='stat-label'>Erros</div></div>""", unsafe_allow_html=True)
        
        st.markdown(f"""<div class='stat-box'><div class='stat-value'>{daily_stats['total']}</div><div class='stat-label'>Questões Hoje</div></div>""", unsafe_allow_html=True)
        
        if daily_stats['total'] > 0:
            d_perc = (daily_stats['acertos'] / daily_stats['total']) * 100
        else:
            d_perc = 0.0
        st.markdown(f"**Eficiência Diária:** {d_perc:.1f}%")
        st.progress(d_perc / 100)

    # --- HERO HEADER ---
    if os.path.exists(HERO_IMG_FILE):
        img_b64 = get_base64_of_bin_file(HERO_IMG_FILE)
        st.markdown(f"""
        <div class="full-width-hero" style="background-color: #FFF8DC; border-bottom: 4px solid #DAA520; display:flex; justify-content:center; height:250px; overflow:hidden;">
            <img src="data:image/jpg;base64,{img_b64}" style="height:100%; width:auto;">
        </div>
        """, unsafe_allow_html=True)

    # --- TABS PRINCIPAIS ---
    tab_batalha, tab_doctore, tab_historico = st.tabs(["Combates no Coliseum", "🦉 Doctore", "📜 Histórico"])

    # -------------------------------------------------------------------------
    # TAB 1: BATALHA (PAGINAÇÃO + BLOQUEIO VISUAL)
    # -------------------------------------------------------------------------
    with tab_batalha:
        st.markdown("### 🗺️ A Jornada do Gladiador")
        fase_max = arena_data['progresso_arena']['fase_maxima_desbloqueada']
        fases_vencidas = arena_data['progresso_arena']['fases_vencidas']

        # Paginação
        ITEMS_PER_PAGE = 3
        if 'coliseum_page' not in st.session_state: st.session_state['coliseum_page'] = 0
        total_pages = (len(OPONENTS_DB) - 1) // ITEMS_PER_PAGE + 1
        
        # Botões Navegação (Topo)
        c_prev, c_info, c_next = st.columns([1, 4, 1])
        with c_prev:
            if st.session_state['coliseum_page'] > 0:
                if st.button("⬅️ Anterior"): st.session_state['coliseum_page'] -= 1; st.rerun()
        with c_next:
            if st.session_state['coliseum_page'] < total_pages - 1:
                if st.button("Próximo ➡️"): st.session_state['coliseum_page'] += 1; st.rerun()

        start_idx = st.session_state['coliseum_page'] * ITEMS_PER_PAGE
        page_opponents = OPONENTS_DB[start_idx : start_idx + ITEMS_PER_PAGE]
        
        # Exibe página atual
        c_info.markdown(f"<div style='text-align:center; padding-top:10px;'>Página {st.session_state['coliseum_page'] + 1} de {total_pages}</div>", unsafe_allow_html=True)

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
            
            with c_info:
                st.markdown(f"### {opp['nome']}")
                st.markdown(f"*{opp['descricao']}*")
                
                if is_locked:
                    st.markdown("### 🔒 BLOQUEADO")
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
            
            # Status Image (Prepare-se / Vitória / Derrota)
            status_img = None
            if is_completed: status_img = opp['img_vitoria']
            elif is_current and st.session_state.get('last_result') == 'derrota' and st.session_state.get('last_opp_id') == opp['id']:
                status_img = opp['img_derrota']
            elif not is_locked:
                if os.path.exists(PREPARE_SE_FILE): status_img = PREPARE_SE_FILE
            
            if status_img: render_centered_image(status_img, width=400)
            st.markdown("</div>", unsafe_allow_html=True)

            # Formulário de Batalha
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

    # -------------------------------------------------------------------------
    # TAB 2: DOCTORE (100% FUNCIONAL)
    # -------------------------------------------------------------------------
    with tab_doctore:
        if 'doctore_state' not in st.session_state: st.session_state['doctore_state'] = 'selection'
        
        # 1. TELA DE SELEÇÃO
        if st.session_state['doctore_state'] == 'selection':
            cols = st.columns(2)
            for idx, (key, master) in enumerate(DOCTORE_DB.items()):
                with cols[idx % 2]:
                    with st.container():
                        st.markdown("<div class='master-card'>", unsafe_allow_html=True)
                        if master.get('imagem'): render_centered_image(master['imagem'])
                        st.markdown(f"### {master['nome']}")
                        st.markdown(f"*{master['descricao']}*")
                        if st.button(f"Treinar", key=f"sel_{key}"):
                            st.session_state['selected_master'] = key
                            st.session_state['doctore_state'] = 'training'
                            st.session_state['doctore_session'] = {"active": False, "questions": [], "idx": 0, "wrong_ids": [], "mode": "normal"}
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
        
        # 2. TELA DE TREINAMENTO
        elif st.session_state['doctore_state'] == 'training':
             if st.button("🔙 Voltar ao Panteão"):
                 st.session_state['doctore_state'] = 'selection'
                 st.rerun()
             
             master_key = st.session_state['selected_master']
             master = DOCTORE_DB.get(master_key)
             if not master: st.rerun()
             
             st.markdown(f"## {master['nome']}")
             st.markdown("---")
             
             if 'doctore_session' not in st.session_state:
                 st.session_state['doctore_session'] = {"active": False, "questions": [], "idx": 0}
             ds = st.session_state['doctore_session']
             
             # Filtros de Matéria
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
             
             # Execução do Quiz
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
                             
                             stats['total_questoes'] += 1
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
                     
                     # Botões Finais
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
