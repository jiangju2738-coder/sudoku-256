#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DLX 精确覆盖算法求解 256 数独 (16x16, 4x4宫格)
核心：CP-SAT 求解精确覆盖问题（等价于 DLX）
完整支持：行/列/宫 AllDifferent + 符闔排列约束 + 完整验证
"""

import json
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

# ─────────────────────────────────────────────
# 数据加载
# ─────────────────────────────────────────────

def load_config():
    with open(os.path.join(BASE_DIR, "sudoku_config.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def load_permutations(row_idx):
    with open(os.path.join(BASE_DIR, f"A{row_idx+1}_permutations.json"), "r", encoding="utf-8") as f:
        return json.load(f)

# ─────────────────────────────────────────────
# 约束过滤
# ─────────────────────────────────────────────

def filter_permutations(grid, permutation_sets):
    N = 16
    row_used = [set() for _ in range(N)]
    col_used = [set() for _ in range(N)]
    box_used = [set() for _ in range(N)]
    conflicts = []

    for r in range(N):
        for c in range(N):
            v = grid[r][c]
            if v:
                b = (r//4)*4 + (c//4)
                if v in row_used[r]: conflicts.append(f"行{r+1} 值{v} 行内重复")
                if v in col_used[c]: conflicts.append(f"列{c+1} 值{v} 列冲突（行{r+1} vs 其他行）")
                if v in box_used[b]: conflicts.append(f"宫{b+1} 值{v} 宫冲突")
                row_used[r].add(v)
                col_used[c].add(v)
                box_used[b].add(v)

    if conflicts:
        return None, conflicts

    valid_perms = []
    for r in range(N):
        filtered = []
        for perm in permutation_sets[r]:
            # 已知值匹配
            if any(grid[r][c] != 0 and perm[c] != grid[r][c] for c in range(N)):
                continue
            # 列约束
            if any(grid[r][c] == 0 and perm[c] in col_used[c] for c in range(N)):
                continue
            # 宫约束
            ok = True
            for c in range(N):
                if grid[r][c] == 0:
                    b = (r//4)*4 + (c//4)
                    if perm[c] in box_used[b]:
                        ok = False
                        break
            if ok:
                filtered.append(perm)
        valid_perms.append(filtered)
        log(f"  行{r+1:2d}: {len(permutation_sets[r]):>8,} → 过滤后 {len(filtered):>6,} 个")

    empty = [r+1 for r in range(N) if not valid_perms[r]]
    if empty:
        return None, [f"行 {empty} 在符闔+约束过滤后无有效排列"]
    return valid_perms, []

# ─────────────────────────────────────────────
# CP-SAT 精确覆盖求解（等价于 DLX）
# ─────────────────────────────────────────────

def solve_with_cpsat(grid, valid_perms, time_limit=120):
    """
    精确覆盖问题的 CP-SAT 编码：
    - 为每行每个有效排列创建一个布尔变量 x[r][k]
    - 约束1：每行恰好选一个排列 → sum(x[r]) == 1
    - 约束2：精确覆盖列约束 → 等价于 AllDifferent (由排列本身保证)
    - 附加：显式添加列约束和宫约束以提升搜索效率
    """
    from ortools.sat.python import cp_model
    N = 16
    
    model = cp_model.CpModel()
    
    # 变量：x[r][k] = 1 表示第r行选第k个排列
    x = []
    for r in range(N):
        row_vars = [model.NewBoolVar(f'x_{r}_{k}') for k in range(len(valid_perms[r]))]
        x.append(row_vars)
        # 每行恰好选一个排列
        model.AddExactlyOne(row_vars)
    
    # 为每个单元格创建值变量（便于列/宫约束）
    cell_val = {}
    for r in range(N):
        for c in range(N):
            if grid[r][c] != 0:
                cell_val[(r,c)] = grid[r][c]
            else:
                v = model.NewIntVar(1, N, f'v_{r}_{c}')
                cell_val[(r,c)] = v
                # 链接：v[r][c] = sum(perm[k][c] * x[r][k])
                model.Add(v == sum(
                    valid_perms[r][k][c] * x[r][k]
                    for k in range(len(valid_perms[r]))
                ))
    
    # 列 AllDifferent
    for c in range(N):
        model.AddAllDifferent([cell_val[(r,c)] for r in range(N)])
    
    # 宫 AllDifferent
    for b in range(N):
        br, bc = (b//4)*4, (b%4)*4
        box_cells = [cell_val[(br+dr, bc+dc)] for dr in range(4) for dc in range(4)]
        model.AddAllDifferent(box_cells)
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # 解码
        sol_grid = [[0]*N for _ in range(N)]
        for r in range(N):
            for k, var in enumerate(x[r]):
                if solver.Value(var) == 1:
                    sol_grid[r] = list(valid_perms[r][k])
                    break
        return "SOLVED", sol_grid, solver.WallTime()
    elif status == cp_model.INFEASIBLE:
        return "INFEASIBLE", None, solver.WallTime()
    else:
        return "TIMEOUT", None, solver.WallTime()

# ─────────────────────────────────────────────
# 验证
# ─────────────────────────────────────────────

def verify_solution(grid, permutation_sets, config):
    N = 16
    errors = []

    for r in range(N):
        if sorted(grid[r]) != list(range(1, 17)):
            errors.append(f"行{r+1}: {grid[r]} 不是1-16全排列")

    for c in range(N):
        col = [grid[r][c] for r in range(N)]
        if sorted(col) != list(range(1, 17)):
            errors.append(f"列{c+1}: {col} 不是1-16全排列")

    for b in range(N):
        br, bc = (b//4)*4, (b%4)*4
        box = [grid[br+dr][bc+dc] for dr in range(4) for dc in range(4)]
        if sorted(box) != list(range(1, 17)):
            errors.append(f"宫{b+1}: {box} 不是1-16全排列")

    perm_ok = perm_fail = 0
    for r in range(N):
        perm_list = [list(p) for p in permutation_sets[r]]
        if list(grid[r]) in perm_list:
            perm_ok += 1
        else:
            perm_fail += 1
            errors.append(f"行{r+1}: 不在符闔排列集合中")

    anchor_ok = True
    anchor_fails = []
    for cell in config["known_digits"]:
        r, c, v = cell["row"]-1, cell["col"]-1, cell["value"]
        if grid[r][c] != v:
            anchor_ok = False
            anchor_fails.append(f"锚点(行{r+1},列{c+1}): 期望{v} 实际{grid[r][c]}")

    return errors, perm_ok, perm_fail, anchor_ok, anchor_fails

# ─────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────

def main():
    log("=" * 60)
    log("DLX 精确覆盖算法求解 256 数独 (CP-SAT 核心)")
    log("=" * 60)

    N = 16
    t_start = time.time()

    log("\n[1] 加载配置...")
    config = load_config()
    grid = [[0]*N for _ in range(N)]
    for cell in config["known_digits"]:
        r, c, v = cell["row"]-1, cell["col"]-1, cell["value"]
        grid[r][c] = v
    anchor_count = sum(1 for r in range(N) for c in range(N) if grid[r][c] != 0)
    log(f"  锚点: {anchor_count} 个")

    log("\n[2] 加载符闔排列...")
    permutation_sets = []
    total_perms = 0
    for i in range(N):
        perms = load_permutations(i)
        permutation_sets.append(perms)
        total_perms += len(perms)
        log(f"  A{i+1}: {len(perms):,} 个")
    log(f"  总计: {total_perms:,} 个")

    log("\n[3] 过滤符闔排列（行+列+宫约束）...")
    t_filter = time.time()
    valid_perms, filter_errors = filter_permutations(grid, permutation_sets)

    if valid_perms is None:
        log("\n[错误] 约束预检查失败：")
        for e in filter_errors:
            log(f"  {e}")
        result = {
            "status": "BUILD_FAILED",
            "errors": filter_errors,
            "total_time_sec": round(time.time() - t_start, 3)
        }
        with open(os.path.join(BASE_DIR, "solution.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log("\n错误详情已保存到 solution.json")
        return

    filter_time = time.time() - t_filter
    total_valid = sum(len(vp) for vp in valid_perms)
    log(f"\n  过滤耗时: {filter_time:.2f}s")
    log(f"  过滤后总排列: {total_valid:,} 个")
    log("\n  过滤率概览:")
    for r in range(N):
        orig = len(permutation_sets[r])
        filt = len(valid_perms[r])
        pct = filt/orig*100 if orig > 0 else 0
        bar = "█" * int(pct/5) + "░" * (20 - int(pct/5))
        log(f"    行{r+1:2d} |{bar}| {filt:>6,}/{orig:>8,} ({pct:.1f}%)")

    log("\n[4] 运行 CP-SAT 精确覆盖求解...")
    log("  (等价于 DLX 精确覆盖，使用约束传播加速)")
    t_solve = time.time()
    status, sol_grid, cpsat_time = solve_with_cpsat(grid, valid_perms, time_limit=120)
    solve_time = time.time() - t_solve
    total_time = time.time() - t_start

    log(f"  CP-SAT 耗时: {cpsat_time:.3f}s")
    log(f"  求解状态: {status}")

    if status == "INFEASIBLE":
        log("\n[结果] ❌ INFEASIBLE — 约束系统无解")
        log("  (符闔排列 + 行/列/宫约束不可同时满足)")

        result = {
            "status": "INFEASIBLE",
            "message": "DLX/CP-SAT 精确覆盖搜索：无解",
            "anchor_count": anchor_count,
            "filter_time_sec": round(filter_time, 3),
            "solve_time_sec": round(solve_time, 3),
            "total_time_sec": round(total_time, 3),
            "filter_stats": [
                {"row": r+1,
                 "original": len(permutation_sets[r]),
                 "filtered": len(valid_perms[r]),
                 "ratio_pct": round(len(valid_perms[r])/max(len(permutation_sets[r]),1)*100, 2)}
                for r in range(N)
            ]
        }
        with open(os.path.join(BASE_DIR, "solution.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log("\n结果已保存到 solution.json")
        return

    if status == "TIMEOUT":
        log("\n[结果] ⏱ TIMEOUT — 搜索超时，未找到解（120秒）")
        result = {
            "status": "TIMEOUT",
            "message": "搜索超时120秒，未找到解",
            "anchor_count": anchor_count,
            "filter_time_sec": round(filter_time, 3),
            "solve_time_sec": round(solve_time, 3),
            "total_time_sec": round(total_time, 3)
        }
        with open(os.path.join(BASE_DIR, "solution.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log("\n结果已保存到 solution.json")
        return

    # status == "SOLVED"
    log("\n[5] 解码并验证解...")
    errors, perm_ok, perm_fail, anchor_ok, anchor_fails = verify_solution(
        sol_grid, permutation_sets, config
    )

    row_errs  = [e for e in errors if "行" in e and "全排列" in e]
    col_errs  = [e for e in errors if "列" in e]
    box_errs  = [e for e in errors if "宫" in e]
    fum_errs  = [e for e in errors if "符闔" in e]

    row_ok  = not row_errs
    col_ok  = not col_errs
    box_ok  = not box_errs
    fum_ok  = perm_fail == 0

    log("\n验证结果:")
    log(f"  {'✅' if row_ok else '❌'} 行约束  ({N - len(row_errs)}/{N} 行通过)")
    log(f"  {'✅' if col_ok else '❌'} 列约束  ({N - len(col_errs)}/{N} 列通过)")
    log(f"  {'✅' if box_ok else '❌'} 宫约束  ({N - len(box_errs)}/{N} 宫通过)")
    log(f"  {'✅' if fum_ok else '❌'} 符闔排列 ({perm_ok}/{N} 行通过)")
    log(f"  {'✅' if anchor_ok else '❌'} 锚点验证 ({anchor_count} 个)")

    final_status = "SOLVED" if not errors else "SOLVED_WITH_ISSUES"
    if not errors:
        log("\n🎉 解验证完全通过！四项约束全部满足！")
    else:
        log(f"\n⚠ 发现 {len(errors)} 个问题：")
        for e in errors[:8]:
            log(f"  {e}")

    # 打印网格
    log("\n解的网格 (16×16)：")
    log("     " + " ".join(f"C{c+1:02d}" for c in range(N)))
    log("    " + "-" * 64)
    for r in range(N):
        row_label = f"R{r+1:02d}|"
        row_str = " ".join(f"{v:3d}" for v in sol_grid[r])
        log(row_label + row_str)
        if r in [3, 7, 11]:
            log("    " + "-" * 64)

    # 保存结果
    result = {
        "status": final_status,
        "solver": "CP-SAT (DLX精确覆盖等价形式)",
        "anchor_count": anchor_count,
        "filter_time_sec": round(filter_time, 3),
        "solve_time_sec": round(cpsat_time, 3),
        "total_time_sec": round(total_time, 3),
        "solution": sol_grid,
        "verification": {
            "row_ok": row_ok,
            "col_ok": col_ok,
            "box_ok": box_ok,
            "fummel_ok": fum_ok,
            "fummel_rows_pass": perm_ok,
            "fummel_rows_fail": perm_fail,
            "anchor_ok": anchor_ok,
            "anchor_fails": anchor_fails,
            "errors": errors
        },
        "filter_stats": [
            {"row": r+1,
             "original": len(permutation_sets[r]),
             "filtered": len(valid_perms[r]),
             "ratio_pct": round(len(valid_perms[r])/max(len(permutation_sets[r]),1)*100, 2)}
            for r in range(N)
        ]
    }

    out_path = os.path.join(BASE_DIR, "solution.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log(f"\n✅ 结果已保存到 solution.json")
    log(f"总耗时: {total_time:.3f}s")

if __name__ == "__main__":
    main()
