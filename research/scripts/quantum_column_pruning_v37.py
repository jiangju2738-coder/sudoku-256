#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 量子坍缩 + 列冲突排列交换剪枝 + 未知行相容性分析 V37
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

核心功能：
1. 列冲突排列交换剪枝 — 当检测到列AllDifferent冲突时，
   通过交换行排列来剪枝搜索空间，避免无效搜索
2. 量子坍缩状态更新 — 基于约束传播和冲突检测，
   更新每行的量子态（SUPERPOSITION → PARTIAL_COLLAPSE → COLLAPSED）
3. 未知行相容性分析 — 对所有未知行（非固定行）进行两两相容性检查，
   生成相容性矩阵和约束图

作者: Jualius + AI Assistant
日期: 2026-05-17
版本: V37.0
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Iterator
from enum import Enum
from collections import defaultdict
import json
import time
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram
import matplotlib.pyplot as plt


# ======================== 常量定义 ========================

GRID_SIZE = 16
BOX_SIZE = 4
FUMMEL_ROWS = {2, 3, 8, 15}  # C, D, I, P 行（完全固定）

# 量子态枚举
class QuantumState(Enum):
    SUPERPOSITION = "superposition"      # 叠加态：未确定
    PARTIAL_COLLAPSE = "partial_collapse"  # 部分坍缩：部分值确定
    COLLAPSED = "collapsed"             # 坍缩态：完全确定
    CONFLICT = "conflict"               # 冲突态：不可满足
    FILTERED = "filtered"               # 过滤态：排列已被过滤


# ======================== 数据结构 ========================

@dataclass
class ColumnConflictRecord:
    """列冲突记录"""
    col_idx: int
    conflict_values: Dict[int, List[Tuple[int, int]]]  # value -> [(row, perm_idx), ...]
    attempted_swaps: List[Tuple[int, int, int, int]]  # (row1, perm1, row2, perm2)
    success_count: int = 0
    failure_count: int = 0


@dataclass
class RowQuantumState:
    """行量子态"""
    row_idx: int
    state: QuantumState
    permutations: List[Tuple[int, ...]]  # 当前有效的排列集合
    collapsed_values: Dict[int, int]  # 已确定的列->值映射
    collapse_probability: float = 1.0  # 坍缩概率
    entropy: float = 0.0  # 排列熵
    compatibility_score: float = 1.0  # 与其他行的相容性得分


@dataclass
class CompatibilityMatrix:
    """行相容性矩阵"""
    matrix: np.ndarray  # (16, 16) 对称矩阵
    row_labels: List[str]
    constraint_edges: List[Tuple[int, int, str]]  # (row_i, row_j, constraint_type)
    
    def get_compatibility(self, row_i: int, row_j: int) -> float:
        return self.matrix[row_i, row_j]
    
    def get_incompatible_pairs(self, threshold: float = 0.0) -> List[Tuple[int, int]]:
        """获取不相容的行对"""
        pairs = []
        for i in range(len(self.row_labels)):
            for j in range(i + 1, len(self.row_labels)):
                if self.matrix[i, j] < threshold:
                    pairs.append((i, j))
        return pairs


@dataclass
class PruningResult:
    """剪枝结果"""
    total_swaps_attempted: int
    successful_swaps: int
    columns_resolved: int
    remaining_conflicts: int
    search_space_reduction: float  # 搜索空间缩减比例
    timestamp: float


# ======================== 列冲突排列交换剪枝器 ========================

class ColumnConflictPruner:
    """列冲突排列交换剪枝器
    
    核心算法：
    1. 检测列冲突：检查每列的AllDifferent约束
    2. 冲突定位：找出导致冲突的行-排列组合
    3. 交换剪枝：尝试交换不同行的排列组合
    4. 记忆学习：记录成功/失败的交换模式
    """
    
    def __init__(self, permutations: List[List[Tuple[int, ...]]]):
        self.permutations = permutations  # 每行的排列列表
        self.conflict_records: Dict[int, ColumnConflictRecord] = {}
        self.success_patterns: Dict[Tuple[int, int], int] = defaultdict(int)
        self.failure_patterns: Dict[Tuple[int, int], int] = defaultdict(int)
        
    def detect_column_conflicts(self, grid: List[List[int]]) -> Dict[int, List[int]]:
        """检测所有列冲突
        
        返回: {col_idx: [conflicting_values, ...]}
        """
        conflicts = {}
        
        for c in range(GRID_SIZE):
            col_values = [grid[r][c] for r in range(GRID_SIZE)]
            value_to_rows = defaultdict(list)
            for r, v in enumerate(col_values):
                value_to_rows[v].append(r)
            
            # 找出重复值
            conflicting = []
            for v, rows in value_to_rows.items():
                if len(rows) > 1:
                    conflicting.append(v)
            
            if conflicting:
                conflicts[c] = conflicting
        
        return conflicts
    
    def find_conflict_sources(self, grid: List[List[int]], 
                              col_idx: int, 
                              conflict_values: List[int]) -> Dict[int, List[Tuple[int, int]]]:
        """找出冲突来源：哪个行的哪个排列导致了冲突
        
        返回: {value: [(row_idx, perm_idx), ...]}
        """
        sources = defaultdict(list)
        
        for v in conflict_values:
            for r in range(GRID_SIZE):
                if grid[r][col_idx] == v:
                    # 找到该行使用的排列索引
                    row_perm = tuple(grid[r])
                    for perm_idx, perm in enumerate(self.permutations[r]):
                        if perm == row_perm:
                            sources[v].append((r, perm_idx))
                            break
        
        return dict(sources)
    
    def attempt_swap(self, grid: List[List[int]], 
                     col_idx: int,
                     source_a: Tuple[int, int],  # (row, perm_idx)
                     source_b: Tuple[int, int]) -> Optional[List[List[int]]]:
        """尝试交换两个行的排列
        
        Args:
            grid: 当前网格
            col_idx: 冲突列
            source_a: 第一个冲突来源 (row_a, perm_idx_a)
            source_b: 第二个冲突来源 (row_b, perm_idx_b)
            
        Returns:
            交换后的新网格，如果交换无效则返回None
        """
        row_a, perm_idx_a = source_a
        row_b, perm_idx_b = source_b
        
        # 检查交换可行性
        if row_a == row_b or perm_idx_a == perm_idx_b:
            return None
        
        # 创建新网格
        new_grid = [row.copy() for row in grid]
        
        # 执行交换
        new_grid[row_a] = list(self.permutations[row_a][perm_idx_b])
        new_grid[row_b] = list(self.permutations[row_b][perm_idx_a])
        
        # 验证交换后列冲突是否缓解
        new_conflicts = self.detect_column_conflicts(new_grid)
        
        # 检查该列的冲突是否减少
        old_conflict_count = len(grid[row_a][col_idx] for r in range(GRID_SIZE) 
                                 if grid[r][col_idx] == grid[row_a][col_idx])
        new_conflict_count = len(new_grid[r][col_idx] for r in range(GRID_SIZE) 
                                 if new_grid[r][col_idx] == new_grid[row_a][col_idx])
        
        if new_conflict_count < old_conflict_count:
            return new_grid
        
        return None
    
    def prune_with_exchange(self, grid: List[List[int]], 
                            max_swaps: int = 100,
                            verbose: bool = True) -> Tuple[List[List[int]], PruningResult]:
        """执行列冲突排列交换剪枝
        
        算法流程：
        1. 检测所有列冲突
        2. 对每个冲突列，找出冲突来源
        3. 尝试交换不同行的排列
        4. 接受能减少冲突的交换
        5. 记忆成功/失败模式
        
        Returns:
            (优化后的网格, 剪枝结果)
        """
        start_time = time.time()
        total_swaps = 0
        successful_swaps = 0
        columns_resolved = set()
        
        current_grid = [row.copy() for row in grid]
        
        for iteration in range(max_swaps):
            conflicts = self.detect_column_conflicts(current_grid)
            
            if not conflicts:
                break
            
            # 选择冲突最严重的列
            worst_col = max(conflicts.keys(), 
                           key=lambda c: len(conflicts[c]))
            conflict_values = conflicts[worst_col]
            
            # 找出冲突来源
            sources = self.find_conflict_sources(current_grid, worst_col, conflict_values)
            
            # 尝试交换
            source_list = []
            for v, v_sources in sources.items():
                source_list.extend(v_sources)
            
            swapped = False
            for i in range(len(source_list)):
                for j in range(i + 1, len(source_list)):
                    new_grid = self.attempt_swap(
                        current_grid, worst_col, source_list[i], source_list[j]
                    )
                    
                    if new_grid is not None:
                        # 记录成功模式
                        pattern = (source_list[i][0], source_list[j][0])
                        self.success_patterns[pattern] += 1
                        
                        current_grid = new_grid
                        successful_swaps += 1
                        total_swaps += 1
                        swapped = True
                        
                        # 检查该列是否已解决
                        new_conflicts = self.detect_column_conflicts(current_grid)
                        if worst_col not in new_conflicts:
                            columns_resolved.add(worst_col)
                        
                        break
                
                if swapped:
                    break
            
            if not swapped:
                # 记录失败模式
                for i in range(len(source_list)):
                    for j in range(i + 1, len(source_list)):
                        pattern = (source_list[i][0], source_list[j][0])
                        self.failure_patterns[pattern] += 1
                
                total_swaps += 1
        
        # 计算搜索空间缩减
        remaining_conflicts = len(self.detect_column_conflicts(current_grid))
        initial_conflicts = sum(len(v) for v in self.detect_column_conflicts(grid).values())
        space_reduction = 1.0 - (remaining_conflicts / max(initial_conflicts, 1))
        
        result = PruningResult(
            total_swaps_attempted=total_swaps,
            successful_swaps=successful_swaps,
            columns_resolved=len(columns_resolved),
            remaining_conflicts=remaining_conflicts,
            search_space_reduction=space_reduction,
            timestamp=time.time()
        )
        
        if verbose:
            print(f"  [列冲突剪枝] 尝试 {total_swaps} 次交换, 成功 {successful_swaps} 次")
            print(f"             解决 {len(columns_resolved)} 个冲突列, 剩余 {remaining_conflicts} 个冲突")
            print(f"             搜索空间缩减: {space_reduction:.2%}")
        
        return current_grid, result
    
    def get_exchange_probability(self, row_i: int, row_j: int) -> float:
        """计算两行交换的成功概率"""
        success = self.success_patterns.get((row_i, row_j), 0)
        failure = self.failure_patterns.get((row_i, row_j), 0)
        total = success + failure
        
        if total == 0:
            return 0.5  # 先验概率
        
        return success / total


# ======================== 量子坍缩状态管理器 ========================

class QuantumCollapseManager:
    """量子坍缩状态管理器
    
    量子态定义：
    - SUPERPOSITION: 叠加态，所有排列都可能
    - PARTIAL_COLLAPSE: 部分坍缩，部分值已确定
    - COLLAPSED: 坍缩态，完全确定
    - CONFLICT: 冲突态，不可满足
    - FILTERED: 过滤态，排列集合被约束过滤
    
    坍缩触发条件：
    1. 锚点固定 → 直接COLLAPSED
    2. 排列过滤至1个 → PARTIAL_COLLAPSE → COLLAPSED
    3. 冲突检测 → CONFLICT
    4. 约束传播 → 更新其他行的量子态
    """
    
    def __init__(self, num_rows: int = GRID_SIZE):
        self.row_states: Dict[int, RowQuantumState] = {}
        self.collapse_history: List[Dict] = []
        self.global_state = QuantumState.SUPERPOSITION
        
    def initialize(self, 
                   anchors: Dict[Tuple[int, int], int],
                   permutations: List[List[Tuple[int, ...]]]) -> None:
        """初始化所有行的量子态"""
        
        for r in range(GRID_SIZE):
            # 检查是否完全固定
            row_anchors = {c: v for (row, c), v in anchors.items() if row == r}
            
            if len(row_anchors) == GRID_SIZE:
                # 完全固定 → COLLAPSED
                state = QuantumState.COLLAPSED
                collapsed_values = row_anchors
                perm_list = []
            elif row_anchors:
                # 部分固定 → PARTIAL_COLLAPSE
                state = QuantumState.PARTIAL_COLLAPSE
                collapsed_values = row_anchors
                # 过滤排列
                perm_list = self._filter_permutations(
                    permutations[r], row_anchors
                )
            else:
                # 无锚点 → SUPERPOSITION
                state = QuantumState.SUPERPOSITION
                collapsed_values = {}
                perm_list = permutations[r]
            
            # 计算熵
            entropy = self._compute_permutation_entropy(perm_list)
            
            self.row_states[r] = RowQuantumState(
                row_idx=r,
                state=state,
                permutations=perm_list,
                collapsed_values=collapsed_values,
                collapse_probability=1.0 if state == QuantumState.COLLAPSED else 0.0,
                entropy=entropy
            )
    
    def _filter_permutations(self, 
                             permutations: List[Tuple[int, ...]],
                             fixed_values: Dict[int, int]) -> List[Tuple[int, ...]]:
        """根据固定值过滤排列"""
        filtered = []
        for perm in permutations:
            valid = True
            for col, val in fixed_values.items():
                if perm[col] != val:
                    valid = False
                    break
            if valid:
                filtered.append(perm)
        return filtered
    
    def _compute_permutation_entropy(self, permutations: List[Tuple[int, ...]]) -> float:
        """计算排列集合的熵（不确定性度量）"""
        n = len(permutations)
        if n <= 1:
            return 0.0
        
        # 计算每个位置的熵
        total_entropy = 0.0
        for c in range(GRID_SIZE):
            value_counts = defaultdict(int)
            for perm in permutations:
                value_counts[perm[c]] += 1
            
            # Shannon entropy
            for count in value_counts.values():
                p = count / n
                if p > 0:
                    total_entropy -= p * np.log2(p)
        
        return total_entropy / GRID_SIZE
    
    def update_quantum_state(self, 
                             row_idx: int,
                             new_permutations: List[Tuple[int, ...]],
                             new_collapsed: Optional[Dict[int, int]] = None) -> QuantumState:
        """更新某行的量子态
        
        坍缩规则：
        1. permutations -> 1: COLLAPSED
        2. permutations -> 0: CONFLICT
        3. new_collapsed 增加: PARTIAL_COLLAPSE → COLLAPSED
        """
        if row_idx not in self.row_states:
            return QuantumState.SUPERPOSITION
        
        current = self.row_states[row_idx]
        
        # 检查冲突
        if len(new_permutations) == 0:
            new_state = QuantumState.CONFLICT
        elif len(new_permutations) == 1:
            new_state = QuantumState.COLLAPSED
        elif new_collapsed and len(new_collapsed) >= GRID_SIZE:
            new_state = QuantumState.COLLAPSED
        elif new_collapsed and len(new_collapsed) > len(current.collapsed_values):
            new_state = QuantumState.PARTIAL_COLLAPSE
        elif len(new_permutations) < len(current.permutations):
            new_state = QuantumState.FILTERED
        else:
            new_state = current.state
        
        # 更新状态
        old_state = current.state
        current.state = new_state
        current.permutations = new_permutations
        if new_collapsed is not None:
            current.collapsed_values = new_collapsed
        current.entropy = self._compute_permutation_entropy(new_permutations)
        current.collapse_probability = (
            1.0 if new_state == QuantumState.COLLAPSED 
            else 0.5 if new_state == QuantumState.PARTIAL_COLLAPSE
            else 0.0
        )
        
        # 记录坍缩事件
        if new_state != old_state:
            self.collapse_history.append({
                'row': row_idx,
                'old_state': old_state.value,
                'new_state': new_state.value,
                'permutations_count': len(new_permutations),
                'timestamp': time.time()
            })
            
            # 更新全局状态
            self._update_global_state()
        
        return new_state
    
    def _update_global_state(self) -> None:
        """根据各行状态更新全局量子态"""
        states = [s.state for s in self.row_states.values()]
        
        if all(s == QuantumState.COLLAPSED for s in states):
            self.global_state = QuantumState.COLLAPSED
        elif any(s == QuantumState.CONFLICT for s in states):
            self.global_state = QuantumState.CONFLICT
        elif any(s in [QuantumState.COLLAPSED, QuantumState.PARTIAL_COLLAPSE] for s in states):
            self.global_state = QuantumState.PARTIAL_COLLAPSE
        else:
            self.global_state = QuantumState.SUPERPOSITION
    
    def propagate_collapse(self, 
                          row_idx: int,
                          col_idx: int,
                          value: int) -> List[Tuple[int, QuantumState]]:
        """传播坍缩：当某行某列确定值后，更新其他行的量子态
        
        约束传播：
        - 列AllDifferent：其他行在该列不能取该值
        - 更新其他行的排列集合
        """
        updated_rows = []
        
        for other_row in range(GRID_SIZE):
            if other_row == row_idx:
                continue
            
            other = self.row_states[other_row]
            
            # 过滤掉在该列取值为value的排列
            new_perms = [
                perm for perm in other.permutations
                if perm[col_idx] != value
            ]
            
            old_count = len(other.permutations)
            new_state = self.update_quantum_state(other_row, new_perms)
            
            if old_count != len(new_perms):
                updated_rows.append((other_row, new_state))
        
        return updated_rows
    
    def get_quantum_summary(self) -> Dict:
        """获取量子态汇总"""
        state_counts = defaultdict(int)
        for state in self.row_states.values():
            state_counts[state.state.value] += 1
        
        return {
            'global_state': self.global_state.value,
            'row_states': dict(state_counts),
            'total_collapse_events': len(self.collapse_history),
            'collapsed_rows': sum(1 for s in self.row_states.values() 
                                 if s.state == QuantumState.COLLAPSED),
            'conflict_rows': sum(1 for s in self.row_states.values() 
                                if s.state == QuantumState.CONFLICT),
            'average_entropy': np.mean([s.entropy for s in self.row_states.values()])
        }


# ======================== 未知行相容性分析器 ========================

class CompatibilityAnalyzer:
    """未知行相容性分析器
    
    分析所有未知行（非固定行）之间的相容性：
    1. 计算两两相容性得分
    2. 生成相容性矩阵
    3. 构建约束图
    4. 识别不相容行对
    5. 聚类分析
    """
    
    def __init__(self, permutations: List[List[Tuple[int, ...]]],
                 anchors: Dict[Tuple[int, int], int]):
        self.permutations = permutations
        self.anchors = anchors
        self.compatibility_matrix: Optional[CompatibilityMatrix] = None
        
    def get_unknown_rows(self) -> List[int]:
        """获取所有未知行（非完全固定的行）"""
        unknown = []
        for r in range(GRID_SIZE):
            row_anchors = sum(1 for (row, c) in self.anchors.keys() if row == r)
            if row_anchors < GRID_SIZE:
                unknown.append(r)
        return unknown
    
    def compute_pairwise_compatibility(self, 
                                       row_i: int,
                                       row_j: int) -> float:
        """计算两行之间的相容性得分
        
        相容性定义：
        - 基于排列集合的交集大小
        - 基于列值冲突的概率
        - 基于约束图的边权重
        
        得分范围: [0, 1]，1表示完全相容，0表示完全不相容
        """
        perms_i = self.permutations[row_i]
        perms_j = self.permutations[row_j]
        
        if not perms_i or not perms_j:
            return 0.0
        
        # 方法1：基于列冲突的概率
        conflict_probability = 0.0
        for c in range(GRID_SIZE):
            values_i = set(perm[c] for perm in perms_i)
            values_j = set(perm[c] for perm in perms_j)
            
            # 计算重叠比例
            overlap = len(values_i & values_j)
            total = len(values_i | values_j)
            
            if total > 0:
                conflict_probability += overlap / total
        
        conflict_probability /= GRID_SIZE
        
        # 方法2：基于排列交集
        # 检查是否存在一对排列完全不相冲突
        compatible_pairs = 0
        total_pairs = len(perms_i) * len(perms_j)
        
        if total_pairs > 0:
            # 采样检查（避免O(n²)）
            sample_size = min(100, total_pairs)
            sampled = 0
            for perm_i in perms_i[:10]:
                for perm_j in perms_j[:10]:
                    if sampled >= sample_size:
                        break
                    # 检查列冲突
                    has_conflict = False
                    for c in range(GRID_SIZE):
                        if perm_i[c] == perm_j[c]:
                            has_conflict = True
                            break
                    if not has_conflict:
                        compatible_pairs += 1
                    sampled += 1
            
            compatibility_ratio = compatible_pairs / max(sampled, 1)
        else:
            compatibility_ratio = 0.0
        
        # 综合得分
        compatibility = (1.0 - conflict_probability) * 0.4 + compatibility_ratio * 0.6
        
        return max(0.0, min(1.0, compatibility))
    
    def analyze_all_unknown_rows(self) -> CompatibilityMatrix:
        """分析所有未知行的相容性"""
        unknown_rows = self.get_unknown_rows()
        n = len(unknown_rows)
        
        if n == 0:
            # 所有行都固定
            matrix = np.eye(GRID_SIZE)
            labels = [f"Row {r}" for r in range(GRID_SIZE)]
            return CompatibilityMatrix(
                matrix=matrix,
                row_labels=labels,
                constraint_edges=[]
            )
        
        # 计算相容性矩阵
        compat_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        constraint_edges = []
        
        for i, row_i in enumerate(unknown_rows):
            for j, row_j in enumerate(unknown_rows):
                if i == j:
                    compat_matrix[row_i, row_j] = 1.0
                elif i < j:
                    score = self.compute_pairwise_compatibility(row_i, row_j)
                    compat_matrix[row_i, row_j] = score
                    compat_matrix[row_j, row_i] = score
                    
                    if score < 0.3:
                        constraint_edges.append((row_i, row_j, 'low_compatibility'))
                    elif score < 0.5:
                        constraint_edges.append((row_i, row_j, 'moderate'))
        
        # 固定行的相容性为1.0（已确定）
        for r in range(GRID_SIZE):
            if r not in unknown_rows:
                compat_matrix[r, r] = 1.0
                for c in range(GRID_SIZE):
                    if c != r:
                        compat_matrix[r, c] = 0.0  # 固定行与其他行的关系待定
        
        labels = [f"Row {chr(65 + r)}" for r in range(GRID_SIZE)]
        
        self.compatibility_matrix = CompatibilityMatrix(
            matrix=compat_matrix,
            row_labels=labels,
            constraint_edges=constraint_edges
        )
        
        return self.compatibility_matrix
    
    def visualize_compatibility(self, 
                                output_path: str = "compatibility_matrix.png") -> str:
        """可视化相容性矩阵"""
        if self.compatibility_matrix is None:
            self.analyze_all_unknown_rows()
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # 热力图
        im = axes[0].imshow(self.compatibility_matrix.matrix, 
                           cmap='RdYlGn', vmin=0, vmax=1)
        axes[0].set_xticks(range(GRID_SIZE))
        axes[0].set_yticks(range(GRID_SIZE))
        axes[0].set_xticklabels([f"{chr(65+i)}" for i in range(GRID_SIZE)])
        axes[0].set_yticklabels([f"{chr(65+i)}" for i in range(GRID_SIZE)])
        axes[0].set_title('行相容性矩阵')
        plt.colorbar(im, ax=axes[0], shrink=0.8)
        
        # 添加不相容对标记
        incompatible = self.compatibility_matrix.get_incompatible_pairs(0.3)
        for r1, r2 in incompatible:
            axes[0].plot([r1, r2], [r1, r2], 'rx', markersize=12, markeredgewidth=2)
        
        # 约束图（网络图）
        import networkx as nx
        G = nx.Graph()
        
        for r in range(GRID_SIZE):
            G.add_node(r, label=f"{chr(65+r)}")
        
        for r1, r2, edge_type in self.compatibility_matrix.constraint_edges:
            weight = 1.0 if edge_type == 'low_compatibility' else 0.5
            G.add_edge(r1, r2, weight=weight, type=edge_type)
        
        pos = nx.circular_layout(G)
        node_colors = ['red' if G.degree(n) > 3 else 'lightblue' for n in G.nodes()]
        
        nx.draw_networkx_nodes(G, pos, ax=axes[1], node_color=node_colors, 
                              node_size=500, alpha=0.8)
        nx.draw_networkx_labels(G, pos, ax=axes[1], 
                               labels={n: f"{chr(65+n)}" for n in G.nodes()},
                               font_size=10)
        nx.draw_networkx_edges(G, pos, ax=axes[1], alpha=0.5, width=1.5)
        
        axes[1].set_title('约束图（红节点=高冲突度）')
        axes[1].axis('off')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_compatibility_report(self) -> Dict:
        """生成相容性分析报告"""
        if self.compatibility_matrix is None:
            self.analyze_all_unknown_rows()
        
        unknown_rows = self.get_unknown_rows()
        
        # 统计不相容对
        incompatible_pairs = self.compatibility_matrix.get_incompatible_pairs(0.3)
        moderate_pairs = self.compatibility_matrix.get_incompatible_pairs(0.5)
        moderate_pairs = [p for p in moderate_pairs if p not in incompatible_pairs]
        
        # 计算平均相容性
        avg_compat = 0.0
        count = 0
        for i in range(GRID_SIZE):
            for j in range(i + 1, GRID_SIZE):
                if i in unknown_rows or j in unknown_rows:
                    avg_compat += self.compatibility_matrix.matrix[i, j]
                    count += 1
        
        avg_compat /= max(count, 1)
        
        return {
            'unknown_rows': unknown_rows,
            'unknown_row_count': len(unknown_rows),
            'incompatible_pairs': incompatible_pairs,
            'incompatible_count': len(incompatible_pairs),
            'moderate_pairs': moderate_pairs,
            'moderate_count': len(moderate_pairs),
            'average_compatibility': avg_compat,
            'constraint_edges': self.compatibility_matrix.constraint_edges,
            'recommendations': self._generate_recommendations(incompatible_pairs)
        }
    
    def _generate_recommendations(self, incompatible_pairs: List[Tuple[int, int]]) -> List[str]:
        """生成基于相容性分析的建议"""
        recommendations = []
        
        if len(incompatible_pairs) == 0:
            recommendations.append("所有未知行均相容，搜索空间连通性良好")
        elif len(incompatible_pairs) <= 3:
            recommendations.append(f"发现 {len(incompatible_pairs)} 对不相容行，建议优先处理这些约束")
        else:
            recommendations.append(f"发现 {len(incompatible_pairs)} 对不相容行，搜索空间可能存在多个孤立区域")
        
        # 分析冲突热点
        conflict_counts = defaultdict(int)
        for r1, r2 in incompatible_pairs:
            conflict_counts[r1] += 1
            conflict_counts[r2] += 1
        
        hotspots = sorted(conflict_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        if hotspots:
            hotspot_rows = [f"Row {chr(65+r)}" for r, _ in hotspots]
            recommendations.append(f"冲突热点: {', '.join(hotspot_rows)}")
        
        return recommendations


# ======================== 融合求解器 ========================

class QuantumFusionSolver:
    """量子融合求解器
    
    整合三大功能：
    1. 列冲突排列交换剪枝
    2. 量子坍缩状态更新
    3. 未知行相容性分析
    """
    
    def __init__(self, 
                 anchors: Dict[Tuple[int, int], int],
                 permutations: List[List[Tuple[int, ...]]]):
        self.anchors = anchors
        self.permutations = permutations
        
        # 初始化各模块
        self.column_pruner = ColumnConflictPruner(permutations)
        self.quantum_manager = QuantumCollapseManager()
        self.compatibility_analyzer = CompatibilityAnalyzer(permutations, anchors)
        
        # 状态
        self.current_grid: Optional[List[List[int]]] = None
        self.solve_history: List[Dict] = []
    
    def initialize(self) -> None:
        """初始化求解器"""
        # 初始化量子态
        self.quantum_manager.initialize(self.anchors, self.permutations)
        
        # 初始网格：从每个行的第一个排列开始
        self.current_grid = [
            list(perms[0]) if perms else list(range(1, GRID_SIZE + 1))
            for perms in self.permutations
        ]
        
        print("=" * 70)
        print("量子融合求解器初始化")
        print("=" * 70)
        
        # 打印初始量子态
        summary = self.quantum_manager.get_quantum_summary()
        print(f"  全局量子态: {summary['global_state']}")
        print(f"  行状态分布: {dict(summary['row_states'])}")
        print(f"  平均熵: {summary['average_entropy']:.4f}")
        
        # 相容性分析
        compat_report = self.compatibility_analyzer.analyze_all_unknown_rows()
        print(f"  未知行数: {len(self.compatibility_analyzer.get_unknown_rows())}")
        print(f"  不相容对: {len(compat_report.get_incompatible_pairs())}")
    
    def solve_step(self, verbose: bool = True) -> Dict:
        """执行一步求解
        
        步骤：
        1. 检测列冲突
        2. 执行排列交换剪枝
        3. 更新量子坍缩状态
        4. 传播约束
        5. 检查收敛
        """
        if self.current_grid is None:
            raise ValueError("求解器未初始化，请先调用 initialize()")
        
        step_result = {
            'step': len(self.solve_history) + 1,
            'timestamp': time.time(),
            'actions': []
        }
        
        # 1. 检测列冲突
        conflicts = self.column_pruner.detect_column_conflicts(self.current_grid)
        step_result['column_conflicts'] = len(conflicts)
        
        if verbose and conflicts:
            print(f"\n  [步骤 {step_result['step']}] 检测到 {len(conflicts)} 个列冲突")
        
        # 2. 执行排列交换剪枝
        if conflicts:
            self.current_grid, prune_result = self.column_pruner.prune_with_exchange(
                self.current_grid, max_swaps=50, verbose=verbose
            )
            step_result['pruning'] = {
                'swaps_attempted': prune_result.total_swaps_attempted,
                'swaps_successful': prune_result.successful_swaps,
                'space_reduction': prune_result.search_space_reduction
            }
            step_result['actions'].append('column_exchange_pruning')
        
        # 3. 更新量子坍缩状态
        for r in range(GRID_SIZE):
            row_anchors = {c: v for (row, c), v in self.anchors.items() if row == r}
            current_perms = self.permutations[r]
            
            # 根据当前网格选择排列
            grid_row = tuple(self.current_grid[r])
            if grid_row in current_perms:
                new_perms = [grid_row]
            else:
                new_perms = current_perms
            
            new_state = self.quantum_manager.update_quantum_state(r, new_perms, row_anchors)
            
            if new_state == QuantumState.COLLAPSED and verbose:
                print(f"    行 {chr(65+r)} 坍缩至确定态")
        
        # 4. 约束传播（对坍缩行）
        for r in range(GRID_SIZE):
            row_state = self.quantum_manager.row_states.get(r)
            if row_state and row_state.state == QuantumState.COLLAPSED:
                for c, v in row_state.collapsed_values.items():
                    propagated = self.quantum_manager.propagate_collapse(r, c, v)
                    if propagated and verbose:
                        for pr, ps in propagated:
                            print(f"    传播: 行{chr(65+pr)} → {ps.value}")
        
        # 5. 检查收敛
        global_state = self.quantum_manager.global_state
        step_result['global_state'] = global_state.value
        step_result['actions'].append('quantum_collapse_update')
        
        if global_state == QuantumState.COLLAPSED:
            step_result['converged'] = True
        elif global_state == QuantumState.CONFLICT:
            step_result['conflict'] = True
        else:
            step_result['converged'] = False
        
        self.solve_history.append(step_result)
        
        return step_result
    
    def solve(self, max_steps: int = 100, verbose: bool = True) -> Tuple[bool, List[List[int]]]:
        """执行完整求解
        
        Returns:
            (是否成功, 最终网格)
        """
        self.initialize()
        
        for step in range(max_steps):
            result = self.solve_step(verbose=(verbose and step < 10))
            
            if result.get('converged'):
                if verbose:
                    print(f"\n  ✓ 求解收敛！共 {step + 1} 步")
                return True, self.current_grid
            
            if result.get('conflict'):
                if verbose:
                    print(f"\n  ✗ 检测到冲突，求解失败")
                return False, self.current_grid
        
        if verbose:
            print(f"\n  ⚠ 达到最大步数 {max_steps}，未完全收敛")
        
        return False, self.current_grid
    
    def get_full_report(self) -> Dict:
        """获取完整分析报告"""
        compat_report = self.compatibility_analyzer.generate_compatibility_report()
        quantum_summary = self.quantum_manager.get_quantum_summary()
        
        # 将元组键转换为字符串以便JSON序列化
        success_patterns = {f"{k[0]}-{k[1]}": v for k, v in self.column_pruner.success_patterns.items()}
        failure_patterns = {f"{k[0]}-{k[1]}": v for k, v in self.column_pruner.failure_patterns.items()}
        
        return {
            'quantum_state': quantum_summary,
            'compatibility_analysis': compat_report,
            'solve_history': self.solve_history,
            'column_pruning_patterns': {
                'success': success_patterns,
                'failure': failure_patterns
            }
        }


# ======================== 主程序 ========================

def load_config(config_path: str = "sudoku_config.json") -> Tuple[
    Dict[Tuple[int, int], int],
    List[List[Tuple[int, ...]]]
]:
    """加载配置并解析锚点和排列"""
    import json
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 解析锚点（转换为0-indexed）
    anchors = {}
    for anchor in config.get('known_digits', []):
        r = anchor['row'] - 1  # 转0-indexed
        c = anchor['col'] - 1
        anchors[(r, c)] = anchor['value']
    
    # 加载排列（从JSON文件或生成）
    permutations = []
    for r in range(GRID_SIZE):
        perm_file = f"A{r+1}_permutations.json"
        try:
            with open(perm_file, 'r', encoding='utf-8') as f:
                row_perms = json.load(f)
            permutations.append([tuple(p) for p in row_perms])
        except FileNotFoundError:
            # 生成随机排列作为备用
            import random
            base = list(range(1, GRID_SIZE + 1))
            perms = set()
            while len(perms) < 100:
                perm = base.copy()
                random.shuffle(perm)
                perms.add(tuple(perm))
            permutations.append(list(perms))
    
    return anchors, permutations


def main():
    """主程序入口"""
    print("=" * 70)
    print("量子坍缩 + 列冲突排列交换剪枝 + 未知行相容性分析 V37")
    print("=" * 70)
    
    # 加载配置
    try:
        anchors, permutations = load_config()
    except FileNotFoundError:
        print("  未找到 sudoku_config.json，使用模拟数据")
        # 模拟锚点
        anchors = {
            (2, 0): 7, (2, 1): 15, (2, 2): 3, (2, 3): 9,
            (3, 0): 11, (3, 1): 4, (3, 2): 13, (3, 3): 7
        }
        # 模拟排列
        permutations = []
        for r in range(GRID_SIZE):
            import random
            base = list(range(1, GRID_SIZE + 1))
            perms = set()
            while len(perms) < 100:
                perm = base.copy()
                random.shuffle(perm)
                perms.add(tuple(perm))
            permutations.append(list(perms))
    
    # 创建求解器
    solver = QuantumFusionSolver(anchors, permutations)
    
    # 执行求解
    success, final_grid = solver.solve(max_steps=50, verbose=True)
    
    # 生成报告
    report = solver.get_full_report()
    
    # 保存报告
    with open('v37_quantum_collapse_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 可视化相容性矩阵
    compat_img = solver.compatibility_analyzer.visualize_compatibility()
    
    print("\n" + "=" * 70)
    print("分析完成")
    print("=" * 70)
    print(f"  求解状态: {'成功' if success else '未完成'}")
    print(f"  全局量子态: {report['quantum_state']['global_state']}")
    print(f"  不相容行对: {report['compatibility_analysis']['incompatible_count']}")
    print(f"  报告已保存至: v37_quantum_collapse_report.json")
    print(f"  相容性矩阵: {compat_img}")
    
    return success, final_grid


if __name__ == "__main__":
    main()
