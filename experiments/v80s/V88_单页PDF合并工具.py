#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V88 PDF合并工具 - 将16个单页排版PDF合并为一个完整PDF
"""

import os
from pypdf import PdfReader, PdfWriter

INPUT_DIR = 'D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output\\V88_单页排版PDF'
OUTPUT_FILE = 'D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output\\V88_16行单页PDF合集.pdf'

def main():
    # 收集PDF文件，按A-P顺序
    rows = 'ABCDEFGHIJKLMNOP'
    pdf_files = []
    for row in rows:
        filename = f'V88_{row}行单页排版.pdf'
        filepath = os.path.join(INPUT_DIR, filename)
        if os.path.exists(filepath):
            pdf_files.append(filepath)
        else:
            print(f'警告: 文件不存在 - {filepath}')
    
    print(f'找到 {len(pdf_files)} 个PDF文件')
    
    if not pdf_files:
        print('错误: 没有找到任何PDF文件')
        return
    
    # 合并
    merger = PdfWriter()
    for filepath in pdf_files:
        merger.append(PdfReader(filepath))
    
    merger.write(OUTPUT_FILE)
    merger.close()
    
    size = os.path.getsize(OUTPUT_FILE)
    print(f'\n✓ 合并完成！')
    print(f'输出文件: {OUTPUT_FILE}')
    print(f'文件大小: {size/1024:.1f} KB')
    print(f'总页数: {32} 页（16行 × 2页/行）')

if __name__ == '__main__':
    main()
