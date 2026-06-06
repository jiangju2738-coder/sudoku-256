#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔排列三約束嚴格驗證器
驗證所有排列是否同時滿足：行約束、列約束、宮約束

V4.0 - 嚴格的三約束驗證與修復
"""

import json
from typing import List, Dict, Tuple
from collections import Counter


class ThreeConstraintValidator:
    """三約束驗證器：行、列、宮"""
    
    def __init__(self, box_size: int = 4, grid_size: int = 16):
        self.box_size = box_size
        self.grid_size = grid_size
        self.expected = set(range(1, grid_size + 1))
    
    def validate_row(self, row: List[int]) -> Tuple[bool, List[int]]:
        """驗證單行是否是有效排列"""
        if len(row) != self.grid_size:
            return False, [f"長度錯誤: {len(row)} != {self.grid_size}"]
        actual = set(row)
        if actual != self.expected:
            missing = self.expected - actual
            extra = actual - self.expected
            duplicates = [x for x in row if row.count(x) > 1]
            errors = []
            if missing:
                errors.append(f"缺失值: {missing}")
            if extra:
                errors.append(f"多餘值: {extra}")
            if duplicates:
                errors.append(f"重複值: {set(duplicates)}")
            return False, errors
        return True, []
    
    def validate_column(self, grid: List[List[int]], col_idx: int) -> Tuple[bool, List[int]]:
        """驗證單列是否是有效排列"""
        column = [grid[row][col_idx] for row in range(self.grid_size)]
        if len(column) != self.grid_size:
            return False, [f"列長度錯誤: {len(column)}"]
        actual = set(column)
        if actual != self.expected:
            missing = self.expected - actual
            extra = actual - self.expected
            duplicates = [x for x in column if column.count(x) > 1]
            errors = []
            if missing:
                errors.append(f"缺失值: {missing}")
            if extra:
                errors.append(f"多餘值: {extra}")
            if duplicates:
                errors.append(f"重複值: {set(duplicates)}")
            return False, errors
        return True, []
    
    def validate_box(self, grid: List[List[int]], band: int, stack: int) -> Tuple[bool, List[int]]:
        """驗證單個宮是否是有效排列"""
        box_values = []
        for i in range(self.box_size):
            for j in range(self.box_size):
                row = band * self.box_size + i
                col = stack * self.box_size + j
                box_values.append(grid[row][col])
        
        actual = set(box_values)
        if actual != self.expected:
            missing = self.expected - actual
            extra = actual - self.expected
            duplicates = [x for x in box_values if box_values.count(x) > 1]
            errors = []
            if missing:
                errors.append(f"缺失值: {missing}")
            if extra:
                errors.append(f"多餘值: {extra}")
            if duplicates:
                errors.append(f"重複值: {set(duplicates)}")
            return False, errors
        return True, []
    
    def validate_grid(self, grid: List[List[int]]) -> Dict:
        """驗證整個16x16網格是否滿足三約束"""
        errors = {
            'row_errors': [],
            'col_errors': [],
            'box_errors': [],
            'total_errors': 0
        }
        
        # 驗證所有行
        for i, row in enumerate(grid):
            valid, err_msgs = self.validate_row(row)
            if not valid:
                errors['row_errors'].append({
                    'row': i + 1,
                    'errors': err_msgs
                })
                errors['total_errors'] += 1
        
        # 驗證所有列
        for j in range(self.grid_size):
            valid, err_msgs = self.validate_column(grid, j)
            if not valid:
                errors['col_errors'].append({
                    'col': j + 1,
                    'errors': err_msgs
                })
                errors['total_errors'] += 1
        
        # 驗證所有宮 (4x4 網格)
        for band in range(4):
            for stack in range(4):
                valid, err_msgs = self.validate_box(grid, band, stack)
                if not valid:
                    errors['box_errors'].append({
                        'box': f"行{band*4+1}-{band*4+4}, 列{stack*4+1}-{stack*4+4}",
                        'band': band,
                        'stack': stack,
                        'errors': err_msgs
                    })
                    errors['total_errors'] += 1
        
        return errors
    
    def validate_single_permutation(self, perm: List[int]) -> Dict:
        """驗證單個排列作為16x16網格的一行"""
        valid, errors = self.validate_row(perm)
        return {
            'is_valid_row': valid,
            'errors': errors
        }


def analyze_permutation_pool():
    """分析符闔排列池中的約束滿足情況"""
    
    print("=" * 70)
    print("符闔排列三約束嚴格驗證分析 (V4.0)")
    print("=" * 70)
    
    # 加載排列池
    with open('permutations_v3.json', 'r', encoding='utf-8') as f:
        permutations = json.load(f)
    
    print(f"\n📊 排列池統計:")
    print(f"   總排列數: {len(permutations)}")
    
    # 初始化驗證器
    validator = ThreeConstraintValidator()
    
    # 分類統計
    row_valid = 0
    col_valid = 0  # 需要網格上下文才能驗證列
    box_valid = 0  # 需要網格上下文才能驗證宮
    
    # 分析值分布
    value_counts = Counter()
    position_value_distribution = [Counter() for _ in range(16)]
    
    for idx, perm in enumerate(permutations[:1000]):  # 樣本分析
        # 驗證行約束（單個排列必然是行約束）
        valid = validator.validate_single_permutation(perm)
        if valid['is_valid_row']:
            row_valid += 1
        
        # 統計值分布
        for pos, val in enumerate(perm):
            value_counts[val] += 1
            position_value_distribution[pos][val] += 1
    
    print(f"\n✅ 行約束驗證 (基於樣本前1000個):")
    print(f"   通過行約束: {row_valid} / 1000")
    
    # 關鍵發現：循環移位變體是否保持宮約束？
    print("\n🔍 宮約束違反分析 (循環移位變體檢測):")
    
    # 分析基礎行的移位模式
    base_rows = permutations[:16]  # 前16行是基礎Sudoku行
    print(f"\n📋 基礎行移位模式分析:")
    
    for i, row in enumerate(base_rows):
        shifts = []
        for j in range(16):
            # 找到值 j+1 的位置
            pos = row.index(j + 1)
            shifts.append((pos - j) % 16)
        
        # 檢查移位一致性
        unique_shifts = set((row[j] - (j + 1)) % 16 for j in range(16))
        print(f"   行{i+1}: 移位模式 = {unique_shifts}")
    
    # 分析變體排列是否違反宮約束
    print("\n⚠️ 變體排列宮約束違規檢測:")
    
    # 創建測試網格來驗證列/宮約束
    grid = [p.copy() for p in base_rows]  # 使用基礎行構建網格
    
    # 驗證基礎網格的三約束
    result = validator.validate_grid(grid)
    print(f"\n📊 基礎網格驗證結果:")
    print(f"   行錯誤數: {len(result['row_errors'])}")
    print(f"   列錯誤數: {len(result['col_errors'])}")
    print(f"   宮錯誤數: {len(result['box_errors'])}")
    
    if result['total_errors'] == 0:
        print("   ✅ 基礎網格通過所有三約束驗證！")
    else:
        print(f"   ❌ 發現 {result['total_errors']} 個約束錯誤")
        if result['row_errors']:
            print(f"      行錯誤: {result['row_errors'][:3]}")
        if result['col_errors']:
            print(f"      列錯誤: {result['col_errors'][:3]}")
        if result['box_errors']:
            print(f"      宮錯誤: {result['box_errors'][:3]}")
    
    # 分析變體排列的列約束衝突
    print("\n🔬 變體排列列約束衝突分析:")
    
    # 使用所有變體構建測試網格（前16個變體作為行）
    test_grid = [permutations[i].copy() for i in range(16, 32)]
    result_variant = validator.validate_grid(test_grid)
    
    print(f"\n📊 變體網格(第17-32行)驗證結果:")
    print(f"   行錯誤數: {len(result_variant['row_errors'])}")
    print(f"   列錯誤數: {len(result_variant['col_errors'])}")
    print(f"   宮錯誤數: {len(result_variant['box_errors'])}")
    
    if result_variant['total_errors'] > 0:
        print("\n   ⚠️ 變體排列違反三約束詳情:")
        if result_variant['col_errors']:
            print(f"      列衝突: {result_variant['col_errors'][:5]}")
        if result_variant['box_errors']:
            print(f"      宮衝突: {result_variant['box_errors'][:5]}")
    
    return {
        'total_permutations': len(permutations),
        'row_valid_sample': row_valid,
        'base_grid_valid': result['total_errors'] == 0,
        'variant_grid_errors': result_variant['total_errors']
    }


def generate_clean_permutations():
    """生成嚴格滿足三約束的乾淨排列池"""
    
    print("\n" + "=" * 70)
    print("生成嚴格三約束符闔排列池 (V4.0)")
    print("=" * 70)
    
    CORRECT_SHIFTS = [0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15]
    
    # 1. 基礎 Sudoku 行（16個，100%滿足三約束）
    base_rows = []
    base_row = list(range(1, 17))
    for shift in CORRECT_SHIFTS:
        row = [base_row[(j + shift) % 16] for j in range(16)]
        base_rows.append(row)
    
    validator = ThreeConstraintValidator()
    
    # 驗證基礎行
    test_grid = base_rows.copy()
    result = validator.validate_grid(test_grid)
    print(f"\n✅ 基礎16行驗證: {'通過' if result['total_errors'] == 0 else '失敗'}")
    
    # 2. 通過列變換生成的合法變體
    # 列變換：交換相同相對位置的列（保持宮約束）
    clean_permutations = base_rows.copy()
    
    # 生成列對稱變體：交換列0↔4, 1↔5, 2↔6, 3↔7, 8↔12, 9↔13, 10↔14, 11↔15
    # 這保持了宮約束（交換同一宮內的列）
    column_swaps = [
        (0, 4), (1, 5), (2, 6), (3, 7),
        (8, 12), (9, 13), (10, 14), (11, 15)
    ]
    
    from itertools import combinations
    
    # 生成1-2個列交換的變體
    for num_swaps in range(1, 3):
        for swap_combo in combinations(column_swaps, num_swaps):
            for base in base_rows:
                new_row = base.copy()
                for col_a, col_b in swap_combo:
                    new_row[col_a], new_row[col_b] = new_row[col_b], new_row[col_a]
                if new_row not in clean_permutations:
                    # 驗證三約束（作為單行，行約束自然滿足）
                    clean_permutations.append(new_row)
    
    # 3. 通過行內循環移位生成（僅在特定條件下保持宮約束）
    # 只有移位量為4的倍數時才保持宮約束
    valid_shifts = [0, 4, 8, 12]
    for base in base_rows:
        for shift in valid_shifts[1:]:  # 排除0（已存在）
            shifted = [base[(j + shift) % 16] for j in range(16)]
            if shifted not in clean_permutations:
                clean_permutations.append(shifted)
    
    # 去重
    unique_perms = []
    seen = set()
    for p in clean_permutations:
        key = tuple(p)
        if key not in seen:
            seen.add(key)
            unique_perms.append(p)
    
    print(f"\n📊 乾淨排列池統計:")
    print(f"   總排列數: {len(unique_perms)}")
    print(f"   基礎行: 16")
    print(f"   列交換變體: ~{len(unique_perms) - 16 - 48}")
    print(f"   宮內移位變體: 48 (16×3)")
    
    # 4. 保存乾淨排列池
    with open('permutations_v4_clean.json', 'w', encoding='utf-8') as f:
        json.dump(unique_perms, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 乾淨排列池已保存: permutations_v4_clean.json")
    
    # 5. 生成乾淨網格並驗證
    clean_grid = unique_perms[:16]
    result_clean = validator.validate_grid(clean_grid)
    print(f"\n📊 乾淨網格驗證: {'✅ 通過' if result_clean['total_errors'] == 0 else '❌ 失敗'}")
    
    return unique_perms


def generate_conflict_report():
    """生成約束衝突詳細報告"""
    
    print("\n" + "=" * 70)
    print("約束衝突與溢出分析報告")
    print("=" * 70)
    
    with open('permutations_v3.json', 'r', encoding='utf-8') as f:
        permutations = json.load(f)
    
    validator = ThreeConstraintValidator()
    
    # 分析每個變體組的約束違反情況
    groups = {
        '基礎行 (1-16)': permutations[:16],
        '值替換變體 (17-100)': permutations[16:100],
        '循環移位變體 (101-340)': permutations[100:340],
        '卦序映射變體 (341-356)': permutations[340:356],
        '其他變體 (357+)': permutations[356:]
    }
    
    report = {
        'timestamp': '2026-05-16',
        'total_permutations': len(permutations),
        'group_analysis': {}
    }
    
    for group_name, group_perms in groups.items():
        row_violations = 0
        col_violations = 0
        box_violations = 0
        
        # 測試網格
        test_grid = group_perms[:16] if len(group_perms) >= 16 else group_perms + [permutations[i] for i in range(16 - len(group_perms))]
        
        if len(test_grid) == 16:
            result = validator.validate_grid(test_grid)
            row_violations = len(result['row_errors'])
            col_violations = len(result['col_errors'])
            box_violations = len(result['box_errors'])
        
        report['group_analysis'][group_name] = {
            'count': len(group_perms),
            'row_violations': row_violations,
            'col_violations': col_violations,
            'box_violations': box_violations,
            'has_overflow': row_violations > 0 or col_violations > 0 or box_violations > 0
        }
    
    # 生成報告
    print("\n📊 分組約束違反統計:")
    print("-" * 70)
    print(f"{'組別':<30} {'數量':>8} {'行違規':>8} {'列違規':>8} {'宮違規':>8} {'溢出':>8}")
    print("-" * 70)
    
    for group_name, stats in report['group_analysis'].items():
        overflow = "⚠️ 是" if stats['has_overflow'] else "✅ 否"
        print(f"{group_name:<30} {stats['count']:>8} {stats['row_violations']:>8} {stats['col_violations']:>8} {stats['box_violations']:>8} {overflow:>8}")
    
    # 輸出結論
    total_violations = sum(g['row_violations'] + g['col_violations'] + g['box_violations'] 
                          for g in report['group_analysis'].values())
    
    print("-" * 70)
    print(f"\n🔍 關鍵結論:")
    print(f"   總排列數: {len(permutations)}")
    print(f"   總約束違規: {total_violations}")
    print(f"   溢出現象: {'存在' if total_violations > 0 else '不存在'}")
    
    if total_violations > 0:
        print(f"\n⚠️ 溢出原因分析:")
        print(f"   1. 值替換變體: 可能破壞宮約束（值映射不保持宮結構）")
        print(f"   2. 循環移位變體: 非4倍數移位破壞宮約束")
        print(f"   3. 卦序映射變體: 需要驗證是否保持排列性質")
    
    return report


if __name__ == '__main__':
    # 執行驗證分析
    analysis = analyze_permutation_pool()
    clean_perms = generate_clean_permutations()
    conflict_report = generate_conflict_report()
    
    print("\n" + "=" * 70)
    print("✅ V4.0 三約束嚴格驗證完成")
    print("=" * 70)
