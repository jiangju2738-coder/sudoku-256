#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys

# 解决编码问题
sys.stdout.reconfigure(encoding='utf-8')

with open('backup_fuyi/A1_permutations.json', 'r', encoding='utf-8') as f:
    a1 = json.load(f)

COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']

print("A1_permutations.json分析：")
print(f"  总排列数: {len(a1)}")
print()

# 固定位置
fixed_positions = []
for i, col in enumerate(COL_NAMES):
    values = set(perm[i] for perm in a1)
    if len(values) == 1:
        fixed_positions.append((col, list(values)[0]))
        print(f"  {col}: 固定值 = {list(values)[0]}")

print()
print(f"固定列数量: {len(fixed_positions)}")
print(f"固定列: {[f'{c}={v}' for c,v in fixed_positions]}")

# 对比92锚点
print()
print("与92锚点对比：")
a_anchor_map = {'AF':3, 'AI':12, 'AK':5, 'AO':14, 'AQ':16, 'AS':8}
for col, val in fixed_positions:
    anchor_name = 'A' + col
    if anchor_name in a_anchor_map:
        expected = a_anchor_map[anchor_name]
        match = "OK" if val == expected else "MISMATCH"
        print(f"  {anchor_name}={val} | 92锚点期望{expected} [{match}]")
    else:
        print(f"  {col}={val} | 92锚点无此定义")

# 检查AQ和AS
print()
print("关键：AQ和AS在A1中是否固定？")
q_vals = set(p[13] for p in a1)
s_vals = set(p[15] for p in a1)
print(f"  AQ=16 (92锚点): A1中Q列取值范围={sorted(q_vals)} | 包含16? {16 in q_vals}")
print(f"  AS=8 (92锚点): A1中S列取值范围={sorted(s_vals)} | 包含8? {8 in s_vals}")

print()
print("=" * 60)
print("重要发现：")
print("=" * 60)
print("""
A1_permutations.json只有4个固定列：F=3, I=12, K=5, O=14

但92锚点中A行有6个固定值：AF=3, AI=12, AK=5, AO=14, AQ=16, AS=8

这说明：
1. backup_fuyi/的固定列不完全等于92锚点
2. Q和S列在A1中是可变的（不是固定列）
3. backup_fuyi/可能是用'行约束'（仅考虑单行的列约束）筛选的
4. 92锚点的AQ=16和AS=8可能需要跨行约束才能固定

结论：backup_fuyi/中的固定列 = 92锚点的子集
      4个匹配 + 0个额外 = 4/6 的92锚点被固定
""")
