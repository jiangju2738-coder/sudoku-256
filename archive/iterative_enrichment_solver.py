#!/usr/bin/env python3
"""
符闔數獨迭代增項求解系統
核心流程：
1. 邏輯推理增項（隱含單調、唯一候选數、X-Wing等）
2. 搜索增項（當邏輯無法推導時）
3. 每步重構約束規則
4. 重複直到滿盤或無法增項
"""

import json
import time
import re
from datetime import datetime
from collections import defaultdict, deque
from copy import deepcopy
from typing import List, Dict, Set, Tuple, Optional

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"
N = 16
N_BOX = 4


# =============================================================================
# 第一部分：謎題解析與約束建模
# =============================================================================

def parse_super_sudoku_config() -> Tuple[List[List[int]], List[Dict]]:
    """解析超級大數獨配置文件"""
    with open(f"{BASE_DIR}/超級大數獨_box_size4.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    grid = []
    
    for line in lines[2:]:
        line = line.strip()
        if not line:
            continue
        numbers = re.findall(r'\d+', line)
        numbers = [int(x) for x in numbers]
        if len(numbers) == 16:
            grid.append(numbers)
        if len(grid) >= 16:
            break
    
    known_digits = []
    for r in range(16):
        for c in range(16):
            if grid[r][c] != 0:
                known_digits.append({
                    "row": r+1,
                    "col": c+1,
                    "value": grid[r][c],
                    "cell_num": r*16 + c + 1,
                    "box": (r//4)*4 + (c//4) + 1
                })
    
    return grid, known_digits


class ConstraintModel:
    """行/列/宮三重約束模型"""
    
    def __init__(self, grid: List[List[int]]):
        self.grid = deepcopy(grid)
        self.constraints = {
            "row": {},  # 每行使用的值
            "col": {},  # 每列使用的值
            "box": {}   # 每宮使用的值
        }
        self.candidates = {}  # 每個格子的候选值
        self.build_constraints()
    
    def build_constraints(self):
        """建立約束模型"""
        # 初始化
        for r in range(16):
            self.constraints["row"][r] = set()
        for c in range(16):
            self.constraints["col"][c] = set()
        for b in range(16):
            self.constraints["box"][b] = set()
        
        self.candidates = {}
        
        # 填入已知數字並建構候选值
        for r in range(16):
            for c in range(16):
                if self.grid[r][c] != 0:
                    self.constraints["row"][r].add(self.grid[r][c])
                    self.constraints["col"][c].add(self.grid[r][c])
                    box_id = (r//4)*4 + (c//4)
                    self.constraints["box"][box_id].add(self.grid[r][c])
                    self.candidates[(r, c)] = {self.grid[r][c]}
                else:
                    self.candidates[(r, c)] = set(range(1, 17))
        
        # 更新空白格的候选值
        for r in range(16):
            for c in range(16):
                if self.grid[r][c] == 0:
                    box_id = (r//4)*4 + (c//4)
                    self.candidates[(r, c)] -= self.constraints["row"][r]
                    self.candidates[(r, c)] -= self.constraints["col"][c]
                    self.candidates[(r, c)] -= self.constraints["box"][box_id]
    
    def get_candidates_count(self) -> int:
        """獲取空白格數"""
        return sum(1 for r in range(16) for c in range(16) if self.grid[r][c] == 0)
    
    def fill_rate(self) -> float:
        """獲取填滿率"""
        known = sum(1 for r in range(16) for c in range(16) if self.grid[r][c] != 0)
        return known / 256


# =============================================================================
# 第二部分：邏輯推理引擎
# =============================================================================

class LogicReasoner:
    """邏輯推理引擎 - 基於約束傳播推導唯一值"""
    
    def __init__(self, constraint_model: ConstraintModel):
        self.cm = constraint_model
    
    def find_hidden_singles(self) -> List[Tuple[int, int, int]]:
        """尋找隱含單調 - 在某行/列/宮中只有某個位置能填某個值"""
        new_values = []
        
        # 行隱含單調
        for r in range(16):
            for v in range(1, 17):
                if v not in self.cm.constraints["row"][r]:
                    positions = [(r, c) for c in range(16) if v in self.cm.candidates[(r, c)]]
                    if len(positions) == 1:
                        new_values.append((positions[0][0], positions[0][1], v))
        
        # 列隱含單調
        for c in range(16):
            for v in range(1, 17):
                if v not in self.cm.constraints["col"][c]:
                    positions = [(r, c) for r in range(16) if v in self.cm.candidates[(r, c)]]
                    if len(positions) == 1:
                        new_values.append((positions[0][0], positions[0][1], v))
        
        # 宮隱含單調
        for b in range(16):
            br, bc = b // 4, b % 4
            for v in range(1, 17):
                if v not in self.cm.constraints["box"][b]:
                    positions = []
                    for dr in range(4):
                        for dc in range(4):
                            r, c = br*4 + dr, bc*4 + dc
                            if v in self.cm.candidates[(r, c)]:
                                positions.append((r, c))
                    if len(positions) == 1:
                        new_values.append((positions[0][0], positions[0][1], v))
        
        return new_values
    
    def find_naked_singles(self) -> List[Tuple[int, int, int]]:
        """尋找唯一候選數 - 某個格子只剩一個候选值"""
        new_values = []
        for r in range(16):
            for c in range(16):
                if self.cm.grid[r][c] == 0 and len(self.cm.candidates[(r, c)]) == 1:
                    v = next(iter(self.cm.candidates[(r, c)]))
                    new_values.append((r, c, v))
        return new_values
    
    def propagate(self) -> List[Tuple[int, int, int]]:
        """約束傳播 - 迭代推理直到無法推導"""
        all_new_values = []
        changed = True
        
        while changed:
            changed = False
            
            # 唯一候選數
            naked = self.find_naked_singles()
            for r, c, v in naked:
                if self.cm.grid[r][c] == 0:
                    self.fill_cell(r, c, v)
                    all_new_values.append((r, c, v))
                    changed = True
            
            # 隱含單調
            hidden = self.find_hidden_singles()
            for r, c, v in hidden:
                if self.cm.grid[r][c] == 0:
                    self.fill_cell(r, c, v)
                    all_new_values.append((r, c, v))
                    changed = True
        
        return all_new_values
    
    def fill_cell(self, r: int, c: int, v: int):
        """填充滿一個格子並更新約束"""
        if self.cm.grid[r][c] != 0:
            return
        self.cm.grid[r][c] = v
        self.cm.constraints["row"][r].add(v)
        self.cm.constraints["col"][c].add(v)
        box_id = (r//4)*4 + (c//4)
        self.cm.constraints["box"][box_id].add(v)
        self.cm.candidates[(r, c)] = {v}
        
        # 更新同列/行/宮的候选值
        for cc in range(16):
            if self.cm.grid[r][cc] == 0:
                self.cm.candidates[(r, cc)].discard(v)
        for rr in range(16):
            if self.cm.grid[rr][c] == 0:
                self.cm.candidates[(rr, c)].discard(v)
        br, bc = r//4, c//4
        for dr in range(4):
            for dc in range(4):
                rr, cc = br*4 + dr, bc*4 + dc
                if self.cm.grid[rr][cc] == 0:
                    self.cm.candidates[(rr, cc)].discard(v)


# =============================================================================
# 第三部分：搜索增項引擎
# =============================================================================

class SearchEnhancer:
    """搜索增項引擎 - 當邏輯無法推導時嘗試搜索增項"""
    
    def __init__(self, constraint_model: ConstraintModel):
        self.cm = constraint_model
    
    def find_bare_pairs(self) -> List[Tuple[int, int, int, int]]:
        """尋找裸對 - 兩個格子只有相同的兩個候选值"""
        pairs = []
        for r in range(16):
            for c in range(16):
                if self.cm.grid[r][c] == 0 and len(self.cm.candidates[(r, c)]) == 2:
                    cands = list(self.cm.candidates[(r, c)])
                    for cc in range(c+1, 16):
                        if self.cm.grid[r][cc] == 0:
                            if self.cm.candidates[(r, cc)] == set(cands):
                                pairs.append((r, c, c, cands[0]))
        return pairs
    
    def try_fill_from_candidates(self, r: int, c: int) -> Optional[int]:
        """嘗試從候选值中選擇一個值填入"""
        if self.cm.grid[r][c] != 0:
            return None
        
        cands = list(self.cm.candidates[(r, c)])
        if len(cands) == 0:
            return None
        
        # 選擇候选值最少的格子（最受限）
        return cands[0]
    
    def find_lowest_candidate_cell(self) -> Optional[Tuple[int, int, int]]:
        """找到候选值最少的空白格子"""
        min_count = 17
        best_cell = None
        
        for r in range(16):
            for c in range(16):
                if self.cm.grid[r][c] == 0:
                    count = len(self.cm.candidates[(r, c)])
                    if count < min_count:
                        min_count = count
                        best_cell = (r, c)
        
        if best_cell and min_count <= 2:
            r, c = best_cell
            v = next(iter(self.cm.candidates[(r, c)]))
            return (r, c, v)
        
        return None


# =============================================================================
# 第四部分：迭代增項求解系統
# =============================================================================

class IterativeEnrichmentSolver:
    """迭代增項求解系統"""
    
    def __init__(self, grid: List[List[int]], known_digits: List[Dict]):
        self.initial_grid = deepcopy(grid)
        self.initial_known = len(known_digits)
        self.cm = ConstraintModel(grid)
        self.iteration_log = []
        self.total_enrichments = 0
    
    def solve_iteration(self, iteration: int) -> Dict:
        """單次迭代：邏輯推理增項"""
        reasoner = LogicReasoner(self.cm)
        new_values = reasoner.propagate()
        
        return {
            "iteration": iteration,
            "new_values_count": len(new_values),
            "new_values": new_values,
            "fill_rate": self.cm.fill_rate(),
            "blank_cells": self.cm.get_candidates_count()
        }
    
    def enrich_by_search(self, iteration: int) -> Dict:
        """搜索增項"""
        enhancer = SearchEnhancer(self.cm)
        cell = enhancer.find_lowest_candidate_cell()
        
        if cell is None:
            return {
                "iteration": iteration,
                "new_values_count": 0,
                "new_values": [],
                "fill_rate": self.cm.fill_rate(),
                "blank_cells": self.cm.get_candidates_count(),
                "stopped": True,
                "reason": "無法找到可增項的格子"
            }
        
        r, c, v = cell
        reasoner = LogicReasoner(self.cm)
        reasoner.fill_cell(r, c, v)
        
        # 邏輯傳播
        propagated = reasoner.propagate()
        all_new = [(r, c, v)] + propagated
        
        return {
            "iteration": iteration,
            "new_values_count": len(all_new),
            "new_values": all_new,
            "fill_rate": self.cm.fill_rate(),
            "blank_cells": self.cm.get_candidates_count()
        }
    
    def solve(self, max_iterations: int = 100) -> Dict:
        """執行迭代增項求解"""
        print("="*80)
        print("符闔數獨迭代增項求解系統")
        print("="*80)
        print(f"初始已知數字: {self.initial_known} 個 (填滿率: {self.initial_known/256*100:.1f}%)")
        print(f"初始空白格子: {self.cm.get_candidates_count()} 個")
        print()
        
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # 邏輯推理增項
            result = self.solve_iteration(iteration)
            
            if result["new_values_count"] > 0:
                print(f"【迭代 {iteration}】邏輯推理增項: {result['new_values_count']} 個值")
                self.total_enrichments += result["new_values_count"]
                self.iteration_log.append(result)
                
                print(f"  填滿率: {result['fill_rate']*100:.1f}% | 空白: {result['blank_cells']} 格")
                
                if result["blank_cells"] == 0:
                    print(f"\n✅ 滿盤！總迭代: {iteration}, 總增項: {self.total_enrichments}")
                    return self._build_final_result(success=True, reason="滿盤")
                
                continue
            
            # 邏輯無法增項，嘗試搜索增項
            print(f"【迭代 {iteration}】邏輯推理無新值，嘗試搜索增項...")
            enrich_result = self.enrich_by_search(iteration)
            
            if enrich_result["new_values_count"] > 0:
                print(f"  搜索增項成功: {enrich_result['new_values_count']} 個值")
                self.total_enrichments += enrich_result["new_values_count"]
                self.iteration_log.append(enrich_result)
                
                if enrich_result["blank_cells"] == 0:
                    print(f"\n✅ 滿盤！總迭代: {iteration}, 總增項: {self.total_enrichments}")
                    return self._build_final_result(success=True, reason="滿盤")
            else:
                print(f"  ❌ 搜索增項失敗: {enrich_result.get('reason', '未知原因')}")
                return self._build_final_result(success=False, reason=enrich_result.get('reason', '無法增項'))
        
        return self._build_final_result(success=False, reason=f"達到最大迭代次數 {max_iterations}")
    
    def _build_final_result(self, success: bool, reason: str) -> Dict:
        """構建最終結果"""
        return {
            "success": success,
            "reason": reason,
            "initial_known": self.initial_known,
            "total_iterations": len(self.iteration_log),
            "total_enrichments": self.total_enrichments,
            "final_fill_rate": self.cm.fill_rate(),
            "final_blank_cells": self.cm.get_candidates_count(),
            "final_grid": self.cm.grid,
            "iteration_log": self.iteration_log
        }


# =============================================================================
# 第五部分：可視化與報告
# =============================================================================

def print_grid(grid: List[List[int]], known_mask: List[List[bool]] = None):
    """可視化輸出網格"""
    print("    " + " ".join(f" {chr(65+i):2s}" for i in range(16)))
    print("    " + "─"*48)
    for r in range(16):
        row_str = f" {r+1:2d} |"
        for c in range(16):
            val = grid[r][c]
            if known_mask and known_mask[r][c]:
                row_str += f" {val:2d}* "
            else:
                row_str += f" {val:2d}  "
        print(row_str)


def generate_progress_report(result: Dict):
    """生成進度報告"""
    print("\n" + "="*80)
    print("【迭代增項進度報告】")
    print("="*80)
    
    for entry in result["iteration_log"]:
        print(f"\n迭代 {entry['iteration']}:")
        print(f"  新增值數: {entry['new_values_count']}")
        print(f"  填滿率: {entry['fill_rate']*100:.1f}%")
        print(f"  空白格子: {entry['blank_cells']}")
        
        if entry['new_values_count'] <= 20:
            for r, c, v in entry['new_values'][:10]:
                print(f"    ({r+1}, {c+1}) = {v}")
            if entry['new_values_count'] > 10:
                print(f"    ... (還有 {entry['new_values_count']-10} 個)")


# =============================================================================
# 主函數
# =============================================================================

def main():
    grid, known_digits = parse_super_sudoku_config()
    
    # 創建初始謎題掩碼
    initial_mask = [[False]*16 for _ in range(16)]
    for k in known_digits:
        initial_mask[k["row"]-1][k["col"]-1] = True
    
    # 執行迭代增項求解
    solver = IterativeEnrichmentSolver(grid, known_digits)
    result = solver.solve(max_iterations=50)
    
    # 輸出最終網格
    print("\n" + "="*80)
    print("【最終謎題】")
    print("="*80)
    print_grid(result["final_grid"], initial_mask)
    
    # 生成進度報告
    generate_progress_report(result)
    
    # 保存結果
    output = {
        "timestamp": datetime.now().isoformat(),
        "result": result,
        "success": result["success"],
        "final_grid": result["final_grid"]
    }
    
    with open(f"{BASE_DIR}/迭代增項求解結果.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "="*80)
    print("求解完成")
    print("="*80)
    print(f"\n✅ 結果已保存: 迭代增項求解結果.json")
    
    return result


if __name__ == "__main__":
    main()
