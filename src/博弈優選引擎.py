"""
博弈優選引擎 - 五維博弈決策與求解系統
Game Optimization Engine - Five-Dimensional Decision & Solver System

包含：
- DecisionTree: 五維博弈決策樹
- ValueFunction: 博弈值函數計算
- SearchPruner: 搜索剪枝優化
- SymmetryBreaker: 對稱性破缺
- FiveDimensionalSolver: 五維博弈求解器
"""

from typing import Dict, List, Tuple, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import random
import copy

# 導入五維約束系統
from 五維約束系統 import (
    GRID_SIZE, BOX_SIZE, NUM_VALUES, SUM_TARGET,
    PointConstraint, LineConstraint, PlaneConstraint,
    BodyConstraint, SphereConstraint, TimeSpaceConstraint,
    FiveDimensionalSystem, Cell, ConstraintType
)

# 導入易經卦象引擎
from 易經卦象引擎 import (
    HexagramStructure, Hexagram, YANG, YIN,
    FuheTranslator, HexagramMapper, HexagramAnalyzer,
    IChingOptimizer, get_all_hexagrams
)


# ============================================================================
# 博弈決策類型
# ============================================================================

class DecisionType(Enum):
    """決策類型"""
    MRV = "mrv"           # 最小剩餘值
    LCV = "lcv"           # 最少約束值
    DOMINANCE = "dominance"  # 主導性
    HEURISTIC = "heuristic"  # 啟發式


class SearchStrategy(Enum):
    """搜索策略"""
    DFS = "dfs"           # 深度優先
    BFS = "bfs"           # 廣度優先
    BACKTRACK = "backtrack"  # 回溯
    AC3 = "ac3"           # AC-3約束傳播
    MAC = "mac"           # 維持弧一致性


# ============================================================================
# 博弈決策樹節點
# ============================================================================

@dataclass
class DecisionNode:
    """決策樹節點"""
    node_id: int
    depth: int
    variable: Optional[Tuple[int, int]]  # (row, col)
    value: Optional[int]
    domain_size: int
    constraint_strength: float  # 約束強度 (0-1)
    hexagram: Optional[HexagramStructure] = None
    children: List['DecisionNode'] = field(default_factory=list)
    parent: Optional['DecisionNode'] = None
    is_leaf: bool = False
    solution: Optional[List[List[int]]] = None
    
    def get_value(self) -> float:
        """取得節點值"""
        if self.is_leaf and self.solution:
            return 1.0
        return self.constraint_strength


@dataclass
class DecisionTree:
    """博弈決策樹"""
    root: Optional[DecisionNode] = None
    nodes: List[DecisionNode] = field(default_factory=list)
    max_depth: int = GRID_SIZE * GRID_SIZE
    node_counter: int = 0
    
    def create_root(self, system: FiveDimensionalSystem) -> DecisionNode:
        """創建根節點"""
        self.node_counter = 0
        root = DecisionNode(
            node_id=self.node_counter,
            depth=0,
            variable=None,
            value=None,
            domain_size=NUM_VALUES,
            constraint_strength=1.0
        )
        self.root = root
        self.nodes.append(root)
        return root
    
    def add_child(self, parent: DecisionNode, 
                  variable: Tuple[int, int],
                  value: int,
                  system: FiveDimensionalSystem) -> DecisionNode:
        """添加子節點"""
        self.node_counter += 1
        
        cell = system.point.get_cell(variable[0], variable[1])
        
        child = DecisionNode(
            node_id=self.node_counter,
            depth=parent.depth + 1,
            variable=variable,
            value=value,
            domain_size=len(cell.domain),
            constraint_strength=self._calculate_constraint_strength(system),
            parent=parent
        )
        
        # 卦象映射
        dim_statuses = self._get_dimension_statuses(system)
        child.hexagram = FuheTranslator.dimension_to_hexagram(dim_statuses)
        
        parent.children.append(child)
        self.nodes.append(child)
        return child
    
    def _calculate_constraint_strength(self, system: FiveDimensionalSystem) -> float:
        """計算約束強度"""
        unsolved = system.point.get_unsolved_cells()
        if not unsolved:
            return 1.0
        
        avg_domain = sum(c.get_domain_size() for c in unsolved) / len(unsolved)
        # 域越小，約束強度越大
        strength = 1.0 - (avg_domain - 1) / (NUM_VALUES - 1)
        return max(0.0, min(1.0, strength))
    
    def _get_dimension_statuses(self, system: FiveDimensionalSystem) -> Dict[int, bool]:
        """取得五維狀態"""
        unsolved_count = len(system.point.get_unsolved_cells())
        total_cells = GRID_SIZE * GRID_SIZE
        
        return {
            0: unsolved_count < total_cells * 0.1,   # 點層
            1: unsolved_count < total_cells * 0.3,   # 線層
            2: unsolved_count < total_cells * 0.5,   # 面層
            3: unsolved_count < total_cells * 0.7,   # 體層
            4: unsolved_count < total_cells * 0.9,   # 球層
            5: unsolved_count == 0,                   # 時空層
        }
    
    def get_best_child(self, node: DecisionNode) -> Optional[DecisionNode]:
        """取得最佳子節點（按約束強度）"""
        if not node.children:
            return None
        return max(node.children, key=lambda c: c.get_value())
    
    def get_tree_stats(self) -> Dict:
        """取得決策樹統計"""
        return {
            'total_nodes': len(self.nodes),
            'max_depth': max(n.depth for n in self.nodes) if self.nodes else 0,
            'leaves': sum(1 for n in self.nodes if n.is_leaf),
            'solutions': sum(1 for n in self.nodes if n.solution)
        }


# ============================================================================
# 博弈值函數
# ============================================================================

@dataclass
class ValueFunction:
    """博弈值函數"""
    # 五維權重
    w_point: float = 0.15
    w_line: float = 0.20
    w_plane: float = 0.20
    w_body: float = 0.25
    w_sphere: float = 0.10
    w_spacetime: float = 0.10
    
    def calculate(self, system: FiveDimensionalSystem, 
                  node: DecisionNode) -> float:
        """計算值函數"""
        v_point = self._v_point(system)
        v_line = self._v_line(system)
        v_plane = self._v_plane(system)
        v_body = self._v_body(system)
        v_sphere = self._v_sphere(system)
        v_spacetime = self._v_spacetime(node)
        
        total = (self.w_point * v_point +
                self.w_line * v_line +
                self.w_plane * v_plane +
                self.w_body * v_body +
                self.w_sphere * v_sphere +
                self.w_spacetime * v_spacetime)
        
        return total
    
    def _v_point(self, system: FiveDimensionalSystem) -> float:
        """點層值"""
        unsolved = system.point.get_unsolved_cells()
        if not unsolved:
            return 1.0
        
        # 最小域值優先
        min_domain = min(c.get_domain_size() for c in unsolved)
        return 1.0 - (min_domain - 1) / (NUM_VALUES - 1)
    
    def _v_line(self, system: FiveDimensionalSystem) -> float:
        """線層值"""
        row_completes = sum(1 for r in system.line.rows if r.is_complete())
        col_completes = sum(1 for c in system.line.cols if c.is_complete())
        
        return (row_completes + col_completes) / (2 * GRID_SIZE)
    
    def _v_plane(self, system: FiveDimensionalSystem) -> float:
        """面層值"""
        plane_completes = sum(1 for p in system.plane.planes.values() if p.is_complete())
        return plane_completes / GRID_SIZE
    
    def _v_body(self, system: FiveDimensionalSystem) -> float:
        """體層值"""
        if system.check_consistency():
            return 1.0
        return 0.5  # 不一致時扣分
    
    def _v_sphere(self, system: FiveDimensionalSystem) -> float:
        """球層值（解空間密度倒數）"""
        unsolved = len(system.point.get_unsolved_cells())
        # 剩餘變元越少，解空間越集中，值越大
        return 1.0 - (unsolved / (GRID_SIZE * GRID_SIZE))
    
    def _v_spacetime(self, node: DecisionNode) -> float:
        """時空層值（搜索進度）"""
        if node.depth == 0:
            return 0.0
        return node.depth / (GRID_SIZE * GRID_SIZE)


# ============================================================================
# 搜索剪枝器
# ============================================================================

class SearchPruner:
    """搜索剪枝優化器"""
    
    def __init__(self, max_backtracks: int = 100, prune_threshold: float = 0.5):
        self.max_backtracks = max_backtracks
        self.prune_threshold = prune_threshold
        self.backtrack_count = 0
        self.pruned_nodes = 0
    
    def should_prune(self, value: float, system: FiveDimensionalSystem) -> bool:
        """判斷是否剪枝"""
        if value < self.prune_threshold:
            self.pruned_nodes += 1
            return True
        
        # 檢查一致性
        if not system.check_consistency():
            self.pruned_nodes += 1
            return True
        
        # 檢查域空
        for cell in system.point.cells.values():
            if not cell.is_solved() and len(cell.domain) == 0:
                self.pruned_nodes += 1
                return True
        
        return False
    
    def should_backtrack(self) -> bool:
        """判斷是否回溯"""
        return self.backtrack_count >= self.max_backtracks
    
    def record_backtrack(self) -> None:
        """記錄回溯"""
        self.backtrack_count += 1
    
    def reset(self) -> None:
        """重置剪枝器"""
        self.backtrack_count = 0
        self.pruned_nodes = 0
    
    def get_stats(self) -> Dict:
        """取得統計"""
        return {
            'backtracks': self.backtrack_count,
            'pruned_nodes': self.pruned_nodes,
            'max_backtracks': self.max_backtracks,
            'prune_threshold': self.prune_threshold
        }


# ============================================================================
# 對稱性破缺器
# ============================================================================

class SymmetryBreaker:
    """對稱性破缺"""
    
    # 16×16 數獨的對稱操作
    SYMMETRY_OPERATIONS = [
        'identity',      # 恒等
        'rotate_90',     # 90度旋轉
        'rotate_180',    # 180度旋轉
        'rotate_270',    # 270度旋轉
        'reflect_h',     # 水平翻轉
        'reflect_v',     # 垂直翻轉
        'reflect_diag1', # 主對角線翻轉
        'reflect_diag2', # 反對角線翻轉
    ]
    
    @classmethod
    def apply_symmetry(cls, grid: List[List[int]], 
                       operation: str) -> List[List[int]]:
        """應用對稱操作"""
        n = len(grid)
        result = [[0] * n for _ in range(n)]
        
        if operation == 'identity':
            return copy.deepcopy(grid)
        
        elif operation == 'rotate_90':
            for i in range(n):
                for j in range(n):
                    result[j][n-1-i] = grid[i][j]
        
        elif operation == 'rotate_180':
            for i in range(n):
                for j in range(n):
                    result[n-1-i][n-1-j] = grid[i][j]
        
        elif operation == 'rotate_270':
            for i in range(n):
                for j in range(n):
                    result[n-1-j][i] = grid[i][j]
        
        elif operation == 'reflect_h':
            for i in range(n):
                for j in range(n):
                    result[i][n-1-j] = grid[i][j]
        
        elif operation == 'reflect_v':
            for i in range(n):
                for j in range(n):
                    result[n-1-i][j] = grid[i][j]
        
        elif operation == 'reflect_diag1':
            for i in range(n):
                for j in range(n):
                    result[j][i] = grid[i][j]
        
        elif operation == 'reflect_diag2':
            for i in range(n):
                for j in range(n):
                    result[n-1-j][n-1-i] = grid[i][j]
        
        return result
    
    @classmethod
    def get_canonical_form(cls, grid: List[List[int]]) -> List[List[int]]:
        """取得規範形式（最小對稱表示）"""
        all_forms = [
            cls.apply_symmetry(grid, op) 
            for op in cls.SYMMETRY_OPERATIONS
        ]
        # 返回字典序最小的
        return min(all_forms)
    
    @classmethod
    def is_symmetric(cls, grid: List[List[int]], 
                     operation: str) -> bool:
        """檢查是否對稱"""
        return grid == cls.apply_symmetry(grid, operation)


# ============================================================================
# 五維博弈求解器
# ============================================================================

class FiveDimensionalSolver:
    """五維博弈求解器"""
    
    def __init__(self, strategy: SearchStrategy = SearchStrategy.BACKTRACK):
        self.system = FiveDimensionalSystem()
        self.tree = DecisionTree()
        self.value_func = ValueFunction()
        self.pruner = SearchPruner()
        self.strategy = strategy
        
        # 狀態記錄
        self.search_states: List[Dict] = []
        self.solutions: List[List[List[int]]] = []
        self.hexagram_history: List[HexagramStructure] = []
    
    def load_puzzle(self, puzzle: Dict[Tuple[int, int], int]) -> bool:
        """載入數獨題目"""
        self.system.initialize()
        self.system.set_initial_values(puzzle)
        
        # 初始約束傳播
        self.system.propagate_constraints()
        
        # 檢查一致性
        if not self.system.check_consistency():
            return False
        
        return True
    
    def solve(self, use_hexagram: bool = True) -> bool:
        """求解數獨"""
        self.pruner.reset()
        self.solutions = []
        self.search_states = []
        self.hexagram_history = []
        
        # 創建決策樹
        self.tree.create_root(self.system)
        
        # 搜索
        success = self._search(self.tree.root, self.system)
        
        return success
    
    def _search(self, node: DecisionNode, 
                system: FiveDimensionalSystem) -> bool:
        """搜索核心"""
        
        # 記錄狀態
        self._record_state(system, node)
        
        # 取得當前卦象
        dim_statuses = FuheTranslator._get_dimension_statuses(
            self.system if hasattr(self, 'system') else system
        )
        current_hex = FuheTranslator.dimension_to_hexagram(dim_statuses)
        self.hexagram_history.append(current_hex)
        
        # 優化策略
        if use_hexagram:
            opt = IChingOptimizer.optimize_search(current_hex, 
                                                   len(self.solutions) > 0)
            self.pruner.prune_threshold = opt['params']['prune_threshold']
        
        # 檢查是否求解完成
        if system.is_solved():
            solution = system.get_solution()
            if solution:
                node.is_leaf = True
                node.solution = solution
                self.solutions.append(solution)
            return True
        
        # 剪枝檢查
        value = self.value_func.calculate(system, node)
        if self.pruner.should_prune(value, system):
            return False
        
        # MRV選擇變元
        cell = system.point.get_min_remaining_value_cell()
        if not cell:
            return False
        
        variable = (cell.row, cell.col)
        
        # LCV排序值（最少約束值優先）
        values = self._order_values(cell, system)
        
        for value in values:
            if self.pruner.should_backtrack():
                return False
            
            # 創建子節點
            child = self.tree.add_child(node, variable, value, system)
            
            # 保存狀態
            saved_system = self._save_system(system)
            
            # 賦值
            cell.set_value(value)
            
            # 約束傳播
            system.propagate_constraints()
            
            # 遞歸搜索
            if self._search(child, system):
                return True
            
            # 回溯
            self.pruner.record_backtrack()
            self._restore_system(system, saved_system)
        
        return False
    
    def _order_values(self, cell: Cell, 
                      system: FiveDimensionalSystem) -> List[int]:
        """值排序（LCV策略）"""
        # 簡單的LRV：按值大小排序
        return sorted(cell.domain)
    
    def _record_state(self, system: FiveDimensionalSystem, 
                      node: DecisionNode) -> None:
        """記錄搜索狀態"""
        state = {
            'depth': node.depth,
            'unsolved': len(system.point.get_unsolved_cells()),
            'avg_domain': sum(c.get_domain_size() 
                            for c in system.point.get_unsolved_cells()) / 
                         max(1, len(system.point.get_unsolved_cells())),
            'constraints_pass': system.total_checks,
            'backtracks': self.pruner.backtrack_count
        }
        self.search_states.append(state)
    
    def _save_system(self, system: FiveDimensionalSystem) -> Dict:
        """保存系統狀態"""
        return {
            'cells': {
                (r, c): {
                    'value': cell.value,
                    'domain': set(cell.domain),
                    'is_given': cell.is_given
                }
                for (r, c), cell in system.point.cells.items()
            }
        }
    
    def _restore_system(self, system: FiveDimensionalSystem, 
                        saved: Dict) -> None:
        """恢復系統狀態"""
        for (r, c), data in saved['cells'].items():
            cell = system.point.get_cell(r, c)
            cell.value = data['value']
            cell.domain = data['domain']
            cell.is_given = data['is_given']
    
    def get_solution(self) -> Optional[List[List[int]]]:
        """取得解"""
        return self.solutions[0] if self.solutions else None
    
    def get_all_solutions(self) -> List[List[List[int]]]:
        """取得所有解"""
        return self.solutions
    
    def get_search_stats(self) -> Dict:
        """取得搜索統計"""
        return {
            'nodes_explored': len(self.search_states),
            'solutions_found': len(self.solutions),
            'backtracks': self.pruner.backtrack_count,
            'pruned_nodes': self.pruner.pruned_nodes,
            'tree_stats': self.tree.get_tree_stats(),
            'pruner_stats': self.pruner.get_stats(),
            'hexagram_changes': len(self.hexagram_history)
        }
    
    def get_hexagram_evolution(self) -> List[Dict]:
        """取得卦象演化"""
        evolution = []
        for i, hexagram in enumerate(self.hexagram_history):
            evolution.append({
                'step': i,
                'hexagram': hexagram.name,
                'symbol': hexagram.symbol,
                'binary': hexagram.get_binary_string(),
                'upper': hexagram.upper_trigram.name,
                'lower': hexagram.lower_trigram.name
            })
        return evolution
    
    def print_solution(self) -> None:
        """列印解"""
        solution = self.get_solution()
        if not solution:
            print("無解")
            return
        
        print("\n" + "=" * 70)
        print("16×16 數獨解:")
        print("=" * 70)
        
        for i, row in enumerate(solution):
            if i % BOX_SIZE == 0 and i > 0:
                print("-" * 70)
            
            row_str = ""
            for j, val in enumerate(row):
                if j % BOX_SIZE == 0 and j > 0:
                    row_str += " | "
                row_str += f"{val:2} "
            print(row_str)
        
        print("=" * 70)


# ============================================================================
# 範例數獨題目
# ============================================================================

def create_sample_puzzle() -> Dict[Tuple[int, int], int]:
    """創建範例 16×16 數獨題目"""
    puzzle = {
        # 第 0 行
        (0, 0): 1, (0, 1): 2, (0, 2): 3, (0, 3): 4,
        (0, 12): 13, (0, 13): 14, (0, 14): 15, (0, 15): 16,
        
        # 第 1 行
        (1, 0): 5, (1, 1): 6, (1, 2): 7, (1, 3): 8,
        (1, 12): 13, (1, 13): 14, (1, 14): 15, (1, 15): 16,
        
        # 第 2 行
        (2, 0): 9, (2, 1): 10, (2, 2): 11, (2, 3): 12,
        (2, 12): 13, (2, 13): 14, (2, 14): 15, (2, 15): 16,
        
        # 第 3 行
        (3, 0): 13, (3, 1): 14, (3, 2): 15, (3, 3): 16,
        (3, 12): 1, (3, 13): 2, (3, 14): 3, (3, 15): 4,
        
        # 第 4 行
        (4, 0): 1, (4, 1): 2, (4, 2): 3, (4, 3): 4,
        (4, 4): 5, (4, 5): 6, (4, 6): 7, (4, 7): 8,
        
        # 更多給定值...（簡化範例）
    }
    return puzzle


# ============================================================================
# 測試程式碼
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("博弈優選引擎 - 五維博弈決策與求解系統")
    print("=" * 70)
    
    # 1. 創建求解器
    print("\n🎮 1. 初始化五維博弈求解器:")
    solver = FiveDimensionalSolver(strategy=SearchStrategy.BACKTRACK)
    print(f"   策略: {solver.strategy.value}")
    print(f"   五維權重: 點={solver.value_func.w_point}, "
          f"線={solver.value_func.w_line}, 面={solver.value_func.w_plane}, "
          f"體={solver.value_func.w_body}, 球={solver.value_func.w_sphere}")
    
    # 2. 載入題目
    print("\n📝 2. 載入範例題目:")
    puzzle = create_sample_puzzle()
    print(f"   初值數量: {len(puzzle)}")
    
    success = solver.load_puzzle(puzzle)
    print(f"   載入成功: {success}")
    print(f"   初始一致性: {solver.system.check_consistency()}")
    
    # 3. 五維狀態檢查
    print("\n📊 3. 初始五維狀態:")
    status = solver.system.get_dimension_status()
    for dim, info in status.items():
        print(f"   [{dim.upper()}] {info.get('solved_cells', info.get('rows_complete', 'N/A'))}")
    
    # 4. 卦象映射
    print("\n📿 4. 初始卦象映射:")
    dim_statuses = {
        0: status['point']['solved_cells'] > 0,
        1: status['line']['rows_complete'] > 0,
        2: status['plane']['planes_complete'] > 0,
        3: status['body']['consistent'],
        4: status['sphere']['num_states'] > 0,
        5: False,
    }
    initial_hex = FuheTranslator.dimension_to_hexagram(dim_statuses)
    print(f"   卦象: {initial_hex.name}{initial_hex.symbol}")
    print(f"   爻象: {initial_hex.get_yao_sequence()}")
    
    # 5. 對稱性檢查
    print("\n🔄 5. 對稱性分析:")
    sample_grid = [[0] * 16 for _ in range(16)]
    for (r, c), v in puzzle.items():
        sample_grid[r][c] = v
    
    for op in SymmetryBreaker.SYMMETRY_OPERATIONS[:4]:
        is_sym = SymmetryBreaker.is_symmetric(sample_grid, op)
        print(f"   {op}: {'✓ 對稱' if is_sym else '✗ 不對稱'}")
    
    # 6. 決策樹建構
    print("\n🌳 6. 決策樹範例:")
    if solver.tree.root:
        print(f"   根節點: 深度={solver.tree.root.depth}, "
              f"約束強度={solver.tree.root.constraint_strength:.2f}")
    
    # 7. 剪枝器設定
    print("\n✂️ 7. 剪枝器配置:")
    print(f"   最大回溯: {solver.pruner.max_backtracks}")
    print(f"   剪枝閾值: {solver.pruner.prune_threshold}")
    
    # 8. 值函數計算
    print("\n📈 8. 值函數計算:")
    if solver.tree.root:
        value = solver.value_func.calculate(solver.system, solver.tree.root)
        print(f"   初始值: {value:.4f}")
    
    # 9. 卦象優化建議
    print("\n🔮 9. 卦象優化建議:")
    opt = IChingOptimizer.optimize_search(initial_hex, progress=0.0)
    print(f"   策略: {opt['strategy']}")
    print(f"   參數: {opt['params']}")
    print(f"   卦辭: {opt['卦辭']}")
    
    print("\n✅ 博弈優選引擎初始化完成")
    print("=" * 70)
    print("\n💡 提示: 呼叫 solver.solve() 開始博弈求解")
    print("=" * 70)
