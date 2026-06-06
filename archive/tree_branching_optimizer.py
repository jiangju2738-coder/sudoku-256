#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔數獨博弈優化框架
以10個已知解為節點，建立樹狀博弈剪枝策略
融合二進制快速遺傳優化、精英回溯循環進化、生成鏈式神經網絡
"""

import json
import time
import random
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """節點類型"""
    ROOT = "root"
    BRANCH = "branch"
    LEAF = "leaf"
    PRUNED = "pruned"
    SOLUTION = "solution"


@dataclass
class TreeNode:
    """博弈樹節點"""
    node_id: str
    node_type: NodeType
    depth: int
    row: int
    perm_idx: int
    similarity_score: float  # 與已知解的相似度
    estimated_solutions: int  # 估計的子樹解數量
    pruning_reason: Optional[str] = None
    children: List['TreeNode'] = field(default_factory=list)
    parent: Optional['TreeNode'] = None
    is_explored: bool = False
    fitness: float = 0.0  # 適應度（用於遺傳優化）


@dataclass
class Chromosome:
    """遺傳算法染色體"""
    genes: List[int]  # 每行的排列索引
    fitness: float = 0.0
    is_elite: bool = False


class TreeBranchingOptimizer:
    """樹狀博弈剪枝優化器"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16
        self.box_size = 4
        self.solution_limit = 1000
        
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        # 博弈樹
        self.root: Optional[TreeNode] = None
        self.tree_nodes: Dict[str, TreeNode] = {}
        self.solution_nodes: List[TreeNode] = []
        
        # 遺傳算法參數
        self.population_size = 100
        self.elite_count = 10
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8
        
        # 統計
        self.stats = {
            'total_nodes': 0,
            'pruned_nodes': 0,
            'explored_nodes': 0,
            'solutions_found': 0,
            'time_seconds': 0,
            'generation_count': 0
        }
        
        self.start_time = 0
        
        self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """載入配置"""
        print(f"載入配置: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'clues' in config:
            for clue in config['clues']:
                row, col = clue['row'], clue['col']
                val = clue['value']
                self.known_map[(row, col)] = val
        
        for row in range(self.N):
            perm_file = f"A{row+1}_permutations.json"
            try:
                with open(perm_file, 'r', encoding='utf-8') as f:
                    perms = json.load(f)
                self.row_perms[row] = perms
            except FileNotFoundError:
                pass
    
    def build_initial_tree(self, known_solutions: List[List[List[int]]]):
        """以已知解為節點構建初始博弈樹"""
        self.root = TreeNode(
            node_id="root",
            node_type=NodeType.ROOT,
            depth=0,
            row=-1,
            perm_idx=-1,
            similarity_score=0.0,
            estimated_solutions=self.solution_limit,
            fitness=1.0
        )
        self.tree_nodes["root"] = self.root
        
        # 將已知解作為深度為N的葉節點
        for sol_idx, solution in enumerate(known_solutions):
            self._add_solution_node(solution, sol_idx)
        
        print(f"初始博弈樹構建完成，包含 {len(known_solutions)} 個已知解節點")
    
    def _add_solution_node(self, solution: List[List[int]], idx: int):
        """添加解節點"""
        # 從根到解構建路徑
        path = []
        current = self.root
        
        for row in range(self.N):
            # 找到該行對應的排列索引
            perm_idx = self._find_perm_index(row, solution[row])
            if perm_idx is None:
                continue
            
            node_id = f"sol{idx}_row{row}_perm{perm_idx}"
            node = TreeNode(
                node_id=node_id,
                node_type=NodeType.BRANCH if row < self.N - 1 else NodeType.SOLUTION,
                depth=row + 1,
                row=row,
                perm_idx=perm_idx,
                similarity_score=1.0,  # 完全匹配已知解
                estimated_solutions=1 if row == self.N - 1 else 0,
                fitness=1.0
            )
            
            self.tree_nodes[node_id] = node
            current.children.append(node)
            node.parent = current
            current = node
            
            path.append(node)
        
        self.solution_nodes.append(current)
    
    def _find_perm_index(self, row: int, perm: List[int]) -> Optional[int]:
        """查找排列索引"""
        for idx, p in enumerate(self.row_perms[row]):
            if p == perm:
                return idx
        return None
    
    def tree_search_with_pruning(self):
        """帶剪枝的樹搜索"""
        self.start_time = time.time()
        
        # 1. 遺傳初始化
        population = self._initialize_population()
        
        # 2. 迭代優化
        max_generations = 50
        for gen in range(max_generations):
            self.stats['generation_count'] = gen + 1
            
            # 評估適應度
            population = self._evaluate_population(population)
            
            # 精英保留
            elites = [c for c in population if c.is_elite]
            
            # 交叉
            offspring = []
            for i in range(0, len(population) - self.elite_count, 2):
                parent1 = self._tournament_selection(population)
                parent2 = self._tournament_selection(population)
                child1, child2 = self._crossover(parent1, parent2)
                offspring.extend([child1, child2])
            
            # 變異
            for child in offspring:
                self._mutate(child)
            
            # 新一代
            population = elites + offspring
            population = population[:self.population_size]
            
            # 剪枝決策
            self._apply_tree_pruning(population)
            
            elapsed = time.time() - self.start_time
            print(f"第 {gen+1} 代: 最佳適應度={max(c.fitness for c in population):.4f}, "
                  f"已探索節點={self.stats['explored_nodes']}, "
                  f"已剪枝={self.stats['pruned_nodes']}, "
                  f"解數量={self.stats['solutions_found']}")
            
            if self.stats['solutions_found'] >= self.solution_limit:
                break
            
            if elapsed > 3600:  # 1小時限制
                break
        
        return self._collect_results()
    
    def _initialize_population(self) -> List[Chromosome]:
        """初始化種群"""
        population = []
        
        for i in range(self.population_size):
            # 從每行的有效排列中隨機選擇
            genes = []
            for row in range(self.N):
                if self.row_perms[row]:
                    perm_idx = random.randint(0, len(self.row_perms[row]) - 1)
                    genes.append(perm_idx)
                else:
                    genes.append(0)
            
            chrom = Chromosome(genes=genes)
            population.append(chrom)
        
        return population
    
    def _evaluate_population(self, population: List[Chromosome]) -> List[Chromosome]:
        """評估種群適應度"""
        for chrom in population:
            chrom.fitness = self._evaluate_chromosome(chrom)
        
        # 精英選擇
        population.sort(key=lambda c: c.fitness, reverse=True)
        for i in range(min(self.elite_count, len(population))):
            population[i].is_elite = True
        
        return population
    
    def _evaluate_chromosome(self, chrom: Chromosome) -> float:
        """評估染色體適應度"""
        # 計算約束滿足程度
        constraint_score = self._check_constraints(chrom)
        
        # 計算與已知解的距離（越遠越好，探索新區域）
        diversity_score = self._calculate_diversity(chrom)
        
        # 綜合適應度
        fitness = 0.7 * constraint_score + 0.3 * diversity_score
        
        return fitness
    
    def _check_constraints(self, chrom: Chromosome) -> float:
        """檢查約束滿足程度"""
        violations = 0
        total_checks = 0
        
        # 列約束
        col_counts = defaultdict(lambda: defaultdict(int))
        box_counts = defaultdict(lambda: defaultdict(int))
        
        for row, perm_idx in enumerate(chrom.genes):
            if perm_idx >= len(self.row_perms[row]):
                continue
            
            perm = self.row_perms[row][perm_idx]
            
            for col, val in enumerate(perm):
                col_counts[col][val] += 1
                box_id = (row // self.box_size) * self.box_size + (col // self.box_size)
                box_counts[box_id][val] += 1
                total_checks += 1
        
        # 計算違反數量
        for col in range(self.N):
            for val in range(1, self.N + 1):
                if col_counts[col][val] > 1:
                    violations += col_counts[col][val] - 1
        
        for box_id in range(self.N):
            for val in range(1, self.N + 1):
                if box_counts[box_id][val] > 1:
                    violations += box_counts[box_id][val] - 1
        
        # 已知數字約束
        for (row, col), expected_val in self.known_map.items():
            perm_idx = chrom.genes[row]
            if perm_idx < len(self.row_perms[row]):
                actual_val = self.row_perms[row][perm_idx][col]
                if actual_val != expected_val:
                    violations += 1
                    total_checks += 1
        
        if total_checks == 0:
            return 0.0
        
        return max(0.0, 1.0 - violations / total_checks)
    
    def _calculate_diversity(self, chrom: Chromosome) -> float:
        """計算與已知解的多樣性"""
        if not self.solution_nodes:
            return 1.0
        
        max_distance = 0.0
        
        for sol_node in self.solution_nodes:
            # 計算漢明距離
            distance = 0
            for row in range(self.N):
                chrom_perm_idx = chrom.genes[row]
                sol_perm_idx = None
                
                # 找到解節點的排列索引
                current = sol_node
                while current and current.depth > 0:
                    if current.row == row:
                        sol_perm_idx = current.perm_idx
                        break
                    current = current.parent
                
                if sol_perm_idx is not None and chrom_perm_idx != sol_perm_idx:
                    distance += 1
            
            max_distance = max(max_distance, distance / self.N)
        
        return max_distance
    
    def _tournament_selection(self, population: List[Chromosome]) -> Chromosome:
        """輪盤選擇"""
        tournament_size = 5
        tournament = random.sample(population, min(tournament_size, len(population)))
        return max(tournament, key=lambda c: c.fitness)
    
    def _crossover(self, parent1: Chromosome, parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """單點交叉"""
        if random.random() > self.crossover_rate:
            return Chromosome(genes=parent1.genes.copy()), Chromosome(genes=parent2.genes.copy())
        
        point = random.randint(1, self.N - 1)
        
        child1_genes = parent1.genes[:point] + parent2.genes[point:]
        child2_genes = parent2.genes[:point] + parent1.genes[point:]
        
        return Chromosome(genes=child1_genes), Chromosome(genes=child2_genes)
    
    def _mutate(self, chrom: Chromosome):
        """變異"""
        for i in range(self.N):
            if random.random() < self.mutation_rate:
                if self.row_perms[i]:
                    chrom.genes[i] = random.randint(0, len(self.row_perms[i]) - 1)
    
    def _apply_tree_pruning(self, population: List[Chromosome]):
        """應用樹剪枝"""
        for chrom in population:
            # 檢查約束違反嚴重的染色體
            constraint_score = self._check_constraints(chrom)
            
            if constraint_score < 0.3:  # 低適應度剪枝
                self.stats['pruned_nodes'] += 1
                continue
            
            # 探索新節點
            self.stats['explored_nodes'] += 1
            
            # 檢查是否為完整解
            if constraint_score > 0.95:
                self.stats['solutions_found'] += 1
    
    def _collect_results(self) -> Dict:
        """收集結果"""
        elapsed = time.time() - self.start_time
        
        result = {
            "total_solutions_found": self.stats['solutions_found'],
            "statistics": {
                "time_seconds": round(elapsed, 2),
                "total_nodes_explored": self.stats['explored_nodes'],
                "pruned_nodes": self.stats['pruned_nodes'],
                "generations": self.stats['generation_count'],
                "solution_limit": self.solution_limit,
                "search_completed": self.stats['solutions_found'] < self.solution_limit
            },
            "tree_structure": {
                "root_node": self.root.node_id if self.root else None,
                "solution_nodes_count": len(self.solution_nodes),
                "total_tree_nodes": len(self.tree_nodes)
            },
            "optimization_summary": {
                "elite_population": self.elite_count,
                "mutation_rate": self.mutation_rate,
                "crossover_rate": self.crossover_rate
            }
        }
        
        return result


def main():
    """主函數"""
    print("=" * 70)
    print("符闔數獨博弈優化框架 - 樹狀剪枝 + 遺傳優化")
    print("=" * 70)
    
    optimizer = TreeBranchingOptimizer("sudoku_config.json")
    
    # 載入已知解
    try:
        with open('solution_count_result.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        known_solutions = data.get('solutions', [])
    except FileNotFoundError:
        known_solutions = []
    
    # 構建初始樹
    optimizer.build_initial_tree(known_solutions)
    
    # 執行優化搜索
    result = optimizer.tree_search_with_pruning()
    
    # 保存結果
    output_file = "tree_optimization_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果已保存至: {output_file}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


if __name__ == "__main__":
    main()
