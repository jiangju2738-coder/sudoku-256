#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
超級大數獨 16行完整約束提取
16×16, box_size=4
A列 = 行號標識 (第幾行的約束數據)
E-T列 (索引4-19) = 16列數獨區域
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

def extract_permutations(filepath, row_idx):
    """提取單行16列排列 (從E-T列提取)"""
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    
    permutations = []
    count = 0
    
    for row in ws.iter_rows(min_row=1, values_only=True):
        vals = list(row)
        
        # 從E-T列 (索引4-19) 提取1-16的數值
        values = []
        for i in range(4, 20):  # E=4, T=19
            if i < len(vals):
                v = vals[i]
                if isinstance(v, (int, float)) and 1 <= v <= 16:
                    values.append(int(v))
        
        # 如果E-T列有16個有效數字 → 直接作為排列
        if len(values) == 16:
            if len(set(values)) == 16:
                permutations.append(tuple(values))
        
        # 如果E-T列有15個數字 → 自動補齊缺失的第16個數字
        elif len(values) == 15:
            present = set(values)
            missing = [x for x in range(1, 17) if x not in present]
            if len(missing) == 1:
                # 補上缺失的數字 (放在最後)
                perm = tuple(values + [missing[0]])
                permutations.append(perm)
        
        count += 1
        if count % 100000 == 0 and count > 0:
            print(f"  已處理 {count:,} 行... (找到 {len(permutations):,} 排列)")
    
    wb.close()
    return permutations


def main():
    print("=" * 70)
    print("🚀 超級大數獨深度求解")
    print("   16×16, box_size=4")
    print("   A列 = 行號標識, E-T列(第5-20列) = 16列數獨區域")
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
        expected = EXPECTED[row_idx]
        
        print(f"\n📄 提取 A{row_idx}: 預期 {expected:,} 行...")
        
        try:
            perms = extract_permutations(filepath, row_idx)
            constraints[row_idx] = perms
            
            if len(perms) == expected:
                print(f"✓ A{row_idx}: {len(perms):6,} 排列 (完全匹配)")
            else:
                print(f"⚠ A{row_idx}: {len(perms):6,} 排列 (期望 {expected:,})")
                
        except Exception as e:
            print(f"✗ A{row_idx}: 錯誤 - {e}")
            constraints[row_idx] = []
    
    total = sum(len(v) for v in constraints.values())
    elapsed = time.time() - start_time
    
    # 統計結果
    print("\n" + "=" * 70)
    print("📊 約束統計")
    print("=" * 70)
    print(f"{'行':4s} {'提取數':>10s} {'期望數':>10s} {'狀態':>8s}")
    print("-" * 50)
    
    all_match = True
    for row_idx in range(1, 17):
        actual = len(constraints.get(row_idx, []))
        expected = EXPECTED[row_idx]
        status = "✓" if actual == expected else "✗"
        if actual != expected:
            all_match = False
        print(f"{row_idx:4d} {actual:10,} {expected:10,} {status:>8s}")
    
    print("-" * 50)
    print(f"{'總計':4s} {total:10,} {sum(EXPECTED.values()):10,}")
    print(f"\n提取時間: {elapsed:.1f} 秒")
    
    if all_match:
        print("\n✅ 所有16行約束數據完美匹配！")
    else:
        print("\n⚠️ 部分行的數據有差異")
    
    # 儲存完整約束
    output = {
        "row_constraints": {str(k): [list(v) for v in p] for k, p in constraints.items()},
        "statistics": {
            "total_patterns": total,
            "per_row": {k: len(v) for k, v in constraints.items()},
            "expected": EXPECTED,
            "match_all": all_match
        }
    }
    
    with open("完整16行約束.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 完整約束資料已儲存至 完整16行約束.json")
    
    return constraints


if __name__ == "__main__":
    main()
