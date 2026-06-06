#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V91: 初始92錨點 + 終局盤完整P行符闔組闔排列
求解器：CP-SAT完整解空間探索
"""

import json
from datetime import datetime
from ortools.sat.python import cp_model

# === P行終局數據 ===
# 來源: V86匯總數據
INITIAL_PUZZLE = {
    'A': [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8],
    'B': [0,12,0,0, 3,0,9,0, 6,0,5,4, 2,0,1,0],
    'C': [0,0,14,0, 0,2,0,8, 0,0,0,0, 0,0,0,0],
    'D': [0,4,0,13, 7,0,1,0, 0,0,0,11, 0,12,0,0],
    'E': [0,0,0,0, 13,0,0,0, 0,5,0,0, 4,0,0,0],
    'F': [0,8,0,0, 15,0,4,3, 0,9,0,0, 0,13,0,12],
    'G': [14,0,4,6, 0,0,12,0, 2,0,0,0, 0,3,0,0],
    'H': [0,13,0,0, 0,5,0,9, 0,0,14,6, 0,0,16,0],
    'I': [13,0,0,2, 0,11,0,0, 14,0,0,7, 0,15,0,3],
    'J': [0,5,0,0, 0,0,0,0, 0,0,16,0, 8,0,7,0],
    'K': [1,0,6,0, 5,0,0,2, 0,3,0,0, 9,0,0,0],
    'L': [0,0,0,4, 0,16,14,0, 0,0,12,5, 0,0,0,1],
    'M': [15,0,0,0, 12,0,0,0, 5,1,0,3, 0,6,0,7],
    'N': [0,0,9,0, 0,6,0,0, 13,0,0,15, 0,0,3,0],
    'O': [0,1,0,0, 9,0,0,15, 0,0,2,8, 0,5,0,0],
    'P': [0,0,2,0, 0,0,5,0, 0,14,0,0, 1,0,10,15]
}

# P行完整終局符闔組闔排列
P_ROW_FINAL = [8, 3, 2, 12, 16, 13, 5, 4, 7, 14, 6, 9, 1, 11, 10, 15]

# 符闔排列數據（V89 驗證總數 1,360,849）
PERM_STATS = {
    'A': 8731, 'B': 902, 'C': 656777, 'D': 1980,
    'E': 633271, 'F': 359, 'G': 2356, 'H': 4782,
    'I': 164, 'J': 28984, 'K': 2972, 'L': 620,
    'M': 484, 'N': 10668, 'O': 5990, 'P': 1809
}


def count_anchors(row):
    """計算行錨點數"""
    return sum(1 for x in row if x != 0)


def count_total_anchors(puzzle):
    """計算總錨點數"""
    return sum(count_anchors(row) for row in puzzle.values())


def create_puzzle_with_p_row(initial, p_row_final):
    """創建附加載P行終局的謎盤"""
    puzzle = {row: list(initial[row]) for row in initial}
    # 用P行終局填補P行空位
    for i, val in enumerate(p_row_final):
        puzzle['P'][i] = val
    return puzzle


def solve_with_cp_sat(puzzle):
    """CP-SAT求解"""
    model = cp_model.CpModel()
    
    # 創建變量
    cells = {}
    for row_idx, row in enumerate('ABCDEFGHIJKLMNOP'):
        for col_idx in range(16):
            val = puzzle[row][col_idx]
            if val != 0:
                # 已鎖定值，直接賦值
                var = model.NewIntVar(val, val, f'{row}{col_idx}')
                model.Add(var == val)
            else:
                # 未確定值，創建變量
                var = model.NewIntVar(1, 16, f'{row}{col_idx}')
            cells[(row, col_idx)] = var
    
    # 行約束 (AllDifferent)
    for row in 'ABCDEFGHIJKLMNOP':
        model.AddAllDifferent([cells[(row, col)] for col in range(16)])
    
    # 列約束 (AllDifferent)
    for col in range(16):
        model.AddAllDifferent([cells[(row, col)] for row in 'ABCDEFGHIJKLMNOP'])
    
    # 宮約束 (4x4 subgrids)
    for box_row in range(4):
        for box_col in range(4):
            cells_in_box = []
            for dr in range(4):
                for dc in range(4):
                    row = 'ABCDEFGHIJKLMNOP'[box_row * 4 + dr]
                    col = box_col * 4 + dc
                    cells_in_box.append(cells[(row, col)])
            model.AddAllDifferent(cells_in_box)
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0  # 5分鐘限時
    solver.parameters.num_search_workers = 8
    
    print(f"開始CP-SAT求解...")
    print(f"  錨點數: {count_total_anchors(puzzle)}")
    print(f"  P行: 完整鎖定（16錨點）")
    
    status = solver.Solve(model)
    
    return status, solver, cells


def get_solution(cells, solver):
    """提取解盤"""
    solution = {}
    for row in 'ABCDEFGHIJKLMNOP':
        solution[row] = []
        for col in range(16):
            solution[row].append(solver.Value(cells[(row, col)]))
    return solution


def verify_p_row_match(solution, p_row_final):
    """驗證P行是否匹配終局"""
    return solution['P'] == p_row_final


def main():
    print("=" * 70)
    print("V91: 初始92錨點 + 終局盤完整P行符闔組闔排列")
    print("=" * 70)
    
    # 錨點統計
    initial_anchors = count_total_anchors(INITIAL_PUZZLE)
    p_row_anchor_count = count_anchors(INITIAL_PUZZLE['P'])  # 初始P行錨點
    p_row_final_count = 16  # 終局P行16錨點
    p_row_increment = p_row_final_count - p_row_anchor_count
    
    print(f"\n[錨點統計]:")
    print(f"  初始盤錨點: {initial_anchors}")
    print(f"  P行初始錨點: {p_row_anchor_count}")
    print(f"  P行終局錨點: {p_row_final_count}")
    print(f"  P行增量錨點: {p_row_increment}")
    print(f"  總錨點數: {initial_anchors + p_row_increment} = {initial_anchors} + {p_row_increment}")
    
    print(f"\n[P行數據]:")
    print(f"  P行初始: {INITIAL_PUZZLE['P']}")
    print(f"  P行終局: {P_ROW_FINAL}")
    
    # 創建謎盤
    puzzle = create_puzzle_with_p_row(INITIAL_PUZZLE, P_ROW_FINAL)
    
    # 驗證P行錨點是否一致
    print(f"\n[P行錨點一致性檢查]:")
    consistent = True
    for i in range(16):
        init_val = INITIAL_PUZZLE['P'][i]
        final_val = P_ROW_FINAL[i]
        if init_val != 0:
            if init_val == final_val:
                print(f"  [{i}] {init_val} = {final_val} [OK] (保持)")
            else:
                print(f"  [{i}] {init_val} != {final_val} [X] (衝突!)")
                consistent = False
        else:
            print(f"  [{i}] {init_val} -> {final_val} (新增)")
    
    if not consistent:
        print(f"\n[X] P行終局與初始盤存在位置衝突，無法求解！")
        return
    
    print(f"\n[OK] P行錨點位置一致，開始求解...")
    
    # 求解
    status, solver, cells = solve_with_cp_sat(puzzle)
    
    # 結果分析
    print(f"\n{'=' * 70}")
    print(f"[求解結果]")
    print(f"{'=' * 70}")
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        solution = get_solution(cells, solver)
        
        # 驗證P行匹配
        p_match = verify_p_row_match(solution, P_ROW_FINAL)
        print(f"\n  狀態: OPTIMAL (找到解)")
        match_text = "[YES]" if p_match else "[NO]"
        print(f"  P行匹配終局: {match_text}")
        print(f"  P行解盤: {solution['P']}")
        print(f"  P行終局: {P_ROW_FINAL}")
        
        # 顯示完整解盤
        print(f"\n[解盤]:")
        print(f"  行序: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15")
        for row in 'ABCDEFGHIJKLMNOP':
            markers = "   "
            for i in range(16):
                if row == 'P' and i < 16:
                    markers += f" *{solution[row][i]:2d} "
                else:
                    markers += f" {solution[row][i]:2d} "
            marker = "*" if row == 'P' else " "
            print(f"  行{row}: {markers[1:]} <-{marker}")
        
        # 計算P行增量位置
        p_increment_positions = []
        for i in range(16):
            if INITIAL_PUZZLE['P'][i] == 0:
                p_increment_positions.append(i)
        
        # 輸出JSON
        result = {
            "version": "V91",
            "timestamp": datetime.now().isoformat(),
            "puzzle_type": "符闔數獨 16×16",
            "initial_anchors": initial_anchors,
            "row_locked": "P",
            "row_perm_count": PERM_STATS['P'],
            "total_anchors": initial_anchors + p_row_increment,
            "status": "OPTIMAL",
            "p_row_match": p_match,
            "p_increment_positions": p_increment_positions,
            "solution": solution
        }
        
    elif status == cp_model.INFEASIBLE:
        print(f"\n  狀態: INFEASIBLE (無解)")
        print(f"  P行終局排列在符闔集合中存在，但與初始盤存在列約束硬衝突")
        print(f"  耗時: {solver.UserTime():.3f}秒")
        
        result = {
            "version": "V91",
            "timestamp": datetime.now().isoformat(),
            "puzzle_type": "符闔數獨 16×16",
            "initial_anchors": initial_anchors,
            "row_locked": "P",
            "row_perm_count": PERM_STATS['P'],
            "total_anchors": initial_anchors + p_row_increment,
            "status": "INFEASIBLE",
            "p_row_match": False,
            "p_increment_positions": [],
            "solution": None
        }
    
    # 保存JSON
    output_dir = "D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output"
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}\\V91_104_anchor_P_solution.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] JSON結果已保存")
    print(f"  路徑: {output_dir}\\V91_104_anchor_P_solution.json")
    
    print(f"\n{'=' * 70}")
    print(f"V91 求解完成")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
