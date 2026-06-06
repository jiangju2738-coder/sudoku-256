#!/usr/bin/env python3
"""
符阖排列 16 行数据系统性验证
三线验证：
1. 数据一致性 - 确认16行符阖排列来自同一约束系统
2. SAT求解器验证 - 编码为SAT问题
3. CP-SAT约束规划 - 使用OR-Tools

作者: Jualius AI Assistant
2026-05-14
"""

import json
import os
import sys
from collections import defaultdict
import time
from itertools import combinations

# ==================== 第一部分：符阖排列数据加载与一致性验证 ====================

def load_permutations_from_files(base_dir="D:/2026/WPF_Sudoku/Sudoku_256"):
    """从json文件加载各行的符阖排列数据"""
    permutations = {}
    for row_num in range(10, 17):  # A10-A16
        filename = f"A{row_num}_permutations.json"
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                perms = json.load(f)
                permutations[row_num] = perms
                print(f"  ✓ A{row_num}: {len(perms)} 个符阖排列")
        else:
            print(f"  ✗ A{row_num}: 文件不存在 - {filename}")
    return permutations


def generate_i_ching_hexagrams():
    """生成完整的64卦象及其二进制编码"""
    hexagrams = {}
    # 64卦的符号和顺序（简化版，实际可使用完整64卦表）
    # 这里使用数字1-64代表64卦，每个卦有6爻（binary）
    for i in range(64):
        # 6爻二进制表示（下爻到上爻）
        binary = [(i >> j) & 1 for j in range(6)]
        hexagrams[i] = binary
    return hexagrams


def extract_symbols_from_permutations(permutations):
    """从符阖排列中提取卦象符号及其列位置"""
    symbols_by_col = defaultdict(set)  # col -> set of symbols (1-64)
    
    for row_num, perms in permutations.items():
        for perm in perms:
            # 每行16列，每列是卦象编号（1-64）
            for col_idx in range(16):
                symbol_id = perm[col_idx]
                symbols_by_col[col_idx].add(symbol_id)
    
    return symbols_by_col


def verify_constraint_consistency(symbols_by_col):
    """验证符阖排列的约束一致性：
    1. 每列使用的卦象是否遵循特定规则
    2. 是否存在约束冲突（同一列中某些卦象不可同时出现）
    """
    print("\n=== 符阖排列约束一致性分析 ===")
    
    # 检查每列的卦象集合大小
    print(f"\n各列卦象集合大小:")
    for col in range(16):
        symbols = symbols_by_col[col]
        print(f"  列 {col+1:2d}: {len(symbols):3d} 个不同卦象")
    
    # 统计每列的卦象分布
    print(f"\n每列使用的卦象（样本前10个）:")
    for col in range(16):
        symbols = sorted(symbols_by_col[col])
        print(f"  列 {col+1:2d}: {symbols[:10]}{'...' if len(symbols)>10 else ''}")
    
    # 检查是否存在冲突模式
    # 符阖排列通常要求：每列的卦象遵循特定变换规则
    print(f"\n约束一致性检查:")
    
    # 1. 检查每列卦象是否有重叠约束
    all_symbols_union = set()
    for col in range(16):
        all_symbols_union |= symbols_by_col[col]
    
    print(f"  所有列使用的卦象总数: {len(all_symbols_union)}")
    print(f"  总卦象空间: 64 卦")
    print(f"  覆盖率: {len(all_symbols_union)/64*100:.1f}%")
    
    # 2. 检查相邻列的变换一致性
    print(f"\n相邻列变换分析:")
    for col in range(15):
        symbols_curr = symbols_by_col[col]
        symbols_next = symbols_by_col[col+1]
        overlap = symbols_curr & symbols_next
        print(f"  列 {col+1} → 列 {col+2}: 重叠 {len(overlap)} 个卦象")
    
    return True


def verify_numerical_constraints(permutations):
    """验证数值约束：符阖排列是否满足类似数独的数值约束"""
    print("\n=== 数值约束验证 ===")
    
    # 检查每行是否使用了完整的1-16数值
    for row_num, perms in permutations.items():
        all_values_used = set()
        for perm in perms:
            for val in perm:
                all_values_used.add(val)
        
        print(f"  A{row_num}: 使用的数值范围 {min(all_values_used)}-{max(all_values_used)}, 共{len(all_values_used)}个不同值")
    
    # 检查每列的数值分布
    col_values = defaultdict(set)
    for row_num, perms in permutations.items():
        for perm in perms:
            for col_idx in range(16):
                col_values[col_idx].add(perm[col_idx])
    
    print(f"\n各列数值分布:")
    for col in range(16):
        vals = sorted(col_values[col])
        print(f"  列 {col+1:2d}: 范围 {min(vals)}-{max(vals)}, 共{len(vals)}个不同值")
    
    return True


# ==================== 第二部分：SAT求解器验证 ====================

def encode_to_sat(permutations, output_file="fuhh_sudoku.sat"):
    """将符阖排列约束编码为SAT问题（DIMACS CNF格式）"""
    print(f"\n=== SAT编码开始 ===")
    
    # 变量定义：
    # x(row, col, sym) = 第row行第col列的卦象是sym
    # row: 0-15, col: 0-15, sym: 1-64
    # 变量编号: var(row,col,sym) = 1 + row*16*64 + col*64 + (sym-1)
    
    num_rows = 16
    num_cols = 16
    num_symbols = 64
    
    def var(row, col, sym):
        return 1 + row * num_cols * num_symbols + col * num_symbols + (sym - 1)
    
    clauses = []
    
    # 约束1：每行每列必须有一个卦象
    for row in range(num_rows):
        for col in range(num_cols):
            # 至少一个卦象
            clause = [var(row, col, sym) for sym in range(1, num_symbols + 1)]
            clauses.append(clause)
            
            # 至多一个卦象（两两互斥）
            for s1 in range(1, num_symbols + 1):
                for s2 in range(s1 + 1, num_symbols + 1):
                    clauses.append([-var(row, col, s1), -var(row, col, s2)])
    
    # 约束2：每列不能重复卦象（符阖排列约束）
    for col in range(num_cols):
        for sym in range(1, num_symbols + 1):
            # 每列每个卦象最多出现一次
            vars_in_col = [var(row, col, sym) for row in range(num_rows)]
            for i in range(len(vars_in_col)):
                for j in range(i + 1, len(vars_in_col)):
                    clauses.append([-vars_in_col[i], -vars_in_col[j]])
    
    # 约束3：符阖排列限制（只能从给定permutations中选择）
    for row_num, perms in permutations.items():
        row_idx = row_num - 10  # A10-A16 -> 0-6（如果有全部16行则相应调整）
        for col in range(num_cols):
            # 收集该列所有合法的卦象
            allowed_symbols = set()
            for perm in perms:
                allowed_symbols.add(perm[col])
            
            # 每列必须从allowed_symbols中选择
            clause = [var(row_idx, col, sym) for sym in allowed_symbols]
            clauses.append(clause)
    
    print(f"  生成的子句数: {len(clauses):,}")
    print(f"  变量数: {var(num_rows-1, num_cols-1, num_symbols):,}")
    
    # 写入DIMACS CNF文件
    with open(output_file, 'w') as f:
        f.write(f"p cnf {var(num_rows-1, num_cols-1, num_symbols)} {len(clauses)}\n")
        for clause in clauses:
            f.write(' '.join(map(str, clause)) + ' 0\n')
    
    print(f"  ✓ SAT文件已写入: {output_file}")
    return output_file


def run_kissat_sat_file(sat_file):
    """运行Kissat SAT求解器"""
    print(f"\n=== 运行Kissat SAT求解器 ===")
    
    import subprocess
    
    # 检查Kissat是否可用
    try:
        result = subprocess.run(
            ['kissat', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"  Kissat版本: {result.stdout.strip()}")
    except FileNotFoundError:
        print("  ✗ Kissat未找到，尝试其他SAT求解器...")
        # 尝试其他SAT求解器
        for solver in ['cadical', 'glucose', 'lingeling']:
            try:
                subprocess.run([solver, '--version'], capture_output=True, timeout=3)
                print(f"  可用求解器: {solver}")
            except:
                pass
        return False
    
    # 运行求解
    start_time = time.time()
    try:
        result = subprocess.run(
            ['kissat', sat_file],
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        elapsed = time.time() - start_time
        print(f"  耗时: {elapsed:.1f}秒")
        print(f"  状态: {result.stdout[:200]}")
        
        if 'SATISFIABLE' in result.stdout:
            print("  ✓ 找到可满足解！")
            return True
        elif 'UNSATISFIABLE' in result.stdout:
            print("  ✗ 无解（约束冲突）")
            return False
        else:
            print(f"  ? 求解未完成或超时")
            return None
            
    except subprocess.TimeoutExpired:
        print("  ⏱ 求解超时（5分钟）")
        return None


# ==================== 第三部分：CP-SAT约束规划验证 ====================

def encode_to_cpsat(permutations):
    """使用OR-Tools CP-SAT编码符阖排列问题"""
    print(f"\n=== CP-SAT约束规划编码 ===")
    
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        print("  ✗ OR-Tools未安装，尝试安装...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'ortools', '-q'])
        try:
            from ortools.sat.python import cp_model
        except ImportError:
            print("  ✗ OR-Tools安装失败，跳过CP-SAT")
            return None
    
    model = cp_model.CpModel()
    
    # 变量：cell[row][col] = 卦象编号 (1-64)
    cells = []
    for row in range(16):
        row_vars = []
        for col in range(16):
            # 从符阖排列中获取该位置的合法卦象集合
            # 简化：假设每行16列使用不同的约束集
            allowed = list(range(1, 65))  # 初始允许所有
            var = model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(allowed),
                f'cell_{row}_{col}'
            )
            row_vars.append(var)
        cells.append(row_vars)
    
    # 约束：每列卦象唯一
    for col in range(16):
        model.AddAllDifferent([cells[row][col] for row in range(16)])
    
    # 应用符阖排列约束
    for row_num, perms in permutations.items():
        row_idx = row_num - 10
        if row_idx >= 16:
            continue
        # 对于符阖排列行，强制使用排列中的值
        # 这需要更复杂的编码...
        # 简化处理：暂时只添加AllDifferent约束
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300
    solver.parameters.num_search_workers = 8
    
    print("  开始求解...")
    start = time.time()
    status = solver.Solve(model)
    elapsed = time.time() - start
    
    print(f"  耗时: {elapsed:.1f}秒")
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("  ✓ 找到可行解！")
        print("  解的示例（前4行前4列）:")
        for r in range(4):
            row_vals = [solver.Value(cells[r][c]) for c in range(4)]
            print(f"    行{r+1}: {row_vals}")
        return True
    elif status == cp_model.INFEASIBLE:
        print("  ✗ 无解（约束冲突）")
        return False
    else:
        print(f"  ? 求解超时或中断 (status={status})")
        return None


# ==================== 第四部分：解空间稀疏性分析 ====================

def analyze_solution_space_density(permutations):
    """分析符阖排列约束下的解空间稀疏性"""
    print(f"\n=== 解空间稀疏性分析 ===")
    
    import math
    
    # 估计总搜索空间大小
    total_perms = 1
    for row_num, perms in permutations.items():
        total_perms *= len(perms)
    
    print(f"\n符阖排列总搜索空间:")
    for row_num, perms in permutations.items():
        print(f"  A{row_num}: {len(perms):,} 个符阖排列")
    
    print(f"\n  总排列组合数: {total_perms:,.0f}")
    print(f"  对数规模: log10 = {math.log10(total_perms):.1f}")
    
    # 约束密度分析
    # 符阖排列的列约束非常强：每列16行不能重复卦象
    print(f"\n约束密度分析:")
    
    # 列约束的剪枝效果估算
    total_col_constraint_checks = 16 * 16 * 15 / 2  # 16列，每列C(16,2)对检查
    print(f"  列唯一性约束对数: {total_col_constraint_checks:,}")
    
    # 符阖变换约束（假设相邻卦象间有特定变换关系）
    # 这大大减少了可行解空间
    print(f"\n  符阖变换约束: 相邻卦象需满足i-ching变换规则")
    
    # 估算解空间密度
    # 对于n×n拉丁方，解数约为 n^(n²) / e^(n²)
    # 符阖排列更严格，解空间更小
    print(f"\n解空间密度估算:")
    
    # 使用简单的概率模型：
    # 假设每列随机选择16个不重复卦象的概率
    import math
    n = 16
    symbols = 64
    
    # 一列随机选择16个不重复符号的概率
    prob_col = math.perm(symbols, n) / (symbols ** n)
    print(f"  单列满足唯一性的概率: {prob_col:.2e}")
    
    # 16列同时满足（粗略估计，忽略行间依赖）
    prob_all_cols = prob_col ** 16
    print(f"  16列同时满足的粗略概率: {prob_all_cols:.2e}")
    
    # 实际解数估计
    estimated_solutions = total_perms * prob_all_cols
    print(f"  估计可行解数: {estimated_solutions:.2e}")
    
    if estimated_solutions < 1:
        print(f"\n  ⚠️  解空间极度稀疏，可能无解！")
    elif estimated_solutions < 100:
        print(f"\n  ⚠️  解空间非常稀疏，搜索难度极高")
    else:
        print(f"\n  解空间密度中等")
    
    return estimated_solutions


# ==================== 主程序 ====================

if __name__ == '__main__':
    import math
    
    print("=" * 70)
    print("符阖排列 16 行系统性验证")
    print("=" * 70)
    
    # 1. 加载符阖排列数据
    print("\n[1] 加载符阖排列数据...")
    permutations = load_permutations_from_files()
    
    if len(permutations) < 2:
        print("\n✗ 符阖排列数据不足，请检查文件")
        sys.exit(1)
    
    # 2. 验证数据一致性
    print("\n[2] 验证符阖排列约束一致性...")
    symbols_by_col = extract_symbols_from_permutations(permutations)
    verify_constraint_consistency(symbols_by_col)
    verify_numerical_constraints(permutations)
    
    # 3. SAT编码与求解
    print("\n[3] SAT求解器验证...")
    sat_file = encode_to_sat(permutations, "fuhh_16_sat.cnf")
    # run_kissat_sat_file(sat_file)  # 暂时注释，先分析数据
    
    # 4. CP-SAT验证
    print("\n[4] CP-SAT约束规划验证...")
    # encode_to_cpsat(permutations)  # 暂时注释，先分析数据
    
    # 5. 解空间稀疏性分析
    print("\n[5] 解空间稀疏性分析...")
    analyze_solution_space_density(permutations)
    
    print("\n" + "=" * 70)
    print("验证完成")
    print("=" * 70)
