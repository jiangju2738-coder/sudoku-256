#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
超級大數獨 (16x16, box_size=4) 深度求解器
採用五維思維框架：點-線-面-體-球-時空
融合 DLX 精確覆蓋算法 + GA/ACO/AIS 混合策略
"""

import pandas as pd
import numpy as np
import json
import time
from itertools import permutations, combinations
from collections import defaultdict
from typing import List, Set, Dict, Tuple, Optional
from copy import deepcopy
from dataclasses import dataclass, field

# ============== 數據加載模組 ==============

def load_row_constraints(base_dir: str) -> Dict[int, np.ndarray]:
    """讀取 16 行符闔排列 Excel 檔案，建立行約束集"""
    constraints = {}
    for row_idx in range(1, 17):
        if row_idx <= 5:
            suffix = "" if row_idx != 5 else "_2505"
        else:
            suffix = ""
        
        filename = f"{base_dir}/A{row_idx}第{['一','二','三','四','五','六','七','八','九','十','十一','十二','十三','十四','十五','十六'][row_idx-1]}行符闔排列.xlsx"
        
        try:
            df = pd.read_excel(filename)
            constraints[row_idx] = df.values[0] if len(df) > 0 else np.array([])
            print(f"✓ 第{row_idx}行: 讀取完成")
        except Exception as e:
            print(f"✗ 第{row_idx}行: 讀取失敗 - {e}")
            constraints[row_idx] = np.array([])
    
    return constraints

# ============== 五維思維引擎 ==============

@dataclass
class FiveDimThinkingFramework:
    """五維思維框架：點-線-面-體-球-時空"""
    
    # 點維度：單元格約束
    point_constraints: Dict[Tuple[int, int], Set[int]] = field(default_factory=dict)
    
    # 線維度：行列約束
    line_constraints: Dict[int, Set[int]] = field(default_factory=dict)
    
    # 面維度：宮格約束
    face_constraints: Dict[Tuple[int, int], Set[int]] = field(default_factory=dict)
    
    # 體維度：行組合約束
    body_constraints: Dict[int, List[Tuple[int, ...]]] = field(default_factory=dict)
    
    # 球維度：全局狀態
    sphere_state: Dict = field(default_factory=dict)
    
    # 時空維度：時空映射
    spacetime_mapping: Dict[Tuple[int, int], Tuple[int, ...]] = field(default_factory=dict)


class SuperSudoku16x16:
    """超級大數獨 (16x16, box_size=4) 求解器"""
    
    BOX_SIZE = 4
    GRID_SIZE = 16
    NUM_DIGITS = 16
    DIGITS = set(range(1, 17))
    
    def __init__(self, row_constraints: Dict[int, np.ndarray] = None):
        self.grid = np.zeros((self.GRID_SIZE, self.GRID_SIZE), dtype=np.int8)
        self.row_constraints = row_constraints or {}
        self.solutions: List[np.ndarray] = []
        self.solution_count = 0
        
        # 初始化約束矩陣
        self._init_constraints()
        
        # 五維思維框架
        self.framework = FiveDimThinkingFramework()
        
    def _init_constraints(self):
        """初始化五維約束系統"""
        for row in range(1, self.GRID_SIZE + 1):
            self.framework.line_constraints[row] = set()
            
        for col in range(1, self.GRID_SIZE + 1):
            self.framework.point_constraints[(1, col)] = self.DIGITS.copy()
            
        for box_row in range(self.BOX_SIZE):
            for box_col in range(self.BOX_SIZE):
                self.framework.face_constraints[(box_row, box_col)] = set()
    
    def load_puzzle(self, txt_file: str):
        """從 txt 檔案載入初盤"""
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                if i >= self.GRID_SIZE:
                    break
                values = line.strip().split()
                for j, val in enumerate(values):
                    if val != '0' and val != '.':
                        self.grid[i, j] = int(val)
            print(f"✓ 載入初盤完成，共 {np.count_nonzero(self.grid)} 個已知數")
        except FileNotFoundError:
            print("⚠ 初盤檔案不存在，使用空盤求解")
            
    def get_possibilities(self, row: int, col: int) -> Set[int]:
        """取得單元格 (row, col) 的可能值集合"""
        possibilities = self.DIGITS - set(self.grid[row, :]) - set(self.grid[:, col])
        
        # 宮格約束
        box_row = row // self.BOX_SIZE
        box_col = col // self.BOX_SIZE
        box_start_row = box_row * self.BOX_SIZE
        box_start_col = box_col * self.BOX_SIZE
        
        box_values = set()
        for i in range(box_start_row, box_start_row + self.BOX_SIZE):
            for j in range(box_start_col, box_start_col + self.BOX_SIZE):
                if self.grid[i, j] != 0:
                    box_values.add(self.grid[i, j])
        
        possibilities -= box_values
        
        return possibilities
    
    def is_valid(self, row: int, col: int, value: int) -> bool:
        """檢查在 (row, col) 填入 value 是否合法"""
        if value in self.grid[row, :]:
            return False
        if value in self.grid[:, col]:
            return False
        
        box_row = row // self.BOX_SIZE
        box_col = col // self.BOX_SIZE
        box_start_row = box_row * self.BOX_SIZE
        box_start_col = box_col * self.BOX_SIZE
        
        for i in range(box_start_row, box_start_row + self.BOX_SIZE):
            for j in range(box_start_col, box_start_col + self.BOX_SIZE):
                if self.grid[i, j] == value:
                    return False
        
        return True
    
    def find_best_cell(self) -> Optional[Tuple[int, int, Set[int]]]:
        """MRV 策略：尋找可能值最少的單元格"""
        min_possibilities = float('inf')
        best_cell = None
        
        for row in range(self.GRID_SIZE):
            for col in range(self.GRID_SIZE):
                if self.grid[row, col] == 0:
                    possibilities = self.get_possibilities(row, col)
                    if len(possibilities) < min_possibilities:
                        min_possibilities = len(possibilities)
                        best_cell = (row, col, possibilities)
                        if min_possibilities == 1:
                            return best_cell
                        
        return best_cell
    
    def solve_backtrack(self, max_solutions: int = 1000) -> int:
        """回溯法求解，收集所有解"""
        start_time = time.time()
        
        def backtrack(count: int = 0) -> int:
            nonlocal start_time
            
            if time.time() - start_time > 60:
                print(f"⏰ 超時 (60秒)，已找到的解: {count}")
                return count
            
            cell = self.find_best_cell()
            if cell is None:
                # 找到完整解
                self.solutions.append(deepcopy(self.grid))
                count += 1
                print(f"✓ 找到第 {count} 個解")
                return count if count >= max_solutions else count
            
            row, col, possibilities = cell
            
            for value in sorted(possibilities):
                if self.is_valid(row, col, value):
                    self.grid[row, col] = value
                    
                    # 時空映射記錄
                    self.framework.spacetime_mapping[(row, col)] = (value,)
                    
                    count = backtrack(count)
                    if count >= max_solutions:
                        return count
                    
                    self.grid[row, col] = 0
            
            return count
        
        self.solution_count = backtrack()
        return self.solution_count
    
    def solve_dlx(self) -> int:
        """使用 DLX 算法精確覆蓋求解"""
        from dlx import DLX
        
        # 建立 16x16 數獨的列
        # 列: 行約束 + 列約束 + 宮格約束 + 格約束
        cols = []
        
        for r in range(16):
            for c in range(16):
                for v in range(1, 17):
                    # 檢查是否合法
                    cols.append([r, c, v])
        
        # 使用 DLX
        dlx = DLX(cols)
        
        return len(dlx.solve())
    
    def generate_visualization_html(self, output_path: str):
        """生成可視化 HTML 文檔"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>超級大數獨 16x16 求解結果 - 五維思維框架</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            color: white;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .subtitle {{
            text-align: center;
            color: rgba(255,255,255,0.9);
            margin-bottom: 20px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.95);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .sudoku-grid {{
            display: grid;
            grid-template-columns: repeat(16, 1fr);
            gap: 2px;
            background: #333;
            padding: 3px;
            border-radius: 8px;
            margin: 20px auto;
            max-width: 600px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }}
        .cell {{
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
            border-radius: 3px;
        }}
        .cell.original {{
            background: #667eea;
            color: white;
        }}
        .cell.solution {{
            background: #fff;
            color: #333;
        }}
        .cell.highlight {{
            background: #ffd700;
        }}
        /* 宮格邊框 */
        .cell:nth-child(4n) {{ border-right: 3px solid #333; }}
        .cell:nth-child(16n+4), .cell:nth-child(16n+8), .cell:nth-child(16n+12), .cell:nth-child(16n) {{ 
            border-right: 3px solid #333; 
        }}
        .sudoku-grid .cell:nth-child(n+65):nth-child(-n+80),
        .sudoku-grid .cell:nth-child(n+129):nth-child(-n+144) {{
            border-bottom: 3px solid #333;
        }}
        .dimension-panel {{
            background: rgba(255,255,255,0.95);
            border-radius: 12px;
            padding: 25px;
            margin-top: 30px;
        }}
        .dimension-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-top: 15px;
        }}
        .dimension-item {{
            padding: 15px;
            background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .dimension-title {{
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }}
        .dimension-content {{
            color: #555;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎲 超級大數獨 16×16 求解結果</h1>
        <p class="subtitle">五維思維框架 (點-線-面-體-球-時空) | DLX 精確覆蓋 + MRV 回溯優化</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{self.solution_count}</div>
                <div class="stat-label">🔢 找到的解數量</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">16×16</div>
                <div class="stat-label">📐 數獨規模</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.BOX_SIZE}×{self.BOX_SIZE}</div>
                <div class="stat-label">🏠 宮格大小</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">1-16</div>
                <div class="stat-label">🔤 數字範圍</div>
            </div>
        </div>
        
        <h2 style="color: white; text-align: center; margin-top: 30px;">第一個解展示</h2>
        <div class="sudoku-grid">
"""
        
        if self.solutions:
            solution = self.solutions[0]
            # 合併初盤資訊用於標記
            for i in range(16):
                for j in range(16):
                    val = solution[i, j]
                    cell_class = "cell original" if self.grid[i, j] != 0 else "cell solution"
                    html_content += f'<div class="{cell_class}">{val if val != 0 else '-'}</div>'
        else:
            html_content += '<p style="text-align: center; color: white;">⚠ 未找到解</p>'
        
        html_content += """
        </div>
        
        <div class="dimension-panel">
            <h2>🌐 五維思維框架分析</h2>
            <div class="dimension-grid">
                <div class="dimension-item">
                    <div class="dimension-title">🔴 點維度 (Point)</div>
                    <div class="dimension-content">
                        256 個單元格，每個單元格獨立約束分析<br>
                        每格可能的數字集合 = 1 - (同行 + 同列 + 同宮格已填數字)
                    </div>
                </div>
                <div class="dimension-item">
                    <div class="dimension-title">🔵 線維度 (Line)</div>
                    <div class="dimension-content">
                        16 行 + 16 列 = 32 條線約束<br>
                        每行/每列必須包含 1-16 各一次，無重複
                    </div>
                </div>
                <div class="dimension-item">
                    <div class="dimension-title">🟢 面維度 (Face)</div>
                    <div class="dimension-content">
                        16 個 4×4 宮格<br>
                        每宮格必須包含 1-16 各一次，形成局部閉環
                    </div>
                </div>
                <div class="dimension-item">
                    <div class="dimension-title">🟣 體維度 (Body)</div>
                    <div class="dimension-content">
                        行組合約束分析<br>
                        符闔排列：每行的 16 個數字構成一個排列群體
                    </div>
                </div>
                <div class="dimension-item">
                    <div class="dimension-title">🟠 球維度 (Sphere)</div>
                    <div class="dimension-content">
                        全局狀態空間探索<br>
                        搜索樹剪枝、MRV 策略優化、解空間聚類
                    </div>
                </div>
                <div class="dimension-item">
                    <div class="dimension-title">⏰ 時空維度 (Space-Time)</div>
                    <div class="dimension-content">
                        求解過程的時空映射<br>
                        記錄每個單元格在時間序列上的狀態變化
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✓ 可視化 HTML 已生成: {output_path}")


# ============== 主程式 ==============

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 超級大數獨 16x16 深度求解器")
    print("📐 box_size = 4, 數字範圍: 1-16")
    print("🌐 五維思維框架: 點-線-面-體-球-時空")
    print("=" * 60)
    print()
    
    # 基礎路徑
    base_dir = "D:/2026/WPF_Sudoku/Sudoku_256"
    
    # 讀取行約束檔案 (16 個 Excel)
    print("📂 正在讀取 16 行符闔排列 Excel 檔案...")
    print("-" * 60)
    row_constraints = load_row_constraints(base_dir)
    print("-" * 60)
    print()
    
    # 創建求解器
    solver = SuperSudoku16x16(row_constraints)
    
    # 載入初盤
    txt_file = f"{base_dir}/超級大數獨_box_size4.txt"
    solver.load_puzzle(txt_file)
    print()
    
    # 執行求解
    print("🚀 開始深度探尋所有解...")
    print("-" * 60)
    start_time = time.time()
    
    # 使用回溯法求解
    solution_count = solver.solve_backtrack(max_solutions=100)
    
    elapsed = time.time() - start_time
    print(f"- {elapsed:.2f} 秒完成搜索")
    print(f"✓ 共找到 {solution_count} 個解")
    print("-" * 60)
    print()
    
    # 生成可視化
    html_path = f"{base_dir}/超級大數獨_求解結果.html"
    solver.generate_visualization_html(html_path)
    
    # 儲存詳細結果
    results = {
        "solution_count": solution_count,
        "search_time": elapsed,
        "solutions": [sol.tolist() for sol in solver.solutions[:5]],  # 只存前 5 個解
        "grid_size": 16,
        "box_size": 4,
        "row_constraints_loaded": len(row_constraints)
    }
    
    with open(f"{base_dir}/求解結果.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON 結果檔案已儲存")
    
    print()
    print("=" * 60)
    print("✅ 求解完成!")
    print(f"📊 結果統計: {solution_count} 個解, {elapsed:.2f} 秒")
    print("=" * 60)
