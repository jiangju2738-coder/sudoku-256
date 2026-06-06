#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""有效谜题生成器 V4 - 基于拉丁方+逐位验证"""
import numpy as np
import json
from copy import deepcopy

GRID_SIZE = 16

def main():
    print("="*60)
    print("🎯 16×16 数独 — 有效谜题生成器 V4")
    print("="*60)
    
    # 生成一个有效的16x16解（确保每行每列每宫都是0-15的排列）
    # 使用循环移位确保拉丁方性质
    solution = [[0]*16 for _ in range(16)]
    
    # 每行的偏移量
    offsets = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    
    for r in range(16):
        for c in range(16):
            solution[r][c] = (c + offsets[r]) % 16
    
    # 验证：每行每列必须包含所有数字
    for r in range(16):
        row_vals = set(solution[r])
        assert len(row_vals) == 16, f"行{r}无效: {row_vals}"
    
    for c in range(16):
        col_vals = set(solution[r][c] for r in range(16))
        assert len(col_vals) == 16, f"列{c}无效: {col_vals}"
    
    # 验证：每4x4宫必须包含所有数字
    for br in range(4):
        for bc in range(4):
            box_vals = set()
            for dr in range(4):
                for dc in range(4):
                    r, c = br*4+dr, bc*4+dc
                    box_vals.add(solution[r][c])
            assert len(box_vals) == 16, f"宫({br},{bc})无效: {box_vals}"
    
    print("✅ 有效16×16解已生成")
    print(f"   偏移模式: {offsets[:8]}...")
    
    # 显示解
    print(f"\n📋 解预览 (前4行):")
    for r in range(4):
        print("  " + " ".join(f"{solution[r][c]+1:2d}" for c in range(4)))
    
    # 谜题生成：选择性保留数字
    # 策略：每宫至少保留4个数字，确保覆盖所有约束
    
    puzzle = [[-1]*16 for _ in range(16)]
    clues_set = set()
    
    # 确保每宫至少有5个已知数字
    for br in range(4):
        for bc in range(4):
            # 选择宫内的特定位置
            positions = [
                (0, 0), (0, 1), (1, 0), (1, 1),  # 左上4个
                (2, 2), (3, 3),                  # 右下2个
            ]
            for dr, dc in positions:
                r, c = br*4+dr, bc*4+dc
                if (r, c) not in clues_set:
                    puzzle[r][c] = solution[r][c]
                    clues_set.add((r, c))
    
    # 添加对角线额外约束
    for i in range(0, 16, 2):
        if (i, i) not in clues_set:
            puzzle[i][i] = solution[i][i]
            clues_set.add((i, i))
        if (i, 15-i) not in clues_set:
            puzzle[i][15-i] = solution[i][15-i]
            clues_set.add((i, 15-i))
    
    # 添加边界约束
    for c in [0, 4, 8, 12]:
        for r in range(16):
            if (r, c) not in clues_set and r % 4 == 0:
                puzzle[r][c] = solution[r][c]
                clues_set.add((r, c))
    
    for r in [0, 4, 8, 12]:
        for c in range(16):
            if (r, c) not in clues_set and c % 4 == 0:
                puzzle[r][c] = solution[r][c]
                clues_set.add((r, c))
    
    actual_clues = len(clues_set)
    print(f"\n✅ 谜题设计: {actual_clues} 个已知数字")
    
    # 验证约束
    rows_used = [set() for _ in range(16)]
    cols_used = [set() for _ in range(16)]
    boxes_used = [set() for _ in range(16)]
    conflict = False
    
    for r in range(16):
        for c in range(16):
            if puzzle[r][c] >= 0:
                v = puzzle[r][c]
                b = (r//4)*4 + (c//4)
                if v in rows_used[r] or v in cols_used[c] or v in boxes_used[b]:
                    conflict = True
                    print(f"❌ 冲突: ({r},{c}) = {v+1}")
                    break
                rows_used[r].add(v)
                cols_used[c].add(v)
                boxes_used[b].add(v)
        if conflict: break
    
    if conflict:
        print("❌ 存在冲突!")
        return
    
    print("✅ 约束检查: 无冲突")
    
    # 显示谜题
    print(f"\n📋 谜题:")
    print("-" * 60)
    for r in range(16):
        row = ""
        for c in range(16):
            if puzzle[r][c] >= 0:
                row += f" {puzzle[r][c]+1:2d}"
            else:
                row += " . "
            if (c+1) % 4 == 0 and c < 15:
                row += " |"
        print(row)
    print("-" * 60)
    
    # 保存
    puzzle_dict = {
        'id': 'test_puzzle_v4',
        'grid_size': GRID_SIZE,
        'box_size': 4,
        'known_digits': [
            {'row': int(r+1), 'col': int(c+1), 'value': int(puzzle[r][c]+1)}
            for r in range(16) for c in range(16) if puzzle[r][c] >= 0
        ],
        'solution_ref': [[x+1 for x in row] for row in solution]
    }
    
    with open('test_puzzle_v4_valid.json', 'w') as f:
        json.dump(puzzle_dict, f, indent=2)
    print(f"\n💾 谜题: test_puzzle_v4_valid.json")
    print(f"💾 参考解: 包含在谜题文件中 (solution_ref)")
    
    print(f"\n✅ 有效谜题生成完成!")

if __name__ == "__main__":
    main()