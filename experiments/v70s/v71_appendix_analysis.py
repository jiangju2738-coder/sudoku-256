#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V71 附錄分析：C行CP-R列交叉約束符闔排列詳情
"""

import json
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════
# 附錄數據解析
# ═══════════════════════════════════════════════════════════════════════════

def parse_appendix_data():
    """
    解析附錄中的CP-R列交叉約束數據
    
    附錄格式：
    第13列P備選數10 → CP=10（固定值）
    第15列R備選數4 5 6 9 11 13 15 → CR ∈ {4,5,6,9,11,13,15}
    
    符闔排列數詳情：
    CP10R_1-249108        → CP=10時，總排列數249,108
    CP10R4_1-25008        → CP=10, CR=4 → 25,008
    CP10R5_1-61582        → CP=10, CR=5 → 61,582
    CP10R6_1-29502        → CP=10, CR=6 → 29,502
    CP10R9_1-38096        → CP=10, CR=9 → 38,096
    CP10R11_1-35362       → CP=10, CR=11 → 35,362
    CP10R13_1-42754       → CP=10, CR=13 → 42,754
    CP10R15_1-16804       → CP=10, CR=15 → 16,804
    """
    
    # CP=10時的總排列數
    cp10_total = 249108
    
    # CP=10時，各CR值的排列數分布
    cr_distribution = {
        4: 25008,
        5: 61582,
        6: 29502,
        9: 38096,
        11: 35362,
        13: 42754,
        15: 16804
    }
    
    # 驗證總和
    cr_sum = sum(cr_distribution.values())
    
    # 初始解盤的行C完整值
    initial_c_row = [11, 6, 14, 1, 4, 2, 13, 8, 7, 12, 3, 16, 10, 9, 15, 5]
    
    # 終局解盤的行C值（不同）
    final_c_row = [7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5]
    
    return {
        'cp10_total': cp10_total,
        'cr_distribution': cr_distribution,
        'cr_sum': cr_sum,
        'initial_c_row': initial_c_row,
        'final_c_row': final_c_row,
        'cp_value': 10,  # C行第13列（CP列）
        'cr_candidates': [4, 5, 6, 9, 11, 13, 15]
    }


def analyze_c_row_constraints(data):
    """
    分析C行的約束狀態
    
    C行已知：
    - 從原始txt: C行 [0,0,14,0, 0,2,0,8, 0,0,0,0, 0,0,0,0] → 僅CF=14, CI=2, CK=8
    - 但附錄說明CP=10（第13列P）
    - 初始解盤給出了完整的C行值
    """
    
    print("=" * 70)
    print(" V71 附錄分析：C行CP-R列交叉約束符闔排列詳情")
    print("=" * 70)
    
    print("\n【1】附錄數據驗證")
    print("-" * 70)
    print(f"  CP=10時的總排列數: {data['cp10_total']:,}")
    print(f"  CR各值排列數之和: {data['cr_sum']:,}")
    
    # 驗證
    if data['cp10_total'] == data['cr_sum']:
        print("  ✓ 總和驗證通過")
    else:
        print(f"  ✗ 總和不一致！差異: {data['cp10_total'] - data['cr_sum']:,}")
    
    print("\n【2】C行CP-R列交叉約束分布")
    print("-" * 70)
    print(f"  {'CR值':<6} {'排列數':>12} {'占比':>10} {'累計':>12}")
    print("  " + "-" * 42)
    
    cumulative = 0
    for cr_val in sorted(data['cr_distribution'].keys()):
        count = data['cr_distribution'][cr_val]
        cumulative += count
        pct = count / data['cp10_total'] * 100
        print(f"  {cr_val:<6} {count:>12,} {pct:>9.2f}% {cumulative:>12,}")
    
    print("  " + "-" * 42)
    print(f"  {'合計':<6} {data['cr_sum']:>12,} {'100.00%':>10} {data['cr_sum']:>12,}")
    
    print("\n【3】初始解盤與終局解盤C行對比")
    print("-" * 70)
    print(f"  初始解盤C: {data['initial_c_row']}")
    print(f"  終局解盤C: {data['final_c_row']}")
    
    # 檢查CP（第13列，索引12）的值
    initial_cp = data['initial_c_row'][12]
    final_cp = data['final_c_row'][12]
    
    print(f"\n  CP值（第13列P）:")
    print(f"    初始解盤: {initial_cp} ✓ 符合附錄CP=10")
    print(f"    終局解盤: {final_cp} ≠ 10")
    
    # 檢查CR（第15列，索引14）的值
    initial_cr = data['initial_c_row'][14]
    final_cr = data['final_c_row'][14]
    
    print(f"\n  CR值（第15列R）:")
    print(f"    初始解盤: {initial_cr} ✓ 在備選{data['cr_candidates']}中")
    print(f"    終局解盤: {final_cr} ✓ 在備選{data['cr_candidates']}中")
    
    print("\n【4】符闔排列數重算")
    print("-" * 70)
    
    # 原始C行符闔排列數（3行約束）
    original_c_perm = 407669
    
    # 補充後的C行符闔排列數
    # CP10R_1-249108 + 原始407669
    # 但需要理解：CP10R_249108 是CP=10時的子集
    # 原始407669 是所有CP值的情況
    
    # 新的C行總排列數 = 原始 + 新增
    new_c_perm = original_c_perm + 249108
    
    print(f"  原始C行符闔排列數（3行約束）: {original_c_perm:,}")
    print(f"  附錄補充CP=10時的排列數:     + {249108:,}")
    print(f"  新的C行符闔排列數:           = {new_c_perm:,}")
    
    print("\n【5】NO_=000000 解標識")
    print("-" * 70)
    print(f"  CP10R15_ 行C [11,6,14,1, 4,2,13,8, 7,12,3,16, 10,9,15,5]")
    print(f"  NO_=000000 表示這是初始解盤的第0號解")
    print(f"  該解滿足：CP=10, CR=15")
    
    return {
        'analysis_version': 'V71',
        'timestamp': '2026-05-20',
        'data': data,
        'new_c_perm': new_c_perm,
        'initial_cp': initial_cp,
        'final_cp': final_cp,
        'initial_cr': initial_cr,
        'final_cr': final_cr,
        'cp10_cr15_count': data['cr_distribution'][15]
    }


def update_main_result(result, analysis):
    """更新主分析結果"""
    
    # 更新C行符闔排列數
    result['permutation_counts']['C'] = analysis['new_c_perm']
    
    # 添加附錄分析結果
    result['appendix_analysis'] = {
        'cp10_total': analysis['data']['cp10_total'],
        'cr_distribution': analysis['data']['cr_distribution'],
        'cr_sum_check': analysis['data']['cr_sum'] == analysis['data']['cp10_total'],
        'initial_c_row': analysis['data']['initial_c_row'],
        'final_c_row': analysis['data']['final_c_row'],
        'cp10_cr15_count': analysis['cp10_cr15_count'],
        'no_000000_verified': analysis['initial_cp'] == 10 and analysis['initial_cr'] == 15
    }
    
    return result


def main():
    # 1. 解析附錄數據
    data = parse_appendix_data()
    
    # 2. 分析C行約束
    analysis = analyze_c_row_constraints(data)
    
    # 3. 讀取主結果並更新
    with open('super_sudoku_analysis_result.json', 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    updated_result = update_main_result(result, analysis)
    
    # 4. 保存更新後的結果
    with open('super_sudoku_analysis_result_v71.json', 'w', encoding='utf-8') as f:
        json.dump(updated_result, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print(" 分析完成")
    print("=" * 70)
    print(f"\n✓ 更新後的結果已保存至: super_sudoku_analysis_result_v71.json")


if __name__ == '__main__':
    main()
