#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在手工构建的谜题上运行CPU MRV求解器"""
import numpy as np
import time
import json

GRID_SIZE = 16

def load_puzzle(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def puzzle_to_grid(puzzle_dict):
    grid = np.full((16,16), -1, dtype=int)
    for cell in puzzle_dict['known_digits']:
        r = cell['row'] - 1
        c = cell['col'] - 1
        v = cell['value'] - 1
        grid[r,c] = v
    return grid

def solve_mrv(grid):
    """MRV求解器"""
    rows_mask = [0]*16
    cols_mask = [0]*16
    boxes_mask = [0]*16
    
    for r in range(16):
        for c in range(16):
            if grid[r,c] >= 0:
                v = grid[r,c]
                b = (r//4)*4 + (c//4)
                m = 1 << v
                rows_mask[r] |= m
                cols_mask[c] |= m
                boxes_mask[b] |= m
    
    empty = [(r,c) for r in range(16) for c in range(16) if grid[r,c] < 0]
    solution = None
    nodes = [0]
    start = time.time()
    time_limit = 60
    
    def search(idx):
        nodes[0] += 1
        if time.time() - start > time_limit: return False
        if solution is not None: return True  # 已找到解
        
        if idx >= len(empty):
            return True
        
        # MRV选择
        best = idx
        best_count = 17
        for i in range(idx, len(empty)):
            r, c = empty[i]
            b = (r//4)*4 + (c//4)
            mask = rows_mask[r] | cols_mask[c] | boxes_mask[b]
            cnt = 16 - bin(mask).count('1')
            if cnt < best_count:
                best_count = cnt
                best = i
                if cnt <= 1: break
        
        if best_count == 0: return False
        
        # 交换
        empty[idx], empty[best] = empty[best], empty[idx]
        r, c = empty[idx]
        b = (r//4)*4 + (c//4)
        mask = rows_mask[r] | cols_mask[c] | boxes_mask[b]
        
        for v in range(16):
            if not (mask & (1 << v)):
                grid[r,c] = v
                m = 1 << v
                rows_mask[r] |= m
                cols_mask[c] |= m
                boxes_mask[b] |= m
                
                if search(idx+1):
                    return True
                
                grid[r,c] = -1
                rows_mask[r] &= ~m
                cols_mask[c] &= ~m
                boxes_mask[b] &= ~m
        
        empty[idx], empty[best] = empty[best], empty[idx]
        return False
    
    success = search(0)
    
    if success:
        solution = grid.copy()
    
    return success, time.time()-start, nodes[0], solution

def main():
    print("="*60)
    print("🚀 16×16 数独 — CPU MRV求解器验证")
    print("="*60)
    
    # 加载谜题
    puzzle_dict = load_puzzle('test_puzzle_handcrafted.json')
    grid = puzzle_to_grid(puzzle_dict)
    
    clues = len(puzzle_dict['known_digits'])
    print(f"📋 谜题: {clues} 个已知数字, {256-clues} 个空白")
    
    # 显示谜题
    print(f"\n📋 谜题:")
    print("-" * 75)
    for r in range(16):
        row = ""
        for c in range(16):
            if grid[r,c] >= 0:
                row += f" {grid[r,c]+1:2d}"
            else:
                row += " . "
            if (c+1) % 4 == 0:
                row += " |"
        print(row)
    print("-" * 75)
    
    # 求解
    print(f"\n⚡ 运行MRV求解器...")
    success, elapsed, nodes, solved_grid = solve_mrv(grid)
    
    print(f"\n{'='*60}")
    print(f"📊 求解结果")
    print(f"{'='*60}")
    print(f"状态: {'✅ 成功' if success else '❌ 失败'}")
    print(f"时间: {elapsed:.4f} 秒")
    print(f"节点: {nodes:,}")
    print(f"节点/秒: {nodes/elapsed:,.0f}" if elapsed > 0 else "")
    
    if success and solved_grid is not None:
        # 验证解
        ref_sol = puzzle_dict.get('solution_ref')
        if ref_sol:
            ref_grid = np.array(ref_sol) - 1  # 转为0-indexed
            match = np.array_equal(solved_grid, ref_grid)
            print(f"参考解匹配: {'✅ 完全一致' if match else '⚠️ 存在差异'}")
        
        # 显示部分解
        print(f"\n📋 解预览 (前4行):")
        for r in range(4):
            row = " ".join(f"{solved_grid[r,c]+1:2d}" for c in range(4))
            print(f"   {row} | ...")
    
    # 保存报告
    report = {
        'puzzle_file': 'test_puzzle_handcrafted.json',
        'clues': clues,
        'solver': 'MRV + Backtrack',
        'success': success,
        'time_sec': round(elapsed, 4),
        'nodes': nodes,
        'nodes_per_sec': round(nodes/elapsed, 0) if elapsed > 0 else 0
    }
    
    with open('CPU_MRVSolver_手工作品验证报告.json', 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n💾 报告: CPU_MRVSolver_手工作品验证报告.json")
    
    print(f"\n{'='*60}")
    print(f"✅ CPU求解器验证完成!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()