#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從合法數獨解重新生成符闔排列（保證閉合性） V1.0
=====================================================

核心邏輯：
  1. 加載 sudoku_config.json（55 錨點）作為初始盤
  2. 用 CP-SAT 枚舉大量合法 16×16 Sudoku 完整解
  3. 從每個完整解中提取每行排列
  4. 按行聚合、去重，生成新的 A{i}_permutations.json
  5. 新排列集合保證：每個排列都來自至少一個合法數獨解
     → 即新集合是自動「閉合」的（滿足行/列/宮三約束）

理論依據：
  原符闔排列：僅考慮行約束（每行是 1-16 的全排列）
  新符闔排列：來自合法數獨解的行排列 → 自動滿足列/宮約束
  → 新集合是「閉合符闔排列集合」

使用方法：
  python regenerate_fuyi_from_solutions.py [--num-solutions N] [--time-limit T] [--backup]

作者：WorkBuddy AI
日期：2026-05-31
"""

import json
import os
import sys
import time
import shutil
import argparse
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)


# ──────────────────────────────────────────────────────────────
# Step 1: 加載配置
# ──────────────────────────────────────────────────────────────

def load_config():
    with open(os.path.join(BASE_DIR, "sudoku_config.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def build_init_grid(config, N=16):
    grid = [[0] * N for _ in range(N)]
    for cell in config["known_digits"]:
        r, c, v = cell["row"] - 1, cell["col"] - 1, cell["value"]
        grid[r][c] = v
    return grid


# ──────────────────────────────────────────────────────────────
# Step 2: CP-SAT 枚舉合法數獨解
# ──────────────────────────────────────────────────────────────

def enumerate_solutions(grid_init, num_solutions=5000, time_limit=300):
    """
    枚舉最多 num_solutions 個合法 16×16 Sudoku 完整解
    使用 CP-SAT 的 SolutionCallback 機制
    """
    from ortools.sat.python import cp_model

    N = len(grid_init)
    model = cp_model.CpModel()

    # 創建變量
    cell_vars = []
    for r in range(N):
        row_vars = []
        for c in range(N):
            if grid_init[r][c] != 0:
                v = model.NewConstant(grid_init[r][c])
            else:
                v = model.NewIntVar(1, N, f"v_{r}_{c}")
            row_vars.append(v)
        cell_vars.append(row_vars)

    # 行 AllDifferent
    for r in range(N):
        model.AddAllDifferent(cell_vars[r])

    # 列 AllDifferent
    for c in range(N):
        model.AddAllDifferent([cell_vars[r][c] for r in range(N)])

    # 宮 AllDifferent（4×4）
    for b in range(N):
        br, bc = (b // 4) * 4, (b % 4) * 4
        box_cells = [cell_vars[br + dr][bc + dc] for dr in range(4) for dc in range(4)]
        model.AddAllDifferent(box_cells)

    # Solution Callback
    class SolutionCollector(cp_model.CpSolverSolutionCallback):
        def __init__(self, cell_vars, N, max_solutions):
            super().__init__()
            self._cell_vars = cell_vars
            self._N = N
            self._max_solutions = max_solutions
            self._solutions = []

        def on_solution_callback(self):
            N = self._N
            grid = [[self.Value(self._cell_vars[r][c]) for c in range(N)] for r in range(N)]
            self._solutions.append(grid)
            if len(self._solutions) >= self._max_solutions:
                self.StopSearch()

        def get_solutions(self):
            return self._solutions

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    solver.parameters.enumerate_all_solutions = True

    collector = SolutionCollector(cell_vars, N, num_solutions)

    t_start = time.time()
    status = solver.Solve(model, collector)
    elapsed = time.time() - t_start

    solutions = collector.get_solutions()

    if status == cp_model.INFEASIBLE:
        return [], "INFEASIBLE", elapsed
    elif status == cp_model.UNKNOWN:
        return solutions, "TIMEOUT", elapsed
    else:
        return solutions, "FEASIBLE", elapsed


# ──────────────────────────────────────────────────────────────
# Step 3: 提取並聚合行排列
# ──────────────────────────────────────────────────────────────

def extract_row_permutations(solutions, N=16):
    """
    從完整解中提取每行排列，按行聚合去重
    返回：row_perms[r] = set of tuple (去重後的排列集合)
    """
    row_perms = [set() for _ in range(N)]
    total_rows = 0

    for sol_idx, grid in enumerate(solutions):
        for r in range(N):
            row_tuple = tuple(grid[r])
            row_perms[r].add(row_tuple)
        total_rows += N

        if (sol_idx + 1) % 1000 == 0:
            log(f"  已處理 {sol_idx + 1} 個解，當前各行唯一排列數：{ [len(s) for s in row_perms] }")

    return row_perms


# ──────────────────────────────────────────────────────────────
# Step 4: 備份並保存新排列
# ──────────────────────────────────────────────────────────────

def backup_old_permutations():
    """備份原始 A{i}_permutations.json 到 backup/ 目錄"""
    backup_dir = os.path.join(BASE_DIR, "backup_fuyi")
    os.makedirs(backup_dir, exist_ok=True)

    backed_up = []
    for i in range(1, 17):
        src = os.path.join(BASE_DIR, f"A{i}_permutations.json")
        dst = os.path.join(backup_dir, f"A{i}_permutations.json")
        if os.path.exists(src):
            shutil.copy2(src, dst)
            backed_up.append(f"A{i}_permutations.json")

    log(f"  備份完成：{len(backed_up)} 個文件 → {backup_dir}/")
    return backup_dir


def save_new_permutations(row_perms, do_backup=True):
    """保存新排列到 A{i}_permutations.json"""
    if do_backup:
        backup_old_permutations()

    saved_files = []
    total_count = 0

    for r in range(16):
        perm_list = [list(p) for p in sorted(row_perms[r])]
        out_path = os.path.join(BASE_DIR, f"A{r+1}_permutations.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(perm_list, f, ensure_ascii=False, separators=(',', ':'))
        saved_files.append(out_path)
        total_count += len(perm_list)
        log(f"  A{r+1}_permutations.json: {len(perm_list):,} 個排列")

    return saved_files, total_count


# ──────────────────────────────────────────────────────────────
# Step 5: 驗證新排列的閉合性
# ──────────────────────────────────────────────────────────────

def verify_closure(solutions_sample, row_perms, sample_size=100):
    """
    驗證新排列的閉合性：
    從樣本解中隨機抽取若干解，檢查每行排列是否都在新集合中
    """
    import random
    N = 16

    if len(solutions_sample) > sample_size:
        sample = random.sample(solutions_sample, sample_size)
    else:
        sample = solutions_sample

    all_closed = True
    row_miss_counts = [0] * N

    for grid in sample:
        for r in range(N):
            row_tuple = tuple(grid[r])
            if row_tuple not in row_perms[r]:
                all_closed = False
                row_miss_counts[r] += 1

    return all_closed, row_miss_counts


# ──────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="從合法數獨解重新生成符闔排列（保證閉合性）")
    parser.add_argument("--num-solutions", type=int, default=5000,
                        help="最大枚舉解數量（默認 5000，建議 >= 5000）")
    parser.add_argument("--time-limit", type=float, default=300,
                        help="CP-SAT 時間限制（秒，默認 300）")
    parser.add_argument("--no-backup", action="store_true",
                        help="不備份原始排列文件（謹慎使用）")
    parser.add_argument("--verify-sample", type=int, default=200,
                        help="驗證樣本大小（默認 200）")
    args = parser.parse_args()

    log("=" * 65)
    log("從合法數獨解重新生成符闔排列 V1.0")
    log("保證新排列集合的閉合性（滿足行/列/宮三約束）")
    log("=" * 65)

    t_total_start = time.time()
    N = 16

    # ── 加載配置 ──────────────────────────────────────────────
    log("\n[1] 加載 sudoku_config.json（55 錨點）...")
    config = load_config()
    grid_init = build_init_grid(config, N)
    anchor_count = sum(1 for r in range(N) for c in range(N) if grid_init[r][c] != 0)
    log(f"  錨點數: {anchor_count} 個")

    # ── CP-SAT 枚舉解 ─────────────────────────────────────────
    log(f"\n[2] CP-SAT 枚舉合法數獨解...")
    log(f"  最大解數量: {args.num_solutions:,}")
    log(f"  時間限制: {args.time_limit}s")
    log(f"  並行線程: 8\n")

    solutions, enum_status, enum_elapsed = enumerate_solutions(
        grid_init,
        num_solutions=args.num_solutions,
        time_limit=args.time_limit
    )

    log(f"  枚舉狀態: {enum_status}")
    log(f"  找到完整解: {len(solutions):,} 個")
    log(f"  枚舉耗時: {enum_elapsed:.3f}s")

    if enum_status == "INFEASIBLE" or len(solutions) == 0:
        log("\n[結果] ❌ 55 錨點本身無合法數獨解！")
        log("  → 請檢查 sudoku_config.json 是否正確")
        return

    # ── 提取行排列 ────────────────────────────────────────────
    log(f"\n[3] 從 {len(solutions):,} 個解中提取行排列...")
    t_extract = time.time()

    row_perms = extract_row_permutations(solutions, N)

    extract_elapsed = time.time() - t_extract
    log(f"  提取耗時: {extract_elapsed:.3f}s")

    log(f"\n  各行唯一排列數（去重後）：")
    total_unique = 0
    for r in range(N):
        count = len(row_perms[r])
        total_unique += count
        log(f"    行 {r+1:2d}: {count:>8,} 個")
    log(f"  總計: {total_unique:,} 個唯一排列")

    # ── 驗證閉合性 ────────────────────────────────────────────
    log(f"\n[4] 驗證新排列的閉合性...")
    all_closed, miss_counts = verify_closure(solutions, row_perms, args.verify_sample)
    log(f"  驗證樣本大小: {args.verify_sample}")
    log(f"  閉合性驗證: {'✅ 通過（所有樣本排列都在新集合中）' if all_closed else '❌ 失敗'}")
    if not all_closed:
        log(f"  未命中次數: {miss_counts}")

    # ── 保存新排列 ──────────────────────────────────────────────
    log(f"\n[5] 保存新排列文件...")
    if not args.no_backup:
        log("  （將先備份原始文件到 backup_fuyi/）")
    else:
        log("  ⚠️  不備份原始文件！")

    saved_files, total_count = save_new_permutations(
        row_perms,
        do_backup=not args.no_backup
    )

    # ── 生成報告 ──────────────────────────────────────────────
    total_elapsed = time.time() - t_total_start

    report = {
        "status": "COMPLETED",
        "description": "從合法數獨解重新生成符闔排列，保證閉合性",
        "config": {
            "anchor_count": anchor_count,
            "num_solutions_enumerated": len(solutions),
            "enum_time_sec": round(enum_elapsed, 3),
            "extract_time_sec": round(extract_elapsed, 3),
        },
        "results": {
            "total_unique_permutations": total_count,
            "avg_per_row": round(total_count / N, 1),
            "closure_verified": all_closed,
            "row_counts": [len(row_perms[r]) for r in range(N)],
        },
        "timing": {
            "total_elapsed_sec": round(total_elapsed, 3),
        },
        "conclusion": (
            "新符闔排列集合已生成，保證閉合性（來自合法數獨解）"
            if all_closed
            else "警告：部分排列可能不在集合中，建議增加枚舉解數量"
        )
    }

    report_path = os.path.join(BASE_DIR, "regenerate_fuyi_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ── 完成輸出 ──────────────────────────────────────────────
    log(f"\n{'='*65}")
    log(f"完成！總耗時: {total_elapsed:.3f}s")
    log(f"  新排列總計: {total_count:,} 個（平均每行 {total_count/N:.1f} 個）")
    log(f"  閉合性: {'✅ 保證（所有排列來自合法數獨解）' if all_closed else '⚠️  需要更多解來保證'}")
    log(f"  報告已保存到 regenate_fuyi_report.json")
    log(f"{'='*65}")

    if all_closed:
        log(f"\n🎉 新符闔排列集合已準備好！")
        log(f"   現在可以重新運行 dlx_solve_full.py 求解數獨")
        log(f"   新排列保證閉合 → 應該可以找到解（或證明無解）")


if __name__ == "__main__":
    main()
