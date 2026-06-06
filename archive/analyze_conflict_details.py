#!/usr/bin/env python3
"""
深度分析冲突行的数字位置映射关系
检查是否存在位置错位、数据版本不一致等问题
"""

import json
import os

WORK_DIR = r"D:\2026\WPF_Sudoku\Sudoku_256"

# 冲突行分析
CONFLICT_ROWS = [1, 6, 12, 13, 16]

# 初始盘数据
INITIAL_PUZZLE = [
    [0, 0, 3, 0, 0, 12, 0, 5, 0, 0, 0, 14, 0, 16, 0, 8],      # 第1行 A1
    [0, 12, 0, 0, 3, 0, 9, 0, 6, 0, 5, 4, 2, 0, 1, 0],      # 第2行 A2
    [0, 0, 14, 0, 0, 2, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0],      # 第3行 A3
    [0, 4, 0, 13, 7, 0, 1, 0, 0, 0, 0, 11, 0, 12, 0, 0],    # 第4行 A4
    [0, 0, 0, 0, 13, 0, 0, 0, 0, 5, 0, 0, 4, 0, 0, 0],      # 第5行 A5
    [0, 8, 0, 0, 15, 0, 4, 3, 0, 9, 0, 0, 0, 13, 0, 12],    # 第6行 A6
    [14, 0, 4, 6, 0, 0, 12, 0, 2, 0, 0, 0, 0, 3, 0, 0],    # 第7行 A7
    [0, 13, 0, 0, 0, 5, 0, 9, 0, 0, 14, 6, 0, 0, 16, 0],    # 第8行 A8
    [13, 0, 0, 2, 0, 11, 0, 0, 14, 0, 0, 7, 0, 15, 0, 3],    # 第9行 A9
    [0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 8, 0, 7, 0],      # 第10行 A10
    [1, 0, 6, 0, 5, 0, 0, 2, 0, 3, 0, 0, 9, 0, 0, 0],      # 第11行 A11
    [0, 0, 0, 4, 0, 16, 14, 0, 0, 0, 12, 5, 0, 0, 0, 1],    # 第12行 A12
    [15, 0, 0, 0, 12, 0, 0, 0, 5, 1, 0, 3, 0, 6, 0, 7],    # 第13行 A13
    [0, 0, 9, 0, 0, 6, 0, 0, 13, 0, 0, 15, 0, 0, 3, 0],    # 第14行 A14
    [0, 1, 0, 0, 9, 0, 0, 15, 0, 0, 2, 8, 0, 5, 0, 0],    # 第15行 A15
    [0, 0, 2, 0, 0, 0, 5, 0, 0, 14, 0, 0, 1, 0, 10, 15]    # 第16行 A16
]

def load_permutations(row_num):
    filename = f"A{row_num}_permutations.json"
    filepath = os.path.join(WORK_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_conflict_row(row_idx, row_num):
    """深度分析冲突行"""
    print(f"\n{'='*70}")
    print(f"【深度分析】第{row_num}行 (A{row_num})")
    print('='*70)
    
    row_data = INITIAL_PUZZLE[row_idx]
    permutations = load_permutations(row_num)
    
    # 1. 显示行数据
    print(f"\n1. 初始盘第{row_num}行数据:")
    print(f"   位置: {[i+1 for i in range(16)]}")
    print(f"   值:   {row_data}")
    
    known_positions = [(i+1, v) for i, v in enumerate(row_data) if v != 0]
    print(f"\n   已知数字位置: {known_positions}")
    
    # 2. 检查是否存在位置偏移
    print(f"\n2. 检查位置偏移可能性:")
    
    # 收集所有非零数字的出现位置
    value_positions = {}
    for perm in permutations[:100]:  # 采样前100个排列
        for pos, val in enumerate(perm):
            if val not in value_positions:
                value_positions[val] = set()
            value_positions[val].add(pos + 1)  # 1-indexed
    
    for pos, val in known_positions:
        positions_in_perms = sorted(value_positions.get(val, []))[:10]
        print(f"   数字 {val} 在排列中的出现位置: {positions_in_perms} (第{pos}位)")
    
    # 3. 统计每列的约束信息
    print(f"\n3. 检查列约束分布:")
    for pos, val in known_positions:
        col_idx = pos - 1  # 0-indexed
        # 从column_constraints.json读取
        with open(os.path.join(WORK_DIR, "column_constraints.json"), 'r') as f:
            col_constraints = json.load(f)
        
        if str(col_idx + 1) in col_constraints["columns"]:
            col_info = col_constraints["columns"][str(col_idx + 1)]
            missing = col_info.get("possible_values", list(range(1,17)))
            print(f"   列{pos}: 数字{val} - 该列可能值: {sorted(missing)[:10]}...")
            if val not in missing:
                print(f"   ⚠️  警告: 数字{val}不在列{pos}的可能值中!")
    
    # 4. 检查排列数据完整性
    print(f"\n4. 排列数据完整性检查:")
    all_values = set()
    for perm in permutations:
        all_values.update(perm)
    
    print(f"   排列中出现的所有数字: {sorted(all_values)}")
    expected = set(range(1, 17))
    missing_in_perms = expected - all_values
    if missing_in_perms:
        print(f"   ⚠️  排列中缺失的数字: {missing_in_perms}")
    
    # 5. 查找最接近的匹配
    print(f"\n5. 最接近匹配分析:")
    known_vals = [v for v in row_data if v != 0]
    best_matches = []
    
    for perm in permutations:
        match_count = sum(1 for pos, val in enumerate(row_data) if val != 0 and val == perm[pos])
        if match_count >= len(known_vals) - 2:
            best_matches.append((match_count, perm))
    
    best_matches.sort(reverse=True)
    for i, (count, perm) in enumerate(best_matches[:5]):
        diff_positions = []
        for pos, val in enumerate(row_data):
            if val != 0 and val != perm[pos]:
                diff_positions.append(f"位置{pos+1}:盘={val}排列={perm[pos]}")
        print(f"   匹配{count}/{len(known_vals)}: {diff_positions[:3]}...")

def check_data_consistency():
    """检查整体数据一致性"""
    print("\n" + "="*70)
    print("【整体数据一致性检查】")
    print('='*70)
    
    # 1. 检查列约束与行约束的一致性
    print("\n1. 列约束统计:")
    with open(os.path.join(WORK_DIR, "column_constraints.json"), 'r') as f:
        col_constraints = json.load(f)
    
    for col_idx in range(1, 17):
        col_info = col_constraints["columns"][str(col_idx)]
        missing_count = col_info.get("possible_count", 16)
        if missing_count < 16:
            missing_vals = [v for v in range(1, 17) if v not in col_info["possible_values"]]
            print(f"   列{col_idx}: 缺失 {missing_vals}")
    
    # 2. 检查已知数字在列约束中的分布
    print("\n2. 92个已知数字的列约束符合性:")
    non_compliant = []
    for row_idx, row in enumerate(INITIAL_PUZZLE):
        for col_idx, val in enumerate(row):
            if val != 0:
                col_info = col_constraints["columns"][str(col_idx + 1)]
                if val not in col_info["possible_values"]:
                    non_compliant.append((row_idx+1, col_idx+1, val))
    
    if non_compliant:
        print("   ⚠️  发现列约束冲突:")
        for row, col, val in non_compliant:
            print(f"      位置({row},{col}): 数字{val}不在该列可能值中")
    else:
        print("   ✅ 所有已知数字均符合列约束")
    
    # 3. 统计符阖排列总数
    print("\n3. 符阖排列总计数:")
    total_perms = 0
    for row_num in range(1, 17):
        perms = load_permutations(row_num)
        total_perms += len(perms)
        print(f"   A{row_num}: {len(perms):,}个排列")
    print(f"   总计: {total_perms:,}个排列")

def main():
    # 对每个冲突行进行深度分析
    for row_num in CONFLICT_ROWS:
        analyze_conflict_row(row_num - 1, row_num)
    
    # 整体一致性检查
    check_data_consistency()
    
    # 输出诊断建议
    print("\n" + "="*70)
    print("【诊断结论与建议】")
    print('='*70)
    print("""
1. 发现5行约束冲突: 第1、6、12、13、16行
2. 可能原因分析:
   - 初始盘与符阖排列来自不同的数独题目版本
   - 数据提取过程中存在位置映射错误
   - 初始盘已知数字可能有误（录入错误或转录错误）
3. 建议验证步骤:
   a) 核对初始盘数字的源数据准确性
   b) 确认符阖排列数据的生成规则与行映射关系
   c) 检查是否存在行/列索引偏移（如0-indexed vs 1-indexed）
4. 如果数据源不一致，需要重新提取符阖排列或修正初始盘
""")

if __name__ == "__main__":
    main()
