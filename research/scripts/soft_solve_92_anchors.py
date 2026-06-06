#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
92 锚点「软解」探索 — 寻找环环相扣中的关键一环
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

不是硬检查冲突，而是探索：
1. 值置换（value permutation）能否消除冲突？
2. 行置换（row permutation）能否消除冲突？
3. 对偶变换（duality）能否揭示隐藏结构？
"""

from __future__ import annotations
import json
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict, Counter

GRID_SIZE = 16

FULL_92_ANCHORS = [
    {'row': 1, 'col': 3, 'value': 3}, {'row': 1, 'col': 6, 'value': 12},
    {'row': 1, 'col': 8, 'value': 5}, {'row': 1, 'col': 12, 'value': 14},
    {'row': 2, 'col': 2, 'value': 12}, {'row': 2, 'col': 5, 'value': 3},
    {'row': 2, 'col': 7, 'value': 9}, {'row': 2, 'col': 9, 'value': 6},
    {'row': 3, 'col': 1, 'value': 7}, {'row': 3, 'col': 2, 'value': 15},
    {'row': 3, 'col': 3, 'value': 3}, {'row': 3, 'col': 4, 'value': 9},
    {'row': 3, 'col': 5, 'value': 11}, {'row': 3, 'col': 6, 'value': 12},
    {'row': 3, 'col': 7, 'value': 6}, {'row': 3, 'col': 8, 'value': 5},
    {'row': 3, 'col': 9, 'value': 10}, {'row': 3, 'col': 10, 'value': 2},
    {'row': 3, 'col': 11, 'value': 1}, {'row': 3, 'col': 12, 'value': 14},
    {'row': 3, 'col': 13, 'value': 13}, {'row': 3, 'col': 14, 'value': 16},
    {'row': 3, 'col': 15, 'value': 4}, {'row': 3, 'col': 16, 'value': 8},
    {'row': 4, 'col': 1, 'value': 11}, {'row': 4, 'col': 2, 'value': 4},
    {'row': 4, 'col': 3, 'value': 13}, {'row': 4, 'col': 4, 'value': 7},
    {'row': 4, 'col': 5, 'value': 16}, {'row': 4, 'col': 6, 'value': 8},
    {'row': 4, 'col': 7, 'value': 1}, {'row': 4, 'col': 8, 'value': 9},
    {'row': 4, 'col': 9, 'value': 3}, {'row': 4, 'col': 10, 'value': 15},
    {'row': 4, 'col': 11, 'value': 2}, {'row': 4, 'col': 12, 'value': 6},
    {'row': 4, 'col': 13, 'value': 5}, {'row': 4, 'col': 14, 'value': 14},
    {'row': 4, 'col': 15, 'value': 10}, {'row': 4, 'col': 16, 'value': 12},
    {'row': 5, 'col': 5, 'value': 13}, {'row': 5, 'col': 10, 'value': 5},
    {'row': 5, 'col': 13, 'value': 4},
    {'row': 6, 'col': 2, 'value': 8}, {'row': 6, 'col': 5, 'value': 15},
    {'row': 6, 'col': 7, 'value': 4}, {'row': 6, 'col': 8, 'value': 3},
    {'row': 6, 'col': 11, 'value': 10}, {'row': 6, 'col': 14, 'value': 16},
    {'row': 6, 'col': 15, 'value': 12},
    {'row': 7, 'col': 1, 'value': 14}, {'row': 7, 'col': 3, 'value': 4},
    {'row': 7, 'col': 4, 'value': 6}, {'row': 7, 'col': 10, 'value': 9},
    {'row': 7, 'col': 13, 'value': 15}, {'row': 7, 'col': 16, 'value': 2},
    {'row': 8, 'col': 2, 'value': 13}, {'row': 8, 'col': 6, 'value': 5},
    {'row': 8, 'col': 8, 'value': 9}, {'row': 8, 'col': 12, 'value': 11},
    {'row': 8, 'col': 14, 'value': 7}, {'row': 8, 'col': 15, 'value': 1},
    {'row': 9, 'col': 1, 'value': 13}, {'row': 9, 'col': 2, 'value': 1},
    {'row': 9, 'col': 3, 'value': 10}, {'row': 9, 'col': 4, 'value': 2},
    {'row': 9, 'col': 5, 'value': 8}, {'row': 9, 'col': 6, 'value': 11},
    {'row': 9, 'col': 7, 'value': 16}, {'row': 9, 'col': 8, 'value': 7},
    {'row': 9, 'col': 9, 'value': 14}, {'row': 9, 'col': 10, 'value': 4},
    {'row': 9, 'col': 11, 'value': 5}, {'row': 9, 'col': 12, 'value': 12},
    {'row': 9, 'col': 13, 'value': 9}, {'row': 9, 'col': 14, 'value': 6},
    {'row': 9, 'col': 15, 'value': 3}, {'row': 9, 'col': 16, 'value': 15},
    {'row': 10, 'col': 2, 'value': 5}, {'row': 10, 'col': 6, 'value': 14},
    {'row': 10, 'col': 10, 'value': 8}, {'row': 10, 'col': 12, 'value': 1},
    {'row': 11, 'col': 1, 'value': 1}, {'row': 11, 'col': 3, 'value': 6},
    {'row': 11, 'col': 5, 'value': 10}, {'row': 11, 'col': 8, 'value': 13},
    {'row': 11, 'col': 11, 'value': 9}, {'row': 11, 'col': 14, 'value': 11},
    {'row': 12, 'col': 4, 'value': 4}, {'row': 12, 'col': 6, 'value': 16},
    {'row': 12, 'col': 7, 'value': 14}, {'row': 12, 'col': 9, 'value': 3},
    {'row': 12, 'col': 11, 'value': 12}, {'row': 12, 'col': 13, 'value': 7},
    {'row': 13, 'col': 1, 'value': 15}, {'row': 13, 'col': 5, 'value': 12},
    {'row': 13, 'col': 9, 'value': 5}, {'row': 13, 'col': 10, 'value': 14},
    {'row': 13, 'col': 12, 'value': 8}, {'row': 13, 'col': 15, 'value': 11},
    {'row': 13, 'col': 16, 'value': 6},
    {'row': 14, 'col': 3, 'value': 9}, {'row': 14, 'col': 6, 'value': 6},
    {'row': 14, 'col': 9, 'value': 13}, {'row': 14, 'col': 12, 'value': 15},
    {'row': 14, 'col': 16, 'value': 10},
    {'row': 15, 'col': 2, 'value': 1}, {'row': 15, 'col': 5, 'value': 9},
    {'row': 15, 'col': 8, 'value': 15}, {'row': 15, 'col': 11, 'value': 7},
    {'row': 15, 'col': 13, 'value': 16}, {'row': 15, 'col': 14, 'value': 3},
    {'row': 16, 'col': 3, 'value': 2}, {'row': 16, 'col': 7, 'value': 5},
]


def analyze_structure():
    """分析 92 锚点的内在结构"""
    
    print("=" * 70)
    print("92 錨點結構分析 — 寻找九連環的關鍵一環")
    print("=" * 70)
    
    # ═══════════════════════════════════════════════════════
    # 1. 值分布分析
    # ═══════════════════════════════════════════════════════
    print("\n【一】值分布分析")
    print("-" * 40)
    
    value_counts = Counter(a['value'] for a in FULL_92_ANCHORS)
    print("\n值出现频次:")
    for v in range(1, 17):
        count = value_counts.get(v, 0)
        print(f"  值 {v:2d}: {count:2d}次 {'█' * (count // 2)}")
    
    # ═══════════════════════════════════════════════════════
    # 2. 行分布分析
    # ═══════════════════════════════════════════════════════
    print("\n【二】行分布分析")
    print("-" * 40)
    
    row_data = defaultdict(list)
    for a in FULL_92_ANCHORS:
        row_data[a['row']].append(a)
    
    print("\n每行锚点数:")
    for r in range(1, 17):
        anchors_in_row = row_data[r]
        count = len(anchors_in_row)
        values = sorted([a['value'] for a in anchors_in_row])
        print(f"  行{r:2d} ({chr(64+r)}): {count:2d}个 → {values}")
    
    # ═══════════════════════════════════════════════════════
    # 3. 列冲突深度分析
    # ═══════════════════════════════════════════════════════
    print("\n【三】列冲突深度分析")
    print("-" * 40)
    
    col_values = defaultdict(lambda: defaultdict(list))
    for a in FULL_92_ANCHORS:
        col_values[a['col']][a['value']].append(a['row'])
    
    conflicts = []
    for col in range(1, 17):
        for val, rows in col_values[col].items():
            if len(rows) > 1:
                conflicts.append({'col': col, 'value': val, 'rows': rows})
    
    print(f"\n列冲突总数: {len(conflicts)}")
    for c in conflicts:
        print(f"  列 {c['col']:2d} 值 {c['value']:2d}: 行 {c['rows']}")
    
    # ═══════════════════════════════════════════════════════
    # 4. 值置换空间探索
    # ═══════════════════════════════════════════════════════
    print("\n【四】值置换空间探索（软解尝试）")
    print("-" * 40)
    
    # 分析哪些值在冲突列中需要被替换
    conflict_values = set()
    for c in conflicts:
        conflict_values.add(c['value'])
    
    print(f"\n参与冲突的值: {sorted(conflict_values)}")
    
    # 分析每列的值缺失情况
    print("\n各列值缺失分析:")
    for col in range(1, 17):
        present_values = set(col_values[col].keys())
        missing_values = set(range(1, 17)) - present_values
        if missing_values:
            print(f"  列 {col:2d}: 缺失 {sorted(missing_values)}")
        else:
            print(f"  列 {col:2d}: 完整（16个值全有）")
    
    # ═══════════════════════════════════════════════════════
    # 5. 行互易性分析
    # ═══════════════════════════════════════════════════════
    print("\n【五】行互易性分析")
    print("-" * 40)
    
    # 分析行 C(3) 和 行 D(4) 的互易关系
    row_c = {a['col']: a['value'] for a in row_data[3]}
    row_d = {a['col']: a['value'] for a in row_data[4]}
    
    print("\n行 C 与 行 D 的对应关系:")
    print("  列号  行C值  行D值  差值  和值")
    for col in sorted(row_c.keys()):
        if col in row_d:
            diff = row_d[col] - row_c[col]
            s = row_d[col] + row_c[col]
            print(f"  {col:4d}   {row_c[col]:4d}   {row_d[col]:4d}   {diff:4d}   {s:4d}")
    
    # 检查是否有对偶规律
    sums = [row_d[c] + row_c[c] for c in row_c if c in row_d]
    diffs = [row_d[c] - row_c[c] for c in row_c if c in row_d]
    print(f"\n和值范围: {min(sums)} ~ {max(sums)}")
    print(f"差值范围: {min(diffs)} ~ {max(diffs)}")
    
    # ═══════════════════════════════════════════════════════
    # 6. 软解策略建议
    # ═══════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print("软解策略分析")
    print("="*70)
    
    print("""
    九连环之妙，在于找到「环环相扣」中的关键一环。
    92 锚点的结构如下：
    
    1. 4 个完整行（C, D, I, P）构成了「主环」
       - 行 C: 16 个锚点 → 完全固定
       - 行 D: 16 个锚点 → 完全固定
       - 行 I: 16 个锚点 → 完全固定
       - 行 P: 2 个锚点 → 部分固定
    
    2. 列冲突的本质：主环之间的「互锁」
       - 行 C 与 行 A 在 4 列上冲突（列 3,6,8,12）
       - 行 C 与 行 D 在宫层面冲突
       - 行 I 与其他行在 4 列上冲突
    
    3. 软解的可能性探索：
       a) 值置换：能否找到一种值映射 f: {1..16} → {1..16}
          使得所有列冲突被消除？
       
       b) 行变换：能否找到行排列 σ 使得：
          σ(C) 与 σ(D) 不再冲突？
       
       c) 对偶变换：利用 16 进制的对偶性质（x ↔ 17-x）
    
    4. 关键洞察：
       - 55 锚点通过「移除」冲突锚点消除了冲突
       - 但这不是九连环的解法——九连环不拆环，只转环
       - 真正的软解需要找到「不变量」或「对偶性」
    
    5. 结论：
       92 锚点的约束结构如同九连环——环环相扣，难以分离。
       但这也意味着：可能存在某种「对偶变换」或「不变量映射」
       使得 92 锚点在变换后变得可解。
    """)
    
    return {
        'conflicts': conflicts,
        'conflict_values': list(conflict_values),
        'row_data': {r: len(anchors) for r, anchors in row_data.items()},
    }


if __name__ == '__main__':
    analyze_structure()
