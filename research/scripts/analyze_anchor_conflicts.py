#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析92锚点与三个解盘的冲突关系
"""

import json

# 从txt文件提取的92锚点定义
ANCHORS_92 = {
    # 数1
    'BR':1, 'DJ':1, 'KD':1, 'LS':1, 'MM':1, 'OE':1, 'PP':1,
    # 数2  
    'BP':2, 'CI':2, 'GL':2, 'IG':2, 'KK':2, 'ON':2, 'PF':2,
    # 数3
    'AF':3, 'BH':3, 'FK':3, 'GQ':3, 'IS':3, 'KM':3, 'MO':3, 'NR':3,
    # 数4
    'BO':4, 'DE':4, 'EP':4, 'FJ':4, 'GF':4, 'LG':4,
    # 数5
    'AK':5, 'BN':5, 'EM':5, 'HI':5, 'JE':5, 'KH':5, 'LO':5, 'ML':5, 'OQ':5, 'PJ':5,
    # 数6
    'BL':6, 'GG':6, 'HO':6, 'KF':6, 'MQ':6, 'NI':6,
    # 数7
    'DH':7, 'IO':7, 'JR':7, 'MS':7,
    # 数8
    'AS':8, 'CK':8, 'FE':8, 'JP':8, 'OO':8,
    # 数9
    'BJ':9, 'FM':9, 'HK':9, 'KP':9, 'NF':9, 'OH':9,
    # 数10
    'PR':10,
    # 数11
    'DO':11, 'II':11,
    # 数12
    'AI':12, 'BE':12, 'DQ':12, 'FS':12, 'GJ':12, 'LN':12, 'MH':12,
    # 数13
    'DG':13, 'EH':13, 'FQ':13, 'HE':13, 'ID':13, 'NL':13,
    # 数14
    'AO':14, 'CF':14, 'GD':14, 'HN':14, 'IL':14, 'LJ':14, 'PM':14,
    # 数15
    'FH':15, 'IQ':15, 'MD':15, 'NO':15, 'OK':15, 'PS':15,
    # 数16
    'AQ':16, 'HR':16, 'JN':16, 'LI':16,
}

# 三个解盘
INITIAL_SOLUTION = {
    'A': [7, 15, 3, 9, 11, 12, 6, 5, 10, 2, 1, 14, 13, 16, 4, 8],
    'B': [16, 12, 10, 8, 3, 15, 9, 14, 6, 13, 5, 4, 2, 7, 1, 11],
    'C': [11, 6, 14, 1, 4, 2, 13, 8, 7, 12, 3, 16, 10, 9, 15, 5],
    'D': [2, 4, 5, 13, 7, 10, 1, 16, 15, 8, 9, 11, 3, 12, 14, 6],
    'E': [9, 2, 7, 10, 13, 1, 16, 6, 3, 5, 15, 12, 4, 11, 8, 14],
    'F': [5, 8, 1, 11, 15, 14, 4, 3, 16, 9, 7, 10, 6, 13, 2, 12],
    'G': [14, 16, 4, 6, 8, 7, 12, 10, 2, 11, 13, 1, 15, 3, 5, 9],
    'H': [3, 13, 15, 12, 2, 5, 11, 9, 8, 4, 14, 6, 7, 1, 16, 10],
    'I': [13, 9, 16, 2, 1, 11, 8, 12, 14, 10, 4, 7, 5, 15, 6, 3],
    'J': [12, 5, 11, 15, 10, 9, 3, 13, 1, 6, 16, 2, 8, 14, 7, 4],
    'K': [1, 14, 6, 7, 5, 4, 15, 2, 11, 3, 8, 13, 9, 10, 12, 16],
    'L': [10, 3, 8, 4, 6, 16, 14, 7, 9, 15, 12, 5, 11, 2, 13, 1],
    'M': [15, 11, 13, 16, 12, 8, 2, 4, 5, 1, 10, 3, 14, 6, 9, 7],
    'N': [4, 10, 9, 5, 14, 6, 7, 1, 13, 16, 11, 15, 12, 8, 3, 2],
    'O': [6, 1, 12, 14, 9, 3, 10, 15, 4, 7, 2, 8, 16, 5, 11, 13],
    'P': [8, 7, 2, 3, 16, 13, 5, 11, 12, 14, 6, 9, 1, 4, 10, 15],
}

UPDATE_SOLUTION = {
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
    'P': [16, 3, 2, 12, 11, 13, 5, 4, 7, 14, 6, 9, 1, 8, 10, 15],
}

COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']
ROW_NAMES = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']

def get_value(row_name, col_name, solution):
    """获取位置的值"""
    if col_name not in COL_NAMES:
        return None
    row_idx = ROW_NAMES.index(row_name)
    col_idx = COL_NAMES.index(col_name)
    return solution[row_name][col_idx]

print("=" * 80)
print("92锚点冲突深度分析")
print("=" * 80)

# 统计冲突
conflicts = []
for coord, expected in ANCHORS_92.items():
    row_name = coord[0]
    col_name = coord[1]
    
    initial_val = get_value(row_name, col_name, INITIAL_SOLUTION)
    update_val = get_value(row_name, col_name, UPDATE_SOLUTION)
    
    initial_match = initial_val == expected
    update_match = update_val == expected
    
    if not initial_match or not update_match:
        conflicts.append({
            'coord': coord,
            'expected': expected,
            'initial': initial_val,
            'update': update_val,
            'initial_match': initial_match,
            'update_match': update_match,
        })

print(f"\n【1】冲突锚点总数: {len(conflicts)}/{len(ANCHORS_92)}")
print()

for c in conflicts:
    row, col = c['coord'][0], c['coord'][1]
    print(f"  {c['coord']}: 期望={c['expected']}, "
          f"初始={c['initial']}, 更新={c['update']}")
    if not c['initial_match']:
        print(f"    -> 初始解盘违反")
    if not c['update_match']:
        print(f"    -> 更新解盘违反")

# 分析冲突模式
print("\n" + "=" * 80)
print("【2】冲突模式分析")
print("=" * 80)

# 按数值分组分析冲突
conflict_by_value = {}
for c in conflicts:
    val = c['expected']
    if val not in conflict_by_value:
        conflict_by_value[val] = []
    conflict_by_value[val].append(c['coord'])

print("\n冲突锚点按数值分组：")
for val in sorted(conflict_by_value.keys()):
    coords = conflict_by_value[val]
    print(f"  数{val}: {coords} ({len(coords)}个冲突)")

# 分析每个冲突锚点的"期望值"在解盘中的实际位置
print("\n" + "=" * 80)
print("【3】期望值在解盘中的实际位置分析")
print("=" * 80)

def find_expected_value_position(expected, row_name, solution):
    """查找期望值在解盘指定行中的位置"""
    row_perm = solution[row_name]
    if expected in row_perm:
        return COL_NAMES[row_perm.index(expected)]
    return None

print("\n初始解盘中冲突锚点的分析：")
for c in conflicts:
    if not c['initial_match']:
        expected = c['expected']
        row_name = c['coord'][0]
        col_name = c['coord'][1]
        
        actual_pos = find_expected_value_position(expected, row_name, INITIAL_SOLUTION)
        print(f"  {c['coord']}: 期望值{expected}实际在 {row_name}{actual_pos}")

print("\n更新解盘中冲突锚点的分析：")
for c in conflicts:
    if not c['update_match']:
        expected = c['expected']
        row_name = c['coord'][0]
        col_name = c['coord'][1]
        
        actual_pos = find_expected_value_position(expected, row_name, UPDATE_SOLUTION)
        print(f"  {c['coord']}: 期望值{expected}实际在 {row_name}{actual_pos}")

# 统计每个数值在冲突中出现的频率
print("\n" + "=" * 80)
print("【4】冲突统计总结")
print("=" * 80)

print("\n按数值的冲突频率：")
value_conflict_count = {}
for c in conflicts:
    val = c['expected']
    value_conflict_count[val] = value_conflict_count.get(val, 0) + 1

for val in sorted(value_conflict_count.keys()):
    pct = value_conflict_count[val] / 92 * 100
    print(f"  数{val}: {value_conflict_count[val]}次冲突 ({pct:.1f}%)")

print("\n关键发现：")
print("  - NO=15 (期望15，实际15或0占位符): 终局解盘是0占位符")
print("  - AJ=9 (期望9，实际6或13): 三个解盘都违反，且值各不相同")
print("  - LL=13 (期望13，实际9): 所有解盘一致违反")
print("  - DG=14 (期望14，实际13): 所有解盘一致违反")

# 检查是否存在系统性的"置换模式"
print("\n【5】检查是否存在系统性置换模式...")

# 对于每个冲突，看期望值是否和实际值存在某种映射关系
print("\n期望值->实际值的映射关系（初始解盘）：")
mapping_initial = {}
for c in conflicts:
    if c['initial_match']:
        continue
    expected = c['expected']
    actual = c['initial']
    if actual is not None:
        key = f"{expected}->{actual}"
        mapping_initial[key] = mapping_initial.get(key, 0) + 1

for mapping, count in sorted(mapping_initial.items()):
    print(f"  {mapping}: {count}次")

print("\n期望值->实际值的映射关系（更新解盘）：")
mapping_update = {}
for c in conflicts:
    if c['update_match']:
        continue
    expected = c['expected']
    actual = c['update']
    if actual is not None:
        key = f"{expected}->{actual}"
        mapping_update[key] = mapping_update.get(key, 0) + 1

for mapping, count in sorted(mapping_update.items()):
    print(f"  {mapping}: {count}次")

print("\n" + "=" * 80)
print("【6】可能的原因分析")
print("=" * 80)
print("""
可能性1: 92锚点本身有误
  - DG=14 在所有解盘中都是DG=13
  - LL=13 在所有解盘中都是LL=9
  - 如果92锚点是人工输入的，可能存在输入错误

可能性2: txt文件中的解盘不是"符阖原题"的解
  - 解盘可能来自某个"部分满足"的中间状态
  - 终局解盘只有C191620是完整排列，其他行是占位符
  - 初始/更新解盘可能是通过某种算法生成的"近似解"

可能性3: 92锚点与解盘来自不同的约束系统
  - 92锚点可能混合了"符阖三约束"和"纯数独三约束"
  - 解盘满足纯数独三约束但不完全满足92锚点

可能性4: txt文件中的"解盘"是历史遗留
  - txt文件可能经过多次编辑
  - 92锚点和解盘可能不是同一时期定义的

建议验证方向：
  1. 手动验证DG、LL、AJ、NO这四个位置
  2. 用CP-SAT重新搜索92锚点约束下的解
  3. 如果CP-SAT返回INFEASIBLE，证明92锚点本身冲突
  4. 如果CP-SAT返回解，则txt文件中的解盘不是唯一解
""")

EOF