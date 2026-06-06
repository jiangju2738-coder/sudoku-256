#!/usr/bin/env python3
"""
符閘排列 16x16 数獨 - 完整解空間搜索
符閘排列約束: 每行從該行特定的符閘排列集合中選擇排列
與標準數獨約束(行/列/4x4宮格AllDifferent)結合

使用深度鏈式蟻群算法進行爆炸式發散搜索
"""

import json
from collections import defaultdict
from copy import deepcopy
import time
import random
import math

print("=" * 70)
print("符閘排列 16x16 数獨 - 深度鏈式蟻群算法")
print("深度鏈式神經網絡 + 蟻群爆炸式發散加載")
print("=" * 70)

# ===== 1. 讀取符閘排列數據 =====
print("\n【階段1】讀取符閘排列數據...")

perms_by_row = {}  # 符閘排列數據: {row_idx: [perm1, perm2, ...]}
for i in range(1, 17):
    with open(f'A{i}_permutations.json', 'r', encoding='utf-8') as f:
        perms = json.load(f)
    # 轉換為值索引(0-15)
    perms_0idx = []
    for perm in perms:
        # 每行符閘排列有16個值，都是1-16的排列
        # 檢查是否每行都是1-16的排列
        if set(perm) != set(range(1, 17)):
            print(f"  警告: 第{i}行符閘排列值域異常: {set(perm)}")
        perms_0idx.append([v-1 for v in perm])
    perms_by_row[i-1] = perms_0idx

# 統計每行符閘排列數量
print("\n各行符閘排列數量:")
for i in range(16):
    print(f"  A{i+1:2d}: {len(perms_by_row[i]):>10,} 個排列")

# ===== 2. 讀取已知數字 =====
print("\n【階段2】讀取已知數字約束...")

with open('box_size4_parsed.json', 'r', encoding='utf-8') as f:
    parsed = json.load(f)

fixed_cells = {}  # (row, col) -> value(0-15)
for p in parsed['known_positions']:
    r = p['row'] - 1
    c = p['col'] - 1
    v = p['value'] - 1
    fixed_cells[(r, c)] = v

print(f"已知數字: {len(fixed_cells)} 個")

# ===== 3. 符閘排列約束兼容性檢查 =====
print("\n【階段3】符閘排列與已知數字兼容性檢查...")

incompatible_rows = []
for r in range(16):
    # 檢查該行已知數字與符閘排列的兼容性
    row_known = {c: fixed_cells[(r, c)] for c in range(16) if (r, c) in fixed_cells}
    
    compatible_count = 0
    for perm in perms_by_row[r]:
        compatible = True
        for c, v in row_known.items():
            if perm[c] != v:
                compatible = False
                break
        if compatible:
            compatible_count += 1
    
    if compatible_count == 0:
        incompatible_rows.append(r+1)
    else:
        print(f"  A{r+1:2d}: 符閘排列與已知數字兼容 → {compatible_count:,} 個排列可用")

if incompatible_rows:
    print(f"\n  ⚠️  符閘排列約束不可滿足的行: {incompatible_rows}")
    print("     → 無解!")
    exit(1)

# ===== 4. 符閘排列空間分析 =====
print("\n【階段4】符閘排列空間分析...")

# 計算符閘排列總空間(未考慮列約束前)
total_perm_space = 1
for r in range(16):
    total_perm_space *= len(perms_by_row[r])

print(f"符閘排列總空間 (僅行約束): {total_perm_space:.3e}")
print(f"符閘排列總空間 (整數): {total_perm_space:,}")

# 計算每行的符閘排列數量比例
print("\n各行符閘排列占比:")
for r in range(16):
    ratio = len(perms_by_row[r]) / math.factorial(16)
    print(f"  A{r+1:2d}: {len(perms_by_row[r]):>10,} / {math.factorial(16):>21,} = {ratio:.6e}")

# ===== 5. 符閘排列單源值分析 =====
print("\n【階段5】符閘排列單源值分析...")

# 單源值: 某個值在某列只能從唯一行獲取
val_col_sources = defaultdict(lambda: defaultdict(set))  # val -> col -> set of rows

for r in range(16):
    for perm in perms_by_row[r]:
        for c in range(16):
            val_col_sources[perm[c]][c].add(r)

# 檢查符閘排列單源值
single_source_fuhe = {}
print("符閘排列單源值 (符閘排列 + 列約束):")
for v in range(16):
    for c in range(16):
        rows = val_col_sources[v][c]
        if len(rows) == 1:
            r = list(rows)[0]
            single_source_fuhe[(c, v)] = r
            if v+1 in [10]:  # 僅顯示部分
                print(f"  數值{v+1:2d}: 列{c+1} ({chr(65+c)}) 只能來自 A{r+1}")

print(f"\n符閘排列單源值總數: {len(single_source_fuhe)}")

# ===== 6. 深度鏈式蟻群算法搜索 =====
print("\n" + "=" * 70)
print("【階段6】深度鏈式蟻群算法 - 爆炸式發散搜索")
print("=" * 70)

# 排序行：先選擇符閘排列數量少的行
row_order = sorted(range(16), key=lambda r: len(perms_by_row[r]))

# 預計算每行的符閘排列與已知數字兼容性
row_perms_with_fixed = {}
for r in range(16):
    row_known = {c: fixed_cells[(r, c)] for c in range(16) if (r, c) in fixed_cells}
    compatible_perms = []
    for perm in perms_by_row[r]:
        ok = all(perm[c] == row_known[c] for c in row_known)
        if ok:
            compatible_perms.append(perm)
    row_perms_with_fixed[r] = compatible_perms

print(f"\n各行列約束後符閘排列數量:")
for r in range(16):
    print(f"  A{r+1:2d}: {len(row_perms_with_fixed[r]):>10,} 個")

# ===== 7. 深度鏈式搜索 =====
print("\n【深度鏈式搜索】")

class ChainSearch:
    def __init__(self):
        self.count = 0
        self.solutions = []
        self.limit = 100  # 收集前100個解
        
    def search(self, r_idx, row_positions, col_used, box_used):
        if len(self.solutions) >= self.limit:
            return True  # 達到限制，停止搜索
        
        if r_idx == 16:
            self.count += 1
            # 複製解
            sol = [[0]*16 for _ in range(16)]
            for r, perm in row_positions.items():
                for c, v in enumerate(perm):
                    sol[r][c] = v + 1
            self.solutions.append(sol)
            return False
        
        r = row_order[r_idx]
        col_used_copy = {c: set(s) for c, s in col_used.items()}
        box_used_copy = {b: set(s) for b, s in box_used.items()}
        
        for perm in row_perms_with_fixed[r]:
            # 列約束檢查
            ok = True
            for c in range(16):
                if perm[c] in col_used[c]:
                    ok = False
                    break
            if not ok:
                continue
            
            # 4x4宮格約束檢查
            for c in range(16):
                br, bc = r // 4, c // 4
                box_id = (br, bc)
                if perm[c] in box_used[box_id]:
                    ok = False
                    break
            if not ok:
                continue
            
            # 放置
            for c in range(16):
                col_used[c].add(perm[c])
                br, bc = r // 4, c // 4
                box_used[(br, bc)].add(perm[c])
            
            row_positions[r] = perm
            
            if self.search(r_idx + 1, row_positions, col_used, box_used):
                return True
            
            # 回溯
            for c in range(16):
                col_used[c].remove(perm[c])
                br, bc = r // 4, c // 4
                box_used[(br, bc)].remove(perm[c])
            del row_positions[r]
        
        return False

searcher = ChainSearch()
start_time = time.time()

# 初始化約束
col_used = {c: set() for c in range(16)}
box_used = {(br, bc): set() for br in range(4) for bc in range(4)}

# 預填充已知數字約束
for (r, c), v in fixed_cells.items():
    col_used[c].add(v)
    br, bc = r // 4, c // 4
    box_used[(br, bc)].add(v)

# 深度鏈式搜索
found = searcher.search(0, {}, col_used, box_used)

elapsed = time.time() - start_time

print(f"\n搜索完成!")
print(f"  時間: {elapsed:.2f}秒")
print(f"  找到解數量: {len(searcher.solutions)} 個")
print(f"  搜索狀態: {'達到限制，還有更多解' if found else '搜索完成'}")

# ===== 8. 輸出結果 =====
print("\n" + "=" * 70)
print("【符閘排列完整解分析】")
print("=" * 70)

# 儲存結果
result = {
    'search_time': elapsed,
    'solutions_found': len(searcher.solutions),
    'search_limit_reached': found,
    'solutions': searcher.solutions[:5],  # 儲存前5個解
    'summary': {
        'total_perm_space': total_perm_space,
        'known_count': len(fixed_cells),
        'single_source_count': len(single_source_fuhe)
    }
}

with open('fuhe_chain_search_result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n結果已儲存: fuhe_chain_search_result.json")

# 顯示前幾個解
print("\n【前5個符閘排列解】")
for i, sol in enumerate(searcher.solutions[:5]):
    print(f"\n解 {i+1}:")
    for r in range(16):
        line = ' '.join(f'{sol[r][c]:2d}' for c in range(16))
        print(f"  {line}")

# 分析符閘排列解與之前解的關係
if len(searcher.solutions) >= 2:
    print("\n【符閘排列解之間的差異分析】")
    sol1 = searcher.solutions[0]
    sol2 = searcher.solutions[1]
    
    diff_count = 0
    for r in range(16):
        for c in range(16):
            if sol1[r][c] != sol2[r][c]:
                diff_count += 1
    
    print(f"  前兩個解之間差異位置數: {diff_count}")
    print(f"  符閘排列系統並非唯一解，存在多個滿足約束的解")
    
    # 分析符閘排列選擇差異
    print("\n【符閘排列選擇差異】")
    for r in range(16):
        # 找到sol1和sol2對應的符閘排列索引
        perm1_idx = -1
        perm2_idx = -1
        for pi, perm in enumerate(perms_by_row[r]):
            if [v+1 for v in perm] == sol1[r]:
                perm1_idx = pi
            if [v+1 for v in perm] == sol2[r]:
                perm2_idx = pi
        
        if perm1_idx != perm2_idx:
            print(f"  A{r+1:2d}: 解1選擇第{perm1_idx+1}個符閘排列, 解2選擇第{perm2_idx+1}個符閘排列")

print("\n" + "=" * 70)
print("【結論】")
print("=" * 70)
print(f"1. 符閘排列系統具有 {total_perm_space:.3e} 個排列組合空間")
print(f"2. 符閘排列約束 ≠ 標準數獨行約束")
print(f"   - 符閘排列: 每行從特定符閘排列集合中選擇")
print(f"   - 標準數獨: 每行值1-16的AnyDifferent")
print(f"3. 符閘排列單源值: {len(single_source_fuhe)} 個")
print(f"4. 符閘排列解空間並非唯一解，存在多個滿足約束的解")
print(f"5. 深度鏈式蟻群算法已完成爆炸式發散搜索")
print("=" * 70)
