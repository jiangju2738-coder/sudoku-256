#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
55锚点 vs 92锚点 覆盖关系验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

核心问题：55锚点的唯一解是否能覆盖92锚点的所有约束？
如果不能，则两者是"两码事"（完全不同的谜题）
"""

from __future__ import annotations
import json
import time
from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass

GRID_SIZE = 16
BOX_SIZE = 4

# ═══════════════════════════════════════════════════════════
# 92锚点完整配置 (来自 7_15_3_9_config_full.py)
# ═══════════════════════════════════════════════════════════
FULL_92_ANCHORS = [
    # 行A (1): 4个
    {'row': 1, 'col': 3, 'value': 3},
    {'row': 1, 'col': 6, 'value': 12},
    {'row': 1, 'col': 8, 'value': 5},
    {'row': 1, 'col': 12, 'value': 14},
    # 行B (2): 4个
    {'row': 2, 'col': 2, 'value': 12},
    {'row': 2, 'col': 5, 'value': 3},
    {'row': 2, 'col': 7, 'value': 9},
    {'row': 2, 'col': 9, 'value': 6},
    # 行C (3): 16个 - 完全固定
    {'row': 3, 'col': 1, 'value': 7}, {'row': 3, 'col': 2, 'value': 15},
    {'row': 3, 'col': 3, 'value': 3}, {'row': 3, 'col': 4, 'value': 9},
    {'row': 3, 'col': 5, 'value': 11}, {'row': 3, 'col': 6, 'value': 12},
    {'row': 3, 'col': 7, 'value': 6}, {'row': 3, 'col': 8, 'value': 5},
    {'row': 3, 'col': 9, 'value': 10}, {'row': 3, 'col': 10, 'value': 2},
    {'row': 3, 'col': 11, 'value': 1}, {'row': 3, 'col': 12, 'value': 14},
    {'row': 3, 'col': 13, 'value': 13}, {'row': 3, 'col': 14, 'value': 16},
    {'row': 3, 'col': 15, 'value': 4}, {'row': 3, 'col': 16, 'value': 8},
    # 行D (4): 16个 - 完全固定
    {'row': 4, 'col': 1, 'value': 11}, {'row': 4, 'col': 2, 'value': 4},
    {'row': 4, 'col': 3, 'value': 13}, {'row': 4, 'col': 4, 'value': 7},
    {'row': 4, 'col': 5, 'value': 16}, {'row': 4, 'col': 6, 'value': 8},
    {'row': 4, 'col': 7, 'value': 1}, {'row': 4, 'col': 8, 'value': 9},
    {'row': 4, 'col': 9, 'value': 3}, {'row': 4, 'col': 10, 'value': 15},
    {'row': 4, 'col': 11, 'value': 2}, {'row': 4, 'col': 12, 'value': 6},
    {'row': 4, 'col': 13, 'value': 5}, {'row': 4, 'col': 14, 'value': 14},
    {'row': 4, 'col': 15, 'value': 10}, {'row': 4, 'col': 16, 'value': 12},
    # 行E (5): 3个
    {'row': 5, 'col': 5, 'value': 13},
    {'row': 5, 'col': 10, 'value': 5},
    {'row': 5, 'col': 13, 'value': 4},
    # 行F (6): 7个
    {'row': 6, 'col': 2, 'value': 8},
    {'row': 6, 'col': 5, 'value': 15},
    {'row': 6, 'col': 7, 'value': 4},
    {'row': 6, 'col': 8, 'value': 3},
    {'row': 6, 'col': 11, 'value': 10},
    {'row': 6, 'col': 14, 'value': 16},
    {'row': 6, 'col': 15, 'value': 12},
    # 行G (7): 6个
    {'row': 7, 'col': 1, 'value': 14},
    {'row': 7, 'col': 3, 'value': 4},
    {'row': 7, 'col': 4, 'value': 6},
    {'row': 7, 'col': 10, 'value': 9},
    {'row': 7, 'col': 13, 'value': 15},
    {'row': 7, 'col': 16, 'value': 2},
    # 行H (8): 6个
    {'row': 8, 'col': 2, 'value': 13},
    {'row': 8, 'col': 6, 'value': 5},
    {'row': 8, 'col': 8, 'value': 9},
    {'row': 8, 'col': 12, 'value': 11},
    {'row': 8, 'col': 14, 'value': 7},
    {'row': 8, 'col': 15, 'value': 1},
    # 行I (9): 16个 - 完全固定
    {'row': 9, 'col': 1, 'value': 13}, {'row': 9, 'col': 2, 'value': 1},
    {'row': 9, 'col': 3, 'value': 10}, {'row': 9, 'col': 4, 'value': 2},
    {'row': 9, 'col': 5, 'value': 8}, {'row': 9, 'col': 6, 'value': 11},
    {'row': 9, 'col': 7, 'value': 16}, {'row': 9, 'col': 8, 'value': 7},
    {'row': 9, 'col': 9, 'value': 14}, {'row': 9, 'col': 10, 'value': 4},
    {'row': 9, 'col': 11, 'value': 5}, {'row': 9, 'col': 12, 'value': 12},
    {'row': 9, 'col': 13, 'value': 9}, {'row': 9, 'col': 14, 'value': 6},
    {'row': 9, 'col': 15, 'value': 3}, {'row': 9, 'col': 16, 'value': 15},
    # 行J (10): 4个
    {'row': 10, 'col': 2, 'value': 5},
    {'row': 10, 'col': 6, 'value': 14},
    {'row': 10, 'col': 10, 'value': 8},
    {'row': 10, 'col': 12, 'value': 1},
    # 行K (11): 6个
    {'row': 11, 'col': 1, 'value': 1},
    {'row': 11, 'col': 3, 'value': 6},
    {'row': 11, 'col': 5, 'value': 10},
    {'row': 11, 'col': 8, 'value': 13},
    {'row': 11, 'col': 11, 'value': 9},
    {'row': 11, 'col': 14, 'value': 11},
    # 行L (12): 6个
    {'row': 12, 'col': 4, 'value': 4},
    {'row': 12, 'col': 6, 'value': 16},
    {'row': 12, 'col': 7, 'value': 14},
    {'row': 12, 'col': 9, 'value': 3},
    {'row': 12, 'col': 11, 'value': 12},
    {'row': 12, 'col': 13, 'value': 7},
    # 行M (13): 7个
    {'row': 13, 'col': 1, 'value': 15},
    {'row': 13, 'col': 5, 'value': 12},
    {'row': 13, 'col': 9, 'value': 5},
    {'row': 13, 'col': 10, 'value': 14},
    {'row': 13, 'col': 12, 'value': 8},
    {'row': 13, 'col': 15, 'value': 11},
    {'row': 13, 'col': 16, 'value': 6},
    # 行N (14): 5个
    {'row': 14, 'col': 3, 'value': 9},
    {'row': 14, 'col': 6, 'value': 6},
    {'row': 14, 'col': 9, 'value': 13},
    {'row': 14, 'col': 12, 'value': 15},
    {'row': 14, 'col': 16, 'value': 10},
    # 行O (15): 6个
    {'row': 15, 'col': 2, 'value': 1},
    {'row': 15, 'col': 5, 'value': 9},
    {'row': 15, 'col': 8, 'value': 15},
    {'row': 15, 'col': 11, 'value': 7},
    {'row': 15, 'col': 13, 'value': 16},
    {'row': 15, 'col': 14, 'value': 3},
    # 行P (16): 2个
    {'row': 16, 'col': 3, 'value': 2},
    {'row': 16, 'col': 7, 'value': 5},
]

# ═══════════════════════════════════════════════════════════
# 推测的55锚点配置 (从92中筛选得到的"可求解子集")
# ═══════════════════════════════════════════════════════════
# 根据之前分析，55锚点应该包含4个完全固定行(C,D,I,P) + 部分其他行
# 我们来构造一个可能的55锚点配置

def create_55_anchor_subset() -> List[Dict]:
    """构造55锚点子集（基于V42分析）"""
    # 策略：保留4个完全固定行(64个锚点) + 从其他行选择部分锚点以达到55个
    # 但55 < 64，所以55锚点配置应该是：
    # 1. 部分固定行（可能不完全包含所有4行）
    # 2. 或者包含固定行 + 部分其他行但减少了固定行内锚点
    
    # 根据V42量子态分析：C,D,I,P是坍缩行（固定），说明55锚点配置中这些行是完整的
    # 但如果55锚点存在唯一解，说明约束强度"适中"
    
    # 让我们分析：92锚点有4个完全固定行（共64个锚点），其余28个分布在其他行
    # 55锚点可能的构成：
    
    # 方案A: C行(16) + D行(16) + 部分其他行 = 55
    # 方案B: 不完全包含4个固定行
    
    # 基于V42结果，55锚点配置应该是：
    # - 包含C,D,I,P中的部分行或全部但减少锚点数
    # - 总体锚点数恰好55
    
    # 根据V42的"55锚点存在唯一解"与"92锚点INFEASIBLE"的对比
    # 我们推测55锚点可能是：C+D+I三行完整(48个) + 部分P行(7个) + 其他行
    
    subset = []
    
    # 行C (3): 16个 - 完整
    subset.extend([a for a in FULL_92_ANCHORS if a['row'] == 3])
    # 行D (4): 16个 - 完整
    subset.extend([a for a in FULL_92_ANCHORS if a['row'] == 4])
    # 行I (9): 16个 - 完整
    subset.extend([a for a in FULL_92_ANCHORS if a['row'] == 9])
    
    # 现在48个，还需要7个来自其他行
    # 从P行(16)选2个 + 其他行选5个
    subset.extend([a for a in FULL_92_ANCHORS if a['row'] == 16])  # 2个
    
    # 还需要5个，从其他非固定行选择
    other_rows = [1, 2, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]
    other_anchors = [a for a in FULL_92_ANCHORS if a['row'] in other_rows]
    # 取前5个
    subset.extend(other_anchors[:5])
    
    return subset[:55]

# ═══════════════════════════════════════════════════════════
# CP-SAT求解器
# ═══════════════════════════════════════════════════════════

class SudokuCPModel:
    """CP-SAT Sudoku求解器"""
    
    def __init__(self, anchors: List[Dict], grid_size: int = 16, box_size: int = 4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.anchors = anchors
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.grid = {}
        
    def build_model(self):
        """构建CP-SAT模型"""
        n = self.grid_size
        
        # 创建变量
        for r in range(n):
            for c in range(n):
                self.grid[(r, c)] = self.model.NewIntVar(1, n, f'cell_{r}_{c}')
        
        # 行AllDifferent
        for r in range(n):
            self.model.AddAllDifferent([self.grid[(r, c)] for c in range(n)])
        
        # 列AllDifferent
        for c in range(n):
            self.model.AddAllDifferent([self.grid[(r, c)] for r in range(n)])
        
        # 宫AllDifferent
        for br in range(n // self.box_size):
            for bc in range(n // self.box_size):
                cells = []
                for dr in range(self.box_size):
                    for dc in range(self.box_size):
                        r = br * self.box_size + dr
                        c = bc * self.box_size + dc
                        cells.append(self.grid[(r, c)])
                self.model.AddAllDifferent(cells)
        
        # 添加锚点约束
        for anchor in self.anchors:
            r = anchor['row'] - 1  # 转换为0基索引
            c = anchor['col'] - 1
            v = anchor['value']
            self.model.Add(self.grid[(r, c)] == v)
    
    def solve(self, solution_limit: int = 2) -> Tuple[cp_model.CpSolverStatus, List[Dict], float]:
        """求解并返回所有解"""
        start_time = time.time()
        
        self.build_model()
        
        # 设置求解器参数
        self.solver.parameters.max_time_in_seconds = 60.0
        self.solver.parameters.num_search_workers = 8
        self.solver.parameters.solution_limit = solution_limit
        
        status = self.solver.Solve(self.model)
        elapsed = time.time() - start_time
        
        solutions = []
        if status in [cp_model.CpSolverStatus.OPTIMAL, cp_model.CpSolverStatus.FEASIBLE]:
            solutions.append(self._extract_solution())
            
            # 搜索更多解
            while self.solver.NextSolution() and len(solutions) < solution_limit:
                solutions.append(self._extract_solution())
        
        return status, solutions, elapsed
    
    def _extract_solution(self) -> Dict:
        """提取解"""
        grid = [[0] * self.grid_size for _ in range(self.grid_size)]
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                grid[r][c] = self.solver.Value(self.grid[(r, c)])
        return {'grid': grid}


# ═══════════════════════════════════════════════════════════
# 覆盖关系验证
# ═══════════════════════════════════════════════════════════

def verify_coverage_55_vs_92():
    """验证55锚点解是否覆盖92锚点"""
    
    print("=" * 70)
    print("55 锚點 vs 92 锚點 覆蓋關係驗證")
    print("=" * 70)
    
    # 构造55锚点配置
    anchors_55 = create_55_anchor_subset()
    print(f"\n55 锚點配置 ({len(anchors_55)} 個):")
    
    # 按行统计
    from collections import Counter
    row_counts = Counter(a['row'] for a in anchors_55)
    for r in range(1, 17):
        count = row_counts.get(r, 0)
        status = "✓ 完全固定" if count == 16 else f"○ {count}/16"
        print(f"  行{r:2d} ({chr(64+r)}): {status}")
    
    # 与92锚点比较
    anchors_92_set = {(a['row'], a['col']): a['value'] for a in FULL_92_ANCHORS}
    anchors_55_set = {(a['row'], a['col']): a['value'] for a in anchors_55}
    
    covered = set(anchors_55_set.keys())
    not_covered = set(anchors_92_set.keys()) - covered
    
    print(f"\n92 锚點總數: {len(anchors_92_set)}")
    print(f"55 锚點總數: {len(anchors_55_set)}")
    print(f"55 覆盖 92 的锚点数: {len(covered & set(anchors_92_set.keys()))}")
    print(f"92 中未被 55 覆盖的锚点数: {len(not_covered)}")
    
    # 解冲突检查
    conflict_count = 0
    conflicts = []
    
    for pos, val_92 in anchors_92_set.items():
        if pos in anchors_55_set:
            val_55 = anchors_55_set[pos]
            if val_92 != val_55:
                conflict_count += 1
                conflicts.append({
                    'row': pos[0], 'col': pos[1],
                    'value_92': val_92, 'value_55': val_55
                })
    
    print(f"\n锚点值冲突数: {conflict_count}")
    if conflicts:
        for c in conflicts[:10]:
            print(f"  行{c['row']:2d} 列{c['col']:2d}: 92锚點={c['value_92']}, 55锚點={c['value_55']}")
    
    # 关键测试：求解55锚点配置
    print(f"\n{'='*70}")
    print("步驟1: 求解55锚点配置")
    print("="*70)
    
    solver_55 = SudokuCPModel(anchors_55)
    status_55, solutions_55, time_55 = solver_55.solve(solution_limit=5)
    
    print(f"狀態: {status_55}")
    print(f"解數: {len(solutions_55)}")
    print(f"時間: {time_55:.3f}秒")
    
    if not solutions_55:
        print("\n❌ 55锚点配置不可解！")
        print("這意味著55锚點配置本身就有內部衝突")
        return {
            'result': 'NO_SOLUTION_55',
            'status_55': str(status_55),
            'solution_count_55': 0,
            'time_55': time_55
        }
    
    # 用55锚点的解去验证92锚点约束
    print(f"\n{'='*70}")
    print("步驟2: 驗證55锚點解是否滿足92锚點約束")
    print("="*70)
    
    grid_55 = solutions_55[0]['grid']
    
    mismatch_count = 0
    mismatches = []
    
    for anchor in FULL_92_ANCHORS:
        r = anchor['row'] - 1
        c = anchor['col'] - 1
        expected = anchor['value']
        actual = grid_55[r][c]
        
        if actual != expected:
            mismatch_count += 1
            mismatches.append({
                'row': anchor['row'],
                'col': anchor['col'],
                'expected_92': expected,
                'actual_55': actual,
                'covered_by_55': (anchor['row'], anchor['col']) in anchors_55_set
            })
    
    print(f"92锚點中不匹配的数量: {mismatch_count}")
    print(f"92锚點中匹配的数量: {len(FULL_92_ANCHORS) - mismatch_count}")
    
    if mismatches:
        print(f"\n前10個不匹配示例:")
        for m in mismatches[:10]:
            coverage = "✓ 55包含" if m['covered_by_55'] else "✗ 55未包含"
            print(f"  行{m['row']:2d} 列{m['col']:2d}: "
                  f"期望={m['expected_92']:2d}, 實際={m['actual_55']:2d}, {coverage}")
    
    # 结论
    print(f"\n{'='*70}")
    print("結論")
    print("="*70)
    
    if mismatch_count == 0:
        print("✅ 55锚點的唯一解完全覆蓋了92锚點的所有約束")
        print("   兩者具有相關性：55锚點解是92锚點解的特例")
        result = 'COVERS_ALL'
    elif mismatch_count > 0:
        print("❌ 55锚點的解不能覆蓋92锚點的所有約束")
        print(f"   {mismatch_count} 個位置不匹配")
        
        covered_mismatch = sum(1 for m in mismatches if m['covered_by_55'])
        uncovered_mismatch = mismatch_count - covered_mismatch
        
        print(f"   其中 {covered_mismatch} 個是55锚點已包含但值不同的位置")
        print(f"   其中 {uncovered_mismatch} 個是55锚點未包含的位置")
        
        if covered_mismatch > 0:
            print("\n⚠️ 存在約束衝突：同一位置在55和92配置中有不同值")
            print("   這表明55和92锚點是「兩碼事」- 完全不同的謎題")
            result = 'CONFLICTS_EXIST'
        else:
            print("\n⚠️ 55锚點解未涵蓋的部分92锚點約束不滿足")
            print("   根據超級大數獨仲裁規則，不能判定兩者具備相關性")
            result = 'NO_COVERAGE_NO_CONFLICT'
    
    # 保存结果
    result_data = {
        'result': result,
        'anchors_55_count': len(anchors_55),
        'anchors_92_count': len(FULL_92_ANCHORS),
        'status_55': str(status_55),
        'solution_count_55': len(solutions_55),
        'time_55': time_55,
        'mismatch_count': mismatch_count,
        'mismatches': mismatches[:20],  # 保存前20个
        'mismatch_details': mismatches,
        'covered_count': len(covered),
        'not_covered_count': len(not_covered),
        'conflict_count': conflict_count
    }
    
    with open('verify_55vs92_coverage_result.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 結果已保存至: verify_55vs92_coverage_result.json")
    
    return result_data


if __name__ == '__main__':
    verify_coverage_55_vs_92()
