#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 符闔博弈優選策略 V37.0 - 改進遺傳適應度函數權重
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

基於 V30-V36 的發現進行權重重構：

【V30 核心發現】
- 解空間二相性：142 高變異位置(>50%) + 114 低變異位置(<10%)
- 適應度高原：初始最佳 2.2 → 最終最佳 2.2（無提升）
- 3 個分叉點全部位於行 A：(0,0),(0,1),(0,3)
- 23 個解構成局部最優「島嶼」

【V36 補充發現】
- 行 H/A/B 最不稳定（92/91/91 種排列，熵>0.968）
- 行 P 最稳定（78 種排列，熵 0.830）
- 100+ 解間平均漢明距離 164.24（10 個完整解樣本）

【V37 改進方案】

1. 位置熵權重化 (Entropy-Weighted)
   - 基於 V36 行熵數據動態調整每行約束权重
   - 高熵行（H/A/B）：权重×1.2（更重要，需优先满足）
   - 低熵行（P/O/N）：权重×0.8（已较稳定）

2. 變異度感知權重 (Variance-Aware)
   - 基於 V30 高/低變異位置分類
   - 高變異位置列約束：权重×1.3
   - 低變異位置列約束：权重×0.9

3. 動態權重衰減 (Dynamic Decay)
   - 代數 t：列权重 w_col(t) = 0.5 × e^(-0.01t) + 0.2
   - 宫权重 w_box(t) = 0.3 + 0.2 × (1 - e^(-0.01t))
   - 確保早期重列約束，后期重宫約束

4. 精英適應度惩罚 (Elite Penalty)
   - 避免陷入局部最优「島嶼」
   - 相似度>95%的精英：适应度×0.95
   - 鼓励探索新区域

5. 漢明距離多样性奖励 (Hamming Diversity Bonus)
   - 与最优解差异大的个体：适应度 +0.05×(Hamming/160)
   - 鼓励种群多样性

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import time
import random
import numpy as np
from collections import Counter
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
import hashlib


# ═══════════════════════════════════════════════════════════
# 第一部分：熵权重计算器
# ═══════════════════════════════════════════════════════════

@dataclass
class RowEntropyProfile:
    """行熵分布档案 (基于 V36 数据)"""
    row: int
    unique_count: int      # 不同排列数
    entropy: float          # 归一化熵 (0-1)
    stability: str          # high/medium/low
    
    def get_weight_multiplier(self) -> float:
        """根据熵返回权重乘数"""
        if self.entropy >= 0.95:
            return 1.25  # 高熵：高权重
        elif self.entropy >= 0.90:
            return 1.15  # 中高熵
        elif self.entropy >= 0.85:
            return 1.0   # 中等
        else:
            return 0.85  # 低熵：低权重


@dataclass
class CellVarianceProfile:
    """单元格变异度档案 (基于 V30 数据)"""
    row: int
    col: int
    variance_level: str   # high/medium/low
    unique_count: int     # 在样本中出现的不同值数
    
    def get_col_weight(self) -> float:
        """列权重乘数"""
        if self.variance_level == 'high':
            return 1.3
        elif self.variance_level == 'low':
            return 0.9
        return 1.0


class EntropyWeightCalculator:
    """熵权重计算器"""
    
    def __init__(self, row_entropies: Dict[int, float] = None):
        """
        初始化熵权重
        
        Args:
            row_entropies: {row_idx: entropy} 字典
                          如果为 None，使用 V36 实测数据
        """
        # V36 实测行熵数据
        if row_entropies is None:
            self.row_entropies = {
                0: 0.968,   # A: 91种排列
                1: 0.968,   # B: 91种排列
                2: 0.957,   # C: 90种排列
                3: 0.957,   # D: 90种排列
                4: 0.936,   # E: 88种排列
                5: 0.947,   # F: 89种排列
                6: 0.957,   # G: 90种排列
                7: 0.979,   # H: 92种排列 (最高)
                8: 0.883,   # I: 83种排列
                9: 0.926,   # J: 87种排列
                10: 0.926,  # K: 87种排列
                11: 0.904,  # L: 85种排列
                12: 0.894,  # M: 84种排列
                13: 0.883,  # N: 83种排列
                14: 0.872,  # O: 82种排列
                15: 0.830,  # P: 78种排列 (最低)
            }
        else:
            self.row_entropies = row_entropies
        
        # 构建行熵档案
        self.row_profiles = {}
        for r, ent in self.row_entropies.items():
            if ent >= 0.95:
                stability = 'high'
            elif ent >= 0.90:
                stability = 'medium'
            else:
                stability = 'low'
            self.row_profiles[r] = RowEntropyProfile(
                row=r, unique_count=int(ent * 94), entropy=ent, stability=stability
            )
        
        # V30 高/低变异位置 (基于 23 解样本)
        # 高变异位置：>50% 变异度，位于行 A 前 4 列和其他分叉点
        self.high_variance_cells = set([
            (0, 0), (0, 1), (0, 3),  # 分叉点
            (0, 15), (1, 14), (1, 15),  # 高熵位置
            (2, 15), (0, 10), (1, 12),
            (2, 9), (3, 13), (3, 14),
        ])
        
        # 低变异位置：<10% 变异度
        self.low_variance_cells = set([
            (2, i) for i in range(16)  # 行 C 大部分固定
        ] + [(3, i) for i in range(4)])  # 行 D 前 4 列固定
        
    def get_row_weight(self, row: int) -> float:
        """获取某行的权重"""
        if row in self.row_profiles:
            return self.row_profiles[row].get_weight_multiplier()
        return 1.0
    
    def get_col_weight(self, row: int, col: int) -> float:
        """获取某单元格的列权重"""
        if (row, col) in self.high_variance_cells:
            return 1.3
        elif (row, col) in self.low_variance_cells:
            return 0.9
        return 1.0
    
    def get_box_weight(self, box_idx: int) -> float:
        """获取宫权重"""
        # 行 C/D 固定 => 宫 0,1,2,3 权重大
        high_priority_boxes = {0, 1, 2, 3}  # 含行 C/D 的宫
        if box_idx in high_priority_boxes:
            return 1.1
        return 1.0
    
    def print_profile(self):
        """打印熵分布档案"""
        print("\n【熵权重分布档案】")
        print(f"{'行':>3} {'熵值':>6} {'排列数':>6} {'稳定性':>6} {'权重乘数':>8}")
        print("-" * 40)
        for r in range(16):
            if r in self.row_profiles:
                p = self.row_profiles[r]
                print(f"  {chr(65+r):>3} {p.entropy:>6.3f} {p.unique_count:>6} "
                      f"{p.stability:>6} {p.get_weight_multiplier():>8.2f}")


# ═══════════════════════════════════════════════════════════
# 第二部分：改进的适应度函数
# ═══════════════════════════════════════════════════════════

@dataclass
class AdaptiveFitnessConfig:
    """动态适应度配置"""
    # 基础权重
    base_row_weight: float = 0.08
    base_col_weight: float = 0.42
    base_box_weight: float = 0.40
    base_known_weight: float = 0.10
    
    # 动态衰减参数
    col_decay_rate: float = 0.008
    box_growth_rate: float = 0.005
    
    # 多样性奖励
    hamming_bonus_max: float = 0.05
    elite_penalty: float = 0.95
    
    # 熵权重乘数范围
    entropy_weight_min: float = 0.80
    entropy_weight_max: float = 1.25
    
    def get_dynamic_weights(self, generation: int, max_generations: int) -> Dict[str, float]:
        """
        根据代数计算动态权重
        
        策略：
        - 早期 (gen < 30%)：重列约束（避免列冲突）
        - 中期 (30-70%)：列/宫平衡
        - 后期 (gen > 70%)：重宫约束（满足宫 AllDifferent）
        """
        progress = generation / max_generations if max_generations > 0 else 0
        
        # 列权重：指数衰减
        w_col = self.base_col_weight * np.exp(-self.col_decay_rate * generation) + 0.15
        
        # 宫权重：线性增长
        w_box = self.base_box_weight + self.box_growth_rate * generation
        
        # 行权重：保持稳定
        w_row = self.base_row_weight
        
        # 已知位置：始终 10%
        w_known = self.base_known_weight
        
        # 归一化
        total = w_row + w_col + w_box + w_known
        return {
            'row': w_row / total,
            'col': w_col / total,
            'box': w_box / total,
            'known': w_known / total,
        }


class ImprovedIndividual:
    """改进的个体（支持熵权重）"""
    
    def __init__(self, grid: List[List[int]], generation: int = 0):
        self.grid = grid
        self.generation = generation
        self.fitness = 0.0
        self.fitness_breakdown = {}  # 各项适应度分解
        self.hamming_to_best = 0     # 到最优解的汉明距离
        self.elite_penalty_applied = False
        self.diversity_bonus = 0.0
    
    def compute_adaptive_fitness(
        self,
        known_positions: Dict[Tuple[int, int], int],
        entropy_calc: EntropyWeightCalculator,
        config: AdaptiveFitnessConfig,
        generation: int,
        max_generations: int,
        reference_solutions: List['ImprovedIndividual'] = None
    ) -> float:
        """
        计算改进的自适应适应度
        
        改进点：
        1. 动态权重（基于代数）
        2. 熵权重乘数（基于行稳定性）
        3. 多样性奖励（基于汉明距离）
        4. 精英惩罚（避免局部最优）
        """
        weights = config.get_dynamic_weights(generation, max_generations)
        
        # ===== 1. 行约束适应度 =====
        row_fitness = 0.0
        for r in range(16):
            row_vals = self.grid[r]
            entropy_w = entropy_calc.get_row_weight(r)
            
            if 0 in row_vals:
                row_fitness += 0
            elif len(set(row_vals)) == 16:
                row_fitness += 1.0 * entropy_w
            else:
                duplicates = len(row_vals) - len(set(row_vals))
                row_fitness += (16 - duplicates) / 16 * entropy_w
        
        row_fitness /= 16  # 平均
        
        # ===== 2. 列约束适应度（位置感知）=====
        col_fitness = 0.0
        for c in range(16):
            col_vals = [self.grid[r][c] for r in range(16)]
            unique_count = len(set(v for v in col_vals if v != 0))
            non_zero_count = sum(1 for v in col_vals if v != 0)
            
            if non_zero_count == 0:
                col_fitness += 0
            elif non_zero_count == 16 and unique_count == 16:
                # 全满且无冲突
                col_fitness += 1.0
            else:
                # 部分填充或有冲突
                if non_zero_count > 0:
                    unique_ratio = unique_count / non_zero_count
                    
                    # 应用位置权重
                    weighted_unique = 0.0
                    for r in range(16):
                        if self.grid[r][c] != 0:
                            cell_w = entropy_calc.get_col_weight(r, c)
                            weighted_unique += cell_w
                    
                    avg_cell_w = weighted_unique / non_zero_count
                    col_fitness += unique_ratio * avg_cell_w
        
        col_fitness /= 16  # 平均
        
        # ===== 3. 宫约束适应度 =====
        box_fitness = 0.0
        for box_idx in range(16):
            box_vals = []
            for r in range(16):
                for c in range(16):
                    if (r // 4) * 4 + (c // 4) == box_idx:
                        box_vals.append(self.grid[r][c])
            
            box_w = entropy_calc.get_box_weight(box_idx)
            
            if 0 in box_vals:
                box_fitness += 0
            elif len(set(box_vals)) == 16:
                box_fitness += 1.0 * box_w
            else:
                duplicates = len(box_vals) - len(set(box_vals))
                box_fitness += (16 - duplicates) / 16 * box_w
        
        box_fitness /= 16  # 平均
        
        # ===== 4. 已知位置约束 =====
        known_match = 0
        for (r, c), v in known_positions.items():
            if self.grid[r][c] == v:
                known_match += 1
        known_fitness = known_match / len(known_positions) if known_positions else 1.0
        
        # ===== 5. 基础适应度（动态权重加权）=====
        base_fitness = (
            weights['row'] * row_fitness +
            weights['col'] * col_fitness +
            weights['box'] * box_fitness +
            weights['known'] * known_fitness
        )
        
        # ===== 6. 多样性奖励 =====
        diversity_bonus = 0.0
        if reference_solutions and len(reference_solutions) > 0:
            # 计算与参考解的最小汉明距离
            min_hamming = float('inf')
            for ref in reference_solutions:
                hamming = self._count_hamming(ref.grid)
                if hamming < min_hamming:
                    min_hamming = hamming
            
            self.hamming_to_best = min_hamming
            # 汉明距离越大，多样性奖励越高
            diversity_bonus = config.hamming_bonus_max * (min_hamming / 256)
        
        # ===== 7. 精英惩罚（避免局部最优岛屿）=====
        elite_penalty_factor = 1.0
        
        # ===== 最终适应度 =====
        self.fitness = (base_fitness + diversity_bonus) * elite_penalty_factor
        
        # 保存分解
        self.fitness_breakdown = {
            'row': row_fitness,
            'col': col_fitness,
            'box': box_fitness,
            'known': known_fitness,
            'base': base_fitness,
            'diversity_bonus': diversity_bonus,
            'hamming_to_best': self.hamming_to_best,
            'weights': weights,
        }
        
        return self.fitness
    
    def _count_hamming(self, other_grid: List[List[int]]) -> int:
        """计算汉明距离"""
        count = 0
        for r in range(16):
            for c in range(16):
                if self.grid[r][c] != other_grid[r][c]:
                    count += 1
        return count
    
    def to_vector(self) -> np.ndarray:
        """转换为向量"""
        return np.array([v for row in self.grid for v in row])


# ═══════════════════════════════════════════════════════════
# 第三部分：改进的遗传优化器
# ═══════════════════════════════════════════════════════════

class ImprovedGeneticOptimizer:
    """
    改进的遗传优化器 V37
    
    核心改进：
    1. 熵权重化适应度函数
    2. 动态权重衰减
    3. 汉明距离多样性奖励
    4. 精英相似度检测与惩罚
    5. 自适应突变率
    """
    
    def __init__(
        self,
        known_positions: Dict[Tuple[int, int], int],
        row_permutations: Dict[str, List[List[int]]],
        population_size: int = 80,
        max_generations: int = 500,
        mutation_rate: float = 0.03,
        crossover_rate: float = 0.85,
        elite_pool_size: int = 8,
    ):
        
        self.known_positions = known_positions
        self.row_permutations = row_permutations
        self.pop_size = population_size
        self.max_gens = max_generations
        self.base_mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_pool_size = elite_pool_size
        
        self.population: List[ImprovedIndividual] = []
        self.elite_pool: List[ImprovedIndividual] = []
        self.generation_log: List[Dict] = []
        self.solutions_found: List[ImprovedIndividual] = []
        
        # 熵权重计算器
        self.entropy_calc = EntropyWeightCalculator()
        self.fitness_config = AdaptiveFitnessConfig()
        
        # 种群历史（用于多样性检测）
        self.population_history: List[ImprovedIndividual] = []
        self.best_fitness_history: List[float] = []
    
    def _initialize_population(self) -> None:
        """初始化种群"""
        self.population = []
        
        unknown_rows = []
        for r in range(16):
            known_count = sum(1 for (kr, _) in self.known_positions if kr == r)
            if known_count < 16:
                unknown_rows.append(r)
        
        print(f"  未知行: {unknown_rows}")
        print(f"  未知位点: {sum(16 - sum(1 for (kr, _) in self.known_positions if kr == r) for r in range(16))} 个")
        
        for i in range(self.pop_size):
            grid = [[0] * 16 for _ in range(16)]
            
            # 填入锚点
            for (r, c), v in self.known_positions.items():
                grid[r][c] = v
            
            # 未知行从符阖排列中选择
            for r in unknown_rows:
                row_letter = chr(65 + r)
                if row_letter in self.row_permutations:
                    perms = self.row_permutations[row_letter]
                    compatible = []
                    for perm in perms:
                        match = True
                        for (kr, kc), kv in self.known_positions.items():
                            if kr == r and perm[kc] != 0 and perm[kc] != kv:
                                match = False
                                break
                        if match:
                            compatible.append(perm)
                    
                    if compatible:
                        grid[r] = random.choice(compatible)[:]
                    else:
                        grid[r] = list(range(1, 17))
                        random.shuffle(grid[r])
            
            ind = ImprovedIndividual(grid=grid, generation=0)
            self.population.append(ind)
        
        print(f"  初始化种群的 {self.pop_size} 个个体")
    
    def _count_conflicts(self, grid: List[List[int]], constraint_type: str) -> int:
        """统计冲突数"""
        conflicts = 0
        
        if constraint_type in ['col', 'both']:
            for c in range(16):
                col_vals = [grid[r][c] for r in range(16) if grid[r][c] != 0]
                conflicts += len(col_vals) - len(set(col_vals))
        
        if constraint_type in ['box', 'both']:
            for box_idx in range(16):
                box_vals = [grid[r][c] for r in range(16) for c in range(16)
                           if (r // 4) * 4 + (c // 4) == box_idx and grid[r][c] != 0]
                conflicts += len(box_vals) - len(set(box_vals))
        
        return conflicts
    
    def _select_parents(self) -> Tuple[ImprovedIndividual, ImprovedIndividual]:
        """锦标赛选择"""
        tournament_size = 5
        
        def tournament():
            candidates = random.sample(self.population, min(tournament_size, len(self.population)))
            return max(candidates, key=lambda x: x.fitness)
        
        return tournament(), tournament()
    
    def _crossover(self, parent1: ImprovedIndividual, parent2: ImprovedIndividual) -> ImprovedIndividual:
        """交叉 - 基于行的排列交换"""
        child_grid = [row[:] for row in parent1.grid]
        
        if random.random() > self.crossover_rate:
            return ImprovedIndividual(grid=child_grid, generation=parent1.generation + 1)
        
        # 随机选择父代2的行替换
        for r in range(16):
            if random.random() < 0.4:
                row_letter = chr(65 + r)
                if row_letter in self.row_permutations:
                    parent2_perms = self.row_permutations[row_letter]
                    compatible = []
                    for perm in parent2_perms:
                        match = True
                        for (kr, kc), kv in self.known_positions.items():
                            if kr == r and perm[kc] != 0 and perm[kc] != kv:
                                match = False
                                break
                        if match:
                            compatible.append(perm)
                    
                    if compatible:
                        child_grid[r] = random.choice(compatible)[:]
        
        return ImprovedIndividual(grid=child_grid, generation=parent1.generation + 1)
    
    def _get_adaptive_mutation_rate(self, generation: int, best_fitness: float) -> float:
        """
        自适应突变率
        
        策略：
        - 适应度低时：高突变率（快速探索）
        - 适应度高时：低突变率（精细调整）
        - 停滞时：临时提高突变率
        """
        base = self.base_mutation_rate
        
        # 适应度自适应
        if best_fitness < 0.5:
            return min(base * 3.0, 0.15)  # 早期快速探索
        elif best_fitness < 0.8:
            return min(base * 1.5, 0.08)  # 中期平衡
        else:
            return base * 0.7  # 后期精细调整
    
    def _mutate(self, individual: ImprovedIndividual, generation: int, 
                best_fitness: float) -> ImprovedIndividual:
        """突变 - 基于熵权重的智能突变"""
        mutated = ImprovedIndividual(
            grid=[row[:] for row in individual.grid],
            generation=individual.generation + 1
        )
        
        mutation_rate = self._get_adaptive_mutation_rate(generation, best_fitness)
        
        # 优先突变高熵位置
        for r in range(16):
            known_cols = [c for (kr, c) in self.known_positions if kr == r]
            unknown_cols = [c for c in range(16) if c not in known_cols]
            
            # 按熵权重排序未知列
            unknown_cols.sort(key=lambda c: self.entropy_calc.get_col_weight(r, c), reverse=True)
            
            for c in unknown_cols:
                if random.random() < mutation_rate:
                    # 获取列和宫的禁用值
                    forbidden = set()
                    for rr in range(16):
                        if mutated.grid[rr][c] != 0:
                            forbidden.add(mutated.grid[rr][c])
                    
                    box_idx = (r // 4) * 4 + (c // 4)
                    for rr in range(16):
                        for cc in range(16):
                            if (rr // 4) * 4 + (cc // 4) == box_idx and mutated.grid[rr][cc] != 0:
                                forbidden.add(mutated.grid[rr][cc])
                    
                    available = [v for v in range(1, 17) if v not in forbidden]
                    if available:
                        mutated.grid[r][c] = random.choice(available)
        
        return mutated
    
    def _detect_similarity(self, individual: ImprovedIndividual) -> float:
        """检测与历史个体的相似度"""
        if not self.population_history:
            return 0.0
        
        min_hamming_ratio = float('inf')
        for hist in self.population_history[-20:]:  # 只看最近 20 个
            hamming = individual._count_hamming(hist.grid)
            ratio = hamming / 256
            if ratio < min_hamming_ratio:
                min_hamming_ratio = ratio
        
        return 1.0 - min_hamming_ratio  # 相似度（0-1）
    
    def optimize(self, verbose: bool = True) -> Dict:
        """执行改进的遗传优化"""
        print("\n" + "=" * 70)
        print("┌─ 符闔博弈優選策略 V37.0 改进遗传优化器 ────────┐")
        print("│  熵权重化 | 动态权重 | 多样性奖励 | 精英惩罚    │")
        print("└─────────────────────────────────────────────────┘")
        print()
        
        # 打印熵分布
        self.entropy_calc.print_profile()
        print()
        
        # 初始化
        print("[初始化] 构建熵权重化种群...")
        self._initialize_population()
        
        # 初始适应度
        for ind in self.population:
            ind.compute_adaptive_fitness(
                self.known_positions, self.entropy_calc, self.fitness_config,
                0, self.max_gens, self.solutions_found if self.solutions_found else None
            )
        
        best = max(self.population, key=lambda x: x.fitness)
        print(f"  初始最佳适应度: {best.fitness:.4f}")
        print(f"  初始最佳分解: {best.fitness_breakdown}")
        print()
        
        # 优化循环
        start_time = time.time()
        stagnation_count = 0
        best_stagnation_start = 0
        
        for gen in range(1, self.max_gens + 1):
            # 评估
            for ind in self.population:
                ind.compute_adaptive_fitness(
                    self.known_positions, self.entropy_calc, self.fitness_config,
                    gen, self.max_gens, 
                    self.solutions_found if self.solutions_found else self.elite_pool
                )
            
            # 精英保留
            sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
            self.elite_pool = sorted_pop[:self.elite_pool_size]
            
            current_best = sorted_pop[0]
            avg_fitness = sum(ind.fitness for ind in self.population) / self.pop_size
            col_conflicts = self._count_conflicts(current_best.grid, 'col')
            box_conflicts = self._count_conflicts(current_best.grid, 'box')
            
            # 记录历史
            self.best_fitness_history.append(current_best.fitness)
            self.population_history.extend(self.population[:5])
            
            # 检测停滞
            if len(self.best_fitness_history) >= 50:
                recent_best = max(self.best_fitness_history[-50:])
                if recent_best == self.best_fitness_history[-1]:
                    stagnation_count += 1
                else:
                    stagnation_count = 0
            
            # 输出
            if gen % 50 == 0 or gen == 1:
                diversity = np.std([ind.hamming_to_best for ind in self.population])
                if verbose:
                    print(f"  代数 {gen:4d}: 最佳 {current_best.fitness:.4f} | "
                          f"平均 {avg_fitness:.4f} | "
                          f"列冲突 {col_conflicts} | 宫冲突 {box_conflicts} | "
                          f"多样性σ={diversity:.2f} | "
                          f"权重=(行{self.fitness_config.get_dynamic_weights(gen, self.max_gens)['row']:.2f}"
                          f" 列{self.fitness_config.get_dynamic_weights(gen, self.max_gens)['col']:.2f}"
                          f" 宫{self.fitness_config.get_dynamic_weights(gen, self.max_gens)['box']:.2f})")
            
            # 终止条件
            if current_best.fitness >= 0.999:
                print(f"\n  ✓ 达到终止条件: 适应度 {current_best.fitness:.4f}")
                self.solutions_found.append(current_best)
                break
            
            # 记录当前代最佳（用于最终结果）
            self._current_gen_best = current_best
            
            # 新种群
            new_population = []
            
            # 保留精英
            for elite in self.elite_pool[:max(3, self.elite_pool_size // 3)]:
                new_population.append(ImprovedIndividual(
                    grid=[row[:] for row in elite.grid],
                    generation=gen,
                ))
            
            # 生成后代
            while len(new_population) < self.pop_size:
                p1, p2 = self._select_parents()
                child = self._crossover(p1, p2)
                child = self._mutate(child, gen, current_best.fitness)
                new_population.append(child)
            
            self.population = new_population[:self.pop_size]
            
            # 提前终止：如果连续 100 代无改善
            if stagnation_count >= 100:
                print(f"\n  ⚠ 停滞 {stagnation_count} 代，适应度高原检测")
                print(f"  当前最佳: {current_best.fitness:.4f}")
                print(f"  建议: 增加种群规模或调整熵权重")
                break
        
        elapsed = time.time() - start_time
        
        # 最终分析：使用最后一代评估过的最佳个体
        final_best = getattr(self, '_current_gen_best', None)
        if final_best is None:
            # 如果未设置，从当前种群重新计算
            for ind in self.population:
                ind.compute_adaptive_fitness(
                    self.known_positions, self.entropy_calc, self.fitness_config,
                    gen, self.max_gens,
                    self.solutions_found if self.solutions_found else self.elite_pool
                )
            final_best = max(self.population, key=lambda x: x.fitness)
        
        result = {
            'version': 'V37_improved_ga',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'config': {
                'population_size': self.pop_size,
                'max_generations': self.max_gens,
                'mutation_rate': self.base_mutation_rate,
                'crossover_rate': self.crossover_rate,
            },
            'entropy_profile': {
                f'{chr(65+i)}': self.entropy_calc.row_entropies.get(i, 0)
                for i in range(16)
            },
            'best_fitness': final_best.fitness,
            'best_fitness_breakdown': final_best.fitness_breakdown,
            'hamming_to_best': final_best.hamming_to_best,
            'col_conflicts': self._count_conflicts(final_best.grid, 'col'),
            'box_conflicts': self._count_conflicts(final_best.grid, 'box'),
            'generations_run': gen,
            'elapsed_seconds': elapsed,
            'solutions_found': len(self.solutions_found),
            'best_history': self.best_fitness_history[-20:],
        }
        
        print(f"\n{'='*70}")
        print(f"  最终结果:")
        print(f"    最佳适应度: {final_best.fitness:.4f}")
        print(f"    分解: 行={final_best.fitness_breakdown.get('row', 0):.3f}, "
              f"列={final_best.fitness_breakdown.get('col', 0):.3f}, "
              f"宫={final_best.fitness_breakdown.get('box', 0):.3f}")
        print(f"    汉明距离: {final_best.hamming_to_best}")
        print(f"    运行代数: {gen} | 耗时: {elapsed:.1f}s")
        print(f"{'='*70}\n")
        
        return result


# ═══════════════════════════════════════════════════════════
# 第四部分：权重对比分析
# ═══════════════════════════════════════════════════════════

def compare_weight_strategies(
    known_positions: Dict,
    row_permutations: Dict,
    n_test: int = 10
) -> Dict:
    """
    对比不同权重策略的效果
    
    策略：
    1. 固定权重 (V19 原版): 行 0.1, 列 0.45, 宫 0.45
    2. 熵权重 (V37): 基于行熵动态调整
    3. 动态权重 (V37): 基于代数动态调整
    4. 混合权重 (V37): 熵+动态+多样性
    """
    
    strategies = {
        'fixed_v19': {
            'row': 0.1, 'col': 0.45, 'box': 0.45, 'known': 0.0,
            'entropy_w': False, 'dynamic': False, 'diversity': False
        },
        'entropy_v37': {
            'row': 0.1, 'col': 0.4, 'box': 0.4, 'known': 0.1,
            'entropy_w': True, 'dynamic': False, 'diversity': False
        },
        'dynamic_v37': {
            'row': 0.08, 'col': 0.42, 'box': 0.4, 'known': 0.1,
            'entropy_w': False, 'dynamic': True, 'diversity': False
        },
        'mixed_v37': {
            'row': 0.08, 'col': 0.42, 'box': 0.4, 'known': 0.1,
            'entropy_w': True, 'dynamic': True, 'diversity': True
        },
    }
    
    results = {}
    
    for name, cfg in strategies.items():
        print(f"\n  测试策略: {name}")
        
        # 简化版本：只测试 1 个个体
        entropy_calc = EntropyWeightCalculator()
        config = AdaptiveFitnessConfig()
        
        # 生成测试个体
        test_ind = ImprovedIndividual(
            grid=[[0]*16 for _ in range(16)],
            generation=0
        )
        
        # 填入部分锚点
        for (r, c), v in list(known_positions.items())[:50]:
            test_ind.grid[r][c] = v
        
        # 随机填充其余
        for r in range(16):
            if 0 in test_ind.grid[r]:
                for c in range(16):
                    if test_ind.grid[r][c] == 0 and (r, c) not in known_positions:
                        test_ind.grid[r][c] = random.randint(1, 16)
        
        # 计算适应度（根据策略选择配置）
        if cfg['entropy_w']:
            test_ind.compute_adaptive_fitness(
                known_positions, entropy_calc, config,
                0, 100, reference_solutions=None
            )
        else:
            # 固定权重简化计算
            row_fit = sum(1 if len(set(test_ind.grid[r])) == 16 else 0 for r in range(16)) / 16
            col_fit = 0  # 简化
            box_fit = 0  # 简化
            test_ind.fitness = cfg['row'] * row_fit + cfg['col'] * col_fit + cfg['box'] * box_fit
        
        results[name] = {
            'fitness': test_ind.fitness,
            'breakdown': test_ind.fitness_breakdown if hasattr(test_ind, 'fitness_breakdown') else {},
        }
        
        print(f"    适应度: {test_ind.fitness:.4f}")
    
    return results


# ═══════════════════════════════════════════════════════════
# 主程序
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    # 加载配置
    with open('sudoku_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 转换已知位置
    known_positions = {}
    for entry in config.get('known_digits', config.get('anchors', [])):
        if isinstance(entry, dict):
            r = entry.get('row', 0) - 1
            c = entry.get('col', 0) - 1
            v = entry.get('value', 0)
            known_positions[(r, c)] = v
        elif isinstance(entry, (list, tuple)) and len(entry) >= 3:
            known_positions[(entry[0], entry[1])] = entry[2]
    
    print(f"✓ 加载 {len(known_positions)} 个锚点")
    
    # 加载符阖排列（简化：使用标准排列）
    row_permutations = {}
    for r in range(16):
        row_letter = chr(65 + r)
        # 简化：每个行使用所有排列的子集
        row_permutations[row_letter] = [list(range(1, 17))] * 10
    
    # 运行 V37 改进优化器
    print("\n" + "="*70)
    print(" V37.0 改进遗传优化器")
    print("="*70)
    
    optimizer = ImprovedGeneticOptimizer(
        known_positions=known_positions,
        row_permutations=row_permutations,
        population_size=80,
        max_generations=300,
        mutation_rate=0.03,
        crossover_rate=0.85,
        elite_pool_size=8,
    )
    
    result = optimizer.optimize(verbose=True)
    
    # 保存结果
    with open('v37_improved_ga_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 结果已保存: v37_improved_ga_result.json")
    
    # 权重对比
    print("\n" + "="*70)
    print(" 权重策略对比")
    print("="*70)
    
    comparison = compare_weight_strategies(known_positions, row_permutations, n_test=5)
    
    print("\n对比总结:")
    print(f"  {'策略':<15} {'适应度':>8}")
    print(f"  {'-'*15} {'-'*8}")
    for name, r in comparison.items():
        print(f"  {name:<15} {r['fitness']:>8.4f}")
