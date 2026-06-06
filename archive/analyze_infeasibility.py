#!/usr/bin/env python3
"""分析 CP-SAT 预处理不可解的原因"""

import json
from collections import defaultdict

print("=" * 65)
print("🔍 分析不可解原因")
print("=" * 65)

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

# 计算每个宫、行、列的已知数字数量和可用值数量
def get_box(r, c):
    return (r // 4) * 4 + (c // 4)

print("\n[1] 检查每个宫的冲突...")

for box_id in range(16):
    br, bc = divmod(box_id, 4)
    
    # 该宫的已知数字
    known_in_box = []
    all_known_vals = set()
    for r in range(br*4, (br+1)*4):
        for c in range(bc*4, (bc+1)*4):
            if (r, c) in known:
                known_in_box.append((r+1, c+1, known[(r,c)]))
                all_known_vals.add(known[(r,c)])
    
    # 该宫每个格子的符阖排列允许值交集
    intersection_allowed = set(range(1, 17))
    for r in range(br*4, (br+1)*4):
        for c in range(bc*4, (bc+1)*4):
            perms = fuhh_permutations.get(r+1, [])
            if perms:
                col_allowed = set()
                for perm in perms:
                    if c < len(perm):
                        col_allowed.add(perm[c])
                intersection_allowed &= col_allowed
    
    if len(known_in_box) > len(intersection_allowed):
        print(f"\n  ✗ 宫 {box_id} (行{br*4+1}-{br*4+4}, 列{bc*4+1}-{bc*4+4}):")
        print(f"    已知数字: {len(known_in_box)} 个")
        print(f"    符阖排列交集允许值: {len(intersection_allowed)} 个")
        print(f"    冲突: {len(known_in_box)} > {len(intersection_allowed)}")
        print(f"    已知值: {sorted(all_known_vals)}")
        print(f"    允许值: {sorted(intersection_allowed)}")
        missing = all_known_vals - intersection_allowed
        if missing:
            print(f"    不在允许集合中的值: {sorted(missing)}")

print("\n[2] 检查每行的冲突...")

for row in range(1, 17):
    known_in_row = [(kd['col'], kd['value']) for kd in config['known_digits'] if kd['row'] == row]
    
    # 符阖排列允许值
    perms = fuhh_permutations.get(row, [])
    if perms:
        # 每列的允许值
        col_allowed = {}
        for c in range(16):
            allowed = set()
            for perm in perms:
                if c < len(perm):
                    allowed.add(perm[c])
            col_allowed[c] = allowed
    
    # 检查是否有列的允许值只包含一个值（导致冲突）
    for c, val in known_in_row:
        if c-1 in col_allowed:
            allowed = col_allowed[c-1]
            if len(allowed) == 1 and val not in allowed:
                print(f"  ✗ 行 {row}, 列 {c}: 值 {val} 不在唯一允许值 {allowed} 中")

print("\n[3] 详细检查每个宫的符阖排列允许值...")

for box_id in range(16):
    br, bc = divmod(box_id, 4)
    
    print(f"\n  宫 {box_id} (行{br*4+1}-{br*4+4}, 列{bc*4+1}-{bc*4+4}):")
    
    for r in range(br*4, (br+1)*4):
        row_vals = []
        for c in range(bc*4, (bc+1)*4):
            perms = fuhh_permutations.get(r+1, [])
            if perms:
                allowed = set()
                for perm in perms:
                    if c < len(perm):
                        allowed.add(perm[c])
                row_vals.append(len(allowed))
            else:
                row_vals.append(16)
        print(f"    行 {r+1}: {row_vals}")

print("\n[4] 找出关键冲突...")

# 检查哪些宫/行/列的符阖排列允许值太少
critical_cells = []
for r in range(16):
    for c in range(16):
        perms = fuhh_permutations.get(r+1, [])
        if perms:
            allowed = set()
            for perm in perms:
                if c < len(perm):
                    allowed.add(perm[c])
            if len(allowed) <= 2:
                critical_cells.append((r+1, c+1, len(allowed)))

print(f"\n符阖排列允许值 ≤ 2 的格子 ({len(critical_cells)} 个):")
for r, c, n in critical_cells[:20]:
    print(f"  行 {r:2d}, 列 {c:2d}: {n} 个允许值")

print(f"\n{'='*65}")
