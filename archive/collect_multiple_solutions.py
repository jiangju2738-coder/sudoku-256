#!/usr/bin/env python3
"""
符阖排列多解收集 - 验证解空间稀疏性
使用CP-SAT的SolutionCollector收集多个解
"""

from ortools.sat.python import cp_model
import json
import os

def collect_multiple_solutions():
    """使用CP-SAT收集多个符阖排列解"""
    print("=" * 70)
    print("符阖排列多解收集 - 验证解空间稀疏性")
    print("=" * 70)
    
    # 加载符阖排列数据
    permutations = {}
    base_dir = "D:/2026/WPF_Sudoku/Sudoku_256"
    
    for row_num in range(10, 17):
        filename = f"A{row_num}_permutations.json"
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                permutations[row_num] = json.load(f)
                print(f"✓ A{row_num}: {len(permutations[row_num]):,} 个符阖排列")
    
    # 生成A1-A9的符阖排列（简化版）
    import random
    random.seed(42)
    for row in range(1, 10):
        perms = []
        for _ in range(500):
            perm = list(range(1, 17))
            random.shuffle(perm)
            perms.append(perm)
        permutations[row] = perms
    
    print(f"\n开始CP-SAT多解收集...")
    
    # 创建模型
    model = cp_model.CpModel()
    
    # 创建变量
    cells = []
    for row in range(16):
        row_vars = []
        for col in range(16):
            row_num = row + 1
            if row_num in permutations:
                allowed_vals = set()
                for perm in permutations[row_num]:
                    allowed_vals.add(perm[col])
                allowed_list = sorted(allowed_vals)
            else:
                allowed_list = list(range(1, 17))
            
            var = model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(allowed_list),
                f'cell_{row}_{col}'
            )
            row_vars.append(var)
        cells.append(row_vars)
    
    # 约束：每行每列值唯一
    for row in range(16):
        model.AddAllDifferent(cells[row])
    
    for col in range(16):
        model.AddAllDifferent([cells[row][col] for row in range(16)])
    
    # 创建SolutionCollector
    collector = cp_model.CpSolver()
    
    # 配置求解器
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 8
    solver.parameters.log_search_progress = True
    solver.parameters.solution_limit = 100  # 最多收集100个解
    
    # 添加回调收集解
    solutions = []
    
    class SolutionCollector(cp_model.CpSolverSolutionCallback):
        def __init__(self, cells):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.cells = cells
            self.solutions = []
        
        def OnSolutionCallback(self):
            sol = []
            for row in range(16):
                row_vals = [self.Value(self.cells[r][c]) for c in range(16)]
                sol.append(row_vals)
            self.solutions.append(sol)
            print(f"  解 #{len(self.solutions)}: 第1行 = {sol[0][:8]}...")
    
    collector = SolutionCollector(cells)
    
    start_time = __import__('time').time()
    status = solver.Solve(model, collector)
    elapsed = __import__('time').time() - start_time
    
    print(f"\n求解完成！")
    print(f"  耗时: {elapsed:.1f}秒")
    print(f"  找到解数: {len(collector.solutions)}")
    print(f"  状态: {status}")
    
    if len(collector.solutions) > 0:
        print(f"\n解的空间分析:")
        print(f"  平均每10^({elapsed/len(collector.solutions):.2f})秒找到一个解")
        
        # 分析解的多样性
        if len(collector.solutions) >= 2:
            first_sol = collector.solutions[0]
            second_sol = collector.solutions[1]
            
            diff_count = 0
            for r in range(16):
                for c in range(16):
                    if first_sol[r][c] != second_sol[r][c]:
                        diff_count += 1
            
            print(f"  解1和解2的差异单元格数: {diff_count}/256 ({diff_count/256*100:.1f}%)")
    
    # 保存解
    if len(collector.solutions) > 0:
        output_file = "fuhh_solutions.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'num_solutions': len(collector.solutions),
                'elapsed_seconds': elapsed,
                'solutions': collector.solutions[:5]  # 保存前5个
            }, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 解已保存到: {output_file}")
    
    return collector.solutions


if __name__ == '__main__':
    solutions = collect_multiple_solutions()
    
    print("\n" + "=" * 70)
    print("多解收集完成")
    print("=" * 70)
    
    if len(solutions) == 0:
        print("\n⚠️ 警告：未找到多个解，解空间可能确实极度稀疏")
    elif len(solutions) < 10:
        print(f"\n⚠️ 仅找到{len(solutions)}个解，解空间较为稀疏")
    else:
        print(f"\n✓ 找到{len(solutions)}个解，解空间密度可接受")
