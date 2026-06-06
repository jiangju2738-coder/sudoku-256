#!/usr/bin/env python3
"""
V61 - 符闔排列集合閉合性驗證
================================

關鍵發現：
即使完全不固定C行，只從符闔排列集合中貪婪選擇，也在F行遇到無有效排列。

這說明：符闔排列集合本身可能無法構成一個滿足三約束的完整16行解！

這挑戰了用戶的核心洞見：「符闔排列本身已經是滿足三約束的鏈式排列解集」
"""

import json
import time
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional

COL_MAP = {'D': 0, 'E': 1, 'F': 2, 'G': 3, 'H': 4, 'I': 5, 'J': 6, 'K': 7,
           'L': 8, 'M': 9, 'N': 10, 'O': 11, 'P': 12, 'Q': 13, 'R': 14, 'T': 15}


class FummelPermutation:
    def __init__(self, row: int, pid: int, values: Tuple[int, ...]):
        self.row = row
        self.pid = pid
        self.values = values
    
    def val(self, col: int) -> int:
        return self.values[col]


def load_permutations(data_dir: str) -> List[List[FummelPermutation]]:
    perms = [[] for _ in range(16)]
    for i in range(16):
        file_path = f"{data_dir}/A{i+1}_permutations.json"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for pid, vals in enumerate(data):
                perms[i].append(FummelPermutation(i, pid, tuple(vals)))
        except FileNotFoundError:
            pass
    return perms


def greedy_select(perms: List[List[FummelPermutation]], 
                  fixed_rows: Dict[int, List[int]] = None) -> Optional[List[List[int]]]:
    """
    貪婪選擇：逐行選擇第一個可行的符闔排列
    
    fixed_rows: 某些行已經固定的值
    """
    print("\n=== 貪婪選擇 ===")
    
    grid: List[List[Optional[int]]] = [[None]*16 for _ in range(16)]
    
    # 先固定指定的行
    if fixed_rows:
        for row_idx, vals in fixed_rows.items():
            for col_idx, val in enumerate(vals):
                grid[row_idx][col_idx] = val
    
    for row_idx in range(16):
        # 如果這行已固定，跳過
        if fixed_rows and row_idx in fixed_rows:
            continue
        
        print(f"  處理行{chr(65+row_idx)}...")
        
        # 收集該行所有可行的排列
        valid_perms = []
        for perm in perms[row_idx]:
            valid = True
            
            # 檢查列約束
            for col_idx in range(16):
                val = perm.val(col_idx)
                
                # 檢查列是否已有相同值
                for r in range(16):
                    if r != row_idx and grid[r][col_idx] == val:
                        valid = False
                        break
                if not valid:
                    break
                
                # 檢查宮約束
                if valid:
                    br = row_idx // 4
                    bc = col_idx // 4
                    for r in range(16):
                        if r // 4 != br:
                            continue
                        for c in range(16):
                            if c // 4 != bc:
                                continue
                            if grid[r][c] == val:
                                valid = False
                                break
                        if not valid:
                            break
            
            if valid:
                valid_perms.append(perm)
        
        if not valid_perms:
            print(f"    ❌ 行{chr(65+row_idx)} 無有效排列!")
            
            # 顯示前幾個被排除的原因
            print(f"    排除原因分析 (前5個排列):")
            for i, perm in enumerate(perms[row_idx][:5]):
                reasons = []
                for col_idx in range(16):
                    val = perm.val(col_idx)
                    for r in range(16):
                        if r != row_idx and grid[r][col_idx] == val:
                            reasons.append(f"列{list(COL_MAP.keys())[col_idx]}衝突(行{chr(65+r)})")
                            break
                if reasons:
                    print(f"      排列#{perm.pid}: {', '.join(reasons[:3])}")
            
            return None
        
        # 選擇第一個有效排列
        chosen = valid_perms[0]
        for col_idx in range(16):
            grid[row_idx][col_idx] = chosen.val(col_idx)
        
        print(f"    ✓ 選擇排列#{chosen.pid}")
    
    return grid


def backtrack_search(perms: List[List[FummelPermutation]], 
                     fixed_rows: Dict[int, List[int]] = None,
                     max_solutions: int = 10) -> Tuple[int, int]:
    """
    回溯搜索，找到解的數量
    
    返回: (搜索的迭代次數, 找到的解數)
    """
    print("\n=== 回溯搜索 ===")
    
    grid: List[List[Optional[int]]] = [[None]*16 for _ in range(16)]
    
    # 先固定指定的行
    if fixed_rows:
        for row_idx, vals in fixed_rows.items():
            for col_idx, val in enumerate(vals):
                grid[row_idx][col_idx] = val
    
    solutions = []
    iterations = [0]
    
    def is_col_safe(row, col, val):
        for r in range(16):
            if r != row and grid[r][col] == val:
                return False
        return True
    
    def is_box_safe(row, col, val):
        br = row // 4
        bc = col // 4
        for r in range(br*4, br*4+4):
            for c in range(bc*4, bc*4+4):
                if (r != row or c != col) and grid[r][c] == val:
                    return False
        return True
    
    def find_next_cell():
        best_cell = None
        best_count = 17
        
        for row in range(16):
            for col in range(16):
                if grid[row][col] is not None:
                    continue
                if fixed_rows and row in fixed_rows:
                    continue
                
                count = 0
                for perm in perms[row]:
                    val = perm.val(col)
                    if is_col_safe(row, col, val) and is_box_safe(row, col, val):
                        count += 1
                
                if count < best_count:
                    best_count = count
                    best_cell = (row, col)
                    if count == 0:
                        return None
        
        return best_cell
    
    def backtrack():
        if len(solutions) >= max_solutions:
            return True
        
        cell = find_next_cell()
        if cell is None:
            # 檢查是否完整
            for row in range(16):
                for col in range(16):
                    if grid[row][col] is None and not (fixed_rows and row in fixed_rows):
                        return False
            
            solutions.append([r[:] for r in grid])
            print(f"  🎯 解 #{len(solutions)}")
            return len(solutions) < max_solutions
        
        row, col = cell
        
        # 收集可行值
        candidates = []
        for perm in perms[row]:
            val = perm.val(col)
            if is_col_safe(row, col, val) and is_box_safe(row, col, val):
                candidates.append((val, perm))
        
        # MRV排序
        candidates.sort(key=lambda x: -len(x[1].values))
        
        for val, perm in candidates:
            iterations[0] += 1
            
            # 保存狀態
            old_grid = [r[:] for r in grid]
            old_perms = [p[:] for p in perms]
            
            # 應用
            grid[row][col] = val
            
            # 約束傳播
            for r2 in range(16):
                if r2 == row:
                    continue
                remaining = []
                for p2 in perms[r2]:
                    if p2.val(col) == val:
                        continue
                    in_box = False
                    for c in range(16):
                        if p2.val(c) == val:
                            if row // 4 == r2 // 4 and col // 4 == c // 4:
                                in_box = True
                                break
                    if not in_box:
                        remaining.append(p2)
                perms[r2] = remaining
            
            # 遞歸
            if backtrack():
                return True
            
            # 回溯
            grid = old_grid
            perms = old_perms
        
        return False
    
    backtrack()
    
    return iterations[0], len(solutions)


if __name__ == "__main__":
    print("=" * 70)
    print("V61 - 符闔排列集合閉合性驗證")
    print("=" * 70)
    
    print("""
關鍵問題：符闔排列集合本身是否閉合？

用戶洞見：「符闔排列本身已經是滿足三約束的鏈式排列解集」

驗證方法：
1. 貪婪選擇：不固定任何行，逐行選擇第一個可行排列
2. 回溯搜索：不固定任何行，搜索所有可行解

如果符闔排列集合本身閉合 → 應該能找到解
如果符闔排列集合本身不閉合 → 無法找到解
""")
    
    # 載入符闔排列
    print("\n=== 載入符闔排列 ===")
    perms = load_permutations("D:/2026/WPF_Sudoku/Sudoku_256")
    for i in range(16):
        print(f"  行{chr(65+i)}: {len(perms[i]):,}個")
    
    # 測試1：完全不固定，貪婪選擇
    print("\n" + "=" * 70)
    print("測試1：完全不固定，貪婪選擇")
    print("=" * 70)
    
    solution1 = greedy_select([p[:] for p in perms])
    
    if solution1:
        print("\n✓ 找到了解 (貪婪)")
    else:
        print("\n❌ 貪婪選擇失敗")
    
    # 測試2：完全不固定，回溯搜索
    print("\n" + "=" * 70)
    print("測試2：完全不固定，回溯搜索")
    print("=" * 70)
    
    iterations, solutions = backtrack_search([p[:] for p in perms], max_solutions=5)
    
    print(f"\n迭代次數: {iterations:,}")
    print(f"找到的解數: {solutions}")
    
    # 測試3：固定C行，回溯搜索
    print("\n" + "=" * 70)
    print("測試3：固定C行，回溯搜索")
    print("=" * 70)
    
    c_row_values = [11, 6, 14, 1, 4, 2, 13, 8, 7, 12, 3, 16, 10, 9, 15, 5]
    fixed_c = {2: c_row_values}
    
    # 預先過濾符闔排列
    perms_c = [p[:] for p in perms]
    for row_idx in range(16):
        if row_idx == 2:
            continue
        remaining = []
        for perm in perms_c[row_idx]:
            valid = True
            for col_idx in range(16):
                if perm.val(col_idx) == c_row_values[col_idx]:
                    valid = False
                    break
            if valid:
                remaining.append(perm)
        perms_c[row_idx] = remaining
    
    print("\n過濾後符闔排列:")
    for i in range(16):
        print(f"  行{chr(65+i)}: {len(perms_c[i]):,}個")
    
    iterations_c, solutions_c = backtrack_search(perms_c, fixed_c, max_solutions=5)
    
    print(f"\n迭代次數: {iterations_c:,}")
    print(f"找到的解數: {solutions_c}")
    
    # 總結
    print("\n" + "=" * 70)
    print("總結：符闔排列集合閉合性驗證")
    print("=" * 70)
    
    print(f"""
【實驗結果】

| 測試場景 | 迭代次數 | 解數 | 狀態 |
|---------|---------|------|------|
| 完全不固定 (貪婪) | - | 0 或 1 | {("✓ 找到解" if solution1 else "❌ 貪婪失敗")} |
| 完全不固定 (回溯) | {iterations:,} | {solutions} | {("✓ 找到解" if solutions > 0 else "❌ 無解")} |
| 固定C行 (回溯) | {iterations_c:,} | {solutions_c} | {("✓ 找到解" if solutions_c > 0 else "❌ 無解")} |

【分析】

1. 如果符闔排列集合本身閉合：
   - 應該能找到至少一個滿足三約束的16行解
   - 即使不固定任何行

2. 如果符闔排列集合本身不閉合：
   - 無法找到任何滿足三約束的16行解
   - 這說明符闔排列的生成規則可能有問題

【用戶洞見的再驗證】

用戶說：「符闔排列本身已經是滿足包含滿足行約束 列約束 宮約束
三者的各自獨立的鏈式排列解集」

這個結論需要修正：

- ✅ 符闔排列本身滿足行約束 (16個值互不相同) ✓
- ❓ 符闔排列集合本身是否滿足列約束+宮約束？需要驗證
- ❓ 如果符闔排列集合本身不閉合，則用戶的洞見需要修正

【下一步】

1. 如果符闔排列集合本身不閉合 → 需要重新生成符闔排列
2. 如果符闔排列集合本身閉合 → 需要分析為什麼固定C行後無解

"""
    )
