#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CP-SAT SolutionCollector - 符闔數獨精確計數
使用Google OR-Tools進行約束規劃和_solution_limit=1000
"""

import json
import time
from typing import List, Tuple, Dict, Optional
from ortools.sat.python import cp_model


class CPSATCollector:
    """CP-SAT Solution Collector for 16×16 Sudoku"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16
        self.box_size = 4
        self.solution_limit = 1000
        
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        self.model: Optional[cp_model.CpModel] = None
        self.solver: Optional[cp_model.CpSolver] = None
        self.solutions: List[List[List[int]]] = []
        self.solution_count = 0
        
        self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """載入配置"""
        print(f"載入配置: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 載入已知數字
        if 'clues' in config:
            for clue in config['clues']:
                row, col = clue['row'], clue['col']
                val = clue['value']
                self.known_map[(row, col)] = val
        
        # 載入符闔排列
        for row in range(self.N):
            perm_file = f"A{row+1}_permutations.json"
            print(f"載入 {perm_file}...")
            try:
                with open(perm_file, 'r', encoding='utf-8') as f:
                    perms = json.load(f)
                self.row_perms[row] = perms
            except FileNotFoundError:
                print(f"警告: {perm_file} 不存在")
    
    def build_model(self):
        """構建CP-SAT模型"""
        self.model = cp_model.CpModel()
        
        # 創建變數：x[row][col] = 1 表示該位置填 val
        # 使用符闔排列約束而不是傳統數獨約束
        self.x = {}
        
        for row in range(self.N):
            for col in range(self.N):
                self.x[row, col] = self.model.NewIntVar(
                    1, self.N, f'x_{row}_{col}'
                )
        
        # 符闔排列約束：每行必須是一個有效排列
        for row in range(self.N):
            valid_perms = self.row_perms[row]
            if not valid_perms:
                raise ValueError(f"第 {row+1} 行無有效排列")
            
            # 創建排列選擇變數
            perm_vars = []
            for perm_idx, perm in enumerate(valid_perms):
                # 如果選擇這個排列，則該行的每個位置填對應的值
                # 使用邏輯或約束
                pass
        
        # 傳統數獨約束（作為輔助）
        # 1. 每行每個數字出現一次
        for row in range(self.N):
            self.model.AddAllDifferent([self.x[row, col] for col in range(self.N)])
        
        # 2. 每列每個數字出現一次
        for col in range(self.N):
            self.model.AddAllDifferent([self.x[row, col] for row in range(self.N)])
        
        # 3. 每宮每個數字出現一次
        for box_row in range(self.box_size):
            for box_col in range(self.box_size):
                box_cells = []
                for dr in range(self.box_size):
                    for dc in range(self.box_size):
                        r = box_row * self.box_size + dr
                        c = box_col * self.box_size + dc
                        box_cells.append(self.x[r, c])
                self.model.AddAllDifferent(box_cells)
        
        # 4. 已知數字約束
        for (row, col), val in self.known_map.items():
            self.model.Add(self.x[row, col] == val)
        
        # 5. 符闔排列約束（精確版本）
        # 每行必須是A1-A16中的一個排列
        for row in range(self.N):
            valid_perms = self.row_perms[row]
            
            # 創建布爾變數表示選擇哪個排列
            perm_bools = []
            for perm_idx in range(len(valid_perms)):
                pb = self.model.NewBoolVar(f'p_{row}_{perm_idx}')
                perm_bools.append(pb)
            
            # 恰好選擇一個排列
            self.model.AddExactlyOne(perm_bools)
            
            # 如果選擇排列i，則該行必須等於該排列
            for perm_idx, perm in enumerate(valid_perms):
                for col, val in enumerate(perm):
                    # 如果perm_bool[perm_idx]為True，則x[row][col] = val
                    self.model.Add(self.x[row, col] == val).OnlyEnforceIf(perm_bools[perm_idx])
        
        print("CP-SAT模型構建完成")
    
    def collect_solutions(self):
        """收集所有解至solution_limit"""
        self.build_model()
        
        self.solver = cp_model.CpSolver()
        
        # 配置求解器
        self.solver.parameters.max_time_in_seconds = 3600  # 1小時
        self.solver.parameters.num_search_workers = 8  # 使用8個工作線程
        self.solver.parameters.enumerate_all_solutions = True
        
        start_time = time.time()
        
        # 自定義Solution Collector
        collector = SolutionCollector(self.model, self.solution_limit)
        self.solver.parameters.solution_hint = None
        
        # 使用Callback收集解
        class SolutionCallback(cp_model.CpSolverSolutionCallback):
            def __init__(self, collector, limit):
                super().__init__()
                self.collector = collector
                self.limit = limit
                self.solution_count = 0
            
            def on_solution_callback(self):
                if self.solution_count >= self.limit:
                    self.StopSearch()
                    return
                
                solution = []
                for row in range(self.N):
                    row_vals = []
                    for col in range(self.N):
                        row_vals.append(self.Value(self.collector.x[row, col]))
                    solution.append(row_vals)
                
                self.collector.solutions.append(solution)
                self.solution_count += 1
                
                if self.solution_count % 100 == 0:
                    elapsed = time.time() - start_time
                    print(f"已收集 {self.solution_count} 個解，耗時 {elapsed:.1f}s")
        
        callback = SolutionCallback(self, self.solution_limit)
        self.solver.Search(self.model, callback)
        
        elapsed = time.time() - start_time
        
        self.solution_count = len(self.solutions)
        
        return {
            "total_solutions": self.solution_count,
            "statistics": {
                "time_seconds": round(elapsed, 2),
                "solution_limit": self.solution_limit,
                "search_complete": self.solution_count < self.solution_limit
            }
        }


class SolutionCollector:
    """Solution Collector Helper"""
    def __init__(self, model: cp_model.CpModel, limit: int):
        self.model = model
        self.limit = limit
        self.x = {}  # Will be populated by build_model


class SolutionCollectorCallback(cp_model.CpSolverSolutionCallback):
    """內建Solution Collector Callback"""
    def __init__(self, x_vars: Dict, limit: int):
        super().__init__()
        self.x_vars = x_vars
        self.limit = limit
        self.solutions = []
        self.solution_count = 0
    
    def on_solution_callback(self):
        if self.solution_count >= self.limit:
            self.StopSearch()
            return
        
        # 收集當前解
        solution = []
        for row in range(16):
            row_vals = []
            for col in range(16):
                row_vals.append(self.Value(self.x_vars[row, col]))
            solution.append(row_vals)
        
        self.solutions.append(solution)
        self.solution_count += 1
        
        if self.solution_count % 100 == 0:
            print(f"已收集 {self.solution_count} 個解")


def main():
    """主函數"""
    print("=" * 60)
    print("CP-SAT SolutionCollector - 符闔數獨精確計數")
    print("=" * 60)
    
    collector = CPSATCollector("sudoku_config.json")
    result = collector.collect_solutions()
    
    # 保存結果
    output_file = "cpsat_collection_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果已保存至: {output_file}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


if __name__ == "__main__":
    main()
