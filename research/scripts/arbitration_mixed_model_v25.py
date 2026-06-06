#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 V25.0 - 仲裁後混合約束模型
 符闔超級數獨：D-E混合仲裁方案
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

仲裁原則:
- Level 1: 錨點數據（不可變更）
- Level 2: 符闔排列約束（符闔行優先）
- Level 3: 行約束（所有行）
- Level 4: 列約束（非符闔行優先，符闔行鬆綁）
- Level 5: 宮約束（非符闔行標準，符闔行鬆綁）

符闔行: C(3), D(4), I(9), P(16) - 完全固定的行
"""

from ortools.sat.python import cp_model
import json
from collections import defaultdict
import time
import hashlib

# 92錨點數據
ANCHORS_92 = [
    {'row': 1, 'col': 3, 'value': 3}, {'row': 1, 'col': 6, 'value': 12},
    {'row': 1, 'col': 8, 'value': 5}, {'row': 1, 'col': 12, 'value': 14},
    {'row': 2, 'col': 2, 'value': 12}, {'row': 2, 'col': 5, 'value': 3},
    {'row': 2, 'col': 7, 'value': 9}, {'row': 2, 'col': 9, 'value': 6},
    {'row': 3, 'col': 1, 'value': 7}, {'row': 3, 'col': 2, 'value': 15},
    {'row': 3, 'col': 3, 'value': 3}, {'row': 3, 'col': 4, 'value': 9},
    {'row': 3, 'col': 5, 'value': 11}, {'row': 3, 'col': 6, 'value': 12},
    {'row': 3, 'col': 7, 'value': 6}, {'row': 3, 'col': 8, 'value': 5},
    {'row': 3, 'col': 9, 'value': 10}, {'row': 3, 'col': 10, 'value': 2},
    {'row': 3, 'col': 11, 'value': 1}, {'row': 3, 'col': 12, 'value': 14},
    {'row': 3, 'col': 13, 'value': 13}, {'row': 3, 'col': 14, 'value': 16},
    {'row': 3, 'col': 15, 'value': 4}, {'row': 3, 'col': 16, 'value': 8},
    {'row': 4, 'col': 1, 'value': 11}, {'row': 4, 'col': 2, 'value': 4},
    {'row': 4, 'col': 3, 'value': 13}, {'row': 4, 'col': 4, 'value': 7},
    {'row': 4, 'col': 5, 'value': 16}, {'row': 4, 'col': 6, 'value': 8},
    {'row': 4, 'col': 7, 'value': 1}, {'row': 4, 'col': 8, 'value': 9},
    {'row': 4, 'col': 9, 'value': 3}, {'row': 4, 'col': 10, 'value': 15},
    {'row': 4, 'col': 11, 'value': 2}, {'row': 4, 'col': 12, 'value': 6},
    {'row': 4, 'col': 13, 'value': 5}, {'row': 4, 'col': 14, 'value': 14},
    {'row': 4, 'col': 15, 'value': 10}, {'row': 4, 'col': 16, 'value': 12},
    {'row': 5, 'col': 5, 'value': 13},
    {'row': 5, 'col': 10, 'value': 5},
    {'row': 5, 'col': 13, 'value': 4},
    {'row': 6, 'col': 2, 'value': 8},
    {'row': 6, 'col': 5, 'value': 15},
    {'row': 6, 'col': 7, 'value': 4},
    {'row': 6, 'col': 8, 'value': 3},
    {'row': 6, 'col': 11, 'value': 10},
    {'row': 6, 'col': 14, 'value': 16},
    {'row': 6, 'col': 15, 'value': 12},
    {'row': 7, 'col': 1, 'value': 14},
    {'row': 7, 'col': 3, 'value': 4},
    {'row': 7, 'col': 4, 'value': 6},
    {'row': 7, 'col': 10, 'value': 9},
    {'row': 7, 'col': 13, 'value': 15},
    {'row': 7, 'col': 16, 'value': 2},
    {'row': 8, 'col': 2, 'value': 13},
    {'row': 8, 'col': 6, 'value': 5},
    {'row': 8, 'col': 8, 'value': 9},
    {'row': 8, 'col': 12, 'value': 11},
    {'row': 8, 'col': 14, 'value': 7},
    {'row': 8, 'col': 15, 'value': 1},
    {'row': 9, 'col': 1, 'value': 13}, {'row': 9, 'col': 2, 'value': 1},
    {'row': 9, 'col': 3, 'value': 10}, {'row': 9, 'col': 4, 'value': 2},
    {'row': 9, 'col': 5, 'value': 8}, {'row': 9, 'col': 6, 'value': 11},
    {'row': 9, 'col': 7, 'value': 16}, {'row': 9, 'col': 8, 'value': 7},
    {'row': 9, 'col': 9, 'value': 14}, {'row': 9, 'col': 10, 'value': 4},
    {'row': 9, 'col': 11, 'value': 5}, {'row': 9, 'col': 12, 'value': 12},
    {'row': 9, 'col': 13, 'value': 9}, {'row': 9, 'col': 14, 'value': 6},
    {'row': 9, 'col': 15, 'value': 3}, {'row': 9, 'col': 16, 'value': 15},
    {'row': 10, 'col': 2, 'value': 5},
    {'row': 10, 'col': 6, 'value': 14},
    {'row': 10, 'col': 10, 'value': 8},
    {'row': 10, 'col': 12, 'value': 1},
    {'row': 11, 'col': 1, 'value': 1},
    {'row': 11, 'col': 3, 'value': 6},
    {'row': 11, 'col': 5, 'value': 10},
    {'row': 11, 'col': 8, 'value': 13},
    {'row': 11, 'col': 11, 'value': 9},
    {'row': 11, 'col': 14, 'value': 11},
    {'row': 12, 'col': 4, 'value': 4},
    {'row': 12, 'col': 6, 'value': 16},
    {'row': 12, 'col': 7, 'value': 14},
    {'row': 12, 'col': 9, 'value': 3},
    {'row': 12, 'col': 11, 'value': 12},
    {'row': 12, 'col': 13, 'value': 7},
    {'row': 13, 'col': 1, 'value': 15},
    {'row': 13, 'col': 5, 'value': 12},
    {'row': 13, 'col': 9, 'value': 5},
    {'row': 13, 'col': 10, 'value': 14},
    {'row': 13, 'col': 12, 'value': 8},
    {'row': 13, 'col': 15, 'value': 11},
    {'row': 13, 'col': 16, 'value': 6},
    {'row': 14, 'col': 3, 'value': 9},
    {'row': 14, 'col': 6, 'value': 6},
    {'row': 14, 'col': 9, 'value': 13},
    {'row': 14, 'col': 12, 'value': 15},
    {'row': 14, 'col': 16, 'value': 10},
    {'row': 15, 'col': 2, 'value': 1},
    {'row': 15, 'col': 5, 'value': 9},
    {'row': 15, 'col': 8, 'value': 15},
    {'row': 15, 'col': 11, 'value': 7},
    {'row': 15, 'col': 13, 'value': 16},
    {'row': 15, 'col': 14, 'value': 3},
    {'row': 16, 'col': 3, 'value': 2},
    {'row': 16, 'col': 7, 'value': 5},
]

# 符闔行定義（完全固定的行）
FUMMEL_ROWS = [3, 4, 9, 16]  # C, D, I, P

# 列衝突列表（由診斷發現）
COLUMN_CONFLICTS = [
    {'col': 3, 'value': 3, 'rows': [1, 3]},
    {'col': 6, 'value': 12, 'rows': [1, 3]},
    {'col': 8, 'value': 5, 'rows': [1, 3]},
    {'col': 8, 'value': 9, 'rows': [4, 8]},
    {'col': 12, 'value': 14, 'rows': [1, 3]},
    {'col': 2, 'value': 1, 'rows': [9, 15]},
    {'col': 9, 'value': 3, 'rows': [4, 12]},
    {'col': 14, 'value': 16, 'rows': [3, 6]},
]


class ArbitrationMixedModel:
    """仲裁後混合約束模型"""
    
    def __init__(self, grid_size=16, box_size=4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.model = cp_model.CpModel()
        self.var_grid = {}
        self.constraint_log = []
        
    def create_variables(self):
        """創建所有單元格變數"""
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                self.var_grid[(r, c)] = self.model.NewIntVar(
                    1, self.grid_size, f'cell_{r}_{c}'
                )
        self._log('variable_creation', f'創建 {self.grid_size**2} 個變數')
        
    def apply_anchors(self, anchors):
        """Level 1: 應用錨點約束（不可變更）"""
        fixed_count = 0
        for anchor in anchors:
            r, c = anchor['row'] - 1, anchor['col'] - 1
            val = anchor['value']
            self.model.Add(self.var_grid[(r, c)] == val)
            fixed_count += 1
        self._log('anchors', f'固定 {fixed_count} 個錨點值')
        
    def apply_row_all_different(self):
        """Level 3: 行AllDifferent（所有行嚴格）"""
        for r in range(self.grid_size):
            self.model.AddAllDifferent([self.var_grid[(r, c)] for c in range(self.grid_size)])
        self._log('row_ad', f'應用 {self.grid_size} 行 AllDifferent')
        
    def apply_column_all_different_arbitrated(self):
        """
        Level 4: 仲裁後列約束
        
        規則:
        - 非符闔行之間保持列AllDifferent
        - 符闔行之間允許列重複（符闔排列本質）
        - 符闔行與非符闔行之間：非符闔行優先
        """
        # 將列約束按行類型分組
        fummel_rows_idx = [r - 1 for r in FUMMEL_ROWS]  # 0索引
        normal_rows_idx = [r for r in range(self.grid_size) if r not in fummel_rows_idx]
        
        constraints_applied = 0
        
        for c in range(self.grid_size):
            # 非符闔行列AllDifferent
            normal_cells = [self.var_grid[(r, c)] for r in normal_rows_idx]
            if len(normal_cells) > 1:
                self.model.AddAllDifferent(normal_cells)
                constraints_applied += 1
            
            # 符闔行之間不施加列AllDifferent（鬆綁）
            # 這允許符闔行在列上重複值（符闔排列本質）
            
        self._log('col_ad_arbitrated', f'仲裁後列約束，{constraints_applied} 個列（非符闔行優先）')
        return constraints_applied
        
    def apply_box_all_different_arbitrated(self):
        """
        Level 5: 仲裁後宮約束
        
        規則:
        - 非符闔行宮內部保持AllDifferent
        - 符闔行宮內部：檢查是否跨符闔行重複
        - 符闔行與非符闔行混合宮：非符闔行部分AllDifferent
        """
        box_constraints = []
        
        for box_r in range(self.grid_size // self.box_size):
            for box_c in range(self.grid_size // self.box_size):
                fummel_cells = []
                normal_cells = []
                fummel_positions = []
                normal_positions = []
                
                for dr in range(self.box_size):
                    for dc in range(self.box_size):
                        r = box_r * self.box_size + dr
                        c = box_c * self.box_size + dc
                        
                        if (r + 1) in FUMMEL_ROWS:
                            fummel_cells.append(self.var_grid[(r, c)])
                            fummel_positions.append((r, c))
                        else:
                            normal_cells.append(self.var_grid[(r, c)])
                            normal_positions.append((r, c))
                
                # 非符闔行宮內部AllDifferent
                if len(normal_cells) > 1:
                    self.model.AddAllDifferent(normal_cells)
                    box_constraints.append({
                        'box': (box_r, box_c),
                        'type': 'normal_ad',
                        'cells': len(normal_cells),
                        'positions': normal_positions
                    })
                
                # 符闔行宮內部AllDifferent（符闔排列本質要求）
                if len(fummel_cells) > 1:
                    self.model.AddAllDifferent(fummel_cells)
                    box_constraints.append({
                        'box': (box_r, box_c),
                        'type': 'fummel_ad',
                        'cells': len(fummel_cells),
                        'positions': fummel_positions
                    })
        
        self._log('box_ad_arbitrated', f'仲裁後宮約束，{len(box_constraints)} 個約束')
        return box_constraints
        
    def apply_sequence_constraint(self):
        """應用序列「7 15 3 9」約束"""
        # 序列固定在C行（行3）的列1-4
        r = 2  # 0索引
        values = [7, 15, 3, 9]
        
        for i, val in enumerate(values):
            c = i  # 列0-3
            self.model.Add(self.var_grid[(r, c)] == val)
            
        self._log('sequence', '序列「7 15 3 9」固定在C行第1-4列')
        
    def _log(self, constraint_type, message):
        self.constraint_log.append({
            'type': constraint_type,
            'message': message
        })
        
    def build_model(self, use_arbitration=True):
        """構建完整模型"""
        self.create_variables()
        self.apply_anchors(ANCHORS_92)
        self.apply_row_all_different()
        
        if use_arbitration:
            self.apply_column_all_different_arbitrated()
            self.apply_box_all_different_arbitrated()
        else:
            # 標準約束（用於對比）
            for r in range(self.grid_size):
                self.model.AddAllDifferent([self.var_grid[(r, c)] for c in range(self.grid_size)])
            for c in range(self.grid_size):
                self.model.AddAllDifferent([self.var_grid[(r, c)] for r in range(self.grid_size)])
            for box_r in range(4):
                for box_c in range(4):
                    cells = []
                    for dr in range(4):
                        for dc in range(4):
                            r = box_r * 4 + dr
                            c = box_c * 4 + dc
                            cells.append(self.var_grid[(r, c)])
                    self.model.AddAllDifferent(cells)
        
        self.apply_sequence_constraint()
        
    def solve(self, time_limit_seconds=300):
        """求解模型"""
        self._log('solve_start', f'開始求解，時間限制{time_limit_seconds}秒')
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
        
        status = solver.Solve(self.model)
        
        status_map = {
            cp_model.UNKNOWN: 'UNKNOWN',
            cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.OPTIMAL: 'OPTIMAL',
            cp_model.INFEASIBLE: 'INFEASIBLE'
        }
        
        result = {
            'status': status_map.get(status, 'UNKNOWN'),
            'status_code': int(status),
            'time_used': solver.UserTime(),
            'solutions': [],
            'constraint_log': self.constraint_log
        }
        
        if status in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
            # 單解模式
            grid = []
            for r in range(self.grid_size):
                row = []
                for c in range(self.grid_size):
                    row.append(solver.Value(self.var_grid[(r, c)]))
                grid.append(row)
            result['solutions'] = [grid]
            result['solution_count'] = 1
            
        return result


def compute_solution_hash(grid):
    """計算解的唯一哈希"""
    grid_str = ''.join(str(cell) for row in grid for cell in row)
    return hashlib.sha256(grid_str.encode()).hexdigest()[:16]


def main():
    print("=" * 70)
    print("V25.0 - 仲裁後混合約束模型")
    print("符闔超級數獨 - D-E 混合仲裁方案")
    print("=" * 70)
    
    # 場景1: 標準約束（復現V24，預期INFEASIBLE）
    print("\n" + "=" * 70)
    print("場景1: 標準約束（復現V24對比）")
    print("=" * 70)
    
    model1 = ArbitrationMixedModel()
    model1.build_model(use_arbitration=False)
    result1 = model1.solve(time_limit_seconds=30)
    
    print(f"\n狀態: {result1['status']}")
    print(f"時間: {result1['time_used']:.3f}秒")
    
    # 場景2: 仲裁混合約束（預期FEASIBLE）
    print("\n" + "=" * 70)
    print("場景2: 仲裁混合約束（D-E混合）")
    print("=" * 70)
    
    model2 = ArbitrationMixedModel()
    model2.build_model(use_arbitration=True)
    result2 = model2.solve(time_limit_seconds=180)
    
    print(f"\n狀態: {result2['status']}")
    print(f"時間: {result2['time_used']:.3f}秒")
    print(f"解數量: {result2.get('solution_count', 0)}")
    
    if result2['status'] in ['FEASIBLE', 'OPTIMAL'] and result2['solutions']:
        # 顯示第一個解的片段
        sol = result2['solutions'][0]
        print("\n解範例（前4行）:")
        for i in range(4):
            row_str = ' '.join(f'{sol[i][j]:2d}' for j in range(16))
            print(f"  {chr(65+i)}: {row_str}")
        
        # 驗證解
        print("\n驗證:")
        grid = result2['solutions'][0]
        
        # 行檢查
        row_ok = all(len(set(row)) == 16 for row in grid)
        print(f"  行約束: {'✓' if row_ok else '✗'}")
        
        # 列檢查（非符闔行）
        col_ok_normal = True
        fummel_rows_idx = [r - 1 for r in FUMMEL_ROWS]
        for c in range(16):
            normal_vals = [grid[r][c] for r in range(16) if r not in fummel_rows_idx]
            if len(set(normal_vals)) != len(normal_vals):
                col_ok_normal = False
                break
        print(f"  列約束（非符闔行）: {'✓' if col_ok_normal else '✗'}")
        
        # 宮檢查（非符闔行）
        box_ok_normal = True
        for box_r in range(4):
            for box_c in range(4):
                normal_vals = []
                for dr in range(4):
                    for dc in range(4):
                        r = box_r * 4 + dr
                        c = box_c * 4 + dc
                        if (r + 1) not in FUMMEL_ROWS:
                            normal_vals.append(grid[r][c])
                if len(set(normal_vals)) != len(normal_vals):
                    box_ok_normal = False
        print(f"  宮約束（非符闔行）: {'✓' if box_ok_normal else '✗'}")
        
        # 錨點檢查
        anchor_ok = True
        for a in ANCHORS_92:
            r, c = a['row'] - 1, a['col'] - 1
            if grid[r][c] != a['value']:
                anchor_ok = False
                break
        print(f"  錨點約束: {'✓' if anchor_ok else '✗'}")
        
        # 序列檢查
        seq_ok = all(grid[2][i] == v for i, v in enumerate([7, 15, 3, 9]))
        print(f"  序列「7 15 3 9»: {'✓' if seq_ok else '✗'}")
    
    # 保存結果
    output = {
        'arbitration_framework': {
            'scheme': 'D-E 混合仲裁',
            'level1_anchors': '最高優先級（不可變更）',
            'level2_fummel_perm': '符闔排列優先',
            'level3_row': '行約束（所有行）',
            'level4_col': '列約束（非符闔行優先，符闔行鬆綁）',
            'level5_box': '宮約束（非符闔行標準，符闔行鬆綁）',
            'fummel_rows': FUMMEL_ROWS,
            'column_conflicts_exempted': COLUMN_CONFLICTS
        },
        'test_results': {
            'scenario1_standard': {
                'status': result1['status'],
                'time': result1['time_used']
            },
            'scenario2_arbitrated': {
                'status': result2['status'],
                'time': result2['time_used'],
                'solution_count': result2.get('solution_count', 0)
            }
        }
    }
    
    if result2['solutions']:
        output['solution_hash'] = compute_solution_hash(result2['solutions'][0])
    
    with open('arbitration_mixed_result_v25.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("結果已保存至: arbitration_mixed_result_v25.json")
    print("=" * 70)
    
    return result2


if __name__ == '__main__':
    main()
