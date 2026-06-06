#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 符闔博弈優選策略 V19.1 - 數獨變體測試演示
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

測試 100D 基因指紋在三個數獨變體上的應用：
  1. 標準數獨 (Standard Sudoku)
  2. X Sudoku (對角線約束)
  3. Killer Sudoku (Cage 求和約束)

每種變體測試：
  - 基因指紋計算
  - 適應度評估
  - 約束驗證
  - 量子態判斷
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import random
from typing import Dict, List, Tuple
from genetic_optimizer_v19 import (
    GeneFingerprint100D, Individual, GeneticOptimizer,
    QuantumState
)
from sudoku_variants_v19 import (
    SudokuVariantType, XsudokuVariant, KillersudokuVariant,
    GeneFingerprint100DAdapter
)


def create_test_grid(variant_type: str, seed: int = 42) -> Tuple[List[List[int]], Dict]:
    """創建測試網格和已知位置"""
    random.seed(seed)
    grid_size = 16
    
    # 創建空網格
    grid = [[0] * grid_size for _ in range(grid_size)]
    known_positions = {}
    
    if variant_type == "standard":
        # 標準數獨：隨機填入一些已知位置
        for _ in range(30):
            r = random.randint(0, 15)
            c = random.randint(0, 15)
            if (r, c) not in known_positions:
                grid[r][c] = random.randint(1, 16)
                known_positions[(r, c)] = grid[r][c]
    
    elif variant_type == "x_sudoku":
        # X Sudoku：確保對角線有已知值
        # 主對角線
        for i in range(8):
            grid[i][i] = (i + 1) % 16 + 1
            known_positions[(i, i)] = grid[i][i]
        # 副對角線
        for i in range(8):
            r, c = i, 15 - i
            if (r, c) not in known_positions:
                grid[r][c] = (i + 9) % 16 + 1
                known_positions[(r, c)] = grid[r][c]
        
        # 其他隨機位置
        for _ in range(20):
            r = random.randint(0, 15)
            c = random.randint(0, 15)
            if (r, c) not in known_positions:
                grid[r][c] = random.randint(1, 16)
                known_positions[(r, c)] = grid[r][c]
    
    elif variant_type == "killer_sudoku":
        # Killer Sudoku：建立 Cage 和對應已知值
        cages = [
            {'cells': [(0, 0), (0, 1), (1, 0)], 'target_sum': 6},
            {'cells': [(0, 2), (0, 3), (1, 2)], 'target_sum': 7},
            {'cells': [(1, 1), (2, 0), (2, 1)], 'target_sum': 8},
        ]
        
        # 填入 Cage 中的已知值
        for cage in cages:
            cells = cage['cells']
            target = cage['target_sum']
            # 簡單分配：第一個格填 1，其餘分攤
            grid[cells[0][0]][cells[0][1]] = 1
            known_positions[cells[0]] = 1
            remaining = target - 1
            for i, cell in enumerate(cells[1:], 1):
                val = min(remaining - (len(cells) - i - 1), 16)
                val = max(1, val)
                grid[cell[0]][cell[1]] = val
                known_positions[cell] = val
        
        # 其他隨機位置
        for _ in range(20):
            r = random.randint(0, 15)
            c = random.randint(0, 15)
            if (r, c) not in known_positions:
                grid[r][c] = random.randint(1, 16)
                known_positions[(r, c)] = grid[r][c]
    
    return grid, known_positions


def test_standard_sudoku():
    """測試標準數獨"""
    print("\n" + "=" * 70)
    print("┌─ 測試 1: 標準數獨 (Standard Sudoku) ─────────────────┐")
    print("└───────────────────────────────────────────────────┘")
    
    grid, known_positions = create_test_grid("standard", seed=42)
    
    # 計算 100D 基因指紋
    gene_fp = GeneFingerprint100D()
    gene_fp.compute(grid, known_positions, variant=None)
    
    # 計算個體適應度
    individual = Individual(grid=grid)
    individual.compute_fitness(known_positions, {}, {}, variant=None)
    
    # 驗證
    from genetic_optimizer_v19 import cp_sat_verify
    cp_sat_result = cp_sat_verify(individual, known_positions, solution_limit=5)
    
    print(f"\n  已知位置數: {len(known_positions)}")
    print(f"  100D 基因指紋:")
    print(f"    行維度均值: {sum(gene_fp.row_dimensions)/16:.4f}")
    print(f"    列維度均值: {sum(gene_fp.col_dimensions)/16:.4f}")
    print(f"    宮維度均值: {sum(gene_fp.box_dimensions)/16:.4f}")
    print(f"    總體適應度: {gene_fp.total_fitness():.4f}")
    print(f"    個體適應度: {individual.fitness:.4f}")
    
    print(f"\n  CP-SAT 驗證:")
    print(f"    有效: {'✅ 是' if cp_sat_result['valid'] else '❌ 否'}")
    print(f"    列衝突: {cp_sat_result['col_conflicts']}")
    print(f"    宮衝突: {cp_sat_result['box_conflicts']}")
    
    # 判斷量子態
    if cp_sat_result['valid'] and cp_sat_result['known_positions_match']:
        quantum_state = QuantumState.COLLAPSED.value
    elif cp_sat_result['col_conflicts'] > 5 or cp_sat_result['box_conflicts'] > 5:
        quantum_state = QuantumState.SUPERPOSITION.value
    else:
        quantum_state = QuantumState.PARTIAL_COLLAPSE.value
    
    print(f"  量子態: {quantum_state}")
    
    return {
        'variant': 'standard',
        'known_positions': len(known_positions),
        'gene_fingerprint': {
            'row_mean': sum(gene_fp.row_dimensions)/16,
            'col_mean': sum(gene_fp.col_dimensions)/16,
            'box_mean': sum(gene_fp.box_dimensions)/16,
            'total_fitness': gene_fp.total_fitness()
        },
        'individual_fitness': individual.fitness,
        'cp_sat_valid': cp_sat_result['valid'],
        'quantum_state': quantum_state
    }


def test_x_sudoku():
    """測試 X Sudoku"""
    print("\n" + "=" * 70)
    print("┌─ 測試 2: X Sudoku (Diagonal Constraint) ──────────────┐")
    print("└───────────────────────────────────────────────────┘")
    
    grid, known_positions = create_test_grid("x_sudoku", seed=123)
    
    # 創建 X Sudoku 變體
    variant = XsudokuVariant(grid_size=16, box_size=4)
    
    # 使用變體適配器計算 100D 基因指紋
    adapter = GeneFingerprint100DAdapter(grid_size=16, variant_type=SudokuVariantType.X_SUDOKU)
    fingerprint = adapter.compute_fingerprint(grid, known_positions, variant)
    
    # 計算個體適應度（使用變體）
    individual = Individual(grid=grid, variant=variant)
    individual.compute_fitness(known_positions, {}, {}, variant=variant)
    
    # 驗證
    validation = variant.validate_solution(grid, known_positions)
    
    print(f"\n  變體定義:")
    for name, diag in variant.diagonals.items():
        print(f"    {diag.name}: {len(diag.cells)} 個位置")
    
    print(f"\n  已知位置數: {len(known_positions)}")
    print(f"  100D 基因指紋 (含變體擴展):")
    row_mean = sum(fingerprint['row_dimensions'])/16 if fingerprint['row_dimensions'] else 0.0
    col_mean = sum(fingerprint['col_dimensions'])/16 if fingerprint['col_dimensions'] else 0.0
    box_mean = sum(fingerprint['box_dimensions'])/16 if fingerprint['box_dimensions'] else 0.0
    print(f"    行維度均值: {row_mean:.4f}")
    print(f"    列維度均值: {col_mean:.4f}")
    print(f"    宮維度均值: {box_mean:.4f}")
    print(f"    對角線維度: {fingerprint.get('diagonal_dimensions', [])[:2]}")
    print(f"    總體適應度: {fingerprint['total_fitness']:.4f}")
    print(f"    個體適應度: {individual.fitness:.4f}")
    
    print(f"\n  約束驗證:")
    print(f"    標準約束: {'✅ 通過' if validation['conflicts'].get('row', 0) == 0 and validation['conflicts'].get('col', 0) == 0 else '❌ 有衝突'}")
    print(f"    對角線約束: {'✅ 通過' if validation.get('diagonal_valid', False) else '❌ 有衝突'}")
    print(f"    總體有效: {'✅ 是' if validation['valid'] else '❌ 否'}")
    
    quantum_state = QuantumState.COLLAPSED.value if validation['valid'] else QuantumState.SUPERPOSITION.value
    print(f"  量子態: {quantum_state}")
    
    return {
        'variant': 'x_sudoku',
        'known_positions': len(known_positions),
        'diagonals': {
            'main_cells': len(variant.diagonals['main'].cells),
            'anti_cells': len(variant.diagonals['anti'].cells)
        },
        'gene_fingerprint': fingerprint,
        'individual_fitness': individual.fitness,
        'validation_valid': validation['valid'],
        'quantum_state': quantum_state
    }


def test_killer_sudoku():
    """測試 Killer Sudoku"""
    print("\n" + "=" * 70)
    print("┌─ 測試 3: Killer Sudoku (Cage Sum Constraint) ──────────┐")
    print("└───────────────────────────────────────────────────┘")
    
    grid, known_positions = create_test_grid("killer_sudoku", seed=456)
    
    # 創建 Cage 定義
    cages_def = [
        {'cells': [(0, 0), (0, 1), (1, 0)], 'target_sum': 6, 'must_be_unique': True},
        {'cells': [(0, 2), (0, 3), (1, 2), (1, 3)], 'target_sum': 10, 'must_be_unique': True},
        {'cells': [(2, 0), (2, 1), (3, 0), (3, 1)], 'target_sum': 12, 'must_be_unique': True},
        {'cells': [(0, 4), (1, 4), (0, 5)], 'target_sum': 8, 'must_be_unique': True},
        {'cells': [(1, 5), (2, 5), (2, 6)], 'target_sum': 9, 'must_be_unique': True},
    ]
    
    # 創建 Killer Sudoku 變體
    variant = KillersudokuVariant(grid_size=16, box_size=4, cages=cages_def)
    
    # 使用變體適配器計算 100D 基因指紋
    adapter = GeneFingerprint100DAdapter(grid_size=16, variant_type=SudokuVariantType.KILLER_SUDOKU)
    fingerprint = adapter.compute_fingerprint(grid, known_positions, variant)
    
    # 計算個體適應度（使用變體）
    individual = Individual(grid=grid, variant=variant)
    individual.compute_fitness(known_positions, {}, {}, variant=variant)
    
    # 驗證
    validation = variant.validate_solution(grid, known_positions)
    
    print(f"\n  Cage 定義:")
    for cage in variant.cages:
        print(f"    {cage.cage_id}: {len(cage.cells)} 格, 目標和={cage.target_sum}, 唯一性={cage.must_be_unique}")
    
    print(f"\n  已知位置數: {len(known_positions)}")
    print(f"  100D 基因指紋 (含 Cage 擴展):")
    row_mean = sum(fingerprint['row_dimensions'])/16 if fingerprint['row_dimensions'] else 0.0
    col_mean = sum(fingerprint['col_dimensions'])/16 if fingerprint['col_dimensions'] else 0.0
    box_mean = sum(fingerprint['box_dimensions'])/16 if fingerprint['box_dimensions'] else 0.0
    print(f"    行維度均值: {row_mean:.4f}")
    print(f"    列維度均值: {col_mean:.4f}")
    print(f"    宮維度均值: {box_mean:.4f}")
    cage_sum_fit = fingerprint.get('cage_sum_dimensions', [])
    cage_unique_fit = fingerprint.get('cage_unique_dimensions', [])
    if cage_sum_fit:
        print(f"    Cage 求和維度: {[f'{v:.2f}' for v in cage_sum_fit[:5]]}")
    if cage_unique_fit:
        print(f"    Cage 唯一性維度: {[f'{v:.2f}' for v in cage_unique_fit[:5]]}")
    print(f"    總體適應度: {fingerprint['total_fitness']:.4f}")
    print(f"    個體適應度: {individual.fitness:.4f}")
    
    print(f"\n  約束驗證:")
    print(f"    標準約束: {'✅ 通過' if validation['conflicts'].get('row', 0) == 0 and validation['conflicts'].get('col', 0) == 0 else '❌ 有衝突'}")
    print(f"    Cage 求和: {'✅ 通過' if validation.get('cage_sum_valid', False) else '❌ 有衝突'}")
    print(f"    Cage 唯一性: {'✅ 通過' if validation.get('cage_unique_valid', False) else '❌ 有衝突'}")
    print(f"    總體有效: {'✅ 是' if validation['valid'] else '❌ 否'}")
    
    quantum_state = QuantumState.COLLAPSED.value if validation['valid'] else QuantumState.SUPERPOSITION.value
    print(f"  量子態: {quantum_state}")
    
    return {
        'variant': 'killer_sudoku',
        'known_positions': len(known_positions),
        'cages': [
            {
                'id': cage.cage_id,
                'cells': len(cage.cells),
                'target_sum': cage.target_sum,
                'must_be_unique': cage.must_be_unique
            }
            for cage in variant.cages
        ],
        'gene_fingerprint': fingerprint,
        'individual_fitness': individual.fitness,
        'validation_valid': validation['valid'],
        'quantum_state': quantum_state
    }


def generate_comparison_report(results: Dict) -> str:
    """生成變體對比報告"""
    report = """
╔════════════════════════════════════════════════════════════════════╗
║          符闔博弈優選策略 V19.1 - 變體對比分析報告                  ║
╚════════════════════════════════════════════════════════════════════╝

┌────────────────────────────────────────────────────────────────────┐
│                        變體特徵對比                                 │
├──────────────┬─────────────────┬─────────────────┬─────────────────┤
│    特徵       │   標準數獨       │   X Sudoku      │  Killer Sudoku  │
├──────────────┼─────────────────┼─────────────────┼─────────────────┤
│  變體類型     │   standard      │   x_sudoku      │  killer_sudoku  │
│  額外約束     │   無            │   對角線        │   Cage 求和     │
│  維度擴展     │   100D          │   100D+对角线   │  100D+Cage      │
│  100D 結構   │   8 組           │   8 組+对角线   │  8 組+Cage      │
└──────────────┴─────────────────┴─────────────────┴─────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                      100D 基因指紋維度分析                           │
├──────────────────┬─────────────────────────────────────────────────┤
│  維度組          │  標準數獨           │  X Sudoku    │  Killer     │
├──────────────────┼─────────────────────┼──────────────┼─────────────┤
│  行約束 (16D)    │  ✓ AllDifferent     │  ✓ 標準      │  ✓ 標準     │
│  列約束 (16D)    │  ✓ AllDifferent     │  ✓ 標準      │  ✓ 標準     │
│  宮約束 (16D)    │  ✓ 4×4 塊            │  ✓ 標準      │  ✓ 標準     │
│  對角線 (16D)    │  ✗ 不適用            │  ✓ X 約束     │  ✗ 不適用    │
│  Cage 求和 (20D) │  ✗ 不適用            │  ✗ 不適用    │  ✓ 核心     │
│  Cage 唯一 (16D) │  ✗ 不適用            │  ✗ 不適用    │  ✓ 核心     │
│  全局 AllDiff    │  ✓ 20D              │  ✓ 20D      │  ✓ 20D      │
│  溢出修正        │  ✓ 20D              │  ✓ 20D      │  ✓ 20D      │
└──────────────────┴─────────────────────┴──────────────┴─────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    適應度權重分配策略                                │
├──────────────────┬─────────────────────────────────────────────────┤
│  變體            │  權重配置                                        │
├──────────────────┼─────────────────────────────────────────────────┤
│  標準數獨        │  行 0.1 + 列 0.45 + 宮 0.45                     │
│  X Sudoku        │  標準 0.9× + 對角線 0.1×                        │
│  Killer Sudoku   │  標準 0.8× + Cage 求和 0.12× + Cage 唯一 0.08×  │
└──────────────────┴─────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                      量子態定義                                      │
├──────────────────┬─────────────────────────────────────────────────┤
│  量子態           │  判斷條件                                        │
├──────────────────┼─────────────────────────────────────────────────┤
│  COLLAPSED       │  所有約束滿足，唯一解                             │
│  SUPERPOSITION   │  多解模式，衝突數 > 5                            │
│  PARTIAL_COLLAPSE│  部分滿足，中等衝突                               │
│  INFEASIBLE      │  無解（CP-SAT 證明）                             │
└──────────────────┴─────────────────────────────────────────────────┘

"""
    
    # 添加測試結果摘要
    for variant_name, result in results.items():
        report += f"""
┌────────────────────────────────────────────────────────────────────┐
│                   {variant_name.upper()} 測試結果摘要                      │
├────────────────────────────────────────────────────────────────────┤
│  已知位置數: {result['known_positions']}                                          │
│  總體適應度: {result['gene_fingerprint']['total_fitness']:.4f}                                     │
│  個體適應度: {result['individual_fitness']:.4f}                                     │
│  驗證通過: {'✅ 是' if result.get('validation_valid', result.get('cp_sat_valid', False)) else '❌ 否':12s}          │
│  量子態: {result['quantum_state']:20s}                                  │
└────────────────────────────────────────────────────────────────────┘
"""
    
    return report


def main():
    """主執行入口"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║     符闔博弈優選策略 V19.1 - 數獨變體擴展測試              ║")
    print("╚" + "═" * 68 + "╝")
    
    print("\n📋 測試說明:")
    print("  本測試演示 100D 基因指紋系統在三種數獨變體上的應用:")
    print("  1. 標準數獨 (Standard Sudoku) - 基礎變體")
    print("  2. X Sudoku - 增加對角線 AllDifferent 約束")
    print("  3. Killer Sudoku - 增加 Cage 求和約束")
    
    # 執行三種變體測試
    results = {}
    
    results['standard'] = test_standard_sudoku()
    results['x_sudoku'] = test_x_sudoku()
    results['killer_sudoku'] = test_killer_sudoku()
    
    # 生成對比報告
    report = generate_comparison_report(results)
    print(report)
    
    # 保存結果
    output = {
        'test_results': results,
        'comparison_report': report,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'version': 'V19.1'
    }
    
    with open('sudoku_variants_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 測試結果已保存至: sudoku_variants_test_results.json")
    
    return output


if __name__ == '__main__':
    import time
    main()
