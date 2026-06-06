#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔博弈優選策略 - 分段增量多解採樣 V21.0

策略：
1. 先固定已知行，僅搜索未知行
2. 分批添加約束，逐步縮小搜索空間
3. 使用 CP-SAT 收集多解
"""

import json
import time
from ortools.sat.python import cp_model
from collections import Counter

print("=" * 70)
print("  符闔博弈優選策略 - 分段增量多解採樣 V21.0")
print("=" * 70)

# 載入配置
with open('sudoku_config.json', 'r') as f:
    config = json.load(f)

anchors = config['known_digits']
positions = {(a['row']-1, a['col']-1): a['value'] for a in anchors}

print(f"\n[載入] 錨點: {len(anchors)} 個")

# 載入排列
row_perms = {}
for i in range(16):
    letter = chr(65+i)
    with open(f'A{i+1}_permutations.json', 'r') as f:
        data = json.load(f)
        if isinstance(data, list):
            row_perms[letter] = data

print(f"[載入] 排列: {sum(len(v) for v in row_perms.values()):,} 個")

# 確定未知行（從最少約束的行開始）
row_known_counts = {}
for i in range(16):
    known = sum(1 for (r, c) in positions if r == i)
    row_known_counts[i] = known

# 按未知數量排序（先搜索未知多的行，因為它們約束更少）
unknown_rows = sorted(range(16), key=lambda i: -row_known_counts[i])
unknown_rows = [i for i in unknown_rows if row_known_counts[i] < 16]

print(f"\n[分析] 未知行 (按未知度排序):")
for i in unknown_rows:
    letter = chr(65+i)
    known = row_known_counts[i]
    perms = len(row_perms.get(letter, []))
    print(f"  行{letter}: 已知{known:2d}/16, 排列{perms:7,}")

# 分段策略：先固定部分行，逐步擴展
# Phase 1: 僅搜索 P (row 15) - 最多未知
# Phase 2: P + O
# Phase 3: P + O + N
# ...逐步添加

def solve_with_rows(active_rows: list, all_positions: dict) -> list:
    """僅搜索指定行"""
    
    model = cp_model.CpModel()
    row_vars = {}
    row_counts = {}
    
    for i in active_rows:
        letter = chr(65+i)
        if letter in row_perms:
            # 過濾錨點約束
            filtered = [p for p in row_perms[letter]
                       if all(p[c] == all_positions.get((i, c), p[c]) for c in range(16) if (i, c) in all_positions)]
            row_counts[i] = len(filtered)
            if len(filtered) > 0:
                row_vars[i] = [model.NewBoolVar(f'r{i}_p{k}') for k in range(len(filtered))]
                model.AddExactlyOne(row_vars[i])
    
    # 列約束
    for c in range(16):
        for v in range(1, 17):
            exprs = []
            # 不在 active_rows 中的已知位置
            for (kr, kc), kv in all_positions.items():
                if kc == c and kv == v and kr not in active_rows:
                    exprs.append(1)
            # active_rows 中的變數
            for i in active_rows:
                if i in row_vars and chr(65+i) in row_perms:
                    filtered = [p for p in row_perms[chr(65+i)]
                               if all(p[c2] == all_positions.get((i,c2), p[c2]) for c2 in range(16) if (i,c2) in all_positions)]
                    for k, p in enumerate(filtered):
                        if p[c] == v:
                            exprs.append(row_vars[i][k])
            
            if exprs:
                if any(isinstance(x, int) for x in exprs):
                    cnt = sum(1 for x in exprs if isinstance(x, int) and x == 1)
                    if cnt > 1:
                        model.Add(False)
                else:
                    model.Add(sum(exprs) <= 1)
    
    # 宮約束
    for box in range(16):
        for v in range(1, 17):
            exprs = []
            for (kr, kc), kv in all_positions.items():
                if kv == v and kr not in active_rows:
                    br, bc = kr // 4, kc // 4
                    if br * 4 + bc == box:
                        exprs.append(1)
            for i in active_rows:
                if i in row_vars and chr(65+i) in row_perms:
                    filtered = [p for p in row_perms[chr(65+i)]
                               if all(p[c2] == all_positions.get((i,c2), p[c2]) for c2 in range(16) if (i,c2) in all_positions)]
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
    solver.parameters.max_time_in_seconds = 120
    solver.parameters.num_search_workers = 8
    solver.parameters.log_search_progress = False
    
    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.sols = []
        
        def on_solution_callback(self):
            grid = [[0]*16 for _ in range(16)]
            for (r, c), v in all_positions.items():
                grid[r][c] = v
            for i in active_rows:
                if i in row_vars and chr(65+i) in row_perms:
                    filtered = [p for p in row_perms[chr(65+i)]
                               if all(p[c2] == all_positions.get((i,c2), p[c2]) for c2 in range(16) if (i,c2) in all_positions)]
                    for k in range(len(filtered)):
                        if self.Value(row_vars[i][k]):
                            grid[i] = filtered[k][:]
                            break
            self.sols.append(grid)
    
    cb = CB()
    t0 = time.time()
    status = solver.Solve(model, cb)
    t1 = time.time()
    
    return cb.sols, solver.StatusName(status), t1-t0


# 執行分段採樣
all_solutions = []
start_time = time.time()

print("\n" + "-" * 70)
print("  【分段採樣策略】")
print("-" * 70)

# 策略：從 1 個未知行開始，逐步增加
phase_rows = []
for i in unknown_rows:
    phase_rows.append(i)
    
    print(f"\n  第 {len(phase_rows)} 階段: 搜索行 {[chr(65+j) for j in phase_rows]}")
    
    solutions, status, elapsed = solve_with_rows(phase_rows, positions)
    
    print(f"    狀態: {status}, 解數: {len(solutions)}, 時間: {elapsed:.2f}s")
    
    if solutions:
        # 添加新解（去重）
        for sol in solutions:
            grid_hash = str(tuple(tuple(row) for row in sol))
            if grid_hash not in [str(tuple(tuple(row) for row in s)) for s in all_solutions]:
                all_solutions.append(sol)
        
        print(f"    累計: {len(all_solutions)} 個唯一解")
    else:
        print("    ⚠️ 無解")
        break

elapsed_total = time.time() - start_time

# 結果總結
print("\n" + "=" * 70)
print("  【採樣結果】")
print("=" * 70)
print(f"  總解數: {len(all_solutions)}")
print(f"  總時間: {elapsed_total:.2f}秒")
print(f"  搜索的行數: {len(phase_rows)}")

if all_solutions:
    # 保存前 5 個解
    output = {
        'metadata': {
            'version': 'V21.0',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'anchors_count': len(anchors),
            'sequence': '7 15 3 9'
        },
        'summary': {
            'total_solutions': len(all_solutions),
            'total_time': elapsed_total,
            'phases_completed': len(phase_rows)
        },
        'solutions': all_solutions[:5],
        'solution_hashes': [
            str(tuple(tuple(row) for row in s))[:50] + '...' 
            for s in all_solutions[:5]
        ]
    }
    
    with open('incremental_sampling_result.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n  💾 結果已保存至: incremental_sampling_result.json")
    
    # 顯示第一個解
    print("\n  【示例解】(第 1 個解的前 4 行):")
    grid = all_solutions[0]
    for r in range(4):
        row_str = ' '.join(f'{v:2d}' for v in grid[r])
        print(f"    行{r+1}: {row_str}")
else:
    print("\n  ❌ 未找到任何解")

print("\n" + "=" * 70)
