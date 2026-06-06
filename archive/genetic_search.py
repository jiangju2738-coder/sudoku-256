#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
遺傳演算法搜尋：剩餘行排列組合優化
驗證列約束和宮約束
"""

import json
import random
import math
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter

random.seed(42)

# 載入相容性分析結果
with open('compatibility_v2.json', 'r', encoding='utf-8') as f:
    compat_data = json.load(f)

results = compat_data['results']

# 載入謎題配置獲取已知數
with open('超級大數獨_box_size4.txt', 'r', encoding='utf-8') as f:
    puzzle_content = f.read()

import re
grid_template = [[0]*16 for _ in range(16)]
row_labels = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']

for m in re.finditer(r'行([A-P]) \[(.*?)\]', puzzle_content):
    label, vals_str = m.group(1), m.group(2)
    vals = [int(v.strip()) if v.strip()!='0' else 0 for v in vals_str.split(',')]
    idx = ord(label) - ord('A')
    grid_template[idx] = vals

# 識別需要搜尋的行
unknown_rows = []
fixed_rows = {}  # {row_label: [values]}

for label in row_labels:
    r = results[label]
    if r['status'] == 'FULLY_KNOWN' and r['given_count'] == 16:
        # 完全已知的行 - 從模板獲取
        fixed_rows[label] = grid_template[ord(label)-ord('A')]
    elif r['compatible_count'] == 1:
        # 唯一相容排列的行
        fixed_rows[label] = None  # 需要從排列池載入
    elif r['compatible_count'] > 1:
        unknown_rows.append(label)

print("="*80)
print("遺傳演算法搜尋配置")
print("="*80)
print(f"\n固定先行: {list(fixed_rows.keys())}")
print(f"搜尋先行: {unknown_rows}")
print(f"搜尋先行數: {len(unknown_rows)}")

# 為每行載入相容排列（只載入少量以加速）
print("\n載入相容排列池...")
row_perm_cache = {}

for label in unknown_rows:
    r = results[label]
    fname = f"{label}{chr(65+ord(label)-65)}行符闔排列.xlsx"  # 需要修正
    # 使用中文名稱
    chinese_names = {'A':'第一','B':'第二','C':'第三','D':'第四','E':'第五','F':'第六',
                     'G':'第七','H':'第八','I':'第九','J':'第十','K':'第十一','L':'第十二',
                     'M':'第十三','N':'第十四','O':'第十五','P':'第十六'}
    fname = f"{label}{chinese_names[label]}行符闔排列.xlsx"
    
    try:
        import openpyxl
        fpath = Path("D:/2026/WPF_Sudoku/Sudoku_256") / fname
        wb = openpyxl.load_workbook(str(fpath), data_only=True, read_only=True)
        ws = wb.active
        
        perms = []
        given = {j:v for j,v in enumerate(grid_template[ord(label)-ord('A')]) if v != 0}
        
        for row in ws.iter_rows(values_only=True):
            if len(row) >= 19:
                vals = []
                for i in range(3, 19):
                    v = row[i]
                    if isinstance(v, (int, float)) and 1 <= v <= 16:
                        vals.append(int(v))
                if len(vals) == 16:
                    # 檢查相容性
                    if given:
                        ok = all(vals[c] == given[c] for c in given if c < 16)
                        if ok:
                            perms.append(vals)
                    else:
                        perms.append(vals)
            
            if len(perms) >= 100:  # 只載入前100個相容排列以加速
                break
        
        wb.close()
        row_perm_cache[label] = perms
        print(f"   行{label}: 載入 {len(perms)} 個相容排列")
    except Exception as e:
        print(f"   行{label}: 載入失敗 - {e}")
        row_perm_cache[label] = []

# 遺傳演算法配置
POPULATION_SIZE = 50
GENERATIONS = 200
MUTATION_RATE = 0.15
CROSSOVER_RATE = 0.7
ELITE_SIZE = 5

def calc_col_fitness(grid):
    """列約束適應度"""
    conflicts = 0
    for j in range(16):
        col = [grid[i][j] for i in range(16)]
        if len(set(col)) < 16:
            conflicts += 1
    return (16 - conflicts) / 16

def calc_box_fitness(grid, box_size=4):
    """宮約束適應度"""
    conflicts = 0
    for band in range(4):
        for stack in range(4):
            box = []
            for bi in range(box_size):
                for bj in range(box_size):
                    box.append(grid[band*box_size+bi][stack*box_size+bj])
            if len(set(box)) < 16:
                conflicts += 1
    return (16 - conflicts) / 16

def calc_total_fitness(grid):
    """總適應度"""
    return calc_col_fitness(grid) * 0.5 + calc_box_fitness(grid) * 0.5

def create_individual():
    """建立個體：為每行選擇一個排列"""
    individual = {}
    for label in unknown_rows:
        perms = row_perm_cache.get(label, [])
        if perms:
            individual[label] = random.choice(perms)
        else:
            individual[label] = list(range(1, 17))  # 預設
    return individual

def decode_to_grid(individual):
    """解碼為完整網格"""
    grid = [[0]*16 for _ in range(16)]
    
    # 填入固定行
    for label, vals in fixed_rows.items():
        if vals:
            idx = ord(label) - ord('A')
            grid[idx] = vals
    
    # 填入搜尋行
    for label in unknown_rows:
        idx = ord(label) - ord('A')
        if label in individual:
            grid[idx] = individual[label]
    
    return grid

def tournament_select(population, fitnesses, k=5):
    """競賽選擇"""
    tournament = random.sample(list(zip(population, fitnesses)), min(k, len(population)))
    return max(tournament, key=lambda x: x[1])[0]

def crossover(p1, p2):
    """交叉"""
    child = {}
    for label in unknown_rows:
        if random.random() < 0.5:
            child[label] = p1[label]
        else:
            child[label] = p2[label]
    return child

def mutate(individual):
    """突變"""
    for label in unknown_rows:
        if random.random() < MUTATION_RATE:
            perms = row_perm_cache.get(label, [])
            if perms:
                individual[label] = random.choice(perms)
    return individual

# 初始化種群
print("\n" + "="*80)
print("遺傳演算法執行")
print("="*80)

population = [create_individual() for _ in range(POPULATION_SIZE)]
best_fitness = 0.0
best_individual = None
fitness_history = []

for gen in range(GENERATIONS):
    # 評估
    evaluated = []
    for ind in population:
        grid = decode_to_grid(ind)
        fit = calc_total_fitness(grid)
        evaluated.append((ind, fit))
    
    # 排序
    evaluated.sort(key=lambda x: x[1], reverse=True)
    
    # 更新最佳
    if evaluated[0][1] > best_fitness:
        best_fitness = evaluated[0][1]
        best_individual = evaluated[0][0]
    
    fitness_history.append(best_fitness)
    
    if gen % 20 == 0:
        col_fit = calc_col_fitness(decode_to_grid(evaluated[0][0]))
        box_fit = calc_box_fitness(decode_to_grid(evaluated[0][0]))
        print(f"代數 {gen:3d}: 適應度={best_fitness:.4f} (列={col_fit:.3f}, 宮={box_fit:.3f})")
    
    if best_fitness >= 1.0:
        print(f"✅ 找到完美解!")
        break
    
    # 精英保留
    elite = [ind for ind, _ in evaluated[:ELITE_SIZE]]
    
    # 新一代
    new_pop = elite.copy()
    while len(new_pop) < POPULATION_SIZE:
        p1 = tournament_select(population, [e[1] for e in evaluated])
        p2 = tournament_select(population, [e[1] for e in evaluated])
        
        if random.random() < CROSSOVER_RATE:
            child = crossover(p1, p2)
        else:
            child = p1.copy()
        
        mutate(child)
        new_pop.append(child)
    
    population = new_pop[:POPULATION_SIZE]

# 建立最佳解
best_grid = decode_to_grid(best_individual)

# 驗證
print("\n" + "="*80)
print("最佳解驗證")
print("="*80)

col_fit = calc_col_fitness(best_grid)
box_fit = calc_box_fitness(best_grid)
row_fit = 1.0  # 行約束由排列保證

print(f"\n列適應度: {col_fit:.4f}")
print(f"宮適應度: {box_fit:.4f}")
print(f"總適應度: {best_fitness:.4f}")

# 檢查列衝突
col_conflicts = []
for j in range(16):
    col = [best_grid[i][j] for i in range(16)]
    counts = Counter(col)
    duplicates = [v for v, c in counts.items() if c > 1]
    if duplicates:
        col_conflicts.append((j, duplicates))

print(f"\n列衝突數: {len(col_conflicts)}")
if col_conflicts:
    print("衝突詳情（前5）:")
    for j, dups in col_conflicts[:5]:
        print(f"   列{j}: 重複值 {dups}")

# 檢查宮衝突
box_conflicts = []
for band in range(4):
    for stack in range(4):
        box = []
        for bi in range(4):
            for bj in range(4):
                box.append(best_grid[band*4+bi][stack*4+bj])
        counts = Counter(box)
        duplicates = [v for v, c in counts.items() if c > 1]
        if duplicates:
            box_conflicts.append(((band, stack), duplicates))

print(f"\n宮衝突數: {len(box_conflicts)}")
if box_conflicts:
    print("衝突詳情（前5）:")
    for (b, s), dups in box_conflicts[:5]:
        print(f"   宮({b},{s}): 重複值 {dups}")

# 保存結果
output = {
    'best_fitness': best_fitness,
    'column_fitness': col_fit,
    'box_fitness': box_fit,
    'column_conflicts': len(col_conflicts),
    'box_conflicts': len(box_conflicts),
    'fitness_history': fitness_history,
    'best_grid': best_grid,
    'best_individual': {k: v[:4] for k, v in best_individual.items()}  # 只保存前4個值作為範例
}

with open('genetic_search_result.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n💾 結果已保存到: genetic_search_result.json")

# 顯示最佳網格
print("\n" + "="*80)
print("最佳解網格（前8行）")
print("="*80)
for i in range(min(8, 16)):
    row_str = ' '.join(f'{v:2d}' for v in best_grid[i])
    print(f"行{row_labels[i]:2s}: {row_str}")
