Markdown# 🤖 Mavi.IA: Engenharia de Viabilidade de Projetos de IA

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Stack](https://img.shields.io/badge/Stack-LangChain%20%7C%20Streamlit%20%7C%20Gemini-orange)
![Status](https://img.shields.io/badge/Status-MVP%20Funcional-green)

## 📌 Visão Geral

A **Mavi.IA (Metodologia de Análise de Viabilidade e Impacto)** é um agente inteligente projetado para atuar como o **Guardião Financeiro e Técnico** de projetos de Inteligência Artificial Generativa.

O objetivo da ferramenta é eliminar a subjetividade na aprovação de POCs (Provas de Conceito). Ela quantifica o **ROI (Retorno sobre Investimento)**, mede a **Economia de FTE (Full Time Equivalent)** e calcula o **Score de Viabilidade Técnica (SVT)** antes que uma única linha de código seja escrita.

## 🚀 Funcionalidades Principais

* **Análise Híbrida:** Combina a precisão matemática do Python (para cálculos financeiros) com o raciocínio do LLM (Gemini 2.5 Flash) para análise de riscos.
* **Cálculo de Custo Real:** Considera custos ocultos como Tokens (Input/Output), taxas de OCR, Hosting e Custo de Correção Humana (Human-in-the-Loop).
* **Monetização de Risco:** Transforma "redução de erros" em valor financeiro tangível.
* **Lookup Dinâmico:** Simula a busca de custos variáveis (Câmbio USD/BRL e Preços de API) em tempo real.
* **Double Output:** Gera dois relatórios simultâneos:
    1.  **RPT (Relatório de Profundidade Técnica):** Para engenheiros e analistas.
    2.  **Infográfico Executivo:** Para gestores e C-Level.

## 🏗️ Arquitetura do Projeto

O projeto segue uma arquitetura modular *Code-Native*:

| Módulo | Arquivo | Função |
| :--- | :--- | :--- |
| **Interface** | `app_streamlit.py` | Frontend em Streamlit. Coleta inputs (Blocos 1, 2 e 3) e exibe os relatórios. |
| **Orquestrador** | `langchain_agent.py` | Pipeline LCEL. Gerencia o fluxo de dados, carrega o `.env` e chama o LLM. |
| **Motor de Cálculo** | `calc_logic.py` | Funções Python puras (Tools). Executa cálculos de ROI, FTE, Latência e SVT com precisão 100%. |
| **Configuração** | `config_mavi.py` | Armazena o `SYSTEM_PROMPT` (Identidade da IA) e parâmetros globais. |

## 🛠️ Instalação e Configuração

Siga os passos abaixo para rodar o projeto localmente e evitar conflitos de dependência.

### 1. Pré-requisitos
* Python 3.10 ou superior.
* Uma chave de API do Google Gemini (`GEMINI_API_KEY`).

### 2. Clonar e Criar Ambiente Virtual (Recomendado)
Para evitar conflitos com bibliotecas antigas (como `openai` vs `genai`), crie um ambiente limpo:

```bash
# Clone o repositório (ou baixe os arquivos)
git clone [https://github.com/seu-usuario/mavi-ia.git](https://github.com/seu-usuario/mavi-ia.git)
cd mavi-ia

# Crie o ambiente virtual
python -m venv venv_mavi

# Ative o ambiente
# Windows:
venv_mavi\Scripts\activate
# Linux/Mac:
source venv_mavi/bin/activate
3. Instalar DependênciasBashpip install langchain-core langchain-google-genai streamlit pandas python-dotenv
4. Configurar Variáveis de AmbienteCrie um arquivo chamado .env na raiz do projeto e adicione sua chave:Snippet de código# Arquivo .env
GEMINI_API_KEY="cole_sua_chave_aqui_sem_aspas_se_preferir"
▶️ Como UsarNo terminal (com o ambiente virtual ativado), execute:Bashstreamlit run app_streamlit.py
O navegador abrirá a interface da Mavi.IA.Preencha as abas:Bloco 1 (AS-IS): Dados do processo manual atual.Bloco 2 (TO-BE): Estimativas de uso da IA (Tokens, Modelo).Bloco 3 (Risco): Taxas de erro esperadas e necessidade de revisão humana.Clique em "🚀 Gerar Análise de Viabilidade Mavi.IA".🧠 A Metodologia M.A.V.I.O cálculo de viabilidade segue um funil de 3 fases:Fase 1 (Custo Humano): Define o teto de investimento.$$C_{humano} = (Tempo_{unidade} \times Volume) \times Salário_{hora}$$Fase 2 (Custo Operacional IA): Soma custos diretos e indiretos.$$C_{IA} = C_{API} + C_{Hosting} + C_{OCR} + C_{CorreçãoHumana}$$Fase 3 (Veredito):ROI Bruto: $$((C_{humano} + Risco_{evitado}) - C_{IA}) / C_{IA}$$SVT (Score de Viabilidade Técnica): Métrica composta (0-100) baseada em Latência, Qualidade da IA e Conformidade.🤝 ContribuiçãoEste é um projeto interno de Governança de IA. Para contribuir:Abra uma Issue descrevendo a melhoria no cálculo ou no Prompt.Faça um Pull Request atualizando o calc_logic.py.📄 LicençaProprietário. Uso interno para análise de viabilidade.
