#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分治策略求解器 - 16×16 符闔數獨
將16×16分解為4個4×4子問題，分別求解後合併
"""

import json
import time
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
from datetime import datetime


class DivideAndConquerSolver:
    """分治求解器"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16
        self.box_size = 4
        self.sub_size = 4  # 4×4 子問題
        
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        # 4個子問題
        self.sub_problems = []
        
        self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """載入配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'known_digits' in config:
            for clue in config['known_digits']:
                r, c = clue['row']-1, clue['col']-1
                self.known_map[(r, c)] = clue['value']
        
        for row in range(self.N):
            try:
                with open(f"A{row+1}_permutations.json", 'r', encoding='utf-8') as f:
                    self.row_perms[row] = json.load(f)
            except:
                pass
        
        self._create_sub_problems()
    
    def _create_sub_problems(self):
        """創建4個4×4子問題"""
        # 將16×16分為4個4×4子區域
        # 子問題0: 行0-7, 列0-7 (左上)
        # 子問題1: 行0-7, 列8-15 (右上)
        # 子問題2: 行8-15, 列0-7 (左下)
        # 子問題3: 行8-15, 列8-15 (右下)
        
        sub_ranges = [
            ((0, 8), (0, 8)),   # 左上
            ((0, 8), (8, 16)),  # 右上
            ((8, 16), (0, 8)),  # 左下
            ((8, 16), (8, 16)), # 右下
        ]
        
        for idx, (row_range, col_range) in enumerate(sub_ranges):
            sub = {
                'id': idx,
                'row_start': row_range[0],
                'row_end': row_range[1],
                'col_start': col_range[0],
                'col_end': col_range[1],
                'size': 8,  # 8×8 子問題
                'known': {},
                'row_constraints': [],
            }
            
            # 提取該子區域的已知數字
            for r in range(row_range[0], row_range[1]):
                for c in range(col_range[0], col_range[1]):
                    if (r, c) in self.known_map:
                        sub['known'][(r - row_range[0], c - col_range[0])] = self.known_map[(r, c)]
            
            # 提取該子區域的排列約束（行部分）
            for r in range(row_range[0], row_range[1]):
                sub['row_constraints'].append({
                    'original_row': r,
                    'perms': self.row_perms[r],
                })
            
            self.sub_problems.append(sub)
            
            print(f"子問題{idx}: 行{row_range[0]}-{row_range[1]-1}, 列{col_range[0]}-{col_range[1]-1}")
            print(f"  已知數字: {len(sub['known'])} 個")
    
    def solve_sub_problem(self, sub: Dict, limit: int = 100) -> List[Dict]:
        """求解單個子問題"""
        solutions = []
        
        # 子問題大小
        size = sub['size']
        
        # 列約束
        col_used = [set() for _ in range(size)]
        
        # 初始化已知數字
        for (r, c), v in sub['known'].items():
            col_used[c].add(v)
        
        # DFS搜索
        def dfs(row: int, grid: List[List[int]]):
            if len(solutions) >= limit:
                return
            
            if row == size:
                solutions.append({'grid': [r[:] for r in grid]})
                return
            
            # 獲取該行的有效排列
            orig_row = sub['row_constraints'][row]['original_row']
            perms = sub['row_constraints'][row]['perms']
            
            # 篩選有效排列
            valid_perms = []
            for perm in perms:
                # 只取該子區域的部分
                start_col = sub['col_start']
                sub_perm = perm[start_col:start_col + size]
                
                # 檢查是否符合已知數字
                ok = True
                for c, v in enumerate(sub_perm):
                    if (row, c) in sub['known']:
                        if sub['known'][(row, c)] != v:
                            ok = False
                            break
                    if v in col_used[c]:
                        ok = False
                        break
                
                if ok:
                    valid_perms.append(sub_perm)
            
            for sub_perm in valid_perms:
                # 應用
                for c, v in enumerate(sub_perm):
                    col_used[c].add(v)
                    grid[row][c] = v
                
                dfs(row + 1, grid)
                
                # 回溯
                for c, v in enumerate(sub_perm):
                    col_used[c].remove(v)
                
                if len(solutions) >= limit:
                    return
        
        # 初始化空網格
        grid = [[0] * size for _ in range(size)]
        dfs(0, grid)
        
        return solutions
    
    def merge_sub_solutions(self, sub_solutions: List[List[Dict]]) -> List[Dict]:
        """合併子問題解"""
        # 取每個子問題的第一個解進行測試
        merged = []
        
        for i in range(min(10, len(sub_solutions[0]))):
            combined_grid = [[0] * self.N for _ in range(self.N)]
            
            valid = True
            for sub_idx, solutions in enumerate(sub_solutions):
                if i >= len(solutions):
                    valid = False
                    break
                
                sol = solutions[i]
                sub = self.sub_problems[sub_idx]
                
                for r in range(sub['size']):
                    for c in range(sub['size']):
                        orig_r = sub['row_start'] + r
                        orig_c = sub['col_start'] + c
                        combined_grid[orig_r][orig_c] = sol['grid'][r][c]
            
            if valid:
                merged.append({'grid': combined_grid})
        
        return merged
    
    def verify_solution(self, grid: List[List[int]]) -> Tuple[bool, List[str]]:
        """驗證完整解"""
        errors = []
        
        # 檢查已知數字
        for (r, c), expected in self.known_map.items():
            if grid[r][c] != expected:
                errors.append(f"已知數字錯誤: ({r},{c}) 期望{expected}, 實際{grid[r][c]}")
        
        # 檢查列約束
        for c in range(self.N):
            vals = [grid[r][c] for r in range(self.N)]
            if len(set(vals)) != self.N:
                errors.append(f"列{c}有重複值")
        
        # 檢查宮約束
        for br in range(self.box_size):
            for bc in range(self.box_size):
                vals = []
                for dr in range(self.box_size):
                    for dc in range(self.box_size):
                        vals.append(grid[br*4+dr][bc*4+dc])
                if len(set(vals)) != self.N:
                    errors.append(f"宮({br},{bc})有重複值")
        
        return len(errors) == 0, errors
    
    def solve(self, sub_limit: int = 50) -> Dict:
        """主求解方法"""
        start_time = time.time()
        
        print("="*60)
        print("分治策略求解 - 16×16 符闔數獨")
        print("="*60)
        
        # 求解每個子問題
        all_sub_solutions = []
        for idx, sub in enumerate(self.sub_problems):
            print(f"\n求解子問題{idx}...")
            sols = self.solve_sub_problem(sub, limit=sub_limit)
            print(f"  找到 {len(sols)} 個解")
            all_sub_solutions.append(sols)
        
        # 合併解
        print("\n合併子問題解...")
        merged = self.merge_sub_solutions(all_sub_solutions)
        print(f"  合併得到 {len(merged)} 個候選解")
        
        # 驗證
        valid_solutions = []
        for sol in merged:
            is_valid, errors = self.verify_solution(sol['grid'])
            if is_valid:
                valid_solutions.append(sol)
            else:
                print(f"  驗證失敗: {errors[:2]}")
        
        elapsed = time.time() - start_time
        
        result = {
            'sub_problems': len(self.sub_problems),
            'solutions_per_sub': [len(s) for s in all_sub_solutions],
            'merged_candidates': len(merged),
            'valid_solutions': len(valid_solutions),
            'time_seconds': round(elapsed, 2),
            'solutions': valid_solutions[:5] if valid_solutions else [],
            'sub_solutions': all_sub_solutions
        }
        
        return result


def main():
    print("="*60)
    print("分治策略求解器")
    print("="*60)
    print(f"開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    solver = DivideAndConquerSolver()
    result = solver.solve(sub_limit=50)
    
    # 保存結果
    with open("divide_conquer_result.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n" + "="*60)
    print("結果")
    print("="*60)
    print(f"子問題數: {result['sub_problems']}")
    print(f"每個子問題解數: {result['solutions_per_sub']}")
    print(f"合併候選解: {result['merged_candidates']}")
    print(f"有效解: {result['valid_solutions']}")
    print(f"時間: {result['time_seconds']:.2f}秒")
    
    return result


if __name__ == "__main__":
    main()
