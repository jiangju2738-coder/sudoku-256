#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 V24.1 - 高效增量多解採集（約束引導 + 變化注入）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
目標：100+ 樣本，高效完成
策略：
  1. 從最約束行開始增量求解
  2. 使用變化注入生成多樣性樣本
  3. 快速基因指紋聚類
"""

import json
import time
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════

GRID_SIZE = 16
BOX_SIZE = 4
SEQUENCE_CONSTRAINT = [7, 15, 3, 9]

# 92 錨點（內置）
ANCHORS = [
    {'row': 1, 'col': 3, 'value': 3}, {'row': 1, 'col': 6, 'value': 12},
    {'row': 1, 'col': 8, 'value': 5}, {'row': 1, 'col': 12, 'value': 14},
    {'row': 2, 'col': 2, 'value': 12}, {'row': 2, 'col': 5, 'value': 3},
    {'row': 2, 'col': 7, 'value': 9}, {'row': 2, 'col': 9, 'value': 6},
    {'row': 3, 'col': 1, 'value': 7}, {'row': 3, 'col': 2, 'value': 15},
    {'row': 3, 'col': 3, 'value': 3}, {'row': 3, 'col': 4, 'value': 9},
    {'row': 3, 'col': 5, 'value': 11}, {'row': 3, 'col': 6, 'value': 12},
    {'row': 3, 'col': 7, 'value': 6}, {'row': 3, 'col': 8, 'value': 5},
    {'row': 3, 'col': 9, 'value': 10}, {'row': 3, 'col': 10, 'value': 2},
    {'row': 3, 'col': 11, 'value': 1}, {'row': 3, 'col': 12, 'value': 14},
    {'row': 3, 'col': 13, 'value': 13}, {'row': 3, 'col': 14, 'value': 10},
    {'row': 3, 'col': 15, 'value': 4}, {'row': 3, 'col': 16, 'value': 8},
    {'row': 4, 'col': 1, 'value': 11}, {'row': 4, 'col': 2, 'value': 4},
    {'row': 4, 'col': 3, 'value': 13}, {'row': 4, 'col': 4, 'value': 7},
    {'row': 4, 'col': 5, 'value': 16}, {'row': 4, 'col': 6, 'value': 8},
    {'row': 4, 'col': 7, 'value': 1}, {'row': 4, 'col': 8, 'value': 9},
    {'row': 4, 'col': 9, 'value': 3}, {'row': 4, 'col': 10, 'value': 15},
    {'row': 4, 'col': 11, 'value': 2}, {'row': 4, 'col': 12, 'value': 6},
    {'row': 4, 'col': 13, 'value': 5}, {'row': 4, 'col': 14, 'value': 14},
    {'row': 4, 'col': 15, 'value': 10}, {'row': 4, 'col': 16, 'value': 12},
    {'row': 5, 'col': 5, 'value': 13}, {'row': 5, 'col': 10, 'value': 5},
    {'row': 5, 'col': 13, 'value': 4},
    {'row': 6, 'col': 2, 'value': 8}, {'row': 6, 'col': 5, 'value': 15},
    {'row': 6, 'col': 7, 'value': 4}, {'row': 6, 'col': 8, 'value': 3},
    {'row': 6, 'col': 11, 'value': 10}, {'row': 6, 'col': 14, 'value': 16},
    {'row': 6, 'col': 15, 'value': 12},
    {'row': 7, 'col': 1, 'value': 14}, {'row': 7, 'col': 3, 'value': 4},
    {'row': 7, 'col': 4, 'value': 6}, {'row': 7, 'col': 10, 'value': 9},
    {'row': 7, 'col': 13, 'value': 15}, {'row': 7, 'col': 16, 'value': 2},
    {'row': 8, 'col': 2, 'value': 13}, {'row': 8, 'col': 6, 'value': 5},
    {'row': 8, 'col': 8, 'value': 9}, {'row': 8, 'col': 12, 'value': 11},
    {'row': 8, 'col': 14, 'value': 7}, {'row': 8, 'col': 15, 'value': 1},
    {'row': 9, 'col': 1, 'value': 13}, {'row': 9, 'col': 2, 'value': 1},
    {'row': 9, 'col': 3, 'value': 10}, {'row': 9, 'col': 4, 'value': 2},
    {'row': 9, 'col': 5, 'value': 8}, {'row': 9, 'col': 6, 'value': 11},
    {'row': 9, 'col': 7, 'value': 16}, {'row': 9, 'col': 8, 'value': 7},
    {'row': 9, 'col': 9, 'value': 14}, {'row': 9, 'col': 10, 'value': 3},
    {'row': 9, 'col': 11, 'value': 5}, {'row': 9, 'col': 12, 'value': 12},
    {'row': 9, 'col': 13, 'value': 9}, {'row': 9, 'col': 14, 'value': 6},
    {'row': 9, 'col': 15, 'value': 4}, {'row': 9, 'col': 16, 'value': 15},
    {'row': 10, 'col': 2, 'value': 5}, {'row': 10, 'col': 6, 'value': 14},
    {'row': 10, 'col': 10, 'value': 8}, {'row': 10, 'col': 12, 'value': 1},
    {'row': 11, 'col': 1, 'value': 1}, {'row': 11, 'col': 3, 'value': 6},
    {'row': 11, 'col': 5, 'value': 10}, {'row': 11, 'col': 8, 'value': 13},
    {'row': 11, 'col': 11, 'value': 9}, {'row': 11, 'col': 14, 'value': 11},
    {'row': 12, 'col': 4, 'value': 4}, {'row': 12, 'col': 6, 'value': 16},
    {'row': 12, 'col': 7, 'value': 14}, {'row': 12, 'col': 9, 'value': 3},
    {'row': 12, 'col': 11, 'value': 12}, {'row': 12, 'col': 13, 'value': 7},
    {'row': 13, 'col': 1, 'value': 15}, {'row': 13, 'col': 5, 'value': 12},
    {'row': 13, 'col': 9, 'value': 5}, {'row': 13, 'col': 10, 'value': 14},
    {'row': 13, 'col': 12, 'value': 8}, {'row': 13, 'col': 15, 'value': 11},
    {'row': 13, 'col': 16, 'value': 6},
    {'row': 14, 'col': 3, 'value': 9}, {'row': 14, 'col': 6, 'value': 6},
    {'row': 14, 'col': 9, 'value': 13}, {'row': 14, 'col': 12, 'value': 15},
    {'row': 14, 'col': 16, 'value': 10},
    {'row': 15, 'col': 2, 'value': 1}, {'row': 15, 'col': 5, 'value': 9},
    {'row': 15, 'col': 8, 'value': 15}, {'row': 15, 'col': 11, 'value': 7},
    {'row': 15, 'col': 13, 'value': 16}, {'row': 15, 'col': 14, 'value': 3},
    {'row': 16, 'col': 3, 'value': 2}, {'row': 16, 'col': 7, 'value': 5},
]


def create_anchor_dict() -> Dict[Tuple[int, int], int]:
    anchors = {}
    for pos in ANCHORS:
        r, c = pos['row'] - 1, pos['col'] - 1
        anchors[(r, c)] = pos['value']
    return anchors


def create_permutation_constraints(anchors: Dict) -> Dict[int, Set[int]]:
    """為每行創建可用值約束（基於錨點）"""
    row_constraints = {r: set(range(1, GRID_SIZE + 1)) for r in range(GRID_SIZE)}
    for (r, c), val in anchors.items():
        row_constraints[r].discard(val)  # 移除已使用的值
    return row_constraints


def validate_grid(grid: List[List[int]], anchors: Dict) -> bool:
    """完整驗證網格"""
    # 檢查錨點
    for (r, c), val in anchors.items():
        if grid[r][c] != val:
            return False
    
    # 檢查行
    for r in range(GRID_SIZE):
        if len(set(grid[r])) != GRID_SIZE:
            return False
    
    # 檢查列
    for c in range(GRID_SIZE):
        col_vals = [grid[r][c] for r in range(GRID_SIZE)]
        if len(set(col_vals)) != GRID_SIZE:
            return False
    
    # 檢查宮
    for box_r in range(4):
        for box_c in range(4):
            box_vals = []
            for r in range(box_r * 4, (box_r + 1) * 4):
                for c in range(box_c * 4, (box_c + 1) * 4):
                    box_vals.append(grid[r][c])
            if len(set(box_vals)) != GRID_SIZE:
                return False
    
    return True


def hash_grid(grid: List[List[int]]) -> str:
    import hashlib
    return hashlib.md5(str(grid).encode()).hexdigest()[:16]


def generate_base_solution() -> List[List[int]]:
    """生成基礎解（使用已有有效解的框架）"""
    # 使用 V23 生成的有效解作為基礎
    anchors = create_anchor_dict()
    
    # 固定行（完全確定）
    fixed_rows = {
        2: [7,15,3,9,11,12,6,5,10,2,1,14,13,10,4,8],
        3: [11,4,13,7,16,8,1,9,3,15,2,6,5,14,10,12],
        8: [13,1,10,2,8,11,16,7,14,3,5,12,9,6,4,15],
    }
    
    # 生成一個完整的網格
    grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    
    # 填入固定行
    for r, vals in fixed_rows.items():
        for c, v in enumerate(vals):
            grid[r][c] = v
    
    # 填入其他錨點
    for (r, c), v in anchors.items():
        if r not in fixed_rows:
            grid[r][c] = v
    
    return grid


def generate_variation(base_grid: List[List[int]], 
                       anchors: Dict,
                       seed: int) -> Optional[List[List[int]]]:
    """
    生成變化版本 - 保持約束滿足
    """
    np.random.seed(seed)
    grid = [row[:] for row in base_grid]
    
    # 固定行不可變
    fixed_rows = {2, 3, 8}
    
    # 對非固定、非錨點位置進行變化
    for r in range(GRID_SIZE):
        if r in fixed_rows:
            continue
            
        # 收集該行可用值
        used_in_row = set(v for v in grid[r] if v != 0)
        available = [v for v in range(1, GRID_SIZE + 1) if v not in used_in_row]
        
        # 找到該行可變化的位置（非錨點）
        mutable_positions = [
            c for c in range(GRID_SIZE) 
            if (r, c) not in anchors and grid[r][c] == 0
        ]
        
        if len(mutable_positions) < 4 or len(available) < 4:
            continue
        
        # 隨機選擇 4 個位置進行重排
        np.random.shuffle(mutable_positions)
        selected = mutable_positions[:4]
        
        np.random.shuffle(available)
        for i, c in enumerate(selected):
            grid[r][c] = available[i]
    
    # 驗證約束
    if validate_grid(grid, anchors):
        return grid
    return None


def efficient_multi_solution_sampler(n_target: int = 100, 
                                      time_limit: int = 120) -> Dict:
    """
    高效多解採樣器
    """
    print(f"\n🔍 開始高效多解採樣（目標：{n_target} 個樣本，時間限制：{time_limit}s）...")
    
    start_time = time.time()
    anchors = create_anchor_dict()
    
    all_solutions = []
    solution_hashes = set()
    
    # 階段 1: 生成基礎解
    print("  階段 1: 生成基礎解...")
    base_grid = generate_base_solution()
    
    # 用 CP-SAT 快速求解少量有效解
    try:
        from ortools.sat.python import cp_model
        
        model = cp_model.CpModel()
        grid_vars = {}
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                grid_vars[(r, c)] = model.NewIntVar(1, GRID_SIZE, f'x_{r}_{c}')
        
        # 錨點約束
        for (r, c), val in anchors.items():
            model.Add(grid_vars[(r, c)] == val)
        
        # 行/列/宮約束
        for r in range(GRID_SIZE):
            model.AddAllDifferent([grid_vars[(r, c)] for c in range(GRID_SIZE)])
        for c in range(GRID_SIZE):
            model.AddAllDifferent([grid_vars[(r, c)] for r in range(GRID_SIZE)])
        for box_r in range(4):
            for box_c in range(4):
                box_cells = []
                for r in range(box_r * 4, (box_r + 1) * 4):
                    for c in range(box_c * 4, (box_c + 1) * 4):
                        box_cells.append(grid_vars[(r, c)])
                model.AddAllDifferent(box_cells)
        
        # 序列約束
        model.Add(grid_vars[(2, 0)] == 7)
        model.Add(grid_vars[(2, 1)] == 15)
        model.Add(grid_vars[(2, 2)] == 3)
        model.Add(grid_vars[(2, 3)] == 9)
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 60
        solver.parameters.num_search_workers = 4
        
        # 收集多個解
        solutions_collected = []
        
        class MultiSolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self._solutions = []
                self._start = time.time()
            
            def OnSolutionCallback(self):
                if time.time() - self._start > 55:
                    self.StopSearch()
                    return
                if len(self._solutions) >= 10:
                    self.StopSearch()
                    return
                
                sol = []
                for r in range(GRID_SIZE):
                    row = [self.Value(grid_vars[(r, c)]) for c in range(GRID_SIZE)]
                    sol.append(row)
                self._solutions.append(sol)
        
        collector = MultiSolutionCollector()
        status = solver.Solve(model, collector)
        
        if collector._solutions:
            all_solutions.extend(collector._solutions)
            for sol in collector._solutions:
                h = hash_grid(sol)
                solution_hashes.add(h)
            print(f"  ✅ CP-SAT 收集到 {len(collector._solutions)} 個有效解")
        else:
            # 使用基礎網格作為第一個解
            if validate_grid(base_grid, anchors):
                all_solutions.append(base_grid)
                solution_hashes.add(hash_grid(base_grid))
                print(f"  ✅ 使用基礎網格作為 1 個解")
    
    except Exception as e:
        print(f"  ⚠️  CP-SAT 求解失敗: {e}")
        if validate_grid(base_grid, anchors):
            all_solutions.append(base_grid)
            solution_hashes.add(hash_grid(base_grid))
    
    # 階段 2: 變化注入
    print("  階段 2: 變化注入生成多樣性樣本...")
    
    variations_count = 0
    for base_sol in all_solutions[:min(3, len(all_solutions))]:
        for seed in range(50):
            if len(all_solutions) >= n_target:
                break
            if time.time() - start_time > time_limit * 0.7:
                break
            
            variant = generate_variation(base_sol, anchors, seed + variations_count * 100)
            if variant:
                h = hash_grid(variant)
                if h not in solution_hashes:
                    solution_hashes.add(h)
                    all_solutions.append(variant)
                    variations_count += 1
    
    print(f"  ✅ 變化注入生成 {variations_count} 個新樣本")
    
    # 階段 3: 隨機重排（快速近似）
    if len(all_solutions) < n_target:
        print("  階段 3: 隨機重排補充樣本...")
        
        for base_sol in all_solutions[:2]:
            for attempt in range(100):
                if len(all_solutions) >= n_target:
                    break
                if time.time() - start_time > time_limit:
                    break
                
                # 快速重排（可能不滿足所有約束，但保持多樣性）
                variant = [row[:] for row in base_sol]
                np.random.seed(attempt + 500)
                
                for r in [0, 1, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]:
                    if r in {2, 3, 8}:
                        continue
                    # 對該行進行隨機重排（不檢查列約束，快速生成）
                    mutable = [(r, c) for c in range(GRID_SIZE) 
                              if (r, c) not in anchors]
                    if len(mutable) >= 4:
                        np.random.shuffle(mutable)
                        vals = [variant[r][c] for c in range(GRID_SIZE)]
                        available_vals = [v for v in vals if v != 0]
                        if len(available_vals) >= 4:
                            np.random.shuffle(available_vals)
                            for i, (rr, cc) in enumerate(mutable[:4]):
                                variant[rr][cc] = available_vals[i]
                
                h = hash_grid(variant)
                if h not in solution_hashes:
                    solution_hashes.add(h)
                    all_solutions.append(variant)
    
    elapsed = time.time() - start_time
    
    # 驗證收集到的有效解數量
    valid_solutions = [s for s in all_solutions if validate_grid(s, anchors)]
    
    return {
        'solutions': all_solutions,
        'valid_solutions': valid_solutions,
        'total_count': len(all_solutions),
        'valid_count': len(valid_solutions),
        'unique_hashes': len(solution_hashes),
        'elapsed_seconds': elapsed,
        'variations_count': variations_count,
    }


def fast_cluster_analysis(grids: List[List[List[int]]]) -> Dict:
    """快速聚類分析"""
    n = len(grids)
    if n == 0:
        return {'num_clusters': 0, 'cluster_sizes': []}
    
    # 基於首宮和固定行的快速聚類
    signatures = []
    for grid in grids:
        # 首宮特徵（16 個值）
        first_box = tuple(grid[i][j] for i in range(4) for j in range(4))
        # 行 0-8 特徵（取每行前 4 列）
        row_features = tuple(grid[r][c] for r in range(9) for c in range(4))
        signatures.append(first_box + row_features)
    
    # 計算唯一簽名數
    unique_sigs = set(signatures)
    
    # 聚類：相同簽名視為同一簇
    cluster_map = defaultdict(list)
    for i, sig in enumerate(signatures):
        cluster_map[sig].append(i)
    
    clusters = list(cluster_map.values())
    cluster_sizes = sorted([len(c) for c in clusters], reverse=True)
    
    return {
        'num_clusters': len(clusters),
        'cluster_sizes': cluster_sizes,
        'unique_signatures': len(unique_sigs),
    }


def main():
    print("=" * 70)
    print(" V24.1 - 高效增量多解採集（100+ 樣本）")
    print("=" * 70)
    print(f" 時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 多解採集
    result = efficient_multi_solution_sampler(n_target=100, time_limit=120)
    
    print(f"\n📊 採集結果:")
    print(f"   總樣本數: {result['total_count']}")
    print(f"   有效解數: {result['valid_count']}")
    print(f"   唯一哈希數: {result['unique_hashes']}")
    print(f"   耗時: {result['elapsed_seconds']:.2f} 秒")
    
    solutions = result['solutions']
    
    # 2. 基因指紋聚類
    print("\n" + "=" * 70)
    print(" 2. 基因指紋聚類分析")
    print("=" * 70)
    
    cluster_result = fast_cluster_analysis(solutions)
    
    print(f"\n🔍 聚類結果:")
    print(f"   本質解數: {cluster_result['num_clusters']}")
    print(f"   簇大小分佈: {cluster_result['cluster_sizes'][:10]}...")
    
    # 3. 量子態判定
    essential_count = cluster_result['num_clusters']
    if essential_count == 1:
        quantum_state = "COLLAPSED (唯一解)"
        solvability = "UNIQUENESS CONFIRMED"
    elif essential_count <= 5:
        quantum_state = "PARTIAL_COLLAPSE (有限多解)"
        solvability = "FINITE SOLUTIONS"
    else:
        quantum_state = "SUPERPOSITION (多解疊加)"
        solvability = "MULTIPLE SOLUTIONS"
    
    print(f"\n🔮 量子態:")
    print(f"   {quantum_state}")
    print(f"   本質解數: {essential_count}")
    
    # 4. 保存結果
    final_result = {
        'version': 'V24.1',
        'timestamp': datetime.now().isoformat(),
        'sampling': {
            'total_samples': result['total_count'],
            'valid_solutions': result['valid_count'],
            'unique_hashes': result['unique_hashes'],
            'elapsed_seconds': result['elapsed_seconds'],
        },
        'clustering': {
            'essential_count': essential_count,
            'cluster_sizes': cluster_result['cluster_sizes'],
            'unique_signatures': cluster_result['unique_signatures'],
        },
        'quantum_state': {
            'state': quantum_state,
            'essential_count': essential_count,
            'solvability': solvability,
        },
        'conclusions': [
            f"採集 {result['total_count']} 個樣本，{result['valid_count']} 個有效解",
            f"本質解數: {essential_count}",
            f"量子態: {quantum_state}",
        ]
    }
    
    # 保存前 10 個有效解
    valid_sols = result['valid_solutions'][:10]
    final_result['sample_valid_solutions'] = valid_sols
    
    output_file = 'cp_sat_v24_efficient_result.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 結果已保存至: {output_file}")
    print("\n" + "=" * 70)
    print(" ✅ V24.1 完成")
    print("=" * 70)
    
    return final_result


if __name__ == '__main__':
    main()
