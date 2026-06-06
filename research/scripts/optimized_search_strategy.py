#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化策略：用三解盘共有的锚点 + 两两匹配约束压缩搜索空间
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
from ortools.sat.python import cp_model
from collections import Counter

# 从three_solutions_linkage_report.json加载数据
try:
    with open('three_solutions_linkage_report.json', 'r', encoding='utf-8') as f:
        linkage_data = json.load(f)
except:
    # 如果文件不存在，使用之前分析的结果
    print("three_solutions_linkage_report.json 不存在，使用内置数据")
    linkage_data = None

# 如果没有数据文件，使用硬编码的已知数据
INITIAL_SOLUTION = {
    'A': [7, 15, 3, 9, 11, 12, 6, 5, 10, 2, 1, 14, 13, 16, 4, 8],
    'B': [16, 12, 10, 8, 3, 15, 9, 14, 6, 13, 5, 4, 2, 7, 1, 11],
    'C': [11, 6, 14, 1, 4, 2, 13, 8, 7, 12, 3, 16, 10, 9, 15, 5],
    'D': [2, 4, 5, 13, 7, 10, 1, 16, 15, 8, 9, 11, 3, 12, 14, 6],
    'E': [9, 2, 7, 10, 13, 1, 16, 6, 3, 5, 15, 12, 4, 11, 8, 14],
    'F': [5, 8, 1, 11, 15, 14, 4, 3, 16, 9, 7, 10, 6, 13, 2, 12],
    'G': [14, 16, 4, 6, 8, 7, 12, 10, 2, 11, 13, 1, 15, 3, 5, 9],
    'H': [3, 13, 15, 12, 2, 5, 11, 9, 8, 4, 14, 6, 7, 1, 16, 10],
    'I': [13, 9, 16, 2, 1, 11, 8, 12, 14, 10, 4, 7, 5, 15, 6, 3],
    'J': [12, 5, 11, 15, 10, 9, 3, 13, 1, 6, 16, 2, 8, 14, 7, 4],
    'K': [1, 14, 6, 7, 5, 4, 15, 2, 11, 3, 8, 13, 9, 10, 12, 16],
    'L': [10, 3, 8, 4, 6, 16, 14, 7, 9, 15, 12, 5, 11, 2, 13, 1],
    'M': [15, 11, 13, 16, 12, 8, 2, 4, 5, 1, 10, 3, 14, 6, 9, 7],
    'N': [4, 10, 9, 5, 14, 6, 7, 1, 13, 16, 11, 15, 12, 8, 3, 2],
    'O': [6, 1, 12, 14, 9, 3, 10, 15, 4, 7, 2, 8, 16, 5, 11, 13],
    'P': [8, 7, 2, 3, 16, 13, 5, 11, 12, 14, 6, 9, 1, 4, 10, 15],
}

UPDATE_SOLUTION = {
    'A': [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5],
    'B': [8, 12, 7, 10, 3, 15, 9, 11, 6, 16, 5, 4, 2, 14, 1, 13],
    'C': [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5],
    'D': [9, 4, 16, 13, 7, 14, 1, 6, 8, 2, 10, 11, 3, 12, 15, 5],
    'E': [7, 10, 15, 9, 13, 8, 6, 14, 12, 5, 3, 16, 4, 1, 11, 2],
    'F': [2, 8, 5, 16, 15, 1, 4, 3, 11, 9, 7, 10, 6, 13, 14, 12],
    'G': [14, 11, 4, 6, 16, 7, 12, 10, 2, 13, 15, 1, 5, 3, 8, 9],
    'H': [12, 13, 1, 3, 2, 5, 11, 9, 4, 8, 14, 6, 15, 7, 16, 10],
    'I': [13, 9, 8, 2, 6, 11, 10, 12, 14, 4, 1, 7, 16, 15, 5, 3],
    'J': [10, 5, 12, 14, 1, 9, 3, 13, 15, 11, 16, 2, 8, 4, 7, 6],
    'K': [1, 16, 6, 7, 5, 4, 15, 2, 10, 3, 8, 13, 9, 11, 12, 14],
    'L': [3, 15, 11, 4, 8, 16, 14, 7, 9, 6, 12, 5, 13, 10, 2, 1],
    'M': [15, 14, 13, 8, 12, 10, 2, 16, 5, 1, 4, 3, 11, 6, 9, 7],
    'N': [4, 7, 9, 5, 14, 6, 8, 1, 13, 10, 11, 15, 12, 2, 3, 16],
    'O': [6, 1, 10, 11, 9, 3, 7, 15, 16, 12, 2, 8, 14, 5, 13, 4],
    'P': [16, 3, 2, 12, 11, 13, 5, 4, 7, 14, 6, 9, 1, 8, 10, 15],
}

FINAL_C = [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5]

ROW_NAMES = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']

print("=" * 80)
print("优化搜索策略：三解盘共有锚点 + 两两匹配约束")
print("=" * 80)

# 步骤1：计算三解盘共有的锚点（三个解盘中相同值的位置）
print("\n【步骤1】计算三解盘共有锚点...")

shared_anchors = []  # 在三个解盘中都有相同值的位置
initial_update_match = []  # 初始和更新相同
initial_final_partial_match = []  # 初始和终局(非0)相同
update_final_partial_match = []  # 更新和终局(非0)相同

for r_idx, row_name in enumerate(ROW_NAMES):
    for c_idx, col_name in enumerate(COL_NAMES):
        pos = row_name + col_name
        initial_val = INITIAL_SOLUTION[row_name][c_idx]
        update_val = UPDATE_SOLUTION[row_name][c_idx]
        
        # 终局解盘中，有些位置是0（占位符），有些有值
        # 对终局解盘，只使用已知非0的位置
        if row_name == 'C':
            # C行全满
            final_val = FINAL_C[c_idx]
        else:
            # 其他行从txt文件第87行读取的终局解盘
            # A行: [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8]
            # B-P行来自txt文件第278-293行
            # 这里简化：A行用已知锚点，其他行暂用0占位符
            final_vals_map = {
                'A': [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8],
                'B': [8,12,7,10,3,15,9,11,6,16,5,4,2,14,1,13],
                'C': FINAL_C,
                'D': [9,4,16,13,7,14,1,6,8,2,10,11,3,12,15,5],
                'E': [7,10,15,9,13,8,6,14,12,5,3,16,4,1,11,2],
                'F': [2,8,5,16,15,1,4,3,11,9,7,10,6,13,14,12],
                'G': [14,11,4,6,16,7,12,10,2,13,15,1,5,3,8,9],
                'H': [12,13,1,3,2,5,11,9,4,8,14,6,15,7,16,10],
                'I': [13,9,8,2,6,11,10,12,14,4,1,7,16,15,5,3],
                'J': [10,5,12,14,1,9,3,13,15,11,16,2,8,4,7,6],
                'K': [1,16,6,7,5,4,15,2,10,3,8,13,9,11,12,14],
                'L': [3,15,11,4,8,16,14,7,9,6,12,5,13,10,2,1],
                'M': [15,14,13,8,12,10,2,16,5,1,4,3,11,6,9,7],
                'N': [4,7,9,5,14,6,8,1,13,10,11,15,12,2,3,16],
                'O': [6,1,10,11,9,3,7,15,16,12,2,8,14,5,13,4],
                'P': [16,3,2,12,11,13,5,4,7,14,6,9,1,8,10,15],
            }
            final_val = final_vals_map[row_name][c_idx]
        
        # 三解盘共有：初始=更新=终局(且终局非0)
        if final_val != 0 and initial_val == update_val == final_val:
            shared_anchors.append((pos, initial_val))
        
        # 初始与更新匹配
        if initial_val == update_val:
            initial_update_match.append((pos, initial_val))
        
        # 初始与终局(非0)匹配
        if final_val != 0 and initial_val == final_val:
            initial_final_partial_match.append((pos, initial_val))
        
        # 更新与终局(非0)匹配
        if final_val != 0 and update_val == final_val:
            update_final_partial_match.append((pos, update_val))

print(f"  三解盘共有锚点: {len(shared_anchors)}个")
print(f"  初始=更新匹配: {len(initial_update_match)}个")
print(f"  初始与终局匹配: {len(initial_final_partial_match)}个")
print(f"  更新与终局匹配: {len(update_final_partial_match)}个")

# 步骤2：创建强约束集（三解盘共有 + 初始=更新的高频匹配）
print("\n【步骤2】创建优化约束集...")

# 强约束：三解盘共有锚点
strong_constraints = {pos: val for pos, val in shared_anchors}

# 中等约束：初始=更新匹配（排除A行异常数据）
# A行在初始和更新中差异很大，排除A行
medium_constraints = {}
for pos, val in initial_update_match:
    if pos[0] != 'A':  # 排除A行
        medium_constraints[pos] = val

print(f"  强约束（三解盘共有）: {len(strong_constraints)}个")
print(f"  中等约束（B-P行初始=更新）: {len(medium_constraints)}个")

# 展示部分约束
print("\n强约束示例（前20个）：")
for i, (pos, val) in enumerate(list(strong_constraints.items())[:20]):
    print(f"  {pos}={val}")

print("\n中等约束示例（前20个）：")
for i, (pos, val) in enumerate(list(medium_constraints.items())[:20]):
    print(f"  {pos}={val}")

# 步骤3：用CP-SAT搜索优化约束下的解
print("\n【步骤3】CP-SAT搜索优化约束下的解...")

model = cp_model.CpModel()
grid = {(r, c): model.NewIntVar(1, 16, f'g{r}{c}') for r in range(16) for c in range(16)}

# 数独三约束
for r in range(16):
    model.AddAllDifferent([grid[(r, c)] for c in range(16)])
for c in range(16):
    model.AddAllDifferent([grid[(r, c)] for r in range(16)])
for br in range(4):
    for bc in range(4):
        cells = [grid[(br*4+dr, bc*4+dc)] for dr in range(4) for dc in range(4)]
        model.AddAllDifferent(cells)

# C191620约束
for i, val in enumerate(FINAL_C):
    model.Add(grid[(2, i)] == val)

# 强约束
for pos, val in strong_constraints.items():
    row_name, col_name = pos[0], pos[1]
    r = ROW_NAMES.index(row_name)
    c = COL_NAMES.index(col_name)
    model.Add(grid[(r, c)] == val)

# 中等约束（可选：作为软约束或硬约束）
# 这里作为硬约束添加
for pos, val in medium_constraints.items():
    row_name, col_name = pos[0], pos[1]
    r = ROW_NAMES.index(row_name)
    c = COL_NAMES.index(col_name)
    model.Add(grid[(r, c)] == val)

print(f"  约束总数: {len(strong_constraints) + len(medium_constraints) + 16} (含C191620)")

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0
solver.parameters.num_search_workers = 8

print("  开始搜索...")
status = solver.Solve(model)

# 步骤4：分析结果
print("\n【步骤4】结果分析...")

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("  找到解！")
    
    solution = []
    for r in range(16):
        row = [solver.Value(grid[(r, c)]) for c in range(16)]
        solution.append(row)
    
    # 对比txt终局解盘
    txt_final_map = {
        'A': [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8],
        'B': [8,12,7,10,3,15,9,11,6,16,5,4,2,14,1,13],
        'C': FINAL_C,
        'D': [9,4,16,13,7,14,1,6,8,2,10,11,3,12,15,5],
        'E': [7,10,15,9,13,8,6,14,12,5,3,16,4,1,11,2],
        'F': [2,8,5,16,15,1,4,3,11,9,7,10,6,13,14,12],
        'G': [14,11,4,6,16,7,12,10,2,13,15,1,5,3,8,9],
        'H': [12,13,1,3,2,5,11,9,4,8,14,6,15,7,16,10],
        'I': [13,9,8,2,6,11,10,12,14,4,1,7,16,15,5,3],
        'J': [10,5,12,14,1,9,3,13,15,11,16,2,8,4,7,6],
        'K': [1,16,6,7,5,4,15,2,10,3,8,13,9,11,12,14],
        'L': [3,15,11,4,8,16,14,7,9,6,12,5,13,10,2,1],
        'M': [15,14,13,8,12,10,2,16,5,1,4,3,11,6,9,7],
        'N': [4,7,9,5,14,6,8,1,13,10,11,15,12,2,3,16],
        'O': [6,1,10,11,9,3,7,15,16,12,2,8,14,5,13,4],
        'P': [16,3,2,12,11,13,5,4,7,14,6,9,1,8,10,15],
    }
    
    print("\n  对比txt终局解盘：")
    match_count = 0
    for r_idx, row_name in enumerate(ROW_NAMES):
        sol_row = tuple(solution[r_idx])
        txt_row = tuple(txt_final_map[row_name])
        
        # 计算匹配率（忽略txt中0的位置）
        non_zero_match = 0
        non_zero_count = 0
        for i, (s, t) in enumerate(zip(sol_row, txt_row)):
            if t != 0:
                non_zero_count += 1
                if s == t:
                    non_zero_match += 1
        
        if non_zero_count > 0:
            pct = non_zero_match / non_zero_count * 100
            if pct == 100:
                match_count += 1
                print(f"  {row_name}: [MATCH] 100% ({non_zero_match}/{non_zero_count})")
            else:
                print(f"  {row_name}: {non_zero_match}/{non_zero_count} = {pct:.1f}%")
        else:
            print(f"  {row_name}: txt为占位符，跳过")
    
    print(f"\n  完全匹配行数: {match_count}")
    
    # 保存结果
    output = {
        'search_strategy': '三解盘共有锚点 + 两两匹配优化',
        'strong_constraints_count': len(strong_constraints),
        'medium_constraints_count': len(medium_constraints),
        'solutions_found': 1,
        'match_with_txt': match_count,
        'solution': {ROW_NAMES[i]: solution[i] for i in range(16)}
    }
    
    with open('optimized_search_result.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n  结果已保存到 optimized_search_result.json")
    
else:
    print("  无解！")
    print("\n  这表明三解盘共有锚点 + 两两匹配约束可能与C191620冲突")

# 步骤5：总结优化效果
print("\n" + "=" * 80)
print("优化效果总结")
print("=" * 80)
print(f"""
【优化策略】
  传统方法: 92锚点 + C191620 = 108个固定约束
  优化方法: 三解盘共有({len(strong_constraints)}) + 两两匹配({len(medium_constraints)}) + C191620

【约束数量对比】
  传统方法: 92 + 16 = 108个约束
  优化方法: {len(strong_constraints)} + {len(medium_constraints)} + 16 = {len(strong_constraints) + len(medium_constraints) + 16}个约束

【关键优势】
  1. 三解盘共有锚点是"超稳定"约束，更可能接近真实解
  2. B-P行的两两匹配排除了A行异常数据
  3. 约束更具"交叉验证"性质，减少搜索空间
  4. 搜索结果直接可对比txt终局解盘

【下一步建议】
  1. 如果找到解，进一步验证每行是否在backup_fuyi/中
  2. 如果无解，分析冲突约束，调整约束权重
  3. 逐步增加符阖排列约束，逼近原始解空间
""")
