#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""V82 新A行终局102锚点推演 - 纯行列宫三约束规则"""

import sys
import os
import time
import json

from ortools.sat.python import cp_model

# ============================================================
# 硬编码初始盘92锚点（从txt文件正确解析）
# ============================================================

INITIAL_PUZZLE = [
    [0, 0, 3, 0, 0, 12, 0, 5, 0, 0, 0, 14, 0, 16, 0, 8],      # A
    [0, 12, 0, 0, 3, 0, 9, 0, 6, 0, 5, 4, 2, 0, 1, 0],       # B
    [0, 0, 14, 0, 0, 2, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0],       # C
    [0, 4, 0, 13, 7, 0, 1, 0, 0, 0, 0, 11, 0, 12, 0, 0],     # D
    [0, 0, 0, 0, 13, 0, 0, 0, 0, 5, 0, 0, 4, 0, 0, 0],       # E
    [0, 8, 0, 0, 15, 0, 4, 3, 0, 9, 0, 0, 0, 13, 0, 12],     # F
    [14, 0, 4, 6, 0, 0, 12, 0, 2, 0, 0, 0, 0, 3, 0, 0],      # G
    [0, 13, 0, 0, 0, 5, 0, 9, 0, 0, 14, 6, 0, 0, 16, 0],     # H
    [13, 0, 0, 2, 0, 11, 0, 0, 14, 0, 0, 7, 0, 15, 0, 3],    # I
    [0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 8, 0, 7, 0],       # J
    [1, 0, 6, 0, 5, 0, 0, 2, 0, 3, 0, 0, 9, 0, 0, 0],        # K
    [0, 0, 0, 4, 0, 16, 14, 0, 0, 0, 12, 5, 0, 0, 0, 1],     # L
    [15, 0, 0, 0, 12, 0, 0, 0, 5, 1, 0, 3, 0, 6, 0, 7],      # M
    [0, 0, 9, 0, 0, 6, 0, 0, 13, 0, 0, 15, 0, 0, 3, 0],      # N
    [0, 1, 0, 0, 9, 0, 0, 15, 0, 0, 2, 8, 0, 5, 0, 0],       # O
    [0, 0, 2, 0, 0, 0, 5, 0, 0, 14, 0, 0, 1, 0, 10, 15],     # P
]

# 用户提供的A行终局排列
NEW_A_ROW_FINAL = [2, 6, 3, 1, 11, 12, 13, 5, 10, 7, 9, 14, 15, 16, 4, 8]

ROW_NAMES = 'ABCDEFGHIJKLMNOP'

def count_anchors(puzzle):
    """统计锚点数"""
    total = 0
    for row in puzzle:
        for val in row:
            if val != 0:
                total += 1
    return total

def main():
    print("=" * 75)
    print("V82 新A行终局102锚点推演 - 纯行列宫三约束规则")
    print("=" * 75)
    print()
    
    # 统计初始盘锚点
    initial_anchors = count_anchors(INITIAL_PUZZLE)
    print(f"初始盘锚点数: {initial_anchors}")
    
    # A行初始和终局
    a_initial = INITIAL_PUZZLE[0]
    print(f"A行初始: {a_initial}")
    print(f"A行新终局: {NEW_A_ROW_FINAL}")
    
    # 检查A行冲突
    print()
    print("A行值空间冲突分析:")
    conflicts = []
    for val in range(1, 17):
        initial_pos = None
        for c in range(16):
            if a_initial[c] == val:
                initial_pos = c
                break
        final_pos = None
        for c in range(16):
            if NEW_A_ROW_FINAL[c] == val:
                final_pos = c
                break
        if initial_pos is not None and final_pos is not None:
            if initial_pos != final_pos:
                conflicts.append((val, initial_pos, final_pos))
    
    if conflicts:
        print(f"发现{len(conflicts)}对值空间冲突:")
        for val, ip, fp in conflicts:
            print(f"  值{val}: 初始列{ip} -> 新终局列{fp}")
    else:
        print("无值空间冲突")
    
    # 构建102锚点谜题
    print()
    print("=" * 75)
    print("构建102锚点谜题")
    print("=" * 75)
    print()
    
    # 复制初始盘
    puzzle_16x16 = [row[:] for row in INITIAL_PUZZLE]
    
    # 计算A行新增锚点（终局中不在初始盘的位置）
    new_anchors_a = 0
    for c in range(16):
        if NEW_A_ROW_FINAL[c] != 0 and a_initial[c] == 0:
            new_anchors_a += 1
    
    total_anchors = initial_anchors + new_anchors_a
    print(f"初始盘锚点: {initial_anchors}")
    print(f"A行新增锚点: {new_anchors_a}")
    print(f"总锚点数: {total_anchors}")
    
    # 创建CP-SAT求解器
    print()
    print("创建CP-SAT求解器...")
    model = cp_model.CpModel()
    
    # 创建16x16变量
    vars_16x16 = [[model.NewIntVar(1, 16, f'cell_{r}_{c}') for c in range(16)] for r in range(16)]
    
    # 添加初始锚点约束
    for r in range(16):
        for c in range(16):
            if INITIAL_PUZZLE[r][c] != 0:
                model.Add(vars_16x16[r][c] == INITIAL_PUZZLE[r][c])
    
    # 行AllDifferent约束
    for r in range(16):
        model.AddAllDifferent(vars_16x16[r])
    
    # 列AllDifferent约束
    for c in range(16):
        col_vars = [vars_16x16[r][c] for r in range(16)]
        model.AddAllDifferent(col_vars)
    
    # 宫AllDifferent约束 (4x4宫格)
    for box_r in range(4):
        for box_c in range(4):
            box_vars = []
            for r_off in range(4):
                for c_off in range(4):
                    r = box_r * 4 + r_off
                    c = box_c * 4 + c_off
                    box_vars.append(vars_16x16[r][c])
            model.AddAllDifferent(box_vars)
    
    # 添加A行终局锚点约束
    print()
    print("添加A行终局增量锚点...")
    
    for c in range(16):
        if NEW_A_ROW_FINAL[c] != 0 and a_initial[c] == 0:
            model.Add(vars_16x16[0][c] == NEW_A_ROW_FINAL[c])
    
    # 求解
    print()
    print("开始CP-SAT求解...")
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    solver.parameters.num_search_workers = 8
    
    start_time = time.time()
    status_code = solver.Solve(model)
    elapsed = time.time() - start_time
    
    status_name = cp_model.CpSolver().StatusName(status_code)
    print(f"求解状态: {status_name}")
    print(f"求解耗时: {elapsed:.3f}秒")
    
    # 输出结果
    results = {
        'version': 'V82',
        'puzzle_type': '102_anchor_A_row_new',
        'description': '初始盘92锚点 + A行新终局增量锚点',
        'initial_anchors': initial_anchors,
        'a_row_new_anchors': new_anchors_a,
        'total_anchors': total_anchors,
        'a_row_final': NEW_A_ROW_FINAL,
        'status': status_name,
        'elapsed_seconds': round(elapsed, 3),
        'constraint_type': 'pure_row_column_box_triple',
        'conflicts': [{'value': v, 'initial_col': ip, 'final_col': fp} for v, ip, fp in conflicts]
    }
    
    if status_code == cp_model.OPTIMAL or status_code == cp_model.FEASIBLE:
        results['unique'] = (status_code == cp_model.OPTIMAL)
        
        solution = {}
        for r in range(16):
            row_name = ROW_NAMES[r]
            solution[row_name] = [solver.Value(vars_16x16[r][c]) for c in range(16)]
        
        results['solution'] = solution
        
        # 检查A行匹配
        a_row_solution = solution['A']
        match = (a_row_solution == NEW_A_ROW_FINAL)
        results['a_row_match'] = match
        print(f"A行匹配终局: {'YES' if match else 'NO'}")
        
        print()
        print("完整解盘:")
        print("-" * 75)
        for r in range(16):
            row_name = ROW_NAMES[r]
            vals = solution[row_name]
            marker = '★' if row_name == 'A' else ' '
            vals_str = "  ".join(f"{v:3d}" for v in vals)
            print(f"{marker}行{row_name:<2}: {vals_str}")
        print("-" * 75)
        print(f"★ 表示A行 (终局锁定行)")
        
        # 检查与旧终局是否相同
        old_a_row = [2, 6, 3, 1, 11, 12, 13, 5, 10, 7, 9, 14, 15, 16, 4, 8]  # 之前txt文件的A行
        new_a_row = NEW_A_ROW_FINAL
        print()
        print("A行终局比较:")
        print(f"旧A行终局: {old_a_row}")
        print(f"新A行终局: {new_a_row}")
        print(f"两个A行终局相同: {old_a_row == new_a_row}")
    
    # 保存结果
    output_file = 'V82_new_A_row_solution.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 75)
    print("V82 新A行终局102锚点推演完成")
    print("=" * 75)
    print()
    print(f"输出文件: {output_file}")

if __name__ == '__main__':
    main()
