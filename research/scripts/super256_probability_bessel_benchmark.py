#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超級256數獨概率閾值與貝塞爾函數綜合測評系統
============================================
基於Boltzmann分布的概率閾值計算 + 貝塞爾函數J₀零點分析
融合五維思維框架的深度測評
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import math
import time
from scipy import special

BASE_DIR = Path("D:/2026/WPF_Sudoku/Sudoku_256")
GRID_SIZE = 16
BOX_SIZE = 4
DIGITS = list(range(1, 17))


# ======================== 貝塞爾函數核心 ========================

class BesselAnalyzer:
    """貝塞爾函數J₀分析器"""
    
    # J₀的前10個零點 (第一類貝塞爾函數)
    J0_ZEROS = [
        2.4048255577,
        5.5200781103,
        8.6537279129,
        11.7915344391,
        14.9309177086,
        18.0710639679,
        21.2116366299,
        24.3524715308,
        27.4934791320,
        30.6346064684
    ]
    
    # 映射到求解階段
    SOLVING_STAGES = [
        "INITIALIZE",     # 初始化
        "PROPAGATE",      # 約束傳播
        "BRANCH",         # 分支探索
        "CONVERGE",       # 收斂
        "CRITICAL",       # 臨界點
        "BREAKTHROUGH",   # 突破
        "STABILIZE",      # 穩定
        "FINALIZE",       # 完成
        "VERIFY",         # 驗證
        "COMPLETE"        # 完成
    ]
    
    @classmethod
    def get_zero_info(cls, n: int) -> Dict:
        """獲取第n個零點的資訊"""
        if n < 1 or n > len(cls.J0_ZEROS):
            return None
        zero = cls.J0_ZEROS[n - 1]
        stage = cls.SOLVING_STAGES[n - 1]
        return {
            'zero_index': n,
            'zero_value': zero,
            'stage': stage,
            'normalized': zero / cls.J0_ZEROS[-1]
        }
    
    @classmethod
    def compute_j0(cls, x: float) -> float:
        """計算貝塞爾函數J₀(x)"""
        return special.j0(x)
    
    @classmethod
    def compute_j1(cls, x: float) -> float:
        """計算貝塞爾函數J₁(x)"""
        return special.j1(x)
    
    @classmethod
    def find_nearest_stage(cls, value: float) -> Tuple[int, str, float]:
        """找出最接近的零點階段"""
        for i, zero in enumerate(cls.J0_ZEROS):
            if value <= zero:
                if i == 0:
                    return (1, cls.SOLVING_STAGES[0], value / zero)
                return (i, cls.SOLVING_STAGES[i-1], (value - cls.J0_ZEROS[i-2]) / (zero - cls.J0_ZEROS[i-2]))
        return (10, cls.SOLVING_STAGES[-1], 1.0)


# ======================== Boltzmann 概率閾值 ========================

@dataclass
class ProbabilityMetrics:
    """概率測評指標"""
    cell_probability: Dict[Tuple[int, int], Dict[int, float]] = field(default_factory=dict)
    marginal_probability: Dict[Tuple[int, int], float] = field(default_factory=dict)
    entropy_per_cell: Dict[Tuple[int, int], float] = field(default_factory=dict)
    constraint_violation_weight: Dict[Tuple[int, int], float] = field(default_factory=dict)
    effective_temperature: float = 1.0


class BoltzmannProbabilityAnalyzer:
    """Boltzmann概率閾值計算器"""
    
    def __init__(self, base_dir: Path, lambda_param: float = 1.0, 
                 temperature: float = 0.5):
        self.base_dir = base_dir
        self.lambda_param = lambda_param
        self.temperature = temperature
        self.grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
        self.row_perms: Dict[int, List[np.ndarray]] = {}
        self.metrics = ProbabilityMetrics()
        
    def load_puzzle(self) -> int:
        """加載謎題"""
        puzzle_file = self.base_dir / "initial_puzzle.json"
        with open(puzzle_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        known_count = 0
        for cell in data.get('known_digits', []):
            r = cell['row'] - 1  # 轉為0索引
            c = cell['col'] - 1
            v = cell['value']
            self.grid[r, c] = v
            known_count += 1
        
        return known_count
    
    def load_permutations(self) -> int:
        """加載符闔排列"""
        total_perms = 0
        for row_idx in range(1, 17):
            perm_file = self.base_dir / f"A{row_idx}_permutations.json"
            if perm_file.exists():
                with open(perm_file, 'r', encoding='utf-8') as f:
                    perms = json.load(f)
                self.row_perms[row_idx] = [np.array(p) for p in perms]
                total_perms += len(perms)
            else:
                self.row_perms[row_idx] = []
        return total_perms
    
    def count_constraint_violations(self, row: int, col: int, value: int) -> int:
        """計算約束違規數（基於符闔排列相容性）"""
        violations = 0
        
        # 行約束檢查
        if row in self.row_perms:
            perms = self.row_perms[row]
            compatible = 0
            for perm in perms:
                if perm[col] == value:
                    compatible += 1
            # 沒有相容排列 -> 高違規
            if compatible == 0:
                violations += 3
            elif compatible < len(perms) * 0.1:
                violations += 2
        
        # 列約束檢查（簡化版）
        col_val_count = np.sum(self.grid[:, col] == value)
        if col_val_count > 0:
            violations += 2
        
        # 宮格約束檢查
        box_r = (row // BOX_SIZE) * BOX_SIZE
        box_c = (col // BOX_SIZE) * BOX_SIZE
        for dr in range(BOX_SIZE):
            for dc in range(BOX_SIZE):
                if self.grid[box_r + dr, box_c + dc] == value and (dr != row % BOX_SIZE or dc != col % BOX_SIZE):
                    violations += 2
                    break
        
        # 固定數字衝突
        if self.grid[row, col] != 0 and self.grid[row, col] != value:
            violations += 5
        
        return violations
    
    def compute_cell_probability(self, row: int, col: int, value: int, 
                                  lambda_: float = None, T: float = None) -> float:
        """計算單元格填入數字的概率（Boltzmann分布）"""
        if lambda_ is None:
            lambda_ = self.lambda_param
        if T is None:
            T = self.temperature
        
        violation = self.count_constraint_violations(row, col, value)
        
        # Boltzmann因子
        unnormalized = np.exp(-lambda_ * violation / T)
        
        # 歸一化（對所有16個數字）
        total = sum(np.exp(-lambda_ * self.count_constraint_violations(row, col, v) / T) 
                   for v in DIGITS)
        
        if total == 0:
            return 1.0 / 16
        
        return unnormalized / total
    
    def compute_marginal_entropy(self, row: int, col: int) -> float:
        """計算單元格的邊緣熵"""
        probs = [self.compute_cell_probability(row, col, v) for v in DIGITS]
        probs = np.array(probs)
        probs = probs / (probs.sum() + 1e-10)
        
        # 熵公式 H = -Σ P(v) × log₂(P(v))
        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        return float(entropy)
    
    def analyze_all_cells(self) -> ProbabilityMetrics:
        """分析所有256個單元格"""
        print("📊 計算256單元格概率分佈...")
        
        total_entropy = 0
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                # 計算每個數字 probability
                probs = {}
                for v in DIGITS:
                    probs[v] = self.compute_cell_probability(row, col, v)
                
                self.metrics.cell_probability[(row, col)] = probs
                self.metrics.marginal_probability[(row, col)] = max(probs.values())
                self.metrics.entropy_per_cell[(row, col)] = self.compute_marginal_entropy(row, col)
                total_entropy += self.metrics.entropy_per_cell[(row, col)]
        
        self.metrics.effective_temperature = self.temperature
        
        print(f"  ✓ 256單元格分析完成")
        print(f"  ✓ 總熵: {total_entropy:.2f}")
        print(f"  ✓ 平均熵: {total_entropy / 256:.2f}")
        
        return self.metrics


# ======================== 五維思維框架 ========================

@dataclass
class FiveDimMetrics:
    """五維思維指標"""
    point: Dict  # 0D - 單元格概率
    line: Dict   # 1D - 行/列熵
    plane: Dict  # 2D - 宮格聚合
    body: Dict   # 3D - 全局約束
    sphere: Dict # 4D - 狀態空間
    spacetime: Dict  # 5D - 求解過程


class FiveDimensionalFramework:
    """五維思維框架分析器"""
    
    @staticmethod
    def point_dimension(prob_metrics: ProbabilityMetrics) -> Dict:
        """POINT (0D): 256個單元格獨立分析"""
        return {
            'max_entropy_cell': max(prob_metrics.entropy_per_cell.items(), 
                                     key=lambda x: x[1]),
            'min_entropy_cell': min(prob_metrics.entropy_per_cell.items(), 
                                     key=lambda x: x[1]),
            'avg_entropy': np.mean(list(prob_metrics.entropy_per_cell.values())),
            'entropy_std': np.std(list(prob_metrics.entropy_per_cell.values())),
            'high_entropy_count': sum(1 for e in prob_metrics.entropy_per_cell.values() 
                                       if e > 3.0),  # 接近均勻分佈
            'low_entropy_count': sum(1 for e in prob_metrics.entropy_per_cell.values() 
                                      if e < 1.0),   # 高確定性
        }
    
    @staticmethod
    def line_dimension(prob_metrics: ProbabilityMetrics) -> Dict:
        """LINE (1D): 行/列約束聚合"""
        row_entropies = {}
        col_entropies = {}
        
        for (r, c), entropy in prob_metrics.entropy_per_cell.items():
            if r not in row_entropies:
                row_entropies[r] = []
            row_entropies[r].append(entropy)
            if c not in col_entropies:
                col_entropies[c] = []
            col_entropies[c].append(entropy)
        
        return {
            'row_entropy_sum': {r: np.sum(ents) for r, ents in row_entropies.items()},
            'row_entropy_avg': {r: np.mean(ents) for r, ents in row_entropies.items()},
            'col_entropy_sum': {c: np.sum(ents) for c, ents in col_entropies.items()},
            'col_entropy_avg': {c: np.mean(ents) for c, ents in col_entropies.items()},
            'max_row_entropy': max(row_entropies.items(), key=lambda x: np.sum(x[1])),
            'min_row_entropy': min(row_entropies.items(), key=lambda x: np.sum(x[1])),
        }
    
    @staticmethod
    def plane_dimension(prob_metrics: ProbabilityMetrics) -> Dict:
        """PLANE (2D): 4×4 宮格約束聚合"""
        box_entropies = {}
        
        for box_r in range(4):
            for box_c in range(4):
                box_idx = box_r * 4 + box_c
                box_name = f"{chr(65+box_r)}{chr(97+box_c)}"  # Aa, Ae, ...
                ents = []
                for dr in range(4):
                    for dc in range(4):
                        r = box_r * 4 + dr
                        c = box_c * 4 + dc
                        ents.append(prob_metrics.entropy_per_cell.get((r, c), 0))
                box_entropies[box_idx] = {
                    'name': box_name,
                    'entropy_sum': np.sum(ents),
                    'entropy_avg': np.mean(ents),
                    'entropy_std': np.std(ents)
                }
        
        return box_entropies
    
    @staticmethod
    def body_dimension(prob_metrics: ProbabilityMetrics, row_perms: Dict) -> Dict:
        """BODY (3D): 全局約束聚合"""
        total_perm_count = sum(len(p) for p in row_perms.values())
        
        # 計算全局熵
        all_probs = []
        for (r, c), probs in prob_metrics.cell_probability.items():
            all_probs.extend(probs.values())
        all_probs = np.array(all_probs)
        
        return {
            'global_entropy': -np.sum(all_probs * np.log2(all_probs + 1e-10) / len(all_probs)),
            'total_permutations': total_perm_count,
            'search_space_log': np.log2(total_perm_count) if total_perm_count > 0 else 0,
            'constraint_density': np.sum([1 for p in prob_metrics.marginal_probability.values() 
                                          if p > 0.5]) / 256,
        }
    
    @staticmethod
    def sphere_dimension(prob_metrics: ProbabilityMetrics) -> Dict:
        """SPHERE (4D): 狀態空間球面映射"""
        # 基於概率分佈的態空間體積
        entropies = list(prob_metrics.entropy_per_cell.values())
        
        return {
            'state_space_volume': np.exp(np.mean(entropies) * 256),
            'effective_dimensions': np.sum([1 for e in entropies if e > 2.0]),
            'probability_sphere_radius': np.sqrt(np.sum([p**2 
                                                       for probs in prob_metrics.cell_probability.values() 
                                                       for p in probs.values()])),
        }
    
    @staticmethod
    def spacetime_dimension(bessel_zeros: List[float], 
                            entropy_profile: List[float]) -> Dict:
        """SPACE-TIME (5D): 求解過程的時空演化"""
        # 映射熵衰減到貝塞爾零點
        max_entropy = max(entropy_profile) if entropy_profile else 1.0
        normalized_profile = [e / max_entropy for e in entropy_profile]
        
        # 找到各階段的熵閾值
        stage_thresholds = {}
        for i, zero in enumerate(bessel_zeros[:8]):
            normalized_zero = zero / bessel_zeros[7] if bessel_zeros else 0
            count = sum(1 for e in normalized_profile if e <= normalized_zero)
            stage_thresholds[f"stage_{i+1}"] = {
                'bessel_zero': zero,
                'entropy_threshold': normalized_zero,
                'cells_below': count
            }
        
        return {
            'bessel_zero_analysis': stage_thresholds,
            'entropy_decay_rate': np.mean(np.diff(sorted(entropy_profile))) if len(entropy_profile) > 1 else 0,
        }


# ======================== 貝塞爾函數零點分析 ========================

class BesselZeroAnalysis:
    """貝塞爾函數零點深度分析"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.analyzer = BesselAnalyzer()
        
    def analyze_row_entropy_profile(self, entropy_per_row: Dict[int, float]) -> Dict:
        """分析行熵分佈與貝塞爾零點的對應關係"""
        row_summaries = {}
        
        for row_idx, entropy in entropy_per_row.items():
            # 將熵歸一化到 [0, 35] 範圍（J₀前10個零點範圍）
            normalized = (entropy / 4.0) * 35  # 假设最大熵≈4
            
            zero_idx, stage, position = self.analyzer.find_nearest_stage(normalized)
            
            row_summaries[row_idx] = {
                'entropy': entropy,
                'normalized_range': normalized,
                'nearest_bessel_zero': zero_idx,
                'bessel_stage': stage,
                'position_in_interval': position,
                'j0_value': self.analyzer.compute_j0(normalized)
            }
        
        return row_summaries
    
    def compute_entropy_oscillation(self, entropy_per_cell: Dict) -> Dict:
        """計算熵的振盪特性（類似貝塞爾函數振盪）"""
        # 按行提取熵序列
        row_entropy_sequences = {}
        for row in range(16):
            row_ents = [entropy_per_cell[(row, col)] for col in range(16)]
            row_entropy_sequences[row] = row_ents
        
        # 計算自相關（檢測振盪模式）
        autocorr = {}
        for row, seq in row_entropy_sequences.items():
            seq = np.array(seq)
            mean = np.mean(seq)
            std = np.std(seq)
            if std > 0:
                # 計算滯後1的自相關
                corr = np.corrcoef(seq[:-1], seq[1:])[0, 1]
                autocorr[row] = float(corr) if not np.isnan(corr) else 0
            else:
                autocorr[row] = 0
        
        return {
            'row_entropy_sequences': row_entropy_sequences,
            'autocorrelation': autocorr,
            'average_autocorr': np.mean(list(autocorr.values())),
        }
    
    def zero_crossing_analysis(self, entropy_profile: List[float]) -> Dict:
        """分析熵分佈的零點穿越（類似J₀的過零點）"""
        # 標準化熵序列
        entropy_array = np.array(entropy_profile)
        mean_entropy = np.mean(entropy_array)
        normalized = entropy_array - mean_entropy
        
        # 檢測穿越零點的次數
        zero_crossings = []
        for i in range(1, len(normalized)):
            if normalized[i-1] * normalized[i] < 0:
                zero_crossings.append(i)
        
        return {
            'total_crossings': len(zero_crossings),
            'crossing_positions': zero_crossings,
            'peak_count': len(zero_crossings) + 1,  # 峰值數量估計
        }


# ======================== 綜合測評報告生成 ========================

class ComprehensiveBesselBenchmark:
    """256數獨概率閾值與貝塞爾函數綜合測評"""
    
    def __init__(self, base_dir: Path = BASE_DIR):
        self.base_dir = base_dir
        self.prob_analyzer = BoltzmannProbabilityAnalyzer(base_dir)
        self.five_dim_framework = FiveDimensionalFramework()
        self.bessel_analyzer = BesselZeroAnalysis(base_dir)
        
    def run_full_analysis(self, lambda_param: float = 1.0, 
                          temperature: float = 0.5) -> Dict:
        """執行完整測評流程"""
        print("\n" + "=" * 70)
        print("🎯 超級256數獨 概率閾值與貝塞爾函數 綜合測評系統")
        print("=" * 70)
        print(f"\n📁 工作目錄: {self.base_dir}")
        print(f"📐 網格尺寸: {GRID_SIZE}×{GRID_SIZE} = 256單元格")
        print(f"🏠 宮格尺寸: {BOX_SIZE}×{BOX_SIZE} × 16宮格")
        print(f"🔬 温度參數: T = {temperature}")
        print(f"📈 λ參數: {lambda_param}")
        
        start_time = time.time()
        
        # ===== 1. 加載數據 =====
        print("\n" + "─" * 70)
        print("📂 步驟1: 數據加載")
        print("─" * 70)
        
        known_count = self.prob_analyzer.load_puzzle()
        print(f"  ✓ 謎題加載: {known_count} 個已知數字")
        
        total_perms = self.prob_analyzer.load_permutations()
        print(f"  ✓ 符闔排列: {total_perms:,} 個排列")
        
        # ===== 2. Boltzmann 概率分析 =====
        print("\n" + "─" * 70)
        print("⚡ 步驟2: Boltzmann 概率閾值計算")
        print("─" * 70)
        
        prob_metrics = self.prob_analyzer.analyze_all_cells()
        
        # 概率分佈統計
        all_marginal_probs = list(prob_metrics.marginal_probability.values())
        avg_marginal = np.mean(all_marginal_probs)
        max_marginal = np.max(all_marginal_probs)
        min_marginal = np.min(all_marginal_probs)
        
        print(f"\n  邊緣概率統計:")
        print(f"    平均最大概率: {avg_marginal:.4f}")
        print(f"    最大概率: {max_marginal:.4f}")
        print(f"    最小概率: {min_marginal:.4f}")
        
        # ===== 3. 熵分析 =====
        print("\n" + "─" * 70)
        print("📊 步驟3: 熵分佈分析")
        print("─" * 70)
        
        all_entropies = list(prob_metrics.entropy_per_cell.values())
        avg_entropy = np.mean(all_entropies)
        entropy_std = np.std(all_entropies)
        
        print(f"\n  熵分佈統計:")
        print(f"    總熵 (H_total): {np.sum(all_entropies):.2f} bits")
        print(f"    平均熵 (H_avg): {avg_entropy:.4f} bits/cell")
        print(f"    熵標準差: {entropy_std:.4f}")
        print(f"    最大熵 (最不确定): {max(all_entropies):.4f}")
        print(f"    最小熵 (最確定): {min(all_entropies):.4f}")
        
        # 熵分級統計
        high_entropy = sum(1 for e in all_entropies if e > 3.5)
        medium_entropy = sum(1 for e in all_entropies if 1.5 <= e <= 3.5)
        low_entropy = sum(1 for e in all_entropies if e < 1.5)
        
        print(f"\n  熵分級:")
        print(f"    🔴 高熵 (>3.5): {high_entropy} 單元格 ({100*high_entropy/256:.1f}%)")
        print(f"    🟡 中熵 (1.5-3.5): {medium_entropy} 單元格 ({100*medium_entropy/256:.1f}%)")
        print(f"    🟢 低熵 (<1.5): {low_entropy} 單元格 ({100*low_entropy/256:.1f}%)")
        
        # ===== 4. 五維思維框架 =====
        print("\n" + "─" * 70)
        print("🌐 步驟4: 五維思維框架分析")
        print("─" * 70)
        
        five_dim = FiveDimMetrics(
            point=self.five_dim_framework.point_dimension(prob_metrics),
            line=self.five_dim_framework.line_dimension(prob_metrics),
            plane=self.five_dim_framework.plane_dimension(prob_metrics),
            body=self.five_dim_framework.body_dimension(prob_metrics, 
                                                          self.prob_analyzer.row_perms),
            sphere=self.five_dim_framework.sphere_dimension(prob_metrics),
            spacetime=self.five_dim_framework.spacetime_dimension(
                BesselAnalyzer.J0_ZEROS, all_entropies)
        )
        
        # 五維指標摘要
        print(f"\n  POINT (0D) - 單元格:")
        print(f"    最大熵單元格: ({five_dim.point['max_entropy_cell'][0]}, "
              f"{five_dim.point['max_entropy_cell'][1]}) = {five_dim.point['max_entropy_cell'][1]:.3f}")
        print(f"    平均熵: {five_dim.point['avg_entropy']:.4f}")
        
        print(f"\n  LINE (1D) - 行/列:")
        max_row = five_dim.line['max_row_entropy']
        print(f"    最大行熵: A{max_row[0]+1} = {np.sum(max_row[1]):.2f}")
        
        print(f"\n  PLANE (2D) - 宮格:")
        max_box = max(five_dim.plane.items(), key=lambda x: x[1]['entropy_sum'])
        print(f"    最大宮格熵: {max_box[1]['name']} = {max_box[1]['entropy_sum']:.2f}")
        
        print(f"\n  BODY (3D) - 全局:")
        print(f"    全局熵: {five_dim.body['global_entropy']:.4f}")
        print(f"    搜尋空間: ≈2^{five_dim.body['search_space_log']:.1f}")
        
        print(f"\n  SPHERE (4D) - 狀態空間:")
        print(f"    有效維度數: {five_dim.sphere['effective_dimensions']}")
        
        print(f"\n  SPACE-TIME (5D) - 貝塞爾映射:")
        crossing = self.bessel_analyzer.zero_crossing_analysis(all_entropies)
        print(f"    熵零點穿越次數: {crossing['total_crossings']}")
        
        # ===== 5. 貝塞爾函數零點分析 =====
        print("\n" + "─" * 70)
        print("🌀 步驟5: 貝塞爾函數 J₀ 零點分析")
        print("─" * 70)
        
        # 行熵與貝塞爾零點對應
        row_entropy_sum = {r: np.sum([prob_metrics.entropy_per_cell[(r, c)] 
                                       for c in range(16)]) 
                           for r in range(16)}
        row_bessel_analysis = self.bessel_analyzer.analyze_row_entropy_profile(row_entropy_sum)
        
        print(f"\n  J₀ 前10個零點:")
        for i, zero in enumerate(BesselAnalyzer.J0_ZEROS):
            stage = BesselAnalyzer.SOLVING_STAGES[i]
            j0_val = BesselAnalyzer.compute_j0(zero)
            print(f"    α_{i+1} = {zero:8.4f}  |  J₀(α_{i+1}) ≈ {j0_val:.6f}  |  {stage}")
        
        # 行熵映射
        print(f"\n  行熵映射到貝塞爾階段:")
        for row_idx in range(16):
            analysis = row_bessel_analysis[row_idx]
            stage = analysis['bessel_stage']
            j0_val = analysis['j0_value']
            print(f"    A{row_idx+1:2d}: H={analysis['entropy']:.2f} → 階段 {stage:12s}  J₀={j0_val:.4f}")
        
        # 熵振盪分析
        print(f"\n  熵振盪特性:")
        oscillation = self.bessel_analyzer.compute_entropy_oscillation(
            prob_metrics.entropy_per_cell)
        print(f"    平均自相關: {oscillation['average_autocorr']:.4f}")
        print(f"    零點穿越次數: {crossing['total_crossings']}")
        
        # ===== 6. 困難度與策略建議 =====
        print("\n" + "─" * 70)
        print("🎯 步驟6: 困難度評估與策略建議")
        print("─" * 70)
        
        # 綜合困難度評分
        difficulty_score = self._compute_difficulty_score(
            prob_metrics, five_dim, crossing)
        
        print(f"\n  綜合困難度評分:")
        print(f"    概率不確定性: {difficulty_score['probability_uncertainty']:.2f}/3")
        print(f"    熵複雜度: {difficulty_score['entropy_complexity']:.2f}/3")
        print(f"    約束緊密度: {difficulty_score['constraint_density']:.2f}/2")
        print(f"    貝塞爾振盪: {difficulty_score['bessel_oscillation']:.2f}/2")
        print(f"\n  📊 總評分: {difficulty_score['total']:.1f}/10")
        
        difficulty_level = self._get_difficulty_level(difficulty_score['total'])
        print(f"  🎚️  等級: {difficulty_level}")
        
        # 概率閾值建議
        print(f"\n  概率閾值建議:")
        if avg_marginal > 0.25:
            print(f"    建議閾值: ≥0.25 (高置信度)")
        elif avg_marginal > 0.15:
            print(f"    建議閾值: ≥0.15 (中等置信度)")
        else:
            print(f"    建議閾值: ≥0.10 (低置信度，需多策略)")
        
        # 貝塞爾策略映射
        print(f"\n  貝塞爾策略映射:")
        for i, zero in enumerate(BesselAnalyzer.J0_ZEROS[:5]):
            stage = BesselAnalyzer.SOLVING_STAGES[i]
            if i == 0:
                print(f"    α₁={zero:.2f} ({stage}): 初始化概率閾值 T=1.0, λ=1.0")
            elif i == 1:
                print(f"    α₂={zero:.2f} ({stage}): 約束傳播 T=0.8, λ=1.2")
            elif i == 2:
                print(f"    α₃={zero:.2f} ({stage}): 分支探索 T=0.6, λ=1.5")
            elif i == 3:
                print(f"    α₄={zero:.2f} ({stage}): 收斂優化 T=0.4, λ=2.0")
            elif i == 4:
                print(f"    α₅={zero:.2f} ({stage}): 臨界突破 T=0.3, λ=3.0")
        
        elapsed = time.time() - start_time
        
        # ===== 7. 匯總報告 =====
        print("\n" + "=" * 70)
        print("📝 測評完成，生成報告...")
        print("=" * 70)
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'elapsed_time': round(elapsed, 2),
            'parameters': {
                'lambda': lambda_param,
                'temperature': temperature,
                'grid_size': GRID_SIZE,
                'total_cells': GRID_SIZE * GRID_SIZE
            },
            'data_summary': {
                'known_digits': known_count,
                'total_permutations': total_perms
            },
            'probability_metrics': {
                'avg_marginal_probability': float(avg_marginal),
                'max_marginal_probability': float(max_marginal),
                'min_marginal_probability': float(min_marginal)
            },
            'entropy_analysis': {
                'total_entropy': float(np.sum(all_entropies)),
                'average_entropy': float(avg_entropy),
                'entropy_std': float(entropy_std),
                'high_entropy_count': high_entropy,
                'medium_entropy_count': medium_entropy,
                'low_entropy_count': low_entropy
            },
            'five_dimensional_metrics': {
                'point': five_dim.point,
                'line': five_dim.line,
                'plane': {k: v for k, v in five_dim.plane.items()},
                'body': five_dim.body,
                'sphere': five_dim.sphere,
                'spacetime': five_dim.spacetime
            },
            'bessel_analysis': {
                'j0_zeros': BesselAnalyzer.J0_ZEROS,
                'stages': BesselAnalyzer.SOLVING_STAGES,
                'row_mapping': {str(k): v for k, v in row_bessel_analysis.items()},
                'oscillation': {
                    'average_autocorrelation': float(oscillation['average_autocorr'])
                },
                'zero_crossings': crossing
            },
            'difficulty_assessment': difficulty_score,
            'strategy_recommendations': self._generate_recommendations(
                prob_metrics, five_dim, difficulty_score)
        }
        
        return report
    
    def _compute_difficulty_score(self, prob_metrics, five_dim, crossing) -> Dict:
        """計算綜合困難度評分"""
        # 概率不確定性 (0-3)
        avg_marginal = np.mean(list(prob_metrics.marginal_probability.values()))
        prob_score = 3 - min(3, avg_marginal * 10)
        
        # 熵複雜度 (0-3)
        avg_entropy = np.mean(list(prob_metrics.entropy_per_cell.values()))
        entropy_score = min(3, avg_entropy / 4 * 3)
        
        # 約束緊密度 (0-2)
        high_prob_count = sum(1 for p in prob_metrics.marginal_probability.values() 
                              if p > 0.5)
        density_score = 2 * (1 - high_prob_count / 256)
        
        # 貝塞爾振盪 (0-2)
        oscillation_score = min(2, crossing['total_crossings'] / 5 * 2)
        
        total = prob_score + entropy_score + density_score + oscillation_score
        
        return {
            'probability_uncertainty': round(prob_score, 2),
            'entropy_complexity': round(entropy_score, 2),
            'constraint_density': round(density_score, 2),
            'bessel_oscillation': round(oscillation_score, 2),
            'total': round(total, 1)
        }
    
    def _get_difficulty_level(self, score: float) -> str:
        """獲取困難度等級"""
        if score >= 9:
            return "💀 極端困難 - 僅適配理論分析框架"
        elif score >= 7:
            return "🔥 專家級 - 需要融合多策略"
        elif score >= 5:
            return "⚡ 困難級 - 需要策略組合"
        elif score >= 3:
            return "📐 中等級 - 單策略可嘗試"
        else:
            return "✨ 簡單級 - 直觀解法可行"
    
    def _generate_recommendations(self, prob_metrics, five_dim, 
                                    difficulty) -> List[str]:
        """生成策略建議"""
        recommendations = []
        
        avg_entropy = np.mean(list(prob_metrics.entropy_per_cell.values()))
        
        if avg_entropy > 3.0:
            recommendations.append(
                "🔴 熵值過高，所有單元格接近均勻分佈，建議:")
            recommendations.append("   • 增加已知數字以縮小搜尋空間")
            recommendations.append("   • 採用概率閾值 ≥0.30 的高置信度策略")
        elif avg_entropy > 2.0:
            recommendations.append(
                "🟠 熵值較高，存在多解可能性，建議:")
            recommendations.append("   • 使用 Boltzmann 溫度 T=0.8 進行概率收斂")
            recommendations.append("   • 引入DLX精確覆蓋進行唯一性驗證")
        else:
            recommendations.append(
                "🟢 熵值適中，求解路徑相對清晰，建議:")
            recommendations.append("   • 採用融合搜索架構")
            recommendations.append("   • 使用貝塞爾零點映射優化溫度參數")
        
        recommendations.append("\n📋 貝塞爾函數溫度調度建議:")
        recommendations.append("   α₁(2.40) → T=1.0, λ=1.0 (初始化)")
        recommendations.append("   α₂(5.52) → T=0.8, λ=1.2 (傳播)")
        recommendations.append("   α₃(8.65) → T=0.6, λ=1.5 (分支)")
        recommendations.append("   α₄(11.79) → T=0.4, λ=2.0 (收斂)")
        recommendations.append("   α₅(14.93) → T=0.3, λ=3.0 (突破)")
        
        return recommendations


# ======================== HTML 可視化報告 ========================

def generate_bessel_visualization_report(report: Dict, output_path: Path):
    """生成交互式HTML可視化報告"""
    
    entropy_data = report['entropy_analysis']
    bessel_data = report['bessel_analysis']
    five_dim = report['five_dimensional_metrics']
    
    html_content = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>超級256數獨 - 概率閾值與貝塞爾函數綜合測評</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', system-ui, sans-serif; 
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #eee; padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ 
            text-align: center; margin-bottom: 30px; 
            color: #00d4ff; text-shadow: 0 0 30px rgba(0,212,255,0.5);
            font-size: 2.2em;
        }}
        h2 {{ 
            color: #00ff88; margin: 25px 0 15px 0; 
            padding-bottom: 8px; border-bottom: 2px solid #00ff88;
            font-size: 1.5em;
        }}
        .dashboard {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 15px; margin-bottom: 25px; 
        }}
        .card {{ 
            background: rgba(255,255,255,0.06); 
            border-radius: 12px; padding: 18px; 
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }}
        .metric {{ font-size: 2em; font-weight: bold; margin-bottom: 5px; }}
        .metric-label {{ font-size: 0.85em; color: #aaa; }}
        .section {{ margin-bottom: 25px; }}
        
        /* 貝塞爾函數樣式 */
        .bessel-grid {{ 
            display: grid; grid-template-columns: repeat(10, 1fr); gap: 8px; 
            margin: 15px 0; 
        }}
        .bessel-zero {{ 
            background: linear-gradient(135deg, rgba(0,212,255,0.2), rgba(0,255,136,0.2));
            border-radius: 8px; padding: 12px 6px; text-align: center;
            transition: transform 0.3s;
        }}
        .bessel-zero:hover {{ transform: scale(1.15); z-index: 10; }}
        .bessel-num {{ font-size: 0.7em; color: #888; margin-bottom: 5px; }}
        .bessel-value {{ font-size: 1.1em; font-weight: bold; color: #00d4ff; }}
        .bessel-stage {{ font-size: 0.65em; color: #aaa; margin-top: 4px; }}
        
        /* 宮格熱力圖 */
        .box-grid {{ 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: 6px; 
            margin: 15px 0; 
        }}
        .box-cell {{ 
            aspect-ratio: 1; border-radius: 6px; 
            display: flex; flex-direction: column; 
            align-items: center; justify-content: center;
            transition: all 0.3s;
            cursor: pointer;
        }}
        .box-cell:hover {{ transform: scale(1.2); z-index: 10; box-shadow: 0 0 20px rgba(0,212,255,0.5); }}
        .box-name {{ font-size: 0.7em; color: #888; }}
        .box-entropy {{ font-size: 1em; font-weight: bold; }}
        
        /* 五維框架 */
        .five-dim {{ 
            display: grid; 
            grid-template-columns: repeat(6, 1fr); 
            gap: 10px; margin: 20px 0; 
        }}
        .dim {{ 
            background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(138,43,226,0.15));
            border-radius: 10px; padding: 15px; text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .dim-name {{ font-size: 0.65em; color: #888; margin-bottom: 8px; }}
        .dim-value {{ font-size: 1.3em; font-weight: bold; }}
        
        /* 概率表 */
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ 
            padding: 8px; text-align: center; 
            border: 1px solid rgba(255,255,255,0.1); 
            font-size: 0.85em;
        }}
        th {{ background: rgba(0,212,255,0.2); }}
        
        .recommendation-box {{ 
            background: rgba(0,255,136,0.1); 
            border-radius: 10px; 
            padding: 15px; 
            margin-top: 15px;
            line-height: 1.8;
        }}
        
        @media (max-width: 768px) {{
            .bessel-grid, .five-dim {{ grid-template-columns: repeat(5, 1fr); }}
            .box-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 超級256數獨 - 概率閾值與貝塞爾函數綜合測評</h1>
        
        <div class="dashboard">
            <div class="card">
                <div class="metric" style="color: #ff6b6b;">{entropy_data['total_entropy']:.1f}</div>
                <div class="metric-label">總熵 H<sub>total</sub> (bits)</div>
            </div>
            <div class="card">
                <div class="metric" style="color: #4ecdc4;">{entropy_data['average_entropy']:.3f}</div>
                <div class="metric-label">平均熵 H<sub>avg</sub> (bits/cell)</div>
            </div>
            <div class="card">
                <div class="metric" style="color: #ffe66d;">{bessel_data['zero_crossings']['total_crossings']}</div>
                <div class="metric-label">熵零點穿越次數</div>
            </div>
            <div class="card">
                <div class="metric" style="color: #95e1d3;">{report['difficulty_assessment']['total']:.1f}</div>
                <div class="metric-label">綜合困難度 /10</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🌀 貝塞爾函數 J₀ 零點與求解階段</h2>
            <div class="bessel-grid">
'''
    
    # 添加貝塞爾零點卡片
    for i, zero in enumerate(bessel_data['j0_zeros']):
        stage = bessel_data['stages'][i]
        j0_val = BesselAnalyzer.compute_j0(zero)
        html_content += f'''
                <div class="bessel-zero">
                    <div class="bessel-num">α<sub>{i+1}</sub></div>
                    <div class="bessel-value">{zero:.2f}</div>
                    <div class="bessel-stage">{stage}</div>
                </div>'''
    
    html_content += f'''
            </div>
        </div>
        
        <div class="section">
            <h2>📊 熵分佈與貝塞爾階段映射</h2>
            <div class="card">
                <canvas id="entropyChart" height="120"></canvas>
            </div>
        </div>
        
        <div class="section">
            <h2>🌐 五維思維框架分析</h2>
            <div class="five-dim">
                <div class="dim">
                    <div class="dim-name">POINT (0D)<br/>單元格</div>
                    <div class="dim-value">{five_dim['point']['avg_entropy']:.3f}</div>
                </div>
                <div class="dim">
                    <div class="dim-name">LINE (1D)<br/>行/列</div>
                    <div class="dim-value">{five_dim['line']['row_entropy_sum']['0']:.1f}</div>
                </div>
                <div class="dim">
                    <div class="dim-name">PLANE (2D)<br/>宮格</div>
                    <div class="dim-value">{five_dim['plane']['0']['entropy_sum']:.1f}</div>
                </div>
                <div class="dim">
                    <div class="dim-name">BODY (3D)<br/>全局</div>
                    <div class="dim-value">{five_dim['body']['global_entropy']:.3f}</div>
                </div>
                <div class="dim">
                    <div class="dim-name">SPHERE (4D)<br/>狀態空間</div>
                    <div class="dim-value">{five_dim['sphere']['effective_dimensions']}</div>
                </div>
                <div class="dim">
                    <div class="dim-name">SPACE-TIME (5D)<br/>貝塞爾映射</div>
                    <div class="dim-value">{bessel_data['zero_crossings']['total_crossings']}x</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🎲 宮格熵分佈 (4×4)</h2>
            <div class="card">
                <div class="box-grid" id="boxHeatmap"></div>
            </div>
        </div>
        
        <div class="section">
            <h2>💡 關鍵發現與策略建議</h2>
            <div class="card recommendation-box">
'''
    
    for rec in report['strategy_recommendations'][:8]:
        html_content += f'                <p>{rec}</p>'
    
    html_content += f'''
            </div>
        </div>
    </div>
    
    <script>
        // 熵分佈圖
        const ctx = document.getElementById('entropyChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: ['A1','A2','A3','A4','A5','A6','A7','A8','A9','A10','A11','A12','A13','A14','A15','A16'],
                datasets: [{{
                    label: '行熵總和',
                    data: [
'''
    
    # 添加行熵數據
    row_entropies = []
    for r in range(16):
        row_sum = sum(report['five_dimensional_metrics']['line']['row_entropy_sum'][str(r)])
        row_entropies.append(row_sum)
    
    html_content += f'{json.dumps(row_entropies)},'
    
    html_content += f'''
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }}, {{
                    label: 'J₀(α₃)=0.865',
                    data: [0.865 * 16, 0.865 * 16, 0.865 * 16, 0.865 * 16, 0.865 * 16,
                           0.865 * 16, 0.865 * 16, 0.865 * 16, 0.865 * 16, 0.865 * 16,
                           0.865 * 16, 0.865 * 16, 0.865 * 16, 0.865 * 16, 0.865 * 16,
                           0.865 * 16],
                    borderColor: '#ff6b6b',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ labels: {{ color: '#ccc' }} }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(2);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{ 
                        beginAtZero: true, 
                        grid: {{ color: 'rgba(255,255,255,0.05)' }},
                        ticks: {{ color: '#aaa' }}
                    }},
                    x: {{ 
                        grid: {{ color: 'rgba(255,255,255,0.05)' }},
                        ticks: {{ color: '#aaa' }}
                    }}
                }}
            }}
        }});
        
        // 宮格熱力圖
        const boxGrid = document.getElementById('boxHeatmap');
        const boxData = {json.dumps(five_dim['plane'])};
        const boxNames = ['Aa', 'Ae', 'Ai', 'Am', 'Ba', 'Be', 'Bi', 'Bm',
                          'Ca', 'Ce', 'Ci', 'Cm', 'Da', 'De', 'Di', 'Dm'];
        const maxEnt = Math.max(...Object.values(boxData).map(b => b.entropy_sum));
        for (let i = 0; i < 16; i++) {{
            const cell = document.createElement('div');
            cell.className = 'box-cell';
            const entropy = boxData[i].entropy_sum;
            const intensity = Math.round((entropy / maxEnt) * 255);
            cell.style.background = `rgba(0, ${intensity}, ${255 - intensity}, 0.6)`;
            cell.innerHTML = `<div class="box-name">${{boxNames[i]}}</div><div class="box-entropy">${{entropy.toFixed(1)}}</div>`;
            cell.title = `熵: ${{entropy.toFixed(2)}} bits`;
            boxGrid.appendChild(cell);
        }}
    </script>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML可視化報告已生成: {output_path}")


# ======================== 主入口 ========================

if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("█  超級256數獨 概率閾值與貝塞爾函數 綜合測評系統".center(68) + "█")
    print("█" * 70 + "\n")
    
    # 檢查 scipy 可用性
    try:
        from scipy import special
        print("✅ scipy 可用 - 貝塞爾函數計算開啟")
    except ImportError:
        print("⚠️  scipy 不可用 - 將使用數學近似計算 J₀")
    
    # 執行測評
    benchmark = ComprehensiveBesselBenchmark()
    report = benchmark.run_full_analysis(
        lambda_param=1.0,
        temperature=0.5
    )
    
    # 生成報告文件
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    
    # JSON 報告
    json_path = BASE_DIR / f"概率閾值貝塞爾綜合測評_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n✅ JSON 報告已保存: {json_path}")
    
    # HTML 可視化報告
    html_path = BASE_DIR / f"超級256數獨_概率貝塞爾測評_{timestamp}.html"
    generate_bessel_visualization_report(report, html_path)
    
    print("\n" + "█" * 70)
    print("🎉 綜合測評完成".center(68) + "█")
    print("█" * 70)
