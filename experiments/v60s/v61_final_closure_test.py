#!/usr/bin/env python3
"""
V61 - 符闔排列集合閉合性最終驗證
================================

修正版本：測試符闔排列集合本身是否能構成16行解
"""

import json
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


def test_closure_by_greedy(perms: List[List[FummelPermutation]]) -> Tuple[bool, Optional[List[FummelPermutation]], str]:
    """
    用貪婪算法測試閉合性
    
    返回: (是否找到解, 解中使用的排列, 失敗原因)
    """
    grid: List[List[int]] = [[0]*16 for _ in range(16)]
    chosen_perms: List[FummelPermutation] = []
    
    for row_idx in range(16):
        found = False
        for perm in perms[row_idx]:
            # 檢查列約束
            col_ok = True
            for col_idx in range(16):
                val = perm.val(col_idx)
                for r in range(row_idx):
                    if grid[r][col_idx] == val:
                        col_ok = False
                        break
                if not col_ok:
                    break
            
            if not col_ok:
                continue
            
            # 檢查宮約束
            box_ok = True
            for col_idx in range(16):
                val = perm.val(col_idx)
                br = row_idx // 4
                bc = col_idx // 4
                for r in range(br*4, row_idx):
                    if r // 4 != br:
                        continue
                    for c in range(bc*4, bc*4+4):
                        if grid[r][c] == val:
                            box_ok = False
                            break
                    if not box_ok:
                        break
                if not box_ok:
                    break
            
            if box_ok:
                # 選擇這個排列
                for col_idx in range(16):
                    grid[row_idx][col_idx] = perm.val(col_idx)
                chosen_perms.append(perm)
                found = True
                break
        
        if not found:
            return False, None, f"行{chr(65+row_idx)}無有效排列"
    
    return True, chosen_perms, "成功"


def test_closure_by_backtrack(perms: List[List[FummelPermutation]], 
                              max_solutions: int = 3) -> Tuple[int, int, List[List[List[int]]]]:
    """
    用回溯搜索測試閉合性
    
    返回: (迭代次數, 解數, 解列表)
    """
    grid: List[List[Optional[int]]] = [[None]*16 for _ in range(16)]
    solutions: List[List[List[int]]] = []
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
    
    def find_best_cell():
        best_cell = None
        best_count = 17
        
        for row in range(16):
            for col in range(16):
                if grid[row][col] is not None:
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
        
        cell = find_best_cell()
        if cell is None:
            solutions.append([r[:] for r in grid])
            return len(solutions) < max_solutions
        
        row, col = cell
        
        candidates = []
        for perm in perms[row]:
            val = perm.val(col)
            if is_col_safe(row, col, val) and is_box_safe(row, col, val):
                candidates.append((val, perm))
        
        for val, perm in candidates:
            iterations[0] += 1
            
            old_grid = [r[:] for r in grid]
            old_perms = [p[:] for p in perms]
            
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
            
            if backtrack():
                return True
            
            grid = old_grid
            perms = old_perms
        
        return False
    
    backtrack()
    return iterations[0], len(solutions), solutions


def analyze_failure_reason(perms: List[List[FummelPermutation]], 
                           chosen_rows: List[FummelPermutation]) -> str:
    """
    分析為什麼在某些行找不到有效排列
    """
    if len(chosen_rows) == 0:
        return "第一個行就無法選擇"
    
    last_chosen = chosen_rows[-1]
    row_idx = last_chosen.row
    
    print(f"\n分析行{chr(65+row_idx)}失敗原因:")
    
    # 統計前幾行的列值分佈
    col_values = {}
    for r in range(row_idx):
        perm = chosen_rows[r]
        for c in range(16):
            col_values[(r, c)] = perm.val(c)
    
    # 檢查第一行的影響
    first_perm = chosen_rows[0]
    print(f"  行A排列#0: {[first_perm.val(c) for c in range(16)]}")
    
    # 統計每列被占用的值
    col_used = {c: set() for c in range(16)}
    for r in range(row_idx):
        perm = chosen_rows[r]
        for c in range(16):
            col_used[c].add(perm.val(c))
    
    print(f"\n  各列已被占用的值數量:")
    for c in range(16):
        col_label = list(COL_MAP.keys())[c]
        print(f"    列{col_label}: {len(col_used[c])}個值被占用")
    
    return "分析完成"


if __name__ == "__main__":
    print("=" * 70)
    print("V61 - 符闔排列集合閉合性最終驗證")
    print("=" * 70)
    
    print("""
核心問題：符闔排列集合本身是否閉合？

如果閉合 → 可以不固定任何行，直接從符闔排列中選擇構成16行解
如果不閉合 → 需要重新生成符闔排列，或用戶洞見需要修正
""")
    
    # 載入符闔排列
    print("\n=== 載入符闔排列 ===")
    perms = load_permutations("D:/2026/WPF_Sudoku/Sudoku_256")
    for i in range(16):
        print(f"  行{chr(65+i)}: {len(perms[i]):,}個")
    
    # 測試1：貪婪算法
    print("\n" + "=" * 70)
    print("測試1：貪婪算法 (逐行選擇第一個可行排列)")
    print("=" * 70)
    
    success, chosen, reason = test_closure_by_greedy([p[:] for p in perms])
    print(f"\n結果: {'✓ 找到解' if success else '❌ 無法找到解'}")
    print(f"原因: {reason}")
    
    if success:
        print(f"\n解中使用的排列:")
        for i, perm in enumerate(chosen):
            print(f"  行{chr(65+i)}: #{perm.pid}")
    else:
        # 分析失敗原因
        if chosen:
            analyze_failure_reason(perms, chosen)
    
    # 測試2：回溯搜索
    print("\n" + "=" * 70)
    print("測試2：回溯搜索 (MRV啟發式)")
    print("=" * 70)
    
    iterations, solutions, sol_list = test_closure_by_backtrack([p[:] for p in perms], max_solutions=3)
    
    print(f"\n迭代次數: {iterations:,}")
    print(f"找到的解數: {solutions}")
    
    if solutions > 0:
        print(f"\n✓ 找到了 {solutions} 個解")
        print("  這證明符闔排列集合本身是閉合的！")
    else:
        print(f"\n❌ 無法找到任何解")
        print("  這說明符闔排列集合本身不閉合！")
    
    # 總結
    print("\n" + "=" * 70)
    print("總結：回答用戶問題")
    print("=" * 70)
    
    if success or solutions > 0:
        print("""
【結論】符闔排列集合本身是閉合的！

這驗證了用戶的洞見：
「符闔排列本身已經是滿足包含滿足行約束 列約束 宮約束
三者的各自獨立的鏈式排列解集」

✅ 符闔排列集合可以構成滿足三約束的16行解

【用戶策略的正確性】

用戶說：「如果存在基於首行首宮7 15 3 9序列的固定第3行的解，
那其實不用固定牠行直接運用三者約束規則遍歷256宮即可」

答案：是的！如果符闔排列集合閉合，就可以：
1. 固定C行(第3行)的錨點
2. 其他行從符闔排列集合中選擇
3. 只用列約束和宮約束檢查
4. 不需要固定其他錨點

這確實是「另外一廻事」——比固定92錨點約束弱得多。
""")
    else:
        print("""
【結論】符闔排列集合本身不閉合！

這意味著：
1. 符闔排列的生成規則可能有問題
2. 或者符闔排列需要額外的約束才能閉合

【需要修正的步驟】

用戶的洞見需要修正：
- ✅ 符闔排列本身滿足行約束 (16個值互不相同)
- ❌ 符闔排列集合本身不滿足列約束+宮約束

可能的原因：
1. 符闔排列生成時只考慮了行約束
2. 列約束和宮約束需要額外檢查

【建議】

1. 重新生成符闔排列，加入列約束+宮約束過濾
2. 或者接受用戶的「另外一廻事」——固定C行後搜索更複雜
""")
    
    print("\n" + "=" * 70)
    print("實驗文件")
    print("=" * 70)
    print("  v61_fixed_c_row_search.py - 固定C行搜索")
    print("  v61_c_row_filter_analysis.py - C行過濾分析")
    print("  v61_permutation_set_closure.py - 閉合性驗證")
    print("  v61_final_closure_test.py - 最終驗證 (本文件)")
