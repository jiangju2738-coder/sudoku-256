#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实际行动：在backup_fuyi/中搜索完整解，验证终局解盘能否实现
"""

import json
from itertools import product

print("=" * 80)
print("实际行动：从backup_fuyi/搜索符阖排列组闔空间")
print("=" * 80)

# 加载backup_fuyi/的所有排列
backup = {}
row_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']

print("\n加载backup_fuyi/...")
for i, row_name in enumerate(row_names):
    filepath = f'backup_fuyi/A{i+1}_permutations.json'
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            perms = json.load(f)
        backup[row_name] = [tuple(p) for p in perms]
        print(f"  {row_name}: {len(backup[row_name])} 个排列")
    except FileNotFoundError:
        print(f"  {row_name}: 文件不存在！")
        backup[row_name] = []

print(f"\n总排列数: {sum(len(v) for v in backup.values())}")

# 终局解盘定义（从txt文件第87行）
FINAL_C = (7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5)

print("\n" + "=" * 80)
print("验证1: 终局C191620是否在backup_fuyi/的A3集合中？")
print("=" * 80)

if 'C' in backup and len(backup['C']) > 0:
    in_backup = FINAL_C in backup['C']
    print(f"  C191620 in backup C集合: {in_backup}")
    print(f"  backup C集合大小: {len(backup['C'])}")
    if not in_backup:
        print("  结论: C191620不在backup_fuyi/中！")
else:
    print("  backup C集合为空或不存在！")

# 验证终局解盘的B-P行是否在backup中
print("\n" + "=" * 80)
print("验证2: 终局解盘B-P行是否都在backup中？")
print("=" * 80)

FINAL_ROWS = {
    'A': None,  # 终局A行是占位符，跳过
    'B': (8, 12, 7, 10, 3, 15, 9, 11, 6, 16, 5, 4, 2, 14, 1, 13),
    'C': FINAL_C,
    'D': (9, 4, 16, 13, 7, 14, 1, 6, 8, 2, 10, 11, 3, 12, 15, 5),
    'E': (7, 10, 15, 9, 13, 8, 6, 14, 12, 5, 3, 16, 4, 1, 11, 2),
    'F': (2, 8, 5, 16, 15, 1, 4, 3, 11, 9, 7, 10, 6, 13, 14, 12),
    'G': (14, 11, 4, 6, 16, 7, 12, 10, 2, 13, 15, 1, 5, 3, 8, 9),
    'H': (12, 13, 1, 3, 2, 5, 11, 9, 4, 8, 14, 6, 15, 7, 16, 10),
    'I': (13, 9, 8, 2, 6, 11, 10, 12, 14, 4, 1, 7, 16, 15, 5, 3),
    'J': (10, 5, 12, 14, 1, 9, 3, 13, 15, 11, 16, 2, 8, 4, 7, 6),
    'K': (1, 16, 6, 7, 5, 4, 15, 2, 10, 3, 8, 13, 9, 11, 12, 14),
    'L': (3, 15, 11, 4, 8, 16, 14, 7, 9, 6, 12, 5, 13, 10, 2, 1),
    'M': (15, 14, 13, 8, 12, 10, 2, 16, 5, 1, 4, 3, 11, 6, 9, 7),
    'N': (4, 7, 9, 5, 14, 6, 8, 1, 13, 10, 11, 15, 12, 2, 3, 16),
    'O': (6, 1, 10, 11, 9, 3, 7, 15, 16, 12, 2, 8, 14, 5, 13, 4),
    'P': (16, 3, 2, 12, 11, 13, 5, 4, 7, 14, 6, 9, 1, 8, 10, 15),
}

in_backup_count = 0
for row_name, row_perm in FINAL_ROWS.items():
    if row_perm is None:
        print(f"  {row_name}: 占位符，跳过")
        continue
    
    if row_name in backup and row_perm in backup[row_name]:
        print(f"  {row_name}: [OK] 在backup中")
        in_backup_count += 1
    else:
        print(f"  {row_name}: [NO] 不在backup中")

print(f"\n  B-P行在backup中的匹配率: {in_backup_count}/15 = {in_backup_count/15*100:.1f}%")

# 尝试搜索完整解
print("\n" + "=" * 80)
print("搜索3: 在backup_fuyi/中搜索满足数独三约束的完整解")
print("=" * 80)

print("\n注意：backup_fuyi/共有20,603个排列，")
print(f"所有可能的组合数 = {len(backup['A'])} × {len(backup['B'])} × ... ≈ 天文数字")
print("无法穷举，需要用约束搜索...")

# 方法：从终局C191620出发，搜索其他行
print("\n策略：固定C=C191620，搜索其他15行")

if FINAL_C not in backup.get('C', []):
    print("\n  结论：C191620不在backup_fuyi/中！")
    print("  这意味着终局解盘C行不在我们已知的排列子集中。")
    print("  backup_fuyi/是筛选子集，不是完整解空间。")
else:
    print("\n  C191620在backup中，继续搜索...")

# 检查每列在C=C191620下的约束
COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']

print("\nC191620各列值：")
for i, col in enumerate(COL_NAMES):
    print(f"  {col} = {FINAL_C[i]}")

# 搜索与C191620兼容的其他行
print("\n搜索与C191620兼容的行（列不冲突）：")
compatible_rows = {}

for row_name in ['A', 'B', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']:
    if row_name not in backup:
        compatible_rows[row_name] = []
        continue
    
    count = 0
    for perm in backup[row_name]:
        # 检查与C191620是否列冲突
        conflict = False
        for i in range(16):
            if perm[i] == FINAL_C[i]:
                conflict = True
                break
        if not conflict:
            count += 1
    
    compatible_rows[row_name] = count
    print(f"  {row_name}: {count} 个排列与C191620列不冲突（共{len(backup[row_name])}个）")

print("\n" + "=" * 80)
print("搜索4: 尝试用C191620 + 92锚点搜索CP-SAT完整解")
print("=" * 80)

# 用CP-SAT搜索：92锚点 + C191620固定
from ortools.sat.python import cp_model

def solve_with_c191620():
    """用CP-SAT搜索92锚点 + C191620的解"""
    model = cp_model.CpModel()
    
    # 创建变量
    grid = {}
    for r in range(16):
        for c in range(16):
            grid[(r, c)] = model.NewIntVar(1, 16, f'grid_{r}_{c}')
    
    # 行约束
    for r in range(16):
        model.AddAllDifferent([grid[(r, c)] for c in range(16)])
    
    # 列约束
    for c in range(16):
        model.AddAllDifferent([grid[(r, c)] for r in range(16)])
    
    # 宫约束 (4x4宫)
    for br in range(4):
        for bc in range(4):
            cells = []
            for dr in range(4):
                for dc in range(4):
                    cells.append(grid[(br*4+dr, bc*4+dc)])
            model.AddAllDifferent(cells)
    
    # 92锚点
    anchors = {
        'BR':1, 'DJ':1, 'KD':1, 'LS':1, 'MM':1, 'OE':1, 'PP':1,
        'BP':2, 'CI':2, 'GL':2, 'IG':2, 'KK':2, 'ON':2, 'PF':2,
        'AF':3, 'BH':3, 'FK':3, 'GQ':3, 'IS':3, 'KM':3, 'MO':3, 'NR':3,
        'BO':4, 'DE':4, 'EP':4, 'FJ':4, 'GF':4, 'LG':4,
        'AK':5, 'BN':5, 'EM':5, 'HI':5, 'JE':5, 'KH':5, 'LO':5, 'ML':5, 'OQ':5, 'PJ':5,
        'BL':6, 'GG':6, 'HO':6, 'KF':6, 'MQ':6, 'NI':6,
        'DH':7, 'IO':7, 'JR':7, 'MS':7,
        'AS':8, 'CK':8, 'FE':8, 'JP':8, 'OO':8,
        'BJ':9, 'FM':9, 'HK':9, 'KP':9, 'NF':9, 'OH':9,
        'PR':10,
        'DO':11, 'II':11,
        'AI':12, 'BE':12, 'DQ':12, 'FS':12, 'GJ':12, 'LN':12, 'MH':12,
        'DG':13, 'EH':13, 'FQ':13, 'HE':13, 'ID':13, 'NL':13,
        'AO':14, 'CF':14, 'GD':14, 'HN':14, 'IL':14, 'LJ':14, 'PM':14,
        'FH':15, 'IQ':15, 'MD':15, 'NO':15, 'OK':15, 'PS':15,
        'AQ':16, 'HR':16, 'JN':16, 'LI':16,
    }
    
    row_map = {'A':0,'B':1,'C':2,'D':3,'E':4,'F':5,'G':6,'H':7,'I':8,'J':9,'K':10,'L':11,'M':12,'N':13,'O':14,'P':15}
    col_map = {'D':0,'E':1,'F':2,'G':3,'H':4,'I':5,'J':6,'K':7,'L':8,'M':9,'N':10,'O':11,'P':12,'Q':13,'R':14,'S':15}
    
    for coord, val in anchors.items():
        r, c = row_map[coord[0]], col_map[coord[1]]
        model.Add(grid[(r, c)] == val)
    
    # C191620固定
    for i, val in enumerate(FINAL_C):
        model.Add(grid[(2, i)] == val)
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.num_search_workers = 8
    
    print("  开始CP-SAT搜索...")
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("  找到解！")
        solution = []
        for r in range(16):
            row = [solver.Value(grid[(r, c)]) for c in range(16)]
            solution.append(row)
            if r == 2:
                print(f"  行C = {row}")
                # 检查是否与C191620相同
                if tuple(row) == FINAL_C:
                    print("    [SAME] 与C191620一致")
                else:
                    print("    [DIFF] 与C191620不同！")
        return solution
    else:
        print("  无解！")
        return None

solution = solve_with_c191620()

print("\n" + "=" * 80)
print("总结")
print("=" * 80)

if solution:
    print("""
成功找到92锚点 + C191620的解！

这意味着：
1. 92锚点 + C191620 可以导出完整解
2. 该解是否满足其他行的符阖排列约束？需要验证
3. 如果其他行不在backup_fuyi/中，说明backup_fuyi/不是完整解集

下一步：验证解的其他15行是否在backup_fuyi/中
""")
else:
    print("""
92锚点 + C191620 返回无解！

这意味着：
1. C191620与92锚点可能存在冲突
2. 或者我的92锚点定义有误
3. 需要重新检查92锚点和C191620的一致性
""")
