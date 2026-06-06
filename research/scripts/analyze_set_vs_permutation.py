"""
分析"解集"与符阖排列的关系
对比txt文件中的"解集"定义与符阖排列中每个位置的值分布
"""
import json, os, sys

BASE_DIR = r'D:\2026\WPF_Sudoku\Sudoku_256'
backup_dir = os.path.join(BASE_DIR, 'backup_fuyi')

sys.stdout.reconfigure(encoding='utf-8')

# 加载符阖排列
perm_sets = []
for i in range(16):
    path = os.path.join(backup_dir, f'A{i+1}_permutations.json')
    with open(path, 'r', encoding='utf-8') as f:
        perms = json.load(f)
    perm_sets.append(perms)

# 从txt文件中提取的"解集"定义（第151-456行）
row_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
col_letters = ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S']

# 手动提取部分"解集"定义（从txt文件第154-254行）
sample_cells = {
    'A': {
        'D': ('set', [2, 6, 7, 9, 10, 11]),
        'E': ('set', [2, 6, 7, 9, 10, 11, 15]),
        'F': ('fixed', 3),
        'G': ('set', [1, 7, 9, 10, 11, 15]),
        'H': ('set', [4, 6, 10, 11, 14]),
        'I': ('fixed', 12),
        'J': ('set', [6, 10, 11, 13, 15]),
        'K': ('fixed', 5),
        'L': ('set', [1, 7, 9, 10, 12, 15]),
        'M': ('set', [2, 7, 10, 12, 13, 15]),
        'N': ('set', [1, 7, 9, 10, 13, 15]),
        'O': ('fixed', 14),
        'P': ('set', [6, 7, 10, 11, 13, 14, 15]),
        'Q': ('fixed', 16),
        'R': ('set', [4, 6, 9, 11, 13, 14, 15]),
        'S': ('fixed', 8),
    },
    'B': {
        'D': ('set', [7, 8, 10, 11, 16]),
        'E': ('fixed', 12),
        'F': ('set', [1, 7, 8, 10, 11, 15, 16]),
        'G': ('set', [7, 8, 10, 11, 15, 16]),
        'H': ('fixed', 3),
        'I': ('set', [10, 13, 14, 15]),
        'J': ('fixed', 9),
        'K': ('set', [10, 11, 13, 14, 16]),
        'L': ('fixed', 6),
        'M': ('set', [7, 8, 10, 13, 15, 16]),
        'N': ('fixed', 5),
        'O': ('fixed', 4),
        'P': ('fixed', 2),
        'Q': ('set', [7, 10, 11, 14]),
        'R': ('fixed', 1),
        'S': ('set', [10, 11, 13, 14, 15]),
    },
    'C': {
        'D': ('set', [5, 6, 7, 9, 10, 11, 16]),
        'E': ('set', [6, 7, 9, 10, 11, 15, 16]),
        'F': ('fixed', 14),
        'G': ('set', [1, 5, 7, 9, 10, 11, 15, 16]),
        'H': ('set', [4, 6, 10, 11, 16]),
        'I': ('fixed', 2),
        'J': ('set', [6, 10, 11, 13, 15, 16]),
        'K': ('fixed', 8),
        'L': ('set', [1, 3, 7, 9, 10, 12, 15, 16]),
        'M': ('set', [7, 10, 12, 13, 15, 16]),
        'N': ('set', [1, 3, 7, 9, 10, 13, 15]),
        'O': ('set', [1, 9, 10, 12, 13, 16]),
        'P': ('set', [3, 5, 6, 7, 10, 11, 13, 15]),
        'Q': ('set', [4, 7, 9, 10, 11]),
        'R': ('set', [4, 5, 6, 9, 11, 13, 15]),
        'S': ('set', [4, 5, 6, 9, 10, 11, 13, 15]),
    },
}

print('=' * 70)
print('  "解集"与符阖排列的关系分析')
print('=' * 70)
print()
print('分析逻辑：')
print('  - 固定值：txt文件中直接给出具体数值（如AF=3）')
print('  - 解集：txt文件中给出可能值的列表（如AD=0 解集=[2,6,7,9,10,11]）')
print('  - 符阖排列：实际排列中该位置所有可能的值')
print()

results_summary = []

for row_letter, cells in sample_cells.items():
    r_idx = row_letters.index(row_letter)
    n_perms = len(perm_sets[r_idx])
    
    print('=' * 70)
    print(f'  行{row_letter} (第{r_idx+1}行) - {n_perms}个符阖排列')
    print('=' * 70)
    print()
    
    fixed_count = 0
    set_count = 0
    fixed_matches = 0
    set_matches = 0
    mismatches = []
    
    for col_letter, (cell_type, expected) in cells.items():
        c_idx = col_letters.index(col_letter)
        
        # 从符阖排列中提取该位置的所有值
        actual_values = sorted(set(p[c_idx] for p in perm_sets[r_idx]))
        
        if cell_type == 'fixed':
            fixed_count += 1
            # 检查是否是100%固定
            value_counts = {}
            for p in perm_sets[r_idx]:
                v = p[c_idx]
                value_counts[v] = value_counts.get(v, 0) + 1
            
            top_val, top_count = max(value_counts.items(), key=lambda x: x[1])
            pct = top_count / n_perms * 100
            
            if top_val == expected and pct == 100:
                status = '[OK] 匹配'
                fixed_matches += 1
            elif top_val == expected:
                status = f'[WARN] 高频({pct:.1f}%)但非固定'
            else:
                status = f'[FAIL] 期望={expected}, 实际最高频={top_val}({pct:.1f}%)'
                mismatches.append((col_letter, expected, top_val, pct))
            
            print(f'  {col_letter}: txt={expected}(固定) | 符阖值域={actual_values} | {status}')
            
        else:  # set
            set_count += 1
            expected_set = set(expected)
            actual_set = set(actual_values)
            
            if expected_set == actual_set:
                status = '[OK] 完全匹配'
                set_matches += 1
            elif expected_set.issubset(actual_set):
                extra = sorted(actual_set - expected_set)
                status = f'[WARN] 符阖多值: 额外值={extra}'
            elif expected_set.issuperset(actual_set):
                missing = sorted(expected_set - actual_set)
                status = f'[WARN] txt多值: 缺失值={missing}'
            else:
                extra = sorted(actual_set - expected_set)
                missing = sorted(expected_set - actual_set)
                status = f'[WARN] 差异: 额外={extra}, 缺失={missing}'
            
            print(f'  {col_letter}: txt=解集{expected} | 符阖值域={actual_values} | {status}')
        
        results_summary.append({
            'row': row_letter,
            'col': col_letter,
            'type': cell_type,
            'expected': expected,
            'actual_values': actual_values,
            'match': status.startswith('[OK]')
        })
    
    print()
    print(f'  汇总: {fixed_count}个固定值(匹配{fixed_matches}个), {set_count}个解集(匹配{set_matches}个)')
    if mismatches:
        print(f'  [注意] {len(mismatches)}个固定值不匹配符阖排列')
    print()

print()
print('=' * 70)
print('  整体统计')
print('=' * 70)
print()

total_ok = sum(1 for r in results_summary if r['match'])
total = len(results_summary)
print(f'总计验证 {total} 个单元格')
print(f'完全匹配: {total_ok} 个 ({total_ok/total*100:.1f}%)')
print(f'部分匹配: {total - total_ok} 个 ({(total-total_ok)/total*100:.1f}%)')
print()

# 分析固定值vs解集的分布规律
print('=' * 70)
print('  关键发现总结')
print('=' * 70)
print()
