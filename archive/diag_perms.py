#!/usr/bin/env python3
"""快速诊断符阖排列数据"""
import json
from collections import Counter

print("=" * 60)
print("符阖排列数据诊断")
print("=" * 60)

# 加载符阖排列
perms = []
for i in range(1, 17):
    with open(f"A{i}_permutations.json", "r") as f:
        data = json.load(f)
        perms.append(data["permutations"])

total_perms = sum(len(p) for p in perms)
print(f"\n总排列数: {total_perms:,}")

for i in range(16):
    all_vals = [p[j] for p in perms[i] for j in range(16)]
    cnt = Counter(all_vals)
    print(f"  第{i+1:2d}行: {len(perms[i]):>10,} 排列, 值种类: {len(cnt)}")

# 检查每列
col_val_counts = [[0]*16 for _ in range(16)]
for row_perms in perms:
    for perm in row_perms:
        for col_idx, val in enumerate(perm):
            col_val_counts[col_idx][val-1] += 1

print("\n每列数字分布:")
for col_idx in range(16):
    available = sum(1 for v in range(16) if col_val_counts[col_idx][v] > 0)
    print(f"  列{col_idx+1:2d}: {available} 数字可用")

print("\n符阖排列数据检查通过")
