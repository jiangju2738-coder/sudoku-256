#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版：多先行相容性分析
"""

import openpyxl
import json
import re
from pathlib import Path
from typing import List, Dict
from collections import Counter

def get_row_chinese_name(row_label: str) -> str:
    chinese_names = {
        'A': '第一', 'B': '第二', 'C': '第三', 'D': '第四',
        'E': '第五', 'F': '第六', 'G': '第七', 'H': '第八',
        'I': '第九', 'J': '第十', 'K': '第十一', 'L': '第十二',
        'M': '第十三', 'N': '第十四', 'O': '第十五', 'P': '第十六'
    }
    return chinese_names.get(row_label, '')

def load_row_permutations(row_label: str) -> List[Dict]:
    """載入指定行的符闔排列"""
    filename = f"{row_label}{get_row_chinese_name(row_label)}行符闔排列.xlsx"
    filepath = Path("D:/2026/WPF_Sudoku/Sudoku_256") / filename
    
    if not filepath.exists():
        print(f"⚠️ 未找到檔案: {filename}")
        return []
    
    try:
        wb = openpyxl.load_workbook(str(filepath), data_only=True)
        ws = wb.active
        
        permutations = []
        for row in ws.iter_rows(values_only=True):
            if len(row) < 20:
                continue
            
            numeric_values = []
            for i in range(3, 19):
                if i < len(row):
                    val = row[i]
                    if isinstance(val, (int, float)) and 1 <= val <= 16:
                        numeric_values.append(int(val))
            
            if len(numeric_values) == 16:
                permutations.append({
                    'id': row[1],
                    'label': row[2],
                    'values': numeric_values
                })
        
        wb.close()
        return permutations
    except Exception as e:
        print(f"❌ 載入 {filename} 失敗: {e}")
        return []

def load_puzzle_config():
    """載入謎題配置"""
    filepath = Path("D:/2026/WPF_Sudoku/Sudoku_256/超級大數獨_box_size4.txt")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    grid = [[0]*16 for _ in range(16)]
    row_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
    row_given_cells = {}
    
    row_pattern = r'行([A-P]) \[(.*?)\]'
    for match in re.finditer(row_pattern, content):
        row_label = match.group(1)
        values_str = match.group(2)
        values = [int(v.strip()) if v.strip() != '0' else 0 for v in values_str.split(',')]
        
        row_idx = ord(row_label) - ord('A')
        grid[row_idx] = values
        
        given = {}
        for j, val in enumerate(values):
            if val != 0:
                given[j] = val
        
        row_given_cells[row_label] = given
    
    return grid, row_given_cells

def filter_compatible(permutations: List[Dict], given_cells: Dict[int, int]) -> List[Dict]:
    """過濾相容排列"""
    if not given_cells:
        return permutations
    
    compatible = []
    for perm in permutations:
        match = True
        for col, expected_val in given_cells.items():
            if col < len(perm['values']) and perm['values'][col] != expected_val:
                match = False
                break
        if match:
            compatible.append(perm)
    
    return compatible

# 主程式
print("=" * 80)
print("多先行相容性分析（簡化版）")
print("=" * 80)

# 載入謎題配置
grid, row_given_cells = load_puzzle_config()
print(f"✅ 謎題載入: 16×16 網格，總已知數 {sum(len(g) for g in row_given_cells.values())}")

row_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
results = {}

for row_label in row_labels:
    print(f"\n📊 分析行{row_label}...")
    given_cells = row_given_cells.get(row_label, {})
    given_count = len(given_cells)
    
    # 載入排列池
    permutations = load_row_permutations(row_label)
    
    # 過濾相容排列
    compatible = filter_compatible(permutations, given_cells)
    
    # 確定狀態
    if given_count == 16:
        status = "🔬 FULLY_KNOWN"
    elif len(compatible) == 1:
        status = "🔍 SINGLE_COMPATIBLE"
    elif len(compatible) > 1:
        status = "🎯 MULTIPLE_COMPATIBLE"
    else:
        status = "❌ NO_COMPATIBLE"
    
    results[row_label] = {
        'given_count': given_count,
        'pool_size': len(permutations),
        'compatible_count': len(compatible),
        'status': status,
        'compatible_sample': compatible[:3] if compatible else []
    }
    
    print(f"   已知數: {given_count}")
    print(f"   排列池: {len(permutations)}")
    print(f"   相容排列: {len(compatible)}")
    print(f"   狀態: {status}")

# 保存結果
output = {
    'analysis_time': '2026-05-17T03:41:00+08:00',
    'row_results': {k: {
        'given_count': v['given_count'],
        'pool_size': v['pool_size'],
        'compatible_count': v['compatible_count'],
        'status': v['status']
    } for k, v in results.items()}
}

with open('D:/2026/WPF_Sudoku/Sudoku_256/compatibility_analysis_simple.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n✅ 分析完成，結果已保存")

# 輸出總結
print("\n" + "=" * 80)
print("總結")
print("=" * 80)

fully_known = [k for k, v in results.items() if v['given_count'] == 16]
single_compat = [k for k, v in results.items() if v['compatible_count'] == 1 and v['given_count'] < 16]
multi_compat = [k for k, v in results.items() if v['compatible_count'] > 1]
no_compat = [k for k, v in results.items() if v['compatible_count'] == 0 and v['given_count'] < 16]

print(f"\n🔬 完全確定先行 ({len(fully_known)}): {', '.join(fully_known)}")
print(f"🔍 唯一相容先行 ({len(single_compat)}): {', '.join(single_compat)}")
print(f"🎯 多相容先行 ({len(multi_compat)}): {', '.join(multi_compat)}")
print(f"❌ 無相容先行 ({len(no_compat)}): {', '.join(no_compat)}")
