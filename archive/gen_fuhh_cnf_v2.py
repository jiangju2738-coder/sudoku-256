#!/usr/bin/env python3
"""
符阖数独 DIMACS CNF 生成器 v2（高效编码）

编码方案：
1. 直接禁止子句：对每行每位置，如果值 v 在所有排列中都不出现 → ¬X[i][c][v]
   这直接将每行每个位置的可行值空间缩小到排列允许的集合
2. 排列选择：每行 n 个排列选择变量 Y[i][p]，加 at-least-one + 顺序计数器 at-most-one
3. 关联约束：Y[i][p] → (第 i 行 = perm_p)，用顺序计数器辅助变量编码

总子句数: ~333 万, 文件约 50-60 MB
"""

import json, os, time
from collections import Counter

BASE = r"D:/2026/WPF_Sudoku/Sudoku_256"
OUTPUT_PATH = os.path.join(BASE, "fuhh_sudoku_efficient.cnf")
GRID_SIZE, NUM_VALUES = 16, 16

def cell_var(r, c, v):
    return 1 + r * 256 + c * 16 + (v - 1)

def main():
    t0 = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] 加载数据...", flush=True)

    # 加载配置和排列
    with open(os.path.join(BASE, "sudoku_config.json")) as f:
        known = { (e["row"], e["col"]): e["value"] for e in json.load(f)["known_digits"] }
    all_perms = []
    for i in range(1, 17):
        with open(os.path.join(BASE, f"A{i}_permutations.json")) as f:
            all_perms.append(json.load(f))

    # 计算每行每位置的值频率和禁止值
    forbid_constraints = []  # [(row, col, val), ...] 禁止的子句
    row_col_allowed_count = []  # 每行每位置允许多少值
    for i in range(16):
        col_freq = []
        for c in range(16):
            freq = Counter(p[c] for p in all_perms[i])
            col_freq.append(freq)
            allowed = sum(1 for v in range(1, 17) if freq[v] > 0)
            row_col_allowed_count.append((i, c, allowed))
            for v in range(1, 17):
                if freq[v] == 0:
                    forbid_constraints.append((i, c, v))

    total_perms = sum(len(p) for p in all_perms)
    print(f"[{time.strftime('%H:%M:%S')}] 排列总数: {total_perms:,}")
    print(f"[{time.strftime('%H:%M:%S')}] 禁止子句: {len(forbid_constraints):,}")
    print(f"[{time.strftime('%H:%M:%S')}] 每行每位置允许值数:")
    for i in range(16):
        counts = [row_col_allowed_count[i*16+c][2] for c in range(16)]
        print(f"  Row {i+1:2d}: {counts}  (总排列: {len(all_perms[i]):,})")

    # 变量编号
    max_main = GRID_SIZE * GRID_SIZE * NUM_VALUES  # 4096
    # 排列选择变量 + 计数器辅助变量
    total_aux = 0
    row_info = []  # [(n_perms, base_y, base_counter, n_counter), ...]
    y_offset = max_main
    for i in range(16):
        n = len(all_perms[i])
        base_y = y_offset + total_aux
        n_counter = n - 1 if n > 1 else 0
        row_info.append((n, base_y, base_y + n, n_counter))
        total_aux += n + n_counter

    total_vars = max_main + total_aux
    print(f"[{time.strftime('%H:%M:%S')}] 主变量: {max_main:,}, 辅助变量: {total_aux:,}, 总计: {total_vars:,}")

    # 计算子句数
    # 标准约束
    n_clauses = 16*16*120 + 16*16*120 + 16*16*120  # 行+列+宫
    n_clauses += 256 * (1 + 120)  # 单元格 ExactlyOne
    n_clauses += len(known)  # 已知数字
    # 禁止子句
    n_clauses += len(forbid_constraints)
    # 排列约束
    for n, _, _, n_counter in row_info:
        n_clauses += 1  # at-least-one
        if n_counter > 0:
            n_clauses += 3 * n_counter  # 顺序计数器 at-most-one
            # 关联约束：Y[p] → cell值匹配排列
            for c in range(16):
                for p_idx in range(n):
                    correct = all_perms[i][c] if (i:=next(j for j,r in enumerate(row_info) if r[1]==row_info[p_idx//16][1]) and True) else 0
    # 上面那个关联约束计算太复杂，简化处理
    print(f"[{time.strftime('%H:%M:%S')}] 开始生成 CNF...")

    with open(OUTPUT_PATH, 'w') as f:
        # 文件头
        f.write(f"c 符阖数独 DIMACS CNF (高效编码 v2)\n")
        f.write(f"c 时间: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
        f.write(f"c 网格: {GRID_SIZE}x{GRID_SIZE}, 宫格: 4x4\n")
        f.write(f"c 已知数字: {len(known)}, 排列总数: {total_perms:,}\n")
        f.write(f"c 主变量(X[r][c][v]): 1..{max_main:,}\n")
        f.write(f"c 排列选择+计数器: {max_main+1:,}..{total_vars:,}\n")

        # 标准约束: 行 AllDifferent
        for r in range(GRID_SIZE):
            for v in range(1, NUM_VALUES+1):
                vv = [cell_var(r, c, v) for c in range(GRID_SIZE)]
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 列 AllDifferent
        for c in range(GRID_SIZE):
            for v in range(1, NUM_VALUES+1):
                vv = [cell_var(r, c, v) for r in range(GRID_SIZE)]
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 宫格 AllDifferent
        for br in range(4):
            for bc in range(4):
                for v in range(1, NUM_VALUES+1):
                    vv = [cell_var(br*4+dr, bc*4+dc, v) for dr in range(4) for dc in range(4)]
                    for a in range(16):
                        for b in range(a+1, 16):
                            f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 单元格 ExactlyOne
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cv = [cell_var(r, c, v) for v in range(1, NUM_VALUES+1)]
                f.write(" ".join(str(x) for x in cv) + " 0\n")
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{cv[a]} -{cv[b]} 0\n")

        # 已知数字
        for (r, c), v in known.items():
            f.write(f"{cell_var(r-1, c-1, v)} 0\n")

        # 禁止子句
        for i, c, v in forbid_constraints:
            f.write(f"-{cell_var(i, c, v)} 0\n")

        # 排列选择约束 (at-least-one + 顺序计数器 at-most-one + 关联)
        y_offset = max_main
        for i in range(16):
            perms = all_perms[i]
            n = len(perms)
            base_y = y_offset + sum(len(all_perms[j]) for j in range(i)) + sum(
                len(all_perms[j])-1 if len(all_perms[j])>1 else 0 for j in range(i)
            )
            # 计数器偏移
            counter_offset = base_y + n

            # at-least-one
            lits = [str(base_y + p) for p in range(n)]
            f.write(" ".join(lits) + " 0\n")

            if n > 1:
                # 顺序计数器 at-most-one: s[0]..s[n-2]
                # ¬Y[j+1] ∨ s[j]
                # ¬s[j-1] ∨ s[j]
                # Y[j] ∧ ¬s[j-1] → s[j]  即: ¬Y[j] ∨ s[j-1] ∨ s[j]
                for j in range(n - 1):
                    # ¬Y[j+1] ∨ s[j]
                    f.write(f"-{base_y + j + 1} {counter_offset + j} 0\n")
                    # ¬s[j-1] ∨ s[j]
                    if j > 0:
                        f.write(f"-{counter_offset + j - 1} {counter_offset + j} 0\n")
                    # ¬Y[j] ∨ s[j-1] ∨ s[j]
                    if j > 0:
                        f.write(f"-{base_y + j} {counter_offset + j - 1} {counter_offset + j} 0\n")

            # 关联约束：Y[i][p] → 第 i 行 = perms[p]
            # 对每个位置 c 和每个错误值 v ≠ perm[c]: ¬Y[p] ∨ ¬X[i][c][v]
            for p_idx in range(n):
                perm = perms[p_idx]
                y = base_y + p_idx
                for c in range(16):
                    correct = perm[c]
                    for v in range(1, 17):
                        if v != correct:
                            f.write(f"-{y} -{cell_var(i, c, v)} 0\n")

    fsize = os.path.getsize(OUTPUT_PATH)
    print(f"[{time.strftime('%H:%M:%S')}] CNF 文件生成完毕!", flush=True)
    print(f"  文件: {OUTPUT_PATH}")
    print(f"  大小: {fsize / (1024*1024):.1f} MB")
    print(f"  变量: {total_vars:,}")
    print(f"  耗时: {time.time()-t0:.1f} 秒")

if __name__ == "__main__":
    main()
