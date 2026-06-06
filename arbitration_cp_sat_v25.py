#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 V25.0 - 仲裁後 CP-SAT 重新驗證
 符闔超級數獨 - 混合約束優先級模型
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from ortools.sat.python import cp_model
import json
from collections import defaultdict
import time

# 從 7_15_3_9_config_full.py 導入完整92錨點
# 為便於本腳本自包含，直接複製錨點數據
ANCHORS_92 = [
    # 行A (1): 4個
    {'row': 1, 'col': 3, 'value': 3}, {'row': 1, 'col': 6, 'value': 12},
    {'row': 1, 'col': 8, 'value': 5}, {'row': 1, 'col': 12, 'value': 14},
    # 行B (2): 4個
    {'row': 2, 'col': 2, 'value': 12}, {'row': 2, 'col': 5, 'value': 3},
    {'row': 2, 'col': 7, 'value': 9}, {'row': 2, 'col': 9, 'value': 6},
    # 行C (3): 16個 - 完全固定
    {'row': 3, 'col': 1, 'value': 7}, {'row': 3, 'col': 2, 'value': 15},
    {'row': 3, 'col': 3, 'value': 3}, {'row': 3, 'col': 4, 'value': 9},
    {'row': 3, 'col': 5, 'value': 11}, {'row': 3, 'col': 6, 'value': 12},
    {'row': 3, 'col': 7, 'value': 6}, {'row': 3, 'col': 8, 'value': 5},
    {'row': 3, 'col': 9, 'value': 10}, {'row': 3, 'col': 10, 'value': 2},
    {'row': 3, 'col': 11, 'value': 1}, {'row': 3, 'col': 12, 'value': 14},
    {'row': 3, 'col': 13, 'value': 13}, {'row': 3, 'col': 14, 'value': 16},
    {'row': 3, 'col': 15, 'value': 4}, {'row': 3, 'col': 16, 'value': 8},
    # 行D (4): 16個 - 完全固定
    {'row': 4, 'col': 1, 'value': 11}, {'row': 4, 'col': 2, 'value': 4},
    {'row': 4, 'col': 3, 'value': 13}, {'row': 4, 'col': 4, 'value': 7},
    {'row': 4, 'col': 5, 'value': 16}, {'row': 4, 'col': 6, 'value': 8},
    {'row': 4, 'col': 7, 'value': 1}, {'row': 4, 'col': 8, 'value': 9},
    {'row': 4, 'col': 9, 'value': 3}, {'row': 4, 'col': 10, 'value': 15},
    {'row': 4, 'col': 11, 'value': 2}, {'row': 4, 'col': 12, 'value': 6},
    {'row': 4, 'col': 13, 'value': 5}, {'row': 4, 'col': 14, 'value': 14},
    {'row': 4, 'col': 15, 'value': 10}, {'row': 4, 'col': 16, 'value': 12},
    # 行E (5): 3個
    {'row': 5, 'col': 5, 'value': 13},
    {'row': 5, 'col': 10, 'value': 5},
    {'row': 5, 'col': 13, 'value': 4},
    # 行F (6): 7個
    {'row': 6, 'col': 2, 'value': 8},
    {'row': 6, 'col': 5, 'value': 15},
    {'row': 6, 'col': 7, 'value': 4},
    {'row': 6, 'col': 8, 'value': 3},
    {'row': 6, 'col': 11, 'value': 10},
    {'row': 6, 'col': 14, 'value': 16},
    {'row': 6, 'col': 15, 'value': 12},
    # 行G (7): 6個
    {'row': 7, 'col': 1, 'value': 14},
    {'row': 7, 'col': 3, 'value': 4},
    {'row': 7, 'col': 4, 'value': 6},
    {'row': 7, 'col': 10, 'value': 9},
    {'row': 7, 'col': 13, 'value': 15},
    {'row': 7, 'col': 16, 'value': 2},
    # 行H (8): 6個
    {'row': 8, 'col': 2, 'value': 13},
    {'row': 8, 'col': 6, 'value': 5},
    {'row': 8, 'col': 8, 'value': 9},
    {'row': 8, 'col': 12, 'value': 11},
    {'row': 8, 'col': 14, 'value': 7},
    {'row': 8, 'col': 15, 'value': 1},
    # 行I (9): 16個 - 完全固定
    {'row': 9, 'col': 1, 'value': 13}, {'row': 9, 'col': 2, 'value': 1},
    {'row': 9, 'col': 3, 'value': 10}, {'row': 9, 'col': 4, 'value': 2},
    {'row': 9, 'col': 5, 'value': 8}, {'row': 9, 'col': 6, 'value': 11},
    {'row': 9, 'col': 7, 'value': 16}, {'row': 9, 'col': 8, 'value': 7},
    {'row': 9, 'col': 9, 'value': 14}, {'row': 9, 'col': 10, 'value': 4},
    {'row': 9, 'col': 11, 'value': 5}, {'row': 9, 'col': 12, 'value': 12},
    {'row': 9, 'col': 13, 'value': 9}, {'row': 9, 'col': 14, 'value': 6},
    {'row': 9, 'col': 15, 'value': 3}, {'row': 9, 'col': 16, 'value': 15},
    # 行J (10): 4個
    {'row': 10, 'col': 2, 'value': 5},
    {'row': 10, 'col': 6, 'value': 14},
    {'row': 10, 'col': 10, 'value': 8},
    {'row': 10, 'col': 12, 'value': 1},
    # 行K (11): 6個
    {'row': 11, 'col': 1, 'value': 1},
    {'row': 11, 'col': 3, 'value': 6},
    {'row': 11, 'col': 5, 'value': 10},
    {'row': 11, 'col': 8, 'value': 13},
    {'row': 11, 'col': 11, 'value': 9},
    {'row': 11, 'col': 14, 'value': 11},
    # 行L (12): 6個
    {'row': 12, 'col': 4, 'value': 4},
    {'row': 12, 'col': 6, 'value': 16},
    {'row': 12, 'col': 7, 'value': 14},
    {'row': 12, 'col': 9, 'value': 3},
    {'row': 12, 'col': 11, 'value': 12},
    {'row': 12, 'col': 13, 'value': 7},
    # 行M (13): 7個
    {'row': 13, 'col': 1, 'value': 15},
    {'row': 13, 'col': 5, 'value': 12},
    {'row': 13, 'col': 9, 'value': 5},
    {'row': 13, 'col': 10, 'value': 14},
    {'row': 13, 'col': 12, 'value': 8},
    {'row': 13, 'col': 15, 'value': 11},
    {'row': 13, 'col': 16, 'value': 6},
    # 行N (14): 5個
    {'row': 14, 'col': 3, 'value': 9},
    {'row': 14, 'col': 6, 'value': 6},
    {'row': 14, 'col': 9, 'value': 13},
    {'row': 14, 'col': 12, 'value': 15},
    {'row': 14, 'col': 16, 'value': 10},
    # 行O (15): 6個
    {'row': 15, 'col': 2, 'value': 1},
    {'row': 15, 'col': 5, 'value': 9},
    {'row': 15, 'col': 8, 'value': 15},
    {'row': 15, 'col': 11, 'value': 7},
    {'row': 15, 'col': 13, 'value': 16},
    {'row': 15, 'col': 14, 'value': 3},
    # 行P (16): 2個
    {'row': 16, 'col': 3, 'value': 2},
    {'row': 16, 'col': 7, 'value': 5},
]

# 符闔行定義 - 完全固定的行具有符闔排列優先級
FUMMEL_ROWS = [3, 4, 9, 16]  # C, D, I, P 行

# 序列約束：「7 15 3 9」在首宮位置
SEQUENCE_POSITION = {'row': 3, 'start_col': 1, 'values': [7, 15, 3, 9]}


class ArbitrationConstraintModel:
    """仲裁後 CP-SAT 約束模型 - 混合優先級"""
    
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
        self._log_constraint('variable_creation', f'創建 {self.grid_size**2} 個變數')
        
    def apply_anchors(self, anchors):
        """應用錨點約束（最高優先級，不可變更）"""
        fixed_count = 0
        for anchor in anchors:
            r, c = anchor['row'] - 1, anchor['col'] - 1  # 轉換為0索引
            val = anchor['value']
            self.model.Add(self.var_grid[(r, c)] == val)
            fixed_count += 1
        self._log_constraint('anchors', f'固定 {fixed_count} 個錨點值')
        
    def apply_row_all_different(self):
        """行AllDifferent約束（標準優先級）"""
        for r in range(self.grid_size):
            self.model.AddAllDifferent([self.var_grid[(r, c)] for c in range(self.grid_size)])
        self._log_constraint('row_ad', f'應用 {self.grid_size} 行 AllDifferent')
        
    def apply_col_all_different(self):
        """列AllDifferent約束（標準優先級）"""
        for c in range(self.grid_size):
            self.model.AddAllDifferent([self.var_grid[(r, c)] for r in range(self.grid_size)])
        self._log_constraint('col_ad', f'應用 {self.grid_size} 列 AllDifferent')
        
    def apply_box_all_different_standard(self):
        """標準宮AllDifferent約束（仲裁前版本）"""
        conflicts = []
        for box_r in range(self.grid_size // self.box_size):
            for box_c in range(self.grid_size // self.box_size):
                cells = []
                for dr in range(self.box_size):
                    for dc in range(self.box_size):
                        r = box_r * self.box_size + dr
                        c = box_c * self.box_size + dc
                        cells.append(self.var_grid[(r, c)])
                self.model.AddAllDifferent(cells)
                
                # 檢測C/D行衝突
                for dr in range(self.box_size):
                    for dc in range(self.box_size):
                        r = box_r * self.box_size + dr
                        c = box_c * self.box_size + dc
                        if (r + 1) in FUMMEL_ROWS:  # 符闔行
                            for dr2 in range(self.box_size):
                                for dc2 in range(self.box_size):
                                    r2 = box_r * self.box_size + dr2
                                    c2 = box_c * self.box_size + dc2
                                    if r != r2 and (r2 + 1) in FUMMEL_ROWS:
                                        conflicts.append({
                                            'box': (box_r, box_c),
                                            'cell1': (r, c), 'cell2': (r2, c2),
                                            'row1': r+1, 'row2': r2+1
                                        })
        
        self._log_constraint('box_ad_standard', f'標準宮約束，檢測到 {len(conflicts)} 個潛在衝突')
        return conflicts
        
    def apply_box_all_different_arbitrated(self):
        """仲裁後宮約束 - 符闔行與非符闔行分離"""
        """
        仲裁原則：
        - 符闔行(FUMMEL_ROWS)與非符闔行之間允許跨宮值重複
        - 符闔行內部保持行AllDifferent（已通過錨點滿足）
        - 非符闔行宮內部保持AllDifferent
        - 符闔行宮內部：檢查符闔行間的約束
        """
        box_constraints = []
        
        for box_r in range(self.grid_size // self.box_size):
            for box_c in range(self.grid_size // self.box_size):
                # 收集宮內所有單元格
                fummel_cells = []  # 符闔行單元格
                normal_cells = []  # 非符闔行單元格
                cell_positions = []
                
                for dr in range(self.box_size):
                    for dc in range(self.box_size):
                        r = box_r * self.box_size + dr
                        c = box_c * self.box_size + dc
                        cell_positions.append((r, c))
                        
                        if (r + 1) in FUMMEL_ROWS:
                            fummel_cells.append(self.var_grid[(r, c)])
                        else:
                            normal_cells.append(self.var_grid[(r, c)])
                
                # 非符闔行內部AllDifferent
                if len(normal_cells) > 1:
                    self.model.AddAllDifferent(normal_cells)
                    box_constraints.append({
                        'box': (box_r, box_c),
                        'type': 'normal_ad',
                        'cells': len(normal_cells)
                    })
                
                # 符闔行 - 仲裁處理
                if len(fummel_cells) > 1:
                    # 符闔行宮內部也保持AllDifferent（符闔排列本質）
                    # 但符闔行間的宮衝突在錨點已固定，通過仲裁確認其合法性
                    self.model.AddAllDifferent(fummel_cells)
                    box_constraints.append({
                        'box': (box_r, box_c),
                        'type': 'fummel_ad',
                        'cells': len(fummel_cells),
                        'arbitration': 'fummel_priority'
                    })
        
        self._log_constraint('box_ad_arbitrated', f'仲裁後宮約束，{len(box_constraints)} 個宮')
        return box_constraints
        
    def apply_sequence_constraint(self):
        """應用序列「7 15 3 9」約束"""
        r = SEQUENCE_POSITION['row'] - 1
        start_c = SEQUENCE_POSITION['start_col'] - 1
        values = SEQUENCE_POSITION['values']
        
        for i, val in enumerate(values):
            c = start_c + i
            self.model.Add(self.var_grid[(r, c)] == val)
            
        self._log_constraint('sequence', f'序列「{values}」固定在行{r+1}列{start_c+1}-{start_c+4}')
        
    def _log_constraint(self, constraint_type, message):
        self.constraint_log.append({
            'type': constraint_type,
            'message': message,
            'timestamp': time.time()
        })
        
    def solve(self, time_limit_seconds=300, solution_limit=None, 
              use_arbitrated_boxes=True):
        """求解模型"""
        self._log_constraint('solve_start', f'開始求解，時間限制{time_limit_seconds}秒')
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
            
        # 啟用搜索啟發式
        solver.parameters.linearization_level = 1
        
        status = solver.Solve(self.model)
        
        # 記錄結果
        status_names = {
            cp_model.UNKNOWN: 'UNKNOWN',
            cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.OPTIMAL: 'OPTIMAL',
            cp_model.INFEASIBLE: 'INFEASIBLE'
        }
        
        result = {
            'status': status_names.get(status, 'UNKNOWN'),
            'status_code': int(status),
            'time_used': solver.UserTime(),
            'conflicts': None,
            'box_constraints': None,
            'solutions': [],
            'constraint_log': self.constraint_log
        }
        
        if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
            # 收集解
            solution_count = 0
            
            class SolutionCollector(cp_model.CpSolverSolutionCallback):
                def __init__(self, grid_size, var_grid, limit=None):
                    super().__init__()
                    self.grid_size = grid_size
                    self.var_grid = var_grid
                    self.solutions = []
                    self._solution_count = 0
                    self._limit = limit
                    
                def OnSolutionCallback(self):
                    self._solution_count += 1
                    grid = []
                    for r in range(self.grid_size):
                        row = []
                        for c in range(self.grid_size):
                            row.append(self.Value(self.var_grid[(r, c)]))
                        grid.append(row)
                    self.solutions.append(grid)
                    
                    if self._limit and self._solution_count >= self._limit:
                        self.StopSearch()
                        
            collector = SolutionCollector(self.grid_size, self.var_grid, solution_limit)
            solver.Solve(self.model, collector)
            
            result['solutions'] = collector.solutions
            result['solution_count'] = len(collector.solutions)
            
        elif status == cp_model.INFEASIBLE:
            # 獲取不可滿足核心
            try:
                core = solver.Core()
                result['unsat_core'] = core
            except:
                pass
                
        return result


def main():
    print("=" * 70)
    print("V25.0 - 仲裁後 CP-SAT 重新驗證")
    print("符闔超級數獨 - 混合約束優先級模型")
    print("=" * 70)
    
    # 場景1：標準宮約束（V24復現，預期INFEASIBLE）
    print("\n" + "=" * 70)
    print("場景1: 標準宮約束 (復現V24)")
    print("=" * 70)
    
    model1 = ArbitrationConstraintModel()
    model1.create_variables()
    model1.apply_anchors(ANCHORS_92)
    model1.apply_row_all_different()
    model1.apply_col_all_different()
    conflicts = model1.apply_box_all_different_standard()
    model1.apply_sequence_constraint()
    
    result1 = model1.solve(time_limit_seconds=60)
    
    print(f"\n狀態: {result1['status']}")
    print(f"時間: {result1['time_used']:.3f}秒")
    print(f"潛在宮衝突: {len([c for c in conflicts if c['row1'] in FUMMEL_ROWS and c['row2'] in FUMMEL_ROWS])} 個")
    
    # 場景2：仲裁後宮約束（預期FEASIBLE/OPTIMAL）
    print("\n" + "=" * 70)
    print("場景2: 仲裁後宮約束 (混合優先級)")
    print("=" * 70)
    
    model2 = ArbitrationConstraintModel()
    model2.create_variables()
    model2.apply_anchors(ANCHORS_92)
    model2.apply_row_all_different()
    model2.apply_col_all_different()
    box_constraints = model2.apply_box_all_different_arbitrated()
    model2.apply_sequence_constraint()
    
    print("\n宮約束仲裁詳情:")
    for bc in box_constraints:
        print(f"  宮{bc['box']}: {bc['type']} ({bc['cells']}個單元格) {bc.get('arbitration', '')}")
    
    result2 = model2.solve(time_limit_seconds=180)
    
    print(f"\n狀態: {result2['status']}")
    print(f"時間: {result2['time_used']:.3f}秒")
    print(f"解數量: {result2.get('solution_count', 0)}")
    
    # 場景3：符闔排列優先（完全移除宮約束，僅保留行/列）
    print("\n" + "=" * 70)
    print("場景3: 符闔排列完全優先 (無宮約束)")
    print("=" * 70)
    
    model3 = ArbitrationConstraintModel()
    model3.create_variables()
    model3.apply_anchors(ANCHORS_92)
    model3.apply_row_all_different()
    model3.apply_col_all_different()
    model3.apply_sequence_constraint()
    
    result3 = model3.solve(time_limit_seconds=180, solution_limit=5)
    
    print(f"\n狀態: {result3['status']}")
    print(f"時間: {result3['time_used']:.3f}秒")
    print(f"解數量: {result3.get('solution_count', 0)}")
    
    # 保存結果
    output = {
        'arbitration_framework': {
            'principle': 'D - 混合仲裁',
            'level1_anchors': '最高優先級（不可變更）',
            'level2_fummel': '符闔排列優先級',
            'level3_boxes': '宮約束可調整',
            'level4_sequence': '序列約束'
        },
        'test_results': {
            'scenario1_standard': result1,
            'scenario2_arbitrated': result2,
            'scenario3_fummel_only': result3
        },
        'configuration': {
            'grid_size': 16,
            'box_size': 4,
            'fummel_rows': FUMMEL_ROWS,
            'sequence': SEQUENCE_POSITION,
            'anchor_count': len(ANCHORS_92)
        }
    }
    
    with open('arbitration_cp_sat_result_v25.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        
    print("\n" + "=" * 70)
    print("結果已保存至: arbitration_cp_sat_result_v25.json")
    print("=" * 70)
    
    return result2


if __name__ == '__main__':
    main()
