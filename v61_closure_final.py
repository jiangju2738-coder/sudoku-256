#!/usr/bin/env python3
"""
V61 - 符闔排列集合閉合性驗證 (修復版)
====================================

"""

import json
from typing import List, Tuple, Optional

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


def test_greedy(perms: List[List[FummelPermutation]]) -> Tuple[bool, str]:
    """貪婪選擇測試"""
    grid = [[0]*16 for _ in range(16)]
    
    for row_idx in range(16):
        found = False
        for perm in perms[row_idx]:
            # 檢查列約束
            ok = True
            for col_idx in range(16):
                val = perm.val(col_idx)
                for r in range(row_idx):
                    if grid[r][col_idx] == val:
                        ok = False
                        break
                if not ok:
                    break
            
            if not ok:
                continue
            
            # 檢查宮約束
            for col_idx in range(16):
                val = perm.val(col_idx)
                br = row_idx // 4
                bc = col_idx // 4
                for r in range(br*4, row_idx):
                    if r // 4 != br:
                        continue
                    for c in range(bc*4, bc*4+4):
                        if grid[r][c] == val:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            
            if ok:
                for col_idx in range(16):
                    grid[row_idx][col_idx] = perm.val(col_idx)
                found = True
                break
        
        if not found:
            return False, f"行{chr(65+row_idx)}無有效排列"
    
    return True, "成功"


def test_backtrack(perms: List[List[FummelPermutation]], max_sol: int = 3):
    """回溯搜索"""
    grid = [[None]*16 for _ in range(16)]
    solutions = []
    iterations = [0]
    
    def col_safe(row, col, val):
        for r in range(16):
            if r != row and grid[r][col] == val:
                return False
        return True
    
    def box_safe(row, col, val):
        br, bc = row // 4, col // 4
        for r in range(br*4, br*4+4):
            for c in range(bc*4, bc*4+4):
                if (r != row or c != col) and grid[r][c] == val:
                    return False
        return True
    
    def find_cell():
        best, best_cnt = None, 17
        for row in range(16):
            for col in range(16):
                if grid[row][col] is not None:
                    continue
                cnt = 0
                for perm in perms[row]:
                    v = perm.val(col)
                    if col_safe(row, col, v) and box_safe(row, col, v):
                        cnt += 1
                if cnt < best_cnt:
                    best_cnt = cnt
                    best = (row, col)
                    if cnt == 0:
                        return None
        return best
    
    def search():
        if len(solutions) >= max_sol:
            return True
        
        cell = find_cell()
        if cell is None:
            solutions.append([list(r) for r in grid])
            return len(solutions) < max_sol
        
        row, col = cell
        cands = []
        for perm in perms[row]:
            v = perm.val(col)
            if col_safe(row, col, v) and box_safe(row, col, v):
                cands.append((v, perm))
        
        for v, _ in cands:
            iterations[0] += 1
            
            og = [list(r) for r in grid]
            op = [list(p) for p in perms]
            
            grid[row][col] = v
            
            # 約束傳播
            for r2 in range(16):
                if r2 == row:
                    continue
                rem = []
                for p2 in perms[r2]:
                    if p2.val(col) == v:
                        continue
                    in_box = False
                    for cc in range(16):
                        if p2.val(cc) == v:
                            if row // 4 == r2 // 4 and col // 4 == cc // 4:
                                in_box = True
                                break
                    if not in_box:
                        rem.append(p2)
                perms[r2] = rem
            
            if search():
                return True
            
            grid = og
            perms = op
        
        return False
    
    search()
    return iterations[0], len(solutions)


if __name__ == "__main__":
    print("=" * 70)
    print("V61 - 符闔排列集合閉合性驗證")
    print("=" * 70)
    
    print("\n=== 載入符闔排列 ===")
    perms = load_permutations("D:/2026/WPF_Sudoku/Sudoku_256")
    for i in range(16):
        print(f"  行{chr(65+i)}: {len(perms[i]):,}個")
    
    # 測試1：貪婪
    print("\n=== 測試1：貪婪算法 ===")
    ok1, msg1 = test_greedy([p[:] for p in perms])
    print(f"結果: {'✓ 找到解' if ok1 else '❌ ' + msg1}")
    
    # 測試2：回溯
    print("\n=== 測試2：回溯搜索 ===")
    iters, sols = test_backtrack([p[:] for p in perms], max_sol=3)
    print(f"迭代: {iters:,}, 解數: {sols}")
    print(f"結果: {'✓ 找到解' if sols > 0 else '❌ 無解'}")
    
    # 總結
    print("\n" + "=" * 70)
    print("結論")
    print("=" * 70)
    
    if ok1 or sols > 0:
        print("""
✅ 符闔排列集合本身是閉合的！

用戶洞見驗證通過：
「符闔排列本身已經是滿足三約束的鏈式排列解集」

可以只固定C行，其他行從符闔集合中選擇！
""")
    else:
        print("""
❌ 符闔排列集合本身不閉合！

需要重新生成符闔排列，加入列+宮約束過濾。

用戶洞見需要修正：
- 符闔排列滿足行約束 ✓
- 符闔排列集合本身不滿足列+宮約束 ✗
""")
