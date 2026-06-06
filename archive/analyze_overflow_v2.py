#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔排列溢出分析 v2：檢查過度約束問題
"""

import openpyxl
from collections import Counter
from pathlib import Path
import sys

chinese_names = {
    'A':'第一','B':'第二','C':'第三','D':'第四','E':'第五','F':'第六',
    'G':'第七','H':'第八','I':'第九','J':'第十','K':'第十一','L':'第十二',
    'M':'第十三','N':'第十四','O':'第十五','P':'第十六'
}

base_dir = Path('D:/2026/WPF_Sudoku/Sudoku_256')

print('符闔排列溢出分析 v2')
print('='*70)

overflow_summary = {}

for row_name in ['A', 'B', 'P']:  # 先分析關鍵行
    fpath = base_dir / f'{row_name}{chinese_names[row_name]}行符闔排列.xlsx'
    
    if not fpath.exists():
        print(f'行{row_name}: 文件不存在')
        continue
    
    print(f'\n分析行{row_name}...', file=sys.stderr)
    
    try:
        wb = openpyxl.load_workbook(str(fpath), data_only=True, read_only=True)
        ws = wb.active
        
        perms = []
        count = 0
        for row_data in ws.iter_rows(values_only=True):
            if len(row_data) >= 19:
                vals = []
                for i in range(3, 19):
                    v = row_data[i]
                    if isinstance(v, (int, float)) and 1 <= v <= 16:
                        vals.append(int(v))
                if len(vals) == 16:
                    perms.append(tuple(vals))
            count += 1
            if count % 10000 == 0:
                print(f'   已讀取 {count} 行...', file=sys.stderr)
        
        wb.close()
        print(f'   總共 {len(perms)} 個排列', file=sys.stderr)
    except Exception as e:
        print(f'行{row_name}: 讀取錯誤 - {e}', file=sys.stderr)
        continue
    
    if not perms:
        print(f'行{row_name}: 排列為空')
        continue
    
    # 檢查位置約束
    overflow_positions = []
    for pos in range(16):
        counter = Counter(p[pos] for p in perms)
        if len(counter) == 1:
            overflow_positions.append((pos, list(counter.keys())[0]))
    
    status = '⚠️ 溢出' if overflow_positions else 'OK'
    print(f'行{row_name}: {len(perms):6d} 排列, {len(overflow_positions):2d} 個位置過度固定 {status}')
    if overflow_positions:
        overflow_summary[row_name] = overflow_positions
        for pos, val in overflow_positions:
            print(f'         位置 {pos+1:2d} 固定為 {val}')
    
    # 檢查前 4 位組合多樣性
    prefixes = Counter((p[0], p[1], p[2], p[3]) for p in perms)
    print(f'  不同前 4 位組合數: {len(prefixes)}')
    
    # 檢查 CP-SAT 解的前 4 位
    if row_name == 'A':
        cp_sat_prefix = (7, 15, 3, 9)
    elif row_name == 'B':
        cp_sat_prefix = (16, 12, 10, 8)
    else:
        cp_sat_prefix = (8, 7, 2, 3)
    
    matching_count = prefixes.get(cp_sat_prefix, 0)
    print(f'  CP-SAT 前 4 位 {cp_sat_prefix} 出現次數: {matching_count}')
    
    if matching_count == 1:
        print(f'  ⚠️ 溢出警告：前 4 位唯一確定排列！')
    elif matching_count == 0:
        print(f'  ❌ CP-SAT 前 4 位不在排列池中！')
    else:
        print(f'  ✅ 前 4 位有 {matching_count} 個匹配，無溢出問題')

print()
print('='*70)
print('溢出總結')
print('='*70)
if overflow_summary:
    print(f'共 {len(overflow_summary)} 行存在溢出:')
    for row, positions in overflow_summary.items():
        print(f'  行{row}: {len(positions)} 個位置過度固定')
else:
    print('無溢出問題')
