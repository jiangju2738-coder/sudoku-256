#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔數獨 V63: CP-SAT在压缩空间中搜索完整解

任务4：在压缩空间中搜索256数独完整解

配置：
- C行：C191620（完全固定）
- E行：3个锚点固定，13个位置搜索
- 92锚点：全部固定
- 符闔排列约束：从backup_fuyi/加载
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from ortools.sat.python import cp_model
from collections import defaultdict
import json
import time

# ============================================================================
# 常数定义
# ============================================================================

GRID_SIZE = 16
BOX_SIZE = 4

# 列映射
col_letter_to_idx = {
    'D': 0, 'E': 1, 'F': 2, 'G': 3,
    'H': 4, 'I': 5, 'J': 6, 'K': 7,
    'L': 8, 'M': 9, 'N': 10, 'O': 11,
    'P': 12, 'Q': 13, 'R': 14, 'S': 15,
}

idx_to_col_letter = {v: k for k, v in col_letter_to_idx.items()}

row_letter_to_idx = {
    'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5,
    'G': 6, 'H': 7, 'I': 8, 'J': 9, 'K': 10, 'L': 11,
    'M': 12, 'N': 13, 'O': 14, 'P': 15,
}

idx_to_row_letter = {v: k for k, v in row_letter_to_idx.items()}

# ============================================================================
# C191620 和 锚点定义
# ============================================================================

# C191620 (终局解盘C行)
C191620 = [7,10,14,15, 4,2,16,8, 12,13,3,1, 11,9,6,5]

# 92锚点
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
    """构建92锚点网格"""
    anchors = {}
    for value, positions in anchors_by_value.items():
        for pos in positions:
            row = row_letter_to_idx[pos[0]]
            col = col_letter_to_idx[pos[1]]
            anchors[(row, col)] = value
    return anchors

# ============================================================================
# CP-SAT求解器
# ============================================================================

def solve_compressed():
    """在压缩空间中搜索完整解"""
    print("=" * 80)
    print("符闔數獨 V63: CP-SAT在压缩空间中搜索完整解")
    print("=" * 80)
    
    start_time = time.time()
    
    # 创建模型
    model = cp_model.CpModel()
    
    # 创建变量
    grid = {}
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            grid[(r, c)] = model.NewIntVar(1, GRID_SIZE, f'cell_{r}_{c}')
    
    # 1. 添加C行约束（C191620完全固定）
    print("\n步骤1: 添加C行约束（C191620）")
    c_row_idx = row_letter_to_idx['C']
    for c, val in enumerate(C191620):
        model.Add(grid[(c_row_idx, c)] == val)
    print(f"  C行已固定: {C191620}")
    
    # 2. 添加92锚点约束
    print("\n步骤2: 添加92锚点约束")
    anchors = build_anchors_grid()
    
    # 检查C行锚点是否与C191620一致
    c_anchors_conflicts = []
    for (r, c), val in anchors.items():
        if r == c_row_idx:
            if C191620[c] != val:
                c_anchors_conflicts.append(f"C-{idx_to_col_letter[c]}: 期望={val}, C191620={C191620[c]}")
    
    if c_anchors_conflicts:
        print(f"  ✗ C行锚点冲突:")
        for conflict in c_anchors_conflicts:
            print(f"    {conflict}")
    else:
        print(f"  ✓ C行锚点与C191620一致")
    
    # 添加所有锚点（跳过C行，已固定）
    anchor_count = 0
    for (r, c), val in anchors.items():
        if r != c_row_idx:  # C行已固定
            model.Add(grid[(r, c)] == val)
            anchor_count += 1
    
    print(f"  添加锚点: {anchor_count}个（C行{len([a for a in anchors.keys() if a[0]==c_row_idx])}个已跳过）")
    
    # 3. 添加数独三约束
    print("\n步骤3: 添加数独三约束")
    
    # 行约束
    for r in range(GRID_SIZE):
        model.AddAllDifferent([grid[(r, c)] for c in range(GRID_SIZE)])
    print(f"  行约束: {GRID_SIZE}行")
    
    # 列约束
    for c in range(GRID_SIZE):
        model.AddAllDifferent([grid[(r, c)] for r in range(GRID_SIZE)])
    print(f"  列约束: {GRID_SIZE}列")
    
    # 宫约束
    for box_r in range(BOX_SIZE):
        for box_c in range(BOX_SIZE):
            cells = []
            for dr in range(BOX_SIZE):
                for dc in range(BOX_SIZE):
                    r = box_r * BOX_SIZE + dr
                    c = box_c * BOX_SIZE + dc
                    cells.append(grid[(r, c)])
            model.AddAllDifferent(cells)
    print(f"  宫约束: {BOX_SIZE*BOX_SIZE}个宫")
    
    # 4. 设置求解参数
    print("\n步骤4: 设置求解参数")
    
    # 5. 求解
    print("\n步骤5: 开始求解...")
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 8
    solver.parameters.max_time_in_seconds = 120
    
    print("  求解中，请稍候...")
    status = solver.Solve(model)
    
    elapsed_time = time.time() - start_time
    
    # 6. 输出结果
    print("\n" + "=" * 80)
    print("求解结果")
    print("=" * 80)
    
    print(f"\n状态: {solver.StatusName(status)}")
    print(f"耗时: {elapsed_time:.2f}秒")
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"\n找到解！")
        
        # 输出完整解盘
        solution = []
        for r in range(GRID_SIZE):
            row = []
            for c in range(GRID_SIZE):
                row.append(solver.Value(grid[(r, c)]))
            solution.append(row)
        
        # 按字母格式输出
        print("\n完整解盘:")
        for r in range(GRID_SIZE):
            row_letter = idx_to_row_letter[r]
            row_vals = solution[r]
            # 每4个一组
            groups = [row_vals[i:i+4] for i in range(0, 16, 4)]
            group_str = ' '.join(str(g) for g in groups)
            print(f"  行{row_letter} {group_str}")
        
        # 验证C行
        print(f"\nC行验证:")
        actual_c = solution[c_row_idx]
        print(f"  实际C行: {actual_c}")
        print(f"  C191620: {C191620}")
        match = actual_c == C191620
        print(f"  匹配: {'✓' if match else '✗'}")
        
        # 验证E行锚点
        print(f"\nE行锚点验证:")
        e_row_idx = row_letter_to_idx['E']
        e_anchors = [(4, 'H', 13), (9, 'M', 5), (12, 'P', 4)]
        for col_idx, col_letter, expected in e_anchors:
            actual = solution[e_row_idx][col_idx]
            match = actual == expected
            print(f"  E-{col_letter}: 期望={expected}, 实际={actual} {'✓' if match else '✗'}")
        
        # 保存解盘
        solution_data = {
            'C191620': C191620,
            'solution': solution,
            'elapsed_time': elapsed_time,
        }
        
        with open('solution_compressed_search.json', 'w', encoding='utf-8') as f:
            json.dump(solution_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n解盘已保存到: solution_compressed_search.json")
        
        return solution
    
    elif status == cp_model.INFEASIBLE:
        print(f"\n无解！")
        print(f"这表明C191620与92锚点约束存在冲突。")
        return None
    
    else:
        print(f"\n求解超时或未知状态")
        return None

def verify_solution(solution):
    """验证解盘"""
    print("\n" + "=" * 80)
    print("解盘验证")
    print("=" * 80)
    
    if solution is None:
        print("无解盘可验证")
        return
    
    errors = []
    
    # 验证行约束
    for r in range(GRID_SIZE):
        row_vals = solution[r]
        if len(set(row_vals)) != GRID_SIZE:
            errors.append(f"行{idx_to_row_letter[r]}: 有重复值")
        if set(row_vals) != set(range(1, GRID_SIZE+1)):
            errors.append(f"行{idx_to_row_letter[r]}: 不是1-{GRID_SIZE}的排列")
    
    # 验证列约束
    for c in range(GRID_SIZE):
        col_vals = [solution[r][c] for r in range(GRID_SIZE)]
        if len(set(col_vals)) != GRID_SIZE:
            errors.append(f"列{idx_to_col_letter[c]}: 有重复值")
        if set(col_vals) != set(range(1, GRID_SIZE+1)):
            errors.append(f"列{idx_to_col_letter[c]}: 不是1-{GRID_SIZE}的排列")
    
    # 验证宫约束
    for box_r in range(BOX_SIZE):
        for box_c in range(BOX_SIZE):
            cells = []
            for dr in range(BOX_SIZE):
                for dc in range(BOX_SIZE):
                    r = box_r * BOX_SIZE + dr
                    c = box_c * BOX_SIZE + dc
                    cells.append(solution[r][c])
            if len(set(cells)) != GRID_SIZE:
                errors.append(f"宫({box_r},{box_c}): 有重复值")
    
    # 验证92锚点
    anchors = build_anchors_grid()
    for (r, c), expected in anchors.items():
        actual = solution[r][c]
        if actual != expected:
            errors.append(f"锚点{idx_to_row_letter[r]}{idx_to_col_letter[c]}: 期望={expected}, 实际={actual}")
    
    # 验证C行
    c_row_idx = row_letter_to_idx['C']
    if solution[c_row_idx] != C191620:
        errors.append(f"C行不匹配C191620")
    
    if errors:
        print(f"\n发现{len(errors)}个错误:")
        for e in errors[:20]:
            print(f"  {e}")
    else:
        print(f"\n✓ 所有验证通过！")

# ============================================================================
# 主函数
# ============================================================================

def main():
    solution = solve_compressed()
    
    if solution:
        verify_solution(solution)
    
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    
    print("""
关键发现：

1. C行完全固定（C191620）
2. 92锚点全部添加
3. 数独三约束完整
4. 在压缩空间中搜索完整解

下一步：
- 如果找到解，验证是否为符闔原题解
- 如果无解，分析冲突原因
- 尝试枚举所有解，验证唯一性
""")

if __name__ == '__main__':
    main()
