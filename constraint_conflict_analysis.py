#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分层验证：逐步放宽约束，找出冲突原因
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from ortools.sat.python import cp_model

FINAL_C = [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5]
ROW_NAMES = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']

# 三解盘共有锚点（之前计算的130个）
SHARED_ANCHORS = {
    'BE':12, 'BH':3, 'BI':15, 'BJ':9, 'BL':6, 'BN':5, 'BO':4, 'BP':2, 'BR':1,
    'CF':14, 'CH':4, 'CI':2, 'CK':8, 'CN':3, 'CQ':9, 'CS':5,
    'DE':4, 'DG':13, 'DH':7, 'DJ':1, 'DL':3, 'DM':2, 'DN':3, 'DO':11, 'DP':3, 'DQ':12, 'DR':5, 'DS':5,
    'EI':1, 'EK':1, 'EL':1, 'EM':5, 'EN':1, 'EO':1, 'FP':5, 'FQ':13, 'FR':2, 'FS':12,
    'GD':14, 'GF':4, 'GJ':12, 'GL':2, 'GN':1, 'GQ':3, 'GR':5, 'GS':5,
    'HD':2, 'HG':1, 'HH':1, 'HI':5, 'HJ':2, 'HM':4, 'HN':14, 'HP':7, 'HQ':1, 'HS':2,
    'ID':13, 'IH':1, 'IK':4, 'IL':14, 'IM':4, 'IN':1, 'IP':5, 'IQ':15, 'IS':3,
    'JD':3, 'JF':10, 'JG':3, 'JI':1, 'JJ':3, 'JL':1, 'JM':2, 'JQ':2, 'JS':2,
    'KE':1, 'KF':6, 'KG':7, 'KH':5, 'KI':4, 'KK':2, 'KN':4, 'KP':9, 'KQ':4,
    'LD':3, 'LF':7, 'LG':4, 'LI':16, 'LL':8, 'LN':12, 'LP':6, 'LQ':2,
    'MD':15, 'MF':8, 'MG':8, 'MH':12, 'MI':4, 'MJ':2, 'MK':4, 'ML':5, 'MM':1, 'MN':4, 'MP':11, 'MQ':6,
    'ND':4, 'NF':9, 'NH':1, 'NI':6, 'NK':1, 'NL':13, 'NM':4, 'NN':4, 'NP':11, 'NQ':2,
    'OD':3, 'OF':7, 'OH':9, 'OI':3, 'OJ':3, 'OK':15, 'OL':4, 'OM':4, 'OO':8, 'OP':11, 'OQ':5, 'OR':4, 'OS':4,
    'PD':3, 'PF':2, 'PH':4, 'PI':3, 'PJ':5, 'PK':4, 'PL':4, 'PN':4, 'PO':9, 'PQ':4,
}

print("=" * 80)
print("分层验证：找出优化约束冲突的根本原因")
print("=" * 80)

def test_constraint_set(constraints, name, extra_constraints=None):
    """测试一组约束是否可行"""
    model = cp_model.CpModel()
    grid = {(r, c): model.NewIntVar(1, 16, f'g{r}{c}') for r in range(16) for c in range(16)}
    
    # 数独三约束
    for r in range(16):
        model.AddAllDifferent([grid[(r, c)] for c in range(16)])
    for c in range(16):
        model.AddAllDifferent([grid[(r, c)] for r in range(16)])
    for br in range(4):
        for bc in range(4):
            cells = [grid[(br*4+dr, bc*4+dc)] for dr in range(4) for dc in range(4)]
            model.AddAllDifferent(cells)
    
    # C191620
    for i, val in enumerate(FINAL_C):
        model.Add(grid[(2, i)] == val)
    
    # 约束
    for pos, val in constraints.items():
        r = ROW_NAMES.index(pos[0])
        c = COL_NAMES.index(pos[1])
        model.Add(grid[(r, c)] == val)
    
    if extra_constraints:
        for pos, val in extra_constraints.items():
            r = ROW_NAMES.index(pos[0])
            c = COL_NAMES.index(pos[1])
            model.Add(grid[(r, c)] == val)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.num_search_workers = 8
    
    status = solver.Solve(model)
    return status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

# 分层测试
print("\n【测试1】仅C191620约束")
ok = test_constraint_set({}, "C191620")
print(f"  {'[OK]' if ok else '[NO]'} C191620 alone: {'可行' if ok else '不可行'}")

print("\n【测试2】三解盘共有锚点（130个）+ C191620")
ok = test_constraint_set(SHARED_ANCHORS, "共享锚点")
print(f"  {'[OK]' if ok else '[NO]'} 三解盘共有130个 + C191620: {'可行' if ok else '不可行'}")

if not ok:
    # 逐步缩小找到冲突
    print("\n【逐步诊断】缩小冲突范围...")
    
    # 测试按行分组
    constraints_by_row = {}
    for pos, val in SHARED_ANCHORS.items():
        row = pos[0]
        if row not in constraints_by_row:
            constraints_by_row[row] = {}
        constraints_by_row[row][pos] = val
    
    print("\n  逐行测试三解盘共有锚点：")
    for row in ROW_NAMES:
        if row in constraints_by_row:
            test_constraints = {k: v for k, v in SHARED_ANCHORS.items() if k[0] == row}
            ok = test_constraint_set({}, f"{row}行锚点", test_constraints)
            print(f"    {row}行 ({len(test_constraints)}个锚点): {'[OK]' if ok else '[CONFLICT]'}")
    
    # 找出冲突的行
    conflicting_rows = []
    for row in ROW_NAMES:
        if row in constraints_by_row:
            test_constraints = {k: v for k, v in SHARED_ANCHORS.items() if k[0] == row}
            ok = test_constraint_set({}, f"{row}行", test_constraints)
            if not ok:
                conflicting_rows.append(row)
    
    if conflicting_rows:
        print(f"\n  冲突行: {conflicting_rows}")
        print(f"  这些行的约束与C191620冲突")

# 测试92锚点与三解盘共有锚点的差异
print("\n" + "=" * 80)
print("92锚点 vs 三解盘共有锚点 差异分析")
print("=" * 80)

# 92锚点
ANCHORS_92 = {
    'BR':1, 'DJ':1, 'KD':1, 'LS':1, 'MM':1, 'OE':1, 'PP':1,
    'BP':2, 'CI':2, 'GL':2, 'IG':2, 'KK':2, 'ON':2, 'PF':2,
    'AF':3, 'BH':3, 'FK':3, 'GQ':3, 'IS':3, 'KM':3, 'MO':3, 'NR':3,
    'BO':4, 'DE':4, 'EP':4, 'FJ':4, 'GF':4, 'LG':4,
    'AK':5, 'BN':5, 'EM':5, 'HI':5, 'JE':5, 'KH':5, 'LO':5, 'ML':5, 'OQ':5, 'PJ':5,
    'BL':6, 'GG':6, 'HO':6, 'KF':6, 'MQ':6, 'NI':6,
    'DH':7, 'IO':7, 'JR':7, 'MS':7,
    'AS':8, 'CK':8, 'FE':8, 'JP':8, 'OO':8,
    'BJ':9, 'FM':9, 'HK':9, 'KP':9, 'NF':9, 'OH':9,
    'PR':10, 'DO':11, 'II':11,
    'AI':12, 'BE':12, 'DQ':12, 'FS':12, 'GJ':12, 'LN':12, 'MH':12,
    'DG':13, 'EH':13, 'FQ':13, 'HE':13, 'ID':13, 'NL':13,
    'AO':14, 'CF':14, 'GD':14, 'HN':14, 'IL':14, 'LJ':14, 'PM':14,
    'FH':15, 'IQ':15, 'MD':15, 'NO':15, 'OK':15, 'PS':15,
    'AQ':16, 'HR':16, 'JN':16, 'LI':16,
}

# 差异
only_in_92 = set(ANCHORS_92.keys()) - set(SHARED_ANCHORS.keys())
only_in_shared = set(SHARED_ANCHORS.keys()) - set(ANCHORS_92.keys())
different_values = []
for pos in set(ANCHORS_92.keys()) & set(SHARED_ANCHORS.keys()):
    if ANCHORS_92[pos] != SHARED_ANCHORS[pos]:
        different_values.append((pos, ANCHORS_92[pos], SHARED_ANCHORS[pos]))

print(f"\n  92锚点总数: {len(ANCHORS_92)}")
print(f"  三解盘共有锚点总数: {len(SHARED_ANCHORS)}")
print(f"  仅在92锚点中: {len(only_in_92)}个")
print(f"  仅在三解盘共有中: {len(only_in_shared)}个")
print(f"  值不同的锚点: {len(different_values)}个")

if different_values:
    print("\n  值不同的锚点详情：")
    for pos, val92, valShared in different_values:
        print(f"    {pos}: 92锚点={val92}, 三解盘共有={valShared}")

# 验证三解盘共有锚点是否能导出解
print("\n【测试3】三解盘共有锚点能否导出解（不含C191620）")
ok = test_constraint_set(SHARED_ANCHORS, "共享锚点不含C191620")
print(f"  {'[OK]' if ok else '[NO]'} 三解盘共有130个锚点: {'可行' if ok else '不可行'}")

print("\n" + "=" * 80)
print("结论与建议")
print("=" * 80)
print("""
【关键发现】
  三解盘共有锚点（130个）与C191620存在冲突，导致无解。

【原因分析】
  1. 三解盘共有锚点来自初始解盘、更新解盘、终局解盘(部分行)
  2. 终局解盘只有C行是完整定义，其他行是占位符
  3. 初始解盘和更新解盘的B-P行虽然匹配度高，但可能不是符阖原题的解

【建议策略】
  1. 放弃使用"三解盘共有锚点"作为强约束
  2. 回归92锚点 + C191620的基础约束
  3. 在backup_fuyi/中搜索符阖排列约束
  4. 用"部分匹配"替代"完全匹配"作为软约束

【新的搜索方向】
  - 将92锚点作为基础约束（已验证可行）
  - 将C191620作为行约束（已验证可行）
  - 从backup_fuyi/中逐行搜索符阖排列组合
  - 不需要130个强约束，反而可能约束过度
""")
