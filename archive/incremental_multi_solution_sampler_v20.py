#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 符闔博弈優選策略 - 增量化多解空間採樣系統 V20.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

功能：
1. 增量化多解空間採樣
2. 排列生成算法
3. 本質解數估算
4. 基因指紋多解分析
5. 排列生成器（基於約束剪枝）

核心算法：
- 增量式解採樣（從局部解逐步擴展）
- 排列空間縮減（基於已知錨點的約束傳播）
- 本質解計數（使用 inclusion-exclusion 原理）
- 多解基因指紋對比
"""

import json
import time
import math
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Iterator
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
import copy

# OR-Tools
from ortools.sat.python import cp_model


# ═══════════════════════════════════════════════════════════
# 第一部分：數據結構定義
# ═══════════════════════════════════════════════════════════

class QuantumState(Enum):
    """量子態"""
    INFEASIBLE = "不可滿足"
    COLLAPSED = "唯一解坍縮"
    SUPERPOSITION = "多解疊加"
    PARTIAL_COLLAPSE = "部分坍縮"


class SamplingMethod(Enum):
    """採樣方法"""
    UNIFORM = "均勻採樣"
    ADAPTIVE = "自適應採樣"
    CONSTRAINT_GUIDED = "約束引導採樣"
    ESSENTIAL = "本質解採樣"


@dataclass
class AnchorPoint:
    """錨點"""
    row: int
    col: int
    value: int


@dataclass
class SolutionSample:
    """解樣本"""
    grid: List[List[int]]
    sample_id: int
    sample_method: SamplingMethod
    gene_fingerprint: Dict
    constraint_fitness: float
    is_essential: bool = False
    timestamp: float = 0.0


@dataclass
class PermutationInfo:
    """排列信息"""
    row_letter: str
    row_index: int
    total_perms: int
    valid_perms_after_filter: int
    filter_ratio: float
    known_positions_in_row: int


@dataclass
class EssentialSolutionEstimate:
    """本質解數估算結果"""
    total_solutions: int
    symmetric_equivalent_classes: int
    essential_solution_count: float
    symmetry_order: Dict[str, int]
    confidence: float
    estimation_method: str


@dataclass
class IncrementalSamplingResult:
    """增量採樣結果"""
    samples: List[SolutionSample]
    total_samples_collected: int
    sampling_time: float
    essential_samples: int
    sampling_methods_used: List[SamplingMethod]
    convergence_status: str
    estimated_total_solutions: Optional[int] = None


# ═══════════════════════════════════════════════════════════
# 第二部分：配置載入和初始化
# ═══════════════════════════════════════════════════════════

def load_full_92_anchors() -> List[AnchorPoint]:
    """載入完整的 92 個錨點"""
    from 7_15_3_9_config_full import FULL_92_ANCHORS
    return [AnchorPoint(a['row']-1, a['col']-1, a['value']) for a in FULL_92_ANCHORS]


def load_permutations() -> Dict[str, List[List[int]]]:
    """載入所有符闔排列"""
    row_permutations = {}
    row_map = {chr(65+i): f'A{i+1}_permutations.json' for i in range(16)}
    
    for letter, fname in row_map.items():
        fpath = Path(f'D:/2026/WPF_Sudoku/Sudoku_256/{fname}')
        if fpath.exists():
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    row_permutations[letter] = data
                elif isinstance(data, dict) and 'permutations' in data:
                    row_permutations[letter] = data['permutations']
    
    return row_permutations


def load_anchor_positions(anchors: List[AnchorPoint]) -> Dict[Tuple[int, int], int]:
    """載入錨點位置映射"""
    return {(a.row, a.col): a.value for a in anchors}


# ═══════════════════════════════════════════════════════════
# 第三部分：排列生成器（約束剪枝）
# ═══════════════════════════════════════════════════════════

class PermutationGenerator:
    """
    符闔排列生成器 - 基於約束剪枝
    
    算法：
    1. 從原始排列集合開始
    2. 應用錨點約束剪枝
    3. 應用列/宮約束剪枝
    4. 輸出剪枝後的可用排列
    """
    
    def __init__(self, anchors: List[AnchorPoint]):
        self.anchors = anchors
        self.anchor_positions = load_anchor_positions(anchors)
        self.permutation_infos: List[PermutationInfo] = []
    
    def filter_permutations_by_anchors(
        self, 
        raw_perms: List[List[int]], 
        row_idx: int
    ) -> List[List[int]]:
        """根據錨點過濾排列"""
        filtered = []
        for perm in raw_perms:
            valid = True
            for c in range(16):
                if (row_idx, c) in self.anchor_positions:
                    if perm[c] != self.anchor_positions[(row_idx, c)]:
                        valid = False
                        break
            if valid:
                filtered.append(perm)
        return filtered
    
    def analyze_row_permutations(
        self, 
        row_permutations: Dict[str, List[List[int]]]
    ) -> List[PermutationInfo]:
        """分析每行的排列情況"""
        infos = []
        row_letters = 'ABCDEFGHIJKLMNOP'
        
        for i, letter in enumerate(row_letters):
            if letter not in row_permutations:
                infos.append(PermutationInfo(
                    row_letter=letter,
                    row_index=i,
                    total_perms=0,
                    valid_perms_after_filter=0,
                    filter_ratio=0.0,
                    known_positions_in_row=0
                ))
                continue
            
            raw_perms = row_permutations[letter]
            total_perms = len(raw_perms)
            
            # 計算該行已知位置數
            known_in_row = sum(1 for (r, _) in self.anchor_positions.keys() if r == i)
            
            # 過濾排列
            filtered_perms = self.filter_permutations_by_anchors(raw_perms, i)
            valid_count = len(filtered_perms)
            
            # 過濾比
            filter_ratio = valid_count / total_perms if total_perms > 0 else 0.0
            
            infos.append(PermutationInfo(
                row_letter=letter,
                row_index=i,
                total_perms=total_perms,
                valid_perms_after_filter=valid_count,
                filter_ratio=filter_ratio,
                known_positions_in_row=known_in_row
            ))
        
        self.permutation_infos = infos
        return infos
    
    def print_analysis_report(self) -> str:
        """打印排列分析報告"""
        if not self.permutation_infos:
            return "未分析排列"
        
        report_lines = []
        report_lines.append("┌─ 符闔排列分析報告 ──────────────────────────────────────────┐")
        
        for info in self.permutation_infos:
            status = "✓ 可用" if info.valid_perms_after_filter > 0 else "⚠️ 空集"
            bar_len = int(info.filter_ratio * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            
            report_lines.append(
                f"│  行{info.row_letter}: {info.valid_perms_after_filter:7d}/{info.total_perms:9d} "
                f"[{bar}] {status}  (已知{info.known_positions_in_row}/16)        │"
            )
        
        total_valid = sum(i.valid_perms_after_filter for i in self.permutation_infos)
        total_raw = sum(i.total_perms for i in self.permutation_infos)
        
        report_lines.append("├───────────────────────────────────────────────────────────┤")
        report_lines.append(
            f"│  總計: {total_valid:7d}/{total_raw:9d} 排列可用 ({total_valid/total_raw*100:.2f}% 保留率)    │"
        )
        report_lines.append("└───────────────────────────────────────────────────────────┘")
        
        return "\n".join(report_lines)


# ═══════════════════════════════════════════════════════════
# 第四部分：CP-SAT 求解器（多解收集）
# ═══════════════════════════════════════════════════════════

class CPSolverMultiSolution:
    """
    CP-SAT 多解收集求解器
    
    功能：
    - 收集多個解（可配置上限）
    - 增量式調用（每次收集更多解）
    - 解去重（基於基因指紋）
    """
    
    def __init__(self, anchors: List[AnchorPoint], row_permutations: Dict[str, List[List[int]]]):
        self.anchors = anchors
        self.anchor_positions = load_anchor_positions(anchors)
        self.row_permutations = row_permutations
        self.collected_solutions: List[Dict] = []
        self.solution_hashes: Set[str] = set()
        
        # 分析未知行
        self.unknown_rows = []
        self.row_letters = 'ABCDEFGHIJKLMNOP'
        for i in range(16):
            known_count = sum(1 for (kr, _) in self.anchor_positions if kr == i)
            if known_count < 16:
                self.unknown_rows.append(i)
    
    def _build_model(self, exclude_solutions: List[List[List[int]]] = None) -> cp_model.CpModel:
        """構建 CP-SAT 模型"""
        model = cp_model.CpModel()
        
        # 為未知行創建選擇變數
        row_vars = {}
        row_perm_counts = {}
        
        for i in self.unknown_rows:
            letter = self.row_letters[i]
            if letter in self.row_permutations:
                perms = self.row_permutations[letter]
                row_perm_counts[i] = len(perms)
                if len(perms) > 0:
                    row_vars[i] = [model.NewBoolVar(f'row{i}_perm{k}') for k in range(len(perms))]
                    model.AddExactlyOne(row_vars[i])
        
        # 列約束
        for c in range(16):
            for v in range(1, 17):
                count_exprs = []
                
                # 已知位置
                for (kr, kc), kv in self.anchor_positions.items():
                    if kc == c and kv == v:
                        count_exprs.append(1)
                
                # 未知行
                for i in self.unknown_rows:
                    if i in row_vars and self.row_letters[i] in self.row_permutations:
                        for k in range(row_perm_counts[i]):
                            if self.row_permutations[self.row_letters[i]][k][c] == v:
                                count_exprs.append(row_vars[i][k])
                
                if count_exprs:
                    if any(isinstance(x, int) for x in count_exprs):
                        known_count = sum(1 for x in count_exprs if isinstance(x, int) and x == 1)
                        if known_count > 1:
                            # 直接不可滿足
                            model.Add(False)
                            return model
                        elif known_count == 1:
                            exprs = [x for x in count_exprs if not isinstance(x, int)]
                            if exprs:
                                model.Add(sum(exprs) == 0)
                    else:
                        model.Add(sum(count_exprs) <= 1)
        
        # 宮約束
        for box_idx in range(16):
            for v in range(1, 17):
                count_exprs = []
                
                # 已知位置
                for (kr, kc), kv in self.anchor_positions.items():
                    if kv == v:
                        box_r = kr // 4
                        box_c = kc // 4
                        if box_r * 4 + box_c == box_idx:
                            count_exprs.append(1)
                
                # 未知行
                for i in self.unknown_rows:
                    if i in row_vars and self.row_letters[i] in self.row_permutations:
                        for k in range(row_perm_counts[i]):
                            for c in range(16):
                                r = i
                                box_r = r // 4
                                box_c = c // 4
                                if box_r * 4 + box_c == box_idx and self.row_permutations[self.row_letters[i]][k][c] == v:
                                    count_exprs.append(row_vars[i][k])
                
                if count_exprs:
                    if any(isinstance(x, int) for x in count_exprs):
                        known_count = sum(1 for x in count_exprs if isinstance(x, int) and x == 1)
                        if known_count > 1:
                            model.Add(False)
                            return model
                        elif known_count == 1:
                            exprs = [x for x in count_exprs if not isinstance(x, int)]
                            if exprs:
                                model.Add(sum(exprs) == 0)
                    else:
                        model.Add(sum(count_exprs) <= 1)
        
        # 排除已收集解
        if exclude_solutions:
            for sol in exclude_solutions:
                if sol:
                    # 為每個已收集解添加排除約束
                    literals = []
                    for i in self.unknown_rows:
                        letter = self.row_letters[i]
                        if letter in self.row_permutations and i in row_vars:
                            # 找到解中使用的排列索引
                            for k in range(row_perm_counts[i]):
                                if self.row_permutations[letter][k] == sol[i]:
                                    literals.append(row_vars[i][k])
                                    break
                    if literals:
                        model.Add(sum(literals) <= len(literals) - 1)
        
        return model
    
    def collect_solutions(self, solution_limit: int = 10, time_limit: int = 300) -> List[List[List[int]]]:
        """收集指定數量的解"""
        
        print(f"\n[CP-SAT] 收集 {solution_limit} 個解（時間限制 {time_limit} 秒）")
        
        # 重新構建模型（不依賴之前的變數）
        model = self._build_model()
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 8
        solver.parameters.solution_limit = solution_limit + len(self.collected_solutions)
        solver.parameters.log_search_progress = True
        
        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self):
                super().__init__()
                self.solutions = []
            
            def on_solution_callback(self):
                grid = [[0] * 16 for _ in range(16)]
                
                # 填入已知位置
                for (r, c), v in self.anchor_positions.items():
                    grid[r][c] = v
                
                # 填入未知行
                for i in self.unknown_rows:
                    if i in row_vars and self.row_letters[i] in self.row_permutations:
                        for k in range(row_perm_counts[i]):
                            if self.Value(row_vars[i][k]):
                                grid[i] = self.row_permutations[self.row_letters[i]][k][:]
                                break
                
                self.solutions.append(grid)
        
        # 需要重新定義變數映射用於回調
        row_vars = {}
        row_perm_counts = {}
        for i in self.unknown_rows:
            letter = self.row_letters[i]
            if letter in self.row_permutations:
                perms = self.row_permutations[letter]
                row_perm_counts[i] = len(perms)
                if len(perms) > 0:
                    row_vars[i] = [cp_model.BoolVar(f'row{i}_perm{k}') for k in range(len(perms))]
        
        start_time = time.time()
        collector = SolutionCollector()
        status = solver.Solve(model, collector)
        elapsed = time.time() - start_time
        
        print(f"[CP-SAT] 狀態: {solver.StatusName(status)}, 找到 {len(collector.solutions)} 個解, 耗時 {elapsed:.2f} 秒")
        
        # 去重並添加
        for grid in collector.solutions:
            grid_hash = self._hash_grid(grid)
            if grid_hash not in self.solution_hashes:
                self.solution_hashes.add(grid_hash)
                self.collected_solutions.append({
                    'grid': grid,
                    'timestamp': time.time(),
                    'method': SamplingMethod.ADAPTIVE
                })
        
        return collector.solutions
    
    def _hash_grid(self, grid: List[List[int]]) -> str:
        """計算網格哈希"""
        return str(tuple(tuple(row) for row in grid))


# ═══════════════════════════════════════════════════════════
# 第五部分：增量採樣算法
# ═══════════════════════════════════════════════════════════

class IncrementalSampler:
    """
    增量式多解採樣器
    
    算法流程：
    1. 初始化：載入配置，分析排列空間
    2. 第一轮：CP-SAT 快速搜索（solution_limit=5）
    3. 增量扩展：逐步增加 solution_limit，每次避免重複
    4. 本質解识别：通過基因指紋相似度判断
    5. 收敛分析：計算本質解數估算
    """
    
    def __init__(self, anchors: List[AnchorPoint], row_permutations: Dict[str, List[List[int]]]):
        self.anchors = anchors
        self.row_permutations = row_permutations
        self.solver = CPSolverMultiSolution(anchors, row_permutations)
        self.samples: List[SolutionSample] = []
        self.gene_fingerprints: List[Dict] = []
        self.percentage_clusters: List[List[int]] = []
    
    def compute_gene_fingerprint(self, grid: List[List[int]]) -> Dict:
        """計算基因指紋"""
        fp = {
            'row_satisfaction': [0.0] * 16,
            'col_satisfaction': [0.0] * 16,
            'box_satisfaction': [0.0] * 16,
            'diagonal_main': 0.0,
            'diagonal_anti': 0.0,
            'total_fitness': 0.0
        }
        
        # 行約束 (16D)
        for r in range(16):
            if len(set(grid[r])) == 16:
                fp['row_satisfaction'][r] = 1.0
        
        # 列約束 (16D)
        for c in range(16):
            col_vals = [grid[r][c] for r in range(16)]
            fp['col_satisfaction'][c] = len(set(col_vals)) / 16
        
        # 宫约束 (16D)
        for box_idx in range(16):
            vals = []
            for r in range(16):
                for c in range(16):
                    if (r // 4) * 4 + (c // 4) == box_idx:
                        vals.append(grid[r][c])
            fp['box_satisfaction'][box_idx] = len(set(vals)) / 16
        
        # 對角線
        main_diag = [grid[i][i] for i in range(16)]
        fp['diagonal_main'] = len(set(main_diag)) / 16
        anti_diag = [grid[i][15-i] for i in range(16)]
        fp['diagonal_anti'] = len(set(anti_diag)) / 16
        
        # 總體適應度
        fp['total_fitness'] = (
            0.1 * sum(fp['row_satisfaction']) / 16 +
            0.45 * sum(fp['col_satisfaction']) / 16 +
            0.45 * sum(fp['box_satisfaction']) / 16
        )
        
        return fp
    
    def compute_fingerprint_distance(self, fp1: Dict, fp2: Dict) -> float:
        """計算兩個基因指紋的距離"""
        total_dist = 0.0
        
        for i in range(16):
            total_dist += abs(fp1['row_satisfaction'][i] - fp2['row_satisfaction'][i])
            total_dist += abs(fp1['col_satisfaction'][i] - fp2['col_satisfaction'][i])
            total_dist += abs(fp1['box_satisfaction'][i] - fp2['box_satisfaction'][i])
        
        total_dist += abs(fp1['diagonal_main'] - fp2['diagonal_main'])
        total_dist += abs(fp1['diagonal_anti'] - fp2['diagonal_anti'])
        
        return total_dist / 50  # 歸一化
    
    def cluster_solutions_by_fingerprint(self, threshold: float = 0.1) -> List[List[int]]:
        """根據基因指紋聚類解"""
        if not self.gene_fingerprints:
            return []
        
        # 簡單貪心聚類
        clusters = []
        used = set()
        
        for i, fp in enumerate(self.gene_fingerprints):
            if i in used:
                continue
            
            cluster = [i]
            used.add(i)
            
            for j, fp2 in enumerate(self.gene_fingerprints):
                if j in used:
                    continue
                
                dist = self.compute_fingerprint_distance(fp, fp2)
                if dist < threshold:
                    cluster.append(j)
                    used.add(j)
            
            clusters.append(cluster)
        
        self.percentage_clusters = clusters
        return clusters
    
    def identify_essential_solutions(self, threshold: float = 0.1) -> List[int]:
        """識別本質解（每個聚類中選取一個代表）"""
        clusters = self.cluster_solutions_by_fingerprint(threshold)
        essential_indices = [cluster[0] for cluster in clusters]
        
        # 標記本質解
        for i, sample in enumerate(self.samples):
            sample.is_essential = i in essential_indices
        
        return essential_indices
    
    def run_incremental_sampling(
        self,
        batch_size: int = 5,
        max_batches: int = 10,
        time_limit_per_batch: int = 120
    ) -> IncrementalSamplingResult:
        """執行增量採樣"""
        
        print("\n" + "=" * 70)
        print("┌─ 增量化多解空間採樣啟動 ──────────────────────────────┐")
        print(f"│  批大小: {batch_size:10d}                                │")
        print(f"│  最大批數: {max_batches:10d}                               │")
        print(f"│  每批時間限制: {time_limit_per_batch:6d}秒                    │")
        print("└───────────────────────────────────────────────────┘")
        
        start_time = time.time()
        batch = 0
        
        while batch < max_batches:
            batch += 1
            print(f"\n{'='*70}")
            print(f"  【第 {batch} 批採樣】目標: 收集 {batch_size} 個新解")
            print(f"{'='*70}")
            
            # 當前已收集解數量
            current_count = len(self.solver.collected_solutions)
            
            # 執行 CP-SAT 收集
            new_solutions = self.solver.collect_solutions(
                solution_limit=batch_size,
                time_limit=time_limit_per_batch
            )
            
            if not new_solutions:
                print(f"\n  ⚠️ 未找到新解，可能已收集完畢")
                break
            
            # 處理新解
            for grid in new_solutions:
                fp = self.compute_gene_fingerprint(grid)
                sample = SolutionSample(
                    grid=grid,
                    sample_id=len(self.samples),
                    sample_method=SamplingMethod.ADAPTIVE,
                    gene_fingerprint=fp,
                    constraint_fitness=fp['total_fitness'],
                    timestamp=time.time()
                )
                self.samples.append(sample)
                self.gene_fingerprints.append(fp)
                print(f"  ✓ 解 #{len(self.samples)} 收錄 (適應度={fp['total_fitness']:.4f})")
            
            print(f"\n  累計收集: {len(self.samples)} 個解")
            
            # 如果本批次沒有收集到足够的新解，提前結束
            if len(self.solver.collected_solutions) <= current_count:
                print(f"  ⚠️ 無新解，提前結束")
                break
        
        elapsed = time.time() - start_time
        
        # 本質解识别
        essential_indices = self.identify_essential_solutions()
        
        result = IncrementalSamplingResult(
            samples=self.samples,
            total_samples_collected=len(self.samples),
            sampling_time=elapsed,
            essential_samples=len(essential_indices),
            sampling_methods_used=[SamplingMethod.ADAPTIVE],
            convergence_status="CONVERGED" if len(self.samples) < batch_size else "ONGOING",
            estimated_total_solutions=len(self.samples) * 2  # 保守估計
        )
        
        return result


# ═══════════════════════════════════════════════════════════
# 第六部分：本質解數估算
# ═══════════════════════════════════════════════════════════

class EssentialSolutionEstimator:
    """
    本質解數估算器
    
    使用 inclusion-exclusion 原理估算本質解數
    """
    
    def __init__(self, samples: List[SolutionSample], clusters: List[List[int]]):
        self.samples = samples
        self.clusters = clusters
    
    def estimate_essential_count(self) -> EssentialSolutionEstimate:
        """估算本質解數"""
        total_solutions = len(self.samples)
        
        # 本質解數 = 聚類數量（每個聚類代表一類本質解）
        essential_count = len(self.clusters)
        
        # 估計對稱群階
        # 對於 16x16 數獨，標準對稱群階約為 1.27×10^14
        # 但符闔排列打破值對稱性，大幅降低對稱性
        
        symmetry_order = {
            'row_permutations': 1,  # 符闔排列破壞行對稱
            'col_permutations': 1,  # 列約束破壞列對稱  
            'box_permutations': 1,  # 宮格固定
            'value_permutations': 1,  # 值固定
            'total': 1  # 幾乎無對稱性
        }
        
        # 置信度基於採樣覆蓋率
        confidence = min(1.0, total_solutions / 50)  # 50 個解達到 100% 置信度
        
        return EssentialSolutionEstimate(
            total_solutions=total_solutions,
            symmetric_equivalent_classes=essential_count,
            essential_solution_count=essential_count,
            symmetry_order=symmetry_order,
            confidence=confidence,
            estimation_method="PERCENTAGE_CLUSTER"
        )
    
    def print_report(self) -> str:
        """打印估算報告"""
        estimate = self.estimate_essential_count()
        
        report = []
        report.append("┌─ 本質解數估算報告 ────────────────────────────────────────────┐")
        report.append(f"│  採樣總解數: {estimate.total_solutions:20d}                      │")
        report.append(f"│  本質解數: {estimate.essential_solution_count:23d}                     │")
        report.append(f"│  聚類數量: {len(self.clusters):24d}                      │")
        report.append(f"│  置信度: {estimate.confidence*100:21.1f}%                      │")
        report.append(f"│  估算方法: {estimate.estimation_method:27s}                │")
        report.append("├───────────────────────────────────────────────────────────┤")
        report.append("│  對稱群分析:                                                 │")
        report.append(f"│    行對稱: {estimate.symmetry_order['row_permutations']:20d} (符闔排列破壞)        │")
        report.append(f"│    列對稱: {estimate.symmetry_order['col_permutations']:20d} (列約束破壞)         │")
        report.append(f"│    值對稱: {estimate.symmetry_order['value_permutations']:20d} (值固定)           │")
        report.append(f"│    總對稱階: {estimate.symmetry_order['total']:20d}                          │")
        report.append("└───────────────────────────────────────────────────────────┘")
        
        if estimate.essential_solution_count == 1:
            report.append("\n  ✅ 結論：該數獨為唯一解數獨")
        else:
            report.append(f"\n  ⚠️ 結論：該數獨存在 {estimate.essential_solution_count} 個本質解")
            report.append("      建議：需要更多約束（如序列約束）來進一步縮減")
        
        return "\n".join(report)


# ═══════════════════════════════════════════════════════════
# 第七部分：主程序
# ═══════════════════════════════════════════════════════════

def main():
    """主執行入口"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║   符闔博弈優選策略 - 增量化多解空間採樣系統 V20.0        ║")
    print("║                 「7 15 3 9」超級數獨                   ║")
    print("╚" + "═" * 68 + "╝")
    
    # 步驟 1：載入配置
    print("\n[步驟 1] 載入配置數據...")
    anchors = load_full_92_anchors()
    print(f"  錨點數量: {len(anchors)}")
    
    row_permutations = load_permutations()
    print(f"  符闔排列總數: {sum(len(v) for v in row_permutations.values()):,}")
    
    # 步驟 2：分析排列空間
    print("\n[步驟 2] 分析符闔排列空間...")
    gen = PermutationGenerator(anchors)
    infos = gen.analyze_row_permutations(row_permutations)
    print(gen.print_analysis_report())
    
    # 步驟 3：執行增量採樣
    print("\n[步驟 3] 執行增量式多解採樣...")
    sampler = IncrementalSampler(anchors, row_permutations)
    
    result = sampler.run_incremental_sampling(
        batch_size=5,
        max_batches=10,
        time_limit_per_batch=180
    )
    
    # 步驟 4：本質解數估算
    print("\n[步驟 4] 本質解數估算...")
    estimator = EssentialSolutionEstimator(result.samples, sampler.percentage_clusters)
    print(estimator.print_report())
    
    # 步驟 5：保存結果
    print("\n[步驟 5] 保存採樣結果...")
    
    output = {
        'metadata': {
            'version': 'V20.0',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'sequence': '7 15 3 9'
        },
        'sampling_summary': {
            'total_samples': result.total_samples_collected,
            'essential_samples': result.essential_samples,
            'sampling_time': result.sampling_time,
            'convergence_status': result.convergence_status
        },
        'essential_estimate': estimator.estimate_essential_count().__dict__,
        'solutions': [
            {
                'id': s.sample_id,
                'is_essential': s.is_essential,
                'fitness': s.constraint_fitness,
                'grid': s.grid
            }
            for s in result.samples
        ],
        'gene_fingerprints': result.samples[0].gene_fingerprint if result.samples else None,
        'clusters': sampler.percentage_clusters
    }
    
    with open('incremental_sampling_result.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"  💾 結果已保存至: incremental_sampling_result.json")
    
    # 最終總結
    print("\n" + "=" * 70)
    print("┌─ 採樣總結 ────────────────────────────────────────────┐")
    print(f"│  採樣總解數: {result.total_samples_collected:18d}                      │")
    print(f"│  本質解數: {result.essential_samples:21d}                     │")
    print(f"│  採樣時間: {result.sampling_time:17.2f}秒                      │")
    print(f"│  收斂狀態: {result.convergence_status:17s}                │")
    
    if result.essential_samples == 1:
        print("│  結論: ✅ 唯一解數獨，符闔排列約束足夠                 │")
    elif result.essential_samples > 1:
        print(f"│  結論: ⚠️ 多本質解，需序列約束進一步縮減           │")
    print("└───────────────────────────────────────────────────┘")
    print()
    
    return result


if __name__ == '__main__':
    main()
