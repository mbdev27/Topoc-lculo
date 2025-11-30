# app.py
import io

import pandas as pd
import streamlit as st

from processing import (
    REQUIRED_COLS,
    validar_dataframe,
    calcular_linha_a_linha,
    agregar_por_par,
    resumo_linha_a_linha,
    resumo_por_par,
    construir_triangulo_medio,
    construir_triangulo_especifico,
    PONTOS_TRI,
)
from plotagem import plot_triangulo_medio, plot_triangulo_especifico
from utils import dms_str_inteiro, resumo_angulos


st.set_page_config(
    page_title="Topoc-cálculo — Estação Total | UFPE",
    layout="wide",
    page_icon="📐",
)

# Se quiser, aqui você pode colar o CSS que já vinha usando.
# Para simplificar, vou omitir para não alongar demais.
# Você pode reaproveitar o CUSTOM_CSS da versão anterior.


def cabecalho():
    st.title("📐 Topoc-cálculo — Estação Total (UFPE)")
    st.markdown(
        "Aplicação para tratamento das leituras de estação total, "
        "cálculo de distâncias, análise de triângulo e estatísticas básicas."
    )


def secao_modelo_e_upload():
    st.header("1. Dados de campo — modelo e upload")

    template_df = pd.DataFrame(
        {
            "EST": ["P1", "P1", "P3", "P3", "P2", "P2"],
            "PV": ["P2", "P3", "P1", "P2", "P3", "P1"],
            "AnguloHorizontal_PD": ["145°47'33\"", "167°29'03\"", "330°39'26\"", "44°25'11\"", "216°53'49\"", "132°23'14\""],
            "AnguloHorizontal_PI": ["325°47'32\"", "347°29'22\"", "150°39'28\"", "224°24'56\"", "36°52'54\"", "312°23'14\""],
            "AnguloZenital_PD": ["89°48'20\"", "89°36'31\"", "89°03'12\"", "88°05'32\"", "88°55'16\"", "87°31'30\""],
            "AnguloZenital_PI": ["270°12'00\"", "270°23'32\"", "270°57'00\"", "271°54'05\"", "271°05'00\"", "272°28'32\""],
            "DistanciaInclinada_PD": [25365, 26285, 26296, 9788, 25374, 9786],
            "DistanciaInclinada_PI": [25365, 26285, 26296, 9788, 25374, 9785],
        }
    )

    excel_bytes = io.BytesIO()
    template_df.to_excel(excel_bytes, index=False)
    excel_bytes.seek(0)
    st.download_button(
        "📥 Baixar modelo Excel (.xlsx)",
        data=excel_bytes.getvalue(),
        file_name="modelo_estacao_total_ufpe.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded = st.file_uploader(
        "Envie a planilha preenchida (formato igual ao modelo acima).",
        type=["xlsx", "xls", "csv"],
    )
    return uploaded


def processar_upload(uploaded):
    if uploaded is None:
        return None

    try:
        if uploaded.name.lower().endswith(".csv"):
            df_raw = pd.read_csv(uploaded)
        else:
            df_raw = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return None

    st.success(f"Arquivo '{uploaded.name}' carregado com {len(df_raw)} linhas.")
    df_valid, erros = validar_dataframe(df_raw)

    st.subheader("Pré-visualização dos dados brutos")
    st.dataframe(df_valid.head(30), use_container_width=True)

    if erros:
        st.error("Problemas encontrados:")
        for e in erros:
            st.markdown(f"- {e}")
        return None

    return df_valid


def secao_calculos(df_entrada: pd.DataFrame):
    st.header("2. Cálculos por leitura e por par EST–PV")

    df_linha = calcular_linha_a_linha(df_entrada)
    df_par = agregar_por_par(df_linha)

    st.subheader("2.1. Cálculos linha a linha")
    st.dataframe(resumo_linha_a_linha(df_linha), use_container_width=True)

    st.subheader("2.2. Resumo por par (médias e desvios padrão)")
    resumo_par_df = resumo_por_par(df_par)
    st.dataframe(resumo_par_df, use_container_width=True)

    return df_linha, df_par


def secao_triangulos(df_par: pd.DataFrame):
    st.header("3. Análise do triângulo P1–P2–P3")

    if df_par is None or df_par.empty:
        st.info("Carregue dados válidos primeiro.")
        return

    # Verificar se temos todas as combinações para o triângulo
    est_pvs = set(zip(df_par["EST"], df_par["PV"]))
    pares_necessarios = {("P1", "P2"), ("P1", "P3"), ("P2", "P3"), ("P2", "P1"), ("P3", "P1"), ("P3", "P2")}
    if not any(p in est_pvs for p in [("P1", "P2"), ("P2", "P1")]) or \
       not any(p in est_pvs for p in [("P1", "P3"), ("P3", "P1")]) or \
       not any(p in est_pvs for p in [("P2", "P3"), ("P3", "P2")]):
        st.warning("Faltam pares P1–P2, P1–P3 ou P2–P3 para formar o triângulo completo.")
        return

    aba_medio, aba_especifico = st.tabs(
        ["Triângulo médio (todas as leituras)", "Triângulo específico (P1⇒P3, P3⇒P2, P2⇒P1)"]
    )

    # ---- Triângulo médio ----
    with aba_medio:
        try:
            lados, angulos, area, soma_ang, desvio = construir_triangulo_medio(df_par)
        except ValueError as e:
            st.warning(str(e))
            return

        fig, _ = plot_triangulo_medio(lados, angulos)
        st.pyplot(fig)

        # Tabela de distâncias
        dist_df = pd.DataFrame(
            {
                "Lado": ["P2–P3 (oposto a P1)", "P1–P3 (oposto a P2)", "P1–P2 (oposto a P3)"],
                "Distância (m)": [
                    round(lados["A"], 3),
                    round(lados["B"], 3),
                    round(lados["C"], 3),
                ],
            }
        )
        st.subheader("Distâncias médias dos lados (m)")
        st.dataframe(dist_df, use_container_width=True)

        # Tabela de ângulos em DMS
        ang_dms_df = pd.DataFrame(
            {
                "Vértice": ["P1", "P2", "P3", "P1+P2+P3"],
                "Ângulo interno":
                    [
                        dms_str_inteiro(angulos["A"]),
                        dms_str_inteiro(angulos["B"]),
                        dms_str_inteiro(angulos["C"]),
                        dms_str_inteiro(soma_ang),
                    ],
                "Valor (graus decimais)": [
                    round(angulos["A"], 4),
                    round(angulos["B"], 4),
                    round(angulos["C"], 4),
                    round(soma_ang, 4),
                ],
            }
        )
        st.subheader("Ângulos internos do triângulo médio")
        st.dataframe(ang_dms_df, use_container_width=True)

        st.markdown(
            f"Soma dos ângulos (decimal): **{soma_ang:.4f}°** &nbsp; "
            f"Desvio em relação a 180°: **{desvio:+.4f}°**"
        )
        st.markdown(f"Área do triângulo médio (Heron): **{area:.4f} m²**")

    # ---- Triângulo específico ----
    with aba_especifico:
        try:
            coords_tri, (d13, d32, d21), (ang_P1, ang_P3, ang_P2), soma_ang, desvio = construir_triangulo_especifico(
                df_par
            )
        except ValueError as e:
            st.warning(str(e))
            return

        fig2, _ = plot_triangulo_especifico(coords_tri, (d13, d32, d21), (ang_P1, ang_P3, ang_P2))
        st.pyplot(fig2)

        dist_df = pd.DataFrame(
            {
                "Lado": ["P1–P3", "P3–P2", "P2–P1"],
                "Distância média (m)": [
                    round(d13, 3),
                    round(d32, 3),
                    round(d21, 3),
                ],
            }
        )
        st.subheader("Distâncias dos lados (triângulo específico)")
        st.dataframe(dist_df, use_container_width=True)

        # Tabela de ângulos em DMS com linha de soma
        soma, desv = resumo_angulos(ang_P1, ang_P3, ang_P2)
        ang_dms_df = pd.DataFrame(
            {
                "Vértice": ["P1", "P3", "P2", "P1+P2+P3"],
                "Ângulo interno":
                    [
                        dms_str_inteiro(ang_P1),
                        dms_str_inteiro(ang_P3),
                        dms_str_inteiro(ang_P2),
                        dms_str_inteiro(soma),
                    ],
                "Valor (graus decimais)": [
                    round(ang_P1, 4),
                    round(ang_P3, 4),
                    round(ang_P2, 4),
                    round(soma, 4),
                ],
            }
        )

        st.subheader("Ângulos internos do triângulo específico")
        st.dataframe(ang_dms_df, use_container_width=True)

        st.markdown(
            f"Soma dos ângulos (decimal): **{soma:.4f}°** &nbsp; "
            f"Desvio em relação a 180°: **{desv:+.4f}°**"
        )

        # Área (Heron) para triângulo específico
        s = 0.5 * (d13 + d32 + d21)
        area = (s * (s - d13) * (s - d32) * (s - d21)) ** 0.5
        st.markdown(f"Área do triângulo específico (Heron): **{area:.4f} m²**")


def main():
    cabecalho()
    uploaded = secao_modelo_e_upload()
    df_entrada = processar_upload(uploaded)

    if df_entrada is not None:
        df_linha, df_par = secao_calculos(df_entrada)
        secao_triangulos(df_par)


if __name__ == "__main__":
    main()
