#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔數獨 V63: 验证解盘是否为符闔原题解

验证步骤：
1. 对比解盘与txt文件中的终局解盘
2. 枚举所有解，验证唯一性
3. 分析解的特征
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
from ortools.sat.python import cp_model

# ============================================================================
# 加载找到的解
# ============================================================================

with open('solution_compressed_search.json', 'r', encoding='utf-8') as f:
    solution_data = json.load(f)

found_solution = solution_data['solution']
C191620 = solution_data['C191620']

# ============================================================================
# 对比txt文件中的终局解盘
# ============================================================================

def compare_with_txt_final():
    """对比txt文件中的终局解盘"""
    print("=" * 80)
    print("对比txt文件中的终局解盘")
    print("=" * 80)
    
    # txt文件中的终局解盘（只有C行完整，其他行是占位符）
    txt_final_c = [7,10,14,15, 4,2,16,8, 12,13,3,1, 11,9,6,5]
    
    # 我们找到的解的C行
    found_c = found_solution[2]  # C行是索引2
    
    print(f"\ntxt终局C191620: {txt_final_c}")
    print(f"找到的解C行:    {found_c}")
    print(f"匹配: {'✓ 完全匹配' if found_c == txt_final_c else '✗ 不匹配'}")
    
    # txt文件中的初始解盘C行
    txt_initial_c = [11,6,14,1, 4,2,13,8, 7,12,3,16, 10,9,15,5]
    
    print(f"\ntxt初始解盘C:   {txt_initial_c}")
    match_initial = found_c == txt_initial_c
    print(f"与初始解盘C匹配: {'✓' if match_initial else '✗'} ({sum(1 for a,b in zip(found_c, txt_initial_c) if a==b)}/16)")
    
    # txt文件中的更新解盘C行
    txt_update_c = [5,6,14,1, 10,2,16,8, 3,15,13,12, 7,9,4,11]
    
    print(f"\ntxt更新解盘C:   {txt_update_c}")
    match_update = found_c == txt_update_c
    print(f"与更新解盘C匹配: {'✓' if match_update else '✗'} ({sum(1 for a,b in zip(found_c, txt_update_c) if a==b)}/16)")
    
    return {
        'txt_final': txt_final_c,
        'txt_initial': txt_initial_c,
        'txt_update': txt_update_c,
        'found': found_c,
        'matches_final': found_c == txt_final_c,
        'matches_initial': found_c == txt_initial_c,
        'matches_update': found_c == txt_update_c,
    }

# ============================================================================
# 枚举所有解，验证唯一性
# ============================================================================

def enumerate_all_solutions():
    """枚举所有解"""
    print("\n" + "=" * 80)
    print("枚举所有解（验证唯一性）")
    print("=" * 80)
    
    col_letter_to_idx = {
        'D': 0, 'E': 1, 'F': 2, 'G': 3,
        'H': 4, 'I': 5, 'J': 6, 'K': 7,
        'L': 8, 'M': 9, 'N': 10, 'O': 11,
        'P': 12, 'Q': 13, 'R': 14, 'S': 15,
    }
    
    row_letter_to_idx = {
        'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5,
        'G': 6, 'H': 7, 'I': 8, 'J': 9, 'K': 10, 'L': 11,
        'M': 12, 'N': 13, 'O': 14, 'P': 15,
    }
    
    anchors_by_value = {
        1: ['BR', 'DJ', 'KD', 'LS', 'MM', 'OE', 'PP'],
        2: ['BP', 'CI', 'GL', 'IG', 'KK', 'ON', 'PF'],
        3: ['AF', 'BH', 'FK', 'GQ', 'IS', 'KM', 'MO', 'NR'],
        4: ['BO', 'DE', 'EP', 'FJ', 'GF', 'LG'],
        5: ['AK', 'BN', 'EM', 'HI', 'JE', 'KH', 'LO', 'ML', 'OQ', 'PJ'],
        6: ['BL', 'GG', 'HO', 'KF', 'MQ', 'NI'],
        7: ['DH', 'IO', 'JR', 'MS'],
        8: ['AS', 'CK', 'FE', 'JP', 'OO'],
        9: ['BJ', 'FM', 'HK', 'KP', 'NF', 'OH'],
        10: ['PR'],
        11: ['DO', 'II'],
        12: ['AI', 'BE', 'DQ', 'FS', 'GJ', 'LN', 'MH'],
        13: ['DG', 'EH', 'FQ', 'HE', 'ID', 'NL'],
        14: ['AO', 'CF', 'GD', 'HN', 'IL', 'LJ', 'PM'],
        15: ['FH', 'IQ', 'MD', 'NO', 'OK', 'PS'],
        16: ['AQ', 'HR', 'JN', 'LI'],
    }
    
    def build_anchors_grid():
        anchors = {}
        for value, positions in anchors_by_value.items():
            for pos in positions:
                row = row_letter_to_idx[pos[0]]
                col = col_letter_to_idx[pos[1]]
                anchors[(row, col)] = value
        return anchors
    
    GRID_SIZE = 16
    BOX_SIZE = 4
    
    # 创建模型
    model = cp_model.CpModel()
    
    # 创建变量
    grid = {}
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            grid[(r, c)] = model.NewIntVar(1, GRID_SIZE, f'cell_{r}_{c}')
    
    # 添加C行约束（C191620）
    c_row_idx = row_letter_to_idx['C']
    for c, val in enumerate(C191620):
        model.Add(grid[(c_row_idx, c)] == val)
    
    # 添加92锚点约束
    anchors = build_anchors_grid()
    for (r, c), val in anchors.items():
        if r != c_row_idx:
            model.Add(grid[(r, c)] == val)
    
    # 添加数独三约束
    for r in range(GRID_SIZE):
        model.AddAllDifferent([grid[(r, c)] for c in range(GRID_SIZE)])
    for c in range(GRID_SIZE):
        model.AddAllDifferent([grid[(r, c)] for r in range(GRID_SIZE)])
    for box_r in range(BOX_SIZE):
        for box_c in range(BOX_SIZE):
            cells = []
            for dr in range(BOX_SIZE):
                for dc in range(BOX_SIZE):
                    r = box_r * BOX_SIZE + dr
                    c = box_c * BOX_SIZE + dc
                    cells.append(grid[(r, c)])
            model.AddAllDifferent(cells)
    
    # 枚举所有解
    print("\n开始枚举所有解...")
    
    solutions = []
    solution_count = 0
    
    class SolutionCollector(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.solutions = []
            self.solution_count = 0
            
        def on_solution_callback(self):
            self.solution_count += 1
            solution = []
            for r in range(GRID_SIZE):
                row = []
                for c in range(GRID_SIZE):
                    row.append(self.Value(grid[(r, c)]))
                solution.append(row)
            self.solutions.append(solution)
            
            # 每找到100个解打印一次
            if self.solution_count % 100 == 0:
                print(f"  已找到 {self.solution_count} 个解...")
    
    collector = SolutionCollector()
    
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 8
    solver.parameters.max_time_in_seconds = 300
    
    # 枚举所有解
    solver.SearchForAllSolutions(model, collector)
    
    solution_count = collector.solution_count
    solutions = collector.solutions
    
    print(f"\n枚举完成！")
    print(f"  总解数: {solution_count}")
    print(f"  耗时: {solver.WallTime():.2f}秒")
    
    if solution_count == 1:
        print(f"\n★ 唯一解！这表明C191620 + 92锚点 + 数独三约束确定唯一解。")
    elif solution_count > 1:
        print(f"\n发现 {solution_count} 个解，解不唯一。")
        print(f"\n前5个解的C行:")
        for i, sol in enumerate(solutions[:5]):
            print(f"  解{i+1} C行: {sol[2]}")
    
    return solutions, solution_count

# ============================================================================
# 分析解的特征
# ============================================================================

def analyze_solution_features(solution):
    """分析解的特征"""
    print("\n" + "=" * 80)
    print("解的特征分析")
    print("=" * 80)
    
    # 奇偶性分析
    def parity_of_permutation(perm):
        n = len(perm)
        visited = [False] * n
        sign = 1
        for i in range(n):
            if not visited[i]:
                cycle_len = 0
                j = i
                while not visited[j]:
                    visited[j] = True
                    j = perm[j] - 1
                    cycle_len += 1
                sign *= (-1) ** (cycle_len - 1)
        return sign == 1
    
    # 逆序数
    def inversion_count(perm):
        count = 0
        for i in range(len(perm)):
            for j in range(i + 1, len(perm)):
                if perm[i] > perm[j]:
                    count += 1
        return count
    
    print("\n各行特征:")
    print(f"{'行':<4} {'奇偶性':<8} {'逆序数':<8}")
    print("-" * 25)
    
    for r in range(16):
        row = solution[r]
        parity = "偶" if parity_of_permutation(row) else "奇"
        inv = inversion_count(row)
        row_letter = chr(ord('A') + r)
        print(f"{row_letter:<4} {parity:<8} {inv:<8}")
    
    # 检查是否所有行都是偶排列
    all_even = all(parity_of_permutation(solution[r]) for r in range(16))
    print(f"\n所有行都是偶排列: {'✓' if all_even else '✗'}")
    
    # C行与E行关系
    c_row = solution[2]
    e_row = solution[4]
    
    print(f"\nC-E关系分析:")
    print(f"C行: {c_row}")
    print(f"E行: {e_row}")
    
    # 逐列值差
    print(f"\n逐列值差 (E-C mod 16):")
    diffs = [(e_row[i] - c_row[i]) % 16 for i in range(16)]
    for i, d in enumerate(diffs):
        col = chr(ord('D') + i)
        print(f"  列{col}: {d}")
    
    # 检查是否存在模式
    unique_diffs = set(diffs)
    print(f"\n值差种类数: {len(unique_diffs)}")
    if len(unique_diffs) <= 5:
        print(f"★ 值差模式简单: {unique_diffs}")

# ============================================================================
# 主函数
# ============================================================================

def main():
    print("=" * 80)
    print("符闔數獨 V63: 验证解盘是否为符闔原题解")
    print("=" * 80)
    
    # 1. 对比txt文件
    comparison = compare_with_txt_final()
    
    # 2. 枚举所有解
    solutions, solution_count = enumerate_all_solutions()
    
    # 3. 分析特征
    if solutions:
        analyze_solution_features(solutions[0])
    
    # 总结
    print("\n" + "=" * 80)
    print("核心结论")
    print("=" * 80)
    
    print(f"""
关键发现：

1. C行匹配验证:
   - 与txt终局C191620: {'✓ 完全匹配' if comparison['matches_final'] else '✗ 不匹配'}
   - 与txt初始解盘C: {'✓ 匹配' if comparison['matches_initial'] else '✗ 不匹配'}
   - 与txt更新解盘C: {'✓ 匹配' if comparison['matches_update'] else '✗ 不匹配'}

2. 解的唯一性:
   - 总解数: {solution_count}
   - {'★ 唯一解！C191620 + 92锚点 + 数独三约束确定唯一解。' if solution_count == 1 else f'发现 {solution_count} 个解，解不唯一。'}

3. 是否为符闔原题解:
   {'✓ 是符闔原题解（C行与终局解盘完全匹配，且解唯一）' if comparison['matches_final'] and solution_count == 1 else '需要进一步验证符闔排列约束'}

下一步：
- 如果解唯一且C行匹配，验证符闔排列约束
- 如果解不唯一，需要符闔排列组闔约束来进一步压缩
""")

if __name__ == '__main__':
    main()
