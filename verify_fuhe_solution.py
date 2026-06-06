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
    
    # Check rows
    for i in range(n):
        if len(set(grid[i])) != n:
            errors.append('行 ' + str(i) + ' 有重复')
    
    # Check columns
    for j in range(n):
        col = [grid[i][j] for i in range(n)]
        if len(set(col)) != n:
            errors.append('列 ' + str(j) + ' 有重复')
    
    # Check 4x4 boxes
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

# Now check if each row matches fummel permutations
print()
print('=' * 70)
print('检查各行是否属于符闔排列集合')
print('=' * 70)

row_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 
             'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']

base_names = ['一', '二', '三', '四', '五', '六', '七', '八',
              '九', '十', '十一', '十二', '十三', '十四', '十五', '十六']

all_match = True
for row_idx in range(16):
    excel_file = f'D:/2026/WPF_Sudoku/Sudoku_256/{row_names[row_idx]}第{base_names[row_idx]}行符闔排列.xlsx'
    
    try:
        df = pd.read_excel(excel_file, header=None)
        perm_col_start = 3  # Column index where permutation starts
        
        # Check if this solution row exists in the Excel
        solution_row = solution[row_idx]
        found = False
        for _, excel_row in df.iterrows():
            excel_perm = list(excel_row.iloc[perm_col_start:perm_col_start+16])
            if excel_perm == solution_row:
                found = True
                break
        
        status = '✓ 匹配' if found else '✗ 不匹配'
        if not found:
            all_match = False
        print(f'{row_names[row_idx]}行 ({len(df)} 个排列): {status}')
    except Exception as e:
        print(f'{row_names[row_idx]}行: 文件读取错误 - {e}')

print()
if all_match:
    print('🎉 所有16行均属于符闔排列集合！')
else:
    print('⚠️ 部分行不在符闔排列集合中')

# Print full solution grid
print()
print('=' * 70)
print('完整解网格')
print('=' * 70)
for i, row in enumerate(solution):
    print(f'{row_names[i]}: {row}')
