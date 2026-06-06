#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 符闔博弈優選策略 - CP-SAT 驗證（solution_limit=5）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

目標：驗證「7 15 3 9」超級數獨，收集最多 5 個解
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

# OR-Tools
from ortools.sat.python import cp_model


@dataclass
class VerificationResult:
    """驗證結果"""
    status: str
    num_solutions: int
    elapsed_time: float
    quantum_state: str
    solutions: List[List[List[int]]]
    solution_limit: int
    time_limit: int


def load_config() -> tuple:
    """載入所有配置"""
    with open('sudoku_config.json', 'r', encoding='utf-8') as f:
        sudoku_config = json.load(f)
    
    known_positions = {}
    for kd in sudoku_config['known_digits']:
        r = kd['row'] - 1
        c = kd['col'] - 1
        v = kd['value']
        known_positions[(r, c)] = v
    
    # 符闔排列
    row_permutations = {}
    row_map = {chr(65+i): f'A{i+1}_permutations.json' for i in range(16)}
    
    for letter, fname in row_map.items():
        fpath = Path(f'D:/2026/WPF_Sudoku/Sudoku_256/{fname}')
        if fpath.exists():
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    row_permutations[letter] = data
                elif isinstance(data, dict) and 'permutations' in data:
                    row_permutations[letter] = data['permutations']
    
    return known_positions, row_permutations


def cp_sat_verify_with_limit(known_positions: Dict, 
                              row_permutations: Dict,
                              solution_limit: int = 5,
                              time_limit: int = 300) -> VerificationResult:
    """
    CP-SAT 驗證並收集指定數量的解
    """
    print("\n" + "=" * 70)
    print("┌─ CP-SAT 精確驗證（solution_limit=5）──────────────┐")
    print("│  目標：收集最多 5 個有效解                         │")
    print("└───────────────────────────────────────────────────┘")
    print()
    
    # 分析
    row_letters = 'ABCDEFGHIJKLMNOP'
    unknown_rows = []
    known_rows = []
    
    for i, letter in enumerate(row_letters):
        known_count = sum(1 for (kr, _) in known_positions if kr == i)
        if known_count < 16:
            unknown_rows.append(i)
        else:
            known_rows.append(i)
    
    print(f"[分析] 總行數: 16")
    print(f"[分析] 完全已知行: {len(known_rows)} 行 ({', '.join(row_letters[r] for r in known_rows)})")
    print(f"[分析] 部分未知行: {len(unknown_rows)} 行 ({', '.join(row_letters[r] for r in unknown_rows)})")
    
    # 檢查每行排列數
    print(f"\n[分析] 各行符闔排列數:")
    for i, letter in enumerate(row_letters):
        if letter in row_permutations:
            perms_count = len(row_permutations[letter])
            known_count = sum(1 for (kr, _) in known_positions if kr == i)
            unknown_count = 16 - known_count
            if perms_count == 0:
                print(f"  行{letter}: 0 個排列 ⚠️ OVER-FILTERED")
            elif perms_count < 10:
                print(f"  行{letter}: {perms_count:,} 個排列 (未知{unknown_count}位) ★ 極稀少")
            elif perms_count < 1000:
                print(f"  行{letter}: {perms_count:,} 個排列 (未知{unknown_count}位) ✓ 稀少")
            else:
                print(f"  行{letter}: {perms_count:,} 個排列")
        else:
            print(f"  行{letter}: 無排列數據")
    
    model = cp_model.CpModel()
    
    # 為未知行創建選擇變數
    row_vars = {}
    row_perm_counts = {}
    
    for i in unknown_rows:
        if row_letters[i] in row_permutations:
            perms = row_permutations[row_letters[i]]
            row_perm_counts[i] = len(perms)
            if len(perms) > 0:
                row_vars[i] = [model.NewBoolVar(f'row{i}_perm{k}') for k in range(len(perms))]
                model.AddExactlyOne(row_vars[i])
            else:
                print(f"  ⚠️ 行{row_letters[i]}無可用排列，直接不可滿足")
    
    # 列約束：每列的 16 個值互異
    for c in range(16):
        for v in range(1, 17):
            count_exprs = []
            
            # 已知位置的貢獻
            for (kr, kc), kv in known_positions.items():
                if kc == c and kv == v:
                    count_exprs.append(1)
            
            # 未知行的貢獻
            for i in unknown_rows:
                if i in row_vars and row_letters[i] in row_permutations:
                    for k in range(row_perm_counts[i]):
                        if row_permutations[row_letters[i]][k][c] == v:
                            count_exprs.append(row_vars[i][k])
            
            # 約束
            if count_exprs:
                if any(isinstance(x, int) for x in count_exprs):
                    known_count = sum(1 for x in count_exprs if isinstance(x, int) and x == 1)
                    if known_count > 1:
                        print(f"\n  ❌ 列{c+1}值{v}有{known_count}個已知位置，直接衝突")
                        return VerificationResult(
                            status='INFEASIBLE',
                            num_solutions=0,
                            elapsed_time=0.0,
                            quantum_state='INFEASIBLE',
                            solutions=[],
                            solution_limit=solution_limit,
                            time_limit=time_limit
                        )
                    elif known_count == 1:
                        exprs = [x for x in count_exprs if not isinstance(x, int)]
                        if exprs:
                            model.Add(sum(exprs) == 0)
                else:
                    model.Add(sum(count_exprs) <= 1)
    
    # 宮約束：每個 4×4 宮格內 16 個值互異
    for box_idx in range(16):
        for v in range(1, 17):
            count_exprs = []
            
            # 已知位置
            for (kr, kc), kv in known_positions.items():
                if kv == v:
                    box_r = kr // 4
                    box_c = kc // 4
                    if box_r * 4 + box_c == box_idx:
                        count_exprs.append(1)
            
            # 未知行
            for i in unknown_rows:
                if i in row_vars and row_letters[i] in row_permutations:
                    for k in range(row_perm_counts[i]):
                        for c in range(16):
                            r = i
                            box_r = r // 4
                            box_c = c // 4
                            if box_r * 4 + box_c == box_idx and row_permutations[row_letters[i]][k][c] == v:
                                count_exprs.append(row_vars[i][k])
            
            if count_exprs:
                if any(isinstance(x, int) for x in count_exprs):
                    known_count = sum(1 for x in count_exprs if isinstance(x, int) and x == 1)
                    if known_count > 1:
                        print(f"\n  ❌ 宮{box_idx+1}值{v}有{known_count}個已知位置，直接衝突")
                        return VerificationResult(
                            status='INFEASIBLE',
                            num_solutions=0,
                            elapsed_time=0.0,
                            quantum_state='INFEASIBLE',
                            solutions=[],
                            solution_limit=solution_limit,
                            time_limit=time_limit
                        )
                    elif known_count == 1:
                        exprs = [x for x in count_exprs if not isinstance(x, int)]
                        if exprs:
                            model.Add(sum(exprs) == 0)
                else:
                    model.Add(sum(count_exprs) <= 1)
    
    # 設定求解器
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    solver.parameters.solution_limit = solution_limit
    solver.parameters.log_search_progress = True
    
    print(f"\n[求解] 參數設定:")
    print(f"  時間限制: {time_limit} 秒")
    print(f"  解數量限制: {solution_limit}")
    print(f"  工作線程: 8")
    print(f"\n[求解] 開始 CP-SAT 搜索...")
    print("-" * 70)
    
    start_time = time.time()
    
    class SolutionCollector(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.solutions = []
            self.solution_times = []
            self.start_time = time.time()
        
        def on_solution_callback(self):
            grid = [[0] * 16 for _ in range(16)]
            
            # 填入已知位置
            for (r, c), v in known_positions.items():
                grid[r][c] = v
            
            # 填入未知行選擇的排列
            for i in unknown_rows:
                if i in row_vars and row_letters[i] in row_permutations:
                    for k in range(row_perm_counts[i]):
                        if self.Value(row_vars[i][k]):
                            grid[i] = row_permutations[row_letters[i]][k][:]
                            break
            
            self.solutions.append(grid)
            elapsed = time.time() - self.start_time
            self.solution_times.append(elapsed)
            print(f"  ✓ 找到解 #{len(self.solutions)} (累積時間: {elapsed:.3f}秒)")
    
    collector = SolutionCollector()
    status = solver.Solve(model, collector)
    elapsed = time.time() - start_time
    
    num_solutions = len(collector.solutions)
    
    # 量子態判斷
    if num_solutions == 0:
        quantum_state = 'INFEASIBLE'
    elif num_solutions == 1:
        quantum_state = 'COLLAPSED'
    else:
        quantum_state = 'SUPERPOSITION'
    
    print()
    print("=" * 70)
    print("┌─ CP-SAT 求解結果 ───────────────────────────────────┐")
    print(f"│  狀態: {solver.StatusName(status):20s}                  │")
    print(f"│  解數: {num_solutions:20d} / {solution_limit} (requested)          │")
    print(f"│  時間: {elapsed:20.2f}秒                 │")
    print(f"│  量子態: {quantum_state:17s}                  │")
    print("└───────────────────────────────────────────────────┘")
    print()
    
    # 如果找到解，驗證每個解
    if collector.solutions:
        print("┌─ 解驗證 ──────────────────────────────────────────┐")
        for idx, grid in enumerate(collector.solutions):
            # 驗證行
            row_errors = 0
            for r in range(16):
                if len(set(grid[r])) != 16:
                    row_errors += 1
            
            # 驗證列
            col_errors = 0
            for c in range(16):
                col_vals = [grid[r][c] for r in range(16)]
                if len(set(col_vals)) != 16:
                    col_errors += 1
            
            # 驗證宮
            box_errors = 0
            for box_idx in range(16):
                vals = []
                for r in range(16):
                    for c in range(16):
                        if (r // 4) * 4 + (c // 4) == box_idx:
                            vals.append(grid[r][c])
                if len(set(vals)) != 16:
                    box_errors += 1
            
            # 驗證已知位置
            known_match = all(grid[r][c] == v for (r, c), v in known_positions.items())
            
            status_str = "✅ VALID" if (row_errors == 0 and col_errors == 0 and box_errors == 0 and known_match) else "❌ INVALID"
            print(f"│  解 #{idx+1}: {status_str} (行錯{row_errors}, 列錯{col_errors}, 宮錯{box_errors})   │")
        print("└───────────────────────────────────────────────────┘")
        print()
    
    return VerificationResult(
        status=solver.StatusName(status),
        num_solutions=num_solutions,
        elapsed_time=elapsed,
        quantum_state=quantum_state,
        solutions=collector.solutions,
        solution_limit=solution_limit,
        time_limit=time_limit
    )


def compute_gene_fingerprint_100d(grid: List[List[int]], 
                                   known_positions: Dict,
                                   sequence: str = "7 15 3 9") -> Dict:
    """計算 100D 基因指紋並提取關鍵元素"""
    import numpy as np
    
    fingerprint = {
        'row_dimensions': [0.0] * 16,
        'col_dimensions': [0.0] * 16,
        'box_dimensions': [0.0] * 16,
        'diagonal_dimensions': [0.0] * 16,
        'consecutive_dimensions': [0.0] * 16,
        'fuhh_special': [0.0] * 20,
        'global_alldiff': [0.0] * 20,
        'overflow_correction': [0.0] * 20,
        'key_elements': {},
        'total_fitness': 0.0
    }
    
    seq_values = list(map(int, sequence.split()))
    
    # 1. 行約束 (16D)
    for r in range(16):
        if len(set(grid[r])) == 16:
            fingerprint['row_dimensions'][r] = 1.0
        else:
            duplicates = len(grid[r]) - len(set(grid[r]))
            fingerprint['row_dimensions'][r] = (16 - duplicates) / 16
    
    # 2. 列約束 (16D)
    for c in range(16):
        col_vals = [grid[r][c] for r in range(16)]
        fingerprint['col_dimensions'][c] = len(set(col_vals)) / 16
    
    # 3. 宮約束 (16D)
    for box_idx in range(16):
        vals = []
        for r in range(16):
            for c in range(16):
                if (r // 4) * 4 + (c // 4) == box_idx:
                    vals.append(grid[r][c])
        fingerprint['box_dimensions'][box_idx] = len(set(vals)) / 16
    
    # 4. 對角線 (2D)
    # 主對角線
    main_diag = [grid[i][i] for i in range(16)]
    fingerprint['diagonal_dimensions'][0] = len(set(main_diag)) / 16
    # 副對角線
    anti_diag = [grid[i][15-i] for i in range(16)]
    fingerprint['diagonal_dimensions'][1] = len(set(anti_diag)) / 16
    
    # 5. 連續性 (16D)
    for r in range(16):
        consecutive = sum(1 for c in range(15) 
                         if grid[r][c] != 0 and grid[r][c+1] != 0 and abs(grid[r][c] - grid[r][c+1]) == 1)
        fingerprint['consecutive_dimensions'][r] = consecutive / 15
    
    # 6. 符闔特殊 (20D)
    for i in range(20):
        hash_val = sum(grid[r][c] * ((r * 16 + c + 1) % 64) 
                       for r in range(16) for c in range(16) if grid[r][c] != 0)
        fingerprint['fuhh_special'][i] = (hash_val % 100) / 100.0
    
    # 7. 全局 AllDifferent (20D)
    all_vals = [grid[r][c] for r in range(16) for c in range(16) if grid[r][c] != 0]
    unique_ratio = len(set(all_vals)) / max(1, len(all_vals))
    for i in range(20):
        fingerprint['global_alldiff'][i] = unique_ratio * (1 + i * 0.02)
    
    # 8. 過度固定修正 (20D)
    row_known = {}
    for r, _ in known_positions.keys():
        row_known[r] = row_known.get(r, 0) + 1
    avg_known = sum(row_known.values()) / 16 if row_known else 0
    for i in range(20):
        fingerprint['overflow_correction'][i] = (avg_known / 16) * (1 + i * 0.05)
    
    # 關鍵元素提取
    fingerprint['key_elements'] = {
        'sequence': sequence,
        'sequence_values': seq_values,
        'sequence_sum': sum(seq_values),
        'sequence_product': seq_values[0] * seq_values[1] * seq_values[2] * seq_values[3],
        'row_satisfaction': sum(fingerprint['row_dimensions']) / 16,
        'col_satisfaction': sum(fingerprint['col_dimensions']) / 16,
        'box_satisfaction': sum(fingerprint['box_dimensions']) / 16,
        'diagonal_main': fingerprint['diagonal_dimensions'][0],
        'diagonal_anti': fingerprint['diagonal_dimensions'][1],
        'row_16_satisfaction': fingerprint['row_dimensions'][15]
    }
    
    # 總體適應度
    fingerprint['total_fitness'] = (
        0.1 * fingerprint['key_elements']['row_satisfaction'] +
        0.45 * fingerprint['key_elements']['col_satisfaction'] +
        0.45 * fingerprint['key_elements']['box_satisfaction']
    )
    
    return fingerprint


def main():
    """主執行入口"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║   符闔博弈優選策略 - CP-SAT 驗證（solution_limit=5）    ║")
    print("║                    「7 15 3 9」超級數獨                 ║")
    print("╚" + "═" * 68 + "╝")
    
    # 載入配置
    print("\n[載入] 讀取配置數據...")
    known_positions, row_permutations = load_config()
    print(f"  已知位置: {len(known_positions)} 個")
    print(f"  符闔排列總數: {sum(len(v) for v in row_permutations.values()):,} 個")
    
    # 執行 CP-SAT 驗證
    result = cp_sat_verify_with_limit(
        known_positions, 
        row_permutations,
        solution_limit=5,
        time_limit=300
    )
    
    # 如果有解，計算 100D 基因指紋
    if result.solutions:
        print("\n" + "┌─ 100D 基因指紋計算 ────────────────────────────┐")
        for idx, grid in enumerate(result.solutions):
            fp = compute_gene_fingerprint_100d(grid, known_positions)
            print(f"│  解 #{idx+1} 基因指紋特徵:                             │")
            print(f"│    行約束均值: {fp['key_elements']['row_satisfaction']:.4f}                         │")
            print(f"│    列約束均值: {fp['key_elements']['col_satisfaction']:.4f}                         │")
            print(f"│    宮約束均值: {fp['key_elements']['box_satisfaction']:.4f}                         │")
            print(f"│    主對角線: {fp['key_elements']['diagonal_main']:.4f}                           │")
            print(f"│    副對角線: {fp['key_elements']['diagonal_anti']:.4f}                           │")
            print(f"│    P行（行16）: {fp['key_elements']['row_16_satisfaction']:.4f}                           │")
            print(f"│    總體適應度: {fp['total_fitness']:.4f}                          │")
            print(f"│    序列「7 15 3 9」和={fp['key_elements']['sequence_sum']}, 積={fp['key_elements']['sequence_product']}      │")
            print("└───────────────────────────────────────────────────┘")
    
    # 保存結果
    output = {
        'status': result.status,
        'num_solutions': result.num_solutions,
        'solution_limit': result.solution_limit,
        'quantum_state': result.quantum_state,
        'elapsed_time': result.elapsed_time,
        'time_limit': result.time_limit,
        'solutions': result.solutions,
        'gene_fingerprints': [
            compute_gene_fingerprint_100d(grid, known_positions) 
            for grid in result.solutions
        ]
    }
    
    with open('cp_sat_verify_5_solutions_result.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 結果已保存至: cp_sat_verify_5_solutions_result.json")
    
    # 總結
    print("\n" + "=" * 70)
    print("┌─ 驗證總結 ────────────────────────────────────────────┐")
    print(f"│  CP-SAT 狀態: {result.status:20s}                │")
    print(f"│  找到的解數: {result.num_solutions:18d} / {result.solution_limit} (requested)      │")
    print(f"│  量子態: {result.quantum_state:17s}                │")
    print(f"│  耗時: {result.elapsed_time:20.2f}秒                │")
    
    if result.quantum_state == 'COLLAPSED':
        print("│  結論: ✅ 唯一解 - 該數獨具有唯一解                   │")
    elif result.quantum_state == 'SUPERPOSITION':
        print(f"│  結論: ⚠️ 多解 - 找到 {result.num_solutions} 個解，需要更多約束         │")
    else:
        print("│  結論: ❌ 不可滿足 - 約束衝突，無有效解               │")
    print("└───────────────────────────────────────────────────┘")
    print()
    
    return result


if __name__ == '__main__':
    main()
