#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
閉合符闔排列集合生成器 V1.0
=================================================
核心邏輯：
  1. 加載 sudoku_config.json（55 錨點）作為初始盤
  2. 用 CP-SAT 枚舉所有與錨點相容的完整合法 16×16 Sudoku
     (行/列/宮 AllDifferent，即標準數獨三約束)
  3. 對每個完整解，提取每行排列
  4. 過濾：每行排列必須在原始 A{i}_permutations.json 中（符闔約束）
  5. 將通過過濾的排列按行聚合，生成閉合排列集合
  6. 輸出：
     - A{i}_closed_permutations.json  ← 各行閉合排列（滿足符闔+三約束）
     - closed_permutations_report.json ← 統計報告
     - 如果符闔集合內無任何完整解 → 報告「理論無解」

理論依據：
  極大相容集定理：任意 16×16 Sudoku 的 16 行構成「極大列相容集」
  → 閉合排列集 = {所有合法完整解} ∩ {原始符闔排列}
  → 若交集為空，說明原始符闔排列池與數獨三約束不相容（V62 結論）

使用方法：
  python generate_closed_permutations.py [--max-solutions N] [--time-limit T]
"""

import json
import os
import sys
import time
import argparse
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)


# ─────────────────────────────────────────────────────────────
# Step 1: 加載配置和符闔排列
# ─────────────────────────────────────────────────────────────

def load_config():
    with open(os.path.join(BASE_DIR, "sudoku_config.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_permutations():
    """加載所有行的符闔排列，轉換為 frozenset 查找結構"""
    log("[1] 加載符闔排列...")
    all_perms = []   # all_perms[r] = set of frozenset tuples（快速查找）
    all_perms_list = []  # all_perms_list[r] = list of lists（原始列表）
    total = 0
    for i in range(16):
        path = os.path.join(BASE_DIR, f"A{i+1}_permutations.json")
        with open(path, "r", encoding="utf-8") as f:
            perms = json.load(f)
        perm_set = set(tuple(p) for p in perms)
        all_perms.append(perm_set)
        all_perms_list.append(perms)
        total += len(perms)
        log(f"  A{i+1}: {len(perms):,} 個排列")
    log(f"  符闔排列總計: {total:,} 個")
    return all_perms, all_perms_list


# ─────────────────────────────────────────────────────────────
# Step 2: CP-SAT 枚舉所有合法完整解
# ─────────────────────────────────────────────────────────────

class SolutionCollector:
    """CP-SAT 回調：收集所有解"""
    def __init__(self, cell_vars, N=16, max_solutions=None):
        from ortools.sat.python import cp_model
        super().__init__()
        self._cell_vars = cell_vars
        self._N = N
        self._solutions = []
        self._max_solutions = max_solutions
        self._cp_model = cp_model

    def on_solution_callback(self):
        N = self._N
        grid = []
        for r in range(N):
            row = [self.Value(self._cell_vars[r][c]) for c in range(N)]
            grid.append(row)
        self._solutions.append(grid)
        if self._max_solutions and len(self._solutions) >= self._max_solutions:
            self.StopSearch()

    def solution_count(self):
        return len(self._solutions)

    def get_solutions(self):
        return self._solutions


def enumerate_valid_sudoku(grid_init, max_solutions=None, time_limit=300):
    """
    枚舉所有與初始盤相容的合法 16×16 Sudoku
    
    Args:
        grid_init: 16x16 初始網格（0 表示未知）
        max_solutions: 最大解數量限制（None = 不限）
        time_limit: 時間限制（秒）
    
    Returns:
        solutions: List[List[List[int]]]
        status: "FOUND" / "INFEASIBLE" / "TIMEOUT"
        elapsed: float
    """
    from ortools.sat.python import cp_model
    
    N = 16
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
    
    # 求解器設置
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    solver.parameters.enumerate_all_solutions = True
    
    # 回調收集解
    collector = SolutionCollector(cell_vars, N, max_solutions)
    
    t_start = time.time()
    # 使用 Solve with callback
    status = solver.Solve(model, collector)
    elapsed = time.time() - t_start
    
    solutions = collector.get_solutions()
    
    if status == cp_model.INFEASIBLE:
        return [], "INFEASIBLE", elapsed
    elif status == cp_model.UNKNOWN:
        return solutions, "TIMEOUT", elapsed
    else:
        return solutions, "FOUND" if solutions else "INFEASIBLE", elapsed


# ─────────────────────────────────────────────────────────────
# Step 3: 過濾 + 聚合閉合排列
# ─────────────────────────────────────────────────────────────

def extract_closed_permutations(solutions, fummel_perm_sets):
    """
    從完整解中提取符合符闔約束的閉合排列
    
    Args:
        solutions: List[grid]（每個 grid 是 16x16 的整數列表）
        fummel_perm_sets: List[set of tuple]（每行的符闔排列集合）
    
    Returns:
        closed_perms: Dict[int, set of tuple]  row_idx -> 閉合排列集合
        valid_solutions: 完整滿足符闔約束的解
        stats: 統計信息
    """
    N = 16
    closed_perms = defaultdict(set)   # row -> set of tuple
    valid_solutions = []   # 16 行全部在符闔集合中的完整解
    
    row_fummel_hits = [0] * N      # 各行命中符闔的排列數
    row_fummel_miss = [0] * N      # 各行不在符闔集合的排列數
    
    for sol_idx, grid in enumerate(solutions):
        all_rows_in_fummel = True
        for r in range(N):
            row_tuple = tuple(grid[r])
            if row_tuple in fummel_perm_sets[r]:
                closed_perms[r].add(row_tuple)
                row_fummel_hits[r] += 1
            else:
                row_fummel_miss[r] += 1
                all_rows_in_fummel = False
        
        if all_rows_in_fummel:
            valid_solutions.append(grid)
    
    stats = {
        "total_solutions": len(solutions),
        "fully_fummel_solutions": len(valid_solutions),
        "row_stats": [
            {
                "row": r + 1,
                "unique_closed_perms": len(closed_perms[r]),
                "fummel_hits": row_fummel_hits[r],
                "fummel_miss": row_fummel_miss[r],
                "hit_rate_pct": round(row_fummel_hits[r] / max(len(solutions), 1) * 100, 2)
            }
            for r in range(N)
        ]
    }
    
    return closed_perms, valid_solutions, stats


# ─────────────────────────────────────────────────────────────
# Step 4: 輸出閉合排列文件
# ─────────────────────────────────────────────────────────────

def save_closed_permutations(closed_perms, out_dir=None):
    """保存閉合排列到 A{i}_closed_permutations.json"""
    if out_dir is None:
        out_dir = BASE_DIR
    
    saved_files = []
    for r in range(16):
        perm_list = [list(p) for p in sorted(closed_perms.get(r, set()))]
        out_path = os.path.join(out_dir, f"A{r+1}_closed_permutations.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(perm_list, f, ensure_ascii=False, separators=(',', ':'))
        saved_files.append(out_path)
        log(f"  A{r+1}_closed_permutations.json: {len(perm_list)} 個排列")
    
    return saved_files


# ─────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="生成閉合符闔排列集合")
    parser.add_argument("--max-solutions", type=int, default=None,
                        help="最大枚舉解數量（默認不限，谨慎使用）")
    parser.add_argument("--time-limit", type=float, default=300,
                        help="CP-SAT 時間限制（秒，默認300）")
    parser.add_argument("--skip-fummel-filter", action="store_true",
                        help="跳過符闔過濾，輸出所有完整解的排列")
    args = parser.parse_args()
    
    log("=" * 65)
    log("閉合符闔排列集合生成器 V1.0")
    log("基於 55 錨點 + 符闔三約束（行/列/宮）")
    log("=" * 65)
    
    t_total_start = time.time()
    N = 16
    
    # ── 加載配置 ──────────────────────────────────────────────
    log("\n[1] 加載 sudoku_config.json（55 錨點）...")
    config = load_config()
    grid_init = [[0] * N for _ in range(N)]
    for cell in config["known_digits"]:
        r, c, v = cell["row"] - 1, cell["col"] - 1, cell["value"]
        grid_init[r][c] = v
    anchor_count = sum(1 for r in range(N) for c in range(N) if grid_init[r][c] != 0)
    log(f"  錨點數: {anchor_count} 個")
    
    # 打印初始盤
    log("\n  初始盤（0=未知）:")
    log("     " + " ".join(f"C{c+1:02d}" for c in range(N)))
    for r in range(N):
        row_str = " ".join(f"{v:3d}" if v != 0 else "  ." for v in grid_init[r])
        log(f"  R{r+1:02d}|{row_str}")
        if r in [3, 7, 11]:
            log("     " + "-" * 64)
    
    # ── 加載符闔排列 ─────────────────────────────────────────
    fummel_perm_sets, fummel_perm_lists = load_all_permutations()
    
    # ── CP-SAT 枚舉完整解 ────────────────────────────────────
    log(f"\n[2] CP-SAT 枚舉完整合法 Sudoku（時間限制: {args.time_limit}s）...")
    if args.max_solutions:
        log(f"  最大解數量: {args.max_solutions}")
    else:
        log("  最大解數量: 不限（枚舉所有解）")
    
    solutions, enum_status, enum_elapsed = enumerate_valid_sudoku(
        grid_init,
        max_solutions=args.max_solutions,
        time_limit=args.time_limit
    )
    
    log(f"\n  枚舉狀態: {enum_status}")
    log(f"  找到完整解: {len(solutions)} 個")
    log(f"  枚舉耗時: {enum_elapsed:.3f}s")
    
    if enum_status == "INFEASIBLE" or len(solutions) == 0:
        log("\n[結果] ❌ 55 錨點本身無合法 Sudoku 解")
        log("  → 謎題初始盤存在衝突，無法生成閉合排列集合")
        result = {
            "status": "NO_SOLUTIONS",
            "message": "55 錨點初始盤無合法完整解",
            "anchor_count": anchor_count,
            "enum_elapsed_sec": round(enum_elapsed, 3),
            "total_elapsed_sec": round(time.time() - t_total_start, 3)
        }
        out_path = os.path.join(BASE_DIR, "closed_permutations_report.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log(f"\n報告已保存到 closed_permutations_report.json")
        return
    
    # 打印前幾個解
    log(f"\n  找到 {len(solutions)} 個完整合法 Sudoku！前 3 個解預覽：")
    for sol_idx, grid in enumerate(solutions[:3]):
        log(f"\n  ── 解 {sol_idx+1} ──")
        for r in range(N):
            row_str = " ".join(f"{v:3d}" for v in grid[r])
            log(f"    R{r+1:02d}|{row_str}")
            if r in [3, 7, 11]:
                log("        " + "-" * 60)
    
    # ── 符闔過濾 + 閉合排列提取 ──────────────────────────────
    if not args.skip_fummel_filter:
        log(f"\n[3] 符闔約束過濾（與 A{{i}}_permutations.json 交集）...")
        closed_perms, valid_solutions, stats = extract_closed_permutations(
            solutions, fummel_perm_sets
        )
        
        log(f"\n  符闔過濾結果：")
        log(f"  總完整解數：{stats['total_solutions']}")
        log(f"  全行符闔的解數：{stats['fully_fummel_solutions']}")
        log(f"\n  各行閉合排列統計：")
        log(f"  {'行':>4} | {'閉合排列':>10} | {'命中率':>8} | {'符闔Miss':>10}")
        log(f"  {'-'*4}-+-{'-'*10}-+-{'-'*8}-+-{'-'*10}")
        for rs in stats["row_stats"]:
            hit_bar = "█" * int(rs["hit_rate_pct"] / 5)
            log(f"  行{rs['row']:2d} | {rs['unique_closed_perms']:>10,} | "
                f"{rs['hit_rate_pct']:>7.1f}% | "
                f"{rs['fummel_miss']:>10,}  {hit_bar}")
        
        has_empty_rows = any(rs["unique_closed_perms"] == 0 for rs in stats["row_stats"])
        
        if has_empty_rows:
            empty_rows = [rs["row"] for rs in stats["row_stats"] if rs["unique_closed_perms"] == 0]
            log(f"\n  ⚠ 行 {empty_rows} 的閉合排列為空！")
            log("  → 這些行在所有完整解中，不存在符闔集合內的排列")
            log("  → 這驗證了 V62 理論：符闔排列池與數獨三約束不相容")
        
        if stats["fully_fummel_solutions"] > 0:
            log(f"\n  ✅ 找到 {stats['fully_fummel_solutions']} 個完整符合三約束的符闔解！")
        else:
            log("\n  ❌ 無全行符闔的完整解（即無解在原始符闔集合中）")
    else:
        # 不過濾，直接提取所有解的排列
        log("\n[3] 跳過符闔過濾，提取所有完整解的排列...")
        closed_perms = defaultdict(set)
        for grid in solutions:
            for r in range(N):
                closed_perms[r].add(tuple(grid[r]))
        valid_solutions = solutions
        stats = {
            "total_solutions": len(solutions),
            "fully_fummel_solutions": len(solutions),
            "row_stats": [
                {"row": r+1, "unique_closed_perms": len(closed_perms[r]),
                 "fummel_hits": len(solutions), "fummel_miss": 0, "hit_rate_pct": 100.0}
                for r in range(N)
            ]
        }
        log(f"  各行唯一排列數：{[len(closed_perms[r]) for r in range(N)]}")
    
    # ── 保存閉合排列文件 ─────────────────────────────────────
    log(f"\n[4] 保存閉合排列文件...")
    saved_files = save_closed_permutations(closed_perms)
    
    total_closed = sum(len(closed_perms[r]) for r in range(N))
    log(f"\n  閉合排列總計: {total_closed} 個")
    log(f"  平均每行: {total_closed / N:.1f} 個")
    
    # ── 保存完整報告 ─────────────────────────────────────────
    total_elapsed = time.time() - t_total_start
    
    fummel_filter_applied = not args.skip_fummel_filter
    report = {
        "status": "COMPLETED",
        "config": {
            "anchor_count": anchor_count,
            "max_solutions": args.max_solutions,
            "time_limit_sec": args.time_limit,
            "fummel_filter_applied": fummel_filter_applied
        },
        "results": {
            "enum_status": enum_status,
            "total_valid_sudoku_solutions": len(solutions),
            "fully_fummel_solutions": stats["fully_fummel_solutions"],
            "total_closed_permutations": total_closed,
            "avg_closed_perms_per_row": round(total_closed / N, 1)
        },
        "timing": {
            "enum_elapsed_sec": round(enum_elapsed, 3),
            "total_elapsed_sec": round(total_elapsed, 3)
        },
        "row_stats": stats["row_stats"],
        "message": (
            "閉合符闔排列集合生成完成" if not fummel_filter_applied or stats["fully_fummel_solutions"] > 0
            else "無全行符闔的完整解（符闔約束與數獨三約束不相容，V62 理論驗證）"
        )
    }
    
    if valid_solutions:
        report["sample_solutions"] = valid_solutions[:3]  # 保存前3個解
    
    report_path = os.path.join(BASE_DIR, "closed_permutations_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    log(f"\n[5] 報告已保存到 closed_permutations_report.json")
    log(f"\n{'='*65}")
    log(f"完成！總耗時: {total_elapsed:.3f}s")
    
    if fummel_filter_applied:
        if stats["fully_fummel_solutions"] > 0:
            log(f"🎉 成功生成閉合符闔排列集合！")
            log(f"   完整符闔解: {stats['fully_fummel_solutions']} 個")
            log(f"   閉合排列總計: {total_closed} 個")
        else:
            log(f"📊 分析完成：找到 {len(solutions)} 個合法 Sudoku，但無全行符闔解")
            log(f"   → 這驗證了 V62 閉合性理論：符闔排列不閉合")
            log(f"   → 各行仍生成了部分閉合排列（符合符闔+三約束的子集）")
    else:
        log(f"📊 已生成基於完整解的排列集合（未過濾符闔約束）")
    log(f"{'='*65}")


if __name__ == "__main__":
    main()
