#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用CP-SAT枚举92锚点 + C191620下的所有完整解
并与已知解盘对比分析
"""

import json
from ortools.sat.python import cp_model
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("CP-SAT 枚举全部完整解（92锚点 + C191620）")
print("=" * 80)

# 92锚点
ANCHORS = {
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

ROW_MAP = {'A':0,'B':1,'C':2,'D':3,'E':4,'F':5,'G':6,'H':7,'I':8,'J':9,'K':10,'L':11,'M':12,'N':13,'O':14,'P':15}
COL_MAP = {'D':0,'E':1,'F':2,'G':3,'H':4,'I':5,'J':6,'K':7,'L':8,'M':9,'N':10,'O':11,'P':12,'Q':13,'R':14,'S':15}

# C191620
C191620 = [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5]

# 已知的三个解盘
KNOWN_SOLUTIONS = {
    'initial': {
        'A': [7, 15, 3, 9, 11, 12, 6, 5, 10, 2, 1, 14, 13, 16, 4, 8],
        'B': [16, 12, 10, 8, 3, 15, 9, 14, 6, 13, 5, 4, 2, 7, 1, 11],
        'C': [11, 6, 14, 1, 4, 2, 13, 8, 7, 12, 3, 16, 10, 9, 15, 5],
        'D': [2, 4, 5, 13, 7, 10, 1, 16, 15, 8, 9, 11, 3, 12, 14, 6],
        'E': [9, 2, 7, 10, 13, 1, 16, 6, 3, 5, 15, 12, 4, 11, 8, 14],
        'F': [5, 8, 1, 11, 15, 14, 4, 3, 16, 9, 7, 10, 6, 13, 2, 12],
        'G': [14, 16, 4, 6, 8, 7, 12, 10, 2, 11, 13, 1, 15, 3, 5, 9],
        'H': [3, 13, 15, 12, 2, 5, 11, 9, 8, 4, 14, 6, 7, 1, 16, 10],
        'I': [13, 9, 16, 2, 1, 11, 8, 12, 14, 10, 4, 7, 5, 15, 6, 3],
        'J': [12, 5, 11, 15, 10, 9, 3, 13, 1, 6, 16, 2, 8, 14, 7, 4],
        'K': [1, 14, 6, 7, 5, 4, 15, 2, 11, 3, 8, 13, 9, 10, 12, 16],
        'L': [10, 3, 8, 4, 6, 16, 14, 7, 9, 15, 12, 5, 11, 2, 13, 1],
        'M': [15, 11, 13, 16, 12, 8, 2, 4, 5, 1, 10, 3, 14, 6, 9, 7],
        'N': [4, 10, 9, 5, 14, 6, 7, 1, 13, 16, 11, 15, 12, 8, 3, 2],
        'O': [6, 1, 12, 14, 9, 3, 10, 15, 4, 7, 2, 8, 16, 5, 11, 13],
        'P': [8, 7, 2, 3, 16, 13, 5, 11, 12, 14, 6, 9, 1, 4, 10, 15],
    },
    'update': {
        'A': [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5],
        'B': [8, 12, 7, 10, 3, 15, 9, 11, 6, 16, 5, 4, 2, 14, 1, 13],
        'C': [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5],
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
    },
}

class SolutionCollector(cp_model.CpSolverSolutionCallback):
    """收集所有解的回调类"""
    def __init__(self, grid):
        super().__init__()
        self.grid = grid
        self.solutions = []
        self.solution_count = 0
        self.max_solutions = 1000  # 限制最大收集数

    def on_solution_callback(self):
        if self.solution_count >= self.max_solutions:
            return
        solution = []
        for r in range(16):
            row = [self.Value(self.grid[(r, c)]) for c in range(16)]
            solution.append(tuple(row))
        self.solutions.append(solution)
        self.solution_count += 1
        if self.solution_count % 10 == 0:
            print(f"  已找到 {self.solution_count} 个解...")

print("\n构建CP-SAT模型...")

model = cp_model.CpModel()
grid = {}

# 创建变量
for r in range(16):
    for c in range(16):
        grid[(r, c)] = model.NewIntVar(1, 16, f'g{r}{c}')

# 行约束
for r in range(16):
    model.AddAllDifferent([grid[(r, c)] for c in range(16)])

# 列约束
for c in range(16):
    model.AddAllDifferent([grid[(r, c)] for r in range(16)])

# 宫约束
for br in range(4):
    for bc in range(4):
        cells = [grid[(br*4+dr, bc*4+dc)] for dr in range(4) for dc in range(4)]
        model.AddAllDifferent(cells)

# 92锚点
for coord, val in ANCHORS.items():
    r, c = ROW_MAP[coord[0]], COL_MAP[coord[1]]
    model.Add(grid[(r, c)] == val)

# C191620 固定第C行
for i, val in enumerate(C191620):
    model.Add(grid[(2, i)] == val)

print(f"  锚点数量: {len(ANCHORS)}")
print(f"  C191620 已固定")
print()

# 创建求解器
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0  # 5分钟
solver.parameters.num_search_workers = 8
solver.parameters.enumerate_all_solutions = True

# 创建解收集器
collector = SolutionCollector(grid)

print("开始枚举所有解...")
print("=" * 60)

status = solver.Solve(model, collector)

print("=" * 60)
print(f"\n搜索完成！")
print(f"  状态: {status}")
print(f"  找到的解数量: {collector.solution_count}")

all_solutions = collector.solutions

if collector.solution_count == 0:
    print("\n【重要发现】无解！")
    print("这说明 92 锚点 + C191620 存在冲突。")
elif collector.solution_count == 1:
    print("\n【唯一解】只有一个解！")
    print("解盘如下：")
    solution = all_solutions[0]
    for r, row in enumerate(solution):
        print(f"  {chr(65+r)}: {list(row)}")
else:
    print(f"\n【多解】找到 {collector.solution_count} 个解！")
    print(f"说明 92 锚点 + C191620 不足以定义唯一解。")

# 与已知解盘对比
print("\n" + "=" * 80)
print("与已知解盘对比分析")
print("=" * 80)

for sol_idx, solution in enumerate(all_solutions[:10]):  # 只显示前10个解
    print(f"\n--- 解 #{sol_idx + 1} ---")
    matches_with_initial = 0
    matches_with_update = 0
    matches_with_txt_final = 0
    
    txt_final = {
        'B': [8, 12, 7, 10, 3, 15, 9, 11, 6, 16, 5, 4, 2, 14, 1, 13],
        'C': tuple(C191620),
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
    
    for r in range(16):
        rname = chr(65 + r)
        cp_sat_row = tuple(solution[r])
        
        # 对比initial
        if rname in KNOWN_SOLUTIONS['initial']:
            init_row = tuple(KNOWN_SOLUTIONS['initial'][rname])
            if cp_sat_row == init_row:
                matches_with_initial += 1
        
        # 对比update
        if rname in KNOWN_SOLUTIONS['update']:
            update_row = tuple(KNOWN_SOLUTIONS['update'][rname])
            if cp_sat_row == update_row:
                matches_with_update += 1
        
        # 对比txt终局
        if rname in txt_final:
            txt_row = tuple(txt_final[rname])
            if cp_sat_row == txt_row:
                matches_with_txt_final += 1
    
    print(f"  与初始解盘完全匹配行数: {matches_with_initial}/16")
    print(f"  与更新解盘完全匹配行数: {matches_with_update}/16")
    print(f"  与txt终局解盘完全匹配行数: {matches_with_txt_final}/15 (B-P行)")
    
    if matches_with_txt_final >= 14:
        print("  *** 高度匹配txt终局解盘！***")

# 保存所有解
if all_solutions:
    output = {
        'search_config': {
            'anchors': len(ANCHORS),
            'c191620': C191620,
            'constraints': '92 anchors + Sudoku 3 constraints + C191620'
        },
        'solution_count': collector.solution_count,
        'solutions': all_solutions,
        'comparison': {}
    }
    
    with open('all_solutions_found.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n所有解已保存到: all_solutions_found.json")

print("\n" + "=" * 80)
print("关键分析结论")
print("=" * 80)

if collector.solution_count == 0:
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ 结论：92锚点 + C191620 存在冲突，无解                            │
│                                                                 │
│ 这说明：                                                          │
│ 1. txt文件中的C191620与92锚点存在某种冲突                        │
│ 2. 终局解盘不是通过92锚点+C191620推导出来的                      │
│ 3. 终局解盘可能来自原始的符阖排列组闔（1,360,849个排列）         │
│    而不是从92锚点搜索得到的                                      │
└─────────────────────────────────────────────────────────────────┘
""")
elif collector.solution_count == 1:
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ 结论：92锚点 + C191620 定义唯一解                                │
│                                                                 │
│ 该解与txt终局解盘的匹配情况需进一步分析。                        │
│ 如果完全匹配，证明txt终局解盘 = 92锚点+C191620的唯一解。         │
│ 如果不匹配，证明txt终局解盘来自其他约束系统。                    │
└─────────────────────────────────────────────────────────────────┘
""")
else:
    print(f"""
┌─────────────────────────────────────────────────────────────────┐
│ 结论：92锚点 + C191620 有 {collector.solution_count} 个解，非唯一           │
│                                                                 │
│ 说明：                                                            │
│ 1. 92锚点 + C191620 不足以定义唯一解                             │
│ 2. 需要更多约束（如其他行的符阖排列）才能压缩解空间               │
│ 3. txt终局解盘可能是这 {collector.solution_count} 个解中的一个                  │
│    或者是符阖排列组闔约束下的子集                                │
└─────────────────────────────────────────────────────────────────┘
""")
