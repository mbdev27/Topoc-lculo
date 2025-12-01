# plotting.py

import io
import math
from typing import Dict

import matplotlib.pyplot as plt

from processing import decimal_to_dms


def plotar_triangulo_info(info: Dict):
    """
    Desenha o triângulo em planta usando a convenção:

      - A: EST
      - B: PV1
      - C: PV2

    Com coordenadas:
      - A em (0, 0)
      - C em (AC, 0)
      - B calculado via lei dos cossenos a partir dos lados AB, AC, BC.

    Isso garante que o ponto de vista de onde parte o desenho é a estação (A).
    """
    A = info["EST"]
    B = info["PV1"]
    C = info["PV2"]

    AB = info["AB"]
    AC = info["AC"]
    BC = info["BC"]

    # Coordenadas em planta
    x_A, y_A = 0.0, 0.0
    x_C, y_C = AC, 0.0

    if AC == 0:
        # Caso degenerado: colocamos B na mesma linha de C
        x_B, y_B = AB, 0.0
    else:
        # Fórmulas clássicas de coordenadas para o terceiro vértice
        x_B = (AB**2 - BC**2 + AC**2) / (2 * AC)
        arg = max(AB**2 - x_B**2, 0.0)
        y_B = math.sqrt(arg)

    xs = [x_A, x_B, x_C, x_A]
    ys = [y_A, y_B, y_C, y_A]

    fig, ax = plt.subplots()
    ax.plot(xs, ys, "-o", color="#7f0000")
    ax.set_facecolor("#ffffff")
    fig.patch.set_facecolor("#ffffff")
    ax.set_aspect("equal", "box")

    # Rótulos dos vértices
    ax.text(x_A, y_A, f"{A} (A)", fontsize=10, color="#111827")
    ax.text(x_B, y_B, f"{B} (B)", fontsize=10, color="#111827")
    ax.text(x_C, y_C, f"{C} (C)", fontsize=10, color="#111827")

    # Rótulos dos lados no meio dos segmentos
    ax.text(
        (x_A + x_B) / 2,
        (y_A + y_B) / 2,
        f"AB = {AB:.3f} m",
        color="#374151",
        fontsize=9,
    )
    ax.text(
        (x_A + x_C) / 2,
        (y_A + y_C) / 2,
        f"AC = {AC:.3f} m",
        color="#374151",
        fontsize=9,
    )
    ax.text(
        (x_B + x_C) / 2,
        (y_B + y_C) / 2,
        f"BC = {BC:.3f} m",
        color="#374151",
        fontsize=9,
    )

    ax.set_xlabel("X (m)", color="#111827")
    ax.set_ylabel("Y (m)", color="#111827")
    ax.tick_params(colors="#111827")
    ax.grid(True, linestyle="--", alpha=0.3, color="#9ca3af")
    ax.set_title("Representação do triângulo em planta (ponto de vista na estação A/B/C)", color="#111827")

    buf = io.BytesIO()
    fig.savefig(buf, format="jpg", dpi=200, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf, fig
