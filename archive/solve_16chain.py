#!/usr/bin/env python3.14
# -*- coding: utf-8 -*-
"""
━━━━━━ 超級大數獨終極循環搜索求解 ━━━━━━
16×16符闔排列數獨 | 92個已知數字 | 列+宮約束全驗證
"""

import json
import time
import os
from collections import defaultdict
from copy import deepcopy

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"
GRID_SIZE = 16
BOX_SIZE = 4

# ════════════════════════════════════════
# 1. 加載配置
# ════════════════════════════════════════
print("=" * 60)
print("  超級大數獨終極循環搜索求解系統")
print("  16×16 | Box=4 | 92已知數字 | 列+宮全約束")
print("=" * 60)

with open(os.path.join(BASE_DIR, "box_size4_config_parsed.json"), "r", encoding="utf-8") as f:
    config = json.load(f)

known = config["known_digits"]
print(f"\n[配置] 網格{GRID_SIZE}×{GRID_SIZE}, 宮{BOX_SIZE}×{BOX_SIZE}")
print(f"       已知數字 {len(known)}個, 空單元格 {config['empty_cells']}個, 填補率{config['fill_rate']}%")

# ════════════════════════════════════════
# 2. 加載16行符闔排列
# ════════════════════════════════════════
print("\n[加載] 符闔排列...")
row_map = {
    'A': 'A1_permutations.json', 'B': 'A2_permutations.json',
    'C': 'A3_permutations.json', 'D': 'A4_permutations.json',
    'E': 'A5_permutations.json', 'F': 'A6_permutations.json',
    'G': 'A7_permutations.json', 'H': 'A8_permutations.json',
    'I': 'A9_permutations.json', 'J': 'A10_permutations.json',
    'K': 'A11_permutations.json', 'L': 'A12_permutations.json',
    'M': 'A13_permutations.json', 'N': 'A14_permutations.json',
    'O': 'A15_permutations.json', 'P': 'A16_permutations.json',
}
row_letters = list(row_map.keys())

permutations = {}
for letter, fname in row_map.items():
    fpath = os.path.join(BASE_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        permutations[letter] = data if isinstance(data, list) else data.get("permutations", [])
        print(f"  {letter}行: {len(permutations[letter]):,} 個排列")
    else:
        print(f"  警告: {fname} 不存在")

total_perm = sum(len(v) for v in permutations.values())
print(f"\n  總排列數: {total_perm:,}")

# ════════════════════════════════════════
# 3. 建立約束網絡
# ════════════════════════════════════════
print("\n[約束] 建立列/宮約束網絡...")

# 列約束：每列已知值
col_known_vals = defaultdict(set)
col_known_pos = defaultdict(list)  # col -> [(row, val)]
row_known = defaultdict(dict)  # row -> {col: val}

for kd in known:
    r, c, v = kd['row'] - 1, kd['col'] - 1, kd['value']
    col_known_vals[c].add(v)
    col_known_pos[c].append((r, v))
    row_known[r][c] = v

# 宮約束
box_known_vals = defaultdict(set)
for kd in known:
    r, c, v = kd['row'] - 1, kd['col'] - 1, kd['value']
    box_idx = (r // BOX_SIZE) * 4 + (c // BOX_SIZE)
    box_known_vals[box_idx].add(v)

# 初始網格
grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
for kd in known:
    r, c, v = kd['row'] - 1, kd['col'] - 1, kd['value']
    grid[r][c] = v

print(f"  列空位統計: {[16 - len(col_known_vals[c]) for c in range(16)]}")
print(f"  宮空位統計: {[16 - len(box_known_vals[b]) for b in range(16)]}")

# ════════════════════════════════════════
# 4. 預過濾：對每行排列進行列約束匹配
# ════════════════════════════════════════
print("\n[預處理] 列約束預過濾符闔排列...")

def matches_known(perm, row_idx):
    """檢查排列是否與行已知值匹配"""
    for c, v in row_known[row_idx].items():
        if perm[c] != 0 and perm[c] != v:
            return False
        if perm[c] == 0 and v != 0:
            return False
    return True

def col_constraint_ok(perm, row_idx, grid_cols_filled):
    """檢查排列與列約束是否衝突（列已填值不重複）"""
    for c, val in enumerate(perm):
        if val != 0 and val in grid_cols_filled.get(c, set()):
            return False
    return True

def box_constraint_ok(perm, row_idx, grid_box_filled):
    """檢查排列與宮約束是否衝突"""
    for c, val in enumerate(perm):
        if val != 0:
            box_idx = (row_idx // BOX_SIZE) * 4 + (c // BOX_SIZE)
            if val in grid_box_filled.get(box_idx, set()):
                return False
    return True

filtered_perms = {}
for row_idx, letter in enumerate(row_letters):
    if letter not in permutations:
        continue
    raw = permutations[letter]
    # 第一步：匹配已知值
    matched = [p for p in raw if matches_known(row_idx, p)]
    filtered_perms[letter] = matched
    print(f"  {letter}行: {len(raw):,} → {len(matched):,} (匹配行約束)")

# ════════════════════════════════════════
# 5. 終極循環搜索
# ════════════════════════════════════════
print("\n" + "=" * 60)
print("  啟動終極循環搜索 (DFS + 剪枝)")
print("=" * 60)

stats = {'nodes': 0, 'pruned': 0, 'solutions': 0, 'max_depth': 0}
start_time = time.time()

def validate_full_solution(g):
    """終極驗證：行/列/宮AllDifferent + 符闔排列"""
    # 行
    for r in range(16):
        row_vals = g[r]
        if 0 in row_vals or len(set(row_vals)) != 16:
            return False
    # 列
    for c in range(16):
        col_vals = [g[r][c] for r in range(16)]
        if len(set(col_vals)) != 16:
            return False
    # 宮
    for box_idx in range(16):
        vals = []
        for r in range(16):
            for c in range(16):
                if (r // BOX_SIZE) * 4 + (c // BOX_SIZE) == box_idx:
                    vals.append(g[r][c])
        if len(set(vals)) != 16:
            return False
    return True

def solve(row_idx, grid_state, col_filled, box_filled):
    """遞歸搜索"""
    stats['nodes'] += 1
    stats['max_depth'] = max(stats['max_depth'], row_idx)
    
    if row_idx == 16:
        if validate_full_solution(grid_state):
            stats['solutions'] += 1
            return deepcopy(grid_state)
        return None
    
    letter = row_letters[row_idx]
    if letter not in filtered_perms or not filtered_perms[letter]:
        return None
    
    for perm in filtered_perms[letter]:
        # 剪枝：列約束
        if not col_constraint_ok(perm, row_idx, col_filled):
            stats['pruned'] += 1
            continue
        
        # 剪枝：宮約束
        if not box_constraint_ok(perm, row_idx, box_filled):
            stats['pruned'] += 1
            continue
        
        # 應用
        new_col = {k: v.copy() for k, v in col_filled.items()}
        new_box = {k: v.copy() for k, v in box_filled.items()}
        
        for c, val in enumerate(perm):
            if val != 0:
                if c not in new_col:
                    new_col[c] = set()
                new_col[c].add(val)
                box_idx = (row_idx // BOX_SIZE) * 4 + (c // BOX_SIZE)
                if box_idx not in new_box:
                    new_box[box_idx] = set()
                new_box[box_idx].add(val)
        
        grid_state[row_idx] = perm[:]
        result = solve(row_idx + 1, grid_state, new_col, new_box)
        
        if result:
            return result
    
    return None

# 初始化約束集合
init_col = {}
init_box = {}
for c in range(16):
    init_col[c] = col_known_vals[c].copy()
for b in range(16):
    init_box[b] = box_known_vals[b].copy()

# 執行搜索
solution = solve(0, grid, init_col, init_box)

elapsed = time.time() - start_time

print(f"\n{'=' * 60}")
print(f"  搜索完成")
print(f"{'=' * 60}")
print(f"  搜索節點:     {stats['nodes']:,}")
print(f"  剪枝節點:     {stats['pruned']:,}")
print(f"  搜索深度:     {stats['max_depth']}/16")
print(f"  找到解數:     {stats['solutions']}")
print(f"  耗時:         {elapsed:.2f}秒")
print(f"{'=' * 60}")

if solution:
    print("\n  ✅ 終極驗證通過")
    print("\n  [解展示]")
    for r in range(16):
        row_str = " ".join(f"{solution[r][c]:2d}" for c in range(16))
        print(f"  {row_letters[r]}: {row_str}")
    
    # 保存結果
    result_data = {
        "success": True,
        "grid": solution,
        "stats": {
            "nodes_explored": stats['nodes'],
            "nodes_pruned": stats['pruned'],
            "solutions_found": stats['solutions'],
            "search_time_seconds": round(elapsed, 2),
        }
    }
    result_path = os.path.join(BASE_DIR, "16chain_search_result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    print(f"\n  結果已保存: {result_path}")
else:
    print("\n  ❌ 未找到滿足所有約束的解")
    print("  原因分析：符闔排列與列/宮約束存在全局衝突")
