#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
約束傳播引擎 - AC-3 弧一致性 + 符闔排列過濾

提供兩種互補的約束傳播策略:

1. PermutationFilter  - 基於已知值/列/宮約束過濾符闔排列
2. AC3Propagator      - AC-3 弧一致性約束傳播 (純 Python, 不依賴排列文件)

兩者可以組合使用: 先用 PermutationFilter 大幅剪枝,
再用 AC3Propagator 做更細粒度的推導。
"""

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from .constants import N, BOX_SIZE, VALUES, box_index


# ═══════════════════════════════════════════════════════════════
#  符闔排列過濾器
# ═══════════════════════════════════════════════════════════════

class PermutationFilter:
    """
    基於已知錨點的符闔排列預過濾。

    過濾策略 (三層遞進):
      層1: 已知值匹配 - 排列必須與所有已知錨點一致
      層2: 列衝突檢查 - 排列中的值不能與同列已知值衝突
      層3: 宮衝突檢查 - 排列中的值不能與同宮已知值衝突
    """

    def __init__(self, grid: List[List[int]],
                 permutation_sets: List[List[List[int]]],
                 fuhe_rows: Set[int] = None):
        """
        參數:
            grid: 16x16 初始網格
            permutation_sets: 每行的符闔排列集合
            fuhe_rows: 符闔行索引集合 (這些行之間的宮衝突視為預期行為)
                       默認: {2, 3, 8} (C, D, I 行)
        """
        self.grid = grid
        self.permutation_sets = permutation_sets
        self.fuhe_rows = fuhe_rows if fuhe_rows is not None else {2, 3, 8}
        self._precompute_constraints()

    def _is_full_row(self, r: int) -> bool:
        """判斷某行是否完全固定 (16個值全非零)"""
        return all(self.grid[r][c] != 0 for c in range(N))

    def _precompute_constraints(self):
        """
        預計算列和宮的已用值集合。

        衝突分類:
          - 致命衝突: 同行值重複 (數據錯誤)
          - 警告衝突: 符闔行之間的宮衝突 (預期行為, 不阻止求解)
          - 一般衝突: 非符闔行之間的列/宮衝突 (數據不一致)
        """
        self.col_used: List[Set[int]] = [set() for _ in range(N)]
        self.box_used: List[Set[int]] = [set() for _ in range(N)]
        self.row_used: List[Set[int]] = [set() for _ in range(N)]
        self.fatal_conflicts: List[str] = []
        self.warnings: List[str] = []

        # 識別完全固定的符闔行
        fixed_fuhe = {r for r in self.fuhe_rows if self._is_full_row(r)}

        for r in range(N):
            for c in range(N):
                v = self.grid[r][c]
                if v != 0:
                    b = box_index(r, c)
                    # 行內重複 = 致命 (任何行)
                    if v in self.row_used[r]:
                        self.fatal_conflicts.append(
                            f"行{r + 1} 值{v} 行內重複"
                        )
                    # 列衝突: 涉及符闔行 = 警告, 其他 = 致命
                    if v in self.col_used[c]:
                        # 找出衝突的另一行
                        is_fuhe_conflict = r in fixed_fuhe
                        if not is_fuhe_conflict:
                            # 檢查是否有符闔行也在此列放了此值
                            for fr in fixed_fuhe:
                                if self.grid[fr][c] == v:
                                    is_fuhe_conflict = True
                                    break
                        if is_fuhe_conflict:
                            self.warnings.append(
                                f"列{c + 1} 值{v} 符闔行間列衝突 (行{r + 1})"
                            )
                        else:
                            self.fatal_conflicts.append(
                                f"列{c + 1} 值{v} 列衝突 (行{r + 1})"
                            )
                    # 宮衝突: 涉及符闔行 = 警告, 其他 = 致命
                    if v in self.box_used[b]:
                        is_fuhe_conflict = r in fixed_fuhe
                        if not is_fuhe_conflict:
                            # 檢查是否有符闔行在同一宮格(非僅同行組)放了此值
                            for fr in fixed_fuhe:
                                if box_index(fr, c) == b:
                                    for dc in range(BOX_SIZE):
                                        bc = (b % BOX_SIZE) * BOX_SIZE
                                        if self.grid[fr][bc + dc] == v:
                                            is_fuhe_conflict = True
                                            break
                                if is_fuhe_conflict:
                                    break
                        if is_fuhe_conflict:
                            self.warnings.append(
                                f"宮{b + 1} 值{v} 符闔行間宮衝突 (行{r + 1})"
                            )
                        else:
                            self.fatal_conflicts.append(
                                f"宮{b + 1} 值{v} 宮衝突 (行{r + 1})"
                            )
                    self.row_used[r].add(v)
                    self.col_used[c].add(v)
                    self.box_used[b].add(v)

    def has_initial_conflicts(self) -> bool:
        """檢查是否存在致命衝突 (符闔行間的宮衝突不算)"""
        return len(self.fatal_conflicts) > 0

    def get_conflicts(self) -> List[str]:
        """獲取所有衝突 (致命 + 警告)"""
        return list(self.fatal_conflicts) + list(self.warnings)

    def get_fatal_conflicts(self) -> List[str]:
        """獲取致命衝突"""
        return list(self.fatal_conflicts)

    def get_warnings(self) -> List[str]:
        """獲取警告 (符闔行間的預期衝突)"""
        return list(self.warnings)

    def filter_all(self) -> Tuple[Optional[List[List[List[int]]]], List[str]]:
        """
        對全部 16 行執行排列過濾。

        回傳:
            (filtered_perms, errors)
            filtered_perms: 過濾後的排列集合 (若失敗為 None)
            errors: 錯誤訊息列表
        """
        if self.has_initial_conflicts():
            return None, self.fatal_conflicts

        filtered = []
        stats = []

        for r in range(N):
            if not self.permutation_sets[r]:
                # 無排列數據, 跳過
                filtered.append([])
                stats.append((0, 0))
                continue

            row_filtered = self._filter_row(r)
            filtered.append(row_filtered)
            stats.append((len(self.permutation_sets[r]), len(row_filtered)))

            if not row_filtered:
                return None, [
                    f"行{r + 1} 過濾後無有效排列 "
                    f"(原始 {len(self.permutation_sets[r])} 個)"
                ]

        return filtered, stats

    def _filter_row(self, r: int) -> List[List[int]]:
        """對單行執行三層過濾"""
        result = []
        for perm in self.permutation_sets[r]:
            if self._check_known_values(r, perm) and \
               self._check_column_constraints(r, perm) and \
               self._check_box_constraints(r, perm):
                result.append(perm)
        return result

    def _check_known_values(self, r: int, perm: List[int]) -> bool:
        """層1: 排列必須匹配所有已知錨點"""
        for c in range(N):
            if self.grid[r][c] != 0 and perm[c] != self.grid[r][c]:
                return False
        return True

    def _check_column_constraints(self, r: int, perm: List[int]) -> bool:
        """層2: 排列中的值不能與同列已知值衝突"""
        for c in range(N):
            if self.grid[r][c] == 0:  # 只在空格檢查
                if perm[c] in self.col_used[c]:
                    return False
        return True

    def _check_box_constraints(self, r: int, perm: List[int]) -> bool:
        """層3: 排列中的值不能與同宮已知值衝突"""
        for c in range(N):
            if self.grid[r][c] == 0:
                b = box_index(r, c)
                if perm[c] in self.box_used[b]:
                    return False
        return True


# ═══════════════════════════════════════════════════════════════
#  AC-3 約束傳播
# ═══════════════════════════════════════════════════════════════

class AC3Propagator:
    """
    AC-3 弧一致性約束傳播求解器。

    用於:
      - 不依賴符闔排列文件的獨立求解
      - 作為 CP-SAT 的前置剪枝步驟
      - 作為回溯搜索的約束傳播子程序
    """

    def __init__(self, grid: List[List[int]]):
        self.N = N
        self.domains: Dict[Tuple[int, int], Set[int]] = {}
        self._init_domains(grid)
        self._init_arcs()

    def _init_domains(self, grid: List[List[int]]):
        """初始化每個單元格的候選域"""
        for r in range(N):
            for c in range(N):
                if grid[r][c] != 0:
                    self.domains[(r, c)] = {grid[r][c]}
                else:
                    self.domains[(r, c)] = set(VALUES)

        # 初步剪枝: 移除同行/列/宮的已知值
        for r in range(N):
            for c in range(N):
                if grid[r][c] != 0:
                    v = grid[r][c]
                    # 行剪枝
                    for cc in range(N):
                        if cc != c:
                            self.domains[(r, cc)].discard(v)
                    # 列剪枝
                    for rr in range(N):
                        if rr != r:
                            self.domains[(rr, c)].discard(v)
                    # 宮剪枝
                    b_r = (r // BOX_SIZE) * BOX_SIZE
                    b_c = (c // BOX_SIZE) * BOX_SIZE
                    for dr in range(BOX_SIZE):
                        for dc in range(BOX_SIZE):
                            rr, cc = b_r + dr, b_c + dc
                            if (rr, cc) != (r, c):
                                self.domains[(rr, cc)].discard(v)

    def _init_arcs(self):
        """預計算所有約束弧 (pairs of constrained cells)"""
        self.arcs: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
        self.neighbors: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}

        for r in range(N):
            for c in range(N):
                self.neighbors[(r, c)] = []

        # 行約束弧
        for r in range(N):
            for c1 in range(N):
                for c2 in range(c1 + 1, N):
                    self.arcs.append(((r, c1), (r, c2)))
                    self.arcs.append(((r, c2), (r, c1)))
                    self.neighbors[(r, c1)].append((r, c2))
                    self.neighbors[(r, c2)].append((r, c1))

        # 列約束弧
        for c in range(N):
            for r1 in range(N):
                for r2 in range(r1 + 1, N):
                    self.arcs.append(((r1, c), (r2, c)))
                    self.arcs.append(((r2, c), (r1, c)))
                    self.neighbors[(r1, c)].append((r2, c))
                    self.neighbors[(r2, c)].append((r1, c))

        # 宮約束弧
        for b in range(N):
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE
            cells = [
                (br + dr, bc + dc)
                for dr in range(BOX_SIZE)
                for dc in range(BOX_SIZE)
            ]
            for i in range(len(cells)):
                for j in range(i + 1, len(cells)):
                    self.arcs.append((cells[i], cells[j]))
                    self.arcs.append((cells[j], cells[i]))
                    self.neighbors[cells[i]].append(cells[j])
                    self.neighbors[cells[j]].append(cells[i])

    def run(self, max_iterations: int = 50000) -> Tuple[bool, int]:
        """
        執行 AC-3 約束傳播。

        回傳:
            (success, iterations)
            success: True = 一致性達成, False = 域為空 (無解)
            iterations: 迭代次數
        """
        queue = deque(self.arcs)
        iterations = 0

        while queue and iterations < max_iterations:
            xi, xj = queue.popleft()
            iterations += 1

            if self._revise(xi, xj):
                if not self.domains[xi]:
                    return False, iterations  # 域為空, 無解

                # 將所有受影響的弧重新加入佇列
                for xk in self.neighbors[xi]:
                    if xk != xj:
                        queue.append((xk, xi))

        return True, iterations

    def _revise(self, xi: Tuple[int, int],
                xj: Tuple[int, int]) -> bool:
        """
        修正 xi 的域: 移除沒有 xj 支撐的值。
        AllDifferent 約束: 若 xj 的域只有1個值, 則從 xi 移除該值。
        """
        revised = False
        if len(self.domains[xj]) == 1:
            xj_val = next(iter(self.domains[xj]))
            if xj_val in self.domains[xi]:
                self.domains[xi].discard(xj_val)
                revised = True
        return revised

    def get_grid(self) -> List[List[int]]:
        """從域中提取網格 (已確定的值) 和候選集"""
        grid = [[0] * N for _ in range(N)]
        for r in range(N):
            for c in range(N):
                if len(self.domains[(r, c)]) == 1:
                    grid[r][c] = next(iter(self.domains[(r, c)]))
        return grid

    def get_candidates(self) -> Dict[Tuple[int, int], Set[int]]:
        """獲取所有單元格的候選域"""
        return {k: set(v) for k, v in self.domains.items()}

    def is_solved(self) -> bool:
        """檢查是否所有域都只剩1個值"""
        return all(len(d) == 1 for d in self.domains.values())

    def total_candidates(self) -> int:
        """計算剩餘候選總數"""
        return sum(len(d) for d in self.domains.values())
