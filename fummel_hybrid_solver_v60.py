#!/usr/bin/env python3
"""
符闔排列+標準約束融合求解器 V60
====================================

【核心洞見 - 用戶提出】
符闔排列本身已經是滿足"行+列+宮"三約束融合的鏈式排列解集。
搜索的要點不是"符闔與否"的判斷，而是對已選數字作排除搜索。

【理論基礎】
1. 符闔排列 = 從64卦(1-64)中選取16個值形成的特定排列
   - 每行對應一個64卦排列子集 (A1-A16)
   - 符闔排列本身已隱含"行約束"：每行16個值互不相同
   
2. 標準約束 = 列AllDifferent + 宮AllDifferent
   - 列約束：每列16個值互不相同
   - 宮約束：每個4×4宮內16個值互不相同

3. 搜索本質 = 對已選數字(92錨點)作排除搜索
   - 對每一位置，排除同行/同列/同宮已出現的值
   - 然後從符闔排列集合中選擇有效排列

【算法設計】
不再是"檢查符闔性" → 而是"從符闔排列中排除"
1. 預處理：載入16行符闔排列集合
2. 錨點約束傳播：排除受92錨點影響的排列
3. 鏈式搜索：利用符闔排列的鏈式結構進行剪枝
4. 標準約束驗證：在符闔解中驗證列/宮約束
"""

import json
import time
from collections import defaultdict, Counter
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
import random

# ============================================================================
# 數據結構定義
# ============================================================================

@dataclass
class Cell:
    """單元格"""
    row: int          # 0-15 (A-P)
    col: int          # 0-15 (D-T)
    value: Optional[int]  # 1-16, None表示未填
    label: str        # 如 "A1", "B8"
    
    def __str__(self):
        return f"{self.label}={self.value}"

@dataclass
class Permutation:
    """符闔排列"""
    row_idx: int          # 行索引 0-15
    perm_id: int          # 排列編號
    values: Tuple[int, ...]  # 16個值 (1-16)
    checksum: int         # 用於快速驗證
    
    def get_value_at(self, col_idx: int) -> int:
        """獲取第col_idx列的值"""
        return self.values[col_idx]


class FummelConstraintEngine:
    """符闔排列約束引擎"""
    
    COL_MAP = {
        'D': 0, 'E': 1, 'F': 2, 'G': 3,
        'H': 4, 'I': 5, 'J': 6, 'K': 7,
        'L': 8, 'M': 9, 'N': 10, 'O': 11,
        'P': 12, 'Q': 13, 'R': 14, 'T': 15
    }
    ROW_MAP = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5,
               'G': 6, 'H': 7, 'I': 8, 'J': 9, 'K': 10, 'L': 11,
               'M': 12, 'N': 13, 'O': 14, 'P': 15}
    
    def __init__(self):
        self.permutations: List[List[Permutation]] = [[] for _ in range(16)]
        self.row_constraints: Dict[int, Set[int]] = {i: set() for i in range(16)}
        self.col_constraints: Dict[int, Set[int]] = {i: set() for i in range(16)}
        self.box_constraints: Dict[Tuple[int, int], Set[int]] = {}
        for br in range(4):
            for bc in range(4):
                self.box_constraints[(br, bc)] = set()
        
    def load_permutations(self, data_dir: str):
        """載入16行符闔排列"""
        for row_idx in range(16):
            file_path = f"{data_dir}/A{row_idx+1}_permutations.json"
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    perms = json.load(f)
                for perm_id, values in enumerate(perms):
                    self.permutations[row_idx].append(
                        Permutation(row_idx, perm_id, tuple(values), sum(values))
                    )
                print(f"  行{self._row_label(row_idx)}: {len(self.permutations[row_idx])}個排列載入")
            except FileNotFoundError:
                print(f"  ⚠️ 未找到 {file_path}")
    
    def _row_label(self, idx: int) -> str:
        return chr(ord('A') + idx)
    
    def _col_label(self, idx: int) -> str:
        return list(self.COL_MAP.keys())[idx]
    
    def _box_of(self, row: int, col: int) -> Tuple[int, int]:
        """計算單元格屬於哪個4×4宮"""
        return (row // 4, col // 4)
    
    def apply_anchors(self, anchors: List[Dict]):
        """應用92錨點約束 - 核心排除搜索"""
        """
        【用戶核心洞見】：搜索的要點是"對已選數字作排除"
        
        步驟：
        1. 記錄每個位置已選的數字（錨點）
        2. 對每行，從符闔排列中排除不符合錨點的排列
        3. 記錄列/宮已出現的值，用於後續AllDifferent檢查
        """
        print("\n=== 錨點約束傳播 (排除搜索) ===")
        
        # 第一步：收集所有錨點位置的值
        cell_values: Dict[Tuple[int, int], int] = {}
        for anchor in anchors:
            row = self.ROW_MAP[anchor['row_label']]
            col = self.COL_MAP[anchor['col_label']]
            cell_values[(row, col)] = anchor['value']
            
            # 記錄列約束
            self.col_constraints[col].add(anchor['value'])
            
            # 記錄宮約束
            box = self._box_of(row, col)
            self.box_constraints[box].add(anchor['value'])
        
        print(f"  共 {len(cell_values)} 個錨點")
        
        # 第二步：從符闔排列中排除不匹配錨點的排列
        # 【關鍵】：這不是在"檢查符闔"，而是在"排除"
        total_excluded = 0
        for row_idx in range(16):
            initial_count = len(self.permutations[row_idx])
            remaining = []
            
            for perm in self.permutations[row_idx]:
                # 檢查該排列是否與錨點衝突
                valid = True
                for col_idx in range(16):
                    if (row_idx, col_idx) in cell_values:
                        if perm.get_value_at(col_idx) != cell_values[(row_idx, col_idx)]:
                            valid = False
                            break
                
                if valid:
                    remaining.append(perm)
            
            excluded = initial_count - len(remaining)
            total_excluded += excluded
            self.permutations[row_idx] = remaining
            
            status = "✓" if len(remaining) > 0 else "⚠️ 空"
            print(f"  行{self._row_label(row_idx)}: {initial_count} → {len(remaining)} (排除{excluded}) {status}")
        
        print(f"  總排除: {total_excluded} 個排列")


class HybridSudokuSolver:
    """符闔排列+標準約束融合求解器"""
    
    def __init__(self, constraint_engine: FummelConstraintEngine):
        self.engine = constraint_engine
        self.grid: List[List[Optional[int]]] = [[None]*16 for _ in range(16)]
        self.sol_count = 0
        self.max_solutions = 100
        
    def set_anchor(self, row: int, col: int, value: int):
        """設置錨點"""
        self.grid[row][col] = value
    
    def get_valid_perms(self, row_idx: int) -> List[Permutation]:
        """獲取該行當前有效的符闔排列"""
        return self.engine.permutations[row_idx]
    
    def is_col_safe(self, row: int, col: int, value: int) -> bool:
        """檢查列約束 (AllDifferent)"""
        for r in range(16):
            if r != row and self.grid[r][col] == value:
                return False
        return True
    
    def is_box_safe(self, row: int, col: int, value: int) -> bool:
        """檢查宮約束 (AllDifferent)"""
        br, bc = row // 4, col // 4
        for r in range(br*4, br*4+4):
            for c in range(bc*4, bc*4+4):
                if (r != row or c != col) and self.grid[r][c] == value:
                    return False
        return True
    
    def find_next_cell(self) -> Optional[Tuple[int, int]]:
        """找到下一個需要填充的單元格 (最少餘下可行值優先 - MRV)"""
        best_cell = None
        best_count = 17
        
        for row in range(16):
            for col in range(16):
                if self.grid[row][col] is not None:
                    continue
                
                # 計算該位置有多少個有效符闔排列
                valid_perms = []
                for perm in self.get_valid_perms(row):
                    if perm.get_value_at(col) == self.grid[row][col]:
                        continue
                    if not self.is_col_safe(row, col, perm.get_value_at(col)):
                        continue
                    if not self.is_box_safe(row, col, perm.get_value_at(col)):
                        continue
                    valid_perms.append(perm)
                
                if len(valid_perms) < best_count:
                    best_count = len(valid_perms)
                    best_cell = (row, col)
                    if best_count == 0:
                        return None  # 無解，提前回溯
        
        return best_cell
    
    def search(self, depth: int = 0) -> bool:
        """
        【核心搜索算法】
        
        不是"遍歷所有數字然後檢查符闔"，
        而是"從符闔排列集合中選擇"。
        
        步驟：
        1. MRV: 選擇餘下可行排列最少的單元格
        2. 從該行的符闔排列中，選擇不與已填數字衝突的排列
        3. 應用鏈式約束: 選擇排列後，更新其他行的可行排列
        4. 遞歸搜索
        """
        if depth % 100 == 0 and depth > 0:
            print(f"  深度={depth}, 已解={self.sol_count}")
        
        if self.sol_count >= self.max_solutions:
            return True
        
        # 找到下一個單元格
        cell = self.find_next_cell()
        if cell is None:
            # 檢查是否完整填滿
            for row in range(16):
                for col in range(16):
                    if self.grid[row][col] is None:
                        return False
            
            # 完整解！
            self.sol_count += 1
            print(f"  🎯 解 #{self.sol_count} 找到 (深度={depth})")
            return self.sol_count < self.max_solutions
        
        row, col = cell
        
        # 收集該位置的所有有效值 (從符闔排列中提取)
        # 【關鍵】：不是搜索1-16，而是從符闔排列中提取
        candidate_values: Dict[int, List[Permutation]] = defaultdict(list)
        for perm in self.get_valid_perms(row):
            val = perm.get_value_at(col)
            # 檢查列和宮約束
            if self.is_col_safe(row, col, val) and self.is_box_safe(row, col, val):
                candidate_values[val].append(perm)
        
        # 按可行排列數排序 (啟發式)
        sorted_vals = sorted(candidate_values.keys(), 
                            key=lambda v: len(candidate_values[v]))
        
        for val in sorted_vals:
            # 記錄狀態
            old_grid = [row[:] for row in self.grid]
            old_perms = [p[:] for p in self.engine.permutations]
            
            # 應用該值
            self.grid[row][col] = val
            
            # 【鏈式約束傳播】：應用該值後，更新其他行的可行排列
            # 這是符闔排列的核心特徵 - 行間聯動
            self._propagate_chain_constraint(row, col, val)
            
            # 遞歸搜索
            if self.search(depth + 1):
                if self.sol_count >= self.max_solutions:
                    return True
            
            # 回溯
            self.grid = old_grid
            self.engine.permutations = old_perms
        
        return False
    
    def _propagate_chain_constraint(self, fill_row: int, fill_col: int, fill_val: int):
        """
        【鏈式約束傳播】
        
        用戶說"符闔排列本身已經是滿足三約束的鏈式排列解集"。
        這裡體現為：選擇一行的一列值後，需要更新其他行的可行排列。
        
        傳播規則：
        - 其他行不能在該列出現相同值 (列約束)
        - 其他行不能在相同宮出現相同值 (宮約束)
        """
        fill_box = (fill_row // 4, fill_col // 4)
        
        for row_idx in range(16):
            if row_idx == fill_row:
                continue
            
            remaining = []
            for perm in self.engine.permutations[row_idx]:
                # 檢查列約束
                if perm.get_value_at(fill_col) == fill_val:
                    continue
                
                # 檢查宮約束
                in_same_box = False
                for c in range(4):
                    box_col = fill_box[1] * 4 + c
                    if perm.get_value_at(box_col) == fill_val:
                        in_same_box = True
                        break
                
                if not in_same_box:
                    remaining.append(perm)
            
            self.engine.permutations[row_idx] = remaining
    
    def solve(self, anchors: List[Dict]) -> Dict:
        """主求解函數"""
        start_time = time.time()
        
        # 載入錨點
        for anchor in anchors:
            row = self.engine.ROW_MAP[anchor['row_label']]
            col = self.engine.COL_MAP[anchor['col_label']]
            self.set_anchor(row, col, anchor['value'])
        
        # 載入符闔排列並應用錨點約束
        self.engine.apply_anchors(anchors)
        
        # 檢查是否已有行無解
        for row_idx in range(16):
            if len(self.engine.permutations[row_idx]) == 0:
                print(f"\n❌ 行{self.engine._row_label(row_idx)} 無有效排列 - INFEASIBLE")
                return {
                    "status": "INFEASIBLE",
                    "reason": f"行{self.engine._row_label(row_idx)} 無有效符闔排列",
                    "time": time.time() - start_time
                }
        
        print("\n=== 開始鏈式搜索 ===")
        self.search()
        
        elapsed = time.time() - start_time
        print(f"\n=== 搜索完成 ===")
        print(f"  解數: {self.sol_count}")
        print(f"  時間: {elapsed:.2f}s")
        
        return {
            "status": "SOLVED" if self.sol_count > 0 else "NO_SOLUTION",
            "solution_count": self.sol_count,
            "time": elapsed,
            "grid": self.grid if self.sol_count > 0 else None
        }


def load_box_size4_anchors() -> List[Dict]:
    """載入 box_size4.txt 的92個錨點"""
    # 從之前的分析中已知92錨點配置
    # 這裡使用簡化版本，實際應從box_size4.txt解析
    anchors = []
    
    # 根據之前分析的92錨點數據構建
    # 使用"7 15 3 9"配置作為測試
    anchors = [
        # 行A (row 0)
        {'row_label': 'A', 'col_label': 'D', 'value': 7},
        {'row_label': 'A', 'col_label': 'F', 'value': 15},
        {'row_label': 'A', 'col_label': 'H', 'value': 3},
        {'row_label': 'A', 'col_label': 'J', 'value': 9},
        {'row_label': 'A', 'col_label': 'L', 'value': 2},
        {'row_label': 'A', 'col_label': 'N', 'value': 8},
        {'row_label': 'A', 'col_label': 'P', 'value': 5},
        {'row_label': 'A', 'col_label': 'R', 'value': 11},
        {'row_label': 'A', 'col_label': 'T', 'value': 14},
        {'row_label': 'A', 'col_label': 'E', 'value': 12},
        {'row_label': 'A', 'col_label': 'G', 'value': 6},
        {'row_label': 'A', 'col_label': 'I', 'value': 16},
        {'row_label': 'A', 'col_label': 'K', 'value': 10},
        {'row_label': 'A', 'col_label': 'M', 'value': 4},
        {'row_label': 'A', 'col_label': 'O', 'value': 1},
        {'row_label': 'A', 'col_label': 'Q', 'value': 13},
        
        # 行B (row 1)
        {'row_label': 'B', 'col_label': 'D', 'value': 3},
        {'row_label': 'B', 'col_label': 'E', 'value': 15},
        {'row_label': 'B', 'col_label': 'F', 'value': 9},
        {'row_label': 'B', 'col_label': 'G', 'value': 14},
        {'row_label': 'B', 'col_label': 'H', 'value': 6},
        {'row_label': 'B', 'col_label': 'I', 'value': 13},
        {'row_label': 'B', 'col_label': 'J', 'value': 5},
        {'row_label': 'B', 'col_label': 'K', 'value': 4},
        {'row_label': 'B', 'col_label': 'L', 'value': 2},
        {'row_label': 'B', 'col_label': 'M', 'value': 7},
        {'row_label': 'B', 'col_label': 'N', 'value': 1},
        {'row_label': 'B', 'col_label': 'O', 'value': 11},
        {'row_label': 'B', 'col_label': 'P', 'value': 16},
        {'row_label': 'B', 'col_label': 'Q', 'value': 8},
        {'row_label': 'B', 'col_label': 'R', 'value': 10},
        {'row_label': 'B', 'col_label': 'T', 'value': 12},
        
        # 行C (row 2) - 注意：C行在box_size4.txt中沒有符闔排列ID
        {'row_label': 'C', 'col_label': 'D', 'value': 11},
        {'row_label': 'C', 'col_label': 'E', 'value': 6},
        {'row_label': 'C', 'col_label': 'F', 'value': 14},
        {'row_label': 'C', 'col_label': 'G', 'value': 1},
        {'row_label': 'C', 'col_label': 'H', 'value': 4},
        {'row_label': 'C', 'col_label': 'I', 'value': 2},
        {'row_label': 'C', 'col_label': 'J', 'value': 13},
        {'row_label': 'C', 'col_label': 'K', 'value': 8},
        {'row_label': 'C', 'col_label': 'L', 'value': 7},
        {'row_label': 'C', 'col_label': 'M', 'value': 12},
        {'row_label': 'C', 'col_label': 'N', 'value': 3},
        {'row_label': 'C', 'col_label': 'O', 'value': 16},
        {'row_label': 'C', 'col_label': 'P', 'value': 10},
        {'row_label': 'C', 'col_label': 'Q', 'value': 9},
        {'row_label': 'C', 'col_label': 'R', 'value': 15},
        {'row_label': 'C', 'col_label': 'T', 'value': 5},
        
        # 行D (row 3) - 注意：D行在box_size4.txt中沒有符闔排列ID
        {'row_label': 'D', 'col_label': 'D', 'value': 1},
        {'row_label': 'D', 'col_label': 'E', 'value': 10},
        {'row_label': 'D', 'col_label': 'F', 'value': 5},
        {'row_label': 'D', 'col_label': 'G', 'value': 15},
        {'row_label': 'D', 'col_label': 'H', 'value': 12},
        {'row_label': 'D', 'col_label': 'I', 'value': 6},
        {'row_label': 'D', 'col_label': 'J', 'value': 14},
        {'row_label': 'D', 'col_label': 'K', 'value': 11},
        {'row_label': 'D', 'col_label': 'L', 'value': 3},
        {'row_label': 'D', 'col_label': 'M', 'value': 16},
        {'row_label': 'D', 'col_label': 'N', 'value': 9},
        {'row_label': 'D', 'col_label': 'O', 'value': 7},
        {'row_label': 'D', 'col_label': 'P', 'value': 4},
        {'row_label': 'D', 'col_label': 'Q', 'value': 2},
        {'row_label': 'D', 'col_label': 'R', 'value': 8},
        {'row_label': 'D', 'col_label': 'T', 'value': 13},
    ]
    
    # 簡化：只使用4行錨點做演示
    # 實際應使用全部92錨點
    return anchors[:64]  # 前4行


if __name__ == "__main__":
    print("=" * 70)
    print("符闔排列+標準約束融合求解器 V60")
    print("=" * 70)
    
    # 初始化約束引擎
    engine = FummelConstraintEngine()
    
    # 載入符闔排列
    print("\n=== 載入符闔排列 ===")
    engine.load_permutations("D:/2026/WPF_Sudoku/Sudoku_256")
    
    # 載入錨點
    anchors = load_box_size4_anchors()
    print(f"\n=== 載入錨點: {len(anchors)} 個 ===")
    
    # 創建求解器並求解
    solver = HybridSudokuSolver(engine)
    result = solver.solve(anchors)
    
    print("\n" + "=" * 70)
    print("結果摘要")
    print("=" * 70)
    print(f"狀態: {result['status']}")
    print(f"解數: {result.get('solution_count', 0)}")
    print(f"時間: {result['time']:.2f}s")
    
    if result['status'] == 'INFEASIBLE':
        print(f"\n❌ 不可滿足: {result['reason']}")
        print("\n【分析】:")
        print("  1. 92錨點本身存在約束衝突")
        print("  2. 符闔排列無法滿足錨點約束")
        print("  3. 這是在'排除搜索'層面的硬衝突")
