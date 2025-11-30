# utils.py
import math
import re
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

# Regex para parsing de ângulos
ANGLE_RE = re.compile(r"(-?\d+)[^\d\-]+(\d+)[^\d\-]+(\d+(?:[.,]\d+)?)")
NUM_RE = re.compile(r"^-?\d+(?:[.,]\d+)?$")


def parse_angle_to_decimal(x: Any) -> float:
    """
    Converte ângulo em diferentes formatos (DMS, decimal com símbolos, etc.)
    para graus decimais. Retorna NaN se não conseguir interpretar.
    """
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float)):
        return float(x)

    s = str(x).strip()
    if s == "":
        return np.nan

    # Normalização de caracteres
    s = (
        s.replace("º", "°")
        .replace("\u2019", "'")
        .replace("\u201d", '"')
        .replace(":", " ")
        .replace("\t", " ")
    )
    s = re.sub(r"\s+", " ", s)

    # Tenta padrão DMS
    m = ANGLE_RE.search(s)
    if m:
        deg = float(m.group(1))
        minu = float(m.group(2))
        sec = float(m.group(3).replace(",", "."))
        sign = -1 if deg < 0 else 1
        return sign * (abs(deg) + minu / 60.0 + sec / 3600.0)

    # Tenta número simples decimal
    if NUM_RE.match(s.replace(" ", "")):
        return float(s.replace(",", "."))

    # Tenta extrair 3 números como D M S
    nums = re.findall(r"-?\d+(?:[.,]\d+)?", s)
    if len(nums) == 3:
        deg, minu, sec = nums
        deg = float(deg)
        minu = float(minu)
        sec = float(str(sec).replace(",", "."))
        sign = -1 if deg < 0 else 1
        return sign * (abs(deg) + minu / 60.0 + sec / 3600.0)

    return np.nan


def decimal_to_dms(angle: float) -> str:
    """Converte ângulo em graus decimais para string DMS (00°00'00")."""
    if pd.isna(angle):
        return ""
    a = float(angle) % 360.0
    g = int(math.floor(a))
    m_f = (a - g) * 60.0
    m = int(math.floor(m_f))
    s_f = (m_f - m) * 60.0
    s = int(round(s_f))

    # Ajustes de borda
    if s >= 60:
        s = 0
        m += 1
    if m >= 60:
        m = 0
        g += 1

    return f"{g:02d}°{m:02d}'{s:02d}\""


def mean_direction_two(a_deg: float, b_deg: float) -> float:
    """
    Média vetorial de duas direções em graus decimais (resolve problema 359° / 1°).
    Retorna NaN se algum for NaN ou se o vetor resultar em (0,0).
    """
    if pd.isna(a_deg) or pd.isna(b_deg):
        return np.nan
    a_rad = math.radians(a_deg)
    b_rad = math.radians(b_deg)
    x = math.cos(a_rad) + math.cos(b_rad)
    y = math.sin(a_rad) + math.sin(b_rad)
    if x == 0 and y == 0:
        return np.nan
    ang = math.degrees(math.atan2(y, x))
    return ang % 360.0


def mean_direction_list(angles_deg: List[float]) -> float:
    """
    Média vetorial de uma lista de direções em graus (para médias por par EST–PV).
    Ignora valores NaN.
    """
    vals = [float(a) for a in angles_deg if not pd.isna(a)]
    if len(vals) == 0:
        return np.nan
    x = sum(math.cos(math.radians(a)) for a in vals)
    y = sum(math.sin(math.radians(a)) for a in vals)
    if x == 0 and y == 0:
        return np.nan
    ang = math.degrees(math.atan2(y, x))
    return ang % 360.0


def classificar_re_vante(
    est: str,
    pv: str,
    ref_por_estacao: Dict[str, str]
) -> str:
    """
    Retorna 'Ré', 'Vante' ou '' (se não souber classificar) com base em um dicionário
    de ponto de referência por estação.
    """
    est_ = str(est).strip().upper()
    pv_ = str(pv).strip().upper()
    ref = ref_por_estacao.get(est_)
    if ref is None:
        return ""
    return "Ré" if pv_ == ref else "Vante"


def resumo_angulos(angA: float, angB: float, angC: float) -> Tuple[float, float]:
    """
    Retorna (soma, desvio) dos ângulos internos de um triângulo.
    Desvio = soma - 180°.
    """
    soma = angA + angB + angC
    desvio = soma - 180.0
    return soma, desvio
