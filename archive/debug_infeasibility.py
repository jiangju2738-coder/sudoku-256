#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試增量約束不可滿足問題
"""

import json

# 載入數據
with open('solution_v4_final.json', 'r', encoding='utf-8') as f:
    solution = json.load(f)

with open('permutations_v4_final.json', 'r', encoding='utf-8') as f:
    permutations = json.load(f)

with open('puzzle_v4_final.json', 'r', encoding='utf-8') as f:
    puzzle = json.load(f)

print("=" * 80)
print("調試：為什麼添加符闔排列約束後變為 INFEASIBLE？")
print("=" * 80)

print(f"\n📊 數據統計:")
print(f"   解決方案: {len(solution)} 行")
print(f"   符闔排列: {len(permutations)} 個")
print(f"   謎題填滿: {sum(1 for row in puzzle for cell in row if cell != 0)}/256")

# 檢查solution的每一行是否在permutations中
print("\n🔍 檢查解決方案行是否在排列池中:")
solution_rows_set = set(tuple(row) for row in solution)
permutations_set = set(tuple(p) for p in permutations)

in_pool = solution_rows_set & permutations_set
not_in_pool = solution_rows_set - permutations_set

print(f"   在排列池中的行: {len(in_pool)}/16")
print(f"   不在排列池中的行: {len(not_in_pool)}/16")

if not_in_pool:
    print("\n   ❌ 發現不在池中的行:")
    for i, row in enumerate(solution):
        if tuple(row) in not_in_pool:
            print(f"      行{i+1}: {row}")

# 檢查謎題的已知數字是否與某個排列一致
print("\n🔍 檢查謎題已知數字與排列的一致性:")

for row_idx in range(16):
    puzzle_row = puzzle[row_idx]
    solution_row = solution[row_idx]
    
    # 找出謎題中非零的位置和值
    given_positions = [(j, puzzle_row[j]) for j in range(16) if puzzle_row[j] != 0]
    
    if not given_positions:
        continue
    
    # 檢查是否有排列在這些位置與謎題一致
    matching_perms = []
    for perm in permutations:
        match = True
        for j, val in given_positions:
            if perm[j] != val:
                match = False
                break
        if match:
            matching_perms.append(perm)
    
    if not matching_perms:
        print(f"   ❌ 行{row_idx+1}: {len(given_positions)}個已知數字，無匹配排列！")
        print(f"      謎題行: {puzzle_row}")
        print(f"      解行: {solution_row}")
    elif len(matching_perms) == 1:
        if tuple(matching_perms[0]) == tuple(solution_row):
            print(f"   ✅ 行{row_idx+1}: 唯一匹配 → 正確解")
        else:
            print(f"   ⚠️ 行{row_idx+1}: 唯一匹配但≠解行")
    else:
        print(f"   ℹ️ 行{row_idx+1}: {len(matching_perms)} 個匹配排列")

# 分析：為什麼INFEASIBLE？
print("\n" + "=" * 80)
print("💡 原因分析")
print("=" * 80)

# 計算每行的"自由度"
print("\n📊 每行與排列池的兼容性:")
for row_idx in range(16):
    puzzle_row = puzzle[row_idx]
    given_count = sum(1 for x in puzzle_row if x != 0)
    
    # 統計有多少排列與該行的已知數字一致
    matching_count = 0
    for perm in permutations:
        match = True
        for j in range(16):
            if puzzle_row[j] != 0 and perm[j] != puzzle_row[j]:
                match = False
                break
        if match:
            matching_count += 1
    
    compatibility = "✅ 高" if matching_count >= 10 else "⚠️ 中" if matching_count >= 1 else "❌ 無"
    print(f"   行{row_idx+1:2d}: 已知{given_count:2d}個 | 匹配{matching_count:4d}個排列 | {compatibility}")

print("\n🔬 關鍵發現:")
print("""
1. 謎題填滿率 82.4%（211個已知數字）過高
2. 每行平均約13個已知數字，限制 severely
3. 符闔排列池中的排列可能與謎題的已知數字不完全匹配
4. 即使原始 solution 是從合法 Sudoku 生成，謎題的已知數字組合可能"過濾掉"所有匹配排列

💡 解決方案：
   - 降低謎題填滿率至 40-60 個已知數字（25-35%）
   - 這樣每行約有 2-4 個已知數字，留有足夠自由度選擇排列
""")
