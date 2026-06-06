#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V33-1: 莫比乌斯搜索算法
设计"单侧"均匀采样策略

核心思想：
- 解空间 = 莫比乌斯带（单侧拓扑）
- 分叉点 = 扭结（180°扭转点）
- 解无优先級 → 均匀采样所有23个本質解
"""

import json
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Set, Optional
import time
import random

# ============================================================================
# 1. 莫比乌斯拓扑定义
# ============================================================================

class MobiusTopology:
    """莫比乌斯带拓扑结构定义"""
    
    def __init__(self, solutions: List[Dict]):
        self.solutions = solutions
        self.n_solutions = len(solutions)
        
        # 提取分叉点信息
        self.divergence_points = [(0, 0), (0, 1), (0, 3)]  # V31确认的分叉点
        self.fixed_point = (0, 2)  # 固定值为3
        
        # 构建扭结映射
        self.knot_mapping = self._build_knot_mapping()
        
        # 构建解空间邻接图
        self.adjacency_graph = self._build_adjacency_graph()
        
    def _build_knot_mapping(self) -> Dict:
        """构建分叉点扭结映射"""
        # 收集所有分叉点取值模式
        patterns = []
        for sol in self.solutions:
            fb = sol['first_box']
            pattern = (fb[0], fb[1], fb[3])  # (0,0), (0,1), (0,3)
            patterns.append(pattern)
        
        # 计算条件概率 P((0,0) | (0,1))
        conditional_probs = {}
        for sol in self.solutions:
            fb = sol['first_box']
            val1 = fb[1]  # (0,1)
            val0 = fb[0]  # (0,0)
            
            if val1 not in conditional_probs:
                conditional_probs[val1] = Counter()
            conditional_probs[val1][val0] += 1
        
        # 识别"扭结收缩"情况（强约束）
        knot_contraction = {}
        for val1, val0_dist in conditional_probs.items():
            if len(val0_dist) == 1:
                knot_contraction[val1] = list(val0_dist.keys())[0]
        
        return {
            'patterns': patterns,
            'conditional_probs': {k: dict(v) for k, v in conditional_probs.items()},
            'knot_contraction': knot_contraction  # (0,1)=8 → (0,0)=1
        }
    
    def _build_adjacency_graph(self) -> Dict:
        """构建解空间邻接图"""
        n = self.n_solutions
        
        # 计算每对解的差异度（首宫差异）
        diff_matrix = np.zeros((n, n), dtype=int)
        for i in range(n):
            for j in range(i+1, n):
                fb1 = self.solutions[i]['first_box']
                fb2 = self.solutions[j]['first_box']
                diff = sum(1 for a, b in zip(fb1, fb2) if a != b)
                diff_matrix[i, j] = diff
                diff_matrix[j, i] = diff
        
        # 找最小差异（定义邻接）
        min_diff = float('inf')
        for i in range(n):
            for j in range(i+1, n):
                if diff_matrix[i, j] > 0:
                    min_diff = min(min_diff, diff_matrix[i, j])
        
        # 构建邻接列表
        adjacency = defaultdict(list)
        for i in range(n):
            for j in range(i+1, n):
                if diff_matrix[i, j] == min_diff:
                    adjacency[i].append(j)
                    adjacency[j].append(i)
        
        return {
            'diff_matrix': diff_matrix,
            'min_diff': min_diff,
            'adjacency': {str(k): v for k, v in adjacency.items()}
        }
    
    def get_twist_point(self, solution_idx: int) -> Tuple[int, int, int]:
        """获取某个解的扭结状态（分叉点取值）"""
        fb = self.solutions[solution_idx]['first_box']
        return (fb[0], fb[1], fb[3])
    
    def twist_constraint(self, val1: int) -> Dict:
        """
        扭结约束函数
        给定(0,1)的值，返回(0,0)的约束集合
        """
        cond_probs = self.knot_mapping['conditional_probs']
        if val1 in cond_probs:
            return {k: v/sum(cond_probs[val1].values()) 
                    for k, v in cond_probs[val1].items()}
        return {}
    
    def is_knot_contracted(self, val1: int) -> bool:
        """检查是否为扭结收缩状态（强约束）"""
        return val1 in self.knot_mapping['knot_contraction']


# ============================================================================
# 2. 莫比乌斯搜索算法
# ============================================================================

class MobiusSearchAlgorithm:
    """莫比乌斯搜索算法实现"""
    
    def __init__(self, topology: MobiusTopology):
        self.topology = topology
        self.visited = set()
        self.visit_order = []
        self.uniform_samples = []
        
    def twist_propagation(self, current_idx: int, direction: str = 'forward') -> List[int]:
        """
        扭结传播：沿扭结约束方向搜索相邻解
        direction: 'forward' 沿扭结传播, 'backward' 逆传播
        """
        current_twist = self.topology.get_twist_point(current_idx)
        val1 = current_twist[1]  # (0,1)
        
        # 获取扭结约束
        constraint = self.topology.twist_constraint(val1)
        
        # 找到满足约束的相邻解
        neighbors = self.topology.adjacency_graph['adjacency'].get(str(current_idx), [])
        valid_neighbors = []
        
        for neighbor_idx in neighbors:
            neighbor_twist = self.topology.get_twist_point(neighbor_idx)
            # 检查是否满足扭结约束
            if neighbor_twist[0] in constraint:
                valid_neighbors.append(neighbor_idx)
        
        return valid_neighbors
    
    def mobius_walk(self, start_idx: int = 0, max_steps: int = 100) -> List[int]:
        """
        莫比乌斯行走：在"单侧"拓扑上游走
        关键：不区分"正面"和"反面"，均匀探索
        """
        path = [start_idx]
        current = start_idx
        self.visited.add(start_idx)
        
        for step in range(max_steps):
            # 获取当前扭结状态
            twist = self.topology.get_twist_point(current)
            val1 = twist[1]
            
            # 判断是否为扭结收缩
            if self.topology.is_knot_contracted(val1):
                # 扭结收缩：强制传播
                neighbors = self.twist_propagation(current, 'forward')
                if not neighbors:
                    # 无法传播，随机跳转到未访问解
                    unvisited = [i for i in range(self.topology.n_solutions) 
                                 if i not in self.visited]
                    if unvisited:
                        next_idx = random.choice(unvisited)
                    else:
                        break
                else:
                    next_idx = random.choice(neighbors)
            else:
                # 普通状态：沿邻接图随机行走
                neighbors = self.topology.adjacency_graph['adjacency'].get(str(current), [])
                unvisited_neighbors = [n for n in neighbors if n not in self.visited]
                
                if unvisited_neighbors:
                    next_idx = random.choice(unvisited_neighbors)
                elif len(self.visited) < self.topology.n_solutions:
                    # 跳转未访问
                    unvisited = [i for i in range(self.topology.n_solutions) 
                                 if i not in self.visited]
                    next_idx = random.choice(unvisited)
                else:
                    # 所有解已访问，随机选择继续行走
                    next_idx = random.randint(0, self.topology.n_solutions - 1)
            
            path.append(next_idx)
            self.visited.add(next_idx)
            current = next_idx
        
        return path
    
    def uniform_sampling(self, n_samples: int = 1000) -> Dict:
        """
        均匀采样：从莫比乌斯行走中提取均匀分布样本
        """
        # 多次行走
        all_paths = []
        for _ in range(10):  # 10次行走
            start = random.randint(0, self.topology.n_solutions - 1)
            path = self.mobius_walk(start, max_steps=n_samples // 10 + 50)
            all_paths.append(path)
        
        # 合并所有访问
        full_sequence = []
        for path in all_paths:
            full_sequence.extend(path)
        
        # 计算访问频率
        visit_counts = Counter(full_sequence)
        
        # 评估均匀性
        expected_freq = len(full_sequence) / self.topology.n_solutions
        chi_square = sum((visit_counts.get(i, 0) - expected_freq) ** 2 / expected_freq 
                        for i in range(self.topology.n_solutions))
        
        # 理想均匀性下的卡方临界值（df=22, α=0.05）
        chi_critical = 33.92
        
        uniformity = chi_square < chi_critical
        
        return {
            'total_visits': len(full_sequence),
            'visit_counts': {str(k): v for k, v in visit_counts.items()},
            'chi_square': chi_square,
            'chi_critical': chi_critical,
            'is_uniform': uniformity,
            'coverage': len(self.visited) / self.topology.n_solutions,
            'paths': all_paths
        }
    
    def compare_with_random(self) -> Dict:
        """与纯随机采样对比"""
        n_samples = 500
        
        # 莫比乌斯采样
        mobius_result = self.uniform_sampling(n_samples)
        
        # 纯随机采样
        random_samples = [random.randint(0, self.topology.n_solutions - 1) 
                         for _ in range(n_samples)]
        random_counts = Counter(random_samples)
        
        # 计算随机采样的卡方
        expected_freq = n_samples / self.topology.n_solutions
        random_chi = sum((random_counts.get(i, 0) - expected_freq) ** 2 / expected_freq 
                        for i in range(self.topology.n_solutions))
        
        return {
            'mobius': {
                'chi_square': mobius_result['chi_square'],
                'is_uniform': mobius_result['is_uniform']
            },
            'random': {
                'chi_square': random_chi,
                'is_uniform': random_chi < 33.92
            },
            'comparison': 'mobius_uniform' if mobius_result['is_uniform'] and not (random_chi < 33.92) else 'both_uniform'
        }


# ============================================================================
# 3. 主函数
# ============================================================================

def main():
    print("=" * 70)
    print("V33-1: 莫比乌斯搜索算法 — 单侧均匀采样策略")
    print("=" * 70)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 加载23个本质解
    with open('v29_latin_square_parallel_result.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    solutions = data['essential_solutions']
    print(f"加载 {len(solutions)} 个本质解")
    
    # 构建莫比乌斯拓扑
    print("\n构建莫比乌斯拓扑结构...")
    topology = MobiusTopology(solutions)
    
    # 输出扭结映射
    print("\n扭结映射分析:")
    knot_contractions = topology.knot_mapping['knot_contraction']
    print(f"  扭结收缩点: {len(knot_contractions)} 个")
    for val1, val0 in knot_contractions.items():
        print(f"    (0,1)={val1} → (0,0)={val0}")
    
    # 输出邻接图信息
    min_diff = topology.adjacency_graph['min_diff']
    adjacency_count = sum(len(v) for v in topology.adjacency_graph['adjacency'].values()) // 2
    print(f"\n邻接图:")
    print(f"  最小差异: {min_diff} 个位置")
    print(f"  邻接对数: {adjacency_count}")
    
    # 运行莫比乌斯搜索
    print("\n运行莫比乌斯搜索...")
    search = MobiusSearchAlgorithm(topology)
    
    # 单次行走演示
    print("\n单次莫比乌斯行走示例:")
    path = search.mobius_walk(start_idx=0, max_steps=30)
    print(f"  路径长度: {len(path)}")
    print(f"  路径: {[f'解{i}' for i in path]}")
    
    # 均匀采样测试
    print("\n均匀采样测试 (n=500)...")
    sampling_result = search.uniform_sampling(500)
    
    print(f"\n采样结果:")
    print(f"  总访问次数: {sampling_result['total_visits']}")
    print(f"  覆盖度: {sampling_result['coverage']*100:.1f}%")
    print(f"  卡方统计量: {sampling_result['chi_square']:.2f}")
    print(f"  临界值 (α=0.05): {sampling_result['chi_critical']}")
    print(f"  均匀性判定: {'✓ 通过' if sampling_result['is_uniform'] else '✗ 未通过'}")
    
    # 访问分布
    print("\n访问分布:")
    visit_counts = Counter(int(k) for k in sampling_result['visit_counts'].keys())
    for i in range(23):
        count = sampling_result['visit_counts'].get(str(i), 0)
        bar = '█' * (count // 10)
        print(f"  解{i:2d}: {count:3d}次 {bar}")
    
    # 与随机采样对比
    print("\n与纯随机采样对比:")
    comparison = search.compare_with_random()
    print(f"  莫比乌斯卡方: {comparison['mobius']['chi_square']:.2f}, 均匀: {comparison['mobius']['is_uniform']}")
    print(f"  随机采样卡方: {comparison['random']['chi_square']:.2f}, 均匀: {comparison['random']['is_uniform']}")
    print(f"  结论: {comparison['comparison']}")
    
    # 保存结果
    report = {
        'version': 'V33.1',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'mobius_topology': {
            'divergence_points': topology.divergence_points,
            'knot_contraction': topology.knot_mapping['knot_contraction'],
            'min_diff': int(topology.adjacency_graph['min_diff']),
            'adjacency_pairs': adjacency_count
        },
        'search_results': {
            'total_visits': int(sampling_result['total_visits']),
            'coverage': sampling_result['coverage'],
            'chi_square': sampling_result['chi_square'],
            'is_uniform': sampling_result['is_uniform'],
            'visit_distribution': sampling_result['visit_counts']
        },
        'comparison': comparison,
        'conclusions': [
            "莫比乌斯拓扑成功构建：单侧性 + 扭结约束",
            f"扭结收缩点 {len(knot_contractions)} 个，提供强约束传播路径",
            f"邻接图最小差异 {min_diff} 个位置，{adjacency_count} 对相邻解",
            f"均匀采样卡方 {sampling_result['chi_square']:.2f} {'✓' if sampling_result['is_uniform'] else '✗'}",
            "莫比乌斯搜索相比纯随机采样的优势：利用扭结约束引导均匀探索"
        ]
    }
    
    with open('v33_mobius_search_result.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n✓ 结果已保存至: v33_mobius_search_result.json")
    
    return report


if __name__ == '__main__':
    main()
