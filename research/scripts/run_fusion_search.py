#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极融合搜索架构 V1 — 主入口

完美融阖搜索引擎：
初盘定式 → 波浪螺旋深度覆盖 → 五维神经元融阖 → 精英回溯/GA协同 → 黏菌优化 → 策略路由
"""

import json
import sys
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 模块导入
try:
    from fusion_engine_v1 import (
        InitialPuzzleBase, WaveHelixDeepCover, EliteBacktrackGA,
        GRID_SIZE, BOX_SIZE, FUMMEL_ROWS
    )
    from neural_fusion_v1 import FiveDimensionalNeuralFusion
    from slime_mold_optimizer_v1 import SlimeMoldOptimizer, SlimeMoldConfig
    from strategy_router_v1 import (
        FusionSearchEngine, StrategyType, ParallelMode,
        ConstraintFeatures, RoutingDecision
    )
except ImportError as e:
    print(f"模块导入错误: {e}")
    print("请确保所有模块文件在同一目录下")
    sys.exit(1)


# ======================== 配置 ========================

class FusionConfig:
    """融合搜索配置"""
    
    # 时间限制
    max_time: float = 300.0  # 5分钟
    
    # 迭代限制
    max_iterations: int = 100
    ga_max_iterations: int = 50
    slime_max_iterations: int = 150
    
    # 并行配置
    num_workers: int = 4  # 并行工作线程数
    elite_pool_size: int = 50
    num_slime: int = 30  # 黏菌数量
    
    # 波浪螺旋配置
    num_waves: int = 5
    spiral_turns: int = 3
    
    # 神经元配置
    neuron_confidence_threshold: float = 0.7
    
    # 早停配置
    patience: int = 20
    min_improvement: float = 0.005


# ======================== 主引擎 ========================

class UltimateFusionEngine:
    """终极融合搜索引擎 — 统一入口
    
    六大模块完美融阖：
    1. 初盘定式基座
    2. 波浪螺旋深度覆盖
    3. 精英回溯+GA协同
    4. 五维神经元融阖
    5. 黏菌优化算子
    6. 策略路由层
    """
    
    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()
        
        # 模块实例
        self.initial_base: Optional[InitialPuzzleBase] = None
        self.wave_helix: Optional[WaveHelixDeepCover] = None
        self.elite_backtrack: Optional[EliteBacktrackGA] = None
        self.neural_fusion: Optional[FiveDimensionalNeuralFusion] = None
        self.slime_mold: Optional[SlimeMoldOptimizer] = None
        self.router: Optional[FusionSearchEngine] = None
        
        # 共享状态
        self.state = {
            'anchors': {},
            'permutations': [],
            'entropy_profile': [],
            'five_d_state': None,
            'elite_pool': [],
            'all_solutions': [],
            'iteration': 0,
            'elapsed_time': 0.0
        }
        
        # 性能追踪
        self.metrics = {
            'phase_times': {},
            'strategy_results': {},
            'convergence_history': []
        }
    
    def initialize(self, project_root: str = ".") -> bool:
        """初始化所有模块"""
        
        print("=" * 70)
        print("终极融合搜索引擎 V1 — 初始化")
        print("=" * 70)
        
        start = time.time()
        
        # Phase 1: 初盘定式模块
        print("\n[Phase 1] 初盘定式模块初始化...")
        phase_start = time.time()
        
        self.initial_base = InitialPuzzleBase(project_root)
        config_path = f"{project_root}/sudoku_config.json"
        
        try:
            anchors, graph, permutations, five_d_state = self.initial_base.initialize(config_path)
            self.state['anchors'] = anchors
            self.state['permutations'] = permutations
            self.state['five_d_state'] = five_d_state
            self.state['entropy_profile'] = five_d_state.entropy_profile
            
            print(f"      ✓ 锚点: {len(anchors)} 个")
            print(f"      ✓ 排列: {sum(len(p) for p in permutations)} 个")
            print(f"      ✓ 难度: {five_d_state.difficulty_score:.1f}/10")
            
        except FileNotFoundError as e:
            print(f"      ✗ 配置文件未找到: {e}")
            return False
        except Exception as e:
            print(f"      ✗ 初始化错误: {e}")
            return False
        
        self.metrics['phase_times']['initialization'] = time.time() - phase_start
        
        # Phase 2: 波浪螺旋模块
        print("\n[Phase 2] 波浪螺旋深度覆盖模块...")
        phase_start = time.time()
        
        self.wave_helix = WaveHelixDeepCover(
            initial_state=self.state['five_d_state'].__dict__,
            config=None  # 使用默认配置
        )
        
        self.metrics['phase_times']['wave_helix_init'] = time.time() - phase_start
        
        # Phase 3: 精英回溯+GA协同
        print("\n[Phase 3] 精英回溯+GA协同引擎...")
        phase_start = time.time()
        
        # 转换为元组格式
        perm_tuples = [[perm.values for perm in row_perms] for row_perms in permutations]
        
        self.elite_backtrack = EliteBacktrackGA(
            anchors=anchors,
            permutations=perm_tuples,
            max_elite_size=self.config.elite_pool_size
        )
        
        self.metrics['phase_times']['elite_backtrack_init'] = time.time() - phase_start
        
        # Phase 4: 五维神经元融阖
        print("\n[Phase 4] 五维神经元融阖系统...")
        phase_start = time.time()
        
        self.neural_fusion = FiveDimensionalNeuralFusion()
        self.neural_fusion.initialize(anchors)
        
        self.metrics['phase_times']['neural_fusion_init'] = time.time() - phase_start
        
        # Phase 5: 黏菌优化
        print("\n[Phase 5] 黏菌优化算子...")
        phase_start = time.time()
        
        slime_config = SlimeMoldConfig(
            num_slime=self.config.num_slime,
            max_iterations=self.config.slime_max_iterations
        )
        self.slime_mold = SlimeMoldOptimizer(slime_config)
        
        self.metrics['phase_times']['slime_mold_init'] = time.time() - phase_start
        
        # Phase 6: 策略路由
        print("\n[Phase 6] 策略路由层...")
        phase_start = time.time()
        
        self.router = FusionSearchEngine()
        self.router.initialize(
            puzzle_config={'anchors': anchors},
            permutations_data=perm_tuples
        )
        
        self.metrics['phase_times']['router_init'] = time.time() - phase_start
        
        # 总初始化时间
        total_init_time = time.time() - start
        
        print("\n" + "=" * 70)
        print(f"✓ 初始化完成，耗时 {total_init_time:.2f}s")
        print("=" * 70)
        
        return True
    
    def run(self, verbose: bool = True) -> Dict:
        """执行完整融合搜索"""
        
        start_time = time.time()
        
        if verbose:
            print("\n" + "=" * 70)
            print("开始完美融阖搜索")
            print("=" * 70)
        
        # ========== Phase A: 波浪螺旋深度覆盖 ==========
        if verbose:
            print("\n[Phase A] 波浪螺旋深度覆盖...")
        
        phase_start = time.time()
        wave_results = self.wave_helix.run_deep_cover(
            self.state['anchors'],
            max_waves=self.config.num_waves
        )
        self.metrics['phase_times']['wave_helix'] = time.time() - phase_start
        
        if verbose:
            total_wave_solutions = sum(r.solutions_found for r in wave_results)
            print(f"      波浪搜索: {total_wave_solutions} 个解")
        
        # ========== Phase B: 五维神经元融阖 ==========
        if verbose:
            print("\n[Phase B] 五维神经元融阖决策...")
        
        phase_start = time.time()
        
        # 获取当前最佳解
        best_solutions = self.state['elite_pool'][:5] if self.state['elite_pool'] else []
        
        fusion_decision = self.neural_fusion.fuse(
            anchors=self.state['anchors'],
            iteration=1,
            candidate_solutions=[{'fitness': 0.5}],  # 简化
            metrics={'fitness': 0.5, 'iterations': 1}
        )
        
        self.metrics['phase_times']['neural_fusion'] = time.time() - phase_start
        
        if verbose:
            print(f"      推荐策略: {fusion_decision.strategy}")
            print(f"      优先级单元格: {len(fusion_decision.priority_cells)} 个")
        
        # ========== Phase C: 三大引擎并行 ==========
        if verbose:
            print("\n[Phase C] 三大引擎并行执行...")
        
        phase_start = time.time()
        
        # C1: GA探索
        print("      [C1] GA探索...")
        ga_solutions = self.elite_backtrack.ga_explore(
            iteration=1,
            elite_pool=self.elite_backtrack.elite_pool
        )
        
        # C2: 回溯精修
        print("      [C2] 回溯精修...")
        refined = self.elite_backtrack.backtrack_refine(ga_solutions)
        
        # C3: 精英汇聚
        print("      [C3] 精英汇聚...")
        added = self.elite_backtrack.elite_converge(refined)
        self.state['elite_pool'] = self.elite_backtrack.elite_pool.get_top_k(
            len(self.elite_backtrack.elite_pool.elites)
        )
        
        self.metrics['phase_times']['elite_backtrack'] = time.time() - phase_start
        
        if verbose:
            print(f"      GA候选: {len(ga_solutions)}, 精修: {len(refined)}, 精英: {added}")
        
        # ========== Phase D: 黏菌优化 ==========
        if verbose:
            print("\n[Phase D] 黏菌优化探索...")
        
        phase_start = time.time()
        
        # 从精英池提取位置
        elite_positions = []
        for sol in self.state['elite_pool'][:min(10, len(self.state['elite_pool']))]:
            # 将网格转为排列索引（简化）
            pos = tuple(range(len(p)) for p in self.state['permutations'])[0]
            elite_positions.append(pos)
        
        # 运行黏菌优化
        perm_tuples = [[perm.values for perm in row_perms] for row_perms in self.state['permutations']]
        slime_result = self.slime_mold.optimize(
            permutations=perm_tuples,
            elite_pool=elite_positions[:5] if elite_positions else None,
            verbose=False
        )
        
        self.metrics['phase_times']['slime_mold'] = time.time() - phase_start
        
        if verbose:
            print(f"      最佳适应度: {slime_result.best_fitness:.4f}")
            print(f"      收敛迭代: {slime_result.convergence_iteration}")
        
        # ========== Phase E: 多解采样（CP-SAT备用） ==========
        if verbose:
            print("\n[Phase E] 多解采样...")
        
        # 这里可以添加CP-SAT多解采样
        # 简化版本：从精英池获取
        sample_solutions = self.state['elite_pool'][:10]
        self.state['all_solutions'] = sample_solutions
        
        self.metrics['phase_times']['solution_sampling'] = time.time() - phase_start
        
        # ========== 汇总 ==========
        elapsed = time.time() - start_time
        self.state['elapsed_time'] = elapsed
        
        # 构建最终结果
        results = {
            'solutions': self.state['all_solutions'],
            'num_solutions': len(self.state['all_solutions']),
            'best_fitness': max((s.fitness for s in self.state['all_solutions']), default=0),
            'total_time': elapsed,
            'phase_times': self.metrics['phase_times'],
            'elite_pool_size': len(self.state['elite_pool']),
            'wave_results': len(wave_results),
            'convergence': self.neural_fusion.spacetime.convergence_trend,
            'recommendation': fusion_decision.strategy
        }
        
        if verbose:
            print("\n" + "=" * 70)
            print("完美融阖搜索完成")
            print("=" * 70)
            
            print(f"\n📊 结果汇总:")
            print(f"   解数: {results['num_solutions']}")
            print(f"   最佳适应度: {results['best_fitness']:.4f}")
            print(f"   总时间: {elapsed:.2f}s")
            print(f"   精英池: {results['elite_pool_size']} 个")
            
            print(f"\n⏱️  各阶段耗时:")
            for phase, t in results['phase_times'].items():
                print(f"   {phase}: {t:.2f}s")
            
            print(f"\n🎯 最终建议: {results['recommendation']}")
        
        return results
    
    def export_results(self, results: Dict, output_path: str = "fusion_results.json") -> None:
        """导出结果"""
        
        # 简化版本：导出关键信息
        export_data = {
            'num_solutions': results['num_solutions'],
            'best_fitness': results['best_fitness'],
            'total_time': results['total_time'],
            'phase_times': results['phase_times'],
            'elite_pool_size': results['elite_pool_size'],
            'recommendation': results['recommendation'],
            'solutions': [
                {
                    'fitness': s.fitness,
                    'is_valid': s.is_valid
                }
                for s in results['solutions'][:10]  # 仅导出前10个
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 结果已导出至: {output_path}")


# ======================== 命令行入口 ========================

def main():
    """命令行主入口"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description='终极融合搜索引擎 V1 — 完美融阖搜索'
    )
    parser.add_argument(
        '--project-root',
        type=str,
        default='.',
        help='项目根目录'
    )
    parser.add_argument(
        '--max-time',
        type=float,
        default=300.0,
        help='最大搜索时间（秒）'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=100,
        help='最大迭代次数'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='fusion_results.json',
        help='输出文件路径'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='静默模式'
    )
    
    args = parser.parse_args()
    
    # 创建配置
    config = FusionConfig(
        max_time=args.max_time,
        max_iterations=args.max_iterations
    )
    
    # 创建引擎
    engine = UltimateFusionEngine(config)
    
    # 初始化
    if not engine.initialize(args.project_root):
        print("❌ 初始化失败")
        sys.exit(1)
    
    # 执行搜索
    results = engine.run(verbose=not args.quiet)
    
    # 导出结果
    engine.export_results(results, args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
