#!/usr/bin/env python3
"""
DLX 精确覆盖快速求解器（无欧拉冲突图计算）
"""

import json
import time
import sys
import traceback

N = 16
N2 = N * N

def get_box_id(row, col):
    return (row // 4) * 4 + (col // 4)

# ============== DLX 核心 ==============

class DLXNode:
    __slots__ = ['left', 'right', 'up', 'down', 'col']
    def __init__(self, col):
        self.col = col
        self.left = self.right = self
        self.up = self.down = self

class DLXColumn:
    __slots__ = ['left', 'right', 'up', 'down', 'size', 'idx', 'name']
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name
        self.size = 0
        self.left = self.right = self.up = self.down = self

class DancingLinksX:
    def __init__(self, col_names):
        self.col_names = col_names
        self.num_cols = len(col_names)
        self.cols = [DLXColumn(i, name) for i, name in enumerate(col_names)]
        self.root = DLXColumn(-1, "root")
        for i in range(len(self.cols)):
            self._link_right(self.root, self.cols[i])
        self.row_data = []
        self._stack = []

    def _link_right(self, l, r):
        l.right = r
        r.left = l

    def _link_down(self, u, d):
        u.down = d
        d.up = u

    def add_row(self, col_indices):
        nodes = []
        first = None
        for cidx in col_indices:
            col = self.cols[cidx]
            node = DLXNode(col)
            self._link_down(col.up, node)
            col.size += 1
            if first is None:
                first = node
            else:
                self._link_right(first.left, node)
            nodes.append(node)
        if first:
            self._link_right(first.left, first)
        self.row_data.append(col_indices)
        return len(self.row_data) - 1

    def cover(self, col):
        col.left.right = col.right
        col.right.left = col.left
        row = col.down
        while row != col:
            node = row.right
            while node != row:
                node.up.down = node.down
                node.down.up = node.up
                node.col.size -= 1
                node = node.right
            row = row.down

    def uncover(self, col):
        row = col.up
        while row != col:
            node = row.left
            while node != row:
                node.col.size += 1
                node.up.down = node
                node.down.up = node
                node = node.left
            row = row.up
        col.left.right = col
        col.right.left = col

    def search(self, max_solutions=1):
        solutions = []
        def recurse():
            if len(solutions) >= max_solutions:
                return True
            if self.root.right == self.root:
                solutions.append(list(self._stack))
                return True
            min_col = None
            min_size = float('inf')
            c = self.root.right
            while c != self.root:
                if c.size < min_size:
                    min_size = c.size
                    min_col = c
                if min_size == 0:
                    break
                c = c.right
            if min_size == 0 or min_col is None:
                return False
            self.cover(min_col)
            r = min_col.down
            while r != min_col:
                self._stack.append(r.col.idx)
                j = r.right
                while j != r:
                    self.cover(j.col)
                    j = j.right
                if recurse():
                    j = r.left
                    while j != r:
                        self.uncover(j.col)
                        j = j.left
                    self._stack.pop()
                    return True
                j = r.left
                while j != r:
                    self.uncover(j.col)
                    j = j.right
                self._stack.pop()
                r = r.down
            self.uncover(min_col)
            return False
        recurse()
        return solutions


# ============== 快速树搜索（MRV + 剪枝） ==============

def solve_with_tree_mrv(perms: list, col_constraints: dict, time_limit: float = 300.0) -> list:
    """
    使用 MRV + 前向检查的树搜索
    """
    N = 16
    
    # 每行的候选排列按频次排序
    # 首先找出约束最紧的行（排列数最少的行）
    row_perm_counts = [(i, len(perms[i])) for i in range(N)]
    row_order = sorted(row_perm_counts, key=lambda x: x[1])
    
    grid = [[0] * N for _ in range(N)]
    
    def get_possible_values(row: int, col: int, col_vals: list) -> list:
        """获取单元格的可能值"""
        # 列已填值
        filled_in_col = set(col_vals[col])
        
        # 同行已填值（来自其他行的冲突）
        filled_in_row = set(grid[row])
        
        possible = []
        for perm in perms[row]:
            val = perm[col]
            if val not in filled_in_col and val not in filled_in_row:
                possible.append((perm, val))
        
        return possible
    
    solutions = []
    
    def backtrack(idx: int, col_vals: list) -> bool:
        elapsed = time.time() - t0
        if elapsed > time_limit:
            return False
        
        if idx >= N:
            solutions.append(deepcopy(grid))
            print(f"✓ 找到解 #{len(solutions)} | 耗时 {elapsed:.1f}秒")
            return True
        
        # 选择下一个行（按约束紧密度）
        row = row_order[idx][0]
        
        # 找到该行约束最紧的列
        best_col = None
        best_options = None
        min_options = float('inf')
        
        for col in range(N):
            # 检查列约束
            if col in col_constraints:
                allowed = col_constraints[col]
            else:
                allowed = set(range(1, 17))
            
            # 统计该列有多少个合法排列
            options = []
            for perm in perms[row]:
                val = perm[col]
                if val in allowed and val not in col_vals[col]:
                    options.append((perm, val))
            
            if len(options) < min_options:
                min_options = len(options)
                best_col = col
                best_options = options
            
            if min_options == 0:
                return False
            if min_options == 1:
                break
        
        # 尝试候选值
        for perm, val in best_options[:50]:  # 剪枝：最多尝试50个
            grid[row] = perm[:]
            col_vals[best_col].add(val)
            
            if backtrack(idx + 1, col_vals):
                return True
            
            col_vals[best_col].remove(val)
            grid[row] = [0] * N
        
        return False
    
    # 初始化列值跟踪
    from copy import deepcopy
    col_vals = [set() for _ in range(N)]
    
    backtrack(0, col_vals)
    
    return solutions[0] if solutions else None


def load_perms(base_dir: str) -> list:
    """加载符阖排列"""
    perms = []
    for i in range(1, 17):
        with open(f"{base_dir}/A{i}_permutations.json", "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                perms.append(data)
            else:
                perms.append(data["permutations"])
    return perms


def main():
    print("=" * 70)
    print("  🎯 DLX 精确覆盖 + MRV 树搜索 求解器")
    print("  256 数独 (16×16) | 符阖排列约束")
    print("=" * 70)
    
    global t0
    t0 = time.time()
    base_dir = r"D:/2026/WPF_Sudoku/Sudoku_256"
    
    # 加载符阖排列
    print("\n[1/3] 加载符阖排列...")
    perms = load_perms(base_dir)
    
    total_perms = sum(len(p) for p in perms)
    print(f"  总排列数: {total_perms:,}")
    for i, p in enumerate(perms):
        print(f"  第{i+1:2d}行: {len(p):>10,} 个排列")
    
    # 按行排列数从少到多排序（MRV 启发式）
    row_info = [(i, len(perms[i])) for i in range(N)]
    row_info.sort(key=lambda x: x[1])
    print(f"\n  约束紧密度排序: {[(i+1, cnt) for i, cnt in row_info]}")
    
    # 加载列约束
    print("\n[2/3] 加载列约束...")
    try:
        with open(f"{base_dir}/column_constraints.json", "r") as f:
            col_data = json.load(f)
            col_constraints = {}
            for c in range(N):
                key = str(c + 1)
                if key in col_data["columns"]:
                    col_constraints[c] = set(col_data["columns"][key]["possible_values"])
                else:
                    col_constraints[c] = set(range(1, 17))
        print(f"  已加载 16 列约束")
    except Exception as e:
        print(f"  使用全约束 (1-16)")
        col_constraints = {c: set(range(1, 17)) for c in range(N)}
    
    # 策略 1: 先尝试 MRV 树搜索（更快）
    print("\n[3/3] 执行求解...")
    print("\n▶ 策略: MRV 树搜索（优先约束最紧的行）")
    
    solution = solve_with_tree_mrv(perms, col_constraints, time_limit=60.0)
    
    if solution:
        # 验证解
        print("\n" + "=" * 70)
        print("  ✅ 找到解!")
        print("=" * 70)
        
        errors = []
        # 1. 行约束
        for r in range(N):
            if len(set(solution[r])) != N:
                errors.append(f"行 {r+1} 有重复数字")
            if tuple(solution[r]) not in tuple(tuple(p) for p in perms[r]):
                errors.append(f"行 {r+1} 不在符阖排列中")
        
        # 2. 列约束
        for c in range(N):
            col_vals = [solution[r][c] for r in range(N)]
            if len(set(col_vals)) != N:
                errors.append(f"列 {c+1} 有重复数字")
        
        # 3. 宫约束
        for b in range(N):
            box_vals = []
            br, bc = b // 4, b % 4
            for r in range(4):
                for c in range(4):
                    box_vals.append(solution[br*4 + r][bc*4 + c])
            if len(set(box_vals)) != N:
                errors.append(f"宫 {b+1} 有重复数字")
        
        if not errors:
            print("\n验证结果: ✅ 全部通过!")
            print("\n解矩阵:")
            for r in range(N):
                row_str = " ".join(f"{v:3d}" for v in solution[r])
                print(f"  {row_str}")
        else:
            print("\n验证结果: ❌ 部分失败:")
            for e in errors:
                print(f"  {e}")
        
        result = {
            "grid": solution,
            "method": "mrv_tree_search",
            "search_time_seconds": time.time() - t0,
            "verification": "passed" if not errors else "failed",
            "errors": errors,
            "total_permutations": total_perms
        }
        with open(f"{base_dir}/solution.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n解已保存到 solution.json")
    else:
        print("\n" + "=" * 70)
        print("  ❌ MRV 树搜索未找到解，尝试 DLX...")
        print("=" * 70)
        
        # DLX 求解
        print("\n▶ 策略: DLX 精确覆盖")
        
        # 构建列名
        col_names = []
        for r in range(N):
            for c in range(N):
                col_names.append(f'cell[{r},{c}]')
        for r in range(N):
            for v in range(N):
                col_names.append(f'row[{r}][{v+1}]')
        for c in range(N):
            for v in range(N):
                col_names.append(f'col[{c}][{v+1}]')
        for b in range(N):
            for v in range(N):
                col_names.append(f'box[{b}][{v+1}]')
        
        total_cols = 4 * N2
        dlx = DancingLinksX(col_names)
        
        print("\n生成 DLX 行数据...")
        row_count = 0
        
        for row in range(N):
            row_perms = perms[row]
            print(f"  处理第 {row+1} 行，排列数: {len(row_perms):,}")
            
            for perm in row_perms:
                cols_tuple = []
                for col in range(N):
                    val = perm[col]
                    v = val - 1
                    cols_tuple.append(row * N + col)
                    cols_tuple.append(N2 + row * N + v)
                    cols_tuple.append(2*N2 + col * N + v)
                    b = get_box_id(row, col)
                    cols_tuple.append(3*N2 + b * N + v)
                dlx.add_row(tuple(cols_tuple))
                row_count += 1
        
        print(f"\n总行数: {row_count:,}")
        print(f"总列数: {total_cols}")
        
        print("\n执行 DLX 搜索...")
        solutions = dlx.search(max_solutions=1)
        
        if solutions:
            grid = [[0] * N for _ in range(N)]
            for col_idx in solutions[0]:
                name = dlx.col_names[col_idx]
                if name.startswith('cell['):
                    parts = name[5:-1].split(',')
                    r, c = int(parts[0]), int(parts[1])
                    for cc in solutions[0]:
                        cn = dlx.col_names[cc]
                        if cn.startswith(f'row[{r}]['):
                            val_str = cn[7:-1]
                            grid[r][c] = int(val_str)
                            break
            
            print("\n" + "=" * 70)
            print("  ✅ DLX 找到解!")
            print("=" * 70)
            
            print("\n解矩阵:")
            for r in range(N):
                row_str = " ".join(f"{v:3d}" for v in grid[r])
                print(f"  {row_str}")
            
            result = {
                "grid": grid,
                "method": "dlx_exact_cover",
                "search_time_seconds": time.time() - t0,
                "total_permutations": total_perms,
                "dlx_rows": row_count
            }
            with open(f"{base_dir}/solution.json", "w") as f:
                json.dump(result, f, indent=2)
        else:
            print("\n❌ DLX 也未找到解")
    
    print(f"\n总耗时: {time.time() - t0:.2f} 秒")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        traceback.print_exc()
        sys.exit(1)
