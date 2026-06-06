#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速验证：使用预生成有效谜题"""
import numpy as np
import time
import json
from pathlib import Path

GRID_SIZE = 16
BOX_SIZE = 4

# 一个已知的16x16拉丁方解（确保每行每列每宫都是1-16的排列）
KNOWN_SOLUTION = [
    [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],
    [5,6,7,8,9,10,11,12,13,14,15,16,1,2,3,4],
    [9,10,11,12,13,14,15,16,1,2,3,4,5,6,7,8],
    [13,14,15,16,1,2,3,4,5,6,7,8,9,10,11,12],
    [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,1],
    [6,7,8,9,10,11,12,13,14,15,16,1,2,3,4,5],
    [10,11,12,13,14,15,16,1,2,3,4,5,6,7,8,9],
    [14,15,16,1,2,3,4,5,6,7,8,9,10,11,12,13],
    [3,4,5,6,7,8,9,10,11,12,13,14,15,16,1,2],
    [7,8,9,10,11,12,13,14,15,16,1,2,3,4,5,6],
    [11,12,13,14,15,16,1,2,3,4,5,6,7,8,9,10],
    [15,16,1,2,3,4,5,6,7,8,9,10,11,12,13,14],
    [4,5,6,7,8,9,10,11,12,13,14,15,16,1,2,3],
    [8,9,10,11,12,13,14,15,16,1,2,3,4,5,6,7],
    [12,13,14,15,16,1,2,3,4,5,6,7,8,9,10,11],
    [16,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
]

class BitConstraint:
    __slots__ = ['rows', 'cols', 'boxes']
    def __init__(self):
        self.rows = [0]*16
        self.cols = [0]*16
        self.boxes = [0]*16
    def reset(self):
        self.rows = [0]*16; self.cols = [0]*16; self.boxes = [0]*16
    def box_idx(self, r, c): return (r//4)*4 + (c//4)
    def is_valid(self, r, c, v):
        m = 1 << v
        return not (self.rows[r]&m) and not (self.cols[c]&m) and not (self.boxes[self.box_idx(r,c)]&m)
    def place(self, r, c, v):
        m = 1 << v; b = self.box_idx(r,c)
        self.rows[r] |= m; self.cols[c] |= m; self.boxes[b] |= m
    def remove(self, r, c, v):
        m = 1 << v; b = self.box_idx(r,c)
        self.rows[r] &= ~m; self.cols[c] &= ~m; self.boxes[b] &= ~m
    def candidates(self, r, c):
        m = self.rows[r] | self.cols[c] | self.boxes[self.box_idx(r,c)]
        return [v for v in range(16) if not (m & (1<<v))]

def solve_mrv(grid):
    """MRV求解器"""
    cons = BitConstraint()
    empty = []
    for r in range(16):
        for c in range(16):
            if grid[r,c] >= 0:
                cons.place(r, c, grid[r,c])
            else:
                empty.append((r,c))
    
    nodes = [0]
    start = time.time()
    
    def search(idx):
        nodes[0] += 1
        if time.time() - start > 30: return False
        if idx >= len(empty): return True
        
        # MRV: 找候选最少的
        best = idx
        best_cands = None
        for i in range(idx, len(empty)):
            r, c = empty[i]
            cands = cons.candidates(r, c)
            if len(cands) == 0: return False
            if best_cands is None or len(cands) < len(best_cands):
                best = i; best_cands = cands
                if len(cands) == 1: break
        
        # 交换到当前位置
        empty[idx], empty[best] = empty[best], empty[idx]
        r, c = empty[idx]
        
        for v in best_cands:
            grid[r,c] = v
            cons.place(r, c, v)
            if search(idx+1): return True
            grid[r,c] = -1
            cons.remove(r, c, v)
        
        # 恢复顺序
        empty[idx], empty[best] = empty[best], empty[idx]
        return False
    
    success = search(0)
    return success, time.time()-start, nodes[0]

def main():
    print("="*60)
    print("🚀 16×16 数独 — 快速验证")
    print("="*60)
    
    # 从已知解创建谜题
    full = np.array(KNOWN_SOLUTION)
    print("✅ 已知完整解（拉丁方排列）")
    
    # 创建谜题：保留约48个数字
    puzzle = np.full((16,16), -1, dtype=int)
    known_count = 0
    for r in range(16):
        for c in range(16):
            if (r + c) % 3 == 0:  # 约1/3保留
                puzzle[r,c] = full[r,c]
                known_count += 1
    
    print(f"谜题: {known_count} 个已知数字, {256-known_count} 个空白")
    
    # 验证已知数字无冲突
    valid = True
    cons = BitConstraint()
    for r in range(16):
        for c in range(16):
            if puzzle[r,c] >= 0:
                if not cons.is_valid(r, c, puzzle[r,c]):
                    valid = False
                    break
                cons.place(r, c, puzzle[r,c])
    
    print(f"初始约束: {'✅ 无冲突' if valid else '❌ 有冲突'}")
    
    if not valid:
        print("⚠️ 重新生成谜题...")
        # 直接使用每行每列不同的已知数字
        puzzle = np.full((16,16), -1, dtype=int)
        known_count = 0
        for r in range(16):
            for c in range(16):
                if r == c or (r+c) % 4 == 0:
                    puzzle[r,c] = full[r,c]
                    known_count += 1
        print(f"新谜题: {known_count} 个已知数字")
    
    # 显示谜题
    print("\n📋 谜题预览:")
    for r in range(4):
        print("  " + " ".join(f"{puzzle[r,c]+1:2d}" if puzzle[r,c]>=0 else " . " for c in range(4)) + " | ...")
    
    # 求解
    print(f"\n⚡ 运行MRV求解器...")
    success, elapsed, nodes = solve_mrv(puzzle)
    
    print(f"\n{'='*60}")
    print(f"📊 结果")
    print(f"{'='*60}")
    print(f"{'✅ 求解成功' if success else '❌ 超时'} | 时间: {elapsed:.4f}s | 节点: {nodes:,}")
    
    if success:
        # 验证解
        match = np.array_equal(puzzle, full)
        print(f"{'✅' if match else '⚠️'} 解匹配参考: {'一致' if match else '有多解'}")
    
    # 保存
    report = {
        'known_clues': known_count,
        'success': success,
        'time_sec': elapsed,
        'nodes': nodes,
        'puzzle_grid': puzzle.tolist(),
        'solution_ref': full.tolist()
    }
    with open('test_puzzle_v3_quick.json', 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n报告: test_puzzle_v3_quick.json")

if __name__ == "__main__":
    main()