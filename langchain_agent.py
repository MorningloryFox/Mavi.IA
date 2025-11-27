# langchain_agent.py
# Mavi.IA 5.0 - Orquestrador de Inteligência e Relatórios Executivos
# ATUALIZADO: Sintaxe LCEL corrigida para estabilidade do pipeline

from dotenv import load_dotenv
load_dotenv()

from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

import calc_logic
import config_mavi

# ==========================================
# 1. DEFINIÇÃO DO SCHEMA DE DADOS
# ==========================================

class MaviParameters(BaseModel):
    """
    Schema unificado para extração de dados do chat.
    """
    # Classificador Principal
    tipo_projeto: Literal['automacao', 'faq'] = Field(
        ..., 
        description="Classificação do projeto: 'automacao' (substituir tarefa manual) ou 'faq' (chatbot de atendimento)."
    )
    
    # Bloco 1
    volume_mensal: Optional[int] = Field(None, description="Quantidade total de execuções ou atendimentos por mês.")
    tempo_por_unidade_min: Optional[float] = Field(None, description="Tempo manual gasto por unidade (apenas para automação).")
    salario_hora_brl: Optional[float] = Field(None, description="Custo hora do colaborador (apenas para automação).")
    custo_por_ticket_brl: Optional[float] = Field(None, description="Custo médio de um ticket/chamado humano (apenas para FAQ).")
    taxa_retencao_ia_percentual: Optional[float] = Field(None, description="% de chamados que a IA deve resolver sozinha (apenas para FAQ).")

    # Bloco 2
    modelo_llm: Optional[str] = Field(None, description="Modelo de IA sugerido (ex: gpt-4o, gemini-2.5-flash).")
    custo_infra_mensal_brl: Optional[float] = Field(None, description="Custo fixo mensal de infra (n8n Enterprise, Vector DB, Hosting).")
    custo_implementacao_capex_brl: Optional[float] = Field(None, description="Custo único de implementação (Dev Hours) para cálculo de Payback.")
    tokens_input_por_unidade: Optional[int] = Field(None, description="Estimativa de tokens de entrada.")
    tokens_output_por_unidade: Optional[int] = Field(None, description="Estimativa de tokens de saída.")

    # Bloco 3
    taxa_erro_percentual: Optional[float] = Field(None, description="Risco estimado de alucinação/erro.")
    taxa_revisao_percentual: Optional[float] = Field(None, description="% do volume que passará por revisão humana.")
    tempo_revisao_min: Optional[float] = Field(None, description="Tempo gasto pelo humano para revisar/corrigir a IA.")


# ==========================================
# 2. FUNÇÕES DE SUPORTE
# ==========================================

def lookup_dynamic_costs(inputs: dict) -> dict:
    """Simula a busca em tempo real de custos e câmbio."""
    TAXA_ATUAL_USD_BRL = 6.10 
    
    global_cost_data = {
        "TAXA_CONVERSAO_BRL_USD": TAXA_ATUAL_USD_BRL,
        "CUSTOS_API_USD": {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gemini-2.5-flash": {"input": 0.075, "output": 0.30}, 
        },
        "CUSTOS_BASE_FIXOS_BRL": config_mavi.CUSTO_DINAMICO_DUMMY["CUSTOS_BASE_FIXOS_BRL"]
    }
    
    inputs["global_cost_data"] = global_cost_data
    inputs["system_prompt_final"] = config_mavi.SYSTEM_PROMPT 
    
    return inputs


# ==========================================
# 3. AGENTES DE CHAT & EXTRAÇÃO
# ==========================================

def criar_agente_extrator():
    """
    Cria o 'Mavi Analyst' para conversar com o usuário.
    """
    llm_chat = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0.3
    )

    prompt_chat = ChatPromptTemplate.from_messages([
        ("system", """
        Você é o Mavi Analyst, um Arquiteto de Soluções de IA.
        Sua missão é entender a demanda do usuário e classificar tecnicamente.
        
        PASSO 1: Classifique o Projeto
        - É **Automação**? (Ler doc, extrair dados, substituir tarefa repetitiva).
        - É **FAQ/Deflexão**? (Chatbot, tirar dúvidas, evitar chamados de suporte).
        
        PASSO 2: Colete os Dados Certos
        - Se Automação: Pergunte Volume, Tempo Gasto Hoje e Salário da Equipe.
        - Se FAQ: Pergunte Volume de Chamados, Custo do Ticket Atual e Meta de Retenção (%).
        
        PASSO 3: Arquitetura
        - Pergunte sobre a complexidade (tamanho dos textos) para estimar tokens.
        - Sugira ferramentas (LangChain para complexidade, n8n para processos lineares).
        
        Seja breve, técnico e conduza a entrevista.
        """),
        ("placeholder", "{chat_history}"),
        ("user", "{input}")
    ])
    
    return prompt_chat | llm_chat

def extrair_dados_conversa(historico_texto: str) -> Dict[str, Any]:
    """
    Extrai o JSON estruturado da conversa.
    """
    llm_extractor = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    structured_llm = llm_extractor.with_structured_output(MaviParameters)
    
    prompt_extraction = f"""
    Analise a conversa técnica abaixo.
    Classifique o projeto (automacao ou faq) e extraia os parâmetros.
    Retorne NULL para campos não mencionados.
    
    --- CONVERSA ---
    {historico_texto}
    """
    return structured_llm.invoke(prompt_extraction)


# ==========================================
# 4. PIPELINE DE RELATÓRIO TÉCNICO (O CÉREBRO 5.0)
# ==========================================

def formatar_dados_para_prompt(x: dict) -> dict:
    """
    Função auxiliar para formatar os dados numéricos antes de enviar ao Prompt do LLM.
    Isso evita lógica complexa dentro da definição da Chain.
    """
    metrics = x["metrics"]
    original_context = x["original_context"]
    
    as_is = metrics["as_is"]
    to_be = metrics["to_be"]
    resultado = metrics["resultado"]
    
    # Cálculo seguro da porcentagem de saving
    saving_pct = 0
    if as_is["custo_total"] > 0:
        saving_pct = (resultado["saving_liquido"] / as_is["custo_total"]) * 100

    return {
        "prompt_system": original_context["system_prompt_final"],
        "tipo_projeto_label": original_context["bloco_1"]["tipo_projeto"].upper(),
        "original_inputs": original_context["bloco_1"],
        
        # --- FORMATAÇÃO FINANCEIRA (Strings R$) ---
        "custo_as_is": "{:,.2f}".format(as_is["custo_total"]),
        "custo_total_ia": "{:,.2f}".format(to_be["total_ia"]),
        
        "custo_infra": "{:,.2f}".format(to_be["infra"]),
        "custo_tokens": "{:,.2f}".format(to_be["tokens"]),
        "custo_humano_ia": "{:,.2f}".format(to_be["humano_hitl"]),
        
        "saving_liquido": "R$ {:,.2f}".format(resultado["saving_liquido"]),
        "saving_percentual": round(saving_pct, 1),
        
        # --- KPIS OPERACIONAIS ---
        "horas_liberadas": resultado["horas_liberadas"],
        "label_kpi_horas": resultado["label_kpi_horas"],
        
        # --- RETORNO ---
        "roi": resultado["roi"],
        "payback": resultado["payback"],
        
        # --- METADADOS ---
        "modelo": original_context["bloco_2"]["modelo_llm"]
    }

def gerar_relatorio_tecnico():
    """
    Pipeline principal Mavi 5.0:
    Lookup -> Cálculo KPIs -> Formatação Executiva -> Prompt -> Geração LLM.
    """
    
    llm_writer = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0.2,
        convert_system_message_to_human=True
    )

    user_prompt_template = """
    Gere o Relatório Executivo Mavi 5.0.
    
    CONTEXTO:
    - Tipo: {tipo_projeto_label}
    - Inputs Brutos: {original_inputs}
    
    DADOS FINANCEIROS CALCULADOS:
    - Custo AS-IS: R$ {custo_as_is}
    - Custo TO-BE Total: R$ {custo_total_ia}
    
    - Breakdown TO-BE:
      * Infra Fixa: R$ {custo_infra}
      * Tokens: R$ {custo_tokens}
      * Humano na IA (HITL): R$ {custo_humano_ia}
      * Modelo: {modelo}
    
    - KPIs de Sucesso:
      * Saving Financeiro: {saving_liquido} ({saving_percentual}%)
      * Horas Liberadas / Deflexão: {horas_liberadas} ({label_kpi_horas})
      * ROI: {roi}%
      * Payback: {payback} meses
    """

    prompt_relatorio = ChatPromptTemplate.from_messages([
        ("system", "{prompt_system}"),
        ("user", user_prompt_template)
    ])
    
    # Montagem da Chain usando Pipe Syntax (LCEL Puro)
    # Isso evita erros de "Runnable vs String"
    chain = (
        RunnableLambda(lookup_dynamic_costs)
        | RunnableLambda(lambda x: {
            "metrics": calc_logic.calcula_metricas_genai(
                x["bloco_1"], x["bloco_2"], x["bloco_3"], x["global_cost_data"]
            ),
            "original_context": x 
        })
        | RunnableLambda(formatar_dados_para_prompt) # Passo isolado de formatação
        | prompt_relatorio
        | llm_writer
    )
    
    return chain
