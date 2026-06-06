#!/usr/bin/env python3
"""
修复 Level 2 CNF v7 — 最终修正版
修正: 1) AMO 范围 range(n16-1) 2) 额外 AMO !S[n16-2] v !P[n16-1] 3) n_vars 正确值
"""
import json, os, subprocess

BASE = r"D:/2026/WPF_Sudoku/Sudoku_256"
CNF = os.path.join(BASE, "fuhh_sudoku_level2.cnf")
X0, X_END = 1, 4096

counts = [8731,902,407669,1980,633271,359,2356,4782,164,28984,2972,620,484,10668,5990,1562]
cumsum = [0]
for c in counts: cumsum.append(cumsum[-1]+c)
total_p = cumsum[-1]

# S 偏移 (v2 公式)
s_base0 = X_END + total_p - 15
s_off = [0]*16
s_off[0] = s_base0
for i in range(1,16): s_off[i] = s_off[i-1] + counts[i-1] - 1

# 修正: n_vars 应该是最后一个有效 S 变量 = S[n16-2]
n16 = counts[15]
n_vars = s_off[15] + n16 - 2  # = 2227052, 不是 2227053

# 计算截断点 (Row 16 之前)
fixed = 16*16*120*3 + 256*121 + 92
rows_1_15 = sum((4*c-1)+16*c for c in counts[:15])
truncate_to = fixed + rows_1_15

print(f"truncate_to = {truncate_to:,}")
r = subprocess.run(['wc', '-l', CNF], capture_output=True, text=True)
cur = int(r.stdout.split()[0])
print(f"Current lines: {cur:,}")

# 截断
print(f"Truncating to line {truncate_to:,}...", flush=True)
with open(CNF, 'r') as f:
    hdr = [f.readline() for _ in range(truncate_to + 1)]
with open(CNF, 'w') as f:
    f.writelines(hdr)
print(f"  Truncated: {os.path.getsize(CNF)/1024/1024:.1f} MB", flush=True)

# 加载 Row 16 排列
with open(os.path.join(BASE, "A16_permutations.json")) as f:
    p16 = json.load(f)
p0 = X_END + 1 + cumsum[15]
s0 = s_off[15]
print(f"Row 16: n={n16}, P=[{p0},{p0+n16-1}], S=[{s0},{s0+n16-2}]", flush=True)

expected_eo = 1 + (2 + 4*(n16-2)) + 1 + 16*n16  # ALO + AMO(k=0) + AMO(k=1..n-2) + extra AMO + Assoc
print(f"  Expected EO: ALO(1) + AMO(2+{4*(n16-2)}) + extra(1) + Assoc({16*n16}) = {expected_eo:,}", flush=True)

# 重新生成 Row 16
fout = open(CNF, 'a')
buf = []; BSIZE = 500000
def W(s):
    buf.append(s)
    if len(buf) >= BSIZE:
        fout.write("\n".join(buf) + "\n")
        buf.clear()

# ALO
W(" ".join(str(p0+j) for j in range(n16)) + " 0")
print("  [1/4] ALO done", flush=True)

# AMO (修正: k 从 0 到 n16-2)
print("  [2/4] AMO (corrected)...", flush=True)
for k in range(n16 - 1):
    pk = p0 + k
    sk = s0 + k
    if k == 0:
        W(f"-{sk} {pk} 0")
        W(f"-{pk} {sk} 0")
    else:
        W(f"-{sk} {s0+k-1} {pk} 0")
        W(f"-{s0+k-1} {sk} 0")
        W(f"-{pk} {sk} 0")
        W(f"-{s0+k-1} -{pk} 0")
    if k % 200000 == 0 and k > 0:
        print(f"    k={k:,}/{n16-2:,}", flush=True)
print("  AMO done", flush=True)

# 额外 AMO: !S[n16-2] v !P[n16-1] 覆盖 P[n16-1]
print("  [3/4] Extra AMO (!S[1560] v !P[1561])", flush=True)
W(f"-{s0+n16-2} -{p0+n16-1} 0")
print("  Done", flush=True)

# Association
print("  [4/4] Association...", flush=True)
for j in range(n16):
    pj = p0 + j
    for c in range(16):
        W(f"-{pj} {X0+15*256+c*16+p16[j][c]} 0")
    if j % 10000 == 0 and j > 0:
        print(f"    j={j:,}/{n16:,} ({j/n16*100:.0f}%)", flush=True)

if buf:
    fout.write("\n".join(buf) + "\n")
fout.close()

# 统计
r = subprocess.run(['wc', '-l', CNF], capture_output=True, text=True)
final = int(r.stdout.split()[0])
sz = os.path.getsize(CNF)

expected = truncate_to + 1 + (2 + 4*(n16-2)) + 1 + 16*n16
print(f"\nExpected total: {expected:,}", flush=True)
print(f"Actual lines:   {final:,}", flush=True)
print(f"Size:           {sz/1024/1024/1024:.2f} GB", flush=True)

# 更新 p cnf
with open(CNF, 'r') as f: lines = f.readlines()
for i in range(len(lines)):
    if lines[i].startswith('p cnf'):
        lines[i] = f'p cnf {n_vars} {final}\n'
        print(f"\nHeader: p cnf {n_vars} {final}", flush=True)
        break
with open(CNF, 'w') as f: f.writelines(lines)

final_sz = os.path.getsize(CNF)
print(f"\n{'='*60}", flush=True)
print(f"✅ Level 2 CNF 修复完成!", flush=True)
print(f"   文件: {CNF}", flush=True)
print(f"   大小: {final_sz/1024/1024/1024:.2f} GB", flush=True)
print(f"   变量: {n_vars:,}", flush=True)
print(f"   子句: {final:,}", flush=True)
