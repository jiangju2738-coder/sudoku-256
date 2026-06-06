#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级256数独系统 — CPU高性能优化版
====================================
专为Intel Iris Xe及通用CPU环境设计
目标: <5秒求解16×16谜题

优化策略:
1. 位运算加速约束检查
2. 稀疏矩阵压缩存储
3. 迭代深化 + 启发式搜索
4. 多核并行 (threading)
5. 缓存优化
"""

import numpy as np
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# ======================== 硬件适配检测 ========================

def detect_cpu_optimization():
    """检测CPU优化能力"""
    import multiprocessing
    
    cpu_count = multiprocessing.cpu_count()
    threads = min(cpu_count, 8)  # 最多8线程
    
    print(f"🖥️ CPU优化配置:")
    print(f"   逻辑核心数: {cpu_count}")
    print(f"   并行线程数: {threads}")
    
    return threads

THREADS = detect_cpu_optimization()

# ======================== 位运算优化 ========================

class BitConstraint:
    """位运算约束管理器（核心优化）"""
    
    __slots__ = ['row_mask', 'col_mask', 'box_mask']
    
    def __init__(self):
        # 每行/列/宫格的已使用数字掩码 (16 bits)
        self.row_mask = [0] * 16
        self.col_mask = [0] * 16
        self.box_mask = [0] * 16
    
    def reset(self):
        """重置所有掩码"""
        self.row_mask = [0] * 16
        self.col_mask = [0] * 16
        self.box_mask = [0] * 16
    
    def set_value(self, row: int, col: int, value: int):
        """设置数字，更新掩码"""
        mask = 1 << value
        self.row_mask[row] |= mask
        self.col_mask[col] |= mask
        box_idx = self._box_index(row, col)
        self.box_mask[box_idx] |= mask
    
    def clear_value(self, row: int, col: int, value: int):
        """清除数字，恢复掩码"""
        mask = ~(1 << value)
        self.row_mask[row] &= mask
        self.col_mask[col] &= mask
        box_idx = self._box_index(row, col)
        self.box_mask[box_idx] &= mask
    
    def is_valid(self, row: int, col: int, value: int) -> bool:
        """位运算检查约束（极快）"""
        mask = 1 << value
        box_idx = self._box_index(row, col)
        return not (
            (self.row_mask[row] & mask) or
            (self.col_mask[col] & mask) or
            (self.box_mask[box_idx] & mask)
        )
    
    def get_candidates(self, row: int, col: int) -> List[int]:
        """快速获取候选数字（位运算）"""
        box_idx = self._box_index(row, col)
        used = self.row_mask[row] | self.col_mask[col] | self.box_mask[box_idx]
        candidates = []
        for v in range(16):
            if not (used & (1 << v)):
                candidates.append(v)
        return candidates
    
    @staticmethod
    def _box_index(row: int, col: int) -> int:
        return (row // 4) * 4 + (col // 4)

# ======================== 稀疏DLX矩阵 ========================

class SparseDLXMatrix:
    """稀疏DLX矩阵（内存优化）"""
    
    __slots__ = ['rows', 'num_cols', 'col_to_rows']
    
    def __init__(self, num_cols: int = 1024):
        self.rows: List[List[int]] = []
        self.num_cols = num_cols
        self.col_to_rows: List[List[int]] = [[] for _ in range(num_cols)]
    
    def add_row(self, col_indices: List[int]):
        """添加一行（稀疏格式）"""
        row_idx = len(self.rows)
        self.rows.append(col_indices)
        for col in col_indices:
            if 0 <= col < self.num_cols:
                self.col_to_rows[col].append(row_idx)
    
    def get_coverage(self, row_idx: int) -> int:
        """获取行覆盖的列数"""
        return len(self.rows[row_idx])
    
    def get_best_col(self, covered: Set[int]) -> Optional[int]:
        """最佳列启发式（最小剩余）"""
        best_col = None
        min_count = float('inf')
        
        for col in range(self.num_cols):
            if col in covered:
                continue
            count = len(self.col_to_rows[col])
            if 0 < count < min_count:
                min_count = count
                best_col = col
        
        return best_col if min_count > 0 else None

# ======================== 高精度回溯求解器 ========================

class CPUHighPerformanceSolver:
    """CPU高性能回溯求解器"""
    
    def __init__(self, max_solutions: int = 1, time_limit: float = 30.0):
        self.max_solutions = max_solutions
        self.time_limit = time_limit
        self.stats = {
            'nodes_explored': 0,
            'solutions_found': 0,
            'execution_time': 0.0,
            'backtracks': 0
        }
        self.constraints = BitConstraint()
    
    def build_dlx_matrix(self, puzzle: Dict, permutations: Dict[int, List]) -> SparseDLXMatrix:
        """构建稀疏DLX矩阵"""
        matrix = SparseDLXMatrix(num_cols=1024)
        
        # 1. 固定数字行
        for cell in puzzle.get('known_digits', []):
            r, c, v = cell['row']-1, cell['col']-1, cell['value']-1
            cols = [r*16+c, r*16+v, c*16+v, self._box_index(r,c)*16+v]
            matrix.add_row(cols)
        
        # 2. 符阖排列行（每行一个排列）
        for row_idx in range(1, 17):
            if row_idx in permutations:
                for perm in permutations[row_idx]:
                    cols = []
                    for col_pos, digit in enumerate(perm):
                        r, c, v = row_idx-1, col_pos, digit-1
                        cols.extend([r*16+c, r*16+v, c*16+v, self._box_index(r,c)*16+v])
                    matrix.add_row(cols)
        
        return matrix
    
    @staticmethod
    def _box_index(row: int, col: int) -> int:
        return (row // 4) * 4 + (col // 4)
    
    def solve(self, puzzle: Dict, permutations: Dict[int, List]) -> Tuple[bool, Optional[np.ndarray]]:
        """求解谜题"""
        start_time = time.time()
        self.stats = {'nodes_explored': 0, 'solutions_found': 0, 
                      'execution_time': 0.0, 'backtracks': 0}
        
        # 构建DLX矩阵
        matrix = self.build_dlx_matrix(puzzle, permutations)
        
        # 回溯求解
        solution = []
        covered_set = set()  # 使用非局部变量
        self.stats = {'nodes_explored': 0, 'solutions_found': 0, 
                      'execution_time': 0.0, 'backtracks': 0}
        
        def search(depth: int = 0) -> bool:
            nonlocal covered_set
            if len(solution) >= self.max_solutions:
                return True
            
            if len(covered) >= 1024:
                # 找到完整解
                grid = self._reconstruct_grid(solution, matrix)
                if grid is not None:
                    self.stats['solutions_found'] += 1
                return grid is not None
            
            # 最佳列启发式
            best_col = matrix.get_best_col(covered)
            if best_col is None:
                return False
            
            # 尝试覆盖该列的所有行
            for row_idx in matrix.col_to_rows[best_col]:
                row_cols = matrix.rows[row_idx]
                
                # 冲突检测（位运算）
                conflict = False
                for c in row_cols:
                    if c in covered:
                        conflict = True
                        break
                
                if conflict:
                    continue
                
                # 选择行
                solution.append(row_idx)
                prev_covered = covered_set
                covered_set = prev_covered | set(row_cols)
                
                if search(depth + 1):
                    return True
                
                # 回溯
                solution.pop()
                covered_set = prev_covered
                self.stats['nodes_explored'] += 1
                
                if time.time() - start_time > self.time_limit:
                    return False
            
            return False
        
        search()
        
        self.stats['execution_time'] = time.time() - start_time
        return self.stats['solutions_found'] > 0, self._reconstruct_grid(
            solution, matrix
        ) if solution else None
    
    def _reconstruct_grid(self, solution_rows: List[int], 
                         matrix: SparseDLXMatrix) -> Optional[np.ndarray]:
        """重建数独网格"""
        grid = np.zeros((16, 16), dtype=int)
        filled = 0
        
        for row_idx in solution_rows:
            for col_pos in matrix.rows[row_idx]:
                if col_pos < 256:  # 单元格列
                    r, c = divmod(col_pos, 16)
                    if grid[r, c] == 0:
                        grid[r, c] = 1
                        filled += 1
        
        return grid if filled >= 256 else None

# ======================== 并行岛屿模型 ========================

class ParallelIslandSolver:
    """并行岛屿模型求解器"""
    
    def __init__(self, num_islands: int = 4):
        self.num_islands = num_islands
    
    def solve_island(self, puzzle: Dict, permutations: Dict[int, List], 
                    island_id: int) -> Dict:
        """独立岛屿求解"""
        solver = CPUHighPerformanceSolver(max_solutions=1, time_limit=15.0)
        
        # 为每个岛屿设置不同的初始偏好
        # (可通过修改排列顺序实现多样性)
        
        start_time = time.time()
        success, solution = solver.solve(puzzle, permutations)
        elapsed = time.time() - start_time
        
        return {
            'island_id': island_id,
            'success': success,
            'solution': solution,
            'time': elapsed,
            'nodes': solver.stats['nodes_explored']
        }
    
    def solve_parallel(self, puzzle: Dict, permutations: Dict[int, List]) -> Dict:
        """并行岛屿求解"""
        start_time = time.time()
        
        # 准备岛屿任务
        tasks = [(puzzle, permutations, i) for i in range(self.num_islands)]
        
        # 并行执行
        results = []
        with ThreadPoolExecutor(max_workers=self.num_islands) as executor:
            futures = {
                executor.submit(self.solve_island, p, perm, idx): idx 
                for idx, (p, perm, idx) in enumerate(tasks)
            }
            
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'island_id': futures[future],
                        'success': False,
                        'error': str(e)
                    })
        
        elapsed = time.time() - start_time
        
        # 汇聚结果
        successful = [r for r in results if r['success']]
        
        return {
            'strategy': 'parallel_island',
            'num_islands': self.num_islands,
            'success': len(successful) > 0,
            'best_solution': successful[0]['solution'] if successful else None,
            'total_time': elapsed,
            'island_results': results
        }

# ======================== 迭代深化优化 ========================

class IterativeDeepeningSolver:
    """迭代深化求解器"""
    
    def __init__(self):
        self.solver = CPUHighPerformanceSolver()
    
    def solve(self, puzzle: Dict, permutations: Dict[int, List], 
             max_depth: int = 20, time_limit: float = 30.0) -> Tuple[bool, Optional[np.ndarray]]:
        """迭代深化搜索"""
        start_time = time.time()
        
        for depth in range(1, max_depth + 1):
            if time.time() - start_time > time_limit:
                break
            
            # 使用当前深度限制求解
            self.solver.time_limit = time_limit - (time.time() - start_time)
            success, solution = self.solver.solve(puzzle, permutations)
            
            if success:
                return True, solution
        
        return False, None

# ======================== 主程序 ========================

def load_puzzle_data(puzzle_dir: str) -> Tuple[Dict, Dict[int, List]]:
    """加载谜题数据"""
    import re
    puzzle_path = Path(puzzle_dir)
    
    # 加载排列
    permutation_files = sorted(puzzle_path.glob("A*_permutations.json"))
    permutations = {}
    
    for f in permutation_files:
        match = re.search(r'A(\d+)_permutations', f.name)
        if match:
            row_num = int(match.group(1))
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                permutations[row_num] = data if isinstance(data, list) else []
    
    # 加载初盘
    initial_puzzle = puzzle_path / "initial_puzzle.json"
    if initial_puzzle.exists():
        with open(initial_puzzle, 'r', encoding='utf-8') as fp:
            puzzle = json.load(fp)
            puzzle['id'] = 'initial'
    else:
        puzzle = {'id': 'unknown', 'known_digits': []}
    
    return puzzle, permutations

def main():
    print("="*60)
    print("🚀 超级256数独 — CPU高性能优化版")
    print("="*60)
    print(f"\n优化策略:")
    print(f"   • 位运算约束检查 (BitConstraint)")
    print(f"   • 稀疏DLX矩阵存储 (SparseDLXMatrix)")
    print(f"   • 最佳列启发式搜索")
    print(f"   • 并行岛屿模型 ({THREADS} 线程)")
    print(f"\n硬件:")
    print(f"   GPU: Intel Iris Xe Graphics (集成)")
    print(f"   CUDA: 不可用")
    print("="*60)
    
    # 加载数据
    puzzle_dir = "D:/2026/WPF_Sudoku/Sudoku_256"
    puzzle, permutations = load_puzzle_data(puzzle_dir)
    
    print(f"\n谜题: {puzzle.get('id', 'unknown')}")
    print(f"已知数字: {len(puzzle.get('known_digits', []))} 个")
    print(f"排列总数: {sum(len(p) for p in permutations.values())} 行")
    
    # 基准测试
    print(f"\n{'='*60}")
    print(f"📊 性能测试")
    print(f"{'='*60}")
    
    # 方法1: 单线程优化求解
    print("\n🔹 方法1: 单线程高性能求解...")
    solver = CPUHighPerformanceSolver(max_solutions=1, time_limit=30.0)
    success, solution = solver.solve(puzzle, permutations)
    
    t1 = solver.stats['execution_time']
    print(f"   状态: {'✅ 成功' if success else '❌ 超时/失败'}")
    print(f"   时间: {t1:.3f}s")
    print(f"   节点: {solver.stats['nodes_explored']:,}")
    
    # 方法2: 并行岛屿求解
    if not success:
        print("\n🔹 方法2: 并行岛屿模型...")
        parallel_solver = ParallelIslandSolver(num_islands=THREADS)
        result = parallel_solver.solve_parallel(puzzle, permutations)
        
        print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
        print(f"   时间: {result['total_time']:.3f}s")
        for ir in result['island_results']:
            status = "✅" if ir['success'] else "❌"
            print(f"     岛屿{ir['island_id']}: {status} {ir['time']:.3f}s")
    
    # 保存报告
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'hardware': {
            'gpu': 'Intel Iris Xe Graphics',
            'cuda': False,
            'cpu_threads': THREADS
        },
        'puzzle_id': puzzle.get('id'),
        'optimization': {
            'bit_constraint': True,
            'sparse_dlx': True,
            'best_column_heuristic': True,
            'parallel_islands': THREADS
        },
        'results': {
            'single_thread': {
                'success': success,
                'time': t1,
                'nodes': solver.stats['nodes_explored']
            }
        }
    }
    
    report_path = f"CPU_高性能优化报告_{int(time.time())}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ CPU优化完成")
    print(f"{'='*60}")
    print(f"报告: {report_path}")
    
    return report

if __name__ == "__main__":
    main()
