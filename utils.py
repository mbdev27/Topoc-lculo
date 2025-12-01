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

    # Se já vier como datetime
    if isinstance(valor, (datetime, pd.Timestamp)):
        return valor.strftime("%d/%m/%Y")

    s = str(valor).strip()
    if s == "":
        return ""

    # Se já estiver no formato DD/MM/AAAA, apenas normaliza
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d"):
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
    Lê a aba 'Identificação' do Excel no padrão:

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
    em que 'Dados' é sempre string 'DD/MM/AAAA' (se reconhecida) ou ''.
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

    # Normaliza nomes das colunas
    cols_lower = [str(c).strip().lower() for c in df_id.columns]
    col_campo = None
    col_valor = None
    for i, c in enumerate(cols_lower):
        if c in ["campo", "descricao", "descrição", "item"]:
            col_campo = df_id.columns[i]
        if c in ["valor", "valores", "dado"]:
            col_valor = df_id.columns[i]

    # Se não encontrar o padrão "Campo/Valor", tenta usar primeira/segunda colunas
    if col_campo is None:
        col_campo = df_id.columns[0]
    if col_valor is None:
        if len(df_id.columns) > 1:
            col_valor = df_id.columns[1]
        else:
            col_valor = df_id.columns[0]

    for _, row in df_id.iterrows():
        campo = str(row.get(col_campo, "")).strip().lower()
        valor = row.get(col_valor, "")

        if "professor" in campo:
            info["Professor(a)"] = str(valor).strip()
        elif "equip" in campo:
            info["Equipamento"] = str(valor).strip()
        elif campo in ["data", "dados", "data dos dados"]:
            info["Dados"] = _parse_data_flex(valor)
        elif "local" in campo:
            info["Local"] = str(valor).strip()
        elif ("patrim" in campo) or ("tomb" in campo):
            info["Patrimônio"] = str(valor).strip()

    return info
