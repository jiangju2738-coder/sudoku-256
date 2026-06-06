#!/usr/bin/env python3
"""
符闔數獨知識體系與博弈優化框架
V2.0 - 整合DLX、SAT、符闔排列約束
"""

import json
from datetime import datetime

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"


class FuHeSudokuKnowledgeBase:
    """符闔數獨知識庫"""
    
    def __init__(self):
        self.grid_size = 16
        self.box_size = 4
        self.total_cells = 256
        self.values = list(range(1, 17))  # 1-16
        
        self.constraints = {
            "cell": "每個單元格必須填入1-16的某個值",
            "row": "每行必須是1-16的排列（AllDifferent）",
            "col": "每列必須是1-16的排列（AllDifferent）",
            "box": "每宮格必須是1-16的排列（AllDifferent）",
            "fuhe_perm": "每行必須從其符闔排列集中選取恰好1個排列"
        }
        
        self.knowledge = {}
        self.load_knowledge()
    
    def load_knowledge(self):
        """加載已知數字和排列數據"""
        # 加載網格
        with open(f"{BASE_DIR}/sudoku_config.json") as f:
            self.config = json.load(f)
        
        # 加載各行排列
        self.perms = {}
        for r in range(1, 17):
            with open(f"{BASE_DIR}/A{r}_permutations.json") as f:
                self.perms[r] = json.load(f)
        
        # 加載解析的92個數字數據（如果有）
        try:
            with open(f"{BASE_DIR}/box_size4_grid_data.json") as f:
                self.grid_data = json.load(f)
        except:
            self.grid_data = None
        
        print(f"✅ 知識庫加載完成:")
        print(f"   已知數字: {len(self.config.get('known_digits', []))} 個")
        print(f"   總排列: {sum(len(p) for p in self.perms.values()):,} 個")


class ConstraintAnalysis:
    """約束分析器"""
    
    def __init__(self, kb: FuHeSudokuKnowledgeBase):
        self.kb = kb
        self.analysis = {}
    
    def analyze_single_source_values(self):
        """分析單源值（只能在特定行出現的值）"""
        print("\n" + "="*60)
        print("單源值分析")
        print("="*60)
        
        # 統計每個值在每個列位置的來源行
        val_col_sources = {}
        for v in range(1, 17):
            val_col_sources[v] = {}
            for c in range(16):
                sources = set()
                for r in range(1, 17):
                    for perm in self.kb.perms.get(r, []):
                        if perm[c] == v:
                            sources.add(r)
                val_col_sources[v][c] = sources
        
        # 找出單源值
        single_sources = []
        for v in range(1, 17):
            for c in range(16):
                if len(val_col_sources[v][c]) == 1:
                    r = list(val_col_sources[v][c])[0]
                    single_sources.append((v, c+1, r))
        
        print(f"發現 {len(single_sources)} 個單源值:")
        for v, c, r in sorted(single_sources)[:20]:
            print(f"  值{v:2d} 在列{c:2d} 只能來自行{r:2d}")
        
        if len(single_sources) > 20:
            print(f"  ... 還有 {len(single_sources)-20} 個")
        
        return single_sources
    
    def analyze_locking_chains(self):
        """分析鎖定鏈（global constraints）"""
        print("\n" + "="*60)
        print("鎖定鏈分析")
        print("="*60)
        
        # 統計每行的排列數
        row_perm_counts = {r: len(self.kb.perms.get(r, [])) for r in range(1, 17)}
        
        # 最緊約束行
        min_row = min(row_perm_counts, key=row_perm_counts.get)
        max_row = max(row_perm_counts, key=row_perm_counts.get)
        
        print(f"最緊約束行: Row {min_row} ({row_perm_counts[min_row]:,} 排列)")
        print(f"最松約束行: Row {max_row} ({row_perm_counts[max_row]:,} 排列)")
        print(f"約束差異倍數: {row_perm_counts[max_row] / row_perm_counts[min_row]:.1f}x")
        
        # 分析列值域覆蓋
        col_coverage = {}
        for c in range(16):
            covered = set()
            for r in range(1, 17):
                for perm in self.kb.perms.get(r, []):
                    covered.add(perm[c])
            col_coverage[c] = len(covered)
        
        incomplete_cols = [c for c in range(16) if col_coverage[c] < 16]
        if incomplete_cols:
            print(f"\n⚠️ 列值域不完整: {len(incomplete_cols)} 列")
            for c in incomplete_cols[:5]:
                print(f"  列{c+1}: {col_coverage[c]} 個值")
        else:
            print(f"\n✅ 所有列值域完整（1-16）")
        
        return {
            "row_perm_counts": row_perm_counts,
            "col_coverage": col_coverage,
            "min_row": min_row,
            "max_row": max_row
        }
    
    def calculate_search_complexity(self):
        """計算搜索複雜度"""
        from math import log10
        
        print("\n" + "="*60)
        print("搜索複雜度分析")
        print("="*60)
        
        # 組合空間
        total_perms = sum(len(p) for p in self.kb.perms.values())
        combo_space = 1
        log_combo = 0
        
        for r in range(1, 17):
            count = len(self.kb.perms.get(r, []))
            combo_space *= count
            log_combo += log10(count)
        
        print(f"排列總數: {total_perms:,}")
        print(f"組合空間: {combo_space:.2e}")
        print(f"log₁₀(組合空間) = {log_combo:.1f}")
        
        # 標準16x16數獨空間對比
        std_space = (16!)**16 / (4!)**16  # 粗略估計
        log_std = 16 * log10(16!) - 16 * log10(4!)
        
        print(f"\n標準16x16數獨空間: ~10^{log_std:.0f}")
        print(f"符闔數獨壓縮比: {10**(log_std - log_combo):.2e}x")
        
        # 已知數字約束
        known_count = len(self.kb.config.get("known_digits", []))
        remaining_cells = 256 - known_count
        
        print(f"\n已知數字: {known_count}")
        print(f"待填單元格: {remaining_cells}")
        print(f"理論搜索空間上界: {16**remaining_cells:.2e}")
        
        return {
            "combo_space": combo_space,
            "log_combo": log_combo,
            "known_count": known_count,
            "remaining_cells": remaining_cells
        }


class GameTheoryFramework:
    """符闔數獨博弈框架"""
    
    def __init__(self, kb: FuHeSudokuKnowledgeBase, ca: ConstraintAnalysis):
        self.kb = kb
        self.ca = ca
        self.framework = {}
    
    def build_optimization_framework(self):
        """構建優化框架"""
        print("\n" + "="*60)
        print("符闔數獨博弈優化框架")
        print("="*60)
        
        framework = {
            "name": "符闔數獨博弈優化框架",
            "version": "2.0",
            "components": {
                "constraint_system": {
                    "type": "hybrid",
                    "constraints": [
                        "cell_value_assignment",
                        "row_all_different",
                        "col_all_different",
                        "box_all_different",
                        "fuhe_permutation_selection"
                    ]
                },
                "solver_methods": {
                    "exact": ["DLX", "CP-SAT", "SAT"],
                    "heuristic": ["GA", "ACO", "AIS", "Hill Climbing"]
                },
                "optimization_objectives": [
                    "solution_existence",
                    "solution_uniqueness",
                    "solution_count",
                    "search_efficiency"
                ]
            },
            "strategy": {
                "phase1": {
                    "name": "約束建模",
                    "tasks": [
                        "加載符闔排列",
                        "過濾與已知數字相容的排列",
                        "建構精確覆蓋模型"
                    ]
                },
                "phase2": {
                    "name": "解存在性判定",
                    "methods": ["DLX精確計數", "CP-SAT可行性檢查"],
                    "output": ["0解", "1解(唯一)", "多解"]
                },
                "phase3": {
                    "name": "衝突分析",
                    "tasks": [
                        "單源值識別",
                        "鎖定鏈檢測",
                        "不可滿足子集提取"
                    ]
                },
                "phase4": {
                    "name": "求解",
                    "methods": ["回溯搜索", "DLX", "SAT求解"],
                    "output": ["完整解", "部分解", "無解證明"]
                }
            }
        }
        
        print(f"""
框架結構:

【階段1】約束建模
  1. 加載符闔排列集 (1,111,494個排列)
  2. 與已知數字約束相容性過濾
  3. 建構精確覆蓋問題 (DLX/SAT)

【階段2】解存在性判定
  方法: DLX精確計數 + CP-SAT可行性
  輸出:
    - 0解: 約束不可滿足
    - 1解: 唯一解
    - 多解: 存在多個可行解

【階段3】衝突分析
  分析內容:
    - 單源值 (single-source values)
    - 鎖定鏈 (locking chains)
    - 約束衝突根源

【階段4】求解與驗證
  求解方法:
    - 精確: DLX, CP-SAT, SAT
    - 啟發式: GA, ACO, AIS

優化目標:
  1. 快速判定解存在性
  2. 精確計算解的數量
  3. 識別並修復約束衝突
  4. 高效搜索所有解
""")
        
        return framework
    
    def generate_solver_comparison(self):
        """生成求解器對比"""
        print("\n" + "="*60)
        print("求解器性能對比框架")
        print("="*60)
        
        comparison = {
            "DLX": {
                "type": "exact_cover",
                "strengths": ["精確計數", "支援多解", "記憶體效率較高"],
                "weaknesses": ["實現複雜", "大型問題可能記憶體不足"],
                "best_for": "精確解計數、多解搜索"
            },
            "CP-SAT": {
                "type": "constraint_programming",
                "strengths": ["高效傳播", "支援優化", "工業級求解器"],
                "weaknesses": ["需要OR-Tools", "模型建構複雜"],
                "best_for": "可行性判定、約束求解"
            },
            "SAT": {
                "type": "boolean_satisfiability",
                "strengths": ["最成熟求解器", "支援增量求解"],
                "weaknesses": ["編碼複雜", "需要CNF轉換"],
                "best_for": "大規模可行性問題"
            },
            "GA": {
                "type": "genetic_algorithm",
                "strengths": ["快速找到可行解", "支援大規模"],
                "weaknesses": ["不保證唯一性", "可能陷入局部最優"],
                "best_for": "快速可行解搜索"
            },
            "ACO": {
                "type": "ant_colony_optimization",
                "strengths": ["自然啟發", "支援動態约束"],
                "weaknesses": ["調參複雜", "收斂較慢"],
                "best_for": "動態/增量約束問題"
            }
        }
        
        print("\n求解器特性對比:")
        print("-" * 60)
        for solver, info in comparison.items():
            print(f"\n{solver}:")
            print(f"  類型: {info['type']}")
            print(f"  優勢: {', '.join(info['strengths'])}")
            print(f"  劣勢: {', '.join(info['weaknesses'])}")
            print(f"  適用: {info['best_for']}")
        
        return comparison
    
    def build_complete_framework(self):
        """構建完整框架"""
        print("\n" + "="*60)
        print("完整知識體系與博弈框架")
        print("="*60)
        
        # 約束分析
        single_sources = self.ca.analyze_single_source_values()
        locking = self.ca.analyze_locking_chains()
        complexity = self.ca.calculate_search_complexity()
        
        # 博弈框架
        framework = self.build_optimization_framework()
        comparison = self.generate_solver_comparison()
        
        # 整合結果
        complete = {
            "framework": framework,
            "constraint_analysis": {
                "single_sources": single_sources,
                "locking_chains": locking,
                "search_complexity": complexity
            },
            "solver_comparison": comparison,
            "recommendations": self.generate_recommendations(single_sources, locking)
        }
        
        with open(f"{BASE_DIR}/fuhe_sudoku_framework.json", "w", encoding="utf-8") as f:
            json.dump(complete, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n✅ 框架已保存: fuhe_sudoku_framework.json")
        
        return complete
    
    def generate_recommendations(self, single_sources, locking):
        """生成建議"""
        recommendations = []
        
        if len(single_sources) > 50:
            recommendations.append({
                "issue": "大量單源值",
                "count": len(single_sources),
                "recommendation": "單源值過多可能導致全局鎖定鏈，建議檢查排列提取正確性",
                "priority": "high"
            })
        
        if locking["min_row"] == locking["max_row"]:
            recommendations.append({
                "issue": "所有行排列數相同",
                "recommendation": "符闔排列可能未正確區分行約束",
                "priority": "medium"
            })
        
        recommendations.append({
            "issue": "求解策略",
            "recommendation": f"建議優先使用DLX進行精確計數，再使用CP-SAT進行可行性驗證",
            "priority": "info"
        })
        
        return recommendations


def main():
    print("="*70)
    print("符闔數獨知識體系與博弈優化框架 V2.0")
    print("="*70)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化知識庫
    kb = FuHeSudokuKnowledgeBase()
    
    # 約束分析
    ca = ConstraintAnalysis(kb)
    
    # 博弈框架
    gf = GameTheoryFramework(kb, ca)
    
    # 構建完整框架
    framework = gf.build_complete_framework()
    
    print("\n" + "="*70)
    print("【框架構建完成】")
    print("="*70)
    
    return framework


if __name__ == "__main__":
    main()
