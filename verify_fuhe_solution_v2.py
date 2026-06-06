import json
import pandas as pd

# Load the solution
with open(r'D:\2026\WPF_Sudoku\Sudoku_256\fuhe_solution.json', 'r') as f:
    data = json.load(f)

solution = data['solution']

print('=' * 70)
print('fuhe_solution.json 解验证')
print('=' * 70)
print('解的状态: ' + data['status'])
print()
print('首行 (A行):', solution[0])
print()

# Verify basic Sudoku constraints
def verify_solution(grid):
    n = 16
    errors = []
    
    for i in range(n):
        if len(set(grid[i])) != n:
            errors.append('行 ' + str(i) + ' 有重复')
    
    for j in range(n):
        col = [grid[i][j] for i in range(n)]
        if len(set(col)) != n:
            errors.append('列 ' + str(j) + ' 有重复')
    
    for box_row in range(4):
        for box_col in range(4):
            box_values = []
            for i in range(4):
                for j in range(4):
                    box_values.append(grid[box_row*4 + i][box_col*4 + j])
            if len(set(box_values)) != 16:
                errors.append('宫 (' + str(box_row) + ',' + str(box_col) + ') 有重复')
    
    return errors

errors = verify_solution(solution)
if errors:
    print('❌ 约束冲突:')
    for e in errors:
        print('  - ' + e)
else:
    print('✅ 行/列/宫 约束均满足')

# Check all 16 rows against fummel permutations
print()
print('=' * 70)
print('检查各行是否属于符闔排列集合')
print('=' * 70)

row_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 
             'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']

base_names = ['一', '二', '三', '四', '五', '六', '七', '八',
              '九', '十', '十一', '十二', '十三', '十四', '十五', '十六']

# First, let's see what the C row solution is
print('C行 (第三行) 解:', solution[2])
print('D行 (第四行) 解:', solution[3])

# Check C row specifically
print()
print('详细检查 C行:')
c_df = pd.read_excel(r'D:/2026/WPF_Sudoku/Sudoku_256/C第三行符闔排列.xlsx', header=None)
c_solution = solution[2]

# Find if C solution is in the permutations (without checking last column)
found = False
match_row = None
for idx, row in c_df.iterrows():
    perm = list(row.iloc[3:19])  # Columns 3-18 are the 16 values
    if perm == c_solution:
        found = True
        match_row = row
        break

if found:
    print('✓ C行解在符闔排列中找到，标记为:', match_row.iloc[19])
else:
    print('✗ C行解不在 C第三行符闔排列.xlsx 中')
    # Let's check the special row with 1
    special_row = c_df[c_df.iloc[:, 19] == 1].iloc[0]
    special_perm = list(special_row.iloc[3:19])
    print('特殊排列 C191620:', special_perm)
    print('解排列:', c_solution)
    print('差异位置:', [i for i in range(16) if special_perm[i] != c_solution[i]])

# Check D row specifically  
print()
print('详细检查 D行:')
d_df = pd.read_excel(r'D:/2026/WPF_Sudoku/Sudoku_256/D第四行符闔排列.xlsx', header=None)
d_solution = solution[3]

found_d = False
for idx, row in d_df.iterrows():
    perm = list(row.iloc[3:19])
    if perm == d_solution:
        found_d = True
        break

if found_d:
    print('✓ D行解在符闔排列中找到')
else:
    print('✗ D行解不在 D第四行符闔排列.xlsx 中')

# Continue checking remaining rows
print()
print('继续检查 E-P 行:')
for row_idx in range(4, 16):
    excel_file = f'D:/2026/WPF_Sudoku/Sudoku_256/{row_names[row_idx]}第{base_names[row_idx]}行符闔排列.xlsx'
    
    try:
        df = pd.read_excel(excel_file, header=None)
        solution_row = solution[row_idx]
        found = False
        for _, excel_row in df.iterrows():
            excel_perm = list(excel_row.iloc[3:19])
            if excel_perm == solution_row:
                found = True
                break
        
        status = '✓' if found else '✗'
        print(f'{row_names[row_idx]}行 ({len(df)} 个排列): {status}')
    except Exception as e:
        print(f'{row_names[row_idx]}行: 错误 - {str(e)}')
