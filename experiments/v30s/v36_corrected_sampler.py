#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量化多解空间采样排列生成算法 V36.3 (修正版)

关键修正：使用 sudoku_config.json 的正确锚点配置
- 55 锚点（来自 sudoku_config.json）
- C 行：5 个锚点（非完全固定）
- D 行：4 个锚点（非完全固定）
"""

import json
import time
import hashlib
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime
from ortools.sat.python import cp_model
import random


GRID_SIZE = 16
BOX_SIZE = 4
SEQUENCE = [7, 15, 3, 9]


def load_anchors_from_config(config_file: str = 'sudoku_config.json') -> List[Dict]:
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['known_digits']


class IncrementalCPSATSampler:
    def __init__(self, anchors: List[Dict]):
        self.anchors = anchors
        self.anchors_set = {(a['row'] - 1, a['col'] - 1): a['value'] for a in anchors}
        self.non_anchor_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                                  if (r, c) not in self.anchors_set]
        self.solutions: List[List[List[int]]] = []
        self.solution_hashes: Set[str] = set()
        
    def _build_model(self) -> cp_model.CpModel:
        model = cp_model.CpModel()
        x = {}
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                key = (r, c)
                if key in self.anchors_set:
                    x[key] = model.NewConstant(self.anchors_set[key])
                else:
                    x[key] = model.NewIntVar(1, GRID_SIZE, f'x_{r}_{c}')
        
        for r in range(GRID_SIZE):
            model.AddAllDifferent([x[(r, c)] for c in range(GRID_SIZE)])
        for c in range(GRID_SIZE):
            model.AddAllDifferent([x[(r, c)] for r in range(GRID_SIZE)])
        for br in range(4):
            for bc in range(4):
                box_cells = []
                for dr in range(BOX_SIZE):
                    for dc in range(BOX_SIZE):
                        r = br * BOX_SIZE + dr
                        c = bc * BOX_SIZE + dc
                        box_cells.append(x[(r, c)])
                model.AddAllDifferent(box_cells)
        return model
    
    def _extract_solution(self, solver: cp_model.CpSolver, model: cp_model.CpModel) -> Optional[List[List[int]]]:
        try:
            grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
            for (r, c), v in self.anchors_set.items():
                grid[r][c] = v
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if (r, c) not in self.anchors_set:
                        var_name = f'x_{r}_{c}'
                        for v in model._variables:
                            if v.Name() == var_name:
                                grid[r][c] = solver.Value(v)
                                break
            return grid
        except Exception as e:
            print(f"  [Error] 提取解失败: {e}")
            return None
    
    def _get_solution_hash(self, grid: List[List[int]]) -> str:
        flat = tuple(tuple(row) for row in grid)
        return hashlib.sha256(json.dumps(flat, ensure_ascii=False).encode()).hexdigest()[:20]
    
    def _hamming_distance(self, g1: List[List[int]], g2: List[List[int]]) -> int:
        count = 0
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if g1[r][c] != g2[r][c]:
                    count += 1
        return count
    
    def _is_duplicate(self, new_grid: List[List[int]], threshold: int = 1) -> bool:
        new_hash = self._get_solution_hash(new_grid)
        if new_hash in self.solution_hashes:
            return True
        for sol in self.solutions:
            dist = self._hamming_distance(new_grid, sol)
            if dist < threshold:
                return True
        return False
    
    def _add_anti_constraint(self, model: cp_model.CpModel, ref_sol: List[List[int]],
                              n_positions: int = 5) -> List[Tuple]:
        available = [pos for pos in self.non_anchor_cells]
        if len(available) < n_positions:
            n_positions = len(available)
        selected = random.sample(available, n_positions)
        for (r, c) in selected:
            ref_val = ref_sol[r][c]
            for v in model._variables:
                if v.Name() == f'x_{r}_{c}':
                    model.Add(v != ref_val)
                    break
        return selected
    
    def collect_solutions(self, target: int = 100, time_per_solution: float = 45.0,
                          total_time_limit: float = 600.0) -> List[List[List[int]]]:
        print(f"\n  开始增量采样（目标{target}解）...")
        t_start = time.time()
        
        print("  [Phase 1] 搜索基础解...")
        model = self._build_model()
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_per_solution
        solver.parameters.num_search_workers = 8
        solver.parameters.log_search_progress = True
        
        status = solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"  ⚠️ 无法找到基础解 (Status={status})")
            return []
        
        sol1 = self._extract_solution(solver, model)
        if sol1 and not self._is_duplicate(sol1):
            self.solutions.append(sol1)
            self.solution_hashes.add(self._get_solution_hash(sol1))
            t1 = time.time() - t_start
            print(f"  ✓ 第1解，耗时{t1:.1f}s")
        else:
            print(f"  × 第1解提取失败")
            return []
        
        for i in range(2, target + 1):
            t_elapsed = time.time() - t_start
            if t_elapsed > total_time_limit:
                print(f"  ⏱ 超时（{t_elapsed:.0f}s > {total_time_limit}s）")
                break
            
            if i % 5 == 0:
                print(f"  已收集 {len(self.solutions)} 解，继续搜索...")
            
            ref_sol = random.choice(self.solutions)
            if len(self.solutions) <= 10:
                n_hints = 3
            elif len(self.solutions) <= 50:
                n_hints = 5
            else:
                n_hints = 8
            
            model = self._build_model()
            self._add_anti_constraint(model, ref_sol, n_hints)
            
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = min(time_per_solution, total_time_limit - t_elapsed)
            solver.parameters.num_search_workers = 8
            solver.parameters.log_search_progress = False
            
            status = solver.Solve(model)
            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                new_sol = self._extract_solution(solver, model)
                if new_sol and not self._is_duplicate(new_sol):
                    self.solutions.append(new_sol)
                    self.solution_hashes.add(self._get_solution_hash(new_sol))
                    print(f"  ✓ 第{len(self.solutions)}解")
                else:
                    print(f"  - 第{i}次尝试：解重复")
            else:
                print(f"  × 第{i}次尝试：无解/超时 (Status={status})")
        
        return self.solutions
    
    def compute_divergence_points(self) -> List[Dict]:
        if len(self.solutions) < 2:
            return []
        entropy_map = defaultdict(float)
        for (r, c) in self.non_anchor_cells:
            values = [sol[r][c] for sol in self.solutions]
            unique_vals = len(set(values))
            entropy_map[(r, c)] = unique_vals / 16.0
        
        sorted_positions = sorted(entropy_map.items(), key=lambda x: -x[1])
        divergence_points = []
        for pos, entropy in sorted_positions[:20]:
            r, c = pos
            values = sorted(set(sol[r][c] for sol in self.solutions))
            divergence_points.append({
                'position': f'({r},{c})',
                'row': r + 1, 'col': c + 1,
                'entropy': round(entropy, 4),
                'unique_values': len(values),
                'value_set': values[:8] if len(values) > 8 else values
            })
        return divergence_points


def run_incremental_sampling(anchors: List[Dict], target_samples: int = 100,
                             output_file: str = 'v36_v36_3_result.json') -> Dict:
    print("=" * 60)
    print("  增量化多解空间采样排列生成算法 V36.3")
    print("=" * 60)
    print(f"\n  锚点数量: {len(anchors)}")
    print(f"  目标样本: {target_samples}")
    print(f"  网格规模: {GRID_SIZE}x{GRID_SIZE}")
    print(f"  未知位置: {GRID_SIZE * GRID_SIZE - len(anchors)}")
    
    t_start = time.time()
    sampler = IncrementalCPSATSampler(anchors)
    solutions = sampler.collect_solutions(target=target_samples, time_per_solution=45.0, total_time_limit=600.0)
    total_time = time.time() - t_start
    divergence_points = sampler.compute_divergence_points()
    
    results = {
        'metadata': {'version': 'V36.3', 'timestamp': datetime.now().isoformat(),
                     'anchors_count': len(anchors), 'target_samples': target_samples,
                     'method': '增量CP-SAT采样（修正版）'},
        'summary': {'total_solutions': len(solutions), 'total_time_seconds': round(total_time, 2),
                    'avg_time_per_solution': round(total_time / max(1, len(solutions)), 2),
                    'sampling_efficiency': round(len(solutions) / max(0.1, total_time) * 60, 2),
                    'unknown_cells': len(sampler.non_anchor_cells)},
        'divergence_points': divergence_points[:10],
        'solutions': []
    }
    
    for i, sol in enumerate(solutions):
        sol_hash = sampler._get_solution_hash(sol)
        row_hashes = [hashlib.md5(str(tuple(sol[r])).encode()).hexdigest()[:6] for r in range(GRID_SIZE)]
        hamming = sampler._hamming_distance(sol, solutions[i-1]) if i > 0 else None
        results['solutions'].append({'id': i + 1, 'hash': sol_hash, 'row_features': row_hashes,
                                     'hamming_from_prev': hamming})
    
    print("\n" + "=" * 60)
    print(f"  总耗时: {total_time:.2f} 秒 | 获取解数: {len(solutions)} | 效率: {results['summary']['sampling_efficiency']:.2f} 解/分钟")
    if divergence_points:
        print("  分叉点:")
        for dp in divergence_points[:5]:
            print(f"    {dp['position']} (熵={dp['entropy']:.3f})")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  💾 结果: {output_file}")
    return results


if __name__ == '__main__':
    anchors = load_anchors_from_config()
    print(f"加载 {len(anchors)} 个锚点（来自 sudoku_config.json）")
    row_counts = Counter(a['row'] for a in anchors)
    print(f'C行: {row_counts.get(3, 0)} 个 | D行: {row_counts.get(4, 0)} 个')
    run_incremental_sampling(anchors, target_samples=100)
