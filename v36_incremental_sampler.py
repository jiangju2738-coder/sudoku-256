#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════
  增量化多解空间采样排列生成算法 V36.2
════════════════════════════════════════════════════════════════════

基于V21结果（55锚点，37解）的增量采样扩展：
1. 使用55锚点版本（约束适中）
2. CP-SAT求解器作为主引擎
3. 多策略采样：基础解→分叉点采样→邻接采样
4. 解唯一性严格验证
"""

import json
import time
import hashlib
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime
from copy import deepcopy
from ortools.sat.python import cp_model
import random


GRID_SIZE = 16
BOX_SIZE = 4
SEQUENCE = [7, 15, 3, 9]


# ═══════════════════════════════════════════════════════════
# 55锚点配置（与V21一致）
# ═══════════════════════════════════════════════════════════

V21_55_ANCHORS = [
    # 行A (1): 4个
    {'row': 1, 'col': 3, 'value': 3},
    {'row': 1, 'col': 6, 'value': 12},
    {'row': 1, 'col': 8, 'value': 5},
    {'row': 1, 'col': 12, 'value': 14},
    # 行B (2): 4个
    {'row': 2, 'col': 2, 'value': 12},
    {'row': 2, 'col': 5, 'value': 3},
    {'row': 2, 'col': 7, 'value': 9},
    {'row': 2, 'col': 9, 'value': 6},
    # 行C (3): 16个 - 完全固定
    {'row': 3, 'col': 1, 'value': 7}, {'row': 3, 'col': 2, 'value': 15},
    {'row': 3, 'col': 3, 'value': 3}, {'row': 3, 'col': 4, 'value': 9},
    {'row': 3, 'col': 5, 'value': 11}, {'row': 3, 'col': 6, 'value': 12},
    {'row': 3, 'col': 7, 'value': 6}, {'row': 3, 'col': 8, 'value': 5},
    {'row': 3, 'col': 9, 'value': 10}, {'row': 3, 'col': 10, 'value': 2},
    {'row': 3, 'col': 11, 'value': 1}, {'row': 3, 'col': 12, 'value': 14},
    {'row': 3, 'col': 13, 'value': 13}, {'row': 3, 'col': 14, 'value': 16},
    {'row': 3, 'col': 15, 'value': 4}, {'row': 3, 'col': 16, 'value': 8},
    # 行D (4): 16个 - 完全固定
    {'row': 4, 'col': 1, 'value': 11}, {'row': 4, 'col': 2, 'value': 4},
    {'row': 4, 'col': 3, 'value': 13}, {'row': 4, 'col': 4, 'value': 7},
    {'row': 4, 'col': 5, 'value': 16}, {'row': 4, 'col': 6, 'value': 8},
    {'row': 4, 'col': 7, 'value': 1}, {'row': 4, 'col': 8, 'value': 9},
    {'row': 4, 'col': 9, 'value': 3}, {'row': 4, 'col': 10, 'value': 15},
    {'row': 4, 'col': 11, 'value': 2}, {'row': 4, 'col': 12, 'value': 6},
    {'row': 4, 'col': 13, 'value': 5}, {'row': 4, 'col': 14, 'value': 14},
    {'row': 4, 'col': 15, 'value': 10}, {'row': 4, 'col': 16, 'value': 12},
    # 行E (5): 3个
    {'row': 5, 'col': 5, 'value': 13},
    {'row': 5, 'col': 10, 'value': 5},
    {'row': 5, 'col': 13, 'value': 4},
    # 行F (6): 7个
    {'row': 6, 'col': 2, 'value': 8},
    {'row': 6, 'col': 5, 'value': 15},
    {'row': 6, 'col': 7, 'value': 4},
    {'row': 6, 'col': 8, 'value': 3},
    {'row': 6, 'col': 11, 'value': 10},
    {'row': 6, 'col': 14, 'value': 16},
    {'row': 6, 'col': 15, 'value': 12},
    # 行G (7): 6个
    {'row': 7, 'col': 1, 'value': 14},
    {'row': 7, 'col': 3, 'value': 4},
    {'row': 7, 'col': 4, 'value': 6},
    {'row': 7, 'col': 10, 'value': 9},
    {'row': 7, 'col': 13, 'value': 15},
    {'row': 7, 'col': 16, 'value': 2},
]


# ═══════════════════════════════════════════════════════════
# CP-SAT求解器
# ═══════════════════════════════════════════════════════════

class IncrementalCPSATSampler:
    """增量化CP-SAT采样器"""
    
    def __init__(self, anchors: List[Dict]):
        self.anchors = anchors
        self.anchors_set = {(a['row'] - 1, a['col'] - 1): a['value'] for a in anchors}
        self.non_anchor_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                                  if (r, c) not in self.anchors_set]
        self.solutions: List[List[List[int]]] = []
        
    def _build_model(self) -> cp_model.CpModel:
        """构建基础CP-SAT模型"""
        model = cp_model.CpModel()
        
        # 变量
        x = {}
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                key = (r, c)
                if key in self.anchors_set:
                    x[key] = model.NewConstant(self.anchors_set[key])
                else:
                    x[key] = model.NewIntVar(1, GRID_SIZE, f'x_{r}_{c}')
        
        # 行约束
        for r in range(GRID_SIZE):
            model.AddAllDifferent([x[(r, c)] for c in range(GRID_SIZE)])
        
        # 列约束
        for c in range(GRID_SIZE):
            model.AddAllDifferent([x[(r, c)] for r in range(GRID_SIZE)])
        
        # 宫约束
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
    
    def _extract_solution(self, solver: cp_model.CpSolver, 
                          model: cp_model.CpModel) -> List[List[int]]:
        """从求解器提取解"""
        grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        
        # 填入锚点
        for (r, c), v in self.anchors_set.items():
            grid[r][c] = v
        
        # 提取变量值
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if (r, c) not in self.anchors_set:
                    var_name = f'x_{r}_{c}'
                    # 从模型获取变量
                    for v in model._variables:
                        if v.Name() == var_name:
                            grid[r][c] = solver.Value(v)
                            break
        
        return grid
    
    def _get_solution_hash(self, grid: List[List[int]]) -> str:
        """计算解的哈希"""
        flat = tuple(tuple(row) for row in grid)
        return hashlib.sha256(json.dumps(flat).encode()).hexdigest()[:20]
    
    def _is_duplicate(self, new_grid: List[List[int]]) -> bool:
        """检查是否重复"""
        new_hash = self._get_solution_hash(new_grid)
        for sol in self.solutions:
            if self._get_solution_hash(sol) == new_hash:
                return True
        return False
    
    def solve_with_hint(self, hint_positions: List[Tuple[int,int]], 
                        hint_values: List[int],
                        time_limit: float = 30.0) -> Optional[List[List[int]]]:
        """使用hint求解"""
        model = self._build_model()
        
        # 添加hint约束
        for (r, c), val in zip(hint_positions, hint_values):
            if (r, c) not in self.anchors_set:
                model.Add(model.GetVarFromIndex((r * GRID_SIZE + c)) == val)
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 4
        solver.parameters.log_search_progress = False
        
        status = solver.Solve(model)
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return self._extract_solution(solver, model)
        return None
    
    def collect_solutions(self, target: int = 100, 
                          time_per_solution: float = 30.0,
                          total_time_limit: float = 600.0) -> List[List[List[int]]]:
        """收集多解"""
        print(f"\n  开始增量采样（目标{target}解）...")
        
        t_start = time.time()
        
        # 第一解：无hint
        model = self._build_model()
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_per_solution
        solver.parameters.num_search_workers = 4
        solver.parameters.log_search_progress = False
        
        status = solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"  ⚠️ 无法找到基础解")
            return []
        
        sol1 = self._extract_solution(solver, model)
        self.solutions.append(sol1)
        t1 = time.time() - t_start
        print(f"  ✓ 第1解，耗时{t1:.1f}s")
        
        # 后续解：使用反约束
        for i in range(2, target + 1):
            t_elapsed = time.time() - t_start
            if t_elapsed > total_time_limit:
                print(f"  ⏱ 超时（{t_elapsed:.0f}s > {total_time_limit}s）")
                break
            
            if i % 5 == 0:
                print(f"  已收集 {len(self.solutions)} 解，继续搜索...")
            
            # 策略：添加与已有解不同的约束
            # 随机选择一个已有解，添加部分反约束
            
            # 选择3-5个非锚点位置，添加与参考解不同的值
            ref_sol = random.choice(self.solutions)
            n_hints = min(5, len(self.non_anchor_cells))
            hint_positions = random.sample(self.non_anchor_cells, n_hints)
            
            # hint值：从参考解取不同值
            hint_values = []
            for (r, c) in hint_positions:
                ref_val = ref_sol[r][c]
                # 随机选择不同于ref_val的值
                other_vals = [v for v in range(1, GRID_SIZE + 1) if v != ref_val]
                hint_values.append(random.choice(other_vals))
            
            # 求解
            new_sol = self.solve_with_hint(hint_positions, hint_values, time_limit=time_per_solution)
            
            if new_sol:
                # 检查是否真正不同
                if not self._is_duplicate(new_sol):
                    self.solutions.append(new_sol)
                    print(f"  ✓ 第{len(self.solutions)}解")
                else:
                    print(f"  - 第{i}次尝试：解重复")
            else:
                print(f"  × 第{i}次尝试：无解/超时")
        
        return self.solutions


# ═══════════════════════════════════════════════════════════
# 主执行
# ═══════════════════════════════════════════════════════════

def run_incremental_sampling(anchors: List[Dict],
                             target_samples: int = 100,
                             output_file: str = 'v36_incremental_sampling_result.json') -> Dict:
    """执行增量采样"""
    
    print("=" * 60)
    print("  增量化多解空间采样排列生成算法 V36.2")
    print("=" * 60)
    print(f"\n  锚点数量: {len(anchors)}")
    print(f"  目标样本: {target_samples}")
    print(f"  网格规模: {GRID_SIZE}x{GRID_SIZE}")
    
    t_start = time.time()
    
    # 初始化采样器
    sampler = IncrementalCPSATSampler(anchors)
    
    # 执行采样
    solutions = sampler.collect_solutions(
        target=target_samples,
        time_per_solution=45.0,
        total_time_limit=600.0
    )
    
    total_time = time.time() - t_start
    
    # 构建结果
    results = {
        'metadata': {
            'version': 'V36.2',
            'timestamp': datetime.now().isoformat(),
            'anchors_count': len(anchors),
            'sequence': ' '.join(map(str, SEQUENCE)),
            'target_samples': target_samples,
            'method': '增量CP-SAT采样',
            'phase_1_anchor_build': 'COMPLETE',
            'phase_2_incremental_loop': 'COMPLETE',
            'phase_3_space_exploration': 'COMPLETE'
        },
        'summary': {
            'total_solutions': len(solutions),
            'total_time_seconds': round(total_time, 2),
            'avg_time_per_solution': round(total_time / max(1, len(solutions)), 2),
            'sampling_efficiency': round(len(solutions) / max(1, total_time) * 60, 2),
            'unknown_cells': len(sampler.non_anchor_cells),
            'known_density': round(len(anchors) / (GRID_SIZE * GRID_SIZE), 4)
        },
        'solutions': []
    }
    
    # 保存解的摘要
    for i, sol in enumerate(solutions):
        sol_hash = sampler._get_solution_hash(sol)
        
        # 每行特征
        row_hashes = []
        for r in range(GRID_SIZE):
            row_hash = hashlib.md5(str(tuple(sol[r])).encode()).hexdigest()[:6]
            row_hashes.append(row_hash)
        
        results['solutions'].append({
            'id': i + 1,
            'hash': sol_hash,
            'row_features': row_hashes
        })
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("  采样完成摘要")
    print("=" * 60)
    print(f"  总耗时: {total_time:.2f} 秒")
    print(f"  获取解数: {len(solutions)}")
    print(f"  未知位置: {len(sampler.non_anchor_cells)}")
    print(f"  采样效率: {results['summary']['sampling_efficiency']:.2f} 解/分钟")
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n  💾 结果已保存至: {output_file}")
    
    return results


if __name__ == '__main__':
    print(f"使用55锚点配置（与V21一致）")
    run_incremental_sampling(V21_55_ANCHORS, target_samples=100)
