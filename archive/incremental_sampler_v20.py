#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 符闔博弈優選策略 - 增量化多解空間採樣系統 V20.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

功能：
1. 增量化多解空間採樣
2. 排列生成算法
3. 本質解數估算
4. 基因指紋多解分析

核心算法：
- 增量式解採樣
- 排列空間縮減（基於已知錨點的約束傳播）
- 本質解計數（使用百分比聚類）
- 多解基因指紋對比
"""

import json
import time
import math
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum

# OR-Tools
from ortools.sat.python import cp_model


# ═══════════════════════════════════════════════════════════
# 錨點數據（完整 92 個）
# ═══════════════════════════════════════════════════════════

FULL_92_ANCHORS = [
    # 行 A (1): 4 個
    {'row': 1, 'col': 3, 'value': 3},
    {'row': 1, 'col': 6, 'value': 12},
    {'row': 1, 'col': 8, 'value': 5},
    {'row': 1, 'col': 12, 'value': 14},
    # 行 B (2): 4 個
    {'row': 2, 'col': 2, 'value': 12},
    {'row': 2, 'col': 5, 'value': 3},
    {'row': 2, 'col': 7, 'value': 9},
    {'row': 2, 'col': 9, 'value': 6},
    # 行 C (3): 16 個 - 完全固定
    {'row': 3, 'col': 1, 'value': 7}, {'row': 3, 'col': 2, 'value': 15},
    {'row': 3, 'col': 3, 'value': 3}, {'row': 3, 'col': 4, 'value': 9},
    {'row': 3, 'col': 5, 'value': 11}, {'row': 3, 'col': 6, 'value': 12},
    {'row': 3, 'col': 7, 'value': 6}, {'row': 3, 'col': 8, 'value': 5},
    {'row': 3, 'col': 9, 'value': 10}, {'row': 3, 'col': 10, 'value': 2},
    {'row': 3, 'col': 11, 'value': 1}, {'row': 3, 'col': 12, 'value': 14},
    {'row': 3, 'col': 13, 'value': 13}, {'row': 3, 'col': 14, 'value': 10},
    {'row': 3, 'col': 15, 'value': 4}, {'row': 3, 'col': 16, 'value': 8},
    # 行 D (4): 16 個 - 完全固定
    {'row': 4, 'col': 1, 'value': 11}, {'row': 4, 'col': 2, 'value': 4},
    {'row': 4, 'col': 3, 'value': 13}, {'row': 4, 'col': 4, 'value': 7},
    {'row': 4, 'col': 5, 'value': 16}, {'row': 4, 'col': 6, 'value': 8},
    {'row': 4, 'col': 7, 'value': 1}, {'row': 4, 'col': 8, 'value': 9},
    {'row': 4, 'col': 9, 'value': 3}, {'row': 4, 'col': 10, 'value': 15},
    {'row': 4, 'col': 11, 'value': 2}, {'row': 4, 'col': 12, 'value': 6},
    {'row': 4, 'col': 13, 'value': 5}, {'row': 4, 'col': 14, 'value': 14},
    {'row': 4, 'col': 15, 'value': 10}, {'row': 4, 'col': 16, 'value': 12},
    # 行 E (5): 3 個
    {'row': 5, 'col': 5, 'value': 13},
    {'row': 5, 'col': 10, 'value': 5},
    {'row': 5, 'col': 13, 'value': 4},
    # 行 F (6): 7 個
    {'row': 6, 'col': 2, 'value': 8},
    {'row': 6, 'col': 5, 'value': 15},
    {'row': 6, 'col': 7, 'value': 4},
    {'row': 6, 'col': 8, 'value': 3},
    {'row': 6, 'col': 11, 'value': 10},
    {'row': 6, 'col': 14, 'value': 16},
    {'row': 6, 'col': 15, 'value': 12},
    # 行 G (7): 6 個
    {'row': 7, 'col': 1, 'value': 14},
    {'row': 7, 'col': 3, 'value': 4},
    {'row': 7, 'col': 4, 'value': 6},
    {'row': 7, 'col': 10, 'value': 9},
    {'row': 7, 'col': 13, 'value': 15},
    {'row': 7, 'col': 16, 'value': 2},
    # 行 H (8): 6 個
    {'row': 8, 'col': 2, 'value': 13},
    {'row': 8, 'col': 6, 'value': 5},
    {'row': 8, 'col': 8, 'value': 9},
    {'row': 8, 'col': 12, 'value': 11},
    {'row': 8, 'col': 14, 'value': 7},
    {'row': 8, 'col': 15, 'value': 1},
    # 行 I (9): 16 個 - 完全固定
    {'row': 9, 'col': 1, 'value': 13}, {'row': 9, 'col': 2, 'value': 1},
    {'row': 9, 'col': 3, 'value': 10}, {'row': 9, 'col': 4, 'value': 2},
    {'row': 9, 'col': 5, 'value': 8}, {'row': 9, 'col': 6, 'value': 11},
    {'row': 9, 'col': 7, 'value': 16}, {'row': 9, 'col': 8, 'value': 7},
    {'row': 9, 'col': 9, 'value': 14}, {'row': 9, 'col': 10, 'value': 3},
    {'row': 9, 'col': 11, 'value': 5}, {'row': 9, 'col': 12, 'value': 12},
    {'row': 9, 'col': 13, 'value': 9}, {'row': 9, 'col': 14, 'value': 6},
    {'row': 9, 'col': 15, 'value': 4}, {'row': 9, 'col': 16, 'value': 15},
    # 行 J (10): 4 個
    {'row': 10, 'col': 2, 'value': 5},
    {'row': 10, 'col': 6, 'value': 14},
    {'row': 10, 'col': 10, 'value': 8},
    {'row': 10, 'col': 12, 'value': 1},
    # 行 K (11): 6 個
    {'row': 11, 'col': 1, 'value': 1},
    {'row': 11, 'col': 3, 'value': 6},
    {'row': 11, 'col': 5, 'value': 10},
    {'row': 11, 'col': 8, 'value': 13},
    {'row': 11, 'col': 11, 'value': 9},
    {'row': 11, 'col': 14, 'value': 11},
    # 行 L (12): 6 個
    {'row': 12, 'col': 4, 'value': 4},
    {'row': 12, 'col': 6, 'value': 16},
    {'row': 12, 'col': 7, 'value': 14},
    {'row': 12, 'col': 9, 'value': 3},
    {'row': 12, 'col': 11, 'value': 12},
    {'row': 12, 'col': 13, 'value': 7},
    # 行 M (13): 7 個
    {'row': 13, 'col': 1, 'value': 15},
    {'row': 13, 'col': 5, 'value': 12},
    {'row': 13, 'col': 9, 'value': 5},
    {'row': 13, 'col': 10, 'value': 14},
    {'row': 13, 'col': 12, 'value': 8},
    {'row': 13, 'col': 15, 'value': 11},
    {'row': 13, 'col': 16, 'value': 6},
    # 行 N (14): 5 個
    {'row': 14, 'col': 3, 'value': 9},
    {'row': 14, 'col': 6, 'value': 6},
    {'row': 14, 'col': 9, 'value': 13},
    {'row': 14, 'col': 12, 'value': 15},
    {'row': 14, 'col': 16, 'value': 10},
    # 行 O (15): 6 個
    {'row': 15, 'col': 2, 'value': 1},
    {'row': 15, 'col': 5, 'value': 9},
    {'row': 15, 'col': 8, 'value': 15},
    {'row': 15, 'col': 11, 'value': 7},
    {'row': 15, 'col': 13, 'value': 16},
    {'row': 15, 'col': 14, 'value': 3},
    # 行 P (16): 2 個
    {'row': 16, 'col': 3, 'value': 2},
    {'row': 16, 'col': 7, 'value': 5},
]


# ═══════════════════════════════════════════════════════════
# 數據結構定義
# ═══════════════════════════════════════════════════════════

class SamplingMethod(Enum):
    UNIFORM = "均勻採樣"
    ADAPTIVE = "自適應採樣"
    CONSTRAINT_GUIDED = "約束引導採樣"


@dataclass
class SolutionSample:
    grid: List[List[int]]
    sample_id: int
    sample_method: SamplingMethod
    gene_fingerprint: Dict
    constraint_fitness: float
    is_essential: bool = False
    timestamp: float = 0.0


@dataclass
class PermutationInfo:
    row_letter: str
    row_index: int
    total_perms: int
    valid_perms_after_filter: int
    filter_ratio: float
    known_positions_in_row: int


@dataclass  
class EssentialSolutionEstimate:
    total_solutions: int
    essential_solution_count: int
    confidence: float
    estimation_method: str


# ═══════════════════════════════════════════════════════════
# 配置載入
# ═══════════════════════════════════════════════════════════

def load_anchors() -> List[Dict]:
    """載入錨點"""
    return FULL_92_ANCHORS


def load_permutations() -> Dict[str, List[List[int]]]:
    """載入符闔排列"""
    row_permutations = {}
    row_map = {chr(65+i): f'A{i+1}_permutations.json' for i in range(16)}
    
    for letter, fname in row_map.items():
        fpath = Path(f'D:/2026/WPF_Sudoku/Sudoku_256/{fname}')
        if fpath.exists():
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    row_permutations[letter] = data
                elif isinstance(data, dict) and 'permutations' in data:
                    row_permutations[letter] = data['permutations']
    
    return row_permutations


# ═══════════════════════════════════════════════════════════
# CP-SAT 多解收集器
# ═══════════════════════════════════════════════════════════

class MultiSolutionCollector:
    """CP-SAT 多解收集器"""
    
    def __init__(self, anchors: List[Dict], row_permutations: Dict[str, List[List[int]]]):
        self.anchors = anchors
        self.row_permutations = row_permutations
        
        # 建立錨點位置映射
        self.anchor_positions: Dict[Tuple[int, int], int] = {}
        for a in anchors:
            self.anchor_positions[(a['row']-1, a['col']-1)] = a['value']
        
        # 確定未知行
        self.row_letters = 'ABCDEFGHIJKLMNOP'
        self.unknown_rows = []
        for i in range(16):
            known_count = sum(1 for (kr, _) in self.anchor_positions if kr == i)
            if known_count < 16:
                self.unknown_rows.append(i)
        
        print(f"[初始化] 未知行: {[self.row_letters[i] for i in self.unknown_rows]}")
        print(f"[初始化] 完全固定行: {[self.row_letters[i] for i in range(16) if i not in self.unknown_rows]}")
    
    def collect_solutions(self, solution_limit: int = 5, time_limit: int = 180) -> List[List[List[int]]]:
        """收集解"""
        
        print(f"\n[CP-SAT] 收集 {solution_limit} 個解...")
        
        model = cp_model.CpModel()
        
        # 為未知行創建變數
        row_vars = {}
        row_perm_counts = {}
        
        for i in self.unknown_rows:
            letter = self.row_letters[i]
            if letter in self.row_permutations:
                perms = self.row_permutations[letter]
                row_perm_counts[i] = len(perms)
                if len(perms) > 0:
                    row_vars[i] = [model.NewBoolVar(f'row{i}_perm{k}') for k in range(len(perms))]
                    model.AddExactlyOne(row_vars[i])
        
        # 列約束
        for c in range(16):
            for v in range(1, 17):
                count_exprs = []
                
                # 已知位置
                for (kr, kc), kv in self.anchor_positions.items():
                    if kc == c and kv == v:
                        count_exprs.append(1)
                
                # 未知行
                for i in self.unknown_rows:
                    if i in row_vars and self.row_letters[i] in self.row_permutations:
                        for k in range(row_perm_counts[i]):
                            if self.row_permutations[self.row_letters[i]][k][c] == v:
                                count_exprs.append(row_vars[i][k])
                
                if count_exprs:
                    if any(isinstance(x, int) for x in count_exprs):
                        known_count = sum(1 for x in count_exprs if isinstance(x, int) and x == 1)
                        if known_count > 1:
                            model.Add(False)
                            return []
                        elif known_count == 1:
                            exprs = [x for x in count_exprs if not isinstance(x, int)]
                            if exprs:
                                model.Add(sum(exprs) == 0)
                    else:
                        model.Add(sum(count_exprs) <= 1)
        
        # 宮約束
        for box_idx in range(16):
            for v in range(1, 17):
                count_exprs = []
                
                # 已知位置
                for (kr, kc), kv in self.anchor_positions.items():
                    if kv == v:
                        box_r = kr // 4
                        box_c = kc // 4
                        if box_r * 4 + box_c == box_idx:
                            count_exprs.append(1)
                
                # 未知行
                for i in self.unknown_rows:
                    if i in row_vars and self.row_letters[i] in self.row_permutations:
                        for k in range(row_perm_counts[i]):
                            for c in range(16):
                                r = i
                                box_r = r // 4
                                box_c = c // 4
                                if box_r * 4 + box_c == box_idx and self.row_permutations[self.row_letters[i]][k][c] == v:
                                    count_exprs.append(row_vars[i][k])
                
                if count_exprs:
                    if any(isinstance(x, int) for x in count_exprs):
                        known_count = sum(1 for x in count_exprs if isinstance(x, int) and x == 1)
                        if known_count > 1:
                            model.Add(False)
                            return []
                        elif known_count == 1:
                            exprs = [x for x in count_exprs if not isinstance(x, int)]
                            if exprs:
                                model.Add(sum(exprs) == 0)
                    else:
                        model.Add(sum(count_exprs) <= 1)
        
        # 求解
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 8
        solver.parameters.solution_limit = solution_limit
        solver.parameters.log_search_progress = True
        
        class SolutionCallback(cp_model.CpSolverSolutionCallback):
            def __init__(self):
                super().__init__()
                self.solutions = []
            
            def on_solution_callback(self):
                grid = [[0] * 16 for _ in range(16)]
                
                # 填入已知
                for (r, c), v in self.anchor_positions.items():
                    grid[r][c] = v
                
                # 填入未知行
                for i in self.unknown_rows:
                    if i in row_vars and self.row_letters[i] in self.row_permutations:
                        for k in range(row_perm_counts[i]):
                            if self.Value(row_vars[i][k]):
                                grid[i] = self.row_permutations[self.row_letters[i]][k][:]
                                break
                
                self.solutions.append(grid)
        
        start_time = time.time()
        callback = SolutionCallback()
        status = solver.Solve(model, callback)
        elapsed = time.time() - start_time
        
        print(f"[CP-SAT] 狀態: {solver.StatusName(status)}, 解數: {len(callback.solutions)}, 耗時: {elapsed:.2f}秒")
        
        return callback.solutions


# ═══════════════════════════════════════════════════════════
# 基因指紋計算
# ═══════════════════════════════════════════════════════════

def compute_gene_fingerprint(grid: List[List[int]], anchor_positions: Dict) -> Dict:
    """計算基因指紋"""
    fp = {
        'row_satisfaction': [],
        'col_satisfaction': [],
        'box_satisfaction': [],
        'diagonal_main': 0.0,
        'diagonal_anti': 0.0,
        'total_fitness': 0.0
    }
    
    # 行約束
    for r in range(16):
        if len(set(grid[r])) == 16:
            fp['row_satisfaction'].append(1.0)
        else:
            fp['row_satisfaction'].append(0.0)
    
    # 列約束
    for c in range(16):
        col_vals = [grid[r][c] for r in range(16)]
        fp['col_satisfaction'].append(len(set(col_vals)) / 16.0)
    
    # 宮约束
    for box_idx in range(16):
        vals = []
        for r in range(16):
            for c in range(16):
                if (r // 4) * 4 + (c // 4) == box_idx:
                    vals.append(grid[r][c])
        fp['box_satisfaction'].append(len(set(vals)) / 16.0)
    
    # 對角線
    main_diag = [grid[i][i] for i in range(16)]
    fp['diagonal_main'] = len(set(main_diag)) / 16.0
    anti_diag = [grid[i][15-i] for i in range(16)]
    fp['diagonal_anti'] = len(set(anti_diag)) / 16.0
    
    # 總體適應度
    fp['total_fitness'] = (
        0.1 * sum(fp['row_satisfaction']) / 16.0 +
        0.45 * sum(fp['col_satisfaction']) / 16.0 +
        0.45 * sum(fp['box_satisfaction']) / 16.0
    )
    
    return fp


def compute_fingerprint_distance(fp1: Dict, fp2: Dict) -> float:
    """計算指紋距離"""
    dist = 0.0
    for i in range(16):
        dist += abs(fp1['row_satisfaction'][i] - fp2['row_satisfaction'][i])
        dist += abs(fp1['col_satisfaction'][i] - fp2['col_satisfaction'][i])
        dist += abs(fp1['box_satisfaction'][i] - fp2['box_satisfaction'][i])
    dist += abs(fp1['diagonal_main'] - fp2['diagonal_main'])
    dist += abs(fp1['diagonal_anti'] - fp2['diagonal_anti'])
    return dist / 50.0


# ═══════════════════════════════════════════════════════════
# 增量採樣主程序
# ═══════════════════════════════════════════════════════════

def run_incremental_sampling(
    anchors: List[Dict],
    row_permutations: Dict[str, List[List[int]]],
    batch_size: int = 5,
    max_batches: int = 5,
    time_limit: int = 180
) -> Dict:
    """執行增量採樣"""
    
    print("\n" + "=" * 70)
    print("┌─ 增量化多解空間採樣系統啟動 ──────────────────────────────┐")
    print(f"│  批大小: {batch_size:10d}                                │")
    print(f"│  最大批數: {max_batches:10d}                               │")
    print(f"│  每批時間: {time_limit:6d}秒                               │")
    print("└───────────────────────────────────────────────────┘")
    
    collector = MultiSolutionCollector(anchors, row_permutations)
    all_solutions = []
    all_fingerprints = []
    anchor_positions = {(a['row']-1, a['col']-1): a['value'] for a in anchors}
    
    start_time = time.time()
    
    for batch in range(1, max_batches + 1):
        print(f"\n{'='*70}")
        print(f"  【第 {batch} 批】收集 {batch_size} 個解")
        print(f"{'='*70}")
        
        solutions = collector.collect_solutions(solution_limit=batch_size, time_limit=time_limit)
        
        if not solutions:
            print(f"\n  ⚠️ 未找到新解")
            break
        
        for grid in solutions:
            fp = compute_gene_fingerprint(grid, anchor_positions)
            all_solutions.append(grid)
            all_fingerprints.append(fp)
            print(f"  ✓ 解 #{len(all_solutions)} 收錄 (適應度={fp['total_fitness']:.4f})")
    
    elapsed = time.time() - start_time
    
    # 聚類分析
    if all_fingerprints:
        clusters = []
        used = set()
        threshold = 0.05
        
        for i in range(len(all_fingerprints)):
            if i in used:
                continue
            cluster = [i]
            used.add(i)
            for j in range(len(all_fingerprints)):
                if j not in used:
                    dist = compute_fingerprint_distance(all_fingerprints[i], all_fingerprints[j])
                    if dist < threshold:
                        cluster.append(j)
                        used.add(j)
            clusters.append(cluster)
        
        essential_count = len(clusters)
    else:
        clusters = []
        essential_count = 0
    
    return {
        'total_solutions': len(all_solutions),
        'essential_solutions': essential_count,
        'clusters': clusters,
        'solutions': all_solutions,
        'fingerprints': all_fingerprints,
        'sampling_time': elapsed,
        'batch_count': batch
    }


def main():
    """主程序"""
    
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║   符闔博弈優選策略 - 增量化多解空間採樣 V20.0            ║")
    print("║                 「7 15 3 9」超級數獨                   ║")
    print("╚" + "═" * 68 + "╝")
    
    # 載入配置
    print("\n[載入] 錨點和排列...")
    anchors = load_anchors()
    print(f"  錨點: {len(anchors)}")
    
    row_permutations = load_permutations()
    total_perms = sum(len(v) for v in row_permutations.values())
    print(f"  排列總數: {total_perms:,}")
    
    # 分析每行排列
    print("\n[分析] 各行排列狀態:")
    for i, letter in enumerate('ABCDEFGHIJKLMNOP'):
        if letter in row_permutations:
            perms = len(row_permutations[letter])
            known = sum(1 for a in anchors if a['row']-1 == i)
            status = "✓" if perms > 0 else "⚠️"
            print(f"  行{letter}: {perms:7d} 排列, 已知{known}/16 {status}")
    
    # 執行採樣
    result = run_incremental_sampling(
        anchors=anchors,
        row_permutations=row_permutations,
        batch_size=5,
        max_batches=5,
        time_limit=180
    )
    
    # 本質解估算報告
    print("\n" + "=" * 70)
    print("┌─ 採樣結果摘要 ────────────────────────────────────────────┐")
    print(f"│  總採樣解數: {result['total_solutions']:17d}                      │")
    print(f"│  本質解數: {result['essential_solutions']:20d}                     │")
    print(f"│  採樣時間: {result['sampling_time']:17.2f}秒                      │")
    
    if result['essential_solutions'] == 0:
        print("│  結論: ❌ 未找到解，約束過度緊密                     │")
    elif result['essential_solutions'] == 1:
        print("│  結論: ✅ 唯一解數獨                               │")
    else:
        print(f"│  結論: ⚠️ {result['essential_solutions']} 個本質解                     │")
    
    print("└───────────────────────────────────────────────────┘")
    
    # 保存結果
    output = {
        'metadata': {
            'version': 'V20.0',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'sequence': '7 15 3 9'
        },
        'summary': {
            'total_solutions': result['total_solutions'],
            'essential_solutions': result['essential_solutions'],
            'sampling_time': result['sampling_time'],
            'batch_count': result['batch_count']
        },
        'solutions': result['solutions'][:10],  # 保存前 10 個解
        'fingerprints': result['fingerprints'][:10] if result['fingerprints'] else [],
        'clusters': result['clusters']
    }
    
    with open('incremental_sampling_result.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 結果已保存至: incremental_sampling_result.json")
    
    return result


if __name__ == '__main__':
    main()
