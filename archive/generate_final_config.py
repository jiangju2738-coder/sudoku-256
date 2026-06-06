#!/usr/bin/env python3
"""生成符阖排列约束下的一致已知数字配置 - 最终版"""

import json
import random
from collections import defaultdict

TARGET_DISTRIBUTION = [7, 7, 8, 6, 10, 6, 4, 5, 6, 1, 2, 7, 6, 7, 6, 4]

print("=" * 65)
print("📝 生成符阖排列约束下的一致已知数字配置")
print("=" * 65)

# 加载符阖排列
fuhh_permutations = {}
for row_num in range(1, 17):
    filename = f"A{row_num}_permutations.json"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            perms = json.load(f)
            fuhh_permutations[row_num] = perms
    except:
        fuhh_permutations[row_num] = [list(range(1, 17))] * 100

def get_box(r, c):
    return (r // 4) * 4 + (c // 4)

random.seed(20260514)

# 全局已用值跟踪
used_in_row = defaultdict(set)
used_in_col = defaultdict(set)
used_in_box = defaultdict(set)

new_known_digits = []

for row in range(1, 17):
    target_count = TARGET_DISTRIBUTION[row - 1]
    perms = fuhh_permutations.get(row, [])
    
    # 计算每列的允许值（考虑符阖排列）
    col_candidates = {}
    for c in range(16):
        allowed = set()
        for perm in perms:
            if c < len(perm):
                allowed.add(perm[c])
        # 移除已在行内使用的值
        allowed -= used_in_row[row]
        col_candidates[c] = allowed
    
    # 选择 target_count 个位置，确保行内值不重复
    selected = []  # (col, value) 对
    used_values_in_row = set()
    
    # 按约束强度排序：优先选择候选值少的列
    sorted_cols = sorted(range(16), key=lambda c: len(col_candidates[c]))
    
    for c in sorted_cols:
        if len(selected) >= target_count:
            break
        
        if c in [s[0] for s in selected]:
            continue
        
        # 获取该列的可用值（排除列内、宫内、行内已用值）
        allowed = col_candidates[c].copy()
        allowed -= used_in_col[c]
        allowed -= used_in_box[get_box(row - 1, c)]
        allowed -= used_values_in_row  # 确保行内不重复
        
        if allowed:
            val = random.choice(list(allowed))
            selected.append((c, val))
            used_values_in_row.add(val)
    
    # 如果未达到目标数量，使用备用策略
    if len(selected) < target_count:
        remaining = target_count - len(selected)
        available_cols = [c for c in range(16) if c not in [s[0] for s in selected]]
        
        for c in available_cols[:remaining]:
            # 允许更宽松的选择
            allowed = set(range(1, 17))
            allowed -= used_in_col[c]
            allowed -= used_in_box[get_box(row - 1, c)]
            allowed -= used_values_in_row
            
            if not allowed:
                # 即使违反行内约束也要选择（最终会冲突）
                allowed = set(range(1, 17)) - used_in_col[c] - used_in_box[get_box(row - 1, c)]
            
            if allowed:
                val = random.choice(list(allowed))
                selected.append((c, val))
                used_values_in_row.add(val)
    
    # 添加到结果并更新全局状态
    for c, v in selected:
        new_known_digits.append({
            'row': row,
            'col': c + 1,
            'value': v
        })
        used_in_row[row].add(v)
        used_in_col[c].add(v)
        used_in_box[get_box(row - 1, c)].add(v)
    
    # 打印进度
    status = '✓' if len(selected) == target_count else f'⚠️ ({len(selected)}/{target_count})'
    print(f"  行 {row:2d}: {len(selected):2d}/{target_count:2d} {status}")

# 验证配置
print(f"\n{'='*65}")
print("📊 验证生成的配置")
print("=" * 65)

# 1. 分布
row_count = defaultdict(int)
for kd in new_known_digits:
    row_count[kd['row']] += 1

print(f"\n分布验证:")
for r in range(1, 17):
    count = row_count.get(r, 0)
    target = TARGET_DISTRIBUTION[r - 1]
    match = '✓' if count == target else '✗'
    print(f"  行 {r:2d}: {count:2d}/{target:2d} {match}")
print(f"  总计: {len(new_known_digits)}/{sum(TARGET_DISTRIBUTION)}")

# 2. 行内冲突
row_vals = defaultdict(list)
for kd in new_known_digits:
    row_vals[kd['row']].append(kd['value'])

row_conflicts = [(r, [v for v in set(vals) if vals.count(v) > 1]) 
                 for r, vals in row_vals.items() if len(vals) != len(set(vals))]

print(f"\n行内冲突: {len(row_conflicts)} 个")
for r, dups in row_conflicts[:5]:
    print(f"  行 {r}: 重复值 {dups}")

# 3. 列内冲突
col_vals = defaultdict(list)
for kd in new_known_digits:
    col_vals[kd['col']].append(kd['value'])

col_conflicts = [(c, [v for v in set(vals) if vals.count(v) > 1]) 
                 for c, vals in col_vals.items() if len(vals) != len(set(vals))]

print(f"列内冲突: {len(col_conflicts)} 个")
for c, dups in col_conflicts[:5]:
    print(f"  列 {c}: 重复值 {dups}")

# 4. 宫内冲突
box_vals = defaultdict(list)
for kd in new_known_digits:
    r, c = kd['row'] - 1, kd['col'] - 1
    box_vals[get_box(r, c)].append(kd['value'])

box_conflicts = [(b, [v for v in set(vals) if vals.count(v) > 1]) 
                 for b, vals in box_vals.items() if len(vals) != len(set(vals))]

print(f"宫内冲突: {len(box_conflicts)} 个")

# 5. 符阖排列一致性
fuhh_inconsistent = 0
for kd in new_known_digits:
    row, col = kd['row'], kd['col'] - 1
    val = kd['value']
    perms = fuhh_permutations.get(row, [])
    if perms:
        allowed = set(perm[col] for perm in perms if col < len(perm))
        if val not in allowed:
            fuhh_inconsistent += 1

print(f"符阖排列不一致: {fuhh_inconsistent} 个")

# 保存
config = {
    'grid_size': 16,
    'box_size': 4,
    'known_digits': new_known_digits,
    'fuhh_permutations': {k: v[:100] for k, v in fuhh_permutations.items()}
}

with open('sudoku_config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

total_conflicts = len(row_conflicts) + len(col_conflicts) + len(box_conflicts) + fuhh_inconsistent

print(f"\n{'='*65}")
if total_conflicts == 0:
    print(f"✅ 配置完全一致！")
else:
    print(f"⚠️ 总冲突数: {total_conflicts}")
print(f"{'='*65}")
