#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""處理 A5 (633,271 行)"""

import openpyxl
import json
import time
import os

base_dir = r"D:\2026\WPF_Sudoku\Sudoku_256"

filepath = os.path.join(base_dir, "A5第五行符闔排列.xlsx")
print(f"處理 A5: {filepath}")
print(f"期望: 633,271 排列")
print("=" * 60)

wb = openpyxl.load_workbook(filepath, read_only=True)
ws = wb.active

perms = []
count = 0
start = time.time()

for row in ws.iter_rows(min_row=1, min_col=5, max_col=20, values_only=True):
    vals = list(row)
    nums = [int(v) for v in vals if isinstance(v, (int, float)) and 1 <= v <= 16]
    
    if len(nums) == 16:
        perms.append(tuple(nums))
    elif len(nums) == 15:
        missing = [x for x in range(1, 17) if x not in nums]
        if len(missing) == 1:
            perms.append(tuple(nums + [missing[0]]))
    
    count += 1
    
    if count % 100000 == 0:
        elapsed = time.time() - start
        print(f"  已處理 {count:,} 行, {len(perms):,} 排列 ({elapsed:.1f}s)...")

wb.close()

elapsed = time.time() - start
print(f"\n✓ A5 完成: {len(perms):,} 排列 ({elapsed:.1f}s)")

# 儲存
with open("A5_permutations.json", "w", encoding="utf-8") as f:
    json.dump([list(v) for v in perms], f, ensure_ascii=False)

file_size = os.path.getsize("A5_permutations.json") / (1024*1024)
print(f"💾 已儲存 ({file_size:.1f} MB)")

if len(perms) == 633271:
    print("✅ 完美匹配!")
else:
    print(f"⚠️ 期望 633,271，實際 {len(perms):,}")
