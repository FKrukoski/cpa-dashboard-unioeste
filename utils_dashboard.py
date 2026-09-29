"""
UNIOESTE - CPA - Funções Utilitárias e Visualizações Gráficas do Dashboard em Python
Mapeamento fiel das funções do R Shiny para Streamlit + Plotly.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import textwrap

# ==============================================================================
# 1. PALETAS OFICIAIS DE CORES
# ==============================================================================
PALETA_LIKERT_5 = {
    "P1_DiscTot":  "#B2182B",  # Vermelho Escuro (Nível 1)
    "P2_DiscParc": "#F4A582",  # Laranja/Salmão (Nível 2)
    "P3_Neutro":   "#DFDFDF",  # Cinza Neutro (Nível 3)
    "P4_ConcParc": "#92C5DE",  # Azul Claro (Nível 4)
    "P5_ConcTot":  "#2166AC"   # Azul Escuro (Nível 5)
}

NOMES_LIKERT_5 = {
    "P1_DiscTot":  "1 - Discordo Totalmente",
    "P2_DiscParc": "2 - Discordo Parcialmente",
    "P3_Neutro":   "3 - Neutro",
    "P4_ConcParc": "4 - Concordo Parcialmente",
    "P5_ConcTot":  "5 - Concordo Totalmente"
}

PALETA_CAMPI_MAP = {
    "Todos":                   "#1B365D",
    "Cascavel":                "#2166AC",
    "Foz do Iguaçu":           "#4393C3",
    "Francisco Beltrão":       "#1B7837",
    "Marechal":                "#D95F02",
    "Toledo":                  "#762A83",
    "Reitoria":                "#35978F",
    "UNIOESTE (Geral)":        "#1B365D"
}

# ==============================================================================
# 2. CÁLCULO RÁPIDO DE MÉTRICAS LIKERT
# ==============================================================================
def calcular_metricas_rapidas(series):
    """
    Calcula N, P1-P5 percentuais, Favorabilidade (P4+P5), Desfavorabilidade (P1+P2),
    Mediana e Intervalo Interquartílico (IIQ).
    """
    nums = pd.to_numeric(series, errors='coerce').dropna()
    nums = nums[(nums >= 1) & (nums <= 5)]
    n = len(nums)
    if n == 0:
        return {
            "N": 0, "P1": 0.0, "P2": 0.0, "P3": 0.0, "P4": 0.0, "P5": 0.0,
            "Favorabilidade": 0.0, "Desfavorabilidade": 0.0, "Mediana": np.nan, "IIQ": np.nan
        }
    
    counts = nums.value_counts()
    p1 = round((counts.get(1, 0) / n) * 100, 1)
    p2 = round((counts.get(2, 0) / n) * 100, 1)
    p3 = round((counts.get(3, 0) / n) * 100, 1)
    p4 = round((counts.get(4, 0) / n) * 100, 1)
    p5 = round((counts.get(5, 0) / n) * 100, 1)
    
    q25 = float(np.percentile(nums, 25))
    q75 = float(np.percentile(nums, 75))
    iiq = round(q75 - q25, 1)
    
    return {
        "N": n,
        "P1": p1,
        "P2": p2,
        "P3": p3,
        "P4": p4,
        "P5": p5,
        "Favorabilidade": round(p4 + p5, 1),
        "Desfavorabilidade": round(p1 + p2, 1),
        "Mediana": float(np.median(nums)),
        "IIQ": iiq
    }

# ==============================================================================
# 3. GRÁFICO PLOTLY: BARRAS EMPILHADAS 100% LIKERT COM EIXO X TRAVADO
# ==============================================================================
def plot_likert_stacked_plotly(df, item_col="Rotulo_Item", title="", subtitle="", height=None, domain_x=None):
    """
    Gera gráfico de barras horizontais 100% empilhadas na escala Likert 5 níveis.
    Configura domain_x=[0.46, 1.0] para que a coluna de texto da questão ocupe
    a metade esquerda da tela.
    Utiliza anotações alinhadas à esquerda (xanchor='left', align='left') com fonte 12px
    para aproveitar todo o espaço destinado sem deixar vazio à esquerda e sem agrupamento à direita.
    Configura fixedrange=True no eixo X para manter largura fixa durante o scroll/zoom vertical.
    Título centralizado horizontalmente no topo.
    """
    if df is None or len(df) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum dado disponível para os filtros selecionados.",
                           showarrow=False, font=dict(size=14, color="#64748B"),
                           x=0.5, y=0.5, xref="paper", yref="paper")
        fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig
    
    df_plot = df.copy()
    is_campus = (item_col == "Campus_Label")
    
    if domain_x is None:
        domain_x = [0.25, 1.0] if is_campus else [0.46, 1.0]
    
    # Quebrar rótulos: 78 caracteres para perguntas (aproveita todo o espaço esquerdo)
    wrap_width = 35 if is_campus else 78
    def wrap_text(txt):
        if pd.isna(txt) or not str(txt).strip():
            return ""
        return "<br>".join(textwrap.wrap(str(txt), width=wrap_width))
    
    df_plot["Item_Formatado"] = df_plot[item_col].apply(wrap_text)
    
    # Ordenar por favorabilidade se disponível
    if "Favorabilidade" in df_plot.columns:
        df_plot = df_plot.sort_values(by="Favorabilidade", ascending=True)
    
    n_itens = len(df_plot)
    # Altura dinâmica generosa: 62px por item para acomodar enunciados de 2 a 3 linhas confortavelmente
    calc_height = height if height is not None else max(480, n_itens * 62 + 130)
    
    fig = go.Figure()
    y_values = df_plot["Item_Formatado"].tolist()
    
    # P1 - Discordo Totalmente
    fig.add_trace(go.Bar(
        y=y_values,
        x=df_plot["P1_DiscTot"],
        name="1 - Disc. Total",
        orientation="h",
        marker=dict(color=PALETA_LIKERT_5["P1_DiscTot"]),
        hovertemplate="<b>%{y}</b><br>1 - Discordo Totalmente: %{x:.1f}%<extra></extra>"
    ))
    
    # P2 - Discordo Parcialmente
    fig.add_trace(go.Bar(
        y=y_values,
        x=df_plot["P2_DiscParc"],
        name="2 - Disc. Parcial",
        orientation="h",
        marker=dict(color=PALETA_LIKERT_5["P2_DiscParc"]),
        hovertemplate="<b>%{y}</b><br>2 - Discordo Parcialmente: %{x:.1f}%<extra></extra>"
    ))
    
    # P3 - Neutro
    fig.add_trace(go.Bar(
        y=y_values,
        x=df_plot["P3_Neutro"],
        name="3 - Neutro",
        orientation="h",
        marker=dict(color=PALETA_LIKERT_5["P3_Neutro"]),
        hovertemplate="<b>%{y}</b><br>3 - Neutro: %{x:.1f}%<extra></extra>"
    ))
    
    # P4 - Concordo Parcialmente
    fig.add_trace(go.Bar(
        y=y_values,
        x=df_plot["P4_ConcParc"],
        name="4 - Conc. Parcial",
        orientation="h",
        marker=dict(color=PALETA_LIKERT_5["P4_ConcParc"]),
        hovertemplate="<b>%{y}</b><br>4 - Concordo Parcialmente: %{x:.1f}%<extra></extra>"
    ))
    
    # P5 - Concordo Totalmente
    fig.add_trace(go.Bar(
        y=y_values,
        x=df_plot["P5_ConcTot"],
        name="5 - Conc. Total",
        orientation="h",
        marker=dict(color=PALETA_LIKERT_5["P5_ConcTot"]),
        hovertemplate="<b>%{y}</b><br>5 - Concordo Totalmente: %{x:.1f}%<extra></extra>"
    ))
    
    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size: 11.5px; color: #64748B; font-weight: normal;'>{subtitle}</span>"
        
    layout_args = dict(
        barmode='stack',
        title=dict(
            text=title_text,
            font=dict(size=15, color="#1B365D"),
            x=0.5,
            xanchor="center"
        ),
        xaxis=dict(
            title="Distribuição Percentual (%)",
            ticksuffix="%",
            range=[0, 100],
            domain=domain_x,
            fixedrange=True,
            showgrid=True,
            gridcolor="#E2E8F0"
        ),
        legend=dict(
            orientation="h",
            x=domain_x[0],
            y=-0.12,
            font=dict(size=11)
        ),
        margin=dict(l=15, r=20, t=75, b=65),
        hoverlabel=dict(bgcolor="#FFFFFF", font=dict(size=12)),
        height=calc_height,
        template="plotly_white"
    )
    
    if is_campus:
        layout_args["yaxis"] = dict(
            title="",
            automargin=True,
            tickfont=dict(size=12),
            fixedrange=False
        )
        fig.update_layout(**layout_args)
    else:
        # Quando são enunciados de questões: oculta ticks e usa anotações alinhadas à esquerda
        layout_args["yaxis"] = dict(
            title="",
            showticklabels=False,
            fixedrange=False
        )
        fig.update_layout(**layout_args)
        
        for val_y in y_values:
            fig.add_annotation(
                xref="paper",
                yref="y",
                x=0.005,
                y=val_y,
                text=val_y,
                showarrow=False,
                xanchor="left",
                yanchor="middle",
                align="left",
                font=dict(size=12, color="#1E293B")
            )
            
    return fig

# ==============================================================================
# 4. GRÁFICO PLOTLY: COMPARATIVO CROSS-CAMPI (BENCHMARK)
# ==============================================================================
def plot_cross_campi_benchmark(df_campi, modo="empilhado", title="", subtitle=""):
    """
    Visualização comparativa por campus para uma pergunta selecionada.
    """
    if df_campi is None or len(df_campi) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Pergunta não avaliada nos campi selecionados.",
                           showarrow=False, font=dict(size=14, color="#64748B"),
                           x=0.5, y=0.5, xref="paper", yref="paper")
        fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig
    
    df_plot = df_campi.copy()
    df_plot["Campus_Label"] = "<b>" + df_plot["Campus"].astype(str) + "</b> (N=" + df_plot["N"].astype(str) + ")"
    
    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size: 11.5px; color: #64748B; font-weight: normal;'>{subtitle}</span>"
        
    if modo == "lado_a_lado":
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_plot["Campus"],
            y=df_plot["Favorabilidade"],
            name="Favorável (P4+P5)",
            marker=dict(color="#2166AC"),
            customdata=df_plot["N"],
            hovertemplate="<b>%{x}</b><br>Favorabilidade: %{y:.1f}% (N=%{customdata})<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            x=df_plot["Campus"],
            y=df_plot["P3_Neutro"],
            name="Neutro (P3)",
            marker=dict(color="#DFDFDF"),
            hovertemplate="<b>%{x}</b><br>Neutro: %{y:.1f}%<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            x=df_plot["Campus"],
            y=df_plot["Desfavorabilidade"],
            name="Desfavorável (P1+P2)",
            marker=dict(color="#B2182B"),
            hovertemplate="<b>%{x}</b><br>Desfavorabilidade: %{y:.1f}%<extra></extra>"
        ))
        
        fig.update_layout(
            barmode='group',
            title=dict(
                text=title_text,
                font=dict(size=15, color="#1B365D"),
                x=0.5,
                xanchor="center"
            ),
            xaxis=dict(title="Campus / Unidade", fixedrange=True, tickfont=dict(size=12)),
            yaxis=dict(title="Percentual (%)", ticksuffix="%", range=[0, 100], fixedrange=True, gridcolor="#E2E8F0"),
            legend=dict(orientation="h", x=0.2, y=-0.15, font=dict(size=11)),
            margin=dict(l=20, r=20, t=75, b=65),
            height=460,
            template="plotly_white"
        )
        return fig
    else:
        return plot_likert_stacked_plotly(
            df_plot,
            item_col="Campus_Label",
            title=title,
            subtitle=subtitle,
            height=440
        )

# ==============================================================================
# 5. GRÁFICO PLOTLY: MATRIZ DE CALOR (HEATMAP)
# ==============================================================================
def plot_heatmap_matriz_plotly(df_matriz, title="", subtitle="", height=None):
    """
    Heatmap de favorabilidade por segmento respondente.
    Utiliza anotações alinhadas à esquerda para aproveitar todo o espaço à esquerda.
    """
    if df_matriz is None or len(df_matriz) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados para o Eixo/Dimensão selecionado.",
                           showarrow=False, font=dict(size=14, color="#64748B"),
                           x=0.5, y=0.5, xref="paper", yref="paper")
        fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig
    
    df_plot = df_matriz.copy()
    ignored_cols = {"ID_Topico", "Texto_Resumido", "Texto_Pergunta", "Eixo_Codigo", "Dimensao_Codigo", "Mediana", "IIQ"}
    col_grupos = [c for c in df_plot.columns if c not in ignored_cols]
    
    wrap_width = 72
    def wrap_text(txt):
        if pd.isna(txt) or not str(txt).strip():
            return ""
        return "<br>".join(textwrap.wrap(str(txt), width=wrap_width))
    
    y_labels = df_plot["Texto_Resumido"].apply(wrap_text).tolist()
    z_matrix = df_plot[col_grupos].values
    
    colorscale_custom = [
        [0.0, "#B2182B"],
        [0.35, "#F4A582"],
        [0.5, "#F7F7F7"],
        [0.75, "#92C5DE"],
        [1.0, "#2166AC"]
    ]
    
    calc_height = height if height is not None else max(480, len(df_plot) * 48 + 140)
    
    fig = go.Figure(data=go.Heatmap(
        x=col_grupos,
        y=y_labels,
        z=z_matrix,
        colorscale=colorscale_custom,
        zmin=0,
        zmax=100,
        colorbar=dict(title="Favorabilidade (%)", ticksuffix="%"),
        hovertemplate="<b>Tópico:</b> %{y}<br><b>Segmento:</b> %{x}<br><b>Favorabilidade:</b> %{z:.1f}%<extra></extra>"
    ))
    
    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size: 11.5px; color: #64748B; font-weight: normal;'>{subtitle}</span>"
        
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=15, color="#1B365D"),
            x=0.5,
            xanchor="center"
        ),
        xaxis=dict(title="", side="top", domain=[0.46, 1.0], fixedrange=True),
        yaxis=dict(title="", autorange="reversed", showticklabels=False, fixedrange=False),
        margin=dict(l=15, r=25, t=95, b=45),
        height=calc_height,
        template="plotly_white"
    )
    
    for y_item in y_labels:
        fig.add_annotation(
            xref="paper",
            yref="y",
            x=0.005,
            y=y_item,
            text=y_item,
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            align="left",
            font=dict(size=12, color="#1E293B")
        )
    
    return fig

# ==============================================================================
# 6. GRÁFICO PLOTLY: PARTICIPAÇÃO POR SEGMENTO (DONUT/PIE)
# ==============================================================================
def plot_participacao_pizza(df_part, title="Composição de Respondentes por Segmento", subtitle=""):
    """
    Gráfico de pizza/donut de distribuição de respondentes por segmento com título centralizado.
    """
    if df_part is None or len(df_part) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados de participação disponíveis.",
                           showarrow=False, font=dict(size=14, color="#64748B"),
                           x=0.5, y=0.5, xref="paper", yref="paper")
        fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig
    
    colors = ["#2166AC", "#4393C3", "#92C5DE", "#D95F02", "#1B7837", "#762A83"]
    
    fig = go.Figure(data=[go.Pie(
        labels=df_part["Publico_Alvo"],
        values=df_part["Total_Respondentes"],
        hole=0.4,
        textposition="inside",
        textinfo="label+percent",
        insidetextfont=dict(color="#FFFFFF", size=12),
        marker=dict(colors=colors),
        hovertemplate="<b>%{label}</b><br>Total Respondentes: %{value}<br>Proporção: %{percent}<extra></extra>"
    )])
    
    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size: 11.5px; color: #64748B; font-weight: normal;'>{subtitle}</span>"
        
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=15, color="#1B365D"),
            x=0.5,
            xanchor="center"
        ),
        showlegend=True,
        legend=dict(orientation="h", x=0, y=-0.15, font=dict(size=11)),
        margin=dict(l=20, r=20, t=65, b=50),
        height=400,
        template="plotly_white"
    )
    return fig
