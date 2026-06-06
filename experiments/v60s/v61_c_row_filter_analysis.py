#!/usr/bin/env python3
"""
V61 - C行錨點過濾後深度分析
================================

實驗結果：
- 只固定C行，過濾後符闔排列仍有很多
- 但搜索仍然NO_SOLUTION (14.70秒)

需要分析：為什麼過濾後仍然無解？
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


def load_c_row_anchors() -> List[int]:
    return [11, 6, 14, 1, 4, 2, 13, 8, 7, 12, 3, 16, 10, 9, 15, 5]


def analyze_column_conflicts_after_c_filter(perms: List[List[FummelPermutation]], 
                                             c_row_values: List[int]) -> Dict:
    """
    分析C行過濾後，每列的值分佈和潛在衝突
    """
    print("\n=== 列約束深度分析 ===")
    
    # 統計每列在所有符闔排列中的值分佈
    col_value_dist: Dict[int, Counter] = {i: Counter() for i in range(16)}
    
    for row_idx in range(16):
        if row_idx == 2:  # C行已固定
            continue
        
        for perm in perms[row_idx]:
            for col_idx in range(16):
                col_value_dist[col_idx][perm.val(col_idx)] += 1
    
    print("\n每列的值分佈 (排除C行):")
    for col_idx in range(16):
        c_val = c_row_values[col_idx]
        col_label = list(COL_MAP.keys())[col_idx]
        
        # 計算該列不與C行衝突的值有多少
        safe_count = sum(cnt for val, cnt in col_value_dist[col_idx].items() 
                        if val != c_val)
        total = sum(col_value_dist[col_idx].values())
        
        print(f"  列{col_label}(C行={c_val}): 安全值占比 {safe_count}/{total} ({safe_count/total*100:.1f}%)")
        
        # 檢查是否有值在所有排列中都被C行排除
        for val, cnt in col_value_dist[col_idx].most_common(3):
            if val == c_val:
                print(f"    ⚠️ 值{val}與C行衝突 (出現{cnt}次)")
    
    return {"col_value_dist": col_value_dist}


def analyze_box_conflicts_after_c_filter(perms: List[List[FummelPermutation]],
                                          c_row_values: List[int]) -> Dict:
    """
    分析C行過濾後，每個宮的值分佈和潛在衝突
    """
    print("\n=== 宮約束深度分析 ===")
    
    # 統計每個宮的值分佈
    box_value_dist: Dict[Tuple[int,int], Counter] = {}
    for br in range(4):
        for bc in range(4):
            box_value_dist[(br, bc)] = Counter()
    
    for row_idx in range(16):
        if row_idx == 2:  # C行已固定
            continue
        
        for perm in perms[row_idx]:
            for col_idx in range(16):
                br = row_idx // 4
                bc = col_idx // 4
                box_value_dist[(br, bc)][perm.val(col_idx)] += 1
    
    print("\n每個宮的值分佈 (排除C行):")
    for br in range(4):
        for bc in range(4):
            # 計算C行在這個宮的值
            c_vals_in_box = []
            for c in range(bc*4, bc*4+4):
                c_vals_in_box.append(c_row_values[c])
            
            box_label = f"({br},{bc})"
            total = sum(box_value_dist[(br, bc)].values())
            
            # 檢查C行值在該宮的衝突
            conflicts = [v for v in c_vals_in_box if box_value_dist[(br, bc)][v] > 0]
            
            if conflicts:
                print(f"  宮{box_label}: C行值{conflicts}在其他行符闔排列中存在!")
            else:
                print(f"  宮{box_label}: 無C行值衝突")
    
    return {"box_value_dist": box_value_dist}


def find_solution_without_c_constraint(perms: List[List[FummelPermutation]]) -> Optional[List[List[int]]]:
    """
    完全不固定C行，只從符闔排列中選擇一個完整解
    
    用於驗證：符闔排列集合本身是否能構成一個滿足三約束的解
    """
    print("\n=== 完全不固定，只從符闔排列選擇 ===")
    
    # 用啟發式貪婪算法嘗試尋找一個解
    grid: List[List[Optional[int]]] = [[None]*16 for _ in range(16)]
    
    for row_idx in range(16):
        print(f"  處理行{chr(65+row_idx)}...")
        
        # 收集該行所有可行的排列
        valid_perms = []
        for perm in perms[row_idx]:
            # 檢查列約束
            valid = True
            for col_idx in range(16):
                val = perm.val(col_idx)
                # 檢查列
                for r in range(row_idx):
                    if grid[r][col_idx] == val:
                        valid = False
                        break
                if not valid:
                    break
                
                # 檢查宮
                if valid:
                    br = row_idx // 4
                    bc = col_idx // 4
                    for r in range(br*4, row_idx):
                        if r // 4 != br:
                            continue
                        for c in range(bc*4, bc*4+4):
                            if grid[r][c] == val:
                                valid = False
                                break
                        if not valid:
                            break
            
            if valid:
                valid_perms.append(perm)
        
        if not valid_perms:
            print(f"    ❌ 行{chr(65+row_idx)} 無有效排列!")
            return None
        
        # 選擇第一個有效排列
        chosen = valid_perms[0]
        for col_idx in range(16):
            grid[row_idx][col_idx] = chosen.val(col_idx)
        
        print(f"    ✓ 選擇排列#{chosen.pid}")
    
    return grid


def search_with_backtrack(perms: List[List[FummelPermutation]], 
                          c_row_values: List[int],
                          max_solutions: int = 5) -> List[List[List[int]]]:
    """
    回溯搜索，找到最多max_solutions個解
    """
    print("\n=== 回溯搜索 ===")
    
    solutions = []
    iterations = [0]
    
    def is_col_safe(grid, row, col, val):
        for r in range(16):
            if r != row and grid[r][col] == val:
                return False
        return True
    
    def is_box_safe(grid, row, col, val):
        br = row // 4
        bc = col // 4
        for r in range(br*4, br*4+4):
            for c in range(bc*4, bc*4+4):
                if (r != row or c != col) and grid[r][c] == val:
                    return False
        return True
    
    def backtrack(row, col, grid):
        if len(solutions) >= max_solutions:
            return
        
        iterations[0] += 1
        if iterations[0] % 50000 == 0:
            print(f"    迭代={iterations[0]:,}, 解數={len(solutions)}")
        
        # 找到下一個空單元格
        for r in range(16):
            if r == 2:  # C行已固定
                continue
            for c in range(16):
                if grid[r][c] is None:
                    # 收集可行值
                    for perm in perms[r]:
                        val = perm.val(c)
                        if is_col_safe(grid, r, c, val) and is_box_safe(grid, r, c, val):
                            # 選擇這個值
                            old_grid = [rr[:] for rr in grid]
                            grid[r][c] = val
                            
                            # 更新其他行的可行排列
                            old_perms = [pp[:] for pp in perms]
                            for r2 in range(16):
                                if r2 == r:
                                    continue
                                remaining = []
                                for p2 in perms[r2]:
                                    if p2.val(c) == val:
                                        continue
                                    # 檢查宮約束
                                    in_box = False
                                    for cc in range(16):
                                        if p2.val(cc) == val:
                                            if r // 4 == r2 // 4 and c // 4 == cc // 4:
                                                in_box = True
                                                break
                                    if not in_box:
                                        remaining.append(p2)
                                perms[r2] = remaining
                            
                            if backtrack(r, c + 1, grid):
                                return True
                            
                            # 回溯
                            grid = old_grid
                            perms = old_perms
                    return False
        
        # 所有單元格都填滿了
        solutions.append([r[:] for r in grid])
        print(f"    🎯 解 #{len(solutions)}")
        return len(solutions) < max_solutions
    
    # 初始化：固定C行
    grid = [[None]*16 for _ in range(16)]
    for col_idx, val in enumerate(c_row_values):
        grid[2][col_idx] = val
    
    # 根據C行過濾符闔排列
    for row_idx in range(16):
        if row_idx == 2:
            continue
        remaining = []
        for perm in perms[row_idx]:
            valid = True
            for col_idx in range(16):
                if perm.val(col_idx) == c_row_values[col_idx]:
                    valid = False
                    break
            if valid:
                remaining.append(perm)
        perms[row_idx] = remaining
    
    backtrack(0, 0, grid)
    
    return solutions


if __name__ == "__main__":
    print("=" * 70)
    print("V61 - C行錨點過濾後深度分析")
    print("=" * 70)
    
    # 載入符闔排列
    print("\n=== 載入符闔排列 ===")
    perms = load_permutations("D:/2026/WPF_Sudoku/Sudoku_256")
    for i in range(16):
        print(f"  行{chr(65+i)}: {len(perms[i]):,}個")
    
    c_row_values = load_c_row_anchors()
    print(f"\nC行錨點: {c_row_values}")
    
    # 根據C行過濾
    print("\n=== 根據C行過濾符闔排列 ===")
    filtered_perms = [p[:] for p in perms]
    for row_idx in range(16):
        if row_idx == 2:
            continue
        remaining = []
        for perm in filtered_perms[row_idx]:
            valid = True
            for col_idx in range(16):
                if perm.val(col_idx) == c_row_values[col_idx]:
                    valid = False
                    break
            if valid:
                remaining.append(perm)
        filtered_perms[row_idx] = remaining
        print(f"  行{chr(65+row_idx)}: {len(perms[row_idx]):,} → {len(remaining):,}")
    
    # 分析列約束
    analyze_column_conflicts_after_c_filter(filtered_perms, c_row_values)
    
    # 分析宮約束
    analyze_box_conflicts_after_c_filter(filtered_perms, c_row_values)
    
    # 嘗試完全不固定C行
    print("\n" + "=" * 70)
    print("嘗試完全不固定，只從符闔排列選擇")
    print("=" * 70)
    solution_without_c = find_solution_without_c_constraint([p[:] for p in perms])
    
    if solution_without_c:
        print("\n✓ 找到了不固定C行的解!")
    else:
        print("\n❌ 即使不固定C行，也找不到解")
        print("   這說明符闔排列集合本身可能無法構成完整解")
    
    # 回溯搜索
    print("\n" + "=" * 70)
    print("回溯搜索 (固定C行)")
    print("=" * 70)
    solutions = search_with_backtrack([p[:] for p in filtered_perms], c_row_values, max_solutions=3)
    
    print(f"\n找到的解數: {len(solutions)}")
    
    # 總結
    print("\n" + "=" * 70)
    print("總結")
    print("=" * 70)
    
    print("""
【分析結果】

1. C行過濾後符闔排列數量：
   - 大部分行仍有大量排列 (100+ 個)
   - 但搜索仍然無解

2. 可能原因：
   a) 列約束累積衝突：雖然每列有安全值，但16行組合後可能無法滿足
   b) 宮約束累積衝突：雖然每個宮有安全值，但組合後可能無法滿足
   c) 符闔排列集合本身不閉合：選擇某些行後，其他行無有效排列

3. 完全不固定C行的測試：
   - 如果找到解，說明符闔排列集合本身可以構成解
   - 如果找不到解，說明符闔排列集合本身就有問題

【用戶策略的驗證】

用戶說：「如果存在...的解，那其實不用固定牠行直接運用三者約束規則遍歷256宮」

- 如果符闔排列集合本身能構成解 → 策略正確
- 如果符闔排列集合本身不能構成解 → 需要重新生成符闔排列

【下一步】
需要驗證符闔排列集合的生成規則是否正確，以及是否滿足「三約束融合」的特性。
""")
