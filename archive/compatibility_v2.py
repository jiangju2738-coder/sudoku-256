#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐行分析：多先行相容性分析
"""

import openpyxl
import json
import re
import sys
from pathlib import Path

def get_chinese_name(label):
    names = {'A':'第一','B':'第二','C':'第三','D':'第四','E':'第五','F':'第六',
             'G':'第七','H':'第八','I':'第九','J':'第十','K':'第十一','L':'第十二',
             'M':'第十三','N':'第十四','O':'第十五','P':'第十六'}
    return names.get(label, '')

def load_permutations(label):
    fname = f"{label}{get_chinese_name(label)}行符闔排列.xlsx"
    fpath = Path("D:/2026/WPF_Sudoku/Sudoku_256") / fname
    if not fpath.exists():
        return None, f"檔案不存在: {fname}"
    
    try:
        wb = openpyxl.load_workbook(str(fpath), data_only=True, read_only=True)
        ws = wb.active
        perms = []
        count = 0
        for row in ws.iter_rows(values_only=True):
            if len(row) >= 19:
                vals = []
                for i in range(3, 19):
                    v = row[i]
                    if isinstance(v, (int, float)) and 1 <= v <= 16:
                        vals.append(int(v))
                if len(vals) == 16:
                    perms.append({'id': row[1], 'label': row[2], 'values': vals})
            count += 1
            if count % 500 == 0:
                sys.stdout.write(f"  已讀取 {count} 行...\n")
                sys.stdout.flush()
        wb.close()
        return perms, None
    except Exception as e:
        return None, str(e)

def load_config():
    fpath = Path("D:/2026/WPF_Sudoku/Sudoku_256/超級大數獨_box_size4.txt")
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    grid = [[0]*16 for _ in range(16)]
    row_given = {}
    for m in re.finditer(r'行([A-P]) \[(.*?)\]', content):
        label, vals_str = m.group(1), m.group(2)
        vals = [int(v.strip()) if v.strip()!='0' else 0 for v in vals_str.split(',')]
        idx = ord(label) - ord('A')
        grid[idx] = vals
        given = {j:v for j,v in enumerate(vals) if v != 0}
        row_given[label] = given
    return grid, row_given

# 主程式
print("="*80)
print("多先行相容性分析")
print("="*80)

grid, row_given = load_config()
print(f"✅ 謎題載入: 16×16, 總已知數={sum(len(g) for g in row_given.values())}")

labels = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
results = {}

for label in labels:
    print(f"\n{'='*60}")
    print(f"行 {label} ({get_chinese_name(label)}行)")
    print(f"{'='*60}")
    
    given = row_given.get(label, {})
    given_count = len(given)
    print(f"已知數: {given_count}")
    
    # 載入排列
    print("載入排列池...")
    perms, err = load_permutations(label)
    if err:
        print(f"❌ {err}")
        results[label] = {'given': given_count, 'pool': 0, 'compatible': 0, 'error': err}
        continue
    
    print(f"排列池: {len(perms)}")
    
    # 過濾相容
    if given:
        compatible = []
        for p in perms:
            ok = True
            for col, val in given.items():
                if col < 16 and p['values'][col] != val:
                    ok = False
                    break
            if ok:
                compatible.append(p)
    else:
        compatible = perms
    
    print(f"相容排列: {len(compatible)}")
    
    if len(compatible) <= 3 and compatible:
        print("相容排列:")
        for p in compatible:
            print(f"  {p['label']}: {p['values']}")
    
    # 狀態分類
    if given_count == 16:
        status = "FULLY_KNOWN"
    elif len(compatible) == 1:
        status = "SINGLE_COMPATIBLE"
    elif len(compatible) > 1:
        status = "MULTIPLE_COMPATIBLE"
    else:
        status = "NO_COMPATIBLE"
    
    results[label] = {
        'given_count': given_count,
        'pool_size': len(perms),
        'compatible_count': len(compatible),
        'status': status,
        'compatible_sample': [p['label'] for p in compatible[:5]]
    }

# 保存
output = {'results': results}
with open('D:/2026/WPF_Sudoku/Sudoku_256/compatibility_v2.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# 總結
print("\n" + "="*80)
print("總結")
print("="*80)

for label in labels:
    r = results.get(label, {})
    s = r.get('status', 'UNKNOWN')
    icon = {'FULLY_KNOWN':'🔬','SINGLE_COMPATIBLE':'🔍','MULTIPLE_COMPATIBLE':'🎯','NO_COMPATIBLE':'❌'}.get(s, '?')
    print(f"{icon} 行{label}: 已知{r.get('given_count',0)}, 池{r.get('pool_size',0)}, 相容{r.get('compatible_count',0)} [{s}]")
