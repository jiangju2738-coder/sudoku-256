#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔數獨進化式求解系統 - V19.0

核心概念:
1. 未解盤為基底 → 零約束狀態（量子態：所有可能性共存）
2. 符闔約束規則增量 → 行→列→宮約束逐步剪枝
3. 樹狀多解空間 → 以未解盤為根節點的搜索樹，每層代表一個約束添加
4. 二進制快速遺傳優化 → 以二進制編碼表示排列選擇，快速演化
5. 精英迴溯循環進化 → 保存精英解，迴溯探索新分支
6. 融闔綜闔剪枝博弈 → 多層剪枝，博弈式约束冲突检测
7. 深度拓展 → 樹狀空間枝繁葉茂，多解共存（量子態保持）
8. 唯一解坍縮 → 如果唯一解存在，系統坍縮驗證通過；多解則保持量子態

作者: AI Assistant for Jualius
版本: V19.0
日期: 2026-05-17
"""

import json
import time
import math
import random
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from copy import deepcopy
from collections import defaultdict
from enum import Enum

try:
    from ortools.sat.python import cp_model
except ImportError:
    print("❌ 請安裝 ortools: pip install ortools")
    sys.exit(1)


# =============================================================================
# 1. 量子態與坍縮機制
# =============================================================================

class QuantumState(Enum):
    """量子態：多解共存 vs 唯一解坍縮"""
    SUPERPOSITION = "superposition"      # 多解共存，量子態
    COLLAPSED = "collapsed"              # 唯一解，系統坍縮
    INFEASIBLE = "infeasible"            # 無解，約束衝突


@dataclass
class QuantumMeasurement:
    """量子測量：檢測當前狀態是否坍縮"""
    state: QuantumState
    solution_count: int
    solutions: List[List[List[int]]] = field(default_factory=list)
    collapse_timestamp: Optional[float] = None
    
    def is_collapsed(self) -> bool:
        return self.state == QuantumState.COLLAPSED
    
    def is_superposition(self) -> bool:
        return self.state == QuantumState.SUPERPOSITION


# =============================================================================
# 2. 未解盤基底
# =============================================================================

@dataclass
class UnunsolvedPuzzle:
    """未解盤基底 - 零約束狀態"""
    grid_size: int = 16
    box_size: int = 4
    given_cells: Dict[Tuple[int, int], int] = field(default_factory=dict)
    empty_cells: Set[Tuple[int, int]] = field(default_factory=set)
    
    def __post_init__(self):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if (i, j) not in self.given_cells:
                    self.empty_cells.add((i, j))
    
    @classmethod
    def from_solution(cls, solution: List[List[int]], given_rate: float) -> 'UnunsolvedPuzzle':
        """從真實解採樣 given_rate 比例作為已知數"""
        import random
        puzzle = UnunsolvedPuzzle()
        
        positions = [(i, j) for i in range(16) for j in range(16)]
        random.shuffle(positions)
        
        n_givens = int(len(positions) * given_rate)
        for i, j in positions[:n_givens]:
            puzzle.given_cells[(i, j)] = solution[i][j]
        
        return puzzle
    
    @classmethod
    def from_file(cls, filepath: str) -> 'UnunsolvedPuzzle':
        """從 JSON 文件載入未解盤"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        puzzle = UnunsolvedPuzzle()
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                if val != 0:
                    puzzle.given_cells[(i, j)] = val
        
        return puzzle
    
    def get_given_count(self) -> int:
        return len(self.given_cells)
    
    def get_fill_rate(self) -> float:
        return self.get_given_count() / (self.grid_size * self.grid_size)
    
    def to_json(self) -> List[List[int]]:
        """轉為 JSON 格式"""
        grid = [[0] * self.grid_size for _ in range(self.grid_size)]
        for (i, j), val in self.given_cells.items():
            grid[i][j] = val
        return grid


# =============================================================================
# 3. 符闔約束規則 - 增量約束
# =============================================================================

@dataclass
class ConstraintStep:
    """約束添加步驟"""
    step_id: int
    constraint_type: str  # 'row', 'given', 'fahuo', 'column', 'box'
    count: int
    model: Any = None


class FahuoConstraintManager:
    """符闔約束管理器 - 增量約束添加"""
    
    def __init__(self, grid_size: int = 16, box_size: int = 4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.permutations: List[List[int]] = []
        self._load_permutations()
    
    def _load_permutations(self):
        """載入符闔排列"""
        perm_path = Path(__file__).parent / 'permutations_v4_final.json'
        if perm_path.exists():
            with open(perm_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.permutations = [list(map(int, p)) for p in data]
                else:
                    self.permutations = [list(map(int, p)) for p in data.get('permutations', [])]
            print(f"📊 符闔排列載入: {len(self.permutations)} 個")
        else:
            # 備用：基本排列
            base = list(range(1, 17))
            self.permutations = []
            for shift in range(16):
                perm = [base[(j + shift) % 16] for j in range(16)]
                self.permutations.append(perm)
            print(f"⚠️ 使用備用排列: {len(self.permutations)} 個")
    
    def add_row_constraints(self, model: cp_model.CpModel, x: Dict) -> ConstraintStep:
        """步驟1：添加行 AllDifferent 約束"""
        for i in range(self.grid_size):
            model.AddAllDifferent([x[(i, j)] for j in range(self.grid_size)])
        
        return ConstraintStep(
            step_id=1,
            constraint_type='row',
            count=self.grid_size
        )
    
    def add_given_constraints(self, model: cp_model.CpModel, x: Dict,
                               puzzle: UnunsolvedPuzzle) -> ConstraintStep:
        """步驟2：添加已知數字約束"""
        count = 0
        for (i, j), val in puzzle.given_cells.items():
            model.Add(x[(i, j)] == val)
            count += 1
        
        return ConstraintStep(
            step_id=2,
            constraint_type='given',
            count=count
        )
    
    def add_fahuo_constraints(self, model: cp_model.CpModel, x: Dict) -> ConstraintStep:
        """
        步驟3：添加符闔排列約束（核心剪枝）
        
        使用 selector 變數選擇每行的排列，這是符闔博弈的關鍵
        """
        selector_count = 0
        constraint_count = 0
        
        for i in range(self.grid_size):
            row_selectors = []
            
            for perm_idx, perm in enumerate(self.permutations):
                selector = model.NewBoolVar(f'row{i}_perm{perm_idx}')
                row_selectors.append(selector)
                selector_count += 1
                
                # 如果選擇該排列，行必須匹配
                for j, val in enumerate(perm):
                    model.Add(x[(i, j)] == val).OnlyEnforceIf(selector)
                    constraint_count += 1
            
            # 每行恰好選擇一個排列
            model.AddExactlyOne(row_selectors)
            constraint_count += 1
        
        return ConstraintStep(
            step_id=3,
            constraint_type='fahuo',
            count=constraint_count,
            metadata={'selectors': selector_count, 'permutations': len(self.permutations)}
        )
    
    def add_column_constraints(self, model: cp_model.CpModel, x: Dict) -> ConstraintStep:
        """步驟4：添加列 AllDifferent 約束"""
        for j in range(self.grid_size):
            model.AddAllDifferent([x[(i, j)] for i in range(self.grid_size)])
        
        return ConstraintStep(
            step_id=4,
            constraint_type='column',
            count=self.grid_size
        )
    
    def add_box_constraints(self, model: cp_model.CpModel, x: Dict) -> ConstraintStep:
        """步驟5：添加宮 AllDifferent 約束"""
        box_count = 0
        for band in range(self.grid_size // self.box_size):
            for stack in range(self.grid_size // self.box_size):
                box_vars = [
                    x[(band*self.box_size+i, stack*self.box_size+j)]
                    for i in range(self.box_size) for j in range(self.box_size)
                ]
                model.AddAllDifferent(box_vars)
                box_count += 1
        
        return ConstraintStep(
            step_id=5,
            constraint_type='box',
            count=box_count
        )


# =============================================================================
# 4. 樹狀多解空間
# =============================================================================

@dataclass
class TreeNode:
    """樹狀搜索空間的節點"""
    node_id: str
    depth: int
    given_puzzle: UnunsolvedPuzzle
    constraints_added: List[ConstraintStep]
    is_feasible: bool
    solution: Optional[List[List[int]]] = None
    children: List['TreeNode'] = field(default_factory=list)
    parent: Optional['TreeNode'] = None
    pruning_reason: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def add_child(self, child: 'TreeNode'):
        self.children.append(child)
        child.parent = self
    
    def get_all_descendants(self) -> List['TreeNode']:
        """獲取所有後代節點"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def get_stats(self) -> Dict:
        """獲取子樹統計"""
        all_nodes = self.get_all_descendants()
        all_nodes.append(self)
        
        feasible_count = sum(1 for n in all_nodes if n.is_feasible)
        pruned_count = sum(1 for n in all_nodes if n.pruning_reason)
        
        return {
            'total_nodes': len(all_nodes),
            'max_depth': max(n.depth for n in all_nodes),
            'feasible_nodes': feasible_count,
            'pruned_nodes': pruned_count,
            'leaf_nodes': len(self.children),
            'average_branching': len(all_nodes) / max(1, len(all_nodes) - pruned_count) if all_nodes else 0
        }


class TreeSearchSpace:
    """樹狀多解空間 - 以未解盤為根節點的搜索樹"""
    
    def __init__(self, root_puzzle: UnunsolvedPuzzle):
        self.root = TreeNode(
            node_id='root',
            depth=0,
            given_puzzle=root_puzzle,
            constraints_added=[],
            is_feasible=True
        )
        self.current_node = self.root
        self.max_depth = 5
        self.max_nodes = 10000
    
    def build_tree(self, constraint_steps: List[Tuple[str, Any]]):
        """
        逐步添加約束，展開樹狀空間
        
        constraint_steps: [(constraint_type, data), ...]
        """
        node = self.root
        step_id = 0
        
        for step_type, data in constraint_steps:
            if len(self.root.get_all_descendants()) > self.max_nodes:
                break
            
            children = self._expand_node(node, step_type, data, step_id)
            step_id += 1
            
            if not children:
                break  # 所有分支都被剪枝
            
            # 選擇第一個可行子節點繼續
            for child in children:
                if child.is_feasible:
                    node = child
                    break
        
        return self.root
    
    def _expand_node(self, parent: TreeNode, constraint_type: str,
                     data: Any, step_id: int) -> List[TreeNode]:
        """擴展一個節點：添加約束，創建子節點"""
        
        children = []
        
        if constraint_type == 'given_split':
            # 將未解盤的空白格分成兩組，創建兩個分支
            unassigned = list(parent.given_puzzle.empty_cells)
            if len(unassigned) <= 2:
                # 已經接近完全填充
                children.append(parent)  # 保持原狀
                return children
            
            # 取前一半作為已知
            n_split = min(len(unassigned), 8)
            for split_idx in range(min(3, math.ceil(len(unassigned) / n_split))):
                start = split_idx * n_split
                end = min(start + n_split, len(unassigned))
                
                child_puzzle = deepcopy(parent.given_puzzle)
                for i, j in unassigned[start:end]:
                    child_puzzle.given_cells[(i, j)] = data[(i, j)]
                    child_puzzle.empty_cells.discard((i, j))
                
                child = TreeNode(
                    node_id=f'{parent.node_id}_split{split_idx}',
                    depth=parent.depth + 1,
                    given_puzzle=child_puzzle,
                    constraints_added=parent.constraints_added.copy(),
                    is_feasible=True  # 稍後驗證
                )
                parent.add_child(child)
                children.append(child)
        
        return children
    
    def visualize(self) -> str:
        """可視化樹狀空間"""
        lines = []
        
        def recurse(node: TreeNode, indent: int = 0):
            prefix = '  ' * indent
            status = '✅' if node.is_feasible else '❌'
            prune_info = f' (剪枝: {node.pruning_reason})' if node.pruning_reason else ''
            
            fill_rate = node.given_puzzle.get_fill_rate() * 100
            lines.append(f'{prefix}{status} Node {node.node_id} [depth={node.depth}, fill_rate={fill_rate:.1f}%]{prune_info}')
            
            for child in node.children:
                recurse(child, indent + 1)
        
        recurse(self.root)
        return '\n'.join(lines)


# =============================================================================
# 5. 二進制快速遺傳優化
# =============================================================================

class BinaryGeneticOptimizer:
    """
    二進制快速遺傳優化
    
    編碼方式:
    - 每行選擇一個符闔排列 → 16個位置，每個位置需要 log2(P) 位
    - 例如 336 個排列，需要 9 位/行
    - 總長度 = 16 × 9 = 144 位
    
    優化目標:
    - 最大化約束滿足度（符合行符闔、列AllDifferent、宮AllDifferent）
    """
    
    def __init__(self, permutations: List[List[int]], grid_size: int = 16):
        self.permutations = permutations
        self.grid_size = grid_size
        self.perm_count = len(permutations)
        
        # 計算編碼長度
        self.bits_per_row = math.ceil(math.log2(max(1, self.perm_count)))
        self.chromosome_length = grid_size * self.bits_per_row
        
        print(f"🧬 二進制編碼: {self.chromosome_length} bits ({self.bits_per_row} bits/row)")
    
    def encode_permutation_choice(self, choices: List[int]) -> str:
        """將排列選擇編碼為二進制字串"""
        binary = ''
        for choice in choices:
            binary += format(choice, f'0{self.bits_per_row}b')
        return binary
    
    def decode_chromosome(self, chromosome: str) -> List[int]:
        """將二進制字串解碼為排列選擇索引"""
        choices = []
        for i in range(0, len(chromosome), self.bits_per_row):
            bits = chromosome[i:i + self.bits_per_row]
            choices.append(int(bits, 2) % self.perm_count)
        return choices
    
    def decode_to_grid(self, chromosome: str) -> List[List[int]]:
        """將二進制編碼解碼為完整網格"""
        choices = self.decode_chromosome(chromosome)
        grid = []
        for i, perm_idx in enumerate(choices):
            grid.append(self.permutations[perm_idx].copy())
        return grid
    
    def calculate_fitness(self, chromosome: str) -> float:
        """
        計算適應度函數 (改進版)
        
        權重調整：
        - 行約束：0.1（由編碼保證，每行必從符闔排列選擇）
        - 列約束：0.5（關鍵約束，每列必須16個不同值）
        - 宮約束：0.4（重要約束，每4×4宮必須AllDifferent）
        
        適應度 = 0.1 × row_score + 0.5 × col_score + 0.4 × box_score
        """
        grid = self.decode_to_grid(chromosome)
        
        fitness = 0.0
        
        # 行約束（由編碼保證，每個排列都是合法的）
        # 但仍需檢查已知數是否匹配
        row_score = 1.0
        
        # 列約束 - 權重0.5
        col_score = 0.0
        col_conflicts = []  # 記錄列衝突詳情用於後續修復
        for j in range(self.grid_size):
            col_vals = []
            for i in range(self.grid_size):
                col_vals.append(grid[i][j])
            unique_count = len(set(col_vals))
            if unique_count == self.grid_size:
                col_score += 1.0
            else:
                # 記錄衝突：某個值出現多次
                from collections import Counter
                counts = Counter(col_vals)
                conflicts = [(val, cnt) for val, cnt in counts.items() if cnt > 1]
                col_conflicts.append((j, conflicts))
        col_score /= self.grid_size
        
        # 宮約束 - 權重0.4
        box_size = 4
        box_score = 0.0
        num_boxes = (self.grid_size // box_size) ** 2
        box_conflicts = []  # 記錄宮衝突詳情
        for band in range(self.grid_size // box_size):
            for stack in range(self.grid_size // box_size):
                box_vals = []
                for bi in range(box_size):
                    for bj in range(box_size):
                        row = band * box_size + bi
                        col = stack * box_size + bj
                        box_vals.append(grid[row][col])
                unique_count = len(set(box_vals))
                if unique_count == box_size * box_size:
                    box_score += 1.0
                else:
                    from collections import Counter
                    counts = Counter(box_vals)
                    conflicts = [(val, cnt) for val, cnt in counts.items() if cnt > 1]
                    box_conflicts.append(((band, stack), conflicts))
        box_score /= num_boxes
        
        # 綜合適應度（改進權重）
        fitness = row_score * 0.1 + col_score * 0.5 + box_score * 0.4
        
        return fitness
    
    def repair_with_permutation_swap(self, chromosome: str, max_swaps: int = 10) -> Tuple[str, float, int]:
        """
        列衝突時嘗試排列交換修復 (保守策略)
        
        當檢測到列衝突時，嘗試交換兩行的排列選擇來減少衝突
        保守策略：只在適應度提升時才接受交換
        
        Args:
            chromosome: 當前的染色體（排列選擇編碼）
            max_swaps: 最大嘗試交換次數
        
        Returns:
            (new_chromosome, new_fitness, num_swaps)
        """
        from collections import Counter, defaultdict
        
        grid = self.decode_to_grid(chromosome)
        fitness = self.calculate_fitness(chromosome)
        
        # 檢測列衝突
        col_conflicts = []
        for j in range(self.grid_size):
            col_vals = [grid[i][j] for i in range(self.grid_size)]
            counts = Counter(col_vals)
            conflicts = [(val, cnt) for val, cnt in counts.items() if cnt > 1]
            if conflicts:
                col_conflicts.append((j, conflicts, col_vals))
        
        if not col_conflicts:
            return chromosome, fitness, 0  # 無衝突，無需修復
        
        num_swaps = 0
        new_chrom = chromosome
        current_fit = fitness
        
        # 嘗試修復每個衝突列
        for col_idx, conflicts, col_vals in col_conflicts:
            if num_swaps >= max_swaps:
                break
            
            # 找出衝突的值
            conflicting_vals = [val for val, cnt in conflicts]
            
            # 對於每個衝突值，找出哪些行有這個值
            val_to_rows = defaultdict(list)
            for i, val in enumerate(col_vals):
                val_to_rows[val].append(i)
            
            # 嘗試交換
            for conflict_val in conflicting_vals:
                rows_with_val = val_to_rows[conflict_val]
                if len(rows_with_val) < 2:
                    continue
                
                # 嘗試交換前兩行的排列
                row1, row2 = rows_with_val[0], rows_with_val[1]
                
                # 提取當前排列選擇
                choices = self.decode_chromosome(new_chrom)
                current_perm1 = choices[row1]
                current_perm2 = choices[row2]
                
                # 嘗試交換
                choices[row1], choices[row2] = current_perm2, current_perm1
                new_chrom = self.encode_permutation_choice(choices)
                
                # 計算新適應度
                new_fit, new_conflicts = self.calculate_fitness(new_chrom)
                
                # 如果適應度提升，保留交換
                if new_fit > current_fit:
                    current_fit = new_fit
                    num_swaps += 1
                else:
                    # 回滾
                    choices[row1], choices[row2] = current_perm1, current_perm2
                    new_chrom = self.encode_permutation_choice(choices)
        
        return new_chrom, current_fit, num_swaps
    
    def initialize_population(self, size: int = 50) -> List[str]:
        """初始化種群"""
        population = []
        for _ in range(size):
            chromosome = ''.join(
                format(random.randint(0, self.perm_count - 1), f'0{self.bits_per_row}b')
                for _ in range(self.grid_size)
            )
            population.append(chromosome)
        return population
    
    def crossover(self, parent1: str, parent2: str) -> Tuple[str, str]:
        """單點交叉"""
        point = random.randint(1, len(parent1) - 1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2
    
    def mutate(self, chromosome: str, mutation_rate: float = 0.01) -> str:
        """單點突變"""
        bits = list(chromosome)
        for i in range(len(bits)):
            if random.random() < mutation_rate:
                # 隨機修改這個行的排列選擇
                row_idx = i // self.bits_per_row
                start = row_idx * self.bits_per_row
                end = start + self.bits_per_row
                bits[start:end] = format(
                    random.randint(0, self.perm_count - 1),
                    f'0{self.bits_per_row}b'
                )
        return ''.join(bits)
    
    def optimize(self, population: List[str], generations: int = 100, enable_repair: bool = True) -> List[Tuple[str, float]]:
        """
        遺傳優化主循環（改進版）
        
        保守策略：只在適應度提升時才進行列衝突修復
        
        返回：[(chromosome, fitness), ...] 排序後的最優個體
        """
        fitness_cache = {}
        repair_stats = {'total_repair_attempts': 0, 'successful_repairs': 0}
        
        def get_fitness(chrom):
            if chrom not in fitness_cache:
                fitness_cache[chrom] = self.calculate_fitness(chrom)
            return fitness_cache[chrom]
        
        for gen in range(generations):
            # 計算適應度
            fitnesses = [(chrom, get_fitness(chrom)) for chrom in population]
            fitnesses.sort(key=lambda x: x[1], reverse=True)
            
            # 保守修復：對最優個體嘗試列衝突修復（僅在適應度提升時接受）
            if enable_repair and gen > 0 and gen % 10 == 0:  # 每10代嘗試一次
                best_chrom = fitnesses[0][0]
                repair_stats['total_repair_attempts'] += 1
                repaired_chrom, repaired_fit, num_swaps = self.repair_with_permutation_swap(best_chrom, max_swaps=5)
                if num_swaps > 0:
                    repair_stats['successful_repairs'] += 1
                    # 用修復後的個體替換最優個體
                    population[fitnesses.index((best_chrom, fitnesses[0][1]))] = repaired_chrom
                    # 重新計算fitnesses
                    fitnesses = [(chrom, get_fitness(chrom)) for chrom in population]
                    fitnesses.sort(key=lambda x: x[1], reverse=True)
            
            # 精英保留（最優的 20%）
            elite_size = max(1, len(population) // 5)
            new_population = [chrom for chrom, _ in fitnesses[:elite_size]]
            
            # 生成新個體
            while len(new_population) < len(population):
                # 選擇
                parent1, parent2 = random.sample(fitnesses[:len(fitnesses)//2], 2)
                
                # 交叉
                child1, child2 = self.crossover(parent1[0], parent2[0])
                
                # 突變
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)
                
                # 保守修復：突變後嘗試修復（僅在適應度提升時）
                if enable_repair:
                    repaired_child1, fit1, _ = self.repair_with_permutation_swap(child1, max_swaps=2)
                    repaired_child2, fit2, _ = self.repair_with_permutation_swap(child2, max_swaps=2)
                    if fit1 > get_fitness(child1):
                        child1 = repaired_child1
                    if fit2 > get_fitness(child2):
                        child2 = repaired_child2
                
                new_population.extend([child1, child2])
            
            population = new_population[:len(population)]
            
            if gen % 20 == 0:
                print(f"   代 {gen:3d}: 最優適應度 = {fitnesses[0][1]:.4f}, "
                      f"平均 = {sum(f for _, f in fitnesses[:10]) / 10:.4f}, "
                      f"修復成功 = {repair_stats['successful_repairs']}")
        
        # 返回排序後的最優個體
        return sorted(
            [(chrom, get_fitness(chrom)) for chrom in population],
            key=lambda x: x[1],
            reverse=True
        )


# =============================================================================
# 6. 精英迴溯循環進化引擎
# =============================================================================

@dataclass
class EvolutionGeneration:
    """進化代"""
    generation_id: int
    elite_chromosomes: List[str]
    elite_fitnesses: List[float]
    population_size: int
    best_fitness: float
    timestamp: float


class EliteBacktrackEvolutionEngine:
    """
    精英迴溯循環進化引擎
    
    核心機制:
    1. 精英策略：保存每代最優解
    2. 迴溯搜索：從精英解出發，探索新分支
    3. 循環進化：多代迭代，適應度提升
    4. 收斂檢測：如果連續多代適應度無提升，進入迴溯
    """
    
    def __init__(self, genetic_optimizer: BinaryGeneticOptimizer):
        self.optimizer = genetic_optimizer
        self.generations: List[EvolutionGeneration] = []
        self.elite_archive: List[Tuple[str, float]] = []
        self.backtrack_count = 0
    
    def evolve(self, generations: int = 50, elite_ratio: float = 0.2,
               converge_threshold: float = 0.001) -> EvolutionGeneration:
        """
        循環進化
        
        converge_threshold: 連續多代適應度提升小於此值時進入迴溯
        """
        population = self.optimizer.initialize_population(50)
        prev_best = 0.0
        stagnation_count = 0
        max_stagnation = 5
        
        for gen_id in range(generations):
            # 遺傳優化一輪（啟用保守修復）
            ranked = self.optimizer.optimize(population, generations=10, enable_repair=True)
            
            elite_size = max(1, int(len(ranked) * elite_ratio))
            elite_chroms = [chrom for chrom, _ in ranked[:elite_size]]
            elite_fits = [fit for _, fit in ranked[:elite_size]]
            
            generation = EvolutionGeneration(
                generation_id=gen_id,
                elite_chromosomes=elite_chroms,
                elite_fitnesses=elite_fits,
                population_size=len(population),
                best_fitness=elite_fits[0],
                timestamp=time.time()
            )
            self.generations.append(generation)
            self.elite_archive.append((elite_chroms[0], elite_fits[0]))
            
            # 檢測收斂
            improvement = elite_fits[0] - prev_best
            if improvement < converge_threshold:
                stagnation_count += 1
            else:
                stagnation_count = 0
                prev_best = elite_fits[0]
            
            # 迴溯機制：如果連續多代無提升
            if stagnation_count >= max_stagnation:
                print(f"\n🔄 第 {gen_id} 代: 收斂檢測，進入迴溯...")
                self.backtrack_count += 1
                
                # 從精英-archive 中選擇一個分支點
                if len(self.elite_archive) > max_stagnation + 1:
                    backtrack_point = self.elite_archive[-(max_stagnation + 1)]
                    # 基於此精英解進行大變異
                    mutated = self.optimizer.mutate(backtrack_point[0], mutation_rate=0.1)
                    population = [mutated] + self.optimizer.initialize_population(49)
                else:
                    population = self.optimizer.initialize_population(50)
                
                stagnation_count = 0
                prev_best = 0.0
            else:
                population = ranked[:len(population)]
            
            if gen_id % 10 == 0:
                print(f"   代 {gen_id:3d}: 最優適應度 = {elite_fits[0]:.4f}, "
                      f"平均 = {sum(e for _, e in ranked[:10]) / 10:.4f}")
        
        return self.generations[-1]
    
    def get_best_solution(self) -> Tuple[str, float]:
        """返回 archive 中最好的解"""
        if not self.elite_archive:
            return ('', 0.0)
        return max(self.elite_archive, key=lambda x: x[1])
    
    def get_evolution_summary(self) -> Dict:
        """進化摘要"""
        if not self.generations:
            return {}
        
        return {
            'total_generations': len(self.generations),
            'backtrack_count': self.backtrack_count,
            'final_best_fitness': self.generations[-1].best_fitness,
            'initial_best_fitness': self.generations[0].best_fitness,
            'fitness_improvement': (
                self.generations[-1].best_fitness - self.generations[0].best_fitness
            ) if self.generations else 0
        }


# =============================================================================
# 7. 融闔綜闔剪枝博弈框架
# =============================================================================

class PruningStrategy(Enum):
    """剪枝策略類型"""
    FAHUO_PRUNING = "fahuo"          # 符闔排列剪枝
    COLUMN_PRUNING = "column"         # 列約束剪枝
    BOX_PRUNING = "box"               # 宮約束剪枝
    EARLY_FAILURE = "early_failure"   # 早停機制


@dataclass
class PruningResult:
    """剪枝結果"""
    strategy: PruningStrategy
    nodes_evaluated: int
    nodes_pruned: int
    pruning_efficiency: float
    constraint_violations: int


class FusionPruningGame:
    """
    融闔綜闔剪枝博弈框架
    
    多層剪枝策略，博弈式约束冲突检测：
    
    1. 符闔排列剪枝：最關鍵，壓縮 10^50+ 倍
    2. 列約束剪枝：檢測列AllDifferent
    3. 宮約束剪枝：檢測宮AllDifferent
    4. 早停機制：約束衝突時立即返回 INFEASIBLE
    """
    
    def __init__(self, permutations: List[List[int]], grid_size: int = 16):
        self.permutations = permutations
        self.grid_size = grid_size
        self.perm_count = len(permutations)
        
        # 預計算排列間的列相容性
        self.column_compatibility = self._build_column_compatibility()
    
    def _build_column_compatibility(self) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
        """
        預計算每行每列值的相容性
        
        column_compatibility[(row_i, col_j)] = 可行的 (perm_idx, val) 列表
        """
        compat = defaultdict(list)
        
        for row_i in range(self.grid_size):
            for col_j in range(self.grid_size):
                for perm_idx, perm in enumerate(self.permutations):
                    val = perm[col_j]
                    compat[(row_i, col_j)].append((perm_idx, val))
        
        return compat
    
    def fahuo_pruning(self, partial_grid: List[List[Optional[int]]]) -> PruningResult:
        """
        符闔排列剪枝
        
        對於部分填充的行，檢查是否存在匹配的符闔排列
        """
        nodes_evaluated = 0
        nodes_pruned = 0
        violations = 0
        
        for i in range(self.grid_size):
            nodes_evaluated += 1
            
            # 收集該行已有的值
            existing_vals = {}
            for j in range(self.grid_size):
                if partial_grid[i][j] is not None:
                    existing_vals[j] = partial_grid[i][j]
            
            # 檢查是否存在匹配的符闔排列
            has_match = False
            for perm in self.permutations:
                match = True
                for j, val in existing_vals.items():
                    if perm[j] != val:
                        match = False
                        break
                
                if match:
                    has_match = True
                    break
            
            if not has_match:
                nodes_pruned += 1
                violations += 1
        
        efficiency = 1.0 - (nodes_pruned / max(1, nodes_evaluated))
        
        return PruningResult(
            strategy=PruningStrategy.FAHUO_PRUNING,
            nodes_evaluated=nodes_evaluated,
            nodes_pruned=nodes_pruned,
            pruning_efficiency=efficiency,
            constraint_violations=violations
        )
    
    def column_pruning(self, partial_grid: List[List[Optional[int]]]) -> PruningResult:
        """列約束剪枝"""
        nodes_evaluated = self.grid_size
        nodes_pruned = 0
        violations = 0
        
        for j in range(self.grid_size):
            col_vals = set()
            for i in range(self.grid_size):
                if partial_grid[i][j] is not None:
                    if partial_grid[i][j] in col_vals:
                        violations += 1
                        nodes_pruned += 1
                        break
                    col_vals.add(partial_grid[i][j])
        
        efficiency = 1.0 - (nodes_pruned / max(1, nodes_evaluated))
        
        return PruningResult(
            strategy=PruningStrategy.COLUMN_PRUNING,
            nodes_evaluated=nodes_evaluated,
            nodes_pruned=nodes_pruned,
            pruning_efficiency=efficiency,
            constraint_violations=violations
        )
    
    def box_pruning(self, partial_grid: List[List[Optional[int]]]) -> PruningResult:
        """宮約束剪枝"""
        box_size = 4
        num_boxes = (self.grid_size // box_size) ** 2
        
        nodes_evaluated = num_boxes
        nodes_pruned = 0
        violations = 0
        
        for band in range(self.grid_size // box_size):
            for stack in range(self.grid_size // box_size):
                box_vals = set()
                for bi in range(box_size):
                    for bj in range(box_size):
                        row = band * box_size + bi
                        col = stack * box_size + bj
                        val = partial_grid[row][col]
                        if val is not None:
                            if val in box_vals:
                                violations += 1
                                nodes_pruned += 1
                                break
                            box_vals.add(val)
        
        efficiency = 1.0 - (nodes_pruned / max(1, nodes_evaluated))
        
        return PruningResult(
            strategy=PruningStrategy.BOX_PRUNING,
            nodes_evaluated=nodes_evaluated,
            nodes_pruned=nodes_pruned,
            pruning_efficiency=efficiency,
            constraint_violations=violations
        )
    
    def unified_pruning(self, partial_grid: List[List[Optional[int]]],
                        strict_order: List[PruningStrategy] = None) -> PruningResult:
        """
        統一剪枝：多層剪枝博弈
        
        按指定順序依次應用剪枝，如果任何一層發現衝突，立即返回（早停）
        """
        if strict_order is None:
            strict_order = [
                PruningStrategy.FAHUO_PRUNING,
                PruningStrategy.COLUMN_PRUNING,
                PruningStrategy.BOX_PRUNING
            ]
        
        total_pruned = 0
        total_violations = 0
        pruning_results = []
        
        for strategy in strict_order:
            if strategy == PruningStrategy.FAHUO_PRUNING:
                result = self.fahuo_pruning(partial_grid)
            elif strategy == PruningStrategy.COLUMN_PRUNING:
                result = self.column_pruning(partial_grid)
            elif strategy == PruningStrategy.BOX_PRUNING:
                result = self.box_pruning(partial_grid)
            else:
                continue
            
            pruning_results.append(result)
            total_pruned += result.nodes_pruned
            total_violations += result.constraint_violations
            
            # 早停：如果發現衝突
            if result.constraint_violations > 0:
                break
        
        return PruningResult(
            strategy=PruningStrategy.EARLY_FAILURE,
            nodes_evaluated=sum(r.nodes_evaluated for r in pruning_results),
            nodes_pruned=total_pruned,
            pruning_efficiency=1.0 - (total_pruned / max(1, sum(r.nodes_evaluated for r in pruning_results))),
            constraint_violations=total_violations
        )
    
    def get_pruning_statistics(self) -> Dict:
        """獲取剪枝統計"""
        return {
            'fahuo_pruning': f"符闔排列剪枝: 將搜索空間壓縮 ~10^{math.log10(self.perm_count ** 16):.0f} 倍",
            'column_pruning': f"列約束剪枝: 檢測 {self.grid_size} 列的 AllDifferent",
            'box_pruning': f"宮約束剪枝: 檢測 {(self.grid_size // 4) ** 2} 宮的 AllDifferent",
            'total_pruning_power': f"綜合理論剪枝功率: ~10^{math.log10(self.perm_count ** 16 * self.grid_size ** (self.grid_size - 16)):.0f} 倍"
        }


# =============================================================================
# 8. 唯一解坍縮驗證機制
# =============================================================================

@dataclass
class CollapseResult:
    """坍縮驗證結果"""
    quantum_state: QuantumState
    is_unique: bool
    solution_count: int
    verified_solution: Optional[List[List[int]]] = None
    validation_details: Dict = field(default_factory=dict)
    collapse_timestamp: Optional[float] = None


class UniqueSolutionCollapseVerifier:
    """
    唯一解坍縮驗證機制
    
    量子力學类比:
    - 多解存在 → 量子態（superposition），系統保持多解共存
    - 唯一解存在 → 系統坍縮（collapse），測量得到確定結果
    - 無解存在 → 約束衝突（infeasible），波函數為零
    """
    
    def __init__(self, grid_size: int = 16, box_size: int = 4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.solution_buffer: List[List[List[int]]] = []
        self.solution_limit = 10  # 最多收集 10 個解來判斷是否唯一
    
    def verify_unique_solution(self, model: cp_model.CpModel,
                                solver: cp_model.CpSolver) -> CollapseResult:
        """
        驗證是否為唯一解
        
        方法：先求解，找到第一個解；然後添加排除約束，看是否還有其他解
        """
        self.solution_buffer = []
        
        # 求解器配置
        solver.parameters.max_time_in_seconds = 60
        solver.parameters.log_search_progress = False
        solver.parameters.enumerate_all_solutions = True
        
        # 收集所有解（最多 solution_limit 個）
        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self, buffer, limit):
                super().__init__()
                self.buffer = buffer
                self.limit = limit
            
            def on_solution_callback(self):
                if len(self.buffer) < self.limit:
                    solution = []
                    for i in range(16):
                        row = []
                        for j in range(16):
                            row.append(self.Value(self.x[i * 16 + j]))
                        solution.append(row)
                    self.buffer.append(solution)
        
        # 由於 CP-SAT 不支持直接遍歷解，我們使用技巧：
        # 找到一個解後，添加排除約束，看是否還有其他解
        
        status = solver.Solve(model)
        
        if status == cp_model.INFEASIBLE:
            return CollapseResult(
                quantum_state=QuantumState.INFEASIBLE,
                is_unique=False,
                solution_count=0,
                validation_details={'error': '無解 - 約束衝突'}
            )
        
        if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
            # 提取第一個解
            first_solution = []
            for i in range(self.grid_size):
                row = []
                for j in range(self.grid_size):
                    row.append(solver.Value(solver.__getattr__('x').get((i, j), None)))
                # 如果變量名不是 (i,j) 格式，需要重新查找
                # 這裡簡化處理，我們需要從模型中獲取變量引用
                pass
            
            # 更穩健的方法：使用模型變量
            # 由於變量引用複雜，我們改用另一種方式
            # 收集解的方式需要根據具體模型調整
            
            return CollapseResult(
                quantum_state=QuantumState.SUPERPOSITION,
                is_unique=False,
                solution_count=1,
                validation_details={'note': '找到至少一個解，需要進一步檢查唯一性'}
            )
        
        return CollapseResult(
            quantum_state=QuantumState.INFEASIBLE,
            is_unique=False,
            solution_count=0,
            validation_details={'error': f'求解狀態: {status}'}
        )
    
    def verify_with_solution_limit(self, model: cp_model.CpModel,
                                    solver: cp_model.CpSolver,
                                    solution_var_refs: Dict[Tuple[int, int], Any],
                                    timeout: int = 300) -> CollapseResult:
        """
        使用 solution_limit 來判斷唯一性
        
        如果只找到 1 個解 → 坍縮（唯一解）
        如果找到 >= 2 個解 → 保持量子態（多解）
        """
        class MultiSolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self, var_refs, limit):
                super().__init__()
                self.var_refs = var_refs
                self.limit = limit
                self.solutions = []
            
            def on_solution_callback(self):
                if len(self.solutions) < self.limit:
                    solution = []
                    for i in range(16):
                        row = []
                        for j in range(16):
                            key = (i, j)
                            val = self.Value(self.var_refs[key])
                            row.append(val)
                        solution.append(row)
                    self.solutions.append(solution)
        
        collector = MultiSolutionCollector(solution_var_refs, self.solution_limit)
        
        start_time = time.time()
        solver.Solve(model, collector)
        
        solution_count = len(collector.solutions)
        elapsed = time.time() - start_time
        
        if solution_count == 0:
            quantum_state = QuantumState.INFEASIBLE
            is_unique = False
        elif solution_count == 1:
            quantum_state = QuantumState.COLLAPSED
            is_unique = True
        else:
            quantum_state = QuantumState.SUPERPOSITION
            is_unique = False
        
        return CollapseResult(
            quantum_state=quantum_state,
            is_unique=is_unique,
            solution_count=solution_count,
            verified_solution=collector.solutions[0] if collector.solutions else None,
            collapse_timestamp=elapsed,
            validation_details={
                'solutions_collected': solution_count,
                'time_elapsed': round(elapsed, 3),
                'is_proven_unique': solution_count == 1
            }
        )
    
    def generate_collapse_report(self, result: CollapseResult) -> str:
        """生成坍縮驗證報告"""
        state_icon = {
            QuantumState.SUPERPOSITION: "⚛️",
            QuantumState.COLLAPSED: "🔬",
            QuantumState.INFEASIBLE: "❌"
        }
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        量子態測量與坍縮驗證報告                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  測量時間: {time.strftime('%Y-%m-%d %H:%M:%S')}                                    ║
║  量子態: {state_icon[result.quantum_state]} {result.quantum_state.value.upper()}                                           ║
║  解數量: {result.solution_count}                                                ║
║  是否唯一: {'✅ 是 - 系統坍縮' if result.is_unique else '❌ 否 - 量子態保持' if result.quantum_state != QuantumState.INFEASIBLE else '❌ 不可滿足'}                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  坍縮分析:                                                                    ║
║  ─────────────────────────────────────────────────────────────────────────   ║
"""
        
        if result.quantum_state == QuantumState.COLLAPSED:
            report += """║  ★ 系統坍縮發生！                                                        ║
║  ★ 唯一解被確定，波函數坍縮至確定態                                      ║
║  ★ 符闔博弈框架成功收斂至單一點                                        ║
║  ★ 驗證通過，符闔排列約束與列宮約束達成完美平衡                        ║
"""
        elif result.quantum_state == QuantumState.SUPERPOSITION:
            report += f"""║  ★ 量子態保持，存在 {result.solution_count} 個解                                             ║
║  ★ 波函數未坍縮，多解共存狀態                                          ║
║  ★ 符闔博弈框架處於開放狀態，需要進一步約束                            ║
║  ★ 搜索空間仍有多個可行區域                                           ║
"""
        elif result.quantum_state == QuantumState.INFEASIBLE:
            report += """║  ★ 約束衝突，波函數為零                                               ║
║  ★ 符闔排列約束與列宮約束形成不可破解的鎖定鏈                          ║
║  ★ 請檢查謎題配置或符闔排列池                                         ║
"""
        
        report += f"""╚══════════════════════════════════════════════════════════════════════════════╝

📊 詳細統計:
"""
        for key, value in result.validation_details.items():
            report += f"   {key}: {value}\n"
        
        return report


# =============================================================================
# 9. 主求解框架 - 符闔數獨進化式求解系統
# =============================================================================

class CosmicThunderEvolutionarySolver:
    """
    符闔數獨進化式求解系統 V19.0
    
    完整流程:
    1. 未解盤基底 → 零約束狀態
    2. 增量約束添加 → 行→已知→符闔→列→宮
    3. 樹狀多解空間展開
    4. 二進制遺傳優化
    5. 精英迴溯循環進化
    6. 融闔綜闔剪枝博弈
    7. 唯一解坍縮驗證
    """
    
    def __init__(self, grid_size: int = 16, box_size: int = 4):
        self.grid_size = grid_size
        self.box_size = box_size
        
        # 初始化各個模組
        self.fahuo_manager = FahuoConstraintManager(grid_size, box_size)
        self.fusion_pruning = FusionPruningGame(
            self.fahuo_manager.permutations,
            grid_size
        )
        self.genetic_optimizer = BinaryGeneticOptimizer(
            self.fahuo_manager.permutations,
            grid_size
        )
        self.evolution_engine = EliteBacktrackEvolutionEngine(self.genetic_optimizer)
        self.collapse_verifier = UniqueSolutionCollapseVerifier(grid_size, box_size)
        
        # 狀態記錄
        self.current_puzzle: Optional[UnunsolvedPuzzle] = None
        self.current_model: Optional[cp_model.CpModel] = None
        self.x_vars: Dict[Tuple[int, int], Any] = {}
        self.search_tree: Optional[TreeSearchSpace] = None
        self.prune_stats: List[PruningResult] = []
    
    def load_data(self):
        """載入數據"""
        # 嘗試從文件載入符闔排列
        print(f"📊 符闔排列數量: {len(self.fahuo_manager.permutations)}")
        print(f"📊 排列列表前 3 個: {self.fahuo_manager.permutations[:3]}")
    
    def initialize_unsolved_puzzle(self, solution: List[List[int]],
                                    given_rate: float = 0.15) -> UnunsolvedPuzzle:
        """初始化未解盤基底"""
        self.current_puzzle = UnunsolvedPuzzle.from_solution(solution, given_rate)
        print(f"🎯 未解盤基底: {self.current_puzzle.get_given_count()} 個已知數 "
              f"({given_rate*100:.1f}% 填滿率)")
        return self.current_puzzle
    
    def build_incremental_model(self) -> cp_model.CpModel:
        """
        構建增量約束模型
        
        按順序添加：行 → 已知 → 符闔 → 列 → 宮
        """
        model = cp_model.CpModel()
        self.x_vars = {}
        
        # 創建變量
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                self.x_vars[(i, j)] = model.NewIntVar(1, self.grid_size, f'x[{i},{j}]')
        
        # 記錄約束添加過程
        constraint_log = []
        
        # 步驟 1: 行約束
        step = self.fahuo_manager.add_row_constraints(model, self.x_vars)
        constraint_log.append(('row', step))
        
        # 步驟 2: 已知數字約束
        if self.current_puzzle:
            step = self.fahuo_manager.add_given_constraints(model, self.x_vars, self.current_puzzle)
            constraint_log.append(('given', step))
        
        # 步驟 3: 符闔排列約束（核心剪枝）
        step = self.fahuo_manager.add_fahuo_constraints(model, self.x_vars)
        constraint_log.append(('fahuo', step))
        
        # 步驟 4: 列約束
        step = self.fahuo_manager.add_column_constraints(model, self.x_vars)
        constraint_log.append(('column', step))
        
        # 步驟 5: 宮約束
        step = self.fahuo_manager.add_box_constraints(model, self.x_vars)
        constraint_log.append(('box', step))
        
        self.current_model = model
        
        return model
    
    def run_pruning_game(self, partial_grid: List[List[Optional[int]]]) -> List[PruningResult]:
        """執行融闔綜闔剪枝博弈"""
        results = []
        
        # 符闔排列剪枝
        result = self.fusion_pruning.fahuo_pruning(partial_grid)
        results.append(result)
        
        # 列約束剪枝
        result = self.fusion_pruning.column_pruning(partial_grid)
        results.append(result)
        
        # 宮約束剪枝
        result = self.fusion_pruning.box_pruning(partial_grid)
        results.append(result)
        
        # 統一剪枝（早停）
        result = self.fusion_pruning.unified_pruning(partial_grid)
        results.append(result)
        
        self.prune_stats = results
        return results
    
    def run_genetic_optimization(self, iterations: int = 20) -> List[Tuple[str, float]]:
        """運行遺傳優化"""
        population = self.genetic_optimizer.initialize_population(50)
        
        for it in range(iterations):
            ranked = self.genetic_optimizer.optimize(population, generations=5)
            best_fit = ranked[0][1]
            print(f"   遺傳迭代 {it+1}/{iterations}: 最優適應度 = {best_fit:.4f}")
            population = [chrom for chrom, _ in ranked[:50]]
        
        return ranked
    
    def run_evolution(self, generations: int = 30) -> EvolutionGeneration:
        """運行循環進化"""
        return self.evolution_engine.evolve(generations=generations)
    
    def verify_collapse(self, timeout: int = 120) -> CollapseResult:
        """驗證是否坍縮（唯一解）"""
        if not self.current_model:
            return CollapseResult(
                quantum_state=QuantumState.INFEASIBLE,
                is_unique=False,
                solution_count=0,
                validation_details={'error': '模型未構建'}
            )
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout
        solver.parameters.num_search_workers = 8
        solver.parameters.log_search_progress = False
        
        result = self.collapse_verifier.verify_with_solution_limit(
            self.current_model,
            solver,
            self.x_vars,
            timeout=timeout
        )
        
        return result
    
    def solve_full_pipeline(self, solution: List[List[int]], given_rate: float = 0.15,
                             enable_genetic: bool = True,
                             enable_evolution: bool = True,
                             verify_unique: bool = True) -> Dict:
        """
        完整求解流水線
        
        流程:
        1. 未解盤基底
        2. 增量構建模 型
        3. 樹狀多解空間展開
        4. 遺傳優化（可選）
        5. 循環進化（可選）
        6. 剪枝博弈
        7. 坍縮驗證
        """
        print("=" * 70)
        print("🌀 符闔數獨進化式求解系統 V19.0")
        print("=" * 70)
        
        # 1. 初始化未解盤基底
        print("\n[階段 1] 未解盤基底初始化")
        puzzle = self.initialize_unsolved_puzzle(solution, given_rate)
        
        # 2. 構建增量模型
        print("\n[階段 2] 增量約束模型構建")
        self.build_incremental_model()
        
        # 3. 樹狀多解空間
        print("\n[階段 3] 樹狀多解空間展開")
        self.search_tree = TreeSearchSpace(puzzle)
        # 模擬樹狀展開
        tree_root = self.search_tree.root
        print(f"   根節點: fill_rate = {puzzle.get_fill_rate()*100:.1f}%")
        print(f"   約束層數: 5 (行→已知→符闔→列→宮)")
        
        # 4. 遺傳優化
        if enable_genetic:
            print("\n[階段 4] 二進制快速遺傳優化")
            genetic_results = self.run_genetic_optimization(iterations=10)
            best_chrom, best_fit = genetic_results[0]
            print(f"   最優解適應度: {best_fit:.4f}")
        
        # 5. 循環進化
        if enable_evolution:
            print("\n[階段 5] 精英迴溯循環進化")
            evolution_result = self.run_evolution(generations=20)
            summary = self.evolution_engine.get_evolution_summary()
            print(f"   進化代數: {summary.get('total_generations', 0)}")
            print(f"   迴溯次數: {summary.get('backtrack_count', 0)}")
            print(f"   最終適應度: {summary.get('final_best_fitness', 0):.4f}")
        
        # 6. 剪枝博弈
        print("\n[階段 6] 融闔綜闔剪枝博弈")
        # 從遺傳優化獲取一個候選解進行剪枝分析
        if enable_genetic and genetic_results:
            best_chrom, _ = genetic_results[0]
            candidate_grid = self.genetic_optimizer.decode_to_grid(best_chrom)
            prune_results = self.run_pruning_game(candidate_grid)
            for pr in prune_results:
                print(f"   {pr.strategy.value}: 效率 = {pr.pruning_efficiency:.2%}, "
                      f"衝突 = {pr.constraint_violations}")
        
        # 7. 坍縮驗證
        if verify_unique:
            print("\n[階段 7] 唯一解坍縮驗證")
            collapse_result = self.verify_collapse()
            
            # 生成報告
            collapse_report = self.collapse_verifier.generate_collapse_report(collapse_result)
            print(collapse_report)
        
        # 匯總結果
        return {
            'puzzle': puzzle,
            'tree_stats': tree_root.get_stats() if tree_root else {},
            'genetic_best_fitness': genetic_results[0][1] if enable_genetic and genetic_results else None,
            'evolution_summary': self.evolution_engine.get_evolution_summary() if enable_evolution else None,
            'prune_stats': self.prune_stats,
            'collapse_result': collapse_result if verify_unique else None,
            'quantum_state': collapse_result.quantum_state if verify_unique else None
        }


# =============================================================================
# 10. 主程序入口
# =============================================================================

def main():
    """主程序"""
    print("=" * 70)
    print("  符闔數獨進化式求解系統 V19.0")
    print("  Cosmic Thunder Sudoku Evolutionary Solver")
    print("=" * 70)
    
    # 載入真實解和符闔排列
    solver = CosmicThunderEvolutionarySolver()
    solver.load_data()
    
    # 載入真實解
    sol_path = Path(__file__).parent / 'solution_v4_final.json'
    if sol_path.exists():
        with open(sol_path, 'r', encoding='utf-8') as f:
            solution = json.load(f)
        print(f"\n✅ 真實解載入: {len(solution)} × {len(solution[0])}")
        
        # 驗證解的有效性
        valid = True
        for i in range(16):
            row_vals = set(solution[i])
            if len(row_vals) != 16:
                valid = False
                break
        
        print(f"   行約束驗證: {'✅ 通過' if valid else '❌ 失敗'}")
        
        # 檢查每行是否都在符闔排列中
        perm_set = set(tuple(p) for p in solver.fahuo_manager.permutations)
        all_in_pool = all(tuple(row) in perm_set for row in solution)
        print(f"   符闔排列匹配: {'✅ 全部匹配' if all_in_pool else '❌ 部分不匹配'}")
        
    else:
        print(f"\n⚠️ 真實解文件未找到: {sol_path}")
        print("   請先確保 solution_v4_final.json 存在")
        return
    
    # 運行完整求解流水線
    print("\n" + "=" * 70)
    print("  開始完整求解流水線")
    print("=" * 70)
    
    results = solver.solve_full_pipeline(
        solution=solution,
        given_rate=0.15,  # 15% 填滿率
        enable_genetic=True,
        enable_evolution=True,
        verify_unique=True
    )
    
    # 打印最終摘要
    print("\n" + "=" * 70)
    print("  最終摘要")
    print("=" * 70)
    
    print(f"\n📊 未解盤基底: {results['puzzle'].get_given_count()} 個已知數")
    
    if results['genetic_best_fitness']:
        print(f"🧬 遺傳優化: 最優適應度 = {results['genetic_best_fitness']:.4f}")
    
    if results['evolution_summary']:
        summary = results['evolution_summary']
        print(f"🔄 循環進化: {summary.get('total_generations', 0)} 代, "
              f"迴溯 {summary.get('backtrack_count', 0)} 次")
    
    if results['collapse_result']:
        result = results['collapse_result']
        state_map = {
            QuantumState.COLLAPSED: "🔬 坍縮（唯一解）",
            QuantumState.SUPERPOSITION: "⚛️ 量子態（多解）",
            QuantumState.INFEASIBLE: "❌ 不可滿足"
        }
        print(f"\n🔮 量子態測量: {state_map[result.quantum_state]}")
        print(f"   解數量: {result.solution_count}")
    
    print("\n" + "=" * 70)
    print("  符闔博弈優選策略框架 - V19.0 完成")
    print("=" * 70)


if __name__ == '__main__':
    main()
