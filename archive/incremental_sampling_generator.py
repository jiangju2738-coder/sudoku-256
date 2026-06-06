#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量化多解空間採樣排列生成算法
Incremental Multi-Solution Space Sampling with Permutation Generation

核心概念：
1. 增量約束添加：從低約束到高約束逐步剪枝搜索空間
2. 樹狀多解採樣：每個約束步驟產生分支，構建解空間樹
3. 排列生成：基於符闔排列池，動態生成可行的排列組合
4. 多解空間保持：在量子態（SUPERPOSITION）下採樣多個不同解
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


class SamplingStrategy(Enum):
    """採樣策略"""
    UNIFORM_RANDOM = "uniform_random"      # 均勻隨機採樣
    CONSTRAINT_GUIDED = "constraint_guided" # 約束引導採樣
    DIVERSITY_MAXIMIZED = "diversity_maximized"  # 多樣性最大化採樣


class SamplingState(Enum):
    """採樣狀態"""
    ROOT = "root"                  # 根節點（無約束）
    ROW_CONSTRAINED = "row"        # 行約束
    GIVEN_CONSTRAINED = "given"    # 已知數約束
    FAHUO_CONSTRAINED = "fahuo"    # 符闔排列約束
    COLUMN_CONSTRAINED = "column"  # 列約束
    BOX_CONSTRAINED = "box"        # 宮約束
    FULLY_CONSTRAINED = "full"     # 完全約束


@dataclass
class SamplingNode:
    """採樣樹節點"""
    node_id: str
    state: SamplingState
    depth: int
    partial_grid: Optional[List[List[Optional[int]]]] = None
    valid_permutations: Optional[Dict[int, List[int]]] = None  # row -> 可行排列索引列表
    constraint_count: int = 0
    solution_count_estimate: float = 0.0
    children: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class IncrementalSamplingResult:
    """增量採樣結果"""
    sampling_tree: Dict[str, SamplingNode]
    solutions_collected: List[List[List[int]]]
    solution_count: int
    sampling_time: float
    tree_depth: int
    branching_factors: List[int]  # 每個深度層的平均分支因子
    diversity_score: float  # 解空間多樣性評分


class IncrementalConstraintManager:
    """增量約束管理器"""
    
    def __init__(self, grid_size: int = 16, box_size: int = 4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.permutations: List[List[int]] = []
        self._load_permutations()
        
    def _load_permutations(self):
        """載入符闔排列"""
        perm_path = Path(__file__).parent / 'permutations_v4_final.json'
        if perm_path.exists():
            with open(perm_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.permutations = [list(map(int, p)) for p in data]
                else:
                    self.permutations = [list(map(int, p)) for p in data.get('permutations', [])]
            print(f"📊 符闔排列載入: {len(self.permutations)} 個")
        else:
            # 備用：基本排列
            base = list(range(1, 17))
            self.permutations = []
            for shift in range(16):
                perm = [base[(j + shift) % 16] for j in range(16)]
                self.permutations.append(perm)
            print(f"⚠️ 使用備用排列: {len(self.permutations)} 個")
    
    def filter_permutations_by_given(self, row_idx: int, 
                                      given_cells: Dict[Tuple[int, int], int]) -> List[int]:
        """
        根據已知數過濾某行的可行排列
        
        Args:
            row_idx: 行索引
            given_cells: {(col, value), ...} 該行的已知數
        
        Returns:
            可行排列的索引列表
        """
        if row_idx not in given_cells:
            return list(range(len(self.permutations)))
        
        # 收集該行的已知數
        row_givens = {j: val for (i, j), val in given_cells.items() if i == row_idx}
        
        if not row_givens:
            return list(range(len(self.permutations)))
        
        # 過濾排列
        valid_indices = []
        for perm_idx, perm in enumerate(self.permutations):
            match = True
            for col, val in row_givens.items():
                if perm[col] != val:
                    match = False
                    break
            if match:
                valid_indices.append(perm_idx)
        
        return valid_indices


class IncrementalSamplingTree:
    """
    增量多解空間採樣樹
    
    樹狀結構：
    - 根節點：零約束狀態（所有排列皆可）
    - 第一層：添加部分已知數 → 剪枝排列池
    - 第二層：添加符闔排列選擇 → 確定每行排列
    - 第三層：添加列約束 → 進一步剪枝
    - 第四層：添加宮約束 → 最終驗證
    """
    
    def __init__(self, constraint_manager: IncrementalConstraintManager,
                 given_cells: Dict[Tuple[int, int], int]):
        self.manager = constraint_manager
        self.given_cells = given_cells
        self.tree: Dict[str, SamplingNode] = {}
        self.root_id = "root_0"
        
    def build_sampling_tree(self, target_branching: int = 3) -> Dict[str, SamplingNode]:
        """
        構建增量採樣樹
        
        Args:
            target_branching: 目標分支因子（每個節點的子節點數）
        
        Returns:
            完整的採樣樹
        """
        # 根節點
        root = SamplingNode(
            node_id=self.root_id,
            state=SamplingState.ROOT,
            depth=0,
            partial_grid=[[None] * self.manager.grid_size 
                         for _ in range(self.manager.grid_size)],
            constraint_count=0
        )
        
        # 初始化每行的可行排列
        valid_perms = {}
        for i in range(self.manager.grid_size):
            valid_perms[i] = self.manager.filter_permutations_by_given(i, self.given_cells)
        
        root.valid_permutations = valid_perms
        
        self.tree[self.root_id] = root
        self._expand_node(root, target_branching, depth=1)
        
        return self.tree
    
    def _expand_node(self, node: SamplingNode, target_branching: int, 
                     depth: int, max_depth: int = 4):
        """
        擴展節點：在當前約束基礎上添加新約束
        
        Args:
            node: 當前節點
            target_branching: 目標分支因子
            depth: 當前深度
            max_depth: 最大深度
        """
        if depth > max_depth or node.valid_permutations is None:
            return
        
        # 確定當前節點狀態
        state_map = {
            1: SamplingState.GIVEN_CONSTRAINED,
            2: SamplingState.FAHUO_CONSTRAINED,
            3: SamplingState.COLUMN_CONSTRAINED,
            4: SamplingState.BOX_CONSTRAINED
        }
        new_state = state_map.get(depth, SamplingState.FULLY_CONSTRAINED)
        
        # 為每個子節點生成不同的排列選擇
        valid_rows = [i for i, perms in node.valid_permutations.items() if len(perms) > 1]
        
        if not valid_rows:
            # 所有行只有一個選擇，直接返回
            node.state = new_state
            return
        
        # 選擇要分支的行
        rows_to_branch = random.sample(valid_rows, min(target_branching, len(valid_rows)))
        
        for branch_idx, row_idx in enumerate(rows_to_branch):
            child_id = f"{node.node_id}_b{branch_idx}"
            child_perms = node.valid_permutations.copy()
            
            # 為子節點選擇不同的排列
            available_perms = child_perms[row_idx]
            if len(available_perms) > 1:
                # 選擇一個排列作為該分支的固定選擇
                selected_perm = random.choice(available_perms)
                child_perms[row_idx] = [selected_perm]
            
            child = SamplingNode(
                node_id=child_id,
                state=new_state,
                depth=depth,
                partial_grid=self._apply_permutation_choice(
                    node.partial_grid, child_perms
                ),
                valid_permutations=child_perms,
                constraint_count=node.constraint_count + 1
            )
            
            self.tree[child_id] = child
            node.children.append(child_id)
            
            # 遞歸擴展
            self._expand_node(child, target_branching, depth + 1, max_depth)
    
    def _apply_permutation_choice(self, grid: List[List[Optional[int]]],
                                   perm_choices: Dict[int, List[int]]) -> List[List[Optional[int]]]:
        """應用排列選擇到部分網格"""
        new_grid = [row.copy() for row in grid]
        
        for row_idx, choices in perm_choices.items():
            if len(choices) == 1:
                # 已確定排列
                perm_idx = choices[0]
                if perm_idx < len(self.manager.permutations):
                    new_grid[row_idx] = self.manager.permutations[perm_idx].copy()
        
        return new_grid
    
    def sample_solutions(self, max_samples: int = 10) -> List[List[List[int]]]:
        """
        從採樣樹中採樣多個解
        
        Args:
            max_samples: 最大採樣數
        
        Returns:
            採樣到的解列表
        """
        solutions = []
        
        # 遍歷所有葉節點
        leaf_nodes = [n for n in self.tree.values() 
                      if not n.children and n.valid_permutations is not None]
        
        for leaf in leaf_nodes:
            if len(solutions) >= max_samples:
                break
            
            # 從葉節點的排列選擇構建完整解
            grid = self._construct_solution(leaf.valid_permutations)
            
            # 驗證解的有效性
            if self._verify_solution(grid):
                solutions.append(grid)
        
        return solutions
    
    def _construct_solution(self, perm_choices: Dict[int, List[int]]) -> List[List[int]]:
        """從排列選擇構建完整解"""
        grid = []
        for i in range(self.manager.grid_size):
            if i in perm_choices and len(perm_choices[i]) == 1:
                perm_idx = perm_choices[i][0]
                if perm_idx < len(self.manager.permutations):
                    grid.append(self.manager.permutations[perm_idx].copy())
                else:
                    # 無效索引，使用第一個排列
                    grid.append(self.manager.permutations[0].copy())
            else:
                # 未確定行，使用第一個可行排列
                grid.append(self.manager.permutations[0].copy())
        
        return grid
    
    def _verify_solution(self, grid: List[List[int]]) -> bool:
        """驗證解的有效性"""
        # 檢查行約束（符闔排列保證）
        for i in range(self.manager.grid_size):
            if len(set(grid[i])) != self.manager.grid_size:
                return False
        
        # 檢查列約束
        for j in range(self.manager.grid_size):
            col_vals = [grid[i][j] for i in range(self.manager.grid_size)]
            if len(set(col_vals)) != self.manager.grid_size:
                return False
        
        # 檢查宮約束
        box_size = self.manager.box_size
        for band in range(self.manager.grid_size // box_size):
            for stack in range(self.manager.grid_size // box_size):
                box_vals = []
                for bi in range(box_size):
                    for bj in range(box_size):
                        row = band * box_size + bi
                        col = stack * box_size + bj
                        box_vals.append(grid[row][col])
                if len(set(box_vals)) != box_size * box_size:
                    return False
        
        return True


class MultiSolutionSampler:
    """
    多解空間採樣器
    
    整合增量約束樹與多樣性採樣，生成多個不同的解
    """
    
    def __init__(self, grid_size: int = 16, box_size: int = 4):
        self.grid_size = grid_size
        self.box_size = box_size
        self.constraint_manager = IncrementalConstraintManager(grid_size, box_size)
        
    def sample_with_diversity(self, given_cells: Dict[Tuple[int, int], int],
                               target_solutions: int = 10,
                               strategy: SamplingStrategy = SamplingStrategy.DIVERSITY_MAXIMIZED,
                               timeout: int = 300) -> IncrementalSamplingResult:
        """
        以多樣性為目標採樣多個解
        
        Args:
            given_cells: 已知數位置與值
            target_solutions: 目標解數量
            strategy: 採樣策略
            timeout: 超時時間（秒）
        
        Returns:
            採樣結果
        """
        start_time = time.time()
        
        # 構建採樣樹
        sampling_tree = IncrementalSamplingTree(self.constraint_manager, given_cells)
        tree = sampling_tree.build_sampling_tree(target_branching=3)
        
        # 從樹中採樣
        solutions = sampling_tree.sample_solutions(max_samples=target_solutions * 2)
        
        # 如果解不足，使用 CP-SAT 直接求解補充
        if len(solutions) < target_solutions:
            additional = self._cp_sat_sample(given_cells, target_solutions - len(solutions), timeout - (time.time() - start_time))
            solutions.extend(additional)
        
        # 計算多樣性評分
        diversity_score = self._calculate_diversity(solutions)
        
        # 計算分支因子
        branching_factors = self._compute_branching_factors(tree)
        
        elapsed = time.time() - start_time
        
        return IncrementalSamplingResult(
            sampling_tree=tree,
            solutions_collected=solutions,
            solution_count=len(solutions),
            sampling_time=elapsed,
            tree_depth=max(n.depth for n in tree.values()),
            branching_factors=branching_factors,
            diversity_score=diversity_score
        )
    
    def _cp_sat_sample(self, given_cells: Dict[Tuple[int, int], int],
                        num_solutions: int, timeout: float) -> List[List[List[int]]]:
        """使用 CP-SAT 採樣多個解"""
        if timeout <= 0:
            return []
        
        model = cp_model.CpModel()
        x = {}
        
        # 創建變量
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                x[(i, j)] = model.NewIntVar(1, self.grid_size, f'x[{i},{j}]')
        
        # 行約束
        for i in range(self.grid_size):
            model.AddAllDifferent([x[(i, j)] for j in range(self.grid_size)])
        
        # 已知數約束
        for (i, j), val in given_cells.items():
            model.Add(x[(i, j)] == val)
        
        # 符闔排列約束
        for i in range(self.grid_size):
            selector_vars = []
            for perm_idx, perm in enumerate(self.constraint_manager.permutations):
                var = model.NewBoolVar(f'select_row{i}_perm{perm_idx}')
                for j, val in enumerate(perm):
                    model.Add(x[(i, j)] == val).OnlyEnforceIf(var)
                selector_vars.append(var)
            model.AddExactlyOne(selector_vars)
        
        # 列約束
        for j in range(self.grid_size):
            model.AddAllDifferent([x[(i, j)] for i in range(self.grid_size)])
        
        # 宮約束
        for band in range(self.grid_size // self.box_size):
            for stack in range(self.grid_size // self.box_size):
                box_vars = []
                for bi in range(self.box_size):
                    for bj in range(self.box_size):
                        row = band * self.box_size + bi
                        col = stack * self.box_size + bj
                        box_vars.append(x[(row, col)])
                model.AddAllDifferent(box_vars)
        
        # 收集解
        solutions = []
        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self, buffer, limit):
                super().__init__()
                self.buffer = buffer
                self.limit = limit
            
            def on_solution_callback(self):
                if len(self.buffer) < self.limit:
                    solution = []
                    for i in range(16):
                        row = []
                        for j in range(16):
                            row.append(self.Value(x[(i, j)]))
                        solution.append(row)
                    self.buffer.append(solution)
        
        collector = SolutionCollector(solutions, num_solutions)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout
        solver.Solve(model, collector)
        
        return solutions
    
    def _calculate_diversity(self, solutions: List[List[List[int]]]) -> float:
        """
        計算解空間多樣性
        
        方法：計算任意兩解之間的漢明距離平均值
        """
        if len(solutions) < 2:
            return 1.0
        
        total_distance = 0
        pairs = 0
        
        for i in range(len(solutions)):
            for j in range(i + 1, len(solutions)):
                dist = 0
                for row in range(self.grid_size):
                    for col in range(self.grid_size):
                        if solutions[i][row][col] != solutions[j][row][col]:
                            dist += 1
                total_distance += dist
                pairs += 1
        
        avg_distance = total_distance / pairs if pairs > 0 else 0
        max_distance = self.grid_size * self.grid_size
        
        return avg_distance / max_distance
    
    def _compute_branching_factors(self, tree: Dict[str, SamplingNode]) -> List[int]:
        """計算每個深度層的分支因子"""
        depth_children = defaultdict(list)
        
        for node in tree.values():
            depth_children[node.depth].append(len(node.children))
        
        branching = []
        for depth in sorted(depth_children.keys()):
            if depth_children[depth]:
                avg = sum(depth_children[depth]) / len(depth_children[depth])
                branching.append(round(avg, 2))
        
        return branching


def generate_incremental_sampling_report(result: IncrementalSamplingResult,
                                          given_rate: float) -> str:
    """生成增量採樣報告"""
    
    report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    增量化多解空間採樣報告                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  採樣時間: {time.strftime('%Y-%m-%d %H:%M:%S')}                                    ║
║  填滿率: {given_rate*100:.1f}%                                                    ║
║  採樣時長: {result.sampling_time:.2f} 秒                                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  採樣結果:                                                                    ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  解數量: {result.solution_count}                                                 ║
║  採樣樹深度: {result.tree_depth}                                                  ║
║  平均分支因子: {', '.join(f'{b}' for b in result.branching_factors)}                                              ║
║  多樣性評分: {result.diversity_score:.4f} (1.0=完全多樣, 0.0=完全相同)                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  解空間狀態評估:                                                              ║
║  ─────────────────────────────────────────────────────────────────────────   ║
"""
    
    if result.solution_count == 0:
        report += """║  ❌ 未找到任何可行解 - 約束衝突                                             ║
║  請檢查給定數字與符闔排列的相容性                                          ║
"""
    elif result.solution_count == 1:
        report += """║  🔬 找到唯一解 - 系統坍縮 (COLLAPSED)                                      ║
║  ★ 解空間已收斂至單一點                                                    ║
║  ★ 多樣性評分: {:.4f} (低多樣性，符合唯一解特徵)                       ║
""".format(result.diversity_score)
    else:
        report += f"""║  ⚛️ 找到 {result.solution_count} 個解 - 量子態保持 (SUPERPOSITION)                              ║
║  ★ 解空間保持開放，多解共存                                                ║
║  ★ 多樣性評分: {result.diversity_score:.4f} ({'高' if result.diversity_score > 0.3 else '中' if result.diversity_score > 0.1 else '低'}多樣性)                          ║
║  ★ 平均漢明距離: {result.diversity_score * 256:.1f} / 256 cells                                    ║
"""
    
    report += f"""╚══════════════════════════════════════════════════════════════════════════════╝

📊 採樣樹結構:
"""
    
    # 樹結構摘要
    depth_summary = defaultdict(lambda: {'nodes': 0, 'total_children': 0})
    for node in result.sampling_tree.values():
        depth_summary[node.depth]['nodes'] += 1
        depth_summary[node.depth]['total_children'] += len(node.children)
    
    # 深度到狀態的映射
    depth_state_map = {
        0: "ROOT",
        1: "GIVEN",
        2: "FAHUO",
        3: "COLUMN",
        4: "BOX",
        5: "FULL"
    }
    
    for depth in sorted(depth_summary.keys()):
        info = depth_summary[depth]
        state = depth_state_map.get(depth, "UNKNOWN")
        avg_branch = info['total_children'] / info['nodes'] if info['nodes'] > 0 else 0
        report += f"   深度 {depth} ({state}): {info['nodes']} 個節點, 平均分支 {avg_branch:.2f}\n"
    
    if result.solutions_collected:
        report += f"\n📋 採樣到的 {len(result.solutions_collected)} 個解（前3個）:\n"
        for idx, sol in enumerate(result.solutions_collected[:3]):
            report += f"\n   解 #{idx + 1}:\n"
            for row in sol[:4]:  # 只顯示前4行
                report += f"      {' '.join(f'{v:2d}' for v in row)}\n"
            if len(result.solutions_collected) > 3:
                report += f"\n   ... (還有 {len(result.solutions_collected) - 3} 個解)\n"
    
    return report


if __name__ == "__main__":
    # 演示：從已知解採樣並生成多解空間
    
    print("=" * 80)
    print("增量化多解空間採樣排列生成算法 - 演示")
    print("=" * 80)
    
    # 載入真實解
    solution_path = Path(__file__).parent / 'solution_v4_final.json'
    if solution_path.exists():
        with open(solution_path, 'r', encoding='utf-8') as f:
            solution = json.load(f)
        print(f"✅ 載入真實解: 16×16 網格")
    else:
        # 生成一個測試解
        print("⚠️ 無真實解文件，生成測試解")
        solution = [[(i * 4 + j * 2) % 16 + 1 for j in range(16)] for i in range(16)]
    
    # 從解中採樣已知數（15% 填滿率）
    given_rate = 0.15
    given_cells = {}
    positions = [(i, j) for i in range(16) for j in range(16)]
    random.seed(42)
    random.shuffle(positions)
    
    n_givens = int(len(positions) * given_rate)
    for i, j in positions[:n_givens]:
        given_cells[(i, j)] = solution[i][j]
    
    print(f"📊 已知數: {len(given_cells)} 個 ({given_rate*100:.1f}% 填滿率)")
    
    # 初始化採樣器
    sampler = MultiSolutionSampler(grid_size=16, box_size=4)
    
    # 執行增量採樣
    print("\n🔄 開始增量多解空間採樣...")
    result = sampler.sample_with_diversity(
        given_cells=given_cells,
        target_solutions=10,
        strategy=SamplingStrategy.DIVERSITY_MAXIMIZED,
        timeout=60
    )
    
    # 生成報告
    report = generate_incremental_sampling_report(result, given_rate)
    print(report)
    
    # 保存結果
    output_path = Path(__file__).parent / 'incremental_sampling_result.json'
    output_data = {
        'sampling_time': result.sampling_time,
        'solution_count': result.solution_count,
        'diversity_score': result.diversity_score,
        'tree_depth': result.tree_depth,
        'branching_factors': result.branching_factors,
        'solutions': result.solutions_collected[:5]  # 保存前5個解
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 結果已保存到: {output_path}")
