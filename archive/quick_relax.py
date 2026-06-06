#!/usr/bin/env python3
"""快速放松冲突分析"""

import json
from collections import defaultdict

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"
N = 16

# 加载数据
with open(f"{BASE_DIR}/sudoku_config.json") as f:
    config = json.load(f)

perms = {}
for r in range(1, 17):
    with open(f"{BASE_DIR}/A{r}_permutations.json") as f:
        perms[r] = json.load(f)

print("="*70)
print("快速放松冲突分析")
print("="*70)

# 步骤 1: 基于已知数字提取
print("\n【提取符合已知数字的排列】")
refined = {}
for row_num in range(1, 17):
    r = row_num - 1
    known = [(k["col"]-1, k["value"]) for k in config["known_digits"] if k["row"] == row_num]
    
    if not known:
        refined[row_num] = perms.get(row_num, [])
        continue
    
    valid = [p for p in perms.get(row_num, []) if all(p[c] == v for c, v in known)]
    refined[row_num] = valid
    
    before = len(perms.get(row_num, []))
    after = len(valid)
    if before != after:
        print(f"  Row {r+1:2d}: {before:>6,} → {after:>6,}")

# 步骤 2: 计算单源值
print("\n【计算单源值】")
val_col_sources = defaultdict(lambda: defaultdict(set))
for row_num in range(1, 17):
    for perm in refined.get(row_num, []):
        for c in range(N):
            val_col_sources[perm[c]][c].add(row_num - 1)

single_source = {}
for v in range(1, 17):
    for c in range(N):
        rows = val_col_sources[v][c]
        if len(rows) == 1:
            single_source[(c, v)] = list(rows)[0]

print(f"  单源值总数：{len(single_source)}")

# 步骤 3: 分析负载
print("\n【各行单源值负载】")
row_load = defaultdict(list)
for (c, v), r in single_source.items():
    row_load[r].append((c, v))

for r in range(16):
    cnt = len(row_load[r])
    pct = cnt / len(refined.get(r+1, [])) * 100
    print(f"  Row {r+1:2d}: {cnt:2d} 单源值 ({pct:.1f}%)")

# 找出过度锁定
over_locked = [(r, len(ss)) for r, ss in row_load.items() if len(ss) > 5]
print(f"\n过度锁定（>5 个单源值）：{over_locked}")

# 步骤 4: 放松策略
print("\n【放松策略】")
print("  方法：对 Row 9（7 个单源值/164 排列），移除 2 个")
print("  移除：Col 12 值 2, Col 14 值 6")

relaxed_single = {k: v for k, v in single_source.items()}
# 移除 Row 9（索引 8）的部分单源值
to_remove = [(11, 2), (13, 6)]  # Col 12 值 2, Col 14 值 6
for c, v in to_remove:
    if (c, v) in relaxed_single and relaxed_single[(c, v)] == 8:  # Row 9 (index 8)
        del relaxed_single[(c, v)]
        print(f"  移除：Col {c+1}, 值 {v}")

# 检查是否移除成功
removed_count = len([1 for k in to_remove if k not in relaxed_single])
print(f"  实际移除：{removed_count} 个")

print(f"\n放松后单源值：{len(relaxed_single)} 个（原 {len(single_source)}）")

# 保存结果
result = {
    "original_single_source": len(single_source),
    "relaxed_single_source": len(relaxed_single),
    "removed": [(c+1, v) for c, v in to_remove],
    "row_load": {f"Row {r+1}": len(row_load[r]) for r in range(16)}
}

with open(f"{BASE_DIR}/relaxed_result.json", 'w') as f:
    json.dump(result, f, indent=2)

print(f"\n结果已保存：relaxed_result.json")
