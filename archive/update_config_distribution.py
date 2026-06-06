#!/usr/bin/env python3
"""更新 sudoku_config.json 以匹配用户指定的已知数字分布"""

import json
import random
from collections import defaultdict

# 用户指定的分布
TARGET_DISTRIBUTION = [7, 7, 8, 6, 10, 6, 4, 5, 6, 1, 2, 7, 6, 7, 6, 4]
TOTAL_KNOWN = sum(TARGET_DISTRIBUTION)

print("=" * 65)
print("📝 更新 sudoku_config.json 以匹配目标分布")
print("=" * 65)

print(f"\n目标分布: {TARGET_DISTRIBUTION}")
print(f"总计: {TOTAL_KNOWN} 个已知数字")

# 加载符阖排列
fuhh_permutations = {}
for row_num in range(1, 17):
    filename = f"A{row_num}_permutations.json"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            perms = json.load(f)
            fuhh_permutations[row_num] = perms
    except FileNotFoundError:
        print(f"  ⚠️ {filename} 未找到，使用默认值")
        fuhh_permutations[row_num] = [list(range(1, 17))] * 100

# 加载现有配置（保留符阖排列部分）
try:
    with open('sudoku_config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    config = {'grid_size': 16, 'box_size': 4, 'fuhh_permutations': {}}

# 生成新的已知数字配置
# 确保每个已知数字的值与其行的符阖排列一致
new_known_digits = []
random.seed(2026)  # 确定性种子

for row, target_count in enumerate(TARGET_DISTRIBUTION, 1):
    # 获取该行的符阖排列
    perms = fuhh_permutations.get(row, [])
    
    if not perms:
        # 如果没有符阖排列，使用 1-16 的默认值
        allowed_values_by_col = {c: set(range(1, 17)) for c in range(16)}
    else:
        # 计算每列允许的数值集合
        allowed_values_by_col = {c: set() for c in range(16)}
        for perm in perms:
            for col_idx, val in enumerate(perm):
                allowed_values_by_col[col_idx].add(val)
    
    # 选择 target_count 个列位置
    available_cols = list(range(16))
    selected_cols = random.sample(available_cols, target_count)
    
    # 为每个选中的位置分配值
    for col_idx in selected_cols:
        allowed = allowed_values_by_col[col_idx]
        if allowed:
            val = random.choice(list(allowed))
        else:
            val = random.randint(1, 16)
        
        new_known_digits.append({
            'row': row,
            'col': col_idx + 1,  # 转为 1-based
            'value': val
        })

# 更新配置
config['known_digits'] = new_known_digits
config['grid_size'] = 16
config['box_size'] = 4

# 保存
with open('sudoku_config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

# 验证新配置
print(f"\n✓ 新配置已生成并保存")

# 验证分布
new_rows = defaultdict(int)
new_values_by_row = defaultdict(list)
for kd in new_known_digits:
    new_rows[kd['row']] += 1
    new_values_by_row[kd['row']].append(kd['value'])

print(f"\n{'='*65}")
print("📊 新配置验证")
print("=" * 65)

print(f"\n  {'行':>4} {'新分布':>8} {'目标':>8} {'状态':>6} {'已选值(样本)':>20}")
print(f"  {'-'*4} {'-'*8} {'-'*8} {'-'*6} {'-'*20}")

all_match = True
for r in range(1, 17):
    count = new_rows.get(r, 0)
    target = TARGET_DISTRIBUTION[r-1]
    match = '✓' if count == target else '✗'
    if count != target:
        all_match = False
    values = sorted(new_values_by_row.get(r, [])[:5])
    values_str = str(values)[:20]
    print(f"  {r:>4} {count:>8} {target:>8} {match:>6} {values_str:>20}")

print(f"\n  {'总计':>4} {len(new_known_digits):>8} {TOTAL_KNOWN:>8}")

if all_match:
    print(f"\n✅ 分布完全匹配！")
else:
    print(f"\n⚠️ 分布仍有不匹配")

# 检查符阖排列一致性
print(f"\n{'='*65}")
print("🔍 符阖排列一致性检查")
print("=" * 65)

inconsistent = []
for kd in new_known_digits:
    row = kd['row']
    col = kd['col'] - 1  # 转为 0-based
    val = kd['value']
    
    perms = fuhh_permutations.get(row, [])
    if perms:
        allowed = set(perm[col] for perm in perms)
        if val not in allowed:
            inconsistent.append({
                'row': row,
                'col': kd['col'],
                'value': val,
                'allowed_count': len(allowed)
            })

if inconsistent:
    print(f"\n⚠️ 发现 {len(inconsistent)} 个不一致的已知数字:")
    for item in inconsistent[:10]:
        print(f"  行 {item['row']:2d}, 列 {item['col']:2d}: 值 {item['value']} 不在允许集合中")
else:
    print(f"\n✅ 所有已知数字均符阖排列约束！")

print(f"\n{'='*65}")
print("配置更新完成")
print(f"{'='*65}")
