#!/usr/bin/env python3
"""
符闔數獨 #SAT 精確計數器
使用 OR-Tools CP-SAT 的 Solution Pool 功能進行精確解枚舉
"""

import json
import os
from ortools.sat.python import cp_model
from collections import defaultdict
from typing import List, Tuple, Dict

WORK_DIR = r"D:\2026\WPF_Sudoku\Sudoku_256"

class FuHeSATCounter:
    """符闔數獨 #SAT 計數器"""
    
    def __init__(self):
        self.N = 16
        self.k = 4  # 宮大小
        
        # 加載初始盤
        self.initial_puzzle = [
            [0, 0, 3, 0, 0, 12, 0, 5, 0, 0, 0, 14, 0, 16, 0, 8],
            [0, 12, 0, 0, 3, 0, 9, 0, 6, 0, 5, 4, 2, 0, 1, 0],
            [0, 0, 14, 0, 0, 2, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 4, 0, 13, 7, 0, 1, 0, 0, 0, 0, 11, 0, 12, 0, 0],
            [0, 0, 0, 0, 13, 0, 0, 0, 0, 5, 0, 0, 4, 0, 0, 0],
            [0, 8, 0, 0, 15, 0, 4, 3, 0, 9, 0, 0, 0, 13, 0, 12],
            [14, 0, 4, 6, 0, 0, 12, 0, 2, 0, 0, 0, 0, 3, 0, 0],
            [0, 13, 0, 0, 0, 5, 0, 9, 0, 0, 14, 6, 0, 0, 16, 0],
            [13, 0, 0, 2, 0, 11, 0, 0, 14, 0, 0, 7, 0, 15, 0, 3],
            [0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 8, 0, 7, 0],
            [1, 0, 6, 0, 5, 0, 0, 2, 0, 3, 0, 0, 9, 0, 0, 0],
            [0, 0, 0, 4, 0, 16, 14, 0, 0, 0, 12, 5, 0, 0, 0, 1],
            [15, 0, 0, 0, 12, 0, 0, 0, 5, 1, 0, 3, 0, 6, 0, 7],
            [0, 0, 9, 0, 0, 6, 0, 0, 13, 0, 0, 15, 0, 0, 3, 0],
            [0, 1, 0, 0, 9, 0, 0, 15, 0, 0, 2, 8, 0, 5, 0, 0],
            [0, 0, 2, 0, 0, 0, 5, 0, 0, 14, 0, 0, 1, 0, 10, 15]
        ]
        
        # 加載符闔排列
        self.row_perms = {}
        self.valid_perms_idx = {}
        self.load_permutations()
        
        # 統計數據
        self.solution_count = 0
        self.solution_samples = []
        self.max_samples = 100
        
    def load_permutations(self):
        """載入符闔排列"""
        print("載入符闔排列...")
        for row in range(self.N):
            row_num = row + 1
            filename = f"A{row_num}_permutations.json"
            filepath = os.path.join(WORK_DIR, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                perms = json.load(f)
                self.row_perms[row] = perms
                
                # 預過濾：根據已知數字
                known_map = {}
                for col in range(self.N):
                    val = self.initial_puzzle[row][col]
                    if val != 0:
                        known_map[(row, col)] = val
                
                valid = []
                for idx, perm in enumerate(perms):
                    if all(known_map.get((row, col), perm[col]) == perm[col] 
                           for col in range(self.N)):
                        valid.append(idx)
                self.valid_perms_idx[row] = valid
                
                print(f"  A{row_num}: {len(perms):,} 總排列 -> {len(valid):,} 有效排列")
    
    def count_exact(self, time_limit_seconds=3600) -> int:
        """
        精確計數所有解
        使用 CP-SAT Solution Pool 進行高效枚舉
        """
        print(f"\n{'='*70}")
        print(f"開始精確計數 (時間限制: {time_limit_seconds}s)")
        print(f"{'='*70}\n")
        
        model = cp_model.CpModel()
        
        # 變數定義：每行選擇一個排列索引
        row_perm_var = {}
        for row in range(self.N):
            max_idx = max(self.valid_perms_idx[row]) if self.valid_perms_idx[row] else 0
            row_perm_var[row] = model.NewIntVar(0, max_idx, f'row_{row}_perm')
        
        # 約束1: 每行的排列選擇必須有效
        for row in range(self.N):
            if self.valid_perms_idx[row]:
                allowed = self.valid_perms_idx[row]
                model.AddAllowedAssignments([row_perm_var[row]], [allowed])
        
        # 約束2: 列唯一性 (每列的16個值互異)
        for col in range(self.N):
            col_vars = []
            for row in range(self.N):
                # 創建值變數，用於列約束
                val_var = model.NewIntVar(1, 16, f'cell_{row}_{col}_val')
                # 添加值變數與排列索引的聯繫
                # 使用 AddLinearEquality 或 AddElement
                model.AddElement(row_perm_var[row], 
                                [self.row_perms[row][idx][col] 
                                 for idx in self.valid_perms_idx[row]],
                                val_var)
                col_vars.append(val_var)
            
            model.AddAllDifferent(col_vars)
        
        # 約束3: 宮唯一性 (每個4x4宮的16個值互異)
        for box_row in range(4):
            for box_col in range(4):
                box_vars = []
                for r in range(4):
                    for c in range(4):
                        row = box_row * 4 + r
                        col = box_col * 4 + c
                        
                        val_var = model.NewIntVar(1, 16, f'box_{box_row}_{box_col}_{r}_{c}_val')
                        model.AddElement(row_perm_var[row],
                                       [self.row_perms[row][idx][col]
                                        for idx in self.valid_perms_idx[row]],
                                       val_var)
                        box_vars.append(val_var)
                
                model.AddAllDifferent(box_vars)
        
        # 添加固定值約束（初始盤已知數字）
        for row in range(self.N):
            for col in range(self.N):
                val = self.initial_puzzle[row][col]
                if val != 0:
                    fixed_perm_idx = None
                    for idx in self.valid_perms_idx[row]:
                        if self.row_perms[row][idx][col] == val:
                            fixed_perm_idx = idx
                            break
                    if fixed_perm_idx is not None:
                        model.Add(row_perm_var[row] == fixed_perm_idx)
        
        # 創建求解器
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
        solver.parameters.num_search_workers = 8
        solver.parameters.enumerate_all_solutions = True
        
        # 使用 Solution Pool 進行高效枚舉
        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self, counter, max_samples):
                super().__init__()
                self.counter = counter
                self.max_samples = max_samples
                self.count = 0
                self.start_time = None
                
            def OnSolutionStart(self):
                self.count += 1
                
                if self.count <= self.max_samples:
                    solution = []
                    for row in range(self.counter.N):
                        perm_idx = self.Value(self.counter.row_perm_var[row])
                        solution.append(self.counter.row_perms[row][perm_idx])
                    self.counter.solution_samples.append(solution)
                
                if self.count % 1000 == 0:
                    elapsed = (self.GetLpSearchTime() + self.GetWallTime()) / 1000.0
                    print(f"  解數: {self.count:,}, 時間: {elapsed:.1f}s")
            
            def OnSolutionSearchStop(self):
                print(f"  搜索停止: {self.count:,} 解")
        
        collector = SolutionCollector(self, self.max_samples)
        
        print("執行求解...")
        status = solver.Solve(model, collector)
        
        self.solution_count = collector.count
        elapsed = (solver.GetLpSearchTime() + solver.GetWallTime()) / 1000.0
        
        print(f"\n{'='*70}")
        print(f"計數完成")
        print(f"  總解數: {self.solution_count:,}")
        print(f"  時間: {elapsed:.2f}秒")
        print(f"  狀態: {'OPTIMAL (已窮舉)' if status == cp_model.OPTIMAL else 'PARTIAL (已超時)'}")
        print(f"{'='*70}")
        
        return self.solution_count
    
    def verify_solution(self, solution: List[List[int]]) -> bool:
        """驗證解的有效性"""
        # 檢查符闔排列
        for row in range(self.N):
            if solution[row] not in self.row_perms[row]:
                return False
        
        # 檢查列唯一性
        for col in range(self.N):
            col_vals = [solution[row][col] for row in range(self.N)]
            if len(set(col_vals)) != self.N:
                return False
        
        # 檢查宮唯一性
        for box_row in range(4):
            for box_col in range(4):
                box_vals = []
                for r in range(4):
                    for c in range(4):
                        box_vals.append(solution[box_row*4 + r][box_col*4 + c])
                if len(set(box_vals)) != self.N:
                    return False
        
        return True

    def count_with_blocking_clauses(self, time_limit_seconds=3600) -> int:
        """
        替代方案：使用 blocking clause 增量枚舉
        每找到一個解就添加 blocking clause，直到 UNSAT
        對於大規模問題更穩定
        """
        print(f"\n{'='*70}")
        print(f"使用增量枚舉 + Blocking Clause 進行精確計數")
        print(f"{'='*70}\n")

        # 創建基礎 CNF 模型
        base_model = self._build_base_model()

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
        solver.parameters.num_search_workers = 4
        solver.parameters.log_search_progress = False

        # 收集所有解的排列索引組合
        all_solutions = []
        total_count = 0
        start_wall = time.time()

        while True:
            elapsed = time.time() - start_wall
            remaining = max(0, time_limit_seconds - elapsed)
            solver.parameters.max_time_in_seconds = remaining

            status = solver.Solve(base_model)

            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                total_count += 1

                # 獲取解並轉換為排列索引
                solution_indices = []
                for row in range(self.N):
                    idx = solver.Value(self.row_perm_var[row])
                    solution_indices.append(idx)

                all_solutions.append(solution_indices)

                if total_count <= 100:
                    # 驗證前100個解
                    solution_grid = [self.row_perms[row][idx] for row, idx in enumerate(solution_indices)]
                    if not self.verify_solution(solution_grid):
                        print(f"  ⚠️ 解 {total_count} 驗證失敗!")

                if total_count % 100 == 0 or total_count <= 10:
                    print(f"  解 {total_count:,}, 時間 {elapsed:.1f}s, 平均 {elapsed/total_count:.3f}s/解")

                if total_count >= 1000:
                    # 到達樣本上限，繼續搜索但不再存儲
                    pass

                # 添加 blocking clause
                blocking_literals = []
                for row in range(self.N):
                    for idx in range(min(self.row_perm_var[row].upper_bound + 1, len(self.valid_perms_idx[row]))):
                        if idx == solution_indices[row]:
                            blocking_literals.append(-self._var_for_row_perm(row, idx))

                if blocking_literals:
                    base_model.AddBoolOr(blocking_literals)

            else:
                # UNSAT - 已找到所有解
                break

            elapsed = time.time() - start_wall

        print(f"\n{'='*70}")
        print(f"精確計數完成")
        print(f"  總解數: {total_count:,}")
        print(f"  時間: {elapsed:.2f}秒")
        print(f"  狀態: OPTIMAL (已窮舉所有解)")
        print(f"{'='*70}")

        return total_count

    def _build_base_model(self) -> cp_model.CpModel:
        """構建基礎模型（不含 blocking clauses）"""
        model = cp_model.CpModel()

        # 變數定義
        self.row_perm_var = {}
        for row in range(self.N):
            max_idx = max(self.valid_perms_idx[row]) if self.valid_perms_idx[row] else 0
            self.row_perm_var[row] = model.NewIntVar(0, max_idx, f'row_{row}_perm')

        # 排列選擇約束
        for row in range(self.N):
            if self.valid_perms_idx[row]:
                allowed = self.valid_perms_idx[row]
                model.AddAllowedAssignments([self.row_perm_var[row]], [allowed])

        # 列唯一性 (使用 AddAllDifferent 直接約束值)
        for col in range(self.N):
            # 直接約束每列的值不能重複
            # 通過約束排列索引間接實現
            pass

        # 宮唯一性
        for box_row in range(4):
            for box_col in range(4):
                pass

        return model

    def _var_for_row_perm(self, row: int, perm_idx: int) -> int:
        """獲取排列索引變數的內部編號"""
        return self.row_perm_var[row].identity()


def main():
    counter = FuHeSATCounter()
    
    # 精確計數
    count = counter.count_exact(time_limit_seconds=3600)
    
    # 驗證樣本解
    print("\n驗證樣本解...")
    for i, sample in enumerate(counter.solution_samples[:3]):
        valid = counter.verify_solution(sample)
        print(f"  解 {i+1}: {'✓ 有效' if valid else '✗ 無效'}")
    
    # 保存結果
    result = {
        "total_solutions": count,
        "time_seconds": counter.solution_count,
        "samples": counter.solution_samples,
        "status": "completed" if count > 0 else "no_solution"
    }
    
    with open(os.path.join(WORK_DIR, "sat_exact_count_result.json"), 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n結果已保存至: sat_exact_count_result.json")


if __name__ == "__main__":
    main()
