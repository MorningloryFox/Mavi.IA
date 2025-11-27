# calc_logic.py
# Mavi.IA Framework - Motor de Cálculo de Viabilidade Econômica e Técnica
# Versão 5.0: Suporte a KPIs de Horas, ROI Detalhado e Múltiplos Drivers de Valor

from typing import Dict, Any

def calcula_metricas_genai(inputs_bloco_1: Dict[str, Any], 
                           inputs_bloco_2: Dict[str, Any], 
                           inputs_bloco_3: Dict[str, Any],
                           global_cost_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula a viabilidade econômica de um projeto de IA Generativa.
    Retorna métricas financeiras (ROI, Payback) e operacionais (Horas Liberadas).
    """

    # --- 1. IDENTIFICAÇÃO DO CENÁRIO ---
    tipo_projeto = inputs_bloco_1.get("tipo_projeto", "automacao")
    V = inputs_bloco_1.get("volume_mensal", 0) or 0  # Proteção contra None
    
    # --- 2. CUSTOS DE INFRAESTRUTURA E EXECUÇÃO (TO-BE) ---
    # A. Infraestrutura Fixa (Ex: Licença n8n, Vector DB)
    C_infra_fixo = inputs_bloco_2.get("custo_infra_mensal_brl", 0.0) or 0.0
    
    # B. Custos Variáveis (Tokenomics)
    modelo = inputs_bloco_2.get("modelo_llm", "gemini-2.5-flash")
    # Tenta pegar custo do modelo, se não achar usa 0.0
    custos_modelo = global_cost_data["CUSTOS_API_USD"].get(modelo, {"input": 0.0, "output": 0.0})
    taxa_usd_brl = global_cost_data.get("TAXA_CONVERSAO_BRL_USD", 6.0) or 6.0
    
    tokens_in = inputs_bloco_2.get("tokens_input_por_unidade", 0) or 0
    tokens_out = inputs_bloco_2.get("tokens_output_por_unidade", 0) or 0
    
    # Cálculo: (Tokens * Preço / 1M) * Volume * Câmbio
    custo_token_unit_usd = ((tokens_in * custos_modelo["input"]) + (tokens_out * custos_modelo["output"])) / 1_000_000
    custo_token_total_brl = (custo_token_unit_usd * V) * taxa_usd_brl

    # --- 3. CÁLCULO DE VALOR (BENEFÍCIO) ---
    
    C_revisao_humana = 0.0
    horas_liquidas_liberadas = 0.0
    metrics = {}
    
    if tipo_projeto == "automacao":
        # === MODO 1: AUTOMAÇÃO (BACKOFFICE) ===
        # Benefício = Horas que a equipe deixa de gastar fazendo o trabalho manual.
        
        T_humano_min = inputs_bloco_1.get("tempo_por_unidade_min", 0) or 0
        S_hora = inputs_bloco_1.get("salario_hora_brl", 0) or 0
        
        # Custo AS-IS (O desperdício atual)
        horas_totais_as_is = (V * T_humano_min) / 60
        C_as_is = horas_totais_as_is * S_hora
        
        # Custo HITL (Human-in-the-Loop) - O "Imposto" da IA
        taxa_revisao = inputs_bloco_3.get("taxa_revisao_percentual", 0.0) or 0.0
        taxa_revisao = taxa_revisao / 100
        tempo_revisao = inputs_bloco_3.get("tempo_revisao_min", 0.0) or 0.0
        
        horas_revisao = (V * taxa_revisao * tempo_revisao) / 60
        C_revisao_humana = horas_revisao * S_hora
        
        # KPI: Horas Liberadas (Horas que gastava antes - Horas que gasta revisando agora)
        horas_liquidas_liberadas = horas_totais_as_is - horas_revisao
        
        Valor_Bruto_Gerado = C_as_is # O valor gerado é a eliminação do custo velho
        label_valor = "Economia de FTE"
        label_kpi_horas = "Horas-Homem Liberadas"
        detalhe_humano = f"Revisão Humana em {taxa_revisao*100:.0f}% dos casos"
        
    else:
        # === MODO 2: FAQ / DEFLEXÃO (FRONTOFFICE) ===
        # Benefício = Tickets que deixam de ser abertos (Deflexão).
        
        Custo_Ticket = inputs_bloco_1.get("custo_por_ticket_brl", 0.0) or 0
        Taxa_Deflexao = inputs_bloco_3.get("taxa_retencao_ia_percentual", 0.0) or 0.0
        Taxa_Deflexao = Taxa_Deflexao / 100
        
        # Custo AS-IS (Se todos os contatos fossem humanos)
        C_as_is = V * Custo_Ticket
        
        # Valor Gerado = Tickets Deflexionados * Custo Unitário
        Tickets_Deflexionados = V * Taxa_Deflexao
        Valor_Bruto_Gerado = Tickets_Deflexionados * Custo_Ticket
        
        # KPI: Horas Evitadas (Estimativa: Se cada ticket leva 10min, quanto tempo economizamos?)
        # Assumimos 10 min (0.16h) padrão por ticket se não tivermos dado melhor
        horas_por_ticket_estimado = 10 / 60 
        horas_liquidas_liberadas = Tickets_Deflexionados * horas_por_ticket_estimado
        
        # Em FAQ, o custo humano geralmente é tratado como "Ticket não resolvido", 
        # que já foi descontado do Valor Gerado (pois só contamos os deflexionados).
        # Porém, podemos ter custo de curadoria da base de conhecimento (fixo), mas aqui assumiremos 0 variável.
        C_revisao_humana = 0.0 
        
        label_valor = "Deflexão de Tickets"
        label_kpi_horas = "Horas de Atendimento Evitadas"
        detalhe_humano = f"Taxa de Retenção (IA) de {Taxa_Deflexao*100:.0f}%"

    # --- 4. CONSOLIDAÇÃO FINAL (ROI & PAYBACK) ---
    
    # Custo Total Mensal da Solução IA
    Custo_Operacional_IA = C_infra_fixo + custo_token_total_brl + C_revisao_humana
    
    # Saving Mensal Líquido (Dinheiro que sobra no caixa)
    Saving_Mensal = Valor_Bruto_Gerado - Custo_Operacional_IA
    
    # ROI (%)
    if Custo_Operacional_IA > 0:
        ROI = (Saving_Mensal / Custo_Operacional_IA) * 100
    else:
        # Se custo é zero (impossível, mas vai que), ROI é infinito se houver ganho
        ROI = 0.0 if Saving_Mensal <= 0 else 9999.0
        
    # Payback (Meses)
    custo_capex = inputs_bloco_2.get("custo_implementacao_capex_brl", 0.0) or 0.0
    payback_meses = custo_capex / Saving_Mensal if Saving_Mensal > 0 else 999.0
    
    # Montagem do Dicionário de Retorno (Compatível com langchain_agent.py)
    metrics.update({
        "as_is": {
            "custo_total": round(C_as_is, 2),
            "horas_total": round((V * (inputs_bloco_1.get("tempo_por_unidade_min",0) or 0))/60, 1) if tipo_projeto == "automacao" else 0
        },
        "to_be": {
            "infra": round(C_infra_fixo, 2),
            "tokens": round(custo_token_total_brl, 2),
            "humano_hitl": round(C_revisao_humana, 2),
            "total_ia": round(Custo_Operacional_IA, 2)
        },
        "resultado": {
            "valor_gerado": round(Valor_Bruto_Gerado, 2),     # O Ganho Bruto
            "saving_liquido": round(Saving_Mensal, 2),        # O Ganho Líquido
            "roi": round(ROI, 1),
            "payback": round(payback_meses, 1),
            "label_valor": label_valor,
            "horas_liberadas": round(horas_liquidas_liberadas, 1),
            "label_kpi_horas": label_kpi_horas,
            "detalhe_humano": detalhe_humano
        }
    })
    
    return metrics
