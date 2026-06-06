#!/usr/bin/env python3
"""
Level 2 CNF 生成器 v2 — 極致性能版
目標: ~270M 子句 / ~3.9GB
策略: 批量 buffer + 最小化 Python 開銷
"""
import json, os, time

BASE = r"D:/2026/WPF_Sudoku/Sudoku_256"
OUT = os.path.join(BASE, "fuhh_sudoku_level2.cnf")
G, V = 16, 16
X0 = 1  # X: 1..4096

def load():
    with open(os.path.join(BASE, "sudoku_config.json")) as f:
        cfg = json.load(f)
    known = {(e["row"]-1, e["col"]-1): e["value"]-1 for e in cfg["known_digits"]}

    perms = []
    for i in range(16):
        with open(os.path.join(BASE, f"A{i+1}_permutations.json")) as f:
            perms.append(json.load(f))
    return known, perms

def main():
    t0 = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] 載入資料...", flush=True)
    known, perms = load()
    counts = [len(p) for p in perms]
    total_p = sum(counts)
    n_known = len(known)
    print(f"  已知: {n_known}, 排列: {total_p:,}", flush=True)

    # P 變量起始編號
    p_off = [X0 + 4096 + sum(counts[:i]) for i in range(16)]
    # S 變量: 每行 n-1 個, S[i][k] (k=0..n-2) 起始編號
    # S[i][k] = S_START + sum(counts[j]-1 for j<i) + k
    s_base0 = p_off[0] + total_p - 16  # 緊接在所有P之後
    s_off = [0]*16
    s_off[0] = s_base0
    for i in range(1,16):
        s_off[i] = s_off[i-1] + counts[i-1] - 1

    n_vars = s_off[15] + counts[15] - 1
    print(f"  變量: {n_vars:,}", flush=True)

    # 子句數
    n_cl = 0
    n_cl += G*G*120*3  # 行+列+宮
    n_cl += 256*121     # 單元格
    n_cl += n_known
    for c in counts:
        n_cl += (4*c-4) + 16*c
    print(f"  子句: {n_cl:,} (~{n_cl*15//1024//1024} MB)", flush=True)

    f = open(OUT, 'w')
    f.write(f"c Level 2 完整編碼\n")
    f.write(f"c time={time.strftime('%H:%M:%S')}\n")
    f.write(f"p cnf {n_vars} {n_cl}\n")
    f.flush()

    # 批量 buffer
    B = []
    BSIZE = 200000

    def W(s):
        B.append(s)
        if len(B) >= BSIZE:
            f.write("\n".join(B)+"\n")
            B.clear()
            f.flush()

    print(f"[{time.strftime('%H:%M:%S')}] 行 AllDifferent...", flush=True)
    for r in range(G):
        for v in range(V):
            b = X0 + r*256 + v
            for a in range(G):
                va = b + a*G
                for c2 in range(a+1,G):
                    W(f"-{va} -{b+c2*G} 0")

    print(f"[{time.strftime('%H:%M:%S')}] 列 AllDifferent...", flush=True)
    for c in range(G):
        for v in range(V):
            b = X0 + c*16 + v
            for a in range(G):
                va = b + a*256
                for c2 in range(a+1,G):
                    W(f"-{va} -{b+c2*256} 0")

    print(f"[{time.strftime('%H:%M:%S')}] 宫 AllDifferent...", flush=True)
    for br in range(4):
        for bc in range(4):
            for v in range(V):
                box = [X0+(br*4+dr)*256+(bc*4+dc)*16+v for dr in range(4) for dc in range(4)]
                for a in range(16):
                    for c2 in range(a+1,16):
                        W(f"-{box[a]} -{box[c2]} 0")

    print(f"[{time.strftime('%H:%M:%S')}] 單元格 ExactlyOne...", flush=True)
    for r in range(G):
        for c in range(G):
            cv = [X0+r*256+c*16+v for v in range(V)]
            W(" ".join(str(x) for x in cv)+" 0")
            for a in range(V):
                for c2 in range(a+1,V):
                    W(f"-{cv[a]} -{cv[c2]} 0")

    print(f"[{time.strftime('%H:%M:%S')}] 已知數字...", flush=True)
    for (r,c),v in known.items():
        W(f"{X0+r*256+c*16+v} 0")

    print(f"[{time.strftime('%H:%M:%S')}] 符闔排列約束...", flush=True)
    for i in range(16):
        n = counts[i]
        p0 = p_off[i]
        s0 = s_off[i]
        print(f"  Row {i+1}: {n:,} perms (P:{p0}, S:{s0})", flush=True)

        # ALO
        if n > 0:
            W(" ".join(str(p0+j) for j in range(n)) + " 0")

        # Sequential counter AMO
        if n >= 2:
            for k in range(n):
                pk = p0 + k
                sk = s0 + k
                if k == 0:
                    # S[0] <-> P[0]
                    W(f"-{sk} {pk} 0")
                    W(f"-{pk} {sk} 0")
                else:
                    # S[k] <-> (S[k-1] v P[k])
                    W(f"-{sk} {s0+k-1} {pk} 0")
                    W(f"-{s0+k-1} {sk} 0")
                    W(f"-{pk} {sk} 0")
                    # AMO: !S[k-1] v !P[k]
                    W(f"-{s0+k-1} -{pk} 0")

        # Association: !P[j] v X[c][perm[j][c]]
        for j in range(n):
            perm = perms[i][j]
            pj = p0 + j
            for c in range(G):
                W(f"-{pj} {X0+i*256+c*16+perm[c]} 0")

        if i < 15:
            pct = (i+1)/16*100
            print(f"  progress {pct:.0f}%", flush=True)

    # 收尾
    if B:
        f.write("\n".join(B)+"\n")
    f.close()

    sz = os.path.getsize(OUT)
    el = time.time()-t0
    print(f"\n[{time.strftime('%H:%M:%S')}] DONE!", flush=True)
    print(f"  {OUT}")
    print(f"  size={sz//1024//1024} MB, vars={n_vars:,}, clauses={n_cl:,}")
    print(f"  elapsed={el:.0f}s ({el/60:.1f} min)", flush=True)

if __name__=="__main__":
    main()
