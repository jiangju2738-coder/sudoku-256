#!/usr/bin/env python3
"""
符闔數獨 Level 2 CNF 生成器（完整精確編碼）

核心設計：
1. 主變量 X[i][c][v]：256個單元格 × 16個值 = 4,096 個變量
2. 排列選擇變量 P[i][j]：每行 i 有 n_i 個排列，總計 1,111,494 個變量
3. 順序計數器輔助變量 S[i][k]：每行 AMO 編碼需要 n_i-1 個輔助變量

編碼策略：
- ExactlyOne(P[i]) = ALO (1 條) + Sequential Counter AMO (4n_i - 5 條)
- 關聯約束：¬P[i][j] ∨ X[i][c][perm[j][c]]，共 16 × n_i 條/行
- 總計約 2,227,068 變量，~25M 子句

使用流式寫入，不將子句存入記憶體。
"""

import json, os, time
from itertools import combinations

BASE = r"D:/2026/WPF_Sudoku/Sudoku_256"
OUTPUT_PATH = os.path.join(BASE, "fuhh_sudoku_level2.cnf")
GRID_SIZE, NUM_VALUES = 16, 16
X_OFFSET = 0          # X 變量從 1 開始
P_OFFSET = GRID_SIZE * GRID_SIZE * NUM_VALUES  # 4096
CELL_VARS = X_OFFSET + 1  # X 變量起始 = 1

def cell_var(r, c, v):
    """X[r][c][v] → 變量編號 (r,c,v ∈ 0..15)"""
    return CELL_VARS + r * 256 + c * 16 + v

def main():
    t0 = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] === Level 2 完整編碼開始 ===", flush=True)

    # ===== 1. 加載數據 =====
    print(f"[{time.strftime('%H:%M:%S')}] 加載配置數據...", flush=True)
    with open(os.path.join(BASE, "sudoku_config.json")) as f:
        config = json.load(f)
    known = {(e["row"] - 1, e["col"] - 1): e["value"] - 1 for e in config["known_digits"]}

    all_perms = []
    perm_counts = []
    for i in range(16):
        with open(os.path.join(BASE, f"A{i+1}_permutations.json")) as f:
            perms = json.load(f)
        all_perms.append(perms)
        perm_counts.append(len(perms))

    n_known = len(known)
    total_perms = sum(perm_counts)
    print(f"  已知數字: {n_known} 個")
    print(f"  排列總數: {total_perms:,}")
    for i in range(16):
        print(f"  Row {i+1:2d}: {perm_counts[i]:>10,} 排列")

    # ===== 2. 計算變量編號 =====
    # X: 1 .. 4096
    # P[i][j]: 從 4097 開始連續分配
    p_offsets = [0] * 16  # p_offsets[i] = 行 i 的 P 變量起始編號
    p_offsets[0] = P_OFFSET + 1
    for i in range(1, 16):
        p_offsets[i] = p_offsets[i-1] + perm_counts[i-1]

    # S: 順序計數器輔助變量，在 P 變量之後
    s_offsets = [0] * 16  # s_offsets[i] = 行 i 的 S 變量起始編號
    s_offsets[0] = p_offsets[0] + perm_counts[0]
    for i in range(1, 16):
        s_offsets[i] = s_offsets[i-1] + (perm_counts[i-1] - 1)

    # 最後一個 S 變量編號
    last_s = s_offsets[15] + perm_counts[15] - 2  # S[n-1] 是最後一個，索引從1到n-1

    # S 變量實際從 s_offsets[0] + 1 開始（S[1]），因為 S[0] 是隱式的 False
    # 我們直接使用變量編號：S[i][k] = s_offsets[i] + k，k ∈ 1..n_i-1

    total_vars = s_offsets[15] + perm_counts[15] - 1  # 最後一個變量編號
    print(f"\n  變量編號範圍:")
    print(f"  X (單元格): {CELL_VARS:,} .. {CELL_VARS + 4095:,}  ({4096:,} 個)")
    print(f"  P (排列選擇): {p_offsets[0]:,} .. {p_offsets[0] + total_perms - 1:,}  ({total_perms:,} 個)")
    print(f"  S (計數器):   {s_offsets[0]:,} .. {last_s:,}  ({total_perms - 16:,} 個)")
    print(f"  總變量數: {total_vars:,}")

    # ===== 3. 計算子句數 =====
    # 標準數独約束
    n_clauses = 0
    n_clauses += 16 * 16 * 120  # 行 AllDifferent (pairwise)
    n_clauses += 16 * 16 * 120  # 列 AllDifferent
    n_clauses += 16 * 16 * 120  # 宫 AllDifferent
    n_clauses += 256 * (1 + 120)  # 單元格 ExactlyOne (ALO + AMO pairwise)
    n_clauses += n_known  # 已知數字

    # 符闔排列約束
    eo_clauses = 0  # ExactlyOne(P[i]) 子句數
    assoc_clauses = 0  # 關聯約束子句數
    for i in range(16):
        n = perm_counts[i]
        # ExactlyOne(n) = ALO(1) + AMO(4n-5) = 4n-4
        eo_clauses += 4 * n - 4
        # 關聯約束：16 × n
        assoc_clauses += 16 * n

    n_clauses += eo_clauses + assoc_clauses

    print(f"\n  子句分解:")
    print(f"  行 AllDifferent: {16*16*120:,}")
    print(f"  列 AllDifferent: {16*16*120:,}")
    print(f"  宫 AllDifferent: {16*16*120:,}")
    print(f"  單元格 ExactlyOne: {256*121:,}")
    print(f"  已知數字: {n_known}")
    print(f"  ExactlyOne(P): {eo_clauses:,}")
    print(f"  關聯約束: {assoc_clauses:,}")
    print(f"  總子句數: {n_clauses:,}")

    est_size_mb = n_clauses * 15 // 1024 // 1024
    print(f"\n  預計文件大小: ~{est_size_mb} MB")

    # ===== 4. 流式寫入 CNF =====
    print(f"\n[{time.strftime('%H:%M:%S')}] 開始寫入 CNF 文件...", flush=True)

    with open(OUTPUT_PATH, 'w') as f:
        # 文件頭
        f.write(f"c 符闔數獨 Level 2 CNF (完整精確編碼)\n")
        f.write(f"c 生成時間: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
        f.write(f"c 網格: {GRID_SIZE}x{GRID_SIZE}, 宫格: 4x4\n")
        f.write(f"c 已知數字: {n_known} 個\n")
        f.write(f"c 符闔排列總數: {total_perms:,}\n")
        f.write(f"c\n")
        f.write(f"c 變量編碼:\n")
        f.write(f"c   X[r][c][v] = {CELL_VARS} + r*256 + c*16 + v  (r,c,v ∈ 0..15)\n")
        f.write(f"c   P[i][j] = 行 i 選擇第 j 個排列的布林變量\n")
        f.write(f"c   S[i][k] = 行 i 的順序計數器輔助變量\n")
        f.write(f"c\n")
        f.write(f"c 約束:\n")
        f.write(f"c   1. 標準數獨: 行/列/宫 AllDifferent + 單元格 ExactlyOne\n")
        f.write(f"c   2. 已知數字: 固定值\n")
        f.write(f"c   3. ExactlyOne(P[i]): 每行恰好選擇一個符闔排列\n")
        f.write(f"c   4. 關聯約束: P[i][j] → 行i的每個位置值 = perm[j][c]\n")
        f.write(f"c\n")
        f.write(f"c 變量: {total_vars:,}, 子句: {n_clauses:,}\n")
        f.write(f"p cnf {total_vars} {n_clauses}\n")

        # ---- 5.1 行 AllDifferent ----
        print(f"[{time.strftime('%H:%M:%S')}]   1. 行约束 ({16*16*120:,} 條)...", flush=True)
        for r in range(GRID_SIZE):
            for v in range(NUM_VALUES):
                vars_in_row = [cell_var(r, c, v) for c in range(GRID_SIZE)]
                for a in range(16):
                    va = vars_in_row[a]
                    for b in range(a + 1, 16):
                        f.write(f"-{va} -{vars_in_row[b]} 0\n")

        # ---- 5.2 列 AllDifferent ----
        print(f"[{time.strftime('%H:%M:%S')}]   2. 列约束 ({16*16*120:,} 條)...", flush=True)
        for c in range(GRID_SIZE):
            for v in range(NUM_VALUES):
                vars_in_col = [cell_var(r, c, v) for r in range(GRID_SIZE)]
                for a in range(16):
                    va = vars_in_col[a]
                    for b in range(a + 1, 16):
                        f.write(f"-{va} -{vars_in_col[b]} 0\n")

        # ---- 5.3 宫格 AllDifferent ----
        print(f"[{time.strftime('%H:%M:%S')}]   3. 宫格约束 ({16*16*120:,} 條)...", flush=True)
        for br in range(4):
            for bc in range(4):
                for v in range(NUM_VALUES):
                    vars_in_box = [cell_var(br * 4 + dr, bc * 4 + dc, v)
                                   for dr in range(4) for dc in range(4)]
                    for a in range(16):
                        va = vars_in_box[a]
                        for b in range(a + 1, 16):
                            f.write(f"-{va} -{vars_in_box[b]} 0\n")

        # ---- 5.4 單元格 ExactlyOne ----
        print(f"[{time.strftime('%H:%M:%S')}]   4. 單元格约束 ({256*121:,} 條)...", flush=True)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cv = [cell_var(r, c, v) for v in range(NUM_VALUES)]
                # ALO: 至少一個值
                f.write(" ".join(str(x) for x in cv) + " 0\n")
                # AMO: 至多一個值 (pairwise)
                for a in range(16):
                    for b in range(a + 1, 16):
                        f.write(f"-{cv[a]} -{cv[b]} 0\n")

        # ---- 5.5 已知數字 ----
        print(f"[{time.strftime('%H:%M:%S')}]   5. 已知數字 ({n_known} 條)...", flush=True)
        for (r, c), v in known.items():
            f.write(f"{cell_var(r, c, v)} 0\n")

        # ---- 5.6 符闔排列約束 ----
        print(f"[{time.strftime('%H:%M:%S')}]   6. 符闔排列約束...", flush=True)

        for i in range(16):
            n = perm_counts[i]
            p_base = p_offsets[i]
            s_base = s_offsets[i]

            print(f"  Row {i+1:2d}: {n:,} 排列 (P:{p_base}..{p_base+n-1}, S:{s_base+1}..{s_base+n-1})", flush=True)

            # ---- ExactlyOne(P[i]) ----
            # ALO: P[i][0] ∨ P[i][1] ∨ ... ∨ P[i][n-1]
            alo_vars = [p_base + j for j in range(n)]
            f.write(" ".join(str(v) for v in alo_vars) + " 0\n")

            # AMO: Sequential Counter 編碼
            # S[i][k] 表示 "前 k+1 個排列變量中至少一個為真"，k ∈ 0..n-2
            # S[i][-1] 隱式為 False

            if n >= 2:
                # i=0 (第一個 P 變量): S[0] ↔ P[0]
                # ¬S[0] ∨ P[0]
                f.write(f"-{s_base + 1} {p_base} 0\n")
                # ¬P[0] ∨ S[0]
                f.write(f"-{p_base} {s_base + 1} 0\n")
                # AMO: 隱式 S[-1]=False → 無需 ¬S[-1] ∨ ¬P[0]

                # i ≥ 1: S[i] ↔ (S[i-1] ∨ P[i])
                for k in range(1, n - 1):
                    s_k = s_base + k + 1       # S[k]
                    s_prev = s_base + k        # S[k-1]
                    p_k = p_base + k + 1       # P[k+1]
                    # ¬S[k] ∨ S[k-1] ∨ P[k+1]
                    f.write(f"-{s_k} {s_prev} {p_k} 0\n")
                    # ¬S[k-1] ∨ S[k]
                    f.write(f"-{s_prev} {s_k} 0\n")
                    # ¬P[k+1] ∨ S[k]
                    f.write(f"-{p_k} {s_k} 0\n")

                # AMO 約束: ¬S[k-1] ∨ ¬P[k] for k = 1..n-1
                # 以及 ¬S[n-2] ∨ ¬P[n-1]
                for k in range(1, n):
                    if k == 1:
                        # ¬S[0] ∨ ¬P[1]
                        f.write(f"-{s_base + 1} -{p_base + 1} 0\n")
                    else:
                        # ¬S[k-1] ∨ ¬P[k]
                        f.write(f"-{s_base + k} -{p_base + k} 0\n")

            # ---- 關聯約束: P[i][j] → X[i][c][perm[j][c]] ----
            # 等價於: ¬P[i][j] ∨ X[i][c][perm[j][c]]
            for j in range(n):
                perm = all_perms[i][j]
                for c in range(16):
                    val = perm[c]
                    f.write(f"-{p_base + j} {cell_var(i, c, val)} 0\n")

            # 進度更新
            if i < 15:
                progress = (i + 1) / 16 * 100
                print(f"  進度: {progress:.0f}% 完成", flush=True)

    fsize = os.path.getsize(OUTPUT_PATH)
    elapsed = time.time() - t0
    print(f"\n[{time.strftime('%H:%M:%S')}] === Level 2 CNF 生成完成 ===", flush=True)
    print(f"  文件: {OUTPUT_PATH}")
    print(f"  大小: {fsize / 1024 / 1024:.1f} MB")
    print(f"  變量: {total_vars:,}")
    print(f"  子句: {n_clauses:,}")
    print(f"  耗時: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分鐘)")


if __name__ == "__main__":
    main()
