#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
專用符闔數獨求解器 v2 - 惰性載入+高效剪枝
只載入必要的排列數據
"""

import json
import time
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
from datetime import datetime


class FastFuheSolver:
    """快速符闔數獨求解器"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16
        self.box_size = 4
        
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        # 已過濾的有效排列索引
        self.valid_perms_idx: List[List[int]] = [[] for _ in range(self.N)]
        
        # 統計
        self.solutions = []
        self.nodes = 0
        self.start_time = 0
        self.time_limit = 120  # 2分鐘
        
        self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """載入配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'known_digits' in config:
            for clue in config['known_digits']:
                r, c = clue['row']-1, clue['col']-1
                self.known_map[(r, c)] = clue['value']
        
        print(f"已知數字: {len(self.known_map)} 個")
        
        # 只載入小排列集，大集合記錄資訊
        for row in range(self.N):
            try:
                with open(f"A{row+1}_permutations.json", 'r', encoding='utf-8') as f:
                    perms = json.load(f)
                    self.row_perms[row] = perms
                    print(f"  第{row+1}行: {len(perms):,} 排列", end="")
                    
                    # 即時過濾
                    valid = []
                    for idx, perm in enumerate(perms):
                        ok = True
                        for col, val in enumerate(perm):
                            if (row, col) in self.known_map:
                                if self.known_map[(row, col)] != val:
                                    ok = False
                                    break
                        if ok:
                            valid.append(idx)
                    
                    self.valid_perms_idx[row] = valid
                    tight = "極緊" if len(valid) < 200 else "緊" if len(valid) < 1000 else "鬆"
                    print(f" → 有效: {len(valid):,} ({tight})")
                    
            except FileNotFoundError:
                print(f"  第{row+1}行: 文件不存在")
    
    def mrv_order(self) -> List[int]:
        """MRV排序"""
        counts = [(i, len(self.valid_perms_idx[i])) for i in range(self.N)]
        counts.sort(key=lambda x: x[1])
        return [r for r, c in counts]
    
    def solve(self, max_solutions: int = 20) -> Dict:
        """主求解"""
        self.start_time = time.time()
        self.solutions = []
        self.nodes = 0
        
        row_order = self.mrv_order()
        
        print(f"\n{'='*60}")
        print(f"DFS搜索 (上限{max_solutions}解, 時限{self.time_limit}s)")
        print(f"{'='*60}")
        
        # 初始化約束
        col_used = [set() for _ in range(self.N)]
        box_used = [set() for _ in range(self.N)]
        
        for (r, c), v in self.known_map.items():
            col_used[c].add(v)
            box_used[(r//4)*4 + c//4].add(v)
        
        self._dfs(0, row_order, col_used, box_used)
        
        elapsed = time.time() - self.start_time
        
        return {
            'solutions_found': len(self.solutions),
            'nodes_explored': self.nodes,
            'time_seconds': round(elapsed, 2),
            'limit_reached': len(self.solutions) >= max_solutions,
            'solutions': self.solutions[:5]
        }
    
    def _dfs(self, depth: int, row_order: List[int],
             col_used: List[Set[int]], 
             box_used: List[Set[int]]):
        """DFS"""
        self.nodes += 1
        
        elapsed = time.time() - self.start_time
        if len(self.solutions) >= 20 or elapsed > self.time_limit:
            return
        
        if depth == self.N:
            # 重建解
            grid = []
            for r in range(self.N):
                row_vals = [0] * self.N
                for c in range(self.N):
                    if (r, c) in self.known_map:
                        row_vals[c] = self.known_map[(r, c)]
                    else:
                        # 找該列唯一值
                        for v in range(1, 17):
                            if v in col_used[c]:
                                row_vals[c] = v
                                break
                grid.append(row_vals)
            
            self.solutions.append({'grid': grid})
            
            if len(self.solutions) % 5 == 0:
                print(f"  解 {len(self.solutions)}: 節點{self.nodes:,}, {elapsed:.1f}s")
            return
        
        row = row_order[depth]
        valid_indices = self.valid_perms_idx[row]
        
        if not valid_indices:
            return  # 無有效排列，剪枝
        
        for perm_idx in valid_indices:
            perm = self.row_perms[row][perm_idx]
            
            # 快速檢查衝突
            has_conflict = False
            applied = []
            for col, val in enumerate(perm):
                if (row, col) in self.known_map:
                    continue
                if val in col_used[col] or val in box_used[(row//4)*4 + col//4]:
                    has_conflict = True
                    break
                applied.append((col, val))
            
            if has_conflict:
                continue
            
            # 應用
            for c, v in applied:
                col_used[c].add(v)
                box_used[(row//4)*4 + c//4].add(v)
            
            self._dfs(depth + 1, row_order, col_used, box_used)
            
            # 回溯
            for c, v in applied:
                col_used[c].remove(v)
                box_used[(row//4)*4 + c//4].remove(v)
            
            if len(self.solutions) >= 20 or time.time() - self.start_time > self.time_limit:
                return


def main():
    print("="*60)
    print("專用符闔數獨求解器 v2 - 惰性載入")
    print("="*60)
    print(f"開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    solver = FastFuheSolver()
    result = solver.solve(max_solutions=20)
    
    # 保存
    with open("fast_solver_result.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n" + "="*60)
    print("結果")
    print("="*60)
    print(f"解數: {result['solutions_found']}")
    print(f"節點: {result['nodes_explored']:,}")
    print(f"時間: {result['time_seconds']:.2f}秒")
    
    return result


if __name__ == "__main__":
    main()
