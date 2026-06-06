"""符闔排列生成規則 V3.0 - 正確構造（最終版）"""
import json
import random
from typing import List

GRID_SIZE = 16
BOX_SIZE = 4

def check_sudoku(square: List[List[int]]) -> dict:
    """驗證完整的 Sudoku 約束"""
    errors = []
    
    # 行
    for i, row in enumerate(square):
        if len(set(row)) != 16:
            errors.append(f"行{i}重複")
    
    # 列
    for c in range(16):
        col = [square[r][c] for r in range(16)]
        if len(set(col)) != 16:
            errors.append(f"列{c}重複")
    
    # 宮
    for br in range(4):
        for bc in range(4):
            box = []
            for r in range(br*4, (br+1)*4):
                for c in range(bc*4, (bc+1)*4):
                    box.append(square[r][c])
            if len(set(box)) != 16:
                errors.append(f"宮({br},{bc})重複")
    
    return {"valid": len(errors) == 0, "errors": errors}


def construct_correct_sudoku():
    """
    正確的 16×16 Sudoku 構造
    
    方法：使用 4×4 的塊結構，每個塊內按特定模式填充
    
    設計思路：
    - 將 16×16 分為 4 個 band（每 band 4 行）
    - 每個 band 內有 4 個 stack（每 stack 4 列）
    - 每個 band-stack 交點是一個 4×4 子方格
    
    關鍵公式：
    令 band_i = i // 4 (0-3), row_i = i % 4 (0-3)
    令 stack_j = j // 4 (0-3), col_j = j % 4 (0-3)
    
    val(i, j) = 4 * (band_i * 4 + stack_j) + (row_i * 4 + col_j)  這樣會超出 16
    
    正確公式：
    val(i,j) = 4 * ((stack_j + band_i) % 4) + ((col_j + row_i) % 4) + 1
    
    驗證：
    - 行 i: 固定 i，j 變化 → stack_j 和 col_j 變化 → val 變化
    - 列 j: 固定 j，i 變化 → band_i 和 row_i 變化 → val 變化
    - 宮: band_i 和 stack_j 固定，row_i 和 col_j 變化 → val 變化
    """
    
    # 先用簡單方法：構造一個已知的正確 Sudoku
    # 基於 cyclic Latin square 的思想
    
    # 基礎模式：每行的排列是前一行的移位，但移位模式要特殊設計
    
    # 行0: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    # 行1: [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 1, 2, 3, 4]  (移位4)
    # 行2: [9, 10, 11, 12, 13, 14, 15, 16, 1, 2, 3, 4, 5, 6, 7, 8]  (移位8)
    # 行3: [13, 14, 15, 16, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  (移位12)
    # 行4: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 1]  (移位1)
    # ...
    
    # 更系統的构造：使用 "shift by (i*4 + floor(i/4))" 模式
    # 行 i 的移位量 = (4*(i%4) + i//4) mod 16
    
    shifts = []
    for i in range(16):
        shift = (4 * (i % 4) + i // 4) % 16
        shifts.append(shift)
    
    print(f"移位序列: {shifts}")
    
    square = []
    base_row = list(range(1, 17))
    
    for i, shift in enumerate(shifts):
        row = [(base_row[(j + shift) % 16]) for j in range(16)]
        square.append(row)
    
    print("\n構造結果:")
    for i, row in enumerate(square):
        print(f"  行{i}: {row}")
    
    result = check_sudoku(square)
    print(f"\n驗證: {'✅ 完美 Sudoku' if result['valid'] else '❌ 失敗'}")
    if not result['valid']:
        for err in result['errors'][:10]:
            print(f"    {err}")
    
    return square, result['valid']


def construct_sudoku_method2():
    """
    方法2：基於 GF(16) 的構造
    
    GF(16) 的元素可以表示為 {0, 1, α, α², ..., α¹⁴}
    val(i, j) = GF_mult(i, j) 的映射
    
    簡化：使用 XOR 運算（等同於 GF(2^4) 的加法）
    val(i,j) = (i ^ j) + 1  -- 這不是 Sudoku！
    
    正確方法：
    val(i,j) = 4*(i//4) + (j//4) + 4*(i%4)*4 + (j%4) 這樣也不对
    
    最終正確方法：
    val(i,j) = 4 * ((i % 4) * 4 + (j // 4)) + ((i // 4) * 4 + (j % 4)) 這樣會超出範圍
    
    讓我用另一個已知公式：
    val(i,j) = ((i % 4) + 4 * ((i // 4) + (j // 4)) % 4) * 4 + ((j % 4) + 4 * ((i % 4) + (j % 4)) % 4)
    """
    
    # 使用已知正確的公式
    # val(i,j) = 4 * L1(i,j) + L2(i,j) + 1
    # 其中 L1 和 L2 是兩個正交的 4x4 Latin squares
    
    # L1: L1(i,j) = (i % 4 + j % 4) % 4  (簡單的 4x4 cyclic LS)
    # L2: L2(i,j) = ((i // 4) * 4 + (j // 4)) % 4
    
    # 但這樣 val 範圍是 0-15，需要 +1 變為 1-16
    
    square = []
    for i in range(16):
        row = []
        for j in range(16):
            # 分解
            i4 = i % 4      # 0-3 在band內行號
            iB = i // 4     # 0-3 band編號
            j4 = j % 4      # 0-3 在stack內列號
            jS = j // 4     # 0-3 stack編號
            
            # 公式
            val = 4 * ((i4 + jS) % 4) + ((j4 + iB) % 4) + 1
            row.append(val)
        square.append(row)
    
    print("\n方法2構造結果:")
    for i, row in enumerate(square[:4]):
        print(f"  行{i}: {row}")
    print("  ...")
    
    result = check_sudoku(square)
    print(f"驗證: {'✅ 完美 Sudoku' if result['valid'] else '❌ 失敗'}")
    
    return square, result['valid']


def construct_sudoku_method3():
    """
    方法3：直接構造 - 已知正確的公式
    
    val(i, j) = 4 * ((i % 4) + 4 * (j // 4)) + ((i // 4) + (j % 4)) % 4 + 1
    
    等等，讓我重新推導：
    
    目標：val(i,j) ∈ {1,...,16}
    
    正確公式（來自數學文獻）：
    val(i,j) = 1 + 4 * ((i + 4*⌊i/4⌋ + j) mod 4) + ((i + j) mod 4)
    
    讓我用另一種方法：先構造 4 個 4x4 的 Latin squares，然後組合
    """
    
    # 直接構造 - 逐行生成並驗證
    base = list(range(16))
    
    # 行排列模式：每行是 base 的移位
    # 但移位模式要確保宮約束
    
    # 正確的移位序列（每行相鄰兩行移位不同，且同一宮內值互異）
    # 來自已知 Sudoku 模式
    
    shifts = [
        0,  4,  8, 12,   # Band 0: 移位 0,4,8,12
        1,  5,  9, 13,   # Band 1: 移位 1,5,9,13
        2,  6, 10, 14,   # Band 2: 移位 2,6,10,14
        3,  7, 11, 15,   # Band 3: 移位 3,7,11,15
    ]
    
    print(f"移位序列: {shifts}")
    
    square = []
    for i, shift in enumerate(shifts):
        row = [(base[(j + shift) % 16] + 1) for j in range(16)]
        square.append(row)
    
    print("\n方法3構造結果:")
    for i, row in enumerate(square[:4]):
        print(f"  行{i}: {row}")
    
    result = check_sudoku(square)
    print(f"驗證: {'✅ 完美 Sudoku' if result['valid'] else '❌ 失敗'}")
    
    return square, result['valid']


def construct_sudoku_method4():
    """
    方法4：系統構造
    
    核心公式：
    val(i,j) = 4 * ((i % 4) + (j // 4)) % 4 + ((j % 4) + 4 * (i // 4)) % 4 + 1
    
    推導：
    - 第一部分: 4 * ((i % 4) + (j // 4)) % 4 給出 0, 4, 8, 12 的基數
    - 第二部分: ((j % 4) + 4 * (i // 4)) % 4 給出 0, 1, 2, 3 的偏移
    - +1 轉為 1-16
    """
    
    square = []
    for i in range(16):
        row = []
        for j in range(16):
            i4 = i % 4
            iB = i // 4
            j4 = j % 4
            jS = j // 4
            
            val = 4 * ((i4 + jS) % 4) + ((j4 + 4 * iB) % 4) + 1
            row.append(val)
        square.append(row)
    
    print("\n方法4構造結果:")
    for i, row in enumerate(square):
        print(f"  行{i}: {row}")
    
    result = check_sudoku(square)
    print(f"驗證: {'✅ 完美 Sudoku' if result['valid'] else '❌ 失敗'}")
    
    return square, result['valid']


if __name__ == "__main__":
    print("=" * 60)
    print("符闔排列 V3.0 - 正確 Sudoku 構造")
    print("=" * 60)
    
    methods = [
        ("移位模式", construct_correct_sudoku),
        ("正交 LS", construct_sudoku_method2),
        ("系統移位", construct_sudoku_method3),
        ("公式構造", construct_sudoku_method4),
    ]
    
    for name, func in methods:
        print(f"\n{'-' * 50}")
        print(f"【{name}】")
        print(f"{'-' * 50}")
        square, valid = func()
        if valid:
            print(f"\n✅ 找到正確的 Sudoku 構造！")
            break
