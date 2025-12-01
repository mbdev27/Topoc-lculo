# utils.py
# Funções auxiliares (identificação, etc.)

import pandas as pd
from datetime import datetime


def _parse_data_flex(valor):
    """
    Tenta interpretar 'valor' como data e devolver string no formato DD/MM/AAAA.
    Retorna string vazia se não conseguir interpretar.
    """
    if pd.isna(valor):
        return ""

    # Se já vier como datetime / Timestamp (excel normal)
    if isinstance(valor, (datetime, pd.Timestamp)):
        return valor.strftime("%d/%m/%Y")

    s = str(valor).strip()
    if s == "":
        return ""

    # Tenta formatos comuns manualmente
    formatos = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%y",
        "%d-%m-%y",
    ]
    for fmt in formatos:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%d/%m/%Y")
        except Exception:
            pass

    # Última tentativa: deixar o pandas tentar
    try:
        dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.isna(dt):
            return ""
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return ""


def ler_identificacao_from_df(df_id: pd.DataFrame):
    """
    Lê a aba 'Identificação' do Excel no padrão flexível:

        Campo | Valor
        ------+------
        Professor(a) | ...
        Equipamento  | ...
        Dados        | ...
        Local        | ...
        Patrimônio   | ...

    Mas é tolerante a pequenas variações de nomes.

    Retorna um dicionário com as chaves:
      'Professor(a)', 'Equipamento', 'Dados', 'Local', 'Patrimônio'

    Em que 'Dados' é sempre string 'DD/MM/AAAA' (se reconhecida) ou ''.
    """
    info = {
        "Professor(a)": "",
        "Equipamento": "",
        "Dados": "",
        "Local": "",
        "Patrimônio": "",
    }

    if df_id is None or df_id.empty:
        return info

    # Normaliza nomes das colunas para localizar "Campo" e "Valor"
    cols_lower = [str(c).strip().lower() for c in df_id.columns]
    col_campo = None
    col_valor = None
    for i, c in enumerate(cols_lower):
        if c in ["campo", "campos", "descricao", "descrição", "item"]:
            col_campo = df_id.columns[i]
        if c in ["valor", "valores", "dado"]:
            col_valor = df_id.columns[i]

    # Se não encontrar, assume primeira e segunda colunas como Campo/Valor
    if col_campo is None:
        col_campo = df_id.columns[0]
    if col_valor is None:
        col_valor = df_id.columns[1] if len(df_id.columns) > 1 else df_id.columns[0]

    for _, row in df_id.iterrows():
        campo = str(row.get(col_campo, "")).strip().lower()
        valor = row.get(col_valor, "")

        if "professor" in campo:
            info["Professor(a)"] = str(valor).strip()
        elif "equip" in campo:
            info["Equipamento"] = str(valor).strip()
        elif campo in ["data", "dados", "data dos dados", "data da atividade"]:
            info["Dados"] = _parse_data_flex(valor)
        elif "local" in campo:
            info["Local"] = str(valor).strip()
        elif ("patrim" in campo) or ("tomb" in campo):
            info["Patrimônio"] = str(valor).strip()

    return info
