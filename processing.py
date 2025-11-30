# processing.py
from typing import Dict, List, Tuple

import math
import numpy as np
import pandas as pd

from utils import (
    classificar_re_vante,
    decimal_to_dms,
    mean_direction_list,
    mean_direction_two,
    parse_angle_to_decimal,
)

# Pontos e pares fixos usados na análise do triângulo
PONTOS_TRI = ("P1", "P2", "P3")
PARES_TRI = ("P1⇒P3", "P3⇒P2", "P2⇒P1")

REQUIRED_COLS = ["EST", "PV", "Hz_PD", "Hz_PI", "Z_PD", "Z_PI", "DI_PD", "DI_PI"]


def normalizar_colunas(df_original: pd.DataFrame) -> pd.DataFrame:
    """
    Harmoniza nomes de colunas vindos de planilhas diversas para os nomes
    esperados: EST, PV, Hz_PD, Hz_PI, Z_PD, Z_PI, DI_PD, DI_PI.
    """
    df = df_original.copy()
    colmap = {}
    for c in df.columns:
        low = c.strip().lower()
        if low in ["est", "estacao", "estação"]:
            colmap[c] = "EST"
        elif low in ["pv", "ponto visado", "ponto_visado", "ponto"]:
            colmap[c] = "PV"
        elif ("horizontal" in low and "pd" in low) or ("hz" in low and "pd" in low):
            colmap[c] = "Hz_PD"
        elif ("horizontal" in low and "pi" in low) or ("hz" in low and "pi" in low):
            colmap[c] = "Hz_PI"
        elif ("zenital" in low and "pd" in low) or ("z" in low and "pd" in low):
            colmap[c] = "Z_PD"
        elif ("zenital" in low and "pi" in low) or ("z" in low and "pi" in low):
            colmap[c] = "Z_PI"
        elif "dist" in low and "pd" in low:
            colmap[c] = "DI_PD"
        elif "dist" in low and "pi" in low:
            colmap[c] = "DI_PI"
        else:
            colmap[c] = c
    return df.rename(columns=colmap)


def validar_dataframe(df_original: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Normaliza colunas e verifica:
      - Presença de colunas obrigatórias.
      - Se Hz/Z/DI são conversíveis para ângulo/float.
    Retorna (df_normalizado, lista_de_erros).
    """
    erros: List[str] = []
    df = normalizar_colunas(df_original)

    # Garante colunas obrigatórias
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        erros.append("Colunas obrigatórias ausentes: " + ", ".join(missing))

    for c in REQUIRED_COLS:
        if c not in df.columns:
            df[c] = ""

    invalid_rows_hz: List[int] = []
    invalid_rows_z: List[int] = []
    invalid_rows_di: List[int] = []

    for idx, row in df.iterrows():
        hz_pd = parse_angle_to_decimal(row.get("Hz_PD", ""))
        hz_pi = parse_angle_to_decimal(row.get("Hz_PI", ""))
        z_pd = parse_angle_to_decimal(row.get("Z_PD", ""))
        z_pi = parse_angle_to_decimal(row.get("Z_PI", ""))
        if np.isnan(hz_pd) or np.isnan(hz_pi):
            invalid_rows_hz.append(idx + 1)
        if np.isnan(z_pd) or np.isnan(z_pi):
            invalid_rows_z.append(idx + 1)
        try:
            di_pd = float(str(row.get("DI_PD", "")).replace(",", "."))
            di_pi = float(str(row.get("DI_PI", "")).replace(",", "."))
            if np.isnan(di_pd) or np.isnan(di_pi):
                invalid_rows_di.append(idx + 1)
        except Exception:
            invalid_rows_di.append(idx + 1)

    if invalid_rows_hz:
        erros.append(
            "Valores inválidos ou vazios em Hz_PD / Hz_PI nas linhas: "
            + ", ".join(map(str, invalid_rows_hz))
            + "."
        )
    if invalid_rows_z:
        erros.append(
            "Valores inválidos ou vazios em Z_PD / Z_PI nas linhas: "
            + ", ".join(map(str, invalid_rows_z))
            + "."
        )
    if invalid_rows_di:
        erros.append(
            "Valores inválidos ou vazios em DI_PD / DI_PI nas linhas: "
            + ", ".join(map(str, invalid_rows_di))
            + "."
        )

    return df, erros


def calcular_linha_a_linha(
    df_uso: pd.DataFrame,
    ref_por_estacao: Dict[str, str],
) -> pd.DataFrame:
    """
    Aplica todos os cálculos linha a linha:
      - Classificação Ré/Vante.
      - Conversão de Hz/Z para decimal.
      - DH/DN PD/PI + médias.
      - Hz médios (PD/PI) em decimal / DMS.
    Retorna DataFrame `res` com colunas de trabalho (Hz_PD_deg, etc.).
    """
    res = df_uso.copy()

    # Ré / Vante
    res["Tipo"] = res.apply(
        lambda r: classificar_re_vante(r["EST"], r["PV"], ref_por_estacao),
        axis=1,
    )

    # Ângulos em decimal
    for col in ["Hz_PD", "Hz_PI", "Z_PD", "Z_PI"]:
        res[col + "_deg"] = res[col].apply(parse_angle_to_decimal)

    # Distâncias inclinadas
    res["DI_PD_m"] = res["DI_PD"].apply(lambda x: float(str(x).replace(",", ".")))
    res["DI_PI_m"] = res["DI_PI"].apply(lambda x: float(str(x).replace(",", ".")))

    # DH/DN
    z_pd_rad = res["Z_PD_deg"] * np.pi / 180.0
    z_pi_rad = res["Z_PI_deg"] * np.pi / 180.0

    res["DH_PD_m"] = np.abs(res["DI_PD_m"] * np.sin(z_pd_rad)).round(4)
    res["DN_PD_m"] = np.abs(res["DI_PD_m"] * np.cos(z_pd_rad)).round(4)
    res["DH_PI_m"] = np.abs(res["DI_PI_m"] * np.sin(z_pi_rad)).round(4)
    res["DN_PI_m"] = np.abs(res["DI_PI_m"] * np.cos(z_pi_rad)).round(4)

    # Hz médio (PD/PI)
    res["Hz_med_deg"] = res.apply(
        lambda r: mean_direction_two(r["Hz_PD_deg"], r["Hz_PI_deg"]), axis=1
    )
    res["Hz_med_DMS"] = res["Hz_med_deg"].apply(decimal_to_dms)

    # DH/DN médios
    res["DH_med_m"] = np.abs((res["DH_PD_m"] + res["DH_PI_m"]) / 2.0).round(4)
    res["DN_med_m"] = np.abs((res["DN_PD_m"] + res["DN_PI_m"]) / 2.0).round(4)

    return res


def agregar_por_par(res: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega o DataFrame linha a linha em um DataFrame por par EST–PV (`df_par`),
    calculando:
      - Hz/Z médios com média vetorial.
      - DI médias aritméticas.
      - DH/DN médios derivados.
    """
    def agg_par(df_group: pd.DataFrame) -> pd.Series:
        out = {}
        out["Hz_PD_med_deg"] = mean_direction_list(df_group["Hz_PD_deg"])
        out["Hz_PI_med_deg"] = mean_direction_list(df_group["Hz_PI_deg"])
        out["Z_PD_med_deg"] = mean_direction_list(df_group["Z_PD_deg"])
        out["Z_PI_med_deg"] = mean_direction_list(df_group["Z_PI_deg"])
        out["DI_PD_med_m"] = float(df_group["DI_PD_m"].mean())
        out["DI_PI_med_m"] = float(df_group["DI_PI_m"].mean())
        return pd.Series(out)

    df_par = res.groupby(["EST", "PV"], as_index=False).apply(agg_par)

    # Hz médio por par
    df_par["Hz_med_deg_par"] = df_par.apply(
        lambda r: mean_direction_two(r["Hz_PD_med_deg"], r["Hz_PI_med_deg"]),
        axis=1,
    )
    df_par["Hz_med_DMS_par"] = df_par["Hz_med_deg_par"].apply(decimal_to_dms)

    # DH/DN médios por par
    zpd_par_rad = df_par["Z_PD_med_deg"] * np.pi / 180.0
    zpi_par_rad = df_par["Z_PI_med_deg"] * np.pi / 180.0

    df_par["DH_PD_m_par"] = np.abs(
        df_par["DI_PD_med_m"] * np.sin(zpd_par_rad)
    ).round(4)
    df_par["DN_PD_m_par"] = np.abs(
        df_par["DI_PD_med_m"] * np.cos(zpd_par_rad)
    ).round(4)
    df_par["DH_PI_m_par"] = np.abs(
        df_par["DI_PI_med_m"] * np.sin(zpi_par_rad)
    ).round(4)
    df_par["DN_PI_m_par"] = np.abs(
        df_par["DI_PI_med_m"] * np.cos(zpi_par_rad)
    ).round(4)

    df_par["DH_med_m_par"] = np.abs(
        (df_par["DH_PD_m_par"] + df_par["DH_PI_m_par"]) / 2.0
    ).round(4)
    df_par["DN_med_m_par"] = np.abs(
        (df_par["DN_PD_m_par"] + df_par["DN_PI_m_par"]) / 2.0
    ).round(4)

    return df_par


def resumo_linha_a_linha(res: pd.DataFrame) -> pd.DataFrame:
    """
    Monta DataFrame amigável para exibição linha a linha.
    """
    return pd.DataFrame(
        {
            "EST": res["EST"],
            "PV": res["PV"],
            "Tipo": res["Tipo"],
            "Hz_PD": res["Hz_PD"],
            "Hz_PI": res["Hz_PI"],
            "Hz_médio (DMS)": res["Hz_med_DMS"].fillna(""),
            "DH_PD (m)": res["DH_PD_m"],
            "DH_PI (m)": res["DH_PI_m"],
            "DH_médio (m)": res["DH_med_m"],
            "DN_PD (m)": res["DN_PD_m"],
            "DN_PI (m)": res["DN_PI_m"],
            "DN_médio (m)": res["DN_med_m"],
        }
    )


def resumo_por_par(df_par: pd.DataFrame) -> pd.DataFrame:
    """
    Monta DataFrame amigável para exibição das médias por par EST–PV
    (com DH/DN completos, mais “numérica bruta”).
    """
    return pd.DataFrame(
        {
            "EST": df_par["EST"],
            "PV": df_par["PV"],
            "Hz_PD_médio (deg)": df_par["Hz_PD_med_deg"].round(6),
            "Hz_PI_médio (deg)": df_par["Hz_PI_med_deg"].round(6),
            "Hz_médio (DMS)": df_par["Hz_med_DMS_par"],
            "DH_PD_médio (m)": df_par["DH_PD_m_par"],
            "DH_PI_médio (m)": df_par["DH_PI_m_par"],
            "DH_médio (m)": df_par["DH_med_m_par"],
            "DN_PD_médio (m)": df_par["DN_PD_m_par"],
            "DN_PI_médio (m)": df_par["DN_PI_m_par"],
            "DN_médio (m)": df_par["DN_med_m_par"],
        }
    )


def tabela_medicao_angular_horizontal(df_par: pd.DataFrame) -> pd.DataFrame:
    """
    Monta tabela no formato do slide:
    'Medição Angular Horizontal'
    Colunas: EST, PV, Hz PD, Hz PI, Hz Médio, Hz Reduzido, Média das Séries.

    Aqui:
      - Hz PD, Hz PI e Hz Médio em DMS.
      - Hz Reduzido = Hz Médio (por par) tomado diretamente (a redução
        entre ré/vante pode ser feita depois, se desejado).
      - Média das Séries = Hz Médio (média das leituras PD/PI).
    """
    hz_pd_med_dms = df_par["Hz_PD_med_deg"].apply(decimal_to_dms)
    hz_pi_med_dms = df_par["Hz_PI_med_deg"].apply(decimal_to_dms)
    hz_med_dms = df_par["Hz_med_deg_par"].apply(decimal_to_dms)

    return pd.DataFrame(
        {
            "EST": df_par["EST"],
            "PV": df_par["PV"],
            "Hz PD": hz_pd_med_dms,
            "Hz PI": hz_pi_med_dms,
            "Hz Médio": hz_med_dms,
            "Hz Reduzido": hz_med_dms,
            "Média das Séries": hz_med_dms,
        }
    )


def tabela_medicao_angular_vertical(df_par: pd.DataFrame) -> pd.DataFrame:
    """
    Monta tabela no formato do slide:
    'Medição Angular Vertical/Zenital'
    Colunas: EST, PV, Z PD, Z PI, Z Corrigido, Média das Séries.

    Usa a fórmula do slide:
       Z_corr = (Z_PD_med - Z_PI_med) / 2 + 180°
    (tudo em graus decimais internamente, exibido em DMS).
    """
    z_pd_med = df_par["Z_PD_med_deg"]
    z_pi_med = df_par["Z_PI_med_deg"]

    # Z Corrigido em graus decimais
    z_corr_deg = (z_pd_med - z_pi_med) / 2.0 + 180.0

    z_pd_med_dms = z_pd_med.apply(decimal_to_dms)
    z_pi_med_dms = z_pi_med.apply(decimal_to_dms)
    z_corr_dms = z_corr_deg.apply(decimal_to_dms)

    return pd.DataFrame(
        {
            "EST": df_par["EST"],
            "PV": df_par["PV"],
            "Z PD": z_pd_med_dms,
            "Z PI": z_pi_med_dms,
            "Z Corrigido": z_corr_dms,
            "Média das Séries": z_corr_dms,
        }
    )


def dist(
    p: str,
    q: str,
    coords: Dict[str, Tuple[float, float]],
) -> float:
    """Distância euclidiana entre pontos p e q em coords."""
    x1, y1 = coords[p]
    x2, y2 = coords[q]
    return math.hypot(x2 - x1, y2 - y1)


def angulo_oposto(
    lado_oposto: float,
    lado1: float,
    lado2: float,
) -> float:
    """
    Calcula o ângulo oposto a 'lado_oposto' por lei dos cossenos.
    Retorna o ângulo em graus.
    """
    num = lado1 ** 2 + lado2 ** 2 - lado_oposto ** 2
    den = 2 * lado1 * lado2
    if den == 0:
        return float("nan")
    cos_val = max(-1.0, min(1.0, num / den))
    return math.degrees(math.acos(cos_val))


def info_triangulo(
    pA: str,
    pB: str,
    pC: str,
    coords: Dict[str, Tuple[float, float]],
):
    """
    Calcula lados, ângulos e área de um triângulo definido por pA, pB, pC
    em um dicionário de coordenadas 'coords'.
    """
    a = dist(pB, pC, coords)
    b = dist(pA, pC, coords)
    c = dist(pA, pB, coords)

    ang_A = angulo_oposto(a, b, c)
    ang_B = angulo_oposto(b, a, c)
    ang_C = angulo_oposto(c, a, b)

    s = (a + b + c) / 2.0
    area = math.sqrt(max(0.0, s * (s - a) * (s - b) * (s - c)))

    lados = {
        "A": a,
        "B": b,
        "C": c,
        "nome_lado_A": f"{pB}{pC}",
        "nome_lado_B": f"{pA}{pC}",
        "nome_lado_C": f"{pA}{pB}",
    }
    angulos = {"A": ang_A, "B": ang_B, "C": ang_C}
    return lados, angulos, area
