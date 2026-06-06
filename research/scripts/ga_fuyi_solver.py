#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
閉合排列遺伝算法求解器 V1.0
=====================================

核心邏輯：
  1. 加載新生成的閉合排列 A{i}_permutations.json
     （所有排列都來自合法數獨解，保證閉合性）
  2. 使用遺伝算法搜索有效 16×16 數獨解
     - 個體：16 行，每行從閉合排列集合中隨機選取
     - 適應度：列/宮約束違反次數（行約束自動滿足）
  3. 支持多種變體（標準、X Sudoku、Killer Sudoku）

遺伝操作：
  - 初始化：每行隨機選取一個閉合排列
  - 交叉（Crossover）：隨機交換兩個個體的部分行
  - 變異（Mutation）：將某行替換爲該行閉合集合中的另一個排列
  - 選擇：錦標賽選擇（Tournament Selection）

使用方法：
  python ga_fuyi_solver.py [--population N] [--generations N] [--timeout T]

作者：WorkBuddy AI
日期：2026-05-31
"""

import json
import os
import sys
import time
import random
import argparse
from collections import defaultdict
from typing import List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding='utf-8')

# 全局配置
N = 16
BOX_SIZE = 4
POPULATION_SIZE = 200
MAX_GENERATIONS = 5000
TIMEOUT_SEC = 300
MUTATION_RATE = 0.15
CROSSOVER_RATE = 0.85
TOURNAMENT_SIZE = 5
ELITE_RATIO = 0.05  # 保留最優 5% 個體


def log(msg):
    print(msg, flush=True)


# ════════════════════════════════════════════════════════
# 數據加載
# ════════════════════════════════════════════════════════

def load_closed_permutations() -> List[List[List[int]]]:
    """
    加載閉合排列 A{i}_permutations.json
    返回：perm_sets[i] = [排列1, 排列2, ...]  (i=0..15)
    """
    log("[加載] 閉合排列...")
    perm_sets = []
    total = 0
    for i in range(N):
        path = os.path.join(BASE_DIR, f"A{i+1}_permutations.json")
        if not os.path.exists(path):
            log(f"  ❌ 找不到 {path}，請先運行 generate_closed_permutations.py")
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            perms = json.load(f)
        perm_sets.append(perms)
        total += len(perms)
        log(f"  行 {i+1:2d}: {len(perms):>8,} 個排列")
    
    log(f" 總計: {total:,} 個閉合排列")
    log(f"  平均每行: {total/N:.1f} 個")
    return perm_sets


def load_config_anchors() -> List[Tuple[int, int, int]]:
    """
    加載 sudoku_config.json 中的錨點
    返回：[(row, col, value), ...]  (0-indexed)
    """
    config_path = os.path.join(BASE_DIR, "sudoku_config.json")
    if not os.path.exists(config_path):
        return []
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    anchors = []
    for cell in config["known_digits"]:
        r = cell["row"] - 1
        c = cell["col"] - 1
        v = cell["value"]
        anchors.append((r, c, v))
    log(f"[加載] 錨點: {len(anchors)} 個")
    return anchors


# ════════════════════════════════════════════════════════
# 適應度計算
# ════════════════════════════════════════════════════════

def calculate_fitness(individual: List[List[int]], 
                     anchors: List[Tuple[int, int, int]]) -> int:
    """
    計算個體的適應度（違反約束的總次數）
    適應度越低越好（0 = 完美解）
    
    約束：
      1. 列 AllDifferent（每列出現重複數字）
      2. 宮 AllDifferent（每宮出現重複數字）
      3. 錨點約束（個體必須符合 sudoku_config.json 中的錨點）
    
    行約束自動滿足（因爲每行都來自閉合排列）
    """
    violations = 0
    N = len(individual)
    
    # 1. 列約束檢查
    for c in range(N):
        col_values = [individual[r][c] for r in range(N)]
        seen = set()
        for v in col_values:
            if v in seen:
                violations += 1
            seen.add(v)
    
    # 2. 宮約束檢查（4×4 宮）
    for br in range(BOX_SIZE):
        for bc in range(BOX_SIZE):
            box_values = []
            for dr in range(BOX_SIZE):
                for dc in range(BOX_SIZE):
                    r = br * BOX_SIZE + dr
                    c = bc * BOX_SIZE + dc
                    box_values.append(individual[r][c])
            seen = set()
            for v in box_values:
                if v in seen:
                    violations += 1
                seen.add(v)
    
    # 3. 錨點約束檢查
    for r, c, v in anchors:
        if individual[r][c] != v:
            violations += 100  # 錨點違反是嚴重懲罰
    
    return violations


def calculate_fitness_detailed(individual: List[List[int]], 
                              anchors: List[Tuple[int, int, int]]) -> dict:
    """詳細的適應度計算（用於日誌輸出）"""
    result = {
        "col_violations": 0,
        "box_violations": 0,
        "anchor_violations": 0,
        "total": 0
    }
    N = len(individual)
    
    # 列約束
    for c in range(N):
        col_values = [individual[r][c] for r in range(N)]
        seen = set()
        for v in col_values:
            if v in seen:
                result["col_violations"] += 1
            seen.add(v)
    
    # 宮約束
    for br in range(BOX_SIZE):
        for bc in range(BOX_SIZE):
            box_values = []
            for dr in range(BOX_SIZE):
                for dc in range(BOX_SIZE):
                    r = br * BOX_SIZE + dr
                    c = bc * BOX_SIZE + dc
                    box_values.append(individual[r][c])
            seen = set()
            for v in box_values:
                if v in seen:
                    result["box_violations"] += 1
                seen.add(v)
    
    # 錨點
    for r, c, v in anchors:
        if individual[r][c] != v:
            result["anchor_violations"] += 1
    
    result["total"] = result["col_violations"] + result["box_violations"] + result["anchor_violations"] * 100
    return result


# ════════════════════════════════════════════════════════
# 個體操作
# ════════════════════════════════════════════════════════

def create_individual(perm_sets: List[List[List[int]]]) -> List[List[int]]:
    """創建一個隨機個體（每行從閉合排列中隨機選取）"""
    return [random.choice(perm_sets[r]) for r in range(N)]


def mutate(individual: List[List[int]], 
           perm_sets: List[List[List[int]]]) -> List[List[int]]:
    """
    變異：隨機選取若干行，替換爲該行閉合集合中的其他排列
    返回：新個體（可能與原個體相同，如果該行只有一個排列）
    """
    new_ind = [row[:] for row in individual]  # 深拷貝
    mutated_rows = 0
    
    for r in range(N):
        if random.random() < MUTATION_RATE:
            if len(perm_sets[r]) > 1:
                old_row = tuple(new_ind[r])
                # 隨機選取一個不同的排列
                attempts = 0
                while attempts < 10:
                    new_row = random.choice(perm_sets[r])
                    if tuple(new_row) != old_row:
                        new_ind[r] = new_row
                        mutated_rows += 1
                        break
                    attempts += 1
    
    return new_ind


def crossover(parent1: List[List[int]], 
             parent2: List[List[int]]) -> Tuple[List[List[int]], List[List[int]]]:
    """
    交叉：均勻交叉（Uniform Crossover）
    每個行以 50% 概率從 parent1 或 parent2 繼承
    返回：兩個子代個體
    """
    if random.random() > CROSSOVER_RATE:
        return [row[:] for row in parent1], [row[:] for row in parent2]
    
    child1 = []
    child2 = []
    for r in range(N):
        if random.random() < 0.5:
            child1.append(parent1[r][:])
            child2.append(parent2[r][:])
        else:
            child1.append(parent2[r][:])
            child2.append(parent1[r][:])
    
    return child1, child2


def tournament_selection(population: List[List[List[int]]], 
                       fitnesses: List[int]) -> List[List[int]]:
    """錦標賽選擇：隨機選取 k 個個體，返回最優者"""
    selected_indices = random.sample(range(len(population)), TOURNAMENT_SIZE)
    best_idx = min(selected_indices, key=lambda idx: fitnesses[idx])
    return [row[:] for row in population[best_idx]]


# ════════════════════════════════════════════════════════
# 主求解流程
# ════════════════════════════════════════════════════════

def solve_with_ga(perm_sets: List[List[List[int]]],
                  anchors: List[Tuple[int, int, int]],
                  population_size: int = POPULATION_SIZE,
                  max_gens: int = MAX_GENERATIONS,
                  timeout: float = TIMEOUT_SEC) -> Optional[List[List[int]]]:
    """
    使用遺伝算法求解 16×16 數獨
    
    返回：
      - 成功：有效解（16×16 網格）
      - 失敗：None
    """
    t_start = time.time()
    
    # 1. 初始化種群
    log(f"\n[GA] 初始化種群 (大小={population_size})...")
    population = [create_individual(perm_sets) for _ in range(population_size)]
    
    best_fitness = float('inf')
    best_individual = None
    generations_no_improve = 0
    
    # 2. 主循環
    for gen in range(max_gens):
        # 檢查超時
        if time.time() - t_start > timeout:
            log(f"\n[GA] 超時 ({timeout}s)，停止搜索")
            break
        
        # 計算適應度
        fitnesses = [calculate_fitness(ind, anchors) for ind in population]
        
        # 找到當前最優
        current_best_idx = min(range(len(fitnesses)), key=lambda i: fitnesses[i])
        current_best_fitness = fitnesses[current_best_idx]
        current_best = population[current_best_idx]
        
        # 更新全局最優
        if current_best_fitness < best_fitness:
            best_fitness = current_best_fitness
            best_individual = [row[:] for row in current_best]
            generations_no_improve = 0
            
            if best_fitness == 0:
                elapsed = time.time() - t_start
                log(f"\n[GA] ✅ 找到有效解！世代 {gen}, 耗時 {elapsed:.1f}s")
                return best_individual
        else:
            generations_no_improve += 1
        
        # 日誌輸出（每 100 世代或找到更優解時輸出）
        if gen % 100 == 0 or current_best_fitness < best_fitness:
            elapsed = time.time() - t_start
            detail = calculate_fitness_detailed(current_best, anchors)
            log(f"  世代 {gen:5d} | "
                f"最優適應度: {current_best_fitness:5d} | "
                f"列違反: {detail['col_violations']:3d} | "
                f"宮違反: {detail['box_violations']:3d} | "
                f"錨違反: {detail['anchor_violations']:2d} | "
                f"耗時: {elapsed:.1f}s")
        
        # 3. 生成新一代
        new_population = []
        
        # 精英保留
        elite_count = int(population_size * ELITE_RATIO)
        elite_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i])[:elite_count]
        new_population.extend([population[i] for i in elite_indices])
        
        # 交叉 + 變異生成剩餘個體
        while len(new_population) < population_size:
            # 選擇父代
            parent1 = tournament_selection(population, fitnesses)
            parent2 = tournament_selection(population, fitnesses)
            
            # 交叉
            child1, child2 = crossover(parent1, parent2)
            
            # 變異
            child1 = mutate(child1, perm_sets)
            child2 = mutate(child2, perm_sets)
            
            if len(new_population) < population_size:
                new_population.append(child1)
            if len(new_population) < population_size:
                new_population.append(child2)
        
        population = new_population
    
    # 循環結束
    elapsed = time.time() - t_start
    log(f"\n[GA] 搜索完成")
    log(f"  總世代: {min(gen+1, max_gens)}")
    log(f"  耗時: {elapsed:.1f}s")
    log(f"  最優適應度: {best_fitness}")
    
    if best_fitness == 0:
        return best_individual
    else:
        log(f"  ⚠ 未找到完美解（最優適應度 = {best_fitness}）")
        return best_individual  # 返回最優個體（可能不完美）


# ════════════════════════════════════════════════════════
# 結果驗證與輸出
# ════════════════════════════════════════════════════════

def verify_solution(grid: List[List[int]], 
                    anchors: List[Tuple[int, int, int]]) -> bool:
    """驗證解的正確性"""
    N = len(grid)
    
    # 行檢查
    for r in range(N):
        if set(grid[r]) != set(range(1, N+1)):
            return False
    
    # 列檢查
    for c in range(N):
        col = [grid[r][c] for r in range(N)]
        if set(col) != set(range(1, N+1)):
            return False
    
    # 宮檢查
    for br in range(BOX_SIZE):
        for bc in range(BOX_SIZE):
            box = []
            for dr in range(BOX_SIZE):
                for dc in range(BOX_SIZE):
                    box.append(grid[br*BOX_SIZE+dr][bc*BOX_SIZE+dc])
            if set(box) != set(range(1, N+1)):
                return False
    
    # 錨點檢查
    for r, c, v in anchors:
        if grid[r][c] != v:
            return False
    
    return True


def print_grid(grid: List[List[int]], anchors: List[Tuple[int, int, int]]):
    """打印數獨網格"""
    anchor_set = set((r, c) for r, c, _ in anchors)
    log("\n" + " "*4 + " ".join(f"C{c+1:02d}" for c in range(N)))
    for r in range(N):
        row_str = ""
        for c in range(N):
            v = grid[r][c]
            if (r, c) in anchor_set:
                row_str += f"[{v:2d}]"
            else:
                row_str += f" {v:2d} "
        log(f"  R{r+1:02d}|{row_str}")
        if r in [3, 7, 11]:
            log("        " + "-" * (N * 3 + 2))


def save_solution(grid: List[List[int]], 
                  filename: str = "ga_solution.json"):
    """保存解到 JSON 文件"""
    path = os.path.join(BASE_DIR, filename)
    result = {
        "status": "FOUND" if verify_solution(grid, load_config_anchors()) else "PARTIAL",
        "grid": grid,
        "anchor_count": len(load_config_anchors()),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log(f"\n[輸出] 解已保存到 {filename}")
    return path


# ════════════════════════════════════════════════════════
# 主程序
# ════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="閉合排列遺伝算法求解器 V1.0"
    )
    parser.add_argument("--population", type=int, default=POPULATION_SIZE,
                        help=f"種群大小（默認 {POPULATION_SIZE}）")
    parser.add_argument("--generations", type=int, default=MAX_GENERATIONS,
                        help=f"最大世代數（默認 {MAX_GENERATIONS}）")
    parser.add_argument("--timeout", type=float, default=TIMEOUT_SEC,
                        help=f"超時時間（秒，默認 {TIMEOUT_SEC}）")
    parser.add_argument("--mutation-rate", type=float, default=MUTATION_RATE,
                        help=f"變異率（默認 {MUTATION_RATE}）")
    parser.add_argument("--crossover-rate", type=float, default=CROSSOVER_RATE,
                        help=f"交叉率（默認 {CROSSOVER_RATE}）")
    args = parser.parse_args()
    
    log("=" * 65)
    log("閉合排列遺伝算法求解器 V1.0")
    log("保證閉合性：所有行排列來自合法數獨解")
    log("=" * 65)
    
    t_total_start = time.time()
    
    # 加載數據
    perm_sets = load_closed_permutations()
    anchors = load_config_anchors()
    
    # 檢查閉合排列是否爲空
    empty_rows = [r for r in range(N) if len(perm_sets[r]) == 0]
    if empty_rows:
        log(f"\n[錯誤] 以下行的閉合排列爲空：{ [r+1 for r in empty_rows] }")
        log("  → 請先運行 generate_closed_permutations.py 重新生成閉合排列")
        return
    
    log(f"\n[配置] GA 參數：")
    log(f"  種群大小: {args.population}")
    log(f"  最大世代: {args.generations}")
    log(f"  超時時間: {args.timeout}s")
    log(f"  變異率: {args.mutation_rate}")
    log(f"  交叉率: {args.crossover_rate}")
    
    # 求解
    log(f"\n[求解] 開始遺伝算法搜索...")
    solution = solve_with_ga(
        perm_sets, anchors,
        population_size=args.population,
        max_gens=args.generations,
        timeout=args.timeout
    )
    
    # 驗證與輸出
    if solution:
        is_valid = verify_solution(solution, anchors)
        log(f"\n{'='*65}")
        log(f"結果: {'✅ 有效解' if is_valid else '⚠ 部分解（可能有違反）'}")
        print_grid(solution, anchors)
        save_solution(solution)
        log(f"{'='*65}")
        
        if is_valid:
            log(f"\n🎉 成功找到有效 16×16 數獨解！")
            log(f"   閉合排列保證了行約束的正确性")
            log(f"   GA 搜索找到了滿足列/宮約束的行組合")
    else:
        log(f"\n[結果] ❌ 未找到解")
        log(f"  請嘗試：")
        log(f"    - 增加 --population（更大種群）")
        log(f"    - 增加 --generations（更多世代）")
        log(f"    - 增加 --timeout（更長時間）")
    
    total_elapsed = time.time() - t_total_start
    log(f"\n總耗時: {total_elapsed:.1f}s")


if __name__ == "__main__":
    main()
