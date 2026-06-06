#!/usr/bin/env python3
"""
DLX (Dancing Links) 精確覆蓋求解器 - 符闔數獨 16x16
支援符闔排列約束 + 標準數獨約束 + 已知數字
高效實現，支援多解搜索
"""

import json
import time
from collections import defaultdict
from typing import List, Dict, Tuple, Set, Optional
import sys

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"
N = 16
N_BOX = 4


class DLX:
    """Dancing Links 精確覆蓋算法"""
    
    def __init__(self, num_cols):
        self.num_cols = num_cols
        
        # 欄位節點（包括header）
        self.col_left = list(range(num_cols + 1))  # 0 is header
        self.col_right = list(range(num_cols + 1))
        self.col_up = [list(range(num_cols + 1)) for _ in range(num_cols)]  # col_up[col][row] = up node
        self.col_down = [list(range(num_cols + 1)) for _ in range(num_cols)]
        self.col_size = [0] * (num_cols + 1)
        
        # 行節點
        self.row_nodes = []  # row_nodes[row_id] = list of column indices
        
        # 初始化header環
        for i in range(num_cols + 1):
            self.col_left[i] = (i - 1) % (num_cols + 1)
            self.col_right[i] = (i + 1) % (num_cols + 1)
        
        self.solution = []
        self.solution_count = 0
        self.solutions = []
    
    def add_row(self, row_id: int, col_indices: List[int]):
        """添加一行"""
        self.row_nodes.append(col_indices)
        
        for col_idx in col_indices:
            # 插入到欄位底部
            head = col_idx
            last = self.col_up[head][head]  # 當前欄位最後的節點
            
            # 建立新節點並插入
            self.col_down[head][last] = row_id
            self.col_up[head][row_id] = last
            self.col_up[head][head] = row_id
            self.col_size[head] += 1
    
    def cover(self, col_idx: int):
        """覆蓋欄位"""
        self.col_right[self.col_left[col_idx]] = self.col_right[col_idx]
        self.col_left[self.col_right[col_idx]] = self.col_left[col_idx]
        
        # 遍历該欄所有行
        row = self.col_down[col_idx][col_idx]
        while row != col_idx:
            # 遍历該行的其他欄
            for c in self.row_nodes[row]:
                if c != col_idx:
                    # 從該欄移除此行
                    self.col_down[c][self.col_up[c][row]] = self.col_down[c][row]
                    self.col_up[c][self.col_down[c][row]] = self.col_up[c][row]
                    self.col_size[c] -= 1
            row = self.col_down[col_idx][row]
    
    def uncover(self, col_idx: int):
        """恢復欄位"""
        row = self.col_up[col_idx][col_idx]
        while row != col_idx:
            for c in reversed(self.row_nodes[row]):
                if c != col_idx:
                    self.col_size[c] += 1
                    self.col_down[c][self.col_up[c][row]] = row
                    self.col_up[c][self.col_down[c][row]] = row
            row = self.col_up[col_idx][row]
        
        self.col_right[self.col_left[col_idx]] = col_idx
        self.col_left[self.col_right[col_idx]] = col_idx
    
    def search(self, k: int = 0, limit: int = 1000) -> bool:
        """搜索解"""
        if self.solution_count >= limit:
            return True
        
        if self.col_right[0] == 0:  # header.right == header
            self.solution_count += 1
            self.solutions.append(self.solution.copy())
            return False
        
        # 選擇最小欄（啟發式）
        col = self.col_right[0]
        min_size = self.col_size[col]
        j = self.col_right[col]
        
        while j != 0:
            if self.col_size[j] < min_size:
                col = j
                min_size = self.col_size[j]
                if min_size == 0:
                    break
            j = self.col_right[j]
        
        if min_size == 0:
            return False
        
        self.cover(col)
        
        row = self.col_down[col][col]
        while row != col:
            self.solution.append(row)
            
            # 覆蓋此行涉及的所有其他欄
            for c in self.row_nodes[row]:
                if c != col:
                    self.cover(c)
            
            if self.search(k + 1, limit):
                return True
            
            # 回溯
            for c in reversed(self.row_nodes[row]):
                if c != col:
                    self.uncover(c)
            
            self.solution.pop()
            row = self.col_down[col][row]
        
        self.uncover(col)
        return False
    
    def reset(self):
        self.solution = []
        self.solution_count = 0
        self.solutions = []


def get_box_id(row: int, col: int) -> int:
    """計算宮格ID (0-15)"""
    return (row // N_BOX) * N_BOX + (col // N_BOX)


def load_data():
    """加載數據"""
    with open(f"{BASE_DIR}/sudoku_config.json") as f:
        config = json.load(f)
    
    perms = {}
    for r in range(1, 17):
        with open(f"{BASE_DIR}/A{r}_permutations.json") as f:
            perms[r] = json.load(f)
    
    return config, perms


def build_dlx_model(config, perms):
    """構建DLX精確覆蓋模型"""
    
    # 精確覆蓋約束列:
    # 0-255: cell(r,c) 必須被一個值覆蓋
    # 256-271: row(r)使用值v (每行每個值恰好一次)
    # 272-287: col(c)使用值v (每列每個值恰好一次)
    # 288-303: box(b)使用值v (每宮每個值恰好一次)
    
    CELL_CONSTRAINT = 0
    ROW_VAL_CONSTRAINT = 256
    COL_VAL_CONSTRAINT = 512
    BOX_VAL_CONSTRAINT = 768
    
    NUM_COLS = 960  # 256 + 256 + 256 + 192
    
    # 預填已知數字
    fixed = {}
    for k in config.get("known_digits", []):
        fixed[(k["row"]-1, k["col"]-1)] = k["value"]
    
    # 為每行過濾有效排列
    constrained_perms = {}
    for r in range(16):
        row_num = r + 1
        row_known = [(c, v) for (fr, fc), v in fixed.items() if fr == r]
        
        valid = []
        for perm_idx, perm in enumerate(perms.get(row_num, [])):
            ok = all(perm[c] == v for c, v in row_known)
            if ok:
                valid.append((perm_idx, perm))
        constrained_perms[r] = valid
    
    print(f"\n【排列約束過濾】")
    print("-" * 50)
    for r in range(16):
        total = len(perms.get(r+1, []))
        valid = len(constrained_perms[r])
        pct = valid/total*100 if total > 0 else 0
        print(f"  Row {r+1:2d}: {total:>7,} → {valid:>7,} ({pct:>5.1f}%)")
    
    # 檢查是否有行沒有有效排列
    empty_rows = [r for r in range(16) if len(constrained_perms[r]) == 0]
    if empty_rows:
        print(f"\n❌ 嚴重錯誤：行 {[r+1 for r in empty_rows]} 沒有有效排列！")
        print("   這表明排列約束與已知數字存在根本性衝突。")
        return None
    
    # 構建DLX
    print(f"\n【構建DLX模型】")
    print("-" * 50)
    
    dlx = DLX(NUM_COLS)
    total_rows = 0
    
    for r in range(16):
        for perm_idx, perm in constrained_perms[r]:
            row_id = total_rows
            columns = []
            
            # 1. 每個單元格(r,c)必須被覆蓋
            for c in range(16):
                columns.append(CELL_CONSTRAINT + r * 16 + c)
            
            # 2. 每行每個值恰好出現一次
            for v in range(16):  # 值0-15對應1-16
                columns.append(ROW_VAL_CONSTRAINT + r * 16 + v)
            
            # 3. 每列每個值恰好出現一次
            for c in range(16):
                v = perm[c] - 1  # 值轉0-based
                columns.append(COL_VAL_CONSTRAINT + c * 16 + v)
            
            # 4. 每宮格每個值恰好出現一次
            for c in range(16):
                v = perm[c] - 1
                box_id = get_box_id(r, c)
                columns.append(BOX_VAL_CONSTRAINT + box_id * 16 + v)
            
            dlx.add_row(row_id, columns)
            total_rows += 1
    
    print(f"  列數: {NUM_COLS}")
    print(f"  行數: {total_rows:,}")
    print(f"  平均每行約束: {len(dlx.row_nodes[0]) if dlx.row_nodes else 0} 個")
    
    return dlx, constrained_perms, fixed


def extract_grid_from_solution(dlx_solution, constrained_perms):
    """從DLX解中提取網格"""
    grid = [[0]*16 for _ in range(16)]
    
    for row_id in dlx_solution:
        # 找到對應的行和排列
        for r in range(16):
            for perm_idx, perm in constrained_perms[r]:
                # 計算row_id是否屬於此排列
                # 每行的排列數不同，需要累加計算
                pass
        
        # 簡化：遍歷所有行找到匹配的
        for r in range(16):
            for idx, (_, perm) in enumerate(constrained_perms[r]):
                # 需要計算此行在DLX中的起始位置
                pass
    
    # 重新實現：直接遍歷解中的每個行ID
    # 需要記錄每行的排列起始索引
    row_start_idx = {}
    idx = 0
    for r in range(16):
        row_start_idx[r] = idx
        idx += len(constrained_perms[r])
    
    for row_id in dlx_solution:
        for r in range(16):
            start = row_start_idx[r]
            end = row_start_idx.get(r+1, float('inf'))
            if start <= row_id < end:
                perm_idx = row_id - start
                perm = constrained_perms[r][perm_idx][1]
                for c in range(16):
                    grid[r][c] = perm[c]
                break
    
    return grid


def verify_solution(grid):
    """驗證解"""
    errors = []
    
    # 檢查行
    for r in range(16):
        values = grid[r]
        if sorted(values) != list(range(1, 17)):
            errors.append(f"行{r+1}: 不是1-16排列")
    
    # 檢查列
    for c in range(16):
        values = [grid[r][c] for r in range(16)]
        if sorted(values) != list(range(1, 17)):
            errors.append(f"列{c+1}: 不是1-16排列")
    
    # 檢查宮格
    for box_r in range(4):
        for box_c in range(4):
            values = []
            for dr in range(4):
                for dc in range(4):
                    r = box_r * 4 + dr
                    c = box_c * 4 + dc
                    values.append(grid[r][c])
            if sorted(values) != list(range(1, 17)):
                errors.append(f"宮格{box_r*4+box_c+1}: 不是1-16排列")
    
    return len(errors) == 0, errors


def main():
    print("="*70)
    print("符闔數獨 16×16 - DLX精確覆蓋求解器")
    print("="*70)
    print(f"網格尺寸: {N}×{N} = {N*N} 單元格")
    print(f"宮格尺寸: {N_BOX}×{N_BOX} = {N_BOX*N_BOX} 個宮格")
    
    config, perms = load_data()
    print(f"\n【數據加載】")
    print(f"  已知數字: {len(config.get('known_digits', []))} 個")
    total_perms = sum(len(perms.get(r, [])) for r in range(1, 17))
    print(f"  總排列數: {total_perms:,} 個")
    
    # 構建模型
    dlx, constrained_perms, fixed = build_dlx_model(config, perms)
    
    if dlx is None:
        print("\n❌ 模型構建失敗：存在約束衝突")
        # 保存失敗分析
        result = {
            "status": "infeasible",
            "reason": "constraint_conflict",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(f"{BASE_DIR}/dlx_result.json", "w") as f:
            json.dump(result, f, indent=2)
        return
    
    # 搜索
    print("\n【DLX搜索】")
    print("-" * 50)
    start = time.time()
    dlx.search(limit=1000)
    elapsed = time.time() - start
    
    print(f"  搜索時間: {elapsed:.3f} 秒")
    print(f"  找到解數: {dlx.solution_count}")
    
    result = {
        "status": "completed",
        "solution_count": dlx.solution_count,
        "search_time_sec": round(elapsed, 3),
        "solutions": []
    }
    
    if dlx.solution_count > 0:
        # 提取並驗證解
        row_start_idx = {}
        idx = 0
        for r in range(16):
            row_start_idx[r] = idx
            idx += len(constrained_perms[r])
        
        for sol_idx in range(min(5, dlx.solution_count)):
            grid = extract_grid_from_solution(dlx.solutions[sol_idx], constrained_perms)
            valid, errors = verify_solution(grid)
            
            result["solutions"].append({
                "index": sol_idx + 1,
                "valid": valid,
                "errors": errors if not valid else [],
                "grid": grid
            })
            
            if valid:
                print(f"\n✅ 解 #{sol_idx + 1} (已驗證):")
                for r in range(16):
                    print(f"    {' '.join(f'{grid[r][c]:2d}' for c in range(16))}")
            else:
                print(f"\n❌ 解 #{sol_idx + 1} (無效):")
                for e in errors:
                    print(f"    - {e}")
    
    # 保存結果
    with open(f"{BASE_DIR}/dlx_result.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n【結果保存】")
    print(f"  dlx_result.json")
    
    print("\n" + "="*70)
    if dlx.solution_count == 0:
        print("【結論】❌ 無解")
        print("符闔排列約束與數獨約束組合後無可行解。")
        print("建議檢查：")
        print("  1. 排列提取是否正確")
        print("  2. 已知數字是否與排列約束相容")
        print("  3. 是否存在單源值鎖定鏈衝突")
    else:
        print(f"【結論】✅ 找到 {dlx.solution_count} 個解")
    print("="*70)
    
    return dlx


if __name__ == "__main__":
    main()
