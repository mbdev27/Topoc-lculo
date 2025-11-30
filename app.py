import streamlit as st
import pandas as pd
from processamento import validar_dataframe, calcular_linha_a_linha, tabela_hz_por_serie, tabela_z_por_serie
from utils import download_modelo_excel

st.set_page_config(
    page_title="Método das Direções – UFPE",
    layout="wide"
)

# ---------------------------------------------------------
# CONTROLE DE PÁGINAS
# ---------------------------------------------------------
if "pagina" not in st.session_state:
    st.session_state.pagina = "carregar"

if "df" not in st.session_state:
    st.session_state.df = None

# ---------------------------------------------------------
# NAVEGAÇÃO
# ---------------------------------------------------------
menu = st.sidebar.radio(
    "Menu",
    ["1. Carregar dados", "2. Processamento"],
    index=0 if st.session_state.pagina == "carregar" else 1
)

st.session_state.pagina = "carregar" if menu == "1. Carregar dados" else "processamento"

# ---------------------------------------------------------
# PÁGINA 1 — CARREGAR DADOS
# ---------------------------------------------------------
if st.session_state.pagina == "carregar":

    st.title("📄 1. Modelo da planilha")
    st.write("Baixe o modelo oficial:")
    st.download_button(
        label="📥 Baixar modelo Excel",
        data=download_modelo_excel(),
        file_name="modelo_planilha_ufpe.xlsx"
    )

    st.markdown("---")

    st.title("📤 2. Carregar dados de campo")

    uploaded = st.file_uploader("Envie sua planilha (.xlsx ou .csv)", type=["xlsx", "csv"])

    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded, dtype=str)
            else:
                df = pd.read_excel(uploaded, dtype=str)

            df_validado, erros = validar_dataframe(df)

            if erros:
                st.error("⚠️ Erros encontrados:")
                for e in erros:
                    st.write("- ", e)
            else:
                st.success("Arquivo validado com sucesso!")
                st.session_state.df = df_validado

                if st.button("Ir para processamento ➡️"):
                    st.session_state.pagina = "processamento"
                    st.experimental_rerun()

        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

# ---------------------------------------------------------
# PÁGINA 2 — PROCESSAMENTO
# ---------------------------------------------------------
if st.session_state.pagina == "processamento":

    if st.session_state.df is None:
        st.error("Você precisa enviar a planilha primeiro!")
        st.stop()

    # ============================================
    # CABEÇALHO UFPE – sempre no topo
    # ============================================
    st.markdown("""
    <h1 style="text-align:center;">Universidade Federal de Pernambuco</h1>
    <h3 style="text-align:center;">Departamento de Engenharia Cartográfica</h3>
    <hr>
    """, unsafe_allow_html=True)

    st.title("📐 Calculadora de Ângulos e Distâncias – Método das Direções")

    # ------------------------------------------
    # PROCESSAMENTO
    # ------------------------------------------
    df_proc = calcular_linha_a_linha(st.session_state.df)

    st.subheader("3. Tabela com cálculos linha a linha")
    st.dataframe(df_proc, use_container_width=True)

    st.subheader("4. Tabela Hz por série")
    st.dataframe(tabela_hz_por_serie(df_proc), use_container_width=True)

    st.subheader("5. Tabela Z por série")
    st.dataframe(tabela_z_por_serie(df_proc), use_container_width=True)

    st.subheader("6. Download dos resultados")
    st.download_button(
        "Baixar resultados (xlsx)",
        df_proc.to_excel(index=False),
        file_name="resultados_ufpe.xlsx"
    )
