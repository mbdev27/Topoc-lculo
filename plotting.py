# plotting.py
# Funções de plotagem e exportação

import io
import math
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd

from processing import decimal_to_dms


def plotar_triangulo_info(info: Dict, estacao_op: str, conjunto_op: str):
    """
    Desenha o triângulo em planta.

    Conceito geométrico / didático:
      - Pontos reais: P1, P2, P3.
      - Letras didáticas: A=P1, B=P2, C=P3.

    Usamos os comprimentos dos lados:
      - AB ≡ P1–P2
      - AC ≡ P1–P3
      - BC ≡ P2–P3

    Para manter a leitura visual, no caso específico de:
      - Estação selecionada = A
      - Conjunto de leituras = 1ª leitura
    aplicamos uma reflexão no eixo X para evitar que o triângulo pareça
    "de costas" para o observador.
    """
    # Pontos didáticos
    A_ponto = "P1"
    B_ponto = "P2"
    C_ponto = "P3"

    # Comprimentos dos lados
    AB = info["AB"]  # interpretado como P1–P2
    AC = info["AC"]  # interpretado como P1–P3
    BC = info["BC"]  # interpretado como P2–P3

    # Coordenadas base: colocamos A (P1) na origem e C (P3) sobre o eixo X.
    x_A, y_A = 0.0, 0.0
    x_C, y_C = AC, 0.0

    if AC == 0:
        x_B, y_B = AB, 0.0
    else:
        # Fórmulas clássicas para o terceiro vértice de um triângulo
        x_B = (AB**2 - BC**2 + AC**2) / (2 * AC)
        arg = max(AB**2 - x_B**2, 0.0)
        y_B = math.sqrt(arg)

    # ---------------------------------------------------------
    # Caso especial: Estação A + 1ª leitura → refletir em X
    # ---------------------------------------------------------
    if estacao_op == "A" and conjunto_op == "1ª leitura":
        x_A, x_B, x_C = -x_A, -x_B, -x_C

    xs = [x_A, x_B, x_C, x_A]
    ys = [y_A, y_B, y_C, y_A]

    fig, ax = plt.subplots()
    ax.plot(xs, ys, "-o", color="#7f0000")
    ax.set_facecolor("#ffffff")
    fig.patch.set_facecolor("#ffffff")
    ax.set_aspect("equal", "box")

    # Rótulos dos vértices com letras e pontos reais
    ax.text(x_A, y_A, f"{A_ponto} (A)", fontsize=10, color="#111827")
    ax.text(x_B, y_B, f"{B_ponto} (B)", fontsize=10, color="#111827")
    ax.text(x_C, y_C, f"{C_ponto} (C)", fontsize=10, color="#111827")

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
        "Representação do triângulo em planta (A=P1, B=P2, C=P3)",
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
                    "Lado A–B (P1–P2)",
                    "Lado A–C (P1–P3)",
                    "Lado B–C (P2–P3)",
                    "Ângulo interno em A (P1)",
                    "Ângulo interno em B (P2)",
                    "Ângulo interno em C (P3)",
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
