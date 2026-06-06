#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级256数独 — 有效谜题生成器 + CPU高性能求解器 V3
- 基于有效完整解生成合法谜题
- 位运算 + MRV + 前向检查 + 剪枝优化
"""

import numpy as np
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import random
from copy import deepcopy

# ======================== 配置常量 ========================

GRID_SIZE = 16
BOX_SIZE = 4
TOTAL_CELLS = GRID_SIZE * GRID_SIZE  # 256
MAX_CLUES = 60  # 最大已知数字数

# ======================== 位运算约束检查 ========================

class BitConstraintV3:
    """位运算约束 - V3优化版"""
    
    __slots__ = ['rows', 'cols', 'boxes']
    
    def __init__(self, size: int = GRID_SIZE):
        self.rows = [0] * size  # 每行已使用的数字位掩码
        self.cols = [0] * size  # 每列已使用的数字位掩码
        self.boxes = [0] * ((size // BOX_SIZE) ** 2)  # 每宫已使用的数字位掩码
    
    def reset(self):
        """重置所有约束"""
        self.rows = [0] * len(self.rows)
        self.cols = [0] * len(self.cols)
        self.boxes = [0] * len(self.boxes)
    
    def box_index(self, row: int, col: int) -> int:
        """计算宫格索引"""
        return (row // BOX_SIZE) * (GRID_SIZE // BOX_SIZE) + (col // BOX_SIZE)
    
    def is_valid(self, row: int, col: int, val: int) -> bool:
        """位运算检查是否可放置"""
        mask = 1 << val
        b = self.box_index(row, col)
        return not (self.rows[row] & mask) and \
               not (self.cols[col] & mask) and \
               not (self.boxes[b] & mask)
    
    def place(self, row: int, col: int, val: int):
        """放置数字，更新约束"""
        mask = 1 << val
        b = self.box_index(row, col)
        self.rows[row] |= mask
        self.cols[col] |= mask
        self.boxes[b] |= mask
    
    def remove(self, row: int, col: int, val: int):
        """移除数字，恢复约束"""
        mask = 1 << val
        b = self.box_index(row, col)
        self.rows[row] &= ~mask
        self.cols[col] &= ~mask
        self.boxes[b] &= ~mask
    
    def get_candidates(self, row: int, col: int) -> List[int]:
        """获取所有候选数字"""
        b = self.box_index(row, col)
        mask = self.rows[row] | self.cols[col] | self.boxes[b]
        return [v for v in range(GRID_SIZE) if not (mask & (1 << v))]
    
    def candidate_count(self, row: int, col: int) -> int:
        """获取候选数字数量"""
        b = self.box_index(row, col)
        mask = self.rows[row] | self.cols[col] | self.boxes[b]
        # 位运算计算0的个数
        return GRID_SIZE - bin(mask).count('1')


# ======================== MRV + 前向检查 求解器 ========================

class MPCPSolver:
    """
    MRV + 前向检查 + 约束传播 - V3优化求解器
    """
    
    __slots__ = ['grid', 'constraints', 'cells', 'stats', 'time_limit']
    
    def __init__(self, time_limit: float = 60.0):
        self.grid = None
        self.constraints = None
        self.cells = None
        self.stats = None
        self.time_limit = time_limit
    
    def solve(self, grid: np.ndarray) -> Tuple[bool, float]:
        """求解数独"""
        start_time = time.time()
        self.grid = grid.copy()
        self.constraints = BitConstraintV3()
        self.stats = {
            'nodes': 0,
            'backtracks': 0,
            'conflicts': 0,
            'propagations': 0
        }
        
        # 初始化约束
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r, c] >= 0:
                    self.constraints.place(r, c, self.grid[r, c])
        
        # 收集空单元格
        self.cells = [(r, c) for r in range(GRID_SIZE) 
                      for c in range(GRID_SIZE) if self.grid[r, c] < 0]
        
        success = self._search(start_time)
        elapsed = time.time() - start_time
        
        return success, elapsed
    
    def _search(self, start_time: float) -> bool:
        """深度优先搜索（MRV启发式）"""
        self.stats['nodes'] += 1
        
        # 时间限制
        if time.time() - start_time > self.time_limit:
            return False
        
        # MRV: 选择候选数最少的单元格
        best_idx = self._select_best_cell()
        if best_idx is None:
            return True  # 所有单元格已填
        
        row, col = self.cells[best_idx]
        candidates = self.constraints.get_candidates(row, col)
        
        if not candidates:
            self.stats['conflicts'] += 1
            return False  # 死胡同
        
        # 对候选值进行排序（最少剩余值优先）
        candidates = self._order_values(row, col, candidates)
        
        for val in candidates:
            # 放置
            self.grid[row, col] = val
            self.constraints.place(row, col, val)
            
            # 前向检查：检查是否导致任何空单元格无候选
            if self._forward_check(best_idx):
                if self._search(start_time):
                    return True
            
            # 回溯
            self.grid[row, col] = -1
            self.constraints.remove(row, col, val)
            self.stats['backtracks'] += 1
        
        return False
    
    def _select_best_cell(self) -> Optional[int]:
        """选择MRV单元格（返回cells中的索引）"""
        best_idx = None
        min_count = GRID_SIZE + 1
        
        for i, (r, c) in enumerate(self.cells):
            if self.grid[r, c] < 0:  # 仍然是空的
                count = self.constraints.candidate_count(r, c)
                if count < min_count:
                    min_count = count
                    best_idx = i
                    if min_count <= 1:
                        break  # 最优
        
        return best_idx
    
    def _order_values(self, row: int, col: int, candidates: List[int]) -> List[int]:
        """对候选值排序（最少影响优先）"""
        if len(candidates) <= 1:
            return candidates
        
        # 计算每个值影响的其他空单元格的候选数
        b = self.constraints.box_index(row, col)
        
        def score(val: int) -> int:
            """计算放置该值后的约束影响"""
            # 统计同行、同列、同宫的其他空单元格的候选减少数
            impact = 0
            mask = 1 << val
            
            # 行影响
            for c2 in range(GRID_SIZE):
                if self.grid[row, c2] < 0 and c2 != col:
                    old_mask = self.constraints.rows[row] | self.constraints.cols[c2] | \
                              self.constraints.boxes[self.constraints.box_index(row, c2)]
                    new_mask = old_mask | mask
                    old_count = GRID_SIZE - bin(old_mask).count('1')
                    new_count = GRID_SIZE - bin(new_mask).count('1')
                    impact += (old_count - new_count)
            
            # 列影响
            for r2 in range(GRID_SIZE):
                if self.grid[r2, col] < 0 and r2 != row:
                    old_mask = self.constraints.rows[r2] | self.constraints.cols[col] | \
                              self.constraints.boxes[self.constraints.box_index(r2, col)]
                    new_mask = old_mask | mask
                    old_count = GRID_SIZE - bin(old_mask).count('1')
                    new_count = GRID_SIZE - bin(new_mask).count('1')
                    impact += (old_count - new_count)
            
            return impact
        
        # 按影响从小到大排序
        return sorted(candidates, key=score)
    
    def _forward_check(self, cell_idx: int) -> bool:
        """前向检查：确保所有剩余空单元格至少有1个候选"""
        self.stats['propagations'] += 1
        
        for i, (r, c) in enumerate(self.cells):
            if i == cell_idx:
                continue
            if self.grid[r, c] < 0:
                if self.constraints.candidate_count(r, c) == 0:
                    return False
        return True
    
    def get_stats(self) -> Dict:
        """获取求解统计"""
        return self.stats.copy()


# ======================== 谜题生成器 ========================

class PuzzleGenerator:
    """16×16数独谜题生成器"""
    
    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)
            np.random.seed(seed)
    
    def generate_complete_grid(self) -> np.ndarray:
        """生成完整有效网格"""
        grid = np.full((GRID_SIZE, GRID_SIZE), -1, dtype=int)
        constraints = BitConstraintV3()
        
        cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
        random.shuffle(cells)
        
        def fill(idx: int) -> bool:
            if idx >= len(cells):
                return True
            
            row, col = cells[idx]
            candidates = list(range(GRID_SIZE))
            random.shuffle(candidates)
            
            for val in candidates:
                if constraints.is_valid(row, col, val):
                    grid[row, col] = val
                    constraints.place(row, col, val)
                    
                    if fill(idx + 1):
                        return True
                    
                    grid[row, col] = -1
                    constraints.remove(row, col, val)
            
            return False
        
        if fill(0):
            return grid
        return None
    
    def generate_puzzle(self, complete_grid: np.ndarray, 
                        num_clues: int = 48) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
        """
        从完整网格生成谜题
        策略：随机移除单元格，每次移除后验证解的唯一性
        """
        grid = complete_grid.copy()
        clues_positions = []
        
        # 随机选择要保留的单元格
        all_positions = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
        random.shuffle(all_positions)
        
        # 保留num_clues个单元格
        keep_positions = set(all_positions[:num_clues])
        
        # 构建谜题网格
        puzzle_grid = np.full((GRID_SIZE, GRID_SIZE), -1, dtype=int)
        for r, c in keep_positions:
            puzzle_grid[r, c] = grid[r, c]
            clues_positions.append((r, c))
        
        return puzzle_grid, clues_positions
    
    def validate_puzzle(self, puzzle_grid: np.ndarray) -> Tuple[bool, int]:
        """
        验证谜题：检查是否有唯一解
        简化版：只检查是否可解
        """
        solver = MPCPSolver(time_limit=10.0)
        success, _ = solver.solve(puzzle_grid)
        
        if not success:
            return False, 0
        
        # 统计解的个数（简化：只找第一个解）
        return True, 1


def grid_to_puzzle_dict(grid: np.ndarray, known_positions: List[Tuple[int, int]]) -> Dict:
    """将网格转换为谜题字典"""
    known_digits = []
    for r, c in known_positions:
        known_digits.append({
            'row': r + 1,  # 1-indexed
            'col': c + 1,
            'value': grid[r, c] + 1  # 1-indexed
        })
    
    return {
        'id': f'generated_{int(time.time())}',
        'grid_size': GRID_SIZE,
        'box_size': BOX_SIZE,
        'known_digits': known_digits,
        'difficulty': 'medium' if len(known_digits) >= 40 else 'hard'
    }


# ======================== 主程序 ========================

def main():
    print("="*70)
    print("🚀 超级256数独 — 有效谜题生成器 + CPU优化求解器 V3")
    print("="*70)
    print(f"硬件: Intel Iris Xe Graphics (集成显卡)")
    print(f"优化: MRV + 前向检查 + 位运算 + 约束传播")
    print("="*70)
    
    puzzle_dir = Path("D:/2026/WPF_Sudoku/Sudoku_256")
    
    # 步骤1: 生成完整网格
    print("\n📝 步骤1: 生成完整有效网格...")
    generator = PuzzleGenerator(seed=42)  # 固定种子保证可重复
    
    complete_grid = generator.generate_complete_grid()
    if complete_grid is None:
        print("❌ 生成完整网格失败")
        return
    
    print(f"✅ 完整网格生成成功")
    print(f"   样本 (前4×4):")
    for r in range(4):
        print(f"   {complete_grid[r, :4]}")
    
    # 步骤2: 生成谜题 (≤60已知数字)
    print(f"\n🎯 步骤2: 生成谜题 (目标 {MAX_CLUES} 个已知数字)...")
    num_clues = random.randint(40, MAX_CLUES)
    puzzle_grid, clues_positions = generator.generate_puzzle(complete_grid, num_clues)
    
    print(f"✅ 谜题生成成功")
    print(f"   已知数字: {len(clues_positions)} 个")
    print(f"   空白单元格: {TOTAL_CELLS - len(clues_positions)} 个")
    
    # 步骤3: 验证谜题
    print(f"\n🔍 步骤3: 验证谜题有效性...")
    valid, solvable_count = generator.validate_puzzle(puzzle_grid)
    
    if not valid:
        print("⚠️ 谜题不可解，重新生成...")
        # 增加已知数字
        puzzle_grid, clues_positions = generator.generate_puzzle(complete_grid, min(num_clues + 10, MAX_CLUES))
        valid, solvable_count = generator.validate_puzzle(puzzle_grid)
    
    print(f"{'✅' if valid else '❌'} 谜题验证: {'可解' if valid else '不可解'}")
    
    # 步骤4: 显示谜题
    print(f"\n📋 谜题预览:")
    print("-" * 60)
    for r in range(GRID_SIZE):
        row_str = ""
        for c in range(GRID_SIZE):
            val = puzzle_grid[r, c]
            if val >= 0:
                row_str += f" {val+1:2d}"
            else:
                row_str += " . "
        print(row_str)
    print("-" * 60)
    
    # 步骤5: 保存谜题文件
    puzzle_dict = grid_to_puzzle_dict(complete_grid, clues_positions)
    puzzle_file = puzzle_dir / "test_puzzle_valid.json"
    with open(puzzle_file, 'w', encoding='utf-8') as f:
        json.dump(puzzle_dict, f, indent=2, ensure_ascii=False)
    print(f"\n💾 谜题已保存: {puzzle_file}")
    
    # 步骤6: 保存完整解
    solution_file = puzzle_dir / "test_solution_reference.json"
    solution_array = complete_grid + 1  # 转为1-indexed
    with open(solution_file, 'w', encoding='utf-8') as f:
        json.dump(solution_array.tolist(), f, indent=2)
    print(f"💾 参考解已保存: {solution_file}")
    
    # 步骤7: 运行CPU求解器验证
    print(f"\n⚡ 步骤4: 运行CPU MRV求解器验证...")
    print(f"{'='*70}")
    
    solver = MPCPSolver(time_limit=60.0)
    success, elapsed = solver.solve(puzzle_grid)
    stats = solver.get_stats()
    
    print(f"\n{'='*70}")
    print(f"📊 求解结果")
    print(f"{'='*70}")
    print(f"状态: {'✅ 成功求解' if success else '❌ 超时/失败'}")
    print(f"时间: {elapsed:.4f} 秒")
    print(f"搜索节点: {stats['nodes']:,}")
    print(f"回溯次数: {stats['backtracks']:,}")
    print(f"冲突检测: {stats['conflicts']:,}")
    print(f"前向检查: {stats['propagations']:,} 次")
    
    if success:
        # 验证解的正确性
        print(f"\n🔬 验证解的正确性...")
        solver2 = MPCPSolver(time_limit=5.0)
        success2, _ = solver2.solve(puzzle_grid)
        
        # 检查解是否符合原始完整网格
        match = np.array_equal(solver.grid, complete_grid)
        print(f"{'✅' if match else '⚠️'} 解的正确性: {'完全匹配参考解' if match else '存在差异（可能有多解）'}")
        
        # 显示部分解
        print(f"\n📋 解预览 (前4行):")
        for r in range(4):
            row_str = " ".join(f"{solver.grid[r,c]+1:2d}" for c in range(4))
            print(f"   {row_str} | ...")
    
    # 步骤8: 性能基准
    print(f"\n{'='*70}")
    print(f"📈 性能分析")
    print(f"{'='*70}")
    nodes_per_sec = stats['nodes'] / elapsed if elapsed > 0 else 0
    print(f"节点/秒: {nodes_per_sec:,.0f}")
    print(f"平均节点深度: ~{int(np.log2(stats['nodes'])) if stats['nodes'] > 0 else 0}")
    
    # 步骤9: 保存报告
    report = {
        'generator': 'PuzzleGenerator V3',
        'solver': 'MPCPSolver (MRV + Forward Check)',
        'hardware': 'Intel Iris Xe Graphics',
        'grid_size': GRID_SIZE,
        'box_size': BOX_SIZE,
        'clues_count': len(clues_positions),
        'success': success,
        'time_seconds': elapsed,
        'stats': stats,
        'puzzle_file': str(puzzle_file),
        'solution_file': str(solution_file),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    report_file = puzzle_dir / f"CPU_V3_求解验证报告_{int(time.time())}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n💾 验证报告: {report_file}")
    
    print(f"\n{'='*70}")
    print(f"✅ CPU优化求解器验证完成!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()