# utils.py
import numpy as np


def dms_to_decimal(dms_str: str) -> float:
    """
    Converte uma string DMS do tipo 145°47′33′′ ou 145°47'33" para graus decimais.
    Também aceita valores já em decimal (string com ponto).
    """
    if dms_str is None:
        raise ValueError("Valor DMS None")

    s = str(dms_str).strip()

    # Se já aparenta ser decimal (tem ponto), tenta converter direto
    if "." in s and "°" not in s and "'" not in s and "′" not in s:
        return float(s.replace(",", "."))

    # Normalizar símbolos
    s = s.replace("′", "'").replace("’’", '"').replace("″", '"').replace("’", "'")

    # Separar graus
    if "°" not in s:
        raise ValueError(f"Formato DMS inválido: {s}")

    graustr, resto = s.split("°", 1)
    graus = float(graustr.strip())

    minutos = 0.0
    segundos = 0.0

    if "'" in resto:
        minstr, resto2 = resto.split("'", 1)
        minutos = float(minstr.strip())
        if '"' in resto2:
            segstr = resto2.split('"', 1)[0]
            segstr = segstr.replace("''", "").strip()
            if segstr:
                segundos = float(segstr)
    else:
        # Se não tiver minuto, tenta achar segundos direto
        if '"' in resto:
            segstr = resto.split('"', 1)[0]
            segstr = segstr.strip()
            if segstr:
                segundos = float(segstr)

    sinal = 1.0
    if graus < 0:
        sinal = -1.0
        graus = abs(graus)

    dec = graus + minutos / 60.0 + segundos / 3600.0
    return sinal * dec


def decimal_to_dms(dec: float):
    """
    Converte graus decimais para (graus, minutos, segundos).
    """
    sinal = -1 if dec < 0 else 1
    dec = abs(dec)

    g = int(dec)
    resto = (dec - g) * 60.0
    m = int(resto)
    s = (resto - m) * 60.0

    g *= sinal
    return g, m, s


def dms_str(dec: float) -> str:
    """
    Retorna string formatada G°M'S" a partir de graus decimais.
    """
    g, m, s = decimal_to_dms(dec)
    return f"{g:d}°{abs(m):02d}'{abs(s):05.2f}\""


def dms_str_inteiro(dec: float) -> str:
    """
    Versão com segundos inteiros, para visual mais limpo.
    """
    g, m, s = decimal_to_dms(dec)
    s_rounded = int(round(abs(s)))
    # Ajustar estouro 60"
    if s_rounded == 60:
        s_rounded = 0
        m = abs(m) + 1
        if m == 60:
            m = 0
            g = g + 1 if g >= 0 else g - 1
    return f"{g:d}°{abs(m):02d}'{s_rounded:02d}\""


def media_angular_graus(valores_graus):
    """
    Média vetorial de ângulos em graus.
    Retorna média em graus no intervalo [0, 360).
    """
    ang_rad = np.deg2rad(valores_graus)
    c = np.cos(ang_rad).mean()
    s = np.sin(ang_rad).mean()
    media_rad = np.arctan2(s, c)
    media_deg = np.rad2deg(media_rad)
    if media_deg < 0:
        media_deg += 360.0
    return media_deg


def desvio_padrao_angular_graus(valores_graus):
    """
    Desvio padrão aproximado de ângulos em graus:
    calcula diferença mínima em relação à média (no círculo) e faz std desses erros.
    """
    if len(valores_graus) < 2:
        return 0.0

    media = media_angular_graus(valores_graus)
    diffs = []
    for v in valores_graus:
        d = v - media
        # normalizar para [-180, 180]
        while d > 180:
            d -= 360
        while d < -180:
            d += 360
        diffs.append(d)
    return float(np.std(diffs, ddof=1))


def resumo_angulos(A_deg: float, B_deg: float, C_deg: float):
    """
    Retorna (soma_em_graus, desvio_em_graus).
    """
    soma = A_deg + B_deg + C_deg
    desvio = soma - 180.0
    return soma, desvio
