#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 V25 构造性生成器 - 仲裁后部分解构造
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

方法：
1. C/D/I行已完全固定（16个锚点/行）
2. P行有2个锚点，需要构造剩余14个值
3. 其他12行需要完整构造

仲裁规则：
- 行约束：所有行必须为1-16排列
- 列约束：非符阖行之间需要列AllDifferent
- 宫约束：非符阖行宫内需要AllDifferent
"""

import random
import numpy as np
from collections import defaultdict

# 92锚点
ANCHORS_92 = {
    (2, 0): 7, (2, 1): 15, (2, 2): 3, (2, 3): 9,
    (2, 4): 11, (2, 5): 12, (2, 6): 6, (2, 7): 5,
    (2, 8): 10, (2, 9): 2, (2, 10): 1, (2, 11): 14,
    (2, 12): 13, (2, 13): 16, (2, 14): 4, (2, 15): 8,
    (3, 0): 11, (3, 1): 4, (3, 2): 13, (3, 3): 7,
    (3, 4): 16, (3, 5): 8, (3, 6): 1, (3, 7): 9,
    (3, 8): 3, (3, 9): 15, (3, 10): 2, (3, 11): 6,
    (3, 12): 5, (3, 13): 14, (3, 14): 10, (3, 15): 12,
    (8, 0): 13, (8, 1): 1, (8, 2): 10, (8, 3): 2,
    (8, 4): 8, (8, 5): 11, (8, 6): 16, (8, 7): 7,
    (8, 8): 14, (8, 9): 4, (8, 10): 5, (8, 11): 12,
    (8, 12): 9, (8, 13): 6, (8, 14): 3, (8, 15): 15,
}

# 额外锚点（非C/D/I）
ADDITIONAL_ANCHORS = {
    (0, 2): 3, (0, 5): 12, (0, 7): 5, (0, 11): 14,
    (1, 1): 12, (1, 4): 3, (1, 6): 9, (1, 8): 6,
    (4, 4): 13, (4, 9): 5, (4, 12): 4,
    (5, 1): 8, (5, 4): 15, (5, 6): 4, (5, 7): 3,
    (5, 10): 10, (5, 13): 16, (5, 14): 12,
    (6, 0): 14, (6, 2): 4, (6, 3): 6, (6, 9): 9,
    (6, 12): 15, (6, 15): 2,
    (7, 1): 13, (7, 5): 5, (7, 7): 9, (7, 11): 11,
    (7, 13): 7, (7, 14): 1,
    (9, 1): 5, (9, 5): 14, (9, 9): 8, (9, 11): 1,
    (10, 0): 1, (10, 2): 6, (10, 4): 10, (10, 7): 13,
    (10, 10): 9, (10, 13): 11,
    (11, 3): 4, (11, 5): 16, (11, 6): 14, (11, 8): 3,
    (11, 10): 12, (11, 12): 7,
    (12, 0): 15, (12, 4): 12, (12, 8): 5, (12, 9): 14,
    (12, 11): 8, (12, 14): 11, (12, 15): 6,
    (13, 2): 9, (13, 5): 6, (13, 8): 13, (13, 11): 15,
    (13, 15): 10,
    (14, 1): 1, (14, 4): 9, (14, 7): 15, (14, 10): 7,
    (14, 12): 16, (14, 13): 3,
    (15, 2): 2, (15, 6): 5,
}

FUMMEL_ROWS = [2, 3, 8, 15]  # C, D, I, P (0索引)


def create_grid():
    """创建空白网格"""
    return [[0]*16 for _ in range(16)]


def apply_anchors(grid, anchors):
    """应用锚点"""
    for (r, c), val in anchors.items():
        grid[r][c] = val


def get_missing_values(grid, row_idx):
    """获取行缺少的值"""
    existing = set(grid[row_idx][c] for c in range(16) if grid[row_idx][c] != 0)
    return set(range(1, 17)) - existing


def is_valid_row(grid, row_idx):
    """检查行是否有效（1-16排列）"""
    row = grid[row_idx]
    return len(set(row)) == 16 and all(1 <= v <= 16 for v in row)


def check_col_constraint_normal(grid, fummel_rows):
    """检查非符阖行列约束"""
    normal_rows = [r for r in range(16) if r not in fummel_rows]
    for c in range(16):
        vals = [grid[r][c] for r in normal_rows]
        if len(set(vals)) != len(vals):
            return False, c
    return True, -1


def check_box_constraint_normal(grid, fummel_rows):
    """检查非符阖行宫约束"""
    for box_r in range(4):
        for box_c in range(4):
            vals = []
            for dr in range(4):
                for dc in range(4):
                    r = box_r * 4 + dr
                    c = box_c * 4 + dc
                    if r not in fummel_rows:
                        vals.append(grid[r][c])
            if len(set(vals)) != len(vals):
                return False, (box_r, box_c)
    return True, (-1, -1)


def greedy_fill_row(grid, row_idx):
    """贪心填充一行"""
    missing = get_missing_values(grid, row_idx)
    positions = [c for c in range(16) if grid[row_idx][c] == 0]
    
    random.shuffle(positions)
    
    for c in positions:
        for val in sorted(missing):
            grid[row_idx][c] = val
            missing.remove(val)
            break
    
    return is_valid_row(grid, row_idx)


def random_fill_row(grid, row_idx):
    """随机填充一行"""
    missing = list(get_missing_values(grid, row_idx))
    positions = [c for c in range(16) if grid[row_idx][c] == 0]
    
    if len(missing) != len(positions):
        print(f'  警告: 行{chr(65+row_idx)} 缺少{len(missing)}个值但有{len(positions)}个空位')
        return False
    
    random.shuffle(missing)
    random.shuffle(positions)
    
    for c, val in zip(positions, missing):
        grid[row_idx][c] = val
    
    return is_valid_row(grid, row_idx)


def constructive_solve(iterations=1000):
    """构造性求解"""
    best_grid = None
    best_score = -1
    
    # 完全固定的符阖行（16个锚点）
    FULLY_FIXED_FUMMEL = [2, 3, 8]  # C, D, I 行
    
    for iter_num in range(iterations):
        grid = create_grid()
        apply_anchors(grid, ANCHORS_92)
        apply_anchors(grid, ADDITIONAL_ANCHORS)
        
        # 填充非锚点行
        success = True
        for r in range(16):
            if r in FULLY_FIXED_FUMMEL:
                # 完全固定的符阖行 - 检查是否有效
                if not is_valid_row(grid, r):
                    success = False
                    break
                continue
            
            # P行和其他行需要填充
            missing_count = sum(1 for c in range(16) if grid[r][c] == 0)
            if missing_count == 0:
                if not is_valid_row(grid, r):
                    success = False
                    break
                continue
            
            # 尝试多次随机填充
            filled = False
            for attempt in range(10):
                temp_grid = [row[:] for row in grid]
                random_fill_row(temp_grid, r)
                if is_valid_row(temp_grid, r):
                    grid = temp_grid
                    filled = True
                    break
            
            if not filled:
                success = False
                break
        
        if not success:
            continue
        
        # 评分：列约束和宫约束满足度
        col_ok, _ = check_col_constraint_normal(grid, FUMMEL_ROWS)
        box_ok, _ = check_box_constraint_normal(grid, FUMMEL_ROWS)
        
        score = (1 if col_ok else 0) + (1 if box_ok else 0)
        
        if score > best_score:
            best_score = score
            best_grid = [row[:] for row in grid]
            if score == 2:  # 完全满足
                break
        
        if iter_num % 100 == 0:
            print(f'迭代 {iter_num}: 分数 {best_score}/2')
    
    return best_grid, best_score


def print_grid(grid, title=''):
    """打印网格"""
    print(f'\n{title}')
    print('=' * 50)
    for r in range(16):
        row_str = ' '.join(f'{grid[r][c]:2d}' for c in range(16))
        marker = ' <<< FUMMEL' if r in FUMMEL_ROWS else ''
        print(f'{chr(65+r):2s}: {row_str}{marker}')
    print('=' * 50)


def verify_solution(grid):
    """验证解"""
    results = {
        'anchors': True,
        'rows': True,
        'cols_normal': True,
        'cols_fummel': True,
        'boxes_normal': True,
    }
    
    # 检查锚点
    for (r, c), val in {**ANCHORS_92, **ADDITIONAL_ANCHORS}.items():
        if grid[r][c] != val:
            results['anchors'] = False
            break
    
    # 检查行
    for r in range(16):
        if len(set(grid[r])) != 16:
            results['rows'] = False
            break
    
    # 检查列（非符阖行）
    for c in range(16):
        normal_vals = [grid[r][c] for r in range(16) if r not in FUMMEL_ROWS]
        if len(set(normal_vals)) != len(normal_vals):
            results['cols_normal'] = False
            break
    
    # 检查宫（非符阖行）
    for box_r in range(4):
        for box_c in range(4):
            vals = []
            for dr in range(4):
                for dc in range(4):
                    r = box_r * 4 + dr
                    c = box_c * 4 + dc
                    if r not in FUMMEL_ROWS:
                        vals.append(grid[r][c])
            if len(set(vals)) != len(vals):
                results['boxes_normal'] = False
                break
    
    return results


def main():
    print("=" * 70)
    print("V25 构造性生成器 - 仲裁后部分解构造")
    print("=" * 70)
    
    print(f'\n符阖行: {[chr(65+r) for r in FUMMEL_ROWS]}')
    print(f'完全固定行: {[chr(65+r) for r in [2, 3, 8]]} (C, D, I)')
    print(f'锚点总数: {len(ANCHORS_92) + len(ADDITIONAL_ANCHORS)}')
    
    # 尝试更多迭代
    grid, score = constructive_solve(iterations=2000)
    
    if grid:
        print_grid(grid, '生成网格:')
        
        print('\n--- 仲裁规则验证 ---')
        col_ok, _ = check_col_constraint_normal(grid, FUMMEL_ROWS)
        box_ok, _ = check_box_constraint_normal(grid, FUMMEL_ROWS)
        
        print(f'列约束（非符阖行）: {"✓" if col_ok else "✗"}')
        print(f'宫约束（非符阖行）: {"✓" if box_ok else "✗"}')
        
        # 验证所有约束
        results = verify_solution(grid)
        print('\n--- 完整验证 ---')
        for check, ok in results.items():
            print(f'{check}: {"✓" if ok else "✗"}')
        
        if all(results.values()):
            print('\n🎉 找到完全满足仲裁约束的解！')
        elif score == 1:
            print('\n⚠️ 找到部分满足的解（列/宫中有一个满足）')
        else:
            print('\n⚠️ 列约束和宫约束均未满足，但行约束和锚点正确')
        
        # 检查符阖行间列冲突（这是仲裁允许的）
        print('\n--- 符阖行列冲突检查（仲裁允许）---')
        for c in range(16):
            fummel_vals = [grid[r][c] for r in FUMMEL_ROWS]
            conflicts = [v for v in set(fummel_vals) if fummel_vals.count(v) > 1]
            if conflicts:
                print(f'列{c+1}: 冲突值 {conflicts} 位置 {[chr(65+r) for r in FUMMEL_ROWS]}')
        
        # 检查列冲突详情
        print('\n--- 列约束冲突详情 ---')
        for c in range(16):
            normal_vals = [grid[r][c] for r in range(16) if r not in FUMMEL_ROWS]
            val_counts = {}
            for v in normal_vals:
                val_counts[v] = val_counts.get(v, 0) + 1
            conflicts = {v: cnt for v, cnt in val_counts.items() if cnt > 1}
            if conflicts:
                print(f'列{c+1}: {conflicts}')
        
        # 检查宫冲突详情
        print('\n--- 宫约束冲突详情 ---')
        for box_r in range(4):
            for box_c in range(4):
                vals = []
                positions = []
                for dr in range(4):
                    for dc in range(4):
                        r = box_r * 4 + dr
                        c = box_c * 4 + dc
                        if r not in FUMMEL_ROWS:
                            vals.append(grid[r][c])
                            positions.append((r, c))
                val_counts = {}
                for v, pos in zip(vals, positions):
                    val_counts[v] = val_counts.get(v, 0) + 1
                conflicts = {v: cnt for v, cnt in val_counts.items() if cnt > 1}
                if conflicts:
                    print(f'宫({box_r},{box_c}): {conflicts}')
    
    return grid


if __name__ == '__main__':
    random.seed(12345)
    main()
