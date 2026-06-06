#!/usr/bin/env python3
"""分析新配置中的冲突来源"""

import json
from ortools.sat.python import cp_model
from collections import defaultdict

print("=" * 65)
print("🔍 冲突分析")
print("=" * 65)

# 加载配置
with open('sudoku_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 加载符阖排列
for row_num in range(1, 17):
    filename = f"A{row_num}_permutations.json"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            config.setdefault('fuhh_permutations', {})[row_num] = data
    except:
        pass

known = {(kd['row']-1, kd['col']-1): kd['value'] for kd in config['known_digits']}

# 1. 检查已知数字是否有行内/列内/宫内冲突
print("\n[1] 检查已知数字内部冲突...")

def check_conflicts(known_digits, grid_size=16):
    conflicts = []
    
    # 行冲突
    row_vals = defaultdict(list)
    for kd in known_digits:
        row_vals[kd['row']].append(kd['value'])
    for r, vals in row_vals.items():
        if len(vals) != len(set(vals)):
            conflicts.append(f"行 {r} 有重复值: {vals}")
    
    # 列冲突
    col_vals = defaultdict(list)
    for kd in known_digits:
        col_vals[kd['col']].append(kd['value'])
    for c, vals in col_vals.items():
        if len(vals) != len(set(vals)):
            conflicts.append(f"列 {c} 有重复值: {vals}")
    
    # 宫冲突
    for br in range(4):
        for bc in range(4):
            box_vals = []
            for kd in known_digits:
                r, c = kd['row'], kd['col']
                if br*4+1 <= r <= (br+1)*4 and bc*4+1 <= c <= (bc+1)*4:
                    box_vals.append(kd['value'])
            if len(box_vals) != len(set(box_vals)):
                conflicts.append(f"宫 ({br},{bc}) 有重复值: {box_vals}")
    
    return conflicts

internal_conflicts = check_conflicts(config['known_digits'])
if internal_conflicts:
    print(f"  ✗ 发现 {len(internal_conflicts)} 个内部冲突:")
    for c in internal_conflicts[:10]:
        print(f"    - {c}")
else:
    print(f"  ✓ 已知数字内部无冲突")

# 2. 检查符阖排列约束
print("\n[2] 检查符阖排列约束一致性...")
fuhh_inconsistencies = []
for kd in config['known_digits']:
    row = kd['row']
    col = kd['col'] - 1  # 0-based
    val = kd['value']
    
    perms = config.get('fuhh_permutations', {}).get(row, [])
    if perms:
        allowed = set()
        for perm in perms:
            if col < len(perm):
                allowed.add(perm[col])
        if val not in allowed:
            fuhh_inconsistencies.append({
                'row': row,
                'col': kd['col'],
                'value': val,
                'allowed_count': len(allowed)
            })

if fuhh_inconsistencies:
    print(f"  ✗ 发现 {len(fuhh_inconsistencies)} 个符阖排列不一致:")
    for item in fuhh_inconsistencies[:10]:
        print(f"    - 行 {item['row']:2d}, 列 {item['col']:2d}: 值 {item['value']} 不在允许集合中")
else:
    print(f"  ✓ 所有已知数字符合符阖排列约束")

# 3. 增量添加已知数字，找到第一个导致不可解的位置
print("\n[3] 增量测试 - 找到导致不可解的临界点...")

# 按行组织已知数字
known_by_row = defaultdict(list)
for kd in config['known_digits']:
    known_by_row[kd['row']].append(kd)

# 逐行添加测试
fuhh = config.get('fuhh_permutations', {})

for test_row in range(1, 17):
    print(f"\n  测试添加行 {test_row} 的 {len(known_by_row[test_row])} 个已知数字...")
    
    # 构建当前行的模型
    model = cp_model.CpModel()
    test_known = {}
    
    # 添加前面所有行的已知数字
    for r in range(1, test_row + 1):
        for kd in known_by_row[r]:
            test_known[(r-1, kd['col']-1)] = kd['value']
    
    # 创建变量
    cells = {}
    for r in range(16):
        for c in range(16):
            if (r, c) in test_known:
                continue
            allowed = set(range(1, 17))
            if (r+1) in fuhh:
                perms = fuhh[r+1]
                allowed = set()
                for perm in perms:
                    if c < len(perm):
                        allowed.add(perm[c])
            if allowed:
                cells[(r, c)] = model.NewIntVarFromDomain(
                    cp_model.Domain.FromValues(sorted(allowed)), f'x_{r}_{c}')
            else:
                cells[(r, c)] = model.NewIntVar(1, 16, f'x_{r}_{c}')
    
    # 添加约束
    for r in range(16):
        row_vars = []
        for c in range(16):
            if (r, c) in cells:
                row_vars.append(cells[(r, c)])
            elif (r, c) in test_known:
                row_vars.append(test_known[(r, c)])
        if len(row_vars) > 1:
            model.AddAllDifferent(row_vars)
    
    for c in range(16):
        col_vars = []
        for r in range(16):
            if (r, c) in cells:
                col_vars.append(cells[(r, c)])
            elif (r, c) in test_known:
                col_vars.append(test_known[(r, c)])
        if len(col_vars) > 1:
            model.AddAllDifferent(col_vars)
    
    for br in range(4):
        for bc in range(4):
            box_vars = []
            for r in range(br*4, (br+1)*4):
                for c in range(bc*4, (bc+1)*4):
                    if (r, c) in cells:
                        box_vars.append(cells[(r, c)])
                    elif (r, c) in test_known:
                        box_vars.append(test_known[(r, c)])
            if len(box_vars) > 1:
                model.AddAllDifferent(box_vars)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.num_search_workers = 4
    solver.parameters.log_search_progress = False
    
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"    ✓ 可解")
    else:
        print(f"    ✗ 不可解! 问题出现在添加行 {test_row} 后")
        print(f"\n  🎯 关键发现: 行 {test_row} 的已知数字导致不可解")
        
        # 分析行 {test_row} 的已知数字
        print(f"\n  行 {test_row} 的已知数字详情:")
        for kd in known_by_row[test_row]:
            col = kd['col']
            val = kd['value']
            perms = fuhh.get(test_row, [])
            if perms:
                allowed = set(perm[col-1] for perm in perms if col-1 < len(perm))
                print(f"    列 {col:2d}: 值 {val:2d}, 允许值数量: {len(allowed):3d}")
            else:
                print(f"    列 {col:2d}: 值 {val:2d}, 无符阖约束")
        
        break

print(f"\n{'='*65}")
