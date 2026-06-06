#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 V37 增强版：量子坍缩 + 列冲突排列交换剪枝 + 未知行相容性分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

增强功能：
1. 中文字体支持
2. 详细统计分析
3. 多视角可视化
4. 约束传播深度分析
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import font_manager
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 尝试加载更好的中文字体
for font_path in [
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    'C:/Windows/Fonts/simsun.ttc',
    'C:/Windows/Fonts/msyh.ttc',
]:
    try:
        font_manager.fontManager.addfont(font_path)
        plt.rcParams['font.sans-serif'] = [font_manager.FontProperties(fname=font_path).get_name()]
        break
    except:
        pass


# ======================== 常量定义 ========================

GRID_SIZE = 16
BOX_SIZE = 4
FUMMEL_ROWS = {2, 3, 8, 15}  # C, D, I, P 行


class QuantumState(Enum):
    SUPERPOSITION = "叠加态"
    PARTIAL_COLLAPSE = "部分坍缩"
    COLLAPSED = "坍缩态"
    CONFLICT = "冲突态"
    FILTERED = "过滤态"


# ======================== 加载真实配置 ========================

def load_real_config():
    """加载真实的92锚点配置和排列"""
    config_path = "sudoku_config.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"未找到 {config_path}，尝试其他路径...")
        return None, None
    
    # 解析锚点（0-indexed）
    anchors = {}
    for anchor in config.get('known_digits', []):
        r = anchor['row'] - 1
        c = anchor['col'] - 1
        anchors[(r, c)] = anchor['value']
    
    # 加载排列
    permutations = []
    for r in range(GRID_SIZE):
        perm_file = f"A{r+1}_permutations.json"
        try:
            with open(perm_file, 'r', encoding='utf-8') as f:
                row_perms = json.load(f)
            permutations.append([tuple(p) for p in row_perms])
        except FileNotFoundError:
            print(f"  警告: 未找到 {perm_file}")
            permutations.append([])
    
    return anchors, permutations


# ======================== 列冲突分析 ========================

def analyze_column_conflicts(anchors: Dict, permutations: List) -> Dict:
    """详细分析列冲突"""
    
    # 从锚点构建部分网格
    partial_grid = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
    for (r, c), v in anchors.items():
        partial_grid[r][c] = v
    
    # 检测锚点引起的列冲突
    anchor_conflicts = {}
    for c in range(GRID_SIZE):
        values = [partial_grid[r][c] for r in range(GRID_SIZE) if partial_grid[r][c] != 0]
        value_counts = defaultdict(list)
        for r, v in enumerate(partial_grid[c]):
            if v != 0:
                value_counts[v].append(r)
        
        conflicting = {v: rows for v, rows in value_counts.items() if len(rows) > 1}
        if conflicting:
            anchor_conflicts[c] = conflicting
    
    # 分析每个列的值分布
    col_analysis = {}
    for c in range(GRID_SIZE):
        fixed_values = set()
        possible_values = set(range(1, GRID_SIZE + 1))
        
        for r in range(GRID_SIZE):
            if partial_grid[r][c] != 0:
                fixed_values.add(partial_grid[r][c])
                # 从该行排列中找出可能的值
                if permutations[r]:
                    possible_in_row = set(permutations[r][0])  # 简化
                    possible_values &= possible_in_row
        
        col_analysis[c] = {
            'fixed_count': len(fixed_values),
            'fixed_values': sorted(fixed_values),
            'remaining_possible': len(possible_values)
        }
    
    return {
        'anchor_conflicts': anchor_conflicts,
        'column_analysis': col_analysis,
        'total_anchor_conflicts': len(anchor_conflicts)
    }


# ======================== 量子态分析 ========================

def analyze_quantum_states(anchors: Dict, permutations: List) -> Dict:
    """分析每行的量子态"""
    
    row_states = {}
    
    for r in range(GRID_SIZE):
        # 统计该行的锚点数
        row_anchors = {(c, v) for (row, c), v in anchors.items() if row == r}
        anchor_count = len(row_anchors)
        
        # 确定量子态
        if anchor_count == GRID_SIZE:
            state = QuantumState.COLLAPSED
        elif anchor_count > 0:
            state = QuantumState.PARTIAL_COLLAPSE
        else:
            state = QuantumState.SUPERPOSITION
        
        # 检查排列
        perms = permutations[r]
        if not perms:
            perm_state = "未加载"
        elif len(perms) == 1:
            perm_state = "唯一排列"
        else:
            perm_state = f"{len(perms)}个排列"
        
        # 计算熵
        if len(perms) > 1:
            entropy = np.log2(len(perms))
        else:
            entropy = 0.0
        
        row_states[r] = {
            'row_label': f"Row {chr(65 + r)}",
            'state': state.value,
            'anchor_count': anchor_count,
            'anchor_density': anchor_count / GRID_SIZE,
            'permutation_status': perm_state,
            'entropy': entropy,
            'is_fummel': r in FUMMEL_ROWS
        }
    
    # 全局状态
    states_list = [row_states[r]['state'] for r in range(GRID_SIZE)]
    if all(s == QuantumState.COLLAPSED.value for s in states_list):
        global_state = "完全坍缩"
    elif any("冲突" in s for s in states_list):
        global_state = "冲突"
    elif any("坍缩" in s for s in states_list):
        global_state = "部分坍缩"
    else:
        global_state = "叠加态"
    
    return {
        'global_state': global_state,
        'row_states': row_states,
        'state_distribution': {
            'collapsed': sum(1 for s in states_list if '坍缩' in s and '部分' not in s),
            'partial': sum(1 for s in states_list if '部分' in s),
            'superposition': sum(1 for s in states_list if '叠加' in s),
            'conflict': sum(1 for s in states_list if '冲突' in s)
        }
    }


# ======================== 相容性分析 ========================

def analyze_compatibility(anchors: Dict, permutations: List) -> Dict:
    """分析未知行之间的相容性"""
    
    # 找出未知行
    unknown_rows = []
    for r in range(GRID_SIZE):
        row_anchor_count = sum(1 for (row, c) in anchors.keys() if row == r)
        if row_anchor_count < GRID_SIZE:
            unknown_rows.append(r)
    
    if len(unknown_rows) <= 1:
        return {
            'unknown_rows': unknown_rows,
            'matrix': None,
            'incompatible_pairs': [],
            'message': "未知行太少，无法进行相容性分析"
        }
    
    # 计算相容性矩阵
    n = len(unknown_rows)
    matrix = np.ones((GRID_SIZE, GRID_SIZE))
    
    incompatible_pairs = []
    
    for i, r1 in enumerate(unknown_rows):
        for j, r2 in enumerate(unknown_rows):
            if i >= j:
                continue
            
            perms1 = permutations[r1]
            perms2 = permutations[r2]
            
            if not perms1 or not perms2:
                compat = 0.5  # 未知
                continue
            
            # 检查是否存在相容的排列对
            compatible_count = 0
            total_checks = min(100, len(perms1) * len(perms2))
            checked = 0
            
            for p1 in perms1[:10]:
                for p2 in perms2[:10]:
                    if checked >= 100:
                        break
                    # 检查列冲突
                    has_conflict = any(p1[c] == p2[c] for c in range(GRID_SIZE))
                    if not has_conflict:
                        compatible_count += 1
                    checked += 1
            
            compat_ratio = compatible_count / max(checked, 1)
            matrix[r1, r2] = compat_ratio
            matrix[r2, r1] = compat_ratio
            
            if compat_ratio < 0.3:
                incompatible_pairs.append((r1, r2, compat_ratio))
    
    return {
        'unknown_rows': unknown_rows,
        'unknown_count': len(unknown_rows),
        'matrix_shape': (GRID_SIZE, GRID_SIZE),
        'incompatible_pairs': incompatible_pairs,
        'average_compatibility': np.mean([matrix[r1, r2] for r1 in unknown_rows for r2 in unknown_rows if r1 < r2])
    }


# ======================== 可视化 ========================

def create_visualizations(anchors, permutations, col_analysis, quantum_analysis, compat_analysis):
    """创建综合可视化"""
    
    fig = plt.figure(figsize=(16, 12))
    
    # 1. 锚点密度热力图
    ax1 = fig.add_subplot(2, 2, 1)
    anchor_density = np.zeros((GRID_SIZE, GRID_SIZE))
    for (r, c), v in anchors.items():
        anchor_density[r, c] = 1
    
    # 每行的锚点数量
    row_density = np.array([sum(1 for (row, c) in anchors.keys() if row == r) / GRID_SIZE 
                           for r in range(GRID_SIZE)])
    
    im1 = ax1.imshow(row_density.reshape(-1, 1), cmap='YlOrRd', aspect='auto', 
                     extent=[0, 1, 0, GRID_SIZE])
    ax1.set_yticks(range(GRID_SIZE))
    ax1.set_yticklabels([f"{chr(65+i)}" for i in range(GRID_SIZE)])
    ax1.set_xlabel('密度')
    ax1.set_title('各行锚点密度')
    plt.colorbar(im1, ax=ax1, shrink=0.8)
    
    # 2. 量子态分布
    ax2 = fig.add_subplot(2, 2, 2)
    state_dist = quantum_analysis['state_distribution']
    colors = {'collapsed': '#2ecc71', 'partial': '#f39c12', 
              'superposition': '#3498db', 'conflict': '#e74c3c'}
    labels = [f"{k}: {v}" for k, v in state_dist.items()]
    sizes = list(state_dist.values())
    
    if sum(sizes) > 0:
        ax2.pie(sizes, labels=labels, colors=[colors[k] for k in state_dist.keys()],
                autopct='%1.0f%%', startangle=90)
    ax2.set_title(f'量子态分布\n(全局: {quantum_analysis["global_state"]})')
    
    # 3. 每行熵值
    ax3 = fig.add_subplot(2, 2, 3)
    entropies = [quantum_analysis['row_states'][r]['entropy'] for r in range(GRID_SIZE)]
    row_labels = [f"{chr(65+i)}" for i in range(GRID_SIZE)]
    
    bars = ax3.bar(row_labels, entropies, color=['red' if i in FUMMEL_ROWS else 'steelblue' 
                                                   for i in range(GRID_SIZE)])
    ax3.set_xlabel('行')
    ax3.set_ylabel('排列熵 (bits)')
    ax3.set_title('各行排列不确定性')
    ax3.tick_params(axis='x', rotation=45)
    
    # 标注固定行
    for i in FUMMEL_ROWS:
        bars[i].set_edgecolor('red')
        bars[i].set_linewidth(2)
    
    # 4. 列固定值数量
    ax4 = fig.add_subplot(2, 2, 4)
    col_fixed = [col_analysis['column_analysis'][c]['fixed_count'] for c in range(GRID_SIZE)]
    
    ax4.bar(range(GRID_SIZE), col_fixed, color='seagreen')
    ax4.set_xticks(range(GRID_SIZE))
    ax4.set_xticklabels([str(c+1) for c in range(GRID_SIZE)])
    ax4.set_xlabel('列号')
    ax4.set_ylabel('固定值数量')
    ax4.set_title('各列锚点分布')
    ax4.axhline(y=4, color='red', linestyle='--', alpha=0.7, label='AllDifferent阈值')
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig('v37_quantum_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    return 'v37_quantum_analysis.png'


# ======================== 主程序 ========================

def main():
    print("=" * 70)
    print("V37 增强版分析：量子坍缩 + 列冲突 + 相容性")
    print("=" * 70)
    
    # 加载配置
    anchors, permutations = load_real_config()
    
    if anchors is None:
        print("  使用模拟数据...")
        # 模拟92个锚点
        anchors = {}
        import random
        random.seed(42)
        for r in range(GRID_SIZE):
            n_anchors = random.randint(2, 16)
            cols = random.sample(range(GRID_SIZE), n_anchors)
            for c in cols:
                anchors[(r, c)] = random.randint(1, GRID_SIZE)
        
        # 模拟排列
        permutations = []
        for r in range(GRID_SIZE):
            base = list(range(1, GRID_SIZE + 1))
            perms = set()
            while len(perms) < 50:
                perm = base.copy()
                random.shuffle(perm)
                perms.add(tuple(perm))
            permutations.append(list(perms))
    
    print(f"\n  锚点数量: {len(anchors)}")
    print(f"  排列加载: {sum(1 for p in permutations if p)}/{GRID_SIZE} 行")
    
    # 分析
    print("\n[1] 列冲突分析...")
    col_analysis = analyze_column_conflicts(anchors, permutations)
    print(f"    发现 {col_analysis['total_anchor_conflicts']} 个列冲突")
    
    print("\n[2] 量子态分析...")
    quantum_analysis = analyze_quantum_states(anchors, permutations)
    print(f"    全局状态: {quantum_analysis['global_state']}")
    print(f"    分布: {quantum_analysis['state_distribution']}")
    
    print("\n[3] 相容性分析...")
    compat_analysis = analyze_compatibility(anchors, permutations)
    print(f"    未知行数: {compat_analysis['unknown_count']}")
    print(f"    不相容对: {len(compat_analysis['incompatible_pairs'])}")
    
    # 可视化
    print("\n[4] 生成可视化...")
    viz_file = create_visualizations(anchors, permutations, col_analysis, 
                                     quantum_analysis, compat_analysis)
    print(f"    已保存: {viz_file}")
    
    # 保存完整报告
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'column_conflict_analysis': col_analysis,
        'quantum_state_analysis': quantum_analysis,
        'compatibility_analysis': compat_analysis,
        'recommendations': generate_recommendations(col_analysis, quantum_analysis, compat_analysis)
    }
    
    with open('v37_enhanced_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n  报告已保存至: v37_enhanced_report.json")
    
    return report


def generate_recommendations(col_analysis, quantum_analysis, compat_analysis):
    """生成建议"""
    recs = []
    
    # 基于列冲突
    if col_analysis['total_anchor_conflicts'] > 0:
        recs.append(f"存在 {col_analysis['total_anchor_conflicts']} 个列锚点冲突，需要仲裁或修正")
    
    # 基于量子态
    dist = quantum_analysis['state_distribution']
    if dist['conflict'] > 0:
        recs.append(f"{dist['conflict']} 行处于冲突态，检查排列过滤是否正确")
    
    if dist['superposition'] > 8:
        recs.append("超过一半行处于叠加态，建议增加锚点或约束")
    
    # 基于相容性
    if len(compat_analysis['incompatible_pairs']) > 0:
        recs.append(f"发现 {len(compat_analysis['incompatible_pairs'])} 对不相容行，搜索空间可能分裂")
    
    if not recs:
        recs.append("当前配置下搜索空间状态良好")
    
    return recs


if __name__ == "__main__":
    main()
