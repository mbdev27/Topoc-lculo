import math
import pandas as pd
import numpy as np

REQUIRED_COLS = ["EST", "PV", "Hz_PD", "Hz_PI", "Z_PD", "Z_PI", "DI_PD", "DI_PI"]

# ---------------------------------------------------------
# PARSE DE ÂNGULOS
# ---------------------------------------------------------
def parse_angle_to_decimal(value):
    if value is None: return np.nan
    s = str(value).strip()
    if s == "": return np.nan

    # Só número
    try:
        if all(c.isdigit() or c in ".,-" for c in s):
            return float(s.replace(",", "."))
    except:
        pass

    # Substituir símbolos
    for ch in ["°", "º", "'", "′", "´", '"', "″"]:
        s = s.replace(ch, " ")

    s = s.replace(",", ".")

    parts = [p for p in s.split() if p]

    try:
        d = float(parts[0])
        m = float(parts[1]) if len(parts) > 1 else 0
        s_ = float(parts[2]) if len(parts) > 2 else 0
        return d + m/60 + s_/3600
    except:
        return np.nan

# ---------------------------------------------------------
# DECIMAL → DMS
# ---------------------------------------------------------
def decimal_to_dms(angle):
    if angle is None or math.isnan(angle): return ""
    a = angle % 360
    d = int(a)
    m_f = (a - d)*60
    m = int(m_f)
    s = int(round((m_f - m)*60))
    return f"{d:02d}° {m:02d}' {s:02d}\""

# ---------------------------------------------------------
# NORMALIZAÇÃO
# ---------------------------------------------------------
def validar_dataframe(df_original):
    df = df_original.copy()

    # Renomear colunas
    colmap = {}
    for c in df.columns:
        t = c.strip().lower()
        if t in ["est"]: colmap[c] = "EST"
        elif t in ["pv"]: colmap[c] = "PV"
        elif "hz" in t and "pd" in t: colmap[c] = "Hz_PD"
        elif "hz" in t and "pi" in t: colmap[c] = "Hz_PI"
        elif ("z" in t) and ("pd" in t): colmap[c] = "Z_PD"
        elif ("z" in t) and ("pi" in t): colmap[c] = "Z_PI"
        elif "di" in t and "pd" in t: colmap[c] = "DI_PD"
        elif "di" in t and "pi" in t: colmap[c] = "DI_PI"
        else: colmap[c] = c

    df = df.rename(columns=colmap)

    erros = []
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        erros.append("Faltam colunas: " + ", ".join(missing))
        return df, erros

    return df, erros

# ---------------------------------------------------------
# CÁLCULOS
# ---------------------------------------------------------
def calcular_linha_a_linha(df):
    res = df.copy()

    for col in ["Hz_PD", "Hz_PI", "Z_PD", "Z_PI"]:
        res[col + "_deg"] = res[col].apply(parse_angle_to_decimal)

    # Cálculo de médios
    def medio(pd, pi):
        if np.isnan(pd) or np.isnan(pi): return np.nan
        m = (pd + pi)/2
        if pd > pi:
            return (m + 90) % 360
        return (m - 90) % 360

    res["Hz_med_deg"] = res.apply(lambda r: medio(r["Hz_PD_deg"], r["Hz_PI_deg"]), axis=1)
    res["Hz_med_DMS"] = res["Hz_med_deg"].apply(decimal_to_dms)

    # Z corrigido
    def zcorr(pd, pi):
        if np.isnan(pd) or np.isnan(pi): return np.nan
        return (pd - pi)/2 + 180

    res["Z_corr_deg"] = res.apply(lambda r: zcorr(r["Z_PD_deg"], r["Z_PI_deg"]), axis=1)
    res["Z_corr_DMS"] = res["Z_corr_deg"].apply(decimal_to_dms)

    # Distâncias horizontais e verticais
    res["DI_PD_m"] = res["DI_PD"].astype(str).str.replace(",", ".").astype(float)
    res["DI_PI_m"] = res["DI_PI"].astype(str).str.replace(",", ".").astype(float)

    rad = np.radians(res["Z_corr_deg"])
    res["DH_med_m"] = ((res["DI_PD_m"]*np.sin(rad) +
                        res["DI_PI_m"]*np.sin(rad))/2).round(3)

    return res

# ---------------------------------------------------------
# TABELAS POR SÉRIE
# ---------------------------------------------------------
def tabela_hz_por_serie(res):
    df = res.copy()

    mins = df.groupby("EST")["Hz_med_deg"].transform("min")
    df["Hz_reduzido_deg"] = (df["Hz_med_deg"] - mins) % 360
    df["Hz_reduzido_DMS"] = df["Hz_reduzido_deg"].apply(decimal_to_dms)

    return df[["EST", "PV", "Hz_PD", "Hz_PI", "Hz_med_DMS", "Hz_reduzido_DMS"]]

def tabela_z_por_serie(res):
    df = res.copy()
    return df[["EST", "PV", "Z_PD", "Z_PI", "Z_corr_DMS"]]
