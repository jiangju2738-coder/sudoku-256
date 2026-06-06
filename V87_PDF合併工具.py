#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V87 16行PDF合併工具
將16個獨立PDF合併為一個完整文檔
"""

import os
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    import subprocess
    subprocess.run(['pip', 'install', 'pypdf', '-q'], check=True)
    from pypdf import PdfReader, PdfWriter

INPUT_DIR = 'D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output\\V87_16行獨立PDF'
OUTPUT_FILE = 'D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output\\V87_16行完整PDF合集.pdf'

def main():
    # 創建輸出目錄
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # 獲取所有PDF文件並排序（A-P順序）
    pdf_files = []
    for row in 'ABCDEFGHIJKLMNOP':
        pdf_path = os.path.join(INPUT_DIR, f'V87_{row}行獨立測試題型.pdf')
        if os.path.exists(pdf_path):
            pdf_files.append(pdf_path)
        else:
            print(f'⚠️  未找到: {pdf_path}')
    
    if not pdf_files:
        print('❌ 未找到任何PDF文件')
        return
    
    print(f'找到 {len(pdf_files)} 個PDF文件，開始合併...\n')
    
    # 創建合併器
    merger = PdfWriter()
    
    total_pages = 0
    for i, pdf_path in enumerate(pdf_files, 1):
        row_name = Path(pdf_path).stem.replace('V87_', '').replace('行獨立測試題型', '')
        print(f'{i:2d}/16 合併 {row_name}行... ', end='', flush=True)
        
        try:
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)
            total_pages += num_pages
            merger.append(reader)
            print(f'✓ ({num_pages} 頁)')
        except Exception as e:
            print(f'❌ 錯誤: {e}')
    
    print(f'\n正在寫入合併文件...')
    
    # 保存合併結果
    with open(OUTPUT_FILE, 'wb') as output:
        merger.write(output)
    
    # 統計資訊
    file_size = os.path.getsize(OUTPUT_FILE)
    print(f'\n✅ 合併完成！')
    print(f'   總頁數: {total_pages} 頁')
    print(f'   文件大小: {file_size/1024:.1f} KB')
    print(f'   輸出文件: {OUTPUT_FILE}')
    
    return OUTPUT_FILE

if __name__ == '__main__':
    main()
