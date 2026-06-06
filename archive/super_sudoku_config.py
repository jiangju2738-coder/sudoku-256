#!/usr/bin/env python3
"""
超级大数独配置模块 - 16×16 符阖排列约束
支持：自定义已知数字 + 未知格备选项 + 链式深度搜索
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import time
import copy

# ==================== 数据结构 ====================

@dataclass
class Cell:
    """单个格子的状态"""
    row: int
    col: int
    value: Optional[int] = None  # None表示未知
    candidates: Set[int] = field(default_factory=lambda: set(range(1, 17)))
    is_known: bool = False
    constraint_source: str = ""  # 约束来源
    
    def __post_init__(self):
        if self.value is not None:
            self.is_known = True
            self.candidates = {self.value}
    
    def remove_candidate(self, val: int) -> bool:
        """移除一个候选值"""
        if val in self.candidates:
            self.candidates.discard(val)
            if len(self.candidates) == 1:
                self.value = next(iter(self.candidates))
                self.is_known = True
            return True
        return False
    
    def get_single_candidate(self) -> Optional[int]:
        """如果只剩一个候选值，返回该值"""
        if len(self.candidates) == 1:
            return next(iter(self.candidates))
        return None


@dataclass
class SudokuConfig:
    """超级大数独配置"""
    grid_size: int = 16
    box_size: int = 4  # 4×4宫格
    
    # 已知数字
    known_digits: List[Dict] = field(default_factory=list)
    
    # 符阖排列约束
    fuhh_permutations: Dict[int, List[List[int]]] = field(default_factory=dict)
    
    # 行约束
    row_constraints: Dict[int, List[int]] = field(default_factory=dict)
    
    # 列约束
    col_constraints: Dict[int, List[int]] = field(default_factory=dict)
    
    # 宫约束
    box_constraints: Dict[int, List[int]] = field(default_factory=dict)
    
    # 额外约束（如链式约束）
    extra_constraints: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'grid_size': self.grid_size,
            'box_size': self.box_size,
            'known_digits': self.known_digits,
            'fuhh_permutations': {k: v for k, v in self.fuhh_permutations.items()},
            'row_constraints': self.row_constraints,
            'col_constraints': self.col_constraints,
            'box_constraints': self.box_constraints,
            'extra_constraints': self.extra_constraints
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SudokuConfig':
        """从字典创建"""
        config = cls()
        config.grid_size = data.get('grid_size', 16)
        config.box_size = data.get('box_size', 4)
        config.known_digits = data.get('known_digits', [])
        
        # 加载符阖排列
        fp = data.get('fuhh_permutations', {})
        config.fuhh_permutations = {int(k): v for k, v in fp.items()}
        
        config.row_constraints = {int(k): v for k, v in data.get('row_constraints', {}).items()}
        config.col_constraints = {int(k): v for k, v in data.get('col_constraints', {}).items()}
        config.box_constraints = {int(k): v for k, v in data.get('box_constraints', {}).items()}
        config.extra_constraints = data.get('extra_constraints', [])
        
        return config


# ==================== 初始化与配置 ====================

def create_empty_grid(config: SudokuConfig) -> List[List[Cell]]:
    """创建空的16×16网格"""
    grid = []
    for row in range(1, config.grid_size + 1):
        row_cells = []
        for col in range(1, config.grid_size + 1):
            cell = Cell(row=row, col=col)
            
            # 应用符阖排列约束
            if row in config.fuhh_permutations:
                allowed = set()
                for perm in config.fuhh_permutations[row]:
                    allowed.add(perm[col - 1])
                cell.candidates = allowed
            
            row_cells.append(cell)
        grid.append(row_cells)
    
    return grid


def apply_known_digits(grid: List[List[Cell]], known_digits: List[Dict]) -> int:
    """应用已知数字，返回被设置的格子数"""
    count = 0
    for kd in known_digits:
        row = kd['row'] - 1  # 转为0索引
        col = kd['col'] - 1
        value = kd['value']
        
        if not grid[row][col].is_known:
            grid[row][col].value = value
            grid[row][col].is_known = True
            grid[row][col].candidates = {value}
            grid[row][col].constraint_source = "known_digit"
            count += 1
    
    return count


def load_fuhh_permutations(base_dir: str) -> Dict[int, List[List[int]]]:
    """加载所有符阖排列数据"""
    permutations = {}
    
    for row_num in range(1, 17):
        filename = f"A{row_num}_permutations.json"
        filepath = os.path.join(base_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                perms = json.load(f)
                permutations[row_num] = perms
                print(f"  ✓ A{row_num}: {len(perms):,} 个符阖排列")
        else:
            print(f"  ✗ A{row_num}: 文件不存在")
    
    return permutations


def load_initial_puzzle(base_dir: str) -> List[Dict]:
    """加载初始题目"""
    filepath = os.path.join(base_dir, "initial_puzzle.json")
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('known_digits', [])
    
    return []


def create_config_from_files(base_dir: str = "D:/2026/WPF_Sudoku/Sudoku_256") -> SudokuConfig:
    """从文件创建完整配置"""
    print("=" * 70)
    print("加载超级大数独配置")
    print("=" * 70)
    
    config = SudokuConfig()
    
    # 加载符阖排列
    print("\n[1] 加载符阖排列约束...")
    config.fuhh_permutations = load_fuhh_permutations(base_dir)
    
    # 加载初始题目
    print("\n[2] 加载初始题目...")
    known_digits = load_initial_puzzle(base_dir)
    config.known_digits = known_digits
    print(f"  ✓ 已知数字: {len(known_digits)} 个")
    
    # 添加宫约束（标准数独）
    print("\n[3] 添加4×4宫约束...")
    for box_row in range(4):
        for box_col in range(4):
            box_id = box_row * 4 + box_col
            cells_in_box = []
            for r in range(box_row * 4, (box_row + 1) * 4):
                for c in range(box_col * 4, (box_col + 1) * 4):
                    cells_in_box.append((r + 1, c + 1))
            config.box_constraints[box_id] = cells_in_box
    
    print("\n" + "=" * 70)
    print("配置加载完成")
    print(f"  网格大小: 16×16")
    print(f"  宫格大小: 4×4")
    print(f"  符阖排列行: {len(config.fuhh_permutations)}")
    print(f"  已知数字: {len(config.known_digits)}")
    print("=" * 70)
    
    return config


# ==================== 链式深度搜索求解器 ====================

class ChainDeepSearchSolver:
    """链式深度搜索求解器"""
    
    def __init__(self, config: SudokuConfig):
        self.config = config
        self.grid = create_empty_grid(config)
        self.solution_count = 0
        self.search_nodes = 0
        self.start_time = None
        
        # 应用已知数字
        apply_known_digits(self.grid, config.known_digits)
        
        # 初始化约束传播
        self._initialize_constraints()
    
    def _initialize_constraints(self):
        """初始化约束传播"""
        # 应用行、列、宫约束
        self._propagate_all_diff()
    
    def _propagate_all_diff(self):
        """传播AllDifferent约束"""
        # 行约束
        for row in range(16):
            self._apply_all_diff_row(row)
        
        # 列约束
        for col in range(16):
            self._apply_all_diff_col(col)
        
        # 宫约束
        for box in range(16):
            self._apply_all_diff_box(box)
    
    def _apply_all_diff_row(self, row: int):
        """行AllDifferent传播"""
        row_cells = self.grid[row]
        
        # 找出已确定的值
        fixed_values = set()
        for cell in row_cells:
            if cell.is_known:
                fixed_values.add(cell.value)
        
        # 移除其他格子的固定值
        for cell in row_cells:
            if not cell.is_known:
                for val in fixed_values:
                    cell.remove_candidate(val)
    
    def _apply_all_diff_col(self, col: int):
        """列AllDifferent传播"""
        fixed_values = set()
        for row in range(16):
            if self.grid[row][col].is_known:
                fixed_values.add(self.grid[row][col].value)
        
        for row in range(16):
            cell = self.grid[row][col]
            if not cell.is_known:
                for val in fixed_values:
                    cell.remove_candidate(val)
    
    def _apply_all_diff_box(self, box: int):
        """宫AllDifferent传播"""
        box_row = box // 4
        box_col = box % 4
        
        fixed_values = set()
        for r in range(box_row * 4, (box_row + 1) * 4):
            for c in range(box_col * 4, (box_col + 1) * 4):
                if self.grid[r][c].is_known:
                    fixed_values.add(self.grid[r][c].value)
        
        for r in range(box_row * 4, (box_row + 1) * 4):
            for c in range(box_col * 4, (box_col + 1) * 4):
                cell = self.grid[r][c]
                if not cell.is_known:
                    for val in fixed_values:
                        cell.remove_candidate(val)
    
    def _find_best_cell(self) -> Optional[Tuple[int, int, Set[int]]]:
        """使用MRV启发式找到最佳待填格子"""
        best_cell = None
        min_candidates = 17
        
        for row in range(16):
            for col in range(16):
                cell = self.grid[row][col]
                if not cell.is_known:
                    num_candidates = len(cell.candidates)
                    if 0 < num_candidates < min_candidates:
                        min_candidates = num_candidates
                        best_cell = (row, col, cell.candidates.copy())
                        if num_candidates == 1:  # 不能更好
                            return best_cell
        
        return best_cell
    
    def _is_consistent(self, row: int, col: int, value: int) -> bool:
        """检查赋值是否一致"""
        # 检查行
        for c in range(16):
            if c != col and self.grid[row][c].is_known and self.grid[row][c].value == value:
                return False
        
        # 检查列
        for r in range(16):
            if r != row and self.grid[r][col].is_known and self.grid[r][col].value == value:
                return False
        
        # 检查宫
        box_row = row // 4
        box_col = col // 4
        for r in range(box_row * 4, (box_row + 1) * 4):
            for c in range(box_col * 4, (box_col + 1) * 4):
                if (r != row or c != col) and self.grid[r][c].is_known:
                    if self.grid[r][c].value == value:
                        return False
        
        # 检查符阖排列约束
        if (row + 1) in self.config.fuhh_permutations:
            allowed = set()
            for perm in self.config.fuhh_permutations[row + 1]:
                allowed.add(perm[col])
            if value not in allowed:
                return False
        
        return True
    
    def _save_state(self) -> Dict:
        """保存当前状态"""
        state = {
            'grid': [[cell.value for cell in row] for row in self.grid],
            'candidates': [[list(cell.candidates) for cell in row] for row in self.grid]
        }
        return state
    
    def _restore_state(self, state: Dict):
        """恢复状态"""
        for row in range(16):
            for col in range(16):
                self.grid[row][col].value = state['grid'][row][col]
                self.grid[row][col].candidates = set(state['candidates'][row][col])
                self.grid[row][col].is_known = (state['grid'][row][col] is not None)
    
    def search(self, max_solutions: int = 10, timeout: int = 300) -> List[List[List[int]]]:
        """链式深度搜索"""
        self.solution_count = 0
        self.search_nodes = 0
        self.start_time = time.time()
        
        solutions = []
        
        def dfs():
            # 超时检查
            if time.time() - self.start_time > timeout:
                return
            
            # 解数限制
            if len(solutions) >= max_solutions:
                return
            
            # 检查是否完成
            if self._is_complete():
                self.solution_count += 1
                solution = [row[:] for row in self._get_solution_grid()]
                solutions.append(solution)
                print(f"  🎯 找到解 #{self.solution_count} (节点: {self.search_nodes:,})")
                return
            
            # 选择最佳格子
            best = self._find_best_cell()
            if best is None:
                return  # 无合法格子
            
            row, col, candidates = best
            self.search_nodes += 1
            
            # 链式深度搜索：尝试每个候选值
            for value in sorted(candidates):
                if self._is_consistent(row, col, value):
                    # 保存状态
                    state = self._save_state()
                    
                    # 赋值
                    self.grid[row][col].value = value
                    self.grid[row][col].candidates = {value}
                    self.grid[row][col].is_known = True
                    
                    # 约束传播
                    self._propagate_all_diff()
                    
                    # 递归搜索
                    dfs()
                    
                    # 回溯
                    self._restore_state(state)
        
        print("\n开始链式深度搜索...")
        print(f"  MRV启发式: 最小剩余值优先")
        print(f"  最大解数: {max_solutions}")
        print(f"  超时限制: {timeout}秒")
        
        dfs()
        
        elapsed = time.time() - self.start_time
        print(f"\n搜索完成:")
        print(f"  耗时: {elapsed:.1f}秒")
        print(f"  搜索节点: {self.search_nodes:,}")
        print(f"  找到解数: {len(solutions)}")
        
        return solutions
    
    def _is_complete(self) -> bool:
        """检查是否已完整"""
        for row in range(16):
            for cell in self.grid[row]:
                if not cell.is_known:
                    return False
        return True
    
    def _get_solution_grid(self) -> List[List[int]]:
        """获取解的网格"""
        return [[cell.value for cell in row] for row in self.grid]
    
    def print_grid(self, grid: List[List[int]] = None, title: str = "网格"):
        """打印网格"""
        if grid is None:
            grid = self._get_solution_grid()
        
        print(f"\n{title}:")
        print("  " + " ".join(f"{c:2d}" for c in range(1, 17)))
        
        for i, row in enumerate(grid):
            if i % 4 == 0 and i > 0:
                print("  " + "-" * 50)
            row_str = "  "
            for j, val in enumerate(row):
                if j % 4 == 0 and j > 0:
                    row_str += " | "
                row_str += f"{val:2d}"
            print(row_str)


# ==================== 用户交互配置 ====================

def interactive_config_setup():
    """交互式配置设置"""
    print("\n" + "=" * 70)
    print("超级大数独配置编辑器")
    print("=" * 70)
    
    config = SudokuConfig()
    
    print("\n[1] 网格设置")
    config.grid_size = 16
    config.box_size = 4
    print(f"  ✓ 网格: {config.grid_size}×{config.grid_size}")
    print(f"  ✓ 宫格: {config.box_size}×{config.box_size}")
    
    print("\n[2] 已知数字配置")
    print("  格式: row col value (如: 1 1 1 表示第1行第1列值为1)")
    print("  输入 'done' 完成，'load' 加载初始题目")
    
    while True:
        try:
            line = input("  > ").strip()
            if line.lower() == 'done':
                break
            elif line.lower() == 'load':
                known = load_initial_puzzle("D:/2026/WPF_Sudoku/Sudoku_256")
                config.known_digits = known
                print(f"  ✓ 已加载 {len(known)} 个已知数字")
                break
            else:
                parts = line.split()
                if len(parts) == 3:
                    row, col, val = map(int, parts)
                    config.known_digits.append({
                        'row': row,
                        'col': col,
                        'value': val
                    })
                    print(f"  + 添加: ({row}, {col}) = {val}")
                else:
                    print("  格式错误，请重新输入")
        except EOFError:
            break
    
    print("\n[3] 符阖排列约束")
    print("  从文件加载 A1-A16 符阖排列...")
    config.fuhh_permutations = load_fuhh_permutations("D:/2026/WPF_Sudoku/Sudoku_256")
    
    print("\n[4] 额外约束")
    print("  输入 'skip' 跳过，或添加链式约束")
    print("  链式约束格式: chain cell1 cell2 ... (如: chain 1 1 1 2 2 3)")
    
    while True:
        try:
            line = input("  > ").strip()
            if line.lower() in ['done', 'skip', '']:
                break
            elif line.startswith('chain'):
                parts = line.split()[1:]
                if len(parts) >= 2 and len(parts) % 3 == 0:
                    cells = []
                    for i in range(0, len(parts), 3):
                        cells.append({
                            'row': int(parts[i]),
                            'col': int(parts[i+1]),
                            'value': int(parts[i+2])
                        })
                    config.extra_constraints.append({'type': 'chain', 'cells': cells})
                    print(f"  + 添加链式约束: {len(cells)} 个格子")
                else:
                    print("  格式错误")
        except EOFError:
            break
    
    return config


def save_config(config: SudokuConfig, filename: str = "user_config.json"):
    """保存配置"""
    filepath = os.path.join("D:/2026/WPF_Sudoku/Sudoku_256", filename)
    
    # 简化符阖排列保存（只保存前100个排列以节省空间）
    save_data = config.to_dict()
    for row, perms in save_data['fuhh_permutations'].items():
        save_data['fuhh_permutations'][row] = perms[:100]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 配置已保存到: {filename}")


def load_config(filename: str = "user_config.json") -> SudokuConfig:
    """加载配置"""
    filepath = os.path.join("D:/2026/WPF_Sudoku/Sudoku_256", filename)
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return SudokuConfig.from_dict(data)
    
    return None


# ==================== 主程序 ====================

if __name__ == '__main__':
    print("=" * 70)
    print("超级大数独配置模块")
    print("16×16 符阖排列约束 | 链式深度搜索求解")
    print("=" * 70)
    
    # 从文件加载配置
    config = create_config_from_files("D:/2026/WPF_Sudoku/Sudoku_256")
    
    # 可选：交互式配置
    # config = interactive_config_setup()
    # save_config(config)
    
    # 创建求解器
    solver = ChainDeepSearchSolver(config)
    
    # 显示初始网格
    solver.print_grid(title="初始网格（符阖排列约束）")
    
    # 运行求解
    # solutions = solver.search(max_solutions=5, timeout=60)
    
    print("\n" + "=" * 70)
    print("配置模块就绪")
    print("使用 solver.search() 开始链式深度搜索")
    print("=" * 70)
