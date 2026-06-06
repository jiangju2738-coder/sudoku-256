#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
超級大數獨 16行完整約束提取 - 分段處理版
16×16, box_size=4
A列 = 行號標識, E-T列(第5-20列) = 16列數獨區域
"""

import os
import openpyxl
import json
import time

base_dir = r"D:\2026\WPF_Sudoku\Sudoku_256"

# 每行的預期數據行數
EXPECTED = {
    1: 8731, 2: 902, 3: 407669, 4: 1980, 5: 633271,
    6: 359, 7: 2356, 8: 4782, 9: 164, 10: 28984,
    11: 2972, 12: 620, 13: 484, 14: 10668, 15: 5990, 16: 1562
}

# 排序：先小檔案，再大檔案
ORDER = [6, 9, 2, 4, 12, 13, 16, 7, 8, 11, 1, 10, 15, 14, 3, 5]

def extract_permutations_fast(filepath, row_idx):
    """快速提取單行16列排列 - 直接讀取E-T列"""
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    
    permutations = []
    
    for row in ws.iter_rows(min_row=1, min_col=5, max_col=20, values_only=True):
        # row包含E-T列(16個值)
        values = []
        for v in row:
            if isinstance(v, (int, float)) and 1 <= v <= 16:
                values.append(int(v))
        
        if len(values) == 16:
            if len(set(values)) == 16:
                permutations.append(tuple(values))
        elif len(values) == 15:
            # 補齊缺失數字
            present = set(values)
            missing = [x for x in range(1, 17) if x not in present]
            if len(missing) == 1:
                permutations.append(tuple(values + [missing[0]]))
    
    wb.close()
    return permutations


def main():
    print("=" * 70)
    print("🚀 超級大數獨深度求解 - 分段處理版")
    print("   16×16, box_size=4")
    print("   A列 = 行號標識, E-T列(第5-20列) = 16列數獨區域")
    print("=" * 70)
    
    total_start = time.time()
    all_constraints = {}
    
    for row_idx in ORDER:
        expected = EXPECTED[row_idx]
        
        matching = [f for f in os.listdir(base_dir) 
                   if f.startswith(f"A{row_idx}") and "符闔" in f and f.endswith(".xlsx")]
        
        if not matching:
            print(f"✗ 行 {row_idx:2d}: 檔案未找到")
            all_constraints[row_idx] = []
            continue
        
        filename = matching[0]
        filepath = os.path.join(base_dir, filename)
        
        print(f"\n📄 提取 A{row_idx}: 預期 {expected:,} 行 ({os.path.getsize(filepath)/(1024*1024):.1f} MB)...")
        
        try:
            start = time.time()
            perms = extract_permutations_fast(filepath, row_idx)
            elapsed = time.time() - start
            
            all_constraints[row_idx] = perms
            
            if len(perms) == expected:
                print(f"✓ A{row_idx}: {len(perms):6,} 排列 ({elapsed:.1f}s) 完全匹配")
            else:
                print(f"⚠ A{row_idx}: {len(perms):6,} 排列 ({elapsed:.1f}s) 期望 {expected:,}")
                
        except Exception as e:
            print(f"✗ A{row_idx}: 錯誤 - {str(e)[:60]}")
            all_constraints[row_idx] = []
        
        # 每處理完一個檔案，儲存一次進度
        if row_idx in [5, 10]:
            partial_output = {
                "row_constraints": {str(k): [list(v) for v in p] for k, p in all_constraints.items()},
                "progress": f"Completed row {row_idx}",
                "statistics": {
                    "total_patterns": sum(len(v) for v in all_constraints.values()),
                    "per_row": {k: len(v) for k, v in all_constraints.items()}
                }
            }
            with open("完整16行約束_進度.json", "w", encoding="utf-8") as f:
                json.dump(partial_output, f, ensure_ascii=False, indent=2)
            print(f"💾 進度已儲存")
    
    total = sum(len(v) for v in all_constraints.values())
    total_elapsed = time.time() - total_start
    
    print("\n" + "=" * 70)
    print("📊 約束統計")
    print("=" * 70)
    print(f"{'行':4s} {'提取數':>10s} {'期望數':>10s} {'狀態':>8s}")
    print("-" * 50)
    
    all_match = True
    for row_idx in range(1, 17):
        actual = len(all_constraints.get(row_idx, []))
        expected = EXPECTED[row_idx]
        status = "✓" if actual == expected else "✗"
        if actual != expected:
            all_match = False
        print(f"{row_idx:4d} {actual:10,} {expected:10,} {status:>8s}")
    
    print("-" * 50)
    print(f"{'總計':4s} {total:10,} {sum(EXPECTED.values()):10,}")
    print(f"\n總提取時間: {total_elapsed:.1f} 秒")
    
    if all_match:
        print("\n✅ 所有16行約束數據完美匹配！")
    else:
        print("\n⚠️ 部分行的數據有差異")
    
    # 儲存完整約束
    output = {
        "row_constraints": {str(k): [list(v) for v in p] for k, p in all_constraints.items()},
        "statistics": {
            "total_patterns": total,
            "per_row": {k: len(v) for k, v in all_constraints.items()},
            "expected": EXPECTED,
            "match_all": all_match
        }
    }
    
    with open("完整16行約束.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 完整約束資料已儲存至 完整16行約束.json")
    
    return all_constraints


if __name__ == "__main__":
    main()
