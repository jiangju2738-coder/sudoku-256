#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 超級大數獨 box_size4 初始解盤驗證
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# 已知題盤（從文件提取）
KNOWN_PUZZLE = {
    'A': [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8],
    'B': [0,12,0,0, 3,0,9,0, 6,0,5,4, 2,0,1,0],
    'C': [0,0,14,0, 0,2,0,8, 0,0,0,0, 0,0,0,0],
    'D': [0,4,0,13, 7,0,1,0, 0,0,0,11, 0,12,0,0],
    'E': [0,0,0,0, 13,0,0,0, 0,5,0,0, 4,0,0,0],
    'F': [0,8,0,0, 15,0,4,3, 0,9,0,0, 0,13,0,12],
    'G': [14,0,4,6, 0,0,12,0, 2,0,0,0, 0,3,0,0],
    'H': [0,13,0,0, 0,5,0,9, 0,0,14,6, 0,0,16,0],
    'I': [13,0,0,2, 0,11,0,0, 14,0,0,7, 0,15,0,3],
    'J': [0,5,0,0, 0,0,0,0, 0,0,16,0, 8,0,7,0],
    'K': [1,0,6,0, 5,0,0,2, 0,3,0,0, 9,0,0,0],
    'L': [0,0,0,4, 0,16,14,0, 0,0,12,5, 0,0,0,1],
    'M': [15,0,0,0, 12,0,0,0, 5,1,0,3, 0,6,0,7],
    'N': [0,0,9,0, 0,6,0,0, 13,0,0,15, 0,0,3,0],
    'O': [0,1,0,0, 9,0,0,15, 0,0,2,8, 0,5,0,0],
    'P': [0,0,2,0, 0,0,5,0, 0,14,0,0, 1,0,10,15],
}

# 初始解盤（從文件第43-61行提取）
SOLUTION = {
    'A': [7,15,3,9, 11,12,6,5, 10,2,1,14, 13,16,4,8],
    'B824': [16,12,10,8, 3,15,9,14, 6,13,5,4, 2,7,1,11],
    'C': [11,6,14,1, 4,2,13,8, 7,12,3,16, 10,9,15,5],
    'D': [2,4,5,13, 7,10,1,16, 15,8,9,11, 3,12,14,6],
    'E287832': [9,2,7,10, 13,1,16,6, 3,5,15,12, 4,11,8,14],
    'F227': [5,8,1,11, 15,14,4,3, 16,9,7,10, 6,13,2,12],
    'G2113': [14,16,4,6, 8,7,12,10, 2,11,13,1, 15,3,5,9],
    'H2588': [3,13,15,12, 2,5,11,9, 8,4,14,6, 7,1,16,10],
    'I': [13,9,16,2, 1,11,8,12, 14,10,4,7, 5,15,6,3],
    'J25793': [12,5,11,15, 10,9,3,13, 1,6,16,2, 8,14,7,4],
    'K1150': [1,14,6,7, 5,4,15,2, 11,3,8,13, 9,10,12,16],
    'L583': [10,3,8,4, 6,16,14,7, 9,15,12,5, 11,2,13,1],
    'M169': [15,11,13,16, 12,8,2,4, 5,1,10,3, 14,6,9,7],
    'N257': [4,10,9,5, 14,6,7,1, 13,16,11,15, 12,8,3,2],
    'O3011': [6,1,12,14, 9,3,10,15, 4,7,2,8, 16,5,11,13],
    'P1294': [8,7,2,3, 16,13,5,11, 12,14,6,9, 1,4,10,15],
}

def verify_puzzle_solution():
    """驗證已知題盤與初始解盤的一致性"""
    print("="*70)
    print("驗證已知題盤與初始解盤一致性")
    print("="*70)
    
    conflicts = []
    for row_letter, known_row in KNOWN_PUZZLE.items():
        sol_row_key = row_letter if row_letter in SOLUTION else f"{row_letter}..."
        sol_row = None
        for k, v in SOLUTION.items():
            if k.startswith(row_letter):
                sol_row = v
                break
        
        if sol_row is None:
            print(f"⚠️ 行{row_letter}: 解盤中未找到對應行")
            continue
            
        for col_idx, val in enumerate(known_row):
            if val != 0:
                sol_val = sol_row[col_idx]
                if val != sol_val:
                    conflicts.append({
                        'row': row_letter,
                        'col': col_idx + 1,
                        'known': val,
                        'solution': sol_val,
                        'label': f"{row_letter}{col_idx + 1}"
                    })
    
    if conflicts:
        print(f"\n❌ 發現 {len(conflicts)} 個衝突:")
        for c in conflicts:
            print(f"  {c['label']}: 已知={c['known']}, 解盤={c['solution']}")
    else:
        print(f"\n✅ 已知題盤與初始解盤完全一致")

def verify_all_constraints():
    """驗證完整解盤的所有限束"""
    print("\n" + "="*70)
    print("驗證完整解盤約束")
    print("="*70)
    
    # 行约束
    print("\n【行约束验证】")
    row_violations = 0
    for row_letter, row_data in SOLUTION.items():
        if len(set(row_data)) != 16:
            row_violations += 1
            print(f"  ❌ 行{row_letter}: 存在重複值")
    if row_violations == 0:
        print(f"  ✅ 16 行均滿足 AllDifferent")
    
    # 列约束
    print("\n【列约束验证】")
    col_violations = 0
    for col_idx in range(16):
        col_values = [row_data[col_idx] for row_data in SOLUTION.values()]
        if len(set(col_values)) != 16:
            col_violations += 1
            dup_values = [v for v in set(col_values) if col_values.count(v) > 1]
            print(f"  ❌ 列{col_idx+1}: 重複值 {dup_values}")
    if col_violations == 0:
        print(f"  ✅ 16 列均滿足 AllDifferent")
    
    # 宫约束 (4x4)
    print("\n【宫约束验证 (4x4)】")
    box_violations = 0
    for box_r in range(4):
        for box_c in range(4):
            box_values = []
            for dr in range(4):
                for dc in range(4):
                    row_letter = chr(65 + box_r * 4 + dr)
                    sol_row = None
                    for k, v in SOLUTION.items():
                        if k.startswith(row_letter):
                            sol_row = v
                            break
                    if sol_row:
                        box_values.append(sol_row[box_c * 4 + dc])
            
            if len(set(box_values)) != 16:
                box_violations += 1
                dup_values = [v for v in set(box_values) if box_values.count(v) > 1]
                print(f"  ❌ 宮[{box_r+1},{box_c+1}]: 重複值 {dup_values}")
    if box_violations == 0:
        print(f"  ✅ 16 個宫均滿足 AllDifferent")
    
    print(f"\n總結: 行{16-row_violations}/{16} ✅ | 列{16-col_violations}/{16} ✅ | 宫{16-box_violations}/{16} ✅")

def highlight_b824_c():
    """特別展示用戶引用的行B824和行C"""
    print("\n" + "="*70)
    print("用戶引用的關鍵行")
    print("="*70)
    
    print("\n【行B824 (第2行)】")
    b_row = SOLUTION['B824']
    known_b = KNOWN_PUZZLE['B']
    print(f"  標記: B824 (可能是某種編碼識別)")
    print(f"  完整行: {b_row[:4]} | {b_row[4:8]} | {b_row[8:12]} | {b_row[12:16]}")
    print(f"  已知位: ", end="")
    for i, v in enumerate(known_b):
        if v != 0:
            print(f"[{i+1}:{v}] ", end="")
    print()
    
    # 驗證B行已知位
    print("  驗證:")
    for i, (k, s) in enumerate(zip(known_b, b_row)):
        if k != 0:
            status = "✓" if k == s else "✗"
            print(f"    列{i+1}: 已知={k}, 解={s} {status}")
    
    print("\n【行C (第3行)】")
    c_row = SOLUTION['C']
    known_c = KNOWN_PUZZLE['C']
    print(f"  完整行: {c_row[:4]} | {c_row[4:8]} | {c_row[8:12]} | {c_row[12:16]}")
    print(f"  已知位: ", end="")
    for i, v in enumerate(known_c):
        if v != 0:
            print(f"[{i+1}:{v}] ", end="")
    print()
    
    # 驗證C行已知位
    print("  驗證:")
    for i, (k, s) in enumerate(zip(known_c, c_row)):
        if k != 0:
            status = "✓" if k == s else "✗"
            print(f"    列{i+1}: 已知={k}, 解={s} {status}")

def main():
    verify_puzzle_solution()
    verify_all_constraints()
    highlight_b824_c()

if __name__ == '__main__':
    main()
