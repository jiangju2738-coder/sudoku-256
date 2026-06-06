#!/usr/bin/env python3
"""
验证：符阖行约束 + 列约束 + 宫约束 的交集是否非空
关键：仅施加这三者约束，不加已知数字，证明存在至少一个解
"""

import json
from ortools.sat.python import cp_model
from collections import defaultdict
import time

# ========== 加载符阖排列数据 ==========
def load_fuhh_permutations():
    """加载所有符阖排列数据"""
    fuhh = {}
    for row in range(1, 17):
        with open(f'A{row}_permutations.json', 'r', encoding='utf-8') as f:
            fuhh[row] = json.load(f)
        print(f"行 {row}: {len(fuhh[row])} 个符阖排列")
    return fuhh

# ========== 验证模型 ==========
def verify_three_constraints(fuhh_permutations):
    """验证符阖 + 列 + 宫约束的交集"""
    
    print("\n" + "="*60)
    print("  验证：符阖行约束 + 列约束 + 宫约束 交集非空")
    print("="*60)
    
    # 创建模型
    model = cp_model.CpModel()
    
    # 变量定义：16x16 网格，值域 1-16
    cells = {}
    for r in range(16):
        for c in range(16):
            cells[(r, c)] = model.NewIntVar(1, 16, f'cell_{r}_{c}')
    
    # ===== 1. 符阖行约束 =====
    # 每行必须是预定义的符阖排列之一
    for r in range(16):
        row_var = [cells[(r, c)] for c in range(16)]
        perms = fuhh_permutations[r+1]
        
        # 使用线性化方式：行必须是其中一个排列
        # 方法：为每个排列创建布尔变量，恰好一个为真
        is_perm = [model.NewBoolVar(f'row_{r}_perm_{i}') for i in range(len(perms))]
        
        # 恰好一个排列被选择
        model.AddExactlyOne(is_perm)
        
        # 每个单元格值等于被选排列的对应位置值
        for c in range(16):
            # cell[r,c] = sum(perm[c] * is_perm[i]) for all i
            model.Add(row_var[c] == sum(perms[i][c] * is_perm[i] for i in range(len(perms))))
        
        if (r+1) % 4 == 0:
            print(f"  ✓ 行 {r+1} 符阖约束已添加 ({len(perms)} 个排列选项)")
    
    print(f"  符阖约束总数: {16*len(fuhh_permutations[1])} 个排列组合搜索空间")
    
    # ===== 2. 列 AllDifferent 约束 =====
    for c in range(16):
        col_vars = [cells[(r, c)] for r in range(16)]
        model.AddAllDifferent(col_vars)
    print(f"  ✓ 列约束已添加: 16 列 AllDifferent")
    
    # ===== 3. 宫 AllDifferent 约束 =====
    box_size = 4
    for br in range(box_size):
        for bc in range(box_size):
            box_vars = []
            for r in range(br * box_size, (br + 1) * box_size):
                for c in range(bc * box_size, (bc + 1) * box_size):
                    box_vars.append(cells[(r, c)])
            model.AddAllDifferent(box_vars)
    print(f"  ✓ 宫约束已添加: {box_size*box_size} 个宫 AllDifferent")
    
    # ===== 求解 =====
    print("\n" + "-"*60)
    print("  开始求解...")
    print("-"*60)
    
    solver = cp_model.CpSolver()
    
    # 配置求解器
    solver.parameters.max_time_in_seconds = 300.0  # 5 分钟超时
    solver.parameters.num_search_workers = 8
    solver.parameters.log_search_progress = True
    
    start_time = time.time()
    status = solver.Solve(model)
    elapsed = time.time() - start_time
    
    print(f"\n  求解时间: {elapsed:.2f} 秒")
    print(f"  求解状态: {cp_model.CpSolver.StatusName(status)}")
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("\n" + "="*60)
        print("  ✓✓✓ 验证成功！三者交集非空 ✓✓✓")
        print("="*60)
        
        # 输出部分解
        print("\n  解示例（前 4 行）:")
        for r in range(4):
            row_vals = [solver.Value(cells[(r, c)]) for c in range(16)]
            print(f"    行 {r+1}: {row_vals}")
        
        # 验证符阖排列一致性
        print("\n  符阖排列验证:")
        for r in range(4):
            row_vals = [solver.Value(cells[(r, c)]) for c in range(16)]
            is_valid = row_vals in fuhh_permutations[r+1]
            print(f"    行 {r+1}: {'✓ 符阖排列一致' if is_valid else '✗ 不符合'}")
        
        return True, solver, model
    else:
        print("\n" + "="*60)
        print("  ✗ 验证失败：三者交集可能为空")
        print("="*60)
        return False, solver, model

# ========== 主程序 ==========
if __name__ == '__main__':
    print("正在加载符阖排列数据...")
    fuhh = load_fuhh_permutations()
    
    success, solver, model = verify_three_constraints(fuhh)
    
    if success:
        print("\n🎉 理论验证完成：符阖+列+宫 三者交集非空！")
    else:
        print("\n⚠️ 需要进一步分析...")
