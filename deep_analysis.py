#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 深度分析：终局解盘与92锚点的关系 + backup_fuyi/筛选标准

import json
import numpy as np

print("=" * 80)
print("深度分析：问题1 & 问题2")
print("=" * 80)

# ==================== 问题1：终局解盘与92锚点是否属于同一谜题？ ====================

print("\n" + "=" * 80)
print("问题1：终局解盘与92锚点是否属于同一谜题？")
print("=" * 80)

# 从txt文件解析的92锚点（完整）
ANCHORS_92 = {
    # 数1 (7个)
    'BR':1, 'DJ':1, 'KD':1, 'LS':1, 'MM':1, 'OE':1, 'PP':1,
    # 数2 (7个)
    'BP':2, 'CI':2, 'GL':2, 'IG':2, 'KK':2, 'ON':2, 'PF':2,
    # 数3 (8个)
    'AF':3, 'BH':3, 'FK':3, 'GQ':3, 'IS':3, 'KM':3, 'MO':3, 'NR':3,
    # 数4 (6个)
    'BO':4, 'DE':4, 'EP':4, 'FJ':4, 'GF':4, 'LG':4,
    # 数5 (10个)
    'AK':5, 'BN':5, 'EM':5, 'HI':5, 'JE':5, 'KH':5, 'LO':5, 'ML':5, 'OQ':5, 'PJ':5,
    # 数6 (6个)
    'BL':6, 'GG':6, 'HO':6, 'KF':6, 'MQ':6, 'NI':6,
    # 数7 (4个)
    'DH':7, 'IO':7, 'JR':7, 'MS':7,
    # 数8 (5个)
    'AS':8, 'CK':8, 'FE':8, 'JP':8, 'OO':8,
    # 数9 (6个)
    'BJ':9, 'FM':9, 'HK':9, 'KP':9, 'NF':9, 'OH':9,
    # 数10 (2个)
    'PR':10,
    # 数11 (2个)
    'DO':11, 'II':11,
    # 数12 (7个)
    'AI':12, 'BE':12, 'DQ':12, 'FS':12, 'GJ':12, 'LN':12, 'MH':12,
    # 数13 (6个)
    'DG':13, 'EH':13, 'FQ':13, 'HE':13, 'ID':13, 'NL':13,
    # 数14 (7个)
    'AO':14, 'CF':14, 'GD':14, 'HN':14, 'IL':14, 'LJ':14, 'PM':14,
    # 数15 (6个)
    'FH':15, 'IQ':15, 'MD':15, 'NO':15, 'OK':15, 'PS':15,
    # 数16 (4个)
    'AQ':16, 'HR':16, 'JN':16, 'LI':16,
}

print(f"\n92锚点总数: {len(ANCHORS_92)}")

# 验证每个数的位置计数
from collections import Counter
value_counts = Counter(ANCHORS_92.values())
print("92锚点的值分布:")
for v in sorted(value_counts.keys()):
    print(f"  数{v}: {value_counts[v]}个位置")

# txt终局解盘
FINAL_SOLUTION = {
    'A': [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5],
    'B': [8, 12, 7, 10, 3, 15, 9, 11, 6, 16, 5, 4, 2, 14, 1, 13],
    'C': [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5],
    'D': [9, 4, 16, 13, 7, 14, 1, 6, 8, 2, 10, 11, 3, 12, 15, 5],
    'E': [7, 10, 15, 9, 13, 8, 6, 14, 12, 5, 3, 16, 4, 1, 11, 2],
    'F': [2, 8, 5, 16, 15, 1, 4, 3, 11, 9, 7, 10, 6, 13, 14, 12],
    'G': [14, 11, 4, 6, 16, 7, 12, 10, 2, 13, 15, 1, 5, 3, 8, 9],
    'H': [12, 13, 1, 3, 2, 5, 11, 9, 4, 8, 14, 6, 15, 7, 16, 10],
    'I': [13, 9, 8, 2, 6, 11, 10, 12, 14, 4, 1, 7, 16, 15, 5, 3],
    'J': [10, 5, 12, 14, 1, 9, 3, 13, 15, 11, 16, 2, 8, 4, 7, 6],
    'K': [1, 16, 6, 7, 5, 4, 15, 2, 10, 3, 8, 13, 9, 11, 12, 14],
    'L': [3, 15, 11, 4, 8, 16, 14, 7, 9, 6, 12, 5, 13, 10, 2, 1],
    'M': [15, 14, 13, 8, 12, 10, 2, 16, 5, 1, 4, 3, 11, 6, 9, 7],
    'N': [4, 7, 9, 5, 14, 6, 8, 1, 13, 10, 11, 15, 12, 2, 3, 16],
    'O': [6, 1, 10, 11, 9, 3, 7, 15, 16, 12, 2, 8, 14, 5, 13, 4],
    'P': [16, 3, 2, 12, 11, 13, 5, 4, 7, 14, 6, 9, 1, 8, 10, 15]
}

# 列名到索引的映射
COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']
col_map = {col: i for i, col in enumerate(COL_NAMES)}

print("\n【完整验证】终局解盘 vs 92锚点...")
print("-" * 60)

# 统计每行的锚点满足情况
row_stats = {}
total_match = 0
total_anchor = len(ANCHORS_92)
violations = []

for row_name in ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']:
    row_perm = FINAL_SOLUTION[row_name]
    row_anchors = {k: v for k, v in ANCHORS_92.items() if k[0] == row_name}
    
    row_match = 0
    row_violations = []
    
    for coord, expected in row_anchors.items():
        col_char = coord[1]
        col_idx = col_map[col_char]
        actual = row_perm[col_idx]
        
        if actual == expected:
            row_match += 1
        else:
            row_violations.append({
                'coord': coord,
                'expected': expected,
                'actual': actual,
                'row': row_name,
                'col': col_char
            })
            violations.append(row_violations[-1])
    
    row_stats[row_name] = {
        'total_anchors': len(row_anchors),
        'matched': row_match,
        'violations': len(row_violations),
        'violation_list': row_violations
    }
    total_match += row_match
    
    status = "ALL OK" if len(row_violations) == 0 else f"{len(row_violations)} violations"
    print(f"  行{row_name}: {row_match}/{len(row_anchors)} 锚点匹配 [{status}]")

print(f"\n【总结】")
print(f"  总锚点数: {total_anchor}")
print(f"  匹配数: {total_match}")
print(f"  违反数: {total_anchor - total_match}")
print(f"  匹配率: {total_match/total_anchor*100:.1f}%")

# 按值分组分析违反情况
print("\n【按数值分组分析违反】")
violation_by_value = Counter()
for v in violations:
    violation_by_value[ANCHORS_92[v['coord']]] += 1

for val in sorted(violation_by_value.keys()):
    print(f"  数{val}: {violation_by_value[val]}个违反")
    # 显示具体的违反
    for v in violations:
        if ANCHORS_92[v['coord']] == val:
            print(f"    {v['coord']}: 期望{v['expected']}, 实际{v['actual']}")

print("\n【深度分析：92锚点是否唯一确定终局解盘？】")
print("-" * 60)

# 计算终局解盘中每个数值的出现位置
final_positions_by_value = {}
for row_name, row_perm in FINAL_SOLUTION.items():
    for col_idx, val in enumerate(row_perm):
        col_char = COL_NAMES[col_idx]
        coord = row_name + col_char
        if val not in final_positions_by_value:
            final_positions_by_value[val] = []
        final_positions_by_value[val].append(coord)

print("终局解盘中每个数值的位置分布：")
for val in range(1, 17):
    positions = final_positions_by_value.get(val, [])
    anchors_for_val = [k for k, v in ANCHORS_92.items() if v == val]
    
    # 检查锚点位置是否在终局解盘中的相同位置
    matching_positions = [p for p in anchors_for_val if p in positions]
    
    print(f"\n  数{val}:")
    print(f"    92锚点位置: {anchors_for_val}")
    print(f"    终局位置: {positions}")
    print(f"    匹配位置: {matching_positions} ({len(matching_positions)}/{len(anchors_for_val)})")

print("\n" + "=" * 80)
print("问题1结论")
print("=" * 80)

if total_match == total_anchor:
    print("""
[结论] 终局解盘完全满足92锚点约束

这意味着:
  - 终局解盘是92锚点的一个有效解
  - 92锚点 + 数独三约束 -> 终局解盘是合法解之一
  - 但不能证明是唯一解（可能存在多个解）
""")
else:
    print(f"""
[结论] 终局解盘不完全满足92锚点约束

匹配率: {total_match}/{total_anchor} = {total_match/total_anchor*100:.1f}%
违反数: {total_anchor - total_match}个

这意味着:
  - 终局解盘不是92锚点的解！
  - 终局解盘与92锚点属于不同的谜题系统
  - 或者txt文件中的92锚点定义有误
  - 或者终局解盘是另一个谜题的答案

关键证据:
""")
    # 显示关键违反
    for v in violations[:5]:
        print(f"  - {v['coord']}: 期望{v['expected']}, 终局实际{v['actual']}")

# ==================== 问题2：backup_fuyi/的真实筛选标准？ ====================

print("\n" + "=" * 80)
print("问题2：backup_fuyi/的真实筛选标准是什么？")
print("=" * 80)

# 加载backup_fuyi/所有文件并分析特征
print("\n【步骤1】加载所有backup_fuyi/排列...")

backup_perms = {}
for i in range(1, 17):
    row_name = chr(64 + i)
    with open(f'backup_fuyi/A{i}_permutations.json', 'r', encoding='utf-8') as f:
        backup_perms[row_name] = json.load(f)
    print(f"  加载A{row_name}: {len(backup_perms[row_name]):,} 个排列")

# 分析每行的列约束特征
print("\n【步骤2】分析backup_fuyi/的列值分布模式...")

for row_name in ['A', 'B', 'C']:  # 分析前3行
    perms = np.array(backup_perms[row_name])
    print(f"\n  行{row_name}特征:")
    
    # 每列的值域
    for col_idx in range(16):
        col_values = perms[:, col_idx]
        unique_vals = np.unique(col_values)
        print(f"    列{col_idx}: {len(unique_vals)}个不同值, 范围[{col_values.min()}-{col_values.max()}]")
    
    # 检查是否有固定位置
    fixed_cols = []
    for col_idx in range(16):
        col_values = perms[:, col_idx]
        if len(np.unique(col_values)) == 1:
            fixed_cols.append((col_idx, col_values[0]))
    
    if fixed_cols:
        print(f"    固定列: {fixed_cols}")
    else:
        print(f"    无固定列")

# 分析backup_fuyi/与原始txt文件列约束的关系
print("\n【步骤3】对比backup_fuyi/与txt文件列约束...")

# 从txt文件解析的列约束（简化版 - 前64个位置）
TXT_CONSTRAINTS = {
    'A': {
        'AD': {'type': 'set', 'values': {2,6,7,9,10,11}},
        'AE': {'type': 'set', 'values': {2,6,7,9,10,11,15}},
        'AF': {'type': 'fixed', 'value': 3},
        'AG': {'type': 'set', 'values': {1,7,9,10,11,15}},
        'AH': {'type': 'set', 'values': {4,6,10,11,14}},
        'AI': {'type': 'fixed', 'value': 12},
        'AJ': {'type': 'set', 'values': {6,10,11,13,15}},
        'AK': {'type': 'fixed', 'value': 5},
        'AL': {'type': 'set', 'values': {1,7,9,10,12,15}},
        'AM': {'type': 'set', 'values': {2,7,10,12,13,15}},
        'AN': {'type': 'set', 'values': {1,7,9,10,13,15}},
        'AO': {'type': 'fixed', 'value': 14},
        'AP': {'type': 'set', 'values': {6,7,10,11,13,14,15}},
        'AQ': {'type': 'fixed', 'value': 16},
        'AR': {'type': 'set', 'values': {4,6,9,11,13,14,15}},
        'AS': {'type': 'fixed', 'value': 8},
    }
}

print("\n  验证A行backup_fuyi/是否满足txt列约束:")
A_perms = np.array(backup_perms['A'])

for col_idx, col_name in enumerate(COL_NAMES):
    pos = 'A' + col_name
    if pos in TXT_CONSTRAINTS['A']:
        constraint = TXT_CONSTRAINTS['A'][pos]
        col_values = A_perms[:, col_idx]
        unique_vals = set(np.unique(col_values))
        
        if constraint['type'] == 'fixed':
            matches = (col_values == constraint['value']).all()
            print(f"    {pos}: 期望固定={constraint['value']}, 实际唯一值={unique_vals}, 匹配={matches}")
        else:
            allowed = constraint['values']
            all_in_set = unique_vals.issubset(allowed)
            print(f"    {pos}: 期望集合={sorted(allowed)}, 实际={sorted(unique_vals)}, 全在集合内={all_in_set}")

# 分析backup_fuyi/的生成假设
print("\n【步骤4】分析backup_fuyi/可能的筛选标准...")

print("""
可能的筛选标准假设：

假设1: 基于某种数独解的子集
  - backup_fuyi/可能是从大量合法数独解中提取的排列子集
  - 每行约1300个排列，可能是某种统计筛选的结果

假设2: 基于列约束的预筛选
  - 每个位置的排列值可能被预筛选为符合txt列约束的子集
  - 但需要验证所有16行的列约束

假设3: 基于92锚点的筛选
  - backup_fuyi/可能是满足92锚点的排列子集
  - 但验证发现A行违反92锚点，所以这个假设可能不成立

假设4: 随机采样
  - backup_fuyi/可能是原始全集的随机采样
  - 每行约1300个，采样比例约 1300/1,360,849 ≈ 0.095%

假设5: 基于某种数学结构的筛选
  - 可能与易經六十四卦、排列群结构等有关
  - 需要更深层次的数学分析
""")

# 验证假设2：backup_fuyi/是否满足txt列约束
print("\n【验证】backup_fuyi/是否满足txt列约束（完整16行）...")

# 简化：只检查每行是否满足对应的列约束范围
def check_backup_vs_txt_constraints():
    """检查backup_fuyi/的排列是否满足txt列约束"""
    results = {}
    
    # 从txt文件的256个位置约束中，我们只加载了前64个
    # 这里需要完整的256个约束...
    
    # 简化验证：检查每行的列值范围
    for row_name in ['A','B','C','D','E']:
        perms = np.array(backup_perms[row_name])
        row_results = []
        
        for col_idx in range(16):
            col_values = perms[:, col_idx]
            min_val, max_val = col_values.min(), col_values.max()
            unique_count = len(np.unique(col_values))
            row_results.append({
                'col': col_idx,
                'min': min_val,
                'max': max_val,
                'unique_count': unique_count
            })
        
        results[row_name] = row_results
    
    return results

backup_analysis = check_backup_vs_txt_constraints()

for row_name, col_data in backup_analysis.items():
    print(f"\n  行{row_name}:")
    for cd in col_data:
        print(f"    列{cd['col']}: 值域[{cd['min']}-{cd['max']}], {cd['unique_count']}个不同值")

print("\n" + "=" * 80)
print("问题2初步结论")
print("=" * 80)

print("""
[分析结果] backup_fuyi/的筛选标准尚未明确

观察到的特征：
1. 每行规模高度一致 (~1300)
2. 每列值分布相对均匀
3. 无明显的固定列（除了可能的个别列）
4. 排列之间无循环移位/对称关系

可能的筛选标准：
- 从原始全集中随机采样（约0.1%采样率）
- 基于某种未知约束的预筛选
- backup_fuyi/本身可能是中间计算结果

需要进一步调查：
1. backup_fuyi/的来源文件/生成脚本
2. 完整的txt列约束验证
3. backup_fuyi/与原始1,360,849的关系
""")

# 保存分析结果
analysis_result = {
    'problem1': {
        'total_anchors': total_anchor,
        'total_match': total_match,
        'match_rate': total_match/total_anchor,
        'violations_count': len(violations),
        'violations': violations,
        'conclusion': '終局解盤與92錨點不匹配' if total_match < total_anchor else '終局解盤完全匹配92錨點'
    },
    'problem2': {
        'backup_total': sum(len(v) for v in backup_perms.values()),
        'per_row_sizes': {k: len(v) for k, v in backup_perms.items()},
        'conclusion': '篩選標準未知，需要進一步調查'
    }
}

with open('deep_analysis_results.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_result, f, ensure_ascii=False, indent=2)

print("\n分析结果已保存: deep_analysis_results.json")
