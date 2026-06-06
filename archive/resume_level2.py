#!/usr/bin/env python3
"""
Level 2 CNF 增量续接脚本
从已有的 366MB 文件继续，完成 Row 16 剩余部分 + 收尾
"""
import json, os, time

BASE = r"D:/2026/WPF_Sudoku/Sudoku_256"
OUT = os.path.join(BASE, "fuhh_sudoku_level2.cnf")
X0 = 1
X_END = 4096

counts = [8731, 902, 407669, 1980, 633271, 359, 2356, 4782, 164, 28984, 2972, 620, 484, 10668, 5990, 1562]
cumsum = [0]
for c in counts:
    cumsum.append(cumsum[-1] + c)

t0 = time.time()

# 计算正确的 total_vars
s_base0 = X_END + 1 + cumsum[0] + cumsum[-1] - 16  # S_START
s_off = [0]*16
s_off[0] = s_base0
for i in range(1,16):
    s_off[i] = s_off[i-1] + counts[i-1] - 1
n_vars = s_off[15] + counts[15] - 1

# 重新计算 total clauses (精确)
n_cl = 0
n_cl += 16*16*120*3  # 行+列+宫
n_cl += 256*121       # 单元格
n_known = 92
n_cl += n_known
for c in counts:
    n_cl += (4*c-4) + 16*c

print(f"Total vars: {n_vars:,}")
print(f"Total clauses: {n_cl:,}")

# 已知数字
with open(os.path.join(BASE, "sudoku_config.json")) as f:
    cfg = json.load(f)
known = {(e["row"]-1, e["col"]-1): e["value"]-1 for e in cfg["known_digits"]}

# 加载所有排列
perms = []
for i in range(16):
    with open(os.path.join(BASE, f"A{i+1}_permutations.json")) as f:
        perms.append(json.load(f))

# p 和 s offsets (correct formula)
p_off = [X_END + 1 + cumsum[i] for i in range(16)]
s_off = [p_off[0] + cumsum[-1] - 16]  # S_START
for i in range(1,16):
    s_off.append(s_off[-1] + counts[i-1] - 1)

print(f"S_START = {s_off[0]}, S_END = {s_off[15]+counts[15]-1}")
print(f"File exists: {os.path.exists(OUT)}, size: {os.path.getsize(OUT)/1024/1024:.1f} MB")

# 打开文件追加
f = open(OUT, 'a')
f.flush()

B = []
BSIZE = 500000

def W(s):
    B.append(s)
    if len(B) >= BSIZE:
        f.write("\n".join(B)+"\n")
        B.clear()
        f.flush()

# Row 16 was at permutation index 1561 (last one, j=1561)
# Need to finish j=1561 column 13,14,15 and close file
# Actually let's just regenerate rows 16 completely to be safe
# First, we need to figure out where exactly to resume

# The last written line was: -1115590 4053 0
# This is P[1115590] for Row 16, j=1561, col=13
# We need to finish col 14, 15 for j=1561, then all remaining association clauses

# Actually, since the sequential counter encoding for row 16 should already be done
# (it was before the association loop), let's just resume the association loop

row16 = 15  # 0-indexed
p0 = p_off[row16]  # 1114029
print(f"Row 16 P range: {p0}..{p0+counts[row16]-1}")

# Resume from j=1561 (the last permutation), col=14,15
# But also check if earlier rows 10-15 are fully done
# Let's just regenerate rows 10-16 to be safe and overwrite the tail
# This is cleaner than trying to resume mid-stream

# First, truncate the file to before row 10's association clauses
# Count how many lines are in the file
import subprocess
result = subprocess.run(['wc', '-l', OUT], capture_output=True, text=True)
total_lines = int(result.stdout.split()[0])
print(f"Current lines in file: {total_lines:,}")

# Calculate expected lines before Row 10's association
# 行AllDiff + 列AllDiff + 宫AllDiff + 单元格 + 已知 = fixed part
fixed_clauses = 16*16*120*3 + 256*121 + n_known
print(f"Fixed clauses: {fixed_clauses:,}")

# Rows 1-9 ExactlyOne + AMO + association
rows1_9_clauses = 0
for i in range(9):
    c = counts[i]
    rows1_9_clauses += (4*c-4) + 16*c
print(f"Rows 1-9 perm clauses: {rows1_9_clauses:,}")

clauses_before_row10 = fixed_clauses + rows1_9_clauses
print(f"Expected lines before Row 10: {clauses_before_row10:,}")

# The file likely has most of rows 10-15 done. Let's check.
# Actually, since we don't know the exact state, let's just truncate and redo from row 10
truncate_line = clauses_before_row10
print(f"Truncating to line {truncate_line:,}...")

# Read first N lines and rewrite
with open(OUT, 'r') as rf:
    header_lines = []
    for i in range(truncate_line + 1):  # +1 for p cnf line
        header_lines.append(rf.readline())

# Remove the last (partial) line if it exists
if header_lines and not header_lines[-1].startswith('c'):
    # The last line might be partial
    pass

# Rewrite
with open(OUT, 'w') as wf:
    for line in header_lines:
        wf.write(line)
    wf.flush()

print(f"Truncated. New size: {os.path.getsize(OUT)/1024/1024:.1f} MB")

# Now regenerate rows 10-16 completely
B = []
def W(s):
    B.append(s)
    if len(B) >= BSIZE:
        wf.write("\n".join(B)+"\n")
        B.clear()
        wf.flush()

# But we can't use wf since we need to reopen
f = open(OUT, 'a')
f.flush()

# Regenerate rows 10-16 perm constraints
print("Regenerating rows 10-16...")
for i in range(9, 16):
    n = counts[i]
    p0 = p_off[i]
    s0 = s_off[i]
    print(f"  Row {i+1}: {n:,} perms", flush=True)

    # ALO
    W(" ".join(str(p0+j) for j in range(n)) + " 0")

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

    # Association
    for j in range(n):
        perm = perms[i][j]
        pj = p0 + j
        for c in range(16):
            W(f"-{pj} {X0+i*256+c*16+perm[c]} 0")
        if j % 50000 == 0 and j > 0:
            print(f"    j={j}/{n}", flush=True)

    if i < 15:
        print(f"  Row {i+1} done", flush=True)

# Close file
if B:
    f.write("\n".join(B)+"\n")
f.close()

# Add clause count header
fsize = os.path.getsize(OUT)
# Count actual lines
import subprocess
result = subprocess.run(['wc', '-l', OUT], capture_output=True, text=True)
actual_lines = int(result.stdout.split()[0])

# The header says p cnf {n_vars} {n_cl}, need to update it
# Read the file, update header, rewrite
with open(OUT, 'r') as rf:
    lines = rf.readlines()

# Update the p cnf line
for i in range(len(lines)):
    if lines[i].startswith('p cnf'):
        lines[i] = f'p cnf {n_vars} {actual_lines}\n'
        break

with open(OUT, 'w') as wf:
    wf.writelines(lines)

fsize = os.path.getsize(OUT)
el = time.time() - t0
print(f"\n{'='*50}")
print(f"Level 2 CNF 生成完成!")
print(f"  文件: {OUT}")
print(f"  大小: {fsize//1024//1024} MB")
print(f"  变量: {n_vars:,}")
print(f"  子句: {actual_lines:,}")
print(f"  耗时: {el:.0f}s")

if __name__ == "__main__":
    main()
