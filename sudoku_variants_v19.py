#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 符闔博弈優選策略 V19.0 - 數獨變體擴展系統
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

100D 基因指紋應用於多變體數獨：
  [X Sudoku]    - 對角線 AllDifferent 約束
  [Killer Sudoku] - Cage 求和約束 + Cage 內不重複

變體架構設計：
  1. SudokuVariant 基類（抽象變體接口）
  2. XSudokuVariant - X Sudoku 實現
  3. KillerSudokuVariant - Killer Sudoku 實現
  4. 100D 基因指紋變體適配器
  5. 通用遺傳優化器（支援多變體）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import time
import random
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


# ═══════════════════════════════════════════════════════════
# 變體類型定義
# ═══════════════════════════════════════════════════════════

class SudokuVariantType(Enum):
    """數獨變體類型"""
    STANDARD = "standard"           # 標準數獨
    X_SUDOKU = "x_sudoku"          # X Sudoku（對角線約束）
    KILLER_SUDOKU = "killer_sudoku"  # Killer Sudoku（Cage 約束）
    FUMMEL = "fummeL"              # 符闔變體
    HYBRID = "hybrid"              # 混合變體


# ═══════════════════════════════════════════════════════════
# 基類：數獨變體抽象
# ═══════════════════════════════════════════════════════════

@dataclass
class ConstraintViolation:
    """約束違反記錄"""
    constraint_type: str    # 約束類型
    location: Tuple[int, int]  # 位置
    expected: any          # 期望值
    actual: any            # 實際值
    severity: float = 1.0  # 嚴重程度 (0-1)


class SudokuVariant(ABC):
    """
    數獨變體抽象基類
    
    所有變體必須實現：
    - validate_solution: 驗證解的有效性
    - compute_constraint_fitness: 計算約束適應度
    - get_additional_constraints: 獲取額外的變體約束
    """
    
    def __init__(self, grid_size: int = 16, box_size: int = 4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.value_range = range(1, grid_size + 1)
        self.violations: List[ConstraintViolation] = []
    
    @abstractmethod
    def validate_solution(self, grid: List[List[int]], 
                          known_positions: Dict[Tuple[int, int], int]) -> Dict:
        """驗證解是否滿足所有變體約束"""
        pass
    
    @abstractmethod
    def compute_constraint_fitness(self, grid: List[List[int]],
                                    known_positions: Dict) -> float:
        """計算變體約束的適應度"""
        pass
    
    @abstractmethod
    def get_additional_constraints(self) -> Dict:
        """獲取變體特有的約束定義"""
        pass
    
    def validate_standard_constraints(self, grid: List[List[int]]) -> Dict:
        """驗證標準數獨約束（行、列、宮）"""
        errors = []
        conflicts = {'row': 0, 'col': 0, 'box': 0}
        
        # 行約束
        for r in range(self.grid_size):
            vals = grid[r]
            if 0 in vals:
                errors.append(f"行{r+1}存在空值")
            elif len(set(vals)) != self.grid_size:
                errors.append(f"行{r+1}存在重複值")
                conflicts['row'] += 1
        
        # 列約束
        for c in range(self.grid_size):
            vals = [grid[r][c] for r in range(self.grid_size)]
            if len(set(vals)) != self.grid_size:
                errors.append(f"列{c+1}存在重複值")
                conflicts['col'] += 1
        
        # 宮約束
        for box_idx in range(self.grid_size):
            box_vals = []
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if (r // self.box_size) * self.box_size + (c // self.box_size) == box_idx:
                        box_vals.append(grid[r][c])
            if len(set(box_vals)) != self.grid_size:
                errors.append(f"宮{box_idx+1}存在重複值")
                conflicts['box'] += 1
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'conflicts': conflicts,
            'error_count': len(errors)
        }


# ═══════════════════════════════════════════════════════════
# X Sudoku 變體
# ═══════════════════════════════════════════════════════════

@dataclass
class DiagonalConstraint:
    """對角線約束定義"""
    name: str           # 約束名稱
    cells: List[Tuple[int, int]]  # 對角線上的所有位置
    must_be_alldiff: bool = True  # 必須 AllDifferent


class XsudokuVariant(SudokuVariant):
    """
    X Sudoku 變體
    
    在標準數獨基礎上增加：
    - 主對角線 (0,0) → (15,15) 必須 AllDifferent
    - 副對角線 (0,15) → (15,0) 必須 AllDifferent
    
    100D 基因指紋擴展：
    - 新增 diagonal_dimensions (16D) 用於量化對角線滿足程度
    """
    
    def __init__(self, grid_size: int = 16, box_size: int = 4):
        super().__init__(grid_size, box_size)
        self.diagonals = self._build_diagonals()
    
    def _build_diagonals(self) -> Dict[str, DiagonalConstraint]:
        """構建兩條對角線"""
        diagonals = {}
        
        # 主對角線
        main_diag_cells = [(i, i) for i in range(self.grid_size)]
        diagonals['main'] = DiagonalConstraint(
            name='主對角線',
            cells=main_diag_cells,
            must_be_alldiff=True
        )
        
        # 副對角線
        anti_diag_cells = [(i, self.grid_size - 1 - i) for i in range(self.grid_size)]
        diagonals['anti'] = DiagonalConstraint(
            name='副對角線',
            cells=anti_diag_cells,
            must_be_alldiff=True
        )
        
        return diagonals
    
    def validate_solution(self, grid: List[List[int]], 
                          known_positions: Dict[Tuple[int, int], int]) -> Dict:
        """驗證 X Sudoku 解（標準約束 + 對角線約束）"""
        # 先驗證標準約束
        standard_result = self.validate_standard_constraints(grid)
        
        if not standard_result['valid']:
            return standard_result
        
        # 驗證對角線約束
        diagonal_errors = []
        diagonal_conflicts = 0
        
        for diag_name, diag in self.diagonals.items():
            diag_vals = [grid[r][c] for r, c in diag.cells]
            if 0 in diag_vals:
                diagonal_errors.append(f"{diag_name}存在空值")
            elif len(set(diag_vals)) != self.grid_size:
                diagonal_errors.append(f"{diag_name}存在重複值")
                diagonal_conflicts += 1
        
        all_errors = standard_result['errors'] + diagonal_errors
        all_conflicts = standard_result['conflicts'].copy()
        all_conflicts['diagonal'] = diagonal_conflicts
        
        return {
            'valid': len(all_errors) == 0,
            'errors': all_errors,
            'conflicts': all_conflicts,
            'error_count': len(all_errors),
            'diagonal_valid': diagonal_conflicts == 0
        }
    
    def compute_constraint_fitness(self, grid: List[List[int]],
                                    known_positions: Dict) -> float:
        """計算 X Sudoku 適應度"""
        # 標準約束適應度
        standard_fitness = self._compute_standard_fitness(grid)
        
        # 對角線約束適應度
        diagonal_fitness = 0.0
        for diag_name, diag in self.diagonals.items():
            diag_vals = [grid[r][c] for r, c in diag.cells]
            if 0 in diag_vals:
                diag_fit = 0.0
            else:
                unique_ratio = len(set(diag_vals)) / self.grid_size
                diag_fit = unique_ratio
            diagonal_fitness += diag_fit
        
        diagonal_fitness /= len(self.diagonals)
        
        # 加權組合：標準 0.8 + 對角線 0.2
        return 0.8 * standard_fitness + 0.2 * diagonal_fitness
    
    def _compute_standard_fitness(self, grid: List[List[int]]) -> float:
        """計算標準約束適應度"""
        # 行
        row_fit = 0.0
        for r in range(self.grid_size):
            vals = grid[r]
            if 0 not in vals and len(set(vals)) == self.grid_size:
                row_fit += 1.0
        row_fit /= self.grid_size
        
        # 列
        col_fit = 0.0
        for c in range(self.grid_size):
            vals = [grid[r][c] for r in range(self.grid_size)]
            if len(set(vals)) == self.grid_size:
                col_fit += 1.0
        col_fit /= self.grid_size
        
        # 宮
        box_fit = 0.0
        for box_idx in range(self.grid_size):
            box_vals = []
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if (r // self.box_size) * self.box_size + (c // self.box_size) == box_idx:
                        box_vals.append(grid[r][c])
            if 0 not in box_vals and len(set(box_vals)) == self.grid_size:
                box_fit += 1.0
        box_fit /= self.grid_size
        
        return 0.3 * row_fit + 0.35 * col_fit + 0.35 * box_fit
    
    def get_additional_constraints(self) -> Dict:
        """獲取 X Sudoku 特有約束"""
        return {
            'variant_type': SudokuVariantType.X_SUDOKU.value,
            'diagonals': {
                name: {
                    'cells': diag.cells,
                    'must_be_alldiff': diag.must_be_alldiff
                }
                for name, diag in self.diagonals.items()
            },
            'description': 'X Sudoku: 主副對角線必須包含 1-16 所有數字且不重複'
        }
    
    def extract_diagonal_gene_fingerprint(self, grid: List[List[int]]) -> List[float]:
        """提取對角線基因指紋特徵（16D）"""
        fingerprint = []
        
        for diag_name, diag in self.diagonals.items():
            diag_vals = [grid[r][c] for r, c in diag.cells]
            # 計算每個位置的局部特徵
            for i, (r, c) in enumerate(diag.cells):
                # 局部滿足度
                if diag_vals[i] != 0:
                    unique_in_diag = len(set(diag_vals))
                    fingerprint.append(unique_in_diag / self.grid_size)
                else:
                    fingerprint.append(0.0)
        
        return fingerprint[:16]  # 返回 16D 特徵


# ═══════════════════════════════════════════════════════════
# Killer Sudoku 變體
# ═══════════════════════════════════════════════════════════

@dataclass
class Cage:
    """Killer Sudoku 的 Cage（區域）"""
    cage_id: str                    # Cage 編號
    cells: List[Tuple[int, int]]    # Cage 包含的所有位置
    target_sum: int                 # 目標和
    must_be_unique: bool = True     # Cage 內數字必須不重複


class KillersudokuVariant(SudokuVariant):
    """
    Killer Sudoku 變體
    
    在標準數獨基礎上增加：
    - Cage 約束：每個 Cage 內的數字之和必須等於 target_sum
    - Cage 內不重複：每個 Cage 內的數字不能重複
    
    100D 基因指紋擴展：
    - 新增 cage_sum_dimensions (20D) 量化 Cage 和滿足程度
    - 新增 cage_uniq_dimensions (16D) 量化 Cage 內唯一性
    """
    
    def __init__(self, grid_size: int = 16, box_size: int = 4, 
                 cages: Optional[List[Dict]] = None):
        super().__init__(grid_size, box_size)
        self.cages = self._build_cages(cages) if cages else []
    
    def _build_cages(self, cage_defs: List[Dict]) -> List[Cage]:
        """構建 Cage 列表"""
        cages = []
        for i, cage_def in enumerate(cage_defs):
            cage = Cage(
                cage_id=f"CAGE_{i+1:02d}",
                cells=[tuple(cell) for cell in cage_def.get('cells', [])],
                target_sum=cage_def.get('target_sum', 0),
                must_be_unique=cage_def.get('must_be_unique', True)
            )
            cages.append(cage)
        return cages
    
    def load_cages_from_json(self, filepath: str) -> None:
        """從 JSON 文件載入 Cage 定義"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cages_def = data.get('cages', [])
        self.cages = self._build_cages(cages_def)
        print(f"  載入 Cage 數量: {len(self.cages)}")
    
    def validate_solution(self, grid: List[List[int]], 
                          known_positions: Dict[Tuple[int, int], int]) -> Dict:
        """驗證 Killer Sudoku 解（標準約束 + Cage 約束）"""
        # 先驗證標準約束
        standard_result = self.validate_standard_constraints(grid)
        
        if not standard_result['valid']:
            return standard_result
        
        # 驗證 Cage 約束
        cage_errors = []
        cage_sum_errors = 0
        cage_unique_errors = 0
        
        for cage in self.cages:
            cage_vals = [grid[r][c] for r, c in cage.cells if grid[r][c] != 0]
            
            # 檢查求和
            actual_sum = sum(cage_vals)
            if actual_sum != cage.target_sum:
                cage_errors.append(f"{cage.cage_id}求和錯誤: 期望{cage.target_sum}, 實際{actual_sum}")
                cage_sum_errors += 1
            
            # 檢查唯一性
            if cage.must_be_unique and len(set(cage_vals)) != len(cage_vals):
                cage_errors.append(f"{cage.cage_id}存在重複值")
                cage_unique_errors += 1
        
        all_errors = standard_result['errors'] + cage_errors
        all_conflicts = standard_result['conflicts'].copy()
        all_conflicts['cage_sum'] = cage_sum_errors
        all_conflicts['cage_unique'] = cage_unique_errors
        
        return {
            'valid': len(all_errors) == 0,
            'errors': all_errors,
            'conflicts': all_conflicts,
            'error_count': len(all_errors),
            'cage_sum_valid': cage_sum_errors == 0,
            'cage_unique_valid': cage_unique_errors == 0
        }
    
    def compute_constraint_fitness(self, grid: List[List[int]],
                                    known_positions: Dict) -> float:
        """計算 Killer Sudoku 適應度"""
        # 標準約束適應度
        standard_fitness = self._compute_standard_fitness(grid)
        
        # Cage 約束適應度
        cage_fitness = 0.0
        for cage in self.cages:
            cage_vals = [grid[r][c] for r, c in cage.cells if grid[r][c] != 0]
            actual_sum = sum(cage_vals)
            
            # 求和適應度
            if actual_sum == cage.target_sum:
                sum_fit = 1.0
            elif len(cage_vals) > 0:
                # 根據偏差計算適應度
                deviation = abs(actual_sum - cage.target_sum)
                max_possible_sum = sum(range(1, self.grid_size + 1))
                sum_fit = max(0.0, 1.0 - deviation / max_possible_sum)
            else:
                sum_fit = 0.0
            
            # 唯一性適應度
            if cage.must_be_unique:
                unique_fit = 1.0 if len(set(cage_vals)) == len(cage_vals) else 0.0
            else:
                unique_fit = 1.0
            
            cage_fit = 0.6 * sum_fit + 0.4 * unique_fit
            cage_fitness += cage_fit
        
        if self.cages:
            cage_fitness /= len(self.cages)
        
        # 加權組合：標準 0.6 + Cage 0.4
        return 0.6 * standard_fitness + 0.4 * cage_fitness
    
    def _compute_standard_fitness(self, grid: List[List[int]]) -> float:
        """計算標準約束適應度"""
        # 行
        row_fit = 0.0
        for r in range(self.grid_size):
            vals = grid[r]
            if 0 not in vals and len(set(vals)) == self.grid_size:
                row_fit += 1.0
        row_fit /= self.grid_size
        
        # 列
        col_fit = 0.0
        for c in range(self.grid_size):
            vals = [grid[r][c] for r in range(self.grid_size)]
            if len(set(vals)) == self.grid_size:
                col_fit += 1.0
        col_fit /= self.grid_size
        
        # 宮
        box_fit = 0.0
        for box_idx in range(self.grid_size):
            box_vals = []
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if (r // self.box_size) * self.box_size + (c // self.box_size) == box_idx:
                        box_vals.append(grid[r][c])
            if 0 not in box_vals and len(set(box_vals)) == self.grid_size:
                box_fit += 1.0
        box_fit /= self.grid_size
        
        return 0.3 * row_fit + 0.35 * col_fit + 0.35 * box_fit
    
    def get_additional_constraints(self) -> Dict:
        """獲取 Killer Sudoku 特有約束"""
        return {
            'variant_type': SudokuVariantType.KILLER_SUDOKU.value,
            'cages': [
                {
                    'cage_id': cage.cage_id,
                    'cells': cage.cells,
                    'target_sum': cage.target_sum,
                    'must_be_unique': cage.must_be_unique,
                    'cell_count': len(cage.cells)
                }
                for cage in self.cages
            ],
            'cage_count': len(self.cages),
            'description': 'Killer Sudoku: Cage 內數字求和等於目標值且 Cage 內不重複'
        }
    
    def extract_cage_gene_fingerprint(self, grid: List[List[int]]) -> Dict[str, List[float]]:
        """提取 Cage 基因指紋特徵"""
        fingerprint = {
            'cage_sum_fitness': [],
            'cage_unique_fitness': [],
            'cage_coverage': []
        }
        
        for cage in self.cages:
            cage_vals = [grid[r][c] for r, c in cage.cells if grid[r][c] != 0]
            actual_sum = sum(cage_vals)
            
            # 求和適應度
            if actual_sum == cage.target_sum:
                sum_fit = 1.0
            elif len(cage_vals) > 0:
                deviation = abs(actual_sum - cage.target_sum)
                max_possible_sum = sum(range(1, self.grid_size + 1))
                sum_fit = max(0.0, 1.0 - deviation / max_possible_sum)
            else:
                sum_fit = 0.0
            fingerprint['cage_sum_fitness'].append(sum_fit)
            
            # 唯一性適應度
            unique_fit = 1.0 if len(set(cage_vals)) == len(cage_vals) else 0.0
            fingerprint['cage_unique_fitness'].append(unique_fit)
            
            # 覆蓋率
            coverage = len(cage_vals) / len(cage.cells) if cage.cells else 0
            fingerprint['cage_coverage'].append(coverage)
        
        return fingerprint


# ═══════════════════════════════════════════════════════════
# 100D 基因指紋變體適配器
# ═══════════════════════════════════════════════════════════

@dataclass
class GeneFingerprint100DAdapter:
    """
    100D 基因指紋變體適配器
    
    為不同變體提供 100D 基因指紋的適配計算：
    - 標準維度：行(16D) + 列(16D) + 宮(16D)
    - X Sudoku 擴展：對角線(16D)
    - Killer Sudoku 擴展：Cage 求和(20D) + Cage 唯一性(16D)
    - 全局維度：全局 AllDifferent(20D) + 溢出修正(20D)
    """
    
    grid_size: int = 16
    variant_type: SudokuVariantType = SudokuVariantType.STANDARD
    
    def compute_fingerprint(self, grid: List[List[int]], 
                            known_positions: Dict,
                            variant: Optional[SudokuVariant] = None) -> Dict:
        """計算完整的 100D 基因指紋"""
        fingerprint = {
            'variant_type': self.variant_type.value,
            'grid_size': self.grid_size,
            'row_dimensions': self._compute_row_dimensions(grid),
            'col_dimensions': self._compute_col_dimensions(grid),
            'box_dimensions': self._compute_box_dimensions(grid),
            'diagonal_dimensions': self._compute_diagonal_dimensions(grid) if self.variant_type == SudokuVariantType.X_SUDOKU else [],
            'cage_sum_dimensions': self._compute_cage_sum_dimensions(grid, variant) if self.variant_type == SudokuVariantType.KILLER_SUDOKU else [],
            'cage_unique_dimensions': self._compute_cage_unique_dimensions(grid, variant) if self.variant_type == SudokuVariantType.KILLER_SUDOKU else [],
            'global_alldiff': self._compute_global_alldiff(grid),
            'overflow_correction': self._compute_overflow_correction(grid, known_positions),
            'total_fitness': 0.0
        }
        
        # 計算總體適應度
        fingerprint['total_fitness'] = self._compute_total_fitness(fingerprint, variant)
        
        return fingerprint
    
    def _compute_row_dimensions(self, grid: List[List[int]]) -> List[float]:
        """計算行約束維度（16D）"""
        dims = []
        for r in range(self.grid_size):
            vals = grid[r]
            if 0 in vals:
                fitness = 0.0
            elif len(set(vals)) == self.grid_size:
                fitness = 1.0
            else:
                duplicates = len(vals) - len(set(vals))
                fitness = (self.grid_size - duplicates) / self.grid_size
            dims.append(fitness)
        return dims
    
    def _compute_col_dimensions(self, grid: List[List[int]]) -> List[float]:
        """計算列約束維度（16D）"""
        dims = []
        for c in range(self.grid_size):
            vals = [grid[r][c] for r in range(self.grid_size)]
            if len(set(vals)) == self.grid_size:
                fitness = 1.0
            else:
                duplicates = len(vals) - len(set(vals))
                fitness = (self.grid_size - duplicates) / self.grid_size
            dims.append(fitness)
        return dims
    
    def _compute_box_dimensions(self, grid: List[List[int]]) -> List[float]:
        """計算宮約束維度（16D）"""
        box_size = int(np.sqrt(self.grid_size))
        dims = []
        for box_idx in range(self.grid_size):
            box_vals = []
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if (r // box_size) * box_size + (c // box_size) == box_idx:
                        box_vals.append(grid[r][c])
            if 0 in box_vals:
                fitness = 0.0
            elif len(set(box_vals)) == self.grid_size:
                fitness = 1.0
            else:
                duplicates = len(box_vals) - len(set(box_vals))
                fitness = (self.grid_size - duplicates) / self.grid_size
            dims.append(fitness)
        return dims
    
    def _compute_diagonal_dimensions(self, grid: List[List[int]]) -> List[float]:
        """計算對角線約束維度（16D）- X Sudoku"""
        dims = []
        
        # 主對角線
        main_diag = [grid[i][i] for i in range(self.grid_size)]
        if 0 in main_diag:
            main_fit = 0.0
        else:
            main_fit = len(set(main_diag)) / self.grid_size
        
        # 副對角線
        anti_diag = [grid[i][self.grid_size - 1 - i] for i in range(self.grid_size)]
        if 0 in anti_diag:
            anti_fit = 0.0
        else:
            anti_fit = len(set(anti_diag)) / self.grid_size
        
        # 對角線特徵擴展到 16D
        dims.append(main_fit)
        dims.append(anti_fit)
        # 補充其他對角線特徵
        for offset in range(1, 8):
            # 偏移對角線
            diag_vals = []
            for i in range(self.grid_size - offset):
                diag_vals.append(grid[i][i + offset])
            if diag_vals and 0 not in diag_vals:
                dims.append(len(set(diag_vals)) / len(diag_vals))
            else:
                dims.append(0.0)
        
        # 填滿到 16D
        while len(dims) < self.grid_size:
            dims.append(0.0)
        
        return dims[:self.grid_size]
    
    def _compute_cage_sum_dimensions(self, grid: List[List[int]], 
                                      variant: Optional[SudokuVariant]) -> List[float]:
        """計算 Cage 求和維度（20D）- Killer Sudoku"""
        dims = []
        
        if not variant or not hasattr(variant, 'cages'):
            return [0.0] * 20
        
        for cage in variant.cages[:20]:
            cage_vals = [grid[r][c] for r, c in cage.cells if grid[r][c] != 0]
            actual_sum = sum(cage_vals)
            
            if actual_sum == cage.target_sum:
                fit = 1.0
            elif len(cage_vals) > 0:
                deviation = abs(actual_sum - cage.target_sum)
                max_sum = sum(range(1, self.grid_size + 1))
                fit = max(0.0, 1.0 - deviation / max_sum)
            else:
                fit = 0.0
            
            dims.append(fit)
        
        # 填滿到 20D
        while len(dims) < 20:
            dims.append(0.0)
        
        return dims[:20]
    
    def _compute_cage_unique_dimensions(self, grid: List[List[int]], 
                                         variant: Optional[SudokuVariant]) -> List[float]:
        """計算 Cage 唯一性維度（16D）- Killer Sudoku"""
        dims = []
        
        if not variant or not hasattr(variant, 'cages'):
            return [0.0] * 16
        
        for cage in variant.cages[:16]:
            cage_vals = [grid[r][c] for r, c in cage.cells if grid[r][c] != 0]
            unique_fit = 1.0 if len(set(cage_vals)) == len(cage_vals) else 0.0
            dims.append(unique_fit)
        
        # 填滿到 16D
        while len(dims) < self.grid_size:
            dims.append(0.0)
        
        return dims[:self.grid_size]
    
    def _compute_global_alldiff(self, grid: List[List[int]]) -> List[float]:
        """計算全局 AllDifferent 維度（20D）"""
        all_vals = [grid[r][c] for r in range(self.grid_size) for c in range(self.grid_size)]
        unique_vals = set(all_vals)
        unique_ratio = len(unique_vals) / (self.grid_size * self.grid_size)
        
        dims = [unique_ratio * (1 + i * 0.02) for i in range(20)]
        return dims
    
    def _compute_overflow_correction(self, grid: List[List[int]], 
                                      known_positions: Dict) -> List[float]:
        """計算溢出修正維度（20D）"""
        # 每行的已知位置數量
        row_known_counts = Counter(r for r, c in known_positions.keys())
        
        dims = []
        for i in range(20):
            # 計算平均過度固定程度
            avg_known = sum(row_known_counts.values()) / self.grid_size if row_known_counts else 0
            overflow_factor = avg_known / self.grid_size
            dims.append(overflow_factor * (1 + i * 0.05))
        
        return dims
    
    def _compute_total_fitness(self, fingerprint: Dict, 
                                variant: Optional[SudokuVariant]) -> float:
        """計算總體適應度"""
        row_fit = sum(fingerprint['row_dimensions']) / self.grid_size
        col_fit = sum(fingerprint['col_dimensions']) / self.grid_size
        box_fit = sum(fingerprint['box_dimensions']) / self.grid_size
        
        # 基本適應度
        base_fitness = 0.1 * row_fit + 0.45 * col_fit + 0.45 * box_fit
        
        # 變體擴展適應度
        variant_fitness = 0.0
        if self.variant_type == SudokuVariantType.X_SUDOKU and fingerprint.get('diagonal_dimensions'):
            diag_fit = sum(fingerprint['diagonal_dimensions'][:2]) / 2  # 主副對角線
            variant_fitness += 0.1 * diag_fit
            base_fitness *= 0.9  # 調整基本權重
        
        if self.variant_type == SudokuVariantType.KILLER_SUDOKU:
            cage_sum_fit = sum(fingerprint.get('cage_sum_dimensions', [])) / max(1, len(fingerprint.get('cage_sum_dimensions', [])))
            cage_unique_fit = sum(fingerprint.get('cage_unique_dimensions', [])) / max(1, len(fingerprint.get('cage_unique_dimensions', [])))
            cage_fitness = 0.6 * cage_sum_fit + 0.4 * cage_unique_fit
            variant_fitness += 0.2 * cage_fitness
            base_fitness *= 0.8  # 調整基本權重
        
        return base_fitness + variant_fitness


# ═══════════════════════════════════════════════════════════
# 通用變體遺傳優化器
# ═══════════════════════════════════════════════════════════

class VariantGeneticOptimizer:
    """
    通用變體遺傳優化器
    
    支援任意數獨變體的遺傳優化：
    - 標準數獨
    - X Sudoku
    - Killer Sudoku
    - 自定義變體
    """
    
    def __init__(self, 
                 variant: SudokuVariant,
                 known_positions: Dict[Tuple[int, int], int],
                 population_size: int = 100,
                 max_generations: int = 500,
                 mutation_rate: float = 0.05,
                 crossover_rate: float = 0.8):
        
        self.variant = variant
        self.known_positions = known_positions
        self.pop_size = population_size
        self.max_gens = max_generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        self.population: List[Dict] = []
        self.gene_adapter = GeneFingerprint100DAdapter(
            grid_size=variant.grid_size,
            variant_type=self._get_variant_type(variant)
        )
    
    def _get_variant_type(self, variant: SudokuVariant) -> SudokuVariantType:
        """確定變體類型"""
        if isinstance(variant, XsudokuVariant):
            return SudokuVariantType.X_SUDOKU
        elif isinstance(variant, KillersudokuVariant):
            return SudokuVariantType.KILLER_SUDOKU
        else:
            return SudokuVariantType.STANDARD
    
    def _create_individual(self, grid: List[List[int]]) -> Dict:
        """創建個體"""
        fitness = self.variant.compute_constraint_fitness(grid, self.known_positions)
        
        return {
            'grid': grid,
            'fitness': fitness,
            'generation': 0
        }
    
    def _initialize_population(self) -> None:
        """初始化種群"""
        self.population = []
        
        # 初始化所有未知位置
        unknown_cells = []
        for r in range(self.variant.grid_size):
            for c in range(self.variant.grid_size):
                if (r, c) not in self.known_positions:
                    unknown_cells.append((r, c))
        
        for _ in range(self.pop_size):
            grid = [[0] * self.variant.grid_size for _ in range(self.variant.grid_size)]
            
            # 填入已知位置
            for (r, c), v in self.known_positions.items():
                grid[r][c] = v
            
            # 隨機填滿未知位置
            for r, c in unknown_cells:
                available = [v for v in range(1, self.variant.grid_size + 1)
                            if v not in [grid[r][cc] for cc in range(self.variant.grid_size) if grid[r][cc] != 0]
                            and v not in [grid[rr][c] for rr in range(self.variant.grid_size) if grid[rr][c] != 0]]
                if available:
                    grid[r][c] = random.choice(available)
                else:
                    grid[r][c] = random.randint(1, self.variant.grid_size)
            
            self.population.append(self._create_individual(grid))
        
        print(f"  初始化種群: {self.pop_size} 個個體")
        print(f"  未知位點: {len(unknown_cells)} 個")
    
    def optimize(self, verbose: bool = True) -> Dict:
        """執行遺傳優化"""
        print("\n" + "=" * 70)
        print(f"┌─ 遺傳優化器 - {self.variant.__class__.__name__} ─────────┐")
        print(f"│  變體類型: {self._get_variant_type(self.variant).value}                │")
        print("└───────────────────────────────────────────────────┘")
        print()
        
        # 初始化
        print("[初始化] 構建種群...")
        self._initialize_population()
        
        # 記錄最佳適應度
        best_history = []
        generation_start = time.time()
        
        for gen in range(1, self.max_gens + 1):
            # 評估所有個體
            for ind in self.population:
                ind['fitness'] = self.variant.compute_constraint_fitness(
                    ind['grid'], self.known_positions
                )
            
            # 找到最佳個體
            best = max(self.population, key=lambda x: x['fitness'])
            avg_fitness = sum(ind['fitness'] for ind in self.population) / self.pop_size
            
            best_history.append({
                'generation': gen,
                'best_fitness': best['fitness'],
                'avg_fitness': avg_fitness
            })
            
            # 輸出進度
            if gen % 50 == 0 or gen == 1:
                if verbose:
                    print(f"  代數 {gen:4d}: 最佳 {best['fitness']:.4f} | 平均 {avg_fitness:.4f}")
            
            # 終止條件
            if best['fitness'] >= 0.9999:
                print(f"\n  ✓ 達到終止條件: 適應度 {best['fitness']:.4f}")
                break
            
            # 選擇 + 交叉 + 突變
            sorted_pop = sorted(self.population, key=lambda x: x['fitness'], reverse=True)
            
            # 精英保留
            new_population = sorted_pop[:5]
            
            # 生成新個體
            while len(new_population) < self.pop_size:
                # 輪盤賭選擇
                parent1 = self._tournament_select()
                parent2 = self._tournament_select()
                
                # 交叉
                if random.random() < self.crossover_rate:
                    child = self._crossover(parent1, parent2)
                else:
                    child = parent1.copy()
                
                # 突變
                if random.random() < self.mutation_rate:
                    child = self._mutate(child)
                
                new_population.append(child)
            
            self.population = new_population[:self.pop_size]
        
        # 最終結果
        elapsed = time.time() - generation_start
        final_best = max(self.population, key=lambda x: x['fitness'])
        
        # 計算 100D 基因指紋
        fingerprint = self.gene_adapter.compute_fingerprint(
            final_best['grid'], 
            self.known_positions,
            self.variant
        )
        
        # 驗證解
        validation = self.variant.validate_solution(final_best['grid'], self.known_positions)
        
        if verbose:
            print("\n" + "=" * 70)
            print("┌─ 優化完成 ──────────────────────────────────────┐")
            print(f"│  最終適應度: {final_best['fitness']:.4f}                   │")
            print(f"│  遺傳代數: {len(best_history)}                       │")
            print(f"│  耗時: {elapsed:.2f}秒                     │")
            print(f"│  基因指紋適應度: {fingerprint['total_fitness']:.4f}              │")
            print(f"│  解有效: {'✅ 是' if validation['valid'] else '❌ 否':18s}          │")
            print("└───────────────────────────────────────────────┘")
        
        return {
            'best_individual': final_best,
            'best_fitness': final_best['fitness'],
            'generations': len(best_history),
            'elapsed_time': elapsed,
            'gene_fingerprint': fingerprint,
            'validation': validation,
            'variant_type': self._get_variant_type(self.variant).value,
            'history': best_history
        }
    
    def _tournament_select(self, tournament_size: int = 5) -> Dict:
        """輪盤賭選擇"""
        tournament = random.sample(self.population, min(tournament_size, len(self.population)))
        return max(tournament, key=lambda x: x['fitness'])
    
    def _crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """交叉操作"""
        child_grid = [row[:] for row in parent1['grid']]
        
        # 基於行的交換
        for r in range(self.variant.grid_size):
            if random.random() < 0.3 and (r, 0) not in self.known_positions:
                child_grid[r] = parent2['grid'][r][:]
        
        return {
            'grid': child_grid,
            'fitness': 0.0,
            'generation': parent1['generation'] + 1
        }
    
    def _mutate(self, individual: Dict) -> Dict:
        """突變操作"""
        mutated_grid = [row[:] for row in individual['grid']]
        
        # 隨機交換兩個未知位置
        unknown_cells = []
        for r in range(self.variant.grid_size):
            for c in range(self.variant.grid_size):
                if (r, c) not in self.known_positions:
                    unknown_cells.append((r, c))
        
        if len(unknown_cells) >= 2:
            (r1, c1), (r2, c2) = random.sample(unknown_cells, 2)
            mutated_grid[r1][c1], mutated_grid[r2][c2] = mutated_grid[r2][c2], mutated_grid[r1][c1]
        
        return {
            'grid': mutated_grid,
            'fitness': 0.0,
            'generation': individual['generation'] + 1
        }


# ═══════════════════════════════════════════════════════════
# 範例演示
# ═══════════════════════════════════════════════════════════

def demo_x_sudoku():
    """演示 X Sudoku"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║           演示：X Sudoku 變體                      ║")
    print("╚" + "═" * 68 + "╝")
    
    # 創建 X Sudoku 變體
    variant = XsudokuVariant(grid_size=16, box_size=4)
    
    # 創建示例網格
    grid = [[0] * 16 for _ in range(16)]
    
    # 填入一些已知位置
    known_positions = {
        (0, 0): 1, (1, 1): 2, (2, 2): 3, (3, 3): 4,
        (4, 4): 5, (5, 5): 6, (6, 6): 7, (7, 7): 8,
        (0, 15): 16, (1, 14): 15, (2, 13): 14, (3, 12): 13,
    }
    
    for (r, c), v in known_positions.items():
        grid[r][c] = v
    
    # 計算 100D 基因指紋
    adapter = GeneFingerprint100DAdapter(
        grid_size=16,
        variant_type=SudokuVariantType.X_SUDOKU
    )
    fingerprint = adapter.compute_fingerprint(grid, known_positions, variant)
    
    print(f"\n  X Sudoku 約束定義:")
    for name, diag in variant.diagonals.items():
        print(f"    {name}: {len(diag.cells)} 個位置")
    
    print(f"\n  100D 基因指紋:")
    print(f"    行維度均值: {sum(fingerprint['row_dimensions'])/16:.4f}")
    print(f"    列維度均值: {sum(fingerprint['col_dimensions'])/16:.4f}")
    print(f"    宮維度均值: {sum(fingerprint['box_dimensions'])/16:.4f}")
    print(f"    對角線維度: {fingerprint['diagonal_dimensions'][:2]}")
    print(f"    總體適應度: {fingerprint['total_fitness']:.4f}")
    
    # 驗證
    validation = variant.validate_solution(grid, known_positions)
    print(f"\n  驗證結果: {'✅ 有效' if validation['valid'] else '❌ 無效'}")
    
    return variant, fingerprint


def demo_killer_sudoku():
    """演示 Killer Sudoku"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║         演示：Killer Sudoku 變體                   ║")
    print("╚" + "═" * 68 + "╝")
    
    # 創建 Cage 定義
    cages_def = [
        {'cells': [(0, 0), (0, 1), (1, 0)], 'target_sum': 6},
        {'cells': [(0, 2), (0, 3), (1, 2), (1, 3)], 'target_sum': 10},
        {'cells': [(2, 0), (2, 1), (3, 0)], 'target_sum': 7},
        {'cells': [(0, 4), (1, 4), (0, 5)], 'target_sum': 8},
    ]
    
    # 創建 Killer Sudoku 變體
    variant = KillersudokuVariant(grid_size=16, box_size=4, cages=cages_def)
    
    # 創建示例網格
    grid = [[0] * 16 for _ in range(16)]
    
    # 填入一些已知位置
    known_positions = {
        (0, 0): 1, (0, 1): 2, (1, 0): 3,  # Cage 1: sum = 6 ✓
        (0, 2): 1, (0, 3): 2, (1, 2): 3, (1, 3): 4,  # Cage 2: sum = 10 ✓
    }
    
    for (r, c), v in known_positions.items():
        grid[r][c] = v
    
    # 計算 100D 基因指紋
    adapter = GeneFingerprint100DAdapter(
        grid_size=16,
        variant_type=SudokuVariantType.KILLER_SUDOKU
    )
    fingerprint = adapter.compute_fingerprint(grid, known_positions, variant)
    
    print(f"\n  Killer Sudoku Cage 定義:")
    for cage in variant.cages:
        print(f"    {cage.cage_id}: {len(cage.cells)} 個位置, 目標和={cage.target_sum}")
    
    print(f"\n  100D 基因指紋:")
    print(f"    行維度均值: {sum(fingerprint['row_dimensions'])/16:.4f}")
    print(f"    列維度均值: {sum(fingerprint['col_dimensions'])/16:.4f}")
    print(f"    宮維度均值: {sum(fingerprint['box_dimensions'])/16:.4f}")
    print(f"    Cage 求和維度: {fingerprint.get('cage_sum_dimensions', [])[:4]}")
    print(f"    總體適應度: {fingerprint['total_fitness']:.4f}")
    
    # 驗證
    validation = variant.validate_solution(grid, known_positions)
    print(f"\n  驗證結果: {'✅ 有效' if validation['valid'] else '❌ 無效'}")
    
    return variant, fingerprint


def main():
    """主執行入口"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║     符闔博弈優選策略 V19.0 - 數獨變體擴展演示         ║")
    print("╚" + "═" * 68 + "╝")
    
    # 演示 X Sudoku
    x_variant, x_fingerprint = demo_x_sudoku()
    
    # 演示 Killer Sudoku
    killer_variant, killer_fingerprint = demo_killer_sudoku()
    
    # 保存變體配置
    variants_config = {
        'x_sudoku': x_variant.get_additional_constraints(),
        'killer_sudoku': killer_variant.get_additional_constraints(),
        'x_fingerprint_summary': {
            'row_mean': sum(x_fingerprint['row_dimensions']) / 16,
            'col_mean': sum(x_fingerprint['col_dimensions']) / 16,
            'box_mean': sum(x_fingerprint['box_dimensions']) / 16,
            'total_fitness': x_fingerprint['total_fitness']
        },
        'killer_fingerprint_summary': {
            'row_mean': sum(killer_fingerprint['row_dimensions']) / 16,
            'col_mean': sum(killer_fingerprint['col_dimensions']) / 16,
            'box_mean': sum(killer_fingerprint['box_dimensions']) / 16,
            'total_fitness': killer_fingerprint['total_fitness']
        }
    }
    
    with open('sudoku_variants_config.json', 'w', encoding='utf-8') as f:
        json.dump(variants_config, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 變體配置已保存至: sudoku_variants_config.json")
    
    return variants_config


if __name__ == '__main__':
    main()
