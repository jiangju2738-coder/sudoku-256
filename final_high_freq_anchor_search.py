#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终策略：用backup的高频取值构建锚点，逐步逼近符阖排列组闔
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
from ortools.sat.python import cp_model
from collections import Counter

FINAL_C = [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5]
ROW_NAMES = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']

print("=" * 80)
print("最终策略：高频锚点 + backup验证 + 逐步逼近")
print("=" * 80)

# 步骤1：加载backup
backup = {}
for i, row_name in enumerate(ROW_NAMES):
    try:
        with open(f'backup_fuyi/A{i+1}_permutations.json', 'r', encoding='utf-8') as f:
            backup[row_name] = json.load(f)
    except FileNotFoundError:
        backup[row_name] = []

# 步骤2：从backup中提取"高频锚点"——每行每列最常见的值
print("\n【步骤1】从backup提取高频锚点...")

high_freq_anchors = {}
for row_name in ROW_NAMES:
    if backup[row_name]:
        for c_idx, col in enumerate(COL_NAMES):
            values = [perm[c_idx] for perm in backup[row_name]]
            freq = Counter(values)
            most_common_val, most_common_count = freq.most_common(1)[0]
            freq_pct = most_common_count / len(backup[row_name]) * 100
            
            # 只取高频值（出现频率 > 5%）
            if freq_pct > 5:
                pos = row_name + col
                high_freq_anchors[pos] = most_common_val

print(f"  高频锚点总数: {len(high_freq_anchors)}")
print(f"  平均每行锚点数: {len(high_freq_anchors)/16:.1f}")

# 步骤3：验证高频锚点与92锚点的关系
print("\n【步骤2】高频锚点与92锚点对比...")

# 92锚点
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

match_count = 0
for pos in set(high_freq_anchors.keys()) & set(ANCHORS_92.keys()):
    if high_freq_anchors[pos] == ANCHORS_92[pos]:
        match_count += 1

shared_count = len(set(high_freq_anchors.keys()) & set(ANCHORS_92.keys()))
print(f"  高频锚点与92锚点交集: {shared_count}个")
print(f"  交集内值相同: {match_count}个 ({match_count/shared_count*100:.1f}%)")

# 步骤4：用高频锚点+C191620搜索
print("\n【步骤3】用高频锚点+C191620搜索...")

# 排除C行（用C191620覆盖）
high_freq_anchors_no_c = {k: v for k, v in high_freq_anchors.items() if k[0] != 'C'}

# 添加C191620
c191620_constraints = {}
for i, val in enumerate(FINAL_C):
    c191620_constraints[f'C{COL_NAMES[i]}'] = val

all_constraints = dict(high_freq_anchors_no_c)
all_constraints.update(c191620_constraints)

print(f"  约束总数: {len(all_constraints)} (高频{len(high_freq_anchors_no_c)} + C191620 {len(c191620_constraints)})")

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
    backup_details = []
    for r_idx, row_name in enumerate(ROW_NAMES):
        row_tuple = tuple(solution[r_idx])
        is_in = row_tuple in [tuple(p) for p in backup[row_name]]
        backup_details.append((row_name, is_in))
        if is_in:
            in_backup_count += 1
        print(f"    {row_name}: {'[OK]' if is_in else '[NO]'}")
    
    print(f"\n  backup匹配率: {in_backup_count}/16 = {in_backup_count/16*100:.1f}%")
    
    # 分析未匹配行的高频锚点覆盖率
    print("\n  高频锚点覆盖率分析：")
    for row_name in ROW_NAMES:
        if row_name != 'C' and backup[row_name]:
            row_sol = solution[ROW_NAMES.index(row_name)]
            row_anchors = {k: v for k, v in high_freq_anchors.items() if k[0] == row_name}
            covered = sum(1 for k, v in row_anchors.items() if row_sol[COL_NAMES.index(k[1])] == v)
            total = len(row_anchors)
            print(f"    {row_name}: {covered}/{total}个高频锚点覆盖")
    
    # 保存结果
    result = {
        'search_strategy': '高频锚点 + C191620',
        'high_freq_anchors_count': len(high_freq_anchors),
        'total_constraints': len(all_constraints),
        'backup_match_count': in_backup_count,
        'backup_match_details': backup_details,
        'solution': {ROW_NAMES[i]: solution[i] for i in range(16)}
    }
    
    with open('high_freq_anchor_search_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("\n  结果已保存到 high_freq_anchor_search_result.json")

else:
    print("  [NO] 无解")
    print("  高频锚点可能与C191620冲突，需要调整策略")

# 步骤5：总结
print("\n" + "=" * 80)
print("策略总结与下一步")
print("=" * 80)
print("""
【关键发现】
  1. backup_fuyi/ 中所有92锚点都是兼容的（92/92）
  2. 但用92锚点+C191620搜索到的解，16行都不在backup中
  3. 这说明backup_fuyi/本身可能不包含符阖原题的完整解

【backup_fuyi/的本质】
  - backup_fuyi/每行约1300个排列
  - 原始声明1,360,849个排列
  - backup_fuyi/是筛选子集（约1.5%）
  - 筛选标准：55个固定位置（94.5%与92锚点匹配）

【当前困境】
  - 92锚点 + C191620 可以导出唯一解
  - 但该解不在backup_fuyi/中
  - backup_fuyi/可能不是符阖原题的解集

【终极解决方案】
  1. 找到原始1,360,849个排列的完整集合
  2. 在完整集合中搜索符阖排列组合
  3. 当前backup_fuyi/无法穷尽符阖原题解空间

【实际可行方案】
  1. 承认backup_fuyi/是子集
  2. 用92锚点 + C191620 已导出"一个解"
  3. 该解满足数独三约束 + 92锚点 + C191620
  4. 但可能不满足完整的符阖排列组闔约束

【结论】
  在没有原始全集的情况下，我们只能：
  (a) 用已知约束导出"一个可行解"
  (b) 该解与txt终局解盘存在差异（70%位置匹配）
  (c) 差异来自符阖排列组闔的额外约束
""")
