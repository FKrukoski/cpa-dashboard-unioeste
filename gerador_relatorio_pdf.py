"""
Módulo de Geração de Relatório em PDF do Plano de Ação Institucional - CPA / UNIOESTE
Utiliza ReportLab para compilar um documento limpo, profissional e pronto para deliberação.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def gerar_pdf_plano_acao(df_plano, campus="Todos", corte_melhorias=25, total_respondentes=0):
    """
    Gera um documento PDF em formato paisagem (A4) contendo o Plano de Ação
    e Encaminhamentos Estratégicos da CPA para o campus selecionado.
    
    Retorna: bytes do arquivo PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=30,
        rightMargin=30,
        topMargin=25,
        bottomMargin=25
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    style_header_univ = ParagraphStyle(
        'UnivHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.HexColor('#1B365D'),
        alignment=TA_CENTER
    )
    
    style_header_sub = ParagraphStyle(
        'CpaHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#2166AC'),
        alignment=TA_CENTER
    )
    
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        alignment=TA_CENTER
    )
    
    style_meta = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#475569')
    )
    
    style_cell = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1E293B')
    )
    
    style_cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1B365D')
    )
    
    style_th = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.whitesmoke,
        alignment=TA_LEFT
    )
    
    elements = []
    
    # 1. Cabeçalho Institucional
    elements.append(Paragraph("UNIVERSIDADE ESTADUAL DO OESTE DO PARANÁ – UNIOESTE", style_header_univ))
    elements.append(Paragraph("COMISSÃO PRÓPRIA DE AVALIAÇÃO – CPA | AUTOAVALIAÇÃO INSTITUCIONAL", style_header_sub))
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1B365D'), spaceBefore=2, spaceAfter=8))
    
    # 2. Título do Documento
    campus_nome = f"Campus {campus}" if campus not in ["Todos", "Reitoria"] else ("Todos os Campi (Consolidado)" if campus == "Todos" else campus)
    elements.append(Paragraph(f"MATRIZ ESTRATÉGICA DE PLANO DE AÇÃO E ENCAMINHAMENTOS – {campus_nome.upper()}", style_title))
    elements.append(Spacer(1, 6))
    
    # 3. Metadados e Parâmetros
    data_emissao = datetime.now().strftime("%d/%m/%Y às %H:%M")
    txt_meta = f"<b>Data de Emissão:</b> {data_emissao} &nbsp;|&nbsp; <b>Campus de Análise:</b> {campus_nome} &nbsp;|&nbsp; <b>Respondentes no Campus:</b> {total_respondentes:,} &nbsp;|&nbsp; <b>Critério de Melhoria:</b> Desfavorabilidade ≥ {corte_melhorias}%".replace(",", ".")
    elements.append(Paragraph(txt_meta, style_meta))
    elements.append(Spacer(1, 10))
    
    # 4. Tabela de Ações
    # Largura útil total da página A4 paisagem com margem 30: 842 - 60 = 782 pt
    col_widths = [45, 235, 110, 112, 140, 140]
    
    table_data = [[
        Paragraph("<b>Eixo</b>", style_th),
        Paragraph("<b>Descrição da Pergunta / Tópico</b>", style_th),
        Paragraph("<b>Indicadores</b>", style_th),
        Paragraph("<b>Diagnóstico Crítico</b>", style_th),
        Paragraph("<b>Setor Responsável Sugerido</b>", style_th),
        Paragraph("<b>Recomendação Sugerida pela CPA</b>", style_th)
    ]]
    
    for _, row in df_plano.iterrows():
        eixo_val = str(row.get('Eixo', ''))
        perg_val = str(row.get('Descrição da Pergunta / Tópico', ''))
        indic_val = str(row.get('Indicadores', ''))
        diag_val = str(row.get('Diagnóstico Crítico', ''))
        setor_val = str(row.get('Setor Responsável Sugerido', ''))
        recom_val = str(row.get('Recomendação Sugerida pela CPA', 'Revisão setorial e inclusão no plano de metas.'))
        
        table_data.append([
            Paragraph(eixo_val, style_cell_bold),
            Paragraph(perg_val, style_cell),
            Paragraph(indic_val, style_cell),
            Paragraph(diag_val, style_cell_bold),
            Paragraph(setor_val, style_cell),
            Paragraph(recom_val, style_cell)
        ])
    
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B365D')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    elements.append(t)
    
    # 5. Rodapé Informativo
    elements.append(Spacer(1, 12))
    txt_rodape = "<i>Relatório gerado automaticamente pelo Sistema de Informações Estratégicas da CPA / UNIOESTE. Os dados compilados têm caráter orientador para os colegiados e gestores institucionais.</i>"
    elements.append(Paragraph(txt_rodape, style_meta))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
