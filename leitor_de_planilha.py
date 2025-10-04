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

# Função para criar label descritivo das colunas
def criar_label_coluna(nome_coluna, dados_coluna, max_chars=30):
    """Cria um label descritivo com nome da coluna e amostra de valores"""
    # Nome da coluna (truncado se muito longo)
    nome_display = nome_coluna if len(nome_coluna) <= max_chars else nome_coluna[:max_chars-3] + "..."
    
    # Amostra de valores não vazios
    valores_nao_vazios = dados_coluna.dropna().unique()
    if len(valores_nao_vazios) > 0:
        # Pegar os primeiros 2-3 valores como amostra
        amostra_valores = [str(x) for x in valores_nao_vazios[:3] if str(x) not in ['', 'nan', 'NaN']]
        if amostra_valores:
            amostra_text = ", ".join(amostra_valores)
            if len(amostra_text) > 25:
                amostra_text = amostra_text[:22] + "..."
            return f"{nome_display} │ 📊 {amostra_text}"
    
    return f"{nome_display} │ 📝 {len(dados_coluna.dropna())} valores"

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
        
        # Criar labels descritivos para todas as colunas
        colunas_com_labels = []
        for coluna in df.columns:
            label = criar_label_coluna(coluna, df[coluna])
            colunas_com_labels.append((coluna, label))
        
        # Selecionar colunas para filtro
        colunas_filtro_selecionadas = st.sidebar.multiselect(
            "Selecione as colunas para filtrar:",
            options=[label for _, label in colunas_com_labels],
            default=[label for _, label in colunas_com_labels[:3]] if len(colunas_com_labels) >= 3 else [label for _, label in colunas_com_labels],
            help="Cada coluna selecionada mostrará um filtro específico abaixo",
            max_selections=6
        )
        
        # Mapear labels de volta para nomes das colunas
        label_para_coluna = {label: coluna for coluna, label in colunas_com_labels}
        colunas_filtro = [label_para_coluna[label] for label in colunas_filtro_selecionadas]
        
        filtros_aplicados = {}
        
        # Criar filtros dinâmicos para cada coluna selecionada
        for coluna in colunas_filtro:
            if coluna in df.columns:
                st.sidebar.markdown(f"**🎯 Filtro: {coluna}**")
                
                # Verificar se a coluna tem dados
                if len(df[coluna].dropna()) > 0:
                    # Para colunas textuais
                    if df[coluna].dtype in ['object', 'string']:
                        valores_unicos = df[coluna].dropna().unique()
                        valores_unicos = [str(x) for x in valores_unicos if str(x) not in ['', 'nan', 'NaN']]
                        
                        if len(valores_unicos) > 0:
                            if len(valores_unicos) <= 20:  # Se poucos valores, mostra todos
                                selecao = st.sidebar.multiselect(
                                    f"Valores em **{coluna}**:",
                                    options=valores_unicos,
                                    default=[],
                                    help=f"Selecione os valores para filtrar em {coluna}",
                                    key=f"filtro_{coluna}"
                                )
                            else:  # Muitos valores, usar search com selectbox
                                st.sidebar.info(f"📋 {len(valores_unicos)} valores únicos encontrados")
                                valor_padrao = st.sidebar.selectbox(
                                    f"Buscar em **{coluna}**:",
                                    options=[""] + sorted(valores_unicos),
                                    help=f"Selecione um valor para filtrar em {coluna}",
                                    key=f"busca_{coluna}"
                                )
                                selecao = [valor_padrao] if valor_padrao else []
                            
                            if selecao:
                                filtros_aplicados[coluna] = selecao
                            else:
                                # Mostrar estatística rápida
                                st.sidebar.caption(f"💡 {len(valores_unicos)} valores únicos")
                    
                    # Para colunas numéricas
                    elif np.issubdtype(df[coluna].dtype, np.number):
                        min_val = float(df[coluna].min())
                        max_val = float(df[coluna].max())
                        
                        if min_val != max_val:
                            faixa = st.sidebar.slider(
                                f"Faixa de valores em **{coluna}**:",
                                min_value=min_val,
                                max_value=max_val,
                                value=(min_val, max_val),
                                help=f"Selecione a faixa de valores para {coluna}",
                                key=f"faixa_{coluna}"
                            )
                            filtros_aplicados[coluna] = faixa
                            st.sidebar.caption(f"📈 Valores de {min_val:.2f} a {max_val:.2f}")
                    
                    # Para colunas booleanas ou com poucos valores únicos
                    elif df[coluna].nunique() <= 5:
                        valores_unicos = df[coluna].dropna().unique()
                        selecao = st.sidebar.multiselect(
                            f"Valores em **{coluna}**:",
                            options=valores_unicos,
                            default=[],
                            help=f"Selecione os valores para {coluna}",
                            key=f"bool_{coluna}"
                        )
                        if selecao:
                            filtros_aplicados[coluna] = selecao
                
                else:
                    st.sidebar.warning(f"⚠️ Coluna '{coluna}' está vazia")
                
                st.sidebar.markdown("---")
        
        # Botão para limpar filtros
        if st.sidebar.button("🧹 Limpar Todos os Filtros", use_container_width=True):
            filtros_aplicados = {}
            st.rerun()
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        for coluna, filtro in filtros_aplicados.items():
            if isinstance(filtro, list):  # Filtro de múltiplos valores
                mask = df_filtrado[coluna].astype(str).isin([str(x) for x in filtro])
                df_filtrado = df_filtrado[mask]
            elif isinstance(filtro, tuple):  # Filtro de faixa numérica
                mask = (df_filtrado[coluna] >= filtro[0]) & (df_filtrado[coluna] <= filtro[1])
                df_filtrado = df_filtrado[mask]
        
        # Mostrar estatísticas dos filtros
        st.sidebar.markdown("### 📊 Estatísticas")
        col_stat1, col_stat2 = st.sidebar.columns(2)
        with col_stat1:
            st.metric("Registros", len(df_filtrado))
        with col_stat2:
            st.metric("Total", len(df))
        
        taxa_filtro = (len(df_filtrado)/len(df)*100) if len(df) > 0 else 0
        st.sidebar.metric("Taxa", f"{taxa_filtro:.1f}%")
        
        # Área principal de resultados
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"📊 Resultados da Consulta ({len(df_filtrado)} registros)")
            
            if len(df_filtrado) > 0:
                # Selecionar colunas para exibição com labels
                colunas_exibicao_labels = st.multiselect(
                    "Selecione as colunas para exibir:",
                    options=[label for _, label in colunas_com_labels],
                    default=[label for _, label in colunas_com_labels[:8]] if len(colunas_com_labels) >= 8 else [label for _, label in colunas_com_labels],
                    help="Escolha quais colunas mostrar na tabela"
                )
                
                # Converter labels de volta para nomes das colunas
                colunas_exibicao = [label_para_coluna[label] for label in colunas_exibicao_labels]
                
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
                    
                    # Mostrar dataframe com os nomes originais das colunas
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
            st.metric("Colunas", len(df.columns))
            st.metric("Filtros", len(filtros_aplicados))
            
            # Mostrar filtros ativos
            if filtros_aplicados:
                st.write("**🎯 Filtros ativos:**")
                for coluna, filtro in filtros_aplicados.items():
                    if isinstance(filtro, list):
                        valores = ", ".join(map(str, filtro[:2]))  # Mostra apenas os 2 primeiros
                        if len(filtro) > 2:
                            valores += f"... (+{len(filtro)-2})"
                        st.write(f"• **{coluna}:** {valores}")
                    else:
                        st.write(f"• **{coluna}:** {filtro[0]:.2f} a {filtro[1]:.2f}")
            else:
                st.info("ℹ️ Nenhum filtro aplicado")
            
            # Botão rápido para exportar
            if len(df_filtrado) > 0:
                st.markdown("---")
                st.write("**📤 Exportação Rápida**")
                
                # Exportação rápida em CSV
                csv_rapido = df_filtrado.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="💾 Baixar CSV",
                    data=csv_rapido,
                    file_name=f"consulta_rapida_{datetime.now().strftime('%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        # Seção de exportação completa
        if len(df_filtrado) > 0:
            st.markdown("---")
            st.subheader("📤 Exportar Resultados Completos")
            
            col_export1, col_export2, col_export3 = st.columns(3)
            
            with col_export1:
                # Exportar para Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtrado.to_excel(writer, index=False, sheet_name='Dados_Filtrados')
                    
                    # Adicionar uma aba com metadados
                    metadata = pd.DataFrame({
                        'Parâmetro': [
                            'Data da consulta', 
                            'Total de registros', 
                            'Registros filtrados',
                            'Filtros aplicados', 
                            'Arquivo original'
                        ],
                        'Valor': [
                            datetime.now().strftime('%d/%m/%Y %H:%M'),
                            len(df),
                            len(df_filtrado),
                            len(filtros_aplicados),
                            uploaded_file.name
                        ]
                    })
                    metadata.to_excel(writer, index=False, sheet_name='Metadados')
                
                st.download_button(
                    label="📊 Excel Completo",
                    data=output.getvalue(),
                    file_name=f"consulta_comunidades_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )
            
            with col_export2:
                # Exportar para CSV
                csv_data = df_filtrado.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📝 CSV Completo",
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
                        label="🎯 Colunas Selecionadas",
                        data=csv_selecionado,
                        file_name=f"colunas_selecionadas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        # Informações adicionais da planilha
        with st.expander("🔍 Explorar Colunas da Planilha"):
            tab1, tab2 = st.tabs(["📋 Lista de Colunas", "📊 Estatísticas"])
            
            with tab1:
                st.write("**Todas as colunas disponíveis:**")
                
                # Agrupar colunas por tipo
                colunas_texto = df.select_dtypes(include=['object']).columns.tolist()
                colunas_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
                colunas_outras = [col for col in df.columns if col not in colunas_texto + colunas_numericas]
                
                if colunas_texto:
                    st.write("#### 📝 Colunas Textuais:")
                    for coluna in colunas_texto:
                        valores_unicos = df[coluna].dropna().unique()
                        amostra = ", ".join([str(x) for x in valores_unicos[:2] if str(x) not in ['', 'nan']])
                        if len(valores_unicos) > 2:
                            amostra += f"... (+{len(valores_unicos)-2})"
                        st.write(f"- **{coluna}:** {amostra}")
                
                if colunas_numericas:
                    st.write("#### 🔢 Colunas Numéricas:")
                    for coluna in colunas_numericas:
                        min_val = df[coluna].min()
                        max_val = df[coluna].max()
                        st.write(f"- **{coluna}:** {min_val:.2f} a {max_val:.2f}")
                
                if colunas_outras:
                    st.write("#### 🔧 Outras Colunas:")
                    for coluna in colunas_outras:
                        st.write(f"- **{coluna}**")
            
            with tab2:
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("Total Colunas", len(df.columns))
                with col_stat2:
                    st.metric("Colunas Texto", len(colunas_texto))
                with col_stat3:
                    st.metric("Colunas Númericas", len(colunas_numericas))
                
                st.write("**Amostra dos dados:**")
                st.dataframe(df.head(3), use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        st.info("💡 Verifique se o arquivo é um Excel válido e não está corrompido.")

else:
    st.info("👆 Por favor, envie um arquivo Excel para começar a consulta.")
    
    # Instruções de uso
    with st.expander("📖 Como usar esta ferramenta"):
        st.markdown("""
        ## 🎯 **Nova Funcionalidade: Labels Descritivos**
        
        Agora cada coluna mostra:
        - **📝 Nome da coluna**
        - **📊 Amostra dos valores** contidos nela
        - **🔢 Estatísticas** rápidas
        
        ### 💡 **Exemplo:**
        - `Comunidade │ 📊 Vila Aliança, Morro doce...`
        - `Idade │ 📈 18.0 a 85.0`
        - `Problemas │ 📊 Falta de água, Esgoto...`
        
        Isso ajuda a identificar rapidamente qual coluna usar para cada filtro!
        """)

# Footer
st.markdown("---")
st.caption(f"🕐 Sistema de Consulta - Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
