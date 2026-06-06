#!/usr/bin/env python3
"""
16×16符闔數獨精確解數量驗證 - 第四版（修復初始化問題）
"""

import json
import time
import os
import sys

# 使用絕對路徑
BASE_DIR = 'D:/2026/WPF_Sudoku/Sudoku_256'
N = 16  # 16×16
N2 = N * N  # 256個格子
N_BOX = N // 4  # 每宮4×4

class Sudoku256Verifier:
    """16×16符闔數獨驗證器 - 精確計數"""
    
    def __init__(self, known_digits, row_perms):
        """
        known_digits: [(row, col, value), ...] 0-indexed
        row_perms: [row][perm_idx][col] = value (1-16)
        """
        self.known_digits = known_digits
        self.row_perms = row_perms
        self.max_solutions = 10
        
        # 已知數字映射
        self.known_map = {}
        for r, c, v in known_digits:
            self.known_map[(r, c)] = v
            
        # 每行已使用的符闔排列索引
        self.row_selections = [-1] * N
        
        # 列和宮的數字使用情況
        self.col_used = [[False] * N for _ in range(N)]
        self.box_used = [[False] * N for _ in range(N)]
        
        # 結果
        self.solutions = []
        self.nodes_explored = 0
        self.start_time = None
        
    def get_box_id(self, row, col):
        """獲取宮編號"""
        return (row // N_BOX) * N_BOX + (col // N_BOX)
    
    def initialize_constraints(self):
        """初始化列和宮約束"""
        for r in range(N):
            for c in range(N):
                if (r, c) in self.known_map:
                    v = self.known_map[(r, c)] - 1
                    # 注意：這裡標記所有已知數字，但在check_perm_valid中會排除當前行
                    self.col_used[c][v] = True
                    box_id = self.get_box_id(r, c)
                    self.box_used[box_id][v] = True
                    
        # 調試：打印約束統計
        print(f"  初始化約束完成:")
        for r in range(N):
            known_count = sum(1 for c in range(N) if (r, c) in self.known_map)
            print(f"    第{r+1}行已知數字: {known_count}個")
                    
    def check_perm_valid(self, row, perm_idx):
        """檢查排列是否符合已知數字和約束"""
        perm = self.row_perms[row][perm_idx]
        
        for col, val in enumerate(perm):
            # 檢查是否符合該行已知數字
            if (row, col) in self.known_map:
                if self.known_map[(row, col)] != val:
                    return False
            
            # 檢查列約束 - 排除當前行的已知數字
            if (row, col) not in self.known_map:  # 如果不是當前行已知數字
                if self.col_used[col][val - 1]:
                    return False
            
            # 檢查宮約束 - 排除當前行的已知數字
            if (row, col) not in self.known_map:  # 如果不是當前行已知數字
                box_id = self.get_box_id(row, col)
                if self.box_used[box_id][val - 1]:
                    return False
                
        return True
    
    def apply_perm(self, row, perm_idx):
        """應用排列，更新約束"""
        perm = self.row_perms[row][perm_idx]
        
        for col, val in enumerate(perm):
            self.col_used[col][val - 1] = True
            box_id = self.get_box_id(row, col)
            self.box_used[box_id][val - 1] = True
            
        self.row_selections[row] = perm_idx
    
    def revert_perm(self, row, perm_idx):
        """回滾排列，恢復約束"""
        perm = self.row_perms[row][perm_idx]
        
        for col, val in enumerate(perm):
            self.col_used[col][val - 1] = False
            box_id = self.get_box_id(row, col)
            self.box_used[box_id][val - 1] = False
            
        self.row_selections[row] = -1
    
    def build_solution_grid(self):
        """從選擇的排列構建解矩陣"""
        grid = [[0] * N for _ in range(N)]
        
        for row in range(N):
            perm_idx = self.row_selections[row]
            if perm_idx >= 0:
                perm = self.row_perms[row][perm_idx]
                for col, val in enumerate(perm):
                    grid[row][col] = val
                    
        return grid
    
    def solve(self):
        """搜索所有解，返回找到的解數量"""
        self.solutions = []
        self.nodes_explored = 0
        self.start_time = time.time()
        
        print(f"  初始化完成，檢查第一行可行排列...")
        
        # 檢查第一行有多少可行排列
        valid_count = sum(1 for pi in range(len(self.row_perms[0])) 
                         if self.check_perm_valid(0, pi))
        print(f"  第一行可行排列數: {valid_count}")
        
        # 如果第一行沒有可行排列，直接返回
        if valid_count == 0:
            print("  ⚠ 第一行無可行排列，提前終止")
            return 0
        
        # 開始搜索
        print("  開始DFS搜索...")
        self._search(0)
        
        return len(self.solutions)
    
    def _search(self, row):
        """深度優先搜索"""
        if len(self.solutions) >= self.max_solutions:
            return
        
        if time.time() - self.start_time > 300:  # 5分鐘限制
            print("  ⏱ 達到時間限制")
            return
        
        if row == N:
            # 找到一個完整解
            self.solutions.append(self.build_solution_grid())
            print(f"  ✓ 解 #{len(self.solutions)} 找到！")
            return
        
        # 獲取當前行的可行排列
        valid_perms = []
        for perm_idx in range(len(self.row_perms[row])):
            if self.check_perm_valid(row, perm_idx):
                valid_perms.append(perm_idx)
        
        if not valid_perms:
            return  # 無可行排列，回溯
        
        # 打印進度
        if row % 2 == 0:
            print(f"  行 {row+1}: {len(valid_perms)} 個可行排列")
        
        for perm_idx in valid_perms:
            self.nodes_explored += 1
            
            # 應用選擇
            self.apply_perm(row, perm_idx)
            
            # 繼續搜索下一行
            self._search(row + 1)
            
            # 回滾
            self.revert_perm(row, perm_idx)
            
            if len(self.solutions) >= self.max_solutions:
                return
    
    def get_statistics(self):
        """獲取統計資訊"""
        return {
            "solutions_found": len(self.solutions),
            "nodes_explored": self.nodes_explored,
            "time_seconds": time.time() - self.start_time,
            "max_solutions_limit": self.max_solutions
        }


# =============================================================================
# 主程序
# =============================================================================

def load_permutations():
    """載入所有符闔排列"""
    perms = []
    
    for i in range(1, 17):
        filepath = os.path.join(BASE_DIR, f'A{i}_permutations.json')
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    perms.append(data)
                    print(f"  ✓ A{i}: {len(data):,} 個排列")
                else:
                    print(f"  ⚠ A{i}: 非列表格式")
                    perms.append([])
        except Exception as e:
            print(f"  ✗ A{i}: 讀取錯誤 - {e}")
            perms.append([])
            
    return perms


def load_known_digits():
    """載入已知數字"""
    filepath = os.path.join(BASE_DIR, 'sudoku_config.json')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        known = []
        for d in data.get('known_digits', []):
            # 轉換為 0-indexed
            known.append((d['row'] - 1, d['col'] - 1, d['value']))
        
        print(f"  載入 {len(known)} 個已知數字")
        return known
        
    except Exception as e:
        print(f"  ✗ 載入失敗: {e}")
        return []


def validate_solution(grid, known_map, row_perms):
    """驗證解的有效性"""
    errors = []
    
    # 1. 檢查已知數字
    for (r, c), val in known_map.items():
        if grid[r][c] != val:
            errors.append(f"已知數字衝突: grid[{r}][{c}]={grid[r][c]}, 應為 {val}")
    
    # 2. 檢查符闔排列
    for r in range(N):
        row_vals = tuple(grid[r])
        if row_vals not in tuple(tuple(p) for p in row_perms[r]):
            errors.append(f"行 {r+1} 不符合符闔排列")
    
    # 3. 檢查列約束
    for c in range(N):
        col_vals = [grid[r][c] for r in range(N)]
        if len(set(col_vals)) != N:
            errors.append(f"列 {c+1} 有重複數字")
    
    # 4. 檢查宮約束
    for b in range(N):
        box_vals = []
        for r in range(N_BOX):
            for c in range(N_BOX):
                gr = (b // N_BOX) * N_BOX + r
                gc = (b % N_BOX) * N_BOX + c
                box_vals.append(grid[gr][gc])
        if len(set(box_vals)) != N:
            errors.append(f"宮 {b+1} 有重複數字")
    
    return len(errors) == 0, errors


def main():
    print("=" * 70)
    print("  16×16 符闔數獨精確解數量驗證")
    print("=" * 70)
    print(f"\n工作目錄: {BASE_DIR}")
    
    t0 = time.time()
    
    # 1. 載入符闔排列
    print("\n[1/3] 載入符闔排列...")
    row_perms = load_permutations()
    
    # 2. 載入已知數字
    print("\n[2/3] 載入已知數字...")
    known_digits = load_known_digits()
    known_map = {(r, c): v for r, c, v in known_digits}
    
    # 3. 執行驗證
    print("\n[3/3] 執行精確解數量驗證...")
    print(f"      行數: {len(row_perms)}")
    print(f"      已知數字: {len(known_digits)} 個")
    print(f"      最多查找: 10 個解")
    
    t1 = time.time()
    print(f"      載入時間: {t1 - t0:.2f} 秒")
    
    # 創建驗證器
    verifier = Sudoku256Verifier(known_digits, row_perms)
    
    # 執行搜索
    print("\n開始搜索...")
    num_solutions = verifier.solve()
    
    t2 = time.time()
    stats = verifier.get_statistics()
    
    # 輸出結果
    print("\n" + "=" * 70)
    print("  驗證結果")
    print("=" * 70)
    
    print(f"\n解數量: {num_solutions}")
    
    if num_solutions == 0:
        print("\n❌ 無解！")
        print("   可能原因：符闔排列與已知數字存在衝突")
    elif num_solutions == 1:
        print("\n✅ 找到唯一解！")
        
        # 驗證解
        grid = verifier.solutions[0]
        valid, errors = validate_solution(grid, known_map, row_perms)
        
        if valid:
            print("   解驗證通過 ✓")
        else:
            print("   ⚠ 解驗證失敗:")
            for e in errors[:5]:
                print(f"     - {e}")
    else:
        print(f"\n⚠ 找到 {num_solutions} 個解（多解）")
        print("   解空間非稀疏，需要更多分析")
        
        # 分析解的差異
        if num_solutions >= 2:
            diff_count = 0
            for r in range(N):
                for c in range(N):
                    if verifier.solutions[0][r][c] != verifier.solutions[1][r][c]:
                        diff_count += 1
            print(f"   解1與解2差異: {diff_count}/{N2} 個格子 ({diff_count/N2*100:.1f}%)")
    
    # 搜索統計
    print(f"\n搜索統計:")
    print(f"  探索節點: {stats['nodes_explored']:,}")
    print(f"  搜索時間: {stats['time_seconds']:.2f} 秒")
    
    # 保存結果
    output = {
        "total_solutions": num_solutions,
        "statistics": stats,
        "solutions": verifier.solutions[:3] if verifier.solutions else []
    }
    
    output_path = os.path.join(BASE_DIR, 'solution_count_result.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n結果已保存到: {output_path}")
    
    t3 = time.time()
    print(f"\n總耗時: {t3 - t0:.2f} 秒")
    
    return num_solutions


if __name__ == '__main__':
    result = main()
    sys.exit(0)
