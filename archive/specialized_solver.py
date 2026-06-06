#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
專用符闔數獨求解器 - 高效DFS+剪枝
針對16×16符闔數獨特性優化，避免通用求解器限制
"""

import json
import time
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
from datetime import datetime


class SpecializedFuheSolver:
    """專用符闔數獨求解器"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16
        self.box_size = 4
        
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        # 優化數據結構
        self.perm_by_col_val: List[List[List[int]]] = [[] for _ in range(self.N)]
        self.col_val_to_perm_indices: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        self.solutions = []
        self.nodes = 0
        self.start_time = 0
        self.time_limit = 300  # 5分鐘
        
        self.load_config(config_path)
        self._preprocess_perms()
    
    def load_config(self, config_path: str):
        """載入配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'known_digits' in config:
            for clue in config['known_digits']:
                r, c = clue['row']-1, clue['col']-1
                self.known_map[(r, c)] = clue['value']
        elif 'clues' in config:
            for clue in config['clues']:
                r, c = clue['row']-1, clue['col']-1
                self.known_map[(r, c)] = clue['value']
        
        for row in range(self.N):
            try:
                with open(f"A{row+1}_permutations.json", 'r', encoding='utf-8') as f:
                    self.row_perms[row] = json.load(f)
            except:
                self.row_perms[row] = []
        
        print(f"已知數字: {len(self.known_map)} 個")
        print(f"排列總數: {sum(len(p) for p in self.row_perms):,}")
    
    def _preprocess_perms(self):
        """預處理排列數據 - 加速查找"""
        # 為每行建立 col_val -> perm_indices 的映射
        self.col_val_to_perm_indices = [[defaultdict(list) for _ in range(self.N)] for _ in range(self.N)]
        
        for row in range(self.N):
            for col in range(self.N):
                for perm_idx, perm in enumerate(self.row_perms[row]):
                    val = perm[col]
                    self.col_val_to_perm_indices[row][col][val].append(perm_idx)
    
    def filter_valid_perms_by_known(self) -> List[List[int]]:
        """過濾每行符合已知數字的排列"""
        valid = []
        for row in range(self.N):
            row_valid = []
            for perm_idx, perm in enumerate(self.row_perms[row]):
                ok = True
                for col, val in enumerate(perm):
                    if (row, col) in self.known_map:
                        if self.known_map[(row, col)] != val:
                            ok = False
                            break
                if ok:
                    row_valid.append(perm_idx)
            valid.append(row_valid)
        return valid
    
    def mrv_order(self, valid_perms: List[List[int]]) -> List[int]:
        """MRV排序 - 按有效排列數排序"""
        counts = [(i, len(valid_perms[i])) for i in range(self.N)]
        counts.sort(key=lambda x: x[1])
        return [r for r, c in counts]
    
    def solve(self, max_solutions: int = 100) -> Dict:
        """主求解方法"""
        self.start_time = time.time()
        self.solutions = []
        self.nodes = 0
        
        # 過濾有效排列
        valid_perms = self.filter_valid_perms_by_known()
        
        # MRV排序
        row_order = self.mrv_order(valid_perms)
        
        print("\n每行有效排列數:")
        for i, r in enumerate(row_order):
            tight = "極緊" if len(valid_perms[r]) < 200 else "緊" if len(valid_perms[r]) < 1000 else "鬆"
            print(f"  第{r+1}行: {len(valid_perms[r]):,} ({tight})")
        
        # 初始化約束
        col_used = [set() for _ in range(self.N)]
        box_used = [set() for _ in range(self.N)]
        
        for (r, c), v in self.known_map.items():
            col_used[c].add(v)
            box_used[(r//4)*4 + c//4].add(v)
        
        print(f"\nDFS搜索開始 (上限{max_solutions}解, 時限{self.time_limit}s)...")
        print("-"*60)
        
        self._dfs(0, row_order, valid_perms, col_used, box_used)
        
        elapsed = time.time() - self.start_time
        
        return {
            'solutions_found': len(self.solutions),
            'nodes_explored': self.nodes,
            'time_seconds': round(elapsed, 2),
            'limit_reached': len(self.solutions) >= max_solutions,
            'solutions': self.solutions[:10]
        }
    
    def _dfs(self, depth: int, row_order: List[int], 
             valid_perms: List[List[int]],
             col_used: List[Set[int]], 
             box_used: List[Set[int]]):
        """DFS搜索"""
        self.nodes += 1
        
        elapsed = time.time() - self.start_time
        if len(self.solutions) >= 100 or elapsed > self.time_limit:
            return
        
        if depth == self.N:
            # 重建解
            grid = []
            for r in range(self.N):
                # 從排列重建
                row_vals = []
                for c in range(self.N):
                    for v in range(1, 17):
                        if v in col_used[c]:
                            # 檢查是否唯一
                            count = sum(1 for rr in range(self.N) if v in col_used[rr] and (rr, c) not in self.known_map)
                            if count == 1 or (r, c) in self.known_map:
                                row_vals.append(v if (r, c) not in self.known_map else self.known_map[(r, c)])
                                break
                    else:
                        row_vals.append(self.known_map.get((r, c), 0))
                grid.append(row_vals)
            
            self.solutions.append({'grid': grid})
            
            if len(self.solutions) % 10 == 0:
                print(f"  解 {len(self.solutions)}: 節點{self.nodes:,}, {elapsed:.1f}s")
            return
        
        row = row_order[depth]
        
        # 剪枝：如果該行無有效排列，回溯
        if not valid_perms[row]:
            return
        
        # 嘗試每個有效排列
        for perm_idx in valid_perms[row]:
            perm = self.row_perms[row][perm_idx]
            
            # 檢查列/宮衝突
            conflicts = []
            for col, val in enumerate(perm):
                if (row, col) in self.known_map:
                    continue
                if val in col_used[col] or val in box_used[(row//4)*4 + col//4]:
                    conflicts.append((col, val))
            
            if conflicts:
                continue
            
            # 應用排列
            applied = []
            for col, val in enumerate(perm):
                if (row, col) not in self.known_map:
                    col_used[col].add(val)
                    box_used[(row//4)*4 + col//4].add(val)
                    applied.append((col, val))
            
            self._dfs(depth + 1, row_order, valid_perms, col_used, box_used)
            
            # 回溯
            for col, val in applied:
                col_used[col].remove(val)
                box_used[(row//4)*4 + col//4].remove(val)
            
            if len(self.solutions) >= 100 or time.time() - self.start_time > self.time_limit:
                return


def main():
    print("="*60)
    print("專用符闔數獨求解器")
    print("="*60)
    print(f"開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    solver = SpecializedFuheSolver()
    result = solver.solve(max_solutions=50)
    
    # 保存結果
    with open("specialized_solver_result.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n" + "="*60)
    print("結果")
    print("="*60)
    print(f"解數: {result['solutions_found']}")
    print(f"探索節點: {result['nodes_explored']:,}")
    print(f"時間: {result['time_seconds']:.2f}秒")
    
    return result


if __name__ == "__main__":
    main()
