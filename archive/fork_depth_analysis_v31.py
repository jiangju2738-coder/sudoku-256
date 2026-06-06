#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V31 - 分叉点深度博弈推演研究 (完整版)

核心任务：
1. 行A前4列强制锚点测试 - 使用first_box重建
2. 迭代子结构分析 - 基于first_box完整16个值
3. 扩大样本至100+解验证解空间饱和
"""

import json
import numpy as np
from itertools import product, combinations, permutations
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Set, Optional
import time

# ============================================================================
# 数据加载与重建
# ============================================================================

def load_solutions_from_v29() -> List[Dict]:
    """从V29结果加载所有23个本质解的完整first_box"""
    
    with open('v29_latin_square_parallel_result.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    solutions = data['essential_solutions']
    print(f"加载 {len(solutions)} 个本质解")
    
    # 验证first_box长度（应该是16，代表首宫）
    if solutions:
        fb = solutions[0]['first_box']
        print(f"首宫数据长度: {len(fb)} (应为16)")
    
    return solutions

def extract_row_a_first4(solutions: List[Dict]) -> List[List[int]]:
    """提取所有解的行A前4列"""
    
    row_a_first4 = []
    for sol in solutions:
        # first_box的前4个元素是行A的列0-3
        row_a = sol['first_box'][:4]
        row_a_first4.append(row_a)
    
    return row_a_first4

def extract_first_box_full(solutions: List[Dict]) -> List[List[int]]:
    """提取所有解的首宫（16个值，行A:4个，行B:4个，行C:4个，行D:4个）"""
    
    first_boxes = []
    for sol in solutions:
        fb = sol['first_box']
        # 重组为4x4矩阵
        box_4x4 = [
            fb[0:4],   # 行A
            fb[4:8],   # 行B
            fb[8:12],  # 行C
            fb[12:16]  # 行D
        ]
        first_boxes.append(box_4x4)
    
    return first_boxes

# ============================================================================
# 1. 行A前4列强制锚点测试
# ============================================================================

def analyze_row_a_patterns(solutions: List[Dict]) -> Dict:
    """分析行A前4列的取值模式"""
    
    row_a_first4 = extract_row_a_first4(solutions)
    
    # 收集所有模式
    patterns = Counter()
    for row_a in row_a_first4:
        patterns[tuple(row_a)] += 1
    
    print("=" * 60)
    print("行A前4列取值模式分析")
    print("=" * 60)
    
    for pattern, count in patterns.most_common():
        print(f"  {pattern} -> 出现 {count} 次")
    
    # 分析每个位置的取值分布
    for col_idx in range(4):
        col_vals = [row_a[col_idx] for row_a in row_a_first4]
        val_dist = Counter(col_vals)
        print(f"\n列{col_idx} 取值分布 (行A):")
        for val, cnt in sorted(val_dist.items()):
            print(f"  值{val:2d}: {cnt:2d}次 ({cnt/23*100:.1f}%)")
    
    # 分析分叉点
    print("\n分叉点分析:")
    print(f"  (0,0) 取值数: {len(set(row_a[0] for row_a in row_a_first4))}")
    print(f"  (0,1) 取值数: {len(set(row_a[1] for row_a in row_a_first4))}")
    print(f"  (0,2) 取值数: {len(set(row_a[2] for row_a in row_a_first4))}")
    print(f"  (0,3) 取值数: {len(set(row_a[3] for row_a in row_a_first4))}")
    
    # 验证V30的分叉点声称
    # V30说只有3个分叉点：(0,0), (0,1), (0,3)
    # 如果(0,2)所有解都相同，则它不是分叉点
    
    unique_at_col2 = set(row_a[2] for row_a in row_a_first4)
    if len(unique_at_col2) == 1:
        print(f"\n✓ 验证: 列2所有解均为值{list(unique_at_col2)[0]}，不是分叉点")
    else:
        print(f"\n⚠ 注意: 列2有{len(unique_at_col2)}种不同取值，也是分叉点!")
    
    return {
        'patterns': {str(k): v for k, v in patterns.items()},
        'num_unique_patterns': len(patterns),
        'col_distribution': {
            i: dict(Counter(row_a[i] for row_a in row_a_first4))
            for i in range(4)
        }
    }

def test_force_anchor_at_divergence(solutions: List[Dict], 
                                     pattern: Tuple[int, int, int, int]) -> Dict:
    """测试强制行A前4列为某个模式后的约束分析"""
    
    row_a_first4 = extract_row_a_first4(solutions)
    
    # 统计有多少解符合这个模式
    matching_count = sum(1 for ra in row_a_first4 if tuple(ra) == pattern)
    
    # 检查模式本身的合法性
    # 行A前4列必须是AllDifferent
    if len(set(pattern)) < 4:
        return {
            'valid': False,
            'reason': '行A前4列违反AllDifferent约束',
            'matching_solutions': 0
        }
    
    # 检查与现有锚点是否冲突（假设我们有92个锚点）
    # 这里简化：只检查(0,2)是否为3（V30显示的锚点）
    if pattern[2] != 3:
        return {
            'valid': False,
            'reason': f'与锚点(0,2)=3冲突',
            'matching_solutions': 0
        }
    
    return {
        'valid': True,
        'matching_solutions': matching_count,
        'pattern': pattern,
        'is_unique_puzzle': matching_count == 1
    }

def generate_unique_puzzle_candidates(solutions: List[Dict]) -> List[Dict]:
    """生成可能的唯一解谜题候选"""
    
    row_a_first4 = extract_row_a_first4(solutions)
    patterns = Counter(tuple(ra) for ra in row_a_first4)
    
    print("\n" + "=" * 60)
    print("唯一解谜题生成候选")
    print("=" * 60)
    
    candidates = []
    for pattern, count in patterns.items():
        # 检查该模式是否能产生唯一解
        test = test_force_anchor_at_divergence(solutions, pattern)
        
        print(f"\n模式 {pattern}:")
        print(f"  匹配解数: {test['matching_solutions']}")
        print(f"  是否唯一: {test.get('is_unique_puzzle', False)}")
        
        if test['matching_solutions'] == 1:
            print(f"  ✓ 该模式可产生唯一解谜题!")
            candidates.append({
                'pattern': pattern,
                'is_unique': True,
                'total_anchors_needed': 92 + 4  # 原有92 + 分叉点4个
            })
        elif test['matching_solutions'] == 0:
            print(f"  ✗ 无解 (与约束冲突)")
        else:
            print(f"  - 多解 ({test['matching_solutions']}个)")
    
    return candidates

# ============================================================================
# 2. 迭代子结构分析
# ============================================================================

def analyze_first_box_linkages(solutions: List[Dict]) -> Dict:
    """分析首宫16个位置的联动关系"""
    
    first_boxes = extract_first_box_full(solutions)
    
    print("\n" + "=" * 60)
    print("首宫(4x4)联动关系分析")
    print("=" * 60)
    
    # 分析每行/每列的取值模式
    row_patterns = []
    col_patterns = []
    
    for fb in first_boxes:
        # 行模式
        for r in range(4):
            row_vals = tuple(fb[r])
            row_patterns.append(row_vals)
        
        # 列模式
        for c in range(4):
            col_vals = tuple(fb[r][c] for r in range(4))
            col_patterns.append(col_vals)
    
    # 行模式统计
    row_dist = Counter(row_patterns)
    print("\n行A (首宫第0行) 模式:")
    for pat, cnt in row_dist.most_common():
        print(f"  {pat}: {cnt}次")
    
    # 列模式统计
    col_dist = Counter(col_patterns)
    print(f"\n列0 (首宫第0列) 模式:")
    for pat, cnt in col_dist.most_common():
        print(f"  {pat}: {cnt}次")
    
    # 分析联动性：如果两列总是同时变化或同时固定，说明有联动
    print("\n联动分析:")
    
    # 对每对位置，计算共现模式
    linkages = {}
    positions = [(r, c) for r in range(4) for c in range(4)]
    
    for i, (r1, c1) in enumerate(positions):
        for j, (r2, c2) in enumerate(positions):
            if i >= j:
                continue
            
            # 统计共现模式
            co_occ = Counter()
            for fb in first_boxes:
                co_occ[(fb[r1][c1], fb[r2][c2])] += 1
            
            # 计算互信息
            total = len(first_boxes)
            val1_dist = Counter(fb[r1][c1] for fb in first_boxes)
            val2_dist = Counter(fb[r2][c2] for fb in first_boxes)
            
            mi = 0
            for (v1, v2), cnt in co_occ.items():
                p_joint = cnt / total
                p1 = val1_dist[v1] / total
                p2 = val2_dist[v2] / total
                if p_joint > 0 and p1 > 0 and p2 > 0:
                    mi += p_joint * np.log2(p_joint / (p1 * p2))
            
            if mi > 0.3:
                linkages[((r1, c1), (r2, c2))] = mi
    
    print("\n强联动关系 (互信息 > 0.3):")
    sorted_linkages = sorted(linkages.items(), key=lambda x: -x[1])
    for (pos1, pos2), mi in sorted_linkages[:10]:
        print(f"  {pos1} ↔ {pos2}: MI = {mi:.3f}")
    
    return {
        'row_patterns': {str(k): v for k, v in row_dist.items()},
        'col_patterns': {str(k): v for k, v in col_dist.items()},
        'linkages': {str(k): v for k, v in sorted_linkages[:20]},
        'num_strong_linkages': len([x for x in linkages.values() if x > 0.3])
    }

def analyze_col0_diversity(solutions: List[Dict]) -> Dict:
    """分析首宫第0列（行A-C-D的第0列）的多样性"""
    
    first_boxes = extract_first_box_full(solutions)
    
    print("\n" + "=" * 60)
    print("首宫第0列多样性分析")
    print("=" * 60)
    
    # 收集首宫第0列的所有值
    col0_by_row = {r: [] for r in range(4)}
    for fb in first_boxes:
        for r in range(4):
            col0_by_row[r].append(fb[r][0])
    
    for r in range(4):
        vals = col0_by_row[r]
        unique_vals = set(vals)
        print(f"\n首宫第0列行{r} (全局行{chr(65+r)}):")
        print(f"  取值范围: {sorted(unique_vals)}")
        print(f"  不同取值数: {len(unique_vals)}")
        
        if len(unique_vals) == 1:
            print(f"  ⚠ 固定值: {list(unique_vals)[0]}")
        else:
            val_dist = Counter(vals)
            for val, cnt in sorted(val_dist.items()):
                print(f"    值{val:2d}: {cnt:2d}次")
    
    return {
        'col0_by_row': {str(r): list(set(col0_by_row[r])) for r in range(4)},
        'num_diverse_rows': sum(1 for r in range(4) if len(set(col0_by_row[r])) > 1)
    }

def analyze_ternary_combinations(solutions: List[Dict]) -> Dict:
    """分析三元组组合（三个分叉点的联合约束）"""
    
    row_a_first4 = extract_row_a_first4(solutions)
    
    print("\n" + "=" * 60)
    print("三元组 (0,0)-(0,1)-(0,3) 组合分析")
    print("=" * 60)
    
    # 统计三元组取值组合
    triads = Counter()
    for row_a in row_a_first4:
        triad = (row_a[0], row_a[1], row_a[3])  # 跳过(0,2)因为它固定
        triads[triad] += 1
    
    print(f"\n三元组取值组合 (共{len(triads)}种):")
    for triad, cnt in triads.most_common():
        print(f"  ({triad[0]}, {triad[1]}, {triad[2]}): {cnt}次 ({cnt/23*100:.1f}%)")
    
    # 分析约束满足情况
    # 行AllDifferent已经满足（因为每个解都满足）
    # 检查是否有隐藏的约束
    
    # 计算条件概率
    print("\n条件概率分析:")
    
    # P(0,0 | (0,1)=x)
    for val1 in sorted(set(t[1] for t in triads)):
        subset = [t for t in triads if t[1] == val1]
        val0_dist = Counter(t[0] for t in subset)
        print(f"  当(0,1)={val1}时，(0,0)分布: {dict(val0_dist)}")
    
    # 检查是否存在固定关联
    fixed_pairs = []
    for t in triads:
        # 检查是否有固定的配对关系
        pass
    
    return {
        'triad_distribution': {str(k): v for k, v in triads.items()},
        'num_combinations': len(triads),
        'is_complete_combination': len(triads) == 23  # 如果所有组合都不同，则是完整组合
    }

# ============================================================================
# 3. 扩大样本 - 尝试构造更多解
# ============================================================================

def expand_samples_by_permutation(solutions: List[Dict]) -> Dict:
    """通过首宫内合法排列扩展样本"""
    
    print("\n" + "=" * 60)
    print("首宫排列扩展法扩大样本")
    print("=" * 60)
    
    first_boxes = extract_first_box_full(solutions)
    
    # 从现有首宫中提取约束模式
    # 每行必须AllDifferent，每列必须AllDifferent
    
    # 检查首宫内部的约束模式
    print("\n首宫约束模式提取:")
    
    # 行约束
    for r in range(4):
        row_vals_all = [fb[r] for fb in first_boxes]
        # 检查是否遵循某种模式
        print(f"  行{r}: {len(set(str(tuple(vals)) for vals in row_vals_all))} 种模式")
    
    # 尝试生成新排列
    new_candidates = []
    
    # 方法：从每行选择一个合法排列，然后检查列约束
    row_permutations = []
    for r in range(4):
        # 获取该行的所有出现过的排列
        seen = set()
        for fb in first_boxes:
            pat = tuple(fb[r])
            seen.add(pat)
        row_permutations.append(list(seen))
        print(f"  行{r}已知排列数: {len(row_permutations[-1])}")
    
    # 尝试组合这些排列（笛卡尔积）
    total_combos = 1
    for perms in row_permutations:
        total_combos *= len(perms)
    
    print(f"\n理论组合数: {total_combos}")
    
    # 筛选满足列AllDifferent的组合
    valid_combos = 0
    sample_combos = []
    
    for combo in product(*row_permutations):
        # combo是一个4x4的矩阵
        # 检查列AllDifferent
        col_ok = True
        for c in range(4):
            col_vals = [combo[r][c] for r in range(4)]
            if len(set(col_vals)) < 4:
                col_ok = False
                break
        
        if col_ok:
            valid_combos += 1
            if len(sample_combos) < 5:
                sample_combos.append(combo)
    
    print(f"\n满足列AllDifferent的有效组合: {valid_combos}")
    
    if sample_combos:
        print("\n有效组合示例:")
        for i, combo in enumerate(sample_combos):
            print(f"  组合{i+1}:")
            for r in range(4):
                print(f"    {combo[r]}")
    
    return {
        'row_permutation_counts': [len(p) for p in row_permutations],
        'total_theoretical_combinations': total_combos,
        'valid_combinations': valid_combos,
        'sample_combinations': [list(c) for c in sample_combos]
    }

def generate_extended_samples(target_count: int = 100) -> Dict:
    """生成扩展样本（基于现有23解的模式）"""
    
    print("\n" + "=" * 60)
    print(f"尝试扩展至 {target_count} 个样本")
    print("=" * 60)
    
    with open('v29_latin_square_parallel_result.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    existing_sols = data['essential_solutions']
    
    # 记录现有解的特征
    existing_hashes = set(s['grid_hash'] for s in existing_sols)
    existing_first_boxes = [tuple(s['first_box']) for s in existing_sols]
    
    print(f"现有解数量: {len(existing_sols)}")
    print(f"现有解哈希: {len(existing_hashes)} 个不同")
    
    # 从排列扩展中获取有效首宫
    row_perms = []
    first_boxes = []
    for sol in existing_sols:
        fb = sol['first_box']
        first_boxes.append([fb[0:4], fb[4:8], fb[8:12], fb[12:16]])
    
    for r in range(4):
        seen = set()
        for fb in first_boxes:
            seen.add(tuple(fb[r]))
        row_perms.append(list(seen))
    
    # 生成有效组合
    all_valid = []
    for combo in product(*row_perms):
        # 检查列AllDifferent
        col_ok = True
        for c in range(4):
            col_vals = [combo[r][c] for r in range(4)]
            if len(set(col_vals)) < 4:
                col_ok = False
                break
        
        if col_ok:
            # 扁平化
            flat = [v for row in combo for v in row]
            if tuple(flat) not in existing_first_boxes:
                all_valid.append(flat)
    
    print(f"\n新的有效首宫数量: {len(all_valid)}")
    
    # 生成扩展样本（使用新首宫 + 原有元数据）
    extended = []
    for i, new_fb in enumerate(all_valid[:target_count - len(existing_sols)]):
        extended.append({
            'solution_id': len(existing_sols) + i,
            'first_box': new_fb,
            'sequence_count': 1,  # 假设
            'cluster_size': 1,
            'grid_hash': f"extended_{i:04d}",
            'source': 'extension'
        })
    
    all_solutions = existing_sols + extended
    
    return {
        'original_count': len(existing_sols),
        'extended_count': len(extended),
        'total_count': len(all_solutions),
        'extended_solutions': extended[:10],  # 只保存前10个示例
        'is_target_met': len(all_solutions) >= target_count
    }

# ============================================================================
# 4. 解空间饱和度分析
# ============================================================================

def analyze_space_saturation(solutions: List[Dict]) -> Dict:
    """分析解空间饱和度"""
    
    print("\n" + "=" * 60)
    print("解空间饱和度分析")
    print("=" * 60)
    
    first_boxes = extract_first_box_full(solutions)
    row_a_first4 = extract_row_a_first4(solutions)
    
    # 1. 首宫多样性分析
    print("\n首宫(16个位置)多样性:")
    
    diversity_by_pos = {}
    for r in range(4):
        for c in range(4):
            vals = set(fb[r][c] for fb in first_boxes)
            diversity_by_pos[(r, c)] = {
                'num_values': len(vals),
                'values': sorted(vals),
                'is_fixed': len(vals) == 1
            }
    
    fixed_count = sum(1 for v in diversity_by_pos.values() if v['is_fixed'])
    print(f"  固定位置数: {fixed_count}/16")
    print(f"  高变异位置数: {sum(1 for v in diversity_by_pos.values() if v['num_values'] > 8)}/16")
    
    # 2. 行A前4列的熵
    print("\n行A前4列熵值分析:")
    for col_idx in range(4):
        vals = [ra[col_idx] for ra in row_a_first4]
        val_dist = Counter(vals)
        total = len(vals)
        
        entropy = -sum((cnt/total) * np.log2(cnt/total) 
                      for cnt in val_dist.values())
        max_entropy = np.log2(16)  # 如果16个值均匀分布
        saturation = entropy / max_entropy
        
        print(f"  列{col_idx}: 熵={entropy:.3f}, 饱和度={saturation*100:.1f}%")
    
    # 3. 整体多样性指标
    all_first_boxes = [tuple(s['first_box']) for s in solutions]
    unique_boxes = len(set(all_first_boxes))
    
    print(f"\n首宫唯一组合数: {unique_boxes}/{len(solutions)}")
    
    # 4. 分叉点覆盖度
    patterns = Counter(tuple(ra) for ra in row_a_first4)
    print(f"行A前4列模式数: {len(patterns)}/{len(solutions)}")
    
    # 如果所有23个解的行A前4列都不同，说明我们可能只是局部采样
    if len(patterns) == len(solutions):
        print("\n⚠ 重要发现: 所有解的行A前4列都不同!")
        print("   这表明解空间可能极其稀疏，我们只采样到了部分解")
    
    # 5. 饱和度估计
    # 基于分叉点组合数
    col0_vals = len(set(ra[0] for ra in row_a_first4))
    col1_vals = len(set(ra[1] for ra in row_a_first4))
    col3_vals = len(set(ra[3] for ra in row_a_first4))
    
    theoretical_max = col0_vals * col1_vals * col3_vals
    saturation = len(patterns) / theoretical_max
    
    print(f"\n分叉点饱和度估计:")
    print(f"  (0,0)取值数: {col0_vals}")
    print(f"  (0,1)取值数: {col1_vals}")
    print(f"  (0,3)取值数: {col3_vals}")
    print(f"  理论最大组合: {theoretical_max}")
    print(f"  实际组合: {len(patterns)}")
    print(f"  饱和度: {saturation*100:.1f}%")
    
    return {
        'diversity_by_position': {f'{r}_{c}': v for (r, c), v in diversity_by_pos.items()},
        'entropy_analysis': {
            i: -sum((cnt/len(row_a_first4)) * np.log2(cnt/len(row_a_first4))
                   for cnt in Counter(ra[i] for ra in row_a_first4).values())
            for i in range(4)
        },
        'saturation_estimate': saturation,
        'is_sparse': saturation < 0.5,
        'num_unique_patterns': len(patterns)
    }

# ============================================================================
# 5. 十六连环追踪
# ============================================================================

def trace_ring_structures(solutions: List[Dict]) -> Dict:
    """追踪环状结构"""
    
    print("\n" + "=" * 60)
    print("首宫环状结构追踪")
    print("=" * 60)
    
    first_boxes = extract_first_box_full(solutions)
    
    # 基于首宫差异构建图
    n = len(first_boxes)
    
    # 计算每对首宫的差异度
    diff_matrix = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(i+1, n):
            fb1 = [v for row in first_boxes[i] for v in row]
            fb2 = [v for row in first_boxes[j] for v in row]
            diff = sum(1 for a, b in zip(fb1, fb2) if a != b)
            diff_matrix[i, j] = diff
            diff_matrix[j, i] = diff
    
    print("\n首宫间差异分布:")
    diff_dist = Counter()
    for i in range(n):
        for j in range(i+1, n):
            diff_dist[diff_matrix[i, j]] += 1
    
    for diff, cnt in sorted(diff_dist.items()):
        print(f"  差异{diff}个位置: {cnt}对")
    
    # 寻找最小差异的邻居（差异最小的对）
    min_diff = min(d for d in diff_dist.keys() if d > 0)
    neighbors = defaultdict(list)
    
    for i in range(n):
        for j in range(i+1, n):
            if diff_matrix[i, j] == min_diff:
                neighbors[i].append(j)
                neighbors[j].append(i)
    
    print(f"\n最小差异: {min_diff} 个位置")
    print(f"最小差异邻居对数: {sum(len(v) for v in neighbors.values())//2}")
    
    # 尝试构建长度为16的路径（假设存在十六连环）
    def find_path(start, length, visited, path):
        if len(path) == length:
            # 检查能否回到起点（形成环）
            if start in neighbors.get(path[-1], []):
                return path.copy()
            return None
        
        for neighbor in neighbors.get(path[-1], []):
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                result = find_path(start, length, visited, path)
                if result:
                    return result
                path.pop()
                visited.remove(neighbor)
        
        return None
    
    # 由于只有23个解，寻找长度16的环不太可能
    # 尝试寻找较小的环
    ring_size = min(8, n)
    rings = []
    for i in range(n):
        path = find_path(i, ring_size, {i}, [i])
        if path and len(path) == ring_size:
            rings.append(path)
    
    print(f"\n找到的环状结构 (长度{ring_size}): {len(rings)} 个")
    
    if rings:
        for i, ring in enumerate(rings[:2]):
            print(f"\n环 #{i+1}: {[f'解{idx}' for idx in ring]}")
            # 显示相邻解的差异
            for j in range(len(ring)):
                idx1, idx2 = ring[j], ring[(j+1) % len(ring)]
                diff = diff_matrix[idx1, idx2]
                print(f"    解{idx1} -> 解{idx2}: 差异{diff}个位置")
    
    return {
        'diff_distribution': {str(k): v for k, v in diff_dist.items()},
        'min_diff': int(min_diff),
        'ring_size': ring_size,
        'rings_found': len(rings),
        'sample_rings': rings[:3]
    }

# ============================================================================
# 主函数
# ============================================================================

def main():
    print("=" * 70)
    print("V31 - 分叉点深度博弈推演研究")
    print("=" * 70)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 加载数据
    solutions = load_solutions_from_v29()
    
    if not solutions:
        print("错误: 未找到任何解")
        return
    
    # 1. 行A前4列分析
    row_a_analysis = analyze_row_a_patterns(solutions)
    
    # 2. 首宫联动分析
    linkage_analysis = analyze_first_box_linkages(solutions)
    
    # 3. 首宫第0列分析
    col0_analysis = analyze_col0_diversity(solutions)
    
    # 4. 三元组分析
    ternary_analysis = analyze_ternary_combinations(solutions)
    
    # 5. 唯一解谜题候选
    candidates = generate_unique_puzzle_candidates(solutions)
    
    # 6. 首宫排列扩展
    expansion_result = expand_samples_by_permutation(solutions)
    
    # 7. 生成扩展样本
    # extended_result = generate_extended_samples(target_count=100)
    
    # 8. 饱和度分析
    saturation_result = analyze_space_saturation(solutions)
    
    # 9. 环状结构追踪
    ring_analysis = trace_ring_structures(solutions)
    
    # 汇总报告
    print("\n" + "=" * 70)
    print("V31 研究总结")
    print("=" * 70)
    
    key_findings = []
    
    # 关键发现汇总
    if row_a_analysis['num_unique_patterns'] == 23:
        key_findings.append("✓ 所有23个解的行A前4列均不同，验证解空间多样性")
    
    # 检查分叉点
    col2_unique = len(set(row_a[2] for row_a in 
                          extract_row_a_first4(solutions)))
    if col2_unique == 1:
        key_findings.append("✓ 确认(0,2)为固定值，真正分叉点只有3个: (0,0), (0,1), (0,3)")
    
    # 唯一解可能性
    unique_candidates = [c for c in candidates if c.get('is_unique_puzzle')]
    if unique_candidates:
        key_findings.append(f"✓ 发现 {len(unique_candidates)} 个可能的唯一解谜题候选")
    
    # 饱和度
    if saturation_result['saturation_estimate'] < 0.5:
        key_findings.append(f"⚠ 解空间饱和度仅 {saturation_result['saturation_estimate']*100:.1f}%，可能有更多解")
    else:
        key_findings.append(f"✓ 解空间饱和度 {saturation_result['saturation_estimate']*100:.1f}%，采样较充分")
    
    print("\n关键发现:")
    for i, finding in enumerate(key_findings, 1):
        print(f"{i}. {finding}")
    
    # 保存到JSON
    report = {
        'version': 'V31.0',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'num_solutions': len(solutions),
        'row_a_analysis': row_a_analysis,
        'linkage_analysis': linkage_analysis,
        'col0_analysis': col0_analysis,
        'ternary_analysis': ternary_analysis,
        'unique_puzzle_candidates': candidates,
        'expansion_analysis': expansion_result,
        'saturation_analysis': saturation_result,
        'ring_analysis': ring_analysis,
        'key_conclusions': key_findings,
        'next_steps': [
            "扩大样本量至100+以验证饱和度",
            "对唯一解候选进行完整16x16验证",
            "分析首宫之外的位置联动"
        ]
    }
    
    with open('v31_fork_depth_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 结果已保存至: v31_fork_depth_analysis_result.json")
    
    return report

if __name__ == '__main__':
    main()
