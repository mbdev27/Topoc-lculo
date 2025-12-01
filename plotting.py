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

    - O vértice em (0,0) é info["EST"] (P1, P2 ou P3),
      já definido em processing.calcular_triangulo_duas_linhas.
    - Os outros vértices são PV1 e PV2.
    - Rótulos apenas P1, P2, P3.
    """
    est = info["EST"]
    pv1 = info["PV1"]
    pv2 = info["PV2"]

    AB = info["AB"]  # EST–PV1
    AC = info["AC"]  # EST–PV2
    BC = info["BC"]  # PV1–PV2

    x_E, y_E = 0.0, 0.0
    x_V2, y_V2 = AC, 0.0  # segundo visado no eixo X

    if AC == 0:
        x_V1, y_V1 = AB, 0.0
    else:
        x_V1 = (AB**2 - BC**2 + AC**2) / (2 * AC)
        arg = max(AB**2 - x_V1**2, 0.0)
        y_V1 = math.sqrt(arg)

    xs = [x_E, x_V1, x_V2, x_E]
    ys = [y_E, y_V1, y_V2, y_E]

    fig, ax = plt.subplots()
    ax.plot(xs, ys, "-o", color="#7f0000")
    ax.set_facecolor("#ffffff")
    fig.patch.set_facecolor("#ffffff")
    ax.set_aspect("equal", "box")

    ax.text(x_E, y_E, f"{est}", fontsize=10, color="#111827")
    ax.text(x_V1, y_V1, f"{pv1}", fontsize=10, color="#111827")
    ax.text(x_V2, y_V2, f"{pv2}", fontsize=10, color="#111827")

    ax.text(
        (x_E + x_V1) / 2,
        (y_E + y_V1) / 2,
        f"{est}–{pv1} = {AB:.3f} m",
        color="#374151",
        fontsize=9,
    )
    ax.text(
        (x_E + x_V2) / 2,
        (y_E + y_V2) / 2,
        f"{est}–{pv2} = {AC:.3f} m",
        color="#374151",
        fontsize=9,
    )
    ax.text(
        (x_V1 + x_V2) / 2,
        (y_V1 + y_V2) / 2,
        f"{pv1}–{pv2} = {BC:.3f} m",
        color="#374151",
        fontsize=9,
    )

    ax.set_xlabel("X (m)", color="#111827")
    ax.set_ylabel("Y (m)", color="#111827")
    ax.tick_params(colors="#111827")
    ax.grid(True, linestyle="--", alpha=0.3, color="#9ca3af")
    ax.set_title(
        "Representação do triângulo em planta (ponto de vista na estação)",
        color="#111827",
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="jpg", dpi=200, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf, fig


def gerar_xlsx_com_figura(info_triangulo: Dict, figura_buf: io.BytesIO) -> bytes:
    """
    Gera um XLSX com resumo numérico e a figura do triângulo.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        wb = writer.book

        df_resumo = pd.DataFrame(
            {
                "Descrição": [
                    "Lado estação–PV1",
                    "Lado estação–PV2",
                    "Lado PV1–PV2",
                    "Ângulo interno na estação",
                    "Ângulo interno no PV1",
                    "Ângulo interno no PV2",
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
