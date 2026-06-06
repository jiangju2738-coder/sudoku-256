#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sudoku256 - 16x16 符闔超級數獨統一求解框架

模塊化架構:
    constants   單一數據源 (錨點、已知行、排列統計)
    loader      數據加載 (JSON / XLSX / 排列文件)
    propagator  約束傳播 (AC-3 + 符闔排列過濾)
    solver      統一求解器 (CP-SAT 主要 + 回溯備用)
    verifier    解驗證 (行/列/宮/符闔/錨點)

使用方式:
    from sudoku256 import Sudoku256Solver
    engine = Sudoku256Solver()
    result = engine.solve()
"""

from .solver import Sudoku256Solver
from .verifier import SolutionVerifier
from .constants import ANCHORS_92, ROW_LABELS, N, BOX_SIZE

__version__ = "2.0.0"
__all__ = [
    "Sudoku256Solver",
    "SolutionVerifier",
    "ANCHORS_92",
    "ROW_LABELS",
    "N",
    "BOX_SIZE",
]
