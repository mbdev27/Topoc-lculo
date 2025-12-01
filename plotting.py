# plotting.py
# Funções de plotagem e exportação

import io
import math
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd

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

    Isso garante que o ponto de vista de onde parte o desenho é a estação (A/B/C).
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
    ax.set_title(
        "Representação do triângulo em planta (ponto de vista na estação A/B/C)",
        color="#111827",
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="jpg", dpi=200, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf, fig


def gerar_xlsx_com_figura(info_triangulo: Dict, figura_buf: io.BytesIO) -> bytes:
    """
    Gera um arquivo XLSX com um resumo numérico do triângulo e a figura em outra aba.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        wb = writer.book

        df_resumo = pd.DataFrame(
            {
                "Descrição": [
                    "Lado A–B (EST–PV1)",
                    "Lado A–C (EST–PV2)",
                    "Lado B–C (PV1–PV2)",
                    "Ângulo interno em A (EST)",
                    "Ângulo interno em B (PV1)",
                    "Ângulo interno em C (PV2)",
                    "Área do triângulo (m²)",
                ],
                "Valor": [
                    f"{info_triangulo['AB']:.3f} m",
                    f"{info_triangulo['AC']:.3f} m",
                    f"{info_triangulo['BC']:.3f} m",
                    decimal_to_dms(info_triangulo["ang_A_deg"]),
                    decimal_to_dms(info_triangulo["ang_B_deg"]),
                    decimal_to_dms(info_triangulo["ang_C_deg"]),
                    f"{info_triangulo['area_m2']:.3f}",
                ],
            }
        )
        df_resumo.to_excel(writer, sheet_name="ResumoTriangulo", index=False)

        ws_fig = wb.add_worksheet("FiguraTriangulo")
        writer.sheets["FiguraTriangulo"] = ws_fig
        if figura_buf is not None:
            ws_fig.insert_image("B2", "triangulo.jpg", {"image_data": figura_buf})

    output.seek(0)
    return output.getvalue()
