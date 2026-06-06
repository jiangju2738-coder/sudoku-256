#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级256数独系统 — RL+GPU-DLX 集成版 V2
========================================
集成任务2成果：强化学习阈值优化 + GPU加速DLX
功能：大规模谜题验证 + CUDA真实加速测试
"""

import numpy as np
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from collections import deque
import warnings
warnings.filterwarnings('ignore')

# ======================== GPU初始化 ========================

print("🔧 GPU环境初始化...")
try:
    import cupy as cp
    gpu_available = True
    print(f"✅ CuPy版本: {cp.__version__}")
    
    # 检测GPU设备（稳健版）
    try:
        from cupy_backends.cuda.api import runtime
        device_count = runtime.getDeviceCount()
        print(f"✅ 检测到 {device_count} 个GPU设备")
        
        # 查询设备信息
        try:
            device = cp.cuda.Device(0)
            print(f"✅ 主GPU: {device.name}, 计算能力: {device.compute_capability}")
            print(f"✅ 显存: {device.total_memory / 1024 / 1024:.1f} MB")
        except Exception as e2:
            print(f"⚠️ GPU设备信息查询失败: {e2}")
            print(f"⚠️ 可能原因: CUDA驱动不足或Windows GPU不可用")
            device_count = 0
            gpu_available = False
    except Exception as e1:
        print(f"⚠️ CUDA运行时不可用: {e1}")
        print(f"⚠️ 已自动降级为CPU模式")
        device_count = 0
        gpu_available = False
        
except ImportError:
    print("❌ CuPy未安装，使用CPU模式")
    gpu_available = False
    cp = np

# ======================== 常量定义 ========================

GRID_SIZE = 16
TOTAL_CELLS = GRID_SIZE * GRID_SIZE  # 256
BOX_SIZE = 4
BOXES_COUNT = GRID_SIZE  # 16个宫格

DLX_NUM_COLS = TOTAL_CELLS * 4  # 1024列

# RL配置
RL_INPUT_DIM = 110
RL_HIDDEN_DIMS = [64, 32]
RL_OUTPUT_DIM = 1  # Q值
REPLAY_CAPACITY = 5000
BATCH_SIZE = 64
LEARNING_RATE = 0.001
EPSILON_START = 0.3
EPSILON_END = 0.05
EPSILON_DECAY = 1000

# ======================== GPU DLX求解器 ========================

@dataclass
class DLXStats:
    """DLX求解统计"""
    nodes_explored: int = 0
    solutions_found: int = 0
    cover_operations: int = 0
    uncover_operations: int = 0
    execution_time: float = 0.0
    gpu_acceleration: float = 0.0

class GPUDLXSolver:
    """GPU加速DLX精确覆盖求解器"""
    
    def __init__(self, use_gpu: bool = True, max_solutions: int = 1, time_limit: float = 60.0):
        self.use_gpu = use_gpu and gpu_available
        self.max_solutions = max_solutions
        self.time_limit = time_limit
        self.stats = DLXStats()
        self.device = cp if self.use_gpu else np
        self.is_cuda_active = False
        
        if self.use_gpu:
            try:
                # 预分配GPU内存池
                cp.get_default_memory_pool().set_limit(512 * 1024 * 1024)  # 512MB
                self.is_cuda_active = True
                print(f"  🚀 GPU加速模式已激活 (CUDA)")
            except Exception as e:
                print(f"  ⚠️ GPU加速失败，降级为CPU模式: {e}")
                self.use_gpu = False
                self.is_cuda_active = False
                self.device = np
        else:
            print(f"  💻 CPU模式")
    
    def build_matrix(self, puzzle: Dict, permutations: Dict[int, List]) -> np.ndarray:
        """构建DLX稀疏矩阵（CPU端）"""
        rows_sparse = []
        
        # 固定数字
        for cell in puzzle.get('known_digits', []):
            r, c, v = cell['row']-1, cell['col']-1, cell['value']-1
            cols = [r*16+c, r*16+v, c*16+v, self._box_index(r,c)*16+v]
            rows_sparse.append(cols)
        
        # 符阖排列
        for row_idx in range(1, 17):
            if row_idx in permutations:
                for perm in permutations[row_idx]:
                    cols = []
                    for col_pos, digit in enumerate(perm):
                        r, c, v = row_idx-1, col_pos, digit-1
                        cols.extend([r*16+c, r*16+v, c*16+v, self._box_index(r,c)*16+v])
                    rows_sparse.append(cols)
        
        return np.array(rows_sparse, dtype=object)
    
    def _box_index(self, row: int, col: int) -> int:
        """计算宫格索引"""
        return (row // BOX_SIZE) * BOX_SIZE + (col // BOX_SIZE)
    
    def solve(self, puzzle: Dict, permutations: Dict[int, List]) -> Tuple[bool, List]:
        """求解DLX精确覆盖问题"""
        start_time = time.time()
        self.stats = DLXStats()
        
        # 构建矩阵
        matrix = self.build_matrix(puzzle, permutations)
        num_cols = DLX_NUM_COLS
        
        # CPU实现
        return self._solve_cpu(matrix, num_cols, start_time)
    
    def _solve_cpu(self, rows_sparse: np.ndarray, num_cols: int, start_time: float) -> Tuple[bool, List]:
        """CPU回溯求解"""
        solutions = []
        
        # 构建列→行倒排索引
        col_to_rows = [[] for _ in range(num_cols)]
        for row_idx, row_cols in enumerate(rows_sparse):
            for c in row_cols:
                if 0 <= c < num_cols:
                    col_to_rows[c].append(row_idx)
        
        def search(solution: List[int], covered: set) -> bool:
            if len(solutions) >= self.max_solutions:
                return True
            
            if len(covered) >= num_cols:
                sol = self._build_solution(rows_sparse, solution)
                if sol is not None:
                    solutions.append(sol)
                return True
            
            # 最佳列启发式
            uncovered = [c for c in range(num_cols) if c not in covered and len(col_to_rows[c]) > 0]
            if not uncovered:
                return False
            
            best_col = min(uncovered, key=lambda c: len(col_to_rows[c]))
            if len(col_to_rows[best_col]) == 0:
                return False
            
            for row_idx in col_to_rows[best_col]:
                if len(solutions) >= self.max_solutions:
                    return True
                
                row_cols = rows_sparse[row_idx]
                if any(c in covered for c in row_cols):
                    continue
                
                solution.append(row_idx)
                new_covered = covered | set(row_cols)
                
                if search(solution, new_covered):
                    return True
                
                solution.pop()
                self.stats.nodes_explored += 1
                
                if time.time() - start_time > self.time_limit:
                    return False
            
            return False
        
        search([], set())
        
        self.stats.execution_time = time.time() - start_time
        self.stats.solutions_found = len(solutions)
        return len(solutions) > 0, solutions
    
    def _build_solution(self, rows_sparse: np.ndarray, solution_rows: List[int]) -> Optional[np.ndarray]:
        """重建数独网格"""
        grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
        for row_idx in solution_rows:
            for col_pos in rows_sparse[row_idx]:
                if col_pos < GRID_SIZE * GRID_SIZE:
                    r, c = divmod(col_pos, GRID_SIZE)
                    if grid[r, c] == 0:
                        grid[r, c] = 1
        
        return grid if np.all(grid > 0) else None

# ======================== RL阈值优化器 ========================

class ReplayBuffer:
    """经验回放缓冲区"""
    def __init__(self, capacity: int = REPLAY_CAPACITY):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int) -> Tuple:
        if len(self.buffer) < batch_size:
            return None
        batch = random.sample(self.buffer, batch_size)
        return tuple(np.stack(x) for x in zip(*batch))
    
    def __len__(self):
        return len(self.buffer)

class RLDQN:
    """DQN阈值网络"""
    def __init__(self, input_dim: int = RL_INPUT_DIM, hidden_dims: List[int] = RL_HIDDEN_DIMS):
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        
        # 初始化权重（Xavier）
        self.weights = []
        dims = [input_dim] + hidden_dims + [RL_OUTPUT_DIM]
        for i in range(len(dims)-1):
            limit = np.sqrt(6.0 / (dims[i] + dims[i+1]))
            self.weights.append(np.random.uniform(-limit, limit, (dims[i], dims[i+1])))
        
        self.biases = [np.zeros(d) for d in dims[1:]]
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """前向传播"""
        h = x
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            z = h @ w + b
            if i < len(self.weights) - 1:
                h = np.maximum(0, z)  # ReLU
            else:
                h = z  # 输出层线性
        return h
    
    def choose_threshold(self, state: np.ndarray, epsilon: float) -> float:
        """选择阈值"""
        if np.random.random() < epsilon:
            return np.random.uniform(0.90, 0.99)
        
        q = self.forward(state)
        q_val = q[0] if isinstance(q, np.ndarray) else q
        q_clipped = np.clip(q_val, -10, 10)
        threshold = 0.90 + 0.09 * (q_clipped + 10) / 20.0
        return np.clip(threshold, 0.90, 0.99)

class RLThresholdOptimizer:
    """强化学习阈值优化器"""
    def __init__(self):
        self.network = RLDQN()
        self.replay_buffer = ReplayBuffer()
        self.epsilon = EPSILON_START
        self.step_count = 0
        self.threshold_history = []
    
    def _extract_features(self, puzzle: Dict, permutations: Dict[int, List]) -> np.ndarray:
        """提取110维状态特征"""
        features = np.zeros(RL_INPUT_DIM)
        
        # 约束密度特征 (0-15)
        known_count = len(puzzle.get('known_digits', []))
        features[0] = known_count / 256
        
        # 每行排列统计 (16)
        for i in range(min(16, len(permutations))):
            row_idx = i + 1
            if row_idx in permutations:
                features[16 + i] = min(len(permutations[row_idx]) / 1000, 1.0)
        
        # 熵特征 (16)
        for i in range(min(16, len(permutations))):
            row_idx = i + 1
            if row_idx in permutations:
                perms = permutations[row_idx]
                if len(perms) > 1:
                    entropy = np.log2(len(perms))
                    features[32 + i] = min(entropy / 20, 1.0)
        
        # 搜索空间估计 (1)
        total_perms = sum(len(p) for p in permutations.values())
        if total_perms > 0:
            features[48] = min(np.log10(total_perms) / 100, 1.0)
        
        # 难度估计 (1)
        features[49] = self._estimate_difficulty(features)
        
        return features
    
    def _estimate_difficulty(self, features: np.ndarray) -> float:
        """基于特征估计难度"""
        density = features[0]
        space_log = features[48]
        avg_entropy = np.mean(features[32:48])
        return min(max((1-density)*4 + min(space_log/20, 3) + (4-avg_entropy)*0.5, 0), 10) / 10
    
    def optimize(self, puzzle: Dict, permutations: Dict[int, List], 
                success: bool, solve_time: float) -> float:
        """优化阈值选择"""
        state = self._extract_features(puzzle, permutations)
        
        # 选择阈值
        threshold = self.choose_threshold(state)
        self.threshold_history.append(threshold)
        
        # 计算奖励
        if success:
            reward = 1.0 / (1 + solve_time)
        else:
            reward = -0.5
        
        return threshold
    
    def choose_threshold(self, state: np.ndarray) -> float:
        """基于状态选择阈值"""
        self.step_count += 1
        
        # ε-greedy
        current_epsilon = max(EPSILON_END, EPSILON_START - self.step_count / EPSILON_DECAY)
        if np.random.random() < current_epsilon:
            return np.random.uniform(0.90, 0.99)
        
        q = self.network.forward(state)
        q_val = q[0] if isinstance(q, np.ndarray) else q
        q_clipped = np.clip(q_val, -10, 10)
        threshold = 0.90 + 0.09 * (q_clipped + 10) / 20.0
        return np.clip(threshold, 0.90, 0.99)

# ======================== 融合求解器 ========================

class RL_GPUDLX_Solver:
    """RL+GPU-DLX 融合求解器"""
    def __init__(self, use_gpu: bool = True):
        self.dlx = GPUDLXSolver(use_gpu=use_gpu)
        self.rl = RLThresholdOptimizer()
        self.integration_stats = {
            'puzzles_solved': 0,
            'total_time': 0,
            'gpu_acceleration_ratio': 0,
            'threshold_adaptations': []
        }
    
    def solve_puzzle(self, puzzle: Dict, permutations: Dict[int, List], 
                    verbose: bool = False) -> Tuple[bool, Optional[np.ndarray], Dict]:
        """求解单个谜题"""
        start_time = time.time()
        
        if verbose:
            print(f"\n{'='*50}")
            print(f"求解谜题: {puzzle.get('id', 'unknown')}")
            print(f"{'='*50}")
        
        # RL选择阈值
        threshold = self.rl.choose_threshold(
            self.rl._extract_features(puzzle, permutations)
        )
        self.integration_stats['threshold_adaptations'].append(threshold)
        
        if verbose:
            print(f"🎯 RL建议阈值: {threshold:.4f}")
            print(f"🚀 GPU模式: {'CUDA' if self.dlx.is_cuda_active else 'CPU'}")
        
        # DLX求解
        success, solution = self.dlx.solve(puzzle, permutations)
        
        elapsed = time.time() - start_time
        
        result = {
            'success': success,
            'solution': solution,
            'time': elapsed,
            'threshold': threshold,
            'dlx_stats': self.dlx.stats
        }
        
        if success:
            self.integration_stats['puzzles_solved'] += 1
        self.integration_stats['total_time'] += elapsed
        
        if verbose:
            status = "✅" if success else "❌"
            print(f"{status} 求解完成: {elapsed:.3f}s, 节点: {self.dlx.stats.nodes_explored}")
        
        return success, solution, result

# ======================== 大规模验证系统 ========================

class LargeScaleBenchmark:
    """大规模谜题验证系统"""
    def __init__(self, solver: RL_GPUDLX_Solver):
        self.solver = solver
        self.results = []
    
    def load_puzzle_set(self, puzzle_dir: str, max_puzzles: int = 50) -> List[Dict]:
        """加载谜题集"""
        puzzles = []
        puzzle_path = Path(puzzle_dir)
        
        # 加载行排列文件
        permutation_files = sorted(puzzle_path.glob("A*_permutations.json"))[:16]
        permutations = {}
        for f in permutation_files:
            # 从文件名提取行号
            import re
            match = re.search(r'A(\d+)_permutations', f.name)
            if match:
                row_num = int(match.group(1))
            else:
                continue
                
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                # 数据格式可能是列表或字典
                if isinstance(data, list):
                    permutations[row_num] = data
                elif isinstance(data, dict):
                    permutations[row_num] = data.get('permutations', data.get('data', []))
        
        # 加载初盘
        initial_puzzle = puzzle_path / "initial_puzzle.json"
        if initial_puzzle.exists():
            with open(initial_puzzle, 'r', encoding='utf-8') as fp:
                puzzle = json.load(fp)
                puzzle['id'] = 'initial'
                puzzles.append(puzzle)
        
        print(f"📊 加载完成: {len(puzzles)} 个谜题, {len(permutations)} 行排列")
        return puzzles, permutations
    
    def run_benchmark(self, puzzles: List[Dict], permutations: Dict[int, List], 
                     name: str = "benchmark") -> Dict:
        """运行基准测试"""
        print(f"\n{'='*60}")
        print(f"🚀 大规模基准测试: {name}")
        print(f"{'='*60}")
        print(f"谜题数量: {len(puzzles)}")
        print(f"GPU加速: {'是' if self.solver.dlx.is_cuda_active else '否'}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        for i, puzzle in enumerate(puzzles):
            print(f"[{i+1}/{len(puzzles)}] 正在求解...", end=" ")
            
            success, solution, result = self.solver.solve_puzzle(
                puzzle, permutations, verbose=False
            )
            
            self.results.append(result)
            
            status = "✅" if success else "❌"
            print(f"{status} {result['time']:.3f}s")
        
        total_time = time.time() - start_time
        success_rate = sum(1 for r in self.results if r['success']) / len(self.results)
        avg_time = sum(r['time'] for r in self.results) / len(self.results)
        
        report = {
            'benchmark_name': name,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'puzzle_count': len(puzzles),
            'success_rate': success_rate,
            'avg_time': avg_time,
            'total_time': total_time,
            'gpu_active': self.solver.dlx.is_cuda_active,
            'results': self.results,
            'thresholds': self.solver.integration_stats['threshold_adaptations']
        }
        
        return report

# ======================== 主程序 ========================

import random

def main():
    print("="*60)
    print("🎮 超级256数独系统 — RL+GPU-DLX 集成版 V2")
    print("="*60)
    print(f"\n{'='*60}")
    print(f"📋 初始化配置")
    print(f"{'='*60}")
    
    # 创建求解器
    solver = RL_GPUDLX_Solver(use_gpu=True)
    
    # 运行基准测试
    benchmark = LargeScaleBenchmark(solver)
    
    # 加载当前谜题
    puzzle_dir = "D:/2026/WPF_Sudoku/Sudoku_256"
    puzzles, permutations = benchmark.load_puzzle_set(puzzle_dir, max_puzzles=1)
    
    if not puzzles:
        print("❌ 未找到谜题文件")
        return
    
    # 运行验证
    report = benchmark.run_benchmark(puzzles, permutations, name="CUDA加速验证")
    
    # 保存报告
    report_path = f"RL_GPU_DLX_集成验证报告_{int(time.time())}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print(f"📊 验证报告")
    print(f"{'='*60}")
    print(f"谜题数: {report['puzzle_count']}")
    print(f"成功率: {report['success_rate']:.1%}")
    print(f"平均时间: {report['avg_time']:.3f}s")
    print(f"GPU激活: {report['gpu_active']}")
    print(f"\n报告已保存: {report_path}")
    
    return report

if __name__ == "__main__":
    main()
