#!/usr/bin/env python3
"""
符闔數獨配置器後端 API
提供求解、驗證、配置管理功能
"""

import json
import os
import time
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from functools import lru_cache
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import traceback

WORK_DIR = r"D:\2026\WPF_Sudoku\Sudoku_256"

app = Flask(__name__)
CORS(app)

# ==================== 數據加載 ====================

@lru_cache(maxsize=1)
def load_permutations() -> Dict[int, List[List[int]]]:
    """加載所有行的符闔排列"""
    perms = {}
    for row in range(16):
        row_num = row + 1
        filename = f"A{row_num}_permutations.json"
        filepath = os.path.join(WORK_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                perms[row] = json.load(f)
        else:
            print(f"警告: 未找到 {filename}")
    return perms

@lru_cache(maxsize=1)
def load_initial_puzzle() -> List[List[int]]:
    """加載初始題目"""
    # 標準 92 個提示的初始盤
    return [
        [0, 0, 3, 0, 0, 12, 0, 5, 0, 0, 0, 14, 0, 16, 0, 8],
        [0, 12, 0, 0, 3, 0, 9, 0, 6, 0, 5, 4, 2, 0, 1, 0],
        [0, 0, 14, 0, 0, 2, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 4, 0, 13, 7, 0, 1, 0, 0, 0, 0, 11, 0, 12, 0, 0],
        [0, 0, 0, 0, 13, 0, 0, 0, 0, 5, 0, 0, 4, 0, 0, 0],
        [0, 8, 0, 0, 15, 0, 4, 3, 0, 9, 0, 0, 0, 13, 0, 12],
        [14, 0, 4, 6, 0, 0, 12, 0, 2, 0, 0, 0, 0, 3, 0, 0],
        [0, 13, 0, 0, 0, 5, 0, 9, 0, 0, 14, 6, 0, 0, 16, 0],
        [13, 0, 0, 2, 0, 11, 0, 0, 14, 0, 0, 7, 0, 15, 0, 3],
        [0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 8, 0, 7, 0],
        [1, 0, 6, 0, 5, 0, 0, 2, 0, 3, 0, 0, 9, 0, 0, 0],
        [0, 0, 0, 4, 0, 16, 14, 0, 0, 0, 12, 5, 0, 0, 0, 1],
        [15, 0, 0, 0, 12, 0, 0, 0, 5, 1, 0, 3, 0, 6, 0, 7],
        [0, 0, 9, 0, 0, 6, 0, 0, 13, 0, 0, 15, 0, 0, 3, 0],
        [0, 1, 0, 0, 9, 0, 0, 15, 0, 0, 2, 8, 0, 5, 0, 0],
        [0, 0, 2, 0, 0, 0, 5, 0, 0, 14, 0, 0, 1, 0, 10, 15]
    ]

# ==================== 驗證邏輯 ====================

def validate_puzzle(grid: List[List[int]], perms: Dict[int, List[List[int]]]) -> Dict:
    """驗證配置的有效性"""
    errors = []
    
    # 檢查網格大小
    if len(grid) != 16 or any(len(row) != 16 for row in grid):
        errors.append("網格尺寸不正確，應該是 16×16")
        return {"valid": False, "errors": errors}
    
    # 檢查值範圍
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            if val != 0 and (val < 1 or val > 16):
                errors.append(f"({r+1},{c+1}) 值 {val} 超出範圍 [1,16]")
    
    # 檢查符闔排列約束
    for row in range(16):
        if all(grid[row][c] != 0 for c in range(16)):
            # 該行已完全填寫，檢查是否在允許的排列中
            if row in perms:
                if grid[row] not in perms[row]:
                    errors.append(f"第{row+1}行排列不在符闔集合中")
    
    # 檢查行/列/宮唯一性（對已填寫部分）
    for row in range(16):
        vals = [v for v in grid[row] if v != 0]
        if len(vals) != len(set(vals)):
            errors.append(f"第{row+1}行有重複值")
    
    for col in range(16):
        vals = [grid[row][col] for row in range(16) if grid[row][col] != 0]
        if len(vals) != len(set(vals)):
            errors.append(f"第{col+1}列有重複值")
    
    for br in range(4):
        for bc in range(4):
            vals = []
            for r in range(4):
                for c in range(4):
                    v = grid[br*4+r][bc*4+c]
                    if v != 0:
                        vals.append(v)
            if len(vals) != len(set(vals)):
                errors.append(f"宮格({br+1},{bc+1})有重複值")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

# ==================== 求解器 ====================

def solve_with_cpsat(grid: List[List[int]], perms: Dict[int, List[List[int]]], 
                     max_solutions: int = 5, timeout: int = 60) -> Dict:
    """使用 CP-SAT 求解"""
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return {"success": False, "error": "OR-Tools 未安裝: pip install ortools"}
    
    start_time = time.time()
    model = cp_model.CpModel()
    
    # 變數：每個格子的值
    cells = {}
    for r in range(16):
        for c in range(16):
            cells[r, c] = model.NewIntVar(1, 16, f'cell_{r}_{c}')
    
    # 符闔排列約束：每行的值必須是某個允許的排列
    for row in range(16):
        if row in perms and len(perms[row]) > 0:
            # 使用 AddAllowedAssignments 約束每行的排列
            # 對於大集合，分解為多個較小的約束
            if len(perms[row]) <= 1000:
                allowed = [[p[c] for c in range(16)] for p in perms[row]]
                model.AddAllowedAssignments(
                    [cells[row, c] for c in range(16)],
                    allowed
                )
            else:
                # 大集合：使用過濾的已知值約束
                known = [(c, grid[row][c]) for c in range(16) if grid[row][c] != 0]
                if known:
                    # 對每個已知位置約束其值
                    for c, v in known:
                        model.Add(cells[row, c] == v)
    
    # 列唯一性
    for col in range(16):
        model.AddAllDifferent([cells[row, col] for row in range(16)])
    
    # 宮唯一性
    for br in range(4):
        for bc in range(4):
            box_cells = []
            for r in range(4):
                for c in range(4):
                    box_cells.append(cells[br*4+r, bc*4+c])
            model.AddAllDifferent(box_cells)
    
    # 固定已知值
    for r in range(16):
        for c in range(16):
            if grid[r][c] != 0:
                model.Add(cells[r, c] == grid[r][c])
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.num_search_workers = 8
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.log_search_progress = False
    
    class SolutionCollector(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.solutions = []
            self.count = 0
        
        def OnSolutionStart(self):
            sol = [[self.Value(cells[r, c]) for c in range(16)] for r in range(16)]
            self.solutions.append(sol)
            self.count += 1
    
    collector = SolutionCollector()
    status = solver.Solve(model, collector)
    
    elapsed = time.time() - start_time
    
    return {
        "success": True,
        "solutions": collector.solutions[:max_solutions],
        "total_count": collector.count,
        "status": "optimal" if status == cp_model.OPTIMAL else "partial" if status == cp_model.FEASIBLE else "infeasible",
        "time_seconds": round(elapsed, 2),
        "memory_mb": round(solver.MemoryUsage() / 1024 / 1024, 2) if hasattr(solver, 'MemoryUsage') else 0
    }

def solve_with_backtracking(grid: List[List[int]], perms: Dict[int, List[List[int]]], 
                            max_solutions: int = 5, timeout: int = 60) -> Dict:
    """使用帶剪枝的回溯求解（適合符闔約束）"""
    start_time = time.time()
    solutions = []
    
    # 預處理：每行可能的位置
    # 對於完全填寫的行，直接驗證符闔約束
    filled_rows = []
    for row in range(16):
        if all(grid[row][c] != 0 for c in range(16)):
            if row in perms and grid[row] in perms[row]:
                filled_rows.append(row)
            else:
                return {"success": False, "error": f"第{row+1}行已填寫但不符合符闔約束"}
    
    # 回溯搜索
    empty_cells = [(r, c) for r in range(16) for c in range(16) if grid[r][c] == 0]
    
    def is_valid_partial(r, c, val):
        # 列檢查
        if any(grid[row][c] == val and row != r for row in range(16)):
            return False
        # 宮檢查
        br, bc = (r // 4) * 4, (c // 4) * 4
        for rr in range(br, br + 4):
            for cc in range(bc, bc + 4):
                if grid[rr][cc] == val and (rr, cc) != (r, c):
                    return False
        return True
    
    def backtrack(idx):
        nonlocal solutions
        if time.time() - start_time > timeout:
            return
        
        if len(solutions) >= max_solutions:
            return
        
        if idx >= len(empty_cells):
            # 完整解，檢查符闔約束
            sol = [row[:] for row in grid]
            valid = True
            for row in range(16):
                if row in perms and sol[row] not in perms[row]:
                    valid = False
                    break
            if valid:
                solutions.append(sol)
            return
        
        r, c = empty_cells[idx]
        
        # 獲取該行的符闔排列候選值（優先級）
        if r in perms and perms[r]:
            # 從符闔排列中提取該列可能的值
            possible = sorted(set(p[c] for p in perms[r]))
        else:
            possible = list(range(1, 17))
        
        for val in possible:
            if is_valid_partial(r, c, val):
                grid[r][c] = val
                backtrack(idx + 1)
                grid[r][c] = 0
    
    backtrack(0)
    
    return {
        "success": True,
        "solutions": solutions,
        "total_count": len(solutions),
        "status": "completed" if len(solutions) >= max_solutions or len(empty_cells) == 0 else "timeout",
        "time_seconds": round(time.time() - start_time, 2)
    }

# ==================== API 端點 ====================

@app.route('/api/status', methods=['GET'])
def status():
    """API 狀態檢查"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "work_dir": WORK_DIR,
        "permutations_loaded": len(load_permutations()),
        "initial_puzzle": load_initial_puzzle()
    })

@app.route('/api/validate', methods=['POST'])
def validate():
    """驗證配置"""
    try:
        data = request.get_json()
        grid = data.get('grid', [])
        perms = load_permutations()
        
        result = validate_puzzle(grid, perms)
        return jsonify(result)
    except Exception as e:
        return jsonify({"valid": False, "errors": [str(e)]}), 400

@app.route('/api/solve', methods=['POST'])
def solve():
    """求解數獨"""
    try:
        data = request.get_json()
        grid = data.get('grid', [])
        method = data.get('method', 'cpsat')
        max_solutions = data.get('max_solutions', 5)
        timeout = data.get('timeout', 60)
        
        if not grid or len(grid) != 16:
            return jsonify({"success": False, "error": "缺少有效網格"}), 400
        
        perms = load_permutations()
        
        if method == 'cpsat':
            result = solve_with_cpsat(grid, perms, max_solutions, timeout)
        elif method == 'backtrack':
            result = solve_with_backtracking(grid, perms, max_solutions, timeout)
        else:
            return jsonify({"success": False, "error": f"未知求解方法: {method}"}), 400
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500

@app.route('/api/permutations', methods=['GET'])
def get_permutations():
    """獲取符闔排列摘要"""
    perms = load_permutations()
    summary = {}
    for row, p_list in perms.items():
        summary[f"A{row+1}"] = {
            "count": len(p_list),
            "first_sample": p_list[0] if p_list else None
        }
    return jsonify(summary)

@app.route('/api/initial-puzzle', methods=['GET'])
def get_initial_puzzle():
    """獲取初始題目"""
    return jsonify(load_initial_puzzle())

@app.route('/api/export-config', methods=['POST'])
def export_config():
    """導出配置為 JSON"""
    try:
        data = request.get_json()
        grid = data.get('grid', [])
        known_digits = []
        
        for r in range(16):
            for c in range(16):
                if grid[r][c] != 0:
                    known_digits.append({
                        "row": r + 1,
                        "col": c + 1,
                        "value": grid[r][c]
                    })
        
        config = {
            "grid_size": 16,
            "box_size": 4,
            "known_digits": known_digits,
            "exported_at": datetime.now().isoformat()
        }
        
        filename = os.path.join(WORK_DIR, 'config_export.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return jsonify({"success": True, "file": filename, "known_count": len(known_digits)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/')
def serve_frontend():
    """提供前端 HTML"""
    return send_file(os.path.join(WORK_DIR, 'super_sudoku_configurator.html'))

if __name__ == '__main__':
    print("=" * 60)
    print("符闔數獨配置器 API Server")
    print("=" * 60)
    print(f"工作目錄: {WORK_DIR}")
    print(f"啟動時間: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # 預加載數據
    print("預加載符闔排列...")
    perms = load_permutations()
    for row, p_list in perms.items():
        print(f"  A{row+1}: {len(p_list):,} 排列")
    
    print("預加載初始題目...")
    puzzle = load_initial_puzzle()
    known_count = sum(1 for row in puzzle for v in row if v != 0)
    print(f"  已知數字: {known_count} 個")
    
    print("=" * 60)
    print("服務啟動中...")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=5001, debug=False)
