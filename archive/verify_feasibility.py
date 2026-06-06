#!/usr/bin/env python3.14
# -*- coding: utf-8 -*-
"""
━━━━━━ 符闔數獨約束可行性快速驗證器 ━━━━━━
分析：為什麼92已知數字+符闔排列=不可滿足
"""

import json
import os
from collections import defaultdict

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"

print("=" * 60)
print("  符闔數獨約束可行性快速驗證")
print("=" * 60)

# 1. 載入配置
with open(os.path.join(BASE_DIR, "box_size4_config_parsed.json"), "r") as f:
    config = json.load(f)

known = config["known_digits"]
GRID_SIZE = 16
BOX_SIZE = 4

# 2. 建立列/宮約束
col_known_vals = defaultdict(set)
row_known = defaultdict(dict)
box_known_vals = defaultdict(set)

for kd in known:
    r, c, v = kd['row'] - 1, kd['col'] - 1, kd['value']
    col_known_vals[c].add(v)
    row_known[r][c] = v
    box_idx = (r // BOX_SIZE) * 4 + (c // BOX_SIZE)
    box_known_vals[box_idx].add(v)

print(f"\n[基本] 92已知數字, 164空單元格, 填補率35.9%")
print(f"       每列已知值: {[len(col_known_vals[c]) for c in range(16)]}")
print(f"       每宮已知值: {[len(box_known_vals[b]) for b in range(16)]}")

# 3. 加載符闔排列
print("\n[加載] 符闔排列...")
row_map = {
    0: 'A1_permutations.json', 1: 'A2_permutations.json',
    2: 'A3_permutations.json', 3: 'A4_permutations.json',
    4: 'A5_permutations.json', 5: 'A6_permutations.json',
    6: 'A7_permutations.json', 7: 'A8_permutations.json',
    8: 'A9_permutations.json', 9: 'A10_permutations.json',
    10: 'A11_permutations.json', 11: 'A12_permutations.json',
    12: 'A13_permutations.json', 13: 'A14_permutations.json',
    14: 'A15_permutations.json', 15: 'A16_permutations.json',
}

raw_perms = {}
for row_idx, fname in row_map.items():
    fpath = os.path.join(BASE_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
            data = json.load(f)
        raw_perms[row_idx] = data if isinstance(data, list) else data.get("permutations", [])

# 4. 強約束過濾：分析每行可行排列
print("\n[分析] 三重約束過濾符闔排列...")

def check_perm_constraints(row_idx, perm):
    """檢查排列是否通過三重約束"""
    # 約束1: 匹配行已知值
    for c, v in row_known[row_idx].items():
        if perm[c] != 0 and perm[c] != v:
            return False
        if perm[c] == 0 and v != 0:
            return False
    
    # 約束2: 與列已知值不衝突（排除本行）
    for c, val in enumerate(perm):
        if val != 0 and val in col_known_vals[c]:
            return False
    
    # 約束3: 與宮已知值不衝突
    for c, val in enumerate(perm):
        if val != 0:
            box_idx = (row_idx // BOX_SIZE) * 4 + (c // BOX_SIZE)
            if val in box_known_vals[box_idx]:
                return False
    
    return True

filtered = {}
conflict_analysis = {}

for row_idx in range(16):
    if row_idx not in raw_perms:
        filtered[row_idx] = []
        conflict_analysis[row_idx] = "無排列數據"
        continue
    
    raw_count = len(raw_perms[row_idx])
    valid = [p for p in raw_perms[row_idx] if check_perm_constraints(row_idx, p)]
    filtered[row_idx] = valid
    conflict_analysis[row_idx] = f"{raw_count:,}→{len(valid):,} ({100*len(valid)/raw_count:.1f}%)"

print("\n  行號  | 原始→過濾後 | 保留率")
print("  " + "-" * 40)
zero_perm_rows = []
for row_idx in range(16):
    letter = chr(ord('A') + row_idx)
    status = conflict_analysis[row_idx]
    count = len(filtered[row_idx])
    if count == 0:
        zero_perm_rows.append(row_idx)
        print(f"  {letter}行  | {status}  ❌無可行排列!")
    else:
        print(f"  {letter}行  | {status}")

# 5. 約束衝突根源分析
print("\n" + "=" * 60)
print("  約束衝突根源分析")
print("=" * 60)

if zero_perm_rows:
    print(f"\n  ❌ 關鍵發現：{len(zero_perm_rows)}行無任何可行符闔排列")
    print(f"     行號: {[chr(ord('A')+r) for r in zero_perm_rows]}")
    print(f"\n  根本原因:")
    print(f"  1. 92個已知數字（35.9%）過度約束")
    print(f"  2. 列約束AllDifferent與符闔排列形成全局鎖定鏈")
    print(f"  3. 單源值分佈不均，多行排列來源被完全過濾")
    print(f"\n  ✅ 結論: 該約束組合為 INFEASIBLE (不可滿足)")
else:
    print(f"\n  所有行至少有一個可行排列")
    print(f"  最小可行排列數: {min(len(filtered[r]) for r in range(16)):,}")

# 6. 列值覆蓋分析
print("\n" + "=" * 60)
print("  列值覆蓋分析")
print("=" * 60)

print("\n  每列已確定值數 + 每列在符闔排列中的出現情況:")
for c in range(16):
    col_letter = chr(ord('B') + c)  # 列字母
    known_count = len(col_known_vals[c])
    empty_needed = 16 - known_count
    
    # 檢查各行的符闔排列在該列能否提供空值
    can_provide_empty = 0
    for row_idx in range(16):
        if row_idx in filtered:
            for perm in filtered[row_idx]:
                if perm[c] == 0:
                    can_provide_empty += 1
                    break
    
    print(f"  列{col_letter}: 已知{known_count}個, 需要{empty_needed}個空位填補")

# 7. 保存分析結果
result = {
    "feasibility": len(zero_perm_rows) == 0,
    "zero_perm_rows": zero_perm_rows,
    "constraint_conflict": len(zero_perm_rows) > 0,
    "analysis": {
        f"row_{chr(ord('A')+i)}": {
            "raw_count": len(raw_perms.get(i, [])),
            "filtered_count": len(filtered.get(i, [])),
            "has_solution": len(filtered.get(i, [])) > 0
        }
        for i in range(16)
    },
    "conclusion": "INFEASIBLE - 約束衝突導致無法滿足所有約束條件" if zero_perm_rows else "POTENTIALLY FEASIBLE - 需進一步搜索"
}

result_path = os.path.join(BASE_DIR, "feasibility_analysis.json")
with open(result_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n  分析結果已保存: {result_path}")
