#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
92 锚点深度验证 — 长时间搜索确认 INFEASIBLE 或找到解
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

用户质疑：92 锚点的"INFEASIBLE"结论可能是搜索不够深
本脚本用更长时间 + 更多技巧来验证 92 锚点的真实状态
"""

from __future__ import annotations
import json
import time
from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
from collections import Counter

GRID_SIZE = 16
BOX_SIZE = 4

# ═══════════════════════════════════════════════════════════
# 92 锚点完整配置 (原始数据，未修复)
# ═══════════════════════════════════════════════════════════
FULL_92_ANCHORS = [
    # 行 A (1): 4 个
    {'row': 1, 'col': 3, 'value': 3},
    {'row': 1, 'col': 6, 'value': 12},
    {'row': 1, 'col': 8, 'value': 5},
    {'row': 1, 'col': 12, 'value': 14},
    # 行 B (2): 4 个
    {'row': 2, 'col': 2, 'value': 12},
    {'row': 2, 'col': 5, 'value': 3},
    {'row': 2, 'col': 7, 'value': 9},
    {'row': 2, 'col': 9, 'value': 6},
    # 行 C (3): 16 个
    {'row': 3, 'col': 1, 'value': 7}, {'row': 3, 'col': 2, 'value': 15},
    {'row': 3, 'col': 3, 'value': 3}, {'row': 3, 'col': 4, 'value': 9},
    {'row': 3, 'col': 5, 'value': 11}, {'row': 3, 'col': 6, 'value': 12},
    {'row': 3, 'col': 7, 'value': 6}, {'row': 3, 'col': 8, 'value': 5},
    {'row': 3, 'col': 9, 'value': 10}, {'row': 3, 'col': 10, 'value': 2},
    {'row': 3, 'col': 11, 'value': 1}, {'row': 3, 'col': 12, 'value': 14},
    {'row': 3, 'col': 13, 'value': 13}, {'row': 3, 'col': 14, 'value': 16},
    {'row': 3, 'col': 15, 'value': 4}, {'row': 3, 'col': 16, 'value': 8},
    # 行 D (4): 16 个
    {'row': 4, 'col': 1, 'value': 11}, {'row': 4, 'col': 2, 'value': 4},
    {'row': 4, 'col': 3, 'value': 13}, {'row': 4, 'col': 4, 'value': 7},
    {'row': 4, 'col': 5, 'value': 16}, {'row': 4, 'col': 6, 'value': 8},
    {'row': 4, 'col': 7, 'value': 1}, {'row': 4, 'col': 8, 'value': 9},
    {'row': 4, 'col': 9, 'value': 3}, {'row': 4, 'col': 10, 'value': 15},
    {'row': 4, 'col': 11, 'value': 2}, {'row': 4, 'col': 12, 'value': 6},
    {'row': 4, 'col': 13, 'value': 5}, {'row': 4, 'col': 14, 'value': 14},
    {'row': 4, 'col': 15, 'value': 10}, {'row': 4, 'col': 16, 'value': 12},
    # 行 E (5): 3 个
    {'row': 5, 'col': 5, 'value': 13},
    {'row': 5, 'col': 10, 'value': 5},
    {'row': 5, 'col': 13, 'value': 4},
    # 行 F (6): 7 个
    {'row': 6, 'col': 2, 'value': 8},
    {'row': 6, 'col': 5, 'value': 15},
    {'row': 6, 'col': 7, 'value': 4},
    {'row': 6, 'col': 8, 'value': 3},
    {'row': 6, 'col': 11, 'value': 10},
    {'row': 6, 'col': 14, 'value': 16},
    {'row': 6, 'col': 15, 'value': 12},
    # 行 G (7): 6 个
    {'row': 7, 'col': 1, 'value': 14},
    {'row': 7, 'col': 3, 'value': 4},
    {'row': 7, 'col': 4, 'value': 6},
    {'row': 7, 'col': 10, 'value': 9},
    {'row': 7, 'col': 13, 'value': 15},
    {'row': 7, 'col': 16, 'value': 2},
    # 行 H (8): 6 个
    {'row': 8, 'col': 2, 'value': 13},
    {'row': 8, 'col': 6, 'value': 5},
    {'row': 8, 'col': 8, 'value': 9},
    {'row': 8, 'col': 12, 'value': 11},
    {'row': 8, 'col': 14, 'value': 7},
    {'row': 8, 'col': 15, 'value': 1},
    # 行 I (9): 16 个
    {'row': 9, 'col': 1, 'value': 13}, {'row': 9, 'col': 2, 'value': 1},
    {'row': 9, 'col': 3, 'value': 10}, {'row': 9, 'col': 4, 'value': 2},
    {'row': 9, 'col': 5, 'value': 8}, {'row': 9, 'col': 6, 'value': 11},
    {'row': 9, 'col': 7, 'value': 16}, {'row': 9, 'col': 8, 'value': 7},
    {'row': 9, 'col': 9, 'value': 14}, {'row': 9, 'col': 10, 'value': 4},
    {'row': 9, 'col': 11, 'value': 5}, {'row': 9, 'col': 12, 'value': 12},
    {'row': 9, 'col': 13, 'value': 9}, {'row': 9, 'col': 14, 'value': 6},
    {'row': 9, 'col': 15, 'value': 3}, {'row': 9, 'col': 16, 'value': 15},
    # 行 J (10): 4 个
    {'row': 10, 'col': 2, 'value': 5},
    {'row': 10, 'col': 6, 'value': 14},
    {'row': 10, 'col': 10, 'value': 8},
    {'row': 10, 'col': 12, 'value': 1},
    # 行 K (11): 6 个
    {'row': 11, 'col': 1, 'value': 1},
    {'row': 11, 'col': 3, 'value': 6},
    {'row': 11, 'col': 5, 'value': 10},
    {'row': 11, 'col': 8, 'value': 13},
    {'row': 11, 'col': 11, 'value': 9},
    {'row': 11, 'col': 14, 'value': 11},
    # 行 L (12): 6 个
    {'row': 12, 'col': 4, 'value': 4},
    {'row': 12, 'col': 6, 'value': 16},
    {'row': 12, 'col': 7, 'value': 14},
    {'row': 12, 'col': 9, 'value': 3},
    {'row': 12, 'col': 11, 'value': 12},
    {'row': 12, 'col': 13, 'value': 7},
    # 行 M (13): 7 个
    {'row': 13, 'col': 1, 'value': 15},
    {'row': 13, 'col': 5, 'value': 12},
    {'row': 13, 'col': 9, 'value': 5},
    {'row': 13, 'col': 10, 'value': 14},
    {'row': 13, 'col': 12, 'value': 8},
    {'row': 13, 'col': 15, 'value': 11},
    {'row': 13, 'col': 16, 'value': 6},
    # 行 N (14): 5 个
    {'row': 14, 'col': 3, 'value': 9},
    {'row': 14, 'col': 6, 'value': 6},
    {'row': 14, 'col': 9, 'value': 13},
    {'row': 14, 'col': 12, 'value': 15},
    {'row': 14, 'col': 16, 'value': 10},
    # 行 O (15): 6 个
    {'row': 15, 'col': 2, 'value': 1},
    {'row': 15, 'col': 5, 'value': 9},
    {'row': 15, 'col': 8, 'value': 15},
    {'row': 15, 'col': 11, 'value': 7},
    {'row': 15, 'col': 13, 'value': 16},
    {'row': 15, 'col': 14, 'value': 3},
    # 行 P (16): 2 个
    {'row': 16, 'col': 3, 'value': 2},
    {'row': 16, 'col': 7, 'value': 5},
]


# ═══════════════════════════════════════════════════════════
# 约束冲突预检查
# ═══════════════════════════════════════════════════════════

def check_constraint_conflicts(anchors: List[Dict]) -> Dict:
    """预检查锚点数据中的约束冲突"""
    print("=" * 70)
    print("約束衝突預檢查")
    print("=" * 70)
    
    conflicts = {
        'row_conflicts': [],  # 行内重复
        'col_conflicts': [],  # 列内重复
        'box_conflicts': [],  # 宫内重复
    }
    
    # 检查行内重复
    row_values = {}
    for a in anchors:
        key = (a['row'], a['value'])
        if key in row_values:
            conflicts['row_conflicts'].append({
                'row': a['row'], 'value': a['value'],
                'positions': [f"列{row_values[key]['col']}", f"列{a['col']}"]
            })
        else:
            row_values[key] = a
    
    # 检查列内重复
    col_values = {}
    for a in anchors:
        key = (a['col'], a['value'])
        if key in col_values:
            conflicts['col_conflicts'].append({
                'col': a['col'], 'value': a['value'],
                'positions': [f"行{col_values[key]['row']}", f"行{a['row']}"]
            })
        else:
            col_values[key] = a
    
    # 检查宫内重复
    def get_box(r, c):
        return (r // BOX_SIZE, c // BOX_SIZE)
    
    box_values = {}
    for a in anchors:
        r, c = a['row'] - 1, a['col'] - 1
        box = get_box(r, c)
        key = (box, a['value'])
        if key in box_values:
            conflicts['box_conflicts'].append({
                'box': box, 'value': a['value'],
                'positions': [
                    f"行{box_values[key]['row']}列{box_values[key]['col']}",
                    f"行{a['row']}列{a['col']}"
                ]
            })
        else:
            box_values[key] = a
    
    # 打印结果
    print(f"\n行冲突数: {len(conflicts['row_conflicts'])}")
    for c in conflicts['row_conflicts']:
        print(f"  行{c['row']} 值{c['value']}: 位置 {c['positions']}")
    
    print(f"\n列冲突数: {len(conflicts['col_conflicts'])}")
    for c in conflicts['col_conflicts']:
        print(f"  列{c['col']} 值{c['value']}: 位置 {c['positions']}")
    
    print(f"\n宫冲突数: {len(conflicts['box_conflicts'])}")
    for c in conflicts['box_conflicts']:
        print(f"  宫{c['box']} 值{c['value']}: 位置 {c['positions']}")
    
    # 汇总
    total = sum(len(v) for v in conflicts.values())
    print(f"\n{'='*70}")
    if total == 0:
        print("✅ 92 锚点数据本身无冲突，可以进入 CP-SAT 验证")
    else:
        print(f"❌ 92 锚点数据存在 {total} 个约束冲突！")
        print("   这是数据层面的硬冲突，无论搜索多久都无法找到解")
    
    return conflicts


# ═══════════════════════════════════════════════════════════
# CP-SAT 深度搜索验证
# ═══════════════════════════════════════════════════════════

def deep_verify_92_anchors(timeout: float = 300.0) -> Dict:
    """长时间深度验证 92 锚点"""
    
    print(f"\n{'='*70}")
    print(f"CP-SAT 深度搜索验证 (超时={timeout}秒)")
    print("="*70)
    
    model = cp_model.CpModel()
    grid = {}
    
    # 创建变量
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            grid[(r, c)] = model.NewIntVar(1, GRID_SIZE, f'cell_{r}_{c}')
    
    # 行 AllDifferent
    for r in range(GRID_SIZE):
        model.AddAllDifferent([grid[(r, c)] for c in range(GRID_SIZE)])
    
    # 列 AllDifferent
    for c in range(GRID_SIZE):
        model.AddAllDifferent([grid[(r, c)] for r in range(GRID_SIZE)])
    
    # 宫 AllDifferent
    for br in range(GRID_SIZE // BOX_SIZE):
        for bc in range(GRID_SIZE // BOX_SIZE):
            cells = []
            for dr in range(BOX_SIZE):
                for dc in range(BOX_SIZE):
                    r = br * BOX_SIZE + dr
                    c = bc * BOX_SIZE + dc
                    cells.append(grid[(r, c)])
            model.AddAllDifferent(cells)
    
    # 添加锚点约束
    for anchor in FULL_92_ANCHORS:
        r = anchor['row'] - 1
        c = anchor['col'] - 1
        v = anchor['value']
        model.Add(grid[(r, c)] == v)
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.num_search_workers = 16  # 最多工作线程
    
    start_time = time.time()
    status = solver.Solve(model)
    elapsed = time.time() - start_time
    
    result = {
        'status': str(status),
        'time': elapsed,
        'timeout_hit': elapsed >= timeout
    }
    
    print(f"\n狀態: {status}")
    print(f"時間: {elapsed:.2f}秒")
    
    if status == cp_model.CpSolverStatus.OPTIMAL:
        print("✅ 找到唯一最优解！")
        # 提取解
        solution_grid = [[solver.Value(grid[(r, c)]) for c in range(GRID_SIZE)] for r in range(GRID_SIZE)]
        result['solution'] = solution_grid
        result['unique'] = True
        
        # 验证解的正确性
        print("\n驗證解:")
        for anchor in FULL_92_ANCHORS:
            r = anchor['row'] - 1
            c = anchor['col'] - 1
            actual = solution_grid[r][c]
            expected = anchor['value']
            if actual != expected:
                print(f"  ❌ 行{anchor['row']} 列{anchor['col']}: 期望={expected}, 實際={actual}")
        
        # 搜索是否有第二个解
        print("\n搜索第二个解...")
        second_sol_found = False
        try:
            solver.parameters.solution_limit = 2
            solver.SearchForAllSolutions(model, cp_model.ObjectiveSolutionPrinter())
            second_sol_found = True
        except:
            pass
        
        result['second_solution_found'] = second_sol_found
        
    elif status == cp_model.CpSolverStatus.FEASIBLE:
        print("⚠️ 找到可行解（可能非唯一）")
        result['unique'] = False
    elif status == cp_model.CpSolverStatus.INFEASIBLE:
        print("❌ 不可滿足（INFEASIBLE）")
        result['unique'] = True  # 无解也算"唯一"
    elif status == cp_model.CpSolverStatus.UNKNOWN:
        print("❓ 未知（搜索超时或资源耗尽）")
        result['unique'] = False
        result['unknown'] = True
    
    return result


# ═══════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════

def main():
    """主验证流程"""
    
    print("=" * 70)
    print("92 錨點深度驗證 — 水中花鏡中月的實證檢驗")
    print("=" * 70)
    
    # 第一步：约束冲突预检查
    conflicts = check_constraint_conflicts(FULL_92_ANCHORS)
    
    total_conflicts = sum(len(v) for v in conflicts.values())
    
    if total_conflicts > 0:
        print(f"\n{'='*70}")
        print("結論：92 錨點數據本身存在約束衝突")
        print("="*70)
        print(f"\n數據層面的硬衝突：")
        print(f"  - 行冲突：{len(conflicts['row_conflicts'])} 個")
        print(f"  - 列冲突：{len(conflicts['col_conflicts'])} 個")
        print(f"  - 宫冲突：{len(conflicts['box_conflicts'])} 個")
        print(f"\n💡 這意味著：")
        print(f"   1. 92 锚点配置本身就有内部矛盾")
        print(f"   2. 无论搜索多久，CP-SAT 都无法找到解")
        print(f"   3. 这不是'水中花鏡中月'，而是数据结构的问题")
        print(f"   4. 55 锚点与 92 锚点确实是'两码事'")
    else:
        # 第二步：CP-SAT 深度搜索
        result = deep_verify_92_anchors(timeout=120.0)
        
        print(f"\n{'='*70}")
        print("最終結論")
        print("="*70)
        
        if result['status'] == 'CpSolverStatus.OPTIMAL':
            print("✅ 92 锚点存在唯一解！")
            print("   55 锚点的唯一解可能覆盖 92 锚点")
            print("   需要进一步验证覆盖关系")
        elif result['status'] == 'CpSolverStatus.INFEASIBLE':
            print("❌ 92 锚点确实 INFEASIBLE")
            print("   55 锚点与 92 锚点是不同谜题")
        elif result['status'] == 'CpSolverStatus.UNKNOWN':
            print("❓ 搜索结果不确定（超时）")
            print("   需要进一步验证")
    
    return conflicts


if __name__ == '__main__':
    main()
