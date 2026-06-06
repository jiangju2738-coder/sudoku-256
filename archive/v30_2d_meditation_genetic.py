#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 V30.0 - 二次元快速冥進遺傳優化 + 解空間迴縮倒推回溯
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

核心策略：
  • 二次元冥想 (2D Meditation)：行-列雙維度同步演化
  • 解空間迴縮倒推：從 23 個本質解反推解空間的分叉點
  • 十六連環環套追蹤：追蹤解之間的相鄰變換路徑
  • 精英循環進化 (Elite Cyclic Evolution)：循環交叉 + 精英保留
  • 新謎題生成：基於分叉點分析生成唯一解錨點配置

數學框架：
  • 解空間 V = {s₁, s₂, ..., s₂₃}
  • 變換運算子 T: V × V → V (鄰域變換)
  • 分叉點集合 B = {b₁, b₂, ...} (解之間首次分歧的位置)
  • 環套距離 D(sᵢ, sⱼ) = 漢明距離
  • 十六連環鏈：s₁ → s₂ → ... → s₁₆ → s₁
"""

import json
import time
import random
import hashlib
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from itertools import combinations
import copy

# ═══════════════════════════════════════════════════════════════
# 配置數據
# ═══════════════════════════════════════════════════════════════

GRID_SIZE = 16
BOX_SIZE = 4
SEQUENCE_CONSTRAINT = [7, 15, 3, 9]
ELITE_SIZE = 5          # 精英保留數量
POPULATION_SIZE = 50    # 群體大小
GENERATIONS = 200       # 進化代數
MUTATION_RATE = 0.15    # 變異率
CROSSOVER_RATE = 0.8    # 交叉率
THRESHOLD_DIST = 3      # 環套相鄰閾值（漢明距離）

# ═══════════════════════════════════════════════════════════════
# 錨點配置（V28 修復版）
# ═══════════════════════════════════════════════════════════════

def load_anchors_92() -> Dict[Tuple[int, int], int]:
    """加載 92 錨點（V28 修復版）"""
    anchors = {}
    
    # 行 A (1): 4 個
    anchors[(0, 2)] = 3;  anchors[(0, 5)] = 12
    anchors[(0, 7)] = 5;  anchors[(0, 11)] = 14
    
    # 行 B (2): 4 個
    anchors[(1, 1)] = 12; anchors[(1, 4)] = 3
    anchors[(1, 6)] = 9;  anchors[(1, 8)] = 6
    
    # 行 C (3): 16 個 - 完全固定 (符闔行)
    anchors[(2, 0)] = 7;  anchors[(2, 1)] = 15; anchors[(2, 2)] = 3;  anchors[(2, 3)] = 9
    anchors[(2, 4)] = 11; anchors[(2, 5)] = 12; anchors[(2, 6)] = 6;  anchors[(2, 7)] = 5
    anchors[(2, 8)] = 10; anchors[(2, 9)] = 2;  anchors[(2, 10)] = 1; anchors[(2, 11)] = 14
    anchors[(2, 12)] = 13; anchors[(2, 13)] = 16; anchors[(2, 14)] = 4; anchors[(2, 15)] = 8
    
    # 行 D (4): 16 個 - 完全固定 (符闔行)
    anchors[(3, 0)] = 11; anchors[(3, 1)] = 4;  anchors[(3, 2)] = 13; anchors[(3, 3)] = 7
    anchors[(3, 4)] = 16; anchors[(3, 5)] = 8;  anchors[(3, 6)] = 1;  anchors[(3, 7)] = 9
    anchors[(3, 8)] = 3;  anchors[(3, 9)] = 15; anchors[(3, 10)] = 2; anchors[(3, 11)] = 6
    anchors[(3, 12)] = 5; anchors[(3, 13)] = 14; anchors[(3, 14)] = 10; anchors[(3, 15)] = 12
    
    # 行 E (5): 3 個
    anchors[(4, 4)] = 13; anchors[(4, 9)] = 5;  anchors[(4, 12)] = 4
    
    # 行 F (6): 7 個
    anchors[(5, 1)] = 8;  anchors[(5, 4)] = 15; anchors[(5, 6)] = 4
    anchors[(5, 7)] = 3;  anchors[(5, 10)] = 10; anchors[(5, 13)] = 16
    anchors[(5, 14)] = 12
    
    # 行 G (7): 6 個
    anchors[(6, 0)] = 14; anchors[(6, 2)] = 4;  anchors[(6, 3)] = 6
    anchors[(6, 9)] = 9;  anchors[(6, 12)] = 15; anchors[(6, 15)] = 2
    
    # 行 H (8): 6 個
    anchors[(7, 1)] = 13; anchors[(7, 5)] = 5;  anchors[(7, 7)] = 9
    anchors[(7, 11)] = 11; anchors[(7, 13)] = 7; anchors[(7, 14)] = 1
    
    # 行 I (9): 16 個 - 完全固定 (符闔行)
    anchors[(8, 0)] = 13; anchors[(8, 1)] = 1;  anchors[(8, 2)] = 10; anchors[(8, 3)] = 2
    anchors[(8, 4)] = 8;  anchors[(8, 5)] = 11; anchors[(8, 6)] = 16; anchors[(8, 7)] = 7
    anchors[(8, 8)] = 14; anchors[(8, 9)] = 4;  anchors[(8, 10)] = 5; anchors[(8, 11)] = 12
    anchors[(8, 12)] = 9; anchors[(8, 13)] = 6; anchors[(8, 14)] = 3; anchors[(8, 15)] = 15
    
    # 行 J (10): 4 個
    anchors[(9, 1)] = 5;  anchors[(9, 5)] = 14; anchors[(9, 9)] = 8;  anchors[(9, 11)] = 1
    
    # 行 K (11): 6 個
    anchors[(10, 0)] = 1; anchors[(10, 2)] = 6; anchors[(10, 4)] = 10
    anchors[(10, 7)] = 13; anchors[(10, 10)] = 9; anchors[(10, 13)] = 11
    
    # 行 L (12): 6 個
    anchors[(11, 3)] = 4; anchors[(11, 5)] = 16; anchors[(11, 6)] = 14
    anchors[(11, 8)] = 3; anchors[(11, 10)] = 12; anchors[(11, 12)] = 7
    
    # 行 M (13): 7 個
    anchors[(12, 0)] = 15; anchors[(12, 4)] = 12; anchors[(12, 8)] = 5
    anchors[(12, 9)] = 14; anchors[(12, 11)] = 8; anchors[(12, 14)] = 11
    anchors[(12, 15)] = 6
    
    # 行 N (14): 5 個
    anchors[(13, 2)] = 9; anchors[(13, 5)] = 6;  anchors[(13, 8)] = 13
    anchors[(13, 11)] = 15; anchors[(13, 15)] = 10
    
    # 行 O (15): 6 個
    anchors[(14, 1)] = 1; anchors[(14, 4)] = 9;  anchors[(14, 7)] = 15
    anchors[(14, 10)] = 7; anchors[(14, 12)] = 16; anchors[(14, 13)] = 3
    
    # 行 P (16): 2 個
    anchors[(15, 2)] = 2; anchors[(15, 6)] = 5
    
    return anchors


# ═══════════════════════════════════════════════════════════════
# 1. 23 個本質解的模擬數據
# ═══════════════════════════════════════════════════════════════

def generate_23_solutions() -> List[List[List[int]]]:
    """
    生成 23 個本質解（基於 V29 的模擬數據）
    符闔行 C, D, I 固定，非符闔行變化
    """
    anchors = load_anchors_92()
    fixed_rows = {2, 3, 8}
    fixed_row_values = {
        2: [7,15,3,9,11,12,6,5,10,2,1,14,13,16,4,8],
        3: [11,4,13,7,16,8,1,9,3,15,2,6,5,14,10,12],
        8: [13,1,10,2,8,11,16,7,14,4,5,12,9,6,3,15],
    }
    
    np.random.seed(42)
    solutions = []
    
    for i in range(23):
        grid = [[0]*16 for _ in range(16)]
        
        # 填入符闔行
        for r in fixed_rows:
            for c, v in enumerate(fixed_row_values[r]):
                grid[r][c] = v
        
        # 填入其他錨點
        for (r, c), v in anchors.items():
            if r not in fixed_rows:
                grid[r][c] = v
        
        # 隨機填充非符闔行的空位，但確保每行是排列
        for r in range(16):
            if r not in fixed_rows:
                used = set(v for v in grid[r] if v != 0)
                available = [v for v in range(1, 17) if v not in used]
                np.random.shuffle(available)
                for c in range(16):
                    if grid[r][c] == 0 and available:
                        grid[r][c] = available.pop()
        
        # 注入變化（確保每個解不同）
        np.random.seed(42 + i * 7)
        for _ in range(np.random.randint(3, 8)):
            r = np.random.choice([r for r in range(16) if r not in fixed_rows])
            c1, c2 = np.random.choice([c for c in range(16) if (r, c) not in anchors], 2, replace=False)
            grid[r][c1], grid[r][c2] = grid[r][c2], grid[r][c1]
        
        solutions.append(grid)
    
    return solutions


# ═══════════════════════════════════════════════════════════════
# 2. 二次元冥想分析器 (2D Meditation Analyzer)
# ═══════════════════════════════════════════════════════════════

@dataclass
class CellVariance:
    """單元格變異分析"""
    row: int
    col: int
    is_anchor: bool
    is_fixed_row: bool
    value_distribution: Dict[int, int]
    entropy: float
    variability: float  # 0=完全固定，1=最大變異


class SolutionSpaceAnalyzer:
    """
    解空間迴縮倒推分析器
    
    核心分析：
    1. 單元格變異度分析 - 哪些位置在 23 個解中取值不同
    2. 分叉點識別 - 解之間首次分歧的位置
    3. 行-列關聯性分析 - 二次元冥想
    4. 十六連環環套追蹤 - 解之間的相鄰關係
    """
    
    def __init__(self, solutions: List[List[List[int]]], anchors: Dict):
        self.solutions = solutions
        self.anchors = anchors
        self.fixed_rows = {2, 3, 8}
        
        # 分析結果
        self.cell_variances: List[CellVariance] = []
        self.divergence_points: List[Tuple[int, int]] = []
        self.row_col_correlation: np.ndarray = None
        self.solution_graph: Dict[int, List[int]] = {}  # 相鄰解圖
        
    def analyze_cell_variations(self) -> List[CellVariance]:
        """分析每個單元格在 23 個解中的變異"""
        self.cell_variances = []
        
        for r in range(16):
            for c in range(16):
                values = [sol[r][c] for sol in self.solutions]
                value_dist = Counter(values)
                
                # 計算熵和變異度
                n = len(values)
                entropy = -sum((cnt/n) * np.log2(cnt/n) for cnt in value_dist.values() if cnt > 0)
                max_entropy = np.log2(16)  # 最大值在 16 個值均勻分布時
                variability = entropy / max_entropy if max_entropy > 0 else 0
                
                is_anchor = (r, c) in self.anchors
                is_fixed_row = r in self.fixed_rows
                
                cv = CellVariance(
                    row=r, col=c,
                    is_anchor=is_anchor,
                    is_fixed_row=is_fixed_row,
                    value_distribution=dict(value_dist),
                    entropy=entropy,
                    variability=variability
                )
                self.cell_variances.append(cv)
        
        return self.cell_variances
    
    def identify_divergence_points(self) -> List[Tuple[int, int]]:
        """
        識別分叉點：
        對每對解，找到它們首次分歧的位置（按行優先順序）
        """
        divergence_set = set()
        
        for i, j in combinations(range(len(self.solutions)), 2):
            for r in range(16):
                for c in range(16):
                    if self.solutions[i][r][c] != self.solutions[j][r][c]:
                        divergence_set.add((r, c))
                        break
                else:
                    continue
                break
        
        self.divergence_points = sorted(divergence_set)
        return self.divergence_points
    
    def compute_row_col_correlation(self) -> np.ndarray:
        """
        二次元冥想：計算行-列約束關聯性
        
        對於每個解，計算：
        - 行排列特徵
        - 列排列特徵
        - 行與列的相互約束強度
        """
        # 初始化解變異矩陣
        self.row_col_correlation = np.zeros((16, 16))
        
        for r in range(16):
            for c in range(16):
                # 統計在 23 個解中，該行該列的取值模式
                row_values = [tuple(sol[r]) for sol in self.solutions]
                col_values = [tuple(sol[i][c] for i in range(16)) for sol in self.solutions]
                
                # 計算該單元格的取值多樣性
                values_at_cell = [sol[r][c] for sol in self.solutions]
                unique_count = len(set(values_at_cell))
                self.row_col_correlation[r, c] = unique_count / 16
        
        return self.row_col_correlation
    
    def build_solution_adjacency_graph(self) -> Dict[int, List[int]]:
        """
        建構解之間的相鄰圖（十六連環環套）
        
        兩個解相鄰如果漢明距離 <= THRESHOLD_DIST
        """
        n = len(self.solutions)
        self.solution_graph = {i: [] for i in range(n)}
        
        for i in range(n):
            for j in range(i+1, n):
                # 計算漢明距離（非符闔行的差異）
                dist = 0
                for r in range(16):
                    if r not in self.fixed_rows:
                        for c in range(16):
                            if (r, c) not in self.anchors and self.solutions[i][r][c] != self.solutions[j][r][c]:
                                dist += 1
                
                if dist <= THRESHOLD_DIST * 4:  # 閾值乘以每行空位數
                    self.solution_graph[i].append(j)
                    self.solution_graph[j].append(i)
        
        return self.solution_graph
    
    def find_hexadec_ring(self) -> Optional[List[int]]:
        """
        尋找十六連環：16 個解形成的環
        使用深度優先搜索
        """
        if len(self.solutions) < 16:
            return None
        
        graph = self.solution_graph
        
        # 嘗試從每個解開始 DFS
        for start in range(len(self.solutions)):
            visited = [start]
            stack = [(start, [start])]
            
            while stack:
                node, path = stack.pop()
                
                if len(path) == 16:
                    # 檢查是否能閉環
                    last = path[-1]
                    first = path[0]
                    if first in graph[last]:
                        return path
                
                for neighbor in graph[node]:
                    if neighbor not in path:
                        stack.append((neighbor, path + [neighbor]))
        
        return None
    
    def print_analysis_summary(self):
        """打印分析總結"""
        print("\n" + "=" * 70)
        print(" 📊 解空間迴縮倒推分析總結")
        print("=" * 70)
        
        # 單元格變異統計
        high_var = [cv for cv in self.cell_variances if cv.variability > 0.5]
        medium_var = [cv for cv in self.cell_variances if 0.1 <= cv.variability <= 0.5]
        low_var = [cv for cv in self.cell_variances if cv.variability < 0.1]
        
        print(f"\n🔬 單元格變異分布：")
        print(f"   高變異 (>50%)：{len(high_var)} 個位置")
        print(f"   中變異 (10-50%)：{len(medium_var)} 個位置")
        print(f"   低變異 (<10%)：{len(low_var)} 個位置")
        
        # 分叉點
        print(f"\n🔀 分叉點（解首次分歧位置）：{len(self.divergence_points)} 個")
        for r, c in self.divergence_points[:10]:
            vals = [self.solutions[i][r][c] for i in range(5)]
            print(f"   位置 ({r},{c}): 前 5 個解的值 = {vals}")
        
        # 相鄰圖
        print(f"\n🔗 解相鄰圖：")
        for i, neighbors in self.solution_graph.items():
            if neighbors:
                print(f"   解 {i:2d} 相鄰於：{neighbors[:5]}{'...' if len(neighbors) > 5 else ''}")
        
        # 十六連環
        ring = self.find_hexadec_ring()
        if ring:
            print(f"\n🔗 發現十六連環！")
            print(f"   環路：{' → '.join(str(x) for x in ring)} → {ring[0]}")
        else:
            print(f"\n⚠️  未發現完整的十六連環（可嘗試增大閾值）")


# ═══════════════════════════════════════════════════════════════
# 3. 二次元快速冥進遺傳優化
# ═══════════════════════════════════════════════════════════════

class TwoD_Meditation_GA:
    """
    二次元快速冥進遺傳優化
    
    核心思想：
    1. 二次元冥想：同時優化行和列的約束滿足度
    2. 快速冥進：基於分叉點信息的加速進化
    3. 精英循環進化：保留精英個體，循環交叉變異
    """
    
    def __init__(self, anchors: Dict, fixed_rows: Set[int], fixed_row_values: Dict):
        self.anchors = anchors
        self.fixed_rows = fixed_rows
        self.fixed_row_values = fixed_row_values
        
        # 從分析器獲取的分叉點
        self.divergence_points = []
        self.high_variance_cells = []
        
    def set_divergence_info(self, divergence_points: List[Tuple[int, int]], 
                           high_variance: List[CellVariance]):
        """設置分叉點和 high variance 單元格信息"""
        self.divergence_points = divergence_points
        self.high_variance_cells = high_variance
        
    def create_individual(self) -> List[List[int]]:
        """創建一個隨機個體（滿足錨點和符闔行約束）"""
        grid = [[0]*16 for _ in range(16)]
        
        # 填入符闔行
        for r in self.fixed_rows:
            for c, v in enumerate(self.fixed_row_values[r]):
                grid[r][c] = v
        
        # 填入其他錨點
        for (r, c), v in self.anchors.items():
            if r not in self.fixed_rows:
                grid[r][c] = v
        
        # 填充非符闔行
        for r in range(16):
            if r not in self.fixed_rows:
                used = set(v for v in grid[r] if v != 0)
                available = [v for v in range(1, 17) if v not in used]
                np.random.shuffle(available)
                for c in range(16):
                    if grid[r][c] == 0 and available:
                        grid[r][c] = available.pop()
        
        return grid
    
    def fitness(self, grid: List[List[int]]) -> float:
        """
        適應度函數 - 二次元冥想評估
        
        考慮：
        1. 錨點約束符合度
        2. 行 AllDifferent
        3. 列 AllDifferent
        4. 宮 AllDifferent
        5. 序列約束
        """
        score = 0.0
        max_score = 5.0
        
        # 錨點約束
        anchor_match = sum(1 for (r, c), v in self.anchors.items() if grid[r][c] == v)
        score += anchor_match / len(self.anchors)
        
        # 行約束
        row_ok = sum(1 for r in range(16) if len(set(grid[r])) == 16)
        score += row_ok / 16
        
        # 列約束
        col_ok = 0
        for c in range(16):
            col_vals = [grid[r][c] for r in range(16)]
            if len(set(col_vals)) == 16:
                col_ok += 1
        score += col_ok / 16
        
        # 宫約束
        box_ok = 0
        for br in range(4):
            for bc in range(4):
                box_vals = []
                for r in range(br*4, (br+1)*4):
                    for c in range(bc*4, (bc+1)*4):
                        box_vals.append(grid[r][c])
                if len(set(box_vals)) == 16:
                    box_ok += 1
        score += box_ok / 16
        
        # 序列約束
        seq_count = 0
        for r in range(16):
            for c in range(13):
                if grid[r][c:c+4] == SEQUENCE_CONSTRAINT:
                    seq_count += 1
        score += min(seq_count / 5, 1.0)  # 期望至少 5 次出現
        
        return score
    
    def crossover(self, parent1: List[List[int]], parent2: List[List[int]]) -> List[List[int]]:
        """二次元交叉：行-列雙維度交叉"""
        child = [[0]*16 for _ in range(16)]
        
        # 複製符闔行和錨點
        for r in self.fixed_rows:
            for c, v in enumerate(self.fixed_row_values[r]):
                child[r][c] = v
        for (r, c), v in self.anchors.items():
            if r not in self.fixed_rows:
                child[r][c] = v
        
        # 對非符闔行進行交叉
        np.random.seed(hash(str(parent1)) % (2**32))
        for r in range(16):
            if r not in self.fixed_rows:
                for c in range(16):
                    if (r, c) not in self.anchors:
                        if np.random.random() < 0.5:
                            child[r][c] = parent1[r][c]
                        else:
                            child[r][c] = parent2[r][c]
        
        # 修復行約束（確保每行是排列）
        for r in range(16):
            if r not in self.fixed_rows:
                used = set(v for v in child[r] if v != 0)
                missing = [v for v in range(1, 17) if v not in used]
                empty_cols = [c for c in range(16) if child[r][c] == 0]
                for i, c in enumerate(empty_cols):
                    if i < len(missing):
                        child[r][c] = missing[i]
        
        return child
    
    def mutate(self, grid: List[List[int]], rate: float) -> List[List[int]]:
        """二次元變異：在分叉點位置進行變異"""
        mutated = [row[:] for row in grid]
        np.random.seed(hash(str(mutated)) % (2**32))
        
        # 優先在分叉點位置變異
        mutate_cells = self.divergence_points[:min(len(self.divergence_points), 20)]
        
        for r, c in mutate_cells:
            if (r, c) not in self.anchors and np.random.random() < rate:
                # 行內交換
                other_c = np.random.randint(0, 16)
                if (r, other_c) not in self.anchors:
                    mutated[r][c], mutated[r][other_c] = mutated[r][other_c], mutated[r][c]
        
        return mutated
    
    def elitism(self, population: List[List[List[int]]], 
                scores: List[float]) -> List[List[List[int]]]:
        """精英保留"""
        indexed = list(zip(population, scores))
        indexed.sort(key=lambda x: x[1], reverse=True)
        elites = [ind[0] for ind in indexed[:ELITE_SIZE]]
        return elites
    
    def evolve(self, solutions_23: List[List[List[int]]], generations: int = GENERATIONS) -> List[List[List[int]]]:
        """
        精英循環進化主流程
        
        初始化群體包含 23 個已知解，進化過程中保持精英
        """
        print(f"\n🚀 開始二次元快速冥進遺傳優化...")
        print(f"   群體大小：{POPULATION_SIZE}")
        print(f"   進化代數：{generations}")
        print(f"   精英數量：{ELITE_SIZE}")
        
        # 初始化群體：23 個解 + 隨機個體
        population = solutions_23[:min(23, POPULATION_SIZE)]
        while len(population) < POPULATION_SIZE:
            population.append(self.create_individual())
        
        best_solution = None
        best_score = 0.0
        history = []
        
        for gen in range(generations):
            # 評估適應度
            scores = [self.fitness(ind) for ind in population]
            
            # 記錄最佳
            gen_best = max(scores)
            if gen_best > best_score:
                best_score = gen_best
                best_idx = scores.index(gen_best)
                best_solution = population[best_idx]
            
            history.append(gen_best)
            
            if gen % 20 == 0:
                print(f"   Generation {gen:3d}: best fitness = {gen_best:.4f}")
            
            # 精英保留
            elites = self.elitism(population, scores)
            
            # 選擇、交叉、變異
            new_population = elites[:]
            
            while len(new_population) < POPULATION_SIZE:
                # 輪盤賭選擇
                total_score = sum(scores)
                if total_score == 0:
                    probs = [1/len(scores)] * len(scores)
                else:
                    probs = [s/total_score for s in scores]
                
                parent1_idx = np.random.choice(len(population), p=probs)
                parent2_idx = np.random.choice(len(population), p=probs)
                
                child = self.crossover(population[parent1_idx], population[parent2_idx])
                child = self.mutate(child, MUTATION_RATE)
                new_population.append(child)
            
            population = new_population[:POPULATION_SIZE]
        
        print(f"\n✅ 優化完成！")
        print(f"   最佳適應度：{best_score:.4f}")
        
        return population


# ═══════════════════════════════════════════════════════════════
# 4. 新唯一解謎題生成器
# ═══════════════════════════════════════════════════════════════

class NewPuzzleGenerator:
    """
    基於分叉點分析生成新的唯一解超級數獨謎題
    
    策略：
    1. 從 23 個解中選擇「最固定」的單元格作為新錨點
    2. 在分叉點附近增加錨點以消除多解性
    3. 驗證新謎題的唯一解性
    """
    
    def __init__(self, solutions: List[List[List[int]]], 
                 cell_variances: List[CellVariance],
                 divergence_points: List[Tuple[int, int]]):
        self.solutions = solutions
        self.cell_variances = cell_variances
        self.divergence_points = divergence_points
        
    def identify_most_fixed_cells(self, n_cells: int = 20) -> List[Tuple[int, int, int]]:
        """
        識別在 23 個解中最固定的單元格
        返回：(row, col, value) 三元組
        """
        # 找在所有 23 個解中取值相同的單元格
        fixed_cells = []
        for cv in self.cell_variances:
            if cv.variability == 0 and not cv.is_anchor:
                value = next(iter(cv.value_distribution.keys()))
                fixed_cells.append((cv.row, cv.col, value))
        
        return fixed_cells[:n_cells]
    
    def generate_anchor_set(self, base_anchors: Dict, 
                           additional_cells: List[Tuple[int, int, int]],
                           min_anchors: int = 92) -> Dict:
        """
        生成新的錨點集合
        
        包含：
        1. 原有的符闔行錨點
        2. 從 23 個解中提取的固定單元格
        3. 分叉點附近的新錨點
        """
        new_anchors = {}
        
        # 複製原有錨點
        for k, v in base_anchors.items():
            new_anchors[k] = v
        
        # 添加從解中提取的固定單元格
        for r, c, v in additional_cells:
            if (r, c) not in new_anchors:
                new_anchors[(r, c)] = v
        
        return new_anchors
    
    def validate_puzzle(self, anchors: Dict, solutions: List[List[List[int]]], 
                       expected_unique: bool = True) -> Dict:
        """
        驗證新謎題的唯一解性
        
        方法：
        1. 用現有 23 個解檢查哪些滿足新�锚點
        2. 統計滿足的解數量
        """
        matching_solutions = []
        
        for i, sol in enumerate(solutions):
            matches = True
            for (r, c), v in anchors.items():
                if sol[r][c] != v:
                    matches = False
                    break
            if matches:
                matching_solutions.append(i)
        
        return {
            'total_solutions_checked': len(solutions),
            'matching_solutions': len(matching_solutions),
            'matching_indices': matching_solutions,
            'is_unique': len(matching_solutions) == 1,
            'anchor_count': len(anchors)
        }


# ═══════════════════════════════════════════════════════════════
# 5. 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print(" V30.0 - 二次元快速冥進遺傳優化 + 解空間迴縮倒推")
    print("=" * 70)
    
    # 載入配置
    anchors = load_anchors_92()
    fixed_rows = {2, 3, 8}
    fixed_row_values = {
        2: [7,15,3,9,11,12,6,5,10,2,1,14,13,16,4,8],
        3: [11,4,13,7,16,8,1,9,3,15,2,6,5,14,10,12],
        8: [13,1,10,2,8,11,16,7,14,4,5,12,9,6,3,15],
    }
    
    # 生成 23 個本質解
    print("\n📋 生成 23 個本質解...")
    solutions_23 = generate_23_solutions()
    print(f"   已生成 {len(solutions_23)} 個本質解")
    
    # 解空間分析
    print("\n🔍 解空間迴縮倒推分析...")
    analyzer = SolutionSpaceAnalyzer(solutions_23, anchors)
    analyzer.analyze_cell_variations()
    analyzer.identify_divergence_points()
    analyzer.compute_row_col_correlation()
    analyzer.build_solution_adjacency_graph()
    analyzer.print_analysis_summary()
    
    # 二次元遺傳優化
    print("\n" + "=" * 70)
    print(" 二次元快速冥進遺傳優化")
    print("=" * 70)
    
    ga = TwoD_Meditation_GA(anchors, fixed_rows, fixed_row_values)
    
    # 獲取高變異單元格
    high_var = [cv for cv in analyzer.cell_variances if cv.variability > 0.5]
    ga.set_divergence_info(analyzer.divergence_points, high_var)
    
    # 進化
    evolved_population = ga.evolve(solutions_23, generations=100)
    
    # 生成新謎題
    print("\n" + "=" * 70)
    print(" 新唯一解謎題生成")
    print("=" * 70)
    
    generator = NewPuzzleGenerator(solutions_23, analyzer.cell_variances, analyzer.divergence_points)
    
    # 識別固定單元格
    fixed_cells = generator.identify_most_fixed_cells(n_cells=30)
    print(f"\n🔬 從 23 個解中提取的固定單元格：{len(fixed_cells)} 個")
    
    # 生成新錨點
    new_anchors = generator.generate_anchor_set(anchors, fixed_cells)
    print(f"\n📋 新錨點集合大小：{len(new_anchors)}")
    
    # 驗證新謎題
    validation = generator.validate_puzzle(new_anchors, solutions_23)
    print(f"\n✅ 新謎題驗證：")
    print(f"   錨點數量：{validation['anchor_count']}")
    print(f"   滿足新錨點的原解數量：{validation['matching_solutions']}")
    print(f"   匹配的原解索引：{validation['matching_indices'][:10]}")
    
    if validation['is_unique']:
        print(f"   🎉 新謎題可能是唯一解！")
    else:
        print(f"   ⚠️  新謎題仍有 {validation['matching_solutions']} 個解（需要更多錨點）")
    
    # 保存結果
    result = {
        'version': 'V30.0',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'analysis': {
            'num_divergence_points': len(analyzer.divergence_points),
            'divergence_points': [list(p) for p in analyzer.divergence_points],
            'high_variance_cells_count': len(high_var),
        },
        'optimization': {
            'final_best_fitness': max(ga.fitness(ind) for ind in evolved_population),
            'population_size': len(evolved_population),
        },
        'new_puzzle': {
            'anchor_count': validation['anchor_count'],
            'matching_solutions': validation['matching_solutions'],
            'is_unique': validation['is_unique'],
            'new_anchors': {f"({k[0]},{k[1]})": v for k, v in list(new_anchors.items())[:50]},
        }
    }
    
    with open('v30_2d_meditation_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 結果已保存至：v30_2d_meditation_result.json")
    
    # 輸出新謎題配置
    print("\n" + "=" * 70)
    print(" 新謎題 92 錨點配置（前 30 個）")
    print("=" * 70)
    for i, ((r, c), v) in enumerate(list(new_anchors.items())[:30]):
        print(f"   ({r:2d},{c:2d}): {v:2d}")
    
    print("\n" + "=" * 70)
    print(" ✅ V30.0 分析完成")
    print("=" * 70)


if __name__ == '__main__':
    main()
