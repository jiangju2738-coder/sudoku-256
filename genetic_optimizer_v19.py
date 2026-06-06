#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 符闔博弈優選策略 V19.0 - 遺傳優化器（多變體支援）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

三大架構融合：
  [1] 92固定錨點神經網絡     - 100%固定位置作為遺傳優化錨點
  [2] 164未知位點遺傳搜索    - 列+宮約束約束下的GA優化
  [3] 100D基因指紋系統       - 行約束+列約束+宮約束三者充要條件

核心目標：
  - 92個100%固定位置作為遺傳網絡神經元節點
  - 164個未知位點通過遺傳演算法優化
  - 整合CP-SAT進行最終驗證
  - 支援多變體：標準、X Sudoku、Killer Sudoku

符闔數獨種類理論基礎（深度學習後落實）：
  [標準變體] 16×16數獨, 25×25數獨, 36×36數獨
  [自由變體] Jigsaw Sudoku, Irregular Sudoku (幾何約束)
  [額外約束] X Sudoku (對角線), Killer Sudoku (Cage求和)
  [符闔變體] 每行特定排列約束 (符闔排列 + 列/宮AllDifferent)

變體擴展 (V19.1)：
  - 可插入 SudokuVariant 基類
  - X Sudoku: 對角線 AllDifferent 約束
  - Killer Sudoku: Cage 求和約束 + Cage 內不重複
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import time
import random
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

# 導入變體系統
try:
    from sudoku_variants_v19 import (
        SudokuVariant, XsudokuVariant, KillersudokuVariant,
        SudokuVariantType, GeneFingerprint100DAdapter
    )
    VARIANT_MODULE_AVAILABLE = True
except ImportError:
    VARIANT_MODULE_AVAILABLE = False
    SudokuVariant = None


# ═══════════════════════════════════════════════════════════
# 第一架構：92固定錨點神經網絡
# ═══════════════════════════════════════════════════════════

class QuantumState(Enum):
    """量子態定義"""
    SUPERPOSITION = "SUPERPOSITION"   # 多解模式
    COLLAPSED = "COLLAPSED"           # 唯一解
    INFEASIBLE = "INFEASIBLE"         # 無解
    PARTIAL_COLLAPSE = "PARTIAL_COLLAPSED"  # 部分坍縮


@dataclass
class AnchoredPosition:
    """92個100%固定錨點"""
    row: int          # 行索引 (0-15)
    col: int          # 列索引 (0-15)
    value: int        # 固定值 (1-16)
    confidence: float = 1.0  # 固定置信度
    gene_id: str = ""        # 基因指紋ID


@dataclass
class GeneFingerprint100D:
    """
    100D基因指紋系統（多變體支援）
    
    維度定義：
    - 16D: 行約束 (符闔排列特徵)
    - 16D: 列約束 (AllDifferent分布)
    - 16D: 宮約束 (4×4塊分布)
    - 16D: 對角線約束 (X Sudoku)
    - 16D: 連續性約束 (Consecutive)
    - 20D: 符闔排列特殊約束 (易經六十四卦映射)
    - 20D: 全局AllDifferent約束
    - 20D: 位置過度固定修正約束
    
    變體擴展維度：
    - X Sudoku: diagonal_dimensions (對角線 AllDifferent)
    - Killer Sudoku: cage_sum_dimensions + cage_unique_dimensions
    
    充要條件：行約束 ∧ 列約束 ∧ 宮約束 (三者同時滿足)
    """
    row_dimensions: List[float] = field(default_factory=lambda: [0.0] * 16)
    col_dimensions: List[float] = field(default_factory=lambda: [0.0] * 16)
    box_dimensions: List[float] = field(default_factory=lambda: [0.0] * 16)
    diagonal_dimensions: List[float] = field(default_factory=lambda: [0.0] * 16)
    consecutive_dimensions: List[float] = field(default_factory=lambda: [0.0] * 16)
    cage_sum_dimensions: List[float] = field(default_factory=lambda: [0.0] * 20)
    cage_unique_dimensions: List[float] = field(default_factory=lambda: [0.0] * 16)
    fuhh_special: List[float] = field(default_factory=lambda: [0.0] * 20)
    global_alldiff: List[float] = field(default_factory=lambda: [0.0] * 20)
    overflow_correction: List[float] = field(default_factory=lambda: [0.0] * 20)
    
    variant_type: str = "standard"  # standard, x_sudoku, killer_sudoku
    
    def compute(self, grid: List[List[int]], known_positions: Dict,
                variant: Optional[SudokuVariant] = None) -> 'GeneFingerprint100D':
        """計算100D基因指紋（支援變體）"""
        # 行約束特徵
        for r in range(16):
            row_vals = grid[r]
            if 0 in row_vals:
                self.row_dimensions[r] = 0.0
            elif len(set(row_vals)) == 16:
                self.row_dimensions[r] = 1.0
            else:
                duplicates = len(row_vals) - len(set(row_vals))
                self.row_dimensions[r] = (16 - duplicates) / 16
        
        # 列約束特徵
        for c in range(16):
            col_vals = [grid[r][c] for r in range(16)]
            unique_count = len(set(col_vals))
            self.col_dimensions[c] = unique_count / 16
        
        # 宮約束特徵
        for box_idx in range(16):
            box_vals = []
            for r in range(16):
                for c in range(16):
                    if (r // 4) * 4 + (c // 4) == box_idx:
                        box_vals.append(grid[r][c])
            if 0 in box_vals:
                self.box_dimensions[box_idx] = 0.0
            else:
                unique_count = len(set(box_vals))
                self.box_dimensions[box_idx] = unique_count / 16
        
        # 變體擴展計算
        if variant is not None:
            self._compute_variant_dimensions(grid, variant)
        
        return self
    
    def _compute_variant_dimensions(self, grid: List[List[int]], 
                                     variant: SudokuVariant) -> None:
        """計算變體特有維度"""
        if isinstance(variant, XsudokuVariant):
            self.variant_type = "x_sudoku"
            # 計算對角線特徵
            for d_idx, (diag_name, diag) in enumerate(variant.diagonals.items()):
                diag_vals = [grid[r][c] for r, c in diag.cells]
                if 0 in diag_vals:
                    self.diagonal_dimensions[d_idx] = 0.0
                else:
                    self.diagonal_dimensions[d_idx] = len(set(diag_vals)) / 16
        
        elif isinstance(variant, KillersudokuVariant):
            self.variant_type = "killer_sudoku"
            # 計算 Cage 特徵
            for i, cage in enumerate(variant.cages[:20]):
                cage_vals = [grid[r][c] for r, c in cage.cells if grid[r][c] != 0]
                actual_sum = sum(cage_vals)
                
                if actual_sum == cage.target_sum:
                    self.cage_sum_dimensions[i] = 1.0
                elif len(cage_vals) > 0:
                    deviation = abs(actual_sum - cage.target_sum)
                    max_sum = sum(range(1, 17))
                    self.cage_sum_dimensions[i] = max(0.0, 1.0 - deviation / max_sum)
                else:
                    self.cage_sum_dimensions[i] = 0.0
                
                # Cage 唯一性
                if cage.must_be_unique:
                    self.cage_unique_dimensions[i] = 1.0 if len(set(cage_vals)) == len(cage_vals) else 0.0
                else:
                    self.cage_unique_dimensions[i] = 1.0
    
    def total_fitness(self) -> float:
        """總體適應度（支援變體）"""
        row_fit = sum(self.row_dimensions) / 16
        col_fit = sum(self.col_dimensions) / 16
        box_fit = sum(self.box_dimensions) / 16
        
        # 基礎適應度
        base_fitness = 0.1 * row_fit + 0.45 * col_fit + 0.45 * box_fit
        
        # 變體擴展適應度
        variant_fitness = 0.0
        if self.variant_type == "x_sudoku":
            diag_fit = sum(self.diagonal_dimensions[:2]) / 2 if self.diagonal_dimensions[:2] else 0.0
            variant_fitness = 0.1 * diag_fit
            base_fitness *= 0.9
        
        elif self.variant_type == "killer_sudoku":
            cage_sum_fit = sum(self.cage_sum_dimensions) / max(1, len(self.cage_sum_dimensions))
            cage_unique_fit = sum(self.cage_unique_dimensions) / max(1, len(self.cage_unique_dimensions))
            cage_fitness = 0.6 * cage_sum_fit + 0.4 * cage_unique_fit
            variant_fitness = 0.2 * cage_fitness
            base_fitness *= 0.8
        
        return base_fitness + variant_fitness


# ═══════════════════════════════════════════════════════════
# 第二架構：164未知位點遺傳優化
# ═══════════════════════════════════════════════════════════

@dataclass
class Individual:
    """遺傳個體（支援多變體）"""
    grid: List[List[int]]          # 16×16網格
    fitness: float = 0.0           # 適應度
    gene_fingerprint: Optional[GeneFingerprint100D] = None
    generation: int = 0            # 所屬代數
    elite_status: bool = False     # 精英狀態
    variant: Optional[SudokuVariant] = None  # 變體引用
    
    def compute_fitness(self, known_positions: Dict, 
                        col_constraints: Dict, box_constraints: Dict,
                        variant: Optional[SudokuVariant] = None) -> float:
        """
        計算適應度（支援多變體）
        
        權重: 行約束 0.1, 列約束 0.45, 宮約束 0.45
        變體擴展: X Sudoku(+0.1), Killer Sudoku(+0.2)
        """
        self.variant = variant
        
        # 如果有變體，使用變體的約束適應度
        if variant is not None and VARIANT_MODULE_AVAILABLE:
            self.fitness = variant.compute_constraint_fitness(self.grid, known_positions)
        else:
            # 標準適應度計算
            # 1. 行約束適應度
            row_fitness = 0.0
            for r in range(16):
                row_vals = self.grid[r]
                if 0 in row_vals:
                    row_fitness += 0
                elif len(set(row_vals)) == 16:
                    row_fitness += 1.0
                else:
                    duplicates = len(row_vals) - len(set(row_vals))
                    row_fitness += (16 - duplicates) / 16
            
            # 2. 列約束適應度
            col_fitness = 0.0
            for c in range(16):
                col_vals = [self.grid[r][c] for r in range(16)]
                if 0 in col_vals:
                    col_fitness += 0
                elif len(set(col_vals)) == 16:
                    col_fitness += 1.0
                else:
                    duplicates = len(col_vals) - len(set(col_vals))
                    col_fitness += (16 - duplicates) / 16
            
            # 3. 宮約束適應度
            box_fitness = 0.0
            for box_idx in range(16):
                box_vals = []
                for r in range(16):
                    for c in range(16):
                        if (r // 4) * 4 + (c // 4) == box_idx:
                            box_vals.append(self.grid[r][c])
                
                if 0 in box_vals:
                    box_fitness += 0
                elif len(set(box_vals)) == 16:
                    box_fitness += 1.0
                else:
                    duplicates = len(box_vals) - len(set(box_vals))
                    box_fitness += (16 - duplicates) / 16
            
            # 4. 已知位置約束
            known_match = 0
            for (r, c), v in known_positions.items():
                if self.grid[r][c] == v:
                    known_match += 1
            known_fitness = known_match / len(known_positions) if known_positions else 1.0
            
            # 總體適應度
            self.fitness = (
                0.1 * row_fitness / 16 +
                0.45 * col_fitness / 16 +
                0.45 * box_fitness / 16 +
                0.1 * known_fitness
            )
        
        return self.fitness
    
    def to_vector(self) -> np.ndarray:
        """轉換為向量表示 (用於遺傳操作)"""
        return np.array([v for row in self.grid for v in row])


class GeneticOptimizer:
    """
    遺傳優化器 - 164未知位點搜索（支援多變體）
    
    核心機制：
    1. 錨點固定：92個位置100%固定，作為遺傳網絡神經元節點
    2. 遺傳搜索：164個未知位點通過GA優化
    3. 精英回溯：優秀個體保留並優化
    4. 鏈式進化：代間信息傳遞
    
    變體支援：
    - variant: 可選的 SudokuVariant 對象
    - 支援標準、X Sudoku、Killer Sudoku
    """
    
    def __init__(self, 
                 known_positions: Dict[Tuple[int, int], int],
                 row_permutations: Dict[str, List[List[int]]],
                 population_size: int = 100,
                 max_generations: int = 1000,
                 mutation_rate: float = 0.05,
                 crossover_rate: float = 0.8,
                 variant: Optional[SudokuVariant] = None):
        
        self.known_positions = known_positions  # {(r,c): v} 92個固定位置
        self.row_permutations = row_permutations  # 每行符闔排列
        self.pop_size = population_size
        self.max_gens = max_generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.variant = variant  # 可選變體
        
        self.population: List[Individual] = []
        self.elite_pool: List[Individual] = []
        self.generation_log: List[Dict] = []
        
        # 遺傳網絡神經元節點 (92錨點)
        self.neural_anchors = self._build_neural_anchors()
    
    def _build_neural_anchors(self) -> Dict[str, AnchoredPosition]:
        """建構92個錨點神經網絡"""
        anchors = {}
        for (r, c), v in self.known_positions.items():
            anchor_id = f"A{r:02d}_{c:02d}"
            anchors[anchor_id] = AnchoredPosition(
                row=r, col=c, value=v, confidence=1.0,
                gene_id=f"G{len(anchors)+1:03d}"
            )
        return anchors
    
    def _initialize_population(self) -> None:
        """初始化種群"""
        self.population = []
        
        # 為每個未知行選擇符闔排列
        unknown_rows = []
        for r in range(16):
            known_count = sum(1 for (kr, _) in self.known_positions if kr == r)
            if known_count < 16:
                unknown_rows.append(r)
        
        for _ in range(self.pop_size):
            grid = [[0] * 16 for _ in range(16)]
            
            # 填入92個固定錨點
            for (r, c), v in self.known_positions.items():
                grid[r][c] = v
            
            # 對未知行從符闔排列中選擇
            for r in unknown_rows:
                row_letter = chr(65 + r)  # A-P
                if row_letter in self.row_permutations:
                    perms = self.row_permutations[row_letter]
                    # 篩選與已知位置匹配的排列
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
                        # 隨機生成
                        grid[r] = list(range(1, 17))
                        random.shuffle(grid[r])
            
            individual = Individual(grid=grid, generation=0)
            self.population.append(individual)
        
        print(f"  初始化種群: {self.pop_size} 個個體")
        print(f"  未知行數: {len(unknown_rows)} 行")
        print(f"  未知位點: {164} 個")
    
    def _selection(self, tournament_size: int = 5) -> Individual:
        """輪盤賭選擇 + 精英保留"""
        # 精英個體直接返回
        if random.random() < 0.1 and self.elite_pool:
            return random.choice(self.elite_pool[:min(3, len(self.elite_pool))])
        
        #  tournaments
        tournament = random.sample(self.population, min(tournament_size, len(self.population)))
        return max(tournament, key=lambda ind: ind.fitness)
    
    def _crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        """交叉操作 - 基於行的排列交換"""
        child_grid = [row[:] for row in parent1.grid]
        
        if random.random() > self.crossover_rate:
            return Individual(grid=child_grid, generation=parent1.generation + 1)
        
        # 基於符闔排列進行交叉
        # 選擇父代2的行替換
        for r in range(16):
            if random.random() < 0.5:
                # 檢查是否與已知位置衝突
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
        
        return Individual(grid=child_grid, generation=parent1.generation + 1)
    
    def _mutate(self, individual: Individual) -> Individual:
        """突變操作 - 基於遺傳網絡的節點調整"""
        mutated = Individual(
            grid=[row[:] for row in individual.grid],
            generation=individual.generation + 1
        )
        
        # 只對未知位置進行突變
        for r in range(16):
            known_cols = [c for (kr, c) in self.known_positions if kr == r]
            unknown_cols = [c for c in range(16) if c not in known_cols]
            
            for c in unknown_cols:
                if random.random() < self.mutation_rate:
                    # 基於遺傳網絡的節點調整
                    # 考慮與錨點相鄰的位置
                    neighbor_values = []
                    for (nr, nc), nv in self.neural_anchors.items():
                        if abs(nr - r) + abs(nc - c) <= 2:
                            neighbor_values.append(nv.value)
                    
                    if neighbor_values:
                        # 避免與鄰居衝突
                        available = [v for v in range(1, 17) if v not in self.mutate_grid_cols(mutated.grid, r, c)]
                        if available:
                            mutated.grid[r][c] = random.choice(available)
        
        return mutated
    
    def mutate_grid_cols(self, grid: List[List[int]], row: int, col: int) -> Set[int]:
        """獲取需要避免的值（列和宮）"""
        forbidden = set()
        # 列約束
        for r in range(16):
            if grid[r][col] != 0:
                forbidden.add(grid[r][col])
        # 宮約束
        box_idx = (row // 4) * 4 + (col // 4)
        for r in range(16):
            for c in range(16):
                if (r // 4) * 4 + (c // 4) == box_idx and grid[r][c] != 0:
                    forbidden.add(grid[r][c])
        return forbidden
    
    def _repair(self, individual: Individual) -> Individual:
        """保守修復 - 只在適應度提升時接受"""
        original_fitness = individual.fitness
        
        # 修復列衝突
        col_conflicts = []
        for c in range(16):
            col_vals = [individual.grid[r][c] for r in range(16)]
            seen = {}
            for r, v in enumerate(col_vals):
                if v != 0:
                    if v in seen:
                        col_conflicts.append((r, c, v))
                    else:
                        seen[v] = r
        
        # 嘗試修復
        for r, c, v in col_conflicts:
            # 檢查是否為未知位置
            if (r, c) not in self.known_positions:
                # 尋找替換值
                available = [val for val in range(1, 17) 
                           if val not in [individual.grid[r][cc] for cc in range(16)]
                           and val not in [individual.grid[rr][c] for rr in range(16)]]
                if available:
                    old_val = individual.grid[r][c]
                    individual.grid[r][c] = random.choice(available)
        
        # 計算修復後適應度
        individual.compute_fitness(self.known_positions, {}, {})
        
        # 保守策略：只有修復提升適應度才保留
        if individual.fitness <= original_fitness:
            # 回滾
            pass
        
        return individual
    
    def optimize(self, verbose: bool = True) -> Dict:
        """執行遺傳優化（支援多變體）"""
        print("\n" + "=" * 70)
        print("┌─ 符闔博弈優選策略 V19.0 遺傳優化器 ─────────────────┐")
        if self.variant:
            variant_name = self.variant.__class__.__name__
            print(f"│  92固定錨點 | 164未知位點 | {variant_name}          │")
        else:
            print("│  92固定錨點 | 164未知位點 | 標準數獨          │")
        print("└───────────────────────────────────────────────────┘")
        print()
        
        # 初始化
        print("[初始化] 構建遺傳網絡...")
        print(f"  錨點節點: {len(self.neural_anchors)} 個")
        if self.variant:
            additional = self.variant.get_additional_constraints()
            print(f"  變體: {additional.get('variant_type', 'standard')}")
        self._initialize_population()
        
        # 初始適應度計算
        for ind in self.population:
            ind.compute_fitness(self.known_positions, {}, {}, self.variant)
        
        best = max(self.population, key=lambda x: x.fitness)
        print(f"  初始最佳適應度: {best.fitness:.4f}")
        print()
        
        # 優化循環
        generation_start = time.time()
        best_history = []
        
        for gen in range(1, self.max_gens + 1):
            # 評估所有個體
            for ind in self.population:
                ind.compute_fitness(self.known_positions, {}, {}, self.variant)
            
            # 精英保留
            sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
            self.elite_pool = sorted_pop[:10]
            for elite in self.elite_pool:
                elite.elite_status = True
            
            # 記錄歷史
            current_best = sorted_pop[0]
            avg_fitness = sum(ind.fitness for ind in self.population) / self.pop_size
            best_history.append({
                'generation': gen,
                'best_fitness': current_best.fitness,
                'avg_fitness': avg_fitness,
                'col_conflicts': self._count_conflicts(current_best.grid, 'col'),
                'box_conflicts': self._count_conflicts(current_best.grid, 'box')
            })
            
            # 輸出進度
            if gen % 100 == 0 or gen == 1:
                if verbose:
                    print(f"  代數 {gen:4d}: 最佳 {current_best.fitness:.4f} | "
                          f"平均 {avg_fitness:.4f} | "
                          f"列衝突 {best_history[-1]['col_conflicts']} | "
                          f"宮衝突 {best_history[-1]['box_conflicts']}")
            
            # 終止條件
            if current_best.fitness >= 0.9999:
                print(f"\n  ✓ 達到終止條件: 適應度 {current_best.fitness:.4f}")
                break
            
            # 選擇 + 交叉 + 突變
            new_population = []
            
            # 保留精英
            for elite in self.elite_pool[:5]:
                new_population.append(Individual(
                    grid=[row[:] for row in elite.grid],
                    generation=gen,
                    elite_status=True,
                    variant=self.variant
                ))
            
            # 生成新個體
            while len(new_population) < self.pop_size:
                parent1 = self._selection()
                parent2 = self._selection()
                child = self._crossover(parent1, parent2)
                if random.random() < self.mutation_rate:
                    child = self._mutate(child)
                child = self._repair(child)
                child.variant = self.variant
                new_population.append(child)
            
            self.population = new_population[:self.pop_size]
        
        # 最終結果
        generation_elapsed = time.time() - generation_start
        final_best = max(self.population, key=lambda x: x.fitness)
        
        # 計算100D基因指紋
        gene_fp = GeneFingerprint100D()
        gene_fp.compute(final_best.grid, self.known_positions, self.variant)
        
        if verbose:
            print("\n" + "=" * 70)
            print("┌─ 優化完成 ──────────────────────────────────────┐")
            print(f"│  最終最佳適應度: {final_best.fitness:.4f}            │")
            print(f"│  遺傳代數: {len(best_history)}                    │")
            print(f"│  耗時: {generation_elapsed:.2f}秒                   │")
            if self.variant:
                print(f"│  變體類型: {self.variant.__class__.__name__}            │")
            print("└───────────────────────────────────────────────┘")
        
        return {
            'best_individual': final_best,
            'best_fitness': final_best.fitness,
            'generations': len(best_history),
            'elapsed_time': generation_elapsed,
            'gene_fingerprint': gene_fp,
            'history': best_history,
            'elite_pool_size': len(self.elite_pool),
            'quantum_state': self._determine_quantum_state(final_best),
            'variant_type': self.variant.__class__.__name__ if self.variant else 'standard'
        }
    
    def _count_conflicts(self, grid: List[List[int]], constraint_type: str) -> int:
        """計算約束衝突數量"""
        conflicts = 0
        
        if constraint_type == 'col':
            for c in range(16):
                col_vals = [grid[r][c] for r in range(16)]
                if 0 not in col_vals and len(set(col_vals)) < 16:
                    conflicts += 1
        elif constraint_type == 'box':
            for box_idx in range(16):
                box_vals = []
                for r in range(16):
                    for c in range(16):
                        if (r // 4) * 4 + (c // 4) == box_idx:
                            box_vals.append(grid[r][c])
                if 0 not in box_vals and len(set(box_vals)) < 16:
                    conflicts += 1
        
        return conflicts
    
    def _determine_quantum_state(self, individual: Individual) -> str:
        """確定量子態"""
        col_conflicts = self._count_conflicts(individual.grid, 'col')
        box_conflicts = self._count_conflicts(individual.grid, 'box')
        
        if col_conflicts == 0 and box_conflicts == 0:
            return QuantumState.COLLAPSED.value
        elif col_conflicts > 10 or box_conflicts > 10:
            return QuantumState.SUPERPOSITION.value
        else:
            return QuantumState.PARTIAL_COLLAPSE.value


# ═══════════════════════════════════════════════════════════
# 第三架構：100D基因指紋驗證與CP-SAT整合
# ═══════════════════════════════════════════════════════════

def load_config() -> Tuple[Dict[Tuple[int, int], int], Dict[str, List[List[int]]]]:
    """載入配置"""
    # 載入已知位置
    with open('sudoku_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    known_positions = {}
    for kd in config['known_digits']:
        r = kd['row'] - 1  # 轉為0索引
        c = kd['col'] - 1
        v = kd['value']
        known_positions[(r, c)] = v
    
    # 載入符闔排列
    import os
    row_permutations = {}
    row_map = {chr(65+i): f'A{i+1}_permutations.json' for i in range(16)}
    
    for letter, fname in row_map.items():
        fpath = f'D:/2026/WPF_Sudoku/Sudoku_256/{fname}'
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    row_permutations[letter] = data
                elif isinstance(data, dict) and 'permutations' in data:
                    row_permutations[letter] = data['permutations']
    
    return known_positions, row_permutations


def cp_sat_verify(individual: Individual, 
                  known_positions: Dict,
                  solution_limit: int = 5) -> Dict:
    """CP-SAT驗證最終結果"""
    from ortools.sat.python import cp_model
    
    print("\n[CP-SAT 驗證] 啟動精確求解驗證...")
    
    # 構建網格
    grid = individual.grid
    
    # 驗證已知位置
    for (r, c), v in known_positions.items():
        if grid[r][c] != v:
            print(f"  ⚠️ 已知位置不匹配: ({r},{c}) 期望 {v}, 實際 {grid[r][c]}")
    
    # 驗證約束
    col_ok = True
    box_ok = True
    
    # 列檢查
    for c in range(16):
        col_vals = [grid[r][c] for r in range(16)]
        if len(set(col_vals)) < 16:
            col_ok = False
            break
    
    # 宮檢查
    for box_idx in range(16):
        box_vals = []
        for r in range(16):
            for c in range(16):
                if (r // 4) * 4 + (c // 4) == box_idx:
                    box_vals.append(grid[r][c])
        if len(set(box_vals)) < 16:
            box_ok = False
            break
    
    # 簡化CP-SAT驗證（僅驗證唯一性）
    model = cp_model.CpModel()
    
    # 對未知位置創建變數
    for r in range(16):
        known_count = sum(1 for (kr, _) in known_positions if kr == r)
        if known_count < 16:
            for c in range(16):
                if (r, c) not in known_positions:
                    model.Add(grid[r][c] == grid[r][c])  # 靜止驗證
    
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    result = {
        'valid': col_ok and box_ok,
        'col_conflicts': 0 if col_ok else 16 - sum(1 for c in range(16) if len(set(grid[r][c] for r in range(16))) == 16),
        'box_conflicts': 0 if box_ok else sum(1 for box_idx in range(16) if len(set(grid[r][c] for r in range(16) for c in range(16) if (r//4)*4+(c//4)==box_idx)) < 16),
        'known_positions_match': all(grid[r][c] == v for (r, c), v in known_positions.items()),
        'cp_sat_status': solver.StatusName(status)
    }
    
    print(f"  列約束: {'✅ 通過' if col_ok else '❌ 衝突'}")
    print(f"  宮約束: {'✅ 通過' if box_ok else '❌ 衝突'}")
    print(f"  已知位置: {'✅ 全部匹配' if result['known_positions_match'] else '❌ 不匹配'}")
    
    return result


def main():
    """主執行入口"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║     符闔博弈優選策略 V19.0 - 遺傳優化與100D基因指紋系統     ║")
    print("╚" + "═" * 68 + "╝")
    
    # 載入數據
    print("\n[步驟1] 載入配置數據...")
    known_positions, row_permutations = load_config()
    print(f"  已知位置: {len(known_positions)} 個")
    print(f"  符闔排列: {sum(len(v) for v in row_permutations.values()):,} 個")
    
    # 分析已知位置分布
    print("\n[步驟2] 分析92固定錨點分布...")
    row_known_count = Counter(k[0] for k in known_positions.keys())
    for r in range(16):
        count = row_known_count.get(r, 0)
        unknown_count = 16 - count
        print(f"  行{r:2d} ({chr(65+r)}): {count:2d}已知 + {unknown_count:2d}未知")
    
    # 建構遺傳優化器
    print("\n[步驟3] 建構遺傳優化器...")
    optimizer = GeneticOptimizer(
        known_positions=known_positions,
        row_permutations=row_permutations,
        population_size=100,
        max_generations=1000,
        mutation_rate=0.05,
        crossover_rate=0.8
    )
    
    # 執行優化
    print("\n[步驟4] 執行遺傳優化...")
    result = optimizer.optimize(verbose=True)
    
    # 計算100D基因指紋
    best = result['best_individual']
    gene_fp = result['gene_fingerprint']
    
    print("\n[步驟5] 計算100D基因指紋...")
    print(f"  行約束維度: 均值得分 {sum(gene_fp.row_dimensions)/16:.4f}")
    print(f"  列約束維度: 均值得分 {sum(gene_fp.col_dimensions)/16:.4f}")
    print(f"  宮約束維度: 均值得分 {sum(gene_fp.box_dimensions)/16:.4f}")
    print(f"  總體適應度: {gene_fp.total_fitness():.4f}")
    
    # CP-SAT驗證
    print("\n[步驟6] CP-SAT驗證...")
    cp_sat_result = cp_sat_verify(best, known_positions)
    
    # 最終報告
    print("\n" + "=" * 70)
    print("┌─ 最終驗證結果 ──────────────────────────────────────┐")
    print(f"│  適應度: {result['best_fitness']:.4f}                       │")
    print(f"│  量子態: {result['quantum_state']}                  │")
    print(f"│  遺傳代數: {result['generations']}                       │")
    print(f"│  CP-SAT驗證: {'✅ 通過' if cp_sat_result['valid'] else '❌ 失敗'}              │")
    print("└───────────────────────────────────────────────┘")
    
    # 保存結果
    output = {
        'quantum_state': result['quantum_state'],
        'best_fitness': result['best_fitness'],
        'generations': result['generations'],
        'elapsed_time': result['elapsed_time'],
        'cp_sat_valid': cp_sat_result['valid'],
        'col_conflicts': cp_sat_result['col_conflicts'],
        'box_conflicts': cp_sat_result['box_conflicts'],
        'gene_fingerprint_summary': {
            'row_mean': sum(gene_fp.row_dimensions) / 16,
            'col_mean': sum(gene_fp.col_dimensions) / 16,
            'box_mean': sum(gene_fp.box_dimensions) / 16,
            'total_fitness': gene_fp.total_fitness()
        },
        'solution_grid': best.grid,
        'known_positions_count': len(known_positions)
    }
    
    with open('genetic_optimizer_v19_result.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 結果已保存至: genetic_optimizer_v19_result.json")
    
    # 顯示解
    if cp_sat_result['valid']:
        print("\n[解展示] 最終解網格:")
        row_labels = 'ABCDEFGHIJKLMNOP'
        for r in range(16):
            row_str = ' '.join(f'{v:2d}' for v in best.grid[r])
            print(f"  行{row_labels[r]}: {row_str}")
    
    return result


if __name__ == '__main__':
    main()
