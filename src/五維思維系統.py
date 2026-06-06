"""
五維思維框架系統 - 主整合入口
Five-Dimensional Thinking Framework System - Main Integration Entry

整合模組：
- 五維約束系統 (Five-Dimensional Constraint System)
- 易經卦象引擎 (I-Ching Hexagram Engine)  
- 博弈優選引擎 (Game Optimization Engine)

使用方式：
    from 五維思維系統 import FiveDimensionalFramework
    
    framework = FiveDimensionalFramework()
    framework.load_puzzle(puzzle_data)
    framework.solve()
    framework.display()
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

# 導入各模組
from 五維約束系統 import (
    GRID_SIZE, BOX_SIZE, NUM_VALUES, SUM_TARGET,
    PointConstraint, LineConstraint, PlaneConstraint,
    BodyConstraint, SphereConstraint, TimeSpaceConstraint,
    FiveDimensionalSystem, Cell
)
from 易經卦象引擎 import (
    HexagramStructure, Hexagram, YANG, YIN,
    FuheTranslator, HexagramMapper, HexagramAnalyzer,
    IChingOptimizer, get_all_hexagrams
)
from 博弈優選引擎 import (
    DecisionType, SearchStrategy,
    DecisionTree, DecisionNode, ValueFunction,
    SearchPruner, SymmetryBreaker,
    FiveDimensionalSolver
)


# ============================================================================
# 五維思維框架主類
# ============================================================================

@dataclass
class FrameworkConfig:
    """框架配置"""
    grid_size: int = 16
    box_size: int = 4
    use_hexagram: bool = True
    use_symmetry: bool = True
    max_backtracks: int = 100
    prune_threshold: float = 0.5
    search_strategy: str = "backtrack"
    show_progress: bool = True
    verbose: bool = True


class FiveDimensionalFramework:
    """五維思維框架 - 完整整合系統"""
    
    def __init__(self, config: Optional[FrameworkConfig] = None):
        self.config = config or FrameworkConfig()
        
        # 初始化各維系統
        self.constraint_system = FiveDimensionalSystem()
        self.solver = FiveDimensionalSolver(
            strategy=SearchStrategy(self.config.search_strategy)
        )
        
        # 卦象系統
        self.hexagram_engine = {
            'translator': FuheTranslator,
            'mapper': HexagramMapper,
            'analyzer': HexagramAnalyzer,
            'optimizer': IChingOptimizer,
            'all_hexagrams': get_all_hexagrams()
        }
        
        # 狀態記錄
        self.is_loaded = False
        self.is_solved = False
        self.current_hexagram: Optional[HexagramStructure] = None
        self.hexagram_evolution: List[Dict] = []
        self.search_history: List[Dict] = []
    
    def load_puzzle(self, 
                    puzzle: Dict[Tuple[int, int], int],
                    verify: bool = True) -> bool:
        """
        載入數獨題目
        
        Args:
            puzzle: {(row, col): value, ...} 初值字典
            verify: 是否驗證題目有效性
        
        Returns:
            是否載入成功
        """
        self.is_loaded = False
        self.is_solved = False
        
        # 初始化系統
        self.constraint_system.initialize()
        
        # 設定初值
        self.constraint_system.set_initial_values(puzzle)
        
        # 約束傳播
        self.constraint_system.propagate_constraints()
        
        # 驗證
        if verify:
            if not self.constraint_system.check_consistency():
                if self.config.verbose:
                    print("❌ 題目約束不一致")
                return False
        
        self.is_loaded = True
        
        # 初始卦象
        self._update_hexagram()
        
        if self.config.verbose:
            print(f"✅ 題目載入成功，{len(puzzle)} 個初值")
            print(f"📿 初始卦象: {self.current_hexagram.name}{self.current_hexagram.symbol}")
        
        return True
    
    def solve(self, 
              find_all: bool = False,
              time_limit: Optional[float] = None) -> bool:
        """
        求解數獨
        
        Args:
            find_all: 是否尋找所有解
            time_limit: 時間限制（秒）
        
        Returns:
            是否找到解
        """
        if not self.is_loaded:
            print("❌ 請先載入題目")
            return False
        
        if self.config.verbose:
            print("\n🎮 開始五維博弈求解...")
            print(f"   策略: {self.config.search_strategy}")
            print(f"   卦象優化: {self.config.use_hexagram}")
        
        # 啟動求解
        success = self.solver.solve(use_hexagram=self.config.use_hexagram)
        
        self.is_solved = success and len(self.solver.solutions) > 0
        
        # 記錄結果
        if self.is_solved:
            self._record_results()
            
            if self.config.verbose:
                print(f"\n✅ 求解完成！找到 {len(self.solver.solutions)} 個解")
                print(f"📊 搜索統計: {self._get_search_summary()}")
                print(f"📿 卦象演變: {len(self.hexagram_evolution)} 步")
        else:
            if self.config.verbose:
                print("\n❌ 未找到解")
        
        return self.is_solved
    
    def _update_hexagram(self) -> None:
        """更新當前卦象"""
        status = self.constraint_system.get_dimension_status()
        
        dim_statuses = {
            0: status['point']['solved_cells'] > 0,
            1: status['line']['rows_complete'] > 0,
            2: status['plane']['planes_complete'] > 0,
            3: status['body']['consistent'],
            4: status['sphere']['num_states'] > 0,
            5: status['spacetime']['time_step'] > 0,
        }
        
        self.current_hexagram = FuheTranslator.dimension_to_hexagram(dim_statuses)
    
    def _record_results(self) -> None:
        """記錄結果"""
        # 卦象演化
        self.hexagram_evolution = self.solver.get_hexagram_evolution()
        
        # 搜索歷史
        self.search_history = self.solver.search_states
    
    def get_solution(self) -> Optional[List[List[int]]]:
        """取得解"""
        return self.solver.get_solution()
    
    def get_all_solutions(self) -> List[List[List[int]]]:
        """取得所有解"""
        return self.solver.get_all_solutions()
    
    def get_constraint_report(self) -> Dict:
        """取得約束報告"""
        if not self.is_loaded:
            return {}
        
        return {
            'point_layer': self._describe_point_layer(),
            'line_layer': self._describe_line_layer(),
            'plane_layer': self._describe_plane_layer(),
            'body_layer': self._describe_body_layer(),
            'sphere_layer': self._describe_sphere_layer(),
            'spacetime_layer': self._describe_spacetime_layer(),
        }
    
    def _describe_point_layer(self) -> Dict:
        """點層描述"""
        cells = self.constraint_system.point.cells
        solved = sum(1 for c in cells.values() if c.is_solved())
        empty = sum(1 for c in cells.values() if c.is_empty())
        
        return {
            'total_cells': len(cells),
            'solved_cells': solved,
            'empty_cells': empty,
            'given_cells': sum(1 for c in cells.values() if c.is_given),
            'expression': 'P(r,c,v): Cell(r,c) = v or Cell(r,c) ∈ Domain'
        }
    
    def _describe_line_layer(self) -> Dict:
        """線層描述"""
        rows = self.constraint_system.line.rows
        cols = self.constraint_system.line.cols
        
        return {
            'rows': {
                'total': len(rows),
                'complete': sum(1 for r in rows if r.is_complete()),
                'expression': 'L_row(r): AllDifferent(Row(r)) ∧ Sum(Row(r)) = 136'
            },
            'cols': {
                'total': len(cols),
                'complete': sum(1 for c in cols if c.is_complete()),
                'expression': 'L_col(c): AllDifferent(Col(c)) ∧ Sum(Col(c)) = 136'
            }
        }
    
    def _describe_plane_layer(self) -> Dict:
        """面層描述"""
        planes = self.constraint_system.plane.planes
        
        return {
            'planes': {
                'total': len(planes),
                'complete': sum(1 for p in planes.values() if p.is_complete()),
                'box_size': BOX_SIZE,
                'expression': 'P_plane(g): AllDifferent(Plane(g)) ∧ Sum(Plane(g)) = 136'
            }
        }
    
    def _describe_body_layer(self) -> Dict:
        """體層描述"""
        return {
            'network': 'B(r,c,g): Cell(r,c) ∈ Row(r) ∩ Col(c) ∩ Plane(g)',
            'diagonals': {
                'main': 'D_main: AllDifferent({Cell(i,i)})',
                'anti': 'D_anti: AllDifferent({Cell(i,15-i)})'
            },
            'consistent': self.constraint_system.check_consistency(),
            'expression': 'Body: 3D Constraint Network'
        }
    
    def _describe_sphere_layer(self) -> Dict:
        """球層描述"""
        return {
            'solution_space': f'S = {{s | s is valid solution}}',
            'hamming_metric': 'H(s1,s2) = Σᵢ [s1[i] ≠ s2[i]]',
            'sphere_projection': 'π: S → Sⁿ (n-dim unit sphere)',
            'volume_estimate': 'V ≈ Rⁿ where R = avg_hamming_radius'
        }
    
    def _describe_spacetime_layer(self) -> Dict:
        """時空層描述"""
        return {
            'search_process': 'State(t) = {Cells(t), Constraints(t), SearchPath(t)}',
            'evolution': f'{len(self.search_history)} states recorded',
            'constraint_propagation': 'AC-3 / MAC / Forward Checking',
            'expression': 'Space-Time: Search Evolution'
        }
    
    def get_hexagram_analysis(self) -> Optional[Dict]:
        """取得當前卦象分析"""
        if not self.current_hexagram:
            return None
        
        analysis = HexagramAnalyzer.analyze(self.current_hexagram)
        
        return {
            'hexagram': self.current_hexagram.name,
            'symbol': self.current_hexagram.symbol,
            'binary': self.current_hexagram.get_binary_string(),
            'upper_trigram': analysis.upper_analysis.trigram.name,
            'lower_trigram': analysis.lower_analysis.trigram.name,
            'upper_strength': analysis.upper_analysis.strength,
            'lower_strength': analysis.lower_analysis.strength,
            'overall_meaning': analysis.overall_meaning,
            'recommendation': analysis.recommendation,
            'judgment': self.current_hexagram.judgment
        }
    
    def get_optimization_strategy(self) -> Dict:
        """取得優化策略建議"""
        if not self.current_hexagram:
            return {}
        
        progress = 0.0
        if self.search_history:
            solved_ratio = self.search_history[-1].get('unsolved', GRID_SIZE*GRID_SIZE) / (GRID_SIZE*GRID_SIZE)
            progress = 1.0 - solved_ratio
        
        opt = IChingOptimizer.optimize_search(self.current_hexagram, progress)
        
        return {
            'strategy': opt['strategy'],
            'params': opt['params'],
            'hexagram': self.current_hexagram.name,
            'judgment': opt['卦辭'],
            '五維權重建議': self._get_weight_suggestion(opt['strategy'])
        }
    
    def _get_weight_suggestion(self, strategy: str) -> Dict[str, float]:
        """取得五維權重建議"""
        suggestions = {
            'aggressive': {'w_point': 0.1, 'w_line': 0.15, 'w_plane': 0.15, 'w_body': 0.4, 'w_sphere': 0.1, 'w_spacetime': 0.1},
            'conservative': {'w_point': 0.25, 'w_line': 0.25, 'w_plane': 0.25, 'w_body': 0.1, 'w_sphere': 0.1, 'w_spacetime': 0.05},
            'balanced': {'w_point': 0.15, 'w_line': 0.2, 'w_plane': 0.2, 'w_body': 0.25, 'w_sphere': 0.1, 'w_spacetime': 0.1},
            'explore': {'w_point': 0.1, 'w_line': 0.1, 'w_plane': 0.1, 'w_body': 0.2, 'w_sphere': 0.3, 'w_spacetime': 0.2},
            'finalize': {'w_point': 0.05, 'w_line': 0.1, 'w_plane': 0.1, 'w_body': 0.3, 'w_sphere': 0.1, 'w_spacetime': 0.35},
        }
        return suggestions.get(strategy, suggestions['balanced'])
    
    def _get_search_summary(self) -> str:
        """取得搜索摘要"""
        stats = self.solver.get_search_stats()
        return (f"節點={stats['nodes_explored']}, "
                f"回溯={stats['backtracks']}, "
                f"剪枝={stats['pruned_nodes']}, "
                f"解={stats['solutions_found']}")
    
    def display_solution(self) -> None:
        """顯示解"""
        if not self.is_solved:
            print("❌ 無解可顯示")
            return
        
        solution = self.get_solution()
        self.solver.print_solution()
    
    def display_constraint_hierarchy(self) -> None:
        """顯示約束層級"""
        print("\n" + "=" * 70)
        print("📐 五維約束層級架構")
        print("=" * 70)
        
        report = self.get_constraint_report()
        
        print("\n【點層 Point (0D)】")
        p = report['point_layer']
        print(f"   單元格: {p['total_cells']} 個")
        print(f"   已解: {p['solved_cells']} 個 | 空: {p['empty_cells']} 個")
        print(f"   約束: {p['expression']}")
        
        print("\n【線層 Line (1D)】")
        l = report['line_layer']
        print(f"   行: {l['rows']['complete']}/{l['rows']['total']} 完成")
        print(f"   列: {l['cols']['complete']}/{l['cols']['total']} 完成")
        print(f"   約束: {l['rows']['expression']}")
        print(f"          {l['cols']['expression']}")
        
        print("\n【面層 Plane (2D)】")
        p_info = report['plane_layer']
        print(f"   宮格: {p_info['planes']['complete']}/{p_info['planes']['total']} 完成")
        print(f"   宮格大小: {p_info.get('box_size', BOX_SIZE)}×{p_info.get('box_size', BOX_SIZE)}")
        print(f"   約束: {p_info['planes']['expression']}")
        
        print("\n【體層 Body (3D)】")
        b = report['body_layer']
        print(f"   約束網絡: {'✓ 一致' if b['consistent'] else '✗ 不一致'}")
        print(f"   主對角線: {b['diagonals']['main']}")
        print(f"   反對角線: {b['diagonals']['anti']}")
        print(f"   約束: {b['network']}")
        
        print("\n【球層 Sphere (4D)】")
        s = report['sphere_layer']
        print(f"   解空間: {s['solution_space']}")
        print(f"   漢明度量: {s['hamming_metric']}")
        print(f"   球面投影: {s['sphere_projection']}")
        
        print("\n【時空層 Space-Time (5D)】")
        t = report['spacetime_layer']
        print(f"   搜索過程: {t['search_process']}")
        print(f"   狀態記錄: {t['evolution']}")
        print(f"   約束傳播: {t['constraint_propagation']}")
        
        print("=" * 70)
    
    def display_hexagram_evolution(self) -> None:
        """顯示卦象演化"""
        print("\n" + "=" * 70)
        print("📿 卦象演化過程")
        print("=" * 70)
        
        if not self.hexagram_evolution:
            print("   無演化記錄")
            return
        
        for i, entry in enumerate(self.hexagram_evolution[:20]):  # 限制顯示前20步
            arrow = "→" if i < len(self.hexagram_evolution) - 1 else "✓"
            print(f"   步{i:3d}: {entry['hexagram']:4s}{entry['symbol']:2s} "
                  f"({entry['upper']}{entry['lower']}) "
                  f"{entry['binary']} {arrow}")
        
        if len(self.hexagram_evolution) > 20:
            print(f"   ... 共 {len(self.hexagram_evolution)} 步")
        
        print("=" * 70)


# ============================================================================
# 快速使用範例
# ============================================================================

def create_simple_puzzle() -> Dict[Tuple[int, int], int]:
    """創建簡單範例題目"""
    return {
        (0, 0): 1, (0, 1): 2, (0, 2): 3, (0, 3): 4,
        (0, 12): 13, (0, 13): 14, (0, 14): 15, (0, 15): 16,
        (1, 0): 5, (1, 1): 6, (1, 2): 7, (1, 3): 8,
        (1, 4): 9, (1, 5): 10, (1, 6): 11, (1, 7): 12,
        (2, 8): 1, (2, 9): 2, (2, 10): 3, (2, 11): 4,
        (3, 12): 5, (3, 13): 6, (3, 14): 7, (3, 15): 8,
    }


def demo():
    """演示五維思維框架"""
    print("=" * 70)
    print("🌟 五維思維框架 - 數獨博弈系統演示")
    print("=" * 70)
    
    # 創建框架
    config = FrameworkConfig(
        grid_size=16,
        box_size=4,
        use_hexagram=True,
        use_symmetry=True,
        max_backtracks=100,
        prune_threshold=0.5,
        search_strategy="backtrack",
        show_progress=True,
        verbose=True
    )
    
    framework = FiveDimensionalFramework(config)
    
    # 載入題目
    puzzle = create_simple_puzzle()
    framework.load_puzzle(puzzle)
    
    # 顯示約束層級
    framework.display_constraint_hierarchy()
    
    # 顯示卦象分析
    analysis = framework.get_hexagram_analysis()
    if analysis:
        print("\n🔮 當前卦象分析:")
        print(f"   卦名: {analysis['hexagram']}{analysis['symbol']}")
        print(f"   上下卦: {analysis['upper_trigram']}上{analysis['lower_trigram']}下")
        print(f"   含義: {analysis['overall_meaning']}")
        print(f"   建議: {analysis['recommendation']}")
        print(f"   卦辭: {analysis['judgment']}")
    
    # 顯示優化策略
    strategy = framework.get_optimization_strategy()
    if strategy:
        print("\n🎯 優化策略建議:")
        print(f"   策略: {strategy['strategy']}")
        print(f"   五維權重: {strategy['五維權重建議']}")
    
    # 求解（註：範例題目可能不完全有效，這裡演示流程）
    print("\n⚠️  範例題目為演示格式，可能需要完整題目才能求解")
    print("   如需實際求解，請提供完整的 16×16 數獨題目")
    
    print("\n" + "=" * 70)
    print("✅ 演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo()
