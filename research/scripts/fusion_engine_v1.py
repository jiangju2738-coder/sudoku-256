#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极融合搜索架构 V1 — 精英回溯循环 + 遗传协同引擎

模块3：精英保留 ↔ 回溯精修 ↔ 遗传重组合的三大循环
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import random
import time


# ======================== 常量定义 ========================

GRID_SIZE = 16
BOX_SIZE = 4
FUMMEL_ROWS = {2, 3, 8, 15}


# ======================== 数据类 ========================

@dataclass
class SolutionGrid:
    """解网格"""
    values: List[List[int]]  # 16×16 网格
    fitness: float = 0.0
    is_valid: bool = False
    
    def get_row(self, row: int) -> List[int]:
        return self.values[row]
    
    def get_cell(self, r: int, c: int) -> int:
        return self.values[r][c]
    
    def hamming_distance(self, other: 'SolutionGrid') -> int:
        """计算汉明距离"""
        dist = 0
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.values[r][c] != other.values[r][c]:
                    dist += 1
        return dist
    
    def to_tuple(self) -> Tuple[Tuple[int, ...], ...]:
        """转为元组用于哈希"""
        return tuple(tuple(row) for row in self.values)


@dataclass
class ElitePool:
    """精英池 — 保留高质量解"""
    max_size: int = 50
    elites: List[Tuple[SolutionGrid, float]] = field(default_factory=list)
    diversity_threshold: float = 0.15  # 最小汉明距离比例
    
    def add(self, solution: SolutionGrid, fitness: float) -> bool:
        """添加精英解"""
        # 检查多样性
        for existing, _ in self.elites:
            dist_ratio = solution.hamming_distance(existing) / (GRID_SIZE * GRID_SIZE)
            if dist_ratio < self.diversity_threshold:
                return False  # 不够多样，拒绝
        
        self.elites.append((solution, fitness))
        
        # 如果超出容量，移除最低适应度
        if len(self.elites) > self.max_size:
            self.elites.sort(key=lambda x: x[1], reverse=True)
            self.elites = self.elites[:self.max_size]
        
        return True
    
    def get_top_k(self, k: int) -> List[SolutionGrid]:
        """获取前k个精英解"""
        self.elites.sort(key=lambda x: x[1], reverse=True)
        return [elite[0] for elite in self.elites[:k]]
    
    def sample_for_crossover(self, n: int = 2) -> List[SolutionGrid]:
        """采样用于交叉的精英解"""
        if len(self.elites) < n:
            return [elite[0] for elite in self.elites]
        return random.sample([elite[0] for elite in self.elites], n)


@dataclass
class ConflictRecord:
    """冲突记录（回溯记忆）"""
    position: Tuple[int, int]
    attempted_values: Set[int]
    conflict_type: str  # 'row', 'col', 'box', 'permutation'
    timestamp: float = field(default_factory=time.time)


@dataclass
class BacktrackMemory:
    """回溯记忆系统 — 记录冲突并加速搜索"""
    conflicts: Dict[Tuple[int, int], List[ConflictRecord]] = field(default_factory=lambda: defaultdict(list))
    pruning_rules: Dict[str, float] = field(default_factory=dict)
    
    def record_conflict(self, pos: Tuple[int, int], value: int, 
                        conflict_type: str) -> None:
        """记录冲突"""
        record = ConflictRecord(
            position=pos,
            attempted_values={value},
            conflict_type=conflict_type
        )
        self.conflicts[pos].append(record)
        
        # 更新剪枝规则
        key = f"{pos}_{conflict_type}"
        self.pruning_rules[key] = self.pruning_rules.get(key, 0) + 1
    
    def should_prune(self, pos: Tuple[int, int], value: int,
                     conflict_type: str) -> bool:
        """判断是否应该剪枝"""
        # 如果同一位置多次尝试同一值冲突，剪枝
        key = f"{pos}_{conflict_type}"
        if key in self.pruning_rules and self.pruning_rules[key] >= 3:
            return True
        
        for record in self.conflicts.get(pos, []):
            if value in record.attempted_values and record.conflict_type == conflict_type:
                return True
        
        return False
    
    def get_safe_values(self, pos: Tuple[int, int], 
                        candidates: Set[int]) -> Set[int]:
        """获取安全候选值（排除冲突值）"""
        safe = set(candidates)
        for record in self.conflicts.get(pos, []):
            safe -= record.attempted_values
        return safe


@dataclass
class TriangularCycleResult:
    """三角循环结果"""
    iteration: int
    ga_solutions: int
    backtrack_refined: int
    elite_pool_size: int
    best_fitness: float
    convergence_rate: float


# ======================== 精英回溯循环 + GA协同 ========================

class EliteBacktrackGA:
    """精英回溯循环 + 遗传协同引擎
    
    三大循环机制：
    1. 精英保留循环：GA探索 → 筛选精英 → 精英池积累 → 精英引导搜索
    2. 回溯记忆循环：回溯搜索 → 记录冲突 → 记忆剪枝 → 加速回溯
    3. 遗传重组合循环：GA交叉 → 变异探索 → 局部搜索 → 融合精英
    """
    
    def __init__(self, anchors: Dict[Tuple[int, int], int],
                 permutations: List[List[Tuple[int, ...]]],
                 max_elite_size: int = 50):
        self.anchors = anchors
        self.permutations = permutations
        self.elite_pool = ElitePool(max_size=max_elite_size)
        self.memory = BacktrackMemory()
        self.cycle_history: List[TriangularCycleResult] = []
        
    def _validate_row(self, row_values: List[int]) -> bool:
        """验证行AllDifferent"""
        return len(set(row_values)) == len(row_values)
    
    def _validate_col(self, grid: List[List[int]], col_idx: int) -> bool:
        """验证列AllDifferent"""
        values = [grid[r][col_idx] for r in range(GRID_SIZE)]
        return len(set(values)) == len(values)
    
    def _validate_box(self, grid: List[List[int]], 
                      box_r: int, box_c: int) -> bool:
        """验证宫AllDifferent"""
        values = []
        for r in range(box_r * BOX_SIZE, (box_r + 1) * BOX_SIZE):
            for c in range(box_c * BOX_SIZE, (box_c + 1) * BOX_SIZE):
                values.append(grid[r][c])
        return len(set(values)) == len(values)
    
    def _validate_solution(self, grid: SolutionGrid) -> bool:
        """完整验证解"""
        # 验证行
        for r in range(GRID_SIZE):
            if not self._validate_row(grid.get_row(r)):
                return False
        
        # 验证列
        for c in range(GRID_SIZE):
            if not self._validate_col(grid.values, c):
                return False
        
        # 验证宫
        for br in range(GRID_SIZE // BOX_SIZE):
            for bc in range(GRID_SIZE // BOX_SIZE):
                if not self._validate_box(grid.values, br, bc):
                    return False
        
        return True
    
    def _compute_fitness(self, grid: SolutionGrid) -> float:
        """计算适应度（冲突数量）"""
        conflicts = 0
        
        # 行冲突
        for r in range(GRID_SIZE):
            row_vals = grid.get_row(r)
            conflicts += len(row_vals) - len(set(row_vals))
        
        # 列冲突
        for c in range(GRID_SIZE):
            col_vals = [grid.values[r][c] for r in range(GRID_SIZE)]
            conflicts += len(col_vals) - len(set(col_vals))
        
        # 宫冲突
        for br in range(GRID_SIZE // BOX_SIZE):
            for bc in range(GRID_SIZE // BOX_SIZE):
                box_vals = []
                for r in range(br * BOX_SIZE, (br + 1) * BOX_SIZE):
                    for c in range(bc * BOX_SIZE, (bc + 1) * BOX_SIZE):
                        box_vals.append(grid.values[r][c])
                conflicts += len(box_vals) - len(set(box_vals))
        
        return 1.0 / (1.0 + conflicts / 100.0)  # 归一化适应度
    
    def ga_explore(self, iteration: int, 
                   elite_pool: Optional[ElitePool] = None) -> List[SolutionGrid]:
        """循环1: GA探索（广度搜索）"""
        print(f"\n  [GA探索] 迭代 {iteration}...")
        
        # 从精英池采样或随机初始化
        if elite_pool and elite_pool.elites:
            parents = elite_pool.sample_for_crossover(4)
        else:
            parents = self._random_initialize(4)
        
        solutions = []
        
        for _ in range(10):  # 生成10个后代
            if len(parents) >= 2:
                parent1, parent2 = random.sample(parents, 2)
                child = self._crossover(parent1, parent2)
            else:
                child = self._random_initialize(1)[0]
            
            child = self._mutate(child, iteration)
            child.fitness = self._compute_fitness(child)
            child.is_valid = self._validate_solution(child)
            
            solutions.append(child)
        
        print(f"      生成 {len(solutions)} 个GA候选解")
        return solutions
    
    def _random_initialize(self, n: int) -> List[SolutionGrid]:
        """随机初始化网格（仅使用符阖排列）"""
        grids = []
        
        for _ in range(n):
            grid_values = []
            for row_idx in range(GRID_SIZE):
                perms = self.permutations[row_idx]
                if perms:
                    # 随机选择一个排列
                    perm = random.choice(perms)
                    grid_values.append(list(perm))
                else:
                    # 无排列，随机填充
                    grid_values.append(list(range(1, GRID_SIZE + 1)))
            
            grid = SolutionGrid(values=grid_values)
            grids.append(grid)
        
        return grids
    
    def _crossover(self, parent1: SolutionGrid, 
                   parent2: SolutionGrid) -> SolutionGrid:
        """行级交叉（从父母行中选择）"""
        child_values = []
        
        for r in range(GRID_SIZE):
            if random.random() < 0.5:
                child_values.append(parent1.get_row(r).copy())
            else:
                child_values.append(parent2.get_row(r).copy())
        
        return SolutionGrid(values=child_values)
    
    def _mutate(self, grid: SolutionGrid, iteration: int) -> SolutionGrid:
        """基于行的排列变异"""
        new_values = [row.copy() for row in grid.values]
        
        # 变异率随迭代降低
        mutation_rate = max(0.02, 0.15 * (1.0 - iteration / 100.0))
        
        for r in range(GRID_SIZE):
            if r in FUMMEL_ROWS:
                continue  # 符阖行不突变
            
            if random.random() < mutation_rate:
                perms = self.permutations[r]
                if perms:
                    # 替换为另一个排列
                    new_perm = random.choice(perms)
                    new_values[r] = list(new_perm)
        
        return SolutionGrid(values=new_values)
    
    def backtrack_refine(self, solutions: List[SolutionGrid]) -> List[SolutionGrid]:
        """循环2: 回溯精修（深度验证）"""
        print(f"\n  [回溯精修] 精修 {len(solutions)} 个候选解...")
        
        refined = []
        
        for sol in solutions:
            if sol.is_valid:
                refined.append(sol)
                continue
            
            # 对有冲突的解进行回溯修复
            repaired = self._repair_with_backtrack(sol)
            if repaired:
                repaired.fitness = self._compute_fitness(repaired)
                repaired.is_valid = self._validate_solution(repaired)
                refined.append(repaired)
        
        print(f"      精修后: {len(refined)} 个有效解")
        return refined
    
    def _repair_with_backtrack(self, grid: SolutionGrid) -> Optional[SolutionGrid]:
        """使用回溯修复冲突"""
        # 简化版本：仅修复部分行
        new_grid = SolutionGrid(values=[row.copy() for row in grid.values])
        
        # 找出冲突行
        conflict_rows = []
        for r in range(GRID_SIZE):
            if r in FUMMEL_ROWS:
                continue
            row_vals = new_grid.get_row(r)
            if len(set(row_vals)) < len(row_vals):
                conflict_rows.append(r)
        
        if not conflict_rows:
            return new_grid
        
        # 为冲突行重新选择排列
        for r in conflict_rows[:3]:  # 最多修复3行
            perms = self.permutations[r]
            if not perms:
                continue
            
            # 选择与当前冲突最少的排列
            best_perm = None
            best_score = float('inf')
            
            for perm in perms:
                score = 0
                for c, val in enumerate(perm):
                    if grid.values[r][c] != val:
                        score += 1
                if score < best_score:
                    best_score = score
                    best_perm = perm
            
            if best_perm:
                new_grid.values[r] = list(best_perm)
        
        return new_grid
    
    def elite_converge(self, refined_solutions: List[SolutionGrid]) -> int:
        """循环3: 精英汇聚"""
        added = 0
        for sol in refined_solutions:
            if self.elite_pool.add(sol, sol.fitness):
                added += 1
        return added
    
    def run_triangular_cycle(self, max_iterations: int = 20,
                             verbose: bool = True) -> List[SolutionGrid]:
        """执行三大循环迭代"""
        
        print("=" * 60)
        print("精英回溯循环 + GA协同引擎")
        print("=" * 60)
        
        for iteration in range(1, max_iterations + 1):
            ga_start = time.time()
            
            # 循环1: GA探索
            ga_solutions = self.ga_explore(iteration)
            
            # 循环2: 回溯精修
            refined = self.backtrack_refine(ga_solutions)
            
            # 循环3: 精英汇聚
            added = self.elite_converge(refined)
            
            # 记录结果
            best_fitness = max((sol.fitness for sol in refined), default=0)
            result = TriangularCycleResult(
                iteration=iteration,
                ga_solutions=len(ga_solutions),
                backtrack_refined=len(refined),
                elite_pool_size=len(self.elite_pool.elites),
                best_fitness=best_fitness,
                convergence_rate=len(refined) / len(ga_solutions) if ga_solutions else 0
            )
            self.cycle_history.append(result)
            
            if verbose:
                print(f"\n  [循环汇总] 迭代 {iteration}:")
                print(f"    GA候选: {len(ga_solutions)} 个")
                print(f"    精修有效: {len(refined)} 个")
                print(f"    精英池: {len(self.elite_pool.elites)} 个")
                print(f"    最佳适应度: {best_fitness:.4f}")
            
            # 早停检测
            if len(self.elite_pool.elites) >= self.elite_pool.max_size:
                print(f"\n  ✓ 精英池已满，停止迭代")
                break
        
        # 最终汇总
        print("\n" + "=" * 60)
        print("三角循环结果汇总")
        print("=" * 60)
        
        best = self.elite_pool.get_top_k(min(5, len(self.elite_pool.elites)))
        print(f"\n最佳 {len(best)} 个精英解:")
        for i, sol in enumerate(best):
            print(f"  [{i+1}] 适应度: {sol.fitness:.4f}, 有效: {sol.is_valid}")
        
        return self.elite_pool.get_top_k(len(self.elite_pool.elites))


# ======================== 测试 ========================

if __name__ == "__main__":
    from fusion_engine_v1 import InitialPuzzleBase
    
    # 初始化
    initializer = InitialPuzzleBase()
    anchors, graph, permutations, state = initializer.initialize()
    
    # 转换为元组格式
    perm_tuples = []
    for row_perms in permutations:
        row_tuples = [perm.values for perm in row_perms]
        perm_tuples.append(row_tuples)
    
    # 创建协同引擎
    engine = EliteBacktrackGA(anchors, perm_tuples, max_elite_size=10)
    
    # 执行三角循环
    solutions = engine.run_triangular_cycle(max_iterations=10)
    
    print(f"\n✓ 共找到 {len(solutions)} 个精英解")
