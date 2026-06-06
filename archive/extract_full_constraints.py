#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
超級大數獨 16行完整約束提取
16×16, box_size=4
E-T列 (第5-20列) = 16列數獨區域

特殊處理：
- 某些行的S列或R列是ArrayFormula，需要補齊缺失的數字
"""

import os
import openpyxl
import json
import time

base_dir = r"D:\2026\WPF_Sudoku\Sudoku_256"

# 每行的預期資料行數（Excel行數）
EXPECTED_ROWS = {
    1: 8731, 2: 902, 3: 407669, 4: 1980, 5: 633271,
    6: 359, 7: 2356, 8: 4782, 9: 164, 10: 28984,
    11: 2972, 12: 620, 13: 484, 14: 10668, 15: 5990, 16: 1562
}

# 排序：先小檔案，再大檔案
ORDER = [9, 6, 2, 4, 12, 13, 16, 7, 8, 11, 1, 10, 15, 14, 3, 5]

def extract_permutations(filepath, row_idx):
    """提取單行排列 - 處理ArrayFormula"""
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    
    permutations = []
    
    for i, row in enumerate(ws.iter_rows(min_row=1, min_col=5, max_col=20, values_only=True), 1):
        vals = list(row)  # 16個值 (E-T列)
        
        # 分離數值和ArrayFormula位置
        numeric_values = []
        array_positions = []  # 儲存ArrayFormula的位置(0-15)
        
        for j, v in enumerate(vals):
            if isinstance(v, (int, float)) and 1 <= v <= 16:
                numeric_values.append(int(v))
            elif hasattr(v, '__class__') and 'ArrayFormula' in str(v.__class__):
                array_positions.append(j)
        
        # 情況1：16個完整數值
        if len(numeric_values) == 16:
            if len(set(numeric_values)) == 16:
                permutations.append(tuple(numeric_values))
        
        # 情況2：15個數值 + 1個ArrayFormula位置
        elif len(numeric_values) == 15:
            # 從15個數值中找出缺失的第16個數字
            present = set(numeric_values)
            missing = [x for x in range(1, 17) if x not in present]
            if len(missing) == 1:
                # 插入到ArrayFormula的位置
                perm = numeric_values.copy()
                # 在ArrayFormula位置插入缺失值
                array_pos = array_positions[0] if array_positions else 15
                perm.insert(array_pos, missing[0])
                permutations.append(tuple(perm))
        
        # 其他情況：記錄但未處理
        # if len(numeric_values) < 15:
        #     print(f"  警告：行{i} 只有{len(numeric_values)}個數值")
    
    wb.close()
    return permutations


def main():
    print("=" * 70)
    print("🚀 超級大數獨深度求解")
    print("   16×16, box_size=4")
    print("   E-T列(第5-20列) = 16列數獨區域")
    print("   處理ArrayFormula自動補齊缺失數字")
    print("=" * 70)
    
    total_start = time.time()
    all_constraints = {}
    total_excel_rows = 0
    
    for row_idx in ORDER:
        expected_rows = EXPECTED_ROWS[row_idx]
        
        matching = [f for f in os.listdir(base_dir) 
                   if f.startswith(f"A{row_idx}") and "符闔" in f and f.endswith(".xlsx")]
        
        if not matching:
            print(f"✗ 行 {row_idx:2d}: 檔案未找到")
            all_constraints[row_idx] = []
            continue
        
        filename = matching[0]
        filepath = os.path.join(base_dir, filename)
        file_size = os.path.getsize(filepath) / (1024*1024)
        
        print(f"\n📄 提取 A{row_idx}: {expected_rows:,} 行 ({file_size:.1f} MB)...")
        
        try:
            start = time.time()
            perms = extract_permutations(filepath, row_idx)
            elapsed = time.time() - start
            
            all_constraints[row_idx] = perms
            total_excel_rows += expected_rows
            
            if len(perms) == expected_rows:
                print(f"✓ A{row_idx}: {len(perms):6,} 排列 ({elapsed:.1f}s) ✓")
            elif len(perms) > expected_rows:
                print(f"⚠ A{row_idx}: {len(perms):6,} 排列 ({elapsed:.1f}s) 超出期望 {expected_rows:,}")
            else:
                print(f"⚠ A{row_idx}: {len(perms):6,} 排列 ({elapsed:.1f}s) 少於期望 {expected_rows:,}")
                
        except Exception as e:
            print(f"✗ A{row_idx}: 錯誤 - {str(e)[:60]}")
            all_constraints[row_idx] = []
        
        # 每處理完2-3個檔案儲存一次進度
        if row_idx in [8, 14, 5]:
            partial = {
                "row_constraints": {str(k): [list(v) for v in p] for k, p in all_constraints.items()},
                "progress": f"Completed up to row {row_idx}",
                "total_patterns": sum(len(v) for v in all_constraints.values()),
                "per_row": {k: len(v) for k, v in all_constraints.items()}
            }
            with open("完整16行約束_進度.json", "w", encoding="utf-8") as f:
                json.dump(partial, f, ensure_ascii=False, indent=2)
            print(f"💾 進度已儲存 (已處理 {partial['total_patterns']:,} 排列)")
    
    total = sum(len(v) for v in all_constraints.values())
    total_elapsed = time.time() - total_start
    
    # 統計
    print("\n" + "=" * 70)
    print("📊 約束統計")
    print("=" * 70)
    print(f"{'行':4s} {'Excel行數':>10s} {'排列數':>10s} {'狀態':>8s}")
    print("-" * 50)
    
    all_match = True
    for row_idx in range(1, 17):
        actual = len(all_constraints.get(row_idx, []))
        expected = EXPECTED_ROWS[row_idx]
        status = "✓" if actual == expected else ("⚠" if actual > 0 else "✗")
        if actual != expected:
            all_match = False
        print(f"{row_idx:4d} {expected:10,} {actual:10,} {status:>8s}")
    
    print("-" * 50)
    print(f"{'總計':4s} {total_excel_rows:10,} {total:10,}")
    print(f"\n總提取時間: {total_elapsed:.1f} 秒")
    
    if all_match:
        print("\n✅ 所有16行約束數據完美匹配！")
    elif total == 1111494:
        print("\n✅ 總排列數匹配！")
    else:
        print(f"\n⚠️ 總計 {total:,} 排列，期望 {sum(EXPECTED_ROWS.values()):,}")
    
    # 儲存完整約束
    output = {
        "row_constraints": {str(k): [list(v) for v in p] for k, p in all_constraints.items()},
        "statistics": {
            "total_patterns": total,
            "total_excel_rows": total_excel_rows,
            "per_row": {k: len(v) for k, v in all_constraints.items()},
            "expected_rows": EXPECTED_ROWS,
            "match_all": all_match
        }
    }
    
    with open("完整16行約束.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 完整約束資料已儲存至 完整16行約束.json")
    
    return all_constraints


if __name__ == "__main__":
    main()
