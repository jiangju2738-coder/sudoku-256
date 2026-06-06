#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
博弈優化框架 - 完整解空間分析
載入已知解，建立博弈樹，遺傳優化探索
"""

import json
import time
import random
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime


class SolutionSpaceAnalyzer:
    """解空間分析器"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16
        self.box_size = 4
        
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        self.valid_perm_indices: List[List[int]] = [[] for _ in range(self.N)]
        
        self.load_config(config_path)
        self.calc_valid_perms()
    
    def load_config(self, config_path: str):
        """載入配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'known_digits' in config:
            for clue in config['known_digits']:
                r, c = clue['row']-1, clue['col']-1
                self.known_map[(r, c)] = clue['value']
        
        for row in range(self.N):
            try:
                with open(f"A{row+1}_permutations.json", 'r', encoding='utf-8') as f:
                    self.row_perms[row] = json.load(f)
            except:
                pass
    
    def calc_valid_perms(self):
        """計算每行符合已知數字的排列"""
        for row in range(self.N):
            valid = []
            for idx, perm in enumerate(self.row_perms[row]):
                ok = True
                for col, val in enumerate(perm):
                    if (row, col) in self.known_map:
                        if self.known_map[(row, col)] != val:
                            ok = False
                            break
                if ok:
                    valid.append(idx)
            self.valid_perm_indices[row] = valid
        
        print("每行有效排列數:")
        for i in range(self.N):
            tight = "極緊" if len(self.valid_perm_indices[i]) < 200 else "緊" if len(self.valid_perm_indices[i]) < 1000 else "鬆"
            print(f"  第{i+1}行: {len(self.valid_perm_indices[i]):,} ({tight})")
    
    def dfs_search(self, limit: int = 1000, time_limit: int = 300) -> Dict:
        """DFS搜索找解"""
        start_time = time.time()
        solutions = []
        nodes = [0]
        
        # 按緊度排序行
        row_order = sorted(range(self.N), key=lambda r: len(self.valid_perm_indices[r]))
        
        # 列約束
        col_used = [set() for _ in range(self.N)]
        box_used = [set() for _ in range(self.N)]
        
        # 初始化已知數字約束
        for (r, c), v in self.known_map.items():
            col_used[c].add(v)
            box_used[(r//4)*4 + c//4].add(v)
        
        def search(depth: int):
            nodes[0] += 1
            
            elapsed = time.time() - start_time
            if len(solutions) >= limit or elapsed > time_limit:
                return
            
            if depth == self.N:
                # 重建解
                grid = []
                for r in range(self.N):
                    row_vals = []
                    for c in range(self.N):
                        if (r, c) in self.known_map:
                            row_vals.append(self.known_map[(r, c)])
                        else:
                            # 從列約束找唯一值
                            for v in range(1, 17):
                                if v in col_used[c]:
                                    # 檢查是否只出現一次
                                    count = sum(1 for rr in range(self.N) if v in col_used[rr])
                                    if count == 1:
                                        row_vals.append(v)
                                        break
                            else:
                                row_vals.append(0)
                    grid.append(row_vals)
                solutions.append(grid)
                
                if len(solutions) % 50 == 0:
                    print(f"  解 {len(solutions)}: 節點{nodes[0]:,}, {elapsed:.1f}s")
                return
            
            row = row_order[depth]
            
            for perm_idx in self.valid_perm_indices[row]:
                perm = self.row_perms[row][perm_idx]
                
                # 檢查是否與列/宮衝突
                ok = True
                applied = []
                for col, val in enumerate(perm):
                    if (row, col) in self.known_map:
                        continue
                    if val in col_used[col] or val in box_used[(row//4)*4 + col//4]:
                        ok = False
                        break
                    applied.append((col, val))
                
                if not ok:
                    continue
                
                # 應用
                for c, v in applied:
                    col_used[c].add(v)
                    box_used[(row//4)*4 + c//4].add(v)
                
                search(depth + 1)
                
                # 回溯
                for c, v in applied:
                    col_used[c].remove(v)
                    box_used[(row//4)*4 + c//4].remove(v)
                
                if len(solutions) >= limit or time.time() - start_time > time_limit:
                    return
        
        print(f"\nDFS搜索開始 (上限{limit}解, 時限{time_limit}s)...")
        search(0)
        
        elapsed = time.time() - start_time
        return {
            'solutions': solutions,
            'count': len(solutions),
            'nodes': nodes[0],
            'time': round(elapsed, 2),
            'limit_reached': len(solutions) >= limit
        }
    
    def genetic_search(self, generations: int = 50) -> Dict:
        """遺傳算法搜索"""
        pop_size = 100
        elite_count = 10
        
        # 初始化種群
        population = []
        for _ in range(pop_size):
            genes = []
            for row in range(self.N):
                if self.valid_perm_indices[row]:
                    genes.append(random.choice(self.valid_perm_indices[row]))
                else:
                    genes.append(0)
            population.append(genes)
        
        fitness_history = []
        
        for gen in range(generations):
            # 評估
            fitnesses = []
            for genes in population:
                violations = 0
                col_counts = defaultdict(lambda: defaultdict(int))
                box_counts = defaultdict(lambda: defaultdict(int))
                
                for row, perm_idx in enumerate(genes):
                    perm = self.row_perms[row][perm_idx]
                    for col, val in enumerate(perm):
                        col_counts[col][val] += 1
                        box_counts[(row//4)*4 + col//4][val] += 1
                
                for c in range(self.N):
                    for v in range(1, 17):
                        if col_counts[c][v] > 1:
                            violations += col_counts[c][v] - 1
                
                for b in range(self.N):
                    for v in range(1, 17):
                        if box_counts[b][v] > 1:
                            violations += box_counts[b][v] - 1
                
                fit = max(0, 1 - violations / (self.N * 16))
                fitnesses.append(fit)
            
            avg_fit = sum(fitnesses) / len(fitnesses)
            max_fit = max(fitnesses)
            fitness_history.append({'gen': gen, 'avg': round(avg_fit, 4), 'max': round(max_fit, 4)})
            
            if gen % 10 == 0:
                print(f"  代 {gen}: avg={avg_fit:.4f}, max={max_fit:.4f}")
            
            # 精英保留
            sorted_pop = sorted(zip(population, fitnesses), key=lambda x: x[1], reverse=True)
            elites = [p for p, f in sorted_pop[:elite_count]]
            
            # 交叉變異
            new_pop = elites.copy()
            while len(new_pop) < pop_size:
                # 選擇
                i1, i2 = random.sample(range(len(population)), 2)
                p1, p2 = population[i1], population[i2]
                
                # 交叉
                pt = random.randint(1, self.N-1)
                c1 = p1[:pt] + p2[pt:]
                c2 = p2[:pt] + p1[pt:]
                
                # 變異
                for c in [c1, c2]:
                    for i in range(self.N):
                        if random.random() < 0.1 and self.valid_perm_indices[i]:
                            c[i] = random.choice(self.valid_perm_indices[i])
                
                new_pop.extend([c1, c2])
            
            population = new_pop[:pop_size]
        
        return {
            'fitness_progression': fitness_history,
            'best_fitness': fitness_history[-1]['max'] if fitness_history else 0,
            'avg_fitness': fitness_history[-1]['avg'] if fitness_history else 0
        }


def main():
    print("="*70)
    print("博弈優化框架 - 解空間結構分析")
    print("="*70)
    print(f"開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    analyzer = SolutionSpaceAnalyzer()
    
    # DFS搜索
    dfs_result = analyzer.dfs_search(limit=100, time_limit=120)
    
    # 遺傳優化
    genetic_result = analyzer.genetic_search(generations=30)
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'dfs_search': {
            'solutions_found': dfs_result['count'],
            'nodes_explored': dfs_result['nodes'],
            'time_seconds': dfs_result['time'],
            'limit_reached': dfs_result['limit_reached']
        },
        'genetic_optimization': genetic_result,
        'constraint_analysis': {
            'valid_perms_per_row': [len(analyzer.valid_perm_indices[i]) for i in range(16)]
        }
    }
    
    with open("game_space_analysis.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n" + "="*70)
    print("結果")
    print("="*70)
    print(f"DFS解數: {dfs_result['count']}")
    print(f"遺傳最佳適應度: {genetic_result['best_fitness']:.4f}")
    
    return result


if __name__ == "__main__":
    main()
