#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證 92 已知數字是否存在唯一解
如果存在多解，繼續搜尋其他解答

修復版：正確的 CP-SAT 約束添加方式
"""

import json
import time
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

try:
    from ortools.sat.python import cp_model
except ImportError:
    print("❌ 請安裝 ortools: pip install ortools")
    import sys
    sys.exit(1)


def load_puzzle_config():
    """載入已知數字配置"""
    puzzle_path = Path("D:/2026/WPF_Sudoku/Sudoku_256/超級大數獨_box_size4.txt")
    with open(puzzle_path, 'r', encoding='utf-8') as f:
        puzzle_content = f.read()
    
    grid = [[0]*16 for _ in range(16)]
    row_labels = [chr(ord('A') + i) for i in range(16)]
    given_count = 0
    
    for m in re.finditer(r'行([A-P]) \[(.*?)\]', puzzle_content):
        label, vals_str = m.group(1), m.group(2)
        vals = [int(v.strip()) if v.strip()!='0' else 0 for v in vals_str.split(',')]
        idx = ord(label) - ord('A')
        grid[idx] = vals
        given_count += sum(1 for v in vals if v != 0)
    
    print(f"📊 已知數字統計: {given_count} 個")
    return grid, given_count


def verify_known_unique(grid: List[List[int]], given_count: int, 
                        max_solutions: int = 20):
    """
    使用 CP-SAT 驗證已知數字是否存在唯一解
    
    Args:
        grid: 包含已知數字的 16×16 網格
        given_count: 已知數字總數
        max_solutions: 最多搜尋的解數量
    
    Returns:
        驗證結果
    """
    print("\n" + "="*70)
    print(f"已知數字唯一性驗證（{given_count} 個已知數字）")
    print("="*70)
    
    # 確認已知數字
    given_cells = []
    for i in range(16):
        for j in range(16):
            if grid[i][j] != 0:
                given_cells.append((i, j, grid[i][j]))
    
    print(f"🔍 固定已知數字: {len(given_cells)} 個")
    
    # 建立 CP-SAT 模型
    model = cp_model.CpModel()
    
    # 變數：所有 256 個格子
    var_grid = [[model.NewIntVar(1, 16, f'grid[{i}][{j}]') 
                 for j in range(16)] for i in range(16)]
    
    # 固定已知數字
    for i, j, val in given_cells:
        model.Add(var_grid[i][j] == val)
    
    # 行約束：每行 1-16 互異
    for i in range(16):
        model.AddAllDifferent([var_grid[i][j] for j in range(16)])
    
    # 列約束：每列 1-16 互異
    for j in range(16):
        model.AddAllDifferent([var_grid[i][j] for i in range(16)])
    
    # 宮約束：4×4 宮格內 1-16 互異
    box_size = 4
    for band in range(4):
        for stack in range(4):
            box_vars = []
            for bi in range(box_size):
                for bj in range(box_size):
                    i = band * box_size + bi
                    j = stack * box_size + bj
                    box_vars.append(var_grid[i][j])
            model.AddAllDifferent(box_vars)
    
    # 解決方案收集器
    class SolutionCollector(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.solutions = []
            self.solution_count = 0
        
        def on_solution_callback(self):
            grid_sol = [[self.Value(var_grid[i][j]) for j in range(16)] 
                       for i in range(16)]
            self.solutions.append(grid_sol)
            self.solution_count += 1
            print(f"   ✅ 找到解 #{self.solution_count}")
            
            if self.solution_count >= max_solutions:
                self.StopSearch()
    
    collector = SolutionCollector()
    
    # 設定求解器
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 8
    solver.parameters.log_search_progress = False
    
    print("\n🔧 開始搜尋所有解...")
    start_time = time.time()
    
    # 設定解數量限制
    model.solution_limit = max_solutions
    
    status = solver.Solve(model, collector)
    elapsed = time.time() - start_time
    num_solutions = collector.solution_count
    
    print(f"\n📍 搜尋結果: 找到 {num_solutions} 個解，時間 = {elapsed:.2f}s")
    
    # 量子態判斷
    if num_solutions == 0:
        quantum_state = 'INFEASIBLE (無解)'
    elif num_solutions == 1:
        quantum_state = 'COLLAPSED (唯一解)'
    else:
        quantum_state = f'SUPERPOSITION (多解，{num_solutions} 個)'
    
    print(f"\n✨ 量子態: {quantum_state}")
    
    return {
        'status': solver.StatusName(status),
        'quantum_state': quantum_state,
        'num_solutions': num_solutions,
        'solutions': collector.solutions,
        'elapsed_time': elapsed,
        'given_count': given_count,
        'solution_limit': max_solutions
    }


def display_solution(grid: List[List[int]], title: str = "解", row_labels: List[str] = None):
    """顯示網格解"""
    if row_labels is None:
        row_labels = [chr(ord('A') + i) for i in range(16)]
    
    print(f"\n{title}:")
    print("-" * 50)
    for i, row in enumerate(grid):
        row_str = ' '.join(f'{v:2d}' for v in row)
        print(f"行{row_labels[i]:2s}: {row_str}")


def analyze_solution_diversity(solutions: List[List[List[int]]]) -> Dict:
    """分析解之間的多樣性"""
    if len(solutions) < 2:
        return {'avg_hamming_distance': 0, 'diversity_score': 0}
    
    total_distance = 0
    pair_count = 0
    
    for i in range(len(solutions)):
        for j in range(i+1, len(solutions)):
            distance = 0
            for r in range(16):
                for c in range(16):
                    if solutions[i][r][c] != solutions[j][r][c]:
                        distance += 1
            total_distance += distance
            pair_count += 1
    
    avg_distance = total_distance / max(1, pair_count)
    max_distance = 16 * 16
    diversity_score = avg_distance / max_distance
    
    return {
        'avg_hamming_distance': round(avg_distance, 2),
        'max_hamming_distance': max_distance,
        'diversity_score': round(diversity_score, 4),
        'pair_count': pair_count
    }


def find_differences(sol1: List[List[int]], sol2: List[List[int]]) -> List[Tuple]:
    """找出兩個解之間的差異位置"""
    diffs = []
    row_labels = [chr(ord('A') + i) for i in range(16)]
    
    for i in range(16):
        for j in range(16):
            if sol1[i][j] != sol2[i][j]:
                diffs.append((i, j, sol1[i][j], sol2[i][j], 
                             row_labels[i], row_labels[j]))
    
    return diffs


def main():
    """主函數"""
    # 載入已知數字
    grid, given_count = load_puzzle_config()
    
    # 顯示已知數字分布
    print("\n已知數字分布:")
    row_labels = [chr(ord('A') + i) for i in range(16)]
    for i in range(16):
        known_count = sum(1 for v in grid[i] if v != 0)
        print(f"行{row_labels[i]:2s}: {known_count:2d} 個已知數字")
    
    # 驗證唯一性（最多搜尋 20 個解）
    result = verify_known_unique(grid, given_count, max_solutions=20)
    
    # 保存結果
    output_path = Path("D:/2026/WPF_Sudoku/Sudoku_256/unique_verification_result.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        output = result.copy()
        if output['solutions']:
            # 只保存前 5 個解的網格資料（完整 16 行）
            output['solutions_sample'] = [
                sol for sol in output['solutions'][:5]
            ]
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 完整結果已保存: {output_path}")
    
    # 顯示結果總結
    print("\n" + "="*70)
    print("📋 驗證結果總結")
    print("="*70)
    print(f"量子態: {result['quantum_state']}")
    print(f"解數量: {result['num_solutions']}")
    print(f"搜尋時間: {result['elapsed_time']:.2f}秒")
    
    # 如果存在多解，分析多樣性
    if result['num_solutions'] >= 2:
        diversity = analyze_solution_diversity(result['solutions'])
        print(f"\n📊 多樣性分析:")
        print(f"   平均漢明距離: {diversity['avg_hamming_distance']}/{diversity['max_hamming_distance']}")
        print(f"   多樣性分數: {diversity['diversity_score']:.4f}")
        print(f"   解對數量: {diversity['pair_count']}")
    
    # 顯示所有找到的解（完整網格）
    if result['num_solutions'] >= 1:
        print("\n" + "="*70)
        print("📌 所有找到的解（完整 16×16 網格）")
        print("="*70)
        
        for idx, sol in enumerate(result['solutions']):
            display_solution(sol, title=f"解 #{idx+1}", row_labels=row_labels)
    
    # 如果多解，詳細分析差異
    if result['num_solutions'] >= 2:
        print("\n" + "="*70)
        print("🔍 多解差異詳細分析")
        print("="*70)
        
        # 解 1 vs 解 2 的差異
        diffs = find_differences(result['solutions'][0], result['solutions'][1])
        print(f"\n解 #1 vs 解 #2 的差異位置（共 {len(diffs)} 處）:")
        for i, j, v1, v2, rl, cj in diffs:
            print(f"   行{rl}列{j}: 解 1={v1:2d}, 解 2={v2:2d}")
        
        # 如果解數量 >= 3，也分析解 2 vs 解 3
        if result['num_solutions'] >= 3:
            diffs23 = find_differences(result['solutions'][1], result['solutions'][2])
            print(f"\n解 #2 vs 解 #3 的差異位置（共 {len(diffs23)} 處）:")
            for i, j, v1, v2, rl, cj in diffs23:
                print(f"   行{rl}列{j}: 解 2={v1:2d}, 解 3={v2:2d}")
    
    return result


if __name__ == '__main__':
    result = main()
