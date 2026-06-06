#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 假設分析：固定特定行能否得出符闔排列解空間完整解集
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

用戶問題：
「設若在無約束衝突的情況下固定包含第1行 第2行 或第13行等
如果能夠得出全部解集 那是不是又是另外一廻事」

核心假設：
- 固定有排列編號的行（A、B、E、F...）→ 可能得出 S_fummel 的完整解集
- 固定無排列編號的行（C、D、I）→ 可能 S_fummel 為空

驗證方向：
1. 分析哪些行有排列編號（在 S_fummel 中）
2. 哪些行無排列編號（可能不在 S_fummel 中）
3. 如果固定有編號的行，能否得到符闔排列解集
"""

from collections import defaultdict

# 行號映射
ROW_MAP = {chr(64+i): i for i in range(1, 17)}

# 每行符闔排列總數（從文件第65-80行）
ROW_PERM_COUNTS = {
    'A': 8731,
    'B': 902,
    'C': 407669,
    'D': 1980,
    'E': 633271,
    'F': 359,
    'G': 2356,
    'H': 4782,
    'I': 164,
    'J': 28984,
    'K': 2972,
    'L': 620,
    'M': 484,
    'N': 10668,
    'O': 5990,
    'P': 1809,
}

# 初始解盤排列編號（從文件第43-61行）
ROW_PERM_IDS = {
    'A': 5447,    # ✓ 有編號
    'B': 824,     # ✓ 有編號
    'C': None,    # ✗ 無編號
    'D': None,    # ✗ 無編號
    'E': 287832,  # ✓ 有編號
    'F': 227,     # ✓ 有編號
    'G': 2113,    # ✓ 有編號
    'H': 2588,    # ✓ 有編號
    'I': None,    # ✗ 無編號
    'J': 25793,   # ✓ 有編號
    'K': 1150,    # ✓ 有編號
    'L': 583,     # ✓ 有編號
    'M': 169,     # ✓ 有編號
    'N': 257,     # ✓ 有編號
    'O': 3011,    # ✓ 有編號
    'P': 1294,    # ✓ 有編號
}

# 初始解盤數據
SOLUTION = {
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

def analyze_row_classification():
    """分析行的分類：有編號 vs 無編號"""
    print("="*70)
    print("行的分類分析：有符闔排列編號 vs 無符闔排列編號")
    print("="*70)
    
    has_perm_rows = [(r, ROW_PERM_IDS[r], ROW_PERM_COUNTS[r]) for r in ROW_MAP.keys() if ROW_PERM_IDS.get(r) is not None]
    no_perm_rows = [(r, ROW_PERM_COUNTS[r]) for r in ROW_MAP.keys() if ROW_PERM_IDS.get(r) is None]
    
    print("\n【有符闔排列編號的行】(可能 ∈ S_fummel)")
    print("-"*50)
    for row, pid, total in has_perm_rows:
        row_num = ord(row) - 64
        print(f"  行{row}(第{row_num:2d}行): 排列編號 P{pid:>7,} / 總數 {total:>7,}")
    
    print(f"\n  小計: {len(has_perm_rows)} 行有編號")
    
    print("\n【無符闔排列編號的行】(可能 ∉ S_fummel)")
    print("-"*50)
    for row, total in no_perm_rows:
        row_num = ord(row) - 64
        print(f"  行{row}(第{row_num:2d}行): 無編號 (排列總數 {total:>7,})")
    
    print(f"\n  小計: {len(no_perm_rows)} 行無編號")
    
    print("\n" + "="*70)
    print("關鍵觀察")
    print("="*70)
    print(f"""
┌─────────────────────────────────────────────────────────────────┐
│  【有編號的行】A, B, E, F, G, H, J, K, L, M, N, O, P           │
│  (13 行，佔 81.25%)                                              │
│                                                                 │
│  【無編號的行】C, D, I                                          │
│  (3 行，佔 18.75%)                                              │
│                                                                 │
│  → 大部分行有符闔排列編號                                        │
│  → 只有 C, D, I 三行無編號                                       │
│  → 這意味著初始解盤中，13 行的排列在 S_fummel 中                 │
│  → 但 C, D, I 行的排列可能不在 S_fummel 中                      │
│                                                                 │
│  【推測】                                                        │
│  如果固定有編號的行（如 A, B, M），可能能得到 S_fummel 的解集     │
│  這是「另外一廻事」！                                             │
└─────────────────────────────────────────────────────────────────┘
""")

def analyze_fixed_row_scenarios():
    """分析固定不同行組合的情況"""
    print("\n" + "="*70)
    print("固定行組合的解集可能性分析")
    print("="*70)
    
    scenarios = [
        {
            'name': '固定 A 行 (第1行)',
            'fixed': ['A'],
            'perm_id': 5447,
            'perm_total': 8731,
            'hypothesis': '固定 A5447 後，搜索其他 15 行的符闔排列'
        },
        {
            'name': '固定 A+B 行 (第1+2行)',
            'fixed': ['A', 'B'],
            'perm_ids': [5447, 824],
            'perm_totals': [8731, 902],
            'hypothesis': '固定 A5447, B824 後，搜索其他 14 行'
        },
        {
            'name': '固定 M 行 (第13行)',
            'fixed': ['M'],
            'perm_id': 169,
            'perm_total': 484,
            'hypothesis': '固定 M169 後，搜索其他 15 行'
        },
        {
            'name': '固定 A+B+M 行',
            'fixed': ['A', 'B', 'M'],
            'perm_ids': [5447, 824, 169],
            'hypothesis': '固定三行有編號的行，搜索剩餘 13 行'
        },
        {
            'name': '固定 C 行 (第3行)',
            'fixed': ['C'],
            'perm_total': 407669,
            'hypothesis': 'C 行無編號，固定後可能 S_fummel 為空'
        },
    ]
    
    for scenario in scenarios:
        print(f"\n【{scenario['name']}】")
        print(f"  假設: {scenario['hypothesis']}")
        if 'perm_id' in scenario:
            print(f"  排列: 第{scenario['perm_id']:,}種 / 共{scenario['perm_total']:,}種")
        if 'perm_ids' in scenario:
            for i, row in enumerate(scenario['fixed']):
                pid = scenario['perm_ids'][i]
                total = ROW_PERM_COUNTS[row]
                print(f"    {row}行: 第{pid:,}種 / 共{total:,}種")
        
        # 分析可能性
        has_no_perm = any(r in ['C', 'D', 'I'] for r in scenario.get('fixed', []))
        if has_no_perm:
            print(f"  ⚠️ 包含無編號行 → S_fummel 可能為空")
        else:
            print(f"  ✓ 僅包含有編號行 → S_fummel 可能有解")

def theoretical_analysis():
    """理論分析：這是不是「另外一廻事」"""
    print("\n" + "="*70)
    print("理論分析：固定有編號行 vs 無編號行")
    print("="*70)
    
    print("""
┌────────────────────────────────────────────────────────────────────┐
│                   「另外一廻事」的本質                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  【情況 1：固定無編號行 (C, D, I)】                                  │
│  → 推測：符闔排列約束下無有效排列                                   │
│  → 結果：S_fummel = ∅ (空集)                                       │
│  → 這是「空解」情況                                                 │
│                                                                     │
│  【情況 2：固定有編號行 (A, B, M, E...)】                            │
│  → 這些行的排列在符闔排列集合中 ✓                                   │
│  → 如果無約束衝突，可能得到非空解集                                 │
│  → 結果：S_fummel ≠ ∅                                              │
│  → 這是「實解」情況 ← 用戶說的「另外一廻事」                        │
│                                                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                     │
│  【核心問題】                                                        │
│  固定 A5447 (第1行) + B824 (第2行) + M169 (第13行)...            │
│  → 能否得出 S_fummel 的完整解集？                                   │
│                                                                     │
│  如果答案是「能」：                                                   │
│  → 說明這 13 個有編號的行確實在 S_fummel 中                          │
│  → 初始解盤的其他 13 行排列對應符闔排列編號                         │
│  → 這确实是「另外一廻事」！                                          │
│                                                                     │
│  如果答案是「不能」：                                                  │
│  → 說明即使固定有編號的行，S_fummel 仍可能為空                       │
│  → 行間聯動約束可能導致無解                                         │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
    """)

def generate_fixed_rows_config():
    """生成固定行配置示例"""
    print("\n" + "="*70)
    print("固定行配置示例")
    print("="*70)
    
    # 所有有編號的行及其排列
    has_perm = {
        'A': {'id': 5447, 'total': 8731, 'solution': SOLUTION['A']},
        'B': {'id': 824, 'total': 902, 'solution': SOLUTION['B']},
        'E': {'id': 287832, 'total': 633271, 'solution': SOLUTION['E']},
        'F': {'id': 227, 'total': 359, 'solution': SOLUTION['F']},
        'G': {'id': 2113, 'total': 2356, 'solution': SOLUTION['G']},
        'H': {'id': 2588, 'total': 4782, 'solution': SOLUTION['H']},
        'J': {'id': 25793, 'total': 28984, 'solution': SOLUTION['J']},
        'K': {'id': 1150, 'total': 2972, 'solution': SOLUTION['K']},
        'L': {'id': 583, 'total': 620, 'solution': SOLUTION['L']},
        'M': {'id': 169, 'total': 484, 'solution': SOLUTION['M']},
        'N': {'id': 257, 'total': 10668, 'solution': SOLUTION['N']},
        'O': {'id': 3011, 'total': 5990, 'solution': SOLUTION['O']},
        'P': {'id': 1294, 'total': 1809, 'solution': SOLUTION['P']},
    }
    
    print("\n【固定 A 行 (第1行) 的示例】")
    print(f"  排列編號: A5447 (共 8,731 種)")
    print(f"  固定行值: {SOLUTION['A'][:4]} | {SOLUTION['A'][4:8]} | {SOLUTION['A'][8:12]} | {SOLUTION['A'][12:16]}")
    print(f"  搜索空間: 其餘 15 行 × 各自行符闔排列總數")
    print(f"  理論最大解數: 902 × 633271 × 359 × ... (需要驗證聯動約束)")
    
    print("\n【固定 A+B+M 行的示例】")
    print(f"  A5447: {SOLUTION['A'][:4]} | {SOLUTION['A'][4:8]} | {SOLUTION['A'][8:12]} | {SOLUTION['A'][12:16]}")
    print(f"  B824:  {SOLUTION['B'][:4]} | {SOLUTION['B'][4:8]} | {SOLUTION['B'][8:12]} | {SOLUTION['B'][12:16]}")
    print(f"  M169:  {SOLUTION['M'][:4]} | {SOLUTION['M'][4:8]} | {SOLUTION['M'][8:12]} | {SOLUTION['M'][12:16]}")
    print(f"  搜索空間: 其餘 13 行")
    
    print("\n【關鍵驗證】")
    print("  1. 檢查固定行之間是否存在約束衝突")
    print("  2. 檢查固定行與未固定行是否存在列衝突")
    print("  3. 檢查是否存在宮衝突")
    print("  4. 如果無衝突，搜索 S_fummel 解集")

def main():
    analyze_row_classification()
    analyze_fixed_row_scenarios()
    theoretical_analysis()
    generate_fixed_rows_config()
    
    print("\n" + "="*70)
    print("結論：這是「另外一廻事」")
    print("="*70)
    print("""
【用戶問題解答】

「設若在無約束衝突的情況下固定包含第1行 第2行 或第13行等
如果能夠得出全部解集 那是不是又是另外一廻事」

【答案】是的，這是「另外一廻事」！

【理由】

1. 之前討論的情況：
   - box_size4.txt 初始解盤：C、D、I 行無符闔排列編號
   - 可能 S_fummel 中 C、D、I 行無有效排列 → 「空解」

2. 新情況（用戶提出的）：
   - 固定有編號的行（如 A、B、M、E...）
   - 這些行的排列在符闔排列集合中 ✓
   - 如果無約束衝突，可能得到 S_fummel 的非空解集
   - 這確實是「另外一廻事」！

3. 關鍵區別：
   ┌─────────────────┬─────────────────────────────────────────┐
   │ 情況            │ 解空間狀態                                │
   ├─────────────────┼─────────────────────────────────────────┤
   │ 固定 C/D/I 行   │ S_fummel 可能為空 (空解)                  │
   │ 固定 A/B/M 行   │ S_fummel 可能有解 (實解) ← 新情況         │
   └─────────────────┴─────────────────────────────────────────┘

【驗證步驟】
1. 固定 A5447 (第1行)
2. 固定 B824 (第2行)
3. 固定 M169 (第13行)
4. 檢查約束衝突
5. 如果無衝突，搜索 S_fummel 完整解集
""")

if __name__ == '__main__':
    main()
