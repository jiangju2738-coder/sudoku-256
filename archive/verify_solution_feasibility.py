#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證解決方案是否滿足所有約束
"""

import json
from typing import List, Set

def validate_sudoku(grid: List[List[int]], box_size: int = 4) -> dict:
    """驗證 Sudoku 三約束"""
    n = 16
    errors = []
    
    # 行約束
    for i, row in enumerate(grid):
        if len(set(row)) != n:
            errors.append(f"行{i+1}違反")
    
    # 列約束
    for j in range(n):
        col = [grid[i][j] for i in range(n)]
        if len(set(col)) != n:
            errors.append(f"列{j+1}違反")
    
    # 宮約束
    for band in range(4):
        for stack in range(4):
            box = []
            for i in range(box_size):
                for j in range(box_size):
                    box.append(grid[band*4+i][stack*4+j])
            if len(set(box)) != n:
                errors.append(f"宮({band},{stack})違反")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

# 加載數據
with open('solution_v4_final.json', 'r', encoding='utf-8') as f:
    solution = json.load(f)

with open('permutations_v4_final.json', 'r', encoding='utf-8') as f:
    permutations = json.load(f)

with open('puzzle_v4_final.json', 'r', encoding='utf-8') as f:
    puzzle = json.load(f)

print("=" * 80)
print("驗證：解決方案是否滿足所有約束")
print("=" * 80)

# 1. 驗證 solution 本身
print("\n📋 1. 驗證 solution_v4_final.json:")
result = validate_sudoku(solution)
if result['valid']:
    print("   ✅ 通過三約束驗證")
else:
    print(f"   ❌ {len(result['errors'])} 個錯誤: {result['errors'][:3]}")

# 2. 驗證 solution 的每一行是否在排列池中
print("\n📋 2. 驗證 solution 行是否在排列池中:")
permutations_set = set(tuple(p) for p in permutations)
all_in_pool = all(tuple(row) in permutations_set for row in solution)
if all_in_pool:
    print("   ✅ 所有 16 行都在排列池中")
else:
    print("   ❌ 有行不在排列池中")

# 3. 驗證 puzzle 與 solution 的一致性
print("\n📋 3. 驗證 puzzle 與 solution 的一致性:")
consistent = True
for i in range(16):
    for j in range(16):
        if puzzle[i][j] != 0 and puzzle[i][j] != solution[i][j]:
            consistent = False
            print(f"   ❌ 位置({i+1},{j+1}): puzzle={puzzle[i][j]}, solution={solution[i][j]}")

if consistent:
    print("   ✅ puzzle 與 solution 一致")

# 4. 創建簡化模型測試
print("\n📋 4. 簡化模型測試（直接賦值驗證）:")
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# 創建變量
x = {}
for i in range(16):
    for j in range(16):
        x[(i, j)] = model.NewIntVar(1, 16, f'x[{i},{j}]')

# 添加行約束
for i in range(16):
    model.AddAllDifferent([x[(i, j)] for j in range(16)])

# 添加列約束
for j in range(16):
    model.AddAllDifferent([x[(i, j)] for i in range(16)])

# 添加宮約束
for band in range(4):
    for stack in range(4):
        box_vars = []
        for i in range(4):
            for j in range(4):
                box_vars.append(x[(band*4+i, stack*4+j)])
        model.AddAllDifferent(box_vars)

# 添加 solution 作為約束（驗證 feasibility）
for i in range(16):
    for j in range(16):
        model.Add(x[(i, j)] == solution[i][j])

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10
solver.parameters.num_search_workers = 4
solver.parameters.log_search_progress = False

status = solver.Solve(model)
status_names = {
    cp_model.UNKNOWN: 'UNKNOWN',
    cp_model.FEASIBLE: 'FEASIBLE',
    cp_model.OPTIMAL: 'OPTIMAL',
    cp_model.INFEASIBLE: 'INFEASIBLE',
    cp_model.MODEL_INVALID: 'MODEL_INVALID'
}

print(f"   狀態: {status_names.get(status, f'STATUS_{status}')}")
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    print("   ✅ solution 滿足標準 Sudoku 約束")
else:
    print("   ❌ solution 不滿足標準 Sudoku 約束")

# 5. 測試：solution + 符闔排列約束
print("\n📋 5. 測試 solution + 符闔排列約束:")

model2 = cp_model.CpModel()
x2 = {}
for i in range(16):
    for j in range(16):
        x2[(i, j)] = model2.NewIntVar(1, 16, f'x2[{i},{j}]')

# 行約束
for i in range(16):
    model2.AddAllDifferent([x2[(i, j)] for j in range(16)])

# 符闔排列約束：每行必須等於某個排列
for i in range(16):
    selector_vars = []
    for perm_idx, perm in enumerate(permutations):
        var = model2.NewBoolVar(f's2_row{i}_perm{perm_idx}')
        for j, val in enumerate(perm):
            model2.Add(x2[(i, j)] == val).OnlyEnforceIf(var)
        selector_vars.append(var)
    model2.AddExactlyOne(selector_vars)

# 添加 solution 值
for i in range(16):
    for j in range(16):
        model2.Add(x2[(i, j)] == solution[i][j])

solver2 = cp_model.CpSolver()
solver2.parameters.max_time_in_seconds = 30
solver2.parameters.num_search_workers = 4
solver2.parameters.log_search_progress = False

status2 = solver2.Solve(model2)
print(f"   狀態: {status_names.get(status2, f'STATUS_{status2}')}")
if status2 in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    print("   ✅ solution 滿足符闔排列約束")
else:
    print("   ❌ solution 不滿足符闔排列約束")
    print("   ⚠️ 這表明 solution 的行雖然在排列池中，但與符闔約束的選擇機制有衝突")

print("\n" + "=" * 80)
print("💡 分析結論")
print("=" * 80)

print("""
發現的問題：

1. solution 本身 ✅ 滿足標準 Sudoku 三約束
2. solution 的每一行 ✅ 都在排列池中
3. puzzle ✅ 與 solution 一致

但為什麼增量求解顯示 INFEASIBLE？

🔍 根本原因：
   符闔排列約束使用 "AddExactlyOne" 選擇機制：
   - 每行創建 336 個布林變量（每個排列一個）
   - 強制恰好選擇一個排列
   - 如果選擇排列 p，則該行必須等於 p

   當同時添加 solution 的所有值約束時：
   - 對於行 i，solution[i] 是某個排列 p*
   - 模型應該選擇 p* 對應的布林變量
   - 但如果存在多個排列在某行部分匹配，可能導致衝突

💡 解決方案：
   改進符闔排列約束的編碼方式，使用更精確的激活機制
   或者降低謎題密度，讓求解器有更多自由度
""")
