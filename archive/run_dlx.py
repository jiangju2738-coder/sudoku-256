#!/usr/bin/env python3
"""
DLX 精确覆盖求解 256 数独 (16×16)
使用符阖排列约束，全空初始盘（0 个已知数字）
"""

import json
import time
import sys
import os

os.chdir('d:/2026/WPF_Sudoku/Sudoku_256')

N = 16
N2 = N * N
N4 = 4 * N

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
                        j = j.right
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

def main():
    print("=" * 70)
    print("  DLX 精确覆盖求解 256 数独 (16×16)")
    print("  符阖排列约束 + 全空初始盘")
    print("=" * 70)

    t0 = time.time()

    # 加载符阖排列
    print("\n[1/4] 加载符阖排列...")
    perms = []
    for i in range(1, 17):
        with open(f"A{i}_permutations.json", "r") as f:
            data = json.load(f)
            perms.append(data["permutations"])

    total_perms = sum(len(p) for p in perms)
    print(f"  总排列数: {total_perms:,}")
    for i, p in enumerate(perms):
        print(f"  第{i+1:2d}行: {len(p):>10,} 个排列")

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

    # 生成所有可能的行
    print("\n[2/4] 生成 DLX 行数据...")
    row_count = 0

    for row in range(N):
        row_perms = perms[row]
        if row % 2 == 0:
            print(f"  处理第 {row+1} 行，排列数: {len(row_perms):,}")

        for perm in row_perms:
            cols_tuple = []
            for col in range(N):
                val = perm[col]  # 1-16
                v = val - 1  # 0-15
                # cell[r,c]
                cols_tuple.append(row * N + col)
                # row[r][v]
                cols_tuple.append(N2 + row * N + v)
                # col[c][v]
                cols_tuple.append(2*N2 + col * N + v)
                # box[b][v]
                b = get_box_id(row, col)
                cols_tuple.append(3*N2 + b * N + v)
            dlx.add_row(tuple(cols_tuple))
            row_count += 1

    print(f"\n总行数: {row_count:,}")
    print(f"总列数: {total_cols}")
    t1 = time.time()
    print(f"构建时间: {t1 - t0:.2f} 秒")

    # 求解
    print("\n[3/4] 执行 DLX 搜索...")
    t2 = time.time()
    solutions = dlx.search(max_solutions=1)
    t3 = time.time()

    print(f"搜索时间: {t3 - t2:.2f} 秒")
    print(f"找到解数: {len(solutions)}")

    if solutions:
        print("\n" + "=" * 70)
        print("  ✅ 找到解!")
        print("=" * 70)

        # 从解恢复网格
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

        print("\n解矩阵:")
        for r in range(N):
            row_str = " ".join(f"{v:3d}" for v in grid[r])
            print(f"  {row_str}")

        # 验证
        print("\n验证解...")
        errors = []

        # 行约束
        for r in range(N):
            row_vals = grid[r]
            if len(set(row_vals)) != N:
                errors.append(f"行 {r+1} 有重复数字")
            if tuple(row_vals) not in tuple(tuple(p) for p in perms[r]):
                errors.append(f"行 {r+1} 的排列不在符阖排列中")

        # 列约束
        for c in range(N):
            col_vals = [grid[r][c] for r in range(N)]
            if len(set(col_vals)) != N:
                errors.append(f"列 {c+1} 有重复数字")

        # 宫约束
        for b in range(N):
            box_vals = []
            for r in range(4):
                for c in range(4):
                    gr = (b // 4) * 4 + r
                    gc = (b % 4) * 4 + c
                    box_vals.append(grid[gr][gc])
            if len(set(box_vals)) != N:
                errors.append(f"宫 {b+1} 有重复数字")

        if not errors:
            print("  ✅ 解验证通过!")
        else:
            print("  ❌ 解验证失败:")
            for e in errors[:5]:
                print(f"    {e}")

        # 保存
        result = {
            "grid": grid,
            "known_digits_count": 0,
            "total_permutations": total_perms,
            "dlx_rows": row_count,
            "search_time_seconds": t3 - t2,
            "verification": "passed" if not errors else "failed",
            "errors": errors
        }
        with open("solution.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\n解已保存到 solution.json")
    else:
        print("\n" + "=" * 70)
        print("  ❌ 未找到解")
        print("=" * 70)
        print("\n可能原因:")
        print("  1. 符阖排列约束过于严格")
        print("  2. 行之间排列冲突")
        print("  3. 需要检查符阖排列数据")

    t4 = time.time()
    print(f"\n总耗时: {t4 - t0:.2f} 秒")

if __name__ == "__main__":
    main()
