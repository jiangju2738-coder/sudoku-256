#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試正確的移位模式 - 找到滿足三約束的構造公式
"""

def validate_grid(grid, box_size=4):
    """驗證16x16網格的三約束"""
    n = 16
    
    # 行約束
    for row in grid:
        if len(set(row)) != n:
            return False, "行約束違反"
    
    # 列約束
    for col in range(n):
        column = [grid[row][col] for row in range(n)]
        if len(set(column)) != n:
            return False, f"列{col}約束違反"
    
    # 宮約束
    for band in range(4):
        for stack in range(4):
            box_vals = []
            for i in range(box_size):
                for j in range(box_size):
                    box_vals.append(grid[band*box_size+i][stack*box_size+j])
            if len(set(box_vals)) != n:
                return False, f"宮(行{band*4+1}-{band*4+4},列{stack*4+1}-{stack*4+4})約束違反"
    
    return True, "所有約束滿足"


def test_shift_pattern(shifts):
    """測試一個移位模式"""
    base_row = list(range(1, 17))
    grid = []
    for shift in shifts:
        row = [base_row[(j + shift) % 16] for j in range(16)]
        grid.append(row)
    
    valid, msg = validate_grid(grid)
    return valid, msg, grid


# 測試不同的移位模式
print("=" * 80)
print("16×16 Sudoku 移位模式測試")
print("=" * 80)

# 已知的正確模式
CORRECT_SHIFTS = [0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15]
print(f"\n✅ 已知正確模式: {CORRECT_SHIFTS}")
valid, msg, grid = test_shift_pattern(CORRECT_SHIFTS)
print(f"   驗證結果: {msg}")

# 理論分析：為什麼這個模式有效？
print("\n🔍 模式理論分析:")
print("   CORRECT_SHIFTS = [0,4,8,12, 1,5,9,13, 2,6,10,14, 3,7,11,15]")
print("   ")
print("   Band 0 (行0-3):   移位 0,4,8,12 → 列0-3 的值分別偏移0,4,8,12")
print("   Band 1 (行4-7):   移位 1,5,9,13 → 列0-3 的值分別偏移1,5,9,13")
print("   Band 2 (行8-11):  移位 2,6,10,14 → 列0-3 的值分別偏移2,6,10,14")
print("   Band 3 (行12-15): 移位 3,7,11,15 → 列0-3 的值分別偏移3,7,11,15")
print("   ")
print("   對於列 j (0≤j≤15):")
print("   - 每列在所有16行中出現的值是: {(j+s) mod 16 | s ∈ {0,1,...,15}}")
print("   - 由於 s 取遍 0-15，(j+s) mod 16 也取遍 0-15")
print("   - 因此每列包含 1-16 各一次 ✅")
print("   ")
print("   對於宮 (band, stack):")
print("   - 宮內值 = {(j + CORRECT_SHIFTS[band*4+i]) mod 16 | 0≤i,j≤3}")
print("   - 列偏移 j ∈ {0,1,2,3}")
print("   - 行偏移 CORRECT_SHIFTS[band*4+i] ∈ {4*band, 4*band+1, 4*band+2, 4*band+3}")
print("   - 總偏移 = j + 4*band + k，其中 k∈{0,1,2,3}")
print("   - 當 band 固定時，(j+k) 取遍 0-6，但需要 16 個不同值")
print("   - 實際上: 偏移 = j + (4*band + i) = j + i + 4*band")
print("   - 對於 band=0: 偏移 = {0,1,2,3, 4,5,6,7, 8,9,10,11, 12,13,14,15} ✅")
print("   - 對於 band=1: 偏移 = {1,2,3,4, 5,6,7,8, 9,10,11,12, 13,14,15,0} ✅")

# 測試錯誤的模式
print("\n❌ 測試錯誤的移位模式:")
wrong_patterns = [
    list(range(16)),  # [0,1,2,...,15]
    [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
    [0,2,4,6,8,10,12,14,1,3,5,7,9,11,13,15],
]

for i, pattern in enumerate(wrong_patterns):
    valid, msg, _ = test_shift_pattern(pattern)
    print(f"   模式 {i+1}: {pattern[:8]}... → {msg}")

# 輸出正確的 Sudoku
print("\n" + "=" * 80)
print("✅ 正確 16×16 Sudoku (使用 CORRECT_SHIFTS)")
print("=" * 80)
valid, msg, grid = test_shift_pattern(CORRECT_SHIFTS)

print("\n網格:")
for i, row in enumerate(grid):
    print(f"   行{i+1:2d}: {row}")

print(f"\n驗證: {msg}")
