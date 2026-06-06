"""調試V3.0符闔排列生成"""
import json
import random

GRID_SIZE = 16
BOX_SIZE = 4

trigrams = [[(i >> (5-j)) & 1 for j in range(6)] for i in range(64)]

def yao_to_base4(yao):
    vals = []
    for i in range(3):
        base = (yao[i*2] << 1) | yao[i*2+1]
        vals.append(base)
    return vals

# 構造基礎Sudoku
base_perms = []
for i in range(16):
    perm = []
    for j in range(16):
        row_band = i // 4
        row_in_band = i % 4
        col_stack = j // 4
        col_in_stack = j % 4
        row_num = row_band * 4 + row_in_band
        col_num = col_stack * 4 + col_in_stack
        val = (row_num * 4 + col_num) % 16 + 1
        perm.append(val)
    base_perms.append(perm)

print("基礎Sudoku終盤:")
for i, row in enumerate(base_perms):
    print(f"  行{i}: {row}")

# 驗證宮約束
def check_box(square):
    for br in range(4):
        for bc in range(4):
            box = []
            for r in range(br*4, (br+1)*4):
                for c in range(bc*4, (bc+1)*4):
                    box.append(square[r][c])
            if len(set(box)) != 16:
                return False, f"宮({br},{bc})有重複: {box}"
    return True, "OK"

valid, msg = check_box(base_perms)
print(f"\n宮約束驗證: {msg}")

# 現在模擬pool生成
print("\n生成pool...")
all_perms = []
seen = set()

# 添加基礎Sudoku行
for row in base_perms:
    t = tuple(row)
    if t not in seen:
        seen.add(t)
        all_perms.append(row)

print(f"  基礎Sudoku行加入: {len(all_perms)} 個")

# 添加值替換變體
for _ in range(50):
    value_map = list(range(16))
    random.shuffle(value_map)
    for row in base_perms:
        new_row = [value_map[v - 1] + 1 for v in row]
        t = tuple(new_row)
        if t not in seen:
            seen.add(t)
            all_perms.append(new_row)

print(f"  值替換變體加入: {len(all_perms)} 個")

# 檢查基礎Sudoku行是否都在pool中
print("\n檢查基礎Sudoku行是否在pool中:")
for i, base_row in enumerate(base_perms):
    found = tuple(base_row) in seen
    print(f"  行{i}: {'✅ 在pool中' if found else '❌ 不在pool中'}")

# 檢查相容性
def are_compatible(p1, p2):
    for c in range(16):
        if p1[c] == p2[c]:
            return False
    return True

print("\n檢查基礎Sudoku行之間的相容性:")
for i in range(16):
    for j in range(i+1, 16):
        if not are_compatible(base_perms[i], base_perms[j]):
            print(f"  行{i}和行{j}不相容！")
            # 找出衝突列
            for c in range(16):
                if base_perms[i][c] == base_perms[j][c]:
                    print(f"    列{c}: 值{base_perms[i][c]}")

print("\n✅ 基礎Sudoku行兩兩相容" if all(are_compatible(base_perms[i], base_perms[j]) for i in range(16) for j in range(i+1, 16)) else "❌ 有不相容行")
