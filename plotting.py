# plotting.py
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import math
import numpy as np
import pandas as pd

from processing import (
    PARES_TRI,
    PONTOS_TRI,
    angulo_oposto,
)
from utils import resumo_angulos


def construir_coords_approx(df_par: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
    """
    Gera coordenadas aproximadas (locais) para os pontos P1, P2, P3 a partir das
    médias por par EST–PV (df_par), assumindo:
      - P1 em (0,0);
      - Usa DH_med_m_par e Hz_med_deg_par para ir propagando coordenadas.
    """
    coords: Dict[str, Tuple[float, float]] = {"P1": (0.0, 0.0)}

    def add_coord_from(est, pv, dh, hz_deg):
        est_ = str(est).strip().upper()
        pv_ = str(pv).strip().upper()
        if est_ not in coords:
            return
        x_est, y_est = coords[est_]
        az = math.radians(hz_deg)
        dx = dh * math.sin(az)
        dy = dh * math.cos(az)
        x_new = x_est + dx
        y_new = y_est + dy
        if pv_ in coords:
            x_old, y_old = coords[pv_]
            coords[pv_] = ((x_old + x_new) / 2.0, (y_old + y_new) / 2.0)
        else:
            coords[pv_] = (x_new, y_new)

    for _, row in df_par.iterrows():
        if str(row["EST"]).strip().upper() == "P1":
            add_coord_from(row["EST"], row["PV"], row["DH_med_m_par"], row["Hz_med_deg_par"])

    for _ in range(3):
        for _, row in df_par.iterrows():
            add_coord_from(row["EST"], row["PV"], row["DH_med_m_par"], row["Hz_med_deg_par"])

    return coords


def plot_triangulo_medio(coords, lados, angulos):
    """
    Plota triângulo médio P1–P2–P3 em cima das coordenadas 'coords'.
    Retorna fig, ax.
    """
    fig, ax = plt.subplots(figsize=(5, 5))

    # espalha todos os pontos conhecidos
    for nome, (x, y) in coords.items():
        cor = "darkred" if nome == "P1" else "navy"
        ax.scatter(x, y, color=cor, s=40, zorder=3)
        ax.text(x, y, f" {nome}", fontsize=9, va="bottom", ha="left")

    pA, pB, pC = "P1", "P2", "P3"
    xA, yA = coords[pA]
    xB, yB = coords[pB]
    xC, yC = coords[pC]
    ax.plot([xA, xB], [yA, yB], "-k", linewidth=1.8, label="Triângulo médio")
    ax.plot([xB, xC], [yB, yC], "-k", linewidth=1.8)
    ax.plot([xA, xC], [yA, yC], "-k", linewidth=1.8)

    ax.set_aspect("equal", "box")
    ax.set_xlabel("X local (m)")
    ax.set_ylabel("Y local (m)")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="best")

    return fig, ax


def construir_triangulo_especifico(df_par: pd.DataFrame):
    """
    Monta coordenadas de um triângulo abstrato P1–P3–P2 usando as médias
    dos pares P1⇒P3, P3⇒P2 e P2⇒P1 (se existirem no df_par).
    Retorna:
      - coords_tri: dict {P1, P3, P2: (x,y)}
      - distâncias (P1P3, P3P2, P2P1)
      - ângulos internos (ang_P1, ang_P3, ang_P2)
      - área do triângulo
    Lança ValueError se faltar algum par ou distância for 0/NaN.
    """
    df3 = df_par[
        df_par["EST"].isin(PONTOS_TRI) & df_par["PV"].isin(PONTOS_TRI)
    ].copy()
    if df3.empty:
        raise ValueError("Não há médias suficientes entre P1, P2 e P3.")

    df3["par"] = df3["EST"].astype(str).str.upper() + "⇒" + df3["PV"].astype(str).str.upper()
    pares_disponiveis = set(df3["par"].unique())
    if not all(p in pares_disponiveis for p in PARES_TRI):
        raise ValueError("Faltam médias para P1⇒P3, P3⇒P2 ou P2⇒P1.")

    def dh_med_par(par_str):
        sub = df3[df3["par"] == par_str]
        if sub.empty:
            return float("nan")
        return float(sub["DH_med_m_par"].iloc[0])

    L13 = dh_med_par("P1⇒P3")  # P1–P3
    L32 = dh_med_par("P3⇒P2")  # P3–P2
    L21 = dh_med_par("P2⇒P1")  # P2–P1

    if any(np.isnan(v) or v == 0 for v in [L13, L32, L21]):
        raise ValueError("Alguma das distâncias médias P1–P3, P3–P2 ou P2–P1 é nula ou NaN.")

    # Triângulo abstrato P1–P3–P2
    a = L32  # lado oposto a P1
    b = L21  # lado oposto a P3
    c = L13  # lado oposto a P2

    coords_tri = {
        "P1": (0.0, 0.0),
        "P3": (c, 0.0),
    }

    cos_A = max(-1.0, min(1.0, (b ** 2 + c ** 2 - a ** 2) / (2 * b * c)))
    ang_A_rad = math.acos(cos_A)
    x2 = b * math.cos(ang_A_rad)
    y2 = b * math.sin(ang_A_rad)
    coords_tri["P2"] = (x2, y2)

    def dist_t(p, q):
        x1, y1 = coords_tri[p]
        x2_, y2_ = coords_tri[q]
        return math.hypot(x2_ - x1, y2_ - y1)

    d_P1P3 = dist_t("P1", "P3")
    d_P3P2 = dist_t("P3", "P2")
    d_P2P1 = dist_t("P2", "P1")

    ang_P1 = angulo_oposto(d_P3P2, d_P1P3, d_P2P1)
    ang_P3 = angulo_oposto(d_P2P1, d_P1P3, d_P3P2)
    ang_P2 = angulo_oposto(d_P1P3, d_P2P1, d_P3P2)

    soma_ang, desvio = resumo_angulos(ang_P1, ang_P3, ang_P2)
    s_ = (d_P1P3 + d_P3P2 + d_P2P1) / 2.0
    area_ = math.sqrt(max(0.0, s_ * (s_ - d_P1P3) * (s_ - d_P3P2) * (s_ - d_P2P1)))

    return (
        coords_tri,
        (d_P1P3, d_P3P2, d_P2P1),
        (ang_P1, ang_P3, ang_P2),
        soma_ang,
        desvio,
        area_,
    )


def plot_triangulo_especifico(coords_tri, dists, angulos):
    """
    Plota triângulo específico P1–P3–P2, com anotações de lados e ângulos.
    Retorna fig, ax.
    """
    (d_P1P3, d_P3P2, d_P2P1) = dists
    (ang_P1, ang_P3, ang_P2) = angulos

    fig, ax = plt.subplots(figsize=(5, 5))

    # desenha triângulo
    x1, y1 = coords_tri["P1"]
    x3, y3 = coords_tri["P3"]
    x2, y2 = coords_tri["P2"]

    ax.plot([x1, x3], [y1, y3], "-k", linewidth=1.8, label="Triângulo escolhido")
    ax.plot([x3, x2], [y3, y2], "-k", linewidth=1.8)
    ax.plot([x2, x1], [y2, y1], "-k", linewidth=1.8)

    # vértices
    for nome, (x, y) in coords_tri.items():
        cor = {"P1": "red", "P2": "blue", "P3": "green"}.get(nome, "navy")
        ax.scatter(x, y, color=cor, s=55, zorder=4)
        ax.text(x, y, f" {nome}", fontsize=10, va="bottom", ha="left")

    # meios dos lados
    def meio(Pa, Pb):
        xA, yA = coords_tri[Pa]
        xB, yB = coords_tri[Pb]
        return (xA + xB) / 2.0, (yA + yB) / 2.0

    mx_13, my_13 = meio("P1", "P3")
    mx_32, my_32 = meio("P3", "P2")
    mx_21, my_21 = meio("P2", "P1")

    ax.text(mx_13, my_13, f"P1–P3 = {d_P1P3:.4f} m", fontsize=8, color="black", ha="center", va="bottom")
    ax.text(mx_32, my_32, f"P3–P2 = {d_P3P2:.4f} m", fontsize=8, color="black", ha="center", va="bottom")
    ax.text(mx_21, my_21, f"P2–P1 = {d_P2P1:.4f} m", fontsize=8, color="black", ha="center", va="bottom")

    # ângulos junto aos vértices
    ax.text(x1, y1, f" ∠P1 = {ang_P1:.4f}°", fontsize=8, color="darkred", ha="left", va="top")
    ax.text(x3, y3, f" ∠P3 = {ang_P3:.4f}°", fontsize=8, color="darkgreen", ha="right", va="bottom")
    ax.text(x2, y2, f" ∠P2 = {ang_P2:.4f}°", fontsize=8, color="darkblue", ha="left", va="bottom")

    ax.set_aspect("equal", "box")
    ax.set_xlabel("X local (m)")
    ax.set_ylabel("Y local (m)")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="best")

    return fig, ax
