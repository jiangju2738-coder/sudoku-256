#!/usr/bin/env python3
"""
修复 Level 2 CNF — 精确截断至 Row 15 末尾 + 重新生成 Row 16
"""
import json, os, subprocess

BASE = r"D:/2026/WPF_Sudoku/Sudoku_256"
OUT = os.path.join(BASE, "fuhh_sudoku_level2.cnf")
X0, X_END = 1, 4096

counts = [8731,902,407669,1980,633271,359,2356,4782,164,28984,2972,620,484,10668,5990,1562]
cumsum = [0]
for c in counts: cumsum.append(cumsum[-1]+c)
total_p = cumsum[-1]

# v2 S 偏移
s_base0 = X_END + total_p - 15
s_off = [0]*16
s_off[0] = s_base0
for i in range(1,16): s_off[i] = s_off[i-1] + counts[i-1] - 1
n_vars = s_off[15] + counts[15] - 1

# 当前状态
r = subprocess.run(['wc','-l',OUT], capture_output=True, text=True)
cur = int(r.stdout.split()[0])
print(f"Current: {cur:,} lines, {os.path.getsize(OUT)/1024/1024:.1f} MB")

# 计算截断点: 固定 + Rows 1-15 ExactlyOne + AMO + Association
# ExactlyOne(n) = 4n-1 (ALO + S↔P + AMO)
fixed = 16*16*120*3 + 256*121 + 92
rows_1_15 = sum((4*c-1)+16*c for c in counts[:15])
truncate_to = fixed + rows_1_15
print(f"Truncate to line: {truncate_to:,}")

# 截断
print("Truncating...")
with open(OUT,'r') as f:
    hdr = [f.readline() for _ in range(truncate_to+1)]
with open(OUT,'w') as f:
    f.writelines(hdr)
print(f"  Size: {os.path.getsize(OUT)/1024/1024:.1f} MB")

# Row 16
with open(os.path.join(BASE,"A16_permutations.json")) as f:
    p16 = json.load(f)
n16 = len(p16)
p0 = X_END + 1 + cumsum[15]
s0 = s_off[15]
print(f"Row 16: n={n16}, ExactlyOne={4*n16-1:,}, Assoc={16*n16:,}")

fout = open(OUT,'a')
buf = []; BSIZE = 500000
def W(s):
    buf.append(s)
    if len(buf)>=BSIZE:
        fout.write("\n".join(buf)+"\n")
        buf.clear()

# ALO
W(" ".join(str(p0+j) for j in range(n16))+" 0")

# Sequential Counter AMO
for k in range(n16):
    pk,sk = p0+k, s0+k
    if k==0:
        W(f"-{sk} {pk} 0"); W(f"-{pk} {sk} 0")
    else:
        W(f"-{sk} {s0+k-1} {pk} 0")
        W(f"-{s0+k-1} {sk} 0")
        W(f"-{pk} {sk} 0")
        W(f"-{s0+k-1} -{pk} 0")
    if k%200000==0 and k>0: print(f"  AMO k={k:,}", flush=True)
print("  AMO done", flush=True)

# Association
for j in range(n16):
    pj = p0+j
    for c in range(16):
        W(f"-{pj} {X0+15*256+c*16+p16[j][c]} 0")
    if j%10000==0 and j>0: print(f"  Assoc j={j:,}/{n16:,}", flush=True)

if buf: fout.write("\n".join(buf)+"\n")
fout.close()

# 统计
r = subprocess.run(['wc','-l',OUT], capture_output=True, text=True)
final = int(r.stdout.split()[0])
sz = os.path.getsize(OUT)
exp = fixed + rows_1_15 + (4*n16-1) + 16*n16
print(f"\nExpected: {exp:,}")
print(f"Actual:   {final:,}")
print(f"Size:     {sz/1024/1024/1024:.2f} GB")

# 更新 p cnf
with open(OUT,'r') as f: lines = f.readlines()
for i in range(len(lines)):
    if lines[i].startswith('p cnf'):
        lines[i] = f'p cnf {n_vars} {final}\n'
        print(f"\np cnf {n_vars} {final}")
        break
with open(OUT,'w') as f: f.writelines(lines)
print(f"✅ DONE: {os.path.getsize(OUT)/1024/1024/1024:.2f} GB")
