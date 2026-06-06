#!/usr/bin/env python3
"""
符閘排列 16行数獨 DLX精確求解器
基於 Dancing Links 精確覆蓋算法
"""

import json
from collections import defaultdict
from copy import deepcopy

# ===== 1. 讀取已知數據 =====
with open('box_size4_parsed.json', 'r', encoding='utf-8') as f:
    parsed = json.load(f)

known_positions = parsed['known_positions']

# ===== 2. 符閘排列約束 =====
# 數獨256格分布:
# 第1行(A1): 數字1-16   | 第9行(A9): 數字129-144
# 第2行(A2): 數字17-32  | 第10行(A10): 數字145-160
# 第3行(A3): 數字33-48  | 第11行(A11): 數字161-176
# 第4行(A4): 數字49-64  | 第12行(A12): 數字177-192
# 第5行(A5): 數字65-80  | 第13行(A13): 數字193-208
# 第6行(A6): 數字81-96  | 第14行(A14): 數字209-224
# 第7行(A7): 數字97-112 | 第15行(A15): 數字225-240
# 第8行(A8): 數字113-128| 第16行(A16): 數字241-256

# 符閘排列約束: 每行的16個數字恰好是1-16的一個排列
# 即每行必須包含所有16個值，且僅出現1次

# ===== 3. 標準數獨約束 =====
# 每行(水平16格): 值1-16各出現1次
# 每列(垂直16格): 值1-16各出現1次
# 每個4x4宮格: 值1-16各出現1次

N = 16  # 16x16數獨
N2 = N * N  # 256

# ===== 4. DLX 精確覆蓋 =====
class DLXNode:
    def __init__(self):
        self.left = self.right = self.up = self.down = self
        self.col = None
        self.row_id = None

class DLXColumn:
    def __init__(self, name):
        self.left = self.right = self.up = self.down = self
        self.name = name
        self.size = 0
        self.is_header = False

class DLX:
    def __init__(self, n_cols):
        self.headers = [DLXColumn(f'col_{i}') for i in range(n_cols)]
        self.header = DLXColumn('header')
        self.header.is_header = True
        
        # 連接header
        for i, col in enumerate(self.headers):
            col.left = self.headers[i-1]
            col.right = self.header
            col.up = col.down = col
            self.headers[i-1].right = col
            col.size = 0
    
    def add_row(self, cells):
        """添加一列覆蓋的列索引"""
        first = None
        for col_idx in cells:
            node = DLXNode()
            node.col = self.headers[col_idx]
            node.row_id = col_idx
            col = self.headers[col_idx]
            
            # 插入到列末尾
            node.up = col.up
            node.down = col
            col.up.down = node
            col.up = node
            col.size += 1
            
            if first is None:
                first = node
            else:
                node.left = first.left
                node.right = first
                first.left.right = node
                first.left = node
        return first
    
    def cover(self, col):
        col.right.left = col.left
        col.left.right = col.right
        i = col.down
        while i != col:
            j = i.right
            while j != i:
                j.down.up = j.up
                j.up.down = j.down
                j.col.size -= 1
                j = j.right
            i = i.down
    
    def uncover(self, col):
        i = col.up
        while i != col:
            j = i.left
            while j != i:
                j.col.size += 1
                j.down.up = j
                j.up.down = j
                j = j.left
            i = i.up
        col.right.left = col
        col.left.right = col

# ===== 5. 建構符閘排列約束 =====
# 已知數字確定在特定位置
fixed_cells = {}
for p in known_positions:
    r = p['row'] - 1  # 0-indexed
    c = p['col'] - 1  # 0-indexed
    v = p['value'] - 1  # 0-indexed
    fixed_cells[(r, c)] = v

# 符閘排列約束分析：每行的值分佈
print("=" * 60)
print("符閘排列 16行数獨 - DLX精確求解器")
print("=" * 60)

print(f"\n已知數字: {len(fixed_cells)}個")
print(f"未知數字: {N2 - len(fixed_cells)}個")

# 檢查符閘排列約束：每行是否已包含重複值
print("\n=== 符閘排列約束檢查 ===")
row_values = defaultdict(set)
for (r, c), v in fixed_cells.items():
    row_values[r].add(v)

fuhe_conflicts = []
for r in range(N):
    if len(row_values[r]) != len([k for k, v in fixed_cells.items() if k[0] == r]):
        # 有重複值
        vals = [v for (rr, cc), v in fixed_cells.items() if rr == r]
        seen = set()
        for v in vals:
            if v in seen:
                fuhe_conflicts.append(f"行{r+1}(A{r+1})有重複值{v+1}")
            seen.add(v)

if fuhe_conflicts:
    print("符閘排列約束衝突:")
    for c in fuhe_conflicts:
        print(f"  {c}")
else:
    print("符閘排列約束: 每行無重複值 ✓")

# 值-行約束分析
print("\n=== 符閘排列單源值分析 ===")
# 每行必須包含1-16各1次
# 值v 在某列(c)中出現的行數

val_col_rows = defaultdict(lambda: defaultdict(set))
for r in range(N):
    for c in range(N):
        if (r, c) in fixed_cells:
            v = fixed_cells[(r, c)]
            val_col_rows[v][c].add(r)
        else:
            # 未確定位置，該值可能在任何行
            pass

# 檢查每列的值來源
print("\n每列的值來源分析:")
for c in range(N):
    col_vals = set()
    for r in range(N):
        if (r, c) in fixed_cells:
            col_vals.add(fixed_cells[(r, c)])
    known_count = len(col_vals)
    print(f"  第{c+1:2d}列 ({chr(65+c)}): 已知值{col_vals if col_vals else '無'} ({known_count}個)")

# 符閘排列單源值：值v在某列c只能從唯一行獲取
single_source_constraints = []
print("\n符閘排列單源值約束:")
for v in range(N):
    for c in range(N):
        if (None, c) in val_col_rows and v in val_col_rows[v]:
            rows_with_v = val_col_rows[v][c]
            if len(rows_with_v) == 1:
                r = list(rows_with_v)[0]
                single_source_constraints.append((r, c, v))

if single_source_constraints:
    for r, c, v in single_source_constraints:
        print(f"  列{c+1}({chr(65+c)})的值{v+1}只能來自行{r+1}(A{r+1})")
else:
    print("  無列級單源值約束")

print("\n" + "=" * 60)
print("符閘排列約束總結:")
print("=" * 60)
print(f"每行必須包含值1-16各1次 (符閘排列)")
print(f"每列必須包含值1-16各1次")
print(f"每4x4宮格必須包含值1-16各1次")
print(f"已知數字: {len(fixed_cells)}個固定位置")

# ===== 6. 運行求解 =====
print("\n=== 開始DLX求解 ===")

# 使用OR-Tools CP-SAT進行約束求解
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# 變數: x[r][c][v] 表示位置(r,c)的值是否為v
x = {}
for r in range(N):
    for c in range(N):
        for v in range(N):
            x[(r, c, v)] = model.NewBoolVar(f'x_{r}_{c}_{v}')

# 已知數字約束
for (r, c), v in fixed_cells.items():
    for vv in range(N):
        if vv != v:
            model.Add(x[(r, c, vv)] == 0)
    model.Add(x[(r, c, v)] == 1)

# 每格恰好一個值
for r in range(N):
    for c in range(N):
        model.AddExactlyOne(x[(r, c, v)] for v in range(N))

# 每行每個值恰好1次
for r in range(N):
    for v in range(N):
        model.AddExactlyOne(x[(r, c, v)] for c in range(N))

# 每列每個值恰好1次
for c in range(N):
    for v in range(N):
        model.AddExactlyOne(x[(r, c, v)] for r in range(N))

# 每4x4宮格每個值恰好1次
for br in range(4):
    for bc in range(4):
        for v in range(N):
            cells = []
            for dr in range(4):
                for dc in range(4):
                    r, c = br * 4 + dr, bc * 4 + dc
                    cells.append(x[(r, c, v)])
            model.AddExactlyOne(cells)

# 符閘排列約束：已包含在「每行每個值恰好1次」中

# 求解
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300
solver.parameters.num_search_workers = 8
solver.parameters.log_search_progress = True

print("\n求解中...")
result = solver.Solve(model)

if result == cp_model.OPTIMAL or result == cp_model.FEASIBLE:
    print(f"\n*** 解法發現! 狀態: {result} ***")
    
    # 提取解
    solution = [[0] * N for _ in range(N)]
    for r in range(N):
        for c in range(N):
            for v in range(N):
                if solver.Value(x[(r, c, v)]) == 1:
                    solution[r][c] = v + 1  # 轉換為1-16
    
    # 驗證
    print("\n=== 解驗證 ===")
    
    # 行檢查
    valid = True
    for r in range(N):
        vals = solution[r]
        if len(set(vals)) != N:
            print(f"  行{r+1}有重複值! {vals}")
            valid = False
        if set(vals) != set(range(1, 17)):
            print(f"  行{r+1}值域不完整! {set(vals)}")
            valid = False
    
    # 列檢查
    for c in range(N):
        vals = [solution[r][c] for r in range(N)]
        if len(set(vals)) != N:
            print(f"  列{c+1}有重複值! {vals}")
            valid = False
        if set(vals) != set(range(1, 17)):
            print(f"  列{c+1}值域不完整! {set(vals)}")
            valid = False
    
    # 宮格檢查
    for br in range(4):
        for bc in range(4):
            vals = []
            for dr in range(4):
                for dc in range(4):
                    vals.append(solution[br*4+dr][bc*4+dc])
            if len(set(vals)) != N:
                print(f"  宮格({br},{bc})有重複值! {vals}")
                valid = False
            if set(vals) != set(range(1, 17)):
                print(f"  宮格({br},{bc})值域不完整! {set(vals)}")
                valid = False
    
    # 符閘排列檢查
    for r in range(N):
        vals = solution[r]
        if set(vals) != set(range(1, 17)):
            print(f"  符閘排列行{r+1}值域錯誤! {set(vals)}")
            valid = False
    
    if valid:
        print("  ✓ 所有約束通過驗證!")
        print("  ✓ 符閘排列約束滿足")
    
    # 顯示解
    print("\n=== 解決方案 ===")
    for r in range(N):
        line = ' '.join(f'{solution[r][c]:2d}' for c in range(N))
        print(f"  {line}")
    
    # 保存解
    with open('fuhe_solution.json', 'w', encoding='utf-8') as f:
        json.dump({'solution': solution, 'status': str(result)}, f, ensure_ascii=False, indent=2)
    print("\n已保存: fuhe_solution.json")
    
else:
    print(f"\n*** 無解! 狀態: {result} ***")
    if result == cp_model.INFEASIBLE:
        print("約束系統不可滿足，存在衝突")

print("\n求解時間: {:.2f}秒".format(solver.ResponseTime()))
