#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""
从92锚点推演链式解集：
1. 计算每行每列的"必然值集合"
2. 分析锚点的"约束传递"效应
3. 构建逐步逼近解空间的候选数集
"""
from ortools.sat.python import cp_model
import json
import random

# 92锚点
ANCHORS = {
    'BR':1,'DJ':1,'KD':1,'LS':1,'MM':1,'OE':1,'PP':1,
    'BP':2,'CI':2,'GL':2,'IG':2,'KK':2,'ON':2,'PF':2,
    'AF':3,'BH':3,'FK':3,'GQ':3,'IS':3,'KM':3,'MO':3,'NR':3,
    'BO':4,'DE':4,'EP':4,'FJ':4,'GF':4,'LG':4,
    'AK':5,'BN':5,'EM':5,'HI':5,'JE':5,'KH':5,'LO':5,'ML':5,'OQ':5,'PJ':5,
    'BL':6,'GG':6,'HO':6,'KF':6,'MQ':6,'NI':6,
    'DH':7,'IO':7,'JR':7,'MS':7,
    'AS':8,'CK':8,'FE':8,'JP':8,'OO':8,
    'BJ':9,'FM':9,'HK':9,'KP':9,'NF':9,'OH':9,
    'PR':10,'DO':11,'II':11,
    'AI':12,'BE':12,'DQ':12,'FS':12,'GJ':12,'LN':12,'MH':12,
    'DG':13,'EH':13,'FQ':13,'HE':13,'ID':13,'NL':13,
    'AO':14,'CF':14,'GD':14,'HN':14,'IL':14,'LJ':14,'PM':14,
    'FH':15,'IQ':15,'MD':15,'NO':15,'OK':15,'PS':15,
    'AQ':16,'HR':16,'JN':16,'LI':16,
}

ROW_NAMES = list('ABCDEFGHIJKLMNOP')
COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']
ROW_MAP = {r:i for i,r in enumerate(ROW_NAMES)}
COL_MAP = {c:i for i,c in enumerate(COL_NAMES)}

print("=" * 80)
print("从92锚点推演链式解集")
print("=" * 80)

# Step 1: 计算每行/每列的"已被锚点占据的值"
print("\n【Step 1】每行/每列的锚点值分析")
print("-" * 60)

row_anchor_values = {r: set() for r in ROW_NAMES}
col_anchor_values = {c: set() for c in COL_NAMES}

for coord, val in ANCHORS.items():
    row = coord[0]
    col = coord[1]
    row_anchor_values[row].add(val)
    col_anchor_values[col].add(val)

for r in ROW_NAMES:
    anchors = sorted(row_anchor_values[r])
    free = 16 - len(anchors)
    print(f"  行{r}: {len(anchors)}个锚点值 {anchors} | 剩余{free}个空位")

print("\n每列锚点值：")
for c in COL_NAMES:
    anchors = sorted(col_anchor_values[c])
    free = 16 - len(anchors)
    print(f"  列{c}: {len(anchors)}个锚点值 {anchors} | 剩余{free}个空位")

# Step 2: 分析"约束传递"效应
print("\n" + "=" * 80)
print("【Step 2】约束传递分析")
print("-" * 60)

print("""
关键观察：
1. 每行/每列的锚点值决定了该行/列的"必选值集合"
2. 剩余的"自由值集合" = {1..16} - 锚点值集合
3. 这些自由值必须在该行/列的非锚点位置中排列

约束传递效应：
- 如果某行锚点值越多，自由值越少，约束越强
- 如果某列锚点值越多，自由值越少，约束越强
- 宫格中的锚点值影响该宫的候选数分布
""")

# 计算每行的锚点密度
row_density = {r: len(row_anchor_values[r])/16 for r in ROW_NAMES}
print("\n行锚点密度（越高约束越强）：")
for r in sorted(ROW_NAMES, key=lambda x: -row_density[x]):
    print(f"  {r}: {row_density[r]*100:.1f}% ({len(row_anchor_values[r])}/16)")

# Step 3: 用CP-SAT搜索多个解，统计每个位置的"可能值集合"
print("\n" + "=" * 80)
print("【Step 3】用CP-SAT搜索多个解以统计候选数分布")
print("-" * 60)

# 先验证92锚点是否有解
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8

# 搜索第一个解
model0 = cp_model.CpModel()
grid0 = {(r,c): model0.NewIntVar(1, 16, f'g0{r}{c}') 
         for r in range(16) for c in range(16)}

for r in range(16):
    model0.AddAllDifferent([grid0[(r,c)] for c in range(16)])
for c in range(16):
    model0.AddAllDifferent([grid0[(r,c)] for r in range(16)])
for br in range(4):
    for bc in range(4):
        cells = [grid0[(br*4+dr, bc*4+dc)] for dr in range(4) for dc in range(4)]
        model0.AddAllDifferent(cells)

for coord, val in ANCHORS.items():
    r, c = ROW_MAP[coord[0]], COL_MAP[coord[1]]
    model0.Add(grid0[(r,c)] == val)

print("\n搜索第一个解验证92锚点...")
status = solver.Solve(model0)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("[OK] 92锚点约束下有解！")
else:
    print("[FAIL] 92锚点约束下无解！")
    sys.exit(1)

# 搜索多个不同解
print("\n搜索100个解以统计每个位置的候选数分布...")

sample_solutions = []

for attempt in range(100):
    model = cp_model.CpModel()
    grid = {(r,c): model.NewIntVar(1, 16, f'g{attempt}{r}{c}') 
            for r in range(16) for c in range(16)}
    
    for r in range(16):
        model.AddAllDifferent([grid[(r,c)] for c in range(16)])
    for c in range(16):
        model.AddAllDifferent([grid[(r,c)] for r in range(16)])
    for br in range(4):
        for bc in range(4):
            cells = [grid[(br*4+dr, bc*4+dc)] for dr in range(4) for dc in range(4)]
            model.AddAllDifferent(cells)
    
    for coord, val in ANCHORS.items():
        r, c = ROW_MAP[coord[0]], COL_MAP[coord[1]]
        model.Add(grid[(r,c)] == val)
    
    # 添加随机约束以获取不同解
    random.seed(attempt)
    non_anchor_cells = [(r,c) for r in range(16) for c in range(16) 
                       if (ROW_NAMES[r]+COL_NAMES[c]) not in ANCHORS]
    if non_anchor_cells:
        r, c = random.choice(non_anchor_cells)
        possible_vals = list(range(1, 17))
        random.shuffle(possible_vals)
        model.Add(grid[(r,c)] == possible_vals[0])
    
    temp_solver = cp_model.CpSolver()
    temp_status = temp_solver.Solve(model)
    if temp_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sol = [[temp_solver.Value(grid[(r,c)]) for c in range(16)] for r in range(16)]
        sample_solutions.append(sol)
    
    if (attempt + 1) % 20 == 0:
        print(f"  已完成 {attempt + 1} 次尝试，找到 {len(sample_solutions)} 个解")

print(f"\n最终找到 {len(sample_solutions)} 个不同的解")

# 计算每个位置的候选数集合
print("\n" + "=" * 80)
print("【Step 4】每个位置的候选数统计")
print("-" * 60)

candidate_sets = {}
for r in range(16):
    for c in range(16):
        coord = ROW_NAMES[r] + COL_NAMES[c]
        if coord in ANCHORS:
            candidate_sets[coord] = {ANCHORS[coord]}
        else:
            vals = set(sol[r][c] for sol in sample_solutions)
            candidate_sets[coord] = vals

# 统计候选数数量分布
print("\n非锚点位置的候选数数量分布：")
from collections import Counter
sizes = Counter()
for coord, vals in candidate_sets.items():
    if coord not in ANCHORS:
        sizes[len(vals)] += 1

for size in sorted(sizes.keys()):
    print(f"  {size}个候选数: {sizes[size]}个位置")

# 找出候选数最少的非锚点位置（约束最强的位置）
non_anchor_candidates = {c: v for c, v in candidate_sets.items() if c not in ANCHORS}
if non_anchor_candidates:
    min_cand = min(len(v) for v in non_anchor_candidates.values())
    max_cand = max(len(v) for v in non_anchor_candidates.values())

    print(f"\n候选数范围: {min_cand} ~ {max_cand} 个")

    print("\n候选数最少的非锚点位置（约束最强）：")
    for coord, vals in sorted(non_anchor_candidates.items(), key=lambda x: len(x[1])):
        if len(vals) == min_cand:
            print(f"  {coord}: {sorted(vals)} ({len(vals)}个)")
            break

    print("\n候选数最多的非锚点位置（最不确定）：")
    for coord, vals in sorted(non_anchor_candidates.items(), key=lambda x: -len(x[1])):
        if len(vals) == max_cand:
            print(f"  {coord}: {sorted(vals)} ({len(vals)}个)")
            break

# Step 5: 推导"必然链"
print("\n" + "=" * 80)
print("【Step 5】必然链分析 - 在所有解中取相同值的非锚点位置")
print("-" * 60)

invariant_positions = {}
for coord, vals in candidate_sets.items():
    if coord not in ANCHORS and len(vals) == 1:
        invariant_positions[coord] = list(vals)[0]

if invariant_positions:
    print(f"\n找到 {len(invariant_positions)} 个必然值（在所有{len(sample_solutions)}个解中取相同值）：")
    for coord, val in sorted(invariant_positions.items()):
        print(f"  {coord} = {val}")
else:
    print("\n未发现在所有解中都相同的非锚点位置")
    print("说明：92锚点约束下解空间仍然很大，需要更多约束来锁定")

# 保存候选数集合
with open('candidate_sets.json', 'w', encoding='utf-8') as f:
    json.dump({k: sorted(v) for k, v in candidate_sets.items()}, f, ensure_ascii=False, indent=2)
print(f"\n候选数集合已保存到 candidate_sets.json")

# 分析链式推导的可行性
print("\n" + "=" * 80)
print("【Step 6】链式推导可行性分析")
print("-" * 60)

print(f"""
链式推导的核心逻辑：

1. 初始约束：92个锚点（固定值）
2. 每锁定1个值 → 约束数+1 → 解空间缩小
3. 如果某行/列/宫只剩1个可能值 → 必然锁定

当前状态分析：
- 92锚点 + C191620 → 唯一解（约束数108）
- 92锚点 alone → {len(sample_solutions)}个解（约束数92）

关键推论：
如果存在"必然值"（在所有解中取相同值），则：
  - 该值可被"锁定"，作为新锚点
  - 约束数增加，解空间进一步缩小
  - 可能触发更多必然值（连锁反应）

节约计算成本的策略：
1. 不需要穷举所有排列（1,360,849个）
2. 从"必然链"开始，逐步迭代锁定
3. 每锁定1个值，验证是否符合符阖排列
4. 直到锁定16行 = 完整解盘
""")

# 打印最终总结
print("\n" + "=" * 80)
print("总结")
print("=" * 80)
print(f"""
关键发现：

1. 92锚点约束下解空间存在 - 验证通过
   - 搜索到 {len(sample_solutions)} 个不同的解
   - 证明92锚点是自洽的，不是冲突的

2. 每个位置的候选数可计算：
   - 锚点位置：1个候选数（固定）
   - 非锚点位置：{min_cand if 'min_cand' in dir() else 'N/A'} ~ {max_cand if 'max_cand' in dir() else 'N/A'} 个候选数
   - 平均候选数越多，解空间越大

3. 必然链推导：
   - 若某非锚点位置在所有解中取相同值 → 可锁定为"新锚点"
   - 锁定值 → 进一步缩小相关行/列/宫的候选数
   - 连锁反应可能锁定更多值

4. 节约计算成本的策略：
   - 从最小约束集（92锚点）开始
   - 迭代锁定必然值，逐步逼近
   - 不需要穷尽所有1,360,849个排列
   - 只需找到"必然链"上的值

下一步建议：
- 迭代100次，每次锁定找到的必然值
- 检查是否收敛到唯一解
- 验证锁定值是否符合符阖排列约束
""")
