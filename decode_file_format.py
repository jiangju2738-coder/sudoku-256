#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 超級大數獨 box_size4.txt 編碼規則完整驗證
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# 行號映射：A-P → 第1-16行
ROW_MAP = {chr(64+i): i for i in range(1, 17)}

# 列號映射：D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T → 第1-16列
# 注意：文件中列號列表為 D,E,F,G, H,I,J,K, L,M,N,O, P,Q,R,T (共16個，缺S，T=16)
# 但用戶說"列D-T"，實際文件中列號是：D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T
# 讓我們從文件第23行確認
COL_ORDER_FILE = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','T']  # 文件顯示16個
COL_ORDER_USER = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T']  # 用戶說D-T

# 按文件實際內容：D=1, E=2, ..., R=15, T=16（沒有S列）
COL_MAP_FILE = {c: i+1 for i, c in enumerate(COL_ORDER_FILE)}

# 從文件中提取的已知數位置（第25-40行）
ANCHOR_DATA = {
    1: ['BR', 'DJ', 'KD', 'LS', 'MM', 'OE', 'PP'],
    2: ['BP', 'CI', 'GL', 'IG', 'KK', 'ON', 'PF'],
    3: ['AF', 'BH', 'FK', 'GQ', 'IS', 'KM', 'MO', 'NR'],
    4: ['BO', 'DE', 'EP', 'FJ', 'GF', 'LG'],
    5: ['AK', 'BN', 'EM', 'HI', 'JE', 'KH', 'LO', 'ML', 'OQ', 'PJ'],
    6: ['BL', 'GG', 'HO', 'KF', 'MQ', 'NI'],
    7: ['DH', 'IO', 'JR', 'MS'],
    8: ['AS', 'CK', 'FE', 'JP', 'OO'],  # AS中S需確認
    9: ['BJ', 'FM', 'HK', 'KP', 'NF', 'OH'],
    10: ['PR'],
    11: ['DO', 'II'],
    12: ['AI', 'BE', 'DQ', 'FS', 'GJ', 'LN', 'MH'],
    13: ['DG', 'EH', 'FQ', 'HE', 'ID', 'NL'],
    14: ['AO', 'CF', 'GD', 'HN', 'IL', 'LJ', 'PM'],
    15: ['FH', 'IQ', 'MD', 'NO', 'OK', 'PS'],
    16: ['AQ', 'HR', 'JN', 'LI'],
}

# 初始解盤排列編號
SOLUTION_PERM_IDS = {
    'A': 5447, 'B': 824, 'E': 287832, 'F': 227,
    'G': 2113, 'H': 2588, 'J': 25793, 'K': 1150,
    'L': 583, 'M': 169, 'N': 257, 'O': 3011, 'P': 1294
}

# 每行符闔排列總數
PERM_COUNTS = {
    'A': 8731, 'B': 902, 'C': 407669, 'D': 1980,
    'E': 633271, 'F': 359, 'G': 2356, 'H': 4782,
    'I': 164, 'J': 28984, 'K': 2972, 'L': 620,
    'M': 484, 'N': 10668, 'O': 5990, 'P': 1809
}

def verify_encoding_rules():
    """驗證編碼規則"""
    print("="*70)
    print("編碼規則驗證")
    print("="*70)
    
    print("\n【1. 行號映射】")
    print("  A-P 對應 第1-16行")
    for letter, idx in ROW_MAP.items():
        print(f"    {letter} → 第{idx}行")
    
    print("\n【2. 列號映射】")
    print("  文件第23行列號列表：D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,T")
    print("  共16列，對應第1-16列")
    for letter, idx in COL_MAP_FILE.items():
        print(f"    {letter} → 第{idx}列")
    
    print("\n【3. 符闔排列標記】")
    print("  A5447 → 第1行(A)的第5447種符闔排列")
    print("  B824  → 第2行(B)的第824種符闔排列")
    print(f"  A行總數: 8731種，B行總數: 902種")
    print(f"  驗證: 5447 ≤ 8731 ✓ | 824 ≤ 902 ✓")
    
    print("\n【4. 已知數標記】")
    print("  BR → 行B(第2行) 列R(第15列) = 值1")
    print("  DJ → 行D(第4行) 列J(第7列) = 值1")
    print("  依此類推...")

def extract_all_anchors():
    """提取所有錨點並驗證"""
    print("\n" + "="*70)
    print("錨點提取與驗證")
    print("="*70)
    
    anchors = []
    conflicts = []
    
    # 統計每行錨點數
    row_counts = {chr(64+i): 0 for i in range(1, 17)}
    
    for value, positions in ANCHOR_DATA.items():
        for pos in positions:
            row_letter = pos[0]
            col_letter = pos[1]
            
            # 處理S列問題 - 文件中沒有S列，S可能是T的變體或錯誤
            if col_letter == 'S':
                col_letter = 'T'  # 假設S對應T(第16列)
            
            row_idx = ROW_MAP.get(row_letter)
            col_idx = COL_MAP_FILE.get(col_letter)
            
            if row_idx and col_idx:
                anchors.append({
                    'value': value,
                    'row': row_idx,
                    'col': col_idx,
                    'row_letter': row_letter,
                    'col_letter': col_letter,
                    'code': pos
                })
                row_counts[row_letter] += 1
            else:
                print(f"  ⚠️ 無法解析: {pos} (row={row_letter}, col={col_letter})")
    
    print(f"\n共提取 {len(anchors)} 個錨點")
    
    print("\n【每行錨點分佈】")
    for row_letter in 'ABCDEFGHIJKLMNOP':
        count = row_counts.get(row_letter, 0)
        print(f"  行{row_letter}(第{ROW_MAP[row_letter]}行): {count}個")
    
    # 檢查列衝突
    from collections import defaultdict, Counter
    col_values = defaultdict(list)
    for a in anchors:
        col_values[a['col']].append((a['row'], a['value']))
    
    for col, pairs in col_values.items():
        val_counts = Counter(v for _, v in pairs)
        for val, count in val_counts.items():
            if count > 1:
                rows = [r for r, v in pairs if v == val]
                conflicts.append({'col': col, 'value': val, 'rows': rows})
    
    if conflicts:
        print(f"\n❌ 發現 {len(conflicts)} 個列衝突:")
        for c in conflicts:
            print(f"  列{c['col']}: 值{c['value']} 在行{c['rows']}")
    else:
        print("\n✅ 無列衝突")

def verify_solution_consistency():
    """驗證初始解盤與已知數的一致性"""
    print("\n" + "="*70)
    print("初始解盤一致性驗證")
    print("="*70)
    
    # 初始解盤數據（從文件第43-61行）
    solution = {
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
    
    mismatches = []
    
    for value, positions in ANCHOR_DATA.items():
        for pos in positions:
            row_letter = pos[0]
            col_letter = pos[1]
            
            if col_letter == 'S':
                col_letter = 'T'
            
            row_idx = ROW_MAP.get(row_letter)
            col_idx = COL_MAP_FILE.get(col_letter)
            
            if row_idx and col_idx:
                expected_val = solution[row_letter][col_idx - 1]
                if expected_val != value:
                    mismatches.append({
                        'code': pos,
                        'expected': expected_val,
                        'given': value,
                        'row': row_idx,
                        'col': col_idx
                    })
    
    total_anchors_verified = sum(len(positions) for positions in ANCHOR_DATA.values())
    if mismatches:
        print(f"\n❌ 發現 {len(mismatches)} 個不一致:")
        for m in mismatches:
            print(f"  {m['code']}: 解盤值={m['expected']}, 已知數={m['given']} (行{m['row']}列{m['col']})")
    else:
        print(f"\n✅ 初始解盤與{total_anchors_verified}個已知數完全一致")

def main():
    verify_encoding_rules()
    extract_all_anchors()
    verify_solution_consistency()
    
    print("\n" + "="*70)
    print("編碼規則總結")
    print("="*70)
    print("""
┌──────────────────────────────────────────────────────────────────────┐
│                    超級大數獨 box_size4 編碼規則                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  【行號】A-P 對應第1-16行                                            │
│    A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8                          │
│    I=9, J=10, K=11, L=12, M=13, N=14, O=15, P=16                   │
│                                                                      │
│  【列號】D,T 對應第1-16列 (共16列)                                   │
│    D=1, E=2, F=3, G=4, H=5, I=6, J=7, K=8                          │
│    L=9, M=10, N=11, O=12, P=13, Q=14, R=15, T=16                   │
│    (注意：文件中沒有S列，S可能指代T)                                  │
│                                                                      │
│  【符闔排列】A5447 表示第A行的第5447種排列                           │
│    A5447 = [7,15,3,9, 11,12,6,5, 10,2,1,14, 13,16,4,8]             │
│    B824  = [16,12,10,8, 3,15,9,14, 6,13,5,4, 2,7,1,11]            │
│    ...                                                               │
│                                                                      │
│  【已知數】BR 表示行B列R，即第2行第15列                              │
│    BR=1  → 行2列15的值為1                                           │
│    DJ=1  → 行4列7的值為1                                            │
│    ...                                                               │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
    """)

if __name__ == '__main__':
    main()
