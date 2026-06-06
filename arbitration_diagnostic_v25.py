#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 V25 診斷工具：增量約束檢測與衝突定位
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from ortools.sat.python import cp_model
from collections import defaultdict

# 92錨點數據
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


def check_column_conflicts(anchors):
    """檢查列約束衝突"""
    col_values = defaultdict(list)
    conflicts = []
    
    for anchor in anchors:
        c = anchor['col']
        val = anchor['value']
        col_values[c].append((anchor['row'], val))
        
    for c, values in col_values.items():
        if len(values) > 1:
            # 檢查列內是否有重複值
            val_rows = defaultdict(list)
            for r, v in values:
                val_rows[v].append(r)
            for v, rows in val_rows.items():
                if len(rows) > 1:
                    conflicts.append({
                        'type': 'column_duplicate',
                        'column': c,
                        'value': v,
                        'rows': rows
                    })
    return conflicts


def check_row_internal_conflicts(anchors):
    """檢查行內約束衝突"""
    row_values = defaultdict(list)
    conflicts = []
    
    for anchor in anchors:
        r = anchor['row']
        val = anchor['value']
        row_values[r].append((anchor['col'], val))
        
    for r, values in row_values.items():
        if len(values) > 1:
            # 檢查行內是否有重複值
            val_cols = defaultdict(list)
            for c, v in values:
                val_cols[v].append(c)
            for v, cols in val_cols.items():
                if len(cols) > 1:
                    conflicts.append({
                        'type': 'row_duplicate',
                        'row': r,
                        'value': v,
                        'cols': cols
                    })
    return conflicts


def check_box_conflicts(anchors, box_size=4):
    """檢查宮約束衝突"""
    grid_size = 16
    conflicts = []
    
    for box_r in range(grid_size // box_size):
        for box_c in range(grid_size // box_size):
            box_values = defaultdict(list)
            
            for anchor in anchors:
                r, c = anchor['row'], anchor['col']
                box_id = (r-1) // box_size, (c-1) // box_size
                if box_id == (box_r, box_c):
                    box_values[anchor['value']].append((r, c))
            
            for val, positions in box_values.items():
                if len(positions) > 1:
                    conflicts.append({
                        'type': 'box_duplicate',
                        'box': (box_r, box_c),
                        'value': val,
                        'positions': positions
                    })
    return conflicts


def incremental_cp_sat_test(anchors_subset, constraints=['anchors'], time_limit=10):
    """增量CP-SAT測試"""
    model = cp_model.CpModel()
    var_grid = {}
    
    for r in range(16):
        for c in range(16):
            var_grid[(r, c)] = model.NewIntVar(1, 16, f'cell_{r}_{c}')
    
    # 應用錨點
    for anchor in anchors_subset:
        r, c = anchor['row'] - 1, anchor['col'] - 1
        model.Add(var_grid[(r, c)] == anchor['value'])
    
    status_names = {}
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    
    if 'anchors' in constraints:
        pass  # 已應用
    
    if 'row_ad' in constraints:
        for r in range(16):
            model.AddAllDifferent([var_grid[(r, c)] for c in range(16)])
    
    if 'col_ad' in constraints:
        for c in range(16):
            model.AddAllDifferent([var_grid[(r, c)] for r in range(16)])
    
    if 'box_ad' in constraints:
        for box_r in range(4):
            for box_c in range(4):
                cells = []
                for dr in range(4):
                    for dc in range(4):
                        r = box_r * 4 + dr
                        c = box_c * 4 + dc
                        cells.append(var_grid[(r, c)])
                model.AddAllDifferent(cells)
    
    status = solver.Solve(model)
    
    status_map = {
        cp_model.UNKNOWN: 'UNKNOWN',
        cp_model.FEASIBLE: 'FEASIBLE',
        cp_model.OPTIMAL: 'OPTIMAL',
        cp_model.INFEASIBLE: 'INFEASIBLE'
    }
    
    return {
        'constraints': constraints,
        'status': status_map.get(status, 'UNKNOWN'),
        'time': solver.UserTime()
    }


def main():
    print("=" * 70)
    print("V25 增量約束診斷")
    print("=" * 70)
    
    # 1. 檢查錨點自身衝突
    print("\n--- 1. 錨點自身衝突檢查 ---")
    
    row_conflicts = check_row_internal_conflicts(ANCHORS_92)
    col_conflicts = check_column_conflicts(ANCHORS_92)
    box_conflicts = check_box_conflicts(ANCHORS_92)
    
    print(f"行內衝突: {len(row_conflicts)} 個")
    for c in row_conflicts[:5]:
        print(f"  行{c['row']}: 值{c['value']} 在列 {c['cols']}")
    
    print(f"\n列衝突: {len(col_conflicts)} 個")
    for c in col_conflicts[:10]:
        print(f"  列{c['column']}: 值{c['value']} 在行 {c['rows']}")
    
    print(f"\n宮衝突: {len(box_conflicts)} 個")
    for c in box_conflicts[:10]:
        print(f"  宮{c['box']}: 值{c['value']} 在位置 {c['positions']}")
    
    # 2. 增量CP-SAT測試
    print("\n--- 2. 增量約束CP-SAT測試 ---")
    
    test_cases = [
        (['anchors'], '僅錨點'),
        (['anchors', 'row_ad'], '錨點 + 行約束'),
        (['anchors', 'col_ad'], '錨點 + 列約束'),
        (['anchors', 'row_ad', 'col_ad'], '錨點 + 行 + 列'),
        (['anchors', 'row_ad', 'col_ad', 'box_ad'], '錨點 + 完整約束'),
    ]
    
    # 使用完整的92錨點
    result = incremental_cp_sat_test(ANCHORS_92, ['anchors', 'row_ad', 'col_ad'])
    print(f"\n行+列約束測試: {result['status']} ({result['time']:.3f}s)")
    
    # 3. 逐步加入列衝突檢測
    print("\n--- 3. 列衝突分析 ---")
    if col_conflicts:
        print("發現列衝突，需仲裁:")
        for c in col_conflicts:
            print(f"  列{c['column']}: 值{c['value']} 出現於行 {c['rows']}")
    else:
        print("列約束無衝突")
    
    # 4. 測試仅C/D/I三行
    print("\n--- 4. 關鍵行測試 (C/D/I) ---")
    cd_anchors = [a for a in ANCHORS_92 if a['row'] in [3, 4, 9]]
    
    result_cd = incremental_cp_sat_test(cd_anchors, ['anchors', 'row_ad', 'col_ad'], 10)
    print(f"C+D+I + 行+列: {result_cd['status']}")
    
    result_cd_box = incremental_cp_sat_test(cd_anchors, ['anchors', 'row_ad', 'col_ad', 'box_ad'], 10)
    print(f"C+D+I + 完整約束: {result_cd_box['status']}")
    
    # 5. 測試仅C+D两行（无I）
    print("\n--- 5. C+D两行測試 ---")
    cd_anchors_only = [a for a in ANCHORS_92 if a['row'] in [3, 4]]
    
    result_cd2 = incremental_cp_sat_test(cd_anchors_only, ['anchors', 'row_ad', 'col_ad'], 10)
    print(f"C+D + 行+列: {result_cd2['status']}")
    
    result_cd2_box = incremental_cp_sat_test(cd_anchors_only, ['anchors', 'row_ad', 'col_ad', 'box_ad'], 10)
    print(f"C+D + 完整約束: {result_cd2_box['status']}")
    
    # 6. 分析宫(0,0)冲突
    print("\n--- 6. 宮(0,0)詳細分析 ---")
    box_0_0_cells = [a for a in ANCHORS_92 if (a['row'] <= 4 and a['col'] <= 4)]
    print(f"宮(0,0)中的錨點: {len(box_0_0_cells)} 個")
    for a in box_0_0_cells:
        print(f"  行{a['row']}列{a['col']}: {a['value']}")
    
    # 值分布
    box_values = defaultdict(int)
    for a in box_0_0_cells:
        box_values[a['value']] += 1
    print("\n值分布:")
    for v, count in sorted(box_values.items()):
        if count > 1:
            print(f"  值{v}: {count}次 ⚠️ 重複!")
        else:
            print(f"  值{v}: {count}次")
    
    # 7. 生成仲裁建議
    print("\n" + "=" * 70)
    print("仲裁建議")
    print("=" * 70)
    
    if col_conflicts:
        print("\n⚠️ 列約束衝突需要仲裁:")
        for c in col_conflicts:
            print(f"  列{c['column']}: 值{c['value']} 在行 {c['rows']} 重複")
        print("  建議: 檢查原始數據或調整錨點值")
    
    if box_conflicts:
        print("\n⚠️ 宮約束衝突:")
        for c in box_conflicts[:5]:
            print(f"  宮{c['box']}: 值{c['value']} 在 {c['positions']}")
        print("  建議: 符闔超級數獨中，符闔行宮約束需要特殊處理")
    
    print("\n結論: 數據經證明正確後，約束優先級仲裁是關鍵")
    
    return {
        'row_conflicts': row_conflicts,
        'col_conflicts': col_conflicts,
        'box_conflicts': box_conflicts
    }


if __name__ == '__main__':
    main()
