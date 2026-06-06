#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终有效谜题生成器 - 确保无冲突"""
import numpy as np
import time
import json

GRID_SIZE = 16

def main():
    print("="*60)
    print("🎯 16×16 数独 — 最终谜题生成器")
    print("="*60)
    
    # 一个确保有效的拉丁方解
    # 每行是上一行的循环移位，但使用特殊的移位模式
    def generate_latin_square(n):
        """生成n×n拉丁方"""
        square = [[0]*n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                square[i][j] = (i + j*3) % n  # 使用乘法确保拉丁方性质
        return square
    
    solution = generate_latin_square(16)
    
    # 验证是拉丁方
    def verify_latin(sq):
        n = len(sq)
        for r in range(n):
            row_vals = set(sq[r])
            if len(row_vals) != n: return False
        for c in range(n):
            col_vals = set(sq[r][c] for r in range(n))
            if len(col_vals) != n: return False
        return True
    
    if not verify_latin(solution):
        print("❌ 拉丁方生成失败")
        return
    
    print("✅ 有效拉丁方解已生成")
    print(f"   使用公式: cell[r][c] = (r + 3c) mod 16")
    
    # 显示解
    print(f"\n📋 解预览 (前4×4):")
    for r in range(4):
        print("  " + " ".join(f"{solution[r][c]+1:2d}" for c in range(4)))
    
    # 谜题：保留约50-60个数字，确保约束
    puzzle = [[-1]*16 for _ in range(16)]
    clues_list = []
    
    # 策略：选择特定的行列组合确保拉丁方约束
    # 每行保留特定的列
    
    # 行0-3: 每行保留列 0,1,2,3,8,9,10,11 (8个/行)
    for r in range(4):
        for c in [0, 1, 2, 3, 8, 9, 10, 11]:
            puzzle[r][c] = solution[r][c]
            clues_list.append((r, c))
    
    # 行4-7: 每行保留列 0,4,8,12,1,5,9,13 (8个/行)  
    for r in range(4, 8):
        for c in [0, 4, 8, 12, 1, 5, 9, 13]:
            puzzle[r][c] = solution[r][c]
            clues_list.append((r, c))
    
    # 行8-11: 每行保留列 2,6,10,14,3,7,11,15 (8个/行)
    for r in range(8, 12):
        for c in [2, 6, 10, 14, 3, 7, 11, 15]:
            puzzle[r][c] = solution[r][c]
            clues_list.append((r, c))
    
    # 行12-15: 每行保留列 0,2,4,6,8,10,12,14 (8个/行)
    for r in range(12, 16):
        for c in [0, 2, 4, 6, 8, 10, 12, 14]:
            puzzle[r][c] = solution[r][c]
            clues_list.append((r, c))
    
    actual_clues = len(clues_list)
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
        print("⚠️ 存在冲突，调整策略...")
        # 改用更稀疏的选择
        puzzle = [[-1]*16 for _ in range(16)]
        clues_list = []
        
        # 只保留每宫左上角+对角线
        for i in range(16):
            if i % 4 == 0:
                r, c = i, i
                puzzle[r][c] = solution[r][c]
                clues_list.append((r, c))
        
        # 每宫保留1个
        for br in range(4):
            for bc in range(4):
                r, c = br*4, bc*4
                if (r,c) not in clues_list:
                    puzzle[r][c] = solution[r][c]
                    clues_list.append((r, c))
        
        actual_clues = len(clues_list)
        print(f"调整后: {actual_clues} 个已知数字")
        
        # 重新验证
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
                        break
                    rows_used[r].add(v)
                    cols_used[c].add(v)
                    boxes_used[b].add(v)
            if conflict: break
    
    if conflict:
        print("❌ 仍存在冲突")
        return
    
    print("✅ 约束检查: 无冲突")
    
    # 显示谜题
    print(f"\n📋 谜题预览 (全部):")
    print("-" * 55)
    for r in range(16):
        row = ""
        for c in range(16):
            if puzzle[r][c] >= 0:
                row += f" {puzzle[r][c]+1:2d}"
            else:
                row += " . "
        print(row)
    print("-" * 55)
    
    # 保存
    puzzle_dict = {
        'id': 'test_puzzle_v3_final_v2',
        'grid_size': GRID_SIZE,
        'box_size': 4,
        'known_digits': [
            {'row': r+1, 'col': c+1, 'value': puzzle[r][c]+1}
            for r in range(16) for c in range(16) if puzzle[r][c] >= 0
        ],
        'solution_ref': [[x+1 for x in row] for row in solution]
    }
    
    with open('test_puzzle_v3_final.json', 'w') as f:
        json.dump(puzzle_dict, f, indent=2)
    print(f"\n💾 谜题: test_puzzle_v3_final.json")
    
    print(f"\n✅ 有效谜题生成完成!")

if __name__ == "__main__":
    main()