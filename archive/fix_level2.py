#!/usr/bin/env python3
"""
修复 Level 2 CNF - 截断文件并从 Row 16 重新生成
"""
import json, os, time, subprocess

BASE = r"D:/2026/WPF_Sudoku/Sudoku_256"
OUT = os.path.join(BASE, "fuhh_sudoku_level2.cnf")
X0 = 1
X_END = 4096

# 排列计数
counts = [8731, 902, 407669, 1980, 633271, 359, 2356, 4782, 164, 28984, 2972, 620, 484, 10668, 5990, 1562]
cumsum = [0]
for c in counts:
    cumsum.append(cumsum[-1] + c)
total_perms = cumsum[-1]

# 计算 S 变体起始编号
# S[i][k] 紧接在所有 P 变量之后: S_START = P_END + 1 = X_END + 1 + total_perms
S_START = X_END + 1 + total_perms

# 检查: 之前 gen_level2_v2.py 使用的公式不同
# v2 使用了: s_base0 = p_off[0] + total_p - 16
# 让我重新计算 v2 实际使用的值
# p_off[i] = X_END + 1 + cumsum[i]
# s_base0_v2 = p_off[0] + total_p - 16 = X_END + 1 + cumsum[0] + total_p - 16
#            = X_END + 1 + 0 + total_p - 16 = X_END + total_p - 15
s_base0_v2 = X_END + total_perms - 15

print(f"total_perms = {total_perms:,}")
print(f"S_START (simple) = {S_START:,}")
print(f"S_START (v2 formula) = {s_base0_v2:,}")
print(f"Difference: {S_START - s_base0_v2}")

# v2 的实际公式: s_off[0] = s_base0 = X_END + total_p - 15
# s_off[i] = s_off[i-1] + counts[i-1] - 1
# s_off[15] + counts[15] - 1 = (X_END + total_p - 15) + (counts[15] - 1) + (total_p - counts[15]) - 15 ???
# 实际上: s_off[i] = s_base0 + cumsum[i] - i
# s_off[15] = s_base0 + cumsum[15] - 15 = X_END + total_p - 15 + (total_p - counts[15]) - 15

# 让我直接模拟 v2 的计算
s_off_v2 = [0]*16
s_off_v2[0] = s_base0_v2
for i in range(1, 16):
    s_off_v2[i] = s_off_v2[i-1] + counts[i-1] - 1
n_vars_v2 = s_off_v2[15] + counts[15] - 1

print(f"n_vars (v2) = {n_vars_v2:,}")

# 读取当前文件头部
with open(OUT, 'r') as f:
    header_lines = []
    for i in range(20):
        header_lines.append(f.readline().rstrip('\n'))

for line in header_lines:
    print(f"  {line}")

# 检查 p cnf 行
for line in header_lines:
    if line.startswith('p cnf'):
        p_vars, p_clauses = line.split()
        print(f"Parsed: vars={p_vars}, clauses={p_clauses}")
        break

# 计算当前文件的行数
result = subprocess.run(['wc', '-l', OUT], capture_output=True, text=True)
current_lines = int(result.stdout.split()[0])
print(f"Current lines: {current_lines:,}")

# 计算在哪个位置截断
# 固定部分 + Rows 1-15 的 ExactlyOne + AMO + 关联约束
fixed_clauses = 16*16*120*3 + 256*121 + 92
print(f"Fixed clauses: {fixed_clauses:,}")

# Rows 1-15
rows1_15_clauses = 0
for i in range(15):
    c = counts[i]
    rows1_15_clauses += (4*c-4) + 16*c
print(f"Rows 1-15 perm clauses: {rows1_15_clauses:,}")

clauses_before_row16 = fixed_clauses + rows1_15_clauses
print(f"Should truncate to line: {clauses_before_row16:,}")

# 实际截断点
truncate_to = clauses_before_row16

# 读取并截断
print(f"\nTruncating file to {truncate_to} lines...")
with open(OUT, 'r') as rf:
    lines = [rf.readline() for _ in range(truncate_to + 1)]  # +1 for p cnf line

# 更新 p cnf 行中的变量数（暂时保持原样）
with open(OUT, 'w') as wf:
    wf.writelines(lines)
print(f"Truncated size: {os.path.getsize(OUT)/1024/1024:.1f} MB")

# 加载排列数据
with open(os.path.join(BASE, "sudoku_config.json")) as f:
    cfg = json.load(f)

perms = []
for i in range(16):
    with open(os.path.join(BASE, f"A{i+1}_permutations.json")) as f:
        perms.append(json.load(f))

# Row 16
row16_idx = 15
n = counts[row16_idx]
p0 = X_END + 1 + cumsum[row16_idx]
s0 = s_off_v2[row16_idx]

print(f"\nRow 16: n={n}, P range={p0}..{p0+n-1}, S range={s0}..{s0+n-2}")

# 打开文件追加
f = open(OUT, 'a')

B = []
BSIZE = 200000

def W(s):
    B.append(s)
    if len(B) >= BSIZE:
        f.write("\n".join(B) + "\n")
        B.clear()

print("Generating Row 16 permutation constraints...")

# ALO
W(" ".join(str(p0+j) for j in range(n)) + " 0")
print(f"  ALO done", flush=True)

# Sequential counter AMO
if n >= 2:
    for k in range(n):
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

        if k % 100000 == 0 and k > 0:
            print(f"  AMO k={k}/{n}", flush=True)

print(f"  AMO done", flush=True)

# Association
print(f"  Association (16×{n}={16*n:,} clauses)...", flush=True)
for j in range(n):
    perm = perms[row16_idx][j]
    pj = p0 + j
    for c in range(16):
        W(f"-{pj} {X0+row16_idx*256+c*16+perm[c]} 0")
    if j % 50000 == 0 and j > 0:
        print(f"  j={j}/{n} ({j/n*100:.0f}%)", flush=True)

# 收尾
if B:
    f.write("\n".join(B) + "\n")
f.close()

# 统计
result = subprocess.run(['wc', '-l', OUT], capture_output=True, text=True)
final_lines = int(result.stdout.split()[0])
final_size = os.path.getsize(OUT)

# 计算正确的总子句数
n_clauses = fixed_clauses + rows1_15_clauses + (4*n-4) + 16*n
print(f"\nExpected clauses: {n_clauses:,}")
print(f"Actual lines: {final_lines:,}")
print(f"File size: {final_size//1024//1024} MB ({final_size/1024/1024/1024:.2f} GB)")

# 更新 p cnf 行
with open(OUT, 'r') as rf:
    all_lines = rf.readlines()

for i in range(len(all_lines)):
    if all_lines[i].startswith('p cnf'):
        all_lines[i] = f'p cnf {n_vars_v2} {final_lines}\n'
        print(f"Updated p cnf to: {all_lines[i].strip()}")
        break

with open(OUT, 'w') as wf:
    wf.writelines(all_lines)

print(f"\nDone! File: {OUT}")
print(f"  Size: {os.path.getsize(OUT)/1024/1024/1024:.2f} GB")
print(f"  Vars: {n_vars_v2:,}")
print(f"  Clauses: {final_lines:,}")
