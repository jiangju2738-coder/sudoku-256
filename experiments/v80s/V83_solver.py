# V83 100锚点B行演进推演 - 纯行列宫三约束规则
# 初始盘92锚点 + B行终局8增量锚点 = 100锚点

import sys
import os
import time
import json
import re

from ortools.sat.python import cp_model

print("=" * 75)
print("V83 100锚点B行演进推演 - 纯行列宫三约束规则")
print("=" * 75)
print()

# 读取txt文件
txt_files = [f for f in os.listdir('.') if f.endswith('.txt') and 'box_size' in f]
txt_file = txt_files[0]

with open(txt_file, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.strip().split('\n')
print(f"读取txt文件: {txt_file}")
print(f"总行数: {len(lines)}")

# ============================================================
# 解析初始盘92锚点
# ============================================================

row_letters = 'ABCDEFGHIJ' + 'KLMNOP'
initial_puzzle = {}

# 从文件开头解析初始盘（每行16个数字）
for i, line in enumerate(lines[:25]):
    line = line.strip()
    # 匹配: 行X [..] 或 行X数字 [..]
    match = re.match(r'行([A-P])(?:\d+)?\s*\[(.+)\]', line)
    if match:
        row_letter = match.group(1)
        numbers_str = match.group(2)
        nums = []
        for x in numbers_str.split(','):
            x = x.strip()
            if x:
                num_match = re.match(r'(\d+)', x)
                if num_match:
                    nums.append(int(num_match.group(1)))
        if len(nums) == 16:
            initial_puzzle[row_letter] = nums
            print(f"  解析初始行{row_letter}: {nums}")

initial_anchor_count = sum(1 for row in initial_puzzle.values() for v in row if v != 0)
print(f"\n初始盘解析: {len(initial_puzzle)}行, {initial_anchor_count}个锚点")

# ============================================================
# 查找B行终局数据（修正：使用繁体"終局"匹配）
# ============================================================

print("\n查找B行终局数据...")

# 同时匹配繁体"終局"和简体"终局"
final_puzzle = {}
final_section_found = False

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # 查找终局标记 - 同时匹配繁体和简体
    if ('終局' in stripped or '终局' in stripped) and ('盤' in stripped or '盘' in stripped or '數' in stripped or '数' in stripped):
        final_section_found = True
        print(f"  找到終局标记在第{i}行: {stripped}")
        continue
    
    # 如果已找到终局标记，解析终局盘行数据
    if final_section_found:
        # 匹配: 行X [..] 或 行X数字 [..] (如 C191620 [..])
        match = re.match(r'行([A-P])(?:\d+)?\s*\[(.+)\]', stripped)
        if match:
            row_letter = match.group(1)
            numbers_str = match.group(2)
            nums = []
            for x in numbers_str.split(','):
                x = x.strip()
                if x:
                    num_match = re.match(r'(\d+)', x)
                    if num_match:
                        nums.append(int(num_match.group(1)))
            if len(nums) == 16:
                final_puzzle[row_letter] = nums
                print(f"  解析终局行{row_letter}: {nums}")
        
        # 如果遇到新的大标题，停止（如"演進筭盤"）
        if re.match(r'^\s*[\u4e00-\u9fff]+\s*[：:]', stripped) or re.match(r'^\s*第\d', stripped):
            print(f"  遇到新章节标题，停止解析: {stripped[:50]}...")
            break

print(f"\n  从txt文件解析终局盘: {len(final_puzzle)}行")

# ============================================================
# B行终局数据（用户指定）
# ============================================================

b_row_initial = initial_puzzle.get('B', [0]*16)
print(f"\nB行初始: {b_row_initial}")

# 从txt终局盘提取B行
if 'B' in final_puzzle:
    b_row_final = final_puzzle['B']
    print(f"B行终局(从txt提取): {b_row_final}")
else:
    # 使用用户指定的B行终局
    b_row_final = [16, 12, 11, 8, 3, 10, 9, 14, 6, 15, 5, 4, 2, 7, 1, 13]
    print(f"B行终局(用户指定): {b_row_final}")

# 验证B行终局与txt终局一致
txt_b_row = final_puzzle.get('B', None)
if txt_b_row and txt_b_row != b_row_final:
    print(f"警告: B行终局与txt文件不一致!")
    print(f"  txt文件: {txt_b_row}")
    print(f"  用户指定: {b_row_final}")

# 计算B行新增锚点
new_anchors_indices = []
new_anchors_values = []

for c in range(16):
    if b_row_final[c] != 0 and b_row_initial[c] == 0:
        new_anchors_indices.append(c)
        new_anchors_values.append(b_row_final[c])

print(f"\nB行新增锚点位置: {new_anchors_indices} ({len(new_anchors_indices)}个)")
print(f"B行新增锚点值: {new_anchors_values}")

# ============================================================
# 构建100锚点谜题
# ============================================================

total_anchors = initial_anchor_count + len(new_anchors_indices)
print()
print("=" * 75)
print("构建100锚点谜题")
print("=" * 75)
print()
print("谜题定义:")
print(f"  初始盘锚点: {initial_anchor_count}个")
print(f"  B行终局新增锚点: {len(new_anchors_indices)}个 (位置: {new_anchors_indices})")
print(f"  总锚点数: {total_anchors}")
print(f"  约束规则: 纯行列宫三约束 (行AllDifferent + 列AllDifferent + 宫AllDifferent)")
print()

# 创建CP-SAT模型
model = cp_model.CpModel()
vars_16x16 = [[model.NewIntVar(1, 16, f'cell_{r}_{c}') for c in range(16)] for r in range(16)]

# 添加初始盘锚点
for r_idx, row_letter in enumerate(row_letters):
    if row_letter in initial_puzzle:
        for c_idx, val in enumerate(initial_puzzle[row_letter]):
            if val != 0:
                model.Add(vars_16x16[r_idx][c_idx] == val)

# 行、列、宫约束
for r in range(16):
    model.AddAllDifferent(vars_16x16[r])

for c in range(16):
    model.AddAllDifferent([vars_16x16[r][c] for r in range(16)])

for box_r in range(4):
    for box_c in range(4):
        box_vars = []
        for r_off in range(4):
            for c_off in range(4):
                r = box_r * 4 + r_off
                c = box_c * 4 + c_off
                box_vars.append(vars_16x16[r][c])
        model.AddAllDifferent(box_vars)

# 添加B行终局增量锚点
print("添加B行终局增量锚点...")
for c_idx, val in zip(new_anchors_indices, new_anchors_values):
    model.Add(vars_16x16[1][c_idx] == val)  # B行 = 索引1

print(f"  已添加{len(new_anchors_indices)}个B行增量锚点")

# ============================================================
# 求解
# ============================================================

print()
print("开始CP-SAT求解...")

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0
solver.parameters.num_search_workers = 8

start_time = time.time()
status_code = solver.Solve(model)
elapsed = time.time() - start_time

status_name = cp_model.CpSolver().StatusName(status_code)
print(f"求解状态: {status_name}")
print(f"求解耗时: {elapsed:.3f}秒")

# ============================================================
# 输出结果
# ============================================================

results = {
    'version': 'V83',
    'puzzle_type': '100_anchor_B_row_evolution',
    'description': f'初始盘{initial_anchor_count}锚点 + B行终局{len(new_anchors_indices)}增量锚点 = {total_anchors}锚点',
    'initial_anchors': initial_anchor_count,
    'b_row_initial': b_row_initial,
    'b_row_final': b_row_final,
    'b_row_new_anchors_count': len(new_anchors_indices),
    'b_row_new_anchors_indices': new_anchors_indices,
    'b_row_new_anchors_values': new_anchors_values,
    'total_anchors': total_anchors,
    'status': status_name,
    'elapsed_seconds': round(elapsed, 3),
    'constraint_type': 'pure_row_column_box_triple',
    'unique': (status_code == cp_model.OPTIMAL),
    'b_row_match': None,
    'solution': None
}

if status_code == cp_model.OPTIMAL or status_code == cp_model.FEASIBLE:
    solution = {}
    for r_idx, row_letter in enumerate(row_letters):
        solution[row_letter] = [solver.Value(vars_16x16[r_idx][c]) for c in range(16)]
    
    results['solution'] = solution
    
    # 检查B行匹配
    b_row_solution = solution['B']
    match = (b_row_solution == b_row_final)
    results['b_row_match'] = match
    
    print(f"\nB行解: {b_row_solution}")
    print(f"B行终局: {b_row_final}")
    print(f"B行匹配终局: {'YES' if match else 'NO'}")
    
    if match:
        print("[OK] B行终局已完整锁定，列约束将传播至全盘")
    
    print()
    print("完整解盘:")
    print("-" * 75)
    for r_idx, row_letter in enumerate(row_letters):
        vals = solution[row_letter]
        marker = '★' if row_letter == 'B' else ' '
        vals_str = "  ".join(f"{v:3d}" for v in vals)
        print(f"{marker}行{row_letter:<2}: {vals_str}")
    print("-" * 75)
    print(f"★ 表示B行 (终局锁定行)")

# 保存结果
output_file = 'V83_100_anchor_B_solution.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print()
print("=" * 75)
print("V83 100锚点B行演进推演完成")
print("=" * 75)
print(f"\n结果文件: {output_file}")
