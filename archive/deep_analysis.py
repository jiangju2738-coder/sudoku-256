#!/usr/bin/env python3
"""深入分析符阖排列与标准约束的冲突"""

import json
from collections import defaultdict

print("=" * 65)
print("🔍 深入分析符阖排列约束冲突")
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

def get_box(r, c):
    return (r // 4) * 4 + (c // 4)

print("\n分析每个未填格子的符阖排列允许值...")

# 检查每个未填格子
empty_cells = []
for r in range(16):
    for c in range(16):
        if (r, c) in known:
            continue
        
        # 符阖排列允许值
        perms = fuhh_permutations.get(r+1, [])
        if perms:
            fuhh_allowed = set()
            for perm in perms:
                if c < len(perm):
                    fuhh_allowed.add(perm[c])
        else:
            fuhh_allowed = set(range(1, 17))
        
        # 列已用值
        col_used = set()
        for r2 in range(16):
            if (r2, c) in known:
                col_used.add(known[(r2, c)])
        
        # 宫已用值
        box_used = set()
        br, bc = r // 4, c // 4
        for r2 in range(br*4, (br+1)*4):
            for c2 in range(bc*4, (bc+1)*4):
                if (r2, c2) in known:
                    box_used.add(known[(r2, c2)])
        
        # 有效允许值 = 符阖排列允许值 - 列已用值 - 宫已用值
        valid_allowed = fuhh_allowed - col_used - box_used
        
        if len(valid_allowed) == 0:
            empty_cells.append({
                'row': r + 1,
                'col': c + 1,
                'fuhh_allowed': fuhh_allowed,
                'col_used': col_used,
                'box_used': box_used,
                'fuhh_size': len(fuhh_allowed)
            })

print(f"\n发现 {len(empty_cells)} 个空域格子:")

# 按符阖排列允许值数量排序
empty_cells.sort(key=lambda x: x['fuhh_size'])

for cell in empty_cells[:30]:
    print(f"\n  行 {cell['row']:2d}, 列 {cell['col']:2d}:")
    print(f"    符阖排列允许值: {len(cell['fuhh_allowed']):2d} 个 → {sorted(cell['fuhh_allowed'])[:10]}")
    print(f"    列已用值: {len(cell['col_used'])} 个 → {sorted(cell['col_used'])}")
    print(f"    宫已用值: {len(cell['box_used'])} 个 → {sorted(cell['box_used'])}")
    print(f"    有效允许值: 0 个 (空域!)")

# 统计
print(f"\n{'='*65}")
print("📊 统计摘要")
print("=" * 65)

print(f"\n符阖排列允许值 ≤ 2 的格子:")
for r in range(16):
    for c in range(16):
        if (r, c) in known:
            continue
        perms = fuhh_permutations.get(r+1, [])
        if perms:
            allowed = set()
            for perm in perms:
                if c < len(perm):
                    allowed.add(perm[c])
            if len(allowed) <= 2:
                print(f"  行 {r+1:2d}, 列 {c+1:2d}: {len(allowed)} 个允许值")

print(f"\n结论:")
print(f"  符阖排列约束使得某些格子的允许值极少（≤2 个）")
print(f"  当这些格子所在列/宫已用值覆盖了所有符阖排列允许值时，导致空域")
print(f"  这是符阖排列约束与标准数独约束的内在冲突")

print(f"\n建议:")
print(f"  1. 减少已知数字数量（降低约束强度）")
print(f"  2. 选择符阖排列允许值较多的格子作为已知数字")
print(f"  3. 或者接受：符阖排列约束下的 92 个已知数字可能无解")

print(f"\n{'='*65}")
