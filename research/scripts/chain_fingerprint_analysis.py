#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔數獨 V63: 链式指纹分析
提取行间不变量、对称性、映射关系

核心问题：
1. C191620 与 E行是否存在链式约束？
2. 从三解盘中提取行间指纹
3. 验证"第三行与第五行匹配压缩搜索空间"的假设
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
from collections import Counter, defaultdict
from math import gcd
from functools import reduce

# ============================================================================
# 数据定义
# ============================================================================

# C191620 (终局解盘行C)
C191620 = [7,10,14,15, 4,2,16,8, 12,13,3,1, 11,9,6,5]

# 初始解盘各行
initial_solution = {
    'A': [7,15,3,9, 11,12,6,5, 10,2,1,14, 13,16,4,8],
    'B': [16,12,10,8, 3,15,9,14, 6,13,5,4, 2,7,1,11],
    'C': [11,6,14,1, 4,2,13,8, 7,12,3,16, 10,9,15,5],
    'D': [2,4,5,13, 7,10,1,16, 15,8,9,11, 3,12,14,6],
    'E': [9,2,7,10, 13,1,16,6, 3,5,15,12, 4,11,8,14],
    'F': [5,8,1,11, 15,14,4,3, 16,9,7,10, 6,13,2,12],
    'G': [14,16,4,6, 8,7,12,10, 2,11,13,1, 15,3,5,9],
    'H': [3,13,15,12, 2,5,11,9, 8,4,14,6, 7,1,16,10],
    'I': [13,9,16,2, 1,11,8,12, 14,10,4,7, 5,15,6,3],
    'J': [12,5,11,15, 10,9,3,13, 1,6,16,2, 8,14,7,4],
    'K': [1,14,6,7, 5,4,15,2, 11,3,8,13, 9,10,12,16],
    'L': [10,3,8,4, 6,16,14,7, 9,15,12,5, 11,2,13,1],
    'M': [15,11,13,16, 12,8,2,4, 5,1,10,3, 14,6,9,7],
    'N': [4,10,9,5, 14,6,7,1, 13,16,11,15, 12,8,3,2],
    'O': [6,1,12,14, 9,3,10,15, 4,7,2,8, 16,5,11,13],
    'P': [8,7,2,3, 16,13,5,11, 12,14,6,9, 1,4,10,15],
}

# 更新解盘各行
update_solution = {
    'A': [11,2,3,15, 4,12,13,5, 1,7,9,14, 10,16,6,8],
    'B': [8,12,7,10, 3,15,9,11, 6,16,5,4, 2,14,1,13],
    'C': [5,6,14,1, 10,2,16,8, 3,15,13,12, 7,9,4,11],
    'D': [9,4,16,13, 7,14,1,6, 8,2,10,11, 3,12,15,5],
    'E': [7,10,15,9, 13,8,6,14, 12,5,3,16, 4,1,11,2],
    'F': [2,8,5,16, 15,1,4,3, 11,9,7,10, 6,13,14,12],
    'G': [14,11,4,6, 16,7,12,10, 2,13,15,1, 5,3,8,9],
    'H': [12,13,1,3, 2,5,11,9, 4,8,14,6, 15,7,16,10],
    'I': [13,9,8,2, 6,11,10,12, 14,4,1,7, 16,15,5,3],
    'J': [10,5,12,14, 1,9,3,13, 15,11,16,2, 8,4,7,6],
    'K': [1,16,6,7, 5,4,15,2, 10,3,8,13, 9,11,12,14],
    'L': [3,15,11,4, 8,16,14,7, 9,6,12,5, 13,10,2,1],
    'M': [15,14,13,8, 12,10,2,16, 5,1,4,3, 11,6,9,7],
    'N': [4,7,9,5, 14,6,8,1, 13,10,11,15, 12,2,3,16],
    'O': [6,1,10,11, 9,3,7,15, 16,12,2,8, 14,5,13,4],
    'P': [16,3,2,12, 11,13,5,4, 7,14,6,9, 1,8,10,15],
}

# 符闔排列规模 (从txt文件)
fummel_counts = {
    'A': 8731, 'B': 902, 'C': 656777, 'D': 1980, 'E': 633271,
    'F': 359, 'G': 2356, 'H': 4782, 'I': 164, 'J': 28984,
    'K': 2972, 'L': 620, 'M': 484, 'N': 10668, 'O': 5990, 'P': 1809,
}

# ============================================================================
# 数学工具函数
# ============================================================================

def parity_of_permutation(perm):
    """计算排列的奇偶性 (偶排列=True, 奇排列=False)"""
    n = len(perm)
    visited = [False] * n
    sign = 1
    for i in range(n):
        if not visited[i]:
            cycle_len = 0
            j = i
            while not visited[j]:
                visited[j] = True
                j = perm[j] - 1  # 转换为0-indexed
                cycle_len += 1
            # 长度为k的循环贡献 (-1)^(k-1)
            sign *= (-1) ** (cycle_len - 1)
    return sign == 1  # True = 偶, False = 奇

def inversion_count(perm):
    """计算逆序数"""
    count = 0
    for i in range(len(perm)):
        for j in range(i + 1, len(perm)):
            if perm[i] > perm[j]:
                count += 1
    return count

def permutation_order(perm):
    """计算置换的阶 (最小公倍数 of 循环长度)"""
    n = len(perm)
    visited = [False] * n
    cycle_lengths = []
    for i in range(n):
        if not visited[i]:
            cycle_len = 0
            j = i
            while not visited[j]:
                visited[j] = True
                j = perm[j] - 1
                cycle_len += 1
            cycle_lengths.append(cycle_len)
    return reduce(lambda a, b: a * b // gcd(a, b), cycle_lengths, 1)

def cyclic_decomposition(perm):
    """获取循环分解"""
    n = len(perm)
    visited = [False] * n
    cycles = []
    for i in range(n):
        if not visited[i]:
            cycle = []
            j = i
            while not visited[j]:
                visited[j] = True
                cycle.append(perm[j])
                j = perm[j] - 1
            cycles.append(cycle)
    return cycles

def sum_by_position(perm1, perm2):
    """两排列逐位求和 mod 16"""
    return [(a + b) % 16 for a, b in zip(perm1, perm2)]

def diff_by_position(perm1, perm2):
    """两排列逐位差 mod 16"""
    return [(a - b) % 16 for a, b in zip(perm1, perm2)]

def xor_by_position(perm1, perm2):
    """两排列逐位异或 (作为4位二进制)"""
    return [(a ^ b) for a, b in zip(perm1, perm2)]

def position_value_mapping(perm):
    """位置到值的映射"""
    return {i: v for i, v in enumerate(perm)}

# ============================================================================
# 分析函数
# ============================================================================

def analyze_single_permutation(perm, name):
    """分析单个排列的特征"""
    return {
        'name': name,
        'perm': perm,
        'parity': '偶' if parity_of_permutation(perm) else '奇',
        'inversion_count': inversion_count(perm),
        'order': permutation_order(perm),
        'cycles': cyclic_decomposition(perm),
        'sum_1_to_16': sum(perm),
        'first_4_sum': sum(perm[:4]),
        'second_4_sum': sum(perm[4:8]),
        'third_4_sum': sum(perm[8:12]),
        'fourth_4_sum': sum(perm[12:16]),
    }

def analyze_row_pair(row1, row2, name1, name2, row_label1, row_label2):
    """分析两行之间的关系"""
    p1 = analyze_single_permutation(row1, name1)
    p2 = analyze_single_permutation(row2, name2)
    
    sum_mod = sum_by_position(row1, row2)
    diff_mod = diff_by_position(row1, row2)
    xor_mod = xor_by_position(row1, row2)
    
    # 检查是否存在某种变换关系
    is_inverse = all((a + b) % 17 == 0 or (a + b) % 17 == 17 for a, b in zip(row1, row2))
    
    return {
        'row1': p1,
        'row2': p2,
        'sum_mod_16': sum_mod,
        'diff_mod_16': diff_mod,
        'xor_mod_16': xor_mod,
        'sum_parity': parity_of_permutation(sum_mod),
        'diff_parity': parity_of_permutation(diff_mod),
        'sum_inversions': inversion_count(sum_mod),
        'diff_inversions': inversion_count(diff_mod),
    }

def analyze_all_solutions():
    """分析三解盘中所有行的特征"""
    results = {}
    
    for sol_name, solution in [('初始', initial_solution), ('更新', update_solution)]:
        results[sol_name] = {}
        for row_name, row in solution.items():
            results[sol_name][row_name] = analyze_single_permutation(row, f"{sol_name}-{row_name}")
    
    return results

def compare_c_e_relationship():
    """比较C行与E行的关系"""
    print("=" * 80)
    print("C行与E行关系分析")
    print("=" * 80)
    
    analysis = analyze_all_solutions()
    
    for sol_name in ['初始', '更新']:
        c_row = initial_solution['C'] if sol_name == '初始' else update_solution['C']
        e_row = initial_solution['E'] if sol_name == '初始' else update_solution['E']
        
        print(f"\n--- {sol_name}解盘 ---")
        print(f"C行: {c_row}")
        print(f"E行: {e_row}")
        
        pair_analysis = analyze_row_pair(c_row, e_row, f"{sol_name}-C", f"{sol_name}-E", 'C', 'E')
        
        print(f"\n奇偶性: C={pair_analysis['row1']['parity']}, E={pair_analysis['row2']['parity']}")
        print(f"逆序数: C={pair_analysis['row1']['inversion_count']}, E={pair_analysis['row2']['inversion_count']}")
        print(f"置换阶: C={pair_analysis['row1']['order']}, E={pair_analysis['row2']['order']}")
        
        # 逐位关系分析
        sum_vals = pair_analysis['sum_mod_16']
        diff_vals = pair_analysis['diff_mod_16']
        xor_vals = pair_analysis['xor_mod_16']
        
        print(f"\n逐位和 mod 16: {sum_vals}")
        print(f"逐位差 mod 16: {diff_vals}")
        print(f"逐位异或: {xor_vals}")
        
        # 检查常数列
        const_sum = len(set(sum_vals)) == 1
        const_diff = len(set(diff_vals)) == 1
        const_xor = len(set(xor_vals)) == 1
        
        if const_sum:
            print(f"★ 逐位和为常数: {sum_vals[0]}")
        if const_diff:
            print(f"★ 逐位差为常数: {diff_vals[0]}")
        if const_xor:
            print(f"★ 逐位异或为常数: {xor_vals[0]}")

def analyze_c191620_vs_solutions():
    """分析C191620与两解盘C行的关系"""
    print("\n" + "=" * 80)
    print("C191620 vs 解盘C行 对比")
    print("=" * 80)
    
    c191620_analysis = analyze_single_permutation(C191620, 'C191620')
    
    print(f"\nC191620 特征:")
    print(f"  排列: {C191620}")
    print(f"  奇偶性: {c191620_analysis['parity']}")
    print(f"  逆序数: {c191620_analysis['inversion_count']}")
    print(f"  置换阶: {c191620_analysis['order']}")
    print(f"  循环分解: {c191620_analysis['cycles']}")
    print(f"  4组4位和: [{c191620_analysis['first_4_sum']}, {c191620_analysis['second_4_sum']}, "
          f"{c191620_analysis['third_4_sum']}, {c191620_analysis['fourth_4_sum']}]")
    
    # 与初始解盘C行比较
    initial_c = initial_solution['C']
    update_c = update_solution['C']
    
    print(f"\n与初始解盘C行比较:")
    print(f"  初始C: {initial_c}")
    print(f"  匹配位置数: {sum(1 for a, b in zip(C191620, initial_c) if a == b)}/16")
    
    print(f"\n与更新解盘C行比较:")
    print(f"  更新C: {update_c}")
    print(f"  匹配位置数: {sum(1 for a, b in zip(C191620, update_c) if a == b)}/16")

def analyze_chain_fingerprints():
    """分析所有行的链式指纹"""
    print("\n" + "=" * 80)
    print("所有行的链式指纹矩阵")
    print("=" * 80)
    
    analysis = analyze_all_solutions()
    
    # 构建指纹矩阵
    print("\n奇偶性矩阵:")
    print("     ", " ".join(f"{r:4s}" for r in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                                                  'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']))
    
    for sol_name in ['初始', '更新']:
        row_signs = []
        for row_name in 'ABCDEFGHIJKLMNOP':
            parity = analysis[sol_name][row_name]['parity']
            row_signs.append('偶' if parity else '奇')
        print(f"{sol_name}: ", " ".join(f"{s:4s}" for s in row_signs))
    
    # 逆序数矩阵
    print("\n逆序数矩阵:")
    for sol_name in ['初始', '更新']:
        invs = [analysis[sol_name][r]['inversion_count'] for r in 'ABCDEFGHIJKLMNOP']
        print(f"{sol_name}: ", " ".join(f"{v:4d}" for v in invs))
    
    # 置换阶矩阵
    print("\n置换阶矩阵:")
    for sol_name in ['初始', '更新']:
        orders = [analysis[sol_name][r]['order'] for r in 'ABCDEFGHIJKLMNOP']
        print(f"{sol_name}: ", " ".join(f"{v:4d}" for v in orders))

def analyze_ce_constraint_hypothesis():
    """分析C-E约束假设"""
    print("\n" + "=" * 80)
    print("C-E链式约束假设验证")
    print("=" * 80)
    
    # 假设：C和E行存在某种函数关系 f(C, E) = constant
    # 验证：在两个解盘中检查
    
    solutions = [
        ('初始', initial_solution),
        ('更新', update_solution),
    ]
    
    # 检查各种可能的不变量
    invariants_to_check = [
        ('逐位和 mod 16', lambda c, e: [(c[i] + e[i]) % 16 for i in range(16)]),
        ('逐位差 mod 16', lambda c, e: [(c[i] - e[i]) % 16 for i in range(16)]),
        ('逐位异或', lambda c, e: [c[i] ^ e[i] for i in range(16)]),
        ('逐位和 mod 17', lambda c, e: [(c[i] + e[i]) % 17 for i in range(16)]),
        ('位置值偏移', lambda c, e: [(e[i] - c[i]) % 16 for i in range(16)]),
    ]
    
    for name, func in invariants_to_check:
        print(f"\n--- {name} ---")
        results = []
        for sol_name, solution in solutions:
            c_row = solution['C']
            e_row = solution['E']
            result = func(c_row, e_row)
            results.append(result)
            print(f"  {sol_name}: {result}")
        
        # 检查是否一致
        if results[0] == results[1]:
            print(f"  ★ 两个解盘中结果一致!")
        else:
            print(f"  × 两个解盘中结果不一致")

def main():
    print("=" * 80)
    print("符闔數獨 V63: 链式指纹分析")
    print("=" * 80)
    
    # 1. C191620 特征分析
    analyze_c191620_vs_solutions()
    
    # 2. C行与E行关系分析
    compare_c_e_relationship()
    
    # 3. 所有行的链式指纹
    analyze_chain_fingerprints()
    
    # 4. C-E约束假设验证
    analyze_ce_constraint_hypothesis()
    
    # 5. 符闔排列规模分析
    print("\n" + "=" * 80)
    print("符闔排列规模分析")
    print("=" * 80)
    print("\n各行排列数量:")
    for row, count in fummel_counts.items():
        print(f"  行{row}: {count:>7,}")
    
    print(f"\n总数: {sum(fummel_counts.values()):>10,}")
    
    # C和E是最大规模的两行
    print(f"\nC行 (656,777) 和 E行 (633,271) 是规模最大的两行")
    print(f"如果C-E之间存在链式约束，可能将搜索空间压缩到:")
    print(f"  假设 C191620 确定后，E行候选从 633,271 缩减到 N")
    print(f"  如果 N 很小，搜索空间大幅压缩")

if __name__ == '__main__':
    main()
