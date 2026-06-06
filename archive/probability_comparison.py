#!/usr/bin/env python3
"""
符閘排列 vs 標準數獨 - 概率比對比測評
"""

import json
import math
from collections import defaultdict

print('=' * 70)
print('符閘排列 vs 標準數獨 - 概率比對比測評')
print('=' * 70)

# ===== 1. 讀取符閘排列數據 =====
print('\n【階段1】讀取符閘排列數據...')

perms_by_row = {}
total_perm_space = 1

for i in range(1, 17):
    with open(f'A{i}_permutations.json', 'r', encoding='utf-8') as f:
        perms = json.load(f)
    perms_by_row[i-1] = perms
    total_perm_space *= len(perms)

print(f'符閘排列總空間: {total_perm_space:.6e}')

# ===== 2. 概率空間分析 =====
print('\n【階段2】概率空間深度分析...')

N = 16
factorial_16 = math.factorial(N)

print(f'\n16! = {factorial_16:,} (單行所有排列數)')
print(f'標準數獨無約束空間: 16^256 ≈ 10^307')

# 每行符閘排列占全排列的比例
print('\n各行符閘排列概率密度 (符閘排列 / 16!):')
prob_densities = []
for i in range(16):
    density = len(perms_by_row[i]) / factorial_16
    prob_densities.append(density)
    print(f'  A{i+1:2d}: {len(perms_by_row[i]):>10,} / {factorial_16:,} = {density:.10f} = {density*100:.8f}%')

# 符閘排列約束的整體概率比
avg_prob_density = sum(prob_densities) / 16
print(f'\n平均單行概率密度: {avg_prob_density:.10f} = {avg_prob_density*100:.8f}%')

# ===== 3. 符閘排列約束的壓縮比 =====
print('\n【階段3】符閘排列約束壓縮比分析...')

compression_ratios = []
for i in range(16):
    ratio = factorial_16 / len(perms_by_row[i])
    compression_ratios.append(ratio)

print('\n各行壓縮比 (16! / 符閘排列數):')
for i in range(16):
    print(f'  A{i+1:2d}: {compression_ratios[i]:.2f}x 壓縮')

avg_compression = sum(compression_ratios) / 16
print(f'\n平均壓縮比: {avg_compression:.2f}x')

# 符閘排列約束的整體壓縮比
total_compression = factorial_16 ** 16 / total_perm_space
print(f'符閘排列約束整體壓縮比: {total_compression:.3e}x')
print(f'即符閘排列約束將 (16!)^16 個排列空間壓縮到 {total_perm_space} 個')

# ===== 4. 標準數獨搜索空間 =====
print('\n【階段4】標準數獨搜索空間分析...')

print('\n標準數獨搜索空間估算:')
print(f'  每行16! = {factorial_16:,} 種選擇')
print(f'  16行總排列: (16!)^16 ≈ {factorial_16**16:.3e}')
print(f'  標準16x16數獨解數量級: ~10^100')

# ===== 5. 符閘排列約束下的搜索空間 =====
print('\n【階段5】符閘排列約束下的搜索空間...')

print(f'符閘排列約束空間: {total_perm_space:.3e}')
print(f'符閘排列約束空間佔標準空間比例: {total_perm_space / (factorial_16**16):.10e}')

# ===== 6. 符閘排列單源值分析 =====
print('\n【階段6】符閘排列單源值分析...')

val_col_sources = defaultdict(lambda: defaultdict(set))

for r in range(16):
    for perm in perms_by_row[r]:
        for c in range(16):
            val_col_sources[perm[c]][c].add(r)

single_source_fuhe = {}
for v in range(16):
    for c in range(16):
        rows = val_col_sources[v][c]
        if len(rows) == 1:
            r = list(rows)[0]
            single_source_fuhe[(c, v)] = r

print(f'符閘排列單源值總數: {len(single_source_fuhe)}')

single_source_values = set(v for (_, v) in single_source_fuhe.keys())
print(f'單源值種類數: {len(single_source_values)} / 16 = {len(single_source_values)/16*100:.1f}%')

# ===== 7. 搜索效率對比 =====
print('\n【階段7】搜索效率對比測評...')

print('\n標準數獨搜索策略:')
print('  - 每格16個值選擇')
print('  - 回溯搜索深度: 256層')
print('  - 分支因子: 最多16')
print('  - 理論最壞情況: 16^256 次嘗試')

print('\n符閘排列搜索策略:')
print(f'  - 每行從排列中選擇')
print('  - 回溯搜索深度: 16層 (按行)')
print('  - 分支因子: 符閘排列數')
print(f'  - 理論最壞情況: 符閘排列總空間 = {total_perm_space} 次嘗試')

print('\n約束傳播效率對比:')
print('  符閘排列約束: 行約束預先壓縮，僅需檢查列+宮格')
print('  標準數獨約束: 需同時檢查行+列+宮格')

# ===== 8. 概率比總結 =====
print('\n' + '=' * 70)
print('【概率比對比測評總結】')
print('=' * 70)

summary = '''
╔══════════════════════════════════════════════════════════════════════╗
║                    符閘排列 vs 標準數獨 概率比對比                   ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  1. 單行排列空間壓縮比:                                              ║
║     - 符閘排列: 平均每行 {:.2f}x 壓縮 (vs 16!)                          ║
║     - 最高壓縮: A{:2d} 行 {:.2f}x                                          ║
║     - 最低壓縮: A{:2d} 行 {:.2f}x                                          ║
║                                                                      ║
║  2. 整體排列空間:                                                    ║
║     - 符閘排列總空間: {:.3e}                                  ║
║     - 標準數獨總空間: (16!)^16 = {:.3e}                      ║
║     - 符閘排列壓縮因子: {:.3e}x                                  ║
║                                                                      ║
║  3. 符閘排列約束概率密度:                                            ║
║     - 平均每行: {:.10f} ({:.8f}%)                              ║
║     - 符閘排列是標準數獨的子集                                       ║
║                                                                      ║
║  4. 搜索效率提升:                                                    ║
║     - 深度: 256 -> 16 (按行搜索)                                     ║
║     - 分支: 16 -> 符閘排列數                                         ║
║     - 約束提前應用: 行約束 -> 列+宮格約束                            ║
║                                                                      ║
║  5. 符閘排列單源值:                                                  ║
║     - 數量: {:d} 個                                                   ║
║     - 價值: 確定性地減少搜索空間                                     ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
'''.format(
    avg_compression,
    16-compression_ratios.index(max(compression_ratios)),
    max(compression_ratios),
    16-compression_ratios.index(min(compression_ratios)),
    min(compression_ratios),
    total_perm_space,
    factorial_16**16,
    total_compression,
    avg_prob_density,
    avg_prob_density*100,
    len(single_source_fuhe)
)

print(summary)

# 儲存分析結果
analysis_result = {
    'factorial_16': factorial_16,
    'total_perm_space': total_perm_space,
    'avg_prob_density': avg_prob_density,
    'avg_compression': avg_compression,
    'total_compression': total_compression,
    'single_source_count': len(single_source_fuhe),
    'row_compression_ratios': compression_ratios,
    'row_prob_densities': prob_densities
}

with open('probability_comparison_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_result, f, ensure_ascii=False, indent=2)

print('分析結果已儲存: probability_comparison_analysis.json')
