# app.py
# Média das Direções (Hz) + DH/DN - UFPE + Croqui P1-P2-P3
# Rode com: streamlit run app.py

import io

import pandas as pd
import streamlit as st

from plotting import (
    construir_coords_approx,
    construir_triangulo_especifico,
    plot_triangulo_especifico,
    plot_triangulo_medio,
)
from processing import (
    REQUIRED_COLS,
    PONTOS_TRI,
    agregar_por_par,
    calcular_linha_a_linha,
    info_triangulo,
    resumo_linha_a_linha,
    resumo_por_par,
    validar_dataframe,
)
from utils import resumo_angulos

# ==================== Config página ====================
st.set_page_config(
    page_title="Média das Direções (Hz) — Estação Total | UFPE",
    layout="wide",
    page_icon="📐",
)

# ==================== CSS (o mesmo da sua versão anterior) ====================
CUSTOM_CSS = """
<style>
body, .stApp {
    background: radial-gradient(circle at top left, #faf5f5 0%, #f7f5f5 45%, #f4f4f4 100%);
    color: #111827;
    font-family: "Trebuchet MS", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}
.main-card {
    background: linear-gradient(145deg, #ffffff 0%, #fdfbfb 40%, #ffffff 100%);
    border-radius: 18px;
    padding: 1.8rem 2.1rem;
    border: 1px solid #e5e7eb;
    box-shadow:
        0 18px 40px rgba(15, 23, 42, 0.22),
        0 0 0 1px rgba(15, 23, 42, 0.03);
}
.ufpe-top-bar {
    width: 100%;
    height: 8px;
    border-radius: 0 0 14px 14px;
    background: linear-gradient(90deg, #5b0000 0%, #990000 52%, #5b0000 100%);
    margin-bottom: 0.9rem;
}
.ufpe-header-text {
    font-size: 0.78rem;
    line-height: 1.15rem;
    text-transform: uppercase;
    color: #111827;
}
.ufpe-header-text strong {
    letter-spacing: 0.04em;
}
.ufpe-separator {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 0.8rem 0 1.0rem 0;
}
.app-title {
    font-size: 2.0rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    display: flex;
    align-items: center;
    gap: 0.65rem;
    margin-bottom: 0.35rem;
    color: #111827;
}
.app-title span.icon {
    font-size: 2.4rem;
}
.app-subtitle {
    font-size: 0.95rem;
    color: #4b5563;
    margin-bottom: 0.9rem;
}
.section-title {
    font-size: 1.02rem;
    font-weight: 600;
    margin-top: 1.6rem;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    color: #111827;
}
.section-title span.dot {
    width: 7px;
    height: 7px;
    border-radius: 999px;
    background: radial-gradient(circle at 30% 30%, #ffffff 0%, #990000 40%, #111827 100%);
}
.helper-box {
    border-radius: 12px;
    padding: 0.6rem 0.85rem;
    background: linear-gradient(135deg, #fdf2f2 0%, #fff5f5 40%, #fdf2f2 100%);
    border: 1px solid rgba(153, 0, 0, 0.25);
    font-size: 0.83rem;
    color: #4b5563;
    margin-bottom: 0.7rem;
}
.footer-text {
    font-size: 0.75rem;
    color: #6b7280;
}
.stDownloadButton > button {
    border-radius: 999px;
    border: 1px solid #990000;
    background: linear-gradient(135deg, #b00000, #730000);
    color: white;
    font-weight: 600;
    font-size: 0.86rem;
    padding: 0.45rem 0.95rem;
    box-shadow: 0 8px 18px rgba(128,0,0,0.35);
}
.stDownloadButton > button:hover {
    border-color: #111827;
    background: linear-gradient(135deg, #111827, #4b0000);
}

/* Tabelas */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    background: linear-gradient(145deg, #ffffff 0%, #f9fafb 60%, #ffffff 100%) !important;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.08);
}
[data-testid="stDataFrame"] thead tr {
    background: linear-gradient(90deg, #f5e6e8 0%, #fdf2f2 100%) !important;
    color: #5b101d !important;
    font-weight: 600;
}
[data-testid="stDataFrame"] tbody tr:nth-child(odd) {
    background-color: #fafafa !important;
}
[data-testid="stDataFrame"] tbody tr:nth-child(even) {
    background-color: #ffffff !important;
}
[data-testid="stDataFrame"] tbody tr:hover {
    background-color: #f3f0f0 !important;
}

/* Inputs */
.stTextInput label, .stFileUploader label {
    font-size: 0.86rem;
    font-weight: 600;
    color: #374151;
}
.stTextInput input {
    background: linear-gradient(145deg, #ffffff, #f9fafb) !important;
    color: #111827 !important;
    border-radius: 999px;
    border: 1px solid #d4d4d4;
    padding: 0.35rem 0.8rem;
    font-size: 0.9rem;
}
.stTextInput input:focus {
    border-color: #a32a36 !important;
    box-shadow: 0 0 0 1px rgba(163,42,54,0.25);
}

/* Botões */
.stButton button {
    background: linear-gradient(135deg, #a32a36, #7d1220) !important;
    color: #ffffff !important;
    border-radius: 999px !important;
    border: none !important;
    padding: 0.4rem 1.4rem;
    font-weight: 600;
    font-size: 0.9rem;
    box-shadow: 0 6px 16px rgba(125,18,32,0.25);
}
.stButton button:hover {
    background: linear-gradient(135deg, #7d1220, #5a0d18) !important;
    box-shadow: 0 4px 12px rgba(90,13,24,0.35);
}

/* Uploader PT-BR */
[data-testid="stFileUploaderDropzone"] > div > div {
    font-size: 0.9rem;
}
[data-testid="stFileUploaderDropzone"]::before {
    content: "Arraste e solte o arquivo aqui ou";
    display: block;
    text-align: center;
    margin-bottom: 0.25rem;
    color: #374151;
    font-size: 0.88rem;
}
[data-testid="stFileUploaderDropzone"] button {
    color: #ffffff !important;
    background: linear-gradient(135deg, #a32a36, #7d1220) !important;
    border-radius: 999px !important;
    border: none !important;
    padding: 0.2rem 0.9rem;
    font-size: 0.85rem;
}
[data-testid="stFileUploaderDropzone"] button::before {
    content: "Escolher arquivo";
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==================== Cabeçalho UFPE ====================
def cabecalho_ufpe():
    with st.container():
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<div class="ufpe-top-bar"></div>', unsafe_allow_html=True)

        col_logo, col_info = st.columns([1, 5])
        with col_logo:
            st.image(
                "https://upload.wikimedia.org/wikipedia/commons/8/85/Bras%C3%A3o_da_UFPE.png",
                width=95,
            )
        with col_info:
            st.markdown(
                """
                <div class="ufpe-header-text">
                    <div><strong>UNIVERSIDADE FEDERAL DE PERNAMBUCO</strong></div>
                    <div>DECART — Departamento de Engenharia Cartográfica</div>
                    <div>LATOP — Laboratório de Topografia</div>
                    <div>Curso: <strong>Engenharia Cartográfica e Agrimensura</strong></div>
                    <div>Disciplina: <strong>Equipamentos de Medição</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_prof, col_local, col_equip, col_data, col_patr = st.columns(
                [1.6, 1.4, 1.6, 1.1, 1.2]
            )
            col_prof.text_input("Professor", value="")
            col_local.text_input("Local", value="")
            col_equip.text_input("Equipamento", value="")
            col_data.text_input("Data", value="")
            col_patr.text_input("Patrimônio", value="")

        st.markdown('<hr class="ufpe-separator">', unsafe_allow_html=True)

        st.markdown(
            """
            <div class="app-title">
                <span class="icon">📐</span>
                <span>Média das Direções (Hz) — Estação Total</span>
            </div>
            <div class="app-subtitle">
                Cálculo da média das direções Hz, distâncias horizontais / diferenças de nível
                e croqui plano do triângulo P1–P2–P3.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="helper-box">
                <b>Modelo esperado de planilha:</b><br>
                Colunas: <code>EST</code>, <code>PV</code>,
                <code>Hz_PD</code>, <code>Hz_PI</code>,
                <code>Z_PD</code>, <code>Z_PI</code>,
                <code>DI_PD</code>, <code>DI_PI</code>.<br>
                Ângulos em <b>DMS</b> (ex.: 145°47'33") ou <b>decimal</b> (ex.: 145.7925).<br>
                Distâncias inclinadas em <b>metros</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )


def secao_modelo_e_upload():
    st.markdown(
        """
        <div class="section-title">
            <span class="dot"></span>
            <span>1. Modelo de dados (Hz, Z e DI)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    template_df = pd.DataFrame(
        {
            "EST": ["P1", "P1"],
            "PV": ["P2", "P3"],
            "Hz_PD": ["145°47'33\"", "167°29'03\""],
            "Hz_PI": ["325°47'32\"", "347°29'22\""],
            "Z_PD": ["89°48'20\"", "89°36'31\""],
            "Z_PI": ["270°12'00\"", "270°23'32\""],
            "DI_PD": [25.365, 26.285],
            "DI_PI": [25.365, 26.285],
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
        key="download_excel_model",
    )

    st.markdown(
        """
        <div class="section-title">
            <span class="dot"></span>
            <span>2. Carregar dados de campo</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Envie a planilha preenchida (EST, PV, Hz_PD, Hz_PI, Z_PD, Z_PI, DI_PD, DI_PI)",
        type=["xlsx", "xls", "csv"],
    )
    return uploaded


def processar_upload(uploaded):
    if uploaded is None:
        return None

    try:
        if uploaded.name.lower().endswith(".csv"):
            raw_df = pd.read_csv(uploaded)
        else:
            raw_df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        return None

    st.success(f"Arquivo '{uploaded.name}' carregado ({len(raw_df)} linhas).")

    df_valid, erros = validar_dataframe(raw_df)
    st.subheader("Pré-visualização dos dados importados")
    st.dataframe(df_valid[REQUIRED_COLS], use_container_width=True)

    if erros:
        st.error("Não foi possível calcular diretamente devido aos seguintes problemas:")
        for e in erros:
            st.markdown(f"- {e}")

        st.markdown("### Corrija os dados abaixo e clique em *Aplicar correções*")
        edited_df = st.data_editor(
            df_valid[REQUIRED_COLS],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_corrigir_tudo",
        )

        if st.button("Aplicar correções"):
            df_corrigido, erros2 = validar_dataframe(edited_df)
            if not erros2:
                st.success("Dados corrigidos com sucesso.")
                return df_corrigido[REQUIRED_COLS].copy()
            else:
                st.error("Ainda há problemas após a correção:")
                for e in erros2:
                    st.markdown(f"- {e}")
                return None
        else:
            return None
    else:
        return df_valid[REQUIRED_COLS].copy()


def secao_calculos_basicos(df_uso):
    st.markdown(
        """
        <div class="section-title">
            <span class="dot"></span>
            <span>3. Cálculos básicos (linha a linha e por par EST–PV)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # referências para Ré/Vante
    ref_por_estacao = {"P1": "P2", "P2": "P1", "P3": "P1"}

    res = calcular_linha_a_linha(df_uso, ref_por_estacao)
    df_par = agregar_por_par(res)

    resumo_df = resumo_linha_a_linha(res)
    st.markdown("##### Tabela linha a linha (cada leitura)")
    st.dataframe(resumo_df, use_container_width=True)

    resumo_par_df = resumo_por_par(df_par)
    st.markdown("##### Resultados médios por par EST–PV")
    st.dataframe(resumo_par_df, use_container_width=True)

    out_csv = resumo_par_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 Baixar resultados médios (CSV)",
        data=out_csv,
        file_name="resultados_medios_estacao_total_ufpe.csv",
        mime="text/csv",
        key="download_saida_csv_par",
    )

    return res, df_par


def secao_triangulo(df_par):
    if df_par is None or df_par.empty:
        st.info("Carregue dados válidos primeiro para visualizar o triângulo.")
        return

    st.markdown(
        """
        <div class="section-title">
            <span class="dot"></span>
            <span>4. Croqui gráfico e análise do triângulo P1–P2–P3</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    coords = construir_coords_approx(df_par)
    if not set(PONTOS_TRI).issubset(coords.keys()):
        st.info(
            "Para montar o triângulo P1–P2–P3 é necessário ter médias para P1–P2, P1–P3 e P2–P3."
        )
        return

    aba1, aba2 = st.tabs(
        [
            "Triângulo médio (todas as leituras)",
            "Triângulo específico (P1⇒P3, P3⇒P2, P2⇒P1)",
        ]
    )

    # ---- Aba Triângulo médio ----
    with aba1:
        pA, pB, pC = "P1", "P2", "P3"
        lados, angulos, area = info_triangulo(pA, pB, pC, coords)
        fig, ax = plot_triangulo_medio(coords, lados, angulos)
        st.pyplot(fig)

        lados_df = pd.DataFrame(
            {
                "Lado": [lados["nome_lado_C"], lados["nome_lado_A"], lados["nome_lado_B"]],
                "Distância (m)": [
                    round(lados["C"], 4),
                    round(lados["A"], 4),
                    round(lados["B"], 4),
                ],
            }
        )
        ang_df = pd.DataFrame(
            {
                "Vértice": [pA, pB, pC],
                "Ângulo interno (graus)": [
                    round(angulos["A"], 4),
                    round(angulos["B"], 4),
                    round(angulos["C"], 4),
                ],
            }
        )

        st.markdown("##### Distâncias dos lados")
        st.dataframe(lados_df, use_container_width=True)

        st.markdown("##### Ângulos internos (lei dos cossenos)")
        st.dataframe(ang_df, use_container_width=True)

        soma_ang, desvio = resumo_angulos(angulos["A"], angulos["B"], angulos["C"])
        st.markdown(
            f"**Soma dos ângulos internos:** `{soma_ang:.4f}°` &nbsp;&nbsp; "
            f"(desvio em relação a 180°: `{desvio:+.4f}°`)"
        )
        st.markdown(f"**Área do triângulo (Heron):** `{area:.4f} m²`")

    # ---- Aba Triângulo específico ----
    with aba2:
        try:
            (
                coords_tri,
                (d_P1P3, d_P3P2, d_P2P1),
                (ang_P1, ang_P3, ang_P2),
                soma_ang,
                desvio,
                area_,
            ) = construir_triangulo_especifico(df_par)
        except ValueError as e:
            st.warning(str(e))
            return

        fig2, ax2 = plot_triangulo_especifico(
            coords_tri,
            (d_P1P3, d_P3P2, d_P2P1),
            (ang_P1, ang_P3, ang_P2),
        )
        st.pyplot(fig2)

        lados_df = pd.DataFrame(
            {
                "Lado": ["P1–P3", "P3–P2", "P2–P1"],
                "Distância (m)": [
                    round(d_P1P3, 4),
                    round(d_P3P2, 4),
                    round(d_P2P1, 4),
                ],
            }
        )
        ang_df = pd.DataFrame(
            {
                "Vértice": ["P1", "P3", "P2"],
                "Ângulo interno (graus)": [
                    round(ang_P1, 4),
                    round(ang_P3, 4),
                    round(ang_P2, 4),
                ],
            }
        )

        st.markdown("##### Distâncias dos lados")
        st.dataframe(lados_df, use_container_width=True)

        st.markdown("##### Ângulos internos (lei dos cossenos)")
        st.dataframe(ang_df, use_container_width=True)

        st.markdown(
            f"**Soma dos ângulos internos:** `{soma_ang:.4f}°` &nbsp;&nbsp; "
            f"(desvio em relação a 180°: `{desvio:+.4f}°`)"
        )
        st.markdown(f"**Área do triângulo (Heron):** `{area_:.4f} m²`")


def rodape():
    st.markdown(
        """
        <p class="footer-text">
            Versão do app: <code>7.0 — Refatorado em camadas (UI, processamento, gráficos) + soma/desvio dos ângulos</code>.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)  # fim main-card


# ==================== Fluxo principal ====================
cabecalho_ufpe()
uploaded = secao_modelo_e_upload()
df_uso = processar_upload(uploaded)

if df_uso is not None:
    res, df_par = secao_calculos_basicos(df_uso)
    secao_triangulo(df_par)

rodape()
