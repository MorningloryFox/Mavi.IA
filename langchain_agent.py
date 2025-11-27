# langchain_agent.py - Finalizado para a Mavi.IA (Stack Gemini/LangChain)

from dotenv import load_dotenv
# --- Carrega as variáveis do arquivo .env ANTES de qualquer LLM ---
load_dotenv() 

from langchain_core.runnables import RunnableLambda, RunnableSequence, RunnableParallel
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI # NOVO: Importando o Gemini

import calc_logic
import config_mavi

# --- 1. FUNÇÕES DE PREPARAÇÃO ---

def lookup_dynamic_costs(inputs: dict) -> dict:
    """Simula a busca em tempo real (câmbio e API prices) e formata o SYSTEM_PROMPT."""
    
    # ⚠️ NOTA: Na implementação real, esta função faria uma chamada real à API ou busca.
    # Usamos os valores fixos recentes obtidos via busca (simulação).
    TAXA_ATUAL_USD_BRL = 5.34 # Simulação da busca de câmbio
    
    global_cost_data = {
        "TAXA_CONVERSAO_BRL_USD": TAXA_ATUAL_USD_BRL,
        "CUSTOS_API_USD": {
            # Valores dinâmicos obtidos via busca (usamos o modelo primário para viabilidade)
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
        },
        "CUSTOS_BASE_FIXOS_BRL": config_mavi.CUSTO_DINAMICO_DUMMY["CUSTOS_BASE_FIXOS_BRL"]
    }
    
    # Formata o SYSTEM_PROMPT com o dado dinâmico para o LLM saber qual taxa usar
    inputs["system_prompt_final"] = config_mavi.SYSTEM_PROMPT.format(TAXA_ATUAL=TAXA_ATUAL_USD_BRL)
    inputs["global_cost_data"] = global_cost_data
    return inputs

# --- 2. DEFINIÇÃO DE TOOLS E LLM ---

# --- NOVO: LLM Gemini para análise e raciocínio ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", 
                             temperature=0.1, # Baixa temperatura para precisão analítica
                             convert_system_message_to_human=True # Necessário para o CoT complexo
                             )

calcula_custo_humano_tool = RunnableLambda(
    lambda inputs: calc_logic.calcula_custo_humano(
        inputs["bloco_1"], 
        config_mavi.CUSTO_FTE_HORAS_MES
    )
).with_config(run_name="Fase_1_Custo_Humano")

calcula_custo_ia_e_risco_tool = RunnableLambda(
    lambda inputs: calc_logic.calcula_custo_ia_e_risco(
        inputs["bloco_2"], 
        inputs["bloco_3"], 
        inputs["fase_1_results"],
        inputs["global_cost_data"]
    )
).with_config(run_name="Fase_2_3_Calculo_Total")

# --- 3. PIPELINE CENTRAL DA MAVI.IA ---

def criar_pipeline_mavi():
    
    # 1. Lookup Dinâmico e Inicialização (Formata o Prompt)
    pipeline_inicial = RunnableLambda(lookup_dynamic_costs).with_config(run_name="Lookup_Custos")
    
    # 2. Execução da FASE 1 (Custo Humano)
    # Roda a tool de cálculo para FTE, C_humano e Risco Evitado.
    fase_1_chain = RunnableSequence(
        lambda x: x,
        {
            "bloco_1": lambda x: x["bloco_1"],
            "CUSTO_FTE_HORAS_MES": lambda x: config_mavi.CUSTO_FTE_HORAS_MES
        } | calcula_custo_humano_tool
    ).with_config(run_name="Fase_1_Chain")

    # 3. Cadeia Principal: Roda a Fase 1 e injeta o resultado na Fase 2/3.
    mavi_chain_completa = pipeline_inicial | {
        
        # 'fase_1_results': Executa a Fase 1 e salva os resultados (HH, FTE, C_humano)
        "fase_1_results": fase_1_chain, 
        
        # 'contexto_total': Mantém todos os inputs e dados globais (bloco_2, global_cost_data)
        "contexto_total": lambda x: x,
        
    } | RunnableSequence(
        
        # 4. Execução da FASE 2/3 (Custo IA, ROI, SVT)
        {
            "calculos_finais": RunnableLambda(
                # Mapeia os inputs e resultados da Fase 1 para a Tool de cálculo
                lambda x: calc_logic.calcula_custo_ia_e_risco(
                    x["contexto_total"]["bloco_2"],
                    x["contexto_total"]["bloco_3"],
                    x["fase_1_results"],
                    x["contexto_total"]["global_cost_data"]
                )
            ).with_config(run_name="Fase_2_3_Calculo_Tool"),
            
            "contexto_para_llm": lambda x: x 
        },

        # 5. Geração do Relatório (LLM)
        lambda x: {
            "prompt_system": x["contexto_para_llm"]["contexto_total"]["system_prompt_final"],
            "dados_analise": f"FASE 1: {x['fase_1_results']} \n FASE 2/3: {x['calculos_finais']} \n\n INPUTS ORIGINAIS: Bloco 1: {x['contexto_para_llm']['contexto_total']['bloco_1']}"
        } | ChatPromptTemplate.from_messages([
            ("system", "{prompt_system}"),
            ("user", "Gere o RPT e o Infográfico Executivo com base nos dados. {dados_analise}")
        ]) | llm
    )
    
    return mavi_chain_completa