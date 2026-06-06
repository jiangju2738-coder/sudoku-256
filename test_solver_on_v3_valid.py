#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在生成的有效谜题上运行CPU MRV求解器"""
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

def solve_mrv_count_solutions(grid, limit=2):
    """MRV求解器，统计解数量"""
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
    solutions = []
    nodes = [0]
    start = time.time()
    time_limit = 60
    
    def search(idx):
        nodes[0] += 1
        if time.time() - start > time_limit: return
        if len(solutions) >= limit: return
        
        if idx >= len(empty):
            sol = grid.copy()
            solutions.append(sol)
            return
        
        # MRV
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
        
        if best_count == 0: return
        
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
                
                search(idx+1)
                
                grid[r,c] = -1
                rows_mask[r] &= ~m
                cols_mask[c] &= ~m
                boxes_mask[b] &= ~m
        
        empty[idx], empty[best] = empty[best], empty[idx]
    
    search(0)
    return len(solutions), time.time()-start, nodes[0], solutions

def verify_solution(grid, expected):
    """验证解是否匹配预期"""
    if expected is None:
        return True, "无参考解"
    
    return np.array_equal(grid, expected), "匹配" if np.array_equal(grid, expected) else "不匹配"

def main():
    print("="*60)
    print("🚀 16×16 数独 — CPU MRV求解器验证")
    print("="*60)
    
    # 加载谜题
    puzzle_dict = load_puzzle('test_puzzle_v3_valid.json')
    grid = puzzle_to_grid(puzzle_dict)
    
    clues = len(puzzle_dict['known_digits'])
    print(f"📋 谜题: {clues} 个已知数字, {256-clues} 个空白")
    
    # 显示谜题
    print(f"\n📋 谜题预览:")
    print("-" * 50)
    for r in range(16):
        row = ""
        for c in range(16):
            if grid[r,c] >= 0:
                row += f" {grid[r,c]+1:2d}"
            else:
                row += " . "
        print(row)
    print("-" * 50)
    
    # 求解
    print(f"\n⚡ 运行MRV求解器 (最多找2个解)...")
    num_sols, elapsed, nodes, solutions = solve_mrv_count_solutions(grid, limit=2)
    
    print(f"\n{'='*60}")
    print(f"📊 求解结果")
    print(f"{'='*60}")
    print(f"状态: {'✅ 有解' if num_sols > 0 else '❌ 无解'}")
    print(f"解数量: {num_sols}")
    print(f"求解时间: {elapsed:.4f} 秒")
    print(f"搜索节点: {nodes:,}")
    print(f"节点/秒: {nodes/elapsed:,.0f}" if elapsed > 0 else "")
    
    if num_sols > 0:
        # 验证解的正确性
        ref_sol = puzzle_dict.get('solution_ref')
        if ref_sol:
            ref_grid = np.array(ref_sol) - 1  # 转为0-indexed
            match, msg = verify_solution(solutions[0], ref_grid)
            print(f"参考解匹配: {'✅ ' if match else '⚠️ '}{msg}")
        else:
            print("参考解: 无")
        
        # 显示部分解
        print(f"\n📋 解预览 (前4行):")
        for r in range(4):
            row = " ".join(f"{solutions[0][r,c]+1:2d}" for c in range(4))
            print(f"   {row} | ...")
    
    # 保存报告
    report = {
        'puzzle_file': 'test_puzzle_v3_valid.json',
        'clues': clues,
        'solver': 'MRV + Backtrack',
        'num_solutions': num_sols,
        'time_sec': round(elapsed, 4),
        'nodes': nodes,
        'nodes_per_sec': round(nodes/elapsed, 0) if elapsed > 0 else 0,
        'success': num_sols > 0
    }
    
    with open('CPU_MRVSolver_v3验证报告.json', 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n💾 报告: CPU_MRVSolver_v3验证报告.json")
    
    print(f"\n{'='*60}")
    print(f"✅ CPU求解器验证完成!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()