#!/usr/bin/env python3
"""
符阖数独 DIMACS CNF 生成器 v3（最终版）

编码方案（两级）：
Level 1 - 快速验证（~1MB）:
  仅添加禁止子句：对每行每位置，如果值 v 在所有排列中都不出现 → ¬X[i][c][v]
  共约 3,112 条禁止子句

Level 2 - 精确计数（~50MB）:
  Level 1 + 排列选择变量 + at-least-one + 顺序计数器 at-most-one
  + 关联约束：Y[i][p] → 第i行 = perm[p]
  共约 333 万条子句

本脚本生成 Level 1 CNF（供快速测试）。
如需 Level 2，运行 gen_fuhh_cnf_full.py
"""

import json, os, time
from collections import Counter

BASE = r"D:/2026/WPF_Sudoku/Sudoku_256"
OUTPUT_L1 = os.path.join(BASE, "fuhh_sudoku.cnf")
OUTPUT_L2 = os.path.join(BASE, "fuhh_sudoku_full.cnf")
GRID_SIZE, NUM_VALUES = 16, 16

def cell_var(r, c, v):
    return 1 + r * 256 + c * 16 + (v - 1)

def write_header(f, total_vars, total_clauses, level="L1"):
    f.write(f"c 符闔數獨 DIMACS CNF ({level})\n")
    f.write(f"c 時間: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
    f.write(f"c 網格: {GRID_SIZE}x{GRID_SIZE}, 宫格: 4x4\n")
    f.write(f"c 已知數字: {n_known} 個\n")
    f.write(f"c 符闔排列總數: {total_perms:,}\n")
    f.write(f"c 主變量(X[r][c][v]): 1..{max_main:,}\n")
    if level == "L2":
        f.write(f"c 排列選擇+計數器: {max_main+1:,}..{total_vars:,}\n")
    f.write(f"c 變量: {total_vars:,} 子句: {total_clauses:,}\n")
    f.write(f"p cnf {total_vars} {total_clauses}\n")

def main():
    t0 = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] 加载数据...", flush=True)

    # 加载配置
    with open(os.path.join(BASE, "sudoku_config.json")) as f:
        known = { (e["row"], e["col"]): e["value"] for e in json.load(f)["known_digits"] }

    # 加载排列
    all_perms = []
    for i in range(1, 17):
        with open(os.path.join(BASE, f"A{i}_permutations.json")) as f:
            all_perms.append(json.load(f))

    n_known = len(known)
    total_perms = sum(len(p) for p in all_perms)

    # 计算每行每位置的禁止值
    forbid = []
    for i in range(16):
        for c in range(16):
            allowed = set(p[c] for p in all_perms[i])
            for v in range(1, 17):
                if v not in allowed:
                    forbid.append((i, c, v))

    print(f"[{time.strftime('%H:%M:%S')}] 排列总数: {total_perms:,}")
    print(f"[{time.strftime('%H:%M:%S')}] 禁止子句: {len(forbid):,}")
    print(f"[{time.strftime('%H:%M:%S')}] 每行每列允许值数:")
    for i in range(16):
        counts = []
        for c in range(16):
            allowed = set(p[c] for p in all_perms[i])
            counts.append(len(allowed))
        print(f"  Row {i+1:2d}: {counts}  (排列: {len(all_perms[i]):,})")

    max_main = GRID_SIZE * GRID_SIZE * NUM_VALUES  # 4096

    # ========== Level 1: 快速版本 ==========
    # 变量: 仅主变量 4096
    # 子句: 标准约束 + 禁止子句 + 已知数字
    n_clauses_l1 = 0
    n_clauses_l1 += 16 * 16 * 120  # 行 AllDifferent
    n_clauses_l1 += 16 * 16 * 120  # 列 AllDifferent
    n_clauses_l1 += 16 * 16 * 120  # 宫 AllDifferent
    n_clauses_l1 += 256 * (1 + 120)  # 单元格 ExactlyOne
    n_clauses_l1 += n_known  # 已知数字
    n_clauses_l1 += len(forbid)  # 禁止子句

    print(f"\n[{time.strftime('%H:%M:%S')}] ===== Level 1: 快速版本 =====")
    print(f"  变量: {max_main:,}")
    print(f"  子句: {n_clauses_l1:,}")

    with open(OUTPUT_L1, 'w') as f:
        write_header(f, max_main, n_clauses_l1, "L1-快速")

        # 行 AllDifferent
        print(f"[{time.strftime('%H:%M:%S')}]   行约束...", flush=True)
        for r in range(GRID_SIZE):
            for v in range(1, NUM_VALUES+1):
                vv = [cell_var(r, c, v) for c in range(GRID_SIZE)]
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 列 AllDifferent
        print(f"[{time.strftime('%H:%M:%S')}]   列约束...", flush=True)
        for c in range(GRID_SIZE):
            for v in range(1, NUM_VALUES+1):
                vv = [cell_var(r, c, v) for r in range(GRID_SIZE)]
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 宫格 AllDifferent
        print(f"[{time.strftime('%H:%M:%S')}]   宫格约束...", flush=True)
        for br in range(4):
            for bc in range(4):
                for v in range(1, NUM_VALUES+1):
                    vv = [cell_var(br*4+dr, bc*4+dc, v) for dr in range(4) for dc in range(4)]
                    for a in range(16):
                        for b in range(a+1, 16):
                            f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 单元格 ExactlyOne
        print(f"[{time.strftime('%H:%M:%S')}]   单元格约束...", flush=True)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cv = [cell_var(r, c, v) for v in range(1, NUM_VALUES+1)]
                f.write(" ".join(str(x) for x in cv) + " 0\n")
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{cv[a]} -{cv[b]} 0\n")

        # 已知数字
        print(f"[{time.strftime('%H:%M:%S')}]   已知数字...", flush=True)
        for (r, c), v in known.items():
            f.write(f"{cell_var(r-1, c-1, v)} 0\n")

        # 禁止子句
        print(f"[{time.strftime('%H:%M:%S')}]   禁止子句 ({len(forbid):,}条)...", flush=True)
        for i, c, v in forbid:
            f.write(f"-{cell_var(i, c, v)} 0\n")

    fsize = os.path.getsize(OUTPUT_L1)
    print(f"[{time.strftime('%H:%M:%S')}] Level 1 完成: {OUTPUT_L1}")
    print(f"  大小: {fsize / 1024:.1f} KB")

    # ========== Level 2: 精确版本 ==========
    print(f"\n[{time.strftime('%H:%M:%S')}] ===== Level 2: 精确版本 =====")

    # 变量编号
    y_offset = max_main
    total_y = 0
    total_counter = 0
    row_info = []  # (n, base_y, base_counter, n_counter)
    for i in range(16):
        n = len(all_perms[i])
        base_y = y_offset + total_y
        n_counter = n - 1 if n > 1 else 0
        row_info.append((n, base_y, base_y + n, n_counter))
        total_y += n
        total_counter += n_counter

    total_aux = total_y + total_counter
    total_vars_l2 = max_main + total_aux

    # 计算子句数
    n_clauses_l2 = n_clauses_l1  # 所有 L1 子句
    for n, _, _, n_counter in row_info:
        n_clauses_l2 += 1  # at-least-one
        if n_counter > 0:
            n_clauses_l2 += 3 * n_counter  # 顺序计数器

        # 关联约束
        i = next(idx for idx, info in enumerate(row_info) if info[1] == base_y) if False else 0
    # 重新计算
    n_clauses_l2 = 0
    # 标准约束
    n_clauses_l2 += 16 * 16 * 120 * 3  # 行+列+宫
    n_clauses_l2 += 256 * (1 + 120)  # 单元格
    n_clauses_l2 += n_known
    n_clauses_l2 += len(forbid)

    y_offset = max_main
    cum_y = 0
    cum_counter = 0
    for i in range(16):
        n = len(all_perms[i])
        base_y = y_offset + cum_y
        n_counter = n - 1 if n > 1 else 0
        cum_y += n
        cum_counter += n_counter

        n_clauses_l2 += 1  # at-least-one
        if n_counter > 0:
            n_clauses_l2 += 3 * n_counter  # at-most-one
        # 关联约束
        n_clauses_l2 += 16 * n * 15

    print(f"  变量: {total_vars_l2:,} (主 {max_main:,} + 排列 {total_y:,} + 计数器 {total_counter:,})")
    print(f"  子句: {n_clauses_l2:,}")

    # 预计算禁止值集合
    forbid_set = set()
    for i, c, v in forbid:
        forbid_set.add((i, c, v))

    with open(OUTPUT_L2, 'w') as f:
        write_header(f, total_vars_l2, n_clauses_l2, "L2-精确")

        # 行 AllDifferent
        print(f"[{time.strftime('%H:%M:%S')}]   行约束...", flush=True)
        for r in range(GRID_SIZE):
            for v in range(1, NUM_VALUES+1):
                vv = [cell_var(r, c, v) for c in range(GRID_SIZE)]
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 列 AllDifferent
        print(f"[{time.strftime('%H:%M:%S')}]   列约束...", flush=True)
        for c in range(GRID_SIZE):
            for v in range(1, NUM_VALUES+1):
                vv = [cell_var(r, c, v) for r in range(GRID_SIZE)]
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 宫格 AllDifferent
        print(f"[{time.strftime('%H:%M:%S')}]   宫格约束...", flush=True)
        for br in range(4):
            for bc in range(4):
                for v in range(1, NUM_VALUES+1):
                    vv = [cell_var(br*4+dr, bc*4+dc, v) for dr in range(4) for dc in range(4)]
                    for a in range(16):
                        for b in range(a+1, 16):
                            f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 单元格 ExactlyOne
        print(f"[{time.strftime('%H:%M:%S')}]   单元格约束...", flush=True)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cv = [cell_var(r, c, v) for v in range(1, NUM_VALUES+1)]
                f.write(" ".join(str(x) for x in cv) + " 0\n")
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{cv[a]} -{cv[b]} 0\n")

        # 已知数字
        print(f"[{time.strftime('%H:%M:%S')}]   已知数字...", flush=True)
        for (r, c), v in known.items():
            f.write(f"{cell_var(r-1, c-1, v)} 0\n")

        # 禁止子句
        print(f"[{time.strftime('%H:%M:%S')}]   禁止子句...", flush=True)
        for i, c, v in forbid:
            f.write(f"-{cell_var(i, c, v)} 0\n")

        # 排列选择约束
        print(f"[{time.strftime('%H:%M:%S')}]   排列选择约束...", flush=True)
        y_offset = max_main
        cum_y = 0
        for i in range(16):
            perms = all_perms[i]
            n = len(perms)
            base_y = y_offset + cum_y
            n_counter = n - 1 if n > 1 else 0
            cum_y += n
            base_counter = base_y + n

            # at-least-one
            lits = [str(base_y + p) for p in range(n)]
            f.write(" ".join(lits) + " 0\n")

            # 顺序计数器 at-most-one
            if n_counter > 0:
                for j in range(n_counter):
                    # ¬Y[j+1] ∨ s[j]
                    f.write(f"-{base_y + j + 1} {base_counter + j} 0\n")
                    if j > 0:
                        # ¬s[j-1] ∨ s[j]
                        f.write(f"-{base_counter + j - 1} {base_counter + j} 0\n")
                        # ¬Y[j] ∨ s[j-1] ∨ s[j]
                        f.write(f"-{base_y + j} {base_counter + j - 1} {base_counter + j} 0\n")

            # 关联约束
            for p_idx in range(n):
                perm = perms[p_idx]
                y = base_y + p_idx
                for c in range(16):
                    correct = perm[c]
                    for v in range(1, 17):
                        if v != correct:
                            f.write(f"-{y} -{cell_var(i, c, v)} 0\n")

    fsize2 = os.path.getsize(OUTPUT_L2)
    print(f"[{time.strftime('%H:%M:%S')}] Level 2 完成: {OUTPUT_L2}")
    print(f"  大小: {fsize2 / (1024*1024):.1f} MB")
    print(f"[{time.strftime('%H:%M:%S')}] 总耗时: {time.time()-t0:.1f} 秒")

if __name__ == "__main__":
    main()
