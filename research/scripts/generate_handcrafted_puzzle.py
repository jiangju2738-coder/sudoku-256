#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""有效谜题生成器 - 手工构建正确的16x16解"""
import numpy as np
import json

GRID_SIZE = 16

def main():
    print("="*60)
    print("🎯 16×16 数独 — 手工构建谜题")
    print("="*60)
    
    # 手工构建：每行是循环移位，确保每宫也是排列
    # 使用公式: cell[r][c] = (r + c) mod 16 是简单的拉丁方
    # 但要确保宫约束，使用特殊设计
    
    # 基本模式：4x4块内循环移位
    # Row i = Row (i-1) shifted by some pattern
    
    # 使用已知的有效16x16模式
    solution = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0, 1, 2, 3],
        [8, 9, 10, 11, 12, 13, 14, 15, 0, 1, 2, 3, 4, 5, 6, 7],
        [12, 13, 14, 15, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [2, 3, 0, 1, 6, 7, 4, 5, 10, 11, 8, 9, 14, 15, 12, 13],
        [6, 7, 4, 5, 10, 11, 8, 9, 14, 15, 12, 13, 2, 3, 0, 1],
        [10, 11, 8, 9, 14, 15, 12, 13, 2, 3, 0, 1, 6, 7, 4, 5],
        [14, 15, 12, 13, 2, 3, 0, 1, 6, 7, 4, 5, 10, 11, 8, 9],
        [1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14],
        [5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14, 1, 0, 3, 2],
        [9, 8, 11, 10, 13, 12, 15, 14, 1, 0, 3, 2, 5, 4, 7, 6],
        [13, 12, 15, 14, 1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10],
        [3, 2, 1, 0, 7, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12],
        [7, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12, 3, 2, 1, 0],
        [11, 10, 9, 8, 15, 14, 13, 12, 3, 2, 1, 0, 7, 6, 5, 4],
        [15, 14, 13, 12, 3, 2, 1, 0, 7, 6, 5, 4, 11, 10, 9, 8],
    ]
    
    # 验证
    print("\n🔍 验证解...")
    
    for r in range(16):
        if len(set(solution[r])) != 16:
            print(f"❌ 行{r}无效")
            return
    print("✅ 所有行有效")
    
    for c in range(16):
        col = [solution[r][c] for r in range(16)]
        if len(set(col)) != 16:
            print(f"❌ 列{c}无效")
            return
    print("✅ 所有列有效")
    
    for br in range(4):
        for bc in range(4):
            box = []
            for dr in range(4):
                for dc in range(4):
                    box.append(solution[br*4+dr][bc*4+dc])
            if len(set(box)) != 16:
                print(f"❌ 宫({br},{bc})无效: {set(box)}")
                return
    print("✅ 所有宫有效")
    
    print("\n✅ 有效16×16解已确认!")
    
    # 显示解
    print(f"\n📋 解预览 (前4行):")
    for r in range(4):
        print("  " + " ".join(f"{solution[r][c]+1:2d}" for c in range(4)))
    
    # 生成谜题 - 保留关键位置
    puzzle = [[-1]*16 for _ in range(16)]
    clues_set = set()
    
    # 每宫保留2个数字（左上和右下）
    for br in range(4):
        for bc in range(4):
            puzzle[br*4][bc*4] = solution[br*4][bc*4]
            clues_set.add((br*4, bc*4))
            puzzle[br*4+3][bc*4+3] = solution[br*4+3][bc*4+3]
            clues_set.add((br*4+3, bc*4+3))
    
    # 对角线
    for i in range(16):
        if (i, i) not in clues_set:
            puzzle[i][i] = solution[i][i]
            clues_set.add((i, i))
    
    # 额外：某些关键行/列
    for r in [0, 4, 8, 12]:
        for c in [0, 4, 8, 12]:
            if (r, c) not in clues_set:
                puzzle[r][c] = solution[r][c]
                clues_set.add((r, c))
    
    # 更多填充
    extra_cells = [
        (1, 1), (2, 2), (3, 3),
        (5, 5), (6, 6), (7, 7),
        (9, 9), (10, 10), (11, 11),
        (13, 13), (14, 14), (15, 15),
    ]
    for r, c in extra_cells:
        if (r, c) not in clues_set:
            puzzle[r][c] = solution[r][c]
            clues_set.add((r, c))
    
    actual_clues = len(clues_set)
    print(f"\n✅ 谜题设计: {actual_clues} 个已知数字")
    
    # 约束验证
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
        print("❌ 存在冲突")
        return
    
    print("✅ 约束检查通过")
    
    # 显示谜题
    print(f"\n📋 谜题:")
    print("-" * 75)
    for r in range(16):
        row = ""
        for c in range(16):
            if puzzle[r][c] >= 0:
                row += f" {puzzle[r][c]+1:2d}"
            else:
                row += " . "
            if (c+1) % 4 == 0:
                row += " |"
        print(row)
    print("-" * 75)
    
    # 保存
    puzzle_dict = {
        'id': 'test_puzzle_handcrafted',
        'grid_size': GRID_SIZE,
        'box_size': 4,
        'known_digits': [
            {'row': int(r+1), 'col': int(c+1), 'value': int(puzzle[r][c]+1)}
            for r in range(16) for c in range(16) if puzzle[r][c] >= 0
        ],
        'solution_ref': [[x+1 for x in row] for row in solution]
    }
    
    with open('test_puzzle_handcrafted.json', 'w') as f:
        json.dump(puzzle_dict, f, indent=2)
    print(f"\n💾 谜题: test_puzzle_handcrafted.json")
    
    print(f"\n✅ 有效谜题生成完成!")

if __name__ == "__main__":
    main()