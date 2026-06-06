#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从16行符闔排列中提取列约束数据
列约束定义：对于每列j（0-15），统计所有行排列中该列位置可能出现的数字集合
"""

import json
import os
from collections import defaultdict
from typing import Dict, List, Set, Tuple

BASE = "D:/2026/WPF_Sudoku/Sudoku_256/"

def load_all_row_permutations() -> Dict[int, List[Tuple[int, ...]]]:
    """加载所有16行的排列数据"""
    row_perms = {}
    for row_idx in range(1, 17):
        json_file = f"A{row_idx}_permutations.json"
        filepath = os.path.join(BASE, json_file)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                row_perms[row_idx] = [tuple(p) for p in data]
            print(f"✓ 第{row_idx}行: {len(row_perms[row_idx]):,} 个排列")
        else:
            print(f"✗ 第{row_idx}行: 文件不存在")
            row_perms[row_idx] = []
    return row_perms


def extract_column_constraints(row_perms: Dict[int, List[Tuple[int, ...]]]) -> Dict[int, Dict]:
    """
    提取列约束
    对于每列j，统计：
    1. 该列位置可能出现的数字集合
    2. 每个数字在该列出现的频率
    3. 与行排列的关联性
    """
    col_constraints = {}
    
    # 初始化16列的约束结构
    for col_idx in range(16):
        col_constraints[col_idx] = {
            'possible_values': set(),
            'value_counts': defaultdict(int),
            'row_distribution': defaultdict(lambda: defaultdict(int))
        }
    
    # 遍历所有行的所有排列，统计列位置的数据分布
    total_perms = 0
    for row_idx, perms in row_perms.items():
        total_perms += len(perms)
        for perm in perms:
            for col_idx, value in enumerate(perm):
                col_constraints[col_idx]['possible_values'].add(value)
                col_constraints[col_idx]['value_counts'][value] += 1
                col_constraints[col_idx]['row_distribution'][row_idx][value] += 1
    
    print(f"\n总共处理 {total_perms:,} 个排列")
    
    # 计算每列的统计信息
    for col_idx in range(16):
        possible = sorted(col_constraints[col_idx]['possible_values'])
        value_counts = dict(col_constraints[col_idx]['value_counts'])
        
        # 计算最常见的数字
        sorted_values = sorted(value_counts.items(), key=lambda x: -x[1])[:5]
        
        col_constraints[col_idx]['possible_values'] = possible
        col_constraints[col_idx]['value_counts'] = value_counts
        col_constraints[col_idx]['most_common'] = sorted_values
        
        # 验证：如果某列的possible_values包含全部1-16，说明无额外约束
        is_full = len(possible) == 16 and set(possible) == set(range(1, 17))
        col_constraints[col_idx]['is_full_constraint'] = is_full
    
    return col_constraints


def save_column_constraints(col_constraints: Dict[int, Dict], output_file: str):
    """保存列约束到JSON文件"""
    # 转换为可JSON序列化的格式
    export_data = {
        'summary': {
            'total_columns': 16,
            'column_count': {i: len(c['possible_values']) for i, c in col_constraints.items()}
        },
        'columns': {}
    }
    
    for col_idx in range(16):
        col_data = col_constraints[col_idx]
        export_data['columns'][col_idx + 1] = {
            'possible_values': col_data['possible_values'],
            'possible_count': len(col_data['possible_values']),
            'value_frequencies': col_data['value_counts'],
            'most_common': col_data['most_common'],
            'is_full_constraint': col_data['is_full_constraint']
        }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✓ 列约束已保存: {output_file}")


def generate_column_constraint_report(col_constraints: Dict[int, Dict]) -> str:
    """生成列约束分析报告"""
    report = []
    report.append("=" * 70)
    report.append("📊 超级大数独 16×16 - 列约束分析报告")
    report.append("=" * 70)
    report.append("")
    
    # 统计摘要
    full_cols = sum(1 for c in col_constraints.values() if c['is_full_constraint'])
    constrained_cols = 16 - full_cols
    
    report.append(f"全约束列数（可填1-16任意数字）: {full_cols}")
    report.append(f"有限约束列数（有特殊约束）: {constrained_cols}")
    report.append("")
    
    # 详细分析每列
    for col_idx in range(16):
        col_data = col_constraints[col_idx]
        status = "✅ 无约束" if col_data['is_full_constraint'] else "⚠️ 有约束"
        report.append(f"第{col_idx+1}列 [{status}]")
        report.append(f"  可能值: {col_data['possible_values']}")
        report.append(f"  可能值数量: {len(col_data['possible_values'])}")
        report.append(f"  最常见数字: {col_data['most_common'][:3]}")
        report.append("")
    
    return "\n".join(report)


def main():
    print("=" * 70)
    print("📊 超级大数独 16×16 - 列约束提取")
    print("=" * 70)
    print()
    
    # 步骤1: 加载所有行排列
    print("📂 步骤1: 加载16行符闔排列数据...")
    print("-" * 70)
    row_perms = load_all_row_permutations()
    print("-" * 70)
    print()
    
    # 步骤2: 提取列约束
    print("📊 步骤2: 提取列约束数据...")
    print("-" * 70)
    col_constraints = extract_column_constraints(row_perms)
    print("-" * 70)
    print()
    
    # 步骤3: 保存列约束
    print("💾 步骤3: 保存列约束文件...")
    output_file = os.path.join(BASE, "column_constraints.json")
    save_column_constraints(col_constraints, output_file)
    print()
    
    # 步骤4: 生成报告
    print("📄 步骤4: 生成分析报告...")
    report = generate_column_constraint_report(col_constraints)
    report_file = os.path.join(BASE, "列约束分析报告.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ 报告已保存: {report_file}")
    print()
    
    # 打印报告
    print(report)
    
    print("=" * 70)
    print("✅ 列约束提取完成!")
    print("=" * 70)
    
    return col_constraints


if __name__ == "__main__":
    main()
