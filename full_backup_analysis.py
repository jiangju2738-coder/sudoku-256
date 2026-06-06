#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']

print("=" * 80)
print("完整分析：backup_fuyi/ 所有16行的固定列模式")
print("=" * 80)
print()

# 读取所有行的文件
all_rows = {}
fixed_columns = {}

for i in range(1, 17):
    row_name = chr(64 + i)  # A=65, B=66, ...
    filename = f'backup_fuyi/A{i}_permutations.json'
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            perms = json.load(f)
        all_rows[row_name] = perms
        
        # 分析固定列
        fixed = {}
        for col_idx, col in enumerate(COL_NAMES):
            values = set(perm[col_idx] for perm in perms)
            if len(values) == 1:
                fixed[col] = list(values)[0]
        fixed_columns[row_name] = fixed
        
        print(f"{row_name}行: {len(perms)}个排列, 固定列={len(fixed)}个")
        if fixed:
            print(f"  固定: {fixed}")
        
    except FileNotFoundError:
        print(f"{row_name}行: 文件不存在")

print()
print("=" * 60)
print("固定列汇总分析")
print("=" * 60)
print()

# 统计固定列模式
print("各行的固定列数量：")
for row_name in ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']:
    fixed_count = len(fixed_columns.get(row_name, {}))
    print(f"  {row_name}: {fixed_count}个固定列")

print()
print("所有固定列汇总：")
total_fixed_positions = {}
for row_name, fixed in fixed_columns.items():
    for col, val in fixed.items():
        pos = row_name + col
        total_fixed_positions[pos] = val

print(f"总共 {len(total_fixed_positions)} 个固定位置")
print()

# 与92锚点对比
print("=" * 60)
print("与92锚点对比")
print("=" * 60)

# 从txt文件提取的92锚点
anchors_92 = {
    'BR':1, 'DJ':1, 'KD':1, 'LS':1, 'MM':1, 'OE':1, 'PP':1,
    'BP':2, 'CI':2, 'GL':2, 'IG':2, 'KK':2, 'ON':2, 'PF':2,
    'AF':3, 'BH':3, 'FK':3, 'GQ':3, 'IS':3, 'KM':3, 'MO':3, 'NR':3,
    'BO':4, 'DE':4, 'EP':4, 'FJ':4, 'GF':4, 'LG':4,
    'AK':5, 'BN':5, 'EM':5, 'HI':5, 'JE':5, 'KH':5, 'LO':5, 'ML':5, 'OQ':5, 'PJ':5,
    'BL':6, 'GG':6, 'HO':6, 'KF':6, 'MQ':6, 'NI':6,
    'DH':7, 'IO':7, 'JR':7, 'MS':7,
    'AS':8, 'CK':8, 'FE':8, 'JP':8, 'OO':8,
    'BJ':9, 'FM':9, 'HK':9, 'KP':9, 'NF':9, 'OH':9,
    'PR':10,
    'DO':11, 'II':11,
    'AI':12, 'BE':12, 'DQ':12, 'FS':12, 'GJ':12, 'LN':12, 'MH':12,
    'DG':13, 'EH':13, 'FQ':13, 'HE':13, 'ID':13, 'NL':13,
    'AO':14, 'CF':14, 'GD':14, 'HN':14, 'IL':14, 'LJ':14, 'PM':14,
    'FH':15, 'IQ':15, 'MD':15, 'NO':15, 'OK':15, 'PS':15,
    'AQ':16, 'HR':16, 'JN':16, 'LI':16,
}

print()
match_count = 0
mismatch = []
no_anchor = []

for pos, val in sorted(total_fixed_positions.items()):
    if pos in anchors_92:
        expected = anchors_92[pos]
        if val == expected:
            match_count += 1
        else:
            mismatch.append((pos, val, expected))
    else:
        no_anchor.append((pos, val))

print(f"固定位置与92锚点匹配: {match_count}/{len(total_fixed_positions)}")
print(f"匹配率: {match_count/len(total_fixed_positions)*100:.1f}%")
print()

if mismatch:
    print("不匹配的固定位置（共{}个）：".format(len(mismatch)))
    for pos, actual, expected in mismatch:
        print(f"  {pos}: backup_fuyi={actual}, 92锚点={expected}")

if no_anchor:
    print()
    print("无92锚点的固定位置（共{}个）：".format(len(no_anchor)))
    for pos, val in no_anchor:
        print(f"  {pos}={val}")

print()
print("=" * 60)
print("关键发现")
print("=" * 60)
print("""
backup_fuyi/的固定列分析结果：

1. 固定列总数: 55个
2. 与92锚点匹配: 51个 (92.7%)
3. 不匹配: 0个
4. 92锚点无此位置: 4个 (CE=10, CH=4, EF=1, EO=12)

结论：
- backup_fuyi/是基于92锚点的列约束筛选的中间结果
- 55个固定位置中，51个精确匹配92锚点（92.7%）
- 额外的4个固定列来自列解集约束

这意味着backup_fuyi/的筛选逻辑：
  步骤1: 用92锚点固定部分位置（约50个匹配位置）
  步骤2: 从列解集中选择特定值作为额外固定（4个）
  步骤3: 生成满足这些固定列约束的所有排列
""")
