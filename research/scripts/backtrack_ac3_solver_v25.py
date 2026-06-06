#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 V25 回溯算法 + AC-3約束傳播求解器
 符闔超級數獨 - 仲裁後混合約束
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

算法特點:
1. AC-3 弧一致性約束傳播 - 提前剪枝
2. 最緊约束變量優先 (MRV) 启发式
3. 分步求解 - 逐行驗證約束傳播效果
4. 回溯搜索 - 系統性探索而非隨機
"""

from collections import defaultdict, deque
import copy
import time
from typing import Dict, List, Set, Tuple, Optional

# 92錨點數據
ANCHORS_92 = {
    # 行A (0): 4個
    (0, 2): 3, (0, 5): 12, (0, 7): 5, (0, 11): 14,
    # 行B (1): 4個
    (1, 1): 12, (1, 4): 3, (1, 6): 9, (1, 8): 6,
    # 行C (2): 16個 - 完全固定
    (2, 0): 7, (2, 1): 15, (2, 2): 3, (2, 3): 9,
    (2, 4): 11, (2, 5): 12, (2, 6): 6, (2, 7): 5,
    (2, 8): 10, (2, 9): 2, (2, 10): 1, (2, 11): 14,
    (2, 12): 13, (2, 13): 16, (2, 14): 4, (2, 15): 8,
    # 行D (3): 16個 - 完全固定
    (3, 0): 11, (3, 1): 4, (3, 2): 13, (3, 3): 7,
    (3, 4): 16, (3, 5): 8, (3, 6): 1, (3, 7): 9,
    (3, 8): 3, (3, 9): 15, (3, 10): 2, (3, 11): 6,
    (3, 12): 5, (3, 13): 14, (3, 14): 10, (3, 15): 12,
    # 行E (4): 3個
    (4, 4): 13, (4, 9): 5, (4, 12): 4,
    # 行F (5): 7個
    (5, 1): 8, (5, 4): 15, (5, 6): 4, (5, 7): 3,
    (5, 10): 10, (5, 13): 16, (5, 14): 12,
    # 行G (6): 6個
    (6, 0): 14, (6, 2): 4, (6, 3): 6, (6, 9): 9,
    (6, 12): 15, (6, 15): 2,
    # 行H (7): 6個
    (7, 1): 13, (7, 5): 5, (7, 7): 9, (7, 11): 11,
    (7, 13): 7, (7, 14): 1,
    # 行I (8): 16個 - 完全固定
    (8, 0): 13, (8, 1): 1, (8, 2): 10, (8, 3): 2,
    (8, 4): 8, (8, 5): 11, (8, 6): 16, (8, 7): 7,
    (8, 8): 14, (8, 9): 4, (8, 10): 5, (8, 11): 12,
    (8, 12): 9, (8, 13): 6, (8, 14): 3, (8, 15): 15,
    # 行J (9): 4個
    (9, 1): 5, (9, 5): 14, (9, 9): 8, (9, 11): 1,
    # 行K (10): 6個
    (10, 0): 1, (10, 2): 6, (10, 4): 10, (10, 7): 13,
    (10, 10): 9, (10, 13): 11,
    # 行L (11): 6個
    (11, 3): 4, (11, 5): 16, (11, 6): 14, (11, 8): 3,
    (11, 10): 12, (11, 12): 7,
    # 行M (12): 7個
    (12, 0): 15, (12, 4): 12, (12, 8): 5, (12, 9): 14,
    (12, 11): 8, (12, 14): 11, (12, 15): 6,
    # 行N (13): 5個
    (13, 2): 9, (13, 5): 6, (13, 8): 13, (13, 11): 15,
    (13, 15): 10,
    # 行O (14): 6個
    (14, 1): 1, (14, 4): 9, (14, 7): 15, (14, 10): 7,
    (14, 12): 16, (14, 13): 3,
    # 行P (15): 2個
    (15, 2): 2, (15, 6): 5,
}

# 符闔行定義
FUMMEL_ROWS = [2, 3, 8, 15]  # C, D, I, P


class AC3Solver:
    """AC-3 弧一致性約束傳播求解器"""
    
    def __init__(self, grid_size=16, box_size=4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.values = {}  # (r,c) -> set of possible values
        self.neighbors = defaultdict(set)  # 變量間的約束關係
        self.arcs = deque()  # AC-3的弧队列
        self.propagation_log = []
        
    def initialize_domains(self, anchors: Dict[Tuple[int,int], int]):
        """初始化所有變量的定義域"""
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if (r, c) in anchors:
                    # 錨點 - 定義域為單值
                    self.values[(r, c)] = {anchors[(r, c)]}
                else:
                    # 空單元格 - 定義域為1-16
                    self.values[(r, c)] = set(range(1, self.grid_size + 1))
        
        self._build_constraint_graph()
        
    def _build_constraint_graph(self):
        """構建約束圖 - 確定變量間的弧"""
        # 行約束
        for r in range(self.grid_size):
            for c1 in range(self.grid_size):
                for c2 in range(c1+1, self.grid_size):
                    self.neighbors[(r, c1)].add((r, c2))
                    self.neighbors[(r, c2)].add((r, c1))
                    
        # 列約束（非符闔行之間）
        for c in range(self.grid_size):
            normal_rows = [r for r in range(self.grid_size) if r not in FUMMEL_ROWS]
            for r1_idx in range(len(normal_rows)):
                for r2_idx in range(r1_idx+1, len(normal_rows)):
                    r1, r2 = normal_rows[r1_idx], normal_rows[r2_idx]
                    self.neighbors[(r1, c)].add((r2, c))
                    self.neighbors[(r2, c)].add((r1, c))
                    
        # 宮約束（非符闔行之間）
        for box_r in range(self.grid_size // self.box_size):
            for box_c in range(self.grid_size // self.box_size):
                normal_cells = []
                for dr in range(self.box_size):
                    for dc in range(self.box_size):
                        r = box_r * self.box_size + dr
                        c = box_c * self.box_size + dc
                        if r not in FUMMEL_ROWS:
                            normal_cells.append((r, c))
                for i in range(len(normal_cells)):
                    for j in range(i+1, len(normal_cells)):
                        self.neighbors[normal_cells[i]].add(normal_cells[j])
                        self.neighbors[normal_cells[j]].add(normal_cells[i])
        
        # 初始化弧队列
        self.arcs = deque()
        for x in self.values:
            for y in self.neighbors[x]:
                self.arcs.append((x, y))
    
    def revise(self, xi: Tuple[int,int], xj: Tuple[int,int]) -> bool:
        """
        AC-3 Revise 函數
        刪除xi定義域中與xj不一致的值
        返回是否修改了xi的定義域
        """
        revised = False
        xi_vals = self.values[xi]
        xj_vals = self.values[xj]
        
        # 如果xj已確定為單值，直接檢查
        if len(xj_vals) == 1:
            xj_val = next(iter(xj_vals))
            new_vals = xi_vals - {xj_val}
            if len(new_vals) != len(xi_vals):
                revised = True
                self.values[xi] = new_vals
        else:
            # 一般情況：檢查每個xi的值是否有xj的某個值支持
            for v in list(xi_vals):
                if v in xj_vals and len(xj_vals) > 1:
                    # v在xj中，但xj有多個值，可能支持
                    continue
                elif v not in xj_vals:
                    # v不在xj中，如果xj確定，則v無支持
                    if len(xj_vals) == 1:
                        revised = True
                        self.values[xi].remove(v)
        
        return revised
    
    def ac3(self, max_iterations=10000) -> bool:
        """
        AC-3 算法主體
        返回：是否達到一致性（無定義域為空）
        """
        iterations = 0
        arc_count = len(self.arcs)
        
        while self.arcs and iterations < max_iterations:
            iterations += 1
            xi, xj = self.arcs.popleft()
            
            if self.revise(xi, xj):
                if len(self.values[xi]) == 0:
                    # 定義域為空 - 約束衝突
                    self.propagation_log.append({
                        'type': 'domain_empty',
                        'var': xi,
                        'iteration': iterations
                    })
                    return False
                
                # xi的定義域被削減，需要重新檢查與xi相鄰的所有變量
                for xk in self.neighbors[xi]:
                    if xk != xj:
                        self.arcs.append((xk, xi))
        
        self.propagation_log.append({
            'type': 'ac3_complete',
            'iterations': iterations,
            'initial_arcs': arc_count,
            'final_arcs': len(self.arcs)
        })
        
        return True
    
    def get_assigned_cells(self) -> Dict[Tuple[int,int], int]:
        """獲取已確定值的單元格"""
        assigned = {}
        for var, vals in self.values.items():
            if len(vals) == 1:
                assigned[var] = next(iter(vals))
        return assigned
    
    def get_unassigned_cells(self) -> List[Tuple[int,int]]:
        """獲取未確定值的單元格"""
        return [var for var, vals in self.values.items() if len(vals) > 1]
    
    def get_domain_size(self, var: Tuple[int,int]) -> int:
        """獲取變量定義域大小"""
        return len(self.values.get(var, set()))
    
    def get_minimum_domain_var(self) -> Optional[Tuple[int,int]]:
        """MRV启发式：獲取定義域最小的未賦值變量"""
        unassigned = self.get_unassigned_cells()
        if not unassigned:
            return None
        return min(unassigned, key=lambda v: len(self.values[v]))
    
    def print_domains(self, title=''):
        """打印當前定義域狀態"""
        if title:
            print(f'\n{title}')
            print('=' * 60)
        
        for r in range(self.grid_size):
            row_str = ''
            for c in range(self.grid_size):
                vals = self.values[(r, c)]
                if len(vals) == 1:
                    row_str += f'{next(iter(vals)):2d}'
                else:
                    row_str += f' {len(vals)}'
            marker = ' <<< FUMMEL' if r in FUMMEL_ROWS else ''
            print(f'{chr(65+r):2s}: {row_str}{marker}')
        print('=' * 60)


class BacktrackSolver:
    """回溯算法求解器"""
    
    def __init__(self, grid_size=16, box_size=4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.ac3 = AC3Solver(grid_size, box_size)
        self.grid = [[0]*grid_size for _ in range(grid_size)]
        self.solution_count = 0
        self.backtrack_count = 0
        self.nodes_explored = 0
        self.time_limit = 60.0
        
    def solve(self, anchors: Dict[Tuple[int,int], int], time_limit=60.0) -> Optional[List[List[int]]]:
        """
        主求解函數
        
        流程：
        1. AC-3 約束傳播 - 提前剪枝
        2. MRV 启发式搜索 - 最緊约束變量優先
        3. 回溯 - 系統性探索
        """
        self.time_limit = time_limit
        start_time = time.time()
        
        print("=" * 60)
        print("AC-3 約束傳播 + 回溯求解")
        print("=" * 60)
        
        # Step 1: 初始化定義域
        print("\n[Step 1] 初始化定義域...")
        self.ac3.initialize_domains(anchors)
        
        # 檢查錨點是否已確定
        assigned = self.ac3.get_assigned_cells()
        print(f'  已確定單元格: {len(assigned)} / {self.grid_size**2}')
        
        # Step 2: AC-3 約束傳播
        print("\n[Step 2] AC-3 約束傳播...")
        ac3_start = time.time()
        consistent = self.ac3.ac3(max_iterations=50000)
        ac3_time = time.time() - ac3_start
        
        if not consistent:
            print("  ❌ AC-3 發現約束衝突")
            return None
        
        print(f"  ✅ AC-3 完成，耗時 {ac3_time:.3f}s")
        
        # 打印傳播後狀態
        print("\n[AC-3 後定義域狀態]")
        self.ac3.print_domains()
        
        # 統計定義域大小
        domain_sizes = defaultdict(int)
        for var, vals in self.ac3.values.items():
            domain_sizes[len(vals)] += 1
        print("定義域大小分佈:")
        for size in sorted(domain_sizes.keys()):
            print(f"  大小 {size}: {domain_sizes[size]} 個變量")
        
        # Step 3: 回溯搜索
        print("\n[Step 3] 回溯搜索...")
        self.grid = [[0]*self.grid_size for _ in range(self.grid_size)]
        
        # 複製錨點到網格
        for (r, c), val in anchors.items():
            self.grid[r][c] = val
        
        # 從AC3狀態開始搜索
        unassigned = self.ac3.get_unassigned_cells()
        if not unassigned:
            # 所有變量已確定，直接驗證
            if self._validate_grid(anchors):
                print("✅ 找到解！")
                return self.grid
            return None
        
        # 回溯搜索入口
        result = self._backtrack(start_time)
        
        print(f"\n回溯統計:")
        print(f"  訪問節點: {self.nodes_explored:,}")
        print(f"  回溯次數: {self.backtrack_count:,}")
        print(f"  總耗時: {time.time() - start_time:.3f}s")
        
        return result
    
    def _backtrack(self, start_time: float) -> Optional[List[List[int]]]:
        """回溯搜索核心"""
        # 時間檢查
        if time.time() - start_time > self.time_limit:
            return None
        
        self.nodes_explored += 1
        
        # MRV: 獲取定義域最小的未賦值變量
        var = self.ac3.get_minimum_domain_var()
        if var is None:
            # 所有變量已賦值，驗證解
            if self._validate_grid_from_values():
                self.solution_count += 1
                return [row[:] for row in self.grid]
            return None
        
        r, c = var
        domain = list(self.ac3.values[var])
        
        # 按值頻次排序（優先選擇在同行/列/宮出現少的值）
        domain = self._order_values(r, c, domain)
        
        for val in domain:
            # 賦值
            self.grid[r][c] = val
            self.ac3.values[(r, c)] = {val}
            
            # 約束傳播：刪除同行/列/宮中相同值
            saved_domains = self._save_domains()
            reduced = self._propagate_assignment(r, c, val)
            
            if reduced:
                # 繼續搜索
                result = self._backtrack(start_time)
                if result is not None:
                    return result
            
            # 回溯
            self.backtrack_count += 1
            self._restore_domains(saved_domains)
            self.grid[r][c] = 0
            self.ac3.values[(r, c)] = set(range(1, self.grid_size + 1))
        
        return None
    
    def _order_values(self, r: int, c: int, domain: List[int]) -> List[int]:
        """值排序启发式：優先選擇約束力弱的值"""
        # 簡單启发式：按值本身排序（或可擴展為度启发式）
        return sorted(domain)
    
    def _save_domains(self) -> Dict:
        """保存當前定義域狀態"""
        return {var: vals.copy() for var, vals in self.ac3.values.items()}
    
    def _restore_domains(self, saved: Dict):
        """恢復定義域狀態"""
        self.ac3.values = saved
    
    def _propagate_assignment(self, r: int, c: int, val: int) -> bool:
        """傳播賦值約束"""
        # 刪除同行其他單元格中的val
        for cc in range(self.grid_size):
            if cc != c and (r, cc) in self.ac3.values:
                if val in self.ac3.values[(r, cc)]:
                    self.ac3.values[(r, cc)].remove(val)
        
        # 刪除同列其他單元格中的val（非符闔行）
        if r not in FUMMEL_ROWS:
            for rr in range(self.grid_size):
                if rr != r and rr not in FUMMEL_ROWS and (rr, c) in self.ac3.values:
                    if val in self.ac3.values[(rr, c)]:
                        self.ac3.values[(rr, c)].remove(val)
        
        # 刪除同宮其他單元格中的val（非符闔行）
        box_r = r // self.box_size
        box_c = c // self.box_size
        for dr in range(self.box_size):
            for dc in range(self.box_size):
                nr = box_r * self.box_size + dr
                nc = box_c * self.box_size + dc
                if (nr, nc) != (r, c) and (nr, nc) in self.ac3.values:
                    if nr not in FUMMEL_ROWS and val in self.ac3.values[(nr, nc)]:
                        self.ac3.values[(nr, nc)].remove(val)
        
        # 檢查是否有定義域變為空
        for var, vals in self.ac3.values.items():
            if len(vals) == 0:
                return False
        
        return True
    
    def _validate_grid_from_values(self) -> bool:
        """從AC3狀態驗證網格"""
        # 複製值到網格
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                vals = self.ac3.values[(r, c)]
                if len(vals) != 1:
                    return False
                self.grid[r][c] = next(iter(vals))
        
        return self._validate_grid({})
    
    def _validate_grid(self, anchors: Dict) -> bool:
        """驗證網格是否滿足所有約束"""
        # 檢查錨點
        for (r, c), val in anchors.items():
            if self.grid[r][c] != val:
                return False
        
        # 檢查行
        for r in range(self.grid_size):
            if len(set(self.grid[r])) != self.grid_size:
                return False
        
        # 檢查列（非符闔行）
        for c in range(self.grid_size):
            normal_vals = [self.grid[r][c] for r in range(self.grid_size) if r not in FUMMEL_ROWS]
            if len(set(normal_vals)) != len(normal_vals):
                return False
        
        # 檢查宮（非符闔行）
        for box_r in range(4):
            for box_c in range(4):
                vals = []
                for dr in range(4):
                    for dc in range(4):
                        r = box_r * 4 + dr
                        c = box_c * 4 + dc
                        if r not in FUMMEL_ROWS:
                            vals.append(self.grid[r][c])
                if len(set(vals)) != len(vals):
                    return False
        
        return True


def incremental_solve_step(step: int, max_rows: int):
    """分步求解：逐步添加行"""
    print(f"\n{'='*60}")
    print(f"分步求解：添加前 {max_rows} 行")
    print(f"{'='*60}")
    
    # 選擇前max_rows行作為錨點
    step_anchors = {k: v for k, v in ANCHORS_92.items() if k[0] < max_rows}
    
    solver = BacktrackSolver()
    solution = solver.solve(step_anchors, time_limit=30)
    
    if solution:
        print(f"\n✅ {max_rows} 行可解！")
        print("前4行解範例:")
        for r in range(min(4, max_rows)):
            row_str = ' '.join(f'{solution[r][c]:2d}' for c in range(16))
            marker = ' <<< FUMMEL' if r in FUMMEL_ROWS else ''
            print(f'{chr(65+r):2s}: {row_str}{marker}')
    else:
        print(f"\n❌ {max_rows} 行不可解或超時")
    
    return solution


def main():
    print("=" * 70)
    print("V25 回溯算法 + AC-3 約束傳播求解器")
    print("符闔超級數獨 - 仲裁後混合約束")
    print("=" * 70)
    
    # Step 0: 分步求解演示
    print("\n" + "=" * 70)
    print("分步求解演示：逐步添加行驗證約束傳播")
    print("=" * 70)
    
    # 從最少行開始
    for step in [4, 8, 12]:
        incremental_solve_step(step, step)
    
    # Step 1: 完整求解
    print("\n" + "=" * 70)
    print("完整求解：16行全部錨點")
    print("=" * 70)
    
    solver = BacktrackSolver()
    solution = solver.solve(ANCHORS_92, time_limit=120)
    
    if solution:
        print("\n" + "=" * 70)
        print("🎉 找到完整解！")
        print("=" * 70)
        
        for r in range(16):
            row_str = ' '.join(f'{solution[r][c]:2d}' for c in range(16))
            marker = ' <<< FUMMEL' if r in FUMMEL_ROWS else ''
            print(f'{chr(65+r):2s}: {row_str}{marker}')
        
        # 驗證
        print("\n--- 驗證 ---")
        print(f'行約束: ✓')
        print(f'列約束（非符闔行）: ✓')
        print(f'宮約束（非符闔行）: ✓')
        print(f'錨點約束: ✓')
    else:
        print("\n❌ 未找到解（可能超時或約束衝突）")
    
    return solution


if __name__ == '__main__':
    main()
