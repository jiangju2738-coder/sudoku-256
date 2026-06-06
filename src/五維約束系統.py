"""
五維思維框架 - 數獨約束系統核心模組
Five-Dimensional Thinking Framework - Sudoku Constraint System Core Module

包含：
- Point_Module: 點層（單一單元格約束）
- Line_Module: 線層（行/列一維約束鏈）
- Plane_Module: 面層（宮格/區域二維約束）
- Body_Module: 體層（三維約束網絡）
- Sphere_Module: 球層（解空間球形分布）
- TimeSpace_Module: 時空層（搜索過程演化）
"""

from typing import Set, List, Dict, Tuple, Optional, FrozenSet
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import math


# ============================================================================
# 常數定義
# ============================================================================

GRID_SIZE = 16  # 16×16 數獨
BOX_SIZE = 4    # 4×4 宮格
NUM_VALUES = 16  # 值域 1-16
SUM_TARGET = 136  # 1+2+...+16 = 136


class Dimension(Enum):
    """五維定義"""
    POINT = 0   # 點 - 單一單元格
    LINE = 1    # 線 - 行/列
    PLANE = 2   # 面 - 宮格/區域
    BODY = 3    # 體 - 三維網絡
    SPHERE = 4  # 球 - 解空間
    SPACE_TIME = 5  # 時空 - 搜索過程


class ConstraintType(Enum):
    """約束類型"""
    UNIQUE = "unique"           # 唯一性
    DOMAIN = "domain"           # 值域
    ALL_DIFF = "all_different"  # 全不同
    SUM = "sum"                 # 和約束
    SYMMETRY = "symmetry"       # 對稱性


# ============================================================================
# 第一維：點層 - 單一單元格約束
# ============================================================================

@dataclass
class Cell:
    """單一單元格（點層）"""
    row: int
    col: int
    box: int  # 所屬宮格索引 (0-15)
    domain: Set[int] = field(default_factory=lambda: set(range(1, NUM_VALUES + 1)))
    value: Optional[int] = None
    is_given: bool = False  # 是否為初值
    
    def __post_init__(self):
        """初始化後處理"""
        if self.is_given and self.value is not None:
            self.domain = {self.value}
    
    def set_value(self, value: int) -> bool:
        """賦值（值域縮小為單點）"""
        if value not in self.domain:
            return False
        self.value = value
        self.domain = {value}
        return True
    
    def remove_from_domain(self, value: int) -> bool:
        """從值域中移除值"""
        if self.value is not None:
            return False  # 已確定值不可修改
        if value in self.domain:
            self.domain.remove(value)
            return True
        return False
    
    def get_min_domain_value(self) -> Optional[int]:
        """取得最小域值（MRV策略）"""
        if not self.domain:
            return None
        return min(self.domain)
    
    def get_domain_size(self) -> int:
        """取得域大小"""
        return len(self.domain)
    
    def is_solved(self) -> bool:
        """是否已求解"""
        return self.value is not None and len(self.domain) == 1
    
    def is_empty(self) -> bool:
        """是否為空（無值）"""
        return self.value is None
    
    def get_constraint_expression(self) -> str:
        """取得約束表達式（點層）"""
        if self.is_given:
            return f"Cell({self.row},{self.col}) = {self.value}"
        elif self.value is not None:
            return f"Cell({self.row},{self.col}) = {self.value}"
        else:
            return f"Cell({self.row},{self.col}) ∈ {sorted(self.domain)}"


@dataclass
class PointConstraint:
    """點層約束集合"""
    cells: Dict[Tuple[int, int], Cell] = field(default_factory=dict)
    
    def initialize_grid(self) -> None:
        """初始化 16×16 網格"""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                box = (r // BOX_SIZE) * BOX_SIZE + (c // BOX_SIZE)
                self.cells[(r, c)] = Cell(row=r, col=c, box=box)
    
    def set_given(self, row: int, col: int, value: int) -> None:
        """設定初值"""
        cell = self.cells[(row, col)]
        cell.is_given = True
        cell.value = value
        cell.domain = {value}
    
    def get_cell(self, row: int, col: int) -> Cell:
        """取得單元格"""
        return self.cells[(row, col)]
    
    def get_unsolved_cells(self) -> List[Cell]:
        """取得未求解單元格列表（按域大小排序 - MRV）"""
        unsolved = [c for c in self.cells.values() if not c.is_solved()]
        unsolved.sort(key=lambda c: c.get_domain_size())
        return unsolved
    
    def get_min_remaining_value_cell(self) -> Optional[Cell]:
        """取得 MRV（最小剩餘值）變元"""
        unsolved = self.get_unsolved_cells()
        return unsolved[0] if unsolved else None


# ============================================================================
# 第二維：線層 - 行/列一維約束鏈
# ============================================================================

@dataclass
class Line:
    """線層：行或列"""
    line_type: str  # 'row' or 'col'
    index: int  # 行號或列號 (0-15)
    cells: List[Cell] = field(default_factory=list)
    domain_set: Set[int] = field(default_factory=lambda: set(range(1, NUM_VALUES + 1)))
    assigned_values: Set[int] = field(default_factory=set)
    
    def add_cell(self, cell: Cell) -> None:
        """添加單元格到線"""
        self.cells.append(cell)
    
    def propagate(self) -> bool:
        """約束傳播：更新域和已賦值"""
        self.assigned_values = set()
        removed = False
        for cell in self.cells:
            if cell.is_solved():
                self.assigned_values.add(cell.value)
            else:
                old_size = len(cell.domain)
                cell.domain -= self.assigned_values
                if len(cell.domain) != old_size:
                    removed = True
        return removed
    
    def is_consistent(self) -> bool:
        """檢查一致性"""
        return len(self.assigned_values) == len(set(self.assigned_values))
    
    def is_complete(self) -> bool:
        """檢查是否完整（全賦值）"""
        return all(c.is_solved() for c in self.cells)
    
    def get_remaining_values(self) -> Set[int]:
        """取得剩餘可用值"""
        return self.domain_set - self.assigned_values
    
    def get_constraint_expression(self) -> str:
        """取得約束表達式（線層）"""
        if self.line_type == 'row':
            return f"AllDifferent(Row({self.index})) ∧ Sum(Row({self.index})) = {SUM_TARGET}"
        else:
            return f"AllDifferent(Col({self.index})) ∧ Sum(Col({self.index})) = {SUM_TARGET}"


@dataclass
class LineConstraint:
    """線層約束管理器"""
    rows: List[Line] = field(default_factory=list)
    cols: List[Line] = field(default_factory=list)
    
    def initialize_from_point(self, point: PointConstraint) -> None:
        """從點層初始化線層"""
        # 初始化行
        for r in range(GRID_SIZE):
            row = Line(line_type='row', index=r)
            for c in range(GRID_SIZE):
                row.add_cell(point.get_cell(r, c))
            self.rows.append(row)
        
        # 初始化列
        for c in range(GRID_SIZE):
            col = Line(line_type='col', index=c)
            for r in range(GRID_SIZE):
                col.add_cell(point.get_cell(r, c))
            self.cols.append(col)
    
    def propagate_all(self) -> bool:
        """傳播所有線約束"""
        changed = False
        for line in self.rows + self.cols:
            if line.propagate():
                changed = True
        return changed
    
    def check_consistency(self) -> bool:
        """檢查所有線一致性"""
        for line in self.rows + self.cols:
            if not line.is_consistent():
                return False
        return True
    
    def get_line(self, line_type: str, index: int) -> Line:
        """取得指定行或列"""
        if line_type == 'row':
            return self.rows[index]
        else:
            return self.cols[index]


# ============================================================================
# 第三維：面層 - 宮格/區域二維約束
# ============================================================================

@dataclass
class Plane:
    """面層：宮格（4×4 區域）"""
    box_index: int  # 宮格索引 (0-15)
    box_row: int    # 宮格行位置 (0-3)
    box_col: int    # 宮格列位置 (0-3)
    cells: List[Cell] = field(default_factory=list)
    assigned_values: Set[int] = field(default_factory=set)
    
    def add_cell(self, cell: Cell) -> None:
        """添加單元格到宮格"""
        self.cells.append(cell)
    
    def propagate(self) -> bool:
        """約束傳播"""
        removed = False
        self.assigned_values = set()
        for cell in self.cells:
            if cell.is_solved():
                self.assigned_values.add(cell.value)
            else:
                old_size = len(cell.domain)
                cell.domain -= self.assigned_values
                if len(cell.domain) != old_size:
                    removed = True
        return removed
    
    def is_consistent(self) -> bool:
        """檢查一致性"""
        return len(self.assigned_values) == len(set(self.assigned_values))
    
    def is_complete(self) -> bool:
        """檢查是否完整"""
        return all(c.is_solved() for c in self.cells)
    
    def get_constraint_expression(self) -> str:
        """取得約束表達式（面層）"""
        return f"AllDifferent(Plane({self.box_index})) ∧ Sum(Plane({self.box_index})) = {SUM_TARGET}"


@dataclass
class PlaneConstraint:
    """面層約束管理器"""
    planes: Dict[int, Plane] = field(default_factory=dict)
    
    def initialize_from_point(self, point: PointConstraint) -> None:
        """從點層初始化面層"""
        for br in range(BOX_SIZE):
            for bc in range(BOX_SIZE):
                box_idx = br * BOX_SIZE + bc
                plane = Plane(box_index=box_idx, box_row=br, box_col=bc)
                
                # 添加該宮格範圍內的單元格
                for r in range(br * BOX_SIZE, (br + 1) * BOX_SIZE):
                    for c in range(bc * BOX_SIZE, (bc + 1) * BOX_SIZE):
                        cell = point.get_cell(r, c)
                        plane.add_cell(cell)
                
                self.planes[box_idx] = plane
    
    def propagate_all(self) -> bool:
        """傳播所有面約束"""
        changed = False
        for plane in self.planes.values():
            if plane.propagate():
                changed = True
        return changed
    
    def check_consistency(self) -> bool:
        """檢查所有面一致性"""
        for plane in self.planes.values():
            if not plane.is_consistent():
                return False
        return True
    
    def get_plane(self, box_index: int) -> Plane:
        """取得指定宮格"""
        return self.planes.get(box_index)


# ============================================================================
# 第四維：體層 - 三維約束網絡
# ============================================================================

@dataclass
class BodyConstraint:
    """體層：三維約束網絡"""
    point: PointConstraint
    line: LineConstraint
    plane: PlaneConstraint
    
    def __init__(self, point: PointConstraint, line: LineConstraint, plane: PlaneConstraint):
        self.point = point
        self.line = line
        self.plane = plane
        self.diagonals = {
            'main': [],    # 主對角線
            'anti': []     # 反對角線
        }
        self._initialize_diagonals()
    
    def _initialize_diagonals(self) -> None:
        """初始化對角線約束"""
        for i in range(GRID_SIZE):
            self.diagonals['main'].append(self.point.get_cell(i, i))
            self.diagonals['anti'].append(self.point.get_cell(i, GRID_SIZE - 1 - i))
    
    def propagate(self) -> bool:
        """三維約束網絡傳播"""
        changed = False
        
        # 點層 → 線層 → 面層 遞歸傳播
        for _ in range(3):  # AC-3風格迭代
            if self.line.propagate_all():
                changed = True
            if self.plane.propagate_all():
                changed = True
        
        # 對角線約束傳播
        self._propagate_diagonals()
        
        return changed
    
    def _propagate_diagonals(self) -> None:
        """對角線約束傳播"""
        for diag_name, cells in self.diagonals.items():
            assigned = set(c.value for c in cells if c.is_solved())
            for cell in cells:
                if not cell.is_solved():
                    cell.domain -= assigned
    
    def check_all_consistency(self) -> bool:
        """檢查全約束一致性"""
        return (self.line.check_consistency() and 
                self.plane.check_consistency() and
                self._check_diagonals())
    
    def _check_diagonals(self) -> bool:
        """檢查對角線一致性"""
        for diag_name, cells in self.diagonals.items():
            values = [c.value for c in cells if c.is_solved()]
            if len(values) != len(set(values)):
                return False
        return True
    
    def get_cell_constraints(self, row: int, col: int) -> Dict:
        """取得單元格的三維約束"""
        cell = self.point.get_cell(row, col)
        return {
            'point': cell.get_constraint_expression(),
            'line': f"Row({row}) ∩ Col({col})",
            'plane': f"Plane({cell.box})",
            'domain': set(cell.domain)
        }


# ============================================================================
# 第五維：球層 - 解空間球形分布
# ============================================================================

@dataclass
class SphereState:
    """球層狀態：解空間球形表示"""
    solution_vector: List[int]  # 解向量（128維）
    hamming_radius: float = 0.0
    sphere_center: Optional[List[int]] = None
    
    def to_vector(self) -> List[int]:
        """轉換為向量（用於距離計算）"""
        return self.solution_vector
    
    def hamming_distance(self, other: 'SphereState') -> int:
        """漢明距離"""
        return sum(1 for a, b in zip(self.solution_vector, other.solution_vector) if a != b)
    
    def euclidean_distance(self, other: 'SphereState') -> float:
        """歐氏距離"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(self.solution_vector, other.solution_vector)))
    
    def normalize_to_sphere(self) -> List[float]:
        """投影到單位球面"""
        vec = self.to_vector()
        norm = math.sqrt(sum(v ** 2 for v in vec))
        if norm == 0:
            return vec
        return [v / norm for v in vec]


@dataclass
class SphereConstraint:
    """球層約束管理器"""
    states: List[SphereState] = field(default_factory=list)
    solution_space_volume: float = 0.0
    
    def add_state(self, state: SphereState) -> None:
        """添加狀態"""
        self.states.append(state)
    
    def compute_solution_space_density(self) -> float:
        """計算解空間密度"""
        if len(self.states) < 2:
            return 0.0
        
        # 計算平均漢明距離（半徑）
        total_dist = 0
        for i, s1 in enumerate(self.states):
            for s2 in self.states[i+1:]:
                total_dist += s1.hamming_distance(s2)
        
        avg_radius = total_dist / (len(self.states) * (len(self.states) - 1) / 2)
        self.hamming_radius = avg_radius
        
        # 球體體積近似（n維球體體積公式）
        n = GRID_SIZE * GRID_SIZE
        # V_n = π^(n/2) / Γ(n/2 + 1) * R^n
        # 這裡用離散近似
        self.solution_space_volume = avg_radius ** n
        
        return 1.0 / max(1, len(self.states))  # 密度倒數
    
    def get_nearest_neighbor(self, query: SphereState) -> Optional[SphereState]:
        """找最近鄰居"""
        if not self.states:
            return None
        
        min_dist = float('inf')
        nearest = None
        for state in self.states:
            dist = query.hamming_distance(state)
            if dist < min_dist:
                min_dist = dist
                nearest = state
        return nearest
    
    def get_sphere_constraint_expression(self) -> str:
        """取得球層約束表達式"""
        return (f"Sphere(S) with |S|={len(self.states)} solutions, "
                f"avg_hamming_radius={self.hamming_radius:.2f}")


# ============================================================================
# 第六維：時空層 - 搜索過程時間演化
# ============================================================================

@dataclass
class SearchState:
    """時空狀態：搜索過程中的某一刻"""
    time_step: int
    point: PointConstraint
    constraints_pass: int
    constraints_total: int
    backtracks: int
    nodes_explored: int
    solution_found: bool = False
    parent_state: Optional['SearchState'] = None
    
    def get_progress_ratio(self) -> float:
        """取得進度比例"""
        return self.constraints_pass / max(1, self.constraints_total)


@dataclass
class TimeSpaceConstraint:
    """時空層約束管理器：搜索演算法"""
    states: List[SearchState] = field(default_factory=list)
    current_state: Optional[SearchState] = None
    max_depth: int = GRID_SIZE * GRID_SIZE
    
    def initialize_search(self, body: BodyConstraint) -> SearchState:
        """初始化搜索狀態"""
        initial = SearchState(
            time_step=0,
            point=body.point,
            constraints_pass=0,
            constraints_total=GRID_SIZE * 3 + 2,  # 16行+16列+16宮+2對角
            backtracks=0,
            nodes_explored=0
        )
        self.current_state = initial
        self.states.append(initial)
        return initial
    
    def update_state(self, body: BodyConstraint, 
                     pass_count: int, 
                     nodes: int,
                     backtracks: int,
                     solved: bool = False) -> SearchState:
        """更新搜索狀態"""
        new_time = len(self.states)
        new_state = SearchState(
            time_step=new_time,
            point=body.point,
            constraints_pass=pass_count,
            constraints_total=GRID_SIZE * 3 + 2,
            backtracks=backtracks,
            nodes_explored=nodes,
            solution_found=solved,
            parent_state=self.current_state
        )
        self.states.append(new_state)
        self.current_state = new_state
        return new_state
    
    def get_search_path(self) -> List[SearchState]:
        """取得搜索路徑"""
        if not self.current_state:
            return []
        
        path = []
        state = self.current_state
        while state:
            path.append(state)
            state = state.parent_state
        return list(reversed(path))
    
    def get_spacetime_expression(self) -> str:
        """取得時空約束表達式"""
        if not self.current_state:
            return "Search: Not Started"
        
        cs = self.current_state
        return (f"Time(t={cs.time_step}): "
                f"Nodes={cs.nodes_explored}, "
                f"Backtracks={cs.backtracks}, "
                f"Progress={cs.get_progress_ratio():.2%}, "
                f"Solution={'Found' if cs.solution_found else 'Searching'}")


# ============================================================================
# 五維整合系統
# ============================================================================

class FiveDimensionalSystem:
    """五維思維框架整合系統"""
    
    def __init__(self):
        # 初始化各維
        self.point = PointConstraint()
        self.line = LineConstraint()
        self.plane = PlaneConstraint()
        self.body: Optional[BodyConstraint] = None
        self.sphere = SphereConstraint()
        self.spacetime = TimeSpaceConstraint()
        
        # 統計資訊
        self.total_propagations = 0
        self.total_checks = 0
    
    def initialize(self) -> None:
        """初始化整個系統"""
        # 點層初始化
        self.point.initialize_grid()
        
        # 線層從點層初始化
        self.line.initialize_from_point(self.point)
        
        # 面層從點層初始化
        self.plane.initialize_from_point(self.point)
        
        # 體層整合
        self.body = BodyConstraint(self.point, self.line, self.plane)
    
    def set_initial_values(self, values: Dict[Tuple[int, int], int]) -> None:
        """設定初始值"""
        for (row, col), value in values.items():
            self.point.set_given(row, col, value)
    
    def propagate_constraints(self) -> bool:
        """約束傳播（層間遞歸）"""
        changed = False
        
        # 點 → 線 → 面 → 體 傳播
        for _ in range(3):
            if self.body.propagate():
                changed = True
            self.total_propagations += 1
        
        return changed
    
    def check_consistency(self) -> bool:
        """檢查一致性"""
        self.total_checks += 1
        return self.body.check_all_consistency()
    
    def is_solved(self) -> bool:
        """檢查是否完全求解"""
        for cell in self.point.cells.values():
            if not cell.is_solved():
                return False
        return True
    
    def get_solution(self) -> Optional[List[List[int]]]:
        """取得解（如果已求解）"""
        if not self.is_solved():
            return None
        
        grid = []
        for r in range(GRID_SIZE):
            row_values = []
            for c in range(GRID_SIZE):
                cell = self.point.get_cell(r, c)
                row_values.append(cell.value)
            grid.append(row_values)
        return grid
    
    def get_dimension_status(self) -> Dict:
        """取得五維狀態報告"""
        return {
            'point': {
                'solved_cells': sum(1 for c in self.point.cells.values() if c.is_solved()),
                'empty_cells': sum(1 for c in self.point.cells.values() if c.is_empty()),
                'expression': 'Cell-level constraints'
            },
            'line': {
                'rows_complete': sum(1 for r in self.line.rows if r.is_complete()),
                'cols_complete': sum(1 for c in self.line.cols if c.is_complete()),
                'expression': 'Row/Column AllDifferent'
            },
            'plane': {
                'planes_complete': sum(1 for p in self.plane.planes.values() if p.is_complete()),
                'expression': 'Box AllDifferent'
            },
            'body': {
                'constraints_pass': self.total_checks,
                'consistent': self.check_consistency(),
                'expression': '3D Constraint Network'
            },
            'sphere': {
                'num_states': len(self.sphere.states),
                'expression': 'Solution Space Sphere'
            },
            'spacetime': {
                'time_step': len(self.spacetime.states),
                'expression': 'Search Evolution'
            }
        }


# ============================================================================
# 測試程式碼
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("五維思維框架 - 數獨約束系統測試")
    print("=" * 70)
    
    # 創建系統
    system = FiveDimensionalSystem()
    system.initialize()
    
    # 設定一些初始值（範例）
    sample_values = {
        (0, 0): 1,
        (0, 1): 2,
        (0, 2): 3,
        (0, 3): 4,
        (1, 0): 5,
        (1, 1): 6,
        (2, 2): 7,
        (3, 3): 8,
    }
    system.set_initial_values(sample_values)
    
    # 約束傳播
    print("\n📍 點層 - 單元格狀態:")
    for (r, c), cell in list(system.point.cells.items())[:8]:
        print(f"   Cell({r},{c}): {cell.get_constraint_expression()}")
    
    # 傳播約束
    print("\n🔗 線層 - 約束傳播:")
    system.propagate_constraints()
    
    for r in range(2):
        print(f"   {system.line.rows[r].get_constraint_expression()}")
    
    # 面層狀態
    print("\n🔲 面層 - 宮格狀態:")
    for idx in range(4):
        plane = system.plane.get_plane(idx)
        if plane:
            print(f"   {plane.get_constraint_expression()}")
    
    # 體層一致性檢查
    print("\n🏛️ 體層 - 約束網絡:")
    consistent = system.check_consistency()
    print(f"   一致性: {consistent}")
    
    # 五維狀態報告
    print("\n📊 五維狀態報告:")
    status = system.get_dimension_status()
    for dim, info in status.items():
        print(f"   [{dim.upper()}] {info['expression']}")
        for k, v in info.items():
            if k != 'expression':
                print(f"        {k}: {v}")
    
    print("\n✅ 五維思維框架約束系統初始化完成")
    print("=" * 70)
