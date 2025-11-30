# Painel Integrado de Vigilância em Saúde

Este projeto unifica dois painéis interativos desenvolvidos com `Streamlit`, voltados para análise e visualização de dados da Vigilância Sanitária do município de Ipojuca.

## 🔍 Painéis Disponíveis

1. **Painel VISA** – Acompanhamento de inspeções sanitárias, produção por localidade, risco e motivação.
2. **Painel REDESIM** – Indicadores de eficiência de resposta como "1ª visita em até 30 dias" e "Conclusão em até 90 dias".

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/painel-vigilancia.git
cd painel-vigilancia
```
2. (Recomendado) Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate     # Linux/macOS
venv\Scripts\activate        # Windows
```
3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## ▶️ Execução

Execute o painel principal com:
```bash
streamlit run visa.py
```

Ou acesse via múltiplas páginas:
```bash
streamlit run pages/1_VISA.py
```

## 🔐 Acesso Restrito

Credenciais padrão para acesso:
- **Usuário:** `administrador`
- **Senha:** `Ipojuca@2025*`

A autenticação é obrigatória para todas as páginas do painel.
