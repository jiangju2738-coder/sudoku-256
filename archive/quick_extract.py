#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速提取16行約束 - 直接處理E-T列"""

import openpyxl
import json
import time
import os

base_dir = r"D:\2026\WPF_Sudoku\Sudoku_256"

# 預期行數
EXPECTED = {
    1: 8731, 2: 902, 3: 407669, 4: 1980, 5: 633271,
    6: 359, 7: 2356, 8: 4782, 9: 164, 10: 28984,
    11: 2972, 12: 620, 13: 484, 14: 10668, 15: 5990, 16: 1562
}

def extract_simple(filepath):
    """快速提取：直接讀取E-T列的16個值"""
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    perms = []
    
    for row in ws.iter_rows(min_row=1, min_col=5, max_col=20, values_only=True):
        vals = list(row)
        # 收集1-16數值
        nums = [int(v) for v in vals if isinstance(v, (int, float)) and 1 <= v <= 16]
        
        if len(nums) == 16:
            perms.append(tuple(nums))
        elif len(nums) == 15:
            # 補齊缺失數字
            missing = [x for x in range(1, 17) if x not in nums]
            if len(missing) == 1:
                nums.append(missing[0])
                perms.append(tuple(nums))
    
    wb.close()
    return perms

# 先驗證已處理的檔案
existing = {}
for i in range(1, 17):
    matching = [f for f in os.listdir(base_dir) 
               if f.startswith(f"A{i}") and "符闔" in f and f.endswith(".xlsx")]
    if matching:
        existing[i] = matching[0]

print("📋 處理剩餘檔案：")
for i, fname in existing.items():
    if EXPECTED[i] in [407669, 633271]:
        print(f"  A{i}: {fname} ({EXPECTED[i]:,} 行) - 大檔案，將單獨處理")

print("\n🚀 開始提取...")
start = time.time()

constraints = {}
for i in [3, 5]:
    fname = existing.get(i)
    if not fname:
        continue
    filepath = os.path.join(base_dir, fname)
    print(f"\n處理 A{i}: {EXPECTED[i]:,} 行...")
    perms = extract_simple(filepath)
    constraints[i] = perms
    print(f"  提取 {len(perms):,} 排列")

elapsed = time.time() - start
print(f"\n總時間: {elapsed:.1f}秒")

# 保存結果
output = {
    "row3": [list(v) for v in constraints.get(3, [])],
    "row5": [list(v) for v in constraints.get(5, [])],
    "count_3": len(constraints.get(3, [])),
    "count_5": len(constraints.get(5, []))
}

with open("大檔案處理結果.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\n✅ 結果已儲存至 大檔案處理結果.json")
