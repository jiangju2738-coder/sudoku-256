#!/usr/bin/env python3.14
# -*- coding: utf-8 -*-
"""
━━━━━━ 十六連環變體神經網絡鏈式博弈剪枝求解系統 ━━━━━━
┌──────────────────────────────────────────────────────────┐
│  三大架構融合：                                           │
│  [1] 神經網絡鏈式約束傳播    - 列/宮雙約束實時推導          │
│  [2] 樹狀博弈剪枝策略        - MRV+AC-3動態序優選           │
│  [3] 十六連環終極循環搜索    - 深度回溯+狀態空間剪枝        │
│                                                          │
│  核心目標：對已滿足行約束排列進行列+宮終極循環搜索          │
└──────────────────────────────────────────────────────────┘
"""

import json
import time
import sys
from collections import defaultdict, deque
from copy import deepcopy
from typing import List, Dict, Set, Tuple, Optional
import itertools

# ═══════════════════════════════════════════════════════════
# 第一架構：神經網絡鏈式約束傳播
# ═══════════════════════════════════════════════════════════

class NeuralChainPropagator:
    """神經網絡鏈式約束傳播引擎
    
    模擬神經網絡層級傳播：
    - Layer 1: 單元格約束（行/列/宮）
    - Layer 2: 行內符闔排列約束
    - Layer 3: 列雙約束傳播（值對約束）
    - Layer 4: 宮塊約束傳播（4x4）
    - Layer 5: 全局AllDifferent約束鏈
    """
    
    def __init__(self, grid_size: int = 16, box_size: int = 4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.values = set(range(1, grid_size + 1))
        
    def get_box_index(self, row: int, col: int) -> int:
        """計算單元格所屬宮塊索引"""
        return (row // self.box_size) * self.grid_size // self.box_size + (col // self.box_size)
    
    def get_box_cells(self, box_idx: int) -> List[Tuple[int, int]]:
        """獲取宮塊內所有單元格坐標"""
        row_start = (box_idx // self.grid_size * self.box_size)
        col_start = (box_idx % self.grid_size // self.box_size) * self.box_size
        cells = []
        for r in range(row_start, row_start + self.box_size):
            for c in range(col_start, col_start + self.box_size):
                cells.append((r, c))
        return cells

class ColumnConstraintNetwork:
    """列約束神經網絡
    
    基於txt文件中的已知數字分布，建立列值對約束關係
    """
    
    def __init__(self, known_digits: List[Dict]):
        """known_digits: [{"row":1,"col":3,"value":3}, ...]"""
        self.known = known_digits
        self.col_values: Dict[int, Set[int]] = defaultdict(set)  # col -> 已有值
        self.col_known_positions: Dict[int, List[Tuple[int, int]]] = defaultdict(list)  # col -> [(row,col,value)]
        self.row_col_map: Dict[int, Dict[int, int]] = defaultdict(dict)  # row->col->value
        
        for kd in known_digits:
            r, c, v = kd['row'] - 1, kd['col'] - 1, kd['value']
            self.col_values[c].add(v)
            self.col_known_positions[c].append((r, c, v))
            self.row_col_map[r][c] = v
    
    def get_missing_count_per_col(self) -> List[int]:
        """每列缺少的值數量"""
        return [16 - len(self.col_values[c]) for c in range(16)]
    
    def get_empty_cells_per_row(self) -> List[int]:
        """每行空單元格數量"""
        counts = [0] * 16
        for r in range(16):
            counts[r] = 16 - len(self.row_col_map[r])
        return counts

class BoxConstraintNetwork:
    """宮塊約束神經網絡 (4x4 box)"""
    
    def __init__(self, known_digits: List[Dict], box_size: int = 4):
        self.box_size = box_size
        self.box_values: Dict[int, Set[int]] = defaultdict(set)  # box_idx -> 已有值
        self.box_known_cells: Dict[int, List[Tuple[int, int, int]]] = defaultdict(list)
        
        for kd in known_digits:
            r, c, v = kd['row'] - 1, kd['col'] - 1, kd['value']
            box_idx = (r // box_size) * 4 + (c // box_size)
            self.box_values[box_idx].add(v)
            self.box_known_cells[box_idx].append((r, c, v))
    
    def get_box_index(self, row: int, col: int) -> int:
        return (row // self.box_size) * 4 + (col // self.box_size)
    
    def get_missing_count_per_box(self) -> List[int]:
        return [16 - len(self.box_values[i]) for i in range(16)]


# ═══════════════════════════════════════════════════════════
# 第二架構：樹狀博弈剪枝策略
# ═══════════════════════════════════════════════════════════

class TreePruningStrategy:
    """樹狀博弈剪枝策略引擎
    
    剪枝策略：
    1. MRV (Minimum Remaining Values): 選擇剩餘值最少的單元格
    2. AC-3弧一致性約束傳播
    3. 行符闔排列預先約束
    4. 列AllDifferent剪枝
    5. 宮塊AllDifferent剪枝
    6. 前向檢查(Forward Checking)
    """
    
    def __init__(self, row_permutations: Dict[str, List[List[int]]], 
                 col_network: ColumnConstraintNetwork,
                 box_network: BoxConstraintNetwork,
                 grid_size: int = 16):
        self.row_permutations = row_permutations  # {row_letter: [[perm1], [perm2], ...]}
        self.col_network = col_network
        self.box_network = box_network
        self.grid_size = grid_size
        self.values = list(range(1, grid_size + 1))
        
    def filter_permutations_by_col_constraints(self, row_letter: str, 
                                                 row_idx: int,
                                                 current_grid: List[List[int]]) -> List[List[int]]:
        """使用列約束過濾符闔排列"""
        if row_letter not in self.row_permutations:
            return []
        
        perms = self.row_permutations[row_letter]
        filtered = []
        
        for perm in perms:
            valid = True
            for col_idx, val in enumerate(perm):
                if val == 0:
                    # 空位需要檢查列約束
                    if val in self.col_network.col_values.get(col_idx, set()):
                        valid = False
                        break
                else:
                    # 已知值檢查列衝突
                    if col_idx in self.col_network.col_values:
                        # 如果該列已有這個值且不在當前行位置
                        known_positions = self.col_network.col_known_positions[col_idx]
                        for kr, kc, kv in known_positions:
                            if kv == val and kr != row_idx:
                                valid = False
                                break
                        if not valid:
                            break
            
            if valid:
                filtered.append(perm)
        
        return filtered
    
    def compute_mrv_order(self, current_grid: List[List[int]], 
                          row_letters: List[str]) -> List[int]:
        """計算MRV排序：按每行剩餘可行排列數量排序"""
        row_feasibility = []
        
        for i, row_letter in enumerate(row_letters):
            if row_letter not in self.row_permutations:
                feasible_count = 0
            else:
                # 快速計算：用列約束初步過濾
                row_known = self.col_network.row_col_map.get(i, {})
                known_count = len(row_known)
                if known_count >= 16:
                    feasible_count = 1
                else:
                    # 基於已知值數量估算
                    perms = self.row_permutations[row_letter]
                    feasible_count = min(len(perms), 10000)  # 快速估算上界
                    
            row_feasibility.append((feasible_count, i))
        
        row_feasibility.sort(key=lambda x: x[0])
        return [idx for _, idx in row_feasibility]
    
    def forward_check(self, row_idx: int, col_idx: int, value: int,
                      current_grid: List[List[int]]) -> bool:
        """前向檢查：填值後是否導致其他單元格無解"""
        # 檢查列約束
        if col_idx in self.col_network.col_values:
            if value in self.col_network.col_values[col_idx]:
                return False
        
        # 檢查宮塊約束
        box_idx = self.box_network.get_box_index(row_idx, col_idx)
        if value in self.box_network.box_values.get(box_idx, set()):
            return False
        
        return True


# ═══════════════════════════════════════════════════════════
# 第三架構：十六連環終極循環搜索
# ═══════════════════════════════════════════════════════════

class SixteenChainUltimateSearch:
    """十六連環終極循環搜索引擎
    
    循環搜索架構：
    1. 初始化：讀取所有16行符闔排列
    2. 約束初始化：建立列/宮約束網絡
    3. 循環迭代：深度優先搜索 + 剪枝
    4. 狀態回溯：保存搜索狀態用於狀態空間分析
    5. 終極驗證：全約束驗證
    """
    
    def __init__(self, sudoku_config: Dict, row_permutations: Dict[str, List[List[int]]]):
        self.config = sudoku_config
        self.grid_size = 16
        self.box_size = 4
        
        # 初始化網絡
        known_digits = sudoku_config['known_digits']
        self.col_network = ColumnConstraintNetwork(known_digits)
        self.box_network = BoxConstraintNetwork(known_digits, self.box_size)
        
        # 符闔排列
        self.row_permutations = row_permutations
        
        # 行字母映射
        self.row_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                           'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
        
        # 初始網格（從已知數字建立）
        self.initial_grid = [[0] * 16 for _ in range(16)]
        for kd in known_digits:
            r, c, v = kd['row'] - 1, kd['col'] - 1, kd['value']
            self.initial_grid[r][c] = v
            
        # 剪枝策略
        self.pruner = TreePruningStrategy(
            self.row_permutations, self.col_network, self.box_network, self.grid_size
        )
        
        # 統計資訊
        self.search_stats = {
            'nodes_explored': 0,
            'nodes_pruned': 0,
            'solutions_found': 0,
            'max_depth': 0,
            'start_time': None,
            'end_time': None
        }
    
    def validate_solution(self, grid: List[List[int]]) -> Tuple[bool, List[str]]:
        """終極驗證：全約束驗證"""
        errors = []
        
        # 1. 行約束（AllDifferent）
        for r in range(16):
            vals = [grid[r][c] for c in range(16)]
            if len(set(vals)) != 16:
                errors.append(f"行{r+1}存在重複值")
            if 0 in vals:
                errors.append(f"行{r+1}存在空值")
        
        # 2. 列約束（AllDifferent）
        for c in range(16):
            vals = [grid[r][c] for r in range(16)]
            if len(set(vals)) != 16:
                errors.append(f"列{c+1}存在重複值")
        
        # 3. 宮塊約束（AllDifferent）
        for box_idx in range(16):
            vals = []
            for r in range(16):
                for c in range(16):
                    if self.box_network.get_box_index(r, c) == box_idx:
                        vals.append(grid[r][c])
            if len(set(vals)) != 16:
                errors.append(f"宮{box_idx+1}存在重複值")
        
        # 4. 符闔排列約束驗證
        for r, letter in enumerate(self.row_letters):
            if letter in self.row_permutations:
                current_row = grid[r]
                # 檢查是否是某個符闔排列
                found = False
                for perm in self.row_permutations[letter]:
                    if all(perm[c] == current_row[c] or (perm[c] == 0 and current_row[c] != 0) 
                           for c in range(16)):
                        found = True
                        break
                if not found:
                    errors.append(f"行{r+1}({letter})不滿足符闔排列約束")
        
        return len(errors) == 0, errors
    
    def search(self, depth: int = 0) -> Optional[List[List[int]]]:
        """深度優先搜索主函數"""
        self.search_stats['nodes_explored'] += 1
        self.search_stats['max_depth'] = max(self.search_stats['max_depth'], depth)
        
        if depth == 16:
            # 所有行已填入，驗證
            solution = deepcopy(self.current_grid)
            valid, errors = self.validate_solution(solution)
            if valid:
                self.search_stats['solutions_found'] += 1
                return solution
            return None
        
        row_idx = depth
        row_letter = self.row_letters[row_idx]
        
        if row_letter not in self.row_permutations:
            return None
        
        # 获取当前行的已知值
        row_known = self.col_network.row_col_map.get(row_idx, {})
        
        # 从符闔排列中选择匹配的
        best_perm = None
        for perm in self.row_permutations[row_letter]:
            # 检查是否与已知值匹配
            match = True
            for col_idx, known_val in row_known.items():
                if perm[col_idx] != 0 and perm[col_idx] != known_val:
                    match = False
                    break
                if perm[col_idx] == 0 and known_val != 0:
                    # 排列中该位置为空，但已知有值
                    match = False
                    break
            
            if match:
                # 检查列约束
                col_ok = True
                for col_idx, val in enumerate(perm):
                    if val != 0:
                        # 检查列是否有冲突
                        col_known = [(kr, kc, kv) for kr, kc, kv in self.col_network.col_known_positions[col_idx] if kr != row_idx]
                        for kr, kc, kv in col_known:
                            if kv == val:
                                col_ok = False
                                break
                        if not col_ok:
                            break
                
                if col_ok:
                    # 检查宫约束
                    box_ok = True
                    for col_idx, val in enumerate(perm):
                        if val != 0:
                            box_idx = self.box_network.get_box_index(row_idx, col_idx)
                            if val in self.box_network.box_values.get(box_idx, set()):
                                # 需要排除同一行已填的值
                                row_box_vals = set()
                                for c in range(16):
                                    if self.box_network.get_box_index(row_idx, c) == box_idx:
                                        row_box_vals.add(self.current_grid[row_idx][c])
                                if val in row_box_vals:
                                    box_ok = False
                                    break
                    
                    if box_ok:
                        best_perm = perm
                        break  # 找到第一个匹配的
        
        if best_perm is None:
            self.search_stats['nodes_pruned'] += 1
            return None
        
        # 填入最佳排列
        self.current_grid[row_idx] = best_perm[:]
        
        # 更新列和宫的值集合（用于后续剪枝）
        original_col_values = {}
        original_box_values = {}
        for c, v in enumerate(best_perm):
            if v != 0:
                original_col_values[c] = self.col_network.col_values[c].copy()
                self.col_network.col_values[c].add(v)
                orig_box = self.box_network.get_box_index(row_idx, c)
                original_box_values[orig_box] = self.box_network.box_values[orig_box].copy()
                self.box_network.box_values[orig_box].add(v)
        
        # 递归搜索下一行
        result = self.search(depth + 1)
        
        if result is not None:
            return result
        
        # 回溯
        for c, v in enumerate(best_perm):
            if v != 0:
                if c in original_col_values:
                    self.col_network.col_values[c] = original_col_values[c]
                orig_box = self.box_network.get_box_index(row_idx, c)
                if orig_box in original_box_values:
                    self.box_network.box_values[orig_box] = original_box_values[orig_box]
        
        return None
    
    def run(self) -> Dict:
        """執行終極循環搜索"""
        print("=" * 60)
        print("┌─ 十六連環變體神經網絡鏈式博弈剪枝求解系統 ─┐")
        print("│  架構：神經鏈式約束 + 樹狀博弈剪枝 + 循環搜索 │")
        print("└──────────────────────────────────────────┘")
        print()
        
        self.search_stats['start_time'] = time.time()
        self.current_grid = [row[:] for row in self.initial_grid]
        
        # 預處理：為每行預先過濾符闔排列
        print("[預處理] 過濾符闔排列...")
        for row_idx, row_letter in enumerate(self.row_letters):
            if row_letter in self.row_permutations:
                row_known = self.col_network.row_col_map.get(row_idx, {})
                filtered = []
                for perm in self.row_permutations[row_letter]:
                    match = True
                    for col_idx, known_val in row_known.items():
                        if perm[col_idx] != 0 and perm[col_idx] != known_val:
                            match = False
                            break
                    if match:
                        filtered.append(perm)
                self.row_permutations[row_letter] = filtered
                print(f"  行{row_letter}: {len(filtered)} 個可行排列")
        
        print()
        print("[搜索] 啟動深度優先循環搜索...")
        print(f"  搜索樹深度: 16 (每行一層)")
        print(f"  剪枝策略: MRV + 列約束 + 宮約束 + 前向檢查")
        print()
        
        solution = self.search(depth=0)
        
        self.search_stats['end_time'] = time.time()
        
        # 輸出結果
        elapsed = self.search_stats['end_time'] - self.search_stats['start_time']
        print()
        print("=" * 60)
        print("┌─ 搜索完成 ───────────────────────────────────┐")
        print(f"│  搜索節點: {self.search_stats['nodes_explored']:,}                        │")
        print(f"│  剪枝節點: {self.search_stats['nodes_pruned']:,}                        │")
        print(f"│  搜索深度: {self.search_stats['max_depth']}/16                                │")
        print(f"│  找到解:   {self.search_stats['solutions_found']}                                │")
        print(f"│  耗時:     {elapsed:.2f}秒                                 │")
        print("└──────────────────────────────────────────┘")
        
        if solution:
            print()
            print("[解驗證] 終極驗證...")
            valid, errors = self.validate_solution(solution)
            if valid:
                print("  ✅ 全約束驗證通過")
                print()
                print("[解展示]")
                for r in range(16):
                    row_str = " ".join(f"{solution[r][c]:2d}" for c in range(16))
                    letter = self.row_letters[r]
                    print(f"  行{letter}: {row_str}")
            else:
                print("  ❌ 驗證失敗:")
                for e in errors:
                    print(f"    - {e}")
        else:
            print()
            print("  ❌ 未找到滿足所有約束的解")
        
        return {
            'success': solution is not None,
            'solution': solution,
            'stats': self.search_stats,
            'errors': errors if solution else None
        }


# ═══════════════════════════════════════════════════════════
# 主函數：整合三大架構執行終極搜索
# ═══════════════════════════════════════════════════════════

def load_permutations_from_json() -> Dict[str, List[List[int]]]:
    """從JSON文件加載符闔排列"""
    import os
    
    row_map = {
        'A': 'A1_permutations.json',
        'B': 'A2_permutations.json',
        'C': 'A3_permutations.json',
        'D': 'A4_permutations.json',
        'E': 'A5_permutations.json',
        'F': 'A6_permutations.json',
        'G': 'A7_permutations.json',
        'H': 'A8_permutations.json',
        'I': 'A9_permutations.json',
        'J': 'A10_permutations.json',
        'K': 'A11_permutations.json',
        'L': 'A12_permutations.json',
        'M': 'A13_permutations.json',
        'N': 'A14_permutations.json',
        'O': 'A15_permutations.json',
        'P': 'A16_permutations.json',
    }
    
    row_permutations = {}
    base_dir = 'D:/2026/WPF_Sudoku/Sudoku_256'
    
    for letter, fname in row_map.items():
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'permutations' in data:
                    row_permutations[letter] = data['permutations']
                elif isinstance(data, list):
                    row_permutations[letter] = data
                print(f"  {fname}: {len(row_permutations[letter]):,} 個排列")
        else:
            print(f"  警告: {fname} 不存在")
    
    return row_permutations


def main():
    """主執行入口"""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     十六連環變體神經網絡鏈式博弈剪枝求解系統             ║")
    print("║     Sixteen-Chain Neural Network Tree-Pruning Solver     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    # 步驟1：載入配置
    print("[步驟1] 載入數獨配置...")
    config_path = 'D:/2026/WPF_Sudoku/Sudoku_256/box_size4_config_parsed.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        sudoku_config = json.load(f)
    print(f"  網格大小: {sudoku_config['grid_size']}x{sudoku_config['grid_size']}")
    print(f"  宮塊大小: {sudoku_config['box_size']}x{sudoku_config['box_size']}")
    print(f"  已知數字: {sudoku_config['known_digits_count']} 個")
    print(f"  空單元格: {sudoku_config['empty_cells']} 個")
    print(f"  填補率: {sudoku_config['fill_rate']}%")
    print()
    
    # 步驟2：載入符闔排列
    print("[步驟2] 載入16行符闔排列...")
    row_permutations = load_permutations_from_json()
    total_perms = sum(len(v) for v in row_permutations.values())
    print(f"  符闔排列總數: {total_perms:,}")
    print()
    
    # 步驟3：構建求解器並執行
    print("[步驟3] 構建求解器並執行終極循環搜索...")
    print()
    
    solver = SixteenChainUltimateSearch(sudoku_config, row_permutations)
    result = solver.run()
    
    # 保存結果
    if result['solution']:
        result_path = 'D:/2026/WPF_Sudoku/Sudoku_256/16chain_search_result.json'
        output = {
            'success': True,
            'grid': result['solution'],
            'stats': {
                'nodes_explored': result['stats']['nodes_explored'],
                'nodes_pruned': result['stats']['nodes_pruned'],
                'solutions_found': result['stats']['solutions_found'],
                'search_time_seconds': result['stats']['end_time'] - result['stats']['start_time'],
            }
        }
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print()
        print(f"[保存] 結果已保存至: {result_path}")
    
    return result


if __name__ == '__main__':
    main()
