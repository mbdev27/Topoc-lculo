# plotting.py
# Funções de plotagem e exportação

import io
import math
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd

from processing import decimal_to_dms


def _nome_para_ordem(ponto: str) -> int:
    """Ordem cíclica P1 < P2 < P3 para organizar os rótulos em sentido horário."""
    ordem = {"P1": 0, "P2": 1, "P3": 2}
    return ordem.get(ponto, 99)


def plotar_triangulo_info(info: Dict, estacao_op: str, conjunto_op: str):
    """
    Desenha o triângulo em planta.

    - O vértice na origem (0,0) é SEMPRE o ponto real da estação usada nas leituras: info["EST"]
      (pode ser P1, P2 ou P3).
    - Os outros dois vértices são info["PV1"] e info["PV2"].
    - Rótulos gráficos exibem apenas P1, P2 e P3 (sem letras A/B/C).
    """
    est = info["EST"]   # ponto estação (ex.: P1)
    pv1 = info["PV1"]   # ponto visado 1 (P2 ou P3)
    pv2 = info["PV2"]   # ponto visado 2 (P2 ou P3)

    # Comprimentos dos lados tal como calculados
    AB = info["AB"]  # EST–PV1
    AC = info["AC"]  # EST–PV2
    BC = info["BC"]  # PV1–PV2

    # Colocamos a estação EST na origem (0,0) – PONTO DE VISTA
    x_E, y_E = 0.0, 0.0
    x_V2, y_V2 = AC, 0.0  # segundo visado em cima do eixo X

    if AC == 0:
        x_V1, y_V1 = AB, 0.0
    else:
        x_V1 = (AB**2 - BC**2 + AC**2) / (2 * AC)
        arg = max(AB**2 - x_V1**2, 0.0)
        y_V1 = math.sqrt(arg)

    # Ordena os dois visados para uma leitura visual mais natural:
    # queremos que, ao girar no sentido horário, eles sigam a sequência P1,P2,P3.
    visados = [
        ("pv1", pv1, x_V1, y_V1),
        ("pv2", pv2, x_V2, y_V2),
    ]
    visados.sort(key=lambda t: _nome_para_ordem(t[1]))

    (tag1, nome1, x1, y1), (tag2, nome2, x2, y2) = visados

    xs = [x_E, x1, x2, x_E]
    ys = [y_E, y1, y2, y_E]

    fig, ax = plt.subplots()
    ax.plot(xs, ys, "-o", color="#7f0000")
    ax.set_facecolor("#ffffff")
    fig.patch.set_facecolor("#ffffff")
    ax.set_aspect("equal", "box")

    # Rótulos: APENAS nomes P1, P2, P3, sem letras entre parênteses
    ax.text(x_E, y_E, f"{est}", fontsize=10, color="#111827")
    ax.text(x1, y1, f"{nome1}", fontsize=10, color="#111827")
    ax.text(x2, y2, f"{nome2}", fontsize=10, color="#111827")

    # Descobrir qual lado é qual, usando nomes dos pontos
    # Lado estação–pv1
    ax.text(
        (x_E + x1) / 2,
        (y_E + y1) / 2,
        f"{est}–{nome1} = {AB:.3f} m",
        color="#374151",
        fontsize=9,
    )
    # Lado estação–pv2
    ax.text(
        (x_E + x2) / 2,
        (y_E + y2) / 2,
        f"{est}–{nome2} = {AC:.3f} m",
        color="#374151",
        fontsize=9,
    )
    # Lado pv1–pv2
    ax.text(
        (x1 + x2) / 2,
        (y1 + y2) / 2,
        f"{nome1}–{nome2} = {BC:.3f} m",
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
    Gera um arquivo XLSX com um resumo numérico do triângulo e a figura em outra aba.
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
