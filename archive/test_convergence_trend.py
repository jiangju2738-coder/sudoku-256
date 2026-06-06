#!/usr/bin/env python3
"""
分析填滿率對求解器收斂趨勢的影響 - 簡化版

驗證假說：填滿率越高 → 約束衝突越明顯 → 符闔博弈剪枝壓縮搜索空間
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cp_sat_incremental_solver_v3 import IncrementalConstraintSolver
from solver_config import SudokuConfig
import json
import random

def analyze_convergence_trend():
    """分析不同填滿率的收斂趨勢"""
    
    config = SudokuConfig()
    
    print("="*70)
    print("🔍 填滿率收斂趨勢分析")
    print("="*70)
    
    # 基準填滿率測試
    test_rates = [10, 20, 30, 40, 45, 50, 60, 70, 80]
    
    results = []
    
    for fill_rate in test_rates:
        n_givens = int(16 * 16 * fill_rate / 100)
        
        print(f"\n{'─'*70}")
        print(f"📊 填滿率: {fill_rate}% ({n_givens} 個已知數)")
        print(f"{'─'*70}")
        
        # 創建求解器
        solver = IncrementalConstraintSolver()
        
        # 1. 添加行約束
        t0 = time.time()
        solver.add_row_constraints()
        t_row = time.time() - t0
        
        # 2. 添加部分已知數（按填滿率）
        t0 = time.time()
        givens_added = 0
        for row in range(16):
            for col in range(16):
                if random.random() < fill_rate / 100 and givens_added < n_givens:
                    value = random.randint(1, 16)
                    solver.add_given(row, col, value)
                    givens_added += 1
        t_given = time.time() - t0
        
        # 3. 添加符闔約束
        t0 = time.time()
        solver.add_fahuo_constraints()
        t_fahuo = time.time() - t0
        
        # 4. 添加列約束
        t0 = time.time()
        solver.add_column_constraints()
        t_col = time.time() - t0
        
        # 5. 添加宮約束
        t0 = time.time()
        solver.add_box_constraints()
        t_box = time.time() - t0
        
        # 6. 求解
        t0 = time.time()
        status = solver.solve()
        t_solve = time.time() - t0
        
        total_time = t_row + t_given + t_fahuo + t_col + t_box + t_solve
        
        is_feasible = status == 2
        status_name = "OPTIMAL" if status == 2 else ("INFEASIBLE" if status == 1 else "UNKNOWN")
        
        result = {
            "fill_rate": fill_rate,
            "n_givens": n_givens,
            "is_feasible": is_feasible,
            "status": status_name,
            "total_time": round(total_time, 3),
            "constraint_times": {
                "row": round(t_row, 3),
                "given": round(t_given, 3),
                "fahuo": round(t_fahuo, 3),
                "col": round(t_col, 3),
                "box": round(t_box, 3),
                "solve": round(t_solve, 3)
            }
        }
        
        results.append(result)
        
        status_icon = "✅" if is_feasible else "❌"
        print(f"  狀態: {status_icon} {status_name}")
        print(f"  時間: {total_time:.3f}s")
        print(f"  行約束: {t_row:.3f}s | 已知數: {t_given:.3f}s | 符闔: {t_fahuo:.3f}s")
        print(f"  列約束: {t_col:.3f}s | 宮約束: {t_box:.3f}s | 求解: {t_solve:.3f}s")
    
    # 生成匯總報告
    print("\n" + "="*70)
    print("📈 收斂趨勢匯總")
    print("="*70)
    
    print("\n填滿率 | 已知數 | 成功率 | 時間(s)")
    print("-"*50)
    
    for r in results:
        feasible_icon = "✅" if r["is_feasible"] else "❌"
        print(f"  {r['fill_rate']:>3}%  |  {r['n_givens']:>4}  | {feasible_icon} {'有解' if r['is_feasible'] else '無解':>4}  | {r['total_time']:>7.3f}")
    
    return results


def main():
    results = analyze_convergence_trend()
    
    # 保存結果
    output_path = Path(__file__).parent / "convergence_analysis_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 結果已保存: {output_path}")


if __name__ == '__main__':
    main()
