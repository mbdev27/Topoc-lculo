# utils.py
# Funções auxiliares (identificação e formatação de data)

import pandas as pd
from typing import Dict


def format_data_ddmmaaaa(raw) -> str:
    if raw is None or str(raw).strip() == "":
        return ""
    s = str(raw).strip()
    try:
        dt = pd.to_datetime(raw)
        return dt.strftime("%d/%m/%Y")
    except Exception:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                dt = pd.to_datetime(s, format=fmt)
                return dt.strftime("%d/%m/%Y")
            except Exception:
                continue
    return s


def ler_identificacao_from_df(df_id: pd.DataFrame) -> Dict[str, str]:
    id_map = {
        "Professor(a)": "",
        "Equipamento": "",
        "Data": "",
        "Local": "",
        "Patrimônio": "",
    }
    if df_id is None or df_id.empty:
        return id_map

    campo_col = None
    valor_col = None
    for c in df_id.columns:
        if c.strip().lower() in ["campo", "campos"]:
            campo_col = c
        if c.strip().lower() in ["valor", "valores"]:
            valor_col = c
    if campo_col is None or valor_col is None:
        return id_map

    for _, row in df_id.iterrows():
        campo = str(row[campo_col]).strip()
        val_raw = row[valor_col]
        if campo == "Data":
            val = format_data_ddmmaaaa(val_raw)
        else:
            val = "" if pd.isna(val_raw) else str(val_raw).strip()
        if campo in id_map:
            id_map[campo] = val
    return id_map
