#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新策略：使用最小可行约束集 + backup_fuyi/搜索
放弃"三解盘共有锚点"（与C191620冲突），回归92锚点+两两匹配的高频值
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
from ortools.sat.python import cp_model
from collections import Counter

FINAL_C = [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5]
ROW_NAMES = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']

# 92锚点（已验证可行）
ANCHORS_92 = {
    'BR':1, 'DJ':1, 'KD':1, 'LS':1, 'MM':1, 'OE':1, 'PP':1,
    'BP':2, 'CI':2, 'GL':2, 'IG':2, 'KK':2, 'ON':2, 'PF':2,
    'AF':3, 'BH':3, 'FK':3, 'GQ':3, 'IS':3, 'KM':3, 'MO':3, 'NR':3,
    'BO':4, 'DE':4, 'EP':4, 'FJ':4, 'GF':4, 'LG':4,
    'AK':5, 'BN':5, 'EM':5, 'HI':5, 'JE':5, 'KH':5, 'LO':5, 'ML':5, 'OQ':5, 'PJ':5,
    'BL':6, 'GG':6, 'HO':6, 'KF':6, 'MQ':6, 'NI':6,
    'DH':7, 'IO':7, 'JR':7, 'MS':7,
    'AS':8, 'CK':8, 'FE':8, 'JP':8, 'OO':8,
    'BJ':9, 'FM':9, 'HK':9, 'KP':9, 'NF':9, 'OH':9,
    'PR':10, 'DO':11, 'II':11,
    'AI':12, 'BE':12, 'DQ':12, 'FS':12, 'GJ':12, 'LN':12, 'MH':12,
    'DG':13, 'EH':13, 'FQ':13, 'HE':13, 'ID':13, 'NL':13,
    'AO':14, 'CF':14, 'GD':14, 'HN':14, 'IL':14, 'LJ':14, 'PM':14,
    'FH':15, 'IQ':15, 'MD':15, 'NO':15, 'OK':15, 'PS':15,
    'AQ':16, 'HR':16, 'JN':16, 'LI':16,
}

print("=" * 80)
print("优化搜索：用最小可行约束集 + backup_fuyi/ 组合")
print("=" * 80)

# 策略：
# 1. 92锚点（108个约束：92 + C191620的16个）
# 2. 从92锚点中找出"高频匹配"的锚点（在backup中出现的频率）
# 3. 逐步增加符阖排列约束

# 步骤1：从backup_fuyi/中统计每行每个位置的取值频率
print("\n【步骤1】统计backup_fuyi/中每行各列的取值频率...")

backup = {}
for i, row_name in enumerate(ROW_NAMES):
    try:
        with open(f'backup_fuyi/A{i+1}_permutations.json', 'r', encoding='utf-8') as f:
            perms = json.load(f)
        backup[row_name] = perms
        print(f"  {row_name}: {len(perms)}个排列")
    except FileNotFoundError:
        print(f"  {row_name}: 文件不存在")
        backup[row_name] = []

# 步骤2：计算每个位置在backup中的取值分布
print("\n【步骤2】计算各列取值分布...")

pos_frequency = {}
for row_name in ROW_NAMES:
    for c_idx, col in enumerate(COL_NAMES):
        if backup[row_name]:
            values = [perm[c_idx] for perm in backup[row_name]]
            freq = Counter(values)
            pos_frequency[f'{row_name}{col}'] = freq

# 步骤3：找出与92锚点匹配的backup约束
print("\n【步骤3】92锚点与backup的兼容性验证...")

compatible_anchors = {}
incompatible_anchors = []

for pos, expected_val in ANCHORS_92.items():
    if pos in pos_frequency:
        freq = pos_frequency[pos]
        if expected_val in freq:
            compatible_anchors[pos] = expected_val
        else:
            incompatible_anchors.append((pos, expected_val, freq.most_common(3)))
    else:
        incompatible_anchors.append((pos, expected_val, "N/A"))

print(f"\n  92锚点总数: {len(ANCHORS_92)}")
print(f"  backup中兼容的锚点: {len(compatible_anchors)}")
print(f"  backup中不兼容的锚点: {len(incompatible_anchors)}")

if incompatible_anchors:
    print("\n  不兼容锚点详情：")
    for pos, expected, top_values in incompatible_anchors:
        print(f"    {pos}: 期望={expected}, backup中最常见值={top_values}")

# 步骤4：用兼容性验证过的锚点进行搜索
print("\n【步骤4】用backup兼容的锚点进行搜索...")

# 只使用与backup兼容的锚点
search_constraints = dict(compatible_anchors)

# 加上C191620
c_constraints = {}
for i, val in enumerate(FINAL_C):
    c_constraints[f'C{COL_NAMES[i]}'] = val

# 合并约束（C行用C191620，其他行用backup兼容的92锚点）
all_constraints = {k: v for k, v in search_constraints.items() if k[0] != 'C'}
all_constraints.update(c_constraints)

print(f"  搜索约束总数: {len(all_constraints)}")

model = cp_model.CpModel()
grid = {(r, c): model.NewIntVar(1, 16, f'g{r}{c}') for r in range(16) for c in range(16)}

# 数独三约束
for r in range(16):
    model.AddAllDifferent([grid[(r, c)] for c in range(16)])
for c in range(16):
    model.AddAllDifferent([grid[(r, c)] for r in range(16)])
for br in range(4):
    for bc in range(4):
        cells = [grid[(br*4+dr, bc*4+dc)] for dr in range(4) for dc in range(4)]
        model.AddAllDifferent(cells)

# 约束
for pos, val in all_constraints.items():
    r = ROW_NAMES.index(pos[0])
    c = COL_NAMES.index(pos[1])
    model.Add(grid[(r, c)] == val)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0
solver.parameters.num_search_workers = 8

print("  开始搜索...")
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("  [OK] 找到解！")
    
    solution = []
    for r in range(16):
        row = [solver.Value(grid[(r, c)]) for c in range(16)]
        solution.append(row)
    
    # 验证每行是否在backup中
    print("\n  验证每行是否在backup_fuyi/中：")
    in_backup_count = 0
    for r_idx, row_name in enumerate(ROW_NAMES):
        row_tuple = tuple(solution[r_idx])
        if row_name in backup and row_tuple in [tuple(p) for p in backup[row_name]]:
            print(f"    {row_name}: [OK] 在backup中")
            in_backup_count += 1
        else:
            print(f"    {row_name}: [NO] 不在backup中")
    
    print(f"\n  backup匹配率: {in_backup_count}/16 = {in_backup_count/16*100:.1f}%")
    
    # 保存结果
    result = {
        'search_strategy': 'backup兼容锚点 + C191620',
        'constraints_count': len(all_constraints),
        'compatible_anchors_count': len(compatible_anchors),
        'incompatible_anchors_count': len(incompatible_anchors),
        'solution_in_backup': f'{in_backup_count}/16',
        'solution': {ROW_NAMES[i]: solution[i] for i in range(16)}
    }
    
    with open('backup_compatible_search_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("\n  结果已保存到 backup_compatible_search_result.json")
    
else:
    print("  [NO] 无解")
    print("\n  即使只使用backup兼容的锚点仍然无解")
    print("  说明backup_fuyi/与92锚点+C191620存在更深层冲突")

# 步骤5：总结
print("\n" + "=" * 80)
print("新策略总结")
print("=" * 80)
print(f"""
【核心思路】
  放弃"三解盘共有锚点"（与C191620严重冲突）
  用backup_fuyi/验证92锚点的兼容性
  只使用backup中存在的锚点值进行搜索

【关键数据】
  92锚点总数: {len(ANCHORS_92)}
  backup兼容: {len(compatible_anchors)} ({len(compatible_anchors)/len(ANCHORS_92)*100:.1f}%)
  backup不兼容: {len(incompatible_anchors)} ({len(incompatible_anchors)/len(ANCHORS_92)*100:.1f}%)

【策略优势】
  1. backup_fuyi/是经过符阖排列验证的排列集合
  2. 与backup兼容的锚点更可能是正确的约束
  3. 不兼容的锚点可能来自错误的解盘数据
  4. 搜索结果可以逐行验证符阖排列约束

【下一步】
  - 如果92锚点兼容性低，需要进一步筛选
  - 可以考虑逐行从backup中搜索符阖排列组合
  - 不需要全局搜索，可以分步验证
""")
