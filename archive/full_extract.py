#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
超級大數獨 16行完整約束提取
16×16, box_size=4, 總排列數: 1,111,494
"""

import os
import openpyxl
import json
import time
from collections import defaultdict

base_dir = r"D:\2026\WPF_Sudoku\Sudoku_256"

# 每行的列提取方式
ROW_TYPES = {
    1: "normal",      # 列5-19 (indices 4-18)
    2: "normal",
    3: "normal",
    4: "normal",
    5: "normal",
    6: "special_6",   # 列5-18 (indices 4-17) + 列20 (index 19)
    7: "normal",
    8: "normal",
    9: "normal",
    10: "normal",
    11: "normal",
    12: "special_12", # 列5-18 + 列20
    13: "special_13", # 列5-18 + 列20
    14: "normal",
    15: "normal",
    16: "special_16", # 列5-17 + 列19 + 列20
}

EXPECTED_COUNTS = {
    1: 8731, 2: 902, 3: 407669, 4: 1980, 5: 633271,
    6: 359, 7: 2356, 8: 4782, 9: 164, 10: 28984,
    11: 2972, 12: 620, 13: 484, 14: 10668, 15: 5990, 16: 1562
}

def extract_row_permutations(filepath, row_idx):
    """提取單行排列"""
    row_type = ROW_TYPES[row_idx]
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    
    permutations = []
    count = 0
    
    for row in ws.iter_rows(min_row=1, values_only=True):
        values = []
        
        if row_type == "normal":
            # 列5-19 (Python indices 4-18)
            for i in range(4, 19):
                if i < len(row):
                    v = row[i]
                    if isinstance(v, (int, float)) and 1 <= v <= 16:
                        values.append(int(v))
        
        elif row_type == "special_6":
            # 列5-18 (4-17) + 列20 (19)
            for i in range(4, 18):
                if i < len(row):
                    v = row[i]
                    if isinstance(v, (int, float)) and 1 <= v <= 16:
                        values.append(int(v))
            if 19 < len(row):
                v = row[19]
                if isinstance(v, (int, float)) and 1 <= v <= 16:
                    values.append(int(v))
        
        elif row_type == "special_12":
            for i in range(4, 18):
                if i < len(row):
                    v = row[i]
                    if isinstance(v, (int, float)) and 1 <= v <= 16:
                        values.append(int(v))
            if 19 < len(row):
                v = row[19]
                if isinstance(v, (int, float)) and 1 <= v <= 16:
                    values.append(int(v))
        
        elif row_type == "special_13":
            for i in range(4, 18):
                if i < len(row):
                    v = row[i]
                    if isinstance(v, (int, float)) and 1 <= v <= 16:
                        values.append(int(v))
            if 19 < len(row):
                v = row[19]
                if isinstance(v, (int, float)) and 1 <= v <= 16:
                    values.append(int(v))
        
        elif row_type == "special_16":
            # 列5-17 (4-16) + 列19 (18) + 列20 (19)
            for i in range(4, 17):
                if i < len(row):
                    v = row[i]
                    if isinstance(v, (int, float)) and 1 <= v <= 16:
                        values.append(int(v))
            if 18 < len(row):
                v = row[18]
                if isinstance(v, (int, float)) and 1 <= v <= 16:
                    values.append(int(v))
            if 19 < len(row):
                v = row[19]
                if isinstance(v, (int, float)) and 1 <= v <= 16:
                    values.append(int(v))
        
        # 驗證排列
        if len(values) == 16:
            if len(set(values)) == 16:
                permutations.append(tuple(values))
        elif len(values) == 15:
            # 補齊缺失數字
            present = set(values)
            missing = [x for x in range(1, 17) if x not in present]
            if len(missing) == 1:
                permutations.append(tuple(values + [missing[0]]))
        
        count += 1
        if count % 100000 == 0:
            print(f"  已處理 {count:,} 行...")
    
    wb.close()
    return permutations


def main():
    print("=" * 70)
    print("🚀 超級大數獨深度求解 - 16行完整約束提取")
    print("   16×16, box_size=4")
    print("   預期總排列數: 1,111,494")
    print("=" * 70)
    
    start_time = time.time()
    constraints = {}
    
    for row_idx in range(1, 17):
        # 尋找檔案
        matching = [f for f in os.listdir(base_dir) 
                   if f.startswith(f"A{row_idx}") and "符闔" in f and f.endswith(".xlsx")]
        
        if not matching:
            print(f"✗ 行 {row_idx:2d}: 檔案未找到")
            constraints[row_idx] = []
            continue
        
        filename = matching[0]
        filepath = os.path.join(base_dir, filename)
        expected = EXPECTED_COUNTS[row_idx]
        
        print(f"\n📄 提取 A{row_idx}: {filename} (預期 {expected:,} 行)...")
        
        try:
            perms = extract_row_permutations(filepath, row_idx)
            constraints[row_idx] = perms
            print(f"✓ A{row_idx}: 提取 {len(perms):,} 個排列 (期望 {expected:,})")
        except Exception as e:
            print(f"✗ A{row_idx}: 錯誤 - {e}")
            constraints[row_idx] = []
    
    total = sum(len(v) for v in constraints.values())
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("📊 約束提取完成")
    print("=" * 70)
    print(f"{'行':4s} {'提取數':>10s} {'期望數':>10s} {'匹配':>8s}")
    print("-" * 50)
    
    for row_idx in range(1, 17):
        actual = len(constraints.get(row_idx, []))
        expected = EXPECTED_COUNTS[row_idx]
        match = "✓" if actual == expected else "✗"
        print(f"{row_idx:4d} {actual:10,} {expected:10,} {match:>8s}")
    
    print("-" * 50)
    print(f"{'總計':4s} {total:10,} {sum(EXPECTED_COUNTS.values()):10,}")
    print(f"\n提取時間: {elapsed:.1f} 秒")
    
    # 儲存
    output = {
        "row_constraints": {str(k): [list(v) for v in p] for k, p in constraints.items()},
        "statistics": {
            "total_patterns": total,
            "per_row": {k: len(v) for k, v in constraints.items()},
            "expected_counts": EXPECTED_COUNTS
        }
    }
    
    with open("完整16行約束.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 完整約束資料已儲存至 完整16行約束.json")
    
    return constraints


if __name__ == "__main__":
    main()
