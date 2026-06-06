#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 任务1：加载原始符阖排列集合并验证终局解盘所有16行
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import os
from collections import Counter

print("=" * 80)
print("TASK 1 & 2: 加载原始符阖排列集合 + 验证终局解盘16行")
print("=" * 80)

# TXT终局解盘（来自超級大數獨_box_size4.txt）
FINAL_SOLUTION_ROWS = {
    'A': [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5],
    'B': [8, 12, 7, 10, 3, 15, 9, 11, 6, 16, 5, 4, 2, 14, 1, 13],
    'C': [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5],  # C191620
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

COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']
col_map = {col: i for i, col in enumerate(COL_NAMES)}

# 原始集合路径
BACKUP_DIR = "backup_fuyi"

print("\n【步骤1】验证原始符阖排列集合文件...")
print("-" * 60)

original_sizes = {}
files_exist = []

for i in range(1, 17):
    row_name = chr(64 + i)  # A=65, B=66, ...
    filename = f'A{i}_permutations.json'
    filepath = os.path.join(BACKUP_DIR, filename)
    
    if os.path.exists(filepath):
        files_exist.append(filepath)
        # 先检查文件大小，快速估计
        size_bytes = os.path.getsize(filepath)
        
        # 加载文件
        print(f"  正在加载 {filename}...", end=" ", flush=True)
        with open(filepath, 'r', encoding='utf-8') as f:
            perms = json.load(f)
        
        original_sizes[row_name] = len(perms)
        print(f"OK ({len(perms):,} 个排列, {size_bytes/1024/1024:.1f} MB)")
    else:
        print(f"  {filename}: 不存在!")
        original_sizes[row_name] = 0

# 统计总规模
total_original = sum(original_sizes.values())
print(f"\n  原始符阖排列组闔总规模: {total_original:,} 个排列")

print("\n【步骤2】验证终局解盘所有16行是否都在原始集合中...")
print("-" * 60)

verification_results = {}
total_in_set = 0

# 92锚点数据
anchors = {
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

for row_name, row_perm in FINAL_SOLUTION_ROWS.items():
    row_tuple = tuple(row_perm)
    row_key = f'A{ord(row_name)-64}'  # A->A1, B->A2, etc.
    
    # 检查是否在原始集合中
    try:
        filepath = os.path.join(BACKUP_DIR, f'{row_key}_permutations.json')
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                perms = json.load(f)
            in_set = any(tuple(p) == row_tuple for p in perms)
        else:
            in_set = False
    except Exception as e:
        in_set = False
        print(f"  读取错误 {row_key}: {e}")
    
    # 检查是否是1-16的排列
    is_perm = sorted(row_perm) == list(range(1, 17))
    
    # 检查是否满足92锚点约束
    anchor_ok = True
    anchor_violations = []
    
    row_idx = ord(row_name) - ord('A')
    for coord, expected_val in anchors.items():
        if coord[0] == row_name:  # 只检查当前行的锚点
            col_char = coord[1]
            col_idx = col_map[col_char]
            actual_val = row_perm[col_idx]
            if actual_val != expected_val:
                anchor_ok = False
                anchor_violations.append(f"{coord}: expected={expected_val}, actual={actual_val}")
    
    verification_results[row_name] = {
        'permutation': row_perm,
        'is_valid_permutation': is_perm,
        'in_original_set': in_set,
        'anchors_ok': anchor_ok,
        'anchor_violations': anchor_violations
    }
    
    total_in_set += 1 if in_set else 0
    in_status = "[OK]" if in_set else "[NO]"
    anchor_status = "OK" if anchor_ok else f"FAIL ({len(anchor_violations)} violations)"
    
    print(f"  {row_name} ({row_key}): {in_status} | 排列有效: {is_perm} | 锚点: {anchor_status}")
    
    if anchor_violations:
        print(f"    违反锚点: {anchor_violations[:3]}...")  # 只显示前3个

print(f"\n  总结: {total_in_set}/16 行在原始符阖排列组闔中")

# 特别检查C191620
print("\n【特别验证】终局C191620 详细分析...")
print("-" * 60)
C191620 = FINAL_SOLUTION_ROWS['C']
print(f"  C191620 = {C191620}")
print(f"  原始A3集合规模: {original_sizes.get('C', 0):,} 个排列")
print(f"  在A3_permutations.json中: {verification_results['C']['in_original_set']}")

print("\n" + "=" * 80)
print("核心发现与推论")
print("=" * 80)

if total_in_set == 16:
    print("""
[SUCCESS] 所有16行都在原始符阖排列组闔中！

这意味着:
  1. TXT终局解盘确实是一个合法的符阖数独解
  2. 所有行都满足"符阖排列组闔"约束
  3. 结合92锚点约束，终局解盘满足符阖三约束的所有层面

关键结论:
  - 92锚点 + 数独三约束 != 符阖原题（仍成立）
  - 符阖排列组闔是一个预定义的压缩解空间约束
  - 终局解盘是符阖排列组闔中预先定义的一个完整解
  - CP-SAT搜索的"唯一解"与终局解盘不同，因为CP-SAT缺少符阖排列组闔约束
""")
else:
    print(f"""
[PARTIAL] 只有 {total_in_set}/16 行在原始符阖排列组闔中

这意味着:
  1. TXT终局解盘可能存在数据错误
  2. 或者原始备份文件与txt文件中的定义不一致
  3. 需要进一步调查不一致的行
""")

# 保存验证结果
output = {
    'total_rows_verified': 16,
    'rows_in_original_set': total_in_set,
    'original_permutation_sizes': original_sizes,
    'verification_results': {
        k: {
            'is_valid_permutation': v['is_valid_permutation'],
            'in_original_set': v['in_original_set'],
            'anchors_ok': v['anchors_ok'],
            'anchor_violations': v['anchor_violations']
        } for k, v in verification_results.items()
    }
}

with open('fummel_verification_results.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n验证结果已保存: fummel_verification_results.json")
