#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 AC-3 衝突診斷工具
 詳細追蹤約束傳播過程中衝突產生的位置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from collections import defaultdict, deque
import copy
from typing import Dict, List, Set, Tuple, Optional
import json

# 92錨點數據
ANCHORS_92 = {
    (0, 2): 3, (0, 5): 12, (0, 7): 5, (0, 11): 14,
    (1, 1): 12, (1, 4): 3, (1, 6): 9, (1, 8): 6,
    (2, 0): 7, (2, 1): 15, (2, 2): 3, (2, 3): 9,
    (2, 4): 11, (2, 5): 12, (2, 6): 6, (2, 7): 5,
    (2, 8): 10, (2, 9): 2, (2, 10): 1, (2, 11): 14,
    (2, 12): 13, (2, 13): 16, (2, 14): 4, (2, 15): 8,
    (3, 0): 11, (3, 1): 4, (3, 2): 13, (3, 3): 7,
    (3, 4): 16, (3, 5): 8, (3, 6): 1, (3, 7): 9,
    (3, 8): 3, (3, 9): 15, (3, 10): 2, (3, 11): 6,
    (3, 12): 5, (3, 13): 14, (3, 14): 10, (3, 15): 12,
    (4, 4): 13, (4, 9): 5, (4, 12): 4,
    (5, 1): 8, (5, 4): 15, (5, 6): 4, (5, 7): 3,
    (5, 10): 10, (5, 13): 16, (5, 14): 12,
    (6, 0): 14, (6, 2): 4, (6, 3): 6, (6, 9): 9,
    (6, 12): 15, (6, 15): 2,
    (7, 1): 13, (7, 5): 5, (7, 7): 9, (7, 11): 11,
    (7, 13): 7, (7, 14): 1,
    (8, 0): 13, (8, 1): 1, (8, 2): 10, (8, 3): 2,
    (8, 4): 8, (8, 5): 11, (8, 6): 16, (8, 7): 7,
    (8, 8): 14, (8, 9): 4, (8, 10): 5, (8, 11): 12,
    (8, 12): 9, (8, 13): 6, (8, 14): 3, (8, 15): 15,
    (9, 1): 5, (9, 5): 14, (9, 9): 8, (9, 11): 1,
    (10, 0): 1, (10, 2): 6, (10, 4): 10, (10, 7): 13,
    (10, 10): 9, (10, 13): 11,
    (11, 3): 4, (11, 5): 16, (11, 6): 14, (11, 8): 3,
    (11, 10): 12, (11, 12): 7,
    (12, 0): 15, (12, 4): 12, (12, 8): 5, (12, 9): 14,
    (12, 11): 8, (12, 14): 11, (12, 15): 6,
    (13, 2): 9, (13, 5): 6, (13, 8): 13, (13, 11): 15,
    (13, 15): 10,
    (14, 1): 1, (14, 4): 9, (14, 7): 15, (14, 10): 7,
    (14, 12): 16, (14, 13): 3,
    (15, 2): 2, (15, 6): 5,
}

FUMMEL_ROWS = [2, 3, 8, 15]


class DetailedAC3Diagnostics:
    """詳細AC-3衝突診斷"""
    
    def __init__(self, grid_size=16, box_size=4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.values = {}
        self.neighbors = defaultdict(set)
        self.arcs = deque()
        self.diagnostic_log = []
        
    def initialize_domains(self, anchors: Dict[Tuple[int,int], int]):
        """初始化定義域"""
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if (r, c) in anchors:
                    self.values[(r, c)] = {anchors[(r, c)]}
                else:
                    self.values[(r, c)] = set(range(1, self.grid_size + 1))
        
        self._build_constraint_graph()
        
    def _build_constraint_graph(self):
        """構建約束圖"""
        # 行約束（所有行）
        for r in range(self.grid_size):
            for c1 in range(self.grid_size):
                for c2 in range(c1+1, self.grid_size):
                    self.neighbors[(r, c1)].add((r, c2))
                    self.neighbors[(r, c2)].add((r, c1))
                    
        # 列約束（非符闔行之間）
        for c in range(self.grid_size):
            normal_rows = [r for r in range(self.grid_size) if r not in FUMMEL_ROWS]
            for r1_idx in range(len(normal_rows)):
                for r2_idx in range(r1_idx+1, len(normal_rows)):
                    r1, r2 = normal_rows[r1_idx], normal_rows[r2_idx]
                    self.neighbors[(r1, c)].add((r2, c))
                    self.neighbors[(r2, c)].add((r1, c))
                    
        # 宮約束（非符闔行之間）
        for box_r in range(self.grid_size // self.box_size):
            for box_c in range(self.grid_size // self.box_size):
                normal_cells = []
                for dr in range(self.box_size):
                    for dc in range(self.box_size):
                        r = box_r * self.box_size + dr
                        c = box_c * self.box_size + dc
                        if r not in FUMMEL_ROWS:
                            normal_cells.append((r, c))
                for i in range(len(normal_cells)):
                    for j in range(i+1, len(normal_cells)):
                        self.neighbors[normal_cells[i]].add(normal_cells[j])
                        self.neighbors[normal_cells[j]].add(normal_cells[i])
        
        # 初始化弧队列
        self.arcs = deque()
        for x in self.values:
            for y in self.neighbors[x]:
                self.arcs.append((x, y))
    
    def revise(self, xi: Tuple[int,int], xj: Tuple[int,int]) -> Tuple[bool, List[int]]:
        """Revise 函數，返回是否修改及被刪除的值"""
        revised = False
        removed_values = []
        
        xi_vals = self.values[xi]
        xj_vals = self.values[xj]
        
        if len(xj_vals) == 1:
            xj_val = next(iter(xj_vals))
            new_vals = xi_vals - {xj_val}
            if len(new_vals) != len(xi_vals):
                revised = True
                removed_values = list(xi_vals - new_vals)
                self.values[xi] = new_vals
        
        return revised, removed_values
    
    def ac3_detailed(self) -> Tuple[bool, List[Dict]]:
        """
        AC-3 詳細診斷
        返回：(是否成功, 診斷日誌)
        """
        self.diagnostic_log = []
        iterations = 0
        arc_count = len(self.arcs)
        
        # 記錄初始狀態
        self.diagnostic_log.append({
            'phase': 'initial',
            'total_vars': len(self.values),
            'arcs': arc_count,
            'assigned': len([v for v, vals in self.values.items() if len(vals) == 1])
        })
        
        conflict_details = []
        
        while self.arcs and iterations < 50000:
            iterations += 1
            xi, xj = self.arcs.popleft()
            
            revised, removed = self.revise(xi, xj)
            
            if revised:
                # 記錄修改詳情
                if len(self.values[xi]) == 0:
                    # 約束衝突
                    conflict_details.append({
                        'iteration': iterations,
                        'xi': xi,
                        'xj': xj,
                        'xi_row': chr(65 + xi[0]),
                        'xj_row': chr(65 + xj[0]),
                        'xi_col': xi[1] + 1,
                        'xj_col': xj[1] + 1,
                        'removed_values': removed,
                        'type': 'column_conflict' if xi[1] == xj[1] else 'box_conflict',
                        'xi_anchor': (xi in self._get_anchors()) and self.values.get(xi, set()),
                        'xj_anchor': (xj in self._get_anchors()) and self.values.get(xj, set()),
                    })
                    self.diagnostic_log.append({
                        'phase': 'conflict',
                        'iteration': iterations,
                        'var': xi,
                        'conflict_with': xj,
                        'constraint_type': 'column' if xi[1] == xj[1] else 'box',
                        'removed_values': removed
                    })
                    return False, conflict_details
                
                # 記錄重要削減
                if len(removed) > 0:
                    self.diagnostic_log.append({
                        'phase': 'reduce',
                        'iteration': iterations,
                        'var': xi,
                        'removed': removed,
                        'from_constraint': xj,
                        'constraint_type': 'column' if xi[1] == xj[1] else 'box',
                    })
                
                for xk in self.neighbors[xi]:
                    if xk != xj:
                        self.arcs.append((xk, xi))
        
        self.diagnostic_log.append({
            'phase': 'complete',
            'iterations': iterations,
            'arcs_processed': arc_count,
            'remaining_arcs': len(self.arcs)
        })
        
        return True, conflict_details
    
    def _get_anchors(self):
        """獲取錨點集合"""
        return set((r, c) for (r, c), v in ANCHORS_92.items())
    
    def analyze_conflicts(self, conflict_details: List[Dict]) -> Dict:
        """分析衝突模式"""
        analysis = {
            'total_conflicts': len(conflict_details),
            'by_constraint_type': defaultdict(int),
            'by_column': defaultdict(int),
            'by_row_pair': defaultdict(int),
            'anchor_related': 0,
        }
        
        for detail in conflict_details:
            ctype = detail['type']
            analysis['by_constraint_type'][ctype] += 1
            
            if ctype == 'column_conflict':
                col = detail['xi_col']
                analysis['by_column'][col] += 1
                row_pair = f"{detail['xi_row']}-{detail['xj_row']}"
                analysis['by_row_pair'][row_pair] += 1
            
            # 檢查是否涉及錨點
            if detail.get('xi_anchor') or detail.get('xj_anchor'):
                analysis['anchor_related'] += 1
        
        # 轉為普通dict
        analysis['by_constraint_type'] = dict(analysis['by_constraint_type'])
        analysis['by_column'] = dict(analysis['by_column'])
        analysis['by_row_pair'] = dict(analysis['by_row_pair'])
        
        return analysis


def incremental_diagnostic(max_rows: int):
    """分步診斷：檢查前max_rows行的約束"""
    anchors_subset = {k: v for k, v in ANCHORS_92.items() if k[0] < max_rows}
    
    print(f"\n{'='*70}")
    print(f"分步診斷：錨點範圍 = 前 {max_rows} 行（行A-{chr(64+max_rows)}）")
    print(f"{'='*70}")
    print(f"錨點數量: {len(anchors_subset)}")
    
    solver = DetailedAC3Diagnostics()
    solver.initialize_domains(anchors_subset)
    
    print(f"\n初始狀態:")
    print(f"  總變量: {len(solver.values)}")
    print(f"  已賦值: {len([v for v, vals in solver.values.items() if len(vals) == 1])}")
    print(f"  約束弧: {len(solver.arcs)}")
    
    success, conflicts = solver.ac3_detailed()
    
    if success:
        print(f"\n✅ AC-3 成功完成")
        print(f"  迭代次數: {len([d for d in solver.diagnostic_log if d['phase'] == 'reduce'])}")
    else:
        print(f"\n❌ AC-3 發現約束衝突")
        print(f"  衝突數量: {len(conflicts)}")
        
        # 分析衝突模式
        analysis = solver.analyze_conflicts(conflicts)
        
        print(f"\n--- 衝突分析 ---")
        print(f"總衝突數: {analysis['total_conflicts']}")
        print(f"列衝突: {analysis['by_constraint_type'].get('column_conflict', 0)}")
        print(f"宮衝突: {analysis['by_constraint_type'].get('box_conflict', 0)}")
        
        if analysis['by_column']:
            print(f"\n列衝突分佈:")
            for col, count in sorted(analysis['by_column'].items(), key=lambda x: -x[1])[:5]:
                print(f"  列{col}: {count}次衝突")
        
        if analysis['by_row_pair']:
            print(f"\n行間衝突分佈:")
            for pair, count in sorted(analysis['by_row_pair'].items(), key=lambda x: -x[1])[:5]:
                print(f"  {pair}: {count}次衝突")
        
        print(f"涉及錨點的衝突: {analysis['anchor_related']}")
        
        # 顯示前5個衝突詳情
        if conflicts:
            print(f"\n--- 前5個衝突詳情 ---")
            for i, c in enumerate(conflicts[:5]):
                print(f"衝突{i+1}: {c['xi_row']}{c['xi_col']} ← {c['xi_col']}列約束 {c['xj_row']}{c['xj_col']}")
                print(f"  涉及錨點: xi={'✓' if c.get('xi_anchor') else '✗'}, xj={'✓' if c.get('xj_anchor') else '✗'}")
    
    return success, conflicts, analysis if not success else None


def main():
    print("=" * 70)
    print("AC-3 衝突診斷工具")
    print("符闔超級數獨 - 仲裁後混合約束")
    print("=" * 70)
    
    # 分步診斷
    results = {}
    for rows in [4, 8, 12, 16]:
        success, conflicts, analysis = incremental_diagnostic(rows)
        results[rows] = {'success': success, 'conflicts': len(conflicts), 'analysis': analysis}
    
    # 匯總
    print(f"\n{'='*70}")
    print("診斷匯總")
    print(f"{'='*70}")
    
    for rows, data in results.items():
        status = "✅" if data['success'] else "❌"
        conflict_count = data['conflicts']
        print(f"  前{rows:2d}行: {status} 衝突數={conflict_count}")
    
    # 關鍵發現
    print(f"\n--- 關鍵發現 ---")
    
    if results[4]['success'] and results[8]['success'] and not results[12]['success']:
        print("約束衝突出現在12行錨點時！")
        print("衝突根源：非符闔行之間的列約束與錨點數據不相容")
        
        # 詳細分析12行衝突
        _, conflicts, analysis = incremental_diagnostic(12)
        
        if analysis:
            print(f"\n列衝突Top 5:")
            for col, count in sorted(analysis['by_column'].items(), key=lambda x: -x[1])[:5]:
                print(f"  列{col}: {count}次衝突")
            
            print(f"\n涉及錨點的衝突占比: {analysis['anchor_related']}/{len(conflicts)} = {analysis['anchor_related']/len(conflicts)*100:.1f}%")
    
    return results


if __name__ == '__main__':
    main()
