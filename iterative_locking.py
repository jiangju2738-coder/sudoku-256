#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迭代锁定算法：从必然值出发，逐步缩小解空间
"""

import json
from ortools.sat.python import cp_model
from collections import Counter

# 92锚点
ANCHORS_92 = {
    'BR':1, 'DJ':1, 'KD':1, 'LS':1, 'MM':1, 'OE':1, 'PP':1,
    'BP':2, 'BP':2, 'CI':2, 'GL':2, 'IG':2, 'KK':2, 'ON':2, 'PF':2,
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

# 7个必然值（从链式分析得出）
LOCKED_VALUES = {
    'HH': 2,
    'JI': 9,
    'JJ': 3,
    'JO': 2,
    'KR': 12,
    'NH': 14,
    'NK': 1,
}

ROW_NAMES = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']
ROW_MAP = {name: i for i, name in enumerate(ROW_NAMES)}
COL_MAP = {name: i for i, name in enumerate(COL_NAMES)}

def create_model(anchors, locked_values):
    """创建CP-SAT模型"""
    model = cp_model.CpModel()
    grid = {}
    for r in range(16):
        for c in range(16):
            grid[(r, c)] = model.NewIntVar(1, 16, f'g{r}{c}')
    
    # 行/列/宫约束
    for r in range(16):
        model.AddAllDifferent([grid[(r, c)] for c in range(16)])
    for c in range(16):
        model.AddAllDifferent([grid[(r, c)] for r in range(16)])
    for br in range(4):
        for bc in range(4):
            cells = [grid[(br*4+dr, bc*4+dc)] for dr in range(4) for dc in range(4)]
            model.AddAllDifferent(cells)
    
    # 锚点约束
    for coord, val in anchors.items():
        r, c = ROW_MAP[coord[0]], COL_MAP[coord[1]]
        model.Add(grid[(r, c)] == val)
    
    # 锁定值约束
    for coord, val in locked_values.items():
        r, c = ROW_MAP[coord[0]], COL_MAP[coord[1]]
        model.Add(grid[(r, c)] == val)
    
    return model, grid

def collect_solutions(anchors, locked_values, max_solutions=30, timeout=60):
    """收集多个解"""
    all_constraints = {**anchors, **locked_values}
    model, grid = create_model(all_constraints, {})
    
    class SolutionCollector(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.solutions = []
        
        def on_solution_callback(self):
            if len(self.solutions) < max_solutions:
                sol = {}
                for r in range(16):
                    for c in range(16):
                        coord = ROW_NAMES[r] + COL_NAMES[c]
                        sol[coord] = self.Value(grid[(r, c)])
                self.solutions.append(sol)
    
    collector = SolutionCollector()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.num_search_workers = 8
    solver.parameters.log_search_progress = False
    
    solver.SearchForAllSolutions(model, collector)
    return collector.solutions

def find_unambiguous_positions(solutions):
    """找出在所有解中取相同值的位置"""
    # 统计每个位置的值分布
    pos_values = {}
    for sol in solutions:
        for coord, val in sol.items():
            if coord not in pos_values:
                pos_values[coord] = set()
            pos_values[coord].add(val)
    
    unambiguous = {}
    for coord, values in pos_values.items():
        if len(values) == 1:
            # 该位置在所有解中取相同值
            val = list(values)[0]
            if coord not in ANCHORS_92 and coord not in LOCKED_VALUES:
                unambiguous[coord] = val
    
    return unambiguous

print("=" * 80)
print("迭代锁定算法：从必然值出发逐步缩小解空间")
print("=" * 80)

# 初始锁定值
current_locked = dict(LOCKED_VALUES)
iteration = 0

print(f"\n【第0轮】初始锁定值：{len(current_locked)}个")
for coord, val in sorted(current_locked.items()):
    print(f"  {coord} = {val}")

print(f"\n【第0轮】合并约束总数：92 + {len(current_locked)} = {92 + len(current_locked)}")

# 第1轮：收集解并找新的必然值
print("\n" + "-" * 60)
print("第1轮：搜索多解，寻找新的必然值")
print("-" * 60)

solutions = collect_solutions(ANCHORS_92, current_locked, max_solutions=30, timeout=30)

print(f"找到解的数量：{len(solutions)}")

if len(solutions) == 0:
    print("⚠️ 无解！当前约束冲突。")
    NEW_VALUES = {}
elif len(solutions) == 1:
    print("✅ 唯一解！迭代锁定收敛。")
    NEW_VALUES = {}
else:
    # 找出新的必然值
    NEW_VALUES = find_unambiguous_positions(solutions)
    print(f"发现 {len(NEW_VALUES)} 个新的必然值：")
    for coord, val in sorted(NEW_VALUES.items()):
        print(f"  {coord} = {val}")

iteration = 1
total_locked = current_locked.copy()
total_locked.update(NEW_VALUES)

print(f"\n【第{iteration}轮】总锁定数：{len(total_locked)}")

# 迭代收敛
ITERATION_LIMIT = 6
while NEW_VALUES and iteration < ITERATION_LIMIT:
    iteration += 1
    print("\n" + "=" * 80)
    print(f"第{iteration}轮：继续迭代")
    print("=" * 80)
    
    print(f"\n【第{iteration}轮】当前锁定数：{len(total_locked)}")
    
    solutions = collect_solutions(ANCHORS_92, total_locked, max_solutions=20, timeout=20)
    
    if len(solutions) == 0:
        print("⚠️ 无解！约束冲突。")
        break
    elif len(solutions) == 1:
        print("✅ 唯一解！迭代收敛。")
        break
    else:
        NEW_VALUES = find_unambiguous_positions(solutions)
        if not NEW_VALUES:
            print("无新的必然值，收敛。")
            break
        
        print(f"发现 {len(NEW_VALUES)} 个新必然值")
        for coord, val in sorted(NEW_VALUES.items()):
            print(f"  {coord} = {val}")
        total_locked.update(NEW_VALUES)
        print(f"总锁定数变为：{len(total_locked)}")

print("\n" + "=" * 80)
print("迭代锁定算法完成")
print("=" * 80)

# 最终结果
print(f"\n【最终锁定数】：{len(total_locked)} 个位置")
print(f"  原始92锚点 + {len(total_locked) - 92} 个必然值")

print(f"\n【所有锁定值】：")
for coord, val in sorted(total_locked.items()):
    is_anchor = coord in ANCHORS_92
    marker = "[锚点]" if is_anchor else "[必然值]"
    print(f"  {coord} = {val} {marker}")

# 最后：搜索一次最终约束的唯一解
print("\n" + "=" * 80)
print("最终验证：用所有锁定值搜索")
print("=" * 80)

final_solutions = collect_solutions(ANCHORS_92, total_locked, max_solutions=3, timeout=60)

if len(final_solutions) == 0:
    print("❌ 无解！锁定值冲突。")
elif len(final_solutions) == 1:
    print("✅ 唯一解！")
    print("\n最终解（前5行示例）：")
    for row_idx in range(5):
        row_name = ROW_NAMES[row_idx]
        row = [final_solutions[0][row_name + col] for col in COL_NAMES]
        print(f"  {row_name}: {row}")
else:
    print(f"[!] 找到 {len(final_solutions)} 个解，仍未收敛到唯一解")
    print("\n解的差异分析：")
    # 找出差异位置
    all_coords = [row + col for row in ROW_NAMES for col in COL_NAMES]
    for coord in all_coords:
        vals = set(sol[coord] for sol in final_solutions)
        if len(vals) > 1:
            print(f"  {coord}: {sorted(vals)}")

# 保存最终锁定结果
output = {
    'total_locked': len(total_locked),
    'locked_values': total_locked,
    'iterations': iteration,
    'final_solutions_count': len(final_solutions),
}

with open('locked_values_final.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n[OK] 最终锁定结果已保存到 locked_values_final.json")