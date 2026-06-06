#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量約束求解器 V2.0 - 改進版

改進：
1. 使用更精確的符闔排列約束編碼
2. 生成適中密度的謎題（45個已知數字）
3. 逐步驗證每步的可行性
4. 添加約束強度量化分析
"""

import json
import time
import math
from typing import List, Dict, Set
from itertools import combinations

try:
    from ortools.sat.python import cp_model
except ImportError:
    print("請安裝 ortools: pip install ortools")
    exit(1)

# 狀態映射
STATUS_NAMES = {
    cp_model.UNKNOWN: 'UNKNOWN',
    cp_model.FEASIBLE: 'FEASIBLE',
    cp_model.OPTIMAL: 'OPTIMAL',
    cp_model.INFEASIBLE: 'INFEASIBLE',
    cp_model.MODEL_INVALID: 'MODEL_INVALID'
}


class IncrementalSolverV2:
    """增量約束求解器 V2.0"""
    
    def __init__(self, grid_size: int = 16, box_size: int = 4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.num_cells = grid_size * grid_size
        
    def load_data(self):
        """載入數據"""
        with open('solution_v4_final.json', 'r', encoding='utf-8') as f:
            self.solution = json.load(f)
        
        with open('permutations_v4_final.json', 'r', encoding='utf-8') as f:
            self.permutations = json.load(f)
        
        print(f"📊 數據載入:")
        print(f"   解決方案: {len(self.solution)} 行（已驗證三約束）")
        print(f"   符闔排列: {len(self.permutations)} 個")
        print(f"   所有 solution 行均在排列池中: {all(tuple(r) in set(tuple(p) for p in self.permutations) for r in self.solution)}")
    
    def create_puzzle(self, num_givens: int = 45) -> List[List[int]]:
        """生成指定數量的已知數字謎題"""
        import random
        random.seed(2026)
        
        puzzle = [row.copy() for row in self.solution]
        
        # 随机選取位置作為已知數字
        positions = [(i, j) for i in range(self.grid_size) for j in range(self.grid_size)]
        random.shuffle(positions)
        
        # 清空非選取位置
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                puzzle[i][j] = 0
        
        # 設置已知數字
        for idx in range(min(num_givens, self.num_cells)):
            i, j = positions[idx]
            puzzle[i][j] = self.solution[i][j]
        
        given_count = sum(1 for row in puzzle for cell in row if cell != 0)
        print(f"\n📋 生成謎題: {given_count}/{self.num_cells} ({given_count/self.num_cells*100:.1f}%)")
        
        return puzzle
    
    def save_puzzle(self, puzzle: List[List[int]], filename: str):
        """保存謎題"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(puzzle, f, ensure_ascii=False, indent=2)
        print(f"💾 謎題已保存: {filename}")
    
    def build_model(self) -> cp_model.CpModel:
        """建立基礎模型"""
        model = cp_model.CpModel()
        
        self.x = {}
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                self.x[(i, j)] = model.NewIntVar(1, self.grid_size, f'x[{i},{j}]')
        
        return model
    
    def add_row_constraints(self, model: cp_model.CpModel) -> Dict:
        """添加行約束"""
        for i in range(self.grid_size):
            model.AddAllDifferent([self.x[(i, j)] for j in range(self.grid_size)])
        
        return {'name': '行約束', 'count': self.grid_size}
    
    def add_given_constraints(self, model: cp_model.CpModel, puzzle: List[List[int]]) -> Dict:
        """添加已知數字約束"""
        count = 0
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if puzzle[i][j] != 0:
                    model.Add(self.x[(i, j)] == puzzle[i][j])
                    count += 1
        return {'name': '已知數字', 'count': count}
    
    def add_fahuo_constraints_efficient(self, model: cp_model.CpModel) -> Dict:
        """
        添加符闔排列約束 - 改進版
        
        使用更精確的編碼：
        - 對每行，直接限制其值必須匹配排列池中的某個排列
        - 使用線性化方法避免大量布林變量
        """
        count = 0
        
        for i in range(self.grid_size):
            # 為該行創建選擇變量（每個排列一個）
            row_selectors = []
            
            for perm_idx, perm in enumerate(self.permutations):
                # 創建布林變量表示「選擇這個排列」
                selector = model.NewBoolVar(f'row{i}_perm{perm_idx}')
                row_selectors.append(selector)
                
                # 如果選擇這個排列，該行的所有值必須匹配
                for j, val in enumerate(perm):
                    # 使用implication: selector → (x[i,j] == val)
                    model.Add(self.x[(i, j)] == val).OnlyEnforceIf(selector)
            
            # 每行恰好選擇一個排列
            model.AddExactlyOne(row_selectors)
            count += len(self.permutations) + 1  # 選擇變量 + ExactlyOne約束
        
        return {'name': '符闔排列約束', 'count': count, 'permutations': len(self.permutations)}
    
    def add_column_constraints(self, model: cp_model.CpModel) -> Dict:
        """添加列約束"""
        for j in range(self.grid_size):
            model.AddAllDifferent([self.x[(i, j)] for i in range(self.grid_size)])
        return {'name': '列約束', 'count': self.grid_size}
    
    def add_box_constraints(self, model: cp_model.CpModel) -> Dict:
        """添加宮約束"""
        for band in range(self.grid_size // self.box_size):
            for stack in range(self.grid_size // self.box_size):
                box_vars = [
                    self.x[(band*self.box_size+i, stack*self.box_size+j)]
                    for i in range(self.box_size) for j in range(self.box_size)
                ]
                model.AddAllDifferent(box_vars)
        
        num_boxes = (self.grid_size // self.box_size) ** 2
        return {'name': '宮約束', 'count': num_boxes}
    
    def solve(self, model: cp_model.CpModel, timeout: int = 30, name: str = "") -> Dict:
        """求解模型"""
        print(f"\n{'=' * 70}")
        print(f"求解: {name}")
        print("=" * 70)
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout
        solver.parameters.num_search_workers = 8
        solver.parameters.log_search_progress = False
        
        start = time.time()
        status = solver.Solve(model)
        elapsed = time.time() - start
        
        result = {
            'name': name,
            'status': STATUS_NAMES.get(status, f'STATUS_{status}'),
            'status_code': status,
            'elapsed': elapsed,
            'feasible': status in [cp_model.OPTIMAL, cp_model.FEASIBLE],
            'conflicts': solver.NumConflicts(),
            'branches': solver.NumBranches()
        }
        
        if result['feasible']:
            # 提取解
            solution = [[solver.Value(self.x[(i, j)]) for j in range(self.grid_size)]
                       for i in range(self.grid_size)]
            result['solution'] = solution
            
            # 檢查是否完全確定
            complete = True
            for i in range(self.grid_size):
                for j in range(self.grid_size):
                    if solver.Value(self.x[(i, j)]) == 0:
                        complete = False
                        break
            
            result['complete'] = complete
            print(f"   狀態: {'✅' if result['complete'] else '⚠️'} {result['status']}")
            print(f"   時間: {elapsed:.3f}s")
            
            if result['complete']:
                print(f"   ✅ 找到完整解")
        else:
            print(f"   狀態: ❌ {result['status']}")
            print(f"   時間: {elapsed:.3f}s")
        
        return result
    
    def run_incremental_solve(self, num_givens: int = 45) -> List[Dict]:
        """執行增量求解"""
        print("=" * 80)
        print("增量約束求解器 V2.0")
        print("=" * 80)
        
        self.load_data()
        
        # 生成謎題
        puzzle = self.create_puzzle(num_givens)
        self.save_puzzle(puzzle, f'puzzle_incremental_{num_givens}.json')
        
        # 建立模型並逐步添加約束
        model = self.build_model()
        results = []
        
        # 步驟1: 行約束
        print("\n📋 步驟1: 添加行約束")
        self.add_row_constraints(model)
        r1 = self.solve(model, timeout=10, name="僅行約束")
        results.append({'step': 1, 'constraint': self.add_row_constraints(model), 'result': r1})
        
        # 步驟2: 已知數字
        print("\n📋 步驟2: 添加已知數字")
        self.add_given_constraints(model, puzzle)
        r2 = self.solve(model, timeout=10, name="行+已知數字")
        results.append({'step': 2, 'constraint': self.add_given_constraints(model, puzzle), 'result': r2})
        
        # 步驟3: 符闔排列約束
        print("\n📋 步驟3: 添加符闔排列約束")
        self.add_fahuo_constraints_efficient(model)
        r3 = self.solve(model, timeout=60, name="行+已知+符闔排列")
        results.append({'step': 3, 'constraint': self.add_fahuo_constraints_efficient(model), 'result': r3})
        
        # 步驟4: 列約束
        print("\n📋 步驟4: 添加列約束")
        self.add_column_constraints(model)
        r4 = self.solve(model, timeout=60, name="行+已知+符闔+列")
        results.append({'step': 4, 'constraint': self.add_column_constraints(model), 'result': r4})
        
        # 步驟5: 宮約束
        print("\n📋 步驟5: 添加宮約束")
        self.add_box_constraints(model)
        r5 = self.solve(model, timeout=120, name="完整約束（最終）")
        results.append({'step': 5, 'constraint': self.add_box_constraints(model), 'result': r5})
        
        return results, puzzle
    
    def generate_report(self, results: List[Dict], puzzle: List[List[int]]) -> str:
        """生成報告"""
        report = []
        report.append("=" * 80)
        report.append("增量約束求解報告 V2.0")
        report.append("=" * 80)
        report.append(f"謎題規模: {self.grid_size}×{self.grid_size}")
        report.append(f"已知數字: {sum(1 for r in puzzle for c in r if c != 0)}")
        report.append(f"符闔排列: {len(self.permutations)} 個")
        report.append("")
        
        # 總結表
        report.append("📊 增量求解進度")
        report.append("-" * 80)
        report.append(f"{'步驟':<6} {'約束':<20} {'狀態':<15} {'時間':<10} {'衝突數':<10}")
        report.append("-" * 80)
        
        for r in results:
            step = r['step']
            name = r['constraint']['name']
            status_icon = "✅" if r['result']['feasible'] else "❌"
            status = r['result']['status']
            time_str = f"{r['result']['elapsed']:.2f}s"
            conflicts = r['result'].get('conflicts', 'N/A')
            report.append(f"{step:<6} {name:<20} {status_icon} {status:<12} {time_str:<10} {conflicts}")
        
        report.append("")
        
        # 關鍵發現
        report.append("🔍 關鍵發現")
        report.append("-" * 80)
        
        final = results[-1]['result']
        if final['feasible'] and final.get('complete'):
            report.append(f"   ✅ 最終找到完整解！")
            report.append(f"   求解時間: {final['elapsed']:.2f}s")
        elif final['feasible']:
            report.append(f"   ⚠️ 最終可行但未完全確定")
        else:
            report.append(f"   ❌ 最終不可行: {final['status']}")
            report.append(f"   原因: 符闔排列約束與已知數字可能過度約束")
        
        report.append("")
        
        # 約束強度分析
        report.append("🔬 約束強度分析")
        report.append("-" * 80)
        
        # 計算每步的搜索空間變化
        for r in results:
            step = r['step']
            if step == 1:
                orig_log = self.num_cells * math.log10(self.grid_size)
                after_log = self.grid_size * math.log10(math.factorial(self.grid_size))
                report.append(f"   步驟{step}: 10^{orig_log:.1f} → 10^{after_log:.1f} (減少{(1-after_log/orig_log)*100:.1f}%)")
            elif step == 2:
                given = r['constraint'].get('count', 0)
                reduction = given * math.log10(self.grid_size)
                report.append(f"   步驟{step}: 固定 {given} 個單元格，減少 10^{reduction:.1f} 倍")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    solver = IncrementalSolverV2()
    
    # 使用適中密度的謎題（45個已知數字）
    print("🎯 使用 45 個已知數字謎題（約 17.6% 填滿率）")
    results, puzzle = solver.run_incremental_solve(num_givens=45)
    
    # 生成報告
    report = solver.generate_report(results, puzzle)
    
    with open('incremental_constraint_report_v2.md', 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n💾 報告已保存: incremental_constraint_report_v2.md")
    
    # 保存最終解
    final_result = results[-1]['result']
    if final_result.get('feasible') and final_result.get('complete'):
        with open('incremental_solution_v2.json', 'w', encoding='utf-8') as f:
            json.dump(final_result['solution'], f, ensure_ascii=False, indent=2)
        print("💾 解已保存: incremental_solution_v2.json")
    
    print("\n" + "=" * 80)
    print("✅ 增量約束求解完成")
    print("=" * 80)


if __name__ == '__main__':
    main()
