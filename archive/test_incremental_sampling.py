#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試增量多解空間採樣 - 集成到進化求解器

測試流程：
1. 載入符闔排列與已知解
2. 從解中採樣不同填滿率（10%, 15%, 20%, 25%）
3. 對每個填滿率執行增量採樣
4. 記錄解數量與多樣性變化
5. 生成完整報告
"""

import sys
import time
import json
import random
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from incremental_sampling_generator import (
    MultiSolutionSampler, SamplingStrategy,
    generate_incremental_sampling_report,
    IncrementalSamplingResult
)


def load_solution(filepath: str) -> List[List[int]]:
    """載入真實解"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def sample_given_cells(solution: List[List[int]], given_rate: float, 
                        seed: int = None) -> Dict[Tuple[int, int], int]:
    """從解中採樣已知數"""
    if seed is not None:
        random.seed(seed)
    
    positions = [(i, j) for i in range(16) for j in range(16)]
    random.shuffle(positions)
    
    n_givens = int(len(positions) * given_rate)
    given_cells = {}
    
    for i, j in positions[:n_givens]:
        given_cells[(i, j)] = solution[i][j]
    
    return given_cells


def run_incremental_sampling_experiment():
    """執行增量採樣實驗"""
    
    print("=" * 80)
    print("增量多解空間採樣實驗")
    print("=" * 80)
    
    # 1. 載入真實解
    solution_path = Path(__file__).parent / 'solution_v4_final.json'
    if not solution_path.exists():
        print("❌ 未找到 solution_v4_final.json")
        return
    
    solution = load_solution(str(solution_path))
    print(f"✅ 載入真實解: 16×16 網格")
    
    # 2. 測試不同填滿率
    test_rates = [0.10, 0.15, 0.20, 0.25]
    results = {}
    
    sampler = MultiSolutionSampler(grid_size=16, box_size=4)
    
    for given_rate in test_rates:
        print(f"\n{'='*60}")
        print(f"📊 填滿率: {given_rate*100:.0f}%")
        print(f"{'='*60}")
        
        # 採樣已知數
        given_cells = sample_given_cells(solution, given_rate, seed=42)
        print(f"   已知數: {len(given_cells)} 個")
        
        # 執行採樣
        start_time = time.time()
        result = sampler.sample_with_diversity(
            given_cells=given_cells,
            target_solutions=10,
            strategy=SamplingStrategy.DIVERSITY_MAXIMIZED,
            timeout=120
        )
        elapsed = time.time() - start_time
        
        results[given_rate] = result
        
        # 輸出結果摘要
        state_icon = "🔬" if result.solution_count == 1 else "⚛️" if result.solution_count > 1 else "❌"
        print(f"   {state_icon} 解數量: {result.solution_count}")
        print(f"   📈 採樣時間: {elapsed:.2f} 秒")
        print(f"   🌳 樹深度: {result.tree_depth}")
        print(f"   📊 多樣性: {result.diversity_score:.4f}")
        
        # 生成詳細報告
        report = generate_incremental_sampling_report(result, given_rate)
        
        # 保存報告
        report_path = Path(__file__).parent / f'incremental_sampling_rate_{int(given_rate*100)}.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"   💾 報告已保存: {report_path.name}")
    
    # 3. 生成實驗總結
    print(f"\n{'='*80}")
    print("📊 實驗總結")
    print(f"{'='*80}")
    
    summary_lines = [
        "# 增量多解空間採樣實驗總結\n",
        f"測試時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "\n## 填滿率 vs 解數量關係\n\n",
        "| 填滿率 | 已知數 | 解數量 | 多樣性評分 | 採樣時間(秒) | 狀態 |\n",
        "|--------|--------|--------|------------|--------------|------|\n"
    ]
    
    for rate, result in sorted(results.items()):
        state = "COLLAPSED" if result.solution_count == 1 else "SUPERPOSITION" if result.solution_count > 1 else "INFEASIBLE"
        summary_lines.append(
            f"| {rate*100:.0f}% | {int(256*rate)} | {result.solution_count} | {result.diversity_score:.4f} | {result.sampling_time:.2f} | {state} |\n"
        )
    
    summary_lines.append("\n## 關鍵發現\n\n")
    
    # 分析趨勢
    if len(results) >= 2:
        rates = sorted(results.keys())
        first_rate, last_rate = rates[0], rates[-1]
        
        if results[last_rate].solution_count < results[first_rate].solution_count:
            summary_lines.append(
                f"1. **填滿率增加導致解數量減少**: 從 {first_rate*100:.0f}% 到 {last_rate*100:.0f}%，"
                f"解數量從 {results[first_rate].solution_count} 減少到 {results[last_rate].solution_count}\n"
            )
        
        # 查找坍縮臨界點
        collapse_rate = None
        for rate in sorted(results.keys()):
            if results[rate].solution_count == 1:
                collapse_rate = rate
                break
        
        if collapse_rate:
            summary_lines.append(
                f"2. **坍縮臨界點**: 在 {collapse_rate*100:.0f}% 填滿率時系統坍縮至唯一解\n"
            )
        else:
            summary_lines.append(
                f"2. **未達坍縮**: 即使在 {max(rates)*100:.0f}% 填滿率下仍存在多解\n"
            )
    
    # 保存總結
    summary_path = Path(__file__).parent / 'incremental_sampling_summary.md'
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(''.join(summary_lines))
    
    print(f"📄 實驗總結已保存到: {summary_path}")
    
    # 4. 保存完整結果數據
    full_results = {
        'experiment_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'test_rates': [r for r in sorted(results.keys())],
        'results': {}
    }
    
    for rate, result in results.items():
        full_results['results'][str(rate)] = {
            'solution_count': result.solution_count,
            'diversity_score': result.diversity_score,
            'sampling_time': result.sampling_time,
            'tree_depth': result.tree_depth,
            'branching_factors': result.branching_factors,
            'solutions_sampled': len(result.solutions_collected)
        }
    
    full_results_path = Path(__file__).parent / 'incremental_sampling_full_results.json'
    with open(full_results_path, 'w', encoding='utf-8') as f:
        json.dump(full_results, f, indent=2, ensure_ascii=False)
    
    print(f"📊 完整結果已保存到: {full_results_path}")
    
    return results


if __name__ == "__main__":
    run_incremental_sampling_experiment()
