# processing.py
import numpy as np
import pandas as pd

from utils import (
    dms_to_decimal,
    media_angular_graus,
    desvio_padrao_angular_graus,
    resumo_angulos,
)

# Colunas obrigatórias, conforme sua planilha
REQUIRED_COLS = [
    "EST",
    "PV",
    "AnguloHorizontal_PD",
    "AnguloHorizontal_PI",
    "AnguloZenital_PD",
    "AnguloZenital_PI",
    "DistanciaInclinada_PD",
    "DistanciaInclinada_PI",
]

# Pontos principais
PONTOS_TRI = ["P1", "P2", "P3"]


def validar_dataframe(df_raw: pd.DataFrame):
    """
    - Garante presença das colunas obrigatórias.
    - Faz cópia só com as colunas relevantes.
    """
    erros = []
    df = df_raw.copy()

    # Verificar colunas
    for c in REQUIRED_COLS:
        if c not in df.columns:
            erros.append(f"Coluna obrigatória ausente: {c}")

    if erros:
        return pd.DataFrame(columns=REQUIRED_COLS), erros

    # Garantir tipos básicos
    df = df[REQUIRED_COLS].copy()

    # Nada muito agressivo aqui, o tratamento principal vem nas funções de cálculo
    return df, erros


def _dist_mm_para_m(val):
    """
    Converte leituras de distância em mm para metros (float).
    """
    if pd.isna(val):
        return np.nan
    try:
        return float(val) / 1000.0
    except Exception:
        return np.nan


def _hz_str_to_decimal(s):
    return dms_to_decimal(s)


def _z_str_to_decimal(s):
    return dms_to_decimal(s)


def calcular_linha_a_linha(df: pd.DataFrame):
    """
    Calcula, para cada linha da tabela de entrada:
    - Hz_PD / Hz_PI em graus decimais
    - Hz_médio (média vetorial de PD e PI)
    - Z_PD / Z_PI em graus decimais
    - Distâncias inclinadas em metros
    - Distâncias horizontais DH e diferenças de nível DN por PD/PI e médias
    """
    linhas = []

    for idx, row in df.iterrows():
        est = str(row["EST"]).strip()
        pv = str(row["PV"]).strip()

        # Hz em graus
        hz_pd = _hz_str_to_decimal(row["AnguloHorizontal_PD"])
        hz_pi = _hz_str_to_decimal(row["AnguloHorizontal_PI"])
        hz_med = media_angular_graus([hz_pd, hz_pi])

        # Z em graus
        z_pd = _z_str_to_decimal(row["AnguloZenital_PD"])
        z_pi = _z_str_to_decimal(row["AnguloZenital_PI"])
        # ângulo zenital = 0 no zênite; DH = DI * sin(Z), DN = DI * cos(Z) se Z medido desse jeito.
        z_pd_rad = np.deg2rad(z_pd)
        z_pi_rad = np.deg2rad(z_pi)

        # DI em metros
        di_pd_m = _dist_mm_para_m(row["DistanciaInclinada_PD"])
        di_pi_m = _dist_mm_para_m(row["DistanciaInclinada_PI"])
        di_med_m = np.nanmean([di_pd_m, di_pi_m])

        # DH, DN
        dh_pd = di_pd_m * np.sin(z_pd_rad)
        dh_pi = di_pi_m * np.sin(z_pi_rad)
        dn_pd = di_pd_m * np.cos(z_pd_rad)
        dn_pi = di_pi_m * np.cos(z_pi_rad)

        dh_med = np.nanmean([dh_pd, dh_pi])
        dn_med = np.nanmean([dn_pd, dn_pi])

        linhas.append(
            {
                "EST": est,
                "PV": pv,
                "Hz_PD_graus": hz_pd,
                "Hz_PI_graus": hz_pi,
                "Hz_med_graus": hz_med,
                "Z_PD_graus": z_pd,
                "Z_PI_graus": z_pi,
                "DI_PD_m": di_pd_m,
                "DI_PI_m": di_pi_m,
                "DI_med_m": di_med_m,
                "DH_PD_m": dh_pd,
                "DH_PI_m": dh_pi,
                "DH_med_m": dh_med,
                "DN_PD_m": dn_pd,
                "DN_PI_m": dn_pi,
                "DN_med_m": dn_med,
            }
        )

    return pd.DataFrame(linhas)


def agregar_por_par(df_linha: pd.DataFrame):
    """
    Agrupa por (EST, PV) e calcula:
    - Hz médio e desvio padrão angular
    - DI média (m) e desvio padrão
    - DH média (m) e desvio padrão
    - DN média (m) e desvio padrão
    """
    grupos = []
    for (est, pv), grupo in df_linha.groupby(["EST", "PV"]):
        hz_todos = list(grupo["Hz_med_graus"].dropna())

        if len(hz_todos) == 0:
            hz_med = np.nan
            hz_std = np.nan
        else:
            hz_med = media_angular_graus(hz_todos)
            hz_std = desvio_padrao_angular_graus(hz_todos)

        for col in ["DI_med_m", "DH_med_m", "DN_med_m"]:
            # iremos pegar a média e o desvio padrão dessa coluna
            pass

        di_vals = grupo["DI_med_m"].dropna().values
        dh_vals = grupo["DH_med_m"].dropna().values
        dn_vals = grupo["DN_med_m"].dropna().values

        di_med = float(np.mean(di_vals)) if len(di_vals) > 0 else np.nan
        dh_med = float(np.mean(dh_vals)) if len(dh_vals) > 0 else np.nan
        dn_med = float(np.mean(dn_vals)) if len(dn_vals) > 0 else np.nan

        di_std = float(np.std(di_vals, ddof=1)) if len(di_vals) > 1 else 0.0
        dh_std = float(np.std(dh_vals, ddof=1)) if len(dh_vals) > 1 else 0.0
        dn_std = float(np.std(dn_vals, ddof=1)) if len(dn_vals) > 1 else 0.0

        grupos.append(
            {
                "EST": est,
                "PV": pv,
                "Hz_med_graus_par": hz_med,
                "Hz_std_graus_par": hz_std,
                "DI_med_m_par": di_med,
                "DI_std_m_par": di_std,
                "DH_med_m_par": dh_med,
                "DH_std_m_par": dh_std,
                "DN_med_m_par": dn_med,
                "DN_std_m_par": dn_std,
            }
        )

    return pd.DataFrame(grupos)


def resumo_linha_a_linha(df_linha: pd.DataFrame):
    """
    Tabela mais amigável linha a linha (para mostrar no app).
    """
    return df_linha[
        [
            "EST",
            "PV",
            "Hz_PD_graus",
            "Hz_PI_graus",
            "Hz_med_graus",
            "DI_PD_m",
            "DI_PI_m",
            "DI_med_m",
            "DH_PD_m",
            "DH_PI_m",
            "DH_med_m",
        ]
    ].copy()


def resumo_por_par(df_par: pd.DataFrame):
    """
    Tabela resumo por par, com médias e desvios padrão de Hz, DI, DH.
    """
    return df_par[
        [
            "EST",
            "PV",
            "Hz_med_graus_par",
            "Hz_std_graus_par",
            "DI_med_m_par",
            "DI_std_m_par",
            "DH_med_m_par",
            "DH_std_m_par",
        ]
    ].copy()


def construir_triangulo_medio(df_par: pd.DataFrame):
    """
    Constrói lados do triângulo médio P1-P2-P3 com base nas
    DI_med_m_par (ou DH_med_m_par) entre pares:
    - P1-P2
    - P1-P3
    - P2-P3
    Retorna (lados, angulos, area) em forma de dicionário.
    """
    # Buscar as distâncias médias (em metros)
    def get_dist(par1, par2):
        g1 = df_par[(df_par["EST"] == par1) & (df_par["PV"] == par2)]
        g2 = df_par[(df_par["EST"] == par2) & (df_par["PV"] == par1)]
        if not g1.empty:
            return float(g1["DI_med_m_par"].iloc[0])
        if not g2.empty:
            return float(g2["DI_med_m_par"].iloc[0])
        return np.nan

    d12 = get_dist("P1", "P2")
    d13 = get_dist("P1", "P3")
    d23 = get_dist("P2", "P3")

    if any(np.isnan([d12, d13, d23])):
        raise ValueError(
            "Faltam distâncias médias para formar o triângulo P1-P2-P3 (DI_med_m_par)."
        )

    # Vamos usar notação A=BC oposto a A, B=AC oposto a B, C=AB oposto a C
    # e vértices A=P1, B=P2, C=P3
    # Lado oposto a A (P1) = BC = d23
    A = d23
    # Lado oposto a B (P2) = AC = d13
    B = d13
    # Lado oposto a C (P3) = AB = d12
    C = d12

    # Lei dos cossenos para ângulos em graus
    def angle(a, b, c):
        # ângulo oposto a a, com lados (a, b, c)
        cosA = (b**2 + c**2 - a**2) / (2 * b * c)
        cosA = max(min(cosA, 1.0), -1.0)
        return np.rad2deg(np.arccos(cosA))

    ang_A = angle(A, B, C)
    ang_B = angle(B, A, C)
    ang_C = angle(C, A, B)

    # Área (Heron)
    s = 0.5 * (A + B + C)
    area = np.sqrt(max(s * (s - A) * (s - B) * (s - C), 0.0))

    lados = {"A": A, "B": B, "C": C}
    angulos = {"A": ang_A, "B": ang_B, "C": ang_C}
    soma_ang, desvio = resumo_angulos(ang_A, ang_B, ang_C)

    return lados, angulos, area, soma_ang, desvio


def construir_triangulo_especifico(df_par: pd.DataFrame):
    """
    Usa o circuito específico:
    - P1 ⇒ P3
    - P3 ⇒ P2
    - P2 ⇒ P1
    E monta um triângulo com lados = DI_med_m_par em metros.
    Retorna:
      coords_tri, (d13, d32, d21), (ang_P1, ang_P3, ang_P2), soma, desvio, area
    """
    def get_di(est, pv):
        g = df_par[(df_par["EST"] == est) & (df_par["PV"] == pv)]
        if g.empty:
            raise ValueError(f"Não há dados médios DI_med_m_par para {est}–{pv}.")
        return float(g["DI_med_m_par"].iloc[0])

    d13 = get_di("P1", "P3")
    d32 = get_di("P3", "P2")
    d21 = get_di("P2", "P1")

    # Notação:
    # vértices: P1, P3, P2
    # lados:
    #   - entre P1 e P3 = d13
    #   - entre P3 e P2 = d32
    #   - entre P2 e P1 = d21
    # Vamos montar coordenadas:
    # P1 = (0, 0)
    # P3 = (d13, 0)
    # P2 em algum lugar definido pela lei dos cossenos

    # ângulo no vértice P3, oposto ao lado P1-P2 (d21)
    def angle(a, b, c):
        cosA = (b**2 + c**2 - a**2) / (2 * b * c)
        cosA = max(min(cosA, 1.0), -1.0)
        return np.rad2deg(np.arccos(cosA))

    # Ângulos internos:
    #   - em P1: oposto a lado P3-P2 (d32)
    ang_P1 = angle(d32, d13, d21)
    #   - em P3: oposto a lado P2-P1 (d21)
    ang_P3 = angle(d21, d13, d32)
    #   - em P2: oposto a lado P1-P3 (d13)
    ang_P2 = angle(d13, d32, d21)

    soma_ang, desvio = resumo_angulos(ang_P1, ang_P3, ang_P2)

    # Área (Heron)
    s = 0.5 * (d13 + d32 + d21)
    area = np.sqrt(max(s * (s - d13) * (s - d32) * (s - d21), 0.0))

    # Coordenadas para desenho:
    P1 = np.array([0.0, 0.0])
    P3 = np.array([d13, 0.0])

    # Para achar P2: lado P2-P1 = d21, P2-P3 = d32
    # Usamos coordenadas: P2 = (x, y)
    # dist^2 P2-P1: x^2 + y^2 = d21^2
    # dist^2 P2-P3: (x - d13)^2 + y^2 = d32^2
    # Subtraindo as duas equações, isolamos x.
    x = (d21**2 - d32**2 + d13**2) / (2 * d13)
    y_sq = d21**2 - x**2
    y = np.sqrt(max(y_sq, 0.0))

    P2 = np.array([x, y])

    coords_tri = {"P1": P1, "P3": P3, "P2": P2}

    return coords_tri, (d13, d32, d21), (ang_P1, ang_P3, ang_P2), soma_ang, desvio, area
