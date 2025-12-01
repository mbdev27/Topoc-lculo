# processing.py
# Funções de processamento numérico/geométrico para o app UFPE

import io
import math
from typing import List, Optional, Tuple, Dict

import numpy as np
import pandas as pd

REQUIRED_COLS_BASE = ["EST", "PV", "Hz_PD", "Hz_PI", "Z_PD", "Z_PI", "DI_PD", "DI_PI"]
OPTIONAL_COLS = ["SEQ"]
REQUIRED_COLS_ALL = REQUIRED_COLS_BASE + OPTIONAL_COLS


# ---------------------------------------------------------------------
# Ângulos
# ---------------------------------------------------------------------
def parse_angle_to_decimal(value: str) -> float:
    if value is None:
        return float("nan")
    s = str(value).strip()
    if s == "":
        return float("nan")

    # Caso simples: só número (com vírgula ou ponto)
    try:
        if all(ch.isdigit() or ch in ".,-+" for ch in s):
            return float(s.replace(",", "."))
    except Exception:
        pass

    # Remover símbolos de graus, minutos, segundos
    for ch in ["°", "º", "'", "´", "′", '"', "″"]:
        s = s.replace(ch, " ")
    s = s.replace(",", ".")
    partes = [p for p in s.split() if p != ""]
    if not partes:
        return float("nan")

    try:
        deg = float(partes[0])
        minutos = float(partes[1]) if len(partes) > 1 else 0.0
        segundos = float(partes[2]) if len(partes) > 2 else 0.0
    except Exception:
        return float("nan")

    sinal = 1.0
    if deg < 0:
        sinal = -1.0
        deg = abs(deg)
    return sinal * (deg + minutos / 60.0 + segundos / 3600.0)


def decimal_to_dms(angle_deg: float) -> str:
    if angle_deg is None or math.isnan(angle_deg):
        return ""
    a = angle_deg % 360.0
    d = int(a)
    m_f = (a - d) * 60
    m = int(m_f)
    s_f = (m_f - m) * 60
    s = int(round(s_f))
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        d += 1
    return f"{d:02d}°{m:02d}'{s:02d}\""


def mean_direction_circular(angles_deg: List[float]) -> float:
    vals = [a for a in angles_deg if not math.isnan(a)]
    if len(vals) == 0:
        return float("nan")
    x = sum(math.cos(math.radians(v)) for v in vals)
    y = sum(math.sin(math.radians(v)) for v in vals)
    if x == 0 and y == 0:
        return float("nan")
    ang = math.degrees(math.atan2(y, x))
    if ang < 0:
        ang += 360.0
    return ang


# ---------------------------------------------------------------------
# Normalização/validação
# ---------------------------------------------------------------------
def normalizar_colunas(df_original: pd.DataFrame) -> pd.DataFrame:
    df = df_original.copy()
    colmap: Dict[str, str] = {}
    for c in df.columns:
        low = c.strip().lower()
        if low in ["est", "estacao", "estação"]:
            colmap[c] = "EST"
        elif low in ["pv", "ponto visado", "ponto_visado", "ponto"]:
            colmap[c] = "PV"
        elif low in ["seq", "sequencia", "sequência", "serie", "série"]:
            colmap[c] = "SEQ"
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


def validar_dataframe(df_original: pd.DataFrame):
    erros = []
    df = normalizar_colunas(df_original)

    missing = [c for c in REQUIRED_COLS_BASE if c not in df.columns]
    if missing:
        erros.append("Colunas obrigatórias ausentes: " + ", ".join(missing))

    for c in REQUIRED_COLS_ALL:
        if c not in df.columns:
            df[c] = ""

    invalid_rows_hz = []
    invalid_rows_z = []
    invalid_rows_di = []
    invalid_rows_seq = []

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

        seq_val = str(row.get("SEQ", "")).strip()
        if seq_val != "":
            try:
                int(seq_val)
            except Exception:
                invalid_rows_seq.append(idx + 1)

    if invalid_rows_hz:
        erros.append(
            "Valores inválidos ou vazios em Hz_PD / Hz_PI nas linhas: "
            + ", ".join(map(str, invalid_rows_hz))
        )
    if invalid_rows_z:
        erros.append(
            "Valores inválidos ou vazios em Z_PD / Z_PI nas linhas: "
            + ", ".join(map(str, invalid_rows_z))
        )
    if invalid_rows_di:
        erros.append(
            "Valores inválidos ou vazios em DI_PD / DI_PI nas linhas: "
            + ", ".join(map(str, invalid_rows_di))
        )
    if invalid_rows_seq:
        erros.append(
            "Valores inválidos em SEQ (devem ser inteiros) nas linhas: "
            + ", ".join(map(str, invalid_rows_seq))
        )

    if "SEQ" in df.columns:
        def _parse_seq(x):
            sx = str(x).strip()
            if sx == "":
                return np.nan
            try:
                return int(sx)
            except Exception:
                return np.nan

        df["SEQ"] = df["SEQ"].apply(_parse_seq)

    return df, erros


# ---------------------------------------------------------------------
# Cálculo linha a linha
# ---------------------------------------------------------------------
def calcular_linha_a_linha(df_uso: pd.DataFrame) -> pd.DataFrame:
    res = df_uso.copy()

    for col in ["Hz_PD", "Hz_PI", "Z_PD", "Z_PI"]:
        res[col + "_deg"] = res[col].apply(parse_angle_to_decimal)

    res["DI_PD_m"] = res["DI_PD"].apply(lambda x: float(str(x).replace(",", ".")))
    res["DI_PI_m"] = res["DI_PI"].apply(lambda x: float(str(x).replace(",", ".")))

    def calc_hz_medio(pd_deg, pi_deg):
        if math.isnan(pd_deg) or math.isnan(pi_deg):
            return float("nan")
        m = (pd_deg + pi_deg) / 2.0
        if pd_deg > pi_deg:
            hz = m + 90.0
        else:
            hz = m - 90.0
        return hz % 360.0

    res["Hz_med_deg"] = res.apply(
        lambda r: calc_hz_medio(r["Hz_PD_deg"], r["Hz_PI_deg"]), axis=1
    )
    res["Hz_med_DMS"] = res["Hz_med_deg"].apply(decimal_to_dms)

    def calc_z_corr(z_pd_deg, z_pi_deg):
        if math.isnan(z_pd_deg) or math.isnan(z_pi_deg):
            return float("nan")
        return (z_pd_deg - z_pi_deg) / 2.0 + 180.0

    res["Z_corr_deg"] = res.apply(
        lambda r: calc_z_corr(r["Z_PD_deg"], r["Z_PI_deg"]), axis=1
    )
    res["Z_corr_DMS"] = res["Z_corr_deg"].apply(decimal_to_dms)

    z_rad = res["Z_corr_deg"] * np.pi / 180.0
    res["DH_PD_m"] = np.abs(res["DI_PD_m"] * np.sin(z_rad)).round(3)
    res["DN_PD_m"] = np.abs(res["DI_PD_m"] * np.cos(z_rad)).round(3)
    res["DH_PI_m"] = np.abs(res["DI_PI_m"] * np.sin(z_rad)).round(3)
    res["DN_PI_m"] = np.abs(res["DI_PI_m"] * np.cos(z_rad)).round(3)

    res["DH_med_m"] = np.abs((res["DH_PD_m"] + res["DH_PI_m"]) / 2.0).round(3)
    res["DN_med_m"] = np.abs((res["DN_PD_m"] + res["DN_PI_m"]) / 2.0).round(3)

    return res


# ---------------------------------------------------------------------
# Tabelas Hz / Z
# ---------------------------------------------------------------------
def tabela_hz_por_serie(res: pd.DataFrame) -> pd.DataFrame:
    df = res.copy().reset_index(drop=False)
    df.rename(columns={"index": "_ordem_original"}, inplace=True)

    df["Hz_reduzido_deg"] = np.nan
    for est in df["EST"].unique():
        sub = df[df["EST"] == est]
        if sub.empty:
            continue
        ref = float(sub["Hz_med_deg"].min())
        mask = df["EST"] == est
        df.loc[mask, "Hz_reduzido_deg"] = (df.loc[mask, "Hz_med_deg"] - ref) % 360.0

    df["Hz_reduzido_DMS"] = df["Hz_reduzido_deg"].apply(decimal_to_dms)

    medias_series = []
    for (est, pv), sub in df.groupby(["EST", "PV"]):
        hz_list = [v for v in sub["Hz_reduzido_deg"].tolist() if not math.isnan(v)]
        hz_med_series = mean_direction_circular(hz_list)
        medias_series.append(
            {"EST": est, "PV": pv, "Hz_med_series_deg": hz_med_series}
        )
    df_med = pd.DataFrame(medias_series)
    df_med["Hz_med_series_DMS"] = df_med["Hz_med_series_deg"].apply(decimal_to_dms)

    df = df.merge(df_med, on=["EST", "PV"], how="left")
    df.sort_values(by="_ordem_original", inplace=True)

    tab = pd.DataFrame(
        {
            "Estação": df["EST"],
            "Ponto Visado": df["PV"],
            "Hz PD": df["Hz_PD"],
            "Hz PI": df["Hz_PI"],
            "Hz Médio": df["Hz_med_DMS"],
            "Hz Reduzido": df["Hz_reduzido_DMS"],
            "Média das séries": df["Hz_med_series_DMS"],
        }
    )
    return tab


def tabela_z_por_serie(res: pd.DataFrame) -> pd.DataFrame:
    df = res.copy().reset_index(drop=False)
    df.rename(columns={"index": "_ordem_original"}, inplace=True)

    medias_series = []
    for (est, pv), sub in df.groupby(["EST", "PV"]):
        z_vals = [v for v in sub["Z_corr_deg"].tolist() if not math.isnan(v)]
        if len(z_vals) == 0:
            z_med = float("nan")
        else:
            z_med = sum(z_vals) / len(z_vals)
        medias_series.append(
            {"EST": est, "PV": pv, "Z_med_series_deg": z_med}
        )
    df_med = pd.DataFrame(medias_series)
    df_med["Z_med_series_DMS"] = df_med["Z_med_series_deg"].apply(decimal_to_dms)

    df = df.merge(df_med, on=["EST", "PV"], how="left")
    df.sort_values(by="_ordem_original", inplace=True)

    tab = pd.DataFrame(
        {
            "Estação": df["EST"],
            "Ponto Visado": df["PV"],
            "Z PD": df["Z_PD"],
            "Z PI": df["Z_PI"],
            "Z Corrigido": df["Z_corr_DMS"],
            "Média das séries": df["Z_med_series_DMS"],
        }
    )
    return tab


# ---------------------------------------------------------------------
# Distâncias e tabela resumo
# ---------------------------------------------------------------------
def tabela_distancias_medias_simetricas(res: pd.DataFrame) -> pd.DataFrame:
    aux = res[["EST", "PV", "DH_med_m"]].copy()
    registros: Dict[Tuple[str, str], List[float]] = {}

    for _, row in aux.iterrows():
        a = str(row["EST"])
        b = str(row["PV"])
        if a == b:
            continue
        par = tuple(sorted([a, b]))
        dh = float(row["DH_med_m"])
        registros.setdefault(par, []).append(dh)

    linhas = []
    for (a, b), valores in registros.items():
        dh_med = float(np.mean(valores))
        linhas.append({"PontoA": a, "PontoB": b, "DH_media": dh_med})

    df_dist = pd.DataFrame(linhas)
    if not df_dist.empty:
        df_dist.sort_values("DH_media", ascending=False, inplace=True)
    return df_dist


def tabela_resumo_final(res: pd.DataFrame, renomear_para_letras: bool = True) -> pd.DataFrame:
    tab_hz_full = tabela_hz_por_serie(res)
    tab_hz = (
        tab_hz_full
        .groupby(["Estação", "Ponto Visado"], as_index=False)
        .agg(
            **{
                "Hz Médio": ("Hz Médio", "first"),
                "Hz Reduzido": ("Hz Reduzido", "first"),
                "Média das séries": ("Média das séries", "first"),
            }
        )
    )

    tab_z_full = tabela_z_por_serie(res)
    tab_z = (
        tab_z_full
        .groupby(["Estação", "Ponto Visado"], as_index=False)
        .agg(
            **{
                "Z Corrigido": ("Z Corrigido", "first"),
                "Média Z das séries": ("Média das séries", "first"),
            }
        )
    )

    resumo = pd.merge(
        tab_hz,
        tab_z,
        on=["Estação", "Ponto Visado"],
        how="outer",
    )

    df_dh = res[["EST", "PV", "DH_med_m"]].copy()
    df_dh["DH_med_str"] = df_dh["DH_med_m"].apply(
        lambda x: f"{x:.3f}" if pd.notna(x) else ""
    )
    df_dh_grp = df_dh.groupby(["EST", "PV"], as_index=False)["DH_med_str"].first()

    resumo = resumo.merge(
        df_dh_grp,
        left_on=["Estação", "Ponto Visado"],
        right_on=["EST", "PV"],
        how="left",
    )

    resumo = resumo[
        [
            "Estação",
            "Ponto Visado",
            "Hz Médio",
            "Hz Reduzido",
            "Média das séries",
            "Z Corrigido",
            "Média Z das séries",
            "DH_med_str",
        ]
    ].rename(
        columns={
            "Média das séries": "Média das séries (Hz)",
            "DH_med_str": "DH Médio (m)",
        }
    )

    if renomear_para_letras:
        mapa_simples = {"P1": "A", "P2": "B", "P3": "C"}
        resumo["EST"] = resumo["Estação"].astype(str).replace(mapa_simples)
        resumo["PV"] = resumo["Ponto Visado"].astype(str).replace(mapa_simples)
        resumo = resumo[
            [
                "EST",
                "PV",
                "Hz Médio",
                "Hz Reduzido",
                "Média das séries (Hz)",
                "Z Corrigido",
                "Média Z das séries",
                "DH Médio (m)",
            ]
        ]
    else:
        resumo = resumo[
            [
                "Estação",
                "Ponto Visado",
                "Hz Médio",
                "Hz Reduzido",
                "Média das séries (Hz)",
                "Z Corrigido",
                "Média Z das séries",
                "DH Médio (m)",
            ]
        ]
    return resumo


# ---------------------------------------------------------------------
# Triângulo
# ---------------------------------------------------------------------
def _angulo_interno(a: float, b: float, c: float) -> float:
    """
    Retorna o ângulo oposto ao lado 'a', num triângulo com lados a, b, c.
    """
    try:
        if a <= 0 or b <= 0 or c <= 0:
            return float("nan")
        cosA = (b**2 + c**2 - a**2) / (2 * b * c)
        cosA = max(-1.0, min(1.0, cosA))
        return math.degrees(math.acos(cosA))
    except Exception:
        return float("nan")


def calcular_triangulo_duas_linhas(res: pd.DataFrame, idx1: int, idx2: int) -> Optional[Dict]:
    """
    Usa duas linhas de 'res' com mesma EST e PV distintos para montar o triângulo:
      - EST é o vértice da estação (ponto de vista);
      - PV1 e PV2 são os outros dois vértices.
    """
    if idx1 == idx2:
        return None
    if idx1 < 0 or idx1 >= len(res) or idx2 < 0 or idx2 >= len(res):
        return None

    r1 = res.iloc[idx1]
    r2 = res.iloc[idx2]

    est1, est2 = str(r1["EST"]), str(r2["EST"])
    pv1, pv2 = str(r1["PV"]), str(r2["PV"])

    if est1 != est2:
        return None
    if pv1 == pv2:
        return None

    est = est1

    AB = float(r1["DH_med_m"])  # EST–PV1
    AC = float(r2["DH_med_m"])  # EST–PV2

    hz1 = float(r1["Hz_med_deg"])
    hz2 = float(r2["Hz_med_deg"])

    ang_A_deg = (hz2 - hz1) % 360.0
    if ang_A_deg > 180.0:
        ang_A_deg = 360.0 - ang_A_deg

    BC = math.sqrt(
        AB**2 + AC**2 - 2 * AB * AC * math.cos(math.radians(ang_A_deg))
    )

    ang_B_deg = _angulo_interno(AC, AB, BC)
    ang_C_deg = _angulo_interno(AB, AC, BC)

    s = (AB + AC + BC) / 2.0
    area = math.sqrt(max(s * (s - AB) * (s - AC) * (s - BC), 0.0))

    info: Dict[str, object] = {
        "EST": est,
        "PV1": pv1,
        "PV2": pv2,
        "AB": AB,
        "AC": AC,
        "BC": BC,
        "ang_A_deg": ang_A_deg,
        "ang_B_deg": ang_B_deg,
        "ang_C_deg": ang_C_deg,
        "area_m2": area,
    }

    mapa_p_letra = {"P1": "A", "P2": "B", "P3": "C"}

    lados_reais = [
        (est, pv1, AB),
        (est, pv2, AC),
        (pv1, pv2, BC),
    ]
    lados_rotulados = []
    for p_ini, p_fim, val in lados_reais:
        letra_ini = mapa_p_letra.get(p_ini, p_ini)
        letra_fim = mapa_p_letra.get(p_fim, p_fim)
        rot = f"{letra_ini}{letra_fim}"
        lados_rotulados.append((rot, p_ini, p_fim, val))

    angulos_reais = [
        (est, ang_A_deg),
        (pv1, ang_B_deg),
        (pv2, ang_C_deg),
    ]
    angulos_rotulados = []
    for p_nome, val in angulos_reais:
        letra = mapa_p_letra.get(p_nome, p_nome)
        angulos_rotulados.append((letra, p_nome, val))

    lados_ordenados = sorted(lados_rotulados, key=lambda x: x[3], reverse=True)
    angulos_ordenados = sorted(angulos_rotulados, key=lambda x: x[2], reverse=True)

    info["lados_ordenados"] = lados_ordenados
    info["angulos_ordenados"] = angulos_ordenados
    info["mapa_p_letra"] = mapa_p_letra

    return info


# ---------------------------------------------------------------------
# Seleção automática de linhas para formar o triângulo
# ---------------------------------------------------------------------
def selecionar_linhas_por_estacao_e_conjunto(
    res: pd.DataFrame, estacao_letra: str, conjunto: str
) -> Optional[Tuple[int, int]]:
    """
    Seleciona automaticamente duas linhas de 'res' para o triângulo, conforme
    estação (A,B,C) e conjunto (1ª,2ª,3ª).
    """
    letra_to_p = {"A": "P1", "B": "P2", "C": "P3"}
    est_ref = letra_to_p.get(estacao_letra)
    if est_ref is None:
        return None

    ordem_map = {"1ª leitura": 1, "2ª leitura": 2, "3ª leitura": 3}
    ordem = ordem_map.get(conjunto)
    if ordem is None:
        return None

    df = res.reset_index(drop=False).rename(columns={"index": "_idx_orig"})

    if est_ref == "P1":  # Estação A
        if ordem == 1:
            mask = (df["EST"] == "P2") & (df["PV"].isin(["P3", "P1"]))
        else:
            mask = (df["EST"] == "P1") & (df["PV"].isin(["P2", "P3"]))
    elif est_ref == "P2":  # Estação B
        mask = (df["EST"] == "P2") & (df["PV"].isin(["P3", "P1"]))
    else:  # P3, Estação C
        mask = (df["EST"] == "P3") & (df["PV"].isin(["P1", "P2"]))

    cand = df[mask].sort_values(by="_idx_orig")
    if len(cand) < 2:
        return None

    cand = cand.reset_index(drop=True)
    cand["par_id"] = cand.index // 2

    par_desejado = ordem - 1
    par = cand[cand["par_id"] == par_desejado]
    if len(par) < 2:
        return None

    idxs = par["_idx_orig"].tolist()[:2]
    return int(idxs[0]), int(idxs[1])


# ---------------------------------------------------------------------
# Modelo Excel (duas abas)
# ---------------------------------------------------------------------
def gerar_modelo_excel_bytes() -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df_id = pd.DataFrame(
            {
                "Campo": [
                    "Professor(a)",
                    "Equipamento",
                    "Dados",
                    "Local",
                    "Patrimônio",
                ],
                "Valor": ["", "", "", "", ""],
            }
        )
        df_id.to_excel(writer, sheet_name="Identificação", index=False)

        df_dados = pd.DataFrame(
            {
                "EST": ["P1", "P1", "P1", "P1"],
                "PV": ["P2", "P3", "P2", "P3"],
                "SEQ": [1, 1, 2, 2],
                "Hz_PD": ["00°00'00\"", "18°58'22\"", "00°01'01\"", "18°59'34\""],
                "Hz_PI": ["179°59'48\"", "198°58'14\"", "180°00'45\"", "198°59'24\""],
                "Z_PD": ["90°51'08\"", "90°51'25\"", "90°51'06\"", "90°51'24\""],
                "Z_PI": ["269°08'52\"", "269°08'33\"", "269°08'50\"", "269°08'26\""],
                "DI_PD": [25.365, 26.285, 25.365, 26.285],
                "DI_PI": [25.365, 26.285, 25.365, 26.285],
            }
        )
        df_dados.to_excel(writer, sheet_name="Dados", index=False)
    buf.seek(0)
    return buf.getvalue()
