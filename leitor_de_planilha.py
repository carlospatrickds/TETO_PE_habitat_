import streamlit as st
import pandas as pd

st.title("🔎 Busca por Cabeçalho na Planilha")

uploaded_file = st.file_uploader("Envie sua planilha Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Listar cabeçalhos
    colunas = df.columns.tolist()
    escolha = st.selectbox("Escolha um cabeçalho:", colunas)

    if escolha:
        st.write(f"📊 Valores da coluna **{escolha}**:")
        st.dataframe(df[[escolha]])
