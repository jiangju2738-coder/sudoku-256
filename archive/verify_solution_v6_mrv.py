#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔數獨求解 - MRV優化版本
使用最小剩餘值(MRV)啟發式，上限1000解
"""

import json
import time
from collections import defaultdict
from typing import List, Tuple, Dict, Set, Optional


class SudokuSolverMRV:
    """16×16 符闔數獨求解器 - MRV優化版"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16
        self.box_size = 4
        self.solution_limit = 1000
        
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        self.solutions: List[List[List[int]]] = []
        self.nodes_explored = 0
        
        # 約束狀態
        self.col_used: List[Set[int]] = [set() for _ in range(self.N)]
        self.box_used: List[Set[int]] = [set() for _ in range(self.N)]
        
        # 每行有效排列的動態計算
        self.valid_perm_counts: List[int] = []
        
        self.start_time = 0
        self.time_limit = 7200  # 2小時
        
        self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """載入配置"""
        print(f"載入配置: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'clues' in config:
            for clue in config['clues']:
                row, col = clue['row'], clue['col']
                val = clue['value']
                self.known_map[(row, col)] = val
        
        for row in range(self.N):
            perm_file = f"A{row+1}_permutations.json"
            try:
                with open(perm_file, 'r', encoding='utf-8') as f:
                    perms = json.load(f)
                self.row_perms[row] = perms
            except FileNotFoundError:
                print(f"警告: {perm_file} 不存在")
        
        print(f"已知數字: {len(self.known_map)} 個")
    
    def get_box_id(self, row: int, col: int) -> int:
        return (row // self.box_size) * self.box_size + (col // self.box_size)
    
    def check_perm_valid_for_row(self, row: int, perm_idx: int) -> bool:
        """檢查某個排列對某行是否有效（考慮當前約束）"""
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
            
            # 列約束：如果該位置沒有已知數字，檢查是否已使用
            if (row, col) not in self.known_map:
                if val in self.col_used[col]:
                    return False
            
            # 宮約束
            if (row, col) not in self.known_map:
                box_id = self.get_box_id(row, col)
                if val in self.box_used[box_id]:
                    return False
        
        return True
    
    def count_valid_perms_for_row(self, row: int) -> int:
        """計算某行有多少有效排列"""
        count = 0
        for idx in range(len(self.row_perms[row])):
            if self.check_perm_valid_for_row(row, idx):
                count += 1
        return count
    
    def get_row_order_mrv(self) -> List[int]:
        """MRV排序：按有效排列數量排序（緊的約束先）"""
        row_valid_counts = []
        for row in range(self.N):
            count = self.count_valid_perms_for_row(row)
            row_valid_counts.append((row, count))
        
        # 按有效排列數量排序（最小優先）
        row_valid_counts.sort(key=lambda x: x[1])
        
        return [r for r, c in row_valid_counts]
    
    def apply_perm(self, row: int, perm_idx: int, direction: int = 1):
        """應用或回溯排列"""
        perm = self.row_perms[row][perm_idx]
        
        for col, val in enumerate(perm):
            # 跳過已知數字（它們已經在約束中）
            if (row, col) in self.known_map:
                continue
            
            if direction > 0:
                self.col_used[col].add(val)
                box_id = self.get_box_id(row, col)
                self.box_used[box_id].add(val)
            else:
                self.col_used[col].remove(val)
                box_id = self.get_box_id(row, col)
                self.box_used[box_id].remove(val)
    
    def get_current_grid(self) -> List[List[int]]:
        """從當前約束狀態重建網格"""
        grid = []
        for row in range(self.N):
            row_vals = []
            for col in range(self.N):
                if (row, col) in self.known_map:
                    row_vals.append(self.known_map[(row, col)])
                else:
                    # 找到該列唯一可用的值
                    for val in range(1, self.N + 1):
                        if val in self.col_used[col]:
                            # 檢查是否只出現一次
                            count = sum(1 for r in range(self.N) if val in self.col_used[r])
                            if count == 1:
                                row_vals.append(val)
                                break
                    else:
                        row_vals.append(0)  # 未知
            grid.append(row_vals)
        return grid
    
    def dfs_search(self, row_order: List[int], depth: int):
        """DFS搜索（MRV版本）"""
        self.nodes_explored += 1
        
        # 檢查限制
        elapsed = time.time() - self.start_time
        if len(self.solutions) >= self.solution_limit or elapsed > self.time_limit:
            return
        
        if depth == self.N:
            # 找到完整解
            grid = self.get_current_grid()
            self.solutions.append(grid)
            
            if len(self.solutions) % 100 == 0:
                print(f"已找到 {len(self.solutions)} 個解，節點: {self.nodes_explored}, 時間: {elapsed:.1f}s")
            return
        
        # 選擇當前行
        row = row_order[depth]
        
        # 找出所有有效排列
        valid_perms = []
        for idx in range(len(self.row_perms[row])):
            if self.check_perm_valid_for_row(row, idx):
                valid_perms.append(idx)
        
        if not valid_perms:
            return  # 剪枝：無有效排列
        
        # 嘗試每個排列
        for perm_idx in valid_perms:
            # 應用排列
            self.apply_perm(row, perm_idx, 1)
            
            # 遞歸搜索下一行
            self.dfs_search(row_order, depth + 1)
            
            # 回溯
            self.apply_perm(row, perm_idx, -1)
            
            # 檢查是否需要停止
            elapsed = time.time() - self.start_time
            if len(self.solutions) >= self.solution_limit or elapsed > self.time_limit:
                return
    
    def solve(self) -> Dict:
        """主求解方法"""
        self.start_time = time.time()
        
        # 初始化約束
        for row, col in self.known_map:
            val = self.known_map[(row, col)]
            self.col_used[col].add(val)
            box_id = self.get_box_id(row, col)
            self.box_used[box_id].add(val)
        
        # MRV排序
        row_order = self.get_row_order_mrv()
        
        print(f"\n{'='*60}")
        print(f"MRV DFS 搜索開始")
        print(f"{'='*60}")
        print(f"解數量上限: {self.solution_limit}")
        print(f"時間限制: {self.time_limit} 秒")
        print(f"行排序 (MRV): {row_order}")
        
        # 計算每行有效排列數量（初始狀態）
        initial_counts = []
        for row in range(self.N):
            count = self.count_valid_perms_for_row(row)
            initial_counts.append(count)
        print(f"初始有效排列數: {initial_counts}")
        
        # 開始搜索
        self.dfs_search(row_order, 0)
        
        # 格式化結果
        elapsed = time.time() - self.start_time
        
        result = {
            "total_solutions": len(self.solutions),
            "statistics": {
                "nodes_explored": self.nodes_explored,
                "time_seconds": round(elapsed, 2),
                "solution_limit": self.solution_limit,
                "search_completed": len(self.solutions) < self.solution_limit and elapsed < self.time_limit
            },
            "initial_valid_counts_per_row": initial_counts,
            "row_order_mrv": row_order
        }
        
        return result
    
    def save_solutions(self, output_path: str = "solutions_found.json"):
        """保存找到的解"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "solutions": self.solutions,
                "count": len(self.solutions)
            }, f, ensure_ascii=False, indent=2)
        print(f"解已保存至: {output_path}")


def main():
    """主函數"""
    print("="*60)
    print("符闔數獨求解 - MRV優化版本 (上限1000解)")
    print("="*60)
    
    solver = SudokuSolverMRV("sudoku_config.json")
    result = solver.solve()
    
    # 保存結果
    output_file = "solution_count_mrv.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    solver.save_solutions()
    
    print(f"\n{'='*60}")
    print(f"結果摘要")
    print(f"{'='*60}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


if __name__ == "__main__":
    main()
