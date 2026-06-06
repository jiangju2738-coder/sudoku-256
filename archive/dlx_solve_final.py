#!/usr/bin/env python3
"""
DLX 精确覆盖求解 256 数独 (16×16)
正确实现：确保所有行、列、宫、符阖排列约束满足
"""

import json
import time
import sys

N = 16
N2 = N * N

def get_box_id(row, col):
    return (row // 4) * 4 + (col // 4)

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
        self.cols = [DLXColumn(i, name) for i, name in enumerate(col_names)]
        self.root = DLXColumn(-1, "root")
        for i in range(len(self.cols)):
            self._link_right(self.root, self.cols[i])
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


def verify_solution(grid, perms):
    """完整验证解的正确性"""
    errors = []
    
    # 1. 每行 16 个数字不重复
    for r in range(N):
        if len(set(grid[r])) != N:
            errors.append(f"行 {r+1} 有重复数字")
        # 2. 每行排列必须在符阖排列中
        if tuple(grid[r]) not in tuple(tuple(p) for p in perms[r]):
            errors.append(f"行 {r+1} 不在符阖排列中")
    
    # 2. 每列 16 个数字不重复
    for c in range(N):
        col_vals = [grid[r][c] for r in range(N)]
        if len(set(col_vals)) != N:
            errors.append(f"列 {c+1} 有重复数字")
    
    # 3. 每宫 16 个数字不重复
    for b in range(N):
        box_vals = []
        br, bc = b // 4, b % 4
        for r in range(4):
            for c in range(4):
                box_vals.append(grid[br*4 + r][bc*4 + c])
        if len(set(box_vals)) != N:
            errors.append(f"宫 {b+1} 有重复数字")
    
    return len(errors) == 0, errors


def main():
    print("=" * 70)
    print("  🎯 DLX 精确覆盖求解 256 数独 (16×16)")
    print("  符阖排列约束 + 列约束 + 宫约束")
    print("=" * 70)
    
    t0 = time.time()
    base_dir = r"D:/2026/WPF_Sudoku/Sudoku_256"
    
    # 加载符阖排列
    print("\n[1/4] 加载符阖排列...")
    perms = []
    for i in range(1, 17):
        with open(f"{base_dir}/A{i}_permutations.json", "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                perms.append(data)
            else:
                perms.append(data["permutations"])
    
    total_perms = sum(len(p) for p in perms)
    print(f"  总排列数: {total_perms:,}")
    for i, p in enumerate(perms):
        print(f"  第{i+1:2d}行: {len(p):>10,} 个排列")
    
    # 加载列约束
    print("\n[2/4] 加载列约束...")
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
        # 统计约束情况
        full_cols = sum(1 for c in range(N) if len(col_constraints[c]) == 16)
        limited_cols = N - full_cols
        print(f"  完全约束列: {full_cols}，有限约束列: {limited_cols}")
        for c in range(N):
            if len(col_constraints[c]) < 16:
                missing = set(range(1, 17)) - col_constraints[c]
                print(f"    第{c+1}列 缺失: {sorted(missing)}")
    except Exception as e:
        print(f"  未找到列约束文件，使用全约束 (1-16)")
        col_constraints = {c: set(range(1, 17)) for c in range(N)}
    
    # 构建 DLX 精确覆盖模型
    # 列: 256 个 cell + 256 个 row-value + 256 个 col-value + 256 个 box-value = 1024 列
    print("\n[3/4] 构建 DLX 矩阵...")
    
    # 添加列约束过滤
    # 每行选择符阖排列中的一个，确保列值不冲突
    
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
    
    row_count = 0
    print("\n  生成行数据（符阖排列 × 列约束过滤）...")
    
    for row in range(N):
        row_perms = perms[row]
        allowed_cols = col_constraints
        
        if row % 2 == 0:
            print(f"    第{row+1}行: {len(row_perms):,} 个排列", end="")
        
        count_before = row_count
        
        for perm in row_perms:
            # 检查列约束：perm[c] 是否在该列的允许值中
            valid = True
            for c in range(N):
                val = perm[c]
                if val not in allowed_cols.get(c, set(range(1, 17))):
                    valid = False
                    break
            if not valid:
                continue
            
            # 生成 DLX 行
            cols_tuple = []
            for c in range(N):
                val = perm[c]  # 1-16
                v = val - 1    # 0-15
                
                # cell[row, c]
                cols_tuple.append(row * N + c)
                # row[row][val]
                cols_tuple.append(N2 + row * N + v)
                # col[c][val]
                cols_tuple.append(2*N2 + c * N + v)
                # box[b][val]
                b = get_box_id(row, c)
                cols_tuple.append(3*N2 + b * N + v)
            
            dlx.add_row(tuple(cols_tuple))
            row_count += 1
        
        filtered = row_count - count_before
        if row % 2 == 0:
            print(f" → 通过列约束: {filtered:,}")
    
    print(f"\n  总行数（过滤后）: {row_count:,}")
    print(f"  总列数: {total_cols}")
    print(f"  构建耗时: {time.time() - t0:.2f} 秒")
    
    # 执行 DLX 搜索
    print("\n[4/4] 执行 DLX 搜索...")
    t_search = time.time()
    solutions = dlx.search(max_solutions=1)
    t_end = time.time()
    
    print(f"  搜索耗时: {t_end - t_search:.2f} 秒")
    
    if solutions:
        # 恢复网格
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
        
        # 验证
        valid, errors = verify_solution(grid, perms)
        
        print("\n验证结果:")
        if valid:
            print("  ✅ 全部通过!")
        else:
            print("  ❌ 部分失败:")
            for e in errors[:10]:
                print(f"    {e}")
        
        print("\n解矩阵:")
        for r in range(N):
            row_str = " ".join(f"{v:3d}" for v in grid[r])
            print(f"  {row_str}")
        
        # 额外统计
        print("\n统计:")
        for r in range(N):
            row_vals = grid[r]
            # 检查该行是哪个排列
            for pi, perm in enumerate(perms[r]):
                if perm == row_vals:
                    print(f"  第{r+1}行 = 排列 #{pi+1}")
                    break
        
        result = {
            "grid": grid,
            "method": "dlx_exact_cover",
            "search_time_seconds": t_end - t_search,
            "total_build_time": t_end - t0,
            "verification": "passed" if valid else "failed",
            "errors": errors,
            "total_permutations": total_perms,
            "dlx_rows": row_count,
            "column_constraints": {k: list(v) for k, v in col_constraints.items()}
        }
        with open(f"{base_dir}/solution.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ 解已保存到 solution.json")
    else:
        print("\n" + "=" * 70)
        print("  ❌ 未找到解")
        print("=" * 70)
        print("\n可能原因:")
        print("  1. 符阖排列与列约束冲突")
        print("  2. 列约束过于严格")
        print("  3. 数据需要进一步检查")
    
    print(f"\n总耗时: {t_end - t0:.2f} 秒")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"\n❌ 执行出错: {e}")
        traceback.print_exc()
        sys.exit(1)
