# app_streamlit.py - Interface Híbrida Mavi.IA 5.0
# Versão Final: Suporte a Automação e FAQ com Relatórios Executivos
# Conectada ao backend v5.0 (langchain_agent + calc_logic)

import streamlit as st
import time

# Importa as funções do backend 5.0
from langchain_agent import criar_agente_extrator, extrair_dados_conversa, gerar_relatorio_tecnico

# --- 1. GESTÃO DE ESTADO (SESSION STATE) ---
def inicializar_session_state():
    """Define os valores padrão para a Mavi 5.0."""
    defaults = {
        # Classificação Principal
        "tipo_projeto": "automacao", # 'automacao' ou 'faq'
        "volume_mensal": 5000,
        
        # MODO AUTOMAÇÃO (Backoffice)
        "tempo_por_unidade_min": 5.0,
        "salario_hora_brl": 45.0,
        
        # MODO FAQ (Frontoffice)
        "custo_por_ticket_brl": 25.0, # Custo médio de um chamado humano
        "taxa_retencao_ia_percentual": 30.0, # % que a IA resolve sem humano
        
        # ARQUITETURA & CUSTOS (Comum)
        "modelo_llm": "gemini-2.5-flash",
        "tokens_input_por_unidade": 2000,
        "tokens_output_por_unidade": 500,
        "custo_infra_mensal_brl": 200.0, # n8n, Vector DB
        "custo_implementacao_capex_brl": 10000.0, # Custo do Projeto (Dev Hours)
        
        # RISCO & HITL
        "taxa_revisao_percentual": 20, # % de auditoria humana
        "tempo_revisao_min": 1.0,
        
        # Chat
        "messages": [{"role": "assistant", "content": "Olá! Sou Mavi 5.0, sua Arquiteta de Soluções. Vamos analisar um Robô de Automação ou um Chatbot de FAQ hoje?"}]
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Carrega o Pipeline Principal (apenas uma vez)
    if 'mavi_pipeline' not in st.session_state:
        with st.spinner("Inicializando Motor Mavi 5.0..."):
            st.session_state.mavi_pipeline = gerar_relatorio_tecnico()

# --- 2. APLICAÇÃO PRINCIPAL ---

def main():
    st.set_page_config(layout="wide", page_title="🤖 Mavi.IA | Framework 5.0", page_icon="🤖")
    inicializar_session_state()
    
    st.title("🤖 Mavi.IA: Governança & Viabilidade GenAI")
    st.caption("Framework 5.0: Análise Financeira, Técnica e Riscos para Projetos de Inteligência Artificial")
    st.markdown("---")

    col_chat, col_form = st.columns([1, 1.5], gap="large")

    # ==========================================
    # COLUNA 1: CHAT ANALYST (Arquiteto)
    # ==========================================
    with col_chat:
        st.subheader("💬 Consultoria Técnica")
        
        # Container aumentado para melhor leitura
        container_chat = st.container(height=700)
        
        # Exibe histórico
        with container_chat:
            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])

        # Input do Usuário
        if prompt := st.chat_input("Ex: 'Quero um FAQ para RH' ou 'Ler 500 contratos'"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with container_chat:
                st.chat_message("user").write(prompt)

            # Processamento da IA
            with st.spinner("Mavi analisando requisitos..."):
                # 1. Gera resposta conversacional
                agente_chat = criar_agente_extrator()
                historico_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                resposta_ai = agente_chat.invoke({"input": prompt, "chat_history": st.session_state.messages})
                
                st.session_state.messages.append({"role": "assistant", "content": resposta_ai.content})
                with container_chat:
                    st.chat_message("assistant").write(resposta_ai.content)

                # 2. Extração de Dados e Detecção de Modo (Automação vs FAQ)
                novos_dados = extrair_dados_conversa(historico_str + f"\nAI: {resposta_ai.content}")
                
                if novos_dados:
                    dados_dict = novos_dados.dict()
                    atualizou = False
                    
                    # Detecta mudança de tipo de projeto
                    if dados_dict.get("tipo_projeto") and dados_dict["tipo_projeto"] != st.session_state["tipo_projeto"]:
                         st.session_state["tipo_projeto"] = dados_dict["tipo_projeto"]
                         st.toast(f"Modo alterado para: {st.session_state['tipo_projeto'].upper()}", icon="🔄")
                         atualizou = True

                    # Atualiza outros campos se não forem nulos
                    for k, v in dados_dict.items():
                        if v is not None and k in st.session_state:
                            if st.session_state[k] != v:
                                st.session_state[k] = v
                                atualizou = True
                                
                    if atualizou:
                        st.toast("Parâmetros técnicos atualizados via Chat!", icon="✅")
                        time.sleep(1)
                        st.rerun()

    # ==========================================
    # COLUNA 2: FORMULÁRIO DINÂMICO
    # ==========================================
    with col_form:
        st.write("### ⚙️ Definição do Cenário")
        
        # Seletor de Modo (Sincronizado)
        # Nota: removida a atribuição direta que causava erro, o key lida com o session_state
        modo_label = st.radio(
            "Qual o objetivo do projeto?",
            ["Automação (Backoffice/FTE)", "FAQ/Agente (Frontoffice/Deflexão)"],
            index=0 if st.session_state["tipo_projeto"] == "automacao" else 1,
            horizontal=True,
            key="modo_radio_ui"
        )
        
        novo_tipo = "automacao" if "Automação" in modo_label else "faq"
        if novo_tipo != st.session_state["tipo_projeto"]:
            st.session_state["tipo_projeto"] = novo_tipo
            st.rerun()

        # Abas reorganizadas
        tab1, tab2, tab3 = st.tabs(["💰 Drivers de Valor (ROI)", "🏗️ Arquitetura & Custos", "🛡️ Risco (HITL)"])

        # --- ABA 1: ONDE GANHAMOS DINHEIRO? ---
        with tab1:
            c1, c2 = st.columns(2)
            # CORREÇÃO: Removida atribuição st.session_state[...] = widget(...)
            c1.number_input("Volume Mensal (Total):", min_value=1, key="volume_mensal")
            
            if st.session_state["tipo_projeto"] == "automacao":
                st.info("📉 **Modo Eficiência:** Foco em reduzir horas humanas (FTE).")
                c1.number_input("Tempo Humano por Tarefa (min):", min_value=0.1, key="tempo_por_unidade_min")
                c2.number_input("Custo Hora Equipe (BRL):", min_value=1.0, key="salario_hora_brl")
            else:
                st.info("🛡️ **Modo Deflexão:** Foco em evitar abertura de chamados.")
                c1.number_input("Custo Unitário do Ticket (BRL):", min_value=1.0, key="custo_por_ticket_brl")
                c2.slider("% Retenção Esperada (IA resolve):", 0, 100, key="taxa_retencao_ia_percentual")

        # --- ABA 2: QUANTO VAI CUSTAR? ---
        with tab2:
            c1, c2 = st.columns(2)
            c1.selectbox("Modelo LLM:", ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gpt-4o", "gpt-4o-mini"], key="modelo_llm")
            c2.number_input("Custo Fixo Infra (n8n/Vector DB):", min_value=0.0, key="custo_infra_mensal_brl", help="Custo mensal de servidores, licenças n8n ou banco vetorial.")
            
            c1.number_input("CAPEX (Implementação R$):", min_value=0.0, key="custo_implementacao_capex_brl", help="Custo único de desenvolvimento para cálculo de Payback.")
            
            st.markdown("---")
            st.caption("Estimativa de Consumo (Tokenomics)")
            cc1, cc2 = st.columns(2)
            cc1.number_input("Tokens Input (Contexto):", min_value=100, key="tokens_input_por_unidade")
            cc2.number_input("Tokens Output (Geração):", min_value=10, key="tokens_output_por_unidade")

        # --- ABA 3: QUAL O CUSTO DA FALHA? ---
        with tab3:
            st.caption("Human-in-the-Loop: O custo oculto da GenAI")
            c1, c2 = st.columns(2)
            
            if st.session_state["tipo_projeto"] == "automacao":
                c1.slider("% de Auditoria/Revisão Humana:", 0, 100, key="taxa_revisao_percentual")
                c2.number_input("Tempo para Revisar (min):", min_value=0.1, key="tempo_revisao_min")
            else:
                st.warning("No modo FAQ, o 'erro' é considerado como um chamado não deflexionado (já calculado na taxa de retenção).")
                st.caption("Ajuste a % de Retenção na Aba 1 para simular a qualidade da IA.")

        # --- BOTÃO DE AÇÃO ---
        st.markdown("---")
        if st.button("🚀 Gerar Relatório Executivo & ROI", type="primary", use_container_width=True):
            
            # Montagem do Payload Completo
            inputs_totais = {
                "bloco_1": {
                    "tipo_projeto": st.session_state["tipo_projeto"],
                    "volume_mensal": st.session_state["volume_mensal"],
                    "tempo_por_unidade_min": st.session_state["tempo_por_unidade_min"],
                    "salario_hora_brl": st.session_state["salario_hora_brl"],
                    "custo_por_ticket_brl": st.session_state["custo_por_ticket_brl"],
                },
                "bloco_2": {
                    "modelo_llm": st.session_state["modelo_llm"],
                    "tokens_input_por_unidade": st.session_state["tokens_input_por_unidade"],
                    "tokens_output_por_unidade": st.session_state["tokens_output_por_unidade"],
                    "custo_infra_mensal_brl": st.session_state["custo_infra_mensal_brl"],
                    "custo_implementacao_capex_brl": st.session_state["custo_implementacao_capex_brl"]
                },
                "bloco_3": {
                    "taxa_revisao_percentual": st.session_state.get("taxa_revisao_percentual", 0),
                    "tempo_revisao_min": st.session_state.get("tempo_revisao_min", 0),
                    "taxa_retencao_ia_percentual": st.session_state.get("taxa_retencao_ia_percentual", 0)
                }
            }
            
            with st.spinner("Mavi 5.0 analisando viabilidade econômica e gerando relatório..."):
                try:
                    resultado = st.session_state.mavi_pipeline.invoke(inputs_totais)
                    st.success("✅ Relatório Executivo Gerado!")
                    
                    # Exibe o relatório em um container com borda para destacar o formato "Papel"
                    with st.container(border=True):
                        st.markdown(resultado.content)
                        
                except Exception as e:
                    st.error(f"Erro na execução da análise: {e}")

if __name__ == "__main__":
    main()
