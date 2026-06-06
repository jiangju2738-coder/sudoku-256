#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CP-SAT 隱式約束求解器 - 符闔數獨
使用 AddAllowedAssignments 替代顯式排列變數，避免111萬變數
"""

import json
import time
from typing import List, Dict, Tuple
from ortools.sat.python import cp_model
from datetime import datetime


class CPSATImplicitSolver:
    """CP-SAT 隱式約束求解器"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16
        self.box_size = 4
        self.solution_limit = 1000
        
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        self.model: cp_model.CpModel = None
        self.x = {}  # x[row][col] = 值 (1-16)
        
        self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """載入配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'known_digits' in config:
            for clue in config['known_digits']:
                r, c, v = clue['row']-1, clue['col']-1, clue['value']
                self.known_map[(r, c)] = v
        elif 'clues' in config:
            for clue in config['clues']:
                r, c, v = clue['row']-1, clue['col']-1, clue['value']
                self.known_map[(r, c)] = v
        
        for row in range(self.N):
            try:
                with open(f"A{row+1}_permutations.json", 'r', encoding='utf-8') as f:
                    self.row_perms[row] = json.load(f)
            except FileNotFoundError:
                pass
        
        print(f"  已知數字: {len(self.known_map)} 個")
        print(f"  排列總數: {sum(len(p) for p in self.row_perms):,}")
    
    def build_model(self):
        """構建模型（隱式約束）"""
        self.model = cp_model.CpModel()
        n = self.N
        
        # === 創建變數：x[row][col] = 值 ===
        print("創建位置值變數...")
        for row in range(n):
            for col in range(n):
                self.x[row, col] = self.model.NewIntVar(1, n, f'x_{row}_{col}')
        
        # === 基本數獨約束 ===
        print("添加基本約束...")
        
        # 每行 AllDifferent
        for row in range(n):
            self.model.AddAllDifferent([self.x[row, col] for col in range(n)])
        
        # 每列 AllDifferent
        for col in range(n):
            self.model.AddAllDifferent([self.x[row, col] for row in range(n)])
        
        # 每宮 AllDifferent
        for br in range(self.box_size):
            for bc in range(self.box_size):
                cells = []
                for dr in range(self.box_size):
                    for dc in range(self.box_size):
                        r = br * self.box_size + dr
                        c = bc * self.box_size + dc
                        cells.append(self.x[r, c])
                self.model.AddAllDifferent(cells)
        
        # === 已知數字 ===
        print("添加已知數字...")
        for (row, col), val in self.known_map.items():
            self.model.Add(self.x[row, col] == val)
        
        # === 符闔排列約束（隱式）===
        print("添加符闔排列約束（隱式）...")
        
        for row in range(n):
            perms = self.row_perms[row]
            if not perms:
                continue
            
            # AddAllowedAssignments: 該行必須是某個排列
            # 每個排列是一個元組 (val_0, val_1, ..., val_15)
            allowed = []
            for perm in perms:
                allowed.append(tuple(perm))
            
            # 添加約束：該行的值組合必須在允許列表中
            self.model.AddAllowedAssignments(
                [self.x[row, col] for col in range(n)],
                allowed
            )
            
            if len(perms) > 10000:
                print(f"  第{row+1}行: {len(perms):,} 排列（隱式約束）")
        
        print("模型構建完成!")
    
    def collect_solutions(self):
        """收集所有解"""
        self.build_model()
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 3600
        solver.parameters.num_search_workers = 8
        solver.parameters.enumerate_all_solutions = True
        
        class SolutionCallback(cp_model.CpSolverSolutionCallback):
            def __init__(self, x_vars, n, limit):
                super().__init__()
                self.x_vars = x_vars
                self.n = n
                self.limit = limit
                self.solutions = []
                self.count = 0
                self.start_time = time.time()
            
            def on_solution_callback(self):
                if self.count >= self.limit:
                    self.StopSearch()
                    return
                
                grid = []
                for row in range(self.n):
                    row_vals = [self.Value(self.x_vars[row, col]) for col in range(self.n)]
                    grid.append(row_vals)
                
                self.solutions.append(grid)
                self.count += 1
                
                if self.count % 50 == 0:
                    elapsed = time.time() - self.start_time
                    print(f"  解 {self.count}: {elapsed:.1f}s ({self.count/elapsed:.1f}解/秒)")
            
            def get_stats(self):
                elapsed = time.time() - self.start_time
                return {
                    'solutions_found': self.count,
                    'time_seconds': round(elapsed, 2),
                    'limit_reached': self.count >= self.limit
                }
        
        callback = SolutionCallback(self.x, self.N, self.solution_limit)
        
        print("\n開始搜索...")
        print("-"*60)
        solver.Solve(self.model, callback)
        
        stats = callback.get_stats()
        
        return {
            'solutions': callback.solutions[:10],
            'statistics': stats
        }


def main():
    print("="*70)
    print("CP-SAT 隱式約束求解器 - 收集至1000解")
    print("="*70)
    print(f"開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    solver = CPSATImplicitSolver()
    result = solver.collect_solutions()
    
    # 保存結果
    with open("cpsat_implicit_result.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    stats = result['statistics']
    print("\n" + "="*70)
    print("結果")
    print("="*70)
    print(f"解數量: {stats['solutions_found']}")
    print(f"搜索時間: {stats['time_seconds']:.2f} 秒")
    print(f"達到上限: {'是' if stats['limit_reached'] else '否'}")
    
    return result


if __name__ == "__main__":
    main()
