#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分塊處理大檔案 - 記憶體友善"""

import openpyxl
import json
import time
import os

base_dir = r"D:\2026\WPF_Sudoku\Sudoku_256"

def extract_in_chunks(filepath, chunk_size=50000):
    """分塊讀取大檔案"""
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    
    all_perms = []
    count = 0
    chunk_perms = []
    
    for row in ws.iter_rows(min_row=1, min_col=5, max_col=20, values_only=True):
        vals = list(row)
        nums = [int(v) for v in vals if isinstance(v, (int, float)) and 1 <= v <= 16]
        
        if len(nums) == 16:
            chunk_perms.append(tuple(nums))
        elif len(nums) == 15:
            missing = [x for x in range(1, 17) if x not in nums]
            if len(missing) == 1:
                chunk_perms.append(tuple(nums + [missing[0]]))
        
        count += 1
        
        # 每50000行顯示進度
        if count % chunk_size == 0:
            print(f"  已處理 {count:,} 行 ({len(chunk_perms):,} 排列)...")
            if len(chunk_perms) >= 10000:
                # 儲存部分結果並清空記憶體
                all_perms.extend(chunk_perms[:10000])
                chunk_perms = chunk_perms[10000:]
    
    # 添加剩餘
    all_perms.extend(chunk_perms)
    wb.close()
    
    return all_perms

# 先處理A3
print("=" * 60)
print("處理 A3 (407,669 行)...")
print("=" * 60)

filepath = os.path.join(base_dir, "A3第三行符闔排列.xlsx")
start = time.time()

perms = extract_in_chunks(filepath, chunk_size=100000)
elapsed = time.time() - start

print(f"\n✓ A3 完成: {len(perms):,} 排列 ({elapsed:.1f}s)")

# 保存
with open("A3_permutations.json", "w", encoding="utf-8") as f:
    json.dump([list(v) for v in perms], f, ensure_ascii=False)

print(f"💾 已儲存至 A3_permutations.json ({os.path.getsize('A3_permutations.json')/(1024*1024):.1f} MB)")

# 驗證
if len(perms) == 407669:
    print("✅ 排列數匹配!")
else:
    print(f"⚠️ 期望 407,669，實際 {len(perms):,}")
