#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务：联闔初始解盘、更新解盘、终局解盘的联结锚点与候选数分析

核心目标：
1. 提取三个解盘的完整排列
2. 分析它们之间的相同/不同位置
3. 找出联结锚点（多个解盘共有的固定位置）
4. 通过数独基础区位相关性进行运算推演
5. 分析候选数解集的收缩规律
"""

import json
import sys
from collections import defaultdict, Counter
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# ==================== 定义三个解盘 ====================

print("=" * 80)
print("联闔初始解盘、更新解盘、终局解盘的深度分析")
print("=" * 80)

# 解盘定义
SOLVER_INITIAL = {
    'A': [7, 15, 3, 9, 11, 12, 6, 5, 10, 2, 1, 14, 13, 16, 4, 8],   # A5447
    'B': [16, 12, 10, 8, 3, 15, 9, 14, 6, 13, 5, 4, 2, 7, 1, 11],   # B824
    'C': [11, 6, 14, 1, 4, 2, 13, 8, 7, 12, 3, 16, 10, 9, 15, 5],   # 无编号
    'D': [2, 4, 5, 13, 7, 10, 1, 16, 15, 8, 9, 11, 3, 12, 14, 6],   # 无编号
    'E': [9, 2, 7, 10, 13, 1, 16, 6, 3, 5, 15, 12, 4, 11, 8, 14],   # E287832
    'F': [5, 8, 1, 11, 15, 14, 4, 3, 16, 9, 7, 10, 6, 13, 2, 12],   # F227
    'G': [14, 16, 4, 6, 8, 7, 12, 10, 2, 11, 13, 1, 15, 3, 5, 9],   # G2113
    'H': [3, 13, 15, 12, 2, 5, 11, 9, 8, 4, 14, 6, 7, 1, 16, 10],   # H2588
    'I': [13, 9, 16, 2, 1, 11, 8, 12, 14, 10, 4, 7, 5, 15, 6, 3],   # 无编号
    'J': [12, 5, 11, 15, 10, 9, 3, 13, 1, 6, 16, 2, 8, 14, 7, 4],   # J25793
    'K': [1, 14, 6, 7, 5, 4, 15, 2, 11, 3, 8, 13, 9, 10, 12, 16],   # K1150
    'L': [10, 3, 8, 4, 6, 16, 14, 7, 9, 15, 12, 5, 11, 2, 13, 1],   # L583
    'M': [15, 11, 13, 16, 12, 8, 2, 4, 5, 1, 10, 3, 14, 6, 9, 7],   # M169
    'N': [4, 10, 9, 5, 14, 6, 7, 1, 13, 16, 11, 15, 12, 8, 3, 2],   # N257
    'O': [6, 1, 12, 14, 9, 3, 10, 15, 4, 7, 2, 8, 16, 5, 11, 13],   # O3011
    'P': [8, 7, 2, 3, 16, 13, 5, 11, 12, 14, 6, 9, 1, 4, 10, 15],   # P1294
}

SOLVER_UPDATE = {
    'A': [11, 2, 3, 15, 4, 12, 13, 5, 1, 7, 9, 14, 10, 16, 6, 8],
    'B': [8, 12, 7, 10, 3, 15, 9, 11, 6, 16, 5, 4, 2, 14, 1, 13],
    'C': [5, 6, 14, 1, 10, 2, 16, 8, 3, 15, 13, 12, 7, 9, 4, 11],
    'D': [9, 4, 16, 13, 7, 14, 1, 6, 8, 2, 10, 11, 3, 12, 15, 5],
    'E': [7, 10, 15, 9, 13, 8, 6, 14, 12, 5, 3, 16, 4, 1, 11, 2],
    'F': [2, 8, 5, 16, 15, 1, 4, 3, 11, 9, 7, 10, 6, 13, 14, 12],
    'G': [14, 11, 4, 6, 16, 7, 12, 10, 2, 13, 15, 1, 5, 3, 8, 9],
    'H': [12, 13, 1, 3, 2, 5, 11, 9, 4, 8, 14, 6, 15, 7, 16, 10],
    'I': [13, 9, 8, 2, 6, 11, 10, 12, 14, 4, 1, 7, 16, 15, 5, 3],
    'J': [10, 5, 12, 14, 1, 9, 3, 13, 15, 11, 16, 2, 8, 4, 7, 6],
    'K': [1, 16, 6, 7, 5, 4, 15, 2, 10, 3, 8, 13, 9, 11, 12, 14],
    'L': [3, 15, 11, 4, 8, 16, 14, 7, 9, 6, 12, 5, 13, 10, 2, 1],
    'M': [15, 14, 13, 8, 12, 10, 2, 16, 5, 1, 4, 3, 11, 6, 9, 7],
    'N': [4, 7, 9, 5, 14, 6, 8, 1, 13, 10, 11, 15, 12, 2, 3, 16],
    'O': [6, 1, 10, 11, 9, 3, 7, 15, 16, 12, 2, 8, 14, 5, 13, 4],
    'P': [16, 3, 2, 12, 11, 13, 5, 4, 7, 14, 6, 9, 1, 8, 10, 15],
}

# 终局解盘（注意：只有C行是完整排列，其他行是占位符）
SOLVER_FINAL = {
    'A': [0, 0, 3, 0, 0, 12, 0, 5, 0, 0, 0, 14, 0, 16, 0, 8],  # 占位符
    'B': [0, 12, 0, 0, 3, 0, 9, 0, 6, 0, 5, 4, 2, 0, 1, 0],  # 占位符
    'C': [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5],  # C191620 (完整)
    'D': [0, 4, 0, 13, 7, 0, 1, 0, 0, 0, 0, 11, 0, 12, 0, 0],  # 占位符
    'E': [0, 0, 0, 0, 13, 0, 0, 0, 0, 5, 0, 0, 4, 0, 0, 0],  # 占位符
    'F': [0, 8, 0, 0, 15, 0, 4, 3, 0, 9, 0, 0, 0, 13, 0, 12],  # 占位符
    'G': [14, 0, 4, 6, 0, 0, 12, 0, 2, 0, 0, 0, 0, 3, 0, 0],  # 占位符
    'H': [0, 13, 0, 0, 0, 5, 0, 9, 0, 0, 14, 6, 0, 0, 16, 0],  # 占位符
    'I': [13, 0, 0, 2, 0, 11, 0, 0, 14, 0, 0, 7, 0, 15, 0, 3],  # 占位符
    'J': [0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 8, 0, 7, 0],  # 占位符
    'K': [1, 0, 6, 0, 5, 0, 0, 2, 0, 3, 0, 0, 9, 0, 0, 0],  # 占位符
    'L': [0, 0, 0, 4, 0, 16, 14, 0, 0, 0, 12, 5, 0, 0, 0, 1],  # 占位符
    'M': [15, 0, 0, 0, 12, 0, 0, 0, 5, 1, 0, 3, 0, 6, 0, 7],  # 占位符
    'N': [0, 0, 9, 0, 0, 6, 0, 0, 13, 0, 0, 15, 0, 0, 3, 0],  # 占位符
    'O': [0, 1, 0, 0, 9, 0, 0, 15, 0, 0, 2, 8, 0, 5, 0, 0],  # 占位符
    'P': [0, 0, 2, 0, 0, 0, 5, 0, 0, 14, 0, 0, 1, 0, 10, 15],  # 占位符
}

ROW_NAMES = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']

# ==================== 1. 对比三个解盘的相同/不同位置 ====================
print("\n" + "=" * 80)
print("阶段1：三解盘对比分析")
print("=" * 80)

def compare_solutions(sol1, sol2, name1="解盘1", name2="解盘2"):
    """比较两个解盘"""
    same_positions = []
    diff_positions = []
    
    for row in ROW_NAMES:
        for col_idx in range(16):
            val1 = sol1[row][col_idx]
            val2 = sol2[row][col_idx]
            if val1 == val2 and val1 != 0:
                same_positions.append((row, col_idx, val1))
            elif val1 != 0 and val2 != 0:
                diff_positions.append((row, col_idx, val1, val2))
    
    return same_positions, diff_positions

# 初始 vs 更新
print("\n【初始解盘 vs 更新解盘】")
same_init_upd, diff_init_upd = compare_solutions(SOLVER_INITIAL, SOLVER_UPDATE, "初始", "更新")
print(f"  相同位置: {len(same_init_upd)} 个")
print(f"  不同位置: {len(diff_init_upd)} 个")

print(f"\n  相同位置详情（前20个）：")
for row, col_idx, val in same_init_upd[:20]:
    print(f"    {row}{COL_NAMES[col_idx]} = {val}")

# 初始 vs 终局（只看有值的位置）
print("\n【初始解盘 vs 终局解盘（占位符对比）】")
same_init_final, diff_init_final = compare_solutions(SOLVER_INITIAL, SOLVER_FINAL, "初始", "终局")
print(f"  终局占位符中匹配初始解盘: {len(same_init_final)} 个")
print(f"  终局占位符中与初始解盘冲突: {len(diff_init_final)} 个")

if len(same_init_final) > 0:
    print(f"\n  匹配详情：")
    for row, col_idx, val in same_init_final:
        print(f"    {row}{COL_NAMES[col_idx]} = {val}")

if len(diff_init_final) > 0:
    print(f"\n  冲突详情：")
    for row, col_idx, val1, val2 in diff_init_final:
        print(f"    {row}{COL_NAMES[col_idx]}: 初始={val1}, 终局={val2}")

# 更新 vs 终局
print("\n【更新解盘 vs 终局解盘（占位符对比）】")
same_upd_final, diff_upd_final = compare_solutions(SOLVER_UPDATE, SOLVER_FINAL, "更新", "终局")
print(f"  终局占位符中匹配更新解盘: {len(same_upd_final)} 个")
print(f"  终局占位符中与更新解盘冲突: {len(diff_upd_final)} 个")

if len(same_upd_final) > 0:
    print(f"\n  匹配详情：")
    for row, col_idx, val in same_upd_final:
        print(f"    {row}{COL_NAMES[col_idx]} = {val}")

if len(diff_upd_final) > 0:
    print(f"\n  冲突详情：")
    for row, col_idx, val1, val2 in diff_upd_final:
        print(f"    {row}{COL_NAMES[col_idx]}: 更新={val1}, 终局={val2}")

# ==================== 2. 联结锚点分析 ====================
print("\n" + "=" * 80)
print("阶段2：联结锚点分析")
print("=" * 80)

# 定义联结锚点：在至少2个解盘中相同的位置
print("\n定义联结锚点（在≥2个完整解盘中值相同的位置）：")

link_anchors = defaultdict(set)  # {位置: {解盘名, ...}}

for row in ROW_NAMES:
    for col_idx in range(16):
        vals = {}
        if SOLVER_INITIAL[row][col_idx] != 0:
            vals['初始'] = SOLVER_INITIAL[row][col_idx]
        if SOLVER_UPDATE[row][col_idx] != 0:
            vals['更新'] = SOLVER_UPDATE[row][col_idx]
        if SOLVER_FINAL[row][col_idx] != 0:
            vals['终局'] = SOLVER_FINAL[row][col_idx]
        
        if len(vals) >= 2:
            # 检查值是否相同
            unique_vals = set(vals.values())
            if len(unique_vals) == 1:
                pos = f"{row}{COL_NAMES[col_idx]}"
                link_anchors[pos] = set(vals.keys())

print(f"\n联结锚点总数: {len(link_anchors)} 个")
for pos, solvers in sorted(link_anchors.items()):
    val = SOLVER_INITIAL[pos[0]][ord(pos[1])-ord('D')]
    print(f"  {pos} = {val} (存在于: {', '.join(sorted(solvers))})")

# ==================== 3. 候选数解集收缩分析 ====================
print("\n" + "=" * 80)
print("阶段3：候选数解集收缩分析")
print("=" * 80)

# 从 txt 文件中提取的列解集约束
# 这里简化使用部分数据
column_sets = {
    # 行A的列解集
    'AD': {2,6,7,9,10,11}, 'AE': {2,6,7,9,10,11,15}, 'AF': {3},
    'AG': {1,7,9,10,11,15}, 'AH': {4,6,10,11,14}, 'AI': {12},
    'AJ': {6,10,11,13,15}, 'AK': {5}, 'AL': {1,7,9,10,12,15},
    'AM': {2,7,10,12,13,15}, 'AN': {1,7,9,10,13,15}, 'AO': {14},
    'AP': {6,7,10,11,13,14,15}, 'AQ': {16}, 'AR': {4,6,9,11,13,14,15},
    'AS': {8},
}

def analyze_solution_coverage(sol, col_sets):
    """分析解盘对候选数解集的覆盖"""
    covered = 0
    total = 0
    not_in_set = []
    
    for row in ROW_NAMES:
        for col in COL_NAMES:
            pos = row + col
            if pos in col_sets:
                total += 1
                val = sol[row][ord(col)-ord('D')]
                if val in col_sets[pos]:
                    covered += 1
                else:
                    not_in_set.append((pos, val, sorted(col_sets[pos])))
    
    return covered, total, not_in_set

print("\n各解盘对列解集约束的满足率：")
for sol_name, sol in [("初始解盘", SOLVER_INITIAL), ("更新解盘", SOLVER_UPDATE)]:
    covered, total, violations = analyze_solution_coverage(sol, column_sets)
    print(f"\n  {sol_name}:")
    print(f"    满足解集约束: {covered}/{total} ({covered/total*100:.1f}%)")
    if violations:
        print(f"    违反约束 ({len(violations)}个)：")
        for pos, val, allowed in violations[:10]:
            print(f"      {pos}: 实际值={val}, 解集={allowed}")

# ==================== 4. 终局C191620的深度分析 ====================
print("\n" + "=" * 80)
print("阶段4：终局C191620深度分析")
print("=" * 80)

C191620 = SOLVER_FINAL['C']
print(f"\n终局C191620: {C191620}")

# 对比三个C行
C_initial = SOLVER_INITIAL['C']
C_update = SOLVER_UPDATE['C']

print("\n三组C行对比：")
print(f"  初始解盘C: {C_initial}")
print(f"  更新解盘C: {C_update}")
print(f"  终局C191620: {C191620}")

# 计算匹配数
def match_count(a, b):
    return sum(1 for x, y in zip(a, b) if x == y)

print(f"\n匹配数统计：")
print(f"  初始 vs 终局: {match_count(C_initial, C191620)}/16")
print(f"  更新 vs 终局: {match_count(C_update, C191620)}/16")
print(f"  初始 vs 更新: {match_count(C_initial, C_update)}/16")

# 分析C191620的奇偶性
def permutation_parity(perm):
    inversions = 0
    for i in range(len(perm)):
        for j in range(i+1, len(perm)):
            if perm[i] > perm[j]:
                inversions += 1
    return 'odd' if inversions % 2 == 1 else 'even', inversions

parity_c191620, inv_c191620 = permutation_parity(C191620)
parity_c_initial, inv_c_initial = permutation_parity(C_initial)
parity_c_update, inv_c_update = permutation_parity(C_update)

print(f"\nC行排列特征：")
print(f"  初始C: 奇偶={parity_c_initial}, 逆序数={inv_c_initial}")
print(f"  更新C: 奇偶={parity_c_update}, 逆序数={inv_c_update}")
print(f"  C191620: 奇偶={parity_c191620}, 逆序数={inv_c191620}")

# ==================== 5. 92锚点与三个解盘的验证 ====================
print("\n" + "=" * 80)
print("阶段5：92锚点与三个解盘的验证")
print("=" * 80)

# 92锚点定义
anchors_92 = [
    ('B','R',1),('D','J',1),('K','D',1),('L','S',1),('M','M',1),('O','E',1),('P','P',1),
    ('B','P',2),('C','I',2),('G','L',2),('I','G',2),('K','K',2),('N','O',2),('P','F',2),
    ('A','F',3),('B','H',3),('F','K',3),('G','Q',3),('I','S',3),('K','M',3),('M','O',3),('N','R',3),
    ('B','O',4),('D','E',4),('E','P',4),('F','J',4),('G','F',4),('L','G',4),
    ('A','K',5),('B','N',5),('E','M',5),('H','I',5),('J','E',5),('K','H',5),('L','O',5),('M','L',5),
    ('B','L',6),('G','G',6),('H','O',6),('K','F',6),('M','Q',6),('N','I',6),
    ('D','H',7),('I','O',7),('J','R',7),('M','S',7),
    ('A','S',8),('C','K',8),('F','E',8),('J','P',8),('O','O',8),
    ('A','J',9),('F','M',9),('H','K',9),('K','P',9),('N','F',9),('O','H',9),
    ('P','R',10),('D','O',11),('I','I',11),
    ('A','I',12),('B','E',12),('D','Q',12),('F','S',12),('G','J',12),('L','N',12),('M','H',12),
    ('D','G',13),('E','H',13),('F','Q',13),('H','E',13),('I','D',13),('L','L',13),
    ('A','O',14),('C','F',14),('D','G',14),('H','N',14),('I','L',14),('L','J',14),('P','M',14),
    ('F','H',15),('I','Q',15),('M','D',15),('N','O',15),('O','K',15),('P','S',15),
    ('A','Q',16),('H','R',16),('J','N',16),('L','I',16),
]

def verify_anchors(sol, anchors):
    """验证解盘是否满足92锚点"""
    col_map = {'D':0,'E':1,'F':2,'G':3,'H':4,'I':5,'J':6,'K':7,'L':8,'M':9,'N':10,'O':11,'P':12,'Q':13,'R':14,'S':15}
    row_map = {'A':0,'B':1,'C':2,'D':3,'E':4,'F':5,'G':6,'H':7,'I':8,'J':9,'K':10,'L':11,'M':12,'N':13,'O':14,'P':15}
    
    matches = 0
    violations = []
    total = 0
    
    for r_char, c_char, expected in anchors:
        total += 1
        r = row_map[r_char]
        c = col_map[c_char]
        actual = sol[r_char][c]
        if actual == expected:
            matches += 1
        else:
            violations.append((r_char + c_char, expected, actual))
    
    return matches, total, violations

print("\n各解盘对92锚点的满足情况：")
for sol_name, sol in [("初始解盘", SOLVER_INITIAL), ("更新解盘", SOLVER_UPDATE), ("终局解盘（占位符）", SOLVER_FINAL)]:
    matches, total, violations = verify_anchors(sol, anchors_92)
    print(f"\n  {sol_name}:")
    print(f"    锚点匹配: {matches}/{total} ({matches/total*100:.1f}%)")
    if violations:
        print(f"    违反锚点 ({len(violations)}个)：")
        for pos, expected, actual in violations[:10]:
            print(f"      {pos}: 期望={expected}, 实际={actual}")

# ==================== 6. 输出分析报告 ====================
print("\n" + "=" * 80)
print("阶段6：生成联闔分析报告")
print("=" * 80)

report = {
    'timestamp': datetime.now().isoformat(),
    'three_solutions_comparison': {
        'initial_vs_update': {'same': len(same_init_upd), 'different': len(diff_init_upd)},
        'initial_vs_final': {'same': len(same_init_final), 'conflict': len(diff_init_final)},
        'update_vs_final': {'same': len(same_upd_final), 'conflict': len(diff_upd_final)},
    },
    'link_anchors': {pos: list(solvers) for pos, solvers in link_anchors.items()},
    'c_rows_comparison': {
        'initial': {'perm': C_initial, 'parity': parity_c_initial, 'inversions': inv_c_initial},
        'update': {'perm': C_update, 'parity': parity_c_update, 'inversions': inv_c_update},
        'final_c191620': {'perm': C191620, 'parity': parity_c191620, 'inversions': inv_c191620},
        'match_counts': {
            'initial_vs_final': match_count(C_initial, C191620),
            'update_vs_final': match_count(C_update, C191620),
            'initial_vs_update': match_count(C_initial, C_update),
        }
    },
    'anchors_92_verification': {
        'initial': verify_anchors(SOLVER_INITIAL, anchors_92)[0:2],
        'update': verify_anchors(SOLVER_UPDATE, anchors_92)[0:2],
    },
    'conclusions': [
        f"初始解盘与更新解盘有{len(same_init_upd)}个相同位置",
        f"终局C191620与初始C匹配{match_count(C_initial, C191620)}个位置",
        f"终局C191620与更新C匹配{match_count(C_update, C191620)}个位置",
        f"联结锚点共{len(link_anchors)}个",
    ]
}

with open('three_solutions_linkage_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("\n联闔分析报告已保存到: three_solutions_linkage_report.json")
print("\n" + "=" * 80)
print("分析完成！")
print("=" * 80)