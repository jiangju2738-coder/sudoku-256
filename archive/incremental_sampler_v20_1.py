#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔博弈優選策略 - 增量化多解空間採樣 V20.1
使用 sudoku_config.json (55 錨點) 進行多解採樣
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter
from dataclasses import dataclass
from ortools.sat.python import cp_model


@dataclass
class SolutionInfo:
    grid: List[List[int]]
    fitness: float
    timestamp: float


def load_config() -> Tuple[List[Dict], Dict[str, List[List[int]]]]:
    """載入錨點和排列"""
    with open('sudoku_config.json', 'r') as f:
        config = json.load(f)
    anchors = config['known_digits']
    
    # 載入排列 (A1-A16 格式)
    row_perms = {}
    for i in range(16):
        letter = chr(65+i)
        try:
            with open(f'A{i+1}_permutations.json', 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    row_perms[letter] = data
        except FileNotFoundError:
            pass
    
    return anchors, row_perms


def filter_perms(perms: List[List[int]], row_idx: int, positions: Dict) -> List[List[int]]:
    """過濾排列"""
    return [p for p in perms
           if all(p[c] == positions.get((row_idx, c), p[c]) for c in range(16) if (row_idx, c) in positions)]


def compute_fitness(grid: List[List[int]]) -> float:
    """計算適應度"""
    row_fit = sum(1.0 for r in range(16) if len(set(grid[r])) == 16) / 16
    col_fit = sum(1.0 for c in range(16) if len(set(grid[r][c] for r in range(16))) == 16) / 16
    box_fit = sum(1.0 for b in range(16) if len(set(grid[r][c] for r in range(16) for c in range(16) if (r//4)*4+(c//4)==b)) == 16) / 16
    return 0.1 * row_fit + 0.45 * col_fit + 0.45 * box_fit


def solve_and_collect(anchors: List[Dict], row_perms: Dict, 
                       solution_limit: int = 5, time_limit: int = 120) -> List[SolutionInfo]:
    """求解並收集解"""
    
    positions = {(a['row']-1, a['col']-1): a['value'] for a in anchors}
    
    # 未知行
    unknown_rows = [i for i in range(16) if sum(1 for (r, c) in positions if r == i) < 16]
    
    if not unknown_rows:
        print("  所有行已固定")
        return []
    
    model = cp_model.CpModel()
    row_vars = {}
    row_counts = {}
    
    # 創建變數
    for i in unknown_rows:
        letter = chr(65+i)
        if letter in row_perms:
            filtered = filter_perms(row_perms[letter], i, positions)
            row_counts[i] = len(filtered)
            if len(filtered) > 0:
                row_vars[i] = [model.NewBoolVar(f'r{i}_p{k}') for k in range(len(filtered))]
                model.AddExactlyOne(row_vars[i])
    
    # 列約束
    for c in range(16):
        for v in range(1, 17):
            exprs = []
            # 已知位置
            for (kr, kc), kv in positions.items():
                if kc == c and kv == v:
                    exprs.append(1)
            # 未知行
            for i in unknown_rows:
                if i in row_vars and chr(65+i) in row_perms:
                    filtered = filter_perms(row_perms[chr(65+i)], i, positions)
                    for k, p in enumerate(filtered):
                        if p[c] == v:
                            exprs.append(row_vars[i][k])
            
            if exprs:
                if any(isinstance(x, int) for x in exprs):
                    cnt = sum(1 for x in exprs if isinstance(x, int) and x == 1)
                    if cnt > 1:
                        return []  # 直接衝突
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
                if i in row_vars and chr(65+i) in row_perms:
                    filtered = filter_perms(row_perms[chr(65+i)], i, positions)
                    for k, p in enumerate(filtered):
                        for c in range(16):
                            if (i // 4) * 4 + (c // 4) == box and p[c] == v:
                                exprs.append(row_vars[i][k])
            
            if exprs:
                if any(isinstance(x, int) for x in exprs):
                    cnt = sum(1 for x in exprs if isinstance(x, int) and x == 1)
                    if cnt > 1:
                        return []
                    elif cnt == 1:
                        rest = [x for x in exprs if not isinstance(x, int)]
                        if rest:
                            model.Add(sum(rest) == 0)
                else:
                    model.Add(sum(exprs) <= 1)
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    solver.parameters.log_search_progress = True
    
    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.sols = []
        
        def on_solution_callback(self):
            grid = [[0]*16 for _ in range(16)]
            for (r, c), v in positions.items():
                grid[r][c] = v
            for i in unknown_rows:
                if i in row_vars and chr(65+i) in row_perms:
                    filtered = filter_perms(row_perms[chr(65+i)], i, positions)
                    for k in range(len(filtered)):
                        if self.Value(row_vars[i][k]):
                            grid[i] = filtered[k][:]
                            break
            self.sols.append(grid)
    
    cb = CB()
    t0 = time.time()
    status = solver.Solve(model, cb)
    t1 = time.time()
    
    print(f"  狀態: {solver.StatusName(status)}, 解數: {len(cb.sols)}, 時間: {t1-t0:.2f}s")
    
    return [SolutionInfo(g, compute_fitness(g), time.time()) for g in cb.sols]


def main():
    print("\n" + "="*68)
    print("║  符闔博弈優選策略 - 增量化多解空間採樣 V20.1              ║")
    print("╚" + "="*68)
    
    anchors, row_perms = load_config()
    print(f"\n[載入] 錨點: {len(anchors)} 個")
    print(f"[載入] 排列: {sum(len(v) for v in row_perms.values()):,} 個")
    
    positions = {(a['row']-1, a['col']-1): a['value'] for a in anchors}
    
    # 分析未知行
    unknown = [i for i in range(16) if sum(1 for (r,c) in positions if r==i) < 16]
    print(f"\n[分析] 未知行: {len(unknown)} 行 - {[chr(65+i) for i in unknown]}")
    
    # 分析每行可用排列
    print("\n[分析] 各行可用排列:")
    for i in range(16):
        letter = chr(65+i)
        known = sum(1 for (r, c) in positions if r == i)
        if letter in row_perms:
            filtered = filter_perms(row_perms[letter], i, positions)
            print(f"  行{letter}: {len(row_perms[letter]):7d} -> {len(filtered):7d} 可用 (已知{known}/16)")
    
    # 增量採樣
    all_solutions = []
    batch_size = 5
    max_batches = 10
    
    print(f"\n[採樣] 開始增量採樣 (批大小={batch_size}, 最大批數={max_batches})")
    start_time = time.time()
    
    for batch in range(1, max_batches + 1):
        print(f"\n{'─'*60}")
        print(f"  第 {batch} 批: 收集 {batch_size} 個解")
        print(f"{'─'*60}")
        
        # 收集新解
        new_sols = solve_and_collect(anchors, row_perms, batch_size, 120)
        
        if not new_sols:
            print("  ⚠️ 無新解，採樣結束")
            break
        
        all_solutions.extend(new_sols)
        print(f"  累計: {len(all_solutions)} 個解")
        
        # 檢查是否已達到 unique 解上限
        if len(new_sols) < batch_size:
            print("  ⚠️ 本批次未收集足夠解")
            break
    
    elapsed = time.time() - start_time
    
    # 結果總結
    print("\n" + "="*68)
    print("║  採樣結果總結                                          ║")
    print("="*68)
    print(f"  總解數: {len(all_solutions)}")
    print(f"  採樣時間: {elapsed:.2f}秒")
    
    if all_solutions:
        avg_fitness = sum(s.fitness for s in all_solutions) / len(all_solutions)
        print(f"  平均適應度: {avg_fitness:.4f}")
        print(f"  每個解的適應度:")
        for s in all_solutions:
            print(f"    #{s.timestamp - all_solutions[0].timestamp:.1f}s: {s.fitness:.4f}")
    
    # 保存結果
    output = {
        'metadata': {
            'version': 'V20.1',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'anchors_count': len(anchors),
            'sequence': '7 15 3 9'
        },
        'summary': {
            'total_solutions': len(all_solutions),
            'sampling_time': elapsed,
            'batches_run': batch
        },
        'solutions': [
            {'fitness': s.fitness, 'grid': s.grid} for s in all_solutions
        ]
    }
    
    with open('incremental_sampling_result.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n💾 結果已保存至: incremental_sampling_result.json")
    
    return all_solutions


if __name__ == '__main__':
    main()
