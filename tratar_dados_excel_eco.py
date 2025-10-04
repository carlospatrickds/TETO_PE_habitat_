import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import unicodedata

# Configuração da página
st.set_page_config(
    page_title="Consulta de Comunidades", 
    page_icon="🏘️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏘️ Sistema de Consulta - Escuta de Comunidades")
st.markdown("---")

# Função para normalizar texto (remover acentos e converter para minúsculas)
def normalizar_texto(texto):
    """Remove acentos e converte para minúsculas para busca insensitive"""
    if pd.isna(texto):
        return ""
    texto = str(texto)
    # Remove acentos
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto.lower().strip()

# Função para criar label descritivo das colunas
def criar_label_coluna(nome_coluna, dados_coluna, max_chars=30):
    """Cria um label descritivo com nome da coluna e amostra de valores"""
    nome_display = nome_coluna if len(nome_coluna) <= max_chars else nome_coluna[:max_chars-3] + "..."
    
    valores_nao_vazios = dados_coluna.dropna().unique()
    if len(valores_nao_vazios) > 0:
        amostra_valores = [str(x) for x in valores_nao_vazios[:3] if str(x) not in ['', 'nan', 'NaN']]
        if amostra_valores:
            amostra_text = ", ".join(amostra_valores)
            if len(amostra_text) > 25:
                amostra_text = amostra_text[:22] + "..."
            return f"{nome_display} │ 📊 {amostra_text}"
    
    return f"{nome_display} │ 📝 {len(dados_coluna.dropna())} valores"

# Função para buscar valores similares
def encontrar_valores_similares(valor_busca, lista_valores, limite=5):
    """Encontra valores similares na lista (busca case insensitive e sem acentos)"""
    if not valor_busca:
        return []
    
    valor_busca_normalizado = normalizar_texto(valor_busca)
    similares = []
    
    for valor in lista_valores:
        if valor_busca_normalizado in normalizar_texto(valor):
            similares.append(valor)
            if len(similares) >= limite:
                break
    
    return similares

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
                    # Para colunas textuais - SEMPRE permitir seleção múltipla
                    if df[coluna].dtype in ['object', 'string']:
                        valores_unicos = df[coluna].dropna().unique()
                        valores_unicos = [str(x) for x in valores_unicos if str(x) not in ['', 'nan', 'NaN']]
                        
                        if len(valores_unicos) > 0:
                            # Sistema de busca + seleção múltipla para TODAS as colunas textuais
                            st.sidebar.write("**🔍 Buscar valores:**")
                            
                            # Campo de busca
                            busca_texto = st.sidebar.text_input(
                                f"Digite para buscar em {coluna}:",
                                placeholder="Ex: vila, centro, norte...",
                                key=f"busca_{coluna}",
                                help="Busque valores por partes do texto (ignora acentos e maiúsculas)"
                            )
                            
                            # Encontrar valores similares baseado na busca
                            valores_disponiveis = sorted(valores_unicos)
                            
                            if busca_texto:
                                valores_similares = encontrar_valores_similares(busca_texto, valores_unicos)
                                if valores_similares:
                                    st.sidebar.success(f"🎯 {len(valores_similares)} valor(es) encontrado(s)")
                                    valores_disponiveis = valores_similares
                                else:
                                    st.sidebar.warning("❌ Nenhum valor encontrado")
                                    valores_disponiveis = []
                            
                            # Seleção múltipla sempre disponível
                            selecao = st.sidebar.multiselect(
                                f"**Selecione os valores para {coluna}:**",
                                options=valores_disponiveis,
                                default=[],
                                help="💡 **DICA:** Selecione múltiplas variações (com/sem acento, maiúsculas/minúsculas)",
                                key=f"multiselect_{coluna}"
                            )
                            
                            # Sugestões automáticas para valores comuns
                            if not busca_texto and not selecao:
                                # Mostrar valores mais frequentes como sugestão
                                valores_frequentes = df[coluna].value_counts().head(3).index.tolist()
                                if valores_frequentes:
                                    st.sidebar.caption(f"💡 Sugestões: {', '.join(map(str, valores_frequentes))}")
                            
                            if selecao:
                                filtros_aplicados[coluna] = selecao
                                st.sidebar.success(f"✅ {len(selecao)} valor(es) selecionado(s)")
                            
                            # Estatísticas
                            st.sidebar.caption(f"📊 {len(valores_unicos)} valores únicos encontrados")
                    
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
                    elif df[coluna].nunique() <= 10:
                        valores_unicos = df[coluna].dropna().unique()
                        selecao = st.sidebar.multiselect(
                            f"Valores em **{coluna}**:",
                            options=valores_unicos,
                            default=[],
                            help=f"Selecione múltiplos valores para {coluna}",
                            key=f"multiselect_small_{coluna}"
                        )
                        if selecao:
                            filtros_aplicados[coluna] = selecao
                
                else:
                    st.sidebar.warning(f"⚠️ Coluna '{coluna}' está vazia")
                
                st.sidebar.markdown("---")
        
        # Botão para limpar filtros
        col_btn1, col_btn2 = st.sidebar.columns(2)
        with col_btn1:
            if st.button("🧹 Limpar Filtros", use_container_width=True):
                filtros_aplicados = {}
                st.rerun()
        with col_btn2:
            if st.button("🔄 Recarregar", use_container_width=True):
                st.rerun()
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        for coluna, filtro in filtros_aplicados.items():
            if isinstance(filtro, list):  # Filtro de múltiplos valores
                # Converter tudo para string para comparação insensitive
                mask = df_filtrado[coluna].astype(str).apply(lambda x: normalizar_texto(x)).isin(
                    [normalizar_texto(str(x)) for x in filtro]
                )
                df_filtrado = df_filtrado[mask]
            elif isinstance(filtro, tuple):  # Filtro de faixa numérica
                mask = (df_filtrado[coluna] >= filtro[0]) & (df_filtrado[coluna] <= filtro[1])
                df_filtrado = df_filtrado[mask]
        
        # Mostrar estatísticas dos filtros
        st.sidebar.markdown("### 📊 Estatísticas")
        col_stat1, col_stat2 = st.sidebar.columns(2)
        with col_stat1:
            st.metric("Registros", len(df_filtrado))
        with col_btn2:
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
                        valores = ", ".join(map(str, filtro[:3]))  # Mostra apenas os 3 primeiros
                        if len(filtro) > 3:
                            valores += f"... (+{len(filtro)-3})"
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
                    filtros_texto = []
                    for coluna, filtro in filtros_aplicados.items():
                        if isinstance(filtro, list):
                            filtros_texto.append(f"{coluna}: {', '.join(map(str, filtro))}")
                        else:
                            filtros_texto.append(f"{coluna}: {filtro[0]} a {filtro[1]}")
                    
                    metadata = pd.DataFrame({
                        'Parâmetro': [
                            'Data da consulta', 
                            'Total de registros', 
                            'Registros filtrados',
                            'Filtros aplicados', 
                            'Arquivo original',
                            'Detalhes dos Filtros'
                        ],
                        'Valor': [
                            datetime.now().strftime('%d/%m/%Y %H:%M'),
                            len(df),
                            len(df_filtrado),
                            len(filtros_aplicados),
                            uploaded_file.name,
                            '; '.join(filtros_texto) if filtros_texto else 'Nenhum'
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

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        st.info("💡 Verifique se o arquivo é um Excel válido e não está corrompido.")

else:
    st.info("👆 Por favor, envie um arquivo Excel para começar a consulta.")
    
    # Instruções de uso
    with st.expander("📖 Como usar esta ferramenta - NOVAS FUNCIONALIDADES"):
        st.markdown("""
        ## 🎯 **Sistema de Busca Inteligente com Seleção Múltipla**

        ### 🔍 **Busca Inteligente:**
        - **Ignora acentos**: "vila" encontra "Vilã", "Vilá", "Vila"
        - **Case insensitive**: "norte" encontra "NORTE", "Norte", "nOrTe"
        - **Busca parcial**: "centro" encontra "Centro", "Centro-Sul", "Centro-Oeste"

        ### ✅ **Seleção Múltipla em TODOS os Filtros:**
        - **Selecione várias comunidades** de uma vez
        - **Combine variações de escrita**: "Vila Aliança", "vila alianca", "Vila Alianca"
        - **Filtre por múltiplos problemas** simultaneamente

        ### 💡 **Exemplo Prático:**
        Para encontrar **TODAS** as variações de uma comunidade:
        1. **Busque por "alianca"** (sem acento)
        2. **Selecione TODOS os resultados**: 
           - "Vila Aliança" 
           - "vila alianca"
           - "Vila Alianca"
           - "Comunidade Aliança"

        ### 🚨 **Problema Resolvido:**
        Não importa como foi digitado no cadastro - com acento, sem acento, maiúsculas, minúsculas - 
        agora você encontra **TODAS** as variações!
        """)

# Footer
st.markdown("---")
st.caption(f"🕐 Sistema de Consulta - Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
