#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
solve256.py - 256 數獨求解器命令行入口

使用方式:
    python solve256.py                    # 使用 92 錨點默認求解
    python solve256.py --strategy cpsat_perm    # 強制使用 CP-SAT + 排列
    python solve256.py --strategy cpsat_plain   # 強制使用 CP-SAT 標準
    python solve256.py --strategy backtrack     # 強制使用回溯
    python solve256.py --time-limit 600         # 設定 10 分鐘時限
    python solve256.py --enumerate 5            # 枚舉最多 5 個解
    python solve256.py --verify solution.json   # 驗證已有解
    python solve256.py --info                   # 顯示數據源摘要
    python solve256.py --output my_result.json  # 指定輸出檔案
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

# 確保可以從專案根目錄匯入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sudoku256 import Sudoku256Solver, SolutionVerifier
from sudoku256.constants import (
    ANCHORS_92, anchors_to_grid, N, ROW_LABELS,
    KNOWN_SOLUTION_92, PERM_STATS,
)
from sudoku256.loader import DataLoader


def cmd_solve(args):
    """執行求解"""
    engine = Sudoku256Solver(verbose=not args.quiet)
    result = engine.solve(
        time_limit=args.time_limit,
        strategy=args.strategy if args.strategy != "auto" else None,
    )

    # 保存結果
    output_path = args.output or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    result.save(output_path)

    if not args.quiet:
        print(f"\n結果已保存: {output_path}")

    return 0 if result.status == "SOLVED" else 1


def cmd_enumerate(args):
    """枚舉多個解"""
    engine = Sudoku256Solver(verbose=not args.quiet)
    results = engine.enumerate_solutions(
        max_solutions=args.enumerate,
        time_limit=args.time_limit,
    )

    if results:
        print(f"\n找到 {len(results)} 個解:")
        for i, r in enumerate(results):
            v = r.verification
            all_ok = (v.get("row_ok") and v.get("col_ok") and
                      v.get("box_ok") and v.get("anchor_ok"))
            print(f"  解 {i + 1}: 驗證={'通過' if all_ok else '失敗'}")

        # 唯一性判斷
        if len(results) == 1:
            print("\n  結論: 92 錨點下有唯一解")
        else:
            print(f"\n  結論: 找到 {len(results)} 個解 (非唯一)")

    # 保存
    output_path = args.output or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"enumerate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    all_data = {
        "solution_count": len(results),
        "solutions": [r.to_dict() for r in results],
        "timestamp": datetime.now().isoformat(),
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"結果已保存: {output_path}")

    return 0


def cmd_verify(args):
    """驗證已有解"""
    filepath = args.verify
    if not os.path.exists(filepath):
        print(f"檔案不存在: {filepath}")
        return 1

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 提取解
    solution = data.get("solution")
    if solution is None:
        print("檔案中未找到 solution 欄位")
        return 1

    if len(solution) != N or any(len(row) != N for row in solution):
        print(f"解的維度錯誤: 預期 {N}x{N}")
        return 1

    # 驗證
    verifier = SolutionVerifier(solution)
    result = verifier.verify_all(anchors=ANCHORS_92)

    print(f"驗證結果 ({filepath}):")
    checks = [
        ("行約束 (16行全排列)", result["row_ok"]),
        ("列約束 (16列全排列)", result["col_ok"]),
        ("宮約束 (16宮全排列)", result["box_ok"]),
        ("錨點約束 (92錨點)", result["anchor_ok"]),
    ]

    all_pass = True
    for name, ok in checks:
        icon = "PASS" if ok else "FAIL"
        print(f"  [{icon}] {name}")
        if not ok:
            all_pass = False

    if result["errors"]:
        print(f"\n錯誤詳情 ({len(result['errors'])} 項):")
        for e in result["errors"][:20]:
            print(f"  - {e}")

    if all_pass:
        print(f"\n驗證完全通過!")
    else:
        print(f"\n驗證失敗: {result['error_count']} 個錯誤")

    return 0 if all_pass else 1


def cmd_info(args):
    """顯示數據源摘要"""
    loader = DataLoader()
    loader.print_data_summary()

    # 額外資訊
    print(f"\n92 錨點分佈:")
    anchor_counts = {}
    for (r, c), v in ANCHORS_92.items():
        label = ROW_LABELS[r]
        anchor_counts[label] = anchor_counts.get(label, 0) + 1

    for label in ROW_LABELS:
        count = anchor_counts.get(label, 0)
        bar = "#" * count
        status = "完全固定" if count == N else f"{count} 個錨點"
        print(f"  {label}: {bar:16s} {status}")

    print(f"\n總錨點: {len(ANCHORS_92)}")

    # 環境檢測
    try:
        from ortools.sat.python import cp_model
        ortools_status = "已安裝"
    except ImportError:
        ortools_status = "未安裝 (將使用回溯備用)"
    print(f"OR-Tools: {ortools_status}")

    return 0


def cmd_bench(args):
    """效能測試"""
    print("=" * 64)
    print("  256 數獨求解器 - 效能基準測試")
    print("=" * 64)

    engine = Sudoku256Solver(verbose=False)
    strategies = []

    # 探測可用策略
    if engine._check_ortools():
        perm_files = engine.loader.find_permutation_files()
        if len(perm_files) == N:
            strategies.append("cpsat_perm")
        strategies.append("cpsat_plain")
    strategies.append("backtrack")

    results = {}
    for strat in strategies:
        strat_names = {
            "cpsat_perm": "CP-SAT + 排列過濾",
            "cpsat_plain": "CP-SAT 標準模型",
            "backtrack": "回溯 + AC-3",
        }
        name = strat_names.get(strat, strat)
        print(f"\n[{name}]")

        # 計時
        t0 = time.time()
        if strat == "backtrack":
            result = engine.solve(
                time_limit=min(args.time_limit, 30),
                strategy=strat,
            )
        else:
            result = engine.solve(
                time_limit=args.time_limit,
                strategy=strat,
            )
        elapsed = time.time() - t0

        results[strat] = {
            "name": name,
            "status": result.status,
            "total_time": elapsed,
            "solve_time": result.solve_time,
            "filter_time": result.filter_time,
        }

        status_icon = "OK" if result.status == "SOLVED" else "FAIL"
        print(f"  狀態: [{status_icon}] {result.status}")
        print(f"  總耗時: {elapsed:.3f}s")
        if result.filter_time > 0:
            print(f"  過濾: {result.filter_time:.3f}s")
        print(f"  求解: {result.solve_time:.3f}s")

        if result.verification:
            v = result.verification
            all_ok = (v.get("row_ok") and v.get("col_ok") and
                      v.get("box_ok") and v.get("anchor_ok"))
            print(f"  驗證: {'PASS' if all_ok else 'FAIL'}")

    # 比較摘要
    if len(results) > 1:
        print(f"\n{'=' * 64}")
        print(f"  策略比較:")
        print(f"  {'策略':<24s} {'狀態':<12s} {'總耗時':>10s} {'求解':>10s}")
        print(f"  {'-' * 60}")
        for strat, info in results.items():
            print(
                f"  {info['name']:<24s} "
                f"{info['status']:<12s} "
                f"{info['total_time']:>8.3f}s "
                f"{info['solve_time']:>8.3f}s"
            )

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="256 數獨求解器 v2.0 - 16x16 符闔超級數獨",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python solve256.py                        默認求解
  python solve256.py --strategy cpsat_perm  使用 CP-SAT + 排列
  python solve256.py --enumerate 5          枚舉最多 5 個解
  python solve256.py --verify solution.json 驗證已有解
  python solve256.py --info                 數據源摘要
  python solve256.py --bench                效能測試
        """
    )

    parser.add_argument(
        "--strategy", "-s",
        choices=["auto", "cpsat_perm", "cpsat_plain", "backtrack"],
        default="auto",
        help="求解策略 (默認: auto 自動選擇)"
    )
    parser.add_argument(
        "--time-limit", "-t",
        type=float, default=300.0,
        help="超時秒數 (默認: 300)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str, default=None,
        help="輸出 JSON 檔案路徑"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="靜默模式 (減少輸出)"
    )
    parser.add_argument(
        "--enumerate", "-e",
        type=int, default=0,
        help="枚舉解的數量 (0 = 只求一個解)"
    )
    parser.add_argument(
        "--verify", "-v",
        type=str, default=None,
        help="驗證指定 JSON 檔案中的解"
    )
    parser.add_argument(
        "--info", "-i",
        action="store_true",
        help="顯示數據源和環境摘要"
    )
    parser.add_argument(
        "--bench", "-b",
        action="store_true",
        help="執行效能基準測試"
    )

    args = parser.parse_args()

    # 路由到對應命令
    if args.info:
        return cmd_info(args)
    elif args.verify:
        return cmd_verify(args)
    elif args.bench:
        return cmd_bench(args)
    elif args.enumerate > 0:
        return cmd_enumerate(args)
    else:
        return cmd_solve(args)


if __name__ == "__main__":
    sys.exit(main())
