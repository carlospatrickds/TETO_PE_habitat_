import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import unicodedata
import re

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
def criar_label_coluna(nome_coluna, dados_coluna, mostrar_numero_coluna=False, numero_coluna=None, max_chars=30):
    """Cria um label descritivo com nome da coluna e amostra de valores"""
    # Nome da coluna (truncado se muito longo)
    nome_display = nome_coluna if len(nome_coluna) <= max_chars else nome_coluna[:max_chars-3] + "..."
    
    # Adicionar número da coluna se solicitado
    if mostrar_numero_coluna and numero_coluna is not None:
        prefixo = f"Col.{numero_coluna+1:02d} │ "
    else:
        prefixo = ""
    
    valores_nao_vazios = dados_coluna.dropna().unique()
    if len(valores_nao_vazios) > 0:
        amostra_valores = [str(x) for x in valores_nao_vazios[:3] if str(x) not in ['', 'nan', 'NaN']]
        if amostra_valores:
            amostra_text = ", ".join(amostra_valores)
            if len(amostra_text) > 25:
                amostra_text = amostra_text[:22] + "..."
            return f"{prefixo}{nome_display} │ 📊 {amostra_text}"
    
    return f"{prefixo}{nome_display} │ 📝 {len(dados_coluna.dropna())} valores"

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

# Função para buscar colunas por número ou texto
def buscar_colunas_rapido(termo_busca, colunas_com_labels, mostrar_numeros=True):
    """Busca colunas por número (ex: '12') ou por texto (ex: 'comunidade')"""
    if not termo_busca:
        return colunas_com_labels
    
    resultados = []
    termo_busca = termo_busca.strip().lower()
    
    for coluna, label, idx in colunas_com_labels:
        # Buscar por número da coluna (ex: "12" encontra "Col.12")
        if mostrar_numeros and termo_busca.isdigit():
            numero_coluna = idx + 1
            if str(numero_coluna) == termo_busca or f"col.{termo_busca.zfill(2)}" in label.lower():
                resultados.append((coluna, label, idx))
        
        # Buscar por texto no nome da coluna
        elif termo_busca in normalizar_texto(coluna):
            resultados.append((coluna, label, idx))
        
        # Buscar por texto no label completo
        elif termo_busca in normalizar_texto(label):
            resultados.append((coluna, label, idx))
    
    return resultados

# Guia de instruções
with st.expander("📚 GUIA DE INSTRUÇÕES - Como usar esta ferramenta", expanded=False):
    tab_instrucoes, tab_exemplos, tab_dicas, tab_busca = st.tabs(["📖 Instruções", "🎯 Exemplos Práticos", "💡 Dicas Avançadas", "🔎 Busca Rápida"])
    
    with tab_instrucoes:
        st.markdown("""
        ## 🎯 **COMO USAR ESTA FERRAMENTA**
        
        ### **1. 📤 CARREGAR PLANILHA**
        - Faça upload de qualquer arquivo Excel (.xlsx)
        - A planilha será processada automaticamente
        - Colunas vazias serão removidas
        
        ### **2. 🔍 CONFIGURAR FILTROS**
        - **Selecione colunas para filtrar**: Escolha até 6 colunas na barra lateral
        - **Use a busca inteligente**: Digite parte do texto para encontrar valores
        - **Seleção múltipla**: Escolha vários valores para cada filtro
        - **Filtros numéricos**: Use sliders para faixas de valores
        
        ### **3. 📊 VISUALIZAR RESULTADOS**
        - **Selecione colunas para exibir**: Escolha quais colunas ver na tabela
        - **Navegue pelas páginas**: Use paginação para muitos resultados
        - **Veja o resumo**: Confira estatísticas na barra lateral
        
        ### **4. 📤 EXPORTAR DADOS**
        - **Excel completo**: Com metadados da consulta
        - **CSV simples**: Para usar em outros programas
        - **Colunas selecionadas**: Apenas as colunas que você escolheu
        """)
    
    with tab_exemplos:
        st.markdown("""
        ## 🎯 **EXEMPLOS PRÁTICOS**
        
        ### **🔍 EXEMPLO 1: Filtrar por Comunidade**
        ```
        1. Selecione a coluna "Comunidade" nos filtros
        2. Digite "aliança" no campo de busca
        3. Selecione TODAS as variações:
           - "Vila Aliança"
           - "vila alianca" 
           - "Vila Alianca"
        4. Aplique o filtro
        ```
        
        ### **🔢 EXEMPLO 2: Filtrar por Idade e Problema**
        ```
        1. Selecione "Idade" e "Problema_reportado"
        2. Em "Idade": ajuste para 18-60 anos
        3. Em "Problema_reportado": busque "água" e selecione:
           - "Falta de água"
           - "Água contaminada"
           - "Falta d'agua"
        4. Veja os resultados combinados
        ```
        
        ### **📊 EXEMPLO 3: Exportar Dados Específicos**
        ```
        1. Aplique seus filtros
        2. Selecione apenas colunas importantes:
           - "Nome", "Comunidade", "Problema", "Data"
        3. Exporte como "Colunas Selecionadas"
        4. Use no Excel ou outro software
        ```
        """)
    
    with tab_dicas:
        st.markdown("""
        ## 💡 **DICAS AVANÇADAS**
        
        ### **🎯 BUSCA INTELIGENTE**
        - **Ignora acentos**: "alem" encontra "Além", "Alem", "Alêm"
        - **Case insensitive**: "NORTE" = "norte" = "Norte"
        - **Busca parcial**: "centro" encontra "Centro", "Centro-Sul"
        
        ### **📈 NUMERAÇÃO CORRETA**
        - **Linhas**: A contagem inicia na linha 2 (dados reais)
        - **Cabeçalho**: Linha 1 no Excel = Cabeçalhos no sistema
        - **Colunas**: Opção para mostrar números (Col.01, Col.02, etc.)
        
        ### **🚀 PERFORMANCE**
        - **Limite de 6 filtros**: Para não sobrecarregar
        - **Paginação**: Navegue por lotes de 20 registros
        - **Exportação seletiva**: Baixe apenas o necessário
        
        ### **🔧 SOLUÇÃO DE PROBLEMAS**
        - **Valores não aparecem**: Verifique se a coluna tem dados
        - **Busca não funciona**: Tente termos mais simples
        - **Exportação falha**: Tente formato CSV
        """)
    
    with tab_busca:
        st.markdown("""
        ## 🔎 **SISTEMA DE BUSCA RÁPIDA**
        
        ### **🔢 BUSCAR POR NÚMERO DA COLUNA**
        ```
        Digite: "12"
        Retorna: "Col.12 │ Nome da Coluna │ 📊 amostra..."
        ```
        
        ### **📝 BUSCAR POR TEXTO**
        ```
        Digite: "comunidade"
        Retorna: Todas as colunas com "comunidade" no nome
        ```
        
        ### **🎯 BUSCAR POR CONTEÚDO**
        ```
        Digite: "água"
        Retorna: Colunas que contenham "água" nos valores
        ```
        
        ### **💡 EXEMPLOS PRÁTICOS:**
        - **"25"** → Mostra a coluna número 25
        - **"nome"** → Encontra colunas como "Nome", "Nome completo", etc.
        - **"data"** → Encontra "Data nascimento", "Data cadastro", etc.
        - **"rua"** → Encontra "Endereço", "Rua", "Logradouro", etc.
        """)

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
        
        # Configuração opcional - mostrar números das colunas
        st.sidebar.header("⚙️ Configurações")
        mostrar_numeros_colunas = st.sidebar.checkbox(
            "Mostrar números das colunas", 
            value=True,
            help="Exibe 'Col.01', 'Col.02' ao lado dos nomes das colunas"
        )
        
        # Sidebar para filtros
        st.sidebar.header("🔍 Filtros de Consulta")
        
        # Criar labels descritivos para todas as colunas
        colunas_com_labels = []
        for i, coluna in enumerate(df.columns):
            label = criar_label_coluna(coluna, df[coluna], mostrar_numeros_colunas, i)
            colunas_com_labels.append((coluna, label, i))  # Agora inclui o índice
        
        # BUSCA RÁPIDA POR COLUNAS
        st.sidebar.markdown("### 🔎 Busca Rápida de Colunas")
        busca_rapida = st.sidebar.text_input(
            "Buscar coluna por número ou texto:",
            placeholder="Ex: 12, comunidade, água...",
            help="Digite o número da coluna (ex: '12') ou texto para buscar"
        )
        
        # Aplicar busca rápida se houver termo
        if busca_rapida:
            colunas_filtradas = buscar_colunas_rapido(busca_rapida, colunas_com_labels, mostrar_numeros_colunas)
            if colunas_filtradas:
                st.sidebar.success(f"🎯 {len(colunas_filtradas)} coluna(s) encontrada(s)")
                
                # Mostrar resultados da busca
                with st.sidebar.expander("📋 Resultados da Busca", expanded=True):
                    for coluna, label, idx in colunas_filtradas:
                        st.write(f"**{label}**")
            else:
                st.sidebar.warning("❌ Nenhuma coluna encontrada")
                colunas_filtradas = colunas_com_labels
        else:
            colunas_filtradas = colunas_com_labels
        
        # Selecionar colunas para filtro (usando lista filtrada ou completa)
        colunas_filtro_selecionadas = st.sidebar.multiselect(
            "Selecione as colunas para filtrar:",
            options=[label for _, label, _ in colunas_filtradas],
            default=[label for _, label, _ in colunas_filtradas[:3]] if len(colunas_filtradas) >= 3 else [label for _, label, _ in colunas_filtradas],
            help="Cada coluna selecionada mostrará um filtro específico abaixo",
            max_selections=6
        )
        
        # Mapear labels de volta para nomes das colunas
        label_para_coluna = {label: (coluna, idx) for coluna, label, idx in colunas_com_labels}
        colunas_filtro = [label_para_coluna[label] for label in colunas_filtro_selecionadas]
        
        filtros_aplicados = {}
        
        # Criar filtros dinâmicos para cada coluna selecionada
        for coluna_info in colunas_filtro:
            coluna, idx_coluna = coluna_info
            
            if coluna in df.columns:
                # Mostrar número da coluna no título do filtro
                if mostrar_numeros_colunas:
                    titulo_filtro = f"**🎯 Filtro Col.{idx_coluna+1:02d}: {coluna}**"
                else:
                    titulo_filtro = f"**🎯 Filtro: {coluna}**"
                
                st.sidebar.markdown(titulo_filtro)
                
                # Verificar se a coluna tem dados
                if len(df[coluna].dropna()) > 0:
                    # Para colunas textuais - SEMPRE permitir seleção múltipla
                    if df[coluna].dtype in ['object', 'string']:
                        valores_unicos = df[coluna].dropna().unique()
                        valores_unicos = [str(x) for x in valores_unicos if str(x) not in ['', 'nan', 'NaN']]
                        
                        if len(valores_unicos) > 0:
                            # Sistema de busca + seleção múltipla
                            st.sidebar.write("**🔍 Buscar valores:**")
                            
                            # Campo de busca
                            busca_texto = st.sidebar.text_input(
                                f"Digite para buscar:",
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
                                f"**Selecione os valores:**",
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
                                f"Faixa de valores:",
                                min_value=min_val,
                                max_value=max_val,
                                value=(min_val, max_val),
                                help=f"Selecione a faixa de valores",
                                key=f"faixa_{coluna}"
                            )
                            filtros_aplicados[coluna] = faixa
                            st.sidebar.caption(f"📈 Valores de {min_val:.2f} a {max_val:.2f}")
                    
                    # Para colunas booleanas ou com poucos valores únicos
                    elif df[coluna].nunique() <= 10:
                        valores_unicos = df[coluna].dropna().unique()
                        selecao = st.sidebar.multiselect(
                            f"Valores:",
                            options=valores_unicos,
                            default=[],
                            help=f"Selecione múltiplos valores",
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
                    options=[label for _, label, _ in colunas_com_labels],
                    default=[label for _, label, _ in colunas_com_labels[:8]] if len(colunas_com_labels) >= 8 else [label for _, label, _ in colunas_com_labels],
                    help="Escolha quais colunas mostrar na tabela"
                )
                
                # Converter labels de volta para nomes das colunas
                colunas_exibicao = [label_para_coluna[label][0] for label in colunas_exibicao_labels]
                
                if colunas_exibicao:
                    df_exibicao = df_filtrado[colunas_exibicao]
                    
                    # Paginação com numeração correta (linha 2 = primeiro dado real)
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
                    
                    # Mostrar dataframe com numeração correta
                    st.dataframe(
                        df_exibicao.iloc[start_idx:end_idx],
                        use_container_width=True,
                        height=500
                    )
                    
                    # Mostrar numeração correta das linhas (considerando cabeçalho Excel)
                    linha_inicio_real = start_idx + 2  # +2 porque linha 1 Excel = cabeçalho, linha 2 = primeiro dado
                    linha_fim_real = min(end_idx, len(df_exibicao)) + 1  # +1 para compensar
                    
                    st.caption(f"📋 Mostrando registros {start_idx + 1} a {min(end_idx, len(df_exibicao))} de {len(df_exibicao)} | "
                             f"📄 Linhas Excel: {linha_inicio_real} a {linha_fim_real}")
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
                        valores = ", ".join(map(str, filtro[:2]))
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
                        data=cselecionado,
                        file_name=f"colunas_selecionadas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        st.info("💡 Verifique se o arquivo é um Excel válido e não está corrompido.")

else:
    st.info("👆 Por favor, envie um arquivo Excel para começar a consulta.")

# Footer
st.markdown("---")
st.caption(f"🕐 Sistema de Consulta - Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
           f"📊 Numeração de linhas compatível com Excel (Linha 1 = Cabeçalhos)")
