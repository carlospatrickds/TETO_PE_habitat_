import streamlit as st
import pandas as pd

# --- Configuração inicial ---
st.set_page_config(page_title="Habitat Orçamentos", layout="wide")
st.title("📊 Gestão de Orçamentos - TETO Habitat")

# --- Banco de dados temporário ---
if "projetos" not in st.session_state:
    st.session_state.projetos = []

# --- Cadastro de projeto ---
st.header("➕ Cadastrar novo projeto")

with st.form("form_projeto"):
    nome = st.text_input("Nome do projeto")
    tipo = st.selectbox("Tipo de projeto", ["Casa emergencial", "Sede comunitária", "Horta", "Torre de água", "Outro"])
    comunidade = st.text_input("Comunidade / Local")
    responsavel = st.text_input("Responsável")
    submitted = st.form_submit_button("Criar projeto")

if submitted:
    projeto = {
        "nome": nome,
        "tipo": tipo,
        "comunidade": comunidade,
        "responsavel": responsavel,
        "orcamento": []
    }
    st.session_state.projetos.append(projeto)
    st.success(f"✅ Projeto '{nome}' adicionado com sucesso!")

# --- Listar projetos cadastrados ---
st.header("📋 Projetos cadastrados")
if len(st.session_state.projetos) == 0:
    st.info("Nenhum projeto cadastrado ainda.")
else:
    for idx, projeto in enumerate(st.session_state.projetos):
        with st.expander(f"{projeto['nome']} - {projeto['tipo']}"):
            st.write(f"**Comunidade:** {projeto['comunidade']}")
            st.write(f"**Responsável:** {projeto['responsavel']}")

            # --- Cadastro de itens de orçamento ---
            st.subheader("Orçamento")
            with st.form(f"form_item_{idx}"):
                item = st.text_input("Item")
                qtd = st.number_input("Quantidade", min_value=1, value=1)
                preco = st.number_input("Preço unitário (R$)", min_value=0.0, value=0.0, format="%.2f")
                add_item = st.form_submit_button("Adicionar item")

            if add_item and item:
                projeto["orcamento"].append({
                    "item": item,
                    "quantidade": qtd,
                    "preco_unitario": preco,
                    "total": qtd * preco
                })
                st.success(f"Item '{item}' adicionado!")

            # --- Mostrar orçamento ---
            if projeto["orcamento"]:
                df = pd.DataFrame(projeto["orcamento"])
                st.dataframe(df, use_container_width=True)
                st.write(f"💰 **Total do projeto: R$ {df['total'].sum():,.2f}**")

                # --- Exportar ---
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Baixar orçamento (CSV)",
                    data=csv,
                    file_name=f"orcamento_{projeto['nome']}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Nenhum item de orçamento adicionado ainda.")

