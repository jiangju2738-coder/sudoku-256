#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔博弈優選策略 - 約束引導增量多解採樣 V22.0

優化策略：
1. 從最約束的行開始（排列最少的行）
2. 逐步添加較寬鬆的行
3. 利用約束傳播減少搜索空間
"""

import json
import time
from ortools.sat.python import cp_model

print("=" * 70)
print("  符闔博弈優選策略 - 約束引導增量多解採樣 V22.0")
print("=" * 70)

# 載入配置
with open('sudoku_config.json', 'r') as f:
    config = json.load(f)

anchors = config['known_digits']
positions = {(a['row']-1, a['col']-1): a['value'] for a in anchors}

print(f"\n[載入] 錨點: {len(anchors)} 個")

# 載入排列
row_perms = {}
row_perm_counts = {}
for i in range(16):
    letter = chr(65+i)
    with open(f'A{i+1}_permutations.json', 'r') as f:
        data = json.load(f)
        if isinstance(data, list):
            row_perms[letter] = data
            row_perm_counts[i] = len(data)

print(f"[載入] 排列總數: {sum(row_perm_counts.values()):,}")

# 計算每行過濾後的排列數
row_filter_counts = {}
for i in range(16):
    letter = chr(65+i)
    known = sum(1 for (r, c) in positions if r == i)
    if known < 16:
        filtered = [p for p in row_perms[letter]
                   if all(p[c] == positions.get((i, c), p[c]) for c in range(16) if (i, c) in positions)]
        row_filter_counts[i] = len(filtered)
        print(f"  行{letter}: {len(row_perms[letter]):7,} -> {len(filtered):7,} 過濾後 (已知{known}/16)")

# 按過濾後排列數排序（最少排列的行優先）
unknown_rows = sorted(row_filter_counts.keys(), key=lambda i: row_filter_counts[i])

print(f"\n[策略] 約束引導排序（從最約束行開始）:")
for i in unknown_rows:
    letter = chr(65+i)
    print(f"  行{letter}: {row_filter_counts[i]:7,} 可用排列")

def solve_with_rows(active_rows: list, all_positions: dict, row_perms: dict) -> tuple:
    """搜索指定行組合"""
    
    model = cp_model.CpModel()
    row_vars = {}
    
    # 建立變數
    for i in active_rows:
        letter = chr(65+i)
        filtered = [p for p in row_perms[letter]
                   if all(p[c] == all_positions.get((i,c), p[c]) for c in range(16) if (i,c) in all_positions)]
        if len(filtered) > 0:
            row_vars[i] = [model.NewBoolVar(f'r{i}_p{k}') for k in range(len(filtered))]
            model.AddExactlyOne(row_vars[i])
    
    # 列約束
    for c in range(16):
        for v in range(1, 17):
            exprs = []
            # 固定行（不在 active_rows 中）
            for (kr, kc), kv in all_positions.items():
                if kc == c and kv == v and kr not in active_rows:
                    exprs.append(1)
            # 活動行
            for i in active_rows:
                if i in row_vars:
                    letter = chr(65+i)
                    filtered = [p for p in row_perms[letter]
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
                if i in row_vars:
                    letter = chr(65+i)
                    filtered = [p for p in row_perms[letter]
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
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 180
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
                if i in row_vars:
                    letter = chr(65+i)
                    filtered = [p for p in row_perms[letter]
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


# 執行採樣
all_solutions = []
start_time = time.time()
unique_hashes = set()

print("\n" + "-" * 70)
print("  【增量採樣】（約束引導）")
print("-" * 70)

for phase, row_idx in enumerate(unknown_rows, 1):
    active_rows = unknown_rows[:phase]
    
    print(f"\n  第 {phase} 階段: 搜索 {len(active_rows)} 行 {[chr(65+i) for i in active_rows]}")
    
    solutions, status, elapsed = solve_with_rows(active_rows, positions, row_perms)
    
    print(f"    狀態: {status}, 解數: {len(solutions)}, 時間: {elapsed:.2f}s")
    
    if solutions:
        # 去重添加
        new_count = 0
        for sol in solutions:
            grid_hash = str(tuple(tuple(row) for row in sol))
            if grid_hash not in unique_hashes:
                unique_hashes.add(grid_hash)
                all_solutions.append(sol)
                new_count += 1
        
        print(f"    新解: {new_count}, 累計: {len(all_solutions)}")
    else:
        print("    ⚠️ 無解，停止搜索")
        break

elapsed_total = time.time() - start_time

# 最終結果
print("\n" + "=" * 70)
print("  【最終結果】")
print("=" * 70)
print(f"  總解數: {len(all_solutions)}")
print(f"  總時間: {elapsed_total:.2f}秒")
print(f"  搜索階段: {phase}/{len(unknown_rows)}")

if all_solutions:
    # 保存結果
    output = {
        'metadata': {
            'version': 'V22.0',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'anchors_count': len(anchors),
            'sequence': '7 15 3 9'
        },
        'summary': {
            'total_solutions': len(all_solutions),
            'total_time': elapsed_total,
            'phases_completed': phase,
            'search_strategy': 'CONSTRAINT_GUIDED'
        },
        'solutions': all_solutions[:10],  # 保存前 10 個解
    }
    
    with open('incremental_sampling_result.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n  💾 結果已保存至: incremental_sampling_result.json")
    
    # 顯示第一個解
    print("\n  【示例解】:")
    grid = all_solutions[0]
    for r in range(16):
        row_str = ' '.join(f'{v:2d}' for v in grid[r])
        print(f"    行{r+1}: {row_str}")
else:
    print("\n  ❌ 未找到任何解")

print("\n" + "=" * 70)
