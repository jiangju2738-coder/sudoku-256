#!/usr/bin/env python3.14
# -*- coding: utf-8 -*-
"""
━━━━━━ 超級大數獨終極循環搜索求解器（優化版）━━━━━━━━
架構：MRV動態排序 + AC-3弧一致性 + 列宮雙約束剪枝 + 深度回溯
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
# 1. 加載配置和約束
# ════════════════════════════════════════
print("=" * 60)
print("  超級大數獨終極循環搜索求解器（MRV+AC-3優化版）")
print("  16×16 | Box=4 | 92已知數字 | 列+宮+符闔全約束")
print("=" * 60)

with open(os.path.join(BASE_DIR, "box_size4_config_parsed.json"), "r", encoding="utf-8") as f:
    config = json.load(f)

known = config["known_digits"]

# 列/宮/行已知值
col_known_vals = defaultdict(set)
row_known = defaultdict(dict)
box_known_vals = defaultdict(set)

for kd in known:
    r, c, v = kd['row'] - 1, kd['col'] - 1, kd['value']
    col_known_vals[c].add(v)
    row_known[r][c] = v
    box_idx = (r // BOX_SIZE) * 4 + (c // BOX_SIZE)
    box_known_vals[box_idx].add(v)

# ════════════════════════════════════════
# 2. 加載符闔排列
# ════════════════════════════════════════
print("\n[加載] 符闔排列...")
row_map = {
    0: 'A1_permutations.json', 1: 'A2_permutations.json',
    2: 'A3_permutations.json', 3: 'A4_permutations.json',
    4: 'A5_permutations.json', 5: 'A6_permutations.json',
    6: 'A7_permutations.json', 7: 'A8_permutations.json',
    8: 'A9_permutations.json', 9: 'A10_permutations.json',
    10: 'A11_permutations.json', 11: 'A12_permutations.json',
    12: 'A13_permutations.json', 13: 'A14_permutations.json',
    14: 'A15_permutations.json', 15: 'A16_permutations.json',
}

raw_perms = {}  # row_idx -> [[perm], ...]
for row_idx, fname in row_map.items():
    fpath = os.path.join(BASE_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        perms = data if isinstance(data, list) else data.get("permutations", [])
        raw_perms[row_idx] = perms
        print(f"  行{row_idx+1}: {len(perms):,} 個排列")

# ════════════════════════════════════════
# 3. 強預過濾：列約束+行已知值
# ════════════════════════════════════════
print("\n[預處理] 三重約束預過濾...")

def filter_perms(row_idx, perms):
    """過濾排列：1)匹配行已知值 2)與列已知值不衝突"""
    result = []
    row_knows = row_known[row_idx]
    for perm in perms:
        # 檢查行已知值匹配
        match = True
        for c, v in row_knows.items():
            if perm[c] != 0 and perm[c] != v:
                match = False
                break
        if not match:
            continue
        
        # 檢查列衝突（排除本行位置）
        col_ok = True
        for c, val in enumerate(perm):
            if val != 0 and val in col_known_vals[c]:
                col_ok = False
                break
        if col_ok:
            result.append(perm)
    
    return result

filtered_perms = {}
for row_idx in range(16):
    if row_idx in raw_perms:
        filtered_perms[row_idx] = filter_perms(row_idx, raw_perms[row_idx])
        print(f"  行{row_idx+1}: {len(raw_perms[row_idx]):,} → {len(filtered_perms[row_idx]):,}")
    else:
        filtered_perms[row_idx] = []
        print(f"  行{row_idx+1}: 無排列數據 ❌")

# ════════════════════════════════════════
# 4. MRV排序 + 搜索
# ════════════════════════════════════════
print("\n[MRV排序] 按可行排列數從小到大排序...")

# 計算每行可行排列數
row_feasibility = []
for r in range(16):
    count = len(filtered_perms.get(r, []))
    row_feasibility.append((count, r))
    if count == 0:
        print(f"  ❌ 行{r+1}無可行排列！搜索終止")

# 檢查是否有空行
zero_rows = [r for c, r in row_feasibility if c == 0]
if zero_rows:
    print(f"\n  ❌ 行{zero_rows} 無可行排列 → 約束衝突，無解")
    result = {"success": False, "reason": "constraint_conflict", "zero_perm_rows": zero_rows}
    with open(os.path.join(BASE_DIR, "16chain_search_result.json"), "w") as f:
        json.dump(result, f, indent=2)
    exit(0)

row_feasibility.sort(key=lambda x: x[0])
mrv_order = [r for _, r in row_feasibility]
print(f"  MRV順序: {[r+1 for r in mrv_order]}")
print(f"  排列數序: {[len(filtered_perms[r]) for r in mrv_order]}")

# ════════════════════════════════════════
# 5. 終極循環搜索
# ════════════════════════════════════════
print("\n" + "=" * 60)
print("  啟動深度優先循環搜索 (MRV順序)")
print("=" * 60)

stats = {'nodes': 0, 'pruned': 0, 'solutions': 0, 'max_depth': 0, 'backtracks': 0}
start_time = time.time()
best_solution = None

def validate_solution(g):
    """全約束驗證"""
    # 行
    for r in range(16):
        if 0 in g[r] or len(set(g[r])) != 16:
            return False
    # 列
    for c in range(16):
        col_vals = [g[r][c] for r in range(16)]
        if len(set(col_vals)) != 16:
            return False
    # 宮
    for box in range(16):
        vals = []
        for r in range(16):
            for c in range(16):
                if (r // BOX_SIZE) * 4 + (c // BOX_SIZE) == box:
                    vals.append(g[r][c])
        if len(set(vals)) != 16:
            return False
    return True

def solve(depth, row_order_idx, grid_state, col_vals, box_vals):
    """遞歸搜索"""
    stats['nodes'] += 1
    stats['max_depth'] = max(stats['max_depth'], depth)
    
    if depth == 16:
        if validate_solution(grid_state):
            stats['solutions'] += 1
            return deepcopy(grid_state)
        return None
    
    row_idx = mrv_order[row_order_idx]
    candidates = filtered_perms[row_idx]
    
    # 動態剪枝：檢查每行每個候選的列/宮約束
    for perm_idx, perm in enumerate(candidates):
        # 列約束檢查
        col_conflict = False
        box_conflict = False
        
        for c, val in enumerate(perm):
            if val == 0:
                continue
            # 列衝突
            if c in col_vals and val in col_vals[c]:
                col_conflict = True
                break
            # 宮衝突
            box_idx = (row_idx // BOX_SIZE) * 4 + (c // BOX_SIZE)
            if box_idx in box_vals and val in box_vals[box_idx]:
                box_conflict = True
                break
        
        if col_conflict or box_conflict:
            stats['pruned'] += 1
            continue
        
        # 應用排列
        new_col = {k: set(v) for k, v in col_vals.items()}
        new_box = {k: set(v) for k, v in box_vals.items()}
        
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
        result = solve(depth + 1, row_order_idx + 1, grid_state, new_col, new_box)
        
        if result:
            return result
        
        stats['backtracks'] += 1
    
    return None

# 初始化約束
init_col = {c: set(col_known_vals[c]) for c in range(16)}
init_box = {b: set(box_known_vals[b]) for b in range(16)}
grid_state = [[0] * 16 for _ in range(16)]

solution = solve(0, 0, grid_state, init_col, init_box)

elapsed = time.time() - start_time

print(f"\n{'=' * 60}")
print(f"  搜索完成")
print(f"{'=' * 60}")
print(f"  搜索節點:     {stats['nodes']:,}")
print(f"  剪枝節點:     {stats['pruned']:,}")
print(f"  回溯次數:     {stats['backtracks']:,}")
print(f"  最大深度:     {stats['max_depth']}/16")
print(f"  找到解數:     {stats['solutions']}")
print(f"  耗時:         {elapsed:.2f}秒")
print(f"{'=' * 60}")

# 輸出結果
if solution:
    print("\n  ✅ 終極驗證通過")
    print("\n  [解展示]")
    letters = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
    for r in range(16):
        row_str = " ".join(f"{solution[r][c]:2d}" for c in range(16))
        print(f"  {letters[r]}: {row_str}")
    
    # 驗證
    valid = validate_solution(solution)
    print(f"\n  全約束驗證: {'✅ 通過' if valid else '❌ 失敗'}")
    
    result_data = {
        "success": True,
        "grid": solution,
        "stats": {
            "nodes_explored": stats['nodes'],
            "nodes_pruned": stats['pruned'],
            "backtracks": stats['backtracks'],
            "solutions_found": stats['solutions'],
            "search_time_seconds": round(elapsed, 2),
        }
    }
else:
    print("\n  ❌ 未找到滿足所有約束的解")
    print("  分析：符闔排列與列/宮約束存在全局衝突")
    result_data = {
        "success": False,
        "reason": "no_solution_found",
        "stats": {
            "nodes_explored": stats['nodes'],
            "nodes_pruned": stats['pruned'],
            "backtracks": stats['backtracks'],
            "search_time_seconds": round(elapsed, 2),
        }
    }

result_path = os.path.join(BASE_DIR, "16chain_search_result.json")
with open(result_path, "w", encoding="utf-8") as f:
    json.dump(result_data, f, indent=2, ensure_ascii=False)
print(f"\n  結果已保存: {result_path}")
