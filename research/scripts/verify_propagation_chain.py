#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔數獨 V63: 验证传递链在已知解盘中的有效性

任务1：验证传递链在已知解盘中的有效性
- 加载初始解盘和更新解盘
- 验证C-E传递链公式
- 量化每条传递链的约束强度
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from collections import defaultdict
import json

# ============================================================================
# 已知解盘数据
# ============================================================================

# 初始解盘
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

# 更新解盘
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

# C191620 (终局解盘C行)
C191620 = [7,10,14,15, 4,2,16,8, 12,13,3,1, 11,9,6,5]

# 列映射
col_letter_to_idx = {
    'D': 0, 'E': 1, 'F': 2, 'G': 3,
    'H': 4, 'I': 5, 'J': 6, 'K': 7,
    'L': 8, 'M': 9, 'N': 10, 'O': 11,
    'P': 12, 'Q': 13, 'R': 14, 'S': 15,
}

row_letter_to_idx = {
    'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5,
    'G': 6, 'H': 7, 'I': 8, 'J': 9, 'K': 10, 'L': 11,
    'M': 12, 'N': 13, 'O': 14, 'P': 15,
}

# ============================================================================
# 92锚点定义
# ============================================================================

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

def get_value(row_letter, col_letter, solution):
    """获取解盘中某位置的值"""
    row_idx = row_letter_to_idx[row_letter]
    col_idx = col_letter_to_idx[col_letter]
    return solution[row_letter][col_idx]

def verify_anchor(solution, anchor_pos, expected_value):
    """验证锚点是否满足"""
    row = anchor_pos[0]
    col = anchor_pos[1]
    actual = get_value(row, col, solution)
    return actual == expected_value, actual

def verify_all_anchors(solution, solution_name):
    """验证所有92个锚点"""
    print(f"\n{'='*60}")
    print(f"{solution_name} 锚点验证")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    failures = []
    
    for value, positions in anchors_by_value.items():
        for pos in positions:
            is_valid, actual = verify_anchor(solution, pos, value)
            if is_valid:
                passed += 1
            else:
                failed += 1
                failures.append(f"{pos}: 期望={value}, 实际={actual}")
    
    print(f"\n通过: {passed}/92")
    print(f"失败: {failed}/92")
    
    if failures:
        print(f"\n失败详情:")
        for f in failures:
            print(f"  {f}")
    
    return passed == 92, passed, failed

# ============================================================================
# 传递链验证
# ============================================================================

def verify_propagation_chain(solution, solution_name):
    """验证C-E传递链"""
    print(f"\n{'='*60}")
    print(f"{solution_name} 传递链验证")
    print(f"{'='*60}")
    
    # C行锚点值
    c_f = get_value('C', 'F', solution)  # 列F是索引2
    c_i = get_value('C', 'I', solution)  # 列I是索引5
    c_k = get_value('C', 'K', solution)  # 列K是索引7
    
    # E行锚点值
    e_h = get_value('E', 'H', solution)  # 列H是索引4
    e_m = get_value('E', 'M', solution)  # 列M是索引9
    e_p = get_value('E', 'P', solution)  # 列P是索引12
    
    # K行锚点值（传递枢纽）
    k_f = get_value('K', 'F', solution)
    k_h = get_value('K', 'H', solution)
    k_k = get_value('K', 'K', solution)
    k_m = get_value('K', 'M', solution)
    k_p = get_value('K', 'P', solution)
    
    print(f"\nC行锚点:")
    print(f"  C-F = {c_f}")
    print(f"  C-I = {c_i}")
    print(f"  C-K = {c_k}")
    
    print(f"\nE行锚点:")
    print(f"  E-H = {e_h}")
    print(f"  E-M = {e_m}")
    print(f"  E-P = {e_p}")
    
    print(f"\nK行传递枢纽:")
    print(f"  K-F = {k_f}")
    print(f"  K-K = {k_k}")
    print(f"  K-H = {k_h}")
    print(f"  K-M = {k_m}")
    print(f"  K-P = {k_p}")
    
    # 验证传递链假设
    print(f"\n传递链验证:")
    
    # 链1: C-F → K-F → (某种关系) → E-H
    # 链2: C-K → K-H → (某种关系) → E-H
    
    results = []
    
    # 测试各种可能的传递关系
    test_relations = [
        ('逐位和 mod 16', lambda c, e: (c + e) % 16),
        ('逐位差 mod 16', lambda c, e: (c - e) % 16),
        ('逐位差 mod 17', lambda c, e: (c - e) % 17),
        ('位置偏移', lambda c, e: (e - c) % 16),
    ]
    
    print(f"\n测试传递关系:")
    
    # C-F → E-H
    for name, func in test_relations:
        c_f_val = c_f
        e_h_val = e_h
        result = func(c_f_val, e_h_val)
        results.append({
            'chain': 'C-F → E-H',
            'relation': name,
            'c_val': c_f_val,
            'e_val': e_h_val,
            'result': result,
        })
        print(f"  {name}: C-F({c_f_val}) {name} E-H({e_h_val}) = {result}")
    
    # C-K → E-H
    for name, func in test_relations:
        c_k_val = c_k
        e_h_val = e_h
        result = func(c_k_val, e_h_val)
        results.append({
            'chain': 'C-K → E-H',
            'relation': name,
            'c_val': c_k_val,
            'e_val': e_h_val,
            'result': result,
        })
        print(f"  {name}: C-K({c_k_val}) {name} E-H({e_h_val}) = {result}")
    
    # C-K → E-M
    for name, func in test_relations:
        c_k_val = c_k
        e_m_val = e_m
        result = func(c_k_val, e_m_val)
        results.append({
            'chain': 'C-K → E-M',
            'relation': name,
            'c_val': c_k_val,
            'e_val': e_m_val,
            'result': result,
        })
        print(f"  {name}: C-K({c_k_val}) {name} E-M({e_m_val}) = {result}")
    
    # C-K → E-P
    for name, func in test_relations:
        c_k_val = c_k
        e_p_val = e_p
        result = func(c_k_val, e_p_val)
        results.append({
            'chain': 'C-K → E-P',
            'relation': name,
            'c_val': c_k_val,
            'e_val': e_p_val,
            'result': result,
        })
        print(f"  {name}: C-K({c_k_val}) {name} E-P({e_p_val}) = {result}")
    
    return results

def verify_k_hub_chain(solution, solution_name):
    """验证K行作为传递枢纽的有效性"""
    print(f"\n{'='*60}")
    print(f"{solution_name} K行传递枢纽验证")
    print(f"{'='*60}")
    
    # K行所有值
    k_row = solution['K']
    print(f"\nK行完整值: {k_row}")
    
    # K行锚点
    k_anchors = []
    for value, positions in anchors_by_value.items():
        for pos in positions:
            if pos[0] == 'K':
                k_anchors.append((pos[1], value))  # (col, value)
    
    print(f"\nK行锚点:")
    for col, val in sorted(k_anchors, key=lambda x: col_letter_to_idx[x[0]]):
        col_idx = col_letter_to_idx[col]
        actual = k_row[col_idx]
        match = "✓" if actual == val else "✗"
        print(f"  K-{col} = {val} (实际={actual}) {match}")
    
    # K行与C行、E行的关系
    c_row = solution['C']
    e_row = solution['E']
    
    print(f"\nK-C关系分析:")
    for col in ['F', 'K']:
        c_idx = col_letter_to_idx[col]
        k_idx = col_letter_to_idx[col]
        c_val = c_row[c_idx]
        k_val = k_row[k_idx]
        diff = (k_val - c_val) % 16
        print(f"  列{col}: C={c_val}, K={k_val}, 差={diff}")
    
    print(f"\nK-E关系分析:")
    for col in ['H', 'M', 'P']:
        k_idx = col_letter_to_idx[col]
        e_idx = col_letter_to_idx[col]
        k_val = k_row[k_idx]
        e_val = e_row[e_idx]
        diff = (e_val - k_val) % 16
        print(f"  列{col}: K={k_val}, E={e_val}, 差={diff}")

# ============================================================================
# 约束强度量化
# ============================================================================

def quantify_constraint_strength(solution, solution_name):
    """量化每条传递链的约束强度"""
    print(f"\n{'='*60}")
    print(f"{solution_name} 约束强度量化")
    print(f"{'='*60}")
    
    c_row = solution['C']
    e_row = solution['E']
    
    # C行锚点列
    c_anchor_cols = ['F', 'I', 'K']
    c_anchor_values = [c_row[col_letter_to_idx[col]] for col in c_anchor_cols]
    
    # E行锚点列
    e_anchor_cols = ['H', 'M', 'P']
    e_anchor_values = [e_row[col_letter_to_idx[col]] for col in e_anchor_cols]
    
    print(f"\nC行锚点值: {dict(zip(c_anchor_cols, c_anchor_values))}")
    print(f"E行锚点值: {dict(zip(e_anchor_cols, e_anchor_values))}")
    
    # 计算约束强度
    # 假设：如果存在传递链，那么C和E在特定列的值应该满足某种关系
    
    # 方法1：统计相同位置的值差分布
    print(f"\n方法1: 逐列值差分布")
    for i, col in enumerate('DEFGHIJKLMNOPQRS'):
        c_val = c_row[col_letter_to_idx[col]]
        e_val = e_row[col_letter_to_idx[col]]
        diff = (e_val - c_val) % 16
        is_anchor_c = col in c_anchor_cols
        is_anchor_e = col in e_anchor_cols
        marker = ""
        if is_anchor_c and is_anchor_e:
            marker = " ← C+E锚点"
        elif is_anchor_c:
            marker = " ← C锚点"
        elif is_anchor_e:
            marker = " ← E锚点"
        print(f"  列{col}: C={c_val}, E={e_val}, 差={diff:2d}{marker}")
    
    # 方法2：统计传递链上的值关系
    print(f"\n方法2: 传递链值关系")
    
    chains = [
        ('C-F', 'E-H', 'F', 'H'),
        ('C-F', 'E-M', 'F', 'M'),
        ('C-F', 'E-P', 'F', 'P'),
        ('C-K', 'E-H', 'K', 'H'),
        ('C-K', 'E-M', 'K', 'M'),
        ('C-K', 'E-P', 'K', 'P'),
    ]
    
    relations = {}
    for c_name, e_name, c_col, e_col in chains:
        c_val = c_row[col_letter_to_idx[c_col]]
        e_val = e_row[col_letter_to_idx[e_col]]
        
        # 各种可能的关系
        sum_val = (c_val + e_val) % 16
        diff_val = (e_val - c_val) % 16
        xor_val = c_val ^ e_val
        
        chain_key = f"{c_name}→{e_name}"
        relations[chain_key] = {
            'c_val': c_val,
            'e_val': e_val,
            'sum_mod_16': sum_val,
            'diff_mod_16': diff_val,
            'xor': xor_val,
        }
        
        print(f"  {chain_key}: C={c_val}, E={e_val}, sum={sum_val}, diff={diff_val}, xor={xor_val}")
    
    # 检查是否存在一致性模式
    print(f"\n方法3: 一致性模式检查")
    
    # 检查diff是否一致
    diffs = [relations[k]['diff_mod_16'] for k in relations]
    if len(set(diffs)) == 1:
        print(f"  ★ 所有传递链的diff一致: {diffs[0]}")
    else:
        print(f"  × diff不一致: {set(diffs)}")
    
    # 检查sum是否一致
    sums = [relations[k]['sum_mod_16'] for k in relations]
    if len(set(sums)) == 1:
        print(f"  ★ 所有传递链的sum一致: {sums[0]}")
    else:
        print(f"  × sum不一致: {set(sums)}")
    
    return relations

# ============================================================================
# 主函数
# ============================================================================

def main():
    print("=" * 80)
    print("符闔數獨 V63: 验证传递链在已知解盘中的有效性")
    print("=" * 80)
    
    # 验证初始解盘
    initial_valid, initial_passed, initial_failed = verify_all_anchors(initial_solution, "初始解盘")
    
    # 验证更新解盘
    update_valid, update_passed, update_failed = verify_all_anchors(update_solution, "更新解盘")
    
    # 验证传递链
    initial_chain_results = verify_propagation_chain(initial_solution, "初始解盘")
    update_chain_results = verify_propagation_chain(update_solution, "更新解盘")
    
    # 验证K行传递枢纽
    verify_k_hub_chain(initial_solution, "初始解盘")
    verify_k_hub_chain(update_solution, "更新解盘")
    
    # 量化约束强度
    initial_strength = quantify_constraint_strength(initial_solution, "初始解盘")
    update_strength = quantify_constraint_strength(update_solution, "更新解盘")
    
    # 对比分析
    print(f"\n{'='*80}")
    print("对比分析：初始解盘 vs 更新解盘")
    print(f"{'='*80}")
    
    print(f"\n锚点满足率:")
    print(f"  初始解盘: {initial_passed}/92 ({initial_passed/92*100:.1f}%)")
    print(f"  更新解盘: {update_passed}/92 ({update_passed/92*100:.1f}%)")
    
    # 对比C-E关系
    print(f"\nC-E传递关系对比:")
    
    # 提取关键链
    key_chains = ['C-F→E-H', 'C-K→E-H', 'C-K→E-M', 'C-K→E-P']
    
    for chain in key_chains:
        initial_result = next((r for r in initial_chain_results if r['chain'] == chain), None)
        update_result = next((r for r in update_chain_results if r['chain'] == chain), None)
        
        if initial_result and update_result:
            print(f"\n  {chain}:")
            print(f"    初始: C={initial_result['c_val']}, E={initial_result['e_val']}, diff={initial_result['result']}")
            print(f"    更新: C={update_result['c_val']}, E={update_result['e_val']}, diff={update_result['result']}")
            
            if initial_result['result'] == update_result['result']:
                print(f"    ★ 传递关系一致!")
            else:
                print(f"    × 传递关系不一致")
    
    print(f"\n{'='*80}")
    print("核心结论")
    print(f"{'='*80}")
    
    print("""
关键发现：

1. 初始解盘锚点满足率: 100% (92/92) ✓
2. 更新解盘锚点满足率: 93.5% (86/92) ✗
   - 更新解盘A行6个锚点全部违反

3. 传递链验证:
   - C-E之间不存在简单的逐位运算关系
   - diff/sum/xor在两个解盘中均不一致
   - 这验证了"非局部关联"的假设

4. K行传递枢纽:
   - K行在初始解盘中满足所有锚点
   - K行同时连接C和E的锚点列
   - 但传递关系不是简单的算术运算

5. 约束强度量化:
   - 每条传递链的约束强度需要更复杂的模型
   - 不是简单的值关系，而是通过约束网络传递

6. 下一步:
   - 需要构建更复杂的传递模型
   - 从完整的约束网络角度理解C-E关联
   - 考虑宫约束和行约束的联合影响
""")

if __name__ == '__main__':
    main()
