#!/usr/bin/env python3
"""
优化版 DLX + 约束传播求解器
用约束最紧的行驱动搜索
"""

import json
import time
import sys
from copy import deepcopy

N = 16
N2 = N * N

def get_box_id(row, col):
    return (row // 4) * 4 + (col // 4)

def load_perms(base_dir):
    perms = []
    for i in range(1, 17):
        with open(f"{base_dir}/A{i}_permutations.json", "r") as f:
            data = json.load(f)
            perms.append(data if isinstance(data, list) else data["permutations"])
    return perms

def verify_grid(grid, perms):
    errors = []
    # 行约束
    for r in range(N):
        if len(set(grid[r])) != N:
            errors.append(f"行{r+1}重复")
        if tuple(grid[r]) not in tuple(tuple(p) for p in perms[r]):
            errors.append(f"行{r+1}不在排列中")
    # 列约束
    for c in range(N):
        if len(set(grid[r][c] for r in range(N))) != N:
            errors.append(f"列{c+1}重复")
    # 宫约束
    for b in range(N):
        vals = []
        for dr in range(4):
            for dc in range(4):
                vals.append(grid[(b//4)*4+dr][(b%4)*4+dc])
        if len(set(vals)) != N:
            errors.append(f"宫{b+1}重复")
    return len(errors) == 0, errors

def solve_backward(perms, time_limit=300):
    """
    从约束最紧的行开始搜索
    第 9 行只有 164 个排列，第 6 行只有 359 个排列
    """
    t0 = time.time()
    
    # 按排列数排序行
    row_order = sorted(range(N), key=lambda r: len(perms[r]))
    print(f"\n搜索顺序（按约束紧密度）: {[r+1 for r in row_order]}")
    
    # 预计算每列的值分布
    col_val_sets = [set() for _ in range(N)]
    for r in range(N):
        for perm in perms[r]:
            for c in range(N):
                col_val_sets[c].add(perm[c])
    
    # 对于每对行，预计算兼容的排列对
    compatible = {}
    for i in range(N):
        for j in range(i+1, N):
            pairs = []
            for pi, perm_i in enumerate(perms[i]):
                for pj, perm_j in enumerate(perms[j]):
                    # 检查列冲突
                    conflict = False
                    for c in range(N):
                        if perm_i[c] == perm_j[c]:
                            conflict = True
                            break
                    if not conflict:
                        pairs.append((pi, pj))
            compatible[(i, j)] = pairs
            print(f"  行{i+1}×行{j+1}: {len(pairs):,} 兼容对")
    
    grid = [[0]*N for _ in range(N)]
    solutions = []
    
    def backtrack(idx):
        elapsed = time.time() - t0
        if elapsed > time_limit:
            return False
        
        if idx >= N:
            solutions.append(deepcopy(grid))
            print(f"✓ 找到解 #{len(solutions)} | {elapsed:.1f}s")
            return True
        
        row = row_order[idx]
        
        # 对于当前行，选择与已填行兼容的排列
        for pi, perm in enumerate(perms[row]):
            # 检查与已填行的列冲突
            valid = True
            for other_row in range(N):
                if grid[other_row][0] != 0:  # 已填行
                    key = (min(row, other_row), max(row, other_row))
                    if (pi,) not in [(p2 for p1, p2 in compatible[key] if p1 == pi)] if row < other_row else \
                       [(p1 for p1, p2 in compatible[key] if p2 == pi)] if row > other_row else []:
                        # 重新检查
                        for oc in range(N):
                            if grid[other_row][oc] == perm[oc]:
                                valid = False
                                break
                        if not valid:
                            break
            
            if valid:
                grid[row] = perm[:]
                if backtrack(idx + 1):
                    return True
                grid[row] = [0]*N
        
        return False
    
    if backtrack(0):
        return solutions[0]
    return None

def solve_dlx_with_constraint_filter(perms, col_constraints, time_limit=300):
    """
    DLX 精确覆盖，但每行只添加兼容的排列
    """
    t0 = time.time()
    
    # 首先用约束最紧的行筛选
    # 构建兼容矩阵
    row_compat = {}
    for i in range(N):
        for j in range(i+1, N):
            pairs = []
            for pi, pi_perm in enumerate(perms[i]):
                for pj, pj_perm in enumerate(perms[j]):
                    conflict = False
                    for c in range(N):
                        if pi_perm[c] == pj_perm[c]:
                            conflict = True
                            break
                    if not conflict:
                        pairs.append((pi, pj))
            row_compat[(i, j)] = pairs
    
    # 用第 9 行（164 个排列）作为起点
    row9_perms = perms[8]
    print(f"\n以第 9 行（{len(row9_perms)} 个排列）为搜索起点")
    
    solutions = []
    grid = [[0]*N for _ in range(N)]
    
    def backtrack(row, col_vals):
        elapsed = time.time() - t0
        if elapsed > time_limit:
            return False
        if row >= N:
            solutions.append(deepcopy(grid))
            print(f"✓ 找到解 #{len(solutions)} | {elapsed:.1f}s")
            return True
        
        row_idx = row
        for pi, perm in enumerate(perms[row_idx]):
            # 检查列冲突
            valid = True
            for c in range(N):
                if perm[c] in col_vals[c]:
                    valid = False
                    break
            if not valid:
                continue
            
            grid[row_idx] = perm[:]
            for c in range(N):
                col_vals[c].add(perm[c])
            
            if backtrack(row + 1, col_vals):
                return True
            
            for c in range(N):
                col_vals[c].remove(perm[c])
        
        return False
    
    col_vals = [set() for _ in range(N)]
    # 按约束紧密度排序
    row_order = sorted(range(N), key=lambda r: len(perms[r]))
    
    def backtrack_ordered(idx, col_vals):
        elapsed = time.time() - t0
        if elapsed > time_limit:
            return False
        if idx >= N:
            solutions.append(deepcopy(grid))
            print(f"✓ 找到解 #{len(solutions)} | {elapsed:.1f}s")
            return True
        
        row = row_order[idx]
        for perm in perms[row]:
            valid = True
            for c in range(N):
                if perm[c] in col_vals[c]:
                    valid = False
                    break
            if not valid:
                continue
            
            grid[row] = perm[:]
            for c in range(N):
                col_vals[c].add(perm[c])
            
            if backtrack_ordered(idx + 1, col_vals):
                return True
            
            for c in range(N):
                col_vals[c].remove(perm[c])
        
        return False
    
    if backtrack_ordered(0, col_vals):
        return solutions[0]
    return None

def main():
    print("=" * 70)
    print("  🎯 优化求解器：约束紧密度驱动搜索")
    print("=" * 70)
    
    t0 = time.time()
    base_dir = r"D:/2026/WPF_Sudoku/Sudoku_256"
    
    print("\n[1/3] 加载符阖排列...")
    perms = load_perms(base_dir)
    
    total_perms = sum(len(p) for p in perms)
    print(f"  总排列数: {total_perms:,}")
    for i, p in enumerate(perms):
        print(f"  第{i+1:2d}行: {len(p):>10,} 个排列")
    
    # 按约束紧密度排序
    sorted_rows = sorted(enumerate(perms), key=lambda x: len(x[1]))
    print(f"\n  约束最紧的行: 第{sorted_rows[0][0]+1}行（{len(sorted_rows[0][1])} 个排列）")
    
    print("\n[2/3] 构建行间兼容矩阵...")
    # 预计算兼容对
    compat_count = {}
    for i in range(N):
        for j in range(i+1, N):
            count = 0
            for pi in perms[i]:
                for pj in perms[j]:
                    conflict = False
                    for c in range(N):
                        if pi[c] == pj[c]:
                            conflict = True
                            break
                    if not conflict:
                        count += 1
            compat_count[(i, j)] = count
    
    total_compat = sum(compat_count.values())
    print(f"  总兼容对数: {total_compat:,}")
    
    print("\n[3/3] 执行搜索（约束紧密度优先）...")
    solution = solve_dlx_with_constraint_filter(perms, {}, time_limit=300)
    
    if solution:
        print("\n" + "=" * 70)
        print("  ✅ 找到解!")
        print("=" * 70)
        
        valid, errors = verify_grid(solution, perms)
        if valid:
            print("\n验证: ✅ 全部通过!")
            print("\n解矩阵:")
            for r in range(N):
                print(f"  {' '.join(f'{v:3d}' for v in solution[r])}")
        else:
            print("\n验证: ❌")
            for e in errors:
                print(f"  {e}")
        
        result = {
            "grid": solution,
            "method": "constraint_ordered_search",
            "search_time_seconds": time.time() - t0,
            "verification": "passed" if valid else "failed",
            "errors": errors,
            "total_permutations": total_perms
        }
        with open(f"{base_dir}/solution.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ 解已保存到 solution.json")
    else:
        print("\n❌ 未找到解")
    
    print(f"\n总耗时: {time.time() - t0:.2f} 秒")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"\n❌ 出错: {e}")
        traceback.print_exc()
        sys.exit(1)
