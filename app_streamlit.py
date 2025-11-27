# app_streamlit.py - REVISADO E CORRIGIDO PARA MAPEAR VARIÁVEIS

import streamlit as st
import pandas as pd
# Importa a cadeia de orquestração (garanta que o arquivo exista!)
from langchain_agent import criar_pipeline_mavi 
import time # Usado para o spinner

# --- 1. FUNÇÃO PRINCIPAL ---

def main():
    st.set_page_config(layout="wide", page_title="🤖 Mavi.IA | Engenharia de Viabilidade")
    
    st.title("🤖 Mavi.IA: Engenharia de Viabilidade de Projetos de IA")
    st.markdown("---")
    
    # Instancia o pipeline LangChain (isso só funciona se a API Key estiver carregada)
    # Colocamos a instância dentro de uma função para garantir que só seja criada uma vez
    if 'mavi_chain' not in st.session_state:
        st.session_state.mavi_chain = criar_pipeline_mavi()

    # Dicionários para armazenar todos os inputs (usaremos dicionários locais)
    inputs_bloco_1 = {}
    inputs_bloco_2 = {}
    inputs_bloco_3 = {}

    # Cria a estrutura de abas para organizar os inputs
    tab_blocos = st.tabs(["📊 Bloco 1: Financeiro/Operacional (AS-IS)", 
                          "⚙️ Bloco 2: Custo IA (TO-BE)", 
                          "⚠️ Bloco 3: Risco e Calibragem"])
    
    # --- 2. COLETA DE INPUTS ---

    with tab_blocos[0]:
        st.header("Bloco 1: AS-IS (Custo Humano e Risco Evitável)")
        col1, col2 = st.columns(2)
        
        # Inputs Operacionais
        inputs_bloco_1["volume_mensal"] = col1.number_input("Volume Mensal (V):", min_value=1, value=2000, help="Total de vezes que a tarefa é executada no mês.")
        inputs_bloco_1["tempo_por_unidade_min"] = col1.number_input("Tempo Humano por Unidade (min):", min_value=0.1, value=3.0, help="Tempo gasto pelo colaborador (em minutos).")
        
        # Inputs Financeiros (Chave Crítica: Salário)
        inputs_bloco_1["salario_hora_brl"] = col2.number_input("Salário/Hora (BRL):", min_value=1.0, value=45.0, help="Custo total por hora do colaborador (incluindo encargos).")
        
        # Inputs de Risco Humano Monetizado
        st.subheader("Risco Humano Evitado (Monetização)")
        inputs_bloco_1["risco_erro_humano_percentual"] = st.slider("Taxa de Erro Humano (%) - R_erro_humano:", 
                                                                   min_value=0, max_value=100, value=5, help="Percentual de vezes que o humano comete um erro crítico.")
        inputs_bloco_1["custo_erro_critico_brl_unidade"] = st.number_input("Custo de Erro Crítico (BRL/Unidade):", min_value=0.0, value=500.0, help="Custo médio de retificação ou multa por um erro crítico.")

    with tab_blocos[1]:
        st.header("Bloco 2: TO-BE (Custo de Execução da IA)")
        col1, col2 = st.columns(2)
        
        # Inputs de Modelo e Tokens
        # Ajuste: Garantimos que 'gemini-2.5-flash' seja a primeira opção, pois é o LLM que estamos usando
        inputs_bloco_2["modelo_llm"] = col1.selectbox("Modelo LLM:", options=["gemini-2.5-flash", "gpt-4o-mini", "gpt-4o"], index=0, help="Modelo usado para a solução (afeta o custo dinâmico).")
        inputs_bloco_2["tokens_input_por_unidade"] = col1.number_input("Tokens Input (T_in):", min_value=1, value=3000, help="Média de tokens de contexto por unidade processada.")
        inputs_bloco_2["tokens_output_por_unidade"] = col1.number_input("Tokens Output (T_out):", min_value=1, value=300, help="Média de tokens gerados na resposta/JSON.")
        
        # Inputs de Infraestrutura e OCR
        inputs_bloco_2["paginas_por_unidade"] = col2.number_input("Páginas/Unidade (OCR):", min_value=0.0, value=4.0, help="Média de páginas escaneadas/analisadas por OCR por unidade.")
        inputs_bloco_2["custo_hosting_mensal_brl"] = col2.number_input("Custo Hosting Mensal (BRL):", min_value=0.0, value=500.0, help="Custo fixo mensal do servidor/container do LangChain/API Gateway.")


    with tab_blocos[2]:
        st.header("Bloco 3: Risco Operacional e SVT (Score de Viabilidade)")
        
        # Risco de Falha da IA (Erro e Revisão)
        col3, col4 = st.columns(2)
        inputs_bloco_3["taxa_erro_percentual"] = col3.slider("Taxa de Erro da IA (%) - R_erro:", 
                                                             min_value=0, max_value=100, value=5, help="Percentual de saídas que a IA gera de forma incorreta.")
        inputs_bloco_3["tempo_revisao_min"] = col3.number_input("Tempo de Revisão Humana (min):", min_value=0.0, value=0.5, help="Tempo que o humano gasta para conferir a saída da IA (Human-in-the-Loop).")
        inputs_bloco_3["taxa_revisao_percentual"] = col3.slider("Taxa de Revisão Humana (%) - R_rev:", 
                                                                min_value=0, max_value=100, value=100, help="Percentual de unidades que exigem conferência humana.")
        
        # Ganhos Não-Monetários (Para o SVT)
        st.subheader("Ganhos de Qualidade e Estratégia")
        inputs_bloco_3["tempo_ia_resposta_seg"] = col4.number_input("Tempo de Resposta da IA (seg):", min_value=0.1, value=3.0, help="Latência real da IA (simulada ou medida).")
        inputs_bloco_3["risco_conformidade_score"] = col4.slider("Risco de Conformidade Reduzido (1 a 10):", 
                                                                  min_value=1, max_value=10, value=8, help="Score de 1 (Baixo Impacto) a 10 (Alto Impacto Legal/Financeiro).")
        
    # --- 3. BOTÃO DE EXECUÇÃO ---

    st.markdown("---")
    if st.button("🚀 Gerar Análise de Viabilidade Mavi.IA", type="primary"):
        
        # 🐛 CORREÇÃO CRÍTICA: Mapeamento de variáveis cruzadas antes da chamada!
        # Garantir que o salário (chave crítica) seja injetado onde o calc_logic espera.
        salario_hora_brl_value = inputs_bloco_1.get("salario_hora_brl")
        
        if salario_hora_brl_value is None or salario_hora_brl_value <= 0:
            st.error("🚨 ERRO: Por favor, preencha o campo 'Salário/Hora (BRL)' no Bloco 1.")
            return

        # Injetamos o valor do salário nos blocos 2 e 3 para o cálculo de risco R_op (custo de correção)
        inputs_bloco_2["salario_hora_brl"] = salario_hora_brl_value
        inputs_bloco_3["salario_hora_brl"] = salario_hora_brl_value
        
        inputs_totais = {
            "bloco_1": inputs_bloco_1,
            "bloco_2": inputs_bloco_2,
            "bloco_3": inputs_bloco_3,
        }
        
        with st.spinner("Mavi.IA analisando custos dinâmicos e rodando o CoT..."):
            try:
                # Chama o pipeline LangChain (usando a instância salva no state)
                resultado = st.session_state.mavi_chain.invoke(inputs_totais)
                
                st.success("✅ Análise Concluída com Sucesso!")
                
                # --- EXIBIÇÃO ---
                st.subheader("📑 Relatório de Profundidade Técnica (RPT)")
                st.markdown(resultado.content)
                
                st.subheader("📊 Infográfico Executivo (Veredito)")
                st.info(resultado.content)
                
            except Exception as e:
                # O erro 'humano' provavelmente estava aqui. O print do erro real ajudará.
                st.error(f"❌ Erro ao rodar o pipeline LangChain. Erro: {e}")

# Execução da aplicação Streamlit
if __name__ == "__main__":
    # O Streamlit lida com a inicialização da função main()
    main()