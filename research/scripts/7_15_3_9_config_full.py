#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 「7 15 3 9」超級數獨 - 完整92錨點版本
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# 完整的92個錨點（從之前session整合）
FULL_92_ANCHORS = [
    # 行A (1): 4個
    {'row': 1, 'col': 3, 'value': 3},
    {'row': 1, 'col': 6, 'value': 12},
    {'row': 1, 'col': 8, 'value': 5},
    {'row': 1, 'col': 12, 'value': 14},
    # 行B (2): 4個
    {'row': 2, 'col': 2, 'value': 12},
    {'row': 2, 'col': 5, 'value': 3},
    {'row': 2, 'col': 7, 'value': 9},
    {'row': 2, 'col': 9, 'value': 6},
    # 行C (3): 16個 - 完全固定
    {'row': 3, 'col': 1, 'value': 7}, {'row': 3, 'col': 2, 'value': 15},
    {'row': 3, 'col': 3, 'value': 3}, {'row': 3, 'col': 4, 'value': 9},
    {'row': 3, 'col': 5, 'value': 11}, {'row': 3, 'col': 6, 'value': 12},
    {'row': 3, 'col': 7, 'value': 6}, {'row': 3, 'col': 8, 'value': 5},
    {'row': 3, 'col': 9, 'value': 10}, {'row': 3, 'col': 10, 'value': 2},
    {'row': 3, 'col': 11, 'value': 1}, {'row': 3, 'col': 12, 'value': 14},
    {'row': 3, 'col': 13, 'value': 13}, {'row': 3, 'col': 14, 'value': 16},
    {'row': 3, 'col': 15, 'value': 4}, {'row': 3, 'col': 16, 'value': 8},
    # 行D (4): 16個 - 完全固定
    {'row': 4, 'col': 1, 'value': 11}, {'row': 4, 'col': 2, 'value': 4},
    {'row': 4, 'col': 3, 'value': 13}, {'row': 4, 'col': 4, 'value': 7},
    {'row': 4, 'col': 5, 'value': 16}, {'row': 4, 'col': 6, 'value': 8},
    {'row': 4, 'col': 7, 'value': 1}, {'row': 4, 'col': 8, 'value': 9},
    {'row': 4, 'col': 9, 'value': 3}, {'row': 4, 'col': 10, 'value': 15},
    {'row': 4, 'col': 11, 'value': 2}, {'row': 4, 'col': 12, 'value': 6},
    {'row': 4, 'col': 13, 'value': 5}, {'row': 4, 'col': 14, 'value': 14},
    {'row': 4, 'col': 15, 'value': 10}, {'row': 4, 'col': 16, 'value': 12},
    # 行E (5): 3個
    {'row': 5, 'col': 5, 'value': 13},
    {'row': 5, 'col': 10, 'value': 5},
    {'row': 5, 'col': 13, 'value': 4},
    # 行F (6): 7個
    {'row': 6, 'col': 2, 'value': 8},
    {'row': 6, 'col': 5, 'value': 15},
    {'row': 6, 'col': 7, 'value': 4},
    {'row': 6, 'col': 8, 'value': 3},
    {'row': 6, 'col': 11, 'value': 10},
    {'row': 6, 'col': 14, 'value': 16},
    {'row': 6, 'col': 15, 'value': 12},
    # 行G (7): 6個
    {'row': 7, 'col': 1, 'value': 14},
    {'row': 7, 'col': 3, 'value': 4},
    {'row': 7, 'col': 4, 'value': 6},
    {'row': 7, 'col': 10, 'value': 9},
    {'row': 7, 'col': 13, 'value': 15},
    {'row': 7, 'col': 16, 'value': 2},
    # 行H (8): 6個
    {'row': 8, 'col': 2, 'value': 13},
    {'row': 8, 'col': 6, 'value': 5},
    {'row': 8, 'col': 8, 'value': 9},
    {'row': 8, 'col': 12, 'value': 11},
    {'row': 8, 'col': 14, 'value': 7},
    {'row': 8, 'col': 15, 'value': 1},
    # 行I (9): 16個 - 完全固定
    {'row': 9, 'col': 1, 'value': 13}, {'row': 9, 'col': 2, 'value': 1},
    {'row': 9, 'col': 3, 'value': 10}, {'row': 9, 'col': 4, 'value': 2},
    {'row': 9, 'col': 5, 'value': 8}, {'row': 9, 'col': 6, 'value': 11},
    {'row': 9, 'col': 7, 'value': 16}, {'row': 9, 'col': 8, 'value': 7},
    {'row': 9, 'col': 9, 'value': 14}, {'row': 9, 'col': 10, 'value': 4},
    {'row': 9, 'col': 11, 'value': 5}, {'row': 9, 'col': 12, 'value': 12},
    {'row': 9, 'col': 13, 'value': 9}, {'row': 9, 'col': 14, 'value': 6},
    {'row': 9, 'col': 15, 'value': 3}, {'row': 9, 'col': 16, 'value': 15},
    # 行J (10): 4個
    {'row': 10, 'col': 2, 'value': 5},
    {'row': 10, 'col': 6, 'value': 14},
    {'row': 10, 'col': 10, 'value': 8},
    {'row': 10, 'col': 12, 'value': 1},
    # 行K (11): 6個
    {'row': 11, 'col': 1, 'value': 1},
    {'row': 11, 'col': 3, 'value': 6},
    {'row': 11, 'col': 5, 'value': 10},
    {'row': 11, 'col': 8, 'value': 13},
    {'row': 11, 'col': 11, 'value': 9},
    {'row': 11, 'col': 14, 'value': 11},
    # 行L (12): 6個
    {'row': 12, 'col': 4, 'value': 4},
    {'row': 12, 'col': 6, 'value': 16},
    {'row': 12, 'col': 7, 'value': 14},
    {'row': 12, 'col': 9, 'value': 3},
    {'row': 12, 'col': 11, 'value': 12},
    {'row': 12, 'col': 13, 'value': 7},
    # 行M (13): 7個
    {'row': 13, 'col': 1, 'value': 15},
    {'row': 13, 'col': 5, 'value': 12},
    {'row': 13, 'col': 9, 'value': 5},
    {'row': 13, 'col': 10, 'value': 14},
    {'row': 13, 'col': 12, 'value': 8},
    {'row': 13, 'col': 15, 'value': 11},
    {'row': 13, 'col': 16, 'value': 6},
    # 行N (14): 5個
    {'row': 14, 'col': 3, 'value': 9},
    {'row': 14, 'col': 6, 'value': 6},
    {'row': 14, 'col': 9, 'value': 13},
    {'row': 14, 'col': 12, 'value': 15},
    {'row': 14, 'col': 16, 'value': 10},
    # 行O (15): 6個
    {'row': 15, 'col': 2, 'value': 1},
    {'row': 15, 'col': 5, 'value': 9},
    {'row': 15, 'col': 8, 'value': 15},
    {'row': 15, 'col': 11, 'value': 7},
    {'row': 15, 'col': 13, 'value': 16},
    {'row': 15, 'col': 14, 'value': 3},
    # 行P (16): 2個
    {'row': 16, 'col': 3, 'value': 2},
    {'row': 16, 'col': 7, 'value': 5},
]

def main():
    import json
    from collections import Counter
    
    # 保存完整92錨點配置
    config = {
        'grid_size': 16,
        'box_size': 4,
        'known_digits': FULL_92_ANCHORS,
        'sequence': '7 15 3 9',
        'metadata': {
            'version': 'V19.2',
            'description': '完整92錨點超級數獨配置'
        }
    }
    
    with open('sudoku_config_full_92.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    # 統計分析
    print("=" * 70)
    print("「7 15 3 9」超級數獨 - 完整92錨點配置分析")
    print("=" * 70)
    
    print(f"\n錨點總數: {len(FULL_92_ANCHORS)}")
    
    # 行分布
    row_counts = Counter(a['row'] for a in FULL_92_ANCHORS)
    print("\n行分布:")
    for r in range(1, 17):
        count = row_counts.get(r, 0)
        density = count / 16
        status = "✓ 完全固定" if count == 16 else f"○ {count}/16 ({density:.0%})"
        print(f"  行{r:2d} ({chr(64+r)}): {status}")
    
    # 值分布
    value_counts = Counter(a['value'] for a in FULL_92_ANCHORS)
    print("\n值分布:")
    for v in range(1, 17):
        count = value_counts.get(v, 0)
        print(f"  {v:2d}: {count:2d}次")
    
    # 關鍵序列分析
    print("\n關鍵序列「7 15 3 9」分析:")
    seq_values = [7, 15, 3, 9]
    print(f"  序列和: {sum(seq_values)}")
    print(f"  序列積: {seq_values[0] * seq_values[1] * seq_values[2] * seq_values[3]}")
    
    # 在錨點中的出現
    for val in seq_values:
        positions = [(a['row'], a['col']) for a in FULL_92_ANCHORS if a['value'] == val]
        print(f"  值{val}: 出現{len(positions)}次，位置: {positions[:5]}{'...' if len(positions) > 5 else ''}")
    
    print(f"\n💾 配置已保存至: sudoku_config_full_92.json")


if __name__ == '__main__':
    main()
