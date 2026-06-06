#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级256数独系统 — 批量谜题验证框架
====================================
功能：在更大谜题集上验证RL+GPU-DLX性能
"""

import numpy as np
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import warnings
warnings.filterwarnings('ignore')

# 导入集成模块
import sys
sys.path.insert(0, str(Path(__file__).parent))
from rl_gpu_dlx_integration_v2 import RL_GPUDLX_Solver, RLThresholdOptimizer

# ======================== 批量验证配置 ========================

@dataclass
class BatchConfig:
    """批量验证配置"""
    num_puzzles: int = 50
    timeout_per_puzzle: float = 30.0  # 秒
    parallel_workers: int = 4
    use_gpu: bool = True
    output_dir: str = "benchmark_results"

@dataclass
class PuzzleBenchmark:
    """单个谜题基准测试"""
    puzzle_id: str
    success: bool
    time: float
    threshold: float
    nodes: int
    gpu_active: bool
    difficulty_estimate: float

# ======================== 谜题生成器 ========================

class PuzzleGenerator:
    """谜题生成器（用于生成测试集）"""
    
    @staticmethod
    def generate_random_puzzle(n_clues: int = 60) -> Dict:
        """生成随机谜题（带n_clues个已知数字）"""
        grid = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
        clues = []
        
        # 随机放置已知数字
        positions = random.sample([(r, c) for r in range(16) for c in range(16)], n_clues)
        for r, c in positions:
            grid[r][c] = random.randint(1, 16)
            clues.append({'row': r+1, 'col': c+1, 'value': grid[r][c]})
        
        return {
            'id': f'random_{n_clues}',
            'known_digits': clues,
            'grid': grid
        }
    
    @staticmethod
    def generate_symmetric_puzzle(n_clues: int = 60) -> Dict:
        """生成对称谜题"""
        grid = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
        clues = []
        
        # 对称放置（中心对称）
        positions = random.sample([(r, c) for r in range(8) for c in range(16)], n_clues // 2)
        for r, c in positions:
            val = random.randint(1, 16)
            grid[r][c] = val
            grid[15-r][15-c] = val
            clues.append({'row': r+1, 'col': c+1, 'value': val})
            clues.append({'row': 16-r, 'col': 16-c, 'value': val})
        
        return {
            'id': f'symmetric_{n_clues}',
            'known_digits': clues,
            'grid': grid
        }

# ======================== 批量验证器 ========================

class BatchBenchmarkRunner:
    """批量基准测试运行器"""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.solver = RL_GPUDLX_Solver(use_gpu=config.use_gpu)
        self.results: List[PuzzleBenchmark] = []
    
    def load_puzzle_collection(self, puzzle_dir: str) -> Tuple[List[Dict], Dict[int, List]]:
        """加载谜题集合"""
        puzzle_path = Path(puzzle_dir)
        
        # 加载所有排列文件
        permutation_files = sorted(puzzle_path.glob("A*_permutations.json"))
        permutations = {}
        
        for f in permutation_files:
            import re
            match = re.search(r'A(\d+)_permutations', f.name)
            if match:
                row_num = int(match.group(1))
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    if isinstance(data, list):
                        permutations[row_num] = data
                    elif isinstance(data, dict):
                        permutations[row_num] = data.get('permutations', data.get('data', []))
        
        # 加载所有初盘
        puzzles = []
        for f in puzzle_path.glob("*_puzzle.json"):
            with open(f, 'r', encoding='utf-8') as fp:
                puzzle = json.load(fp)
                if 'known_digits' in puzzle:
                    puzzle['id'] = f.stem
                    puzzles.append(puzzle)
        
        print(f"📊 加载: {len(puzzles)} 谜题, {len(permutations)} 行排列")
        return puzzles, permutations
    
    def solve_single_puzzle(self, args: Tuple) -> PuzzleBenchmark:
        """求解单个谜题"""
        puzzle, permutations, idx = args
        start_time = time.time()
        
        success, solution, result = self.solver.solve_puzzle(
            puzzle, permutations, verbose=False
        )
        
        elapsed = time.time() - start_time
        
        return PuzzleBenchmark(
            puzzle_id=puzzle.get('id', f'puzzle_{idx}'),
            success=success,
            time=elapsed,
            threshold=result['threshold'],
            nodes=result['dlx_stats'].nodes_explored,
            gpu_active=self.solver.dlx.is_cuda_active,
            difficulty_estimate=0.0  # 可计算
        )
    
    def run_batch(self, puzzles: List[Dict], permutations: Dict[int, List]) -> Dict:
        """运行批量验证"""
        print(f"\n{'='*60}")
        print(f"🚀 批量基准测试")
        print(f"{'='*60}")
        print(f"谜题数量: {len(puzzles)}")
        print(f"并行线程: {self.config.parallel_workers}")
        print(f"GPU加速: {'是' if self.config.use_gpu else '否'}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        results = []
        
        # 准备任务
        tasks = [(p, permutations, i) for i, p in enumerate(puzzles)]
        
        if self.config.parallel_workers > 1:
            # 并行执行
            with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
                futures = {executor.submit(self.solve_single_puzzle, t): t for t in tasks}
                
                completed = 0
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                        completed += 1
                        status = "✅" if result.success else "❌"
                        print(f"[{completed}/{len(puzzles)}] {status} {result.puzzle_id}: {result.time:.3f}s")
                    except Exception as e:
                        completed += 1
                        print(f"[{completed}/{len(puzzles)}] ❌ 错误: {e}")
        else:
            # 串行执行
            for i, task in enumerate(tasks):
                result = self.solve_single_puzzle(task)
                results.append(result)
                status = "✅" if result.success else "❌"
                print(f"[{i+1}/{len(puzzles)}] {status} {result.puzzle_id}: {result.time:.3f}s")
        
        total_time = time.time() - start_time
        
        # 统计分析
        success_count = sum(1 for r in results if r.success)
        success_rate = success_count / len(results) if results else 0
        avg_time = sum(r.time for r in results) / len(results) if results else 0
        total_nodes = sum(r.nodes for r in results)
        
        report = {
            'config': {
                'num_puzzles': len(puzzles),
                'parallel_workers': self.config.parallel_workers,
                'gpu_enabled': self.config.use_gpu,
                'timeout_per_puzzle': self.config.timeout_per_puzzle
            },
            'summary': {
                'total_time': total_time,
                'success_rate': success_rate,
                'success_count': success_count,
                'avg_time': avg_time,
                'total_nodes': total_nodes,
                'min_time': min(r.time for r in results) if results else 0,
                'max_time': max(r.time for r in results) if results else 0
            },
            'results': [
                {
                    'puzzle_id': r.puzzle_id,
                    'success': r.success,
                    'time': r.time,
                    'threshold': r.threshold,
                    'nodes': r.nodes,
                    'gpu_active': r.gpu_active
                }
                for r in results
            ]
        }
        
        return report

# ======================== 主程序 ========================

def main():
    print("="*60)
    print("🎯 超级256数独 — 批量验证框架")
    print("="*60)
    
    # 配置
    config = BatchConfig(
        num_puzzles=5,  # 测试5个谜题
        timeout_per_puzzle=60.0,
        parallel_workers=1,  # CPU模式下使用1个线程
        use_gpu=False,  # GPU驱动不可用
        output_dir="benchmark_results"
    )
    
    # 创建验证器
    runner = BatchBenchmarkRunner(config)
    
    # 加载谜题
    puzzle_dir = "D:/2026/WPF_Sudoku/Sudoku_256"
    puzzles, permutations = runner.load_puzzle_collection(puzzle_dir)
    
    if not puzzles:
        print("❌ 未找到谜题文件")
        return
    
    # 运行批量测试
    report = runner.run_batch(puzzles, permutations)
    
    # 保存报告
    os.makedirs(config.output_dir, exist_ok=True)
    report_path = f"{config.output_dir}/batch_benchmark_{int(time.time())}.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    # 打印摘要
    print(f"\n{'='*60}")
    print(f"📊 批量验证报告")
    print(f"{'='*60}")
    print(f"总时间: {report['summary']['total_time']:.2f}s")
    print(f"成功率: {report['summary']['success_rate']:.1%}")
    print(f"平均时间: {report['summary']['avg_time']:.3f}s")
    print(f"总节点: {report['summary']['total_nodes']:,}")
    print(f"\n报告保存: {report_path}")

if __name__ == "__main__":
    main()
