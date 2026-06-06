#!/usr/bin/env python3
"""验证 55 个已知数字的可求解性"""

import json
from ortools.sat.python import cp_model
import time

print("=" * 65)
print("🚀 验证 55 个已知数字的可求解性")
print("=" * 65)

with open('sudoku_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

for row_num in range(1, 17):
    filename = f"A{row_num}_permutations.json"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            config.setdefault('fuhh_permutations', {})[row_num] = data
    except:
        pass

from collections import defaultdict
row_count = defaultdict(int)
for kd in config['known_digits']:
    row_count[kd['row']] += 1

print(f"\n📊 配置摘要:")
print(f"  {'行':>4} {'已知':>6} {'剩余':>6}")
for r in range(1, 17):
    known = row_count.get(r, 0)
    print(f"  {r:>4} {known:>6} {16-known:>6}")
print(f"  {'总计':>4} {len(config['known_digits']):>6}")

model = cp_model.CpModel()
known = {(kd['row']-1, kd['col']-1): kd['value'] for kd in config['known_digits']}
fuhh = config.get('fuhh_permutations', {})

cells = {}
for r in range(16):
    for c in range(16):
        if (r, c) in known:
            continue
        allowed = set(range(1, 17))
        if (r+1) in fuhh:
            perms = fuhh[r+1]
            allowed = set(perm[c] for perm in perms if c < len(perm))
        if allowed:
            cells[(r, c)] = model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(sorted(allowed)), f'x_{r}_{c}')

for r in range(16):
    row_vars = [cells.get((r, c), known.get((r, c))) for c in range(16) if (r, c) in cells or (r, c) in known]
    if len(row_vars) > 1:
        model.AddAllDifferent(row_vars)

for c in range(16):
    col_vars = [cells.get((r, c), known.get((r, c))) for r in range(16) if (r, c) in cells or (r, c) in known]
    if len(col_vars) > 1:
        model.AddAllDifferent(col_vars)

for br in range(4):
    for bc in range(4):
        box_vars = [cells.get((r, c), known.get((r, c))) for r in range(br*4,(br+1)*4) for c in range(bc*4,(bc+1)*4) if (r, c) in cells or (r, c) in known]
        if len(box_vars) > 1:
            model.AddAllDifferent(box_vars)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60
solver.parameters.num_search_workers = 8
solver.parameters.log_search_progress = True

print(f"\n开始求解...")
start = time.time()
status = solver.Solve(model)
elapsed = time.time() - start

print(f"\n{'='*65}")
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"✅ 找到可行解! 耗时: {elapsed:.2f} 秒")
    solution = {**known}
    for k, var in cells.items():
        solution[k] = solver.Value(var)
    
    print(f"\n解网格:")
    print("  " + " ".join(f"{c:2d}" for c in range(1, 17)))
    for r in range(16):
        row_str = f"  {r+1:2d} "
        for c in range(16):
            if c % 4 == 0 and c > 0:
                row_str += " | "
            row_str += f"{solution.get((r, c), '?'):2d}"
        print(row_str)
        if (r + 1) % 4 == 0 and r < 15:
            print("  " + "-" * 62)
else:
    print(f"✗ 无解 (status={status})")
print(f"{'='*65}")
