#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CP-SAT SolutionCollector - 收集至1000個解
使用Google OR-Tools 9.15
"""

import json
import time
from typing import List, Dict, Tuple, Optional
from ortools.sat.python import cp_model
import threading
from datetime import datetime


class SudokuCPModel(cp_model.CpSolver):
    """CP-SAT Sudoku Solver"""
    
    def __init__(self):
        super().__init__()
        self.solution_count = 0
        self.solutions = []
        self.limit = 1000
        self.start_time = None
        self.solution_callback = None


class SudokuSolutionCollector(cp_model.CpSolverSolutionCallback):
    """Solution Collector for Sudoku"""
    
    def __init__(self, x_vars: Dict, n_rows: int = 16, n_cols: int = 16, 
                 n_vals: int = 16, limit: int = 1000):
        super().__init__()
        self.x_vars = x_vars
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.n_vals = n_vals
        self.limit = limit
        self.solutions = []
        self.solution_count = 0
        self.nodes_explored = 0
        self.start_time = time.time()
    
    def on_solution_callback(self):
        """回調處理每個找到的解"""
        if self.solution_count >= self.limit:
            self.StopSearch()
            return
        
        # 重建當前解
        solution_grid = []
        for row in range(self.n_rows):
            row_vals = []
            for col in range(self.n_cols):
                for val in range(1, self.n_vals + 1):
                    if self.Value(self.x_vars[row, col, val]):
                        row_vals.append(val)
                        break
                else:
                    row_vals.append(0)  # 應不會發生
            solution_grid.append(row_vals)
        
        self.solutions.append(solution_grid)
        self.solution_count += 1
        
        # 進度報告
        if self.solution_count % 50 == 0 or self.solution_count == 1:
            elapsed = time.time() - self.start_time
            nodes = self.NumNodes()
            print(f"  解 {self.solution_count}: 節點={nodes:,}, 時間={elapsed:.1f}s, "
                  f"速率={self.solution_count/elapsed:.1f}解/秒")
    
    def get_statistics(self) -> Dict:
        """獲取統計信息"""
        elapsed = time.time() - self.start_time
        return {
            "solutions_found": self.solution_count,
            "nodes_explored": self.NumNodes(),
            "time_seconds": round(elapsed, 2),
            "solutions_per_second": round(self.solution_count / max(elapsed, 0.001), 2),
            "limit_reached": self.solution_count >= self.limit
        }


def load_config() -> Dict:
    """載入配置"""
    with open('sudoku_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    # 兼容兩種格式
    if 'known_digits' in config and 'clues' not in config:
        config['clues'] = config['known_digits']
    return config


def load_permutations() -> List[List[List[int]]]:
    """載入符闔排列"""
    row_perms = []
    for i in range(16):
        try:
            with open(f'A{i+1}_permutations.json', 'r', encoding='utf-8') as f:
                perms = json.load(f)
            row_perms.append(perms)
        except FileNotFoundError:
            row_perms.append([])
    return row_perms


def build_cpsat_model(config: Dict, row_perms: List[List[List[int]]]) -> Tuple[cp_model.CpModel, Dict]:
    """構建CP-SAT模型"""
    model = cp_model.CpModel()
    x_vars = {}
    
    n = 16
    box_size = 4
    
    # === 創建變數 ===
    for row in range(n):
        for col in range(n):
            for val in range(1, n + 1):
                x_vars[row, col, val] = model.NewBoolVar(f'x_{row}_{col}_{val}')
    
    # === 基本約束：每個位置恰好一個值 ===
    for row in range(n):
        for col in range(n):
            model.AddExactlyOne(
                x_vars[row, col, val] for val in range(1, n + 1)
            )
    
    # === 行約束：每個值恰好出現一次 ===
    for row in range(n):
        for val in range(1, n + 1):
            model.AddExactlyOne(
                x_vars[row, col, val] for col in range(n)
            )
    
    # === 列約束：每個值恰好出現一次 ===
    for col in range(n):
        for val in range(1, n + 1):
            model.AddExactlyOne(
                x_vars[row, col, val] for row in range(n)
            )
    
    # === 宮約束：每個值恰好出現一次 ===
    for box_r in range(box_size):
        for box_c in range(box_size):
            for val in range(1, n + 1):
                cells = []
                for dr in range(box_size):
                    for dc in range(box_size):
                        r = box_r * box_size + dr
                        c = box_c * box_size + dc
                        cells.append(x_vars[r, c, val])
                model.AddExactlyOne(cells)
    
    # === 已知數字約束 ===
    clues = config.get('clues', [])
    for clue in clues:
        row, col, val = clue['row'], clue['col'], clue['value']
        # 轉換為0基索引
        row_0 = row - 1 if row > 0 else row
        col_0 = col - 1 if col > 0 else col
        if 0 <= row_0 < n and 0 <= col_0 < n and 1 <= val <= n:
            model.Add(x_vars[row_0, col_0, val] == 1)
        else:
            print(f"  警告: 無效約束 ({row}, {col}, {val})")
    
    # === 符闔排列約束 ===
    for row in range(n):
        perms = row_perms[row]
        if not perms:
            continue
        
        # 為每個排列創建選擇變數
        perm_bools = []
        for perm_idx in range(len(perms)):
            pb = model.NewBoolVar(f'perm_{row}_{perm_idx}')
            perm_bools.append(pb)
        
        # 恰好選擇一個排列
        model.AddExactlyOne(perm_bools)
        
        # 如果選擇排列i，則該行必須等於該排列
        for perm_idx, perm in enumerate(perms):
            for col, val in enumerate(perm):
                model.Add(x_vars[row, col, val] == 1).OnlyEnforceIf(perm_bools[perm_idx])
    
    return model, x_vars


def main():
    """主函數"""
    print("="*70)
    print("CP-SAT SolutionCollector - 收集至1000個解")
    print("="*70)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 載入數據
    print("\n載入配置...")
    config = load_config()
    print(f"  已知數字: {len(config.get('clues', []))} 個")
    
    print("載入符闔排列...")
    row_perms = load_permutations()
    total_perms = sum(len(p) for p in row_perms)
    print(f"  總排列數: {total_perms:,}")
    
    # 構建模型
    print("\n構建CP-SAT模型...")
    model, x_vars = build_cpsat_model(config, row_perms)
    
    num_bool_vars = model.NumVariables()
    print(f"  布林變數: {num_bool_vars:,}")
    
    # 設置求解器
    solver = SudokuCPModel()
    solver.parameters.max_time_in_seconds = 7200  # 2小時
    solver.parameters.num_search_workers = 8
    solver.parameters.enumerate_all_solutions = True
    
    # 創建回調
    callback = SudokuSolutionCollector(x_vars, limit=1000)
    
    # 搜索
    print("\n開始搜索...")
    print("-"*70)
    
    solver.Solve(model, callback)
    
    elapsed = time.time() - solver.start_time if hasattr(solver, 'start_time') else None
    
    # 收集結果
    stats = callback.get_statistics()
    
    print("\n" + "="*70)
    print("搜索完成")
    print("="*70)
    
    result = {
        "method": "CP-SAT SolutionCollector",
        "timestamp": datetime.now().isoformat(),
        "statistics": stats,
        "model_info": {
            "num_variables": num_bool_vars,
            "config_clues": len(config.get('clues', [])),
            "total_permutations": total_perms
        },
        "solutions": callback.solutions[:10]  # 保存前10個
    }
    
    # 保存結果
    output_file = "cpsat_1000_solutions.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果已保存至: {output_file}")
    print(f"\n【結果摘要】")
    print(f"  找到解數: {stats['solutions_found']}")
    print(f"  探索節點: {stats['nodes_explored']:,}")
    print(f"  搜索時間: {stats['time_seconds']:.2f} 秒")
    print(f"  搜索速率: {stats['solutions_per_second']:.2f} 解/秒")
    print(f"  達到上限: {'是' if stats['limit_reached'] else '否'}")
    
    return result


if __name__ == "__main__":
    main()
