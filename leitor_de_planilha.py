import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile
import os

# Configuração da página
st.set_page_config(page_title="Consulta de Comunidades", page_icon="🏘️", layout="wide")

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
        
        st.success(f"✅ Planilha carregada com sucesso! {len(df)} registros e {len(df.columns)} colunas encontradas.")
        
        # Sidebar para filtros
        st.sidebar.header("🔍 Filtros de Consulta")
        
        # Selecionar colunas para filtro
        colunas_filtro = st.sidebar.multiselect(
            "Selecione as colunas para filtrar:",
            options=df.columns.tolist(),
            default=df.columns.tolist()[:3] if len(df.columns) >= 3 else df.columns.tolist()
        )
        
        filtros_aplicados = {}
        
        # Criar filtros dinâmicos para cada coluna selecionada
        for coluna in colunas_filtro:
            if coluna in df.columns:
                # Verificar o tipo de dados
                if df[coluna].dtype in ['object', 'string']:
                    # Para colunas textuais, usar multiselect
                    valores_unicos = df[coluna].dropna().unique().tolist()
                    if len(valores_unicos) > 0:
                        selecao = st.sidebar.multiselect(
                            f"Filtrar {coluna}:",
                            options=valores_unicos,
                            help=f"Selecione os valores para filtrar em {coluna}"
                        )
                        if selecao:
                            filtros_aplicados[coluna] = selecao
                
                elif np.issubdtype(df[coluna].dtype, np.number):
                    # Para colunas numéricas, usar range slider
                    if not df[coluna].isna().all():
                        min_val = float(df[coluna].min())
                        max_val = float(df[coluna].max())
                        if min_val != max_val:
                            faixa = st.sidebar.slider(
                                f"Faixa para {coluna}:",
                                min_value=min_val,
                                max_value=max_val,
                                value=(min_val, max_val),
                                help=f"Selecione a faixa de valores para {coluna}"
                            )
                            filtros_aplicados[coluna] = faixa
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        for coluna, filtro in filtros_aplicados.items():
            if isinstance(filtro, list):  # Filtro de múltiplos valores
                df_filtrado = df_filtrado[df_filtrado[coluna].isin(filtro)]
            elif isinstance(filtro, tuple):  # Filtro de faixa numérica
                df_filtrado = df_filtrado[
                    (df_filtrado[coluna] >= filtro[0]) & 
                    (df_filtrado[coluna] <= filtro[1])
                ]
        
        # Mostrar estatísticas dos filtros
        st.sidebar.markdown("---")
        st.sidebar.metric("Registros encontrados", len(df_filtrado))
        st.sidebar.metric("Registros totais", len(df))
        
        # Área principal de resultados
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"📊 Resultados da Consulta ({len(df_filtrado)} registros)")
            
            # Selecionar colunas para exibição
            colunas_exibicao = st.multiselect(
                "Selecione as colunas para exibir:",
                options=df.columns.tolist(),
                default=df.columns.tolist()[:10] if len(df.columns) >= 10 else df.columns.tolist()
            )
            
            if colunas_exibicao:
                df_exibicao = df_filtrado[colunas_exibicao]
                st.dataframe(
                    df_exibicao,
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("Selecione pelo menos uma coluna para exibir.")
        
        with col2:
            st.subheader("📋 Resumo")
            
            # Estatísticas rápidas
            st.metric("Colunas na planilha", len(df.columns))
            st.metric("Filtros aplicados", len(filtros_aplicados))
            
            # Mostrar filtros ativos
            if filtros_aplicados:
                st.write("**Filtros ativos:**")
                for coluna, filtro in filtros_aplicados.items():
                    if isinstance(filtro, list):
                        st.write(f"• {coluna}: {', '.join(map(str, filtro))}")
                    else:
                        st.write(f"• {coluna}: {filtro[0]} a {filtro[1]}")
        
        # Seção de exportação
        st.markdown("---")
        st.subheader("📤 Exportar Resultados")
        
        col_export1, col_export2, col_export3 = st.columns(3)
        
        with col_export1:
            # Exportar para Excel
            if len(df_filtrado) > 0:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtrado.to_excel(writer, index=False, sheet_name='Dados_Filtrados')
                
                st.download_button(
                    label="📥 Baixar Excel",
                    data=output.getvalue(),
                    file_name=f"consulta_comunidades_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.ms-excel"
                )
        
        with col_export2:
            # Exportar para CSV
            if len(df_filtrado) > 0:
                csv_data = df_filtrado.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv_data,
                    file_name=f"consulta_comunidades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        
        with col_export3:
            # Gerar relatório PDF simples
            if len(df_filtrado) > 0:
                if st.button("📄 Gerar Relatório PDF"):
                    with st.spinner("Gerando PDF..."):
                        # Criar PDF simples
                        buffer = io.BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=letter)
                        elements = []
                        
                        # Estilos
                        styles = getSampleStyleSheet()
                        
                        # Título
                        title = Paragraph(f"Relatório de Consulta - Comunidades", styles['Title'])
                        elements.append(title)
                        
                        # Data e estatísticas
                        info_text = f"""
                        Data da consulta: {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>
                        Total de registros: {len(df_filtrado)}<br/>
                        Filtros aplicados: {len(filtros_aplicados)}<br/>
                        """
                        info = Paragraph(info_text, styles['Normal'])
                        elements.append(info)
                        
                        # Dados para a tabela (limitado para PDF)
                        dados_tabela = [df_filtrado.columns.tolist()] + df_filtrado.head(50).values.tolist()
                        
                        tabela = Table(dados_tabela)
                        tabela.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(tabela)
                        
                        doc.build(elements)
                        
                        st.download_button(
                            label="📥 Baixar PDF",
                            data=buffer.getvalue(),
                            file_name=f"relatorio_comunidades_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf"
                        )
        
        # Informações adicionais
        with st.expander("ℹ️ Informações da Planilha Original"):
            st.write(f"**Dimensões:** {len(df)} linhas × {len(df.columns)} colunas")
            st.write("**Colunas disponíveis:**")
            st.write(df.columns.tolist())
            
            st.write("**Amostra dos dados originais:**")
            st.dataframe(df.head(3))
    
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
        st.info("Verifique se o arquivo é um Excel válido e não está corrompido.")

else:
    st.info("👆 Por favor, envie um arquivo Excel para começar a consulta.")
    
    # Instruções de uso
    with st.expander("📖 Como usar esta ferramenta"):
        st.markdown("""
        1. **Envie sua planilha** Excel com os dados das comunidades
        2. **Selecione colunas para filtrar** na barra lateral
        3. **Aplique filtros** específicos para cada coluna:
           - Texto: selecione múltiplos valores
           - Números: use a faixa deslizante
        4. **Escolha as colunas para exibir** na tabela principal
        5. **Exporte os resultados** em Excel, CSV ou PDF
        
        **Dicas:**
        - Comece filtrando por comunidade para focar em áreas específicas
        - Use múltiplos filtros para refinamentos precisos
        - Selecione apenas as colunas relevantes para uma visualização mais limpa
        """)
