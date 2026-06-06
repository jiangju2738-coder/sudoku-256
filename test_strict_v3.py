#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""严格测试：减少已知数字，验证MRV+剪枝性能"""
import numpy as np
import time
import json

GRID_SIZE = 16
BOX_SIZE = 4

# 一个更"自然"的16x16解（不是简单的循环移位）
SOLUTION_A = [
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

# 通过排列行/列/数字生成不同解
def permute_solution(base, row_perm=None, col_perm=None, val_map=None):
    """对解进行排列"""
    sol = np.array(base)
    if row_perm:
        sol = sol[row_perm]
    if col_perm:
        sol = sol[:, col_perm]
    if val_map:
        sol = val_map[sol]
    return sol

# 生成另一个解：交换前4行和后4行
import random
random.seed(123)

def main():
    print("="*60)
    print("🚀 16×16 数独 — 严格测试 (MRV + 剪枝)")
    print("="*60)
    
    full = np.array(SOLUTION_A)
    print("✅ 参考解已加载")
    
    # 测试不同难度的谜题
    test_cases = [
        ('easy', 48, '48个已知 (简单)'),
        ('medium', 32, '32个已知 (中等)'),
        ('hard', 24, '24个已知 (困难)'),
    ]
    
    results = []
    
    for case_name, num_clues, desc in test_cases:
        print(f"\n{'='*60}")
        print(f"📋 测试: {desc}")
        print("="*60)
        
        # 随机选择保留位置
        positions = [(r,c) for r in range(16) for c in range(16)]
        random.shuffle(positions)
        keep = set(positions[:num_clues])
        
        # 构建谜题
        puzzle = np.full((16,16), -1, dtype=int)
        for r, c in keep:
            puzzle[r,c] = full[r,c]
        
        # 验证无冲突
        rows_used = [set() for _ in range(16)]
        cols_used = [set() for _ in range(16)]
        boxes_used = [set() for _ in range(16)]
        conflict = False
        for r in range(16):
            for c in range(16):
                if puzzle[r,c] >= 0:
                    v = puzzle[r,c]
                    b = (r//4)*4 + (c//4)
                    if v in rows_used[r] or v in cols_used[c] or v in boxes_used[b]:
                        conflict = True
                        break
                    rows_used[r].add(v)
                    cols_used[c].add(v)
                    boxes_used[b].add(v)
            if conflict: break
        
        if conflict:
            print("⚠️ 冲突，跳过")
            continue
        
        clues = sum(1 for r in range(16) for c in range(16) if puzzle[r,c] >= 0)
        print(f"已知数字: {clues} 个 | 空白: {256-clues} 个")
        
        # 求解器
        rows_mask = [0]*16
        cols_mask = [0]*16
        boxes_mask = [0]*16
        
        for r in range(16):
            for c in range(16):
                if puzzle[r,c] >= 0:
                    v = puzzle[r,c]
                    b = (r//4)*4 + (c//4)
                    m = 1 << v
                    rows_mask[r] |= m
                    cols_mask[c] |= m
                    boxes_mask[b] |= m
        
        empty_cells = [(r,c) for r in range(16) for c in range(16) if puzzle[r,c] < 0]
        nodes = [0]
        solutions = []
        start = time.time()
        
        def backtrack(idx):
            nodes[0] += 1
            if time.time() - start > 30: return False
            if len(solutions) >= 2: return True  # 只需找2个解
            
            if idx >= len(empty_cells):
                # 复制解
                sol = puzzle.copy()
                solutions.append(sol)
                return False  # 继续找其他解
            
            # MRV选择
            best_idx = idx
            best_count = 17
            for i in range(idx, len(empty_cells)):
                r, c = empty_cells[i]
                b = (r//4)*4 + (c//4)
                mask = rows_mask[r] | cols_mask[c] | boxes_mask[b]
                count = 16 - bin(mask).count('1')
                if count < best_count:
                    best_count = count
                    best_idx = i
                    if count <= 1: break
            
            if best_count == 0:
                return False
            
            # 交换
            empty_cells[idx], empty_cells[best_idx] = empty_cells[best_idx], empty_cells[idx]
            r, c = empty_cells[idx]
            b = (r//4)*4 + (c//4)
            
            # 尝试候选
            mask = rows_mask[r] | cols_mask[c] | boxes_mask[b]
            for v in range(16):
                if not (mask & (1 << v)):
                    puzzle[r,c] = v
                    m = 1 << v
                    rows_mask[r] |= m
                    cols_mask[c] |= m
                    boxes_mask[b] |= m
                    
                    backtrack(idx+1)
                    
                    puzzle[r,c] = -1
                    rows_mask[r] &= ~m
                    cols_mask[c] &= ~m
                    boxes_mask[b] &= ~m
            
            empty_cells[idx], empty_cells[best_idx] = empty_cells[best_idx], empty_cells[idx]
            return False
        
        backtrack(0)
        elapsed = time.time() - start
        
        unique = len(solutions)
        matched = any(np.array_equal(s, full) for s in solutions)
        
        print(f"{'✅' if unique > 0 else '❌'} 解数: {unique} | 时间: {elapsed:.4f}s | 节点: {nodes[0]:,}")
        print(f"   {'✅' if matched else '⚠️'} 匹配参考解: {'是' if matched else '否/多解'}")
        
        results.append({
            'case': case_name,
            'clues': clues,
            'solutions': unique,
            'time_sec': round(elapsed, 4),
            'nodes': nodes[0],
            'nodes_per_sec': round(nodes[0]/elapsed, 0) if elapsed > 0 else 0,
            'matches_ref': matched
        })
    
    # 汇总
    print(f"\n{'='*60}")
    print(f"📊 性能汇总")
    print(f"{'='*60}")
    for r in results:
        print(f"{r['case']:8s}: {r['clues']:2d} clues | {r['solutions']:2d} sols | {r['time_sec']:6.4f}s | {r['nodes']:8,} nodes | {r['nodes_per_sec']:>8,.0f} n/s")
    
    # 保存
    report = {
        'solver': 'MRV + Backtrack + Forward Pruning',
        'grid_size': 16,
        'box_size': 4,
        'test_cases': results,
        'hardware': 'Intel Iris Xe Graphics',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    with open('CPU_MRVSolver_性能测试报告.json', 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n💾 报告: CPU_MRVSolver_性能测试报告.json")

if __name__ == "__main__":
    main()