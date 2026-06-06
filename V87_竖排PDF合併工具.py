#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V87 竖排PDF合併工具 - 將16個竖排獨立PDF合併為一個完整PDF
"""

import os
from pypdf import PdfReader, PdfWriter

INPUT_DIR = 'D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output\\V87_16行獨立PDF_竖排'
OUTPUT_FILE = 'D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output\\V87_16行完整竖排PDF合集.pdf'

def main():
    """合併16個竖排PDF為一個完整PDF"""
    # 收集所有PDF文件，按A-P順序
    pdf_files = []
    for row in 'ABCDEFGHIJKLMNOP':
        filename = f'V87_{row}行獨立測試題型_竖排.pdf'
        filepath = os.path.join(INPUT_DIR, filename)
        if os.path.exists(filepath):
            pdf_files.append(filepath)
        else:
            print(f'警告: 文件不存在 - {filepath}')
    
    print(f'找到 {len(pdf_files)} 個PDF文件')
    
    if not pdf_files:
        print('錯誤: 沒有找到任何PDF文件')
        return
    
    # 合併PDF
    merger = PdfWriter()
    
    for i, filepath in enumerate(pdf_files):
        print(f'添加第 {i+1} 個: {os.path.basename(filepath)}')
        merger.append(PdfReader(filepath))
    
    # 保存合併後的PDF
    merger.write(OUTPUT_FILE)
    merger.close()
    
    # 檢查文件大小
    size = os.path.getsize(OUTPUT_FILE)
    print(f'\n✓ 合併完成！')
    print(f'輸出文件: {OUTPUT_FILE}')
    print(f'文件大小: {size/1024:.1f} KB')
    print(f'總頁數: {len(merger.pages) if hasattr(merger, "pages") else len(pdf_files) * 2} 頁')

if __name__ == '__main__':
    main()
