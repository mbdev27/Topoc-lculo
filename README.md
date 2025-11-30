# Calculadora de Ângulos e Distâncias – Método das Direções para Triângulos (UFPE)

Aplicação Streamlit usada na disciplina **Equipamentos de Medição** (UFPE) para
processar leituras de estação total e gerar:

- Médias de direções horizontais (Hz);
- Ângulos verticais/zenitais corrigidos;
- Distâncias horizontais médias;
- Triângulo formado pelos pontos P1, P2 e P3, com lados, ângulos internos e área.

## Estrutura do projeto

- `app.py` — interface principal em duas páginas:
  - Página 1: **1. Modelo de planilha** e **2. Carregar dados de campo**.
  - Página 2: cabeçalho UFPE + seções 3 a 7.
- `processing.py` — funções de validação, cálculo, tabelas e modelo Excel.
- `plotting.py` — desenho do triângulo em planta e exportação XLSX com figura.
- `utils.py` — leitura da aba `Identificacao` e formatação da data em `DD/MM/AAAA`.
- `requirements.txt` — dependências Python.

## Uso

1. Instale as dependências:

```bash
pip install -r requirements.txt
