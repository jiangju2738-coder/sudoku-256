#!/usr/bin/env python3
"""
符阖数独 DIMACS CNF 生成器 v2
编码方案：位级编码（bit-level encoding）

变量：
  主变量 X[r][c][v] = 1 + r*256 + c*16 + (v-1)  [1..4096]
  排列选择 Y[i][p] 从 4097 开始连续编号

约束：
  1. 标准数独：行/列/宫 AllDifferent + 单元格 ExactlyOne + 已知数字
  2. 符阖排列：
     - 每行至少选一个排列 (at-least-one, 16 条)
     - 位级约束：选择排列 p 时，该行每个位置值必须匹配排列
       ¬Y[i][p] ∨ ¬X[i][c][v]  for all v ≠ perm[c]
     - at-most-one 是多余的（AllDifferent 自动阻止选多个排列）

子句规模：标准约束 ~69K, 位级编码 ~267M, 总计 ~267M 子句, ~4.5GB
"""

import json
import os
import time
from collections import Counter

BASE = r"D:/2026/WPF_Sudoku/Sudoku_256"
CONFIG_PATH = os.path.join(BASE, "sudoku_config.json")
OUTPUT_PATH = os.path.join(BASE, "fuhh_sudoku_with_perms.cnf")

GRID_SIZE = 16
BOX_SIZE = 4
NUM_VALUES = 16

def load_config():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    known = {}
    for entry in config["known_digits"]:
        r, c, v = entry["row"], entry["col"], entry["value"]
        known[(r, c)] = v
    return config, known

def load_permutations():
    all_perms = []
    for i in range(1, 17):
        with open(os.path.join(BASE, f"A{i}_permutations.json")) as f:
            all_perms.append(json.load(f))
    return all_perms

def cell_var(row, col, val):
    """row, col: 0-indexed; val: 1-16"""
    return 1 + row * 256 + col * 16 + (val - 1)

def add_clauses_file(f, clauses_list, batch_size=50000):
    """流式写入子句列表到文件"""
    buf = []
    for clause in clauses_list:
        buf.append(" ".join(str(x) for x in clause) + " 0\n")
        if len(buf) >= batch_size:
            f.writelines(buf)
            buf = []
    if buf:
        f.writelines(buf)

def main():
    t0 = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] 开始生成符阖数独 CNF...", flush=True)

    config, known = load_config()
    all_perms = load_permutations()

    n_known = len(known)
    total_perms = sum(len(p) for p in all_perms)
    print(f"[{time.strftime('%H:%M:%S')}] 已知数字: {n_known}, 排列总数: {total_perms:,}")

    # ===== 变量编号 =====
    max_main = GRID_SIZE * GRID_SIZE * NUM_VALUES  # 4096
    perm_offset = max_main  # 4096
    perm_start = [perm_offset]
    for i in range(16):
        perm_start.append(perm_offset + sum(len(all_perms[j]) for j in range(i + 1)))
    num_perm_vars = perm_start[16] - perm_offset
    total_vars = perm_start[16]

    print(f"[{time.strftime('%H:%M:%S')}] 主变量: {max_main:,}, 排列选择变量: {num_perm_vars:,}, 总计: {total_vars:,}")

    # ===== 计算总子句数 =====
    # 标准约束
    n_clauses = 0
    # 行 AllDifferent: 16行 × 16值 × C(16,2)
    n_clauses += 16 * 16 * 120  # 30720
    # 列 AllDifferent
    n_clauses += 16 * 16 * 120  # 30720
    # 宫格 AllDifferent: 16宫 × 16值 × C(16,2)
    n_clauses += 16 * 16 * 120  # 30720
    # 单元格 ExactlyOne: 256 × (1 + C(16,2))
    n_clauses += 256 * (1 + 120)  # 30976
    # 已知数字
    n_clauses += n_known  # 55
    print(f"[{time.strftime('%H:%M:%S')}] 标准约束子句: {n_clauses:,}")

    # 位级编码 + at-least-one
    bit_clauses = 0
    for i in range(16):
        n = len(all_perms[i])
        bit_clauses += 16 * n * 15  # 位级
    n_atleast = 16  # 每行 1 条
    total_clauses = n_clauses + bit_clauses + n_atleast
    print(f"[{time.strftime('%H:%M:%S')}] 位级编码子句: {bit_clauses:,}")
    print(f"[{time.strftime('%H:%M:%S')}] 总计子句: {total_clauses:,}")

    # ===== 写入文件 =====
    print(f"[{time.strftime('%H:%M:%S')}] 正在写入 CNF 文件...", flush=True)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        # 文件头
        f.write(f"c 符阖数独 DIMACS CNF (位级编码)\n")
        f.write(f"c 时间: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
        f.write(f"c 网格: {GRID_SIZE}x{GRID_SIZE}, 宫格: {BOX_SIZE}x{BOX_SIZE}\n")
        f.write(f"c 已知数字: {n_known} 个\n")
        f.write(f"c 符阖排列: {total_perms:,}\n")
        f.write(f"c 主变量(X[r][c][v]): 1..{max_main:,}\n")
        f.write(f"c 排列选择(Y[i][p]): {perm_offset+1:,}..{total_vars:,}\n")
        f.write(f"c 变量: {total_vars:,} 子句: {total_clauses:,}\n")
        f.write(f"p cnf {total_vars} {total_clauses}\n")

        # ===== 1. 行 AllDifferent =====
        print(f"[{time.strftime('%H:%M:%S')}]   行约束...", flush=True)
        for r in range(GRID_SIZE):
            for v in range(1, NUM_VALUES + 1):
                v_vars = [cell_var(r, c, v) for c in range(GRID_SIZE)]
                for a in range(16):
                    for b in range(a + 1, 16):
                        f.write(f"-{v_vars[a]} -{v_vars[b]} 0\n")

        # ===== 2. 列 AllDifferent =====
        print(f"[{time.strftime('%H:%M:%S')}]   列约束...", flush=True)
        for c in range(GRID_SIZE):
            for v in range(1, NUM_VALUES + 1):
                v_vars = [cell_var(r, c, v) for r in range(GRID_SIZE)]
                for a in range(16):
                    for b in range(a + 1, 16):
                        f.write(f"-{v_vars[a]} -{v_vars[b]} 0\n")

        # ===== 3. 宫格 AllDifferent =====
        print(f"[{time.strftime('%H:%M:%S')}]   宫格约束...", flush=True)
        for br in range(GRID_SIZE // BOX_SIZE):
            for bc in range(GRID_SIZE // BOX_SIZE):
                for v in range(1, NUM_VALUES + 1):
                    v_vars = []
                    for dr in range(BOX_SIZE):
                        for dc in range(BOX_SIZE):
                            r = br * BOX_SIZE + dr
                            c = bc * BOX_SIZE + dc
                            v_vars.append(cell_var(r, c, v))
                    for a in range(16):
                        for b in range(a + 1, 16):
                            f.write(f"-{v_vars[a]} -{v_vars[b]} 0\n")

        # ===== 4. 单元格 ExactlyOne =====
        print(f"[{time.strftime('%H:%M:%S')}]   单元格约束...", flush=True)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell_vals = [cell_var(r, c, v) for v in range(1, NUM_VALUES + 1)]
                # at-least-one
                f.write(" ".join(str(v) for v in cell_vals) + " 0\n")
                # at-most-one
                for a in range(16):
                    for b in range(a + 1, 16):
                        f.write(f"-{cell_vals[a]} -{cell_vals[b]} 0\n")

        # ===== 5. 已知数字 =====
        print(f"[{time.strftime('%H:%M:%S')}]   已知数字...", flush=True)
        for (r, c), v in known.items():
            f.write(f"{cell_var(r - 1, c - 1, v)} 0\n")

        # ===== 6. 符阖排列 at-least-one =====
        print(f"[{time.strftime('%H:%M:%S')}]   排列 at-least-one...", flush=True)
        for i in range(16):
            n = len(all_perms[i])
            base = perm_start[i] + 1
            lits = [str(base + p) for p in range(n)]
            f.write(" ".join(lits) + " 0\n")

        # ===== 7. 位级编码 =====
        print(f"[{time.strftime('%H:%M:%S')}]   位级编码 (2.67 亿子句)...", flush=True)
        for i in range(16):
            perms = all_perms[i]
            n = len(perms)
            base = perm_start[i] + 1
            for p_idx in range(n):
                perm = perms[p_idx]
                y_var = base + p_idx
                for c in range(GRID_SIZE):
                    correct_val = perm[c]
                    for v in range(1, NUM_VALUES + 1):
                        if v != correct_val:
                            x_var = cell_var(i, c, v)
                            f.write(f"-{y_var} -{x_var} 0\n")

    t2 = time.time()
    fsize = os.path.getsize(OUTPUT_PATH)
    print(f"[{time.strftime('%H:%M:%S')}] CNF 文件生成完毕!", flush=True)
    print(f"  文件: {OUTPUT_PATH}", flush=True)
    print(f"  大小: {fsize / (1024*1024):.1f} MB", flush=True)
    print(f"  变量: {total_vars:,}", flush=True)
    print(f"  子句: {total_clauses:,}", flush=True)
    print(f"  耗时: {t2 - t0:.1f} 秒", flush=True)

if __name__ == "__main__":
    main()
