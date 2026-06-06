#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V87 16行獨立PDF生成器
為每行創建獨立的A4 PDF文檔：初始謎盤 + 終局解盤
"""

import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 註冊中文字體
try:
    pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
    pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
    FONT_NAME = 'SimHei'
    FONT_SUN = 'SimSun'
except:
    FONT_NAME = 'Helvetica'
    FONT_SUN = 'Helvetica'

# 顏色定義 - 錦標賽級別配色
HEADER_BG = HexColor('#1a5276')
HEADER_TEXT = white
SUBTITLE_BG = HexColor('#148f77')

# 熵級顏色
HIGH_ENTROPY_BG = HexColor('#fadbd8')  # 紅色
MEDIUM_ENTROPY_BG = HexColor('#f8f9f9')  # 灰白
LOW_ENTROPY_BG = HexColor('#d5f5e3')   # 綠色

# 網格顏色
GRID_LINE = HexColor('#bdc3c7')
BORDER_COLOR = HexColor('#2c3e50')
PUZZLE_BG = HexColor('#fff3e0')  # 謎盤背景 - 暖橙
SOLUTION_BG = HexColor('#e8f5e9')  # 解盤背景 - 淺綠
NEW_ANCHOR_BG = HexColor('#ffcdd2')  # 新增錨點 - 紅粉
NEW_ANCHOR_TEXT = HexColor('#c62828')

# 從JSON讀取數據
with open('D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output\\V86_16行完整數據匯總.json', 'r', encoding='utf-8') as f:
    DATA = json.load(f)

OUTPUT_DIR = 'D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output\\V87_16行獨立PDF'
ROWS = list('ABCDEFGHIJKLMNOP')

# 熵級分類
ENTROPY_CLASS = {
    'high': ['C', 'E', 'J'],
    'medium': ['A', 'D', 'G', 'H', 'K', 'L', 'N', 'O', 'P'],
    'low': ['B', 'F', 'I', 'M']
}

def get_entropy_color(row_name):
    """獲取熵級背景色"""
    if row_name in ENTROPY_CLASS['high']:
        return HIGH_ENTROPY_BG
    elif row_name in ENTROPY_CLASS['low']:
        return LOW_ENTROPY_BG
    else:
        return MEDIUM_ENTROPY_BG

def get_entropy_label(row_name):
    """獲取熵級標籤"""
    if row_name in ENTROPY_CLASS['high']:
        return '★高熵'
    elif row_name in ENTROPY_CLASS['low']:
        return '低熵'
    else:
        return '中熵'

def create_title_table(row_name, entropy_label):
    """創建標題表"""
    header_data = [
        [f'符闔排列256數獨 - {row_name}行獨立測試題型'],
        [f'熵級: {entropy_label} | 初始謎盤錨點: {DATA["anchor_analysis"]["by_row"][row_name]["initial"]} → 終局解盤錨點: 16'],
    ]
    
    t = Table(header_data, colWidths=[180*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('BACKGROUND', (0, 1), (-1, 1), SUBTITLE_BG),
        ('TEXTCOLOR', (0, 0), (-1, -1), HEADER_TEXT),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 16),
        ('FONTSIZE', (0, 1), (-1, 1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 2, BORDER_COLOR),
    ]))
    return t

def create_puzzle_grid(puzzle_data, is_initial=False, target_row=None):
    """創建數獨網格，突出顯示目標行"""
    rows = list('ABCDEFGHIJKLMNOP')
    
    # 表頭
    header = ['行'] + [f'{i+1}' for i in range(16)] + ['錨點']
    table_data = [header]
    
    for row_idx, row_name in enumerate(rows):
        row_data = puzzle_data[row_name]
        anchor_count = sum(1 for x in row_data if x != 0)
        
        row_label = f'{row_name}'
        if row_name == target_row:
            row_label += ' ★'  # 標記目標行
        
        cell_values = []
        for val in row_data:
            if val == 0:
                cell_values.append('·')
            else:
                cell_values.append(str(val))
        
        table_data.append([row_label] + cell_values + [str(anchor_count)])
    
    # 計算欄寬
    col_widths = [12*mm] + [15*mm]*16 + [15*mm]
    
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    
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
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    
    for row_idx in range(16):
        y_start = 1 + row_idx
        y_end = y_start
        row_name = rows[row_idx]
        
        # 宮格行分隔
        if row_idx in [3, 7, 11]:
            style_commands.append(('LINEBELOW', (0, y_end), (-1, y_end), 1.5, BORDER_COLOR))
        
        # 宮格列分隔
        for col_idx in range(1, 17):
            if col_idx in [5, 9, 13]:
                style_commands.append(('LINEBEFORE', (col_idx, y_start), (col_idx, y_end), 1.5, BORDER_COLOR))
        
        # 背景色
        if row_name == target_row:
            # 目標行使用熵級背景色
            entropy_bg = get_entropy_color(row_name)
            style_commands.append(('BACKGROUND', (0, y_start), (-1, y_end), entropy_bg))
            style_commands.append(('BOX', (0, y_start), (-1, y_end), 2, BORDER_COLOR))
        else:
            style_commands.append(('BACKGROUND', (0, y_start), (-1, y_end), HexColor('#fafafa')))
    
    t.setStyle(TableStyle(style_commands))
    return t

def create_comparison_table(target_row):
    """創建謎盤vs解盤對比表"""
    rows = list('ABCDEFGHIJKLMNOP')
    initial = DATA['initial_puzzle']
    final = DATA['final_solution']
    new_positions = DATA['anchor_analysis']['by_row'][target_row]['new_anchor_positions']
    
    # 標題行
    header = ['位置'] + [f'{i+1}' for i in range(16)]
    table_data = [header]
    
    # 謎盤行
    puzzle_row = ['謎盤']
    for val in initial[target_row]:
        puzzle_row.append(str(val) if val != 0 else '·')
    table_data.append(puzzle_row)
    
    # 解盤行
    solution_row = ['解盤']
    for val in final[target_row]:
        solution_row.append(str(val))
    table_data.append(solution_row)
    
    # 變化行
    change_row = ['變化']
    for i in range(16):
        if initial[target_row][i] == 0 and final[target_row][i] != 0:
            change_row.append(f'→{final[target_row][i]}')
        elif initial[target_row][i] == final[target_row][i]:
            change_row.append('=')
        else:
            change_row.append('?')
    table_data.append(change_row)
    
    col_widths = [15*mm] + [15*mm]*16
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, GRID_LINE),
        ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BACKGROUND', (0, 1), (-1, 1), PUZZLE_BG),
        ('BACKGROUND', (0, 2), (-1, 2), SOLUTION_BG),
        ('BACKGROUND', (0, 3), (-1, 3), HexColor('#f3e5f5')),
    ]
    
    # 標記新增錨點位置
    for pos in new_positions:
        x = pos + 1  # +1 因為第一列是行標識
        style_commands.append(('BACKGROUND', (x, 3), (x, 3), NEW_ANCHOR_BG))
        style_commands.append(('TEXTCOLOR', (x, 3), (x, 3), NEW_ANCHOR_TEXT))
        style_commands.append(('FONTNAME', (x, 3), (x, 3), 'Courier-Bold'))
    
    t.setStyle(TableStyle(style_commands))
    return t

def create_stats_table(target_row):
    """創建統計信息表"""
    info = DATA['anchor_analysis']['by_row'][target_row]
    perm_count = DATA['perm_stats'][target_row]
    entropy_label = get_entropy_label(target_row)
    
    stats_data = [
        ['統計指標', '數值'],
        ['目標行', target_row],
        ['熵級分類', entropy_label],
        ['謎盤錨點', str(info['initial'])],
        ['解盤錨點', '16'],
        ['新增錨點數', str(info['increment'])],
        [f'{target_row}行符闔排列數', f'{perm_count:,}'],
        ['新增錨點位置', str([p+1 for p in info['new_anchor_positions']])],
    ]
    
    t = Table(stats_data, colWidths=[80*mm, 80*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
        ('FONTNAME', (0, 1), (-1, -1), FONT_SUN),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, GRID_LINE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#eaf2f8')),
    ]))
    return t

def generate_row_pdf(row_name):
    """生成單行PDF文檔"""
    entropy_label = get_entropy_label(row_name)
    output_file = f'{OUTPUT_DIR}/V87_{row_name}行獨立測試題型.pdf'
    
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
        title=f'V87 {row_name}行符闔排列256數獨測試題型'
    )
    
    story = []
    
    # 1. 標題
    story.append(create_title_table(row_name, entropy_label))
    story.append(Spacer(1, 8*mm))
    
    # 2. 謎盤
    story.append(Paragraph('一、初始謎盤', ParagraphStyle(
        'Section', parent=getSampleStyleSheet()['Heading2'],
        fontName=FONT_NAME, fontSize=13, textColor=HEADER_BG,
        spaceBefore=6*mm, spaceAfter=4*mm
    )))
    story.append(create_puzzle_grid(DATA['initial_puzzle'], is_initial=True, target_row=row_name))
    story.append(Spacer(1, 6*mm))
    
    # 3. 解盤
    story.append(Paragraph('二、終局解盤', ParagraphStyle(
        'Section', parent=getSampleStyleSheet()['Heading2'],
        fontName=FONT_NAME, fontSize=13, textColor=HEADER_BG,
        spaceBefore=6*mm, spaceAfter=4*mm
    )))
    story.append(create_puzzle_grid(DATA['final_solution'], is_initial=False, target_row=row_name))
    story.append(Spacer(1, 6*mm))
    
    # 4. 謎盤vs解盤對比
    story.append(Paragraph(f'三、{row_name}行謎盤與解盤對比', ParagraphStyle(
        'Section', parent=getSampleStyleSheet()['Heading2'],
        fontName=FONT_NAME, fontSize=13, textColor=HEADER_BG,
        spaceBefore=6*mm, spaceAfter=4*mm
    )))
    story.append(Paragraph('新增錨點位置以紅色粗體突出顯示（→數字格式）', ParagraphStyle(
        'Note', parent=getSampleStyleSheet()['Normal'],
        fontName=FONT_SUN, fontSize=8, textColor=HexColor('#7f8c8d'),
        spaceAfter=3*mm
    )))
    story.append(create_comparison_table(row_name))
    story.append(Spacer(1, 6*mm))
    
    # 5. 統計信息
    story.append(Paragraph('四、統計信息', ParagraphStyle(
        'Section', parent=getSampleStyleSheet()['Heading2'],
        fontName=FONT_NAME, fontSize=13, textColor=HEADER_BG,
        spaceBefore=6*mm, spaceAfter=4*mm
    )))
    story.append(create_stats_table(row_name))
    
    doc.build(story)
    return output_file

def main():
    """主函數：生成16行PDF文檔"""
    import os
    
    # 創建輸出目錄
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f'開始生成16行獨立PDF文檔...')
    print(f'輸出目錄: {OUTPUT_DIR}\n')
    
    generated_files = []
    for row_name in ROWS:
        output_file = generate_row_pdf(row_name)
        generated_files.append(output_file)
        print(f'✓ {row_name}行完成: {output_file}')
    
    print(f'\n全部完成！共生成 {len(generated_files)} 個PDF文件')
    return generated_files

if __name__ == '__main__':
    files = main()
    print('\n=== 輸出文件清單 ===')
    for f in files:
        import os
        size = os.path.getsize(f)
        print(f'  {os.path.basename(f)} ({size/1024:.1f} KB)')
