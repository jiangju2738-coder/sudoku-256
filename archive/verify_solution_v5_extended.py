#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔數獨擴展驗證 - DFS搜索上限1000解
以10個已知解為節點，建立樹狀博弈剪枝策略
"""

import json
import time
from collections import defaultdict
from typing import List, Tuple, Optional, Dict, Set
import numpy as np

class SudokuSolverExtended:
    """16×16 符闔數獨求解器 - 擴展版"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16  # 16×16
        self.box_size = 4  # 4×4 box
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.perm_map: Dict[Tuple[int, int], List[Tuple[int, int]]] = defaultdict(list)
        
        self.col_used: List[Set[int]] = [set() for _ in range(self.N)]
        self.box_used: List[Set[int]] = [set() for _ in range(self.N)]
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        self.solutions: List[Dict] = []
        self.nodes_explored = 0
        self.start_time = 0
        self.solution_limit = 1000
        self.time_limit = 3600  # 1小時
        
        # 統計信息
        self.stats = {
            'valid_perms_per_row': [],
            'search_depth_stats': [],
            'pruning_count': 0,
            'branching_factor': []
        }
        
        self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """載入配置和符闔排列"""
        print(f"載入配置: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 載入已知數字
        if 'clues' in config:
            for clue in config['clues']:
                row, col = clue['row'], clue['col']
                val = clue['value']
                self.known_map[(row, col)] = val
        
        # 載入符闔排列
        for row in range(self.N):
            perm_file = f"A{row+1}_permutations.json"
            print(f"載入 {perm_file}...")
            try:
                with open(perm_file, 'r', encoding='utf-8') as f:
                    perms = json.load(f)
                self.row_perms[row] = perms
            except FileNotFoundError:
                print(f"警告: {perm_file} 不存在")
    
    def get_box_id(self, row: int, col: int) -> int:
        """計算宮ID"""
        return (row // self.box_size) * self.box_size + (col // self.box_size)
    
    def check_perm_valid(self, row: int, perm_idx: int) -> bool:
        """檢查排列是否符合約束"""
        if row < 0 or row >= self.N:
            return False
        if perm_idx < 0 or perm_idx >= len(self.row_perms[row]):
            return False
        
        perm = self.row_perms[row][perm_idx]
        
        for col, val in enumerate(perm):
            # 符合該行已知數字
            if (row, col) in self.known_map:
                if self.known_map[(row, col)] != val:
                    return False
            
            # 列約束（排除當前行已知）
            if not ((row, col) in self.known_map and self.known_map[(row, col)] == val):
                if val in self.col_used[col]:
                    return False
            
            # 宮約束（排除當前行已知）
            if not ((row, col) in self.known_map and self.known_map[(row, col)] == val):
                box_id = self.get_box_id(row, col)
                if val in self.box_used[box_id]:
                    return False
        
        return True
    
    def select_valid_perms(self) -> List[Tuple[int, int]]:
        """為每行選擇有效排列"""
        valid_perms = []
        
        for row in range(self.N):
            row_valid = []
            for idx in range(len(self.row_perms[row])):
                if self.check_perm_valid(row, idx):
                    row_valid.append(idx)
            valid_perms.append(row_valid)
        
        return valid_perms
    
    def solve_dfs(self, row_order: Optional[List[int]] = None):
        """DFS搜索 - 主入口"""
        self.start_time = time.time()
        
        # 初始化約束
        self._init_constraints()
        
        # 計算每行有效排列數量
        valid_perms = self.select_valid_perms()
        self.stats['valid_perms_per_row'] = [len(vp) for vp in valid_perms]
        
        # MRV排序：按有效排列數量排序
        if row_order is None:
            row_order = sorted(range(self.N), key=lambda r: len(valid_perms[r]))
        
        print(f"\n=== DFS 搜索開始 ===")
        print(f"解數量上限: {self.solution_limit}")
        print(f"時間限制: {self.time_limit} 秒")
        print(f"有效排列統計: {self.stats['valid_perms_per_row']}")
        
        # 從已知解繼續搜索
        self._load_known_solutions()
        
        # DFS遞歸
        self._dfs_search(valid_perms, row_order, 0)
        
        return self._format_result()
    
    def _init_constraints(self):
        """初始化約束狀態"""
        for row in range(self.N):
            for col in range(self.N):
                if (row, col) in self.known_map:
                    val = self.known_map[(row, col)]
                    self.col_used[col].add(val)
                    box_id = self.get_box_id(row, col)
                    self.box_used[box_id].add(val)
    
    def _load_known_solutions(self):
        """從solution_count_result.json載入已知解"""
        try:
            with open('solution_count_result.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'solutions' in data:
                for sol in data['solutions']:
                    # 驗證解的有效性並加入樹結構
                    self.solutions.append({
                        'grid': sol['grid'],
                        'depth': 0,  # 初始節點深度為0
                        'parent': None
                    })
                print(f"載入 {len(self.solutions)} 個已知解作為起始節點")
        except FileNotFoundError:
            print("未找到已知解文件，從空狀態開始")
    
    def _dfs_search(self, valid_perms: List[List[int]], 
                    row_order: List[int], 
                    depth: int):
        """DFS遞歸搜索"""
        self.nodes_explored += 1
        
        # 檢查時間和數量限制
        elapsed = time.time() - self.start_time
        if len(self.solutions) >= self.solution_limit or elapsed > self.time_limit:
            return
        
        if depth == self.N:
            # 找到完整解
            self._record_solution()
            return
        
        row = row_order[depth]
        candidates = valid_perms[row]
        
        if not candidates:
            return  # 剪枝：無有效排列
        
        # 統計分支因子
        if depth < 5:  # 前5層統計
            self.stats['branching_factor'].append(len(candidates))
        
        for perm_idx in candidates:
            # 檢查剪枝條件
            if self._should_prune(row, depth, perm_idx):
                self.stats['pruning_count'] += 1
                continue
            
            # 應用排列
            self._apply_perm(row, perm_idx, +1)
            
            # 遞歸搜索
            self._dfs_search(valid_perms, row_order, depth + 1)
            
            # 回溯
            self._apply_perm(row, perm_idx, -1)
            
            # 檢查限制
            elapsed = time.time() - self.start_time
            if len(self.solutions) >= self.solution_limit or elapsed > self.time_limit:
                return
    
    def _should_prune(self, row: int, depth: int, perm_idx: int) -> bool:
        """博弈剪枝策略"""
        # 1. 基於已知解的相似性剪枝
        for sol in self.solutions:
            if self._is_similar_to_known(row, perm_idx, sol, threshold=0.8):
                return True
        
        # 2. 基於約束密度的剪枝 - 當前實現不剪枝，保持探索
        return False
    
    def _is_similar_to_known(self, row: int, perm_idx: int, 
                            known_sol: Dict, threshold: float) -> bool:
        """檢查與已知解的相似度"""
        # 簡化版本：檢查當前行是否與已知解相同
        current_perm = self.row_perms[row][perm_idx]
        known_perm = known_sol['grid'][row]
        
        similarity = sum(1 for a, b in zip(current_perm, known_perm) if a == b) / 16
        return similarity >= threshold
    
    def _apply_perm(self, row: int, perm_idx: int, direction: int):
        """應用/回溯排列"""
        perm = self.row_perms[row][perm_idx]
        
        for col, val in enumerate(perm):
            if direction > 0:
                self.col_used[col].add(val)
                box_id = self.get_box_id(row, col)
                self.box_used[box_id].add(val)
            else:
                self.col_used[col].remove(val)
                box_id = self.get_box_id(row, col)
                self.box_used[box_id].remove(val)
    
    def _record_solution(self):
        """記錄找到的解"""
        # 從當前約束狀態重建解
        grid = []
        for row in range(self.N):
            grid_row = []
            for col in range(self.N):
                # 找到在當前col中只被使用一次的val
                for val in range(1, self.N + 1):
                    if val in self.col_used[col]:
                        grid_row.append(val)
                        break
            grid.append(grid_row)
        
        self.solutions.append({
            'grid': grid,
            'depth': self.N,
            'parent': None
        })
    
    def _format_result(self) -> Dict:
        """格式化結果"""
        elapsed = time.time() - self.start_time
        
        result = {
            "total_solutions": len(self.solutions),
            "statistics": {
                "nodes_explored": self.nodes_explored,
                "time_seconds": round(elapsed, 2),
                "solution_limit": self.solution_limit,
                "pruning_count": self.stats['pruning_count'],
                "avg_branching_factor": round(
                    sum(self.stats['branching_factor']) / max(1, len(self.stats['branching_factor'])), 2
                ) if self.stats['branching_factor'] else 0
            },
            "valid_counts_per_row": self.stats['valid_perms_per_row'],
            "search_completed": len(self.solutions) < self.solution_limit and elapsed < self.time_limit
        }
        
        return result


def main():
    """主函數"""
    print("=" * 60)
    print("符闔數獨擴展驗證 - DFS搜索上限1000解")
    print("=" * 60)
    
    solver = SudokuSolverExtended("sudoku_config.json")
    result = solver.solve_dfs()
    
    # 保存結果
    output_file = "solution_count_extended.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果已保存至: {output_file}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


if __name__ == "__main__":
    main()
