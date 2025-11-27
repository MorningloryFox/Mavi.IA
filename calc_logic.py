# calc_logic.py - Funções de Cálculo Crítico para o Agente Mavi.IA

from typing import Dict, Any

# --- Funções Tool para LangChain ---

def calcula_custo_humano(inputs_bloco_1: Dict[str, Any], CUSTO_FTE_HORAS_MES: int) -> Dict[str, float]:
    """
    Calcula o custo mensal humano (C_humano) e a economia em FTE com base nos inputs do Bloco 1.
    Esta função implementa a Lógica da FASE 1 (AS-IS).
    """
    
    # Extração e conversão de inputs (assumindo que tempo está em minutos)
    V = inputs_bloco_1["volume_mensal"]
    T_humano = inputs_bloco_1["tempo_por_unidade_min"]
    S_hora = inputs_bloco_1["salario_hora_brl"]

    # 1. Cálculo do tempo total economizado (em horas)
    tempo_total_h_economizado = (V * T_humano) / 60
    
    # 2. Custo humano por mês (C_humano)
    C_humano = tempo_total_h_economizado * S_hora
    
    # 3. Cálculo do FTE (Equivalente de Tempo Integral)
    FTE_economizado = tempo_total_h_economizado / CUSTO_FTE_HORAS_MES
    
    # 4. Impacto Monetizado de Erros Humanos
    C_erro_unitario = inputs_bloco_1.get("custo_erro_critico_brl_unidade", 0.0)
    R_erro_humano = inputs_bloco_1.get("risco_erro_humano_percentual", 0.0) / 100

    # Custo de Risco Humano Mensal Evitado (Economia)
    C_risco_humano_evitado = V * R_erro_humano * C_erro_unitario
    
    return {
        "C_humano_mensal_brl": round(C_humano, 2),
        "horas_economizadas_hh": round(tempo_total_h_economizado, 2),
        "FTE_economizado": round(FTE_economizado, 3),
        "C_risco_humano_evitado": round(C_risco_humano_evitado, 2),
        "tempo_humano_unidade_seg": round(T_humano * 60, 2) # Adicionado T_humano em segundos
    }

def calcula_custo_ia_e_risco(inputs_bloco_2: Dict[str, Any], inputs_bloco_3: Dict[str, Any], resultados_fase_1: Dict[str, float], global_cost_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula o custo total da IA (C_IA) incluindo execução e risco operacional,
    o ROI bruto e o Score de Viabilidade Técnica (SVT).
    Esta função implementa as Lógicas das FASES 2 e 3.
    """
    
    # --- Dados Reutilizados e Entradas (inputs_bloco_2/3) ---
    V = inputs_bloco_2["volume_mensal"]
    C_humano = resultados_fase_1["C_humano_mensal_brl"]
    C_risco_humano_evitado = resultados_fase_1["C_risco_humano_evitado"]
    S_hora = inputs_bloco_2["salario_hora_brl"]
    
    # Latência e Tempo (Inputs)
    T_humano_seg = resultados_fase_1["tempo_humano_unidade_seg"]
    T_ia_seg = inputs_bloco_3.get("tempo_ia_resposta_seg", 0.0) # Novo input: Latência da IA em segundos
    
    # --- FASE 2: Custo de Execução (C_exec) ---
    TAXA = global_cost_data["TAXA_CONVERSAO_BRL_USD"]
    custo_modelo = global_cost_data["CUSTOS_API_USD"].get(inputs_bloco_2["modelo_llm"])
    C_ocr_unit = global_cost_data["CUSTOS_BASE_FIXOS_BRL"]["ocr_base_unit_brl"]

    # 1. Custo LLM
    T_in = inputs_bloco_2["tokens_input_por_unidade"]
    T_out = inputs_bloco_2["tokens_output_por_unidade"]
    
    C_llm_usd = (V * T_in * custo_modelo["input"] + V * T_out * custo_modelo["output"]) / 1_000_000
    C_llm_brl = C_llm_usd * TAXA
    
    # 2. Custo OCR e Hosting
    C_ocr = V * C_ocr_unit * inputs_bloco_2["paginas_por_unidade"]
    C_host = inputs_bloco_2["custo_hosting_mensal_brl"]
    
    C_exec = C_llm_brl + C_ocr + C_host
    
    # --- Risco Operacional (R_op) ---
    R_erro = inputs_bloco_3["taxa_erro_percentual"] / 100
    T_rev = inputs_bloco_3["tempo_revisao_min"]
    R_rev = inputs_bloco_3["taxa_revisao_percentual"] / 100
    
    # 1. Custo de Correção Humana (R_op)
    C_correcao_brl = (V * R_rev) * (T_rev / 60) * S_hora
    
    C_IA = C_exec + C_correcao_brl
    
    # --- FASE 3: Veredito e Ganhos Não-Monetários ---
    
    # 1. Monetização do Ganho Total
    Ganho_Total = C_humano + C_risco_humano_evitado
    
    # 2. ROI (com Risco Monetizado)
    ROI = ((Ganho_Total - C_IA) / C_IA) * 100
    
    # 3. Melhoria de Latência Percentual (Nova Métrica de Eficiência!)
    if T_humano_seg > 0:
        Melhoria_Latencia_Perc = ((T_humano_seg - T_ia_seg) / T_humano_seg) * 100
    else:
        Melhoria_Latencia_Perc = 0.0 # Evita divisão por zero
    
    # 4. Score de Viabilidade Técnica (SVT - 0 a 100)
    latencia = Melhoria_Latencia_Perc # Usamos a métrica de eficiência
    conformidade_score = inputs_bloco_3.get("risco_conformidade_score", 5) # 1 a 5
    qualidade_ia = (100 - (R_erro * 100)) 
    
    # SPV: 40% Qualidade da IA + 40% Eficiência (Latência) + 20% Conformidade
    SVT = (qualidade_ia * 0.40) + (latencia * 0.40) + (conformidade_score * 4) 

    return {
        "C_exec_brl": round(C_exec, 2),
        "C_IA_total_brl": round(C_IA, 2),
        "C_correcao_brl": round(C_correcao_brl, 2),
        "Ganho_Total_Bruto": round(Ganho_Total, 2),
        "ROI_total_percentual": round(ROI, 2),
        "Melhoria_Latencia_Perc": round(Melhoria_Latencia_Perc, 2), # Adicionada!
        "Score_Viabilidade_Tecnica": round(SVT, 2)
    }

# --- FIM do calc_logic.py ---