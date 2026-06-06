#!/usr/bin/env python3
"""
符闔數獨 Level 2 CNF 生成器 — 高度優化版本
使用 buffer 批量寫入 + 最小化 Python 循環開銷
"""
import json, os, time, sys

BASE = r"D:/2026/WPF_Sudoku/Sudoku_256"
OUTPUT_PATH = os.path.join(BASE, "fuhh_sudoku_level2.cnf")
GRID_SIZE, NUM_VALUES = 16, 16

def main():
    t0 = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] === Level 2 CNF 生成開始 ===", flush=True)

    # ===== 1. 載入資料 =====
    with open(os.path.join(BASE, "sudoku_config.json")) as f:
        config = json.load(f)
    known = {(e["row"] - 1, e["col"] - 1): e["value"] - 1 for e in config["known_digits"]}

    all_perms = []
    perm_counts = []
    for i in range(16):
        with open(os.path.join(BASE, f"A{i+1}_permutations.json")) as f:
            all_perms.append(json.load(f))
        perm_counts.append(len(all_perms[i]))

    n_known = len(known)
    total_perms = sum(perm_counts)
    print(f"  已知數字: {n_known}, 排列總數: {total_perms:,}", flush=True)

    # ===== 2. 計算變量編號 =====
    X_START = 1
    X_END = GRID_SIZE * GRID_SIZE * NUM_VALUES  # 4096
    P_START = X_END + 1
    p_offsets = [P_START + sum(perm_counts[:i]) for i in range(16)]
    S_START = p_offsets[0] + perm_counts[0] + (total_perms - 16) - (total_perms - 16)
    # S 變量: 每行 n-1 個，總計 total_perms - 16
    s_offsets = [S_START + sum(perm_counts[:i] - 1 for i in range(i))] if False else []
    s_offsets = [0] * 16
    s_offsets[0] = P_START + total_perms - 16
    for i in range(1, 16):
        s_offsets[i] = s_offsets[i-1] + perm_counts[i-1] - 1

    S_END = s_offsets[15] + perm_counts[15] - 1
    total_vars = S_END
    print(f"  變量: {total_vars:,}", flush=True)

    # ===== 3. 計算子句數 =====
    n_clauses = 0
    n_clauses += 16 * 16 * 120 * 3  # 行+列+宮 AllDifferent
    n_clauses += 256 * 121           # 單元格 ExactlyOne
    n_clauses += n_known             # 已知數字
    for i in range(16):
        n = perm_counts[i]
        n_clauses += (4 * n - 4) + (16 * n)  # ExactlyOne + 關聯
    print(f"  子句: {n_clauses:,}", flush=True)

    # ===== 4. 寫入 CNF =====
    f = open(OUTPUT_PATH, 'w')
    f.write(f"c 符闔數獨 Level 2 CNF\n")
    f.write(f"c 生成: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
    f.write(f"c 網格: {GRID_SIZE}x{GRID_SIZE}, 已知數字: {n_known}, 排列總數: {total_perms:,}\n")
    f.write(f"c 變量: X[1..{X_END}] P[{P_START}..{P_START+total_perms-1}] S[{S_START}..{S_END}]\n")
    f.write(f"p cnf {total_vars} {n_clauses}\n")
    f.flush()

    buf = []
    BUF_SIZE = 500000

    def write_clauses(lines):
        nonlocal buf
        buf.extend(lines)
        if len(buf) > BUF_SIZE:
            f.write("\n".join(buf) + "\n")
            buf = []
            f.flush()

    def flush():
        nonlocal buf
        if buf:
            f.write("\n".join(buf) + "\n")
            buf = []
            f.flush()

    # 5.1 行 AllDifferent
    print(f"[{time.strftime('%H:%M:%S')}]   1. 行 AllDifferent...", flush=True)
    for r in range(GRID_SIZE):
        for v in range(NUM_VALUES):
            base = X_START + r * 256 + v
            for a in range(16):
                va = base + a * 16
                for b in range(a + 1, 16):
                    write_clauses([f"-{va} -{base + b * 16} 0"])

    # 5.2 列 AllDifferent
    print(f"[{time.strftime('%H:%M:%S')}]   2. 列 AllDifferent...", flush=True)
    for c in range(GRID_SIZE):
        for v in range(NUM_VALUES):
            base = X_START + c * 16 + v
            for a in range(16):
                va = base + a * 256
                for b in range(a + 1, 16):
                    write_clauses([f"-{va} -{base + b * 256} 0"])

    # 5.3 宫格 AllDifferent
    print(f"[{time.strftime('%H:%M:%S')}]   3. 宫格 AllDifferent...", flush=True)
    for br in range(4):
        for bc in range(4):
            for v in range(NUM_VALUES):
                vars_in_box = []
                for dr in range(4):
                    for dc in range(4):
                        vars_in_box.append(X_START + (br * 4 + dr) * 256 + (bc * 4 + dc) * 16 + v)
                for a in range(16):
                    for b in range(a + 1, 16):
                        write_clauses([f"-{vars_in_box[a]} -{vars_in_box[b]} 0"])

    flush()

    # 5.4 單元格 ExactlyOne
    print(f"[{time.strftime('%H:%M:%S')}]   4. 單元格 ExactlyOne...", flush=True)
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            cv = [X_START + r * 256 + c * 16 + v for v in range(NUM_VALUES)]
            write_clauses([" ".join(str(x) for x in cv) + " 0"])
            for a in range(16):
                for b in range(a + 1, 16):
                    write_clauses([f"-{cv[a]} -{cv[b]} 0"])
    flush()

    # 5.5 已知數字
    print(f"[{time.strftime('%H:%M:%S')}]   5. 已知數字...", flush=True)
    for (r, c), v in known.items():
        write_clauses([f"{X_START + r * 256 + c * 16 + v} 0"])
    flush()

    # 5.6 符闔排列約束
    print(f"[{time.strftime('%H:%M:%S')}]   6. 符闔排列約束...", flush=True)
    for i in range(16):
        n = perm_counts[i]
        p_base = p_offsets[i]
        s_base = s_offsets[i]

        print(f"  Row {i+1:2d}: {n:,} 排列", flush=True)

        if n >= 1:
            # ALO
            write_clauses([" ".join(str(p_base + j) for j in range(n)) + " 0"])

        if n >= 2:
            # S↔P 關聯 + AMO 約束
            for k in range(n):
                pk = p_base + k
                if k == 0:
                    # S[0] ↔ P[0]
                    s0 = s_base
                    write_clauses([f"-{s0} {pk} 0", f"-{pk} {s0} 0"])
                    # AMO: 隱式
                else:
                    # S[k] ↔ (S[k-1] ∨ P[k])
                    sk = s_base + k
                    sk_1 = s_base + k - 1
                    write_clauses([f"-{sk} {sk_1} {pk} 0", f"-{sk_1} {sk} 0", f"-{pk} {sk} 0"])
                    # AMO: ¬S[k-1] ∨ ¬P[k]
                    write_clauses([f"-{sk_1} -{pk} 0"])

        # 關聯約束: ¬P[i][j] ∨ X[i][c][perm[j][c]]
        for j in range(n):
            perm = all_perms[i][j]
            pj = p_base + j
            for c in range(16):
                val = perm[c]
                xvar = X_START + i * 256 + c * 16 + val
                write_clauses([f"-{pj} {xvar} 0"])
            if j % 50000 == 0 and j > 0:
                print(f"    進度: {j}/{n} ({j/n*100:.0f}%)", flush=True)
                flush()

    flush()
    f.close()

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
