#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一求解器 - 自動選擇最佳算法

求解策略優先級:
  1. CP-SAT + 符闔排列過濾  (最快, ~43s, 需要 OR-Tools + 排列文件)
  2. CP-SAT 標準模型        (可靠, ~0.14s/92錨點, 需要 OR-Tools)
  3. 回溯 + AC-3            (純 Python 備用, 不需要外部依賴)

自動選擇邏輯:
  - 探測 OR-Tools 是否可用
  - 探測排列文件是否可用
  - 選擇當前環境下的最佳策略
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .constants import (
    N, BOX_SIZE, VALUES, ROW_LABELS,
    ANCHORS_92, INITIAL_PUZZLE_92, PERM_STATS,
    anchors_to_grid, puzzle_dict_to_grid, count_anchors, box_index,
)
from .loader import DataLoader
from .propagator import PermutationFilter, AC3Propagator
from .verifier import SolutionVerifier


# ═══════════════════════════════════════════════════════════════
#  結果數據類
# ═══════════════════════════════════════════════════════════════

@dataclass
class SolveResult:
    """求解結果"""
    status: str               # SOLVED / INFEASIBLE / TIMEOUT / ERROR
    solution: Optional[List[List[int]]] = None
    solver_name: str = ""
    strategy: str = ""
    anchor_count: int = 0
    filter_time: float = 0.0
    solve_time: float = 0.0
    total_time: float = 0.0
    filter_stats: List[dict] = field(default_factory=list)
    verification: dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """轉化為可 JSON 序列化的字典"""
        return {
            "status": self.status,
            "solver": self.solver_name,
            "strategy": self.strategy,
            "anchor_count": self.anchor_count,
            "filter_time_sec": round(self.filter_time, 3),
            "solve_time_sec": round(self.solve_time, 3),
            "total_time_sec": round(self.total_time, 3),
            "solution": self.solution,
            "verification": self.verification,
            "filter_stats": self.filter_stats,
            "errors": self.errors,
            "timestamp": datetime.now().isoformat(),
            "metadata": self.metadata,
        }

    def save(self, filepath: str):
        """保存結果到 JSON 檔案"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  求解器引擎
# ═══════════════════════════════════════════════════════════════

class Sudoku256Solver:
    """
    16x16 符闔超級數獨統一求解器。

    使用方式:
        engine = Sudoku256Solver()
        result = engine.solve()
        print(result.status)
    """

    def __init__(self, base_dir: str = None, verbose: bool = True):
        self.loader = DataLoader(base_dir)
        self.verbose = verbose
        self._ortools_available = None

    def _log(self, msg: str):
        """條件式日誌輸出"""
        if self.verbose:
            print(msg, flush=True)

    # ─────────────────────────────────────────────
    #  環境探測
    # ─────────────────────────────────────────────

    def _check_ortools(self) -> bool:
        """檢測 OR-Tools 是否可用"""
        if self._ortools_available is None:
            try:
                from ortools.sat.python import cp_model
                self._ortools_available = True
            except ImportError:
                self._ortools_available = False
        return self._ortools_available

    def _detect_strategy(self) -> str:
        """
        自動探測最佳求解策略。

        回傳:
            "cpsat_perm"   - CP-SAT + 符闔排列 (最佳)
            "cpsat_plain"  - CP-SAT 標準模型 (次佳)
            "backtrack"    - 回溯 + AC-3 (備用)
        """
        has_ortools = self._check_ortools()
        perm_files = self.loader.find_permutation_files()
        has_perms = len(perm_files) == N

        if has_ortools and has_perms:
            return "cpsat_perm"
        elif has_ortools:
            return "cpsat_plain"
        else:
            return "backtrack"

    # ─────────────────────────────────────────────
    #  主求解入口
    # ─────────────────────────────────────────────

    def solve(self, grid: List[List[int]] = None,
              time_limit: float = 300.0,
              strategy: str = None,
              extra_anchors: Dict[Tuple[int, int], int] = None) -> SolveResult:
        """
        求解 16x16 數獨。

        參數:
            grid: 16x16 初始網格 (None = 使用 92 錨點)
            time_limit: 超時秒數
            strategy: 強制指定策略 ("cpsat_perm" / "cpsat_plain" / "backtrack")
            extra_anchors: 額外錨點 {(row, col): value}

        回傳:
            SolveResult
        """
        t_start = time.time()

        # 初始化網格
        if grid is None:
            grid = anchors_to_grid(ANCHORS_92)

        # 加入額外錨點
        if extra_anchors:
            for (r, c), v in extra_anchors.items():
                if grid[r][c] != 0 and grid[r][c] != v:
                    return SolveResult(
                        status="ERROR",
                        errors=[f"額外錨點衝突: ({r},{c}) 現有{grid[r][c]} vs 新{v}"],
                        total_time=time.time() - t_start,
                    )
                grid[r][c] = v

        anchor_count = count_anchors(grid)

        # 選擇策略
        if strategy is None:
            strategy = self._detect_strategy()

        strategy_names = {
            "cpsat_perm": "CP-SAT + 符闔排列過濾",
            "cpsat_plain": "CP-SAT 標準 AllDifferent 模型",
            "backtrack": "回溯搜索 + AC-3 約束傳播",
        }
        self._log("=" * 64)
        self._log(f"  256 數獨求解器 v2.0")
        self._log(f"  策略: {strategy_names.get(strategy, strategy)}")
        self._log(f"  錨點: {anchor_count} 個")
        self._log(f"  時限: {time_limit}s")
        self._log("=" * 64)

        # 執行求解
        if strategy == "cpsat_perm":
            result = self._solve_cpsat_perm(grid, time_limit)
        elif strategy == "cpsat_plain":
            result = self._solve_cpsat_plain(grid, time_limit)
        elif strategy == "backtrack":
            result = self._solve_backtrack(grid, time_limit)
        else:
            result = SolveResult(
                status="ERROR",
                errors=[f"未知策略: {strategy}"],
            )

        result.anchor_count = anchor_count
        result.total_time = time.time() - t_start
        result.strategy = strategy

        # 驗證解
        if result.solution is not None:
            verifier = SolutionVerifier(result.solution)
            result.verification = verifier.verify_all(anchors=ANCHORS_92)

        # 輸出摘要
        self._print_summary(result)

        return result

    # ─────────────────────────────────────────────
    #  策略 1: CP-SAT + 符闔排列過濾
    # ─────────────────────────────────────────────

    def _solve_cpsat_perm(self, grid: List[List[int]],
                          time_limit: float) -> SolveResult:
        """CP-SAT 精確覆蓋 + 符闔排列預過濾 (最佳策略)"""
        from ortools.sat.python import cp_model

        result = SolveResult(
            status="UNKNOWN",
            solver_name="CP-SAT + Permutation Filter",
        )

        # 加載排列
        self._log("\n[1] 加載符闔排列...")
        perm_sets = self.loader.load_all_permutations()
        total_perms = sum(len(p) for p in perm_sets)
        self._log(f"    總排列數: {total_perms:,}")

        # 過濾
        self._log("\n[2] 三層約束過濾...")
        t_filter = time.time()
        pf = PermutationFilter(grid, perm_sets)
        filtered, filter_info = pf.filter_all()
        filter_time = time.time() - t_filter
        result.filter_time = filter_time

        if filtered is None:
            result.status = "BUILD_FAILED"
            result.errors = filter_info if isinstance(filter_info, list) else [str(filter_info)]
            return result

        # 過濾統計
        total_valid = sum(len(f) for f in filtered)
        for r in range(N):
            orig = len(perm_sets[r])
            filt = len(filtered[r])
            pct = filt / orig * 100 if orig > 0 else 0
            result.filter_stats.append({
                "row": r + 1,
                "original": orig,
                "filtered": filt,
                "ratio_pct": round(pct, 2),
            })
            self._log(
                f"    行{r + 1:2d}: {orig:>8,} -> {filt:>6,} ({pct:.1f}%)"
            )

        self._log(f"    過濾耗時: {filter_time:.3f}s")
        self._log(f"    有效排列: {total_valid:,}")

        # CP-SAT 建模
        self._log("\n[3] CP-SAT 精確覆蓋建模...")
        t_solve = time.time()

        model = cp_model.CpModel()

        # 布爾變量: x[r][k] = 第 r 行選擇第 k 個排列
        x = []
        for r in range(N):
            row_vars = [
                model.NewBoolVar(f"x_{r}_{k}")
                for k in range(len(filtered[r]))
            ]
            x.append(row_vars)
            model.AddExactlyOne(row_vars)

        # 單元格值變量 (用於列/宮約束)
        cell_val = {}
        for r in range(N):
            for c in range(N):
                if grid[r][c] != 0:
                    cell_val[(r, c)] = grid[r][c]
                else:
                    v = model.NewIntVar(1, N, f"v_{r}_{c}")
                    cell_val[(r, c)] = v
                    # 值鏈接: v = sum(perm[k][c] * x[r][k])
                    model.Add(
                        v == sum(
                            filtered[r][k][c] * x[r][k]
                            for k in range(len(filtered[r]))
                        )
                    )

        # 識別符闔行間的列衝突
        fuhe_rows = {2, 3, 8}  # C, D, I
        fixed_fuhe = {r for r in fuhe_rows if all(grid[r][c] != 0 for c in range(N))}

        # 找出有符闔行間列衝突的列
        col_conflict_cols = set()
        for c in range(N):
            fuhe_vals_in_col = []
            for r in fixed_fuhe:
                fuhe_vals_in_col.append(grid[r][c])
            if len(fuhe_vals_in_col) != len(set(fuhe_vals_in_col)):
                col_conflict_cols.add(c)

        if col_conflict_cols:
            self._log(f"    放鬆列: {sorted(col_conflict_cols)} (符闔行間列衝突)")

        # 列 AllDifferent (嚴格列: 全部16行; 放鬆列: 非符闔行 + 排除約束)
        for c in range(N):
            if c not in col_conflict_cols:
                model.AddAllDifferent([cell_val[(r, c)] for r in range(N)])
            else:
                # 放鬆列: 非符闔行彼此不同 + 不等於任何符闔行值
                non_fuhe_cells = [
                    cell_val[(r, c)] for r in range(N) if r not in fixed_fuhe
                ]
                if len(non_fuhe_cells) > 1:
                    model.AddAllDifferent(non_fuhe_cells)
                fuhe_vals = {grid[r][c] for r in fixed_fuhe}
                for cell in non_fuhe_cells:
                    for fv in fuhe_vals:
                        model.Add(cell != fv)

        # 識別「放鬆宮格」: 含有多個完全固定符闔行且彼此有值衝突的宮格
        fuhe_rows = {2, 3, 8}  # C, D, I
        fixed_fuhe = {r for r in fuhe_rows if all(grid[r][c] != 0 for c in range(N))}
        relaxed_boxes = set()
        for b in range(N):
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE
            box_fixed_fuhe = [
                r for r in range(br, br + BOX_SIZE) if r in fixed_fuhe
            ]
            if len(box_fixed_fuhe) >= 2:
                # 檢查這些固定符闔行在此宮格內是否有值衝突
                vals_seen = set()
                has_conflict = False
                for r in box_fixed_fuhe:
                    for dc in range(BOX_SIZE):
                        v = grid[r][bc + dc]
                        if v in vals_seen:
                            has_conflict = True
                            break
                        vals_seen.add(v)
                    if has_conflict:
                        break
                if has_conflict:
                    relaxed_boxes.add(b)

        if relaxed_boxes:
            self._log(f"    放鬆宮格: {sorted(relaxed_boxes)} (符闔行間有預期衝突)")

        # 宮 AllDifferent (嚴格宮格 + 放鬆宮格分別處理)
        for b in range(N):
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE

            if b not in relaxed_boxes:
                # 嚴格宮格: 標準 AllDifferent
                box_cells = [
                    cell_val[(br + dr, bc + dc)]
                    for dr in range(BOX_SIZE)
                    for dc in range(BOX_SIZE)
                ]
                model.AddAllDifferent(box_cells)
            else:
                # 放鬆宮格: 收集固定符闔行的已用值
                fixed_vals = set()
                non_fixed_cells = []
                for dr in range(BOX_SIZE):
                    r = br + dr
                    for dc in range(BOX_SIZE):
                        c = bc + dc
                        if r in fixed_fuhe:
                            fixed_vals.add(grid[r][c])
                        else:
                            non_fixed_cells.append(cell_val[(r, c)])

                # 非固定行的宮格值不能與固定符闔行衝突
                for cell in non_fixed_cells:
                    for fv in fixed_vals:
                        model.Add(cell != fv)

                # 非固定行的宮格值彼此不同
                if len(non_fixed_cells) > 1:
                    model.AddAllDifferent(non_fixed_cells)

        # 求解
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 8

        self._log("    求解中...")
        status = solver.Solve(model)
        result.solve_time = time.time() - t_solve

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            sol_grid = [[0] * N for _ in range(N)]
            for r in range(N):
                for k, var in enumerate(x[r]):
                    if solver.Value(var) == 1:
                        sol_grid[r] = list(filtered[r][k])
                        break
            result.status = "SOLVED"
            result.solution = sol_grid
            self._log(f"    求解耗時: {solver.WallTime():.3f}s")
        elif status == cp_model.INFEASIBLE:
            result.status = "INFEASIBLE"
            self._log("    無解 (約束系統不可滿足)")
        else:
            result.status = "TIMEOUT"
            self._log(f"    超時 ({time_limit}s)")

        return result

    # ─────────────────────────────────────────────
    #  策略 2: CP-SAT 標準模型 (無需排列文件)
    # ─────────────────────────────────────────────

    def _solve_cpsat_plain(self, grid: List[List[int]],
                           time_limit: float) -> SolveResult:
        """CP-SAT 標準 AllDifferent 模型 (無需排列文件)"""
        from ortools.sat.python import cp_model

        result = SolveResult(
            status="UNKNOWN",
            solver_name="CP-SAT Standard Model",
        )

        self._log("\n[1] CP-SAT 標準模型建模...")
        t_solve = time.time()

        model = cp_model.CpModel()

        # 變量
        cells = {}
        for r in range(N):
            for c in range(N):
                if grid[r][c] != 0:
                    var = model.NewIntVar(grid[r][c], grid[r][c], f"c_{r}_{c}")
                else:
                    var = model.NewIntVar(1, N, f"c_{r}_{c}")
                cells[(r, c)] = var

        # 行 AllDifferent
        for r in range(N):
            model.AddAllDifferent([cells[(r, c)] for c in range(N)])

        # 識別符闔行與放鬆約束
        fuhe_rows = {2, 3, 8}
        fixed_fuhe = {r for r in fuhe_rows if all(grid[r][c] != 0 for c in range(N))}

        # 列衝突檢測
        col_conflict_cols = set()
        for c in range(N):
            fuhe_vals_in_col = [grid[r][c] for r in fixed_fuhe]
            if len(fuhe_vals_in_col) != len(set(fuhe_vals_in_col)):
                col_conflict_cols.add(c)

        # 列 AllDifferent
        for c in range(N):
            if c not in col_conflict_cols:
                model.AddAllDifferent([cells[(r, c)] for r in range(N)])
            else:
                non_fuhe_cells = [
                    cells[(r, c)] for r in range(N) if r not in fixed_fuhe
                ]
                if len(non_fuhe_cells) > 1:
                    model.AddAllDifferent(non_fuhe_cells)
                fuhe_vals = {grid[r][c] for r in fixed_fuhe}
                for cell in non_fuhe_cells:
                    for fv in fuhe_vals:
                        model.Add(cell != fv)

        # 識別放鬆宮格 (與 cpsat_perm 策略相同邏輯)
        fuhe_rows = {2, 3, 8}
        fixed_fuhe = {r for r in fuhe_rows if all(grid[r][c] != 0 for c in range(N))}
        relaxed_boxes = set()
        for b in range(N):
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE
            box_fixed_fuhe = [r for r in range(br, br + BOX_SIZE) if r in fixed_fuhe]
            if len(box_fixed_fuhe) >= 2:
                vals_seen = set()
                has_conflict = False
                for r in box_fixed_fuhe:
                    for dc in range(BOX_SIZE):
                        v = grid[r][bc + dc]
                        if v in vals_seen:
                            has_conflict = True
                            break
                        vals_seen.add(v)
                    if has_conflict:
                        break
                if has_conflict:
                    relaxed_boxes.add(b)

        # 宮 AllDifferent
        for b in range(N):
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE
            if b not in relaxed_boxes:
                box_cells = [
                    cells[(br + dr, bc + dc)]
                    for dr in range(BOX_SIZE)
                    for dc in range(BOX_SIZE)
                ]
                model.AddAllDifferent(box_cells)
            else:
                fixed_vals = set()
                non_fixed_cells = []
                for dr in range(BOX_SIZE):
                    r = br + dr
                    for dc in range(BOX_SIZE):
                        c = bc + dc
                        if r in fixed_fuhe:
                            fixed_vals.add(grid[r][c])
                        else:
                            non_fixed_cells.append(cells[(r, c)])
                for cell in non_fixed_cells:
                    for fv in fixed_vals:
                        model.Add(cell != fv)
                if len(non_fixed_cells) > 1:
                    model.AddAllDifferent(non_fixed_cells)

        # 求解
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 8

        self._log("    求解中...")
        status = solver.Solve(model)
        result.solve_time = time.time() - t_solve

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            sol_grid = [[0] * N for _ in range(N)]
            for r in range(N):
                for c in range(N):
                    sol_grid[r][c] = solver.Value(cells[(r, c)])
            result.status = "SOLVED"
            result.solution = sol_grid
            self._log(f"    求解耗時: {solver.WallTime():.3f}s")
        elif status == cp_model.INFEASIBLE:
            result.status = "INFEASIBLE"
            self._log("    無解")
        else:
            result.status = "TIMEOUT"
            self._log(f"    超時 ({time_limit}s)")

        return result

    # ─────────────────────────────────────────────
    #  策略 3: 回溯 + AC-3 (純 Python 備用)
    # ─────────────────────────────────────────────

    def _solve_backtrack(self, grid: List[List[int]],
                         time_limit: float) -> SolveResult:
        """回溯搜索 + AC-3 約束傳播 (不依賴 OR-Tools)"""
        result = SolveResult(
            status="UNKNOWN",
            solver_name="Backtrack + AC-3",
        )

        self._log("\n[1] AC-3 約束傳播...")
        t_solve = time.time()

        propagator = AC3Propagator(grid)
        success, iterations = propagator.run()
        self._log(f"    AC-3 迭代: {iterations:,} 次")
        self._log(f"    剩餘候選: {propagator.total_candidates()}")

        if not success:
            result.status = "INFEASIBLE"
            result.solve_time = time.time() - t_solve
            self._log("    AC-3 判定無解")
            return result

        if propagator.is_solved():
            result.status = "SOLVED"
            result.solution = propagator.get_grid()
            result.solve_time = time.time() - t_solve
            self._log("    AC-3 直接求解!")
            return result

        # 回溯搜索
        self._log("\n[2] 回溯搜索...")
        domains = propagator.get_candidates()
        t_deadline = time.time() + time_limit

        sol = self._backtrack_search(grid, domains, t_deadline)
        result.solve_time = time.time() - t_solve

        if sol is not None:
            result.status = "SOLVED"
            result.solution = sol
        elif time.time() >= t_deadline:
            result.status = "TIMEOUT"
        else:
            result.status = "INFEASIBLE"

        return result

    def _backtrack_search(self, grid: List[List[int]],
                          domains: Dict[Tuple[int, int], set],
                          t_deadline: float) -> Optional[List[List[int]]]:
        """MRV 啟發式回溯搜索"""
        # 深拷貝
        dom = {k: set(v) for k, v in domains.items()}

        # 找最小候選域的空格 (MRV)
        best_cell = None
        best_size = N + 1
        for r in range(N):
            for c in range(N):
                if grid[r][c] == 0:
                    sz = len(dom[(r, c)])
                    if sz == 0:
                        return None
                    if sz < best_size:
                        best_size = sz
                        best_cell = (r, c)

        if best_cell is None:
            # 所有格子都已填充
            return [row[:] for row in grid]

        if time.time() > t_deadline:
            return None

        r, c = best_cell
        for val in sorted(dom[(r, c)]):
            # 嘗試賦值
            grid[r][c] = val
            new_dom = {k: set(v) for k, v in dom.items()}
            new_dom[(r, c)] = {val}

            # 前向檢查
            if self._forward_check(r, c, val, new_dom):
                result = self._backtrack_search(grid, new_dom, t_deadline)
                if result is not None:
                    return result

            # 回溯
            grid[r][c] = 0

        return None

    def _forward_check(self, r: int, c: int, val: int,
                       domains: Dict[Tuple[int, int], set]) -> bool:
        """前向檢查: 從相關單元的域中移除 val"""
        # 行
        for cc in range(N):
            if cc != c:
                domains[(r, cc)].discard(val)
                if not domains[(r, cc)]:
                    return False
        # 列
        for rr in range(N):
            if rr != r:
                domains[(rr, c)].discard(val)
                if not domains[(rr, c)]:
                    return False
        # 宮
        br = (r // BOX_SIZE) * BOX_SIZE
        bc = (c // BOX_SIZE) * BOX_SIZE
        for dr in range(BOX_SIZE):
            for dc in range(BOX_SIZE):
                rr, cc = br + dr, bc + dc
                if (rr, cc) != (r, c):
                    domains[(rr, cc)].discard(val)
                    if not domains[(rr, cc)]:
                        return False
        return True

    # ─────────────────────────────────────────────
    #  解枚舉 (唯一性驗證)
    # ─────────────────────────────────────────────

    def enumerate_solutions(self, grid: List[List[int]] = None,
                            max_solutions: int = 10,
                            time_limit: float = 300.0) -> List[SolveResult]:
        """
        枚舉多個解 (用於唯一性驗證)。
        僅支持 CP-SAT 策略。
        """
        if not self._check_ortools():
            self._log("枚舉解需要 OR-Tools")
            return []

        from ortools.sat.python import cp_model

        if grid is None:
            grid = anchors_to_grid(ANCHORS_92)

        model = cp_model.CpModel()

        cells = {}
        for r in range(N):
            for c in range(N):
                if grid[r][c] != 0:
                    var = model.NewIntVar(grid[r][c], grid[r][c], f"c_{r}_{c}")
                else:
                    var = model.NewIntVar(1, N, f"c_{r}_{c}")
                cells[(r, c)] = var

        for r in range(N):
            model.AddAllDifferent([cells[(r, c)] for c in range(N)])
        for c in range(N):
            model.AddAllDifferent([cells[(r, c)] for r in range(N)])
        for b in range(N):
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE
            box_cells = [
                cells[(br + dr, bc + dc)]
                for dr in range(BOX_SIZE)
                for dc in range(BOX_SIZE)
            ]
            model.AddAllDifferent(box_cells)

        class Collector(cp_model.CpSolverSolutionCallback):
            def __init__(self, cells, limit):
                super().__init__()
                self.cells = cells
                self.limit = limit
                self.solutions = []

            def on_solution_callback(self):
                sol = [[0] * N for _ in range(N)]
                for r in range(N):
                    for c in range(N):
                        sol[r][c] = self.Value(self.cells[(r, c)])
                self.solutions.append(sol)
                if len(self.solutions) >= self.limit:
                    self.StopSearch()

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 8

        collector = Collector(cells, max_solutions)
        solver.Solve(model, collector)

        results = []
        for sol in collector.solutions:
            r = SolveResult(
                status="SOLVED",
                solution=sol,
                solver_name="CP-SAT Enumerator",
            )
            verifier = SolutionVerifier(sol)
            r.verification = verifier.verify_all(anchors=ANCHORS_92)
            results.append(r)

        self._log(f"找到 {len(results)} 個解")
        return results

    # ─────────────────────────────────────────────
    #  輸出格式化
    # ─────────────────────────────────────────────

    def _print_summary(self, result: SolveResult):
        """打印結果摘要"""
        self._log(f"\n{'=' * 64}")
        self._log(f"  結果: {result.status}")
        self._log(f"  求解器: {result.solver_name}")
        self._log(f"  錨點數: {result.anchor_count}")

        if result.filter_time > 0:
            self._log(f"  過濾耗時: {result.filter_time:.3f}s")
        self._log(f"  求解耗時: {result.solve_time:.3f}s")
        self._log(f"  總耗時:   {result.total_time:.3f}s")

        if result.verification:
            v = result.verification
            checks = [
                ("行約束", v.get("row_ok")),
                ("列約束", v.get("col_ok")),
                ("宮約束 (嚴格)", v.get("box_strict_ok")),
                ("宮約束 (放鬆)", v.get("box_relaxed_ok")),
                ("錨點", v.get("anchor_ok")),
            ]
            self._log(f"\n  驗證:")
            for name, ok in checks:
                if ok is not None:
                    icon = "PASS" if ok else "FAIL"
                    self._log(f"    [{icon}] {name}")

            relaxed = v.get("relaxed_boxes", [])
            if relaxed:
                self._log(f"    (放鬆宮格: {relaxed} - 符闔行間宮衝突已豁免)")

        if result.solution is not None:
            self._print_grid(result.solution)

        self._log(f"{'=' * 64}")

    def _print_grid(self, grid: List[List[int]]):
        """打印 16x16 網格"""
        self._log("")
        header = "     " + " ".join(f"{c + 1:3d}" for c in range(N))
        self._log(header)
        self._log("    " + "-" * 64)
        for r in range(N):
            row_str = " ".join(f"{v:3d}" for v in grid[r])
            self._log(f"  {ROW_LABELS[r]} |{row_str}")
            if r in (3, 7, 11):
                self._log("    " + "-" * 64)
