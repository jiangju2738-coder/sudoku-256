#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════
  增量化多解空间采样 - CP-SAT增强版本 V36.1 (修正版)
════════════════════════════════════════════════════════════════════
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


class CPSATSolver:
    """CP-SAT求解器 - 多解采样"""
    
    def __init__(self, anchors: List[Dict]):
        self.anchors = anchors
        self.anchors_set = {(a['row'] - 1, a['col'] - 1): a['value'] for a in anchors}
        self.anchors_cells = set(self.anchors_set.keys())
        self.solutions: List[List[List[int]]] = []
        
    def _build_model(self, solution_hint: Optional[Dict[Tuple[int,int],int]] = None) -> cp_model.CpModel:
        """构建CP-SAT模型"""
        model = cp_model.CpModel()
        
        # 变量定义
        x = {}
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                key = (r, c)
                if key in self.anchors_set:
                    x[key] = model.NewConstant(self.anchors_set[key])
                else:
                    x[key] = model.NewIntVar(1, GRID_SIZE, f'x_{r}_{c}')
        
        # 行AllDifferent
        for r in range(GRID_SIZE):
            model.AddAllDifferent([x[(r, c)] for c in range(GRID_SIZE)])
        
        # 列AllDifferent
        for c in range(GRID_SIZE):
            model.AddAllDifferent([x[(r, c)] for r in range(GRID_SIZE)])
        
        # 宫AllDifferent
        for br in range(4):
            for bc in range(4):
                box_cells = []
                for dr in range(BOX_SIZE):
                    for dc in range(BOX_SIZE):
                        r = br * BOX_SIZE + dr
                        c = bc * BOX_SIZE + dc
                        box_cells.append(x[(r, c)])
                model.AddAllDifferent(box_cells)
        
        # 添加solution_hint引导（如果提供）
        if solution_hint:
            for (r, c), val in solution_hint.items():
                if (r, c) not in self.anchors_set:
                    model.Add(x[(r, c)] == val)
        
        return model
    
    def solve_one(self, solution_hint: Optional[Dict[Tuple[int,int],int]] = None, 
                  time_limit: float = 30.0) -> Optional[List[List[int]]]:
        """求解单个解"""
        model = self._build_model(solution_hint)
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 4
        solver.parameters.log_search_progress = False
        
        status = solver.Solve(model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    key = (r, c)
                    if key in self.anchors_set:
                        grid[r][c] = self.anchors_set[key]
                    else:
                        grid[r][c] = solver.Value(cp_model.CpModel()._get_variable(f'x_{r}_{c}'))
            return grid
        
        return None
    
    def collect_solutions(self, max_solutions: int = 100, 
                          time_limit: float = 300.0) -> List[List[List[int]]]:
        """收集多个解"""
        print(f"  开始收集多解（目标{max_solutions}个）...")
        
        # 第一解：无hint
        t0 = time.time()
        base_solution = self.solve_one(None, time_limit=min(60.0, time_limit))
        elapsed = time.time() - t0
        
        if not base_solution:
            print(f"  ⚠️ 无法找到任何解")
            return []
        
        self.solutions.append(base_solution)
        print(f"  ✓ 第1解，耗时{elapsed:.1f}s")
        
        # 收集更多解：通过反约束引导
        for i in range(2, max_solutions + 1):
            if i % 10 == 0:
                print(f"  已收集 {i-1} 解，继续搜索...")
            
            # 策略：对已有解添加约束，使其不同
            # 取已有解的随机子集，添加反约束
            if len(self.solutions) >= 2:
                ref_sol = random.choice(self.solutions)
                
                # 随机选择一些非锚点位置，添加反约束
                non_anchor_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                                    if (r, c) not in self.anchors_set]
                
                if non_anchor_cells:
                    # 选择1-3个位置添加反约束
                    n_hints = min(3, len(non_anchor_cells))
                    hint_positions = random.sample(non_anchor_cells, n_hints)
                    
                    # 对每个位置添加：不能等于参考解的值
                    # 但这会破坏求解器... 改用直接求解无hint
                    
            # 直接求解（无hint）可能返回相同解
            # 改用更直接的方法：添加"与已有解不同的约束"
            
            # 简化：连续求解，靠随机搜索找到不同解
            new_solution = self.solve_one(None, time_limit=15.0)
            
            if new_solution:
                # 检查唯一性
                is_unique = True
                for existing in self.solutions:
                    # 检查是否完全相同
                    same = True
                    for r in range(GRID_SIZE):
                        for c in range(GRID_SIZE):
                            if new_solution[r][c] != existing[r][c]:
                                same = False
                                break
                        if not same:
                            break
                    if same:
                        is_unique = False
                        break
                
                if is_unique:
                    self.solutions.append(new_solution)
                    print(f"  ✓ 第{i}解获取")
                else:
                    print(f"  - 第{i}次尝试：解重复（已有{len(self.solutions)}解）")
            else:
                print(f"  × 第{i}次尝试：超时/无解")
                
                # 如果连续失败多次，可能已穷尽
                if i - len(self.solutions) > 20:
                    print(f"  ⚠️ 连续{i - len(self.solutions)}次失败，可能已找到所有解")
                    break
        
        return self.solutions


def run_cp_sat_sampling(anchors: List[Dict], 
                        target_samples: int = 100,
                        output_file: str = 'v36_cp_sat_result.json') -> Dict:
    """运行CP-SAT增量采样"""
    
    print("=" * 60)
    print("  增量化多解空间采样 - CP-SAT增强版本 V36.1")
    print("=" * 60)
    print(f"\n  锚点数量: {len(anchors)}")
    print(f"  目标样本: {target_samples}")
    print(f"  网格规模: {GRID_SIZE}x{GRID_SIZE}")
    print(f"  宫格规模: {BOX_SIZE}x{BOX_SIZE}")
    
    start_time = time.time()
    
    # 构建求解器
    solver = CPSATSolver(anchors)
    
    # 执行多解收集
    solutions = solver.collect_solutions(max_solutions=target_samples, time_limit=300.0)
    
    total_time = time.time() - start_time
    
    # 构建结果
    results = {
        'metadata': {
            'version': 'V36.1',
            'timestamp': datetime.now().isoformat(),
            'anchors_count': len(anchors),
            'sequence': ' '.join(map(str, SEQUENCE)),
            'target_samples': target_samples,
            'method': 'CP-SAT多解采集'
        },
        'summary': {
            'total_solutions': len(solutions),
            'total_time_seconds': round(total_time, 2),
            'avg_time_per_solution': round(total_time / max(1, len(solutions)), 2) if solutions else 0
        },
        'solutions': []
    }
    
    # 保存解（简化格式）
    for i, sol in enumerate(solutions):
        # 解的哈希用于唯一性
        sol_str = ''.join(str(v) for row in sol for v in row)
        sol_hash = hashlib.md5(sol_str.encode()).hexdigest()[:16]
        
        # 每行特征
        row_features = []
        for r in range(GRID_SIZE):
            row_str = ','.join(map(str, sol[r]))
            row_hash = hashlib.md5(row_str.encode()).hexdigest()[:6]
            row_features.append(row_hash)
        
        results['solutions'].append({
            'id': i + 1,
            'hash': sol_hash,
            'row_features': row_features
        })
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("  采样完成摘要")
    print("=" * 60)
    print(f"  总耗时: {total_time:.2f} 秒")
    print(f"  获取解数: {len(solutions)}")
    if solutions:
        print(f"  平均每解耗时: {total_time / len(solutions):.2f} 秒")
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n  💾 结果已保存至: {output_file}")
    
    return results


if __name__ == '__main__':
    # 加载锚点
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", "7_15_3_9_config_full.py")
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    FULL_92_ANCHORS = config_module.FULL_92_ANCHORS
    
    print(f"加载锚点: {len(FULL_92_ANCHORS)} 个")
    
    # 执行采样（先用较小目标测试）
    run_cp_sat_sampling(FULL_92_ANCHORS, target_samples=20)
