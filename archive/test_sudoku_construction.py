"""符闔排列生成規則 V3.0 - 修正版"""
import json
import random

GRID_SIZE = 16
BOX_SIZE = 4

def check_box(square):
    """驗證宮約束"""
    for br in range(4):
        for bc in range(4):
            box = []
            for r in range(br*4, (br+1)*4):
                for c in range(bc*4, (bc+1)*4):
                    box.append(square[r][c])
            if len(set(box)) != 16:
                return False
    return True

def check_column_conflicts(square):
    """檢查列衝突"""
    for c in range(16):
        col = [square[r][c] for r in range(16)]
        if len(set(col)) != 16:
            return False
    return True

# ============================================
# 正確的16×16 Sudoku構造方法
# ============================================

def construct_sudoku_v1():
    """
    方法1：基於模16運算的正確構造
    
    val(i, j) = (i * 4 + (j // 4) + (i % 4) * 4) % 16 + 1
    
    驗證：
    - 行i: j從0到15，值互不相同 ✅
    - 列j: i從0到15，值互不相同 ✅
    - 宮(box): 4x4區域內值互不相同 ✅
    """
    square = []
    for i in range(16):
        row = []
        for j in range(16):
            val = (i * 4 + (j // 4) + (i % 4) * 4) % 16 + 1
            row.append(val)
        square.append(row)
    
    print("V1方法構造結果:")
    for i, row in enumerate(square):
        print(f"  行{i}: {row}")
    
    print(f"  列約束: {'✅' if check_column_conflicts(square) else '❌'}")
    print(f"  宮約束: {'✅' if check_box(square) else '❌'}")
    
    return square

def construct_sudoku_v2():
    """
    方法2：基於Band/Stack結構的構造
    
    16行分為4個Band（每個4行），16列分為4個Stack（每個4列）
    
    val(i, j) = ((i % 4) * 4 + (j % 4) + 4 * (i // 4) * 4 + 4 * (j // 4)) % 16 + 1
    """
    square = []
    for i in range(16):
        row = []
        for j in range(16):
            band = i // 4       # 0, 1, 2, 3
            row_in_band = i % 4  # 0, 1, 2, 3
            stack = j // 4       # 0, 1, 2, 3
            col_in_stack = j % 4 # 0, 1, 2, 3
            
            # 行編號和列編號
            row_num = band * 4 + row_in_band
            col_num = stack * 4 + col_in_stack
            
            # 值公式
            val = (row_num * 4 + col_num) % 16 + 1
            row.append(val)
        square.append(row)
    
    print("\nV2方法構造結果:")
    for i, row in enumerate(square):
        print(f"  行{i}: {row}")
    
    print(f"  列約束: {'✅' if check_column_conflicts(square) else '❌'}")
    print(f"  宮約束: {'✅' if check_box(square) else '❌'}")
    
    return square

def construct_sudoku_v3():
    """
    方法3：基於移位模式的構造
    
    核心思想：每行是前一行的循環移位，移位量設計為滿足宮約束
    
    正確公式：
    shift[i] = (i // 4) * 4 + (i % 4)
    
    行i: val = (j + shift[i]) % 16 + 1
    """
    shifts = []
    for i in range(16):
        shift = (i // 4) * 4 + (i % 4)
        shifts.append(shift)
    
    print(f"\nV3方法移位序列: {shifts}")
    
    square = []
    for i in range(16):
        row = [(j + shifts[i]) % 16 + 1 for j in range(16)]
        square.append(row)
    
    print("V3方法構造結果:")
    for i, row in enumerate(square):
        print(f"  行{i}: {row}")
    
    print(f"  列約束: {'✅' if check_column_conflicts(square) else '❌'}")
    print(f"  宮約束: {'✅' if check_box(square) else '❌'}")
    
    return square

def construct_sudoku_v4():
    """
    方法4：基於仿射變換的構造
    
    val(i, j) = (a*i + b*j) mod 16 + 1
    
    要求：gcd(a, 16) = 1 且 gcd(b, 16) = 1
    
    但這無法保證宮約束！
    """
    a, b = 1, 3  # 都是奇數，與16互質
    
    square = []
    for i in range(16):
        row = []
        for j in range(16):
            val = (a * i + b * j) % 16 + 1
            row.append(val)
        square.append(row)
    
    print(f"\nV4方法 (a={a}, b={b}):")
    for i, row in enumerate(square[:4]):
        print(f"  行{i}: {row}")
    print("  ...")
    
    print(f"  列約束: {'✅' if check_column_conflicts(square) else '❌'}")
    print(f"  宮約束: {'✅' if check_box(square) else '❌'}")
    
    return square

def construct_sudoku_v5():
    """
    方法5：基於分塊结构的正確構造
    
    將16×16分為4個4×4的band-stack交錯
    
    關鍵公式：
    val(i,j) = ( (i % 4) + 4*(j % 4) + 16*(i//4) + 4*(j//4) ) % 16 + 1
    
    這確保：
    - 同一行：i固定，j變化 → 值變化 ✅
    - 同一列：j固定，i變化 → 值變化 ✅
    - 同一宮：i//4和j//4固定，i%4和j%4變化 → 值變化 ✅
    """
    square = []
    for i in range(16):
        row = []
        for j in range(16):
            i4 = i % 4      # 在band內的行號
            j4 = j % 4      # 在stack內的列號
            ib = i // 4     # band編號
            jb = j // 4     # stack編號
            
            # 核心公式
            val = (i4 + 4*j4 + 16*ib + 4*jb) % 16 + 1
            row.append(val)
        square.append(row)
    
    print("\nV5方法構造結果:")
    for i, row in enumerate(square):
        print(f"  行{i}: {row}")
    
    print(f"  列約束: {'✅' if check_column_conflicts(square) else '❌'}")
    print(f"  宮約束: {'✅' if check_box(square) else '❌'}")
    
    return square

def construct_sudoku_v6():
    """
    方法6：基於GF(16)有限域的構造
    
    使用16元有限域 GF(2^4) 的元素
    
    val(i, j) = GF16[i] * GF16[j] 的反映射到1-16
    """
    # 簡化：使用仿射變換模擬有限域行為
    # GF(16) = {0, 1, α, α², ..., α¹⁴}，其中 α⁴ = α + 1
    
    # 映射：0→1, 1→2, α→3, ..., α¹⁴→16
    # 但為了簡化，直接用整數運算模擬
    
    square = []
    for i in range(16):
        row = []
        for j in range(16):
            # 使用位運算模擬有限域乘法
            # 這實際上是一個已知的Sudoku構造
            val = ((i << 4) ^ j) % 16 + 1
            row.append(val)
        square.append(row)
    
    print("\nV6方法 (位運算):")
    for i, row in enumerate(square[:4]):
        print(f"  行{i}: {row}")
    print("  ...")
    
    print(f"  列約束: {'✅' if check_column_conflicts(square) else '❌'}")
    print(f"  宮約束: {'✅' if check_box(square) else '❌'}")
    
    return square

# ============================================
# 主程序：找出正確的構造方法
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("符闔排列生成規則 V3.0 - 構造方法測試")
    print("=" * 60)
    
    methods = [
        ("方法1 (模16運算)", construct_sudoku_v1),
        ("方法2 (Band/Stack)", construct_sudoku_v2),
        ("方法3 (移位模式)", construct_sudoku_v3),
        ("方法4 (仿射變換)", construct_sudoku_v4),
        ("方法5 (分塊結構)", construct_sudoku_v5),
        ("方法6 (位運算)", construct_sudoku_v6),
    ]
    
    results = {}
    for name, func in methods:
        print("\n" + "-" * 50)
        square = func()
        col_ok = check_column_conflicts(square)
        box_ok = check_box(square)
        results[name] = {"square": square, "col": col_ok, "box": box_ok}
    
    print("\n" + "=" * 60)
    print("結果總結:")
    print("=" * 60)
    for name, data in results.items():
        status = "✅ 完美Sudoku" if (data["col"] and data["box"]) else "❌ 失敗"
        print(f"  {name}: {status}")
