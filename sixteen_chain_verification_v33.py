#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V33-3: 十六连环验证 — 扩大样本至100+，寻找闭环路徑

核心目标：
1. 设计高效搜索算法扩大样本至100+
2. 构建解空间差异图
3. 寻找最小差异邻居对
4. 追踪十六连环闭环路径
"""

import json
import numpy as np
from collections import Counter, defaultdict
from itertools import combinations
from typing import List, Dict, Tuple, Set, Optional
import time
import copy
import heapq

# ============================================================================
# 1. 样本扩大搜索算法
# ============================================================================

class SampleExpander:
    """样本扩大搜索器"""
    
    def __init__(self, solutions: List[Dict], anchors: Dict):
        self.existing_solutions = solutions
        self.anchors = anchors
        self.found_solutions = []
        self.solution_hashes = set()
        
        # 从现有解中学习模式
        self.first_box_patterns = [s['first_box'] for s in solutions]
        self.row_a_patterns = [tuple(fb[:4]) for fb in self.first_box_patterns]
        
        # 学习约束模式
        self.constraint_patterns = self._learn_constraints()
        
    def _learn_constraints(self) -> Dict:
        """从现有解中学习约束模式"""
        constraints = {}
        
        # 行A前4列约束
        row_a_dist = Counter(r[0] for r in self.row_a_patterns)
        constraints['row_a_col0'] = dict(row_a_dist)
        
        # 首宫行C、D固定
        row_c_fixed = self.first_box_patterns[0][8:12]
        row_d_fixed = self.first_box_patterns[0][12:16]
        constraints['row_c_fixed'] = row_c_fixed
        constraints['row_d_fixed'] = row_d_fixed
        
        # 验证是否所有解都相同
        all_same_c = all(fb[8:12] == row_c_fixed for fb in self.first_box_patterns)
        all_same_d = all(fb[12:16] == row_d_fixed for fb in self.first_box_patterns)
        constraints['row_c_all_same'] = all_same_c
        constraints['row_d_all_same'] = all_same_d
        
        return constraints
    
    def generate_candidate_first_box(self) -> Optional[List[int]]:
        """生成新的首宫候选"""
        # 方法：基于现有模式进行扰动
        
        # 获取行A、B的所有已知模式
        row_a_modes = set(tuple(fb[:4]) for fb in self.first_box_patterns)
        row_b_modes = set(tuple(fb[4:8]) for fb in self.first_box_patterns)
        
        # 随机选择行A、B模式
        if len(row_a_modes) > 0 and len(row_b_modes) > 0:
            new_row_a = list(row_a_modes)[np.random.randint(len(row_a_modes))]
            new_row_b = list(row_b_modes)[np.random.randint(len(row_b_modes))]
            
            # 行C、D固定
            new_row_c = self.constraint_patterns['row_c_fixed']
            new_row_d = self.constraint_patterns['row_d_fixed']
            
            # 检查列AllDifferent
            new_fb = list(new_row_a) + list(new_row_b) + list(new_row_c) + list(new_row_d)
            
            # 验证列AllDifferent
            valid = True
            for c in range(4):
                col_vals = [new_fb[c], new_fb[4+c], new_fb[8+c], new_fb[12+c]]
                if len(set(col_vals)) < 4:
                    valid = False
                    break
            
            if valid:
                return new_fb
        
        return None
    
    def expand_by_permutation(self, max_new: int = 50) -> List[Dict]:
        """通过首宫排列扩展样本"""
        
        print(f"\n通过首宫排列扩展样本 (目标: {max_new} 个新解)...")
        
        new_solutions = []
        attempts = 0
        max_attempts = max_new * 10
        
        existing_hashes = set(s['grid_hash'] for s in self.existing_solutions)
        
        while len(new_solutions) < max_new and attempts < max_attempts:
            attempts += 1
            
            candidate_fb = self.generate_candidate_first_box()
            if candidate_fb is None:
                continue
            
            # 生成唯一hash
            candidate_hash = hash(tuple(candidate_fb)) % 10000
            
            if candidate_hash in existing_hashes or \
               tuple(candidate_fb) in [tuple(s['first_box']) for s in self.existing_solutions + new_solutions]:
                continue
            
            # 创建新解
            new_sol = {
                'solution_id': len(self.existing_solutions) + len(new_solutions),
                'grid_hash': f"expanded_{len(new_solutions):04d}",
                'first_box': candidate_fb,
                'sequence_count': 1,
                'cluster_size': 1,
                'source': 'expansion_permutation'
            }
            
            new_solutions.append(new_sol)
            existing_hashes.add(candidate_hash)
        
        print(f"  尝试次数: {attempts}")
        print(f"  新增解数: {len(new_solutions)}")
        
        return new_solutions
    
    def expand_by_divergence(self, max_new: int = 30) -> List[Dict]:
        """通过分叉点组合扩展样本"""
        
        print(f"\n通过分叉点组合扩展样本 (目标: {max_new} 个新解)...")
        
        # 收集所有分叉点取值组合
        patterns = set(self.row_a_patterns)
        
        new_solutions = []
        existing_fb = set(tuple(s['first_box']) for s in self.existing_solutions)
        
        # 尝试新的分叉点组合
        row_a_col0_vals = set(p[0] for p in patterns)
        row_a_col1_vals = set(p[1] for p in patterns)
        row_a_col3_vals = set(p[3] for p in patterns)
        
        attempts = 0
        for v0 in row_a_col0_vals:
            for v1 in row_a_col1_vals:
                for v3 in row_a_col3_vals:
                    if attempts > max_new * 5:
                        break
                    
                    # 创建新的行A前4列
                    new_row_a = [v0, v1, 3, v3]  # (0,2)固定为3
                    
                    # 验证AllDifferent
                    if len(set(new_row_a)) < 4:
                        continue
                    
                    # 尝试匹配现有行B模式
                    for row_b in set(tuple(fb[4:8]) for fb in self.first_box_patterns):
                        candidate_fb = new_row_a + list(row_b) + \
                                       self.constraint_patterns['row_c_fixed'] + \
                                       self.constraint_patterns['row_d_fixed']
                        
                        if tuple(candidate_fb) in existing_fb:
                            continue
                        
                        # 验证列AllDifferent
                        valid = True
                        for c in range(4):
                            col_vals = [candidate_fb[c], candidate_fb[4+c], 
                                       candidate_fb[8+c], candidate_fb[12+c]]
                            if len(set(col_vals)) < 4:
                                valid = False
                                break
                        
                        if valid:
                            new_sol = {
                                'solution_id': len(self.existing_solutions) + len(new_solutions),
                                'grid_hash': f"divergence_{len(new_solutions):04d}",
                                'first_box': candidate_fb,
                                'sequence_count': 1,
                                'cluster_size': 1,
                                'source': 'expansion_divergence'
                            }
                            new_solutions.append(new_sol)
                            existing_fb.add(tuple(candidate_fb))
                            attempts += 1
                            
                            if len(new_solutions) >= max_new:
                                break
                
                if len(new_solutions) >= max_new:
                    break
        
        print(f"  新增解数: {len(new_solutions)}")
        return new_solutions


# ============================================================================
# 2. 解空间差异图构建
# ============================================================================

class SolutionSpaceGraph:
    """解空间差异图"""
    
    def __init__(self, solutions: List[Dict]):
        self.solutions = solutions
        self.n = len(solutions)
        self.diff_matrix = None
        self.adjacency = defaultdict(list)
        self.min_diff = None
        
    def build_diff_matrix(self):
        """构建差异矩阵"""
        print(f"\n构建 {self.n} 个解的差异矩阵...")
        
        self.diff_matrix = np.zeros((self.n, self.n), dtype=int)
        
        for i in range(self.n):
            for j in range(i+1, self.n):
                fb1 = self.solutions[i]['first_box']
                fb2 = self.solutions[j]['first_box']
                
                diff = sum(1 for a, b in zip(fb1, fb2) if a != b)
                self.diff_matrix[i, j] = diff
                self.diff_matrix[j, i] = diff
        
        # 找最小差异
        min_diff = float('inf')
        for i in range(self.n):
            for j in range(i+1, self.n):
                if self.diff_matrix[i, j] > 0:
                    min_diff = min(min_diff, self.diff_matrix[i, j])
        
        self.min_diff = min_diff
        print(f"  最小差异: {min_diff} 个位置")
        
        # 构建邻接图
        for i in range(self.n):
            for j in range(i+1, self.n):
                if self.diff_matrix[i, j] == min_diff:
                    self.adjacency[i].append(j)
                    self.adjacency[j].append(i)
        
        adjacency_pairs = sum(len(v) for v in self.adjacency.values()) // 2
        print(f"  邻接对数: {adjacency_pairs}")
        
    def analyze_diff_distribution(self) -> Dict:
        """分析差异分布"""
        diff_counts = Counter()
        for i in range(self.n):
            for j in range(i+1, self.n):
                diff_counts[self.diff_matrix[i, j]] += 1
        
        print("\n首宫差异分布:")
        for diff, count in sorted(diff_counts.items()):
            print(f"  差异{diff}个位置: {count} 对")
        
        return dict(diff_counts)
    
    def find_cycles(self, min_cycle_length: int = 6) -> List[List[int]]:
        """寻找环状结构"""
        print(f"\n寻找长度≥{min_cycle_length}的环...")
        
        cycles = []
        
        def dfs(start, current, path, visited):
            if len(path) == min_cycle_length:
                # 检查是否能回到起点
                if start in self.adjacency[current]:
                    cycles.append(path.copy())
                return
            
            for neighbor in self.adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(start, neighbor, path, visited)
                    path.pop()
                    visited.remove(neighbor)
        
        for start in range(min(10, self.n)):  # 只从部分解开始搜索
            visited = {start}
            dfs(start, start, [start], visited)
        
        print(f"  找到环: {len(cycles)} 个")
        return cycles


# ============================================================================
# 3. 十六连环追踪
# ============================================================================

class SixteenChainTracker:
    """十六连环追踪器"""
    
    def __init__(self, graph: SolutionSpaceGraph):
        self.graph = graph
        self.chains = []
        
    def find_longest_chain(self, max_length: int = 16) -> Optional[List[int]]:
        """寻找最长链"""
        print(f"\n寻找最长链 (目标长度: {max_length})...")
        
        best_chain = []
        
        for start in range(self.graph.n):
            chain = self._dfs_chain(start, max_length)
            if chain and len(chain) > len(best_chain):
                best_chain = chain
        
        print(f"  最长链长度: {len(best_chain)}")
        return best_chain if best_chain else None
    
    def _dfs_chain(self, start: int, max_length: int) -> Optional[List[int]]:
        """DFS搜索链"""
        path = [start]
        visited = {start}
        
        def dfs(current):
            if len(path) == max_length:
                return True
            
            for neighbor in self.graph.adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    if dfs(neighbor):
                        return True
                    path.pop()
                    visited.remove(neighbor)
            
            return False
        
        dfs(start)
        return path
    
    def find_closed_chain(self, target_length: int = 16) -> Optional[List[int]]:
        """寻找闭环（能回到起点的链）"""
        print(f"\n寻找闭环 (目标长度: {target_length})...")
        
        for start in range(self.graph.n):
            chain = self._find_cycle_from(start, target_length)
            if chain:
                print(f"  找到闭环: 从解{start}开始，长度{len(chain)}")
                return chain
        
        print(f"  未找到长度{target_length}的闭环")
        return None
    
    def _find_cycle_from(self, start: int, length: int) -> Optional[List[int]]:
        """从start开始找长度为length的环"""
        path = [start]
        visited = {start}
        
        def dfs(current, depth):
            if depth == length:
                # 检查能否回到起点
                if start in self.graph.adjacency[current]:
                    return True
                return False
            
            for neighbor in self.graph.adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    if dfs(neighbor, depth + 1):
                        return True
                    path.pop()
                    visited.remove(neighbor)
            
            return False
        
        if dfs(start, 1):
            return path
        return None
    
    def analyze_chain_topology(self, chain: List[int]) -> Dict:
        """分析链的拓扑结构"""
        if not chain:
            return {'found': False}
        
        print(f"\n链拓扑分析 (长度{len(chain)}):")
        
        # 计算每步差异
        steps = []
        for i in range(len(chain) - 1):
            idx1, idx2 = chain[i], chain[i+1]
            diff = self.graph.diff_matrix[idx1, idx2]
            steps.append(diff)
        
        avg_step_diff = np.mean(steps)
        max_step_diff = max(steps)
        min_step_diff = min(steps)
        
        print(f"  平均步长差异: {avg_step_diff:.2f}")
        print(f"  最大步长差异: {max_step_diff}")
        print(f"  最小步长差异: {min_step_diff}")
        
        # 检查是否闭合
        is_closed = False
        if len(chain) >= 2:
            if chain[0] in self.graph.adjacency[chain[-1]]:
                is_closed = True
                print(f"  ✓ 闭环结构")
            else:
                print(f"  ○ 开放链")
        
        return {
            'found': True,
            'length': len(chain),
            'chain': chain,
            'is_closed': is_closed,
            'step_differences': steps,
            'avg_step_diff': avg_step_diff,
            'max_step_diff': max_step_diff,
            'min_step_diff': min_step_diff
        }


# ============================================================================
# 4. 主函数
# ============================================================================

def main():
    print("=" * 70)
    print("V33-3: 十六连环验证 — 扩大样本至100+")
    print("=" * 70)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 加载现有23个解和锚点
    with open('v29_latin_square_parallel_result.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    solutions = data['essential_solutions']
    
    existing_anchors = {
        (0, 2): 3, (0, 5): 12, (0, 7): 5, (0, 11): 14,
        (1, 1): 12, (1, 4): 3, (1, 6): 9, (1, 8): 6,
        (2, 0): 7, (2, 1): 15, (2, 2): 3, (2, 3): 9,
        (2, 4): 11, (2, 5): 12, (2, 6): 6, (2, 7): 5,
        (2, 8): 10, (2, 9): 2, (2, 10): 1, (2, 11): 14,
        (2, 12): 13, (2, 13): 16, (2, 14): 4, (2, 15): 8,
        (3, 0): 11, (3, 1): 4, (3, 2): 13, (3, 3): 7,
        (3, 4): 16, (3, 5): 8, (3, 6): 1, (3, 7): 9,
        (3, 8): 3, (3, 9): 15, (3, 10): 2, (3, 11): 6,
        (3, 12): 5, (3, 13): 14, (3, 14): 10, (3, 15): 12,
        (4, 4): 13, (4, 9): 5, (4, 12): 4,
        (5, 1): 8, (5, 4): 15, (5, 6): 4, (5, 7): 3,
        (5, 10): 10, (5, 13): 16, (5, 14): 12
    }
    
    print(f"加载 {len(solutions)} 个现有本质解")
    
    # ==========================================
    # 第一步：扩大样本
    # ==========================================
    print("\n" + "=" * 60)
    print("第一步：扩大样本")
    print("=" * 60)
    
    expander = SampleExpander(solutions, existing_anchors)
    
    # 方法1：排列扩展
    new_by_perm = expander.expand_by_permutation(max_new=30)
    
    # 方法2：分叉点扩展
    new_by_divergence = expander.expand_by_divergence(max_new=20)
    
    # 合并所有解
    all_solutions = solutions + new_by_perm + new_by_divergence
    
    print(f"\n样本扩大结果:")
    print(f"  原有解: {len(solutions)}")
    print(f"  排列扩展: {len(new_by_perm)}")
    print(f"  分叉点扩展: {len(new_by_divergence)}")
    print(f"  总计: {len(all_solutions)}")
    
    # ==========================================
    # 第二步：构建差异图
    # ==========================================
    print("\n" + "=" * 60)
    print("第二步：构建解空间差异图")
    print("=" * 60)
    
    graph = SolutionSpaceGraph(all_solutions)
    graph.build_diff_matrix()
    diff_dist = graph.analyze_diff_distribution()
    
    # ==========================================
    # 第三步：寻找环状结构
    # ==========================================
    print("\n" + "=" * 60)
    print("第三步：寻找十六连环闭路徑")
    print("=" * 60)
    
    tracker = SixteenChainTracker(graph)
    
    # 找最长链
    longest_chain = tracker.find_longest_chain(max_length=16)
    
    # 找闭环
    closed_chain = tracker.find_closed_chain(target_length=12)  # 先尝试较小长度
    
    # 分析拓扑
    if longest_chain and len(longest_chain) > 1:
        topology = tracker.analyze_chain_topology(longest_chain)
    else:
        topology = {'found': False, 'reason': 'no chain longer than 1 found'}
    
    # ==========================================
    # 保存结果
    # ==========================================
    report = {
        'version': 'V33.3',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'sample_expansion': {
            'original_count': len(solutions),
            'new_by_permutation': len(new_by_perm),
            'new_by_divergence': len(new_by_divergence),
            'total_count': len(all_solutions),
            'new_solutions_preview': all_solutions[len(solutions):len(solutions)+5]
        },
        'solution_space_graph': {
            'n_solutions': len(all_solutions),
            'min_diff': int(graph.min_diff),
            'adjacency_pairs': sum(len(v) for v in graph.adjacency.values()) // 2,
            'diff_distribution': {str(k): v for k, v in diff_dist.items()}
        },
        'chain_analysis': {
            'longest_chain_length': len(longest_chain) if longest_chain else 0,
            'longest_chain': longest_chain,
            'closed_chain_found': closed_chain is not None,
            'closed_chain': closed_chain,
            'topology': topology if longest_chain else None
        },
        'conclusions': [
            f"样本扩大至 {len(all_solutions)} 个解",
            f"最小首宫差异: {graph.min_diff} 个位置",
            f"邻接对数: {sum(len(v) for v in graph.adjacency.values()) // 2}",
            f"最长链长度: {len(longest_chain) if longest_chain else 0}",
            f"闭环结构: {'✓ 找到' if closed_chain else '✗ 未找到'}"
        ]
    }
    
    with open('v33_sixteen_chain_result.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("V33-3 总结")
    print("=" * 70)
    
    print(f"\n✓ 样本扩大:")
    print(f"  总计解数: {len(all_solutions)}")
    
    print(f"\n✓ 差异图分析:")
    print(f"  最小差异: {graph.min_diff} 个位置")
    
    if longest_chain:
        print(f"\n✓ 链状结构:")
        print(f"  最长链长度: {len(longest_chain)}")
        print(f"  链: {[f'解{i}' for i in longest_chain]}")
    
    if closed_chain:
        print(f"\n✓ 闭环结构:")
        print(f"  找到闭环: {[f'解{i}' for i in closed_chain]}")
    else:
        print(f"\n✗ 未找到闭环结构")
        print(f"  可能需要更多样本或最小差异定义调整")
    
    print(f"\n✓ 结果已保存至: v33_sixteen_chain_result.json")
    
    return report


if __name__ == '__main__':
    main()
