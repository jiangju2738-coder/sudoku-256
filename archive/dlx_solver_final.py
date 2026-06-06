#!/usr/bin/env python3
"""
DLX (Dancing Links) 精確覆蓋求解器 - 符闔數獨 16x16 (最終版)
使用92個已知數字 + 符闔排列約束
"""

import json
import time
from datetime import datetime

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"
N = 16
N_BOX = 4


class DLX:
    """Dancing Links精確覆蓋算法 - 高效實現"""
    
    def __init__(self, num_cols):
        self.num_cols = num_cols
        self.UL = [[0] * (num_cols + 1) for _ in range(num_cols + 1)]
        self.DR = [[0] * (num_cols + 1) for _ in range(num_cols + 1)]
        self.L = [0] * (num_cols + 1)
        self.R = [0] * (num_cols + 1)
        self.U = [0] * (num_cols + 1)
        self.D = [0] * (num_cols + 1)
        self.Col = [0] * (num_cols + 1)
        self.Row = [0] * (num_cols + 1)
        
        self.S = [0] * (num_cols + 1)  # 每欄節點數
        
        self.idx = num_cols + 1  # 節點索引
        self.solution = []
        self.solution_count = 0
        self.solutions = []
        
        # 初始化header環
        for i in range(num_cols + 1):
            self.L[i] = i - 1
            self.R[i] = i + 1
            self.U[i] = i
            self.D[i] = i
        
        self.L[0] = num_cols
        self.R[num_cols] = 0
    
    def add_row(self, row_id: int, col_indices: list):
        """添加一行"""
        first = self.idx
        for c in col_indices:
            self.Row[self.idx] = row_id
            self.Col[self.idx] = c
            
            # 插入到欄c底部
            self.D[self.idx] = c
            self.U[self.idx] = self.U[c]
            self.D[self.U[c]] = self.idx
            self.U[c] = self.idx
            
            self.S[c] += 1
            self.idx += 1
        
        # 行內環
        for i in range(len(col_indices)):
            self.L[first + i] = first + i - 1
            self.R[first + i] = first + i + 1
        
        self.L[first] = first + len(col_indices) - 1
        self.R[first + len(col_indices) - 1] = first
    
    def cover(self, c):
        """覆蓋欄c"""
        self.L[self.R[c]] = self.L[c]
        self.R[self.L[c]] = self.R[c]
        
        i = self.D[c]
        while i != c:
            j = self.R[i]
            while j != i:
                self.U[self.D[j]] = self.U[j]
                self.D[self.U[j]] = self.D[j]
                self.S[self.Col[j]] -= 1
                j = self.R[j]
            i = self.D[i]
    
    def uncover(self, c):
        """恢復欄c"""
        i = self.U[c]
        while i != c:
            j = self.L[i]
            while j != i:
                self.S[self.Col[j]] += 1
                self.U[self.D[j]] = j
                self.D[self.U[j]] = j
                j = self.L[j]
            i = self.U[i]
        
        self.L[self.R[c]] = c
        self.R[self.L[c]] = c
    
    def search(self, k=0, limit=1000):
        """搜索"""
        if self.solution_count >= limit:
            return True
        
        if self.R[0] == 0:
            self.solution_count += 1
            self.solutions.append(self.solution.copy())
            return False
        
        # 選擇最小欄
        c = self.R[0]
        min_s = self.S[c]
        j = self.R[c]
        while j != 0:
            if self.S[j] < min_s:
                c = j
                min_s = self.S[j]
                if min_s == 0:
                    break
            j = self.R[j]
        
        if min_s == 0:
            return False
        
        self.cover(c)
        
        i = self.D[c]
        while i != c:
            self.solution.append(self.Row[i])
            
            j = self.R[i]
            while j != i:
                self.cover(self.Col[j])
                j = self.R[j]
            
            if self.search(k + 1, limit):
                return True
            
            j = self.L[i]
            while j != i:
                self.uncover(self.Col[j])
                j = self.L[j]
            
            self.solution.pop()
            i = self.D[i]
        
        self.uncover(c)
        return False


def get_box_id(row, col):
    return (row // N_BOX) * N_BOX + (col // N_BOX)


def load_data():
    with open(f"{BASE_DIR}/sudoku_config.json") as f:
        config = json.load(f)
    
    perms = {}
    for r in range(1, 17):
        with open(f"{BASE_DIR}/A{r}_permutations.json") as f:
            perms[r] = json.load(f)
    
    return config, perms


def build_and_solve():
    print("="*70)
    print("符闔數獨 16×16 - DLX精確覆蓋求解器")
    print("="*70)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    config, perms = load_data()
    known_count = len(config.get("known_digits", []))
    total_perms = sum(len(perms.get(r, [])) for r in range(1, 17))
    
    print(f"\n【數據統計】")
    print(f"  已知數字: {known_count} 個")
    print(f"  總排列數: {total_perms:,} 個")
    
    # 預填已知數字
    fixed = {}
    for k in config.get("known_digits", []):
        fixed[(k["row"]-1, k["col"]-1)] = k["value"]
    
    # 過濾每行有效排列
    constrained_perms = {}
    for r in range(16):
        row_num = r + 1
        row_known = [(c, v) for (fr, fc), v in fixed.items() if fr == r]
        
        valid = []
        for perm in perms.get(row_num, []):
            ok = all(perm[c] == v for c, v in row_known)
            if ok:
                valid.append(perm)
        constrained_perms[r] = valid
    
    print(f"\n【排列過濾】")
    for r in range(16):
        total = len(perms.get(r+1, []))
        valid = len(constrained_perms[r])
        print(f"  Row {r+1:2d}: {total:>7,} → {valid:>7,}")
    
    empty_rows = [r for r in range(16) if len(constrained_perms[r]) == 0]
    if empty_rows:
        print(f"\n❌ 行 {[r+1 for r in empty_rows]} 無有效排列 - 約束衝突！")
        return {"status": "infeasible", "reason": "empty_perm_rows"}
    
    # 構建DLX
    CELL = 0
    ROW_VAL = 256
    COL_VAL = 512
    BOX_VAL = 768
    NUM_COLS = 960
    
    print(f"\n【構建DLX模型】")
    print(f"  列數: {NUM_COLS}")
    
    dlx = DLX(NUM_COLS)
    total_rows = 0
    row_start = {}
    
    for r in range(16):
        row_start[r] = total_rows
        for perm in constrained_perms[r]:
            columns = []
            
            # 1. 每個單元格(r,c)
            for c in range(16):
                columns.append(CELL + r * 16 + c)
            
            # 2. 每行每值
            for v in range(16):
                columns.append(ROW_VAL + r * 16 + v)
            
            # 3. 每列每值
            for c in range(16):
                v = perm[c] - 1
                columns.append(COL_VAL + c * 16 + v)
            
            # 4. 每宮每值
            for c in range(16):
                v = perm[c] - 1
                box_id = get_box_id(r, c)
                columns.append(BOX_VAL + box_id * 16 + v)
            
            dlx.add_row(total_rows, columns)
            total_rows += 1
    
    print(f"  行數: {total_rows:,}")
    
    # 搜索
    print(f"\n【DLX搜索】")
    start = time.time()
    dlx.search(limit=1000)
    elapsed = time.time() - start
    
    print(f"  時間: {elapsed:.3f} 秒")
    print(f"  解數: {dlx.solution_count}")
    
    result = {
        "status": "solved" if dlx.solution_count > 0 else "infeasible",
        "solution_count": dlx.solution_count,
        "search_time_sec": round(elapsed, 3),
        "timestamp": datetime.now().isoformat()
    }
    
    if dlx.solution_count > 0:
        # 提取解
        solutions = []
        for sol_idx in range(min(3, dlx.solution_count)):
            grid = [[0]*16 for _ in range(16)]
            
            for row_id in dlx.solutions[sol_idx]:
                for r in range(16):
                    start_idx = row_start[r]
                    end_idx = row_start.get(r+1, total_rows)
                    if start_idx <= row_id < end_idx:
                        perm_idx = row_id - start_idx
                        perm = constrained_perms[r][perm_idx]
                        for c in range(16):
                            grid[r][c] = perm[c]
                        break
            
            # 驗證
            valid = True
            errors = []
            
            for r in range(16):
                if sorted(grid[r]) != list(range(1, 17)):
                    valid = False
                    errors.append(f"行{r+1}不是排列")
            
            for c in range(16):
                vals = [grid[r][c] for r in range(16)]
                if sorted(vals) != list(range(1, 17)):
                    valid = False
                    errors.append(f"列{c+1}不是排列")
            
            for br in range(4):
                for bc in range(4):
                    vals = []
                    for dr in range(4):
                        for dc in range(4):
                            vals.append(grid[br*4+dr][bc*4+dc])
                    if sorted(vals) != list(range(1, 17)):
                        valid = False
                        errors.append(f"宮格{br*4+bc+1}不是排列")
            
            solutions.append({
                "index": sol_idx + 1,
                "valid": valid,
                "errors": errors,
                "grid": grid
            })
            
            if valid:
                print(f"\n✅ 解 #{sol_idx+1}:")
                for r in range(16):
                    print(f"   {' '.join(f'{grid[r][c]:2d}' for c in range(16))}")
            else:
                print(f"\n❌ 解 #{sol_idx+1} 無效: {errors}")
        
        result["solutions"] = solutions
    
    with open(f"{BASE_DIR}/dlx_result.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ 結果保存: dlx_result.json")
    print("\n" + "="*70)
    
    if dlx.solution_count == 0:
        print("【結論】❌ 無解 - 約束系統不可滿足")
    else:
        print(f"【結論】✅ 找到 {dlx.solution_count} 個解")
    
    return result


if __name__ == "__main__":
    build_and_solve()
