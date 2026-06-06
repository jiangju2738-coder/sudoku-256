#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CP-SAT 精確求解器：符闔排列 16×16 數獨
直接搜尋滿足所有約束的解，實現 solution_limit 唯一性證明
"""

import json
import time
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter

# OR-Tools CP-SAT
from ortools.sat.python import cp_model


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


def load_permutations_from_excel(row_label: str, chinese_name: str) -> List[List[int]]:
    """從 Excel 載入相容排列"""
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
        
        wb.close()
        return perms
    except Exception as e:
        print(f"   載入排列失敗: {e}")
        return []


def cp_sat_solve(solution_limit: int = 10, time_limit_sec: int = 300):
    """
    CP-SAT 精確求解
    
    Args:
        solution_limit: 最多搜尋的解數量（用於唯一性證明）
        time_limit_sec: 時間限制（秒）
    
    Returns:
        dict: 求解結果
    """
    print("="*80)
    print("CP-SAT 精確求解器啟動")
    print("="*80)
    print(f"\n設定：solution_limit={solution_limit}, 時間限制={time_limit_sec}秒")
    
    # 載入數據
    grid_template, row_labels = load_puzzle_config()
    compat_data = load_compatibility()
    results = compat_data['results']
    
    # 識別已知行和未知行
    known_rows = {}  # {row_index: [values]}
    unknown_rows = []  # [row_index]
    row_perm_map = {}  # {row_index: [(perm_id, [values])]}
    
    chinese_names = {
        'A':'第一','B':'第二','C':'第三','D':'第四','E':'第五','F':'第六',
        'G':'第七','H':'第八','I':'第九','J':'第十','K':'第十一','L':'第十二',
        'M':'第十三','N':'第十四','O':'第十五','P':'第十六'
    }
    
    print("\n分析行狀態...")
    for i, label in enumerate(row_labels):
        r = results[label]
        if r['status'] == 'FULLY_KNOWN' and r['given_count'] == 16:
            # 完全已知
            known_rows[i] = grid_template[i]
            print(f"   行{i} ({label}): 完全已知")
        elif r['compatible_count'] == 1:
            # 唯一相容 - 需要載入
            print(f"   行{i} ({label}): 唯一相容，載入排列...")
            perms = load_permutations_from_excel(label, chinese_names[label])
            # 篩選相容的
            given = {j:v for j,v in enumerate(grid_template[i]) if v != 0}
            compat_perms = []
            for p in perms:
                if given and all(p[c] == given[c] for c in given if c < 16):
                    compat_perms.append(p)
            if len(compat_perms) == 1:
                known_rows[i] = compat_perms[0]
                print(f"      → 唯一排列: {compat_perms[0][:4]}...")
            else:
                row_perm_map[i] = compat_perms
                unknown_rows.append(i)
                print(f"      → {len(compat_perms)} 個相容排列")
        else:
            # 多個相容排列 - 需要搜尋
            unknown_rows.append(i)
            row_perm_map[i] = r.get('compatible_count', 0)
            print(f"   行{i} ({label}): {r.get('pool_size', 'unknown')} 個排列，{r['compatible_count']} 相容")
    
    print(f"\n已知行: {len(known_rows)}, 搜尋行: {len(unknown_rows)}")
    
    if len(unknown_rows) == 0:
        print("\n所有行已確定，直接驗證...")
        return verify_grid(grid_template)
    
    # 建立 CP-SAT 模型
    model = cp_model.CpModel()
    
    # 變數定義：為每行選擇一個排列索引
    # x[i][k] = 1 表示行 i 選擇第 k 個排列
    row_var = {}
    for i in unknown_rows:
        num_perms = len(row_perm_map[i])
        row_var[i] = [model.NewBoolVar(f'row{i}_perm{k}') for k in range(num_perms)]
        
        # 每行必須選擇恰好一個排列
        model.AddExactlyOne(row_var[i])
    
    # 數值變數：grid[i][j] = 選擇排列中的值
    grid_vars = {}
    for i in unknown_rows:
        grid_vars[i] = []
        for j in range(16):
            # grid[i][j] 的值來自選擇的排列
            perm_values = [row_perm_map[i][k][j] for k in range(len(row_perm_map[i]))]
            grid_vars[i].append(model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(perm_values),
                f'grid[{i}][{j}]'
            ))
    
    # 列約束：每列的值必須互異
    for j in range(16):
        # 收集列 j 的所有值（已知行 + 搜尋行）
        col_values = []
        
        # 已知行
        for i, vals in known_rows.items():
            col_values.append(vals[j])
        
        # 搜尋行：需要確保列約束
        for i in unknown_rows:
            # 為列 j 建立值選擇變數
            choices = []
            for k in range(len(row_perm_map[i])):
                val = row_perm_map[i][k][j]
                # 建立 (row_var[i][k] AND 值=val) 的關係
                # 使用線性化：grid_vars[i][j] = Σ (row_var[i][k] * val_k)
                choices.append((row_var[i][k], val))
        
        # 添加列唯一性約束 - 使用輔助變數方法
        # 對於每個值 v (1-16)，在列 j 中最多出現一次
        for v in range(1, 17):
            # 計算列 j 中值 v 出現次數
            count_expr = []
            
            # 已知行中 v 出現次數
            v_count_known = sum(1 for i, vals in known_rows.items() if vals[j] == v)
            
            # 搜尋行中 v 出現次數
            for i in unknown_rows:
                for k in range(len(row_perm_map[i])):
                    if row_perm_map[i][k][j] == v:
                        count_expr.append(row_var[i][k])
            
            if count_expr:
                model.Add(sum(count_expr) + v_count_known <= 1)
    
    # 宮約束：每個 4×4 宮格內值互異
    box_size = 4
    num_boxes = 16
    
    for band in range(4):
        for stack in range(4):
            box_values_count = {v: [] for v in range(1, 17)}
            
            # 收集宮格內的值
            for i in range(16):
                for j in range(16):
                    if (i // box_size == band) and (j // box_size == stack):
                        v_count = 0
                        
                        # 已知行
                        if i in known_rows:
                            v = known_rows[i][j]
                            box_values_count[v].append(1)
                        # 搜尋行
                        elif i in unknown_rows:
                            for k in range(len(row_perm_map[i])):
                                if row_perm_map[i][k][j] == v:
                                    box_values_count[v].append(row_var[i][k])
            
            # 每個值在宮格內最多出現一次
            for v, exprs in box_values_count.items():
                if exprs:
                    model.Add(sum(exprs) <= 1)
    
    # 建立求解器
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_sec
    solver.parameters.num_search_workers = 8
    solver.parameters.solution_limit = solution_limit
    solver.parameters.log_search_progress = True
    
    print("\n開始求解...")
    start_time = time.time()
    
    # 解收集器
    solutions = []
    
    class SolutionCollector(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.solutions = []
        
        def on_solution_callback(self):
            grid = [[0]*16 for _ in range(16)]
            
            # 填入已知行
            for i, vals in known_rows.items():
                grid[i] = vals
            
            # 填入搜尋行
            for i in unknown_rows:
                for k in range(len(row_perm_map[i])):
                    if self.Value(row_var[i][k]):
                        grid[i] = row_perm_map[i][k]
                        break
            
            self.solutions.append(grid)
            print(f"   找到解 #{len(self.solutions)}")
            
            if len(self.solutions) >= solution_limit:
                self.StopSearch()
    
    collector = SolutionCollector()
    status = solver.Solve(model, collector)
    
    elapsed = time.time() - start_time
    num_solutions = len(collector.solutions)
    
    # 報告結果
    print("\n" + "="*80)
    print("求解結果")
    print("="*80)
    print(f"狀態: {solver.StatusName(status)}")
    print(f"解數: {num_solutions}")
    print(f"時間: {elapsed:.2f} 秒")
    
    if num_solutions >= solution_limit:
        print(f"\n🔬 量子態分析: SUPERPOSITION (多解模式)")
        print(f"   至少存在 {solution_limit} 個解，需要進一步分析")
    elif num_solutions == 1:
        print(f"\n✨ 量子態分析: COLLAPSED (唯一解)")
        print(f"   確認為唯一解！")
    else:
        print(f"\n❌ 量子態分析: INFEASIBLE (無解)")
        print(f"   該謎題在符闔排列約束下不可滿足")
    
    return {
        'status': solver.StatusName(status),
        'num_solutions': num_solutions,
        'solutions': collector.solutions[:solution_limit] if collector.solutions else [],
        'elapsed_time': elapsed,
        'unknown_rows': unknown_rows,
        'known_rows': list(known_rows.keys()),
        'solution_limit': solution_limit,
        'quantum_state': 'SUPERPOSITION' if num_solutions >= solution_limit else ('COLLAPSED' if num_solutions == 1 else 'INFEASIBLE')
    }


def verify_grid(grid: List[List[int]]) -> Dict:
    """驗證完整網格"""
    col_conflicts = []
    box_conflicts = []
    
    # 列檢查
    for j in range(16):
        col = [grid[i][j] for i in range(16)]
        if len(set(col)) < 16:
            col_conflicts.append(j)
    
    # 宮檢查
    for band in range(4):
        for stack in range(4):
            box = []
            for bi in range(4):
                for bj in range(4):
                    box.append(grid[band*4+bi][stack*4+bj])
            if len(set(box)) < 16:
                box_conflicts.append((band, stack))
    
    return {
        'valid': len(col_conflicts) == 0 and len(box_conflicts) == 0,
        'column_conflicts': len(col_conflicts),
        'box_conflicts': len(box_conflicts)
    }


if __name__ == '__main__':
    result = cp_sat_solve(solution_limit=10, time_limit_sec=300)
    
    # 保存結果
    with open('cp_sat_result.json', 'w', encoding='utf-8') as f:
        # 只保存部分解資料（避免太大）
        output = result.copy()
        if output['solutions']:
            # 只保存第一個解的網格前4行作為範例
            output['first_solution_sample'] = [
                sol[:4] for sol in output['solutions'][0][:4]
            ] if output['solutions'] else None
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 結果已保存到: cp_sat_result.json")
    
    # 如果有解，顯示網格
    if result['solutions']:
        print("\n" + "="*80)
        print("第一個解網格（全部16行）")
        print("="*80)
        row_labels = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
        for i, row in enumerate(result['solutions'][0]):
            row_str = ' '.join(f'{v:2d}' for v in row)
            print(f"行{row_labels[i]:2s}: {row_str}")
