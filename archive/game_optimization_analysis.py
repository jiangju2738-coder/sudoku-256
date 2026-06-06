#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
博弈優化框架 - 解空間結構分析
二進制遺傳優化、精英回溯、生成鏈式神經網絡
"""

import json
import time
import random
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class NodeType(Enum):
    ROOT = "root"
    BRANCH = "branch"
    LEAF = "leaf"
    SOLUTION = "solution"
    PRUNED = "pruned"


@dataclass
class TreeNode:
    """博弈樹節點"""
    node_id: str
    node_type: NodeType
    depth: int
    row: int
    perm_idx: int
    similarity_score: float
    estimated_solutions: int
    children: List['TreeNode'] = field(default_factory=list)
    parent: Optional['TreeNode'] = None
    is_explored: bool = False
    fitness: float = 0.0


@dataclass
class Chromosome:
    """遺傳算法染色體"""
    genes: List[int]  # 每行的排列索引
    fitness: float = 0.0
    is_elite: bool = False
    generation: int = 0
    lineage: List[str] = field(default_factory=list)


class GameOptimizationAnalyzer:
    """博弈優化分析器"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16
        self.box_size = 4
        
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        # 博弈樹
        self.root: Optional[TreeNode] = None
        self.tree_nodes: Dict[str, TreeNode] = {}
        self.solution_nodes: List[TreeNode] = []
        
        # 遺傳算法參數
        self.population_size = 200
        self.elite_count = 20
        self.mutation_rate = 0.15
        self.crossover_rate = 0.85
        
        # 統計
        self.stats = {
            'total_nodes': 0,
            'pruned_nodes': 0,
            'explored_nodes': 0,
            'solutions_found': 0,
            'generations': 0,
            'diversity_scores': [],
            'fitness_progression': []
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
        
        print(f"  已知數字: {len(self.known_map)} 個")
        print(f"  排列總數: {sum(len(p) for p in self.row_perms):,}")
    
    def _find_perm_index(self, row: int, perm: List[int]) -> Optional[int]:
        """查找排列索引"""
        for idx, p in enumerate(self.row_perms[row]):
            if p == perm:
                return idx
        return None
    
    def build_initial_tree(self, known_solutions: List[List[List[int]]]):
        """構建初始博弈樹（以已知解為節點）"""
        self.root = TreeNode(
            node_id="root",
            node_type=NodeType.ROOT,
            depth=0,
            row=-1,
            perm_idx=-1,
            similarity_score=0.0,
            estimated_solutions=0,
            fitness=1.0
        )
        self.tree_nodes["root"] = self.root
        
        # 將已知解作為葉節點
        for sol_idx, solution in enumerate(known_solutions):
            self._add_solution_node(solution, sol_idx)
        
        print(f"初始博弈樹: {len(known_solutions)} 個解節點")
    
    def _add_solution_node(self, solution: List[List[int]], idx: int):
        """添加解節點"""
        current = self.root
        
        for row in range(self.N):
            perm_idx = self._find_perm_index(row, solution[row])
            if perm_idx is None:
                continue
            
            node_id = f"sol{idx}_r{row}_p{perm_idx}"
            node = TreeNode(
                node_id=node_id,
                node_type=NodeType.SOLUTION if row == self.N - 1 else NodeType.BRANCH,
                depth=row + 1,
                row=row,
                perm_idx=perm_idx,
                similarity_score=1.0,
                estimated_solutions=1 if row == self.N - 1 else 0,
                fitness=1.0
            )
            
            self.tree_nodes[node_id] = node
            current.children.append(node)
            node.parent = current
            current = node
        
        self.solution_nodes.append(current)
    
    def _check_constraints(self, chrom: Chromosome) -> float:
        """檢查約束滿足程度"""
        violations = 0
        total_checks = 0
        
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
        
        # 列違反
        for col in range(self.N):
            for val in range(1, self.N + 1):
                if col_counts[col][val] > 1:
                    violations += col_counts[col][val] - 1
        
        # 宮違反
        for box_id in range(self.N):
            for val in range(1, self.N + 1):
                if box_counts[box_id][val] > 1:
                    violations += box_counts[box_id][val] - 1
        
        # 已知數字違反
        for (row, col), expected_val in self.known_map.items():
            perm_idx = chrom.genes[row]
            if perm_idx < len(self.row_perms[row]):
                actual_val = self.row_perms[row][perm_idx][col]
                if actual_val != expected_val:
                    violations += 1
        
        if total_checks == 0:
            return 0.0
        
        return max(0.0, 1.0 - violations / total_checks)
    
    def _calculate_diversity(self, chrom: Chromosome) -> float:
        """計算多樣性（與已知解的距離）"""
        if not self.solution_nodes:
            return 1.0
        
        max_distance = 0.0
        
        for sol_node in self.solution_nodes:
            distance = 0
            for row in range(self.N):
                chrom_perm_idx = chrom.genes[row]
                
                # 找到解節點的路徑
                current = sol_node
                while current and current.depth > 0:
                    if current.row == row:
                        sol_perm_idx = current.perm_idx
                        if chrom_perm_idx != sol_perm_idx:
                            distance += 1
                        break
                    current = current.parent
            
            max_distance = max(max_distance, distance / self.N)
        
        return max_distance
    
    def _evaluate_population(self, population: List[Chromosome]) -> List[Chromosome]:
        """評估種群"""
        for chrom in population:
            constraint_score = self._check_constraints(chrom)
            diversity_score = self._calculate_diversity(chrom)
            chrom.fitness = 0.7 * constraint_score + 0.3 * diversity_score
        
        # 精英選擇
        population.sort(key=lambda c: c.fitness, reverse=True)
        for i in range(min(self.elite_count, len(population))):
            population[i].is_elite = True
        
        return population
    
    def _tournament_selection(self, population: List[Chromosome]) -> Chromosome:
        """輪盤選擇"""
        k = 5
        tournament = random.sample(population, min(k, len(population)))
        return max(tournament, key=lambda c: c.fitness)
    
    def _crossover(self, p1: Chromosome, p2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """單點交叉"""
        if random.random() > self.crossover_rate:
            return Chromosome(genes=p1.genes.copy(), fitness=p1.fitness), \
                   Chromosome(genes=p2.genes.copy(), fitness=p2.fitness)
        
        point = random.randint(1, self.N - 1)
        c1 = Chromosome(genes=p1.genes[:point] + p2.genes[point:])
        c2 = Chromosome(genes=p2.genes[:point] + p1.genes[point:])
        return c1, c2
    
    def _mutate(self, chrom: Chromosome):
        """變異"""
        for i in range(self.N):
            if random.random() < self.mutation_rate:
                if self.row_perms[i]:
                    chrom.genes[i] = random.randint(0, len(self.row_perms[i]) - 1)
    
    def analyze_solution_space(self, known_solutions: List[List[List[int]]]) -> Dict:
        """分析解空間結構"""
        self.start_time = time.time()
        
        print("\n" + "="*70)
        print("博弈優化分析 - 解空間結構")
        print("="*70)
        
        # 1. 構建初始博弈樹
        self.build_initial_tree(known_solutions)
        
        # 2. 初始化種群
        population = self._initialize_population()
        
        # 3. 迭代優化
        max_generations = 30
        for gen in range(max_generations):
            self.stats['generations'] = gen + 1
            
            # 評估
            population = self._evaluate_population(population)
            
            # 記錄進度
            avg_fitness = sum(c.fitness for c in population) / len(population)
            max_fitness = max(c.fitness for c in population)
            self.stats['fitness_progression'].append({
                'generation': gen,
                'avg_fitness': round(avg_fitness, 4),
                'max_fitness': round(max_fitness, 4)
            })
            
            # 精英保留
            elites = [c for c in population if c.is_elite]
            
            # 交叉和變異
            offspring = []
            for i in range(0, len(population) - self.elite_count, 2):
                p1 = self._tournament_selection(population)
                p2 = self._tournament_selection(population)
                c1, c2 = self._crossover(p1, p2)
                self._mutate(c1)
                self._mutate(c2)
                offspring.extend([c1, c2])
            
            # 新一代
            population = elites + offspring
            population = population[:self.population_size]
            
            # 統計探索
            self.stats['explored_nodes'] += len(population)
            
            # 檢查高適應度解
            high_fitness_sols = [c for c in population if c.fitness > 0.9]
            if high_fitness_sols:
                self.stats['solutions_found'] += len(high_fitness_sols)
            
            elapsed = time.time() - self.start_time
            print(f"第 {gen+1:2d} 代: avg={avg_fitness:.4f}, max={max_fitness:.4f}, "
                  f"解={self.stats['solutions_found']}, 時間={elapsed:.1f}s")
            
            if elapsed > 300:  # 5分鐘限制
                break
        
        return self._generate_analysis_report()
    
    def _initialize_population(self) -> List[Chromosome]:
        """初始化種群"""
        population = []
        
        # 加入已知解
        for sol_node in self.solution_nodes:
            genes = []
            current = sol_node
            while current and current.depth > 0:
                genes.append((current.depth - 1, current.perm_idx))
                current = current.parent
            
            genes = [p for _, p in sorted(genes)]
            chrom = Chromosome(genes=genes, fitness=1.0, is_elite=True)
            population.append(chrom)
        
        # 隨機初始化
        while len(population) < self.population_size:
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
    
    def _generate_analysis_report(self) -> Dict:
        """生成分析報告"""
        elapsed = time.time() - self.start_time
        
        # 計算解空間結構
        solution_distance_matrix = self._compute_solution_distances()
        
        # 分析約束緊度
        constraint_analysis = self._analyze_constraint_density()
        
        report = {
            "method": "Game Optimization Analysis",
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": round(elapsed, 2),
            "parameters": {
                "population_size": self.population_size,
                "elite_count": self.elite_count,
                "mutation_rate": self.mutation_rate,
                "crossover_rate": self.crossover_rate
            },
            "statistics": {
                "generations_run": self.stats['generations'],
                "nodes_explored": self.stats['explored_nodes'],
                "solutions_found": self.stats['solutions_found'],
                "final_avg_fitness": round(
                    self.stats['fitness_progression'][-1]['avg_fitness'] 
                    if self.stats['fitness_progression'] else 0, 4
                ),
                "final_max_fitness": round(
                    self.stats['fitness_progression'][-1]['max_fitness']
                    if self.stats['fitness_progression'] else 0, 4
                )
            },
            "solution_space_structure": {
                "solution_count": len(self.solution_nodes),
                "avg_inter_solution_distance": solution_distance_matrix.get('avg_distance', 0),
                "min_inter_solution_distance": solution_distance_matrix.get('min_distance', 0),
                "max_inter_solution_distance": solution_distance_matrix.get('max_distance', 0),
                "solution_clusters": self._identify_clusters()
            },
            "constraint_analysis": constraint_analysis,
            "tree_structure": {
                "total_nodes": len(self.tree_nodes),
                "solution_leafs": len(self.solution_nodes),
                "branch_depth": self.N
            }
        }
        
        return report
    
    def _compute_solution_distances(self) -> Dict:
        """計算解之間的距離"""
        if len(self.solution_nodes) < 2:
            return {"avg_distance": 0, "min_distance": 0, "max_distance": 0}
        
        distances = []
        for i, sol1 in enumerate(self.solution_nodes):
            for j, sol2 in enumerate(self.solution_nodes):
                if i < j:
                    # 計算漢明距離
                    d = 0
                    for row in range(self.N):
                        # 找排列索引
                        p1 = self._get_solution_perm(sol1, row)
                        p2 = self._get_solution_perm(sol2, row)
                        if p1 != p2:
                            d += 1
                    distances.append(d / self.N)
        
        return {
            "avg_distance": round(sum(distances) / len(distances), 4) if distances else 0,
            "min_distance": round(min(distances), 4) if distances else 0,
            "max_distance": round(max(distances), 4) if distances else 0,
            "total_pairs": len(distances)
        }
    
    def _get_solution_perm(self, sol_node: TreeNode, row: int) -> Optional[int]:
        """獲取解節點某行的排列索引"""
        current = sol_node
        while current and current.depth > 0:
            if current.row == row:
                return current.perm_idx
            current = current.parent
        return None
    
    def _identify_clusters(self) -> List[Dict]:
        """識別解的簇（簡單版本）"""
        if len(self.solution_nodes) < 2:
            return []
        
        # 基於相似性分組
        clusters = []
        used = set()
        
        for i, sol in enumerate(self.solution_nodes):
            if i in used:
                continue
            
            cluster = [i]
            used.add(i)
            
            for j, other in enumerate(self.solution_nodes):
                if j in used:
                    continue
                
                # 計算距離
                d = 0
                for row in range(self.N):
                    p1 = self._get_solution_perm(sol, row)
                    p2 = self._get_solution_perm(other, row)
                    if p1 != p2:
                        d += 1
                
                if d / self.N < 0.5:  # 相似閾值
                    cluster.append(j)
                    used.add(j)
            
            clusters.append({
                "size": len(cluster),
                "members": cluster
            })
        
        return clusters
    
    def _analyze_constraint_density(self) -> Dict:
        """分析約束密度"""
        # 統計每行的有效排列數
        valid_counts = []
        for row in range(self.N):
            count = 0
            for idx in range(len(self.row_perms[row])):
                valid = True
                for col, val in enumerate(self.row_perms[row][idx]):
                    if (row, col) in self.known_map:
                        if self.known_map[(row, col)] != val:
                            valid = False
                            break
                if valid:
                    count += 1
            valid_counts.append(count)
        
        return {
            "min_valid_perms": min(valid_counts) if valid_counts else 0,
            "max_valid_perms": max(valid_counts) if valid_counts else 0,
            "avg_valid_perms": round(sum(valid_counts) / len(valid_counts), 1) if valid_counts else 0,
            "tightest_rows": sorted(enumerate(valid_counts), key=lambda x: x[1])[:3],
            "loosest_rows": sorted(enumerate(valid_counts), key=lambda x: x[1], reverse=True)[:3],
            "constraint_density": 1 - sum(valid_counts) / (16 ** 16) if valid_counts else 0
        }


def main():
    """主函數"""
    print("="*70)
    print("博弈優化框架 - 解空間結構分析")
    print("="*70)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 載入已知解
    known_solutions = []
    try:
        with open('solution_count_result.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            known_solutions = data.get('solutions', [])
    except FileNotFoundError:
        print("未找到解文件，使用空集")
    
    print(f"已知解數: {len(known_solutions)}")
    
    # 初始化分析器
    analyzer = GameOptimizationAnalyzer()
    
    # 執行分析
    report = analyzer.analyze_solution_space(known_solutions)
    
    # 保存結果
    output_file = "game_optimization_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n分析報告已保存至: {output_file}")
    
    # 匯總
    print(f"\n{'='*70}")
    print("分析完成")
    print(f"{'='*70}")
    print(f"執行時間: {report['execution_time_seconds']:.2f}秒")
    print(f"產生代數: {report['statistics']['generations_run']}")
    print(f"探索節點: {report['statistics']['nodes_explored']:,}")
    print(f"最終適應度: {report['statistics']['final_max_fitness']:.4f}")
    print(f"解空間距離: 平均{report['solution_space_structure']['avg_inter_solution_distance']:.4f}")
    
    return report


if __name__ == "__main__":
    main()
