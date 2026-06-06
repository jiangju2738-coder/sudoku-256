#!/usr/bin/env python3
"""测试更少已知数字下的可求解性"""

import json
from ortools.sat.python import cp_model
from collections import defaultdict

# 加载配置
with open('sudoku_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 加载符阖排列
fuhh_permutations = {}
for row_num in range(1, 17):
    filename = f"A{row_num}_permutations.json"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            fuhh_permutations[row_num] = json.load(f)
    except:
        fuhh_permutations[row_num] = []

known = {(kd['row']-1, kd['col']-1): kd['value'] for kd in config['known_digits']}

print("=" * 65)
print("🔬 测试不同已知数字数量下的可求解性")
print("=" * 65)

# 逐行移除已知数字，测试可解性
rows_with_clues = defaultdict(list)
for kd in config['known_digits']:
    rows_with_clues[kd['row']].append(kd)

# 从完整配置开始，逐行移除
test_configs = []
current_known = list(config['known_digits'])

for remove_row in range(1, 17):
    # 移除第 remove_row 行的所有已知数字
    new_known = [kd for kd in current_known if kd['row'] != remove_row]
    test_configs.append((remove_row, len(new_known), new_known))
    current_known = new_known

print(f"\n{'行移除':>6} {'剩余':>6} {'状态':>10}")
print(f"{'-'*6} {'-'*6} {'-'*10}")

for remove_row, count, known_list in test_configs:
    # 构建模型
    model = cp_model.CpModel()
    known_dict = {(kd['row']-1, kd['col']-1): kd['value'] for kd in known_list}
    
    cells = {}
    for r in range(16):
        for c in range(16):
            if (r, c) in known_dict:
                continue
            
            allowed = set(range(1, 17))
            if (r+1) in fuhh_permutations:
                perms = fuhh_permutations[r+1]
                allowed = set()
                for perm in perms:
                    if c < len(perm):
                        allowed.add(perm[c])
            
            if allowed:
                cells[(r, c)] = model.NewIntVarFromDomain(
                    cp_model.Domain.FromValues(sorted(allowed)), f'x_{r}_{c}')
    
    # 约束
    for r in range(16):
        row_vars = []
        for c in range(16):
            if (r, c) in cells:
                row_vars.append(cells[(r, c)])
            elif (r, c) in known_dict:
                row_vars.append(known_dict[(r, c)])
        if len(row_vars) > 1:
            model.AddAllDifferent(row_vars)
    
    for c in range(16):
        col_vars = []
        for r in range(16):
            if (r, c) in cells:
                col_vars.append(cells[(r, c)])
            elif (r, c) in known_dict:
                col_vars.append(known_dict[(r, c)])
        if len(col_vars) > 1:
            model.AddAllDifferent(col_vars)
    
    for br in range(4):
        for bc in range(4):
            box_vars = []
            for r in range(br*4, (br+1)*4):
                for c in range(bc*4, (bc+1)*4):
                    if (r, c) in cells:
                        box_vars.append(cells[(r, c)])
                    elif (r, c) in known_dict:
                        box_vars.append(known_dict[(r, c)])
            if len(box_vars) > 1:
                model.AddAllDifferent(box_vars)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    solver.parameters.num_search_workers = 4
    solver.parameters.log_search_progress = False
    
    status = solver.Solve(model)
    solvable = '✓ 可解' if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else '✗ 无解'
    
    print(f"移除行 {remove_row:>2}: {count:>4} {solvable:>10}")

print(f"\n{'='*65}")
