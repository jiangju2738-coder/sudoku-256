#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速驗證：測試不同錨點數量的解存在性
"""

import json
from pathlib import Path
from ortools.sat.python import cp_model
from collections import Counter

# 載入 sudoku_config.json (55 anchors)
with open('sudoku_config.json', 'r') as f:
    config = json.load(f)

anchors_55 = config['known_digits']

# 載入 FULL_92_ANCHORS
import importlib.util
spec = importlib.util.spec_from_file_location('cfg', '7_15_3_9_config_full.py')
cfg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfg)
anchors_114 = cfg.FULL_92_ANCHORS

def load_permutations():
    row_perms = {}
    for i in range(16):
        letter = chr(65 + i)
        fpath = Path(f'D:/2026/WPF_Sudoku/Sudoku_256/A{letter}_permutations.json')
        if fpath.exists():
            with open(fpath, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    row_perms[letter] = data
    return row_perms

def try_solve(anchors, label, solution_limit=3):
    print(f"\n{'='*60}")
    print(f"測試: {label} ({len(anchors)} 錨點)")
    print(f"{'='*60}")
    
    # 錨點位置映射
    positions = {(a['row']-1, a['col']-1): a['value'] for a in anchors}
    
    # 未知行
    unknown_rows = []
    for i in range(16):
        known = sum(1 for (r, c) in positions if r == i)
        if known < 16:
            unknown_rows.append(i)
    
    print(f"未知行: {[chr(65+i) for i in unknown_rows]}")
    
    row_perms = load_permutations()
    
    # 檢查每行可用排列
    for i in unknown_rows:
        letter = chr(65 + i)
        if letter in row_perms:
            # 過濾錨點約束
            filtered = [p for p in row_perms[letter] 
                       if all(p[c] == positions.get((i, c), p[c]) for c in range(16) if (i, c) in positions)]
            print(f"  行{letter}: {len(filtered)} 排列可用")
    
    model = cp_model.CpModel()
    row_letters = 'ABCDEFGHIJKLMNOP'
    row_vars = {}
    row_counts = {}
    
    for i in unknown_rows:
        letter = row_letters[i]
        if letter in row_perms:
            filtered = [p for p in row_perms[letter]
                       if all(p[c] == positions.get((i, c), p[c]) for c in range(16) if (i, c) in positions)]
            row_counts[i] = len(filtered)
            if len(filtered) > 0:
                row_vars[i] = [model.NewBoolVar(f'r{i}_p{k}') for k in range(len(filtered))]
                model.AddExactlyOne(row_vars[i])
    
    # 列約束
    for c in range(16):
        for v in range(1, 17):
            exprs = []
            for (kr, kc), kv in positions.items():
                if kc == c and kv == v:
                    exprs.append(1)
            for i in unknown_rows:
                if i in row_vars and row_letters[i] in row_perms:
                    filtered = [p for p in row_perms[row_letters[i]]
                               if all(p[c2] == positions.get((i, c2), p[c2]) for c2 in range(16) if (i, c2) in positions)]
                    for k, p in enumerate(filtered):
                        if p[c] == v:
                            exprs.append(row_vars[i][k])
            
            if exprs:
                if any(isinstance(x, int) for x in exprs):
                    cnt = sum(1 for x in exprs if isinstance(x, int) and x == 1)
                    if cnt > 1:
                        print(f"  ❌ 列{c+1}值{v}衝突")
                        return False
                    elif cnt == 1:
                        rest = [x for x in exprs if not isinstance(x, int)]
                        if rest:
                            model.Add(sum(rest) == 0)
                else:
                    model.Add(sum(exprs) <= 1)
    
    # 宮約束
    for box in range(16):
        for v in range(1, 17):
            exprs = []
            for (kr, kc), kv in positions.items():
                if kv == v:
                    br, bc = kr // 4, kc // 4
                    if br * 4 + bc == box:
                        exprs.append(1)
            for i in unknown_rows:
                if i in row_vars and row_letters[i] in row_perms:
                    filtered = [p for p in row_perms[row_letters[i]]
                               if all(p[c2] == positions.get((i, c2), p[c2]) for c2 in range(16) if (i, c2) in positions)]
                    for k, p in enumerate(filtered):
                        for c in range(16):
                            if (i // 4) * 4 + (c // 4) == box and p[c] == v:
                                exprs.append(row_vars[i][k])
            
            if exprs:
                if any(isinstance(x, int) for x in exprs):
                    cnt = sum(1 for x in exprs if isinstance(x, int) and x == 1)
                    if cnt > 1:
                        return False
                    elif cnt == 1:
                        rest = [x for x in exprs if not isinstance(x, int)]
                        if rest:
                            model.Add(sum(rest) == 0)
                else:
                    model.Add(sum(exprs) <= 1)
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 120
    solver.parameters.num_search_workers = 4
    solver.parameters.num_search_workers = 4
    # solution_limit not available, will use callback to limit
    solver.parameters.log_search_progress = False
    
    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.sols = []
        def on_solution_callback(self):
            grid = [[0]*16 for _ in range(16)]
            for (r,c),v in positions.items():
                grid[r][c] = v
            for i in unknown_rows:
                if i in row_vars and row_letters[i] in row_perms:
                    filtered = [p for p in row_perms[row_letters[i]]
                               if all(p[c2] == positions.get((i, c2), p[c2]) for c2 in range(16) if (i, c2) in positions)]
                    for k in range(len(filtered)):
                        if self.Value(row_vars[i][k]):
                            grid[i] = filtered[k][:]
                            break
            self.sols.append(grid)
    
    cb = CB()
    import time
    t0 = time.time()
    status = solver.Solve(model, cb)
    t1 = time.time()
    
    print(f"狀態: {solver.StatusName(status)}, 解數: {len(cb.sols)}, 時間: {t1-t0:.2f}s")
    
    if cb.sols:
        print(f"  找到 {len(cb.sols)} 個解")
        # 顯示第一個解
        g = cb.sols[0]
        print("  解示例（前4行）:")
        for r in range(4):
            print(f"    行{r+1}: {g[r]}")
    else:
        print("  ❌ 無解")
    
    return len(cb.sols) > 0

# 測試
print("="*60)
print("錨點數量驗證測試")
print("="*60)

r1 = try_solve(anchors_55, "55 anchors", 3)
r2 = try_solve(anchors_114, "114 anchors (FULL_92_ANCHORS)", 3)

print("\n" + "="*60)
print("總結")
print("="*60)
print(f"55 anchors: {'有解' if r1 else '無解'}")
print(f"114 anchors: {'有解' if r2 else '無解'}")
