# plotting.py
# Funções de plotagem e exportação

import io
import math
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd

from processing import decimal_to_dms


def plotar_triangulo_info(info: Dict):
    est = info["EST"]
    pv1 = info["PV1"]
    pv2 = info["PV2"]

    b = info["b_EST_PV1"]
    c = info["c_EST_PV2"]
    a = info["a_PV1_PV2"]

    x_est, y_est = 0.0, 0.0
    x_pv2, y_pv2 = c, 0.0

    if c == 0:
        x_pv1, y_pv1 = b, 0.0
    else:
        x_pv1 = (b**2 - a**2 + c**2) / (2 * c)
        arg = max(b**2 - x_pv1**2, 0.0)
        y_pv1 = math.sqrt(arg)

    xs = [x_est, x_pv1, x_pv2, x_est]
    ys = [y_est, y_pv1, y_pv2, y_est]

    fig, ax = plt.subplots()
    ax.plot(xs, ys, "-o", color="#7f0000")
    ax.set_facecolor("#ffffff")
    fig.patch.set_facecolor("#ffffff")
    ax.set_aspect("equal", "box")

    ax.text(x_est, y_est, f" {est}", fontsize=10, color="#111827")
    ax.text(x_pv1, y_pv1, f" {pv1}", fontsize=10, color="#111827")
    ax.text(x_pv2, y_pv2, f" {pv2}", fontsize=10, color="#111827")

    ax.text((x_est + x_pv1) / 2, (y_est + y_pv1) / 2,
            f"{b:.3f} m", color="#374151", fontsize=9)
    ax.text((x_est + x_pv2) / 2, (y_est + y_pv2) / 2,
            f"{c:.3f} m", color="#374151", fontsize=9)
    ax.text((x_pv1 + x_pv2) / 2, (y_pv1 + y_pv2) / 2,
            f"{a:.3f} m", color="#374151", fontsize=9)

    ax.set_xlabel("X (m)", color="#111827")
    ax.set_ylabel("Y (m)", color="#111827")
    ax.tick_params(colors="#111827")
    ax.grid(True, linestyle="--", alpha=0.3, color="#9ca3af")
    ax.set_title("Representação do triângulo em planta", color="#111827")

    buf = io.BytesIO()
    fig.savefig(buf, format="jpg", dpi=200, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf, fig


def gerar_xlsx_com_figura(info_triangulo: Dict, figura_buf: io.BytesIO) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        wb = writer.book

        df_resumo = pd.DataFrame(
            {
                "Descrição": [
                    "Lado EST–PV1",
                    "Lado EST–PV2",
                    "Lado PV1–PV2",
                    "Ângulo interno em P1",
                    "Ângulo interno em P2",
                    "Ângulo interno em P3",
                    "Área do triângulo (m²)",
                ],
                "Valor": [
                    f"{info_triangulo['b_EST_PV1']:.3f} m",
                    f"{info_triangulo['c_EST_PV2']:.3f} m",
                    f"{info_triangulo['a_PV1_PV2']:.3f} m",
                    decimal_to_dms(info_triangulo["ang_P1_deg"]),
                    decimal_to_dms(info_triangulo["ang_P2_deg"]),
                    decimal_to_dms(info_triangulo["ang_P3_deg"]),
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
