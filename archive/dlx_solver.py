#!/usr/bin/env python3
"""
DLX (Dancing Links) 精确覆盖算法求解 256 数独 (16×16)

核心思路：
- 符阖排列约束：每行必须选择该行许可的排列之一
- 标准数独约束：每行、每列、每宫数字 1-16 不重复
- 初始盘：92 个已知数字（由用户指定）

模型设计：
将问题建模为精确覆盖问题，但需要特殊处理符阖排列约束。

方法 A: 将"选择符阖排列 + 数字分配"作为行
  - 每行有 |perms| 种选择
  - 每种选择产生 64 个约束（16 cell × 4 维度）
  - 需要为每行选择恰好 1 个排列

方法 B: 使用对称差 DLX
  - 先在每行选择符阖排列（16 次选择，每次从该行 perm 中选 1 个）
  - 然后处理列/宫约束

这里使用方法 A，构建标准 DLX 精确覆盖问题。

列约束 (1024 列):
1. cell[r][c]: 每个格子必须有一个值 (256)
2. row[r][v]: 每行每个数字恰好出现一次 (256)
3. col[c][v]: 每列每个数字恰好出现一次 (256)
4. box[b][v]: 每宫每个数字恰好出现一次 (256)

行定义:
对于每行 r，从 perms[r] 中选择一个排列 p，
该排列在第 c 格填值为 p[c] (1-16)
生成 64 个约束：cell[r][c], row[r][p[c]], col[c][p[c]], box[r,c][p[c]]
"""

import json
import time
import sys
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

# =============================================================================
# 常量
# =============================================================================
N = 16  # 16×16 数独
N2 = N * N  # 256 个格子
N4 = 4 * N  # 1024 列
N_BOX = N // 4  # 每宫 4×4


def get_box_id(row: int, col: int) -> int:
    """获取格子所属的宫编号 (0-15)"""
    return (row // N_BOX) * N_BOX + (col // N_BOX)


def box_id_to_cells(box_id: int) -> List[Tuple[int, int]]:
    """获取某宫的所有格子坐标"""
    box_r = box_id // N_BOX
    box_c = box_id % N_BOX
    cells = []
    for r in range(box_r * N_BOX, (box_r + 1) * N_BOX):
        for c in range(box_c * N_BOX, (box_c + 1) * N_BOX):
            cells.append((r, c))
    return cells


# =============================================================================
# DLX 核心数据结构
# =============================================================================

class DLXNode:
    """DLX 节点 - 双向链表"""
    __slots__ = ['left', 'right', 'up', 'down', 'col']
    
    def __init__(self, column: 'DLXColumn'):
        self.col = column
        self.left = self.right = self
        self.up = self.down = self


class DLXColumn:
    """DLX 列头"""
    __slots__ = ['left', 'right', 'up', 'down', 'size', 'idx', 'name']
    
    def __init__(self, idx: int, name: str):
        self.idx = idx
        self.name = name
        self.size = 0
        self.left = self.right = self.up = self.down = self


class DancingLinksX:
    """
    Knuth's Algorithm X with Dancing Links
    
    精确覆盖：选择最少的行使得每列恰好有一个 1
    """
    
    def __init__(self, col_names: List[str]):
        self.col_names = col_names
        self.num_cols = len(col_names)
        
        # 创建列头
        self.cols = [DLXColumn(i, name) for i, name in enumerate(col_names)]
        self.root = DLXColumn(-1, "root")
        
        # 链接列头成循环链表
        for i in range(len(self.cols)):
            self._link_right(self.root, self.cols[i])
        
        # 存储行数据
        self.row_data: List[Tuple[int, ...]] = []
        
        # 当前解栈
        self._stack: List[int] = []
    
    def _link_right(self, l: DLXColumn, r: DLXColumn):
        l.right = r
        r.left = l
    
    def _link_down(self, u: DLXNode, d: DLXNode):
        u.down = d
        d.up = u
    
    def add_row(self, col_indices: Tuple[int, ...]) -> int:
        """添加一行，返回行索引"""
        nodes: List[DLXNode] = []
        first = None
        
        for cidx in col_indices:
            col = self.cols[cidx]
            node = DLXNode(col)
            
            # 垂直插入
            self._link_down(col.up, node)
            col.size += 1
            
            # 水平插入
            if first is None:
                first = node
            else:
                self._link_right(first.left, node)
            nodes.append(node)
        
        # 循环链接
        if first:
            self._link_right(first.left, first)
        
        self.row_data.append(col_indices)
        return len(self.row_data) - 1
    
    def cover(self, col: DLXColumn):
        """覆盖列"""
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
    
    def uncover(self, col: DLXColumn):
        """恢复列"""
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
    
    def search(self, depth: int = 0, max_solutions: int = 1) -> List[List[int]]:
        """Algorithm X 搜索"""
        solutions: List[List[int]] = []
        
        def recurse(k: int):
            if len(solutions) >= max_solutions:
                return True
            
            if self.root.right == self.root:
                # 找到解
                solutions.append(list(self._stack))
                return len(solutions) >= max_solutions
            
            # 启发式：选节点最少的列
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
                
                # 覆盖该行其他列
                j = r.right
                while j != r:
                    self.cover(j.col)
                    j = j.right
                
                if recurse(k + 1):
                    # 恢复
                    j = r.left
                    while j != r:
                        self.uncover(j.col)
                        j = j.left
                    self._stack.pop()
                    return True
                
                # 回溯
                j = r.left
                while j != r:
                    self.uncover(j.col)
                    j = j.left
                self._stack.pop()
                r = r.down
            
            self.uncover(min_col)
            return False
        
        recurse(0)
        return solutions
    
    def get_solution_grid(self, solution_row_indices: List[int]) -> List[List[int]]:
        """从解索引恢复 16×16 网格"""
        grid = [[0] * N for _ in range(N)]
        
        for row_idx in solution_row_indices:
            cols = self.row_data[row_idx]
            # cols 包含 64 个列索引：cell, row_val, col_val, box_val 各 16 个
            # 我们需要从中提取每格的值
            
            # 从 cell 约束推断
            for cidx in cols:
                name = self.col_names[cidx]
                if name.startswith('cell['):
                    # 解析 cell[r,c]
                    parts = name[5:-1].split(',')
                    r, c = int(parts[0]), int(parts[1])
                    
                    # 找到对应的值列
                    val_col = None
                    for cc in cols:
                        cn = self.col_names[cc]
                        if cn.startswith(f'row[{r}]['):
                            val_str = cn[7:-1]
                            grid[r][c] = int(val_str)
                            break
        
        return grid


# =============================================================================
# 256 数独 DLX 构建器
# =============================================================================

class Sudoku256DLXBuilder:
    """构建 256 数独的 DLX 精确覆盖问题"""
    
    def __init__(self, known_digits: List[Tuple[int, int, int]], 
                 row_perms: List[List[List[int]]]):
        """
        known_digits: [(row, col, value), ...] 0-indexed
        row_perms: [row][perm_idx][col] = value (1-16)
        """
        self.known_digits = known_digits
        self.row_perms = row_perms
        
        # 已知数字映射
        self.known_map: dict[Tuple[int, int], int] = {}
        for r, c, v in known_digits:
            self.known_map[(r, c)] = v
    
    def _cell_col(self, r: int, c: int) -> int:
        """cell[r,c] 列索引"""
        return r * N + c
    
    def _row_val_col(self, r: int, v: int) -> int:
        """row[r][v] 列索引"""
        return N2 + r * N + v
    
    def _col_val_col(self, c: int, v: int) -> int:
        """col[c][v] 列索引"""
        return 2 * N2 + c * N + v
    
    def _box_val_col(self, r: int, c: int, v: int) -> int:
        """box[b][v] 列索引"""
        b = get_box_id(r, c)
        return 3 * N2 + b * N + v
    
    def _col_name(self, idx: int) -> str:
        """列索引 -> 列名"""
        if idx < N2:
            r, c = divmod(idx, N)
            return f'cell[{r},{c}]'
        elif idx < 2 * N2:
            r, v = divmod(idx - N2, N)
            return f'row[{r}][{v+1}]'
        elif idx < 3 * N2:
            c, v = divmod(idx - 2*N2, N)
            return f'col[{c}][{v+1}]'
        else:
            b, v = divmod(idx - 3*N2, N)
            return f'box[{b}][{v+1}]'
    
    def build(self, verbose: bool = True) -> Tuple[DancingLinksX, int]:
        """
        构建 DLX 问题
        
        返回: (dlx 实例, 总行数)
        """
        # 创建列名
        col_names = []
        for i in range(N4):
            col_names.append(self._col_name(i))
        
        dlx = DancingLinksX(col_names)
        
        # 生成所有可能的行
        total_rows = 0
        
        for row in range(N):
            perms = self.row_perms[row]
            known_in_row = {c: v for (r, c), v in self.known_map.items() if r == row}
            
            if verbose and row % 2 == 0:
                print(f"  第 {row+1:2d} 行: {len(perms):>8d} 个排列, {len(known_in_row)} 个已知数字")
            
            for perm in perms:
                # 检查是否符合已知数字
                valid = True
                for col in range(N):
                    val = perm[col]
                    if col in known_in_row and known_in_row[col] != val:
                        valid = False
                        break
                
                if not valid:
                    continue
                
                # 检查是否有列冲突（提前剪枝）
                # 同一列不能有两个不同的值
                # 但这里是单行的排列，不涉及跨行检查
                
                # 生成约束列
                cols_tuple = []
                for col in range(N):
                    val = perm[col]  # 1-16
                    v = val - 1  # 0-15
                    
                    cols_tuple.append(self._cell_col(row, col))
                    cols_tuple.append(self._row_val_col(row, v))
                    cols_tuple.append(self._col_val_col(col, v))
                    cols_tuple.append(self._box_val_col(row, col, v))
                
                dlx.add_row(tuple(cols_tuple))
                total_rows += 1
        
        if verbose:
            print(f"\n总行数: {total_rows:,}")
            print(f"平均每行覆盖列数: {len(col_names) * total_rows / max(total_rows, 1):.0f}")
        
        return dlx, total_rows


# =============================================================================
# 主函数
# =============================================================================

def load_permutations() -> List[List[List[int]]]:
    """加载符阖排列"""
    perms = []
    for i in range(1, 17):
        filepath = f'A{i}_permutations.json'
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            perms.append(data['permutations'])
    
    total = sum(len(p) for p in perms)
    print(f"符阖排列加载完成，总计 {total:,} 个排列:")
    for i, p in enumerate(perms):
        print(f"  A{i+1:2d}: {len(p):>10,} 个排列")
    
    return perms


def load_initial_puzzle() -> List[Tuple[int, int, int]]:
    """加载初始盘 92 个已知数字"""
    with open('initial_puzzle.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    known = [(d['row'] - 1, d['col'] - 1, d['value']) for d in data['known_digits']]
    print(f"初始盘加载完成: {len(known)} 个已知数字")
    
    return known


def validate_solution(grid: List[List[int]], known_map: dict, 
                      row_perms: List[List[List[int]]]) -> bool:
    """验证解的正确性"""
    errors = []
    
    # 1. 检查已知数字
    for (r, c), val in known_map.items():
        if grid[r][c] != val:
            errors.append(f"已知数字冲突: grid[{r}][{c}]={grid[r][c]}, 应为 {val}")
    
    # 2. 检查行约束
    for r in range(N):
        row_vals = grid[r]
        if len(set(row_vals)) != N:
            errors.append(f"行 {r+1} 有重复数字")
        if tuple(row_vals) not in tuple(tuple(p) for p in row_perms[r]):
            errors.append(f"行 {r+1} 的排列不在符阖排列中")
    
    # 3. 检查列约束
    for c in range(N):
        col_vals = [grid[r][c] for r in range(N)]
        if len(set(col_vals)) != N:
            errors.append(f"列 {c+1} 有重复数字")
    
    # 4. 检查宫约束
    for b in range(N):
        box_vals = []
        for r in range(N_BOX):
            for c in range(N_BOX):
                gr = (b // N_BOX) * N_BOX + r
                gc = (b % N_BOX) * N_BOX + c
                box_vals.append(grid[gr][gc])
        if len(set(box_vals)) != N:
            errors.append(f"宫 {b+1} 有重复数字")
    
    return len(errors) == 0, errors


def main():
    print("=" * 70)
    print("  DLX 精确覆盖算法求解 256 数独 (16×16)")
    print("  符阖排列约束 + 标准数独约束 + 已知数字")
    print("=" * 70)
    
    t0 = time.time()
    
    # 1. 加载符阖排列
    print("\n[1/4] 加载符阖排列...")
    row_perms = load_permutations()
    
    # 2. 加载初始盘
    print("\n[2/4] 加载初始盘...")
    known_digits = load_initial_puzzle()
    known_map = {(r, c): v for r, c, v in known_digits}
    print(f"      已知数字: {len(known_digits)} 个")
    
    # 3. 构建 DLX 问题
    print("\n[3/4] 构建 DLX 精确覆盖问题...")
    builder = Sudoku256DLXBuilder(known_digits, row_perms)
    dlx, total_rows = builder.build(verbose=True)
    
    # 4. 求解
    print("\n[4/4] 执行 DLX 搜索...")
    print(f"      列数: {dlx.num_cols}")
    print(f"      行数: {total_rows:,}")
    
    t1 = time.time()
    print(f"      构建时间: {t1 - t0:.2f} 秒")
    
    solutions = dlx.search(max_solutions=1)
    
    t2 = time.time()
    print(f"      搜索时间: {t2 - t1:.2f} 秒")
    print(f"      找到解数: {len(solutions)}")
    
    if solutions:
        print("\n" + "=" * 70)
        print("  ✅ 找到解!")
        print("=" * 70)
        
        # 从解中提取网格
        grid = dlx.get_solution_grid(solutions[0])
        
        # 打印网格
        print("\n解矩阵:")
        for r in range(N):
            row_str = " ".join(f"{v:3d}" for v in grid[r])
            print(f"  {row_str}")
        
        # 验证
        print("\n验证解...")
        valid, errors = validate_solution(grid, known_map, row_perms)
        
        if valid:
            print("  ✅ 解验证通过!")
        else:
            print("  ❌ 解验证失败:")
            for e in errors[:10]:
                print(f"    {e}")
        
        # 保存解
        with open('solution.json', 'w', encoding='utf-8') as f:
            json.dump({
                "grid": grid,
                "known_digits_count": len(known_digits),
                "total_permutations_used": total_rows,
                "search_time_seconds": t2 - t1
            }, f, indent=2, ensure_ascii=False)
        print(f"\n解已保存到 solution.json")
    else:
        print("\n" + "=" * 70)
        print("  ❌ 未找到解")
        print("=" * 70)
        print("\n可能的原因:")
        print("  1. 符阖排列与已知数字存在冲突")
        print("  2. 初始盘数据有误")
        print("  3. 该数独无解")
    
    t3 = time.time()
    print(f"\n总耗时: {t3 - t0:.2f} 秒")


if __name__ == '__main__':
    main()
