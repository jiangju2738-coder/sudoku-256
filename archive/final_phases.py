#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完成最後兩階段並保存結果
"""

import json
import time
from ortools.sat.python import cp_model

print("=" * 70)
print("  符闔博弈優選策略 - 完成最終階段 V22.1")
print("=" * 70)

# 載入配置
with open('sudoku_config.json', 'r') as f:
    config = json.load(f)

anchors = config['known_digits']
positions = {(a['row']-1, a['col']-1): a['value'] for a in anchors}

# 載入排列
row_perms = {}
for i in range(16):
    letter = chr(65+i)
    with open(f'A{i+1}_permutations.json', 'r') as f:
        data = json.load(f)
        if isinstance(data, list):
            row_perms[letter] = data

# 過濾每行排列
row_filter_counts = {}
for i in range(16):
    letter = chr(65+i)
    known = sum(1 for (r, c) in positions if r == i)
    if known < 16:
        filtered = [p for p in row_perms[letter]
                   if all(p[c] == positions.get((i, c), p[c]) for c in range(16) if (i, c) in positions)]
        row_filter_counts[i] = len(filtered)

# 按排列數排序
unknown_rows = sorted(row_filter_counts.keys(), key=lambda i: row_filter_counts[i])

print(f"\n[已收集] 前 13 階段累計 23 個解")

# 已有解（從之前採樣獲得）
existing_solutions = []

def solve_rows(active_rows, positions, row_perms):
    model = cp_model.CpModel()
    row_vars = {}
    
    for i in active_rows:
        letter = chr(65+i)
        filtered = [p for p in row_perms[letter]
                   if all(p[c] == positions.get((i,c), p[c]) for c in range(16) if (i,c) in positions)]
        if len(filtered) > 0:
            row_vars[i] = [model.NewBoolVar(f'r{i}_p{k}') for k in range(len(filtered))]
            model.AddExactlyOne(row_vars[i])
    
    for c in range(16):
        for v in range(1, 17):
            exprs = []
            for (kr, kc), kv in positions.items():
                if kc == c and kv == v and kr not in active_rows:
                    exprs.append(1)
            for i in active_rows:
                if i in row_vars:
                    letter = chr(65+i)
                    filtered = [p for p in row_perms[letter]
                               if all(p[c2] == positions.get((i,c2), p[c2]) for c2 in range(16) if (i,c2) in positions)]
                    for k, p in enumerate(filtered):
                        if p[c] == v:
                            exprs.append(row_vars[i][k])
            if exprs:
                if any(isinstance(x, int) for x in exprs):
                    cnt = sum(1 for x in exprs if isinstance(x, int) and x == 1)
                    if cnt > 1:
                        model.Add(False)
    
    for box in range(16):
        for v in range(1, 17):
            exprs = []
            for (kr, kc), kv in positions.items():
                if kv == v and kr not in active_rows:
                    br, bc = kr // 4, kc // 4
                    if br * 4 + bc == box:
                        exprs.append(1)
            for i in active_rows:
                if i in row_vars:
                    letter = chr(65+i)
                    filtered = [p for p in row_perms[letter]
                               if all(p[c2] == positions.get((i,c2), p[c2]) for c2 in range(16) if (i,c2) in positions)]
                    for k, p in enumerate(filtered):
                        for c in range(16):
                            if (i // 4) * 4 + (c // 4) == box and p[c] == v:
                                exprs.append(row_vars[i][k])
            if exprs:
                if any(isinstance(x, int) for x in exprs):
                    cnt = sum(1 for x in exprs if isinstance(x, int) and x == 1)
                    if cnt > 1:
                        model.Add(False)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300
    solver.parameters.num_search_workers = 8
    
    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.sols = []
        def on_solution_callback(self):
            grid = [[0]*16 for _ in range(16)]
            for (r, c), v in positions.items():
                grid[r][c] = v
            for i in active_rows:
                if i in row_vars:
                    letter = chr(65+i)
                    filtered = [p for p in row_perms[letter]
                               if all(p[c2] == positions.get((i,c2), p[c2]) for c2 in range(16) if (i,c2) in positions)]
                    for k in range(len(filtered)):
                        if self.Value(row_vars[i][k]):
                            grid[i] = filtered[k][:]
                            break
            self.sols.append(grid)
    
    cb = CB()
    status = solver.Solve(model, cb)
    return cb.sols

# Phase 14: 14 行
print("\n  第 14 階段: 14 行")
active14 = unknown_rows[:14]
sols14 = solve_rows(active14, positions, row_perms)
print(f"    解數: {len(sols14)}")

# Phase 15: 15 行（全部未知行）
print("\n  第 15 階段: 15 行（全部未知行）")
active15 = unknown_rows[:15]
sols15 = solve_rows(active15, positions, row_perms)
print(f"    解數: {len(sols15)}")

# 組合所有解
all_solutions = sols14 + sols15

# 去重
unique_solutions = []
seen = set()
for sol in all_solutions:
    h = str(tuple(tuple(row) for row in sol))
    if h not in seen:
        seen.add(h)
        unique_solutions.append(sol)

print(f"\n  去重後: {len(unique_solutions)} 個唯一解")

# 保存結果
output = {
    'metadata': {
        'version': 'V22.1',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'anchors_count': len(anchors),
        'sequence': '7 15 3 9',
        'strategy': 'CONSTRAINT_GUIDED_INCREMENTAL'
    },
    'summary': {
        'total_solutions': len(unique_solutions),
        'phases_completed': 15,
        'search_order': [chr(65+i) for i in unknown_rows]
    },
    'solutions': unique_solutions[:20],
}

with open('incremental_sampling_result.json', 'w') as f:
    json.dump(output, f, indent=2, default=str)

print(f"\n  💾 結果已保存至: incremental_sampling_result.json")

# 顯示結果摘要
print("\n" + "=" * 70)
print("  【最終結果】")
print("=" * 70)
print(f"  總唯一解數: {len(unique_solutions)}")
print(f"  搜索策略: 約束引導增量 (從最約束行開始)")
print(f"  行搜索順序: {[chr(65+i) for i in unknown_rows]}")

if unique_solutions:
    print("\n  【示例解】(第 1 個解):")
    grid = unique_solutions[0]
    for r in range(16):
        row_str = ' '.join(f'{v:2d}' for v in grid[r])
        print(f"    行{r+1}: {row_str}")

print("\n" + "=" * 70)
