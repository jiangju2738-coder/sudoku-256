#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解驗證器 - 全面檢查五項約束

驗證項目:
  1. 行約束: 每行必須是 1-16 的全排列
  2. 列約束: 每列必須是 1-16 的全排列
  3. 宮約束: 每個 4x4 宮格必須是 1-16 的全排列
  4. 錨點約束: 所有錨點位置的值必須與初始數據一致
  5. 符闔約束: 每行必須存在於對應的符闔排列集合中 (可選)
"""

from typing import Dict, List, Optional, Set, Tuple

from .constants import N, BOX_SIZE, VALUES, ROW_LABELS, box_index


class SolutionVerifier:
    """16x16 數獨解驗證器"""

    def __init__(self, solution: List[List[int]]):
        self.solution = solution
        self.errors: List[str] = []

    def verify_all(self,
                   anchors: Dict[Tuple[int, int], int] = None,
                   permutation_sets: List[List[List[int]]] = None) -> dict:
        """
        執行全部驗證。

        參數:
            anchors: 錨點字典 {(row, col): value}
            permutation_sets: 符闔排列集合 (可選)

        回傳:
            {
                "row_ok": bool,
                "col_ok": bool,
                "box_ok": bool,
                "box_strict_ok": bool,
                "box_relaxed_ok": bool,
                "anchor_ok": bool,
                "fummel_ok": bool | None,
                "errors": List[str],
                "error_count": int,
            }
        """
        self.errors = []

        fuhe_rows = {2, 3, 8}  # C, D, I

        row_ok = self.verify_rows()
        col_ok = self.verify_columns_fuhe(fuhe_rows)

        # 宮約束: 分為嚴格宮和放鬆宮
        relaxed_boxes = self._find_relaxed_boxes(fuhe_rows)
        box_strict_ok = self.verify_boxes_strict(relaxed_boxes)
        box_relaxed_ok = self.verify_boxes_relaxed(relaxed_boxes, fuhe_rows)
        box_ok = box_strict_ok and box_relaxed_ok

        anchor_ok = True
        if anchors is not None:
            anchor_ok = self.verify_anchors(anchors)

        fummel_ok = None
        if permutation_sets is not None:
            fummel_ok = self.verify_fummel(permutation_sets)

        result = {
            "row_ok": row_ok,
            "col_ok": col_ok,
            "box_ok": box_ok,
            "box_strict_ok": box_strict_ok,
            "box_relaxed_ok": box_relaxed_ok,
            "relaxed_boxes": sorted(relaxed_boxes),
            "anchor_ok": anchor_ok,
            "fummel_ok": fummel_ok,
            "errors": list(self.errors),
            "error_count": len(self.errors),
        }
        return result

    def _find_relaxed_boxes(self, fuhe_rows: Set[int]) -> Set[int]:
        """找出含有多個完全固定符闔行且有值衝突的宮格"""
        fixed_fuhe = {
            r for r in fuhe_rows
            if all(self.solution[r][c] != 0 for c in range(N))
        }
        relaxed = set()
        for b in range(N):
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE
            box_fixed_fuhe = [r for r in range(br, br + BOX_SIZE) if r in fixed_fuhe]
            if len(box_fixed_fuhe) >= 2:
                vals = []
                for r in box_fixed_fuhe:
                    for dc in range(BOX_SIZE):
                        vals.append(self.solution[r][bc + dc])
                if len(vals) != len(set(vals)):
                    relaxed.add(b)
        return relaxed

    def verify_rows(self) -> bool:
        """驗證行約束: 每行是 1-16 全排列"""
        ok = True
        expected = set(VALUES)
        for r in range(N):
            row_vals = set(self.solution[r])
            if row_vals != expected:
                ok = False
                missing = expected - row_vals
                extra = row_vals - expected
                msg = f"行{r + 1} ({ROW_LABELS[r]}): "
                if missing:
                    msg += f"缺少 {sorted(missing)}"
                if extra:
                    msg += f" 多餘 {sorted(extra)}"
                self.errors.append(msg)
        return ok

    def verify_columns(self) -> bool:
        """驗證列約束: 每列是 1-16 全排列 (嚴格模式)"""
        ok = True
        expected = set(VALUES)
        for c in range(N):
            col_vals = set(self.solution[r][c] for r in range(N))
            if col_vals != expected:
                ok = False
                missing = expected - col_vals
                extra = col_vals - expected
                msg = f"列{c + 1}: "
                if missing:
                    msg += f"缺少 {sorted(missing)}"
                if extra:
                    msg += f" 多餘 {sorted(extra)}"
                self.errors.append(msg)
        return ok

    def verify_columns_fuhe(self, fuhe_rows: Set[int] = None) -> bool:
        """
        驗證列約束 (符闔放鬆模式):
        - 嚴格列: 全部16行 AllDifferent
        - 放鬆列: 非符闔行彼此不同 + 不等於符闔行值
        """
        if fuhe_rows is None:
            return self.verify_columns()

        ok = True
        expected = set(VALUES)
        fixed_fuhe = {
            r for r in fuhe_rows
            if all(self.solution[r][c] != 0 for c in range(N))
        }

        for c in range(N):
            # 檢查此列是否有符闔行間衝突
            fuhe_vals = [self.solution[r][c] for r in fixed_fuhe]
            has_fuhe_conflict = len(fuhe_vals) != len(set(fuhe_vals))

            if not has_fuhe_conflict:
                # 嚴格檢查: 全部16行
                col_vals = set(self.solution[r][c] for r in range(N))
                if col_vals != expected:
                    ok = False
                    self.errors.append(f"列{c + 1}: 嚴格列驗證失敗")
            else:
                # 放鬆列: 只檢查非符闔行
                non_fuhe_vals = [
                    self.solution[r][c]
                    for r in range(N) if r not in fixed_fuhe
                ]
                # 非符闔行彼此不同
                if len(non_fuhe_vals) != len(set(non_fuhe_vals)):
                    ok = False
                    self.errors.append(
                        f"列{c + 1}: 非符闔行間有重複值"
                    )
                # 非符闔行不等於任何符闔行值
                fuhe_val_set = set(fuhe_vals)
                for v in non_fuhe_vals:
                    if v in fuhe_val_set:
                        ok = False
                        self.errors.append(
                            f"列{c + 1}: 值{v} 與符闔行衝突"
                        )
                        break
        return ok

    def verify_boxes(self) -> bool:
        """驗證宮約束: 每個 4x4 宮格是 1-16 全排列 (嚴格模式)"""
        ok = True
        expected = set(VALUES)
        for b in range(N):
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE
            box_vals = set()
            for dr in range(BOX_SIZE):
                for dc in range(BOX_SIZE):
                    box_vals.add(self.solution[br + dr][bc + dc])
            if box_vals != expected:
                ok = False
                missing = expected - box_vals
                extra = box_vals - expected
                msg = f"宮{b + 1} (行{ROW_LABELS[br]}-{ROW_LABELS[br + 3]}, " \
                      f"列{bc + 1}-{bc + 4}): "
                if missing:
                    msg += f"缺少 {sorted(missing)}"
                if extra:
                    msg += f" 多餘 {sorted(extra)}"
                self.errors.append(msg)
        return ok

    def verify_boxes_strict(self, relaxed_boxes: Set[int] = None) -> bool:
        """驗證非放鬆宮格的嚴格 AllDifferent 約束"""
        if relaxed_boxes is None:
            relaxed_boxes = set()
        ok = True
        expected = set(VALUES)
        for b in range(N):
            if b in relaxed_boxes:
                continue
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE
            box_vals = set()
            for dr in range(BOX_SIZE):
                for dc in range(BOX_SIZE):
                    box_vals.add(self.solution[br + dr][bc + dc])
            if box_vals != expected:
                ok = False
                self.errors.append(f"宮{b + 1}: 嚴格宮格驗證失敗")
        return ok

    def verify_boxes_relaxed(self, relaxed_boxes: Set[int],
                             fuhe_rows: Set[int]) -> bool:
        """
        驗證放鬆宮格: 非符闔行的值不與符闔行衝突,
        且非符闔行之間彼此不同。
        """
        if not relaxed_boxes:
            return True
        ok = True
        for b in relaxed_boxes:
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE

            # 收集符闔行值和非符闔行值
            fuhe_vals = set()
            non_fuhe_vals = []
            for dr in range(BOX_SIZE):
                r = br + dr
                for dc in range(BOX_SIZE):
                    v = self.solution[r][bc + dc]
                    if r in fuhe_rows:
                        fuhe_vals.add(v)
                    else:
                        non_fuhe_vals.append(v)

            # 非符闔行不能與符闔行值衝突
            for v in non_fuhe_vals:
                if v in fuhe_vals:
                    ok = False
                    self.errors.append(
                        f"宮{b + 1} (放鬆): 值{v} 與符闔行衝突"
                    )

            # 非符闔行值彼此不同
            if len(non_fuhe_vals) != len(set(non_fuhe_vals)):
                ok = False
                self.errors.append(
                    f"宮{b + 1} (放鬆): 非符闔行間有重複值"
                )
        return ok

    def verify_anchors(self, anchors: Dict[Tuple[int, int], int]) -> bool:
        """驗證錨點約束: 所有錨點的值與初始數據一致"""
        ok = True
        for (r, c), expected_val in anchors.items():
            actual_val = self.solution[r][c]
            if actual_val != expected_val:
                ok = False
                self.errors.append(
                    f"錨點 ({ROW_LABELS[r]}{c + 1}): "
                    f"期望 {expected_val}, 實際 {actual_val}"
                )
        return ok

    def verify_fummel(self,
                      permutation_sets: List[List[List[int]]]) -> bool:
        """驗證符闔約束: 每行必須是有效的符闔排列"""
        ok = True
        pass_count = 0
        for r in range(N):
            row = list(self.solution[r])
            perm_list = [list(p) for p in permutation_sets[r]]
            if row in perm_list:
                pass_count += 1
            else:
                ok = False
                self.errors.append(
                    f"行{r + 1} ({ROW_LABELS[r]}): "
                    f"不在符闔排列集合中 "
                    f"(集合大小: {len(permutation_sets[r])})"
                )
        return ok

    def is_valid(self, anchors: Dict[Tuple[int, int], int] = None) -> bool:
        """快速驗證 (不含符闔), 回傳 True/False"""
        result = self.verify_all(anchors=anchors)
        return result["error_count"] == 0

    # ─────────────────────────────────────────────
    #  靜態工具方法
    # ─────────────────────────────────────────────

    @staticmethod
    def quick_check(grid: List[List[int]]) -> dict:
        """
        快速網格檢查 (不依賴 SolutionVerifier 實例)。
        回傳 {row_ok, col_ok, box_ok, all_ok, issues}
        """
        issues = []

        # 行
        row_ok = True
        for r in range(N):
            if sorted(grid[r]) != VALUES:
                row_ok = False
                issues.append(f"行{r + 1}")

        # 列
        col_ok = True
        for c in range(N):
            col = [grid[r][c] for r in range(N)]
            if sorted(col) != VALUES:
                col_ok = False
                issues.append(f"列{c + 1}")

        # 宮
        box_ok = True
        for b in range(N):
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE
            box = [
                grid[br + dr][bc + dc]
                for dr in range(BOX_SIZE)
                for dc in range(BOX_SIZE)
            ]
            if sorted(box) != VALUES:
                box_ok = False
                issues.append(f"宮{b + 1}")

        return {
            "row_ok": row_ok,
            "col_ok": col_ok,
            "box_ok": box_ok,
            "all_ok": row_ok and col_ok and box_ok,
            "issues": issues,
        }
