#!/usr/bin/env python3
"""
生成符阖排列约束下可解的配置
目标：约 54 个已知数字（临界点以下）
"""

import json
import random
from collections import defaultdict

# 修改目标分布：减少已知数字数量
# 原始: [7, 7, 8, 6, 10, 6, 4, 5, 6, 1, 2, 7, 6, 7, 6, 4] = 92
# 调整后: 减少每行的已知数字，目标约 54 个

TARGET_DISTRIBUTION = [4, 4, 5, 4, 5, 4, 3, 3, 4, 1, 2, 4, 3, 4, 3, 2]  # 总计 55
# 或者保持分布比例，减少数量

print("=" * 65)
print("📝 生成符阖排列约束下可解的配置")
print("=" * 65)

print(f"\n目标分布: {TARGET_DISTRIBUTION}")
print(f"总计: {sum(TARGET_DISTRIBUTION)} 个已知数字")

# 加载符阖排列
fuhh_permutations = {}
for row_num in range(1, 17):
    filename = f"A{row_num}_permutations.json"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            fuhh_permutations[row_num] = json.load(f)
    except:
        fuhh_permutations[row_num] = []

random.seed(20260514)

new_known_digits = []
used_in_col = defaultdict(set)
used_in_box = defaultdict(set)

def get_box(r, c):
    return (r // 4) * 4 + (c // 4)

for row in range(1, 17):
    target_count = TARGET_DISTRIBUTION[row - 1]
    perms = fuhh_permutations.get(row, [])
    
    if not perms:
        continue
    
    # 选择模板
    template = random.choice(perms)
    
    # 计算每列的约束强度
    col_constraint_strength = []
    for c in range(16):
        allowed = set()
        for perm in perms:
            if c < len(perm):
                allowed.add(perm[c])
        col_constraint_strength.append((len(allowed), c))
    
    col_constraint_strength.sort()  # 优先选择约束强的列
    
    selected = []
    used_values = set()
    
    for _, c in col_constraint_strength:
        if len(selected) >= target_count:
            break
        if c in [s[0] for s in selected]:
            continue
        
        val = template[c]
        if val in used_in_col[c]:
            continue
        if val in used_in_box[get_box(row - 1, c)]:
            continue
        if val in used_values:
            continue
        
        selected.append((c, val))
        used_values.add(val)
    
    # 如果未达到，放宽约束
    if len(selected) < target_count:
        for c in range(16):
            if len(selected) >= target_count:
                break
            if c in [s[0] for s in selected]:
                continue
            val = template[c]
            selected.append((c, val))
            used_values.add(val)
    
    # 添加到结果
    for c, v in selected:
        new_known_digits.append({
            'row': row,
            'col': c + 1,
            'value': v
        })
        used_in_col[c].add(v)
        used_in_box[get_box(row - 1, c)].add(v)
    
    print(f"  行 {row:2d}: {len(selected):2d}/{target_count:2d}")

# 验证
print(f"\n{'='*65}")
print("📊 验证配置")
print("=" * 65)

row_count = defaultdict(int)
for kd in new_known_digits:
    row_count[kd['row']] += 1

print(f"\n分布验证:")
for r in range(1, 17):
    count = row_count.get(r, 0)
    target = TARGET_DISTRIBUTION[r - 1]
    match = '✓' if count == target else '✗'
    print(f"  行 {r:2d}: {count:2d}/{target:2d} {match}")
print(f"  总计: {len(new_known_digits)}")

# 符阖一致性
fuhh_ok = sum(1 for kd in new_known_digits
              if kd['value'] in set(perm[kd['col']-1] for perm in fuhh_permutations.get(kd['row'], []) if kd['col']-1 < len(perm)))
print(f"符阖一致: {fuhh_ok}/{len(new_known_digits)}")

# 行/列/宫冲突
row_vals = defaultdict(list)
col_vals = defaultdict(list)
box_vals = defaultdict(list)
for kd in new_known_digits:
    row_vals[kd['row']].append(kd['value'])
    col_vals[kd['col']].append(kd['value'])
    box_vals[get_box(kd['row']-1, kd['col']-1)].append(kd['value'])

row_conflicts = sum(1 for vals in row_vals.values() if len(vals) != len(set(vals)))
col_conflicts = sum(1 for vals in col_vals.values() if len(vals) != len(set(vals)))
box_conflicts = sum(1 for vals in box_vals.values() if len(vals) != len(set(vals)))

print(f"行内冲突: {row_conflicts}")
print(f"列内冲突: {col_conflicts}")
print(f"宫内冲突: {box_conflicts}")

# 保存
config = {
    'grid_size': 16,
    'box_size': 4,
    'known_digits': new_known_digits
}

with open('sudoku_config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"\n✅ 配置已保存至 sudoku_config.json")
print(f"{'='*65}")
