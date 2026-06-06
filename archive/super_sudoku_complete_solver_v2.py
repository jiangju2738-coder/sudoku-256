#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级大数独 16×16 完整求解器 v2
修复初始盘解析问题，正确识别92个已知数字
"""

import json
import numpy as np
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from copy import deepcopy
import time
import re

class SuperSudoku16x16Complete:
    """16×16 超级大数独完整求解器"""
    
    GRID_SIZE = 16
    BOX_SIZE = 4
    NUM_DIGITS = 16
    DIGITS = set(range(1, 17))
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.grid = np.zeros((16, 16), dtype=np.int8)
        self.initial_grid = np.zeros((16, 16), dtype=np.int8)
        
        self.row_constraints: Dict[int, List[Tuple[int, ...]]] = {}
        self.col_constraints: Dict[int, Set[int]] = {}
        
        self.possibilities: np.ndarray = None
        
        self.solutions: List[np.ndarray] = []
        self.solve_count = 0
        self.backtrack_count = 0
        
    def parse_initial_puzzle(self) -> int:
        """
        从 txt 文件解析初始盘 - 修复版
        直接硬编码已知数字以避免解析错误
        """
        # 直接从文件内容中解析 - 使用更健壮的正则
        puzzle_file = f"{self.base_dir}/超級大數獨_box_size4.txt"
        
        with open(puzzle_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有 [数字,...] 模式
        pattern = r'\[([^\]]+)\]'
        matches = re.findall(pattern, content)
        
        # 过滤掉不完整的行（少于16个数字的）
        valid_rows = []
        for match in matches:
            numbers = [int(n.strip()) for n in match.split(',') if n.strip()]
            if len(numbers) == 16:
                valid_rows.append(numbers)
        
        print(f"  找到 {len(valid_rows)} 个完整的16数字行")
        
        if len(valid_rows) < 16:
            print("  ⚠ 行数不足16，尝试备用方案...")
            # 备用：手动定义已知数字
            valid_rows = [
                [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8],
                [0,12,0,0, 3,0,9,0, 6,0,5,4, 2,0,1,0],
                [0,0,14,0, 0,2,0,8, 0,0,0,0, 0,0,0,0],
                [0,4,0,13, 7,0,1,0, 0,0,0,11, 0,12,0,0],
                [0,0,0,0, 13,0,0,0, 0,5,0,0, 4,0,0,0],
                [0,8,0,0, 15,0,4,3, 0,9,0,0, 0,13,0,12],
                [14,0,4,6, 0,0,12,0, 2,0,0,0, 0,3,0,0],
                [0,13,0,0, 0,5,0,9, 0,0,14,6, 0,0,16,0],
                [13,0,0,2, 0,11,0,0, 14,0,0,7, 0,15,0,3],
                [0,5,0,0, 0,0,0,0, 0,0,16,0, 8,0,7,0],
                [1,0,6,0, 5,0,0,2, 0,3,0,0, 9,0,0,0],
                [0,0,0,4, 0,16,14,0, 0,0,12,5, 0,0,0,1],
                [15,0,0,0, 12,0,0,0, 5,1,0,3, 0,6,0,7],
                [0,0,9,0, 0,6,0,0, 13,0,0,15, 0,0,3,0],
                [0,1,0,0, 9,0,0,15, 0,0,2,8, 0,5,0,0],
                [0,0,2,0, 0,0,5,0, 0,14,0,0, 1,0,10,15]
            ]
        
        # 填入网格
        row_idx = 0
        for row_data in valid_rows[:16]:
            for col_idx, val in enumerate(row_data):
                self.grid[row_idx, col_idx] = val
                self.initial_grid[row_idx, col_idx] = val
            row_idx += 1
        
        known_count = np.count_nonzero(self.initial_grid)
        print(f"✓ 解析初始盘完成: {known_count} 个已知数字")
        
        # 显示每行统计
        for i in range(16):
            known = sum(1 for v in self.initial_grid[i, :] if v != 0)
            values = [v for v in self.initial_grid[i, :] if v != 0]
            print(f"  第{i+1:2d}行: {known:2d}个 → {values}")
        
        return known_count
    
    def load_row_constraints(self):
        """加载16行符闔排列约束"""
        print("📂 加载行约束排列...")
        for row_idx in range(1, 17):
            json_file = f"A{row_idx}_permutations.json"
            filepath = f"{self.base_dir}/{json_file}"
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.row_constraints[row_idx] = [tuple(p) for p in data]
                print(f"  ✓ 第{row_idx}行: {len(self.row_constraints[row_idx]):,} 个排列")
            except Exception as e:
                print(f"  ✗ 第{row_idx}行: {e}")
                self.row_constraints[row_idx] = []
    
    def load_col_constraints(self):
        """加载列约束分析"""
        print("📂 加载列约束...")
        try:
            with open(f"{self.base_dir}/column_constraints.json", 'r', encoding='utf-8') as f:
                col_data = json.load(f)
                for col_idx in range(1, 17):
                    self.col_constraints[col_idx - 1] = set(
                        col_data['columns'][str(col_idx)]['possible_values']
                    )
            print(f"  ✓ 加载 {len(self.col_constraints)} 列约束")
        except Exception as e:
            print(f"  ✗ 加载列约束失败: {e}")
            for col_idx in range(16):
                self.col_constraints[col_idx] = set(range(1, 17))
    
    def initialize_possibilities(self):
        """初始化每个单元格的可能值"""
        self.possibilities = np.empty((16, 16), dtype=object)
        
        for row in range(16):
            for col in range(16):
                if self.grid[row, col] != 0:
                    self.possibilities[row, col] = {self.grid[row, col]}
                else:
                    possible = self.DIGITS.copy()
                    
                    # 排除同行已知
                    possible -= set(self.grid[row, :])
                    possible -= {0}
                    
                    # 排除同列已知
                    possible -= set(self.grid[:, col])
                    possible -= {0}
                    
                    # 排除同宫格已知
                    box_r, box_c = row // 4, col // 4
                    for r in range(box_r * 4, (box_r + 1) * 4):
                        for c in range(box_c * 4, (box_c + 1) * 4):
                            possible.discard(self.grid[r, c])
                    
                    # 列约束
                    if col in self.col_constraints:
                        possible &= self.col_constraints[col]
                    
                    self.possibilities[row, col] = possible
    
    def update_possibilities(self, row: int, col: int, value: int):
        """填入后更新候选值"""
        for c in range(16):
            if c != col:
                self.possibilities[row, c] -= {value}
        
        for r in range(16):
            if r != row:
                self.possibilities[r, col] -= {value}
        
        box_r, box_c = row // 4, col // 4
        for r in range(box_r * 4, (box_r + 1) * 4):
            for c in range(box_c * 4, (box_c + 1) * 4):
                if not (r == row and c == col):
                    self.possibilities[r, c] -= {value}
    
    def find_best_cell_mrv(self) -> Optional[Tuple[int, int, Set[int]]]:
        """MRV策略：候选值最少的单元格"""
        min_poss = float('inf')
        best_cell = None
        
        for row in range(16):
            for col in range(16):
                if self.grid[row, col] == 0:
                    poss = self.possibilities[row, col]
                    if len(poss) < min_poss:
                        min_poss = len(poss)
                        best_cell = (row, col, poss)
                        if min_poss == 1:
                            return best_cell
        return best_cell
    
    def check_complete_solution(self) -> bool:
        """检查完整解"""
        if np.any(self.grid == 0):
            return False
        
        # 行约束
        for row in range(16):
            row_tuple = tuple(self.grid[row, :])
            if row + 1 in self.row_constraints:
                if row_tuple not in self.row_constraints[row + 1]:
                    return False
        
        # 列约束
        for col in range(16):
            col_values = set(self.grid[:, col])
            if col in self.col_constraints:
                if not col_values.issubset(self.col_constraints[col]):
                    return False
        
        # 标准约束
        for row in range(16):
            if set(self.grid[row, :]) != self.DIGITS:
                return False
        for col in range(16):
            if set(self.grid[:, col]) != self.DIGITS:
                return False
        for box_r in range(4):
            for box_c in range(4):
                box_vals = set(self.grid[box_r*4:(box_r+1)*4, box_c*4:(box_c+1)*4].flatten())
                if box_vals != self.DIGITS:
                    return False
        
        return True
    
    def solve(self, max_solutions: int = 10, time_limit: float = 120.0) -> int:
        """主求解函数"""
        start_time = time.time()
        
        print("🚀 开始求解...")
        print(f"   时间限制: {time_limit}秒")
        print(f"   最大解数: {max_solutions}")
        print()
        
        def backtrack(count: int = 0) -> int:
            elapsed = time.time() - start_time
            if elapsed > time_limit:
                print(f"⏰ 超时 ({elapsed:.1f}秒)")
                return count
            
            if count % 50 == 0 and count > 0:
                print(f"  已找到 {count} 个解, {elapsed:.1f}s, 回溯 {self.backtrack_count:,} 次")
            
            if count >= max_solutions:
                return count
            
            cell = self.find_best_cell_mrv()
            if cell is None:
                if self.check_complete_solution():
                    self.solutions.append(deepcopy(self.grid))
                    count += 1
                    print(f"  ✓ 找到第 {count} 个完整解!")
                return count
            
            row, col, possibilities = cell
            
            if not possibilities:
                return count
            
            self.backtrack_count += 1
            
            for value in sorted(possibilities):
                # 列约束检查
                if col in self.col_constraints and value not in self.col_constraints[col]:
                    continue
                
                # 宫格检查
                box_r, box_c = row // 4, col // 4
                box_values = set()
                for r in range(box_r * 4, (box_r + 1) * 4):
                    for c in range(box_c * 4, (box_c + 1) * 4):
                        box_values.add(self.grid[r, c])
                if value in box_values:
                    continue
                
                # 填入
                old_value = self.grid[row, col]
                self.grid[row, col] = value
                
                # 保存旧候选值
                old_poss = {}
                for r in range(16):
                    for c in range(16):
                        old_poss[(r, c)] = self.possibilities[r, c].copy()
                
                # 更新候选值
                self.update_possibilities(row, col, value)
                
                # 递归
                count = backtrack(count)
                
                if count >= max_solutions:
                    self.grid[row, col] = old_value
                    for (r, c), poss in old_poss.items():
                        self.possibilities[r, c] = poss
                    return count
                
                # 回溯
                self.grid[row, col] = old_value
                for (r, c), poss in old_poss.items():
                    self.possibilities[r, c] = poss
            
            return count
        
        # 初始化已知数字的候选值
        for row in range(16):
            for col in range(16):
                if self.initial_grid[row, col] != 0:
                    self.possibilities[row, col] = {self.initial_grid[row, col]}
        
        # 开始搜索
        self.solve_count = backtrack()
        
        elapsed = time.time() - start_time
        print(f"\n📊 求解完成:")
        print(f"   找到解数: {self.solve_count}")
        print(f"   搜索时间: {elapsed:.2f}秒")
        print(f"   回溯次数: {self.backtrack_count:,}")
        
        return self.solve_count
    
    def generate_html_report(self, output_path: str):
        """生成HTML报告"""
        if not self.solutions:
            print("⚠ 未找到解")
            return
        
        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>超级大数独 16×16 完整求解结果</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: white; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: rgba(255,255,255,0.95); border-radius: 12px; padding: 20px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; }}
        .solution {{ background: rgba(255,255,255,0.95); border-radius: 12px; padding: 25px; margin: 20px 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(16, 1fr); gap: 2px; background: #333; padding: 3px; border-radius: 8px; margin: 20px auto; max-width: 640px; }}
        .cell {{ width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; border-radius: 3px; }}
        .cell.known {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; }}
        .cell.solved {{ background: #f8f9fa; color: #333; }}
        .grid .cell:nth-child(4n) {{ border-right: 3px solid #333; }}
        .grid .cell:nth-child(16n+5), .grid .cell:nth-child(16n+9), .grid .cell:nth-child(16n+13) {{ border-right: 3px solid #333; }}
        .grid .cell:nth-child(n+65):nth-child(-n+80), .grid .cell:nth-child(n+129):nth-child(-n+144) {{ border-bottom: 3px solid #333; }}
        .constraint-info {{ background: #f8f9fa; border-radius: 8px; padding: 15px; margin: 15px 0; }}
    </style>
</head>
<body>
<div class="container">
    <h1>🎲 超级大数独 16×16 完整求解结果</h1>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{len(self.solutions)}</div>
            <div class="stat-label">找到的解数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{np.count_nonzero(self.initial_grid)}</div>
            <div class="stat-label">初始已知数字</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{sum(len(v) for v in self.row_constraints.values()):,}</div>
            <div class="stat-label">行约束排列总数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{self.backtrack_count:,}</div>
            <div class="stat-label">回溯次数</div>
        </div>
    </div>
    
    <div class="constraint-info">
        <h3>约束统计</h3>
        <p>• 16行符闔排列约束: {sum(len(v) for v in self.row_constraints.values()):,} 个排列</p>
        <p>• 5列有限约束: 第3列(缺3), 第8列(缺5), 第12列(缺14), 第14列(缺16), 第16列(缺1,7,12)</p>
        <p>• 11列无约束: 可填1-16任意数字</p>
        <p>• 16个4×4宫格约束</p>
        <p>• 初始盘: {np.count_nonzero(self.initial_grid)} 个已知数字</p>
    </div>
"""
        
        for i, sol in enumerate(self.solutions[:3]):
            html += f"""
    <div class="solution">
        <h3>解 #{i+1}</h3>
        <div class="grid">
"""
            for row in range(16):
                for col in range(16):
                    val = int(sol[row, col])
                    cell_class = "cell known" if self.initial_grid[row, col] != 0 else "cell solved"
                    html += f'<div class="{cell_class}">{val}</div>'
            html += """
        </div>
    </div>
"""
        
        html += """
</div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✓ HTML报告已保存: {output_path}")
    
    def save_results(self, output_path: str):
        """保存结果JSON"""
        results = {
            'solution_count': len(self.solutions),
            'initial_known': int(np.count_nonzero(self.initial_grid)),
            'backtrack_count': self.backtrack_count,
            'row_constraint_total': sum(len(v) for v in self.row_constraints.values()),
            'col_constraints': {str(k): list(v) for k, v in self.col_constraints.items()},
            'solutions': [sol.tolist() for sol in self.solutions]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✓ JSON结果已保存: {output_path}")


def main():
    print("=" * 70)
    print("🎯 超级大数独 16×16 完整求解器 v2")
    print("📐 整合行约束 + 列约束 + 宫格约束")
    print("=" * 70)
    print()
    
    base_dir = "D:/2026/WPF_Sudoku/Sudoku_256"
    
    solver = SuperSudoku16x16Complete(base_dir)
    
    # 步骤1: 解析初始盘
    print("📋 步骤1: 解析初始盘")
    print("-" * 70)
    known_count = solver.parse_initial_puzzle()
    print("-" * 70)
    print()
    
    # 步骤2: 加载约束
    print("📊 步骤2: 加载约束数据")
    print("-" * 70)
    solver.load_row_constraints()
    solver.load_col_constraints()
    print("-" * 70)
    print()
    
    # 步骤3: 初始化候选值
    print("🔍 步骤3: 初始化候选值")
    print("-" * 70)
    solver.initialize_possibilities()
    
    empty_count = np.count_nonzero(solver.grid == 0)
    avg_poss = np.mean([len(solver.possibilities[r,c]) for r in range(16) for c in range(16) if solver.grid[r,c]==0])
    print(f"  待填单元格: {empty_count}")
    print(f"  平均候选值: {avg_poss:.1f}")
    print("-" * 70)
    print()
    
    # 步骤4: 求解
    print("🚀 步骤4: 执行求解")
    print("-" * 70)
    solver.solve(max_solutions=10, time_limit=180.0)
    print("-" * 70)
    print()
    
    # 步骤5: 输出
    if solver.solutions:
        print("✅ 找到有效解!")
        
        first_sol = solver.solutions[0]
        print("\n🔍 验证第一个解:")
        
        row_ok = 0
        for row in range(16):
            row_tuple = tuple(first_sol[row, :])
            if row + 1 in solver.row_constraints:
                if row_tuple in solver.row_constraints[row + 1]:
                    row_ok += 1
        print(f"  行约束满足: {row_ok}/16")
        
        col_ok = 0
        for col in range(16):
            col_values = set(first_sol[:, col])
            if col in solver.col_constraints:
                if col_values.issubset(solver.col_constraints[col]):
                    col_ok += 1
        print(f"  列约束满足: {col_ok}/16")
        
        std_ok = True
        for row in range(16):
            if set(first_sol[row, :]) != solver.DIGITS:
                std_ok = False
                break
        for col in range(16):
            if set(first_sol[:, col]) != solver.DIGITS:
                std_ok = False
                break
        print(f"  标准数独约束: {'✅' if std_ok else '❌'}")
        
        solver.save_results(f"{base_dir}/完整求解结果_v2.json")
        solver.generate_html_report(f"{base_dir}/完整求解结果_v2.html")
    else:
        print("⚠ 未找到解")
    
    print()
    print("=" * 70)
    print("✅ 求解流程完成!")
    print("=" * 70)


if __name__ == "__main__":
    main()
