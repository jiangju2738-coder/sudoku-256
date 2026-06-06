#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V84: 101锚点谜题求解器
- 初始盘92锚点 + M行终局新增9锚点
- 总锚点数: 101
"""

import json
import re
from datetime import datetime
from ortools.sat.python import cp_model

def parse_txt_file(filepath):
    """从txt文件解析初始盘和终局盘"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析初始盘（行A到行P，共16行）
    initial_puzzle = {}
    lines = content.split('\n')
    for i in range(20):  # 扩大范围以包含行P（可能包含空行）
        if i + 3 >= len(lines):
            break
        line = lines[i+3]
        match = re.match(r'行([A-P])\s*\[(.+)\]', line)
        if match:
            row_letter = match.group(1)
            numbers_str = match.group(2)
            numbers = []
            for x in numbers_str.split(','):
                x = x.strip().rstrip('.,')
                if x:
                    numbers.append(int(x))
            if len(numbers) == 16:
                initial_puzzle[row_letter] = numbers
    
    # 解析终局盘M行（第102行）
    final_m_row = [15, 14, 13, 11, 12, 8, 2, 10, 5, 1, 4, 3, 16, 6, 9, 7]
    
    return initial_puzzle, final_m_row

def solve_101_anchor_m(puzzle, m_row_final):
    """求解101锚点谜题（92初始 + M行9新增）"""
    print("="*60)
    print("V84: 101锚点谜题求解器")
    print("初始盘92锚点 + M行终局新增9锚点")
    print("="*60)
    
    # 构建16x16网格
    grid = [[0]*16 for _ in range(16)]
    row_names = 'ABCDEFGHIJKLMNOP'
    
    # 填入初始盘
    anchor_count = 0
    for row_idx, row_name in enumerate(row_names):
        if row_name in puzzle:
            for col_idx, val in enumerate(puzzle[row_name]):
                if val != 0:
                    grid[row_idx][col_idx] = val
                    anchor_count += 1
    
    # 填入M行终局新增锚点
    m_row_idx = 12  # M是第13行，索引12
    for col_idx, val in enumerate(m_row_final):
        if grid[m_row_idx][col_idx] == 0:  # 初始盘为空的位置
            grid[m_row_idx][col_idx] = val
            anchor_count += 1
            print(f"  M行新增锚点: 位置[{m_row_idx},{col_idx}] = {val}")
    
    print(f"\n总锚点数: {anchor_count}")
    
    # 创建CP-SAT模型
    model = cp_model.CpModel()
    
    # 创建变量
    vars = {}
    for r in range(16):
        for c in range(16):
            vars[(r, c)] = model.NewIntVar(1, 16, f'cell_{r}_{c}')
    
    # 添加已知的锚点约束
    for r in range(16):
        for c in range(16):
            if grid[r][c] != 0:
                model.Add(vars[(r, c)] == grid[r][c])
    
    # 行约束
    for r in range(16):
        model.AddAllDifferent([vars[(r, c)] for c in range(16)])
    
    # 列约束
    for c in range(16):
        model.AddAllDifferent([vars[(r, c)] for r in range(16)])
    
    # 宫约束（4x4宫）
    for box_r in range(4):
        for box_c in range(4):
            cells = []
            for dr in range(4):
                for dc in range(4):
                    r = box_r * 4 + dr
                    c = box_c * 4 + dc
                    cells.append(vars[(r, c)])
            model.AddAllDifferent(cells)
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0
    solver.parameters.num_search_workers = 8
    
    print("\n开始求解...")
    start_time = datetime.now()
    status = solver.Solve(model)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # 输出结果
    print(f"\n求解状态: {solver.StatusName(status)}")
    print(f"耗时: {elapsed:.3f}秒")
    
    result = {
        "version": "V84",
        "timestamp": datetime.now().isoformat(),
        "total_anchors": anchor_count,
        "status": solver.StatusName(status),
        "elapsed_seconds": round(elapsed, 3),
        "m_row_final": m_row_final,
        "solution": None,
        "m_row_match": False
    }
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # 构建解盘
        solution = []
        for r in range(16):
            row = []
            for c in range(16):
                row.append(solver.Value(vars[(r, c)]))
            solution.append(row)
        
        result["solution"] = solution
        
        # 检查M行是否匹配
        m_row_solution = solution[m_row_idx]
        match = m_row_solution == m_row_final
        result["m_row_match"] = match
        
        print(f"\nM行匹配终局: {'是' if match else '否'}")
        if match:
            print("[OK] M行终局已完整锁定，列约束将传播至全盘")
        else:
            print(f"终局M行: {m_row_final}")
            print(f"解盘M行: {m_row_solution}")
        
        # 输出完整解盘
        print("\n完整解盘:")
        for r in range(16):
            row_str = "行" + row_names[r] + ": "
            for c in range(16):
                val = solution[r][c]
                if r == m_row_idx:
                    row_str += f"*{val:2d} "
                else:
                    row_str += f" {val:2d} "
            print(row_str)
    
    return result

def main():
    txt_file = "超級大數獨_box_size4.txt"
    
    # 解析文件
    puzzle, m_row_final = parse_txt_file(txt_file)
    
    print(f"\n初始盘锚点统计:")
    for row_name in 'ABCDEFGHIJKLMNOP':
        if row_name in puzzle:
            anchors = sum(1 for x in puzzle[row_name] if x != 0)
            print(f"  行{row_name}: {anchors}个锚点")
    
    # 求解
    result = solve_101_anchor_m(puzzle, m_row_final)
    
    # 保存结果
    output_file = "V84_101_anchor_M_solution.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存至: {output_file}")
    
    return result

if __name__ == "__main__":
    main()
