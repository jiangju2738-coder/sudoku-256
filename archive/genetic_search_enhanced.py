#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
遺傳演算法搜尋（增強版）：剩餘行排列組合優化
增強參數：500+排列樣本，1000+代數，剪枝優化
"""

import json
import random
import math
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter

random.seed(42)

# === 增強參數 ===
POPULATION_SIZE = 100        # 從 50 增加到 100
GENERATIONS = 1000           # 從 200 增加到 1000
MUTATION_RATE = 0.25          # 從 0.15 增加到 0.25（更高探索）
CROSSOVER_RATE = 0.8         # 從 0.7 增加到 0.8
ELITE_SIZE = 10              # 從 5 增加到 10
PERM_SAMPLE_SIZE = 500       # 從 100 增加到 500
TOURNAMENT_K = 7             # 競賽選擇大小

# 剪枝參數
ENABLE_PRUNING = True
PRUNING_THRESHOLD = 0.05     # 適應度低於此值的個體被淘汰
MIN_FITNESS_IMPROVEMENT = 0.001  # 最小適應度提升


def load_puzzle_config():
    """載入謎題配置"""
    with open('超級大數獨_box_size4.txt', 'r', encoding='utf-8') as f:
        puzzle_content = f.read()
    
    grid_template = [[0]*16 for _ in range(16)]
    row_labels = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
    
    for m in re.finditer(r'行([A-P]) \[(.*?)\]', puzzle_content):
        label, vals_str = m.group(1), m.group(2)
        vals = [int(v.strip()) if v.strip()!='0' else 0 for v in vals_str.split(',')]
        idx = ord(label) - ord('A')
        grid_template[idx] = vals
    
    return grid_template, row_labels


def load_compatibility():
    """載入相容性分析結果"""
    with open('compatibility_v2.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def load_permutations_from_excel(row_label: str, chinese_name: str, sample_size: int = 500) -> List[List[int]]:
    """從 Excel 載入相容排列（增強版：更多樣本）"""
    import openpyxl
    
    fpath = Path("D:/2026/WPF_Sudoku/Sudoku_256") / f"{row_label}{chinese_name}行符闔排列.xlsx"
    
    try:
        wb = openpyxl.load_workbook(str(fpath), data_only=True, read_only=True)
        ws = wb.active
        
        perms = []
        for row in ws.iter_rows(values_only=True):
            if len(row) >= 19:
                vals = []
                for i in range(3, 19):
                    v = row[i]
                    if isinstance(v, (int, float)) and 1 <= v <= 16:
                        vals.append(int(v))
                if len(vals) == 16:
                    perms.append(vals)
            
            if len(perms) >= sample_size:  # 載入更多樣本
                break
        
        wb.close()
        return perms
    except Exception as e:
        print(f"   載入排列失敗: {e}")
        return []


def calc_col_fitness(grid):
    """列約束適應度 - 計數衝突數"""
    conflicts = 0
    conflict_details = []
    for j in range(16):
        col = [grid[i][j] for i in range(16)]
        counts = Counter(col)
        col_conflicts = sum(c - 1 for c in counts.values() if c > 1)
        if col_conflicts > 0:
            conflicts += 1
            conflict_details.append((j, col_conflicts))
    return (16 - conflicts) / 16, conflicts, conflict_details


def calc_box_fitness(grid, box_size=4):
    """宮約束適應度 - 計數衝突數"""
    conflicts = 0
    conflict_details = []
    for band in range(4):
        for stack in range(4):
            box = []
            for bi in range(box_size):
                for bj in range(box_size):
                    box.append(grid[band*box_size+bi][stack*box_size+bj])
            counts = Counter(box)
            box_conflicts = sum(c - 1 for c in counts.values() if c > 1)
            if box_conflicts > 0:
                conflicts += 1
                conflict_details.append(((band, stack), box_conflicts))
    return (16 - conflicts) / 16, conflicts, conflict_details


def calc_total_fitness(grid, w_row=0.1, w_col=0.5, w_box=0.4):
    """總適應度（改進權重）"""
    row_fit = 1.0  # 行約束由排列保證
    col_fit, col_conflicts, _ = calc_col_fitness(grid)
    box_fit, box_conflicts, _ = calc_box_fitness(grid)
    
    total = row_fit * w_row + col_fit * w_col + box_fit * w_box
    return total, col_conflicts, box_conflicts


def load_all_data():
    """載入所有數據"""
    import re
    
    grid_template, row_labels = load_puzzle_config()
    compat_data = load_compatibility()
    results = compat_data['results']
    
    # 識別行狀態
    known_rows = {}
    unknown_rows = []
    row_perm_cache = {}
    
    chinese_names = {
        'A':'第一','B':'第二','C':'第三','D':'第四','E':'第五','F':'第六',
        'G':'第七','H':'第八','I':'第九','J':'第十','K':'第十一','L':'第十二',
        'M':'第十三','N':'第十四','O':'第十五','P':'第十六'
    }
    
    print("\n載入相容排列池（增強版：500 樣本）...")
    for label in row_labels:
        r = results[label]
        idx = ord(label) - ord('A')
        
        if r['status'] == 'FULLY_KNOWN' and r['given_count'] == 16:
            # 完全已知
            known_rows[idx] = grid_template[idx]
            print(f"   行{label}: 完全已知")
        elif r['compatible_count'] == 1:
            # 唯一相容
            perms = load_permutations_from_excel(label, chinese_names[label], PERM_SAMPLE_SIZE)
            given = {j:v for j,v in enumerate(grid_template[idx]) if v != 0}
            compat_perms = [p for p in perms if not given or all(p[c] == given[c] for c in given)]
            if compat_perms:
                known_rows[idx] = compat_perms[0]
                print(f"   行{label}: 唯一相容 ({len(compat_perms)} 個)")
        else:
            # 多相容 - 需要搜尋
            unknown_rows.append(idx)
            perms = load_permutations_from_excel(label, chinese_names[label], PERM_SAMPLE_SIZE)
            given = {j:v for j,v in enumerate(grid_template[idx]) if v != 0}
            compat_perms = [p for p in perms if not given or all(p[c] == given[c] for c in given)]
            row_perm_cache[idx] = compat_perms
            print(f"   行{label}: {len(compat_perms)} 相容排列（載入 {len(perms)} 個）")
    
    return grid_template, row_labels, known_rows, unknown_rows, row_perm_cache, results


def create_individual(unknown_rows: List[int], row_perm_cache: Dict) -> Dict:
    """建立個體：為每行選擇一個排列"""
    individual = {}
    for idx in unknown_rows:
        perms = row_perm_cache.get(idx, [])
        if perms:
            individual[idx] = random.choice(perms)
        else:
            individual[idx] = list(range(1, 17))  # 預設
    return individual


def decode_to_grid(individual: Dict, known_rows: Dict) -> List[List[int]]:
    """解碼為完整網格"""
    grid = [[0]*16 for _ in range(16)]
    
    # 填入已知行
    for idx, vals in known_rows.items():
        grid[idx] = vals
    
    # 填入搜尋行
    for idx in individual:
        grid[idx] = individual[idx]
    
    return grid


def tournament_select(population: List[Dict], fitnesses: List[float], k: int = TOURNAMENT_K) -> Dict:
    """競賽選擇（增強版：更大 k 值）"""
    indices = list(range(len(population)))
    tournament_indices = random.sample(indices, min(k, len(population)))
    best_idx = max(tournament_indices, key=lambda i: fitnesses[i])
    return population[best_idx]


def crossover(p1: Dict, p2: Dict, unknown_rows: List[int]) -> Dict:
    """交叉"""
    child = {}
    for idx in unknown_rows:
        if random.random() < CROSSOVER_RATE:
            child[idx] = p1[idx]
        else:
            child[idx] = p2[idx]
    return child


def mutate(individual: Dict, unknown_rows: List[int], row_perm_cache: Dict, mutation_rate: float = MUTATION_RATE) -> Dict:
    """突變（增強版：更高突變率）"""
    for idx in unknown_rows:
        if random.random() < mutation_rate:
            perms = row_perm_cache.get(idx, [])
            if perms:
                individual[idx] = random.choice(perms)
    return individual


def optimize():
    """遺傳演算法優化（增強版）"""
    print("="*80)
    print("遺傳演算法搜尋（增強版）")
    print("="*80)
    print(f"\n參數設定:")
    print(f"   種群大小: {POPULATION_SIZE}")
    print(f"   代數: {GENERATIONS}")
    print(f"   突變率: {MUTATION_RATE}")
    print(f"   交叉率: {CROSSOVER_RATE}")
    print(f"   精英數: {ELITE_SIZE}")
    print(f"   排列樣本: {PERM_SAMPLE_SIZE}/行")
    
    # 載入數據
    grid_template, row_labels, known_rows, unknown_rows, row_perm_cache, results = load_all_data()
    
    print(f"\n搜尋先行: {len(unknown_rows)} 行")
    if len(unknown_rows) == 0:
        print("無需搜尋，所有行已確定")
        return
    
    # 初始化種群
    print("\n初始化種群...")
    population = [create_individual(unknown_rows, row_perm_cache) for _ in range(POPULATION_SIZE)]
    
    best_fitness = 0.0
    best_individual = None
    fitness_history = []
    col_fitness_history = []
    box_fitness_history = []
    start_time = time.time()
    
    # 主進化迴圈
    print("\n" + "="*80)
    print("進化開始")
    print("="*80)
    
    stagnation_count = 0
    max_stagnation = 100  # 最大停滯代數
    
    for gen in range(GENERATIONS):
        # 評估
        evaluated = []
        for ind in population:
            grid = decode_to_grid(ind, known_rows)
            fit, col_conf, box_conf = calc_total_fitness(grid)
            evaluated.append((ind, fit, col_conf, box_conf))
        
        # 排序
        evaluated.sort(key=lambda x: x[1], reverse=True)
        
        # 更新最佳
        current_best_fit = evaluated[0][1]
        if current_best_fit > best_fitness:
            best_fitness = current_best_fit
            best_individual = evaluated[0][0]
            stagnation_count = 0
        else:
            stagnation_count += 1
        
        fitness_history.append(best_fitness)
        
        # 統計
        col_fit = (16 - evaluated[0][2]) / 16
        box_fit = (16 - evaluated[0][3]) / 16
        col_fitness_history.append(col_fit)
        box_fitness_history.append(box_fit)
        
        elapsed = time.time() - start_time
        
        # 列印進度
        if gen % 50 == 0 or gen == GENERATIONS - 1:
            print(f"代數 {gen:4d}: fit={best_fitness:.4f} (列={col_fit:.3f}, 宮={box_fit:.3f}) "
                  f"衝突: 列={evaluated[0][2]}, 宮={evaluated[0][3]} | "
                  f"時間={elapsed:.1f}s | 停滯={stagnation_count}")
        
        # 檢查完美解
        if best_fitness >= 1.0:
            print(f"\n✅ 找到完美解！代數 {gen}, 時間 {elapsed:.1f}秒")
            break
        
        # 停滯檢查
        if stagnation_count >= max_stagnation:
            print(f"\n⚠️ 進化停滯 {stagnation_count} 代，嘗試增加突變率...")
            # 動態增加突變率
            for _ in range(50):
                mutate(population[random.randint(0, POPULATION_SIZE-1)], unknown_rows, row_perm_cache, 
                       mutation_rate=min(0.5, MUTATION_RATE + 0.1))
            stagnation_count = 0
        
        # 精英保留
        elite = [ind for ind, _, _, _ in evaluated[:ELITE_SIZE]]
        
        # 剪枝：移除低適應度個體
        if ENABLE_PRUNING:
            elite = [ind for ind, fit, _, _ in evaluated if fit >= PRUNING_THRESHOLD]
        
        # 新一代
        new_pop = elite.copy()
        while len(new_pop) < POPULATION_SIZE:
            p1 = tournament_select(population, [e[1] for e in evaluated])
            p2 = tournament_select(population, [e[1] for e in evaluated])
            
            child = crossover(p1, p2, unknown_rows)
            child = mutate(child, unknown_rows, row_perm_cache)
            new_pop.append(child)
        
        population = new_pop[:POPULATION_SIZE]
    
    # 建立最佳解
    best_grid = decode_to_grid(best_individual, known_rows)
    
    # 驗證
    elapsed_total = time.time() - start_time
    print("\n" + "="*80)
    print("最佳解驗證")
    print("="*80)
    
    total_fit, col_conflicts, box_conflicts = calc_total_fitness(best_grid)
    
    print(f"\n總適應度: {total_fit:.4f}")
    print(f"列適應度: {(16-col_conflicts)/16:.4f} ({col_conflicts} 個衝突)")
    print(f"宮適應度: {(16-box_conflicts)/16:.4f} ({box_conflicts} 個衝突)")
    print(f"總搜尋時間: {elapsed_total:.1f} 秒")
    
    # 顯示衝突詳情
    if col_conflicts > 0:
        print(f"\n列衝突詳情:")
        for j in range(16):
            col = [best_grid[i][j] for i in range(16)]
            counts = Counter(col)
            duplicates = [(v, c) for v, c in counts.items() if c > 1]
            if duplicates:
                print(f"   列{j}: {duplicates}")
    
    if box_conflicts > 0:
        print(f"\n宮衝突詳情:")
        for band in range(4):
            for stack in range(4):
                box = [best_grid[band*4+bi][stack*4+bj] for bi in range(4) for bj in range(4)]
                counts = Counter(box)
                duplicates = [(v, c) for v, c in counts.items() if c > 1]
                if duplicates:
                    print(f"   宮({band},{stack}): {duplicates}")
    
    # 保存結果
    output = {
        'best_fitness': total_fit,
        'column_fitness': (16-col_conflicts)/16,
        'box_fitness': (16-box_conflicts)/16,
        'column_conflicts': col_conflicts,
        'box_conflicts': box_conflicts,
        'fitness_history': fitness_history,
        'col_fitness_history': col_fitness_history,
        'box_fitness_history': box_fitness_history,
        'best_grid': best_grid,
        'best_individual': {f'row{i}': v[:4] for i, v in best_individual.items()},
        'parameters': {
            'population_size': POPULATION_SIZE,
            'generations': GENERATIONS,
            'mutation_rate': MUTATION_RATE,
            'crossover_rate': CROSSOVER_RATE,
            'elite_size': ELITE_SIZE,
            'perm_sample_size': PERM_SAMPLE_SIZE
        },
        'elapsed_time': elapsed_total,
        'final_stagnation': stagnation_count
    }
    
    with open('genetic_search_enhanced_result.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 結果已保存到: genetic_search_enhanced_result.json")
    
    # 顯示最佳網格
    print("\n" + "="*80)
    print("最佳解網格（全部16行）")
    print("="*80)
    row_labels_full = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
    for i, row in enumerate(best_grid):
        row_str = ' '.join(f'{v:2d}' for v in row)
        print(f"行{row_labels_full[i]:2s}: {row_str}")
    
    return output


if __name__ == '__main__':
    result = optimize()
