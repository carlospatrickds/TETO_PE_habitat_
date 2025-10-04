import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import tempfile
import os

# Configuração da página
st.set_page_config(
    page_title="Consulta de Comunidades", 
    page_icon="🏘️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏘️ Sistema de Consulta - Escuta de Comunidades")
st.markdown("---")

# Upload do arquivo
uploaded_file = st.file_uploader("📤 Envie sua planilha Excel", type=["xlsx"])

if uploaded_file:
    try:
        # Ler o arquivo Excel
        df = pd.read_excel(uploaded_file)
        
        # Remover colunas completamente vazias
        df = df.dropna(axis=1, how='all')
        
        # Preencher NaN com string vazia para colunas de texto
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].fillna('')
        
        st.success(f"✅ Planilha carregada com sucesso! {len(df)} registros e {len(df.columns)} colunas encontradas.")
        
        # Sidebar para filtros
        st.sidebar.header("🔍 Filtros de Consulta")
        
        # Selecionar colunas para filtro (máximo 5 para não sobrecarregar)
        colunas_disponiveis = df.columns.tolist()
        colunas_filtro = st.sidebar.multiselect(
            "Selecione as colunas para filtrar:",
            options=colunas_disponiveis,
            default=colunas_disponiveis[:3] if len(colunas_disponiveis) >= 3 else colunas_disponiveis,
            help="Selecione até 5 colunas para melhor performance",
            max_selections=5
        )
        
        filtros_aplicados = {}
        
        # Criar filtros dinâmicos para cada coluna selecionada
        for coluna in colunas_filtro:
            if coluna in df.columns:
                # Verificar se a coluna tem dados
                if len(df[coluna].dropna()) > 0:
                    # Para colunas textuais
                    if df[coluna].dtype in ['object', 'string']:
                        valores_unicos = df[coluna].dropna().unique()
                        valores_unicos = [str(x) for x in valores_unicos if x not in ['', 'nan', 'NaN']]
                        
                        if len(valores_unicos) > 0:
                            if len(valores_unicos) <= 20:  # Se poucos valores, mostra todos
                                selecao = st.sidebar.multiselect(
                                    f"**{coluna}:**",
                                    options=valores_unicos,
                                    default=[],
                                    help=f"Selecione os valores para {coluna}"
                                )
                            else:  # Muitos valores, usar search
                                valor_padrao = st.sidebar.selectbox(
                                    f"**{coluna}:**",
                                    options=[""] + valores_unicos,
                                    help=f"Selecione um valor para {coluna}"
                                )
                                selecao = [valor_padrao] if valor_padrao else []
                            
                            if selecao:
                                filtros_aplicados[coluna] = selecao
                    
                    # Para colunas numéricas
                    elif np.issubdtype(df[coluna].dtype, np.number):
                        min_val = float(df[coluna].min())
                        max_val = float(df[coluna].max())
                        
                        if min_val != max_val:
                            faixa = st.sidebar.slider(
                                f"**{coluna}:**",
                                min_value=min_val,
                                max_value=max_val,
                                value=(min_val, max_val),
                                help=f"Selecione a faixa de valores para {coluna}"
                            )
                            filtros_aplicados[coluna] = faixa
        
        # Botão para limpar filtros
        if st.sidebar.button("🧹 Limpar Todos os Filtros"):
            filtros_aplicados = {}
            st.rerun()
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        for coluna, filtro in filtros_aplicados.items():
            if isinstance(filtro, list):  # Filtro de múltiplos valores
                mask = df_filtrado[coluna].isin(filtro)
                df_filtrado = df_filtrado[mask]
            elif isinstance(filtro, tuple):  # Filtro de faixa numérica
                mask = (df_filtrado[coluna] >= filtro[0]) & (df_filtrado[coluna] <= filtro[1])
                df_filtrado = df_filtrado[mask]
        
        # Mostrar estatísticas dos filtros
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Estatísticas")
        st.sidebar.metric("Registros encontrados", len(df_filtrado))
        st.sidebar.metric("Registros totais", len(df))
        st.sidebar.metric("Taxa de filtragem", f"{(len(df_filtrado)/len(df)*100):.1f}%")
        
        # Área principal de resultados
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"📊 Resultados da Consulta ({len(df_filtrado)} registros)")
            
            if len(df_filtrado) > 0:
                # Selecionar colunas para exibição
                colunas_exibicao = st.multiselect(
                    "Selecione as colunas para exibir:",
                    options=df.columns.tolist(),
                    default=df.columns.tolist()[:8] if len(df.columns) >= 8 else df.columns.tolist(),
                    help="Escolha quais colunas mostrar na tabela"
                )
                
                if colunas_exibicao:
                    df_exibicao = df_filtrado[colunas_exibicao]
                    
                    # Paginação
                    items_per_page = 20
                    total_pages = max(1, (len(df_exibicao) - 1) // items_per_page + 1)
                    
                    col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
                    with col_page2:
                        page_number = st.number_input(
                            "Página:", 
                            min_value=1, 
                            max_value=total_pages, 
                            value=1,
                            help=f"Total de {total_pages} páginas"
                        )
                    
                    start_idx = (page_number - 1) * items_per_page
                    end_idx = start_idx + items_per_page
                    
                    st.dataframe(
                        df_exibicao.iloc[start_idx:end_idx],
                        use_container_width=True,
                        height=500
                    )
                    
                    st.caption(f"Mostrando registros {start_idx + 1} a {min(end_idx, len(df_exibicao))} de {len(df_exibicao)}")
                else:
                    st.info("📝 Selecione pelo menos uma coluna para exibir.")
            else:
                st.warning("🔍 Nenhum registro encontrado com os filtros aplicados. Tente ajustar os critérios de busca.")
        
        with col2:
            st.subheader("📋 Resumo da Consulta")
            
            # Informações gerais
            st.metric("Colunas na planilha", len(df.columns))
            st.metric("Filtros aplicados", len(filtros_aplicados))
            
            # Mostrar filtros ativos
            if filtros_aplicados:
                st.write("**🎯 Filtros ativos:**")
                for coluna, filtro in filtros_aplicados.items():
                    if isinstance(filtro, list):
                        valores = ", ".join(map(str, filtro[:3]))  # Mostra apenas os 3 primeiros
                        if len(filtro) > 3:
                            valores += f"... (+{len(filtro)-3})"
                        st.write(f"• **{coluna}:** {valores}")
                    else:
                        st.write(f"• **{coluna}:** {filtro[0]} a {filtro[1]}")
            else:
                st.info("ℹ️ Nenhum filtro aplicado - mostrando todos os registros")
            
            # Botão rápido para exportar
            if len(df_filtrado) > 0:
                st.markdown("---")
                st.write("**📤 Exportação Rápida**")
        
        # Seção de exportação
        if len(df_filtrado) > 0:
            st.markdown("---")
            st.subheader("📤 Exportar Resultados")
            
            col_export1, col_export2, col_export3 = st.columns(3)
            
            with col_export1:
                # Exportar para Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtrado.to_excel(writer, index=False, sheet_name='Dados_Filtrados')
                    # Adicionar uma aba com metadados
                    metadata = pd.DataFrame({
                        'Parâmetro': ['Data da consulta', 'Total de registros', 'Filtros aplicados', 'Arquivo original'],
                        'Valor': [
                            datetime.now().strftime('%d/%m/%Y %H:%M'),
                            len(df_filtrado),
                            len(filtros_aplicados),
                            uploaded_file.name
                        ]
                    })
                    metadata.to_excel(writer, index=False, sheet_name='Metadados')
                
                st.download_button(
                    label="📊 Baixar Excel",
                    data=output.getvalue(),
                    file_name=f"consulta_comunidades_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )
            
            with col_export2:
                # Exportar para CSV
                csv_data = df_filtrado.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📝 Baixar CSV",
                    data=csv_data,
                    file_name=f"consulta_comunidades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_export3:
                # Exportar apenas colunas selecionadas
                if 'colunas_exibicao' in locals() and colunas_exibicao:
                    csv_selecionado = df_filtrado[colunas_exibicao].to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(
                        label="🎯 CSV das Colunas Selecionadas",
                        data=csv_selecionado,
                        file_name=f"consulta_selecionada_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        # Informações adicionais
        with st.expander("ℹ️ Informações da Planilha Original"):
            tab1, tab2, tab3 = st.tabs(["📋 Colunas", "📊 Estatísticas", "👀 Amostra"])
            
            with tab1:
                st.write("**Colunas disponíveis:**")
                colunas_por_linha = 4
                colunas = df.columns.tolist()
                
                for i in range(0, len(colunas), colunas_por_linha):
                    cols = st.columns(colunas_por_linha)
                    for j, col in enumerate(colunas[i:i+colunas_por_linha]):
                        with cols[j]:
                            st.code(col, language='text')
            
            with tab2:
                st.write(f"**Dimensões:** {len(df)} linhas × {len(df.columns)} colunas")
                st.write(f"**Colunas numéricas:** {len(df.select_dtypes(include=[np.number]).columns)}")
                st.write(f"**Colunas textuais:** {len(df.select_dtypes(include=['object']).columns)}")
                
                # Tipos de dados
                st.write("**Tipos de dados:**")
                tipos = df.dtypes.value_counts()
                for tipo, count in tipos.items():
                    st.write(f"- {tipo}: {count} colunas")
            
            with tab3:
                st.dataframe(df.head(5), use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        st.info("💡 Verifique se o arquivo é um Excel válido e não está corrompido.")

else:
    st.info("👆 Por favor, envie um arquivo Excel para começar a consulta.")
    
    # Instruções de uso
    with st.expander("📖 Como usar esta ferramenta"):
        st.markdown("""
        ## 🏘️ Sistema de Consulta - Escuta de Comunidades
        
        ### 🚀 **Funcionalidades:**
        
        1. **📤 Upload de Planilha**
           - Suporte para arquivos Excel (.xlsx)
           - Processamento automático de dados
        
        2. **🔍 Filtros Avançados**
           - Filtros por texto (seleção múltipla)
           - Filtros numéricos (faixa de valores)
           - Múltiplos filtros simultâneos
        
        3. **📊 Visualização Flexível**
           - Selecione quais colunas exibir
           - Paginação para grandes conjuntos de dados
           - Layout responsivo
        
        4. **📤 Exportação Completa**
           - Excel com metadados
           - CSV para análise externa
           - CSV apenas com colunas selecionadas
        
        ### 💡 **Dicas de Uso:**
        
        - **Comece filtrando por comunidade** para focar em áreas específicas
        - **Use múltiplos filtros** para refinamentos precisos
        - **Selecione apenas colunas relevantes** para visualização mais limpa
        - **Exporte em CSV** para usar em outros softwares
        - **Use a paginação** para navegar em grandes resultados
        
        ### 🎯 **Para Planilhas de Comunidades:**
        
        - Filtre por **comunidade/região**
        - Busque por **tipos de problemas específicos**
        - Filtre por **data** ou **período**
        - Exporte resultados para **relatórios e análises**
        """)

# Footer
st.markdown("---")
st.caption(f"🕐 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
