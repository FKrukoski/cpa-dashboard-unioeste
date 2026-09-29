# ==============================================================================
# UNIOESTE - COMISSÃO PRÓPRIA DE AVALIAÇÃO (CPA)
# DASHBOARD INTERATIVO DE AUTOAVALIAÇÃO INSTITUCIONAL (VERSÃO PYTHON / STREAMLIT)
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import io

from utils_dashboard import (
    calcular_metricas_rapidas,
    plot_likert_stacked_plotly,
    plot_cross_campi_benchmark,
    plot_heatmap_matriz_plotly,
    plot_participacao_pizza
)
from gerador_relatorio_pdf import gerar_pdf_plano_acao

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="UNIOESTE | CPA - Painel Interativo",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado para estilização corporativa institucional
st.markdown("""
<style>
    /* Estilos Gerais */
    .main {
        background-color: #F8F9FA;
    }
    .kpi-container {
        display: flex;
        flex-direction: row;
        gap: 15px;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #1B365D;
        flex: 1;
    }
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E293B;
        margin: 4px 0;
    }
    .kpi-subtitle {
        font-size: 0.8rem;
        color: #94A3B8;
    }
    .kpi-blue { border-left-color: #2166AC; }
    .kpi-green { border-left-color: #1B7837; }
    .kpi-orange { border-left-color: #D95F02; }
    .kpi-red { border-left-color: #B2182B; }
    
    /* Badges */
    .badge-desfavoravel {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-dissonancia {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    /* Estilo para abas principais */
    div[data-testid="stSegmentedControl"] {
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. CARREGAMENTO DOS DADOS COM CACHE
# ------------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

@st.cache_data
def carregar_dados():
    parquet_file = os.path.join(DATA_DIR, "base_respostas_longa_cpa.parquet")
    csv_file = os.path.join(DATA_DIR, "base_respostas_longa_cpa.csv")
    
    if os.path.exists(parquet_file):
        df_longa = pd.read_parquet(parquet_file)
    else:
        df_longa = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)
        
    paineis_exec = pd.read_csv(os.path.join(DATA_DIR, "paineis_executivos_campi.csv"), encoding='utf-8-sig')
    dissonancias = pd.read_csv(os.path.join(DATA_DIR, "dissonancias_executivas_campi.csv"), encoding='utf-8-sig')
    participacao = pd.read_csv(os.path.join(DATA_DIR, "participacao_campi.csv"), encoding='utf-8-sig')
    dicionario = pd.read_csv(os.path.join(DATA_DIR, "dicionario_perguntas_completo.csv"), encoding='utf-8-sig')
    vinculacao = pd.read_csv(os.path.join(DATA_DIR, "dicionario_vinculacao_topicos.csv"), encoding='utf-8-sig')
    
    with open(os.path.join(DATA_DIR, "mapa_eixos.json"), "r", encoding="utf-8") as f:
        mapa_eixos = json.load(f)
    with open(os.path.join(DATA_DIR, "mapa_dimensoes.json"), "r", encoding="utf-8") as f:
        mapa_dimensoes = json.load(f)
        
    return df_longa, paineis_exec, dissonancias, participacao, dicionario, vinculacao, mapa_eixos, mapa_dimensoes

df_longa, paineis_exec, dissonancias, participacao, dicionario, vinculacao, mapa_eixos, mapa_dimensoes = carregar_dados()

# ------------------------------------------------------------------------------
# 3. NAVEGAÇÃO SUPERIOR CONTROLADA (4 ABAS - PLANO DE AÇÃO OCULTO NA NAVEGAÇÃO)
# ------------------------------------------------------------------------------
opcoes_navegacao = [
    "🎯 Painel Executivo",
    "📊 Eixos & Dimensões",
    "🏛️ Benchmark Cross-Campi",
    "🌐 Visão Consolidada Macro"
]

aba_selecionada = st.segmented_control(
    "Navegação do Painel:",
    options=opcoes_navegacao,
    default=opcoes_navegacao[0],
    label_visibility="collapsed"
)
if not aba_selecionada:
    aba_selecionada = opcoes_navegacao[0]

# ------------------------------------------------------------------------------
# 4. SIDEBAR (FILTROS DE ANÁLISE PROGRESSIVOS E CONTEXTUAIS)
# ------------------------------------------------------------------------------
st.sidebar.title("🏛️ CPA | UNIOESTE")
st.sidebar.markdown("**Autoavaliação Institucional**")
st.sidebar.markdown("---")

# Filtro de Campus: contextualmente desativado no Benchmark (compara todos)
opcoes_campi = {
    "Todos os Campi (Consolidado)": "Todos",
    "Campus Cascavel": "Cascavel",
    "Campus Foz do Iguaçu": "Foz do Iguaçu",
    "Campus Francisco Beltrão": "Francisco Beltrão",
    "Campus Marechal Cândido Rondon": "Marechal",
    "Campus Toledo": "Toledo",
    "Reitoria": "Reitoria"
}

if "sel_campus_idx" not in st.session_state:
    st.session_state["sel_campus_idx"] = 0

if aba_selecionada == "🏛️ Benchmark Cross-Campi":
    st.sidebar.selectbox(
        "Campus / Unidade:",
        ["Todos os Campi (Comparativo Geral)"],
        index=0,
        disabled=True,
        help="Na aba Benchmark a comparação avalia todos os campi simultaneamente para a questão selecionada."
    )
    filtro_campus = "Todos"
    st.sidebar.info("ℹ️ **Filtro de Campus desativado:**\nA análise de Benchmark Cross-Campi compara automaticamente todos os campi da UNIOESTE.")
else:
    campus_keys = list(opcoes_campi.keys())
    sel_campus_label = st.sidebar.selectbox(
        "Campus / Unidade:",
        campus_keys,
        index=st.session_state["sel_campus_idx"]
    )
    st.session_state["sel_campus_idx"] = campus_keys.index(sel_campus_label)
    filtro_campus = opcoes_campi[sel_campus_label]

# Comportamento dos Filtros de Eixo e Dimensão por Aba
if aba_selecionada == "🎯 Painel Executivo":
    # Desativados no Painel Executivo com mensagem clara
    st.sidebar.selectbox("Eixo SINAES:", ["Todos os Eixos (Consolidado)"], disabled=True,
                        help="No Painel Executivo os indicadores avaliam a instituição de forma global.")
    st.sidebar.selectbox("Dimensão SINAES:", ["Todas as Dimensões"], disabled=True,
                        help="No Painel Executivo os indicadores avaliam a instituição de forma global.")
    st.sidebar.info("ℹ️ **Filtros de Eixo e Dimensão desativados:**\nO Painel Executivo apresenta o diagnóstico geral consolidado do campus selecionado. Para filtros temáticos detalhados, acesse a aba **📊 Eixos & Dimensões** ou **🌐 Visão Consolidada Macro**.")
    filtro_eixo = "Todos"
    filtro_dims = ["Todos"]

elif aba_selecionada == "📊 Eixos & Dimensões":
    st.sidebar.markdown("**Filtros Analíticos Progressivos:**")
    opcoes_eixos_prog = {"[Selecione um Eixo...]": "NENHUM"}
    opcoes_eixos_prog.update(mapa_eixos)
    
    sel_eixo_label = st.sidebar.selectbox(
        "1. Escolha o Eixo SINAES:",
        list(opcoes_eixos_prog.values()),
        index=0,
        help="Selecione um dos 6 Eixos institucionais para carregar as dimensões vinculadas."
    )
    filtro_eixo = [k for k, v in opcoes_eixos_prog.items() if v == sel_eixo_label][0]
    
    if filtro_eixo == "NENHUM":
        st.sidebar.selectbox("2. Escolha as Dimensões:", ["Aguardando seleção do Eixo..."], disabled=True)
        filtro_dims = []
    else:
        sub_dic = dicionario[dicionario['eixo_codigo'] == filtro_eixo]
        valid_dims = [d for d in sub_dic['dimensao_codigo'].dropna().unique() if d in mapa_dimensoes]
        mapa_dims_eixo = {d: mapa_dimensoes[d] for d in valid_dims}
        
        # Permitir agrupar duas ou mais dimensões do mesmo eixo
        agrupar_todas = st.sidebar.checkbox("Agrupar todas as dimensões deste Eixo", value=True)
        if agrupar_todas:
            filtro_dims = valid_dims
            st.sidebar.caption(f"✓ Todas as {len(valid_dims)} dimensões do {filtro_eixo} agrupadas.")
        else:
            sel_dims_labels = st.sidebar.multiselect(
                "2. Selecione as Dimensões desejadas:",
                options=list(mapa_dims_eixo.values()),
                default=list(mapa_dims_eixo.values()),
                help="Selecione uma, duas ou mais dimensões para combiná-las na análise."
            )
            filtro_dims = [k for k, v in mapa_dims_eixo.items() if v in sel_dims_labels]

elif aba_selecionada == "🌐 Visão Consolidada Macro":
    opcoes_eixos_macro = {"Todos os Eixos": "Todos"}
    opcoes_eixos_macro.update(mapa_eixos)
    sel_eixo_label = st.sidebar.selectbox("Filtrar por Eixo SINAES:", list(opcoes_eixos_macro.values()), index=0)
    filtro_eixo = [k for k, v in opcoes_eixos_macro.items() if v == sel_eixo_label][0]
    filtro_dims = ["Todos"]

else: # Benchmark Cross-Campi
    filtro_eixo = "Todos"
    filtro_dims = ["Todos"]

# Segmentos Respondentes
opcoes_segmentos = ["Discentes", "Docentes", "Agentes Universitários", "NEADUNI Discentes", "HUOP", "Público Externo"]
filtro_segmentos = st.sidebar.multiselect("Segmentos Respondentes:", opcoes_segmentos, default=opcoes_segmentos)

st.sidebar.markdown("---")
st.sidebar.markdown("**Parâmetros de Corte (%)**")
corte_forcas = st.sidebar.slider("Limiar de Forças (Favorável ≥):", min_value=50, max_value=95, value=75, step=5)
corte_melhorias = st.sidebar.slider("Limiar de Melhorias (Desfavorável ≥):", min_value=10, max_value=50, value=25, step=5)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size: 0.82rem; color: #64748B; text-align: center;">
    <p><b>Comissão Própria de Avaliação - CPA</b><br>
    UNIOESTE • Avaliação Institucional<br>
    3.230 Respondentes Catalogados</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 5. APLICAÇÃO DOS FILTROS NA BASE LONGA
# ------------------------------------------------------------------------------
df_filtrado = df_longa.copy()

if filtro_campus != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Campus'] == filtro_campus]

if filtro_eixo not in ["Todos", "NENHUM"]:
    df_filtrado = df_filtrado[df_filtrado['Eixo_Codigo'] == filtro_eixo]

if "Todos" not in filtro_dims and len(filtro_dims) > 0:
    df_filtrado = df_filtrado[df_filtrado['Dimensao_Codigo'].isin(filtro_dims)]

if filtro_segmentos:
    df_filtrado = df_filtrado[df_filtrado['Publico_Alvo'].isin(filtro_segmentos)]

# ------------------------------------------------------------------------------
# CONSTRUÇÃO DO DATAFRAME DE PLANO DE AÇÃO DO CAMPUS (UTILIZADO NO PAINEL EXECUTIVO)
# ------------------------------------------------------------------------------
def obter_dataframe_plano_acao(campus_atual, corte_melh):
    plano_rows = []
    
    # Oportunidades de melhoria acima do corte
    melh_crit = paineis_exec[(paineis_exec['Campus'] == campus_atual) & 
                            (paineis_exec['Tipo_Painel'] == 'Top_Melhorias') & 
                            (paineis_exec['Desfavorabilidade'] >= corte_melh)]
    
    for _, r in melh_crit.iterrows():
        eixo_c = str(r['Eixo_Codigo'])
        dim_c = str(r.get('Dimensao_Codigo', ''))
        if "E6" in eixo_c or "D11" in dim_c or "D5" in dim_c:
            setor = "Pró-Reitoria de Recursos Humanos (PRORH) / Gestão de Pessoas"
            recom = "Ações continuadas de valorização, clima organizacional, apoio psicossocial e desenvolvimento humano."
        elif "E5" in eixo_c or "D7" in dim_c:
            setor = "Prefeitura do Campus / Setor de Obras e Infraestrutura"
            recom = "Priorização de investimentos em infraestrutura física, conectividade e manutenção de equipamentos."
        elif "E3" in eixo_c or "D2" in dim_c or "D9" in dim_c:
            setor = "Pró-Reitorias Acadêmicas (PROGRAD / PRPPG / PROEX)"
            recom = "Fortalecimento das políticas acadêmicas, apoio pedagógico e canais de diálogo com discentes/docentes."
        elif "E4" in eixo_c or "D10" in dim_c:
            setor = "Reitoria / Pró-Reitoria de Planejamento (PROPLAN)"
            recom = "Revisão de processos de gestão, capacitação contínua e alocação orçamentária estratégica."
        elif "E1" in eixo_c or "D8" in dim_c:
            setor = "Comissão Própria de Avaliação (CPA) / Reitoria"
            recom = "Aprimorar a ampla divulgação das ações de autoavaliação institucional e comunicação interna."
        else:
            setor = "Reitoria / Colegiados Gestores"
            recom = "Diagnóstico setorial detalhado e alinhamento de metas no Plano de Desenvolvimento Institucional (PDI)."
            
        plano_rows.append({
            "ID_Topico": r['ID_Topico'],
            "Eixo": r['Eixo_Codigo'],
            "Descrição da Pergunta / Tópico": r['Texto_Pergunta'],
            "Indicadores": f"Desfav: {r['Desfavorabilidade']:.1f}% | Fav: {r['Favorabilidade']:.1f}% | Md: {r['Mediana']:.0f}",
            "Diagnóstico Crítico": "Alto Descontentamento",
            "Setor Responsável Sugerido": setor,
            "Recomendação Sugerida pela CPA": recom
        })
        
    # Dissonâncias críticas
    diss_crit = dissonancias[dissonancias['Campus'] == campus_atual].head(5)
    for _, r in diss_crit.iterrows():
        eixo_c = str(r['Eixo_Codigo'])
        if "E6" in eixo_c:
            setor = "Pró-Reitoria de Recursos Humanos (PRORH) / Gestão de Pessoas"
            recom = "Mediação de diálogo intergrupos e alinhamento de expectativas de trabalho e suporte."
        elif "E5" in eixo_c:
            setor = "Prefeitura do Campus / Infraestrutura"
            recom = "Vistorias setoriais para identificar divergências de condições físicas entre os segmentos."
        elif "E3" in eixo_c:
            setor = "PROGRAD / PRPPG e Colegiados de Curso"
            recom = "Fóruns de escuta com discentes e docentes para harmonização de práticas pedagógicas."
        else:
            setor = "Reitoria / Direções de Centro"
            recom = "Reuniões colegiadas para pactuação de entendimentos comuns."
            
        plano_rows.append({
            "ID_Topico": r['ID_Topico'],
            "Eixo": r['Eixo_Codigo'],
            "Descrição da Pergunta / Tópico": r['Texto_Pergunta'],
            "Indicadores": f"Δ Dissonância: {r['Deltadissonancia']:.1f}% ({r['Grupo_Mais_Favoravel']} vs {r['Grupo_Menos_Favoravel']})",
            "Diagnóstico Crítico": "Alta Dissonância Intergrupos",
            "Setor Responsável Sugerido": setor,
            "Recomendação Sugerida pela CPA": recom
        })
        
    df_res = pd.DataFrame(plano_rows)
    if len(df_res) > 0:
        df_res = df_res.drop_duplicates(subset=['ID_Topico'])
    return df_res

# ==============================================================================
# RENDERIZAÇÃO DA ABA 1: PAINEL EXECUTIVO
# ==============================================================================
if aba_selecionada == "🎯 Painel Executivo":
    # 4 KPI Cards Dinâmicos
    part_campus = participacao[participacao['Campus'] == filtro_campus]
    total_respondentes = int(part_campus['Total_Respondentes'].sum()) if len(part_campus) > 0 else 0
    
    # Métricas globais do campus
    df_campus_geral = df_longa[df_longa['Campus'] == filtro_campus] if filtro_campus != "Todos" else df_longa
    if len(df_campus_geral) > 0:
        nums_resp = pd.to_numeric(df_campus_geral['Resposta_Num'], errors='coerce')
        fav_media = round((nums_resp.isin([4, 5]).mean()) * 100, 1)
        neutro_media = round((nums_resp.isin([3]).mean()) * 100, 1)
        desfav_media = round((nums_resp.isin([1, 2]).mean()) * 100, 1)
    else:
        fav_media = 0.0
        neutro_media = 0.0
        desfav_media = 0.0
        
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.markdown(f"""
        <div class="kpi-card kpi-blue">
            <div class="kpi-title">Total Respondentes</div>
            <div class="kpi-value">{total_respondentes:,}</div>
            <div class="kpi-subtitle">Campus: {filtro_campus}</div>
        </div>
        """.replace(",", "."), unsafe_allow_html=True)
        
    with kpi_col2:
        st.markdown(f"""
        <div class="kpi-card kpi-green">
            <div class="kpi-title">Taxa de Favorabilidade</div>
            <div class="kpi-value">{fav_media}%</div>
            <div class="kpi-subtitle">Respostas favoráveis (P4 + P5)</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col3:
        st.markdown(f"""
        <div class="kpi-card kpi-orange">
            <div class="kpi-title">Índice de Neutralidade</div>
            <div class="kpi-value">{neutro_media}%</div>
            <div class="kpi-subtitle">Respostas neutras (P3)</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col4:
        st.markdown(f"""
        <div class="kpi-card kpi-red">
            <div class="kpi-title">Taxa de Desfavorabilidade</div>
            <div class="kpi-value">{desfav_media}%</div>
            <div class="kpi-subtitle">Respostas críticas (P1 + P2)</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Sub-abas do Painel Executivo
    subtab_forcas, subtab_melhorias, subtab_dissonancias, subtab_participacao = st.tabs([
        "👍 Top 10 Forças\nInstitucionais",
        "⚠️ Top 10 Oportunidades\nde Melhoria",
        "↔️ Principais\nDissonâncias",
        "🥧 Participação\npor Segmento"
    ])
    
    # Sub-aba 1: Top 10 Forças
    with subtab_forcas:
        st.caption("Questões com as maiores taxas de Favorabilidade (% Concordo Parcialmente + % Concordo Totalmente).")
        p_forcas = paineis_exec[(paineis_exec['Campus'] == filtro_campus) & 
                                (paineis_exec['Tipo_Painel'] == 'Top_Forcas') & 
                                (paineis_exec['Favorabilidade'] >= corte_forcas)].head(10)
        
        if len(p_forcas) == 0:
            st.info("Nenhuma questão atingiu o limiar de Força especificado.")
        else:
            p_forcas_plot = p_forcas.copy()
            p_forcas_plot["Rotulo_Item"] = "[" + p_forcas_plot["Eixo_Codigo"] + "] " + p_forcas_plot["Texto_Pergunta"]
            fig_forcas = plot_likert_stacked_plotly(
                p_forcas_plot,
                item_col="Rotulo_Item",
                title="Top 10 Forças Institucionais",
                subtitle=f"Campus: {filtro_campus} | Escopo: Consolidado Geral (Todos os Eixos) | Limiar: Favorabilidade ≥ {corte_forcas}%",
                height=max(480, len(p_forcas) * 62 + 100)
            )
            st.plotly_chart(fig_forcas, width='stretch')
            
            st.markdown("##### Detalhamento Quantitativo - Top 10 Forças Institucionais")
            t_forcas = p_forcas[['Eixo_Codigo', 'Texto_Pergunta', 'Favorabilidade', 'P4_ConcParc', 'P5_ConcTot', 'Mediana', 'IIQ']].copy()
            t_forcas.columns = ["Eixo", "Descrição da Pergunta", "Fav (%)", "P4 (%)", "P5 (%)", "Md", "IIQ"]
            st.dataframe(t_forcas, hide_index=True, width='stretch')
            
    # Sub-aba 2: Top 10 Melhorias + EXPORTAÇÃO DO PLANO DE AÇÃO
    with subtab_melhorias:
        st.caption("Itens com maiores taxas de Desfavorabilidade (% Discordo Totalmente + % Discordo Parcialmente).")
        p_melh = paineis_exec[(paineis_exec['Campus'] == filtro_campus) & 
                             (paineis_exec['Tipo_Painel'] == 'Top_Melhorias') & 
                             (paineis_exec['Desfavorabilidade'] >= corte_melhorias)].head(10)
        
        if len(p_melh) == 0:
            st.info("Nenhuma questão atingiu o limiar de Desfavorabilidade especificado.")
        else:
            p_melh_plot = p_melh.copy()
            p_melh_plot["Rotulo_Item"] = "[" + p_melh_plot["Eixo_Codigo"] + "] " + p_melh_plot["Texto_Pergunta"]
            fig_melh = plot_likert_stacked_plotly(
                p_melh_plot,
                item_col="Rotulo_Item",
                title="Top 10 Oportunidades de Melhoria",
                subtitle=f"Campus: {filtro_campus} | Escopo: Consolidado Geral (Todos os Eixos) | Limiar: Desfavorabilidade ≥ {corte_melhorias}%",
                height=max(480, len(p_melh) * 62 + 100)
            )
            st.plotly_chart(fig_melh, width='stretch')
            
            st.markdown("##### Detalhamento Quantitativo - Top 10 Oportunidades de Melhoria")
            t_melh = p_melh[['Eixo_Codigo', 'Texto_Pergunta', 'Desfavorabilidade', 'P1_DiscTot', 'P2_DiscParc', 'Mediana', 'IIQ']].copy()
            t_melh.columns = ["Eixo", "Descrição da Pergunta", "Desfav (%)", "P1 (%)", "P2 (%)", "Md", "IIQ"]
            st.dataframe(t_melh, hide_index=True, width='stretch')
            
        # ----------------------------------------------------------------------
        # SEÇÃO EXECUTIVA: EXPORTAÇÃO DO PLANO DE AÇÃO EM PDF, EXCEL E CSV
        # ----------------------------------------------------------------------
        st.markdown("---")
        st.markdown("### 📋 Encaminhamentos e Plano de Ação Institucional")
        st.markdown(f"Gere a matriz executiva contendo os pontos críticos de melhoria (Desfavorabilidade ≥ {corte_melhorias}%), diagnósticos, setores responsáveis sugeridos e recomendações da CPA para deliberação dos colegiados.")
        
        df_plano_campus = obter_dataframe_plano_acao(filtro_campus, corte_melhorias)
        
        if len(df_plano_campus) > 0:
            col_exp_pdf, col_exp_xlsx, col_exp_csv, _ = st.columns([1.8, 1.3, 1.3, 2])
            
            with col_exp_pdf:
                pdf_bytes = gerar_pdf_plano_acao(
                    df_plano_campus,
                    campus=filtro_campus,
                    corte_melhorias=corte_melhorias,
                    total_respondentes=total_respondentes
                )
                st.download_button(
                    label="📥 Baixar Plano de Ação em PDF",
                    data=pdf_bytes,
                    file_name=f"plano_de_acao_cpa_{filtro_campus}.pdf",
                    mime="application/pdf",
                    help="Gera relatório formal em PDF formatado para impressão e deliberação institucional."
                )
                
            with col_exp_xlsx:
                buffer_xlsx = io.BytesIO()
                with pd.ExcelWriter(buffer_xlsx, engine='openpyxl') as writer:
                    df_plano_campus.to_excel(writer, index=False, sheet_name="Plano_de_Acao")
                st.download_button(
                    label="📊 Exportar para Excel (.xlsx)",
                    data=buffer_xlsx.getvalue(),
                    file_name=f"plano_de_acao_cpa_{filtro_campus}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            with col_exp_csv:
                csv_bytes = df_plano_campus.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📄 Exportar para CSV",
                    data=csv_bytes,
                    file_name=f"plano_de_acao_cpa_{filtro_campus}.csv",
                    mime="text/csv"
                )
                
            with st.expander("👁️ Visualizar Matriz de Encaminhamentos na Tela", expanded=False):
                st.dataframe(
                    df_plano_campus[['Eixo', 'Descrição da Pergunta / Tópico', 'Indicadores', 'Diagnóstico Crítico', 'Setor Responsável Sugerido', 'Recomendação Sugerida pela CPA']],
                    hide_index=True,
                    width='stretch'
                )
        else:
            st.info("Nenhuma vulnerabilidade crítica atingiu o limiar de melhoria estipulado para compor o Plano de Ação.")
            
    # Sub-aba 3: Dissonâncias
    with subtab_dissonancias:
        st.caption("Tópicos com maior divergência percentual de opinião entre os diferentes segmentos de respondentes (Δ Dissonância).")
        p_diss = dissonancias[dissonancias['Campus'] == filtro_campus].head(10)
        if len(p_diss) == 0:
            st.info("Nenhuma dissonância mapeada para o campus.")
        else:
            t_diss = p_diss[['Texto_Pergunta', 'Deltadissonancia', 'Grupo_Mais_Favoravel', 'Grupo_Menos_Favoravel']].copy()
            t_diss.columns = ["Descrição da Pergunta", "Dissonância (Δ %)", "Segmento Mais Favorável", "Segmento Menos Favorável"]
            st.dataframe(t_diss, hide_index=True, width='stretch')
            
    # Sub-aba 4: Participação por Segmento
    with subtab_participacao:
        st.caption("Distribuição quantitativa e proporção de participação dos segmentos avaliados.")
        p_part = participacao[participacao['Campus'] == filtro_campus].copy()
        if len(p_part) == 0:
            st.info("Sem dados de participação para este campus.")
        else:
            fig_part = plot_participacao_pizza(
                p_part,
                title="Composição de Respondentes por Segmento",
                subtitle=f"Campus: {filtro_campus} | Total: {total_respondentes:,} Respondentes".replace(",", ".")
            )
            st.plotly_chart(fig_part, width='stretch')
            
            st.markdown("##### Tabela de Participação dos Respondentes por Segmento")
            t_part = p_part[['Questionario', 'Publico_Alvo', 'Total_Respondentes', 'Percentual_Participacao']].copy()
            t_part.columns = ["Cód.", "Público-Alvo", "Total Respondentes", "Participação (%)"]
            st.dataframe(t_part, hide_index=True, width='stretch')

# ==============================================================================
# RENDERIZAÇÃO DA ABA 2: EIXOS & DIMENSÕES (FILTROS PROGRESSIVOS & AGRUPAMENTO)
# ==============================================================================
elif aba_selecionada == "📊 Eixos & Dimensões":
    st.subheader("📊 Comparativo Analítico por Eixo & Dimensões")
    
    if filtro_eixo == "NENHUM":
        st.info(
            "### 👈 Como Visualizar esta Análise:\n\n"
            "1. Na barra lateral à esquerda, selecione o **Eixo SINAES** desejado (E1 a E6).\n"
            "2. Em seguida, escolha uma ou mais **Dimensões** vinculadas a esse eixo (você pode agrupar várias dimensões para comparar em conjunto).\n"
            "3. O sistema gerará a **Matriz de Calor por Segmento** e a **Distribuição 100% Likert** automaticamente!"
        )
    elif len(filtro_dims) == 0:
        st.warning("👈 Por favor, marque pelo menos uma dimensão na barra lateral para carregar os gráficos.")
    elif len(df_filtrado) == 0:
        st.info("Nenhuma resposta encontrada para a combinação de filtros selecionada.")
    else:
        nome_eixo_sel = mapa_eixos.get(filtro_eixo, filtro_eixo)
        dims_desc = [mapa_dimensoes.get(d, d) for d in filtro_dims]
        dims_texto = " e ".join(dims_desc) if len(dims_desc) <= 2 else f"{len(dims_desc)} Dimensões Agrupadas (" + ", ".join(filtro_dims) + ")"
        
        st.caption(f"Exibindo dados para o **{nome_eixo_sel}** com as dimensões: **{dims_texto}** no Campus: **{filtro_campus}**.")
        
        # 1. Heatmap por segmento
        st.markdown("##### Matriz de Calor de Favorabilidade por Segmento (Plotly Heatmap)")
        df_hm = df_filtrado.copy()
        df_hm['Is_Fav'] = df_hm['Resposta_Num'].isin([4, 5])
        
        agg_hm = df_hm.groupby(['ID_Topico', 'Texto_Resumido', 'Publico_Alvo'], observed=False)['Is_Fav'].agg(
            Fav=lambda x: round(x.mean() * 100, 1)
        ).reset_index()
        
        pivot_hm = agg_hm.pivot(index=['ID_Topico', 'Texto_Resumido'], columns='Publico_Alvo', values='Fav').reset_index()
        fig_heat = plot_heatmap_matriz_plotly(
            pivot_hm,
            title="Matriz de Favorabilidade por Segmento",
            subtitle=f"Campus: {filtro_campus} | Eixo: {nome_eixo_sel} | Dimensão: {dims_texto}"
        )
        st.plotly_chart(fig_heat, width='stretch')
        
        st.markdown("---")
        # 2. Gráfico Likert empilhado
        st.markdown("##### Distribuição Detalhada dos 5 Níveis Likert por Pergunta")
        st.caption("Detalhamento integral de Discordância Total (P1) a Concordância Total (P5). Metade da tela reservada para a leitura nítida das perguntas.")
        
        res_list = []
        for top_id, group in df_filtrado.groupby('ID_Topico', observed=False):
            if len(group) == 0: continue
            txt = group['Texto_Pergunta'].iloc[0]
            eixo_c = group['Eixo_Codigo'].iloc[0]
            dim_c = group['Dimensao_Codigo'].iloc[0]
            m = calcular_metricas_rapidas(group['Resposta_Num'])
            m['ID_Topico'] = top_id
            m['Eixo_Codigo'] = eixo_c
            m['Dimensao_Codigo'] = dim_c
            m['Texto_Pergunta'] = txt
            m['Rotulo_Item'] = f"[{eixo_c}] {txt}"
            res_list.append(m)
            
        df_likert_dim = pd.DataFrame(res_list)
        if len(df_likert_dim) > 0:
            df_likert_dim_renamed = df_likert_dim.rename(columns={
                'P1': 'P1_DiscTot', 'P2': 'P2_DiscParc', 'P3': 'P3_Neutro',
                'P4': 'P4_ConcParc', 'P5': 'P5_ConcTot'
            })
            fig_dim_bars = plot_likert_stacked_plotly(
                df_likert_dim_renamed,
                item_col="Rotulo_Item",
                title=f"Distribuição Likert nos 5 Níveis ({len(df_likert_dim)} Questões)",
                subtitle=f"Campus: {filtro_campus} | Eixo: {nome_eixo_sel} | Dimensão: {dims_texto}",
                height=max(480, len(df_likert_dim) * 62 + 100)
            )
            st.plotly_chart(fig_dim_bars, width='stretch')
            
            st.markdown("##### Tabela Quantitativa das Questões Selecionadas")
            t_dim = df_likert_dim[['Eixo_Codigo', 'Dimensao_Codigo', 'Texto_Pergunta', 'N',
                                   'P1', 'P2', 'P3', 'P4', 'P5', 'Favorabilidade',
                                   'Desfavorabilidade', 'Mediana', 'IIQ']].copy()
            t_dim.columns = ["Eixo", "Dim.", "Descrição da Pergunta", "N", "P1 (%)", "P2 (%)", "P3 (%)", "P4 (%)", "P5 (%)", "Fav (%)", "Desfav (%)", "Md", "IIQ"]
            st.dataframe(t_dim, hide_index=True, width='stretch')

# ==============================================================================
# RENDERIZAÇÃO DA ABA 3: BENCHMARK CROSS-CAMPI
# ==============================================================================
elif aba_selecionada == "🏛️ Benchmark Cross-Campi":
    st.subheader("🏛️ Comparativo Cross-Campi para a Mesma Pergunta")
    
    # Lista de tópicos com perguntas likert (sem truncamento de texto)
    topicos_likert = vinculacao[vinculacao['tipo_pergunta'] == 'Likert'].copy()
    topicos_likert['label'] = "[" + topicos_likert['id_topico'] + "] (" + topicos_likert['eixo_codigo'] + ") " + topicos_likert['texto_pergunta']
    dict_topicos = dict(zip(topicos_likert['label'], topicos_likert['id_topico']))
    
    col_sel_p, col_modo = st.columns([3, 1])
    with col_sel_p:
        sel_p_label = st.selectbox(
            "Selecione uma pergunta ou digite parte da pergunta para buscar:",
            list(dict_topicos.keys()),
            index=0,
            help="💡 Dica: Clique na caixa e digite qualquer palavra-chave (ex: 'laboratórios', 'saúde', 'assédio', 'biblioteca') para filtrar instantaneamente."
        )
        top_id_sel = dict_topicos[sel_p_label]
        
    with col_modo:
        modo_cross = st.radio("Modo de Visualização:", ["Barras Empilhadas (5 Níveis)", "Barras Agrupadas (Fav x Desfav)"], index=0)
        modo_param = "empilhado" if modo_cross.startswith("Barras Empilhadas") else "lado_a_lado"
        
    df_p = df_longa[df_longa['ID_Topico'] == top_id_sel]
    if len(df_p) == 0:
        st.info("Pergunta sem dados na base catalogada.")
    else:
        campi_nomes = ["Cascavel", "Foz do Iguaçu", "Francisco Beltrão", "Marechal", "Toledo", "Reitoria"]
        res_campi = []
        for cmp in campi_nomes:
            sub_c = df_p[df_p['Campus'] == cmp]
            if len(sub_c) > 0:
                m = calcular_metricas_rapidas(sub_c['Resposta_Num'])
                res_campi.append({
                    "Campus": cmp,
                    "N": m["N"],
                    "P1_DiscTot": m["P1"],
                    "P2_DiscParc": m["P2"],
                    "P3_Neutro": m["P3"],
                    "P4_ConcParc": m["P4"],
                    "P5_ConcTot": m["P5"],
                    "Favorabilidade": m["Favorabilidade"],
                    "Desfavorabilidade": m["Desfavorabilidade"],
                    "Mediana": m["Mediana"],
                    "IIQ": m["IIQ"]
                })
        # Adicionar UNIOESTE (Geral)
        m_geral = calcular_metricas_rapidas(df_p['Resposta_Num'])
        res_campi.append({
            "Campus": "UNIOESTE (Geral)",
            "N": m_geral["N"],
            "P1_DiscTot": m_geral["P1"],
            "P2_DiscParc": m_geral["P2"],
            "P3_Neutro": m_geral["P3"],
            "P4_ConcParc": m_geral["P4"],
            "P5_ConcTot": m_geral["P5"],
            "Favorabilidade": m_geral["Favorabilidade"],
            "Desfavorabilidade": m_geral["Desfavorabilidade"],
            "Mediana": m_geral["Mediana"],
            "IIQ": m_geral["IIQ"]
        })
        
        df_bench = pd.DataFrame(res_campi)
        
        top_info = topicos_likert[topicos_likert['id_topico'] == top_id_sel].iloc[0]
        txt_completo = top_info['texto_pergunta']
        eixo_bench_str = f"{top_info['eixo_codigo']} - {top_info['eixo_nome']}" if 'eixo_nome' in top_info and pd.notna(top_info['eixo_nome']) else str(top_info['eixo_codigo'])
        dim_bench_str = f"{top_info['dimensao_codigo']} - {top_info['dimensao_nome']}" if 'dimensao_nome' in top_info and pd.notna(top_info['dimensao_nome']) else str(top_info['dimensao_codigo'])
        
        st.markdown(f"**Pergunta Selecionada:** *{txt_completo}*")
        
        fig_cross = plot_cross_campi_benchmark(
            df_bench,
            modo=modo_param,
            title="Comparativo Cross-Campi para a Pergunta Selecionada",
            subtitle=f"Escopo: Comparativo Geral (Todos os Campi) | Eixo: {eixo_bench_str} | Dimensão: {dim_bench_str}"
        )
        st.plotly_chart(fig_cross, width='stretch')
        
        st.markdown("##### Tabela Comparativa de Indicadores por Campus")
        t_bench = df_bench.copy()
        
        # Exibição com larguras de colunas estreitas e compactas
        st.dataframe(
            t_bench,
            hide_index=True,
            width='stretch',
            column_config={
                "Campus": st.column_config.TextColumn("Campus / Unidade", width="medium"),
                "N": st.column_config.NumberColumn("N", width="small"),
                "P1_DiscTot": st.column_config.NumberColumn("P1 (%)", width="small", format="%.1f%%"),
                "P2_DiscParc": st.column_config.NumberColumn("P2 (%)", width="small", format="%.1f%%"),
                "P3_Neutro": st.column_config.NumberColumn("P3 (%)", width="small", format="%.1f%%"),
                "P4_ConcParc": st.column_config.NumberColumn("P4 (%)", width="small", format="%.1f%%"),
                "P5_ConcTot": st.column_config.NumberColumn("P5 (%)", width="small", format="%.1f%%"),
                "Favorabilidade": st.column_config.NumberColumn("Fav (%)", width="small", format="%.1f%%"),
                "Desfavorabilidade": st.column_config.NumberColumn("Desfav (%)", width="small", format="%.1f%%"),
                "Mediana": st.column_config.NumberColumn("Md", width="small", format="%.1f"),
                "IIQ": st.column_config.NumberColumn("IIQ", width="small", format="%.1f"),
            }
        )

# ==============================================================================
# RENDERIZAÇÃO DA ABA 4: VISÃO CONSOLIDADA MACRO (INSTRUÇÕES E SLIDER DINÂMICO)
# ==============================================================================
elif aba_selecionada == "🌐 Visão Consolidada Macro":
    st.subheader("🌐 Visão Consolidada Macro das Questões")
    
    # Painel com instruções claras de uso
    st.info(
        "💡 **Instruções de Análise e Navegação:**\n\n"
        "- **Filtros Laterais:** Utilize o seletor de **Campus** e o filtro de **Eixo** na barra lateral para definir o escopo da consulta.\n"
        "- **Critério de Ordenação:**\n"
        "  - *Maior Favorabilidade:* destaca as melhores fortalezas institucionais avaliadas.\n"
        "  - *Maior Descontentamento:* evidencia com prioridade os alertas de vulnerabilidade.\n"
        "  - *Ordem Oficial SINAES:* organiza os temas na sequência regulatória de Eixos e Dimensões.\n"
        "- **Controle de Questões:** O controle deslizante abaixo ajusta-se automaticamente à quantidade real de itens disponíveis no filtro atual."
    )
    
    if len(df_filtrado) == 0:
        st.warning("Sem dados disponíveis para os filtros atuais.")
    else:
        res_macro = []
        for top_id, group in df_filtrado.groupby('ID_Topico', observed=False):
            if len(group) == 0: continue
            m = calcular_metricas_rapidas(group['Resposta_Num'])
            res_macro.append({
                "ID_Topico": top_id,
                "Eixo_Codigo": group['Eixo_Codigo'].iloc[0],
                "Dimensao_Codigo": group['Dimensao_Codigo'].iloc[0],
                "Texto_Pergunta": group['Texto_Pergunta'].iloc[0],
                "Texto_Resumido": group['Texto_Resumido'].iloc[0],
                "N": m["N"],
                "P1_DiscTot": m["P1"],
                "P2_DiscParc": m["P2"],
                "P3_Neutro": m["P3"],
                "P4_ConcParc": m["P4"],
                "P5_ConcTot": m["P5"],
                "Favorabilidade": m["Favorabilidade"],
                "Desfavorabilidade": m["Desfavorabilidade"],
                "Mediana": m["Mediana"],
                "IIQ": m["IIQ"]
            })
            
        df_all_macro = pd.DataFrame(res_macro)
        total_questoes_disp = len(df_all_macro)
        
        # Ajustar dinamicamente o slider conforme o total real de questões
        max_slider_val = max(5, min(total_questoes_disp, 50))
        default_val = min(20, max_slider_val)
        step_val = 5 if max_slider_val >= 10 else 1
        
        col_ord, col_tg, col_topn = st.columns(3)
        with col_ord:
            sel_ord = st.selectbox("Ordenar Questões por:", [
                "Maior Favorabilidade",
                "Maior Descontentamento",
                "Ordem Oficial SINAES (Eixo/Dimensão)"
            ], index=0)
        with col_tg:
            sel_tg = st.radio("Tipo de Gráfico:", ["Barras Empilhadas (5 Níveis)", "Matriz Heatmap Geral"], index=0)
        with col_topn:
            top_n = st.slider(
                "Quantidade de Questões para Exibir:",
                min_value=min(5, total_questoes_disp),
                max_value=max_slider_val,
                value=default_val,
                step=step_val,
                help=f"Total de questões disponíveis para o filtro atual: {total_questoes_disp}."
            )
            st.caption(f"Exibindo as **{top_n}** principais questões (de um total de **{total_questoes_disp}** disponíveis).")
            
        if sel_ord == "Maior Favorabilidade":
            df_all_macro = df_all_macro.sort_values(by="Favorabilidade", ascending=False)
        elif sel_ord == "Maior Descontentamento":
            df_all_macro = df_all_macro.sort_values(by="Desfavorabilidade", ascending=False)
        else:
            df_all_macro = df_all_macro.sort_values(by=["Eixo_Codigo", "Dimensao_Codigo"])
            
        df_all_macro_plot = df_all_macro.head(top_n).copy()
        df_all_macro_plot["Rotulo_Item"] = "[" + df_all_macro_plot["Eixo_Codigo"] + "] " + df_all_macro_plot["Texto_Pergunta"]
        
        nome_eixo_macro = mapa_eixos.get(filtro_eixo, "Todos os Eixos SINAES") if filtro_eixo != "Todos" else "Todos os Eixos (Consolidado Geral)"
        
        if sel_tg.startswith("Barras Empilhadas"):
            fig_macro = plot_likert_stacked_plotly(
                df_all_macro_plot,
                item_col="Rotulo_Item",
                title=f"Visão Consolidada Macro (Top {top_n} de {total_questoes_disp} Questões)",
                subtitle=f"Campus: {filtro_campus} | Eixo: {nome_eixo_macro} | Dimensões: Todas | Ordenação: {sel_ord}",
                height=max(480, len(df_all_macro_plot) * 62 + 100)
            )
            st.plotly_chart(fig_macro, width='stretch')
        else:
            df_matriz_macro = df_all_macro_plot[['ID_Topico', 'Texto_Resumido', 'P1_DiscTot', 'P2_DiscParc', 'P3_Neutro', 'P4_ConcParc', 'P5_ConcTot']].copy()
            df_matriz_macro.columns = ["ID_Topico", "Texto_Resumido", "P1 (Disc. Tot)", "P2 (Disc. Parc)", "P3 (Neutro)", "P4 (Conc. Parc)", "P5 (Conc. Tot)"]
            fig_hm_macro = plot_heatmap_matriz_plotly(
                df_matriz_macro,
                title=f"Matriz de Frequências nos 5 Níveis Likert (Top {top_n} Questões)",
                subtitle=f"Campus: {filtro_campus} | Eixo: {nome_eixo_macro} | Dimensões: Todas | Ordenação: {sel_ord}",
                height=max(480, len(df_all_macro_plot) * 48 + 100)
            )
            st.plotly_chart(fig_hm_macro, width='stretch')
