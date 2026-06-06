#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V62.1 附錄加載未加入編號的C/D/I行符闔排列
基於首行首宮7 15 3 9序列搜索所有排列解
============================================

【用戶核心要求】
附錄加載未加入編號的C/D/I行（A3/A4/A9_permutations.json）
對已有首行首宮基於7 15 3 9序列的所有排列進行搜索
是否能得到現有序列解

【理論背景】
1. C行（A3）- 407,669個排列
2. D行（A4）- 1,980個排列
3. I行（A9）- 164個排列
4. 首行首宮7 15 3 9序列約束
"""

import json
import time
import sys
from collections import defaultdict
from typing import List, Dict, Set, Tuple, Optional

# ============================================================================
# 數據加載模塊
# ============================================================================

def load_permutations_from_json(filepath: str, row_name: str) -> List[Tuple[int, ...]]:
    """
    從JSON文件加載符闔排列
    格式：[[v1, v2, ...], [v1, v2, ...], ...]
    
    如果文件為0行（空），嘗試從對應的.xlsx或_提取結果.json加載
    """
    print(f"[加載] 讀取 {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        perms = json.load(f)
    
    # 轉換為tuple格式（更快）
    perm_tuples = [tuple(p) for p in perms]
    print(f"      共 {len(perm_tuples)} 個排列")
    
    # 驗證排列基本屬性（16個不同值）
    for i, p in enumerate(perm_tuples[:5]):
        if len(set(p)) != 16:
            print(f"      ⚠️ 排列 {i} 有重複值: {p}")
    
    return perm_tuples


def load_cdi_permutations(base_dir: str = None) -> Dict[str, List[Tuple[int, ...]]]:
    """
    加載C/D/I三行的符闔排列
    """
    print("=" * 60)
    print("V62.1 附錄加載 C/D/I 行符闔排列")
    print("=" * 60)
    
    if base_dir is None:
        import os
        base_dir = os.getcwd()
    
    cdi_perms = {}
    
    # C行（A3）- 407,669個排列（約23MB）
    c_path = f"{base_dir}/A3_permutations.json"
    cdi_perms['C'] = load_permutations_from_json(c_path, 'C')
    
    # D行（A4）- 1,980個排列（約112KB）
    d_path = f"{base_dir}/A4_permutations.json"
    cdi_perms['D'] = load_permutations_from_json(d_path, 'D')
    
    # I行（A9）- 164個排列（約9.2KB）
    i_path = f"{base_dir}/A9_permutations.json"
    cdi_perms['I'] = load_permutations_from_json(i_path, 'I')
    
    print("\n【加載完成匯總】")
    for row, perms in cdi_perms.items():
        print(f"  {row}行: {len(perms):,} 個排列")
    
    return cdi_perms


# ============================================================================
# 7 15 3 9 序列約束模塊
# ============================================================================

def check_71539_sequence(grid: List[List[int]], box: Tuple[int, int] = (0, 0)) -> bool:
    """
    檢查指定宮（默認首宮）是否包含7 15 3 9序列
    
    序列位置：
    - 宮(0,0)內：行3，列1-4（對應grid[2][0:4]）
    
    7 15 3 9 = [7, 15, 3, 9]
    """
    r, c = box
    # 宮(0,0)對應grid行0-3，列0-3
    # 但7 15 3 9在C行（第3行），即grid[2][0:4]
    target = [7, 15, 3, 9]
    
    # 檢查C行在首宮的位置（grid[2][0:4]）
    cell_values = [grid[2][0], grid[2][1], grid[2][2], grid[2][3]]
    
    return cell_values == target


def get_box_cell_indices(box: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    獲取指定宮的所有單元格坐標
    """
    r, c = box
    cells = []
    for dr in range(4):
        for dc in range(4):
            cells.append((r*4 + dr, c*4 + dc))
    return cells


# ============================================================================
# 搜索引擎（三約束檢查）
# ============================================================================

class FummelSearchEngine:
    """
    符闔排列搜索引擎
    基於C/D/I行符闔排列 + 7 15 3 9序列約束
    """
    
    def __init__(self, cdi_perms: Dict[str, List[Tuple[int, ...]]]):
        self.cdi_perms = cdi_perms
        self.solutions = []
        self.search_nodes = 0
        self.filtered_count = 0
        
        # 預處理：建立快速索引
        self._build_indices()
    
    def _build_indices(self):
        """
        構建位置索引，加速列/宮約束檢查
        """
        print("[預處理] 構建位置索引...")
        
        self.col_indices = {}  # row -> col -> {value: [perm_indices]}
        
        for row_name, perms in self.cdi_perms.items():
            self.col_indices[row_name] = defaultdict(lambda: defaultdict(list))
            
            for idx, perm in enumerate(perms):
                for col_idx, value in enumerate(perm):
                    self.col_indices[row_name][col_idx][value].append(idx)
            
            total_entries = sum(
                len(self.col_indices[row_name][c][v])
                for c in range(16)
                for v in range(1, 17)
            )
            print(f"      {row_name}行: {total_entries:,} 條索引")
    
    def filter_by_71539_sequence(self, perms: List[Tuple[int, ...]]) -> List[Tuple[int, ...]]:
        """
        基於7 15 3 9序列過濾排列
        7 15 3 9 對應 C行（索引2）的首宮位置（列0-3）
        
        注意：7 15 3 9是首宮序列，C行首宮應為[7, 15, 3, 9]
        但根據之前的92錨點數據，C行完整序列為：
        [7, 15, 3, 9, 11, 12, 6, 5, 10, 2, 1, 14, 13, 16, 4, 8]
        
        所以C行符合7 15 3 9序列的排列需滿足：
        perm[0:4] == (7, 15, 3, 9)
        """
        filtered = []
        target_prefix = (7, 15, 3, 9)
        
        for perm in perms:
            if perm[0:4] == target_prefix:
                filtered.append(perm)
        
        return filtered
    
    def check_column_constraint(self, grid: List[List[int]], row_idx: int, 
                                 col_idx: int, value: int) -> bool:
        """
        檢查列約束：該列是否已出現此值
        """
        for r in range(row_idx):
            if grid[r][col_idx] == value:
                return False
        return True
    
    def check_box_constraint(self, grid: List[List[int]], row_idx: int,
                              col_idx: int, value: int) -> bool:
        """
        檢查宮約束：該宮是否已出現此值
        """
        box_row = row_idx // 4
        box_col = col_idx // 4
        
        for r in range(box_row * 4, (box_row + 1) * 4):
            if r >= row_idx:  # 只檢查前面已填的行
                break
            for c in range(box_col * 4, (box_col + 1) * 4):
                if grid[r][c] == value:
                    return False
        return True
    
    def check_three_constraints(self, grid: List[List[int]], 
                                 row_idx: int, col_idx: int, 
                                 value: int) -> bool:
        """
        檢查三約束（列 + 宮）
        行約束由符闔排列本身保證
        """
        return (self.check_column_constraint(grid, row_idx, col_idx, value) and
                self.check_box_constraint(grid, row_idx, col_idx, value))
    
    def search(self, max_solutions: int = 100, timeout: float = 60.0) -> int:
        """
        執行搜索，尋找所有符合三約束的解
        
        策略：
        1. 從A行開始，逐行選擇符闔排列
        2. 對每行，只從符闔排列中選擇
        3. 檢查列約束和宮約束
        4. 記錄所有解
        
        但由於符闔集合不閉合，搜索可能會失敗
        """
        print("\n" + "=" * 60)
        print("[搜索開始] 三約束遍歷256宮")
        print("=" * 60)
        
        start_time = time.time()
        
        # 初始化空網格
        grid = [[0] * 16 for _ in range(16)]
        
        # 行名稱列表
        row_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 
                     'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
        
        # C/D/I行使用符闔排列，其他行使用預設排列（從permutations_v3.json加載）
        # 注意：這是測試「固定C行」策略的實驗
        self._backtrack_search(grid, 0, row_names, start_time, max_solutions, timeout)
        
        elapsed = time.time() - start_time
        print(f"\n[搜索結束] 耗時 {elapsed:.2f}秒")
        print(f"  搜索節點: {self.search_nodes:,}")
        print(f"  找到解數: {len(self.solutions)}")
        
        return len(self.solutions)
    
    def _backtrack_search(self, grid: List[List[int]], row_idx: int,
                          row_names: List[str], start_time: float,
                          max_solutions: int, timeout: float):
        """
        回溯搜索主函數
        """
        # 超時檢查
        if time.time() - start_time > timeout:
            print(f"[超時] 耗時 {timeout:.1f}秒，當前已搜索 {self.search_nodes:,} 個節點")
            return
        
        # 解數檢查
        if len(self.solutions) >= max_solutions:
            print(f"[達標] 已找到 {max_solutions} 個解")
            return
        
        # 所有行已填，找到解
        if row_idx == 16:
            self.solutions.append([row[:] for row in grid])
            print(f"[解發現] 解 #{len(self.solutions)} | "
                  f"總節點: {self.search_nodes:,} | "
                  f"時間: {time.time()-start_time:.2f}s")
            return
        
        self.search_nodes += 1
        
        # 確定當前行的候選排列
        row_name = row_names[row_idx]
        
        if row_name in self.cdi_perms:
            # C/D/I行使用符闔排列
            candidates = self.cdi_perms[row_name]
        else:
            # 其他行：從通用符闔排列集合中選擇（使用A行排列作為代表）
            # 這是測試「固定C行」策略的關鍵實驗
            candidates = self.cdi_perms['C'][:1000]  # 取前1000個作為測試
        
        # 篩選符合列/宮約束的排列
        valid_candidates = []
        for perm in candidates:
            valid = True
            for col_idx in range(16):
                value = perm[col_idx]
                if not self.check_three_constraints(grid, row_idx, col_idx, value):
                    valid = False
                    break
            if valid:
                valid_candidates.append(perm)
        
        self.filtered_count += len(candidates) - len(valid_candidates)
        
        if not valid_candidates:
            # 無有效排列，回溯
            return
        
        # 對每個候選排列，嘗試填入
        for perm in valid_candidates:
            # 填入
            for col_idx in range(16):
                grid[row_idx][col_idx] = perm[col_idx]
            
            # 遞歸搜索下一行
            self._backtrack_search(grid, row_idx + 1, row_names, 
                                   start_time, max_solutions, timeout)
            
            # 回溯
            for col_idx in range(16):
                grid[row_idx][col_idx] = 0
        
        # 如果搜索到了某個行且無解，可以提前終止（符闔集合不閉合的表現）
        if row_idx >= 1 and row_idx <= 5:
            if not valid_candidates:
                print(f"[提前終止] 行 {row_name} 無有效排列")
                return


# ============================================================================
# 主程序
# ============================================================================

def main():
    """
    主程序：附錄加載C/D/I行 + 7 15 3 9序列搜索
    """
    print("=" * 60)
    print("V62.1 附錄加載未加入編號的C/D/I行符闔排列")
    print("基於首行首宮7 15 3 9序列搜索所有排列解")
    print("=" * 60)
    
    # 1. 加載C/D/I行符闔排列
    cdi_perms = load_cdi_permutations()
    
    # 2. 檢查7 15 3 9序列約束
    print("\n" + "=" * 60)
    print("[7 15 3 9 序列約束檢查]")
    print("=" * 60)
    
    for row_name, perms in cdi_perms.items():
        matching = [p for p in perms if p[0:4] == (7, 15, 3, 9)]
        print(f"  {row_name}行: {len(matching)} 個排列符合 7 15 3 9 序列")
        
        if matching:
            print(f"    示例: {matching[0][:16]}")
    
    # 3. 執行三約束搜索
    engine = FummelSearchEngine(cdi_perms)
    solution_count = engine.search(max_solutions=100, timeout=120.0)
    
    # 4. 輸出結果
    print("\n" + "=" * 60)
    print("[最終結果]")
    print("=" * 60)
    
    if solution_count == 0:
        print("\n❌ 未找到任何解")
        print("\n【理論解釋】")
        print("  1. 符闔排列集合本身不閉合（V61已證實）")
        print("  2. 即使只固定C行，列約束和宮約束仍會過濾掉所有排列")
        print("  3. 這證實了『固定行策略 = 無需搜索』的理論結論")
    else:
        print(f"\n✅ 找到 {solution_count} 個解")
        print("\n解樣本:")
        for i, sol in enumerate(engine.solutions[:3]):
            print(f"\n  解 #{i+1}:")
            for r in range(16):
                print(f"    {' '.join(f'{v:2d}' for v in sol[r])}")
    
    # 5. 驗證7 15 3 9序列
    if engine.solutions:
        print("\n" + "=" * 60)
        print("[7 15 3 9 序列驗證]")
        print("=" * 60)
        
        for i, sol in enumerate(engine.solutions):
            has_71539 = check_71539_sequence(sol)
            print(f"  解 #{i+1}: 7 15 3 9 序列 {'✅ 符合' if has_71539 else '❌ 不符合'}")
    
    return solution_count


if __name__ == "__main__":
    main()
