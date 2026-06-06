#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V75 演进算盘加E版 - 完整解盘推演
新超级数独谜题：初始盘92锚点 + E行13锚点 = 105锚点

融闔系统三大架构：
1. 综闔博弈框架 - 博弈参与者分析、约束强度
2. 五维思维框架 - 点线面体球时空六维分析
3. 链式环式原理 - C-E链式约束传播

输入：105锚点新超级数独谜题
输出：完整解盘 + 三大架构分析报告
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
from typing import Dict, List, Tuple
from datetime import datetime

# ============================================================
# 第一部分：三大架构框架定义
# ============================================================

class ZhongheGameFramework:
    """综闔博弈框架 - 分析博弈参与者与约束强度"""
    
    def __init__(self, puzzle: Dict[str, List[int]]):
        self.puzzle = puzzle
        self.players = []  # 博弈参与者
        
    def analyze_constraints(self) -> Dict:
        """分析每行约束强度"""
        row_analysis = {}
        for row in 'ABCDEFGHIJKLMNOP':
            known = sum(1 for v in self.puzzle[row] if v != 0)
            unknown = 16 - known
            strength = known / 16.0
            row_analysis[row] = {
                'known': known,
                'unknown': unknown,
                'constraint_strength': round(strength, 4)
            }
        return row_analysis
    
    def analyze_105_anchors(self) -> Dict:
        """分析105锚点分布"""
        distribution = {}
        for row in 'ABCDEFGHIJKLMNOP':
            known = sum(1 for v in self.puzzle[row] if v != 0)
            if known not in distribution:
                distribution[known] = []
            distribution[known].append(row)
        return distribution
    
    def full_analysis(self) -> Dict:
        return {
            'row_constraints': self.analyze_constraints(),
            'anchor_distribution': self.analyze_105_anchors(),
            'summary': {
                'total_anchors': sum(v['known'] for v in self.analyze_constraints().values()),
                'avg_constraint': sum(v['constraint_strength'] for v in self.analyze_constraints().values()) / 16
            }
        }


class FiveDimensionalFramework:
    """五维思维框架 - 点线面体球时空六维分析"""
    
    def __init__(self, puzzle: Dict[str, List[int]]):
        self.puzzle = puzzle
        
    def point_dimension(self) -> Dict:
        """点维度：256个单元格的填充状态"""
        filled = 0
        empty = 0
        for row in 'ABCDEFGHIJKLMNOP':
            for val in self.puzzle[row]:
                if val == 0:
                    empty += 1
                else:
                    filled += 1
        return {
            'total_cells': 256,
            'filled_cells': filled,
            'empty_cells': empty,
            'fill_rate': round(filled / 256 * 100, 2)
        }
    
    def line_dimension(self) -> Dict:
        """线维度：16行的锁定状态"""
        row_status = {}
        for i, row in enumerate('ABCDEFGHIJKLMNOP'):
            known = sum(1 for v in self.puzzle[row] if v != 0)
            row_status[row] = {
                'locked': known == 16,
                'known': known,
                'lock_rate': round(known / 16 * 100, 2)
            }
        return {'rows': row_status}
    
    def plane_dimension(self) -> Dict:
        """面维度：16个4×4宫的填充状态"""
        palace_status = {}
        row_list = 'ABCDEFGHIJKLMNOP'
        for p_row in range(4):
            for p_col in range(4):
                palace_id = f"P{p_row*4+p_col+1}"
                cells = []
                for r in range(4):
                    for c in range(4):
                        row_name = row_list[p_row*4 + r]
                        col_idx = p_col*4 + c
                        cells.append(self.puzzle[row_name][col_idx])
                filled = sum(1 for v in cells if v != 0)
                palace_status[palace_id] = {
                    'filled': filled,
                    'empty': 16 - filled,
                    'fill_rate': round(filled / 16 * 100, 2)
                }
        return {'palaces': palace_status}
    
    def body_dimension(self) -> Dict:
        """体维度：列的约束传播强度"""
        col_status = {}
        for col in range(16):
            col_vals = [self.puzzle[row][col] for row in 'ABCDEFGHIJKLMNOP']
            known = sum(1 for v in col_vals if v != 0)
            col_letter = chr(ord('A') + col)
            col_status[col_letter] = {
                'known': known,
                'empty': 16 - known,
                'constraint_strength': round(known / 16 * 100, 2)
            }
        return {'columns': col_status}
    
    def sphere_dimension(self) -> Dict:
        """球维度：全空间约束网络"""
        return {
            'description': '105锚点构成的约束网络',
            'anchor_density': round(105 / 256 * 100, 2)
        }
    
    def spacetime_dimension(self) -> Dict:
        """时空维度：演进过程"""
        return {
            'initial_state': '92锚点',
            'evolution': '92 + E行13 = 105锚点',
            'convergence_rate': '105/256 = 41.02%'
        }
    
    def full_analysis(self) -> Dict:
        return {
            'point': self.point_dimension(),
            'line': self.line_dimension(),
            'plane': self.plane_dimension(),
            'body': self.body_dimension(),
            'sphere': self.sphere_dimension(),
            'spacetime': self.spacetime_dimension()
        }


class ChainRingPrinciple:
    """链式环式原理 - 链式约束传播分析"""
    
    def __init__(self, puzzle: Dict[str, List[int]], e_row: List[int]):
        self.puzzle = puzzle
        self.e_row = e_row
        
    def analyze_ce_constraint(self) -> Dict:
        """分析C-E链式约束"""
        c_row = self.puzzle['C']
        e_row = self.e_row
        
        c_known = sum(1 for v in c_row if v != 0)
        e_known = sum(1 for v in e_row if v != 0)
        
        # C-E通过列约束关联
        # C行已知约束传递到E行的效果
        # C行已知列：C-C3=14, C-C6=2, C-C8=8
        c_columns = [i for i, v in enumerate(c_row) if v != 0]
        e_columns = [i for i, v in enumerate(e_row) if v != 0]
        
        return {
            'c_row_known': c_known,
            'e_row_known': e_known,
            'c_columns_constrained': c_columns,
            'e_row_complete': e_known == 16,
            'chain_strength': round(e_known / 16 * 100, 2),
            'analysis': f'C行有{c_known}个锚点，E行完整锁定(16锚点)，C-E通过列约束完全关联'
        }
    
    def full_analysis(self) -> Dict:
        return {
            'ce_constraint': self.analyze_ce_constraint(),
            'description': 'C行和E行通过列约束形成链式关联，E行完整排列锁定进一步压缩解空间'
        }


# ============================================================
# 第二部分：CP-SAT求解器
# ============================================================

def solve_evolution_plus_e() -> Dict:
    """求解演进加E盘（105锚点）"""
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return {'status': 'IMPORT_ERROR', 'error': 'ortools not installed'}
    
    # 105锚点谜题
    puzzle = {
        'A': [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8],
        'B': [0,12,0,0, 3,0,9,0, 6,0,5,4, 2,0,1,0],
        'C': [0,0,14,0, 0,2,0,8, 0,0,0,0, 0,0,0,0],
        'D': [0,4,0,13, 7,0,1,0, 0,0,0,11, 0,12,0,0],
        'E': [11,2,1,9, 13,7,6,16, 3,5,15,12, 4,10,8,14],  # E行完整锁定
        'F': [0,8,0,0, 15,0,4,3, 0,9,0,0, 0,13,0,12],
        'G': [14,0,4,6, 0,0,12,0, 2,0,0,0, 0,3,0,0],
        'H': [0,13,0,0, 0,5,0,9, 0,0,14,6, 0,0,16,0],
        'I': [13,0,0,2, 0,11,0,0, 14,0,0,7, 0,15,0,3],
        'J': [0,5,0,0, 0,0,0,0, 0,0,16,0, 8,0,7,0],
        'K': [1,0,6,0, 5,0,0,2, 0,3,0,0, 9,0,0,0],
        'L': [0,0,0,4, 0,16,14,0, 0,0,12,5, 0,0,0,1],
        'M': [15,0,0,0, 12,0,0,0, 5,1,0,3, 0,6,0,7],
        'N': [0,0,9,0, 0,6,0,0, 13,0,0,15, 0,0,3,0],
        'O': [0,1,0,0, 9,0,0,15, 0,0,2,8, 0,5,0,0],
        'P': [0,0,2,0, 0,0,5,0, 0,14,0,0, 1,0,10,15]
    }
    
    # 构建CP-SAT模型
    model = cp_model.CpModel()
    
    # 变量：每个单元格0-16
    vars = {}
    for row in 'ABCDEFGHIJKLMNOP':
        for col in range(16):
            vars[(row, col)] = model.NewIntVar(1, 16, f'{row}{col}')
    
    # 约束1：锚点约束（105个）
    for row in 'ABCDEFGHIJKLMNOP':
        for col in range(16):
            if puzzle[row][col] != 0:
                model.Add(vars[(row, col)] == puzzle[row][col])
    
    # 约束2：行约束（AllDifferent）
    for row in 'ABCDEFGHIJKLMNOP':
        model.AddAllDifferent([vars[(row, col)] for col in range(16)])
    
    # 约束3：列约束（AllDifferent）
    for col in range(16):
        model.AddAllDifferent([vars[(row, col)] for row in 'ABCDEFGHIJKLMNOP'])
    
    # 约束4：宫约束（4x4宫）
    for p_row in range(4):
        for p_col in range(4):
            palace_vars = []
            for r in range(4):
                for c in range(4):
                    palace_vars.append(vars[(chr(ord('A') + p_row*4 + r), p_col*4 + c)])
            model.AddAllDifferent(palace_vars)
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 8
    solver.parameters.max_time_in_seconds = 120
    
    print("求解中...")
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        solution = []
        for row in 'ABCDEFGHIJKLMNOP':
            row_vals = [solver.Value(vars[(row, col)]) for col in range(16)]
            solution.append(row_vals)
        
        return {
            'status': 'SOLVED',
            'solution': solution,
            'time': solver.WallTime()
        }
    else:
        return {'status': 'NO_SOLUTION', 'error': '未找到解'}


# ============================================================
# 第三部分：主程序
# ============================================================

def main():
    print("="*70)
    print("V75 演进算盘加E版 - 完整解盘推演")
    print("新超级数独谜题：92锚点 + E行13锚点 = 105锚点")
    print("="*70)
    print()
    
    # ====== 1. 定义105锚点谜题 ======
    print("【步骤1】定义105锚点新超级数独谜题")
    puzzle = {
        'A': [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8],
        'B': [0,12,0,0, 3,0,9,0, 6,0,5,4, 2,0,1,0],
        'C': [0,0,14,0, 0,2,0,8, 0,0,0,0, 0,0,0,0],
        'D': [0,4,0,13, 7,0,1,0, 0,0,0,11, 0,12,0,0],
        'E': [11,2,1,9, 13,7,6,16, 3,5,15,12, 4,10,8,14],  # E行完整锁定
        'F': [0,8,0,0, 15,0,4,3, 0,9,0,0, 0,13,0,12],
        'G': [14,0,4,6, 0,0,12,0, 2,0,0,0, 0,3,0,0],
        'H': [0,13,0,0, 0,5,0,9, 0,0,14,6, 0,0,16,0],
        'I': [13,0,0,2, 0,11,0,0, 14,0,0,7, 0,15,0,3],
        'J': [0,5,0,0, 0,0,0,0, 0,0,16,0, 8,0,7,0],
        'K': [1,0,6,0, 5,0,0,2, 0,3,0,0, 9,0,0,0],
        'L': [0,0,0,4, 0,16,14,0, 0,0,12,5, 0,0,0,1],
        'M': [15,0,0,0, 12,0,0,0, 5,1,0,3, 0,6,0,7],
        'N': [0,0,9,0, 0,6,0,0, 13,0,0,15, 0,0,3,0],
        'O': [0,1,0,0, 9,0,0,15, 0,0,2,8, 0,5,0,0],
        'P': [0,0,2,0, 0,0,5,0, 0,14,0,0, 1,0,10,15]
    }
    
    total_anchors = sum(sum(1 for v in row if v != 0) for row in puzzle.values())
    print(f"  总锚点数: {total_anchors} (92初始 + 13 E行 = 105)")
    print(f"  E行终局排列: [11,2,1,9, 13,7,6,16, 3,5,15,12, 4,10,8,14]")
    print()
    
    # ====== 2. 综闔博弈框架分析 ======
    print("【步骤2】综闔博弈框架分析")
    zhonghe = ZhongheGameFramework(puzzle)
    zhonghe_analysis = zhonghe.full_analysis()
    
    print(f"  总锚点数: {zhonghe_analysis['summary']['total_anchors']}")
    print(f"  平均约束强度: {zhonghe_analysis['summary']['avg_constraint']:.2%}")
    print("  锚点分布:")
    for anchor_count, rows in sorted(zhonghe_analysis['anchor_distribution'].items(), reverse=True):
        print(f"    {anchor_count}锚点: {', '.join(rows)}")
    print()
    
    # ====== 3. 五维思维框架分析 ======
    print("【步骤3】五维思维框架分析")
    five_dim = FiveDimensionalFramework(puzzle)
    five_dim_analysis = five_dim.full_analysis()
    
    print(f"  点维度: {five_dim_analysis['point']['empty_cells']}个空单元格 ({five_dim_analysis['point']['fill_rate']}%填充)")
    print(f"  线维度: 16行中有{sum(1 for r in five_dim_analysis['line']['rows'].values() if r['locked'])}行已锁定")
    print(f"  体维度: E列约束强度=100%")
    print(f"  时空维度: 演进率 {five_dim_analysis['spacetime']['convergence_rate']}")
    print()
    
    # ====== 4. 链式环式原理分析 ======
    print("【步骤4】链式环式原理分析")
    e_row_final = [11,2,1,9, 13,7,6,16, 3,5,15,12, 4,10,8,14]
    chain_ring = ChainRingPrinciple(puzzle, e_row_final)
    chain_ring_analysis = chain_ring.full_analysis()
    
    print(f"  C行锚点: {chain_ring_analysis['ce_constraint']['c_row_known']}")
    print(f"  E行锚点: {chain_ring_analysis['ce_constraint']['e_row_known']} (完整锁定)")
    print(f"  C-E链式约束强度: {chain_ring_analysis['ce_constraint']['chain_strength']}%")
    print()
    
    # ====== 5. CP-SAT求解 ======
    print("【步骤5】CP-SAT求解演进加E盘")
    solve_result = solve_evolution_plus_e()
    
    if solve_result['status'] == 'SOLVED':
        solution = solve_result['solution']
        print(f"  求解成功! 耗时: {solve_result['time']:.3f}秒")
        print()
        
        # 打印解
        print("  演进加E盘完整解:")
        print("  " + "-"*60)
        for i, row in enumerate('ABCDEFGHIJKLMNOP'):
            vals = solution[i]
            print(f"  行{row}: " + " ".join(f"{v:3d}" for v in vals))
        print("  " + "-"*60)
        print()
        
        # 验证解
        print("【步骤6】验证解的正确性")
        
        # 验证C行和E行
        c191620 = [7,10,14,15, 4,2,16,8, 12,13,3,1, 11,9,6,5]
        e_final = e_row_final
        
        c_match = solution[2] == c191620
        e_match = solution[4] == e_final
        
        print(f"  C行匹配C191620: {'✓' if c_match else '✗'}")
        print(f"  E行匹配终局: {'✓' if e_match else '✗'}")
        
        # 与txt终局解盘对比
        txt_final = {
            'A': [2,6,3,1,11,12,13,5,10,7,9,14,15,16,4,8],
            'B': [16,12,11,8,3,10,9,14,6,15,5,4,2,7,1,13],
            'C': [7,10,14,15,4,2,16,8,12,13,3,1,11,9,6,5],
            'D': [9,4,5,13,7,15,1,6,16,2,8,11,3,12,14,10],
            'E': [11,2,1,9,13,7,6,16,3,5,15,12,4,10,8,14],
            'F': [5,8,7,10,15,14,4,3,1,9,11,16,6,13,2,12],
            'G': [14,16,4,6,8,1,12,11,2,10,7,13,5,3,15,9],
            'H': [12,13,15,3,2,5,10,9,4,8,14,6,7,1,16,11],
            'I': [13,9,16,2,6,11,8,12,14,4,1,7,10,15,5,3],
            'J': [10,5,12,14,1,9,3,13,15,11,16,2,8,4,7,6],
            'K': [1,11,6,7,5,4,15,2,8,3,13,10,9,14,12,16],
            'L': [3,15,8,4,10,16,14,7,9,6,12,5,13,2,11,1],
            'M': [15,14,13,11,12,8,2,10,5,1,4,3,16,6,9,7],
            'N': [4,7,9,5,14,6,11,1,13,16,10,15,12,8,3,2],
            'O': [6,1,10,16,9,3,7,15,11,12,2,8,14,5,13,4],
            'P': [8,3,2,12,16,13,5,4,7,14,6,9,1,11,10,15]
        }
        
        all_match = True
        for i, row in enumerate('ABCDEFGHIJKLMNOP'):
            if solution[i] != txt_final[row]:
                all_match = False
                break
        
        print(f"  与txt终局解盘对比: {'✓ 完全一致' if all_match else '✗ 存在差异'}")
        print()
        
        # 输出结果
        result = {
            'puzzle': puzzle,
            'total_anchors': total_anchors,
            'zhonghe_analysis': zhonghe_analysis,
            'five_dim_analysis': five_dim_analysis,
            'chain_ring_analysis': chain_ring_analysis,
            'solution': solution,
            'verification': {
                'c_match_c191620': c_match,
                'e_match_final': e_match,
                'matches_txt_final': all_match
            },
            'timestamp': datetime.now().isoformat()
        }
        
        with open('V75_evolution_plus_E_solution_105.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("结果已保存: V75_evolution_plus_E_solution_105.json")
        
    else:
        print(f"  求解失败: {solve_result.get('error', '未知错误')}")

if __name__ == '__main__':
    main()