#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极融合搜索架构 V1 — 黏菌优化算子

模块5：生物智能模拟 + 自适应权重 + 振荡觅食
"""

import numpy as np
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import random


# ======================== 常量定义 ========================

GRID_SIZE = 16


# ======================== 数据类 ========================

@dataclass
class SlimeMoldAgent:
    """黏菌代理"""
    position: Tuple[int, int, ...]  # 在解空间中的位置（16个排列索引）
    velocity: np.ndarray
    individual_best: Tuple[int, ...]
    individual_best_fitness: float = 0.0
    
    def __hash__(self):
        return hash(self.position)


@dataclass
class SlimeMoldConfig:
    """黏菌优化配置"""
    num_slime: int = 30           # 黏菌数量
    max_iterations: int = 200     # 最大迭代数
    omega: float = 2 * math.pi / 100  # 振荡周期
    v_max: float = 0.3            # 最大振荡速度
    v_min: float = -0.3           # 最小振荡速度
    b_factor: float = 0.1         # 权重缩放因子
    food_source_radius: float = 0.05  # 食物源半径


@dataclass
class OptimizationResult:
    """优化结果"""
    best_solution: Tuple[int, ...]
    best_fitness: float
    iteration_history: List[float]
    convergence_iteration: int


# ======================== 黏菌优化算子 ========================

class SlimeMoldOptimizer:
    """黏菌优化算子 — 生物智能搜索
    
    核心方程（改进版）：
    
    SM(t+1) = SB + W(t) · ( A · (IB + p · (I₂ - IB)) )
    
    其中:
    - SM: 当前位置
    - SB: 食物源位置（精英解）
    - IB: 个体历史最优
    - I₂: 随机个体
    - p: 振荡参数 p = ν · cos(ω · t)
    - W: 自适应权重
    
    权重更新：
    W(t) = 1 + b · log( (fb - S) / (wb - S) )
    
    振荡机制：
    - 收缩阶段: |W| > 1，向食物源收缩
    - 探索阶段: |W| < 1，扩大搜索范围
    """
    
    def __init__(self, config: Optional[SlimeMoldConfig] = None):
        self.config = config or SlimeMoldConfig()
        self.slime_agents: List[SlimeMoldAgent] = []
        self.global_best: Optional[Tuple[int, ...]] = None
        self.global_best_fitness: float = 0.0
        self.iteration_history: List[float] = []
    
    def initialize(self, 
                   permutations: List[List[Tuple[int, ...]]],
                   elite_pool: Optional[List[Tuple[int, ...]]] = None) -> None:
        """初始化黏菌种群"""
        
        self.slime_agents = []
        self.global_best = None
        self.global_best_fitness = 0.0
        
        for i in range(self.config.num_slime):
            # 从排列中选择随机位置
            position = []
            for row_idx in range(GRID_SIZE):
                perms = permutations[row_idx]
                if perms:
                    # 随机选择排列索引
                    perm_idx = random.randint(0, len(perms) - 1)
                    position.append(perm_idx)
                else:
                    position.append(0)
            
            # 初始化速度
            velocity = np.zeros(GRID_SIZE)
            
            agent = SlimeMoldAgent(
                position=tuple(position),
                velocity=velocity,
                individual_best=tuple(position),
                individual_best_fitness=0.0
            )
            
            self.slime_agents.append(agent)
            
            # 如果有精英池，用精英初始化部分黏菌
            if elite_pool and i < len(elite_pool):
                agent.position = elite_pool[i]
                agent.individual_best = elite_pool[i]
    
    def compute_fitness(self, position: Tuple[int, ...],
                        permutations: List[List[Tuple[int, ...]]]) -> float:
        """计算适应度（基于排列位置的解质量）"""
        
        # 构建网格
        grid = []
        for row_idx, perm_idx in enumerate(position):
            perms = permutations[row_idx]
            if perm_idx < len(perms):
                grid.append(list(perms[perm_idx]))
            else:
                grid.append(list(range(1, GRID_SIZE + 1)))
        
        # 计算冲突数
        conflicts = 0
        
        # 列冲突
        for c in range(GRID_SIZE):
            col_vals = [grid[r][c] for r in range(GRID_SIZE)]
            conflicts += len(col_vals) - len(set(col_vals))
        
        # 宫冲突
        for br in range(GRID_SIZE // 4):
            for bc in range(GRID_SIZE // 4):
                box_vals = []
                for r in range(br * 4, (br + 1) * 4):
                    for c in range(bc * 4, (bc + 1) * 4):
                        box_vals.append(grid[r][c])
                conflicts += len(box_vals) - len(set(box_vals))
        
        # 适应度：冲突越少越好
        fitness = 1.0 / (1.0 + conflicts / 100.0)
        return fitness
    
    def update_weights(self, generation: int,
                       fitnesses: List[float]) -> np.ndarray:
        """更新自适应权重"""
        
        weights = np.zeros(self.config.num_slime)
        
        # 全局最优适应度
        wb = max(fitnesses) if fitnesses else 0.0
        
        # 基准值（适应度下限）
        S = 0.0
        
        for i, fb in enumerate(fitnesses):
            # 避免除零
            numerator = max(fb - S, 1e-10)
            denominator = max(wb - S, 1e-10)
            
            if denominator > 0:
                ratio = numerator / denominator
                # 权重公式：W = 1 + b · log(ratio)
                weights[i] = 1.0 + self.config.b_factor * math.log(max(ratio, 1e-10))
            else:
                weights[i] = 1.0
            
            # 限制权重范围
            weights[i] = max(0.1, min(3.0, weights[i]))
        
        return weights
    
    def oscillate_forage(self, generation: int,
                         permutations: List[List[Tuple[int, ...]]]) -> None:
        """振荡觅食行为"""
        
        # 计算当前适应度
        fitnesses = []
        for agent in self.slime_agents:
            fit = self.compute_fitness(agent.position, permutations)
            fitnesses.append(fit)
            
            # 更新个体最优
            if fit > agent.individual_best_fitness:
                agent.individual_best_fitness = fit
                agent.individual_best = agent.position
        
        # 更新全局最优
        max_fit = max(fitnesses)
        max_idx = fitnesses.index(max_fit)
        if max_fit > self.global_best_fitness:
            self.global_best_fitness = max_fit
            self.global_best = self.slime_agents[max_idx].position
        
        # 计算自适应权重
        weights = self.update_weights(generation, fitnesses)
        
        # 振荡觅食
        for i, agent in enumerate(self.slime_agents):
            # 振荡参数
            p = self.config.v_max * math.cos(self.config.omega * generation)
            
            # 选择两个随机个体
            indices = [j for j in range(self.config.num_slime) if j != i]
            if len(indices) >= 2:
                idx1, idx2 = random.sample(indices, 2)
            elif len(indices) == 1:
                idx1, idx2 = indices[0], indices[0]
            else:
                idx1, idx2 = i, i
            
            # 获取位置
            ib = np.array(agent.individual_best, dtype=float)
            i2_pos = np.array(self.slime_agents[idx2].position, dtype=float)
            
            if self.global_best:
                sb = np.array(self.global_best, dtype=float)
            else:
                sb = ib
            
            # 更新位置（离散化）
            # 公式：SM(t+1) = SB + W · ( A · (IB + p · (I₂ - IB)) )
            # A 是随机方向矩阵（0或1）
            A = np.random.randint(0, 2, size=GRID_SIZE)
            
            delta = ib + p * (i2_pos - ib)
            new_pos = sb + weights[i] * A * delta
            
            # 离散化到排列索引范围
            new_position = []
            for row_idx, val in enumerate(new_pos):
                perms = permutations[row_idx]
                if perms:
                    # 限制在有效索引范围内
                    new_idx = int(max(0, min(len(perms) - 1, round(val))))
                    new_position.append(new_idx)
                else:
                    new_position.append(0)
            
            agent.position = tuple(new_position)
        
        # 记录历史
        self.iteration_history.append(max(fitnesses))
    
    def optimize(self, 
                 permutations: List[List[Tuple[int, ...]]],
                 elite_pool: Optional[List[Tuple[int, ...]]] = None,
                 verbose: bool = False) -> OptimizationResult:
        """执行黏菌优化"""
        
        if verbose:
            print("=" * 60)
            print("黏菌优化算子")
            print("=" * 60)
        
        # 初始化
        self.initialize(permutations, elite_pool)
        
        if verbose:
            print(f"\n黏菌数量: {self.config.num_slime}")
            print(f"最大迭代: {self.config.max_iterations}")
        
        # 优化循环
        for gen in range(self.config.max_iterations):
            self.oscillate_forage(gen, permutations)
            
            if verbose and gen % 20 == 0:
                print(f"  迭代 {gen}: 最佳适应度 = {self.global_best_fitness:.4f}")
            
            # 早停：如果连续50代无改善
            if len(self.iteration_history) >= 50:
                recent_best = max(self.iteration_history[-50:])
                if abs(recent_best - self.global_best_fitness) < 0.001:
                    if verbose:
                        print(f"  迭代 {gen}: 早停（无改善）")
                    break
        
        # 收敛迭代
        convergence_iter = self.config.max_iterations
        for i, fit in enumerate(self.iteration_history):
            if abs(fit - self.global_best_fitness) < 0.001:
                convergence_iter = i
                break
        
        result = OptimizationResult(
            best_solution=self.global_best,
            best_fitness=self.global_best_fitness,
            iteration_history=self.iteration_history,
            convergence_iteration=convergence_iter
        )
        
        if verbose:
            print("\n" + "=" * 60)
            print("优化结果")
            print("=" * 60)
            print(f"最佳适应度: {result.best_fitness:.4f}")
            print(f"收敛迭代: {convergence_iter}")
            print(f"最终迭代数: {len(self.iteration_history)}")
        
        return result
    
    def get_best_solution_grid(self, 
                                permutations: List[List[Tuple[int, ...]]]) -> List[List[int]]:
        """获取最佳解的网格"""
        
        if not self.global_best:
            return [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        
        grid = []
        for row_idx, perm_idx in enumerate(self.global_best):
            perms = permutations[row_idx]
            if perm_idx < len(perms):
                grid.append(list(perms[perm_idx]))
            else:
                grid.append(list(range(1, GRID_SIZE + 1)))
        
        return grid


# ======================== 测试 ========================

if __name__ == "__main__":
    # 模拟排列数据
    permutations = []
    for row_idx in range(GRID_SIZE):
        # 每行生成100个随机排列
        row_perms = []
        for _ in range(100):
            perm = list(range(1, GRID_SIZE + 1))
            random.shuffle(perm)
            row_perms.append(tuple(perm))
        permutations.append(row_perms)
    
    # 创建优化器
    optimizer = SlimeMoldOptimizer(SlimeMoldConfig(
        num_slime=20,
        max_iterations=100
    ))
    
    # 执行优化
    result = optimizer.optimize(permutations, verbose=True)
    
    print(f"\n✓ 优化完成，最佳适应度: {result.best_fitness:.4f}")
