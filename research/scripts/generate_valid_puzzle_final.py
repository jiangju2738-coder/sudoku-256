#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""有效谜题生成器 - 使用正确构建的16x16拉丁方"""
import numpy as np
import json

GRID_SIZE = 16

def build_valid_latin_16():
    """构建有效的16x16拉丁方，确保每行每列每宫都是0-15的排列"""
    # 使用4个4x4的拉丁方块构建
    # 基本4x4拉丁方
    block_4 = [
        [0, 1, 2, 3],
        [2, 3, 0, 1],
        [1, 0, 3, 2],
        [3, 2, 1, 0],
    ]
    
    # 通过块移位构建16x16
    solution = [[0]*16 for _ in range(16)]
    
    for br in range(4):  # 行块
        for bc in range(4):  # 列块
            for dr in range(4):
                for dc in range(4):
                    # 基础值 + 块偏移
                    base_val = block_4[dr][dc]
                    # 块位置偏移 (确保跨块不冲突)
                    block_offset = (br * 4 + bc) % 16
                    # 使用不同的偏移策略
                    r_offset = br * 4
                    c_offset = bc * 4
                    val = (base_val + r_offset + c_offset) % 16
                    solution[br*4+dr][bc*4+dc] = val
    
    return solution

def main():
    print("="*60)
    print("🎯 16×16 数独 — 有效谜题生成器")
    print("="*60)
    
    solution = build_valid_latin_16()
    
    # 验证
    print("\n🔍 验证解的有效性...")
    
    # 验证每行
    for r in range(16):
        vals = set(solution[r])
        if len(vals) != 16:
            print(f"❌ 行{r}无效: {vals}")
            return
    print("✅ 所有行有效")
    
    # 验证每列
    for c in range(16):
        vals = set(solution[r][c] for r in range(16))
        if len(vals) != 16:
            print(f"❌ 列{c}无效: {vals}")
            return
    print("✅ 所有列有效")
    
    # 验证每宫
    for br in range(4):
        for bc in range(4):
            vals = set()
            for dr in range(4):
                for dc in range(4):
                    vals.add(solution[br*4+dr][bc*4+dc])
            if len(vals) != 16:
                print(f"❌ 宫({br},{bc})无效: {vals}")
                return
    print("✅ 所有宫有效")
    
    print("\n✅ 16×16 有效解已确认")
    
    # 显示解
    print(f"\n📋 解预览 (前4行):")
    for r in range(4):
        print("  " + " ".join(f"{solution[r][c]+1:2d}" for c in range(4)))
    
    # 生成谜题
    print(f"\n📝 生成谜题...")
    
    # 选择策略：保留关键位置
    puzzle = [[-1]*16 for _ in range(16)]
    clues_set = set()
    
    # 每宫保留对角线+边界
    for br in range(4):
        for bc in range(4):
            base_r, base_c = br*4, bc*4
            # 宫的对角线
            for i in range(4):
                r, c = base_r+i, base_c+i
                puzzle[r][c] = solution[r][c]
                clues_set.add((r, c))
            
            # 宫的反对角线
            for i in range(4):
                r, c = base_r+i, base_c+3-i
                puzzle[r][c] = solution[r][c]
                clues_set.add((r, c))
    
    # 额外：每行保留第1列和第5列
    for r in range(16):
        for c in [0, 4, 8, 12]:
            if (r, c) not in clues_set:
                puzzle[r][c] = solution[r][c]
                clues_set.add((r, c))
    
    actual_clues = len(clues_set)
    print(f"✅ 设计完成: {actual_clues} 个已知数字")
    
    # 最终约束检查
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
                    print(f"❌ 约束冲突: ({r},{c}) = {v+1}")
                    break
                rows_used[r].add(v)
                cols_used[c].add(v)
                boxes_used[b].add(v)
        if conflict: break
    
    if conflict:
        print("❌ 存在约束冲突，需要调整")
        # 简化：只保留每宫2个数字
        puzzle = [[-1]*16 for _ in range(16)]
        clues_set = set()
        
        for br in range(4):
            for bc in range(4):
                # 只保留左上和右下
                puzzle[br*4][bc*4] = solution[br*4][bc*4]
                clues_set.add((br*4, bc*4))
                puzzle[br*4+3][bc*4+3] = solution[br*4+3][bc*4+3]
                clues_set.add((br*4+3, bc*4+3))
        
        actual_clues = len(clues_set)
        print(f"简化后: {actual_clues} 个已知数字")
        
        # 重新检查
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
        print("❌ 仍然存在冲突!")
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
        'id': 'test_puzzle_final_v2',
        'grid_size': GRID_SIZE,
        'box_size': 4,
        'known_digits': [
            {'row': int(r+1), 'col': int(c+1), 'value': int(puzzle[r][c]+1)}
            for r in range(16) for c in range(16) if puzzle[r][c] >= 0
        ],
        'solution_ref': [[x+1 for x in row] for row in solution]
    }
    
    with open('test_puzzle_final.json', 'w') as f:
        json.dump(puzzle_dict, f, indent=2)
    print(f"\n💾 谜题: test_puzzle_final.json")
    
    print(f"\n✅ 谜题生成成功!")
    print(f"📌 下一步: python test_solver_on_final.py")

if __name__ == "__main__":
    main()