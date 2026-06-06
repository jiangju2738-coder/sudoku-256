#!/usr/bin/env python3
"""生成符阖排列约束下的一致已知数字配置"""

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

# 计算每行每列每宫允许的候选值
def get_allowed_values(row, col, fuhh):
    """获取某格在符阖排列下的允许值"""
    perms = fuhh.get(row, [])
    if not perms:
        return set(range(1, 17))
    allowed = set()
    for perm in perms:
        if col < len(perm):
            allowed.add(perm[col])
    return allowed

# 生成一致配置
random.seed(20260514)  # 确定性

new_known_digits = []
used_in_row = defaultdict(set)    # 行内已用值
used_in_col = defaultdict(set)    # 列内已用值
used_in_box = defaultdict(set)    # 宫内已用值

def get_box(r, c):
    return (r // 4) * 4 + (c // 4)

for row in range(1, 17):
    target_count = TARGET_DISTRIBUTION[row - 1]
    
    # 获取该行的符阖排列
    perms = fuhh_permutations.get(row, [])
    
    # 计算每列的允许值
    col_allowed = {}
    for c in range(16):
        allowed = set()
        for perm in perms:
            if c < len(perm):
                allowed.add(perm[c])
        # 移除已在行内使用的值
        allowed -= used_in_row[row]
        col_allowed[c] = allowed
    
    # 贪心选择位置
    selected = []
    
    for attempt in range(1000):  # 最大尝试次数
        if len(selected) >= target_count:
            break
        
        # 从有最多可用值的列中选择
        candidates = []
        for c in range(16):
            if c not in [s[0] for s in selected]:  # 未选中
                # 检查列和宫
                if not (TARGET_DISTRIBUTION[row-1] - len(selected) > 16 - len(selected)):
                    pass
                candidates.append((len(col_allowed[c]), c))
        
        if not candidates:
            break
        
        # 按可用值数量排序，优先选择约束强的列
        candidates.sort(reverse=True)
        _, best_col = candidates[0]
        
        # 从该列的允许值中选择一个
        allowed = col_allowed[best_col]
        allowed -= used_in_col[best_col]
        box_id = get_box(row - 1, best_col)
        allowed -= used_in_box[box_id]
        
        if not allowed:
            # 尝试其他列
            for _, c in candidates[1:]:
                allowed = col_allowed[c]
                allowed -= used_in_col[c]
                allowed -= used_in_box[get_box(row - 1, c)]
                if allowed:
                    best_col = c
                    break
            else:
                break
        
        val = random.choice(list(allowed))
        selected.append((best_col, val))
        
        # 更新已用值
        used_in_row[row].add(val)
        used_in_col[best_col].add(val)
        used_in_box[get_box(row - 1, best_col)].add(val)
    
    # 如果未达到目标数量，使用回溯/重新尝试
    if len(selected) < target_count:
        # 记录失败，稍后重试
        print(f"  ⚠️ 行 {row}: 只选择了 {len(selected)}/{target_count} 个，将重试...")
        # 重置该行
        for c, v in selected:
            used_in_row[row].discard(v)
            used_in_col[c].discard(v)
            used_in_box[get_box(row - 1, c)].discard(v)
        # 用简单随机选择
        available_cols = list(range(16))
        selected_cols = random.sample(available_cols, min(target_count, 16))
        selected = []
        for c in selected_cols:
            allowed = set(range(1, 17))
            allowed -= used_in_row[row]
            allowed -= used_in_col[c]
            allowed -= used_in_box[get_box(row - 1, c)]
            if allowed:
                val = random.choice(list(allowed))
                selected.append((c, val))
                used_in_row[row].add(val)
                used_in_col[c].add(val)
                used_in_box[get_box(row - 1, c)].add(val)
    
    # 添加到结果
    for c, v in selected:
        new_known_digits.append({
            'row': row,
            'col': c + 1,
            'value': v
        })

# 验证配置
print(f"\n{'='*65}")
print("📊 验证生成的配置")
print("=" * 65)

# 1. 检查分布
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

# 2. 检查行内冲突
print(f"\n行内冲突检查:")
row_vals = defaultdict(list)
for kd in new_known_digits:
    row_vals[kd['row']].append(kd['value'])

row_conflicts = []
for r, vals in row_vals.items():
    if len(vals) != len(set(vals)):
        duplicates = [v for v in set(vals) if vals.count(v) > 1]
        row_conflicts.append(f"行 {r}: {duplicates}")

if row_conflicts:
    print(f"  ✗ {len(row_conflicts)} 个行冲突")
    for c in row_conflicts:
        print(f"    - {c}")
else:
    print(f"  ✓ 无行内冲突")

# 3. 检查列内冲突
print(f"\n列内冲突检查:")
col_vals = defaultdict(list)
for kd in new_known_digits:
    col_vals[kd['col']].append(kd['value'])

col_conflicts = []
for c, vals in col_vals.items():
    if len(vals) != len(set(vals)):
        duplicates = [v for v in set(vals) if vals.count(v) > 1]
        col_conflicts.append(f"列 {c}: {duplicates}")

if col_conflicts:
    print(f"  ✗ {len(col_conflicts)} 个列冲突")
    for c in col_conflicts[:10]:
        print(f"    - {c}")
else:
    print(f"  ✓ 无列内冲突")

# 4. 检查宫内冲突
print(f"\n宫内冲突检查:")
box_vals = defaultdict(list)
for kd in new_known_digits:
    r, c = kd['row'] - 1, kd['col'] - 1
    box_id = get_box(r, c)
    box_vals[box_id].append(kd['value'])

box_conflicts = []
for b, vals in box_vals.items():
    if len(vals) != len(set(vals)):
        duplicates = [v for v in set(vals) if vals.count(v) > 1]
        box_conflicts.append(f"宫 {b}: {duplicates}")

if box_conflicts:
    print(f"  ✗ {len(box_conflicts)} 个宫冲突")
    for c in box_conflicts:
        print(f"    - {c}")
else:
    print(f"  ✓ 无宫内冲突")

# 5. 检查符阖排列一致性
print(f"\n符阖排列一致性检查:")
fuhh_inconsistent = []
for kd in new_known_digits:
    row = kd['row']
    col = kd['col'] - 1
    val = kd['value']
    
    perms = fuhh_permutations.get(row, [])
    if perms:
        allowed = set()
        for perm in perms:
            if col < len(perm):
                allowed.add(perm[col])
        if val not in allowed:
            fuhh_inconsistent.append(f"行 {row}, 列 {kd['col']}: {val} 不在允许集合中")

if fuhh_inconsistent:
    print(f"  ✗ {len(fuhh_inconsistent)} 个不一致")
    for c in fuhh_inconsistent[:10]:
        print(f"    - {c}")
else:
    print(f"  ✓ 符阖排列一致")

# 保存配置
config = {
    'grid_size': 16,
    'box_size': 4,
    'known_digits': new_known_digits,
    'fuhh_permutations': {k: v[:100] for k, v in fuhh_permutations.items()}  # 只保存前100个
}

with open('sudoku_config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

# 总结
print(f"\n{'='*65}")
total_conflicts = len(row_conflicts) + len(col_conflicts) + len(box_conflicts) + len(fuhh_inconsistent)
if total_conflicts == 0:
    print(f"✅ 配置完全一致！已保存至 sudoku_config.json")
else:
    print(f"⚠️ 仍有 {total_conflicts} 个冲突，需要进一步处理")
print(f"{'='*65}")
