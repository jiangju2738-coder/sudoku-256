#!/usr/bin/env python3
"""验证新配置的 CP-SAT 可求解性"""

import json
from ortools.sat.python import cp_model
import time
from collections import defaultdict

print("=" * 65)
print("🚀 验证新配置的 CP-SAT 可求解性")
print("=" * 65)

# 加载更新后的配置
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

# 统计分布
row_count = defaultdict(int)
for kd in config['known_digits']:
    row_count[kd['row']] += 1

print(f"\n📊 更新后的已知数字分布:")
target_dist = [7, 7, 8, 6, 10, 6, 4, 5, 6, 1, 2, 7, 6, 7, 6, 4]
print(f"  {'行':>4} {'已知数':>8} {'目标':>8} {'剩余':>8}")
print(f"  {'-'*4} {'-'*8} {'-'*8} {'-'*8}")
for r in range(1, 17):
    known = row_count.get(r, 0)
    target = target_dist[r-1]
    remaining = 16 - known
    print(f"  {r:>4} {known:>8} {target:>8} {remaining:>8}")
print(f"  {'总计':>4} {len(config['known_digits']):>8} {sum(target_dist):>8}")

# 构建 CP-SAT 模型
print(f"\n构建 CP-SAT 模型...")

model = cp_model.CpModel()
known = {(kd['row']-1, kd['col']-1): kd['value'] for kd in config['known_digits']}
fuhh = config.get('fuhh_permutations', {})

cells = {}
for r in range(16):
    for c in range(16):
        if (r, c) in known:
            continue
        
        # 符阖排列约束
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
            #  fallback
            cells[(r, c)] = model.NewIntVar(1, 16, f'x_{r}_{c}')

# 行 AllDifferent
for r in range(16):
    row_vars = []
    for c in range(16):
        if (r, c) in cells:
            row_vars.append(cells[(r, c)])
        elif (r, c) in known:
            row_vars.append(known[(r, c)])
    if len(row_vars) > 1:
        model.AddAllDifferent(row_vars)

# 列 AllDifferent
for c in range(16):
    col_vars = []
    for r in range(16):
        if (r, c) in cells:
            col_vars.append(cells[(r, c)])
        elif (r, c) in known:
            col_vars.append(known[(r, c)])
    if len(col_vars) > 1:
        model.AddAllDifferent(col_vars)

# 宫 AllDifferent
for br in range(4):
    for bc in range(4):
        box_vars = []
        for r in range(br*4, (br+1)*4):
            for c in range(bc*4, (bc+1)*4):
                if (r, c) in cells:
                    box_vars.append(cells[(r, c)])
                elif (r, c) in known:
                    box_vars.append(known[(r, c)])
        if len(box_vars) > 1:
            model.AddAllDifferent(box_vars)

# 求解
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60
solver.parameters.num_search_workers = 8
solver.parameters.log_search_progress = False

print(f"开始求解...")
start = time.time()
status = solver.Solve(model)
elapsed = time.time() - start

print(f"\n{'='*65}")
print("📊 求解结果")
print("=" * 65)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"✅ 找到可行解!")
    print(f"   耗时: {elapsed:.2f} 秒")
    
    # 构建解网格
    solution = {}
    for k, v in known.items():
        solution[k] = v
    for k, var in cells.items():
        solution[k] = solver.Value(var)
    
    print(f"\n解网格 (16×16):")
    print("  " + " ".join(f"{c:2d}" for c in range(1, 17)))
    for r in range(16):
        row_str = f"  {r+1:2d} "
        for c in range(16):
            if c % 4 == 0 and c > 0:
                row_str += " | "
            val = solution.get((r, c), '?')
            row_str += f"{val:2d}"
        print(row_str)
        if (r + 1) % 4 == 0 and r < 15:
            print("  " + "-" * 62)
    
    # 验证
    print(f"\n验证解的正确性...")
    errors = []
    for r in range(16):
        row_vals = [solution[(r, c)] for c in range(16)]
        if len(row_vals) != len(set(row_vals)):
            errors.append(f"行 {r+1} 有重复")
    for c in range(16):
        col_vals = [solution[(r, c)] for r in range(16)]
        if len(col_vals) != len(set(col_vals)):
            errors.append(f"列 {c+1} 有重复")
    for br in range(4):
        for bc in range(4):
            box_vals = []
            for r in range(br*4, (br+1)*4):
                for c in range(bc*4, (bc+1)*4):
                    box_vals.append(solution[(r, c)])
            if len(box_vals) != len(set(box_vals)):
                errors.append(f"宫 ({br},{bc}) 有重复")
    
    if errors:
        print(f"  ✗ 发现 {len(errors)} 个错误:")
        for e in errors[:5]:
            print(f"    - {e}")
    else:
        print(f"  ✅ 验证通过!")
    
else:
    print(f"✗ 无解 (status={status})")
    print(f"   可能原因:")
    print(f"   1. 已知数字冲突")
    print(f"   2. 符阖排列约束过强")
    print(f"   3. 超时")

print(f"\n{'='*65}")
