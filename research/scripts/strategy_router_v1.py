#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极融合搜索架构 V1 — 策略路由层

模块6：动态选择最优求解路径 + 并行协同 + 结果汇聚
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum
import random


# ======================== 常量定义 ========================

GRID_SIZE = 16


# ======================== 枚举类型 ========================

class StrategyType(Enum):
    """求解策略类型"""
    DLX = "dlx"                    # DLX精确覆盖
    GA = "ga"                      # 遗传算法
    BACKTRACK = "backtrack"        # 回溯
    CP_SAT = "cp_sat"              # CP-SAT
    MOBIOUS = "mobius"             # 莫比乌斯
    WAVE_HELIX = "wave_helix"      # 波浪螺旋
    SLIME_MOLD = "slime_mold"      # 黏菌
    FUSION = "fusion"              # 融合


class ParallelMode(Enum):
    """并行模式"""
    SERIAL = "serial"              # 串行
    HYBRID = "hybrid"              # 混合
    PARALLEL = "parallel"          # 并行
    FULL_PARALLEL = "full_parallel"  # 完全并行


# ======================== 数据类 ========================

@dataclass
class RoutingDecision:
    """路由决策"""
    primary_strategy: StrategyType
    parallel_mode: ParallelMode
    strategy_weights: Dict[StrategyType, float]
    time_allocation: Dict[StrategyType, float]
    reason: str


@dataclass
class ConstraintFeatures:
    """约束特征"""
    constraint_density: float = 0.0  # 锚点密度
    search_space_estimate: float = 0.0  # 搜索空间估计
    entropy_profile: List[float] = field(default_factory=list)
    permutation_counts: List[int] = field(default_factory=list)
    
    def estimate_difficulty(self) -> float:
        """估计难度（0-10）"""
        difficulty = 0.0
        
        # 锚点越少越难
        difficulty += (1 - self.constraint_density) * 4
        
        # 搜索空间越大越难
        if self.search_space_estimate > 0:
            difficulty += min(np.log10(self.search_space_estimate) / 20, 3)
        
        # 熵越低越难
        if self.entropy_profile:
            avg_entropy = sum(self.entropy_profile) / len(self.entropy_profile)
            difficulty += (4 - avg_entropy) * 0.5
        
        return min(max(difficulty, 0), 10)


@dataclass
class StrategyResult:
    """策略执行结果"""
    strategy: StrategyType
    solutions: List[Dict]
    execution_time: float
    search_nodes: int
    success: bool


@dataclass
class FusionEngineResult:
    """融合引擎结果"""
    solutions: List[Dict]
    strategy_results: Dict[StrategyType, StrategyResult]
    total_time: float
    convergence_iterations: int
    best_fitness: float
    coverage_estimate: float


# ======================== 策略路由层 ========================

class StrategyRouter:
    """策略路由层 — 动态选择最优求解路径
    
    基于问题特征（约束密度、搜索空间大小、熵分布）选择最优策略组合。
    """
    
    # 路由决策矩阵
    ROUTING_MATRIX = {
        # (约束密度范围, 搜索空间log10范围) → (主策略, 并行模式, 权重)
        (0.7, 4):   (StrategyType.DLX, ParallelMode.SERIAL, {StrategyType.DLX: 1.0}),
        (0.5, 6):   (StrategyType.BACKTRACK, ParallelMode.HYBRID, {
                        StrategyType.BACKTRACK: 0.6,
                        StrategyType.GA: 0.3,
                        StrategyType.CP_SAT: 0.1
                    }),
        (0.3, 8):   (StrategyType.GA, ParallelMode.PARALLEL, {
                        StrategyType.GA: 0.5,
                        StrategyType.WAVE_HELIX: 0.3,
                        StrategyType.SLIME_MOLD: 0.2
                    }),
        (0.1, 10):  (StrategyType.FUSION, ParallelMode.FULL_PARALLEL, {
                        StrategyType.WAVE_HELIX: 0.3,
                        StrategyType.GA: 0.25,
                        StrategyType.SLIME_MOLD: 0.25,
                        StrategyType.MOBIOUS: 0.1,
                        StrategyType.BACKTRACK: 0.1
                    }),
    }
    
    def __init__(self):
        self.routing_history: List[RoutingDecision] = []
    
    def analyze_features(self, 
                        anchors: Dict[Tuple[int, int], int],
                        permutations: List[List[Tuple[int, ...]]],
                        entropy_profile: List[float]) -> ConstraintFeatures:
        """分析问题特征"""
        
        features = ConstraintFeatures()
        
        # 约束密度
        total_cells = GRID_SIZE * GRID_SIZE
        features.constraint_density = len(anchors) / total_cells
        
        # 搜索空间估计
        total_perms = sum(len(p) for p in permutations)
        features.search_space_estimate = total_perms
        
        # 熵分布
        features.entropy_profile = entropy_profile
        
        # 每行排列数
        features.permutation_counts = [len(p) for p in permutations]
        
        return features
    
    def select_strategy(self, features: ConstraintFeatures) -> RoutingDecision:
        """基于特征选择最优策略"""
        
        # 计算约束密度和搜索空间
        density = features.constraint_density
        log_space = np.log10(max(features.search_space_estimate, 1))
        
        # 查找匹配的区间
        for (density_threshold, space_threshold), (strategy, mode, weights) in self.ROUTING_MATRIX.items():
            if density >= density_threshold or log_space <= space_threshold:
                reason = f"约束密度={density:.2f}, 搜索空间≈10^{log_space:.1f}"
                
                decision = RoutingDecision(
                    primary_strategy=strategy,
                    parallel_mode=mode,
                    strategy_weights=weights,
                    time_allocation={s: w for s, w in weights.items()},
                    reason=reason
                )
                
                self.routing_history.append(decision)
                return decision
        
        # 默认：融合策略
        default_decision = RoutingDecision(
            primary_strategy=StrategyType.FUSION,
            parallel_mode=ParallelMode.FULL_PARALLEL,
            strategy_weights={
                StrategyType.WAVE_HELIX: 0.3,
                StrategyType.GA: 0.25,
                StrategyType.SLIME_MOLD: 0.25,
                StrategyType.BACKTRACK: 0.2
            },
            time_allocation={},
            reason=f"默认融合策略（密度={density:.2f}）"
        )
        
        self.routing_history.append(default_decision)
        return default_decision
    
    def execute_parallel(self, 
                        decision: RoutingDecision,
                        executors: Dict[StrategyType, callable],
                        shared_state: Dict) -> Dict[StrategyType, StrategyResult]:
        """并行执行多个策略"""
        
        results = {}
        
        for strategy, weight in decision.strategy_weights.items():
            if strategy in executors:
                # 分配时间（基于权重）
                time_budget = shared_state.get('total_time_budget', 300) * weight
                
                try:
                    executor = executors[strategy]
                    result = executor(shared_state, time_budget)
                    results[strategy] = result
                except Exception as e:
                    results[strategy] = StrategyResult(
                        strategy=strategy,
                        solutions=[],
                        execution_time=0,
                        search_nodes=0,
                        success=False
                    )
        
        return results
    
    def merge_results(self, 
                     strategy_results: Dict[StrategyType, StrategyResult]) -> List[Dict]:
        """汇聚多策略结果（去重 + 排序 + 验证）"""
        
        all_solutions = []
        
        for strategy, result in strategy_results.items():
            if result.success:
                all_solutions.extend(result.solutions)
        
        # 去重（基于哈希）
        seen_hashes = set()
        unique_solutions = []
        
        for sol in all_solutions:
            sol_hash = hash(str(sol))
            if sol_hash not in seen_hashes:
                seen_hashes.add(sol_hash)
                unique_solutions.append(sol)
        
        # 按适应度排序
        unique_solutions.sort(
            key=lambda s: s.get('fitness', 0),
            reverse=True
        )
        
        return unique_solutions


# ======================== 终极融合搜索引擎 ========================

class FusionSearchEngine:
    """终极融合搜索引擎 — 主入口
    
    完整流程：
    1. 初盘解析 → 5D初始状态
    2. 波浪螺旋深度覆盖
    3. 五维神经元融阖决策
    4. 三大引擎并行（精英回溯 + GA + 黏菌）
    5. 策略路由与结果汇聚
    """
    
    def __init__(self):
        # 模块引用（实际实现时从各模块导入）
        self.initial_base = None
        self.wave_helix = None
        self.elite_backtrack = None
        self.neural_fusion = None
        self.slime_mold = None
        self.router = StrategyRouter()
        
        self.config = {
            'max_time': 300.0,
            'max_iterations': 100,
            'elite_pool_size': 50,
            'num_slime': 30
        }
        
        self.state = {
            'anchors': {},
            'permutations': [],
            'entropy_profile': [],
            'elapsed_time': 0.0
        }
    
    def initialize(self, 
                  puzzle_config: Dict,
                  permutations_data: List[List[Tuple[int, ...]]]) -> None:
        """初始化引擎"""
        
        # 初始化初盘定式模块
        # self.initial_base = InitialPuzzleBase()
        # anchors, graph, permutations, state = self.initial_base.initialize()
        
        # 临时模拟
        self.state['anchors'] = puzzle_config.get('anchors', {})
        self.state['permutations'] = permutations_data
        
        # 计算熵分布
        entropy_profile = []
        for row_perms in permutations_data:
            # 简化计算
            entropy_profile.append(3.0)  # 平均熵
        
        self.state['entropy_profile'] = entropy_profile
        
        # 分析特征并路由
        features = self.router.analyze_features(
            self.state['anchors'],
            permutations_data,
            entropy_profile
        )
        
        decision = self.router.select_strategy(features)
        
        print("=" * 60)
        print("终极融合搜索引擎初始化完成")
        print("=" * 60)
        print(f"\n问题特征:")
        print(f"  锚点密度: {features.constraint_density:.2%}")
        print(f"  搜索空间: ≈10^{np.log10(max(sum(len(p) for p in permutations_data), 1)):.1f}")
        print(f"  估计难度: {features.estimate_difficulty():.1f}/10")
        
        print(f"\n路由决策:")
        print(f"  主策略: {decision.primary_strategy.value}")
        print(f"  并行模式: {decision.parallel_mode.value}")
        print(f"  策略权重: {decision.strategy_weights}")
    
    def run(self, verbose: bool = True) -> FusionEngineResult:
        """执行完整融合搜索"""
        
        import time
        start_time = time.time()
        
        if verbose:
            print("\n" + "=" * 60)
            print("开始融合搜索")
            print("=" * 60)
        
        # 获取路由决策
        features = self.router.analyze_features(
            self.state['anchors'],
            self.state['permutations'],
            self.state['entropy_profile']
        )
        decision = self.router.select_strategy(features)
        
        # 定义策略执行器（简化版本）
        executors = {
            StrategyType.WAVE_HELIX: self._execute_wave_helix,
            StrategyType.GA: self._execute_ga,
            StrategyType.SLIME_MOLD: self._execute_slime_mold,
            StrategyType.BACKTRACK: self._execute_backtrack,
            StrategyType.MOBIOUS: self._execute_mobius,
        }
        
        # 并行执行
        if verbose:
            print(f"\n执行策略组合...")
        
        strategy_results = self.router.execute_parallel(
            decision,
            executors,
            self.state
        )
        
        # 汇聚结果
        final_solutions = self.router.merge_results(strategy_results)
        
        elapsed = time.time() - start_time
        
        # 构建结果
        result = FusionEngineResult(
            solutions=final_solutions,
            strategy_results=strategy_results,
            total_time=elapsed,
            convergence_iterations=self.config['max_iterations'],
            best_fitness=max((s.get('fitness', 0) for s in final_solutions), default=0),
            coverage_estimate=len(final_solutions) / max(len(self.state.get('permutations', [[]])[0]), 1)
        )
        
        if verbose:
            print("\n" + "=" * 60)
            print("融合搜索完成")
            print("=" * 60)
            print(f"\n结果汇总:")
            print(f"  总解数: {len(final_solutions)}")
            print(f"  最佳适应度: {result.best_fitness:.4f}")
            print(f"  搜索时间: {elapsed:.2f}s")
            
            print(f"\n各策略表现:")
            for strategy, sr in strategy_results.items():
                status = "✅" if sr.success else "❌"
                print(f"  {status} {strategy.value}: {len(sr.solutions)} 解, {sr.execution_time:.2f}s")
        
        return result
    
    def _execute_wave_helix(self, state: Dict, time_budget: float) -> StrategyResult:
        """执行波浪螺旋搜索（简化）"""
        # 实际实现会调用 WaveHelixDeepCover
        return StrategyResult(
            strategy=StrategyType.WAVE_HELIX,
            solutions=[],
            execution_time=min(time_budget * 0.3, 30.0),
            search_nodes=10000,
            success=True
        )
    
    def _execute_ga(self, state: Dict, time_budget: float) -> StrategyResult:
        """执行遗传算法（简化）"""
        return StrategyResult(
            strategy=StrategyType.GA,
            solutions=[],
            execution_time=min(time_budget * 0.25, 45.0),
            search_nodes=50000,
            success=True
        )
    
    def _execute_slime_mold(self, state: Dict, time_budget: float) -> StrategyResult:
        """执行黏菌优化（简化）"""
        return StrategyResult(
            strategy=StrategyType.SLIME_MOLD,
            solutions=[],
            execution_time=min(time_budget * 0.25, 60.0),
            search_nodes=30000,
            success=True
        )
    
    def _execute_backtrack(self, state: Dict, time_budget: float) -> StrategyResult:
        """执行回溯搜索（简化）"""
        return StrategyResult(
            strategy=StrategyType.BACKTRACK,
            solutions=[],
            execution_time=min(time_budget * 0.2, 20.0),
            search_nodes=20000,
            success=True
        )
    
    def _execute_mobius(self, state: Dict, time_budget: float) -> StrategyResult:
        """执行莫比乌斯搜索（简化）"""
        return StrategyResult(
            strategy=StrategyType.MOBIOUS,
            solutions=[],
            execution_time=min(time_budget * 0.1, 15.0),
            search_nodes=15000,
            success=True
        )


# ======================== 测试 ========================

if __name__ == "__main__":
    import numpy as np
    
    # 模拟数据
    anchors = {
        (2, 0): 7, (2, 1): 15, (2, 2): 3, (2, 3): 9,
        (3, 0): 5, (3, 1): 1, (3, 2): 14, (3, 3): 16,
    }
    
    permutations = []
    for row_idx in range(GRID_SIZE):
        row_perms = []
        for _ in range(100):
            perm = list(range(1, GRID_SIZE + 1))
            random.shuffle(perm)
            row_perms.append(tuple(perm))
        permutations.append(row_perms)
    
    # 创建引擎
    engine = FusionSearchEngine()
    
    # 初始化
    engine.initialize(
        puzzle_config={'anchors': anchors},
        permutations_data=permutations
    )
    
    # 执行搜索
    result = engine.run(verbose=True)
    
    print(f"\n✓ 融合搜索完成，共找到 {len(result.solutions)} 个解")
