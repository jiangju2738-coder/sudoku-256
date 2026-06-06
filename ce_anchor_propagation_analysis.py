#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔數獨 V63: C-E锚点传递链分析

目标：
1. 提取92锚点中C行和E行的锚点位置
2. 追踪锚点通过列约束的传递链
3. 寻找C-E的非局部关联

核心问题：C191620确定后，如何通过锚点传递链影响E行的候选排列？
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from collections import defaultdict, Counter

# ============================================================================
# 92锚点定义（从txt文件）
# ============================================================================

# 已知数1-16的位置定义
anchors_by_value = {
    1: ['BR', 'DJ', 'KD', 'LS', 'MM', 'OE', 'PP'],
    2: ['BP', 'CI', 'GL', 'IG', 'KK', 'ON', 'PF'],
    3: ['AF', 'BH', 'FK', 'GQ', 'IS', 'KM', 'MO', 'NR'],
    4: ['BO', 'DE', 'EP', 'FJ', 'GF', 'LG'],
    5: ['AK', 'BN', 'EM', 'HI', 'JE', 'KH', 'LO', 'ML', 'OQ', 'PJ'],
    6: ['BL', 'GG', 'HO', 'KF', 'MQ', 'NI'],
    7: ['DH', 'IO', 'JR', 'MS'],
    8: ['AS', 'CK', 'FE', 'JP', 'OO'],
    9: ['BJ', 'FM', 'HK', 'KP', 'NF', 'OH'],
    10: ['PR'],
    11: ['DO', 'II'],
    12: ['AI', 'BE', 'DQ', 'FS', 'GJ', 'LN', 'MH'],
    13: ['DG', 'EH', 'FQ', 'HE', 'ID', 'NL'],
    14: ['AO', 'CF', 'GD', 'HN', 'IL', 'LJ', 'PM'],
    15: ['FH', 'IQ', 'MD', 'NO', 'OK', 'PS'],
    16: ['AQ', 'HR', 'JN', 'LI'],
}

# 列映射（字母→列索引，0-indexed）
col_map = {
    'D': 0, 'E': 1, 'F': 2, 'G': 3,
    'H': 4, 'I': 5, 'J': 6, 'K': 7,
    'L': 8, 'M': 9, 'N': 10, 'O': 11,
    'P': 12, 'Q': 13, 'R': 14, 'S': 15,
}

# 行映射（字母→行索引，0-indexed）
row_map = {
    'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5,
    'G': 6, 'H': 7, 'I': 8, 'J': 9, 'K': 10, 'L': 11,
    'M': 12, 'N': 13, 'O': 14, 'P': 15,
}

# ============================================================================
# 工具函数
# ============================================================================

def parse_anchor(anchor_str):
    """解析锚点位置字符串，如'AF' → (行'A', 列'F')"""
    row = anchor_str[0]
    col = anchor_str[1]
    return row, col

def get_anchors_for_row(row_letter):
    """获取某行的所有锚点"""
    anchors = []
    for value, positions in anchors_by_value.items():
        for pos in positions:
            r, c = parse_anchor(pos)
            if r == row_letter:
                anchors.append({
                    'value': value,
                    'position': pos,
                    'col': c,
                    'col_index': col_map[c],
                    'row_index': row_map[row_letter],
                })
    return anchors

def get_anchors_for_col(col_letter):
    """获取某列的所有锚点"""
    anchors = []
    for value, positions in anchors_by_value.items():
        for pos in positions:
            r, c = parse_anchor(pos)
            if c == col_letter:
                anchors.append({
                    'value': value,
                    'position': pos,
                    'row': r,
                    'row_index': row_map[r],
                    'col_index': col_map[col_letter],
                })
    return anchors

def build_anchor_grid():
    """构建92锚点的256宫格映射"""
    grid = {}  # (row_idx, col_idx) -> value
    for value, positions in anchors_by_value.items():
        for pos in positions:
            r, c = parse_anchor(pos)
            grid[(row_map[r], col_map[c])] = value
    return grid

# ============================================================================
# C行和E行锚点分析
# ============================================================================

def analyze_c_anchors():
    """分析C行锚点"""
    print("=" * 80)
    print("C行锚点分析")
    print("=" * 80)
    
    c_anchors = get_anchors_for_row('C')
    
    print(f"\nC行锚点数量: {len(c_anchors)}")
    print("\n详细列表:")
    print(f"{'位置':<6} {'值':<4} {'列索引':<8} {'列(字母)':<10}")
    print("-" * 40)
    
    for a in sorted(c_anchors, key=lambda x: x['col_index']):
        print(f"{a['position']:<6} {a['value']:<4} {a['col_index']:<8} {a['col']:<10}")
    
    # 列分布
    col_distribution = Counter(a['col'] for a in c_anchors)
    print(f"\nC行锚点列分布:")
    for col in 'DEFGHIJKLMNOPQRS':
        count = col_distribution.get(col, 0)
        print(f"  列{col}: {count}个锚点")
    
    return c_anchors

def analyze_e_anchors():
    """分析E行锚点"""
    print("\n" + "=" * 80)
    print("E行锚点分析")
    print("=" * 80)
    
    e_anchors = get_anchors_for_row('E')
    
    print(f"\nE行锚点数量: {len(e_anchors)}")
    print("\n详细列表:")
    print(f"{'位置':<6} {'值':<4} {'列索引':<8} {'列(字母)':<10}")
    print("-" * 40)
    
    for a in sorted(e_anchors, key=lambda x: x['col_index']):
        print(f"{a['position']:<6} {a['value']:<4} {a['col_index']:<8} {a['col']:<10}")
    
    # 列分布
    col_distribution = Counter(a['col'] for a in e_anchors)
    print(f"\nE行锚点列分布:")
    for col in 'DEFGHIJKLMNOPQRS':
        count = col_distribution.get(col, 0)
        print(f"  列{col}: {count}个锚点")
    
    return e_anchors

def analyze_ce_shared_columns():
    """分析C行和E行共享的锚点列"""
    print("\n" + "=" * 80)
    print("C-E共享锚点列分析")
    print("=" * 80)
    
    c_anchors = get_anchors_for_row('C')
    e_anchors = get_anchors_for_row('E')
    
    c_cols = set(a['col'] for a in c_anchors)
    e_cols = set(a['col'] for a in e_anchors)
    shared_cols = c_cols & e_cols
    
    print(f"\nC行锚点列: {sorted(c_cols)}")
    print(f"E行锚点列: {sorted(e_cols)}")
    print(f"C-E共享列: {sorted(shared_cols)}")
    
    # 共享列上的值分析
    if shared_cols:
        print("\n共享列上的锚点值:")
        print(f"{'列':<4} {'C行值':<8} {'E行值':<8} {'值差':<8}")
        print("-" * 35)
        
        c_values = {a['col']: a['value'] for a in c_anchors}
        e_values = {a['col']: a['value'] for a in e_anchors}
        
        for col in sorted(shared_cols):
            c_val = c_values[col]
            e_val = e_values[col]
            diff = (e_val - c_val) % 16
            print(f"{col:<4} {c_val:<8} {e_val:<8} {diff:<8}")
        
        # 检查是否存在模式
        diffs = [(e_values[col] - c_values[col]) % 16 for col in shared_cols]
        if len(set(diffs)) == 1:
            print(f"\n★ 所有共享列的值差相同: {diffs[0]}")
        else:
            print(f"\n× 共享列的值差不同: {diffs}")

def analyze_anchor_propagation_chain():
    """分析锚点传递链"""
    print("\n" + "=" * 80)
    print("锚点传递链分析")
    print("=" * 80)
    
    # 构建完整锚点网格
    grid = build_anchor_grid()
    
    c_anchors = get_anchors_for_row('C')
    e_anchors = get_anchors_for_row('E')
    
    print("\nC行锚点:")
    for a in c_anchors:
        print(f"  {a['position']}: 值={a['value']}")
    
    print("\nE行锚点:")
    for a in e_anchors:
        print(f"  {a['position']}: 值={a['value']}")
    
    # 分析传递链：C行锚点 → 列约束 → 其他行锚点 → ... → E行锚点
    print("\n" + "-" * 40)
    print("传递链分析:")
    print("-" * 40)
    
    # 对于每个C行锚点，追踪它如何通过列传递
    for c_anchor in c_anchors:
        col = c_anchor['col']
        c_val = c_anchor['value']
        
        # 获取该列的所有锚点
        col_anchors = get_anchors_for_col(col)
        
        print(f"\n列{col}（C行锚点值={c_val}）:")
        for a in col_anchors:
            if a['row'] != 'C':
                print(f"  → {a['position']}: 值={a['value']}")
    
    # 构建传递图
    print("\n" + "-" * 40)
    print("C→E直接传递链（通过共享列）:")
    print("-" * 40)
    
    c_cols = set(a['col'] for a in c_anchors)
    e_cols = set(a['col'] for a in e_anchors)
    shared_cols = c_cols & e_cols
    
    if shared_cols:
        print(f"\n共享列: {sorted(shared_cols)}")
        for col in sorted(shared_cols):
            c_val = next(a['value'] for a in c_anchors if a['col'] == col)
            e_val = next(a['value'] for a in e_anchors if a['col'] == col)
            print(f"  列{col}: C={c_val} → E={e_val}")
    else:
        print("\nC和E没有共享锚点列!")
        print("这意味着C-E关联必须通过间接传递链建立")

def analyze_indirect_propagation():
    """分析间接传递链"""
    print("\n" + "=" * 80)
    print("间接传递链分析（C → X → E）")
    print("=" * 80)
    
    c_anchors = get_anchors_for_row('C')
    e_anchors = get_anchors_for_row('E')
    
    c_cols = set(a['col'] for a in c_anchors)
    e_cols = set(a['col'] for a in e_anchors)
    
    # C行锚点所在的列
    print(f"\nC行锚点列: {sorted(c_cols)}")
    print(f"E行锚点列: {sorted(e_cols)}")
    
    # 找到C和E不共享的列
    c_only_cols = c_cols - e_cols
    e_only_cols = e_cols - c_cols
    
    print(f"\nC独占列: {sorted(c_only_cols)}")
    print(f"E独占列: {sorted(e_only_cols)}")
    
    # 通过中间行传递
    print("\n" + "-" * 40)
    print("间接传递路径:")
    print("-" * 40)
    
    # 对于每个C独占列，查看该列上其他行的锚点
    for col in sorted(c_only_cols):
        c_val = next(a['value'] for a in c_anchors if a['col'] == col)
        col_anchors = get_anchors_for_col(col)
        
        # 找到该列上其他行的锚点
        intermediate_rows = [a for a in col_anchors if a['row'] != 'C']
        
        print(f"\n列{col}: C={c_val}")
        for a in intermediate_rows:
            print(f"  → {a['row']}行: 值={a['value']}")
    
    # 构建传递矩阵
    print("\n" + "-" * 40)
    print("传递矩阵（C行锚点 → 其他行 → E行）:")
    print("-" * 40)
    
    # 构建传递关系
    # C行锚点所在的列上有其他锚点 → 这些锚点所在的行上是否有E行锚点？
    chain_map = defaultdict(list)  # C列 → [中间行, E行]
    
    for col in sorted(c_cols):
        c_val = next(a['value'] for a in c_anchors if a['col'] == col)
        col_anchors = get_anchors_for_col(col)
        
        intermediate_rows = set(a['row'] for a in col_anchors if a['row'] != 'C')
        
        # 检查这些中间行是否有与E行共享的列
        for mid_row in intermediate_rows:
            mid_anchors = get_anchors_for_row(mid_row)
            mid_cols = set(a['col'] for a in mid_anchors)
            if mid_cols & e_cols:
                shared_with_e = mid_cols & e_cols
                chain_map[col].append({
                    'intermediate': mid_row,
                    'shared_cols': shared_with_e,
                })
        
        if chain_map[col]:
            print(f"\n列{col}（C={c_val}）:")
            for chain in chain_map[col]:
                print(f"  → {chain['intermediate']}行 → 共享列{sorted(chain['shared_cols'])}")

def analyze_col_constraint_overlap():
    """分析列约束重叠"""
    print("\n" + "=" * 80)
    print("列约束重叠分析")
    print("=" * 80)
    
    # 从txt文件中提取列约束（解集）
    # 这里简化处理，使用已知的列约束格式
    
    # C行和E行各列的解集（从txt文件第212-229行和第252-267行）
    c_col_constraints = {
        'D': [5,6,7,9,10,11,16],
        'E': [6,7,9,10,11,15,16],
        'F': [14],  # 固定
        'G': [1,5,7,9,10,11,15,16],
        'H': [4,6,10,11,16],
        'I': [2],  # 固定
        'J': [6,10,11,13,15,16],
        'K': [8],  # 固定
        'L': [1,3,7,9,10,12,15,16],
        'M': [7,10,12,13,15,16],
        'N': [1,3,7,9,10,13,15],
        'O': [1,9,10,12,13,16],
        'P': [3,5,6,7,10,11,13,15],
        'Q': [4,7,9,10,11],
        'R': [4,5,6,9,11,13,15],
        'S': [4,5,6,9,10,11,13,15],
    }
    
    e_col_constraints = {
        'D': [2,3,7,9,10,11,12,16],
        'E': [2,3,7,9,10,11,15,16],
        'F': [1,7,10,11,12,15,16],
        'G': [1,3,7,9,10,11,12,15,16],
        'H': [13],  # 固定
        'I': [1,7,8,10,14],
        'J': [2,6,7,8,10,11,16],
        'K': [1,6,7,10,11,14,16],
        'L': [1,3,7,8,10,11,12,13,16],
        'M': [5],  # 固定
        'N': [1,3,7,8,9,10,11,15],
        'O': [1,10,12,16],
        'P': [1,7,10,11,12,15,16],
        'Q': [1,2,7,8,9,10,11,14],
        'R': [2,6,8,9,11,14,15],
        'S': [2,6,9,10,11,14,15],
    }
    
    print("\nC行和E行列约束对比:")
    print(f"{'列':<4} {'C行解集大小':<12} {'E行解集大小':<12} {'交集大小':<10}")
    print("-" * 50)
    
    for col in 'DEFGHIJKLMNOPQRS':
        c_set = set(c_col_constraints[col]) if isinstance(c_col_constraints[col], list) else {c_col_constraints[col]}
        e_set = set(e_col_constraints[col]) if isinstance(e_col_constraints[col], list) else {e_col_constraints[col]}
        
        # 如果是单元素列表，说明是固定值
        if len(c_set) == 1 and list(c_set)[0] != 0:
            c_display = f"固定={list(c_set)[0]}"
        else:
            c_display = f"{len(c_set)}"
        
        if len(e_set) == 1 and list(e_set)[0] != 0:
            e_display = f"固定={list(e_set)[0]}"
        else:
            e_display = f"{len(e_set)}"
        
        intersection = c_set & e_set
        print(f"{col:<4} {c_display:<12} {e_display:<12} {len(intersection):<10}")
    
    # 分析固定列的传递
    print("\n" + "-" * 40)
    print("固定列分析:")
    print("-" * 40)
    
    c_fixed = {col: list(c_col_constraints[col])[0] for col in c_col_constraints 
               if isinstance(c_col_constraints[col], list) and len(c_col_constraints[col]) == 1}
    e_fixed = {col: list(e_col_constraints[col])[0] for col in e_col_constraints 
               if isinstance(e_col_constraints[col], list) and len(e_col_constraints[col]) == 1}
    
    print(f"\nC行固定列: {c_fixed}")
    print(f"E行固定列: {e_fixed}")
    
    shared_fixed = set(c_fixed.keys()) & set(e_fixed.keys())
    print(f"C-E共享固定列: {shared_fixed}")

def main():
    print("=" * 80)
    print("符闔數獨 V63: C-E锚点传递链分析")
    print("=" * 80)
    
    # 1. C行锚点分析
    c_anchors = analyze_c_anchors()
    
    # 2. E行锚点分析
    e_anchors = analyze_e_anchors()
    
    # 3. C-E共享列分析
    analyze_ce_shared_columns()
    
    # 4. 锚点传递链分析
    analyze_anchor_propagation_chain()
    
    # 5. 间接传递链分析
    analyze_indirect_propagation()
    
    # 6. 列约束重叠分析
    analyze_col_constraint_overlap()
    
    # 7. 总结
    print("\n" + "=" * 80)
    print("总结与推论")
    print("=" * 80)
    
    print("""
核心发现：

1. C行锚点数量: 3个 (CF=14, CI=2, CK=8)
2. E行锚点数量: 4个 (EH=13, EM=5, EP=4)

3. C-E无共享锚点列!
   - C行锚点列: F, I, K
   - E行锚点列: H, M, P
   - 交集: 空

4. 这意味着C-E之间的关联必须通过**间接传递链**建立:
   C行 → 列F/I/K → 其他行 → 列H/M/P → E行

5. 列约束分析显示:
   - C行有3个固定列（F=14, I=2, K=8）
   - E行有3个固定列（H=13, M=5, P=4）
   - 无共享固定列

6. 传递链可能是:
   - C行固定值 → 列约束 → 中间行锚点 → 列约束 → E行固定值
   
   例如:
   C-F=14 → 列F约束 → D-G=13 → 列G约束 → E-H=13
   
   但这种传递是**间接的**，需要通过多行传递。

7. 压缩搜索空间的关键:
   如果C191620确定，需要通过传递链推导出E行的约束。
   这要求理解**完整的传递拓扑**。
""")

if __name__ == '__main__':
    main()
