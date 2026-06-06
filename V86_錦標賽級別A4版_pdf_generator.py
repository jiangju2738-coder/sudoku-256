#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86 錦標賽級別A4版電子文檔生成器
將JSON數據轉換為PDF格式，專業排版
"""

import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 嘗試註冊中文字體
try:
    pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
    pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
    FONT_NAME = 'SimHei'
    FONT_SUN = 'SimSun'
except:
    FONT_NAME = 'Helvetica'
    FONT_SUN = 'Helvetica'

# 顏色定義
HEADER_BG = HexColor('#1a5276')
HEADER_TEXT = white
ROW_A_BG = HexColor('#d4e6f1')
ROW_C_BG = HexColor('#fadbd8')  # 高熵行
ROW_E_BG = HexColor('#fadbd8')
ROW_J_BG = HexColor('#fadbd8')
ROW_B_BG = HexColor('#d5f5e3')  # 低熵行
ROW_F_BG = HexColor('#d5f5e3')
ROW_I_BG = HexColor('#d5f5e3')
ROW_M_BG = HexColor('#d5f5e3')
ROW_OTHER_BG = HexColor('#f8f9f9')
GRID_LINE = HexColor('#bdc3c7')
BORDER_COLOR = HexColor('#2c3e50')

# 從JSON讀取數據
with open('D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output\\V86_16行完整數據匯總.json', 'r', encoding='utf-8') as f:
    DATA = json.load(f)

OUTPUT_DIR = 'D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output'
OUTPUT_FILE = f'{OUTPUT_DIR}/V86_錦標賽級別測試題型.pdf'

# 建立樣式
styles = getSampleStyleSheet()

# 主標題樣式
title_style = ParagraphStyle(
    'MainTitle',
    parent=styles['Heading1'],
    fontName=FONT_NAME,
    fontSize=24,
    alignment=TA_CENTER,
    spaceAfter=6*mm,
    textColor=HEADER_BG,
    borderWidth=1,
    borderColor=BORDER_COLOR,
    borderPadding=10*mm,
    backColor=HexColor('#eaf2f8')
)

# 副標題
subtitle_style = ParagraphStyle(
    'Subtitle',
    parent=styles['Heading2'],
    fontName=FONT_NAME,
    fontSize=14,
    alignment=TA_CENTER,
    spaceAfter=12*mm,
    textColor=HexColor('#5d6d7e')
)

# 章節標題
section_style = ParagraphStyle(
    'Section',
    parent=styles['Heading2'],
    fontName=FONT_NAME,
    fontSize=14,
    spaceBefore=8*mm,
    spaceAfter=4*mm,
    textColor=HEADER_BG,
    borderWidth=0.5,
    borderColor=HEADER_BG,
    borderPadding=(2*mm, 0, 2*mm, 0)
)

# 表格標題
table_title_style = ParagraphStyle(
    'TableTitle',
    parent=styles['Normal'],
    fontName=FONT_NAME,
    fontSize=11,
    alignment=TA_CENTER,
    spaceAfter=4*mm
)

# 常規文字
body_style = ParagraphStyle(
    'Body',
    parent=styles['Normal'],
    fontName=FONT_SUN,
    fontSize=9,
    leading=14,
    alignment=TA_JUSTIFY,
    spaceAfter=3*mm
)

# 數據行樣式
data_style = ParagraphStyle(
    'Data',
    parent=styles['Normal'],
    fontName='Courier',
    fontSize=8,
    alignment=TA_CENTER
)

# 錨點標記樣式
anchor_style = ParagraphStyle(
    'Anchor',
    parent=styles['Normal'],
    fontName='Courier',
    fontSize=9,
    alignment=TA_CENTER,
    textColor=HexColor('#c0392b'),
    backColor=HexColor('#f9ebea')
)

def create_header_table():
    """建立標題表"""
    header_data = [
        ['符闔排列256數獨', '16×16 錦標賽級別測試題型'],
        ['版本: V86', f'生成時間: {DATA["metadata"]["generated"][:10]}'],
        ['謎盤錨點: 92', f'解盤錨點: 256 (16行×16列)'],
    ]
    
    t = Table(header_data, colWidths=[200*mm, 200*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), HEADER_BG),
        ('BACKGROUND', (1, 0), (1, 0), HexColor('#148f77')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('SPAN', (0, 0), (1, 0)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#eaf2f8')),
    ]))
    return t

def create_puzzle_grid(puzzle_data, is_initial=False):
    """建立數獨謎盤/解盤網格"""
    rows = list('ABCDEFGHIJKLMNOP')
    
    # 標題列
    header = ['行'] + [f'{i+1}' for i in range(16)] + ['錨點']
    table_data = [header]
    
    for row_idx, row_name in enumerate(rows):
        row_data = puzzle_data[row_name]
        anchor_count = sum(1 for x in row_data if x != 0)
        
        # 行標識
        row_label = f'{row_name}'
        if is_initial:
            row_label += ' (謎盤)'
        else:
            row_label += ' (解盤)'
        
        # 數值行
        cell_values = []
        for val in row_data:
            if val == 0:
                cell_values.append('·')
            else:
                cell_values.append(str(val))
        
        table_data.append([row_label] + cell_values + [str(anchor_count)])
    
    # 計算欄寬
    col_widths = [15*mm] + [18*mm]*16 + [15*mm]
    total_width = sum(col_widths)
    
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # 樣式設定
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, GRID_LINE),
        ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    
    # 設定宮格邊框和背景顏色
    for row_idx in range(16):
        y_start = 1 + row_idx
        y_end = y_start
        
        # 宮格行分隔
        if row_idx in [3, 7, 11]:
            style_commands.append(('LINEBELOW', (0, y_end), (-1, y_end), 1.5, BORDER_COLOR))
        
        # 高熵行背景色 (C, E, J)
        row_name = rows[row_idx]
        if row_name in ['C', 'E', 'J']:
            style_commands.append(('BACKGROUND', (0, y_start), (-1, y_end), ROW_C_BG))
        elif row_name in ['B', 'F', 'I', 'M']:
            style_commands.append(('BACKGROUND', (0, y_start), (-1, y_end), ROW_B_BG))
        else:
            style_commands.append(('BACKGROUND', (0, y_start), (-1, y_end), ROW_OTHER_BG))
        
        # 宮格列分隔
        for col_idx in range(1, 17):
            if col_idx in [5, 9, 13]:
                style_commands.append(('LINEBEFORE', (col_idx, y_start), (col_idx, y_end), 1.5, BORDER_COLOR))
    
    t.setStyle(TableStyle(style_commands))
    return t

def create_anchor_increment_table():
    """建立錨點增量統計表"""
    rows = list('ABCDEFGHIJKLMNOP')
    
    header = ['行', '初始錨點', '終局錨點', '增量', '熵級', '排列數']
    table_data = [header]
    
    anchor_analysis = DATA['anchor_analysis']['by_row']
    perm_stats = DATA['perm_stats']
    entropy_class = DATA['anchor_analysis']['entropy_classification']
    
    for row_name in rows:
        info = anchor_analysis[row_name]
        entropy = '高熵' if row_name in entropy_class['high'] else ('中熵' if row_name in entropy_class['medium'] else '低熵')
        
        table_data.append([
            row_name,
            str(info['initial']),
            str(info['final']),
            f'+{info["increment"]}',
            entropy,
            f'{perm_stats[row_name]:,}'
        ])
    
    # 總計行
    total_initial = sum(info['initial'] for info in anchor_analysis.values())
    total_increment = sum(info['increment'] for info in anchor_analysis.values())
    
    table_data.append([
        '合計',
        str(total_initial),
        '256',
        f'+{total_increment}',
        '-',
        f'{DATA["permutation_upper_bound"]:,}'
    ])
    
    t = Table(table_data, colWidths=[18*mm]*6)
    
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, GRID_LINE),
        ('FONTNAME', (0, 1), (-1, -2), FONT_SUN),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor('#d5f5e3')),
        ('FONTNAME', (0, -1), (-1, -1), FONT_NAME),
        ('FONTNAME', (0, -1), (-1, -1), FONT_NAME),
    ]
    
    # 設定熵級背景色
    for row_idx in range(1, 17):
        y = row_idx
        row_name = rows[row_idx - 1]
        if row_name in entropy_class['high']:
            style_commands.append(('BACKGROUND', (0, y), (-1, y), ROW_C_BG))
        elif row_name in entropy_class['low']:
            style_commands.append(('BACKGROUND', (0, y), (-1, y), ROW_B_BG))
        else:
            style_commands.append(('BACKGROUND', (0, y), (-1, y), ROW_OTHER_BG))
    
    t.setStyle(TableStyle(style_commands))
    return t

def build_document():
    """建立PDF文檔"""
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
        title='V86 符闔排列256數獨 - 錦標賽級別測試題型'
    )
    
    story = []
    
    # 1. 標題
    story.append(create_header_table())
    story.append(Spacer(1, 8*mm))
    
    # 2. 項目概述
    story.append(Paragraph('一、項目概述', section_style))
    
    overview_text = f'''
    本文件為符闔排列256數獨（16×16 Fummel Sudoku）錦標賽級別測試題型資料彙總。
    數獨採用符闔排列組闔約束，每行需從對應的符闔排列集合中選擇合法排列。
    '''
    story.append(Paragraph(overview_text, body_style))
    
    # 關鍵指標表格
    metrics_data = [
        ['指標', '數值'],
        ['謎盤錨點', '92'],
        ['解盤錨點', '256 (16×16)'],
        ['錨點增量', '164'],
        ['符闔排列總空間', '1,360,849'],
        ['謎盤密度', '35.9%'],
        ['解盤密度', '100%'],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[80*mm, 100*mm])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
        ('FONTNAME', (0, 1), (-1, -1), FONT_SUN),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, GRID_LINE),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9f9')),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 6*mm))
    
    # 3. 初始謎盤
    story.append(Paragraph('二、初始謎盤（92錨點）', section_style))
    story.append(create_puzzle_grid(DATA['initial_puzzle'], is_initial=True))
    story.append(PageBreak())
    
    # 4. 終局解盤
    story.append(Paragraph('三、終局解盤（完整符闔組闔排列）', section_style))
    story.append(create_puzzle_grid(DATA['final_solution'], is_initial=False))
    story.append(PageBreak())
    
    # 5. 錨點增量統計
    story.append(Paragraph('四、錨點增量統計與熵值分析', section_style))
    
    increment_intro = '''
    下表展示各行從初始謎盤到終局解盤的錨點變化情況，以及符闔排列熵值分類。
    熵值越高表示該行在符闔排列空間中的稀疏性越高，求解難度相對較大。
    '''
    story.append(Paragraph(increment_intro, body_style))
    story.append(Spacer(1, 4*mm))
    story.append(create_anchor_increment_table())
    story.append(Spacer(1, 6*mm))
    
    # 熵值說明
    entropy_text = '''
    <b>熵值分類說明：</b><br/>
    • <b>高熵組</b> (C, E, J)：增量≥12，符闔排列稀疏性最高，搜尋空間最大<br/>
    • <b>中熵組</b> (A, D, G, H, K, L, N, O, P)：增量10-11，中等填補度<br/>
    • <b>低熵組</b> (B, F, I, M)：增量8-9，初始錨點較多，約束較強
    '''
    story.append(Paragraph(entropy_text, body_style))
    story.append(Spacer(1, 8*mm))
    
    # 6. 各行詳細數據（謎盤vs解盤對比）
    story.append(Paragraph('五、各行謎盤與解盤對比', section_style))
    
    rows = list('ABCDEFGHIJKLMNOP')
    anchor_analysis = DATA['anchor_analysis']['by_row']
    
    for row_name in rows:
        initial = DATA['initial_puzzle'][row_name]
        final = DATA['final_solution'][row_name]
        new_positions = anchor_analysis[row_name]['new_anchor_positions']
        
        # 建立對比表
        compare_header = ['位置', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']
        compare_data = [compare_header]
        
        # 謎盤行
        puzzle_row = ['謎盤'] + [str(x) if x != 0 else '·' for x in initial]
        compare_data.append(puzzle_row)
        
        # 解盤行
        solution_row = ['解盤'] + [str(x) for x in final]
        compare_data.append(solution_row)
        
        # 差異標記行
        diff_row = ['差異']
        for i in range(16):
            if initial[i] == 0 and final[i] != 0:
                diff_row.append(f'→{final[i]}')  # 新增
            elif initial[i] == final[i]:
                diff_row.append('=')  # 保持
            else:
                diff_row.append('?')  # 不一致（不應發生）
        compare_data.append(diff_row)
        
        t = Table(compare_data, colWidths=[12*mm] + [12*mm]*16)
        
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),
            ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.3, GRID_LINE),
            ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('BACKGROUND', (0, 1), (-1, 1), HexColor('#fdebd0')),  # 謎盤
            ('BACKGROUND', (0, 2), (-1, 2), HexColor('#d5f5e3')),  # 解盤
            ('BACKGROUND', (0, 3), (-1, 3), HexColor('#e8daef')),  # 差異
            ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
        ]
        
        # 標記新增錨點
        for pos in new_positions:
            x = pos + 1  # +1 因為第一列是行標識
            style_commands.append(('BACKGROUND', (x, 2), (x, 2), HexColor('#fadbd8')))
            style_commands.append(('TEXTCOLOR', (x, 2), (x, 2), HexColor('#c0392b')))
            style_commands.append(('FONTNAME', (x, 2), (x, 2), 'Courier-Bold'))
        
        t.setStyle(TableStyle(style_commands))
        story.append(t)
        story.append(Spacer(1, 3*mm))
    
    # 7. 匯總統計
    story.append(PageBreak())
    story.append(Paragraph('六、匯總統計', section_style))
    
    summary_text = f'''
    <b>符闔排列256數獨 V86 匯總統計</b><br/><br/>
    • <b>謎盤錨點</b>：{DATA["summary"]["initial_anchors"]} 個<br/>
    • <b>解盤錨點</b>：{DATA["summary"]["final_anchors"]} 個 (16行 × 16列)<br/>
    • <b>錨點增量</b>：{DATA["summary"]["total_increment"]} 個<br/>
    • <b>符闔排列總空間</b>：{DATA["permutation_upper_bound"]:,} 個<br/>
    • <b>謎盤密度</b>：{DATA["summary"]["initial_anchors"]}/{DATA["summary"]["final_anchors"]} = {DATA["summary"]["initial_anchors"]/DATA["summary"]["final_anchors"]*100:.1f}%<br/><br/>
    
    <b>熵值分布</b><br/>
    • 高熵行：C, E, J（3行）<br/>
    • 中熵行：A, D, G, H, K, L, N, O, P（9行）<br/>
    • 低熵行：B, F, I, M（4行）<br/><br/>
    
    <b>輸出文件</b><br/>
    • V86_16行完整數據匯總.md（Markdown格式）<br/>
    • V86_16行完整數據匯總.json（JSON格式）<br/>
    • V86_錦標賽級別測試題型.pdf（A4版PDF文檔）
    '''
    story.append(Paragraph(summary_text, body_style))
    
    # 建立文檔
    doc.build(story)
    print(f'✓ PDF文檔已生成: {OUTPUT_FILE}')
    return OUTPUT_FILE

if __name__ == '__main__':
    output_file = build_document()
    print(f'完成！文件路徑: {output_file}')
