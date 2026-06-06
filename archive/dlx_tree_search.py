#!/usr/bin/env python3
"""
DLX 精确覆盖 + 树状博弈剪枝 + 欧拉路径启发式求解器
融合五维思维框架的 256 数独求解
"""

import json
import time
import sys
import traceback
import math
from collections import defaultdict, Counter
from typing import List, Dict, Set, Tuple, Optional
from copy import deepcopy

N = 16
N2 = N * N

def get_box_id(row, col):
    return (row // 4) * 4 + (col // 4)

# ============== 欧拉路径启发式 ==============

class EulerPathHeuristic:
    """欧拉路径启发式：将每行视为欧拉图中的节点，使用最优路径选择"""
    
    def __init__(self, perms: List[List[List[int]]]):
        """
        perms[row][perm_idx][col] = value (1-16)
        """
        self.perms = perms
        self.row_count = N
        self._build_conflict_graph()
        self._compute_edge_weights()
        
    def _build_conflict_graph(self):
        """构建冲突图：两行排列之间的列冲突统计"""
        # conflict[row_i][row_j][value_i][value_j] = conflict_count
        self.conflicts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
        for i in range(self.row_count):
            for j in range(i + 1, self.row_count):
                for vi, perm_i in enumerate(self.perms[i]):
                    for vj, perm_j in enumerate(self.perms[j]):
                        # 检查列冲突
                        for c in range(N):
                            if perm_i[c] == perm_j[c]:  # 同列同值冲突
                                self.conflicts[i][j][(perm_i[c], perm_j[c])] += 1
    
    def _compute_edge_weights(self):
        """计算行间的边权重（冲突越少越好）"""
        self.edge_weights = {}
        for i in range(self.row_count):
            for j in range(i + 1, self.row_count):
                total_conflict = 0
                for c in range(N):
                    for perm_i in self.perms[i]:
                        for perm_j in self.perms[j]:
                            if perm_i[c] == perm_j[c]:
                                total_conflict += 1
                self.edge_weights[(i, j)] = total_conflict
    
    def get_row_order(self) -> List[int]:
        """基于冲突图生成最优行搜索顺序（欧拉路径启发）"""
        # 使用贪心策略：先选冲突少的行
        rows = list(range(N))
        # 按总冲突度排序
        total_conflict = {}
        for i in range(N):
            total = sum(self.edge_weights.get((min(i, j), max(i, j)), 0) 
                       for j in range(N) if j != i)
            total_conflict[i] = total
        
        # 按冲突从少到多排序（先确定冲突少的行）
        return sorted(rows, key=lambda r: total_conflict[r])
    
    def get_perm_candidates(self, row: int, fixed_values: Dict[Tuple[int, int], int]) -> List[Tuple[int, List[int], int]]:
        """
        获取某行可能的排列（按得分排序）
        返回: [(score, permutation, permutation_index)]
        """
        candidates = []
        for idx, perm in enumerate(self.perms[row]):
            score = 1000  # 基础分
            
            # 检查与已固定值的冲突
            for (fr, fc), fval in fixed_values.items():
                if fr == row:
                    if perm[fc] != fval:
                        score -= 100  # 严重冲突
                # 检查列冲突
                col_val = perm[fc] if fc < N else 0
                # 这里检查列的唯一性约束
                for other_row in range(N):
                    if other_row != row and other_row in fixed_values:
                        for oc in range(N):
                            if (other_row, oc) in fixed_values:
                                if oc == fc and fixed_values[(other_row, oc)] == col_val:
                                    score -= 10
            
            candidates.append((score, perm, idx))
        
        candidates.sort(reverse=True)
        return candidates


# ============== 树状博弈剪枝引擎 ==============

class TreePruningEngine:
    """树状博弈剪枝引擎：MRV + 前向检查 + 约束传播"""
    
    def __init__(self, perms: List[List[List[int]]], col_constraints: Dict[int, Set[int]] = None):
        self.perms = perms
        self.col_constraints = col_constraints or {c: set(range(1, 17)) for c in range(N)}
        self.forward_check = True
        self.arc_consistency = True
        
    def get_domain(self, row: int, col: int, fixed_grid: List[List[int]]) -> Set[int]:
        """获取单元格的合法域"""
        domain = set(range(1, 17))
        
        # 同行约束（来自行的符阖排列）
        if self.perms[row]:
            possible_in_row = set()
            for perm in self.perms[row]:
                possible_in_row.add(perm[col])
            domain &= possible_in_row
        
        # 同列已填值
        for r in range(N):
            if r != row and fixed_grid[r][col] != 0:
                domain.discard(fixed_grid[r][col])
        
        # 同列约束
        domain &= self.col_constraints.get(col, set(range(1, 17)))
        
        # 同宫格已填值
        box_row = row // 4
        box_col = col // 4
        for r in range(box_row * 4, box_row * 4 + 4):
            for c in range(box_col * 4, box_col * 4 + 4):
                if r != row or c != col:
                    if fixed_grid[r][c] != 0:
                        domain.discard(fixed_grid[r][c])
        
        return domain
    
    def select_best_cell(self, fixed_grid: List[List[int]]) -> Optional[Tuple[int, int, Set[int]]]:
        """MRV: 选择剩余值最少的单元格"""
        best_cell = None
        min_domain_size = float('inf')
        
        for r in range(N):
            for c in range(N):
                if fixed_grid[r][c] == 0:
                    domain = self.get_domain(r, c, fixed_grid)
                    if len(domain) < min_domain_size:
                        min_domain_size = len(domain)
                        best_cell = (r, c, domain)
                        if min_domain_size == 1:
                            return best_cell
        
        return best_cell
    
    def propagate_constraints(self, grid: List[List[int]], 
                            cell_values: Dict[Tuple[int, int], int]) -> Tuple[bool, Dict[Tuple[int, int], Set[int]]]:
        """
        AC-3 式约束传播
        返回: (是否成功, 剩余域)
        """
        domains = {}
        for r in range(N):
            for c in range(N):
                if cell_values.get((r, c), 0) == 0:
                    domains[(r, c)] = self.get_domain(r, c, grid)
                else:
                    domains[(r, c)] = {cell_values[(r, c)]}
        
        # AC-3
        queue = list(domains.keys())
        while queue:
            (r, c) = queue.pop(0)
            current_domain = domains[(r, c)]
            
            if len(current_domain) == 0:
                return False, domains
            
            # 检查同行
            for cc in range(N):
                if cc != c:
                    old_size = len(domains[(r, cc)])
                    # 移除与当前单元格冲突的值
                    for v in list(domains[(r, cc)].keys()):
                        if v in current_domain:
                            domains[(r, cc)].discard(v)
                    if len(domains[(r, cc)]) == 0:
                        return False, domains
                    if len(domains[(r, cc)]) < old_size and cc not in queue:
                        queue.append((r, cc))
            
            # 检查同列
            for rr in range(N):
                if rr != r:
                    old_size = len(domains[(rr, c)])
                    for v in list(domains[(rr, c)].keys()):
                        if v in current_domain:
                            domains[(rr, c)].discard(v)
                    if len(domains[(rr, c)]) == 0:
                        return False, domains
                    if len(domains[(rr, c)]) < old_size and (rr, c) not in queue:
                        queue.append((rr, c))
        
        return True, domains


# ============== DLX 精确覆盖核心 ==============

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


# ============== 混合求解器 ==============

class HybridSolver:
    """融合 DLX + 树搜索 + 欧拉路径启发的混合求解器"""
    
    def __init__(self, perms: List[List[List[int]]], col_constraints: Dict[int, Set[int]] = None):
        self.perms = perms
        self.col_constraints = col_constraints or {c: set(range(1, 17)) for c in range(N)}
        self.euler_heuristic = EulerPathHeuristic(perms)
        self.pruning_engine = TreePruningEngine(perms, col_constraints)
        
    def verify_solution(self, grid: List[List[int]]) -> Tuple[bool, List[str]]:
        """验证解的正确性"""
        errors = []
        
        # 1. 每行 16 个数字不重复
        for r in range(N):
            if len(set(grid[r])) != N:
                errors.append(f"行 {r+1} 有重复数字: {grid[r]}")
        
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
        
        # 4. 每行排列必须在符阖排列中
        for r in range(N):
            row_tuple = tuple(grid[r])
            if row_tuple not in tuple(tuple(p) for p in self.perms[r]):
                errors.append(f"行 {r+1} 的排列不在符阖排列中")
        
        return len(errors) == 0, errors
    
    def solve_with_dlx(self) -> Optional[List[List[int]]]:
        """使用 DLX 精确覆盖求解"""
        print("\n" + "=" * 70)
        print("  [DLX 模式] 构建精确覆盖矩阵")
        print("=" * 70)
        
        t0 = time.time()
        
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
        
        # 生成所有可能的行（每行选择符阖排列中的一个排列）
        print("\n生成 DLX 行数据...")
        row_count = 0
        
        for row in range(N):
            row_perms = self.perms[row]
            if row % 2 == 0:
                print(f"  处理第 {row+1} 行，排列数: {len(row_perms):,}")
            
            for perm in row_perms:
                cols_tuple = []
                for col in range(N):
                    val = perm[col]  # 1-16
                    v = val - 1  # 0-15
                    cols_tuple.append(row * N + col)           # cell[r,c]
                    cols_tuple.append(N2 + row * N + v)         # row[r][v]
                    cols_tuple.append(2*N2 + col * N + v)       # col[c][v]
                    b = get_box_id(row, col)
                    cols_tuple.append(3*N2 + b * N + v)         # box[b][v]
                dlx.add_row(tuple(cols_tuple))
                row_count += 1
        
        print(f"\n总行数: {row_count:,}")
        print(f"总列数: {total_cols}")
        print(f"构建时间: {time.time() - t0:.2f} 秒")
        
        # 执行搜索
        print("\n执行 DLX 搜索...")
        t2 = time.time()
        solutions = dlx.search(max_solutions=1)
        t3 = time.time()
        
        print(f"搜索时间: {t3 - t2:.2f} 秒")
        
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
            
            return grid
        
        return None
    
    def solve_with_tree_search(self, time_limit: float = 300.0) -> Optional[List[List[int]]]:
        """使用树搜索 + 剪枝求解（融合欧拉路径启发）"""
        print("\n" + "=" * 70)
        print("  [树搜索模式] 融合欧拉路径启发 + 树状博弈剪枝")
        print("=" * 70)
        
        t0 = time.time()
        
        # 获取最优行顺序
        row_order = self.euler_heuristic.get_row_order()
        print(f"\n最优行搜索顺序: {[r+1 for r in row_order]}")
        
        # 使用树搜索
        grid = [[0] * N for _ in range(N)]
        self.solutions = []
        
        def backtrack(row_idx: int = 0) -> bool:
            elapsed = time.time() - t0
            if elapsed > time_limit:
                print(f"⏰ 时间限制 {time_limit}秒已达")
                return False
            
            if row_idx >= N:
                # 找到完整解
                self.solutions.append(deepcopy(grid))
                print(f"✓ 找到解 #{len(self.solutions)} | 耗时 {elapsed:.1f}秒")
                return True
            
            # 按欧拉路径顺序选择行
            row = row_order[row_idx]
            
            # 获取该行候选排列
            candidates = self.euler_heuristic.get_perm_candidates(row, {})
            
            for _, perm, _ in candidates[:100]:  # 剪枝，只尝试前100个
                # 验证列约束
                valid = True
                for col in range(N):
                    val = perm[col]
                    # 检查列是否已有该值
                    for other_row in range(N):
                        if grid[other_row][col] == val:
                            valid = False
                            break
                    if not valid:
                        break
                
                if valid:
                    grid[row] = perm[:]
                    if backtrack(row_idx + 1):
                        return True
                    grid[row] = [0] * N
            
            return False
        
        if backtrack():
            return self.solutions[0]
        
        return None


def load_perms_from_json(base_dir: str) -> List[List[List[int]]]:
    """从 JSON 文件加载符阖排列"""
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
    print("  🎯 DLX + 树状博弈剪枝 + 欧拉路径 混合求解器")
    print("  256 数独 (16×16) | 符阖排列约束 + 列约束")
    print("=" * 70)
    
    t0 = time.time()
    base_dir = r"D:/2026/WPF_Sudoku/Sudoku_256"
    
    # 加载符阖排列
    print("\n[1/4] 加载符阖排列...")
    perms = load_perms_from_json(base_dir)
    
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
        print(f"  已加载 {len(col_constraints)} 列约束")
    except Exception as e:
        print(f"  未找到列约束文件，使用全约束 (1-16)")
        col_constraints = {c: set(range(1, 17)) for c in range(N)}
    
    # 初始化混合求解器
    print("\n[3/4] 初始化混合求解器...")
    solver = HybridSolver(perms, col_constraints)
    
    # 策略 1: DLX 精确覆盖
    print("\n" + "=" * 70)
    print("  ▶ 策略 1: DLX 精确覆盖算法")
    print("=" * 70)
    dlx_solution = solver.solve_with_dlx()
    
    if dlx_solution:
        print("\n" + "=" * 70)
        print("  ✅ DLX 找到解!")
        print("=" * 70)
        
        # 验证
        valid, errors = solver.verify_solution(dlx_solution)
        
        if valid:
            print("\n验证结果: ✅ 全部通过!")
        else:
            print("\n验证结果: ❌ 部分失败")
            for e in errors:
                print(f"  {e}")
        
        # 打印解
        print("\n解矩阵:")
        for r in range(N):
            row_str = " ".join(f"{v:3d}" for v in dlx_solution[r])
            print(f"  {row_str}")
        
        # 保存
        result = {
            "grid": dlx_solution,
            "method": "DLX_exact_cover",
            "search_time_seconds": time.time() - t0,
            "verification": "passed" if valid else "failed",
            "errors": errors,
            "total_permutations": total_perms,
            "row_constraints": [len(p) for p in perms],
            "column_constraints": {k: list(v) for k, v in col_constraints.items()}
        }
        with open(f"{base_dir}/solution.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n解已保存到 solution.json")
        print(f"总耗时: {time.time() - t0:.2f} 秒")
        return
    
    # 策略 2: 树搜索（如果 DLX 失败）
    print("\n" + "=" * 70)
    print("  ▶ 策略 2: 树搜索 + 欧拉路径启发")
    print("=" * 70)
    
    tree_solution = solver.solve_with_tree_search(time_limit=300.0)
    
    if tree_solution:
        print("\n" + "=" * 70)
        print("  ✅ 树搜索找到解!")
        print("=" * 70)
        
        valid, errors = solver.verify_solution(tree_solution)
        
        if valid:
            print("\n验证结果: ✅ 全部通过!")
        else:
            print("\n验证结果: ❌ 部分失败")
            for e in errors:
                print(f"  {e}")
        
        print("\n解矩阵:")
        for r in range(N):
            row_str = " ".join(f"{v:3d}" for v in tree_solution[r])
            print(f"  {row_str}")
        
        result = {
            "grid": tree_solution,
            "method": "tree_search_euler_heuristic",
            "search_time_seconds": time.time() - t0,
            "verification": "passed" if valid else "failed",
            "errors": errors,
            "total_permutations": total_perms
        }
        with open(f"{base_dir}/solution.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n解已保存到 solution.json")
    else:
        print("\n" + "=" * 70)
        print("  ❌ 未找到解")
        print("=" * 70)
    
    print(f"\n总耗时: {time.time() - t0:.2f} 秒")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        traceback.print_exc()
        sys.exit(1)
