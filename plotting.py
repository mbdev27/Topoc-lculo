# plotagem.py
import matplotlib.pyplot as plt
import numpy as np

from utils import dms_str_inteiro


def plot_triangulo_medio(lados, angulos):
    """
    Desenha triângulo médio com vértices A=P1, B=P2, C=P3.
    Usa lados A, B, C (opostos a A,B,C) já em metros.
    """
    A = lados["A"]
    B = lados["B"]
    C = lados["C"]

    # Coordenadas: A=P1, B=P2, C=P3
    P1 = np.array([0.0, 0.0])
    P2 = np.array([C, 0.0])  # lado C é P1-P2

    # Para P3 (C): lado P1-P3 = B, P2-P3 = A
    x = (B**2 - A**2 + C**2) / (2 * C)
    y_sq = B**2 - x**2
    y = np.sqrt(max(y_sq, 0.0))
    P3 = np.array([x, y])

    fig, ax = plt.subplots(figsize=(6, 5))

    # Desenhar lados
    xs = [P1[0], P2[0], P3[0], P1[0]]
    ys = [P1[1], P2[1], P3[1], P1[1]]
    ax.plot(xs, ys, "-o", color="#7d1220", linewidth=2, markersize=6)

    # Rótulos dos vértices
    ax.text(P1[0] - 0.2, P1[1] - 0.2, "P1", fontsize=10, color="#111827")
    ax.text(P2[0] + 0.2, P2[1] - 0.2, "P2", fontsize=10, color="#111827")
    ax.text(P3[0], P3[1] + 0.2, "P3", fontsize=10, color="#111827")

    # Comprimentos dos lados, em metros, no meio de cada segmento
    P1P2_mid = 0.5 * (P1 + P2)
    P2P3_mid = 0.5 * (P2 + P3)
    P3P1_mid = 0.5 * (P3 + P1)

    ax.text(
        P1P2_mid[0],
        P1P2_mid[1] - 0.2,
        f"{C:.3f} m",
        fontsize=9,
        color="#374151",
        ha="center",
    )
    ax.text(
        P2P3_mid[0] + 0.1,
        P2P3_mid[1],
        f"{A:.3f} m",
        fontsize=9,
        color="#374151",
        ha="center",
    )
    ax.text(
        P3P1_mid[0] - 0.1,
        P3P1_mid[1],
        f"{B:.3f} m",
        fontsize=9,
        color="#374151",
        ha="center",
    )

    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title("Triângulo médio P1–P2–P3", fontsize=11)
    ax.grid(True, alpha=0.3)

    return fig, ax


def plot_triangulo_especifico(coords_tri, d_lados, angulos):
    """
    Desenha triângulo específico com vértices P1, P3, P2.
    d_lados = (d13, d32, d21)
    angulos = (ang_P1, ang_P3, ang_P2)
    """
    P1 = coords_tri["P1"]
    P3 = coords_tri["P3"]
    P2 = coords_tri["P2"]

    d13, d32, d21 = d_lados
    ang_P1, ang_P3, ang_P2 = angulos

    fig, ax = plt.subplots(figsize=(6, 5))

    xs = [P1[0], P3[0], P2[0], P1[0]]
    ys = [P1[1], P3[1], P2[1], P1[1]]
    ax.plot(xs, ys, "-o", color="#7d1220", linewidth=2, markersize=6)

    # Rótulos dos vértices
    ax.text(P1[0] - 0.2, P1[1] - 0.2, "P1", fontsize=10, color="#111827")
    ax.text(P3[0] + 0.2, P3[1] - 0.2, "P3", fontsize=10, color="#111827")
    ax.text(P2[0], P2[1] + 0.2, "P2", fontsize=10, color="#111827")

    # Rótulos de comprimentos (m)
    P1P3_mid = 0.5 * (P1 + P3)
    P3P2_mid = 0.5 * (P3 + P2)
    P2P1_mid = 0.5 * (P2 + P1)

    ax.text(
        P1P3_mid[0],
        P1P3_mid[1] - 0.2,
        f"{d13:.3f} m",
        fontsize=9,
        color="#374151",
        ha="center",
    )
    ax.text(
        P3P2_mid[0] + 0.1,
        P3P2_mid[1],
        f"{d32:.3f} m",
        fontsize=9,
        color="#374151",
        ha="center",
    )
    ax.text(
        P2P1_mid[0] - 0.1,
        P2P1_mid[1],
        f"{d21:.3f} m",
        fontsize=9,
        color="#374151",
        ha="center",
    )

    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title("Triângulo específico (P1⇒P3, P3⇒P2, P2⇒P1)", fontsize=11)
    ax.grid(True, alpha=0.3)

    return fig, ax
