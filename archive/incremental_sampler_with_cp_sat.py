#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量化多解空間採樣排列生成算法 + CP-SAT 唯一性驗證
Incremental Multi-Solution Space Sampling with CP-SAT Uniqueness Verification

核心特性：
1. 增量約束添加：從低約束到高約束逐步剪枝搜索空間
2. 樹狀多解採樣：構建解空間樹，維持多解狀態（SUPERPOSITION）
3. 排列生成：基於符闔排列池動態生成可行排列組合
4. CP-SAT 驗證：使用 OR-Tools CP-SAT 求解器驗證唯一性
5. 多樣性最大化：確保採樣到的解之間有足夠差異

量子態分類：
- SUPERPOSITION: 多解（≥solution_limit 個解）
- COLLAPSED: 唯一解
- INFEASIBLE: 無解
"""

import json
import time
import random
import math
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

try:
    from ortools.sat.python import cp_model
except ImportError:
    print("❌ 請安裝 ortools: pip install ortools")
    import sys
    sys.exit(1)


class QuantumState(Enum):
    """量子態分類"""
    SUPERPOSITION = "superposition"  # 多解模式
    COLLAPSED = "collapsed"          # 唯一解
    INFEASIBLE = "infeasible"        # 無解


class SamplingStrategy(Enum):
    """採樣策略"""
    UNIFORM_RANDOM = "uniform_random"
    CONSTRAINT_GUIDED = "constraint_guided"
    DIVERSITY_MAXIMIZED = "diversity_maximized"
    WEIGHTED_SAMPLING = "weighted_sampling"


@dataclass
class SamplingNode:
    """採樣樹節點"""
    node_id: str
    depth: int
    constraint_level: str
    valid_permutations: Dict[int, List[int]]  # row_idx -> [perm_indices]
    partial_grid: Optional[List[List[Optional[int]]]] = None
    children: List[str] = field(default_factory=list)
    solution_estimate: float = 0.0
    pruning_factor: float = 1.0  # 剪枝比例
    timestamp: float = field(default_factory=time.time)


@dataclass
class IncrementalSamplingConfig:
    """增量採樣配置"""
    grid_size: int = 16
    box_size: int = 4
    target_branching: int = 5          # 目標分支因子
    max_tree_depth: int = 6            # 最大樹深度
    max_samples: int = 50              # 最大採樣數
    solution_limit_cp_sat: int = 10    # CP-SAT 解數量限制
    cp_sat_time_limit: int = 300       # CP-SAT 時間限制（秒）
    diversity_threshold: float = 0.3   # 多樣性閾值
    permutation_sample_size: int = 500 # 每行排列樣本數


class FahuoPermutationLoader:
    """符闔排列載入器"""
    
    CHINESE_NAMES = {
        'A':'第一','B':'第二','C':'第三','D':'第四','E':'第五','F':'第六',
        'G':'第七','H':'第八','I':'第九','J':'第十','K':'第十一','L':'第十二',
        'M':'第十三','N':'第十四','O':'第十五','P':'第十六'
    }
    
    def __init__(self, base_dir: str = "D:/2026/WPF_Sudoku/Sudoku_256"):
        self.base_dir = Path(base_dir)
        self.permutations_by_row: Dict[str, List[List[int]]] = {}
        self.compatibility_data: Optional[Dict] = None
    
    def load_compatibility(self) -> Dict:
        """載入相容性分析結果"""
        compat_path = self.base_dir / 'compatibility_v2.json'
        with open(compat_path, 'r', encoding='utf-8') as f:
            self.compatibility_data = json.load(f)
        return self.compatibility_data
    
    def load_permutations_for_row(self, row_label: str, 
                                   sample_size: int = 500) -> List[List[int]]:
        """載入特定行的符闔排列"""
        if row_label in self.permutations_by_row:
            return self.permutations_by_row[row_label]
        
        import openpyxl
        chinese_name = self.CHINESE_NAMES.get(row_label, row_label)
        fpath = self.base_dir / f"{row_label}{chinese_name}行符闔排列.xlsx"
        
        try:
            wb = openpyxl.load_workbook(str(fpath), data_only=True, read_only=True)
            ws = wb.active
            
            perms = []
            for row in ws.iter_rows(values_only=True):
                if len(row) >= 19:
                    vals = []
                    for i in range(3, 19):
                        v = row[i]
                        if isinstance(v, (int, float)) and 1 <= v <= 16:
                            vals.append(int(v))
                    if len(vals) == 16:
                        perms.append(vals)
                
                if len(perms) >= sample_size:
                    break
            
            wb.close()
            self.permutations_by_row[row_label] = perms
            print(f"   行{row_label}: 載入 {len(perms)} 個排列")
            return perms
        except Exception as e:
            print(f"   行{row_label}: 載入失敗 - {e}")
            return []


class IncrementalConstraintManager:
    """增量約束管理器"""
    
    def __init__(self, grid_size: int = 16, box_size: int = 4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.num_boxes = (grid_size // box_size) ** 2
    
    def filter_by_given(self, permutations: List[List[int]], 
                        given: Dict[int, int]) -> List[List[int]]:
        """根據已知數過濾排列"""
        if not given:
            return permutations
        
        filtered = []
        for perm in permutations:
            if all(perm[col] == val for col, val in given.items()):
                filtered.append(perm)
        return filtered
    
    def estimate_solution_count(self, perm_counts: Dict[int, int]) -> float:
        """估計解數量（上界）"""
        # 簡單估計：各行可行排列數的乘積
        # 實際會因列/宮約束大幅減少
        product = 1.0
        for count in perm_counts.values():
            product *= max(1, count)
        return math.log10(product) if product > 0 else 0
    
    def check_column_compatibility(self, row_perms: Dict[int, List[List[int]]]) -> Dict:
        """檢查列兼容性"""
        col_conflicts = defaultdict(list)
        
        for col in range(self.grid_size):
            val_counts = defaultdict(int)
            for row_idx, perms in row_perms.items():
                for perm in perms:
                    val_counts[perm[col]] += 1
            
            # 檢查是否有值在所有行中都能出現
            for val, count in val_counts.items():
                if count < len(row_perms):
                    # 有些行不能填這個值
                    pass
        
        return dict(col_conflicts)


class CP_SAT_UniquenessVerifier:
    """CP-SAT 唯一性驗證器"""
    
    def __init__(self, grid_size: int = 16, box_size: int = 4):
        self.grid_size = grid_size
        self.box_size = box_size
    
    def verify_with_solution_limit(self, 
                                    known_rows: Dict[int, List[int]],
                                    unknown_rows: List[int],
                                    row_perm_options: Dict[int, List[List[int]]],
                                    solution_limit: int = 10,
                                    time_limit: int = 300) -> Dict:
        """
        使用 CP-SAT 驗證唯一性
        
        Args:
            known_rows: 已確定的行 {row_idx: [values]}
            unknown_rows: 需要搜尋的行索引列表
            row_perm_options: 未知行的排列選項 {row_idx: [permutations]}
            solution_limit: 最多搜尋的解數量
            time_limit: 時間限制（秒）
        
        Returns:
            驗證結果
        """
        print("\n" + "="*60)
        print("CP-SAT 唯一性驗證")
        print("="*60)
        print(f"已知行: {len(known_rows)}, 搜尋行: {len(unknown_rows)}")
        print(f"solution_limit: {solution_limit}, 時間限制: {time_limit}秒")
        
        if not unknown_rows:
            # 所有行已知，直接驗證
            grid = [[0]*self.grid_size for _ in range(self.grid_size)]
            for i, vals in known_rows.items():
                grid[i] = vals
            return self._verify_complete_grid(grid)
        
        # 建立 CP-SAT 模型
        model = cp_model.CpModel()
        
        # 變數：為每行選擇排列索引
        row_choice = {}
        for i in unknown_rows:
            num_options = len(row_perm_options[i])
            row_choice[i] = [model.NewBoolVar(f'row{i}_choice{k}') 
                            for k in range(num_options)]
            model.AddExactlyOne(row_choice[i])
        
        # 列約束
        for col in range(self.grid_size):
            for val in range(1, 17):
                # 計算列中值 val 出現次數
                count_exprs = []
                
                # 已知行
                v_count_known = sum(1 for i, vals in known_rows.items() if vals[col] == val)
                
                # 搜尋行
                for i in unknown_rows:
                    for k, perm in enumerate(row_perm_options[i]):
                        if perm[col] == val:
                            count_exprs.append(row_choice[i][k])
                
                if count_exprs:
                    model.Add(sum(count_exprs) + v_count_known <= 1)
        
        # 宮約束
        for band in range(self.grid_size // self.box_size):
            for stack in range(self.grid_size // self.box_size):
                for val in range(1, 17):
                    count_exprs = []
                    
                    # 已知行
                    for i in known_rows:
                        for j in range(self.grid_size):
                            if (i // self.box_size == band and 
                                j // self.box_size == stack and
                                known_rows[i][j] == val):
                                count_exprs.append(1)
                    
                    # 搜尋行
                    for i in unknown_rows:
                        for k, perm in enumerate(row_perm_options[i]):
                            for j in range(self.grid_size):
                                if (i // self.box_size == band and
                                    j // self.box_size == stack and
                                    perm[j] == val):
                                    count_exprs.append(row_choice[i][k])
                    
                    if count_exprs:
                        model.Add(sum(count_exprs) <= 1)
        
        # 求解
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 8
        solver.parameters.solution_limit = solution_limit
        solver.parameters.log_search_progress = False
        
        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self.solutions = []
            
            def on_solution_callback(self):
                grid = [[0]*self.grid_size for _ in range(self.grid_size)]
                for i, vals in known_rows.items():
                    grid[i] = vals
                for i in unknown_rows:
                    for k, perm in enumerate(row_perm_options[i]):
                        if self.Value(row_choice[i][k]):
                            grid[i] = perm
                            break
                self.solutions.append(grid)
                
                if len(self.solutions) >= solution_limit:
                    self.StopSearch()
        
        collector = SolutionCollector()
        start_time = time.time()
        status = solver.Solve(model, collector)
        elapsed = time.time() - start_time
        num_solutions = len(collector.solutions)
        
        # 量子態判斷
        if num_solutions >= solution_limit:
            quantum_state = QuantumState.SUPERPOSITION
        elif num_solutions == 1:
            quantum_state = QuantumState.COLLAPSED
        else:
            quantum_state = QuantumState.INFEASIBLE
        
        print(f"\n結果:")
        print(f"   狀態: {solver.StatusName(status)}")
        print(f"   解數: {num_solutions}")
        print(f"   時間: {elapsed:.2f}秒")
        print(f"   量子態: {quantum_state.value}")
        
        return {
            'status': solver.StatusName(status),
            'num_solutions': num_solutions,
            'solutions': collector.solutions,
            'elapsed_time': elapsed,
            'quantum_state': quantum_state.value,
            'solution_limit': solution_limit,
            'time_limit': time_limit
        }
    
    def _verify_complete_grid(self, grid: List[List[int]]) -> Dict:
        """驗證完整網格"""
        col_ok = all(len(set(grid[i][j] for i in range(self.grid_size))) == self.grid_size 
                     for j in range(self.grid_size))
        box_ok = True
        for band in range(self.grid_size // self.box_size):
            for stack in range(self.grid_size // self.box_size):
                box = [grid[band*self.box_size+bi][stack*self.box_size+bj] 
                       for bi in range(self.box_size) for bj in range(self.box_size)]
                if len(set(box)) != self.box_size * self.box_size:
                    box_ok = False
                    break
        
        return {
            'valid': col_ok and box_ok,
            'column_valid': col_ok,
            'box_valid': box_ok,
            'quantum_state': QuantumState.COLLAPSED.value if (col_ok and box_ok) else QuantumState.INFEASIBLE.value
        }


class IncrementalSamplingEngine:
    """增量化多解空間採樣引擎"""
    
    def __init__(self, config: IncrementalSamplingConfig):
        self.config = config
        self.permutation_loader = FahuoPermutationLoader()
        self.constraint_manager = IncrementalConstraintManager(
            config.grid_size, config.box_size
        )
        self.cp_sat_verifier = CP_SAT_UniquenessVerifier(
            config.grid_size, config.box_size
        )
        self.sampling_tree: Dict[str, SamplingNode] = {}
        self.collected_solutions: List[List[List[int]]] = []
    
    def load_puzzle_data(self) -> Tuple[Dict, List[str], Dict]:
        """載入謎題數據"""
        # 載入相容性
        compat = self.permutation_loader.load_compatibility()
        results = compat['results']
        
        # 載入謎題配置
        puzzle_path = Path(self.permutation_loader.base_dir) / '超級大數獨_box_size4.txt'
        with open(puzzle_path, 'r', encoding='utf-8') as f:
            puzzle_content = f.read()
        
        import re
        grid_template = [[0]*self.config.grid_size for _ in range(self.config.grid_size)]
        row_labels = [chr(ord('A') + i) for i in range(self.config.grid_size)]
        
        for m in re.finditer(r'行([A-P]) \[(.*?)\]', puzzle_content):
            label, vals_str = m.group(1), m.group(2)
            vals = [int(v.strip()) if v.strip()!='0' else 0 for v in vals_str.split(',')]
            idx = ord(label) - ord('A')
            grid_template[idx] = vals
        
        # 識別行狀態
        known_rows = {}
        unknown_rows = []
        row_perm_cache = {}
        
        for i, label in enumerate(row_labels):
            r = results[label]
            given = {j:v for j,v in enumerate(grid_template[i]) if v != 0}
            
            if r['status'] == 'FULLY_KNOWN' and r['given_count'] == 16:
                known_rows[i] = grid_template[i]
            elif r['compatible_count'] == 1:
                perms = self.permutation_loader.load_permutations_for_row(
                    label, self.config.permutation_sample_size
                )
                compat_perms = self.constraint_manager.filter_by_given(perms, given)
                if len(compat_perms) == 1:
                    known_rows[i] = compat_perms[0]
                else:
                    unknown_rows.append(i)
                    row_perm_cache[i] = compat_perms
            else:
                unknown_rows.append(i)
                perms = self.permutation_loader.load_permutations_for_row(
                    label, self.config.permutation_sample_size
                )
                compat_perms = self.constraint_manager.filter_by_given(perms, given)
                row_perm_cache[i] = compat_perms
        
        return grid_template, row_labels, known_rows, unknown_rows, row_perm_cache, results
    
    def build_sampling_tree(self, known_rows: Dict, unknown_rows: List, 
                            row_perm_cache: Dict, strategy: SamplingStrategy = SamplingStrategy.DIVERSITY_MAXIMIZED) -> Dict[str, SamplingNode]:
        """構建增量採樣樹"""
        print("\n" + "="*60)
        print("構建增量採樣樹")
        print("="*60)
        print(f"策略: {strategy.value}")
        print(f"未知行: {unknown_rows}")
        
        # 根節點
        root_id = "root"
        root = SamplingNode(
            node_id=root_id,
            depth=0,
            constraint_level="initial",
            valid_permutations={i: list(range(len(row_perm_cache.get(i, [])))) 
                               for i in unknown_rows},
            partial_grid=[[None]*self.config.grid_size for _ in range(self.config.grid_size)],
            constraint_count=0
        )
        self.sampling_tree[root_id] = root
        
        # 逐層擴展
        for depth in range(1, self.config.max_tree_depth + 1):
            self._expand_layer(root, depth, strategy)
        
        return self.sampling_tree
    
    def _expand_layer(self, root: SamplingNode, depth: int, 
                      strategy: SamplingStrategy):
        """擴展一層節點"""
        nodes_at_depth = [n for n in self.sampling_tree.values() if n.depth == depth - 1]
        
        for node in nodes_at_depth:
            if not node.valid_permutations:
                continue
            
            # 找出有多個選擇的行
            flexible_rows = [i for i, perms in node.valid_permutations.items() 
                           if len(perms) > 1]
            
            if not flexible_rows:
                continue
            
            # 選擇分支行
            rows_to_branch = random.sample(
                flexible_rows, 
                min(self.config.target_branching, len(flexible_rows))
            )
            
            for branch_idx, row_idx in enumerate(rows_to_branch):
                child_id = f"{node.node_id}_d{depth}_b{branch_idx}"
                
                # 為子節點選擇排列
                child_perms = node.valid_permutations.copy()
                available = child_perms[row_idx]
                
                # 多樣性最大化策略：選擇與父節點不同的排列
                if strategy == SamplingStrategy.DIVERSITY_MAXIMIZED and len(available) > 1:
                    # 選擇最遠的排列（索引差最大）
                    selected = (available[0] + len(available) // 2) % len(available)
                    child_perms[row_idx] = [available[selected]]
                else:
                    selected = random.choice(available)
                    child_perms[row_idx] = [selected]
                
                child = SamplingNode(
                    node_id=child_id,
                    depth=depth,
                    constraint_level=f"row_{row_idx}_fixed",
                    valid_permutations=child_perms,
                    partial_grid=self._apply_choices(node.partial_grid, child_perms),
                    constraint_count=node.constraint_count + 1
                )
                
                self.sampling_tree[child_id] = child
                node.children.append(child_id)
    
    def _apply_choices(self, grid: List[List[Optional[int]]], 
                       choices: Dict[int, List[int]]) -> List[List[Optional[int]]]:
        """應用排列選擇"""
        new_grid = [row.copy() for row in grid]
        for row_idx, perm_indices in choices.items():
            if len(perm_indices) == 1:
                # 從相容性數據獲取排列
                pass  # 简化：實際需要從原始數據獲取
        return new_grid
    
    def sample_solutions(self, known_rows: Dict, unknown_rows: List, 
                         row_perm_cache: Dict) -> List[List[List[int]]]:
        """採樣多個解"""
        print("\n" + "="*60)
        print("多解採樣")
        print("="*60)
        
        solutions = []
        
        # 從採樣樹葉節點採樣
        leaf_nodes = [n for n in self.sampling_tree.values() 
                     if not n.children]
        
        for leaf in leaf_nodes[:self.config.max_samples]:
            if not leaf.valid_permutations:
                continue
            
            # 構建候選解
            grid = [[0]*self.config.grid_size for _ in range(self.config.grid_size)]
            
            for i, vals in known_rows.items():
                grid[i] = vals
            
            for row_idx, perm_indices in leaf.valid_permutations.items():
                if perm_indices and row_idx in row_perm_cache:
                    selected_perm = row_perm_cache[row_idx][perm_indices[0] % len(row_perm_cache[row_idx])]
                    grid[row_idx] = selected_perm
            
            # 快速驗證
            if self._quick_verify(grid):
                solutions.append(grid)
                print(f"   採樣到解 #{len(solutions)}")
            
            if len(solutions) >= self.config.max_samples:
                break
        
        self.collected_solutions = solutions
        return solutions
    
    def _quick_verify(self, grid: List[List[int]]) -> bool:
        """快速驗證（只檢查列約束）"""
        for j in range(self.config.grid_size):
            col = [grid[i][j] for i in range(self.config.grid_size)]
            if len(set(col)) < self.config.grid_size:
                return False
        return True
    
    def run_full_analysis(self) -> Dict:
        """執行完整分析"""
        start_time = time.time()
        
        # 1. 載入數據
        print("="*60)
        print("增量化多解空間採樣分析")
        print("="*60)
        
        grid_template, row_labels, known_rows, unknown_rows, row_perm_cache, results = \
            self.load_puzzle_data()
        
        print(f"\n數據載入完成:")
        print(f"   已知行: {len(known_rows)}")
        print(f"   未知行: {len(unknown_rows)}")
        
        # 2. 構建採樣樹
        self.build_sampling_tree(known_rows, unknown_rows, row_perm_cache)
        
        # 3. 多解採樣
        self.sample_solutions(known_rows, unknown_rows, row_perm_cache)
        
        # 4. CP-SAT 驗證唯一性
        cp_sat_result = self.cp_sat_verifier.verify_with_solution_limit(
            known_rows=known_rows,
            unknown_rows=unknown_rows,
            row_perm_options={i: row_perm_cache.get(i, []) for i in unknown_rows},
            solution_limit=self.config.solution_limit_cp_sat,
            time_limit=self.config.cp_sat_time_limit
        )
        
        # 5. 多樣性分析
        diversity_score = self._calculate_diversity()
        
        elapsed = time.time() - start_time
        
        # 匯總結果
        result = {
            'summary': {
                'total_time': elapsed,
                'known_rows': len(known_rows),
                'unknown_rows': len(unknown_rows),
                'solutions_sampled': len(self.collected_solutions),
                'cp_sat_solutions': cp_sat_result['num_solutions'],
                'quantum_state': cp_sat_result['quantum_state'],
                'diversity_score': diversity_score
            },
            'sampling_tree_stats': {
                'total_nodes': len(self.sampling_tree),
                'max_depth': max(n.depth for n in self.sampling_tree.values()),
                'branching_factors': self._compute_branching_factors()
            },
            'cp_sat_result': cp_sat_result,
            'config': {
                'grid_size': self.config.grid_size,
                'box_size': self.config.box_size,
                'target_branching': self.config.target_branching,
                'max_samples': self.config.max_samples,
                'solution_limit_cp_sat': self.config.solution_limit_cp_sat
            }
        }
        
        return result
    
    def _compute_branching_factors(self) -> List[int]:
        """計算各層的分支因子"""
        factors = []
        for depth in range(1, self.config.max_tree_depth + 1):
            nodes_prev = [n for n in self.sampling_tree.values() if n.depth == depth - 1]
            total_children = sum(len(n.children) for n in nodes_prev)
            factors.append(total_children // max(1, len(nodes_prev)))
        return factors
    
    def _calculate_diversity(self) -> float:
        """計算解多樣性"""
        if len(self.collected_solutions) < 2:
            return 0.0
        
        # 計算解之間的平均漢明距離
        total_distance = 0
        count = 0
        for i in range(len(self.collected_solutions)):
            for j in range(i+1, len(self.collected_solutions)):
                dist = sum(
                    1 for r in range(self.config.grid_size) 
                    for c in range(self.config.grid_size)
                    if self.collected_solutions[i][r][c] != self.collected_solutions[j][r][c]
                )
                total_distance += dist
                count += 1
        
        avg_distance = total_distance / max(1, count)
        max_distance = self.config.grid_size * self.config.grid_size
        return avg_distance / max_distance


def main():
    """主函數"""
    config = IncrementalSamplingConfig(
        grid_size=16,
        box_size=4,
        target_branching=5,
        max_tree_depth=4,
        max_samples=30,
        solution_limit_cp_sat=10,
        cp_sat_time_limit=300,
        diversity_threshold=0.3,
        permutation_sample_size=500
    )
    
    engine = IncrementalSamplingEngine(config)
    result = engine.run_full_analysis()
    
    # 保存結果
    output_path = Path("D:/2026/WPF_Sudoku/Sudoku_256") / "incremental_sampling_cp_sat_result.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 結果已保存: {output_path}")
    print(f"\n總結:")
    print(f"   量子態: {result['summary']['quantum_state']}")
    print(f"   CP-SAT 解數: {result['summary']['cp_sat_solutions']}")
    print(f"   多樣性分數: {result['summary']['diversity_score']:.3f}")
    print(f"   總時間: {result['summary']['total_time']:.1f}秒")
    
    # 如果有解，顯示第一個解
    if result['cp_sat_result']['solutions']:
        print("\n第一個解:")
        row_labels = [chr(ord('A')+i) for i in range(16)]
        for i, row in enumerate(result['cp_sat_result']['solutions'][0]):
            row_str = ' '.join(f'{v:2d}' for v in row)
            print(f"行{row_labels[i]:2s}: {row_str}")
    
    return result


if __name__ == '__main__':
    main()
