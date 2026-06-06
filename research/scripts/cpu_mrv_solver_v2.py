#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级256数独 — CPU优化版 V2 (直接实现)
适用于Intel Iris Xe等集成显卡环境
"""

import numpy as np
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

# ======================== 位运算约束 ========================

def check_constraint_bitwise(grid: np.ndarray, row: int, col: int, val: int) -> bool:
    """位运算约束检查"""
    mask = 1 << val
    
    # 行检查
    row_mask = 0
    for c in range(16):
        if grid[row, c] >= 0:
            row_mask |= (1 << grid[row, c])
    if row_mask & mask:
        return False
    
    # 列检查
    col_mask = 0
    for r in range(16):
        if grid[r, col] >= 0:
            col_mask |= (1 << grid[r, col])
    if col_mask & mask:
        return False
    
    # 宫格检查
    box_r, box_c = (row // 4) * 4, (col // 4) * 4
    box_mask = 0
    for r in range(box_r, box_r + 4):
        for c in range(box_c, box_c + 4):
            if grid[r, c] >= 0:
                box_mask |= (1 << grid[r, c])
    if box_mask & mask:
        return False
    
    return True

def get_candidates_bitwise(grid: np.ndarray, row: int, col: int) -> List[int]:
    """获取候选数字"""
    if grid[row, col] >= 0:
        return []
    
    mask = 0
    # 行
    for c in range(16):
        if grid[row, c] >= 0:
            mask |= (1 << grid[row, c])
    # 列
    for r in range(16):
        if grid[r, col] >= 0:
            mask |= (1 << grid[r, col])
    # 宫格
    box_r, box_c = (row // 4) * 4, (col // 4) * 4
    for r in range(box_r, box_r + 4):
        for c in range(box_c, box_c + 4):
            if grid[r, c] >= 0:
                mask |= (1 << grid[r, c])
    
    return [v for v in range(16) if not (mask & (1 << v))]

# ======================== MRV启发式求解 ========================

def solve_with_mrv(grid: np.ndarray, time_limit: float = 30.0) -> Tuple[bool, float]:
    """使用MRV启发式的回溯求解"""
    start_time = time.time()
    nodes = [0]
    
    def find_best_cell() -> Optional[Tuple[int, int]]:
        """找到候选数最少的空单元格"""
        min_candidates = float('inf')
        best_cell = None
        
        for r in range(16):
            for c in range(16):
                if grid[r, c] < 0:
                    cands = get_candidates_bitwise(grid, r, c)
                    if len(cands) < min_candidates:
                        min_candidates = len(cands)
                        best_cell = (r, c)
                        if min_candidates <= 1:
                            return best_cell
        
        return best_cell
    
    def backtrack() -> bool:
        nodes[0] += 1
        
        # 时间检查
        if time.time() - start_time > time_limit:
            return False
        
        # 找到空单元格
        cell = find_best_cell()
        if cell is None:
            return True  # 完成
        
        r, c = cell
        candidates = get_candidates_bitwise(grid, r, c)
        
        if not candidates:
            return False  # 死胡同
        
        for val in candidates:
            grid[r, c] = val
            if backtrack():
                return True
            grid[r, c] = -1
        
        return False
    
    success = backtrack()
    elapsed = time.time() - start_time
    
    return success, elapsed, nodes[0]

# ======================== 主程序 ========================

def load_puzzle(puzzle_dir: str) -> Tuple[Dict, Dict[int, List]]:
    """加载谜题"""
    import re
    
    puzzle_path = Path(puzzle_dir)
    
    # 加载排列
    permutations = {}
    for f in sorted(puzzle_path.glob("A*_permutations.json")):
        match = re.search(r'A(\d+)_permutations', f.name)
        if match:
            row_num = int(match.group(1))
            with open(f, 'r') as fp:
                data = json.load(fp)
                permutations[row_num] = data if isinstance(data, list) else []
    
    # 加载初盘
    initial = puzzle_path / "initial_puzzle.json"
    if initial.exists():
        with open(initial, 'r') as fp:
            puzzle = json.load(fp)
    else:
        puzzle = {'known_digits': []}
    
    return puzzle, permutations

def build_grid_from_puzzle(puzzle: Dict, permutations: Dict[int, List]) -> Optional[np.ndarray]:
    """从谜题和排列构建可能的网格"""
    # 从已知数字和排列约束构建
    grid = np.full((16, 16), -1, dtype=int)
    
    # 填入已知数字
    for cell in puzzle.get('known_digits', []):
        r, c, v = cell['row']-1, cell['col']-1, cell['value']-1
        grid[r, c] = v
    
    return grid

def main():
    print("="*60)
    print("🚀 超级256数独 — CPU优化版 V2")
    print("="*60)
    print("\n硬件: Intel Iris Xe Graphics")
    print("优化: MRV启发式 + 位运算约束")
    print("="*60)
    
    # 加载
    puzzle_dir = "D:/2026/WPF_Sudoku/Sudoku_256"
    puzzle, permutations = load_puzzle(puzzle_dir)
    
    print(f"\n谜题: {puzzle.get('id', 'unknown')}")
    print(f"已知数字: {len(puzzle.get('known_digits', []))} 个")
    
    # 构建网格
    grid = build_grid_from_puzzle(puzzle, permutations)
    
    # 验证初始约束
    conflicts = 0
    for cell in puzzle.get('known_digits', []):
        r, c, v = cell['row']-1, cell['col']-1, cell['value']-1
        if not check_constraint_bitwise(grid, r, c, v):
            conflicts += 1
    
    print(f"初始冲突: {conflicts}")
    
    if conflicts > 0:
        print("\n⚠️ 已知数字存在约束冲突，无法求解")
        return
    
    # 求解
    print("\n🔹 开始MRV求解...")
    success, elapsed, nodes = solve_with_mrv(grid, time_limit=30.0)
    
    print(f"\n{'='*60}")
    print(f"📊 结果")
    print(f"{'='*60}")
    print(f"状态: {'✅ 成功' if success else '❌ 超时'}")
    print(f"时间: {elapsed:.3f}s")
    print(f"节点: {nodes:,}")
    
    if success:
        # 检查解的完整性
        filled = np.sum(grid >= 0)
        print(f"填充单元格: {filled}/256")
        
        # 显示部分解
        print(f"\n📋 解预览 (前4行):")
        for r in range(4):
            row_str = " ".join(f"{grid[r,c]:2d}" for c in range(4))
            print(f"  {row_str} | ...")
    
    # 保存报告
    report = {
        'hardware': 'Intel Iris Xe Graphics',
        'cuda_available': False,
        'optimization': 'MRV + Bitwise',
        'success': success,
        'time': elapsed,
        'nodes': nodes,
        'grid_filled': int(np.sum(grid >= 0)) if success else 0
    }
    
    report_path = f"CPU_MRV_优化报告_{int(time.time())}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n报告: {report_path}")

if __name__ == "__main__":
    main()
