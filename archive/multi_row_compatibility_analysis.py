#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多先行相容性分析與遺傳演算法搜尋
對A、B、E、F、G、H、J、K、L、M、N、O行進行符闔排列相容性分析
使用遺傳演算法搜尋剩餘行的排列組合，驗證列約束和宮約束
"""

import openpyxl
import json
import math
import random
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum

# ============================================================
# 1. 數據載入模組
# ============================================================

class RowStatus(Enum):
    """先行狀態"""
    FULLY_KNOWN = "fully_known"      # 完全已知（16個已知數）
    PARTIAL_KNOWN = "partial_known"  # 部分已知
    UNKNOWN = "unknown"              # 未知（無已知數）


@dataclass
class RowInfo:
    """先行資訊"""
    label: str  # A, B, C, ...
    index: int  # 0-15
    given_cells: Dict[int, int]  # {col_index: value}
    given_count: int
    status: RowStatus
    permutation_pool: List[Dict]  # 該行的符闔排列池
    compatible_perms: List[Dict]  # 與已知數相容的排列


def load_puzzle_config(filepath: str) -> Tuple[List[List[int]], Dict[str, Dict[int, int]]]:
    """載入謎題配置，返回網格和每行的已知數"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    grid = [[0]*16 for _ in range(16)]
    row_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
    row_given_cells = {}
    
    # 解析每行的已知數
    row_pattern = r'行([A-P]) \[(.*?)\]'
    for match in re.finditer(row_pattern, content):
        row_label = match.group(1)
        values_str = match.group(2)
        values = [int(v.strip()) if v.strip() != '0' else 0 for v in values_str.split(',')]
        
        row_idx = ord(row_label) - ord('A')
        grid[row_idx] = values
        
        # 提取已知數（非0的值）
        given = {}
        for j, val in enumerate(values):
            if val != 0:
                given[j] = val
        
        row_given_cells[row_label] = given
    
    return grid, row_given_cells


def load_row_permutations(row_label: str, base_path: str = ".") -> List[Dict]:
    """載入指定行的符闔排列"""
    filename = f"{row_label}{get_row_chinese_name(row_label)}行符闔排列.xlsx"
    filepath = Path(base_path) / filename
    
    if not filepath.exists():
        print(f"⚠️ 未找到檔案: {filename}")
        return []
    
    try:
        wb = openpyxl.load_workbook(str(filepath), data_only=True)
        ws = wb.active
        
        permutations = []
        for row in ws.iter_rows(values_only=True):
            if len(row) < 20:
                continue
            
            # 提取排列值（位置3-18，跳過公式欄位）
            numeric_values = []
            for i in range(3, 19):
                if i < len(row):
                    val = row[i]
                    if isinstance(val, (int, float)) and 1 <= val <= 16:
                        numeric_values.append(int(val))
            
            if len(numeric_values) == 16:
                permutations.append({
                    'id': row[1],
                    'label': row[2],
                    'values': numeric_values
                })
        
        wb.close()
        return permutations
    except Exception as e:
        print(f"❌ 載入 {filename} 失敗: {e}")
        return []


def get_row_chinese_name(row_label: str) -> str:
    """獲取先行中文名"""
    chinese_names = {
        'A': '第一', 'B': '第二', 'C': '第三', 'D': '第四',
        'E': '第五', 'F': '第六', 'G': '第七', 'H': '第八',
        'I': '第九', 'J': '第十', 'K': '第十一', 'L': '第十二',
        'M': '第十三', 'N': '第十四', 'O': '第十五', 'P': '第十六'
    }
    return chinese_names.get(row_label, '')


def filter_compatible_permutations(permutations: List[Dict], given_cells: Dict[int, int]) -> List[Dict]:
    """過濾與已知數相容的排列"""
    if not given_cells:
        return permutations  # 無已知數，所有排列均相容
    
    compatible = []
    for perm in permutations:
        match = True
        for col, expected_val in given_cells.items():
            if col < len(perm['values']) and perm['values'][col] != expected_val:
                match = False
                break
        if match:
            compatible.append(perm)
    
    return compatible


# ============================================================
# 2. 相容性分析
# ============================================================

def analyze_all_rows_compatibility(puzzle_file: str, base_path: str = ".") -> Dict[str, RowInfo]:
    """分析所有先行的相容性"""
    
    print("=" * 80)
    print("多先行符闔排列相容性分析")
    print("=" * 80)
    
    # 載入謎題配置
    grid, row_given_cells = load_puzzle_config(puzzle_file)
    
    row_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
    row_info_dict = {}
    
    print("\n📊 謎題配置載入:")
    print(f"   網格大小: 16×16")
    print(f"   總先行: 16 行")
    
    # 統計已知數
    total_given = sum(len(given) for given in row_given_cells.values())
    print(f"   總已知數: {total_given}")
    
    # 分析每行
    for row_label in row_labels:
        row_idx = ord(row_label) - ord('A')
        given_cells = row_given_cells.get(row_label, {})
        given_count = len(given_cells)
        
        # 確定狀態
        if given_count == 16:
            status = RowStatus.FULLY_KNOWN
        elif given_count > 0:
            status = RowStatus.PARTIAL_KNOWN
        else:
            status = RowStatus.UNKNOWN
        
        # 載入排列池
        permutations = load_row_permutations(row_label, base_path)
        
        # 過濾相容排列
        compatible_perms = filter_compatible_permutations(permutations, given_cells)
        
        row_info = RowInfo(
            label=row_label,
            index=row_idx,
            given_cells=given_cells,
            given_count=given_count,
            status=status,
            permutation_pool=permutations,
            compatible_perms=compatible_perms
        )
        
        row_info_dict[row_label] = row_info
        
        # 輸出結果
        status_icon = {
            RowStatus.FULLY_KNOWN: "🔬",
            RowStatus.PARTIAL_KNOWN: "🔍",
            RowStatus.UNKNOWN: "❓"
        }
        
        print(f"\n{status_icon[status]} 行{row_label}:")
        print(f"   狀態: {status.value}")
        print(f"   已知數: {given_count} 個")
        print(f"   排列池: {len(permutations)} 個")
        print(f"   相容排列: {len(compatible_perms)} 個")
        
        if len(compatible_perms) > 0 and len(compatible_perms) <= 5:
            print(f"   相容排列列表:")
            for p in compatible_perms:
                print(f"      {p['label']}: {p['values']}")
        elif len(compatible_perms) > 5:
            print(f"   相容排列範例（前3個）:")
            for p in compatible_perms[:3]:
                print(f"      {p['label']}: {p['values']}")
    
    return row_info_dict


# ============================================================
# 3. 遺傳演算法搜尋
# ============================================================

class GeneticAlgorithmConfig:
    """遺傳演算法配置"""
    def __init__(self):
        self.population_size = 100
        self.generations = 500
        self.mutation_rate = 0.1
        self.crossover_rate = 0.7
        self.elite_size = 10
        self.tournament_size = 5


def calculate_column_fitness(grid: List[List[int]]) -> float:
    """計算列約束適應度（列AllDifferent）"""
    n = len(grid)
    conflicts = 0
    for j in range(n):
        col_vals = [grid[i][j] for i in range(n)]
        if len(set(col_vals)) < n:
            conflicts += 1
    return (n - conflicts) / n


def calculate_box_fitness(grid: List[List[int]], box_size: int = 4) -> float:
    """計算宮約束適應度（宮AllDifferent）"""
    n = len(grid)
    num_boxes = (n // box_size) ** 2
    conflicts = 0
    
    for band in range(n // box_size):
        for stack in range(n // box_size):
            box_vals = []
            for bi in range(box_size):
                for bj in range(box_size):
                    row = band * box_size + bi
                    col = stack * box_size + bj
                    box_vals.append(grid[row][col])
            if len(set(box_vals)) < box_size * box_size:
                conflicts += 1
    
    return (num_boxes - conflicts) / num_boxes


def calculate_total_fitness(grid: List[List[int]], box_size: int = 4) -> float:
    """總適應度 = 列適應度 × 0.5 + 宮適應度 × 0.5"""
    col_fit = calculate_column_fitness(grid)
    box_fit = calculate_box_fitness(grid, box_size)
    return col_fit * 0.5 + box_fit * 0.5


def create_individual(row_info_dict: Dict[str, RowInfo], unknown_rows: List[str]) -> Dict[str, int]:
    """建立個體：為每個未知先行隨機選擇一個相容排列"""
    individual = {}
    
    for row_label in unknown_rows:
        row_info = row_info_dict[row_label]
        if row_info.compatible_perms:
            # 從相容排列中隨機選擇
            selected = random.choice(row_info.compatible_perms)
            individual[row_label] = selected['id']
        else:
            # 無相容排列，從排列池中隨機選擇（可能與已知數衝突）
            if row_info.permutation_pool:
                selected = random.choice(row_info.permutation_pool)
                individual[row_label] = selected['id']
            else:
                individual[row_label] = 0  # 預設值
    
    return individual


def decode_individual(individual: Dict[str, int], row_info_dict: Dict[str, RowInfo]) -> List[List[int]]:
    """將個體解碼為網格"""
    grid = [[0]*16 for _ in range(16)]
    
    # 填入已知行
    for row_label, row_info in row_info_dict.items():
        if row_info.status == RowStatus.FULLY_KNOWN:
            # 該行已完全確定，需要從相容排列中取得
            if row_info.compatible_perms:
                # 只有一個相容排列
                grid[row_info.index] = row_info.compatible_perms[0]['values'].copy()
            else:
                # 從排列池中找匹配已知數的排列
                for perm in row_info.permutation_pool:
                    match = True
                    for col, val in row_info.given_cells.items():
                        if perm['values'][col] != val:
                            match = False
                            break
                    if match:
                        grid[row_info.index] = perm['values'].copy()
                        break
        elif row_label in individual:
            # 未知行，從選擇的排列ID取得值
            selected_id = individual[row_label]
            row_info = row_info_dict[row_label]
            
            # 找到對應排列
            selected_perm = None
            for perm in row_info.compatible_perms:
                if perm['id'] == selected_id:
                    selected_perm = perm
                    break
            
            if not selected_perm:
                for perm in row_info.permutation_pool:
                    if perm['id'] == selected_id:
                        selected_perm = perm
                        break
            
            if selected_perm:
                grid[row_info.index] = selected_perm['values'].copy()
            else:
                # 預設使用第一個相容排列
                if row_info.compatible_perms:
                    grid[row_info.index] = row_info.compatible_perms[0]['values'].copy()
    
    return grid


def genetic_optimization(row_info_dict: Dict[str, RowInfo], 
                         unknown_rows: List[str],
                         config: GeneticAlgorithmConfig,
                         max_iterations: int = 1000) -> Tuple[Dict, float, List]:
    """遺傳演算法優化"""
    
    print("\n" + "=" * 80)
    print("遺傳演算法搜尋")
    print("=" * 80)
    
    # 初始化種群
    population = [create_individual(row_info_dict, unknown_rows) for _ in range(config.population_size)]
    
    best_fitness = 0.0
    best_individual = None
    fitness_history = []
    
    for gen in range(config.generations):
        # 評估每個個體
        evaluated = []
        for individual in population:
            grid = decode_individual(individual, row_info_dict)
            fitness = calculate_total_fitness(grid)
            evaluated.append((individual, fitness))
        
        # 排序
        evaluated.sort(key=lambda x: x[1], reverse=True)
        
        # 更新最佳解
        if evaluated[0][1] > best_fitness:
            best_fitness = evaluated[0][1]
            best_individual = evaluated[0][0]
        
        fitness_history.append(best_fitness)
        
        # 輸出進度
        if gen % 50 == 0:
            print(f"   代數 {gen:4d}: 最佳適應度 = {best_fitness:.4f}")
        
        # 如果找到完美解，提前終止
        if best_fitness >= 1.0:
            print(f"   ✅ 找到完美解！適應度 = {best_fitness:.4f}")
            break
        
        # 精英保留
        elite = [ind for ind, _ in evaluated[:config.elite_size]]
        
        # 建立新一代
        new_population = elite.copy()
        
        while len(new_population) < config.population_size:
            # 選擇
            parent1 = tournament_selection(evaluated, config.tournament_size)
            parent2 = tournament_selection(evaluated, config.tournament_size)
            
            # 交叉
            if random.random() < config.crossover_rate:
                child = crossover(parent1, parent2)
            else:
                child = parent1.copy()
            
            # 突變
            mutate(child, unknown_rows, row_info_dict, config.mutation_rate)
            
            new_population.append(child)
        
        population = new_population[:config.population_size]
    
    return best_individual, best_fitness, fitness_history


def tournament_selection(evaluated: List[Tuple[Dict, float]], tournament_size: int) -> Dict:
    """競賽選擇"""
    tournament = random.sample(evaluated, min(tournament_size, len(evaluated)))
    return max(tournament, key=lambda x: x[1])[0]


def crossover(parent1: Dict, parent2: Dict) -> Dict:
    """交叉"""
    child = {}
    for key in parent1:
        if random.random() < 0.5:
            child[key] = parent1[key]
        else:
            child[key] = parent2[key]
    return child


def mutate(individual: Dict, unknown_rows: List[str], 
           row_info_dict: Dict[str, RowInfo], mutation_rate: float):
    """突變"""
    for row_label in unknown_rows:
        if random.random() < mutation_rate:
            row_info = row_info_dict[row_label]
            if row_info.compatible_perms:
                selected = random.choice(row_info.compatible_perms)
            elif row_info.permutation_pool:
                selected = random.choice(row_info.permutation_pool)
            else:
                selected = {'id': 0}
            individual[row_label] = selected['id']


# ============================================================
# 4. 約束驗證
# ============================================================

def verify_solution(grid: List[List[int]], box_size: int = 4) -> Dict:
    """驗證解的約束滿足情況"""
    n = len(grid)
    
    result = {
        'row_valid': True,
        'column_valid': True,
        'box_valid': True,
        'row_details': [],
        'column_details': [],
        'box_details': [],
        'total_errors': 0
    }
    
    # 檢查行
    for i in range(n):
        row_vals = grid[i]
        if len(set(row_vals)) != n:
            result['row_valid'] = False
            duplicates = [v for v, c in Counter(row_vals).items() if c > 1]
            result['row_details'].append({
                'row': i,
                'error': 'duplicates',
                'values': duplicates
            })
            result['total_errors'] += 1
    
    # 檢查列
    for j in range(n):
        col_vals = [grid[i][j] for i in range(n)]
        if len(set(col_vals)) != n:
            result['column_valid'] = False
            duplicates = [v for v, c in Counter(col_vals).items() if c > 1]
            result['column_details'].append({
                'col': j,
                'error': 'duplicates',
                'values': duplicates
            })
            result['total_errors'] += 1
    
    # 檢查宮
    for band in range(n // box_size):
        for stack in range(n // box_size):
            box_vals = []
            for bi in range(box_size):
                for bj in range(box_size):
                    row = band * box_size + bi
                    col = stack * box_size + bj
                    box_vals.append(grid[row][col])
            
            if len(set(box_vals)) != box_size * box_size:
                result['box_valid'] = False
                duplicates = [v for v, c in Counter(box_vals).items() if c > 1]
                result['box_details'].append({
                    'box': (band, stack),
                    'error': 'duplicates',
                    'values': duplicates
                })
                result['total_errors'] += 1
    
    result['is_valid'] = result['row_valid'] and result['column_valid'] and result['box_valid']
    
    return result


# ============================================================
# 5. 主程式
# ============================================================

def main():
    """主程式"""
    
    print("=" * 80)
    print("多先行相容性分析與遺傳演算法搜尋")
    print("符闔博弈優選策略 V19.0")
    print("=" * 80)
    
    # 設定隨機種子（確保可重現）
    random.seed(42)
    
    # 1. 相容性分析
    row_info_dict = analyze_all_rows_compatibility('超級大數獨_box_size4.txt')
    
    # 2. 識別未知先行
    unknown_rows = [label for label, info in row_info_dict.items() 
                   if info.status != RowStatus.FULLY_KNOWN and len(info.compatible_perms) > 1]
    
    fully_known_rows = [label for label, info in row_info_dict.items() 
                       if info.status == RowStatus.FULLY_KNOWN]
    
    partial_rows = [label for label, info in row_info_dict.items() 
                   if info.status == RowStatus.PARTIAL_KNOWN and len(info.compatible_perms) == 1]
    
    print("\n" + "=" * 80)
    print("先行分類總結")
    print("=" * 80)
    print(f"\n🔬 完全確定先行 ({len(fully_known_rows)} 行): {', '.join(fully_known_rows)}")
    print(f"\n🔍 單相容排列先行 ({len(partial_rows)} 行): {', '.join(partial_rows)}")
    print(f"\n🎯 多相容排列先行 ({len(unknown_rows)} 行): {', '.join(unknown_rows)}")
    
    # 3. 遺傳演算法搜尋
    if unknown_rows:
        config = GeneticAlgorithmConfig()
        config.generations = 300
        config.population_size = 80
        
        best_individual, best_fitness, fitness_history = genetic_optimization(
            row_info_dict, unknown_rows, config
        )
        
        # 4. 建立最佳解網格
        best_grid = decode_individual(best_individual, row_info_dict)
        
        # 5. 驗證解
        print("\n" + "=" * 80)
        print("解驗證")
        print("=" * 80)
        
        verification = verify_solution(best_grid)
        
        print(f"\n📊 驗證結果:")
        print(f"   行約束: {'✅ 滿足' if verification['row_valid'] else '❌ 不滿足'}")
        print(f"   列約束: {'✅ 滿足' if verification['column_valid'] else '❌ 不滿足'}")
        print(f"   宮約束: {'✅ 滿足' if verification['box_valid'] else '❌ 不滿足'}")
        print(f"   總錯誤數: {verification['total_errors']}")
        print(f"   適應度: {best_fitness:.4f}")
        
        if verification['is_valid']:
            print("\n🎉 找到有效解！")
        else:
            print("\n⚠️ 解仍存在一些約束衝突，需要進一步優化")
        
        # 6. 保存結果
        output_data = {
            'analysis_summary': {
                'fully_known_rows': fully_known_rows,
                'single_compatible_rows': partial_rows,
                'multiple_compatible_rows': unknown_rows
            },
            'genetic_optimization': {
                'best_fitness': best_fitness,
                'generations_run': len(fitness_history),
                'fitness_history': fitness_history[-50:]  # 最後50代
            },
            'verification': verification,
            'best_individual': best_individual,
            'best_grid': best_grid
        }
        
        with open('multi_row_analysis_result.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 結果已保存到: multi_row_analysis_result.json")
        
        # 7. 生成報告
        generate_final_report(row_info_dict, unknown_rows, best_individual, 
                            best_fitness, verification, fitness_history)
    
    else:
        print("\n✅ 所有先行都已確定，無需遺傳演算法搜尋")
    
    return row_info_dict


def generate_final_report(row_info_dict: Dict[str, RowInfo], 
                         unknown_rows: List[str],
                         best_individual: Dict,
                         best_fitness: float,
                         verification: Dict,
                         fitness_history: List[float]):
    """生成最終報告"""
    
    report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    多先行相容性分析與遺傳演算法搜尋報告                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  分析時間: 2026-05-17 03:41 GMT+8                                                ║
║  版本: V19.0                                                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 先行分類總結
───────────────────────────────────────────────────────────────────────────────

"""
    
    # 完全確定先行
    report += "🔬 完全確定先行:\n"
    for label in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']:
        info = row_info_dict[label]
        if info.status == RowStatus.FULLY_KNOWN:
            report += f"   行{label}: 16個已知數，排列池 {len(info.permutation_pool)} 個，相容 {len(info.compatible_perms)} 個\n"
    
    # 單相容排列先行
    report += "\n🔍 單相容排列先行:\n"
    for label in unknown_rows:
        info = row_info_dict[label]
        if len(info.compatible_perms) == 1:
            report += f"   行{label}: 已知數 {info.given_count} 個，唯一相容排列: {info.compatible_perms[0]['label']}\n"
    
    # 多相容排列先行
    report += f"\n🎯 多相容排列先行 ({len(unknown_rows)} 行):\n"
    for label in unknown_rows:
        info = row_info_dict[label]
        report += f"   行{label}: 已知數 {info.given_count} 個，相容排列 {len(info.compatible_perms)} 個\n"
    
    report += f"""
🧬 遺傳演算法搜尋結果
───────────────────────────────────────────────────────────────────────────────
   適應度: {best_fitness:.4f}
   搜索代數: {len(fitness_history)}
   最終列約束滿足率: {calculate_column_fitness(decode_individual(best_individual, row_info_dict))*100:.1f}%
   最終宮約束滿足率: {calculate_box_fitness(decode_individual(best_individual, row_info_dict))*100:.1f}%

🔮 約束驗證結果
───────────────────────────────────────────────────────────────────────────────
   行約束: {'✅ 滿足' if verification['row_valid'] else '❌ 不滿足'}
   列約束: {'✅ 滿足' if verification['column_valid'] else '❌ 不滿足'}
   宮約束: {'✅ 滿足' if verification['box_valid'] else '❌ 不滿足'}
   總錯誤數: {verification['total_errors']}

"""
    
    if verification['is_valid']:
        report += """🎉 成功找到有效解！
   所有行、列、宮約束均滿足。
"""
    else:
        report += f"""⚠️ 解仍存在一些約束衝突。
   列衝突: {len(verification['column_details'])} 處
   宮衝突: {len(verification['box_details'])} 處
   建議: 增加遺傳演算法代數或調整參數
"""
    
    report += f"""
📁 輸出檔案
───────────────────────────────────────────────────────────────────────────────
   • multi_row_analysis_result.json - 完整分析數據
   • multi_row_compatibility_report.md - 本報告

✅ 分析完成
"""
    
    print(report)
    
    # 保存報告
    with open('multi_row_compatibility_report.md', 'w', encoding='utf-8') as f:
        f.write(report)


if __name__ == "__main__":
    main()
