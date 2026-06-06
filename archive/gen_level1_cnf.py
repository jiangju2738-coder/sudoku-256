#!/usr/bin/env python3
"""
符闔數獨 Level 1 CNF 生成器（禁止子句版本）

约束：
1. 标准数独：行/列/宫 AllDifferent + 单元格 ExactlyOne
2. 已知数字
3. 禁止子句：对每行每位置，如果值 v 在所有排列中都不出现 → ¬X[i][c][v]

注意：Level 1 只能确保每行每位置的值来自允许集合，
不能确保整行恰好等于某个排列（混合排列解是可能的）。
用于快速测试和基准比较。

如需完整编码，见 gen_level2_cnf.py
"""

import json, os, time
from collections import Counter

BASE = r"D:/2026/WPF_Sudoku/Sudoku_256"
OUTPUT_PATH = os.path.join(BASE, "fuhh_sudoku_level1.cnf")
GRID_SIZE, NUM_VALUES = 16, 16

def cell_var(r, c, v):
    return 1 + r * 256 + c * 16 + (v - 1)

def main():
    t0 = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] 加载数据...", flush=True)

    with open(os.path.join(BASE, "sudoku_config.json")) as f:
        config = json.load(f)
    known = { (e["row"], e["col"]): e["value"] for e in config["known_digits"] }

    all_perms = []
    for i in range(1, 17):
        with open(os.path.join(BASE, f"A{i}_permutations.json")) as f:
            all_perms.append(json.load(f))

    # 计算禁止值
    forbid = []
    col_info = []  # [(i, c, allowed_count), ...]
    for i in range(16):
        for c in range(16):
            allowed = set(p[c] for p in all_perms[i])
            col_info.append((i, c, len(allowed)))
            for v in range(1, 17):
                if v not in allowed:
                    forbid.append((i, c, v))

    n_known = len(known)
    total_perms = sum(len(p) for p in all_perms)

    # 变量数
    total_vars = GRID_SIZE * GRID_SIZE * NUM_VALUES  # 4096

    # 子句数
    n_clauses = 0
    n_clauses += 16 * 16 * 120  # 行 AllDifferent
    n_clauses += 16 * 16 * 120  # 列 AllDifferent
    n_clauses += 16 * 16 * 120  # 宫 AllDifferent
    n_clauses += 256 * (1 + 120)  # 单元格 ExactlyOne
    n_clauses += n_known  # 已知数字
    n_clauses += len(forbid)  # 禁止子句

    print(f"[{time.strftime('%H:%M:%S')}] 已知数字: {n_known}")
    print(f"[{time.strftime('%H:%M:%S')}] 排列总数: {total_perms:,}")
    print(f"[{time.strftime('%H:%M:%S')}] 禁止子句: {len(forbid):,}")
    print(f"[{time.strftime('%H:%M:%S')}] 变量: {total_vars:,}, 子句: {n_clauses:,}")

    # 写入 CNF
    with open(OUTPUT_PATH, 'w') as f:
        f.write(f"c 符闔數獨 Level 1 CNF (禁止子句)\n")
        f.write(f"c 時間: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
        f.write(f"c 網格: {GRID_SIZE}x{GRID_SIZE}, 宫格: 4x4\n")
        f.write(f"c 已知數字: {n_known} 個\n")
        f.write(f"c 符闔排列總數: {total_perms:,}\n")
        f.write(f"c 主變量(X[r][c][v]): 1..{total_vars:,}\n")
        f.write(f"c 子句分解: 行{16*16*120:,} + 列{16*16*120:,} + 宫{16*16*120:,} + 單元{256*121:,} + 已知{n_known} + 禁止{len(forbid):,}\n")
        f.write(f"c 總子句: {n_clauses:,}\n")
        f.write(f"p cnf {total_vars} {n_clauses}\n")

        # 1. 行 AllDifferent
        print(f"[{time.strftime('%H:%M:%S')}]   行约束...", flush=True)
        for r in range(GRID_SIZE):
            for v in range(1, NUM_VALUES+1):
                vv = [cell_var(r, c, v) for c in range(GRID_SIZE)]
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 2. 列 AllDifferent
        print(f"[{time.strftime('%H:%M:%S')}]   列约束...", flush=True)
        for c in range(GRID_SIZE):
            for v in range(1, NUM_VALUES+1):
                vv = [cell_var(r, c, v) for r in range(GRID_SIZE)]
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 3. 宫格 AllDifferent
        print(f"[{time.strftime('%H:%M:%S')}]   宫格约束...", flush=True)
        for br in range(4):
            for bc in range(4):
                for v in range(1, NUM_VALUES+1):
                    vv = [cell_var(br*4+dr, bc*4+dc, v) for dr in range(4) for dc in range(4)]
                    for a in range(16):
                        for b in range(a+1, 16):
                            f.write(f"-{vv[a]} -{vv[b]} 0\n")

        # 4. 单元格 ExactlyOne
        print(f"[{time.strftime('%H:%M:%S')}]   单元格约束...", flush=True)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cv = [cell_var(r, c, v) for v in range(1, NUM_VALUES+1)]
                # at-least-one
                f.write(" ".join(str(x) for x in cv) + " 0\n")
                # at-most-one
                for a in range(16):
                    for b in range(a+1, 16):
                        f.write(f"-{cv[a]} -{cv[b]} 0\n")

        # 5. 已知数字
        print(f"[{time.strftime('%H:%M:%S')}]   已知数字...", flush=True)
        for (r, c), v in known.items():
            f.write(f"{cell_var(r-1, c-1, v)} 0\n")

        # 6. 禁止子句
        print(f"[{time.strftime('%H:%M:%S')}]   禁止子句 ({len(forbid):,}条)...", flush=True)
        for i, c, v in forbid:
            f.write(f"-{cell_var(i, c, v)} 0\n")

    fsize = os.path.getsize(OUTPUT_PATH)
    print(f"[{time.strftime('%H:%M:%S')}] Level 1 CNF 生成完成!", flush=True)
    print(f"  文件: {OUTPUT_PATH}")
    print(f"  大小: {fsize / 1024:.1f} KB")
    print(f"  变量: {total_vars:,}")
    print(f"  子句: {n_clauses:,}")
    print(f"  耗时: {time.time()-t0:.1f} 秒")

    # 打印每行每列允许值数的摘要
    print(f"\n=== 每行每列允许值数 ===")
    for i in range(16):
        counts = [col_info[i*16+c][2] for c in range(16)]
        print(f"  Row {i+1:2d}: {counts}  (排列数: {len(all_perms[i]):,})")

if __name__ == "__main__":
    main()
