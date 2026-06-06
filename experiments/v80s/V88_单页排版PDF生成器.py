#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V88 单页排版PDF生成器
每行2页：第1页谜题 + 第2页解盘
使用竖排A4纸张，缩小格子使16列在一页内显示
"""

import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册中文字体
try:
    pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
    pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
    FONT_NAME = 'SimHei'
    FONT_SUN = 'SimSun'
except:
    FONT_NAME = 'Helvetica'
    FONT_SUN = 'Helvetica'

# 颜色定义
HEADER_BG = HexColor('#1a5276')
HEADER_TEXT = white
SUBTITLE_BG = HexColor('#148f77')

# 熵级颜色
HIGH_ENTROPY_BG = HexColor('#fadbd8')
MEDIUM_ENTROPY_BG = HexColor('#f8f9f9')
LOW_ENTROPY_BG = HexColor('#d5f5e3')

GRID_LINE = HexColor('#bdc3c7')
BORDER_COLOR = HexColor('#2c3e50')
PUZZLE_BG = HexColor('#fff3e0')
SOLUTION_BG = HexColor('#e8f5e9')

# 读取数据
DATA_FILE = 'D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output\\V86_16行完整數據匯總.json'
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    DATA = json.load(f)

OUTPUT_DIR = 'D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output\\V88_单页排版PDF'
ROWS = list('ABCDEFGHIJKLMNOP')

ENTROPY_CLASS = {
    'high': ['C', 'E', 'J'],
    'medium': ['A', 'D', 'G', 'H', 'K', 'L', 'N', 'O', 'P'],
    'low': ['B', 'F', 'I', 'M']
}

def get_entropy_color(row_name):
    if row_name in ENTROPY_CLASS['high']:
        return HIGH_ENTROPY_BG
    elif row_name in ENTROPY_CLASS['low']:
        return LOW_ENTROPY_BG
    else:
        return MEDIUM_ENTROPY_BG

def get_entropy_label(row_name):
    if row_name in ENTROPY_CLASS['high']:
        return '★高熵'
    elif row_name in ENTROPY_CLASS['low']:
        return '低熵'
    else:
        return '中熵'

def create_grid_table(puzzle_data, is_initial=True, target_row=None):
    """创建数独网格 - 单页16列紧凑排版"""
    rows = list('ABCDEFGHIJKLMNOP')
    
    # 表头：行标识 + 16列 + 锚点数
    header = ['行'] + [f'{i+1}' for i in range(16)] + ['锚点']
    table_data = [header]
    
    for row_name in rows:
        row_data = puzzle_data[row_name]
        anchor_count = sum(1 for x in row_data if x != 0)
        
        # 行标签（带★标记目标行）
        row_label = f'{row_name}'
        if row_name == target_row:
            row_label = f'{row_name} ★'
        
        # 单元格内容
        cells = []
        for val in row_data:
            if val == 0:
                cells.append('·')
            else:
                cells.append(str(val))
        
        table_data.append([row_label] + cells + [str(anchor_count)])
    
    # 计算列宽：(可用宽度 210-36=174mm) / 18列 = 9.67mm/列
    # 留一些边距，使用9mm
    col_width = 9 * mm
    col_widths = [10 * mm] + [col_width] * 16 + [12 * mm]
    
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, GRID_LINE),
        ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]
    
    # 宫格分隔线和目标行标记
    for row_idx in range(16):
        y = 1 + row_idx
        row_name = rows[row_idx]
        
        # 宫格行分隔（每4行一粗线）
        if row_idx in [3, 7, 11]:
            style_cmds.append(('LINEBELOW', (0, y), (-1, y), 1.2, BORDER_COLOR))
        
        # 宫格列分隔（每4列一粗线）
        for col_idx in [5, 9, 13]:
            style_cmds.append(('LINEBEFORE', (col_idx, y), (col_idx, y), 1.2, BORDER_COLOR))
        
        # 目标行特殊标记
        if row_name == target_row:
            entropy_bg = get_entropy_color(row_name)
            style_cmds.append(('BACKGROUND', (0, y), (-1, y), entropy_bg))
            style_cmds.append(('BOX', (0, y), (-1, y), 1.5, BORDER_COLOR))
    
    t.setStyle(TableStyle(style_cmds))
    return t


def generate_row_pdf(row_name):
    """生成单行PDF - 2页（谜题1页 + 解盘1页）"""
    entropy_label = get_entropy_label(row_name)
    output_file = f'{OUTPUT_DIR}/V88_{row_name}行单页排版.pdf'
    
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=12*mm,
        bottomMargin=12*mm,
        title=f'V88 {row_name}行符闔256数独'
    )
    
    story = []
    
    # 标题
    title_data = [
        [f'符闔排列256数独 - {row_name}行', f'熵级: {entropy_label}'],
        [f'初始谜盘 锚点: {DATA["anchor_analysis"]["by_row"][row_name]["initial"]}', 
         f'终局解盘 锚点: 16'],
    ]
    title_table = Table(title_data, colWidths=[90*mm, 70*mm])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, -1), HEADER_TEXT),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, 1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 2, BORDER_COLOR),
        ('LINEBELOW', (0, 0), (-1, 0), 1, BORDER_COLOR),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 4*mm))
    
    # 第1页：初始谜盘
    story.append(Paragraph('第1页：初始谜盘（92锚点）', ParagraphStyle(
        'Header', parent=getSampleStyleSheet()['Normal'],
        fontName=FONT_NAME, fontSize=10, textColor=HEADER_BG,
        alignment=TA_CENTER, spaceAfter=3*mm
    )))
    puzzle_grid = create_grid_table(DATA['initial_puzzle'], is_initial=True, target_row=row_name)
    story.append(puzzle_grid)
    
    # 页面分隔符
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', ParagraphStyle(
        'Divider', parent=getSampleStyleSheet()['Normal'],
        fontName=FONT_NAME, fontSize=10, textColor=HexColor('#cccccc'),
        alignment=TA_CENTER
    )))
    story.append(Spacer(1, 10*mm))
    
    # 第2页：终局解盘
    story.append(Paragraph('第2页：终局解盘（完整符阖排列）', ParagraphStyle(
        'Header', parent=getSampleStyleSheet()['Normal'],
        fontName=FONT_NAME, fontSize=10, textColor=HEADER_BG,
        alignment=TA_CENTER, spaceAfter=3*mm
    )))
    solution_grid = create_grid_table(DATA['final_solution'], is_initial=False, target_row=row_name)
    story.append(solution_grid)
    
    doc.build(story)
    return output_file


def main():
    import os
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f'开始生成16行单页排版PDF...')
    print(f'输出目录: {OUTPUT_DIR}\n')
    
    generated_files = []
    for row_name in ROWS:
        output_file = generate_row_pdf(row_name)
        generated_files.append(output_file)
        print(f'✓ {row_name}行完成: {os.path.basename(output_file)}')
    
    print(f'\n全部完成！共生成 {len(generated_files)} 个PDF文件')
    print(f'每个文件2页：第1页谜盘 + 第2页解盘')
    
    return generated_files


if __name__ == '__main__':
    files = main()
    print('\n=== 文件清单 ===')
    for f in files:
        size = os.path.getsize(f)
        print(f'  {os.path.basename(f)} ({size/1024:.1f} KB)')
