#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 超級大數獨 256 宮格 - 智能解析與三約束推理系統 V2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

解析來源：超級大數獨_box_size4.txt
功能：
  1. 自動解析 92 個錨點
  2. 計算單行符闔排列解數
  3. 三約束規則推理（行/列/宮）
  4. 內存靈活調用優化
"""

import json
import re
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════════════════
# 數據結構定義
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Cell:
    """單元格"""
    row: str          # A-P
    col: str          # D-S (1-16)
    row_idx: int      # 0-15
    col_idx: int      # 0-15
    value: Optional[int] = None  # 已知值，0 表示未知
    candidate_set: Set[int] = field(default_factory=lambda: set(range(1, 17)))  # 候選集
    constraint: str = "unknown"  # 約束類型

@dataclass
class RowConstraint:
    """行符闔排列約束"""
    row_letter: str
    row_idx: int
    permutation_count: int  # 符闔排列總數
    permutations: List[List[int]] = field(default_factory=list)  # 實際排列
    known_values: Dict[int, int] = field(default_factory=dict)  # 列索引->值

@dataclass
class SudokuGrid:
    """數獨網格"""
    size: int = 16
    box_size: int = 4
    cells: Dict[Tuple[int, int], Cell] = field(default_factory=dict)
    row_constraints: Dict[str, RowConstraint] = field(default_factory=dict)
    column_constraints: Dict[int, Set[int]] = field(default_factory=dict)
    box_constraints: Dict[Tuple[int, int], Set[int]] = field(default_factory=dict)

# ═══════════════════════════════════════════════════════════════════════════
# 解析器：自動讀取並解析謎題錨點
# ═══════════════════════════════════════════════════════════════════════════

class SuperSudokuParser:
    """超級大數獨解析器"""
    
    # 錨點名稱映射（從文件提取）
    ANCHOR_NAMES = {
        'A': 'AD', 'B': 'AE', 'C': 'AF', 'D': 'AG',
        'E': 'AH', 'F': 'AI', 'G': 'AJ', 'H': 'AK',
        'I': 'AL', 'J': 'AM', 'K': 'AN', 'L': 'AO',
        'M': 'AP', 'N': 'AQ', 'O': 'AR', 'P': 'AS'
    }
    
    # 行符闔排列數量
    PERM_COUNTS = {
        'A': 8731, 'B': 902, 'C': 407669, 'D': 1980,
        'E': 633271, 'F': 359, 'G': 2356, 'H': 4782,
        'I': 164, 'J': 28984, 'K': 2972, 'L': 620,
        'M': 484, 'N': 10668, 'O': 5990, 'P': 1809
    }
    
    # 列映射
    COL_MAP = {
        0: 'D', 1: 'E', 2: 'F', 3: 'G',
        4: 'H', 5: 'I', 6: 'J', 7: 'K',
        8: 'L', 9: 'M', 10: 'N', 11: 'O',
        12: 'P', 13: 'Q', 14: 'R', 15: 'S'
    }
    
    def __init__(self):
        self.grid = SudokuGrid()
        self.known_cells = []
        self.unknown_cells = []
        self.parsed_data = {}
        
    def parse_anchors(self, text: str) -> Dict[Tuple[int, int], int]:
        """
        解析錨點數據
        
        從超級大數獨_box_size4.txt 中提取已知數字
        格式：行字母 [值1, 值2, ...] 其中 0 表示未知
        """
        anchors = {}
        
        # 模式 1: 行錨點 [0,0,3,0, 0,12,0,5, ...]
        row_pattern = r'行([A-P])\s*\[(.*?)\]'
        
        for match in re.finditer(row_pattern, text):
            row_letter = match.group(1)
            values_str = match.group(2)
            values = [int(v.strip()) for v in values_str.split(',')]
            
            row_idx = ord(row_letter) - ord('A')
            
            for col_idx, val in enumerate(values):
                if val != 0:  # 0 表示未知
                    anchors[(row_idx, col_idx)] = val
                    cell = Cell(
                        row=row_letter,
                        col=self.COL_MAP[col_idx],
                        row_idx=row_idx,
                        col_idx=col_idx,
                        value=val,
                        candidate_set=set([val])  # 已知值
                    )
                    self.grid.cells[(row_idx, col_idx)] = cell
                    self.known_cells.append(cell)
                else:
                    cell = Cell(
                        row=row_letter,
                        col=self.COL_MAP[col_idx],
                        row_idx=row_idx,
                        col_idx=col_idx,
                        value=None,
                        candidate_set=set(range(1, 17))  # 初始全候選
                    )
                    self.grid.cells[(row_idx, col_idx)] = cell
                    self.unknown_cells.append(cell)
        
        return anchors
    
    def parse_permutation_counts(self, text: str) -> Dict[str, int]:
        """
        解析每行符闔排列數量
        
        格式：第1行：A1-A8731 第一行符闔排列.xlsx；滿足1行約束規則排列數 8731
        """
        perm_pattern = r'第(\d+)行：([A-P])(\d+)-[A-P](\d+)\s+.*?滿足\d+行約束規則排列數\s+(\d+)'
        
        for match in re.finditer(perm_pattern, text):
            row_num = int(match.group(1))
            row_letter = match.group(2)
            start_idx = int(match.group(3))
            end_idx = int(match.group(4))
            count = int(match.group(5))
            
            self.PERM_COUNTS[row_letter] = count
            
            # 創建行約束
            row_constraint = RowConstraint(
                row_letter=row_letter,
                row_idx=row_num - 1,
                permutation_count=count
            )
            self.grid.row_constraints[row_letter] = row_constraint
        
        return self.PERM_COUNTS
    
    def parse_cell_candidates(self, text: str) -> Dict[Tuple[int, int], Set[int]]:
        """
        解析每個單元格的候選集
        
        格式：1：AD = 0 解集 = 2 6 7 9 10 11
             3：AF = 3  (已知值)
        """
        candidates = {}
        
        # 匹配單元格定義：行號：AB = X 解集 = ... 或 AB = 值
        cell_pattern = r'(\d+):\s*([A-P])([A-S])\s*=\s*(\d+)(?:\s+解集\s*=\s*(.+))?'
        
        for match in re.finditer(cell_pattern, text):
            row_num = int(match.group(1))
            row_letter = match.group(2)
            col_letter = match.group(3)
            value = int(match.group(4))
            candidates_str = match.group(5)
            
            row_idx = ord(row_letter) - ord('A')
            
            # 查找列索引
            col_idx = None
            for ci, cl in self.COL_MAP.items():
                if cl == col_letter:
                    col_idx = ci
                    break
            
            if col_idx is None:
                continue
            
            if value != 0:
                # 已知值
                candidates[(row_idx, col_idx)] = {value}
            elif candidates_str:
                # 候選集
                cand_set = set(int(x) for x in candidates_str.split())
                candidates[(row_idx, col_idx)] = cand_set
            else:
                # 全候選
                candidates[(row_idx, col_idx)] = set(range(1, 17))
        
        return candidates
    
    def load_file(self, filepath: str) -> bool:
        """
        從文件加載數據
        
        讀取超級大數獨_box_size4.txt
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析錨點
            anchors = self.parse_anchors(content)
            print(f"✓ 解析錨點: {len(anchors)} 個已知數字")
            
            # 解析符闔排列數量
            perm_counts = self.parse_permutation_counts(content)
            print(f"✓ 解析符闔排列: 16 行數據")
            
            # 解析單元格候選集
            candidates = self.parse_cell_candidates(content)
            print(f"✓ 解析單元格候選: {len(candidates)} 個")
            
            # 更新單元格候選集
            for (row_idx, col_idx), cand_set in candidates.items():
                if (row_idx, col_idx) in self.grid.cells:
                    self.grid.cells[(row_idx, col_idx)].candidate_set = cand_set
            
            self.parsed_data = {
                'anchors': anchors,
                'permutation_counts': perm_counts,
                'cell_candidates': candidates
            }
            
            return True
            
        except Exception as e:
            print(f"✗ 文件加載失敗: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# 三約束規則推理引擎
# ═══════════════════════════════════════════════════════════════════════════

class ConstraintInferenceEngine:
    """三約束規則推理引擎"""
    
    def __init__(self, grid: SudokuGrid):
        self.grid = grid
        self.inference_log = []
        
    def apply_row_constraint(self, row_idx: int) -> Dict[Tuple[int, int], Set[int]]:
        """
        應用行約束：每行 16 個值互異
        
        從符闔排列中篩選符合已知值的排列
        """
        row_letter = chr(ord('A') + row_idx)
        known_in_row = {}
        
        for col_idx in range(16):
            cell = self.grid.cells.get((row_idx, col_idx))
            if cell and cell.value is not None:
                known_in_row[col_idx] = cell.value
        
        # 从已知值推断该行所有单元格的候选集
        used_values = set(known_in_row.values())
        reductions = {}
        
        for col_idx in range(16):
            cell = self.grid.cells.get((row_idx, col_idx))
            if cell and cell.value is None:
                # 移除已使用的值
                new_candidates = cell.candidate_set - used_values
                reductions[(row_idx, col_idx)] = new_candidates
                self.grid.cells[(row_idx, col_idx)].candidate_set = new_candidates
        
        return reductions
    
    def apply_column_constraint(self, col_idx: int) -> Dict[Tuple[int, int], Set[int]]:
        """
        應用列約束：每列 16 個值互異
        
        从已知值推断该列所有单元格的候选集
        """
        known_in_col = {}
        
        for row_idx in range(16):
            cell = self.grid.cells.get((row_idx, col_idx))
            if cell and cell.value is not None:
                known_in_col[row_idx] = cell.value
        
        used_values = set(known_in_col.values())
        reductions = {}
        
        for row_idx in range(16):
            cell = self.grid.cells.get((row_idx, col_idx))
            if cell and cell.value is None:
                new_candidates = cell.candidate_set - used_values
                reductions[(row_idx, col_idx)] = new_candidates
                self.grid.cells[(row_idx, col_idx)].candidate_set = new_candidates
        
        return reductions
    
    def apply_box_constraint(self, box_row: int, box_col: int) -> Dict[Tuple[int, int], Set[int]]:
        """
        應用宮約束：每個 4×4 宮格內 16 個值互異
        
        box_row, box_col: 宮格在 4×4 網格中的位置 (0-3, 0-3)
        """
        known_in_box = {}
        cells_in_box = []
        
        for r in range(4):
            for c in range(4):
                row_idx = box_row * 4 + r
                col_idx = box_col * 4 + c
                cell = self.grid.cells.get((row_idx, col_idx))
                cells_in_box.append((row_idx, col_idx, cell))
                if cell and cell.value is not None:
                    known_in_box[(row_idx, col_idx)] = cell.value
        
        used_values = set(known_in_box.values())
        reductions = {}
        
        for row_idx, col_idx, cell in cells_in_box:
            if cell and cell.value is None:
                new_candidates = cell.candidate_set - used_values
                reductions[(row_idx, col_idx)] = new_candidates
                self.grid.cells[(row_idx, col_idx)].candidate_set = new_candidates
        
        return reductions
    
    def apply_all_constraints(self) -> Dict[str, Dict[Tuple[int, int], Set[int]]]:
        """
        應用所有三約束規則
        
        返回每種約束的 reductions
        """
        results = {
            'row': {},
            'column': {},
            'box': {}
        }
        
        # 行約束
        for row_idx in range(16):
            results['row'][f'row_{row_idx}'] = self.apply_row_constraint(row_idx)
        
        # 列約束
        for col_idx in range(16):
            results['column'][f'col_{col_idx}'] = self.apply_column_constraint(col_idx)
        
        # 宮約束
        for box_r in range(4):
            for box_c in range(4):
                key = f'box_{box_r}_{box_c}'
                results['box'][key] = self.apply_box_constraint(box_r, box_c)
        
        return results


# ═══════════════════════════════════════════════════════════════════════════
# 單行解數計算器
# ═══════════════════════════════════════════════════════════════════════════

class RowSolutionCounter:
    """
    單行符闔排列解數計算器
    
    計算每行在已知錨點約束下，符合符闔排列規則的排列數量
    """
    
    def __init__(self, grid: SudokuGrid, parser: SuperSudokuParser):
        self.grid = grid
        self.parser = parser
        
    def count_single_row_solutions(self, row_idx: int) -> Dict:
        """
        計算單行可能的解的數量
        
        1. 從該行的符闔排列中篩選
        2. 匹配已知錨點值
        3. 計算符合條件的排列數
        """
        row_letter = chr(ord('A') + row_idx)
        perm_count = self.parser.PERM_COUNTS.get(row_letter, 0)
        
        # 收集該行的已知錨點
        known_values = {}
        for col_idx in range(16):
            cell = self.grid.cells.get((row_idx, col_idx))
            if cell and cell.value is not None:
                known_values[col_idx] = cell.value
        
        # 計算候選集大小乘積（上界估計）
        candidate_product = 1
        for col_idx in range(16):
            cell = self.grid.cells.get((row_idx, col_idx))
            if cell:
                cand_size = len(cell.candidate_set)
                if cand_size == 0:
                    candidate_product = 0
                    break
                candidate_product *= cand_size
        
        # 實際符闔排列符合度
        # 需要加载该行的排列文件
        # 這裡用比例估算：符闔排列數 / 16! 的比例
        
        result = {
            'row_letter': row_letter,
            'row_idx': row_idx,
            'permutation_count': perm_count,
            'known_anchors': known_values,
            'known_count': len(known_values),
            'candidate_product_upper_bound': candidate_product,
            'estimated_solutions': self._estimate_solutions(row_idx, known_values, perm_count)
        }
        
        return result
    
    def _estimate_solutions(self, row_idx: int, known_values: Dict[int, int], 
                           perm_count: int) -> int:
        """
        估算符闔排列符合已知錨點的排列數
        
        原理：從所有符闔排列中篩選匹配已知值的排列
        """
        # 簡化估算：已知值越多，符合排列越少
        # 比例因子：每增加一個已知值，排列數約減少到 1/16
        
        if len(known_values) == 0:
            return perm_count
        
        # 使用對數估算
        import math
        if perm_count == 0:
            return 0
        
        # 簡化模型：排列約束比例
        ratio = (15/16) ** len(known_values)
        estimated = int(perm_count * ratio)
        
        return max(0, estimated)
    
    def count_all_rows(self) -> List[Dict]:
        """計算所有行的解數"""
        results = []
        for row_idx in range(16):
            result = self.count_single_row_solutions(row_idx)
            results.append(result)
        return results


# ═══════════════════════════════════════════════════════════════════════════
# 主執行：解析 → 約束推理 → 解數計算
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print(" 超級大數獨 256 宮格 - 智能解析與三約束推理系統 V2")
    print("=" * 70)
    
    # 1. 初始化解析器
    parser = SuperSudokuParser()
    
    # 2. 加載文件
    success = parser.load_file('超級大數獨_box_size4.txt')
    if not success:
        print("文件加載失敗，使用內建數據")
        return
    
    print("\n" + "-" * 70)
    print(" 解析完成匯總")
    print("-" * 70)
    
    # 3. 顯示錨點統計
    print(f"\n📊 錨點統計:")
    row_counts = defaultdict(int)
    for (row_idx, col_idx) in parser.grid.cells:
        cell = parser.grid.cells[(row_idx, col_idx)]
        if cell.value is not None:
            row_counts[row_idx] += 1
    
    for row_idx in range(16):
        row_letter = chr(ord('A') + row_idx)
        count = row_counts[row_idx]
        print(f"  行{row_idx+1} ({row_letter}): {count}/16 已知 ({count/16*100:.0f}%)")
    
    total_known = sum(row_counts.values())
    total_cells = 256
    print(f"\n  總計: {total_known}/{total_cells} 已知 ({total_known/total_cells*100:.1f}%)")
    
    # 4. 三約束推理
    print("\n" + "-" * 70)
    print(" 三約束規則推理")
    print("-" * 70)
    
    engine = ConstraintInferenceEngine(parser.grid)
    constraint_results = engine.apply_all_constraints()
    
    # 顯示約束傳播結果
    reductions_summary = {
        'row': 0, 'column': 0, 'box': 0
    }
    
    for constraint_type, data in constraint_results.items():
        for key, reductions in data.items():
            reductions_summary[constraint_type] += len(reductions)
    
    print(f"\n  行約束傳播: {reductions_summary['row']} 個單元格候選集縮減")
    print(f"  列約束傳播: {reductions_summary['column']} 個單元格候選集縮減")
    print(f"  宮約束傳播: {reductions_summary['box']} 個單元格候選集縮減")
    
    # 5. 單行解數計算
    print("\n" + "-" * 70)
    print(" 單行符闔排列解數計算")
    print("-" * 70)
    
    counter = RowSolutionCounter(parser.grid, parser)
    row_results = counter.count_all_rows()
    
    print(f"\n{'行號':<4} {'排列總數':>10} {'已知錨點':>8} {'估算解數':>10} {'候選上界':>12}")
    print("-" * 50)
    
    for result in row_results:
        print(f"{result['row_letter']:<4} {result['permutation_count']:>10} "
              f"{result['known_count']:>8} {result['estimated_solutions']:>10} "
              f"{result['candidate_product_upper_bound']:>12}")
    
    # 6. 內存靈活調用優化總結
    print("\n" + "-" * 70)
    print(" 內存靈活調用優化")
    print("-" * 70)
    
    # 統計候選集分布
    cand_size_dist = Counter()
    for cell in parser.grid.cells.values():
        if cell.value is None:
            cand_size_dist[len(cell.candidate_set)] += 1
    
    print("\n  未知單元格候選集大小分布:")
    for size in sorted(cand_size_dist.keys()):
        count = cand_size_dist[size]
        print(f"    候選數={size}: {count} 個單元格 ({count/len(parser.unknown_cells)*100:.1f}%)")
    
    # 儲存結果
    output = {
        'anchors': {f"{r},{c}": v for (r, c), v in parser.parsed_data['anchors'].items()},
        'permutation_counts': parser.PERM_COUNTS,
        'constraint_reductions': reductions_summary,
        'row_solutions': row_results,
        'candidate_distribution': dict(cand_size_dist)
    }
    
    with open('super_sudoku_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 結果已保存至: super_sudoku_analysis_result.json")
    print("\n" + "=" * 70)
    print(" 分析完成")
    print("=" * 70)


if __name__ == '__main__':
    main()
