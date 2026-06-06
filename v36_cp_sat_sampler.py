#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════
  增量化多解空间采样 - CP-SAT增强版本 V36.1
════════════════════════════════════════════════════════════════════

改进策略：
1. 使用CP-SAT求解器作为主求解引擎
2. 通过solution_hint参数引导求解器探索不同解空间区域
3. 增量固定已知解，引导搜索新解区域
4. 多策略采样：随机初始解、分叉点采样、邻接图采样
"""

import json
import time
import hashlib
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set, Generator
from dataclasses import dataclass, field
from datetime import datetime
from copy import deepcopy
from ortools.sat.python import cp_model
import random


# ═══════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════

GRID_SIZE = 16
BOX_SIZE = 4
SEQUENCE = [7, 15, 3, 9]

# ═══════════════════════════════════════════════════════════
# 核心CP-SAT采样器
# ═══════════════════════════════════════════════════════════

class CPSATSolver:
    """CP-SAT求解器 - 多解采样"""
    
    def __init__(self, anchors: List[Dict]):
        self.anchors = anchors
        self.anchors_set = {(a['row'] - 1, a['col'] - 1): a['value'] for a in anchors}
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
                    # 锚点已固定
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
        
        # 序列约束：在首宫首行特定位置强制「7 15 3 9」
        # 位置：(2,0)=7, (2,1)=15, (2,2)=3, (2,3)=9
        # 这些已经被锚点固定，不需要额外约束
        
        # 添加solution_hint引导
        if solution_hint:
            for (r, c), val in solution_hint.items():
                if (r, c) not in self.anchors_set:
                    model.Add(x[(r, c)] == val)
        
        return model
    
    def solve(self, solution_hint: Optional[Dict[Tuple[int,int],int]] = None, 
              time_limit: float = 30.0) -> Optional[List[List[int]]]:
        """求解单个解"""
        model = self._build_model(solution_hint)
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 8
        solver.parameters.solution_limit = 1
        
        status = solver.Solve(model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    grid[r][c] = solver.Value(model._get_variable(f'x_{r}_{c}'))
            return grid
        
        return None
    
    def collect_solutions(self, max_solutions: int = 100, 
                          time_limit: float = 300.0) -> List[List[List[int]]]:
        """收集多个解"""
        # 首先获取一个基础解
        base_solution = self.solve(None, time_limit=60.0)
        if not base_solution:
            return []
        
        self.solutions.append(base_solution)
        print(f"  第1解获取，耗时{time_limit}秒")
        
        # 增量收集更多解
        # 策略：每次固定部分解，引导求解器探索新区域
        for i in range(1, max_solutions):
            if i % 10 == 0:
                print(f"  已收集 {i} 解，尝试引导搜索...")
            
            # 随机选择一个子集作为hint
            hint_cells = random.sample(
                [pos for pos in self.anchors_set.keys() 
                 if pos not in self.anchors_set],
                min(10, len(self.anchors_set))
            ) if any(pos not in self.anchors_set for pos in [(r,c) for r in range(16) for c in range(16)]) else []
            
            # 从已有解中随机采样hint
            hint = {}
            if hint_cells:
                ref_solution = random.choice(self.solutions)
                for pos in hint_cells:
                    if pos not in self.anchors_set:
                        hint[pos] = ref_solution[pos[0]][pos[1]]
            
            # 尝试求解
            new_solution = self.solve(hint if hint else None, time_limit=30.0)
            
            if new_solution:
                # 检查唯一性
                is_unique = True
                for existing in self.solutions:
                    diff = sum(1 for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                              if new_solution[r][c] != existing[r][c])
                    if diff < GRID_SIZE * GRID_SIZE // 2:  # 相似度太高
                        is_unique = False
                        break
                
                if is_unique:
                    self.solutions.append(new_solution)
                    print(f"  第{i+1}解获取成功")
                else:
                    print(f"  第{i+1}次尝试：解重复")
            else:
                print(f"  第{i+1}次尝试：未找到解")
                
                # 退化为完全随机搜索
                new_solution = self.solve(None, time_limit=10.0)
                if new_solution:
                    is_unique = True
                    for existing in self.solutions:
                        diff = sum(1 for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                                  if new_solution[r][c] != existing[r][c])
                        if diff < GRID_SIZE * GRID_SIZE // 2:
                            is_unique = False
                            break
                    if is_unique:
                        self.solutions.append(new_solution)
                        print(f"  第{i+1}解（随机）获取成功")
        
        return self.solutions


# ═══════════════════════════════════════════════════════════
# 增量采样主控
# ═══════════════════════════════════════════════════════════

def run_cp_sat_sampling(anchors: List[Dict], 
                        target_samples: int = 100,
                        output_file: str = 'incremental_cp_sat_v36_result.json') -> Dict:
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
    print("\n  开始CP-SAT多解采样...")
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
            'method': 'CP-SAT增量采样'
        },
        'summary': {
            'total_solutions': len(solutions),
            'total_time_seconds': round(total_time, 2),
            'avg_time_per_solution': round(total_time / max(1, len(solutions)), 2)
        },
        'solutions': []
    }
    
    # 保存解
    for i, sol in enumerate(solutions):
        # 简化存储：只存部分网格预览
        preview = []
        for r in range(GRID_SIZE):
            preview.append(sol[r][:4] + ['...'] + sol[r][-4:])
        
        # 计算解的特征
        row_hashes = [hashlib.md5(str(tuple(row)).encode()).hexdigest()[:8] for row in sol]
        
        results['solutions'].append({
            'id': i + 1,
            'row_hash_prefixes': row_hashes[:4],
            'grid_preview': preview
        })
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("  采样完成摘要")
    print("=" * 60)
    print(f"  总耗时: {total_time:.2f} 秒")
    print(f"  获取解数: {len(solutions)}")
    print(f"  平均每解耗时: {total_time / max(1, len(solutions)):.2f} 秒")
    
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
    
    # 执行采样
    run_cp_sat_sampling(FULL_92_ANCHORS, target_samples=50)
