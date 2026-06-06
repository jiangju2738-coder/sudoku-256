#!/usr/bin/env python3
"""
生成符阖排列约束下的一致已知数字配置
关键：每行必须从该行的符阖排列集合中选择一个排列
"""

import json
import random
from collections import defaultdict

TARGET_DISTRIBUTION = [7, 7, 8, 6, 10, 6, 4, 5, 6, 1, 2, 7, 6, 7, 6, 4]

print("=" * 65)
print("📝 生成符阖排列约束下的一致配置（正确方法）")
print("=" * 65)

# 加载符阖排列
fuhh_permutations = {}
for row_num in range(1, 17):
    filename = f"A{row_num}_permutations.json"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            fuhh_permutations[row_num] = json.load(f)
    except:
        print(f"  ⚠️ A{row_num}.json 未找到")
        fuhh_permutations[row_num] = []

print(f"\n符阖排列加载:")
for r in range(1, 17):
    perms = fuhh_permutations.get(r, [])
    print(f"  A{r}: {len(perms):,} 个符阖排列")

# 关键策略：
# 1. 每行从符阖排列中选择一个排列作为"模板"
# 2. 从该模板中选择 target_count 个位置作为已知数字
# 3. 确保行内、列内、宫内不重复

random.seed(20260514)

new_known_digits = []

# 全局已用值跟踪
used_in_col = defaultdict(set)
used_in_box = defaultdict(set)

def get_box(r, c):
    return (r // 4) * 4 + (c // 4)

for row in range(1, 17):
    target_count = TARGET_DISTRIBUTION[row - 1]
    perms = fuhh_permutations.get(row, [])
    
    if not perms:
        print(f"  ✗ 行 {row}: 无符阖排列!")
        continue
    
    # 从符阖排列中随机选择一个作为模板
    template = random.choice(perms)
    print(f"  行 {row:2d}: 选择模板 (前 8 个值: {template[:8]})")
    
    # 从模板中选择 target_count 个位置
    # 优先选择符阖排列允许值少的列（约束强的位置）
    
    # 计算每列的符阖排列允许值数量
    col_constraint_strength = []
    for c in range(16):
        allowed = set()
        for perm in perms:
            if c < len(perm):
                allowed.add(perm[c])
        col_constraint_strength.append((len(allowed), c))
    
    # 按约束强度排序（优先选择约束强的列）
    col_constraint_strength.sort()
    
    selected = []
    used_values = set()
    
    for _, c in col_constraint_strength:
        if len(selected) >= target_count:
            break
        
        if c in [s[0] for s in selected]:
            continue
        
        # 获取该位置的值（从模板中）
        val = template[c]
        
        # 检查是否与列内、宫内已用值冲突
        if val in used_in_col[c]:
            continue
        if val in used_in_box[get_box(row - 1, c)]:
            continue
        if val in used_values:  # 行内不重复
            continue
        
        selected.append((c, val))
        used_values.add(val)
    
    # 如果未达到目标数量，使用备选策略
    if len(selected) < target_count:
        # 从模板中选择其他位置
        for c in range(16):
            if len(selected) >= target_count:
                break
            if c in [s[0] for s in selected]:
                continue
            
            val = template[c]
            
            # 即使有冲突也要选择（符阖排列优先）
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
    
    print(f"    选择 {len(selected)}/{target_count} 个")

print(f"\n{'='*65}")
print("📊 验证配置")
print("=" * 65)

# 1. 分布验证
row_count = defaultdict(int)
for kd in new_known_digits:
    row_count[kd['row']] += 1

print(f"\n分布验证:")
all_match = True
for r in range(1, 17):
    count = row_count.get(r, 0)
    target = TARGET_DISTRIBUTION[r - 1]
    match = '✓' if count == target else '✗'
    if count != target:
        all_match = False
    print(f"  行 {r:2d}: {count:2d}/{target:2d} {match}")
print(f"  总计: {len(new_known_digits)}/{sum(TARGET_DISTRIBUTION)}")

# 2. 符阖排列一致性
print(f"\n符阖排列一致性:")
fuhh_ok = 0
fuhh_bad = 0
for kd in new_known_digits:
    row, col = kd['row'], kd['col'] - 1
    val = kd['value']
    perms = fuhh_permutations.get(row, [])
    if perms:
        allowed = set(perm[col] for perm in perms if col < len(perm))
        if val in allowed:
            fuhh_ok += 1
        else:
            fuhh_bad += 1

print(f"  ✓ 符阖一致: {fuhh_ok}")
print(f"  ✗ 符阖不一致: {fuhh_bad}")

# 3. 行内冲突
row_vals = defaultdict(list)
for kd in new_known_digits:
    row_vals[kd['row']].append(kd['value'])

row_conflicts = [(r, [v for v in set(vals) if vals.count(v) > 1])
                 for r, vals in row_vals.items() if len(vals) != len(set(vals))]
print(f"\n行内冲突: {len(row_conflicts)} 个")

# 4. 列内冲突
col_vals = defaultdict(list)
for kd in new_known_digits:
    col_vals[kd['col']].append(kd['value'])

col_conflicts = [(c, [v for v in set(vals) if vals.count(v) > 1])
                 for c, vals in col_vals.items() if len(vals) != len(set(vals))]
print(f"列内冲突: {len(col_conflicts)} 个")

# 5. 宫内冲突
box_vals = defaultdict(list)
for kd in new_known_digits:
    r, c = kd['row'] - 1, kd['col'] - 1
    box_vals[get_box(r, c)].append(kd['value'])

box_conflicts = [(b, [v for v in set(vals) if vals.count(v) > 1])
                 for b, vals in box_vals.items() if len(vals) != len(set(vals))]
print(f"宫内冲突: {len(box_conflicts)} 个")

# 保存
config = {
    'grid_size': 16,
    'box_size': 4,
    'known_digits': new_known_digits
}

with open('sudoku_config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

total_conflicts = len(row_conflicts) + len(col_conflicts) + len(box_conflicts) + fuhh_bad

print(f"\n{'='*65}")
print(f"配置已保存至 sudoku_config.json")
print(f"{'='*65}")
