import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Conexão com Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# Nome da planilha no Google Sheets
SHEET_NAME = "TETO_Habitat"
spreadsheet = client.open(SHEET_NAME)

# Abas do Sheets
ws_projetos = spreadsheet.worksheet("projetos")
ws_orcamentos = spreadsheet.worksheet("orcamentos")
ws_itens = spreadsheet.worksheet("itens")
ws_orcamento_itens = spreadsheet.worksheet("orcamento_itens")

# --- App ---
st.title("📊 Gestão de Orçamentos - TETO Habitat")

# Carregar lista predefinida de itens
itens_predef = ws_itens.col_values(1)[1:]  # ignora cabeçalho

# Criar novo projeto
st.header("➕ Cadastrar novo projeto")
with st.form("form_projeto"):
    nome = st.text_input("Nome do projeto")
    tipo = st.selectbox("Tipo de projeto", ["Casa emergencial", "Sede comunitária", "Horta", "Torre de água", "Outro"])
    comunidade = st.text_input("Comunidade / Local")
    responsavel = st.text_input("Responsável")
    submitted = st.form_submit_button("Criar projeto")

if submitted:
    ws_projetos.append_row([nome, tipo, comunidade, responsavel])
    st.success(f"✅ Projeto '{nome}' cadastrado com sucesso!")

# Listar projetos
st.header("📋 Projetos cadastrados")
projetos = ws_projetos.get_all_records()

if projetos:
    for proj in projetos:
        with st.expander(f"{proj['nome']} - {proj['tipo']}"):
            st.write(f"**Comunidade:** {proj['comunidade']}")
            st.write(f"**Responsável:** {proj['responsavel']}")

            # Adicionar orçamento
            st.subheader("➕ Novo orçamento")
            with st.form(f"form_orcamento_{proj['nome']}"):
                nome_orc = st.text_input("Identificação do orçamento (ex: Ferreira Costa)")
                sub = st.form_submit_button("Criar orçamento")
            if sub:
                ws_orcamentos.append_row([proj['nome'], nome_orc])
                st.success(f"Orçamento '{nome_orc}' adicionado!")

            # Listar orçamentos do projeto
            orcamentos = pd.DataFrame(ws_orcamentos.get_all_records())
            orc_proj = orcamentos[orcamentos["projeto"] == proj["nome"]]

            for _, o in orc_proj.iterrows():
                with st.expander(f"🛒 {o['orcamento']}"):
                    st.write("Adicionar itens ao orçamento:")

                    with st.form(f"form_item_{o['orcamento']}"):
                        item = st.selectbox("Item", itens_predef)
                        qtd = st.number_input("Quantidade", min_value=1, value=1)
                        preco = st.number_input("Preço unitário (R$)", min_value=0.0, format="%.2f")
                        add_item = st.form_submit_button("Adicionar item")

                    if add_item:
                        ws_orcamento_itens.append_row([proj['nome'], o['orcamento'], item, qtd, preco, qtd*preco])
                        st.success(f"Item '{item}' adicionado em {o['orcamento']}!")

                    # Mostrar itens já cadastrados
                    df_itens = pd.DataFrame(ws_orcamento_itens.get_all_records())
                    df_show = df_itens[(df_itens["projeto"] == proj["nome"]) & (df_itens["orcamento"] == o["orcamento"])]
                    if not df_show.empty:
                        st.dataframe(df_show, use_container_width=True)
                        st.write(f"💰 **Total: R$ {df_show['total'].sum():,.2f}**")
