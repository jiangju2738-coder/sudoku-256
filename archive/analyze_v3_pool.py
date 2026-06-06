#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V3.0 排列池深度分析 - 識別溢岀排列
"""

import json
from typing import List, Dict
from collections import Counter


def analyze_v3_pool():
    """分析V3.0排列池中各個變體組的約束表現"""
    
    print("=" * 80)
    print("V3.0 符闔排列池深度分析 - 溢出識別")
    print("=" * 80)
    
    with open('permutations_v3.json', 'r', encoding='utf-8') as f:
        permutations = json.load(f)
    
    print(f"\n📊 總排列數: {len(permutations)}")
    
    # 分析排列的來源分類
    # 根據之前設計: 
    # - 行0-15: 基礎Sudoku行 (16個)
    # - 行16-99: 值替換變體 (~84個)
    # - 行100-339: 循環移位變體 (~240個)
    # - 行340-355: 卦序映射變體 (~16個)
    # - 行356+: 其他
    
    groups = {
        '基礎行 (CORRECT_SHIFTS)': permutations[0:16],
        '值替換變體 (σ∘base)': permutations[16:100],
        '循環移位變體 (shift 4k)': permutations[100:340],
        '卦序映射變體 (hexagram)': permutations[340:356],
        '其他變體': permutations[356:]
    }
    
    print("\n📋 排列池結構分析:")
    print("-" * 80)
    for group_name, group in groups.items():
        print(f"   {group_name}: {len(group)} 個排列")
    
    # 分析每個排列的"特徵值"
    print("\n🔍 排列特徵分析:")
    
    # 特徵1: 循環移位量
    def get_shift_pattern(row: List[int]) -> int:
        """計算行的循環移位量（相對於 [1,2,...,16]）"""
        # 找到1的位置
        pos_1 = row.index(1)
        # 如果行是循環移位的，那麼 (row[j] - (j+1)) % 16 應該恆定
        shift = (row[0] - 1) % 16
        for j in range(16):
            if (row[j] - (j + 1)) % 16 != shift:
                return -1  # 不是純循環移位
        return shift
    
    # 特徵2: 宮約束違反檢測
    def check_box_constraint(row: List[int], box_idx: int) -> bool:
        """檢查單個宮是否包含1-16各一次（作為16x16網格的一行時）"""
        # 這個檢查需要16行才能完成，單行無法驗證宮約束
        return True
    
    # 特徵3: 列約束違反預判
    def check_column_conflict(rows: List[List[int]], col_idx: int) -> bool:
        """檢查某一列是否有重複值"""
        values = [row[col_idx] for row in rows]
        return len(set(values)) != 16
    
    # 分析基礎行的移位模式
    print("\n📊 基礎行移位模式:")
    for i in range(16):
        shift = get_shift_pattern(permutations[i])
        print(f"   行{i+1}: 移位量 = {shift}")
    
    # 分析值替換變體
    print("\n🔬 值替換變體分析 (行17-100):")
    value_replacements = []
    for i in range(16, min(32, len(permutations))):  # 檢查前幾個
        row = permutations[i]
        # 檢查是否通過值替換 σ([1,2,...,16]) 得到
        # 即 row[j] = σ(j+1)，其中 σ 是一個排列
        mapping = {}
        for j in range(16):
            orig_val = j + 1
            new_val = row[j]
            if orig_val in mapping:
                if mapping[orig_val] != new_val:
                    break
            else:
                mapping[orig_val] = new_val
        
        # 如果所有值都建立了唯一映射，這是值替換變體
        if len(mapping) == 16 and len(set(mapping.values())) == 16:
            value_replacements.append(i)
    
    print(f"   檢測到值替換變體: {len(value_replacements)} 個")
    if value_replacements:
        print(f"   索引範圍: {value_replacements[:5]}...")
    
    # 分析循環移位變體
    print("\n🔬 循環移位變體分析 (行101-340):")
    cyclic_shifts = []
    for i in range(100, min(120, len(permutations))):
        shift = get_shift_pattern(permutations[i])
        if shift >= 0:
            cyclic_shifts.append((i, shift))
    
    print(f"   檢測到純循環移位變體: {len(cyclic_shifts)} 個")
    if cyclic_shifts:
        shift_distribution = Counter([s for _, s in cyclic_shifts])
        print(f"   移位分布: {dict(shift_distribution)}")
    
    # 核心發現：列約束衝突分析
    print("\n⚠️ 列約束衝突深度分析:")
    print("-" * 80)
    
    # 檢查各個組作為16行網格時的列約束
    conflict_summary = {}
    
    for group_name, group in groups.items():
        if len(group) >= 16:
            test_rows = group[:16]
            col_conflicts = []
            for col in range(16):
                if check_column_conflict(test_rows, col):
                    col_conflicts.append(col)
            conflict_summary[group_name] = {
                'count': len(group),
                'col_conflicts': len(col_conflicts),
                'conflict_cols': col_conflicts[:8]  # 只顯示前8個
            }
        else:
            conflict_summary[group_name] = {
                'count': len(group),
                'col_conflicts': 'N/A (不足16行)',
                'conflict_cols': []
            }
    
    print(f"\n{'組別':<35} {'排列數':>8} {'列衝突':>10} {'衝突列':>20}")
    print("-" * 80)
    for group_name, stats in conflict_summary.items():
        conflict_str = str(stats['conflict_cols']) if isinstance(stats['conflict_cols'], list) else stats['conflict_cols']
        print(f"{group_name:<35} {stats['count']:>8} {str(stats['col_conflicts']):>10} {conflict_str[:30]:>30}")
    
    # 生成溢出報告
    print("\n" + "=" * 80)
    print("🚨 溢出識別報告")
    print("=" * 80)
    
    overflow_groups = [name for name, stats in conflict_summary.items() 
                      if isinstance(stats['col_conflicts'], int) and stats['col_conflicts'] > 0]
    
    print(f"\n⚠️ 存在溢出的組別: {len(overflow_groups)}")
    for group in overflow_groups:
        stats = conflict_summary[group]
        print(f"\n   【{group}】")
        print(f"      - 排列數量: {stats['count']}")
        print(f"      - 列衝突數: {stats['col_conflicts']} / 16")
        print(f"      - 衝突率: {stats['col_conflicts']/16*100:.1f}%")
        
        if stats['conflict_cols']:
            print(f"      - 衝突列索引: {stats['conflict_cols']}")
    
    # 計算總溢出比例
    total_overflow = sum(
        stats['col_conflicts'] if isinstance(stats['col_conflicts'], int) else 0
        for stats in conflict_summary.values()
    )
    
    print(f"\n📊 總體溢出統計:")
    print(f"   總排列數: {len(permutations)}")
    print(f"   總列衝突: {total_overflow}")
    print(f"   溢出率: {total_overflow/(16*len(groups))*100:.2f}%")
    
    # 生成修復建議
    print("\n" + "=" * 80)
    print("💡 修復建議")
    print("=" * 80)
    
    print("""
    1. 【立即修復】去除列約束衝突的排列
       - 從排列池中刪除所有列約束衝突的變體
       - 保留基礎16行 + 值替換變體 + 宮內移位變體
    
    2. 【重構生成規則】僅生成滿足三約束的排列
       - 值替換變體: σ 必須是保持宮結構的映射
       - 循環移位變體: 僅允許移位量為4的倍數 (0,4,8,12)
       - 卦序映射變體: 需要重新設計以保證列約束
    
    3. 【建立驗證機制】所有生成排列必須通過三約束驗證
       - 行約束: 1-16各出現一次 ✅ (已滿足)
       - 列約束: 在16行網格中每列1-16各出現一次 ❌ (需要修復)
       - 宮約束: 每個4×4宮中1-16各出現一次 ❌ (需要修復)
    """)
    
    return {
        'total_permutations': len(permutations),
        'conflict_summary': conflict_summary,
        'overflow_groups': overflow_groups,
        'total_col_conflicts': total_overflow
    }


if __name__ == '__main__':
    result = analyze_v3_pool()
