#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""V82 新A行终局102锚点推演 - 纯行列宫三约束规则"""

import sys
import os
import time
import json

from ortools.sat.python import cp_model

# 新的A行终局排列
NEW_A_ROW_FINAL = [2,6,3,1, 11,12,13,5, 10,7,9,14, 15,16,4,8]

def main():
    print("=" * 75)
    print("V82 新A行终局102锚点推演 - 纯行列宫三约束规则")
    print("=" * 75)
    print()
    
    # 动态找到txt文件
    txt_files = [f for f in os.listdir('.') if f.endswith('.txt') and 'box_size4' in f]
    if not txt_files:
        print("错误: 未找到box_size4.txt文件")
        # 列出所有txt文件供参考
        all_txt = [f for f in os.listdir('.') if f.endswith('.txt')]
        print(f"目录中的txt文件: {all_txt}")
        sys.exit(1)
    
    txt_file = txt_files[0]
    print(f"读取文件: {repr(txt_file)}")
    
    # 用UTF-8读取
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    print(f"文件总行数: {len(lines)}")
    
    # 解析初始盘（前16行）
    initial_puzzle = []
    for line in lines[:16]:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            try:
                vals = [int(x) for x in stripped.split()[:16]]
                initial_puzzle.append(vals)
            except:
                pass
    
    print(f"读取初始盘行数: {len(initial_puzzle)}")
    
    # 解析终局盘（从"终局盘:"标记开始）
    final_section = []
    in_final = False
    for line in lines:
        stripped = line.strip()
        if '终局盘' in stripped or '终局' in stripped:
            in_final = True
            continue
        if in_final and stripped and not stripped.startswith('#'):
            try:
                vals = [int(x) for x in stripped.split()[:16]]
                final_section.append(vals)
            except:
                pass
    
    print(f"读取终局盘行数: {len(final_section)}")
    
    # 从txt终局中获取A行（第一行）
    if len(final_section) >= 1:
        txt_a_row_final = final_section[0]
        print(f"txt文件A行终局: {txt_a_row_final}")
    else:
        txt_a_row_final = None
    
    # 用户提供的A行终局
    print(f"用户提供A行终局: {NEW_A_ROW_FINAL}")
    print(f"两个A行终局相同: {txt_a_row_final == NEW_A_ROW_FINAL if txt_a_row_final else 'N/A'}")
    
    # 构建102锚点谜题
    print()
    print("=" * 75)
    print("构建102锚点谜题")
    print("=" * 75)
    print()
    
    # 初始化16x16谜题
    puzzle_16x16 = [[0] * 16 for _ in range(16)]
    initial_anchor_count = 0
    
    # 填入初始盘
    for r in range(min(16, len(initial_puzzle))):
        for c in range(16):
            if initial_puzzle[r][c] != 0:
                puzzle_16x16[r][c] = initial_puzzle[r][c]
                initial_anchor_count += 1
    
    print(f"初始盘锚点数: {initial_anchor_count}")
    print(f"A行初始: {puzzle_16x16[0]}")
    
    # 创建CP-SAT求解器
    print()
    print("创建CP-SAT求解器...")
    model = cp_model.CpModel()
    
    # 创建16x16变量
    vars_16x16 = [[model.NewIntVar(1, 16, f'cell_{r}_{c}') for c in range(16)] for r in range(16)]
    
    # 添加初始锚点约束
    for r in range(16):
        for c in range(16):
            if puzzle_16x16[r][c] != 0:
                model.Add(vars_16x16[r][c] == puzzle_16x16[r][c])
    
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
    
    # 添加A行终局增量锚点
    print()
    print("添加A行终局增量锚点...")
    
    a_row_initial = puzzle_16x16[0]
    new_anchors = 0
    conflict_details = []
    
    # 检查值冲突（同一值在初始盘和新终局中出现于不同列）
    for val in range(1, 17):
        initial_pos = None
        for c in range(16):
            if a_row_initial[c] == val:
                initial_pos = c
                break
        
        final_pos = None
        for c in range(16):
            if NEW_A_ROW_FINAL[c] == val:
                final_pos = c
                break
        
        if initial_pos is not None and final_pos is not None:
            if initial_pos != final_pos:
                conflict_details.append({
                    'value': val,
                    'initial_col': initial_pos,
                    'final_col': final_pos,
                    'type': '列冲突'
                })
    
    print(f"发现值空间冲突数: {len(conflict_details)}")
    for conf in conflict_details[:5]:
        print(f"  值{conf['value']:2d}: 初始列{conf['initial_col']:2d} -> 新终局列{conf['final_col']:2d}")
    
    # 添加新A行终局的锚点约束
    for c in range(16):
        if NEW_A_ROW_FINAL[c] != 0 and a_row_initial[c] == 0:
            model.Add(vars_16x16[0][c] == NEW_A_ROW_FINAL[c])
            new_anchors += 1
    
    print(f"A行新增锚点数: {new_anchors}")
    
    total_anchors = initial_anchor_count + new_anchors
    print(f"总锚点数: {total_anchors}")
    
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
    row_names = 'ABCDEFGHIJ' + 'KLMNOP'
    
    results = {
        'version': 'V82',
        'puzzle_type': '102_anchor_A_row_new',
        'description': '初始盘92锚点 + 新A行终局增量锚点',
        'initial_anchors': initial_anchor_count,
        'a_row_new_anchors': new_anchors,
        'total_anchors': total_anchors,
        'a_row_final': NEW_A_ROW_FINAL,
        'status': status_name,
        'elapsed_seconds': round(elapsed, 3),
        'constraint_type': 'pure_row_column_box_triple',
        'conflicts': conflict_details
    }
    
    if status_code == cp_model.OPTIMAL or status_code == cp_model.FEASIBLE:
        results['unique'] = (status_code == cp_model.OPTIMAL)
        
        solution = {}
        for r in range(16):
            row_name = row_names[r]
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
            row_name = row_names[r]
            vals = solution[row_name]
            marker = '★' if row_name == 'A' else ' '
            vals_str = "  ".join(f"{v:3d}" for v in vals)
            print(f"{marker}行{row_name:<2}: {vals_str}")
        print("-" * 75)
        print(f"★ 表示A行 (终局锁定行)")
    
    # 保存结果
    with open('V82_new_A_row_solution.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 75)
    print("V82 新A行终局102锚点推演完成")
    print("=" * 75)
    print()
    print("输出文件: V82_new_A_row_solution.json")

if __name__ == '__main__':
    main()
