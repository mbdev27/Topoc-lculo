# app.py
# Interface principal Streamlit – duas "páginas":
# 1) Carregar dados; 2) Processamento com cabeçalho UFPE.

import streamlit as st
import pandas as pd

from processing import (
    REQUIRED_COLS_ALL,
    validar_dataframe,
    calcular_linha_a_linha,
    tabela_hz_por_serie,
    tabela_z_por_serie,
    tabela_resumo_final,
    selecionar_linhas_por_estacao_e_conjunto,
    calcular_triangulo_duas_linhas,
    gerar_modelo_excel_bytes,
    decimal_to_dms,
)
from plotting import plotar_triangulo_info, gerar_xlsx_com_figura
from utils import ler_identificacao_from_df

st.set_page_config(
    page_title="Calculadora de Ângulos e Distâncias | UFPE",
    layout="wide",
    page_icon="📐",
)

# ========================================================================
# CSS
# ========================================================================
CUSTOM_CSS = """
<style>
body, .stApp {
  background:#f3f4f6;
  color: #111827;
  font-family:"Trebuchet MS",system-ui,-apple-system,BlinkMacSystemFont,sans-serif;
}

.main-card{
  background:#ffffff;
  color: #111827;
  border-radius:22px;
  padding:1.4rem 2.0rem 1.4rem 2.0rem;
  border:1px solid rgba(148,27,37,0.20);
  box-shadow:0 18px 40px rgba(15,23,42,0.18);
  max-width:1320px;
  margin:1.2rem auto 2.0rem auto;
}
.main-card p { text-align: justify; }

.ufpe-header-band{
  width: 100%;
  padding:0.7rem 1.0rem 0.6rem 1.0rem;
  border-radius:14px;
  background:linear-gradient(90deg,#4b0000 0%,#7e0000 40%,#b30000 75%,#4b0000 100%);
  color:#f9fafb;
  display:flex;
  align-items:flex-start;
  gap:0.8rem;
}
.ufpe-header-text{
  font-size:0.87rem;
}
.ufpe-header-text b{
  font-weight:700;
}

.section-title{
  font-size:1.00rem;
  font-weight:700;
  margin-top:1.5rem;
  margin-bottom:0.6rem;
  display:flex;
  align-items:center;
  gap:0.4rem;
  color:#8b0000;
  text-transform:uppercase;
  letter-spacing:0.05em;
}
.section-title span.dot{
  width:9px;
  height:9px;
  border-radius:999px;
  background:radial-gradient(circle at 30% 30%,#ffffff 0%,#ffbdbd 35%,#7f0000 90%);
}

.helper-box{
  border-radius:10px;
  padding:0.6rem 0.8rem;
  background:#fff5f5;
  border:1px solid rgba(148,27,37,0.35);
  font-size:0.86rem;
  color:#111827;
  margin-bottom:0.5rem;
}

[data-testid="stDataFrame"],[data-testid="stDataEditor"]{
  background:#ffffff !important;
  border-radius:10px;
  border:1px solid rgba(148,27,37,0.25);
  box-shadow:0 10px 22px rgba(15,23,42,0.12);
}

.stButton>button, .stDownloadButton>button {
  background: #b30000;
  color: #ffffff;
  border-radius: 999px;
  border: 1px solid #7f0000;
  padding: 0.35rem 1.1rem;
  font-weight: 600;
}
.stButton>button:hover, .stDownloadButton>button:hover {
  background: #ffffff;
  color: #111827;
  border: 1px solid #b30000;
}

.footer-text{
  font-size:0.75rem;
  color:#6b7280;
}

:root{color-scheme:light;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =================================================================
# Cabeçalho UFPE (usado apenas na página de processamento)
# =================================================================
def cabecalho_ufpe(info_id):
    prof = info_id.get("Professor(a)", "")
    equip = info_id.get("Equipamento", "")
    data_str = info_id.get("Dados", "")  # já vem como DD/MM/AAAA ou ''
    local = info_id.get("Local", "")
    patr = info_id.get("Patrimônio", "")

    def linha(label, value):
        if value:
            return f"{label}: <u>{value}</u><br>"
        else:
            return f"{label}: _________________________________<br>"

    st.markdown('<div class="main-card">', unsafe_allow_html=True)

    st.markdown("<div class='ufpe-header-band'>", unsafe_allow_html=True)
    col_logo, col_text = st.columns([1, 9])
    with col_logo:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/8/85/Bras%C3%A3o_da_UFPE.png",
            width=70,
        )
    with col_text:
        texto = (
            "<div class='ufpe-header-text'>"
            "<b>UNIVERSIDADE FEDERAL DE PERNAMBUCO - UFPE</b><br>"
            "DECART — Departamento de Engenharia Cartográfica<br>"
            "LATOP — Laboratório de Topografia<br>"
            "Curso: Engenharia Cartográfica e Agrimensura<br>"
            "Disciplina: Equipamentos de Medição<br>"
            f"{linha('Professor(a)', prof)}"
            f"{linha('Equipamento', equip)}"
            f"{linha('Data', data_str)}"
            f"{linha('Local', local)}"
            f"{linha('Patrimônio', patr)}"
            "</div>"
        )
        st.markdown(texto, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <p style="margin-top:0.9rem;font-size:1.5rem;font-weight:800;color:#7f0000;">
            Calculadora de Ângulos e Distâncias – Método das Direções para Triângulos
        </p>
        <p style="font-size:0.92rem;">
            Esta ferramenta auxilia no processamento das leituras obtidas com estação total,
            calculando médias de direções horizontais (Hz), ângulos verticais/zenitais,
            distâncias horizontais médias e a geometria do triângulo formado pelos
            pontos P1, P2 e P3.
        </p>
        <div class="helper-box">
            <b>Preenchimento dos dados de identificação:</b><br>
            Os campos Professor(a), Equipamento, Dados, Local e Patrimônio são lidos
            automaticamente da aba <b>Identificação</b> do modelo Excel. Os dados são exibidos
            no formato <b>DD/MM/AAAA</b>. Caso algum campo venha em branco, ele pode ser
            completado manualmente no arquivo exportado.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ================================================================
# Página 1 – Modelo + Upload
# ================================================================
def pagina_carregar_dados():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)

    # 1. Modelo de planilha
    st.markdown(
        """
        <div class="section-title">
            <span class="dot"></span>
            <span>1. Modelo de planilha</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    modelo_bytes = gerar_modelo_excel_bytes()
    st.download_button(
        "📥 Baixar modelo Excel (.xlsx)",
        data=modelo_bytes,
        file_name="modelo_medicao_direcoes_ufpe.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.markdown(
        """
        <p style="font-size:0.9rem;">
        O modelo contém duas abas: <b>Identificação</b> (dados do cabeçalho)
        e <b>Dados</b> (leituras Hz, Z e distâncias).
        </p>
        """,
        unsafe_allow_html=True,
    )

    # 2. Carregar dados de campo
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
        "Envie o arquivo Excel (com abas Identificação e Dados)",
        type=["xlsx", "xls"],
    )

    if uploaded is None:
        st.markdown("</div>", unsafe_allow_html=True)
        return

    try:
        xls = pd.ExcelFile(uploaded)

        # Identificação
        sheet_id = None
        for s in xls.sheet_names:
            if s.strip().lower() in ["identificação", "identificacao"]:
                sheet_id = s
                break
        info_id = {
            "Professor(a)": "",
            "Equipamento": "",
            "Dados": "",
            "Local": "",
            "Patrimônio": "",
        }
        if sheet_id is not None:
            df_id = pd.read_excel(xls, sheet_name=sheet_id)
            info_id = ler_identificacao_from_df(df_id)

        # Dados
        sheet_dados = None
        for s in xls.sheet_names:
            if s.strip().lower() in ["dados", "medicoes", "medições"]:
                sheet_dados = s
                break
        if sheet_dados is None:
            sheet_dados = xls.sheet_names[0]

        raw_df = pd.read_excel(xls, sheet_name=sheet_dados)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.success(
        f"Arquivo '{uploaded.name}' carregado. Aba de dados utilizada: '{sheet_dados}'."
    )

    df_valid, erros = validar_dataframe(raw_df)

    st.subheader("Pré-visualização dos dados importados")
    cols_to_show = [c for c in REQUIRED_COLS_ALL if c in df_valid.columns]
    st.dataframe(df_valid[cols_to_show], use_container_width=True)

    if erros:
        st.error("Não foi possível calcular devido aos seguintes problemas:")
        for e in erros:
            st.markdown(f"- {e}")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    cols_use = [c for c in REQUIRED_COLS_ALL if c in df_valid.columns]
    df_uso = df_valid[cols_use].copy()

    st.session_state["df_uso"] = df_uso
    st.session_state["info_id"] = info_id

    if st.button("Ir para processamento"):
        st.session_state["pagina"] = "processamento"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =======================================================================
# Página 2 – Processamento (3 a 7)
# =======================================================================
def pagina_processamento():
    if "df_uso" not in st.session_state or "info_id" not in st.session_state:
        st.warning("Nenhum dado carregado. Volte à página 'Carregar dados' primeiro.")
        if st.button("Voltar para carregar dados"):
            st.session_state["pagina"] = "carregar"
            st.rerun()
        return

    df_uso = st.session_state["df_uso"]
    info_id = st.session_state["info_id"]

    cabecalho_ufpe(info_id)

    st_local = st

    # 3. Cálculo linha a linha
    st_local.markdown(
        """
        <div class="section-title">
            <span class="dot"></span>
            <span>3. Cálculo de Hz, Z e distâncias (linha a linha)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    res = calcular_linha_a_linha(df_uso)

    cols_linha = [
        "EST",
        "PV",
        "SEQ",
        "Hz_PD",
        "Hz_PI",
        "Hz_med_DMS",
        "Z_PD",
        "Z_PI",
        "Z_corr_DMS",
        "DH_PD_m",
        "DH_PI_m",
        "DH_med_m",
    ]
    df_linha = res[cols_linha].copy()
    for c in ["DH_PD_m", "DH_PI_m", "DH_med_m"]:
        df_linha[c] = df_linha[c].apply(
            lambda x: f"{x:.3f}" if pd.notna(x) else ""
        )
    st_local.dataframe(df_linha, use_container_width=True)

    # 4. Medição Angular Horizontal
    st_local.markdown(
        """
        <div class="section-title">
            <span class="dot"></span>
            <span>4. Medição Angular Horizontal</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    tab_hz = tabela_hz_por_serie(res)
    st_local.dataframe(tab_hz, use_container_width=True)

    # 5. Medição Angular Vertical / Zenital
    st_local.markdown(
        """
        <div class="section-title">
            <span class="dot"></span>
            <span>5. Medição Angular Vertical / Zenital</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    tab_z = tabela_z_por_serie(res)
    st_local.dataframe(tab_z, use_container_width=True)

    # 6. Tabela resumo
    st_local.markdown(
        """
        <div class="section-title">
            <span class="dot"></span>
            <span>6. Tabela resumo (Hz, Z e DH)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    resumo = tabela_resumo_final(res, renomear_para_letras=True)
    st_local.dataframe(resumo, use_container_width=True)

    # 7. TRIÂNGULO SELECIONADO
    st_local.markdown(
        """
        <div class="section-title">
            <span class="dot"></span>
            <span>7. TRIÂNGULO SELECIONADO (CONJUNTO AUTOMÁTICO DE MEDIÇÕES)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st_local.columns(2)
    with col_a:
        estacao_op = st_local.selectbox("Estação (A, B, C)", ["A", "B", "C"])
    with col_b:
        conjunto_op = st_local.selectbox(
            "Conjunto de leituras",
            ["1ª leitura", "2ª leitura", "3ª leitura"],
        )

    st_local.markdown(
        "<p>O programa seleciona automaticamente o par de leituras adequadas "
        "para formar o triângulo, conforme as regras definidas para cada estação.</p>",
        unsafe_allow_html=True,
    )

    if st_local.button("Gerar triângulo"):
        pares = selecionar_linhas_por_estacao_e_conjunto(res, estacao_op, conjunto_op)
        if pares is None:
            st_local.error(
                "Não foi possível encontrar duas leituras compatíveis para "
                f"Estação {estacao_op} e {conjunto_op}. "
                "Verifique se a ordem das linhas (EST, PV) segue o modelo."
            )
        else:
            idx1, idx2 = pares
            info = calcular_triangulo_duas_linhas(res, idx1, idx2, estacao_op, conjunto_op)
            if info is None:
                st_local.error(
                    "Falha ao calcular o triângulo a partir das leituras selecionadas."
                )
            else:
                est = info["EST"]
                pv1 = info["PV1"]
                pv2 = info["PV2"]

                st_local.markdown(
                    f"<p><b>Triângulo formado automaticamente pelos pontos {est}, {pv1} e {pv2} "
                    f"(conjunto: {conjunto_op}, estação selecionada: {estacao_op}).</b></p>",
                    unsafe_allow_html=True,
                )

                lados_ord = info.get("lados_ordenados", [])
                ang_ord = info.get("angulos_ordenados", [])

                col1, col2 = st_local.columns(2)
                with col1:
                    st_local.markdown("**Lados (m) – do maior para o menor:**")
                    linhas_lados = []
                    for rot, p_ini, p_fim, val in lados_ord:
                        linhas_lados.append(
                            f"- {p_ini}–{p_fim} ({rot}): ` {val:.3f} ` m"
                        )
                    st_local.markdown("\n".join(linhas_lados))

                    st_local.markdown("**Ângulos internos – do maior para o menor:**")
                    linhas_ang = []
                    for letra, p_nome, val in ang_ord:
                        linhas_ang.append(
                            f"- Em {p_nome} ({letra}): ` {decimal_to_dms(val)} `"
                        )
                    st_local.markdown("\n".join(linhas_ang))

                    st_local.markdown(
                        f"**Área do triângulo:** ` {info['area_m2']:.3f} ` m²"
                    )

                with col2:
                    img_buf, fig = plotar_triangulo_info(info, estacao_op, conjunto_op)
                    st_local.pyplot(fig)

                xlsx_bytes = gerar_xlsx_com_figura(info, img_buf)
                st_local.download_button(
                    "📊 Baixar XLSX com resumo e figura do triângulo",
                    data=xlsx_bytes,
                    file_name="triangulo_ufpe_resumo_figura.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

    st_local.markdown(
        """
        <p class="footer-text">
            Versão do app: <code>UFPE_v21 — triângulo com ponto de vista na estação real (P1/P2/P3),
            croqui sem letras A/B/C nos vértices, caso especial Estação A / 1ª leitura com P1 na base esquerda (0,0),
            cabeçalho com data em formato DD/MM/AAAA.</code>
        </p>
        """,
        unsafe_allow_html=True,
    )


# ==================================================================
# Controle simples de "páginas" via session_state
# ==================================================================
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "carregar"

if st.session_state["pagina"] == "carregar":
    pagina_carregar_dados()
else:
    pagina_processamento()
