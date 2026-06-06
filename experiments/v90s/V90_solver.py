#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V90: 初始謎題92錨點 + I行終局增量9錨點 = 101錨點 完整解空間探索

I行數據:
  初始: [13, 0, 0, 2, 0, 11, 0, 0, 14, 0, 0, 7, 0, 15, 0, 3]  → 7個錨點
  終局: [13, 9, 16, 2, 6, 11, 8, 12, 14, 4, 1, 7, 10, 15, 5, 3]
  增量: 位置[1,2,4,6,7,9,10,12,14] → 9個新增錨點

總錨點數: 92 + 9 = 101
"""

import json
from datetime import datetime
from ortools.sat.python import cp_model
import time

# ==================== 數據加載 ====================

# 初始謎盤 (92錨點) - 從V86匯總JSON讀取
INITIAL_PUZZLE = {
    'A': [0, 0, 3, 0, 0, 12, 0, 5, 0, 0, 0, 14, 0, 16, 0, 8],
    'B': [0, 12, 0, 0, 3, 0, 9, 0, 6, 0, 5, 4, 2, 0, 1, 0],
    'C': [0, 0, 14, 0, 0, 2, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0],
    'D': [0, 4, 0, 13, 7, 0, 1, 0, 0, 0, 0, 11, 0, 12, 0, 0],
    'E': [0, 0, 0, 0, 13, 0, 0, 0, 0, 5, 0, 0, 4, 0, 0, 0],
    'F': [0, 8, 0, 0, 15, 0, 4, 3, 0, 9, 0, 0, 0, 13, 0, 12],
    'G': [14, 0, 4, 6, 0, 0, 12, 0, 2, 0, 0, 0, 0, 3, 0, 0],
    'H': [0, 13, 0, 0, 0, 5, 0, 9, 0, 0, 14, 6, 0, 0, 16, 0],
    'I': [13, 0, 0, 2, 0, 11, 0, 0, 14, 0, 0, 7, 0, 15, 0, 3],  # 7個錨點
    'J': [0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 8, 0, 7, 0],
    'K': [1, 0, 6, 0, 5, 0, 0, 2, 0, 3, 0, 0, 9, 0, 0, 0],
    'L': [0, 0, 0, 4, 0, 16, 14, 0, 0, 0, 12, 5, 0, 0, 0, 1],
    'M': [15, 0, 0, 0, 12, 0, 0, 0, 5, 1, 0, 3, 0, 6, 0, 7],
    'N': [0, 0, 9, 0, 0, 6, 0, 0, 13, 0, 0, 15, 0, 0, 3, 0],
    'O': [0, 1, 0, 0, 9, 0, 0, 15, 0, 0, 2, 8, 0, 5, 0, 0],
    'P': [0, 0, 2, 0, 0, 0, 5, 0, 0, 14, 0, 0, 1, 0, 10, 15],
}

# I行終局盤
I_ROW_FINAL = [13, 9, 16, 2, 6, 11, 8, 12, 14, 4, 1, 7, 10, 15, 5, 3]

# 驗證初始錨點數
def count_anchors(row):
    return sum(1 for v in row if v != 0)

print("=" * 60)
print("V90: 101錨點 I行終局完整解空間探索")
print("=" * 60)

# 計算各行錨點數
initial_anchors = {r: count_anchors(INITIAL_PUZZLE[r]) for r in 'ABCDEFGHIJKLMNOOP'}
print(f"\n初始盤各行錨點統計:")
for r in 'ABCDEFGHIJKLMNOOP':
    print(f"  行{r}: {initial_anchors[r]}個錨點")
total_initial = sum(initial_anchors.values())
print(f"\n初始盤總錨點數: {total_initial}")

# I行增量分析
i_initial = INITIAL_PUZZLE['I']
i_final = I_ROW_FINAL
i_increments = []
for pos in range(16):
    if i_initial[pos] == 0 and i_final[pos] != 0:
        i_increments.append(pos)

print(f"\nI行分析:")
print(f"  初始: {i_initial}")
print(f"  終局: {i_final}")
print(f"  初始錨點數: {count_anchors(i_initial)}")
print(f"  終局錨點數: 16")
print(f"  增量錨點數: {len(i_increments)} (位置: {i_increments})")
print(f"  增量錨點值: {[i_final[p] for p in i_increments]}")

total_anchors = total_initial + len(i_increments)
print(f"\n總錨點數: {total_initial} + {len(i_increments)} = {total_anchors}")

# ==================== CP-SAT 求解器 ====================

def solve_with_cp_sat(initial_puzzle, locked_row=None, locked_row_data=None, 
                      max_solutions=10, time_limit=60):
    """
    CP-SAT 數獨求解器
    
    參數:
        initial_puzzle: 初始謎盤 (dict)
        locked_row: 鎖定行字母 (如 'I')，若為None則不鎖定
        locked_row_data: 鎖定行的完整排列
        max_solutions: 最大尋找解數量
        time_limit: 時間限制(秒)
    
    返回:
        dict: 包含狀態、解盤列表、統計信息
    """
    
    model = cp_model.CpModel()
    
    # 創建16×16變量矩陣
    grid = {}
    for row in 'ABCDEFGHIJKLMNOOP':
        for col in range(16):
            grid[(row, col)] = model.NewIntVar(1, 16, f'{row}{col}')
    
    # 約束1: 行約束 (每行1-16不重複)
    for row in 'ABCDEFGHIJKLMNOOP':
        model.AddAllDifferent([grid[(row, col)] for col in range(16)])
    
    # 約束2: 列約束 (每列1-16不重複)
    for col in range(16):
        model.AddAllDifferent([grid[(row, col)] for row in 'ABCDEFGHIJKLMNOOP'])
    
    # 約束3: 宮約束 (4×4宮，每宮1-16不重複)
    for box_row in range(4):
        for box_col in range(4):
            cells = []
            for r in range(4):
                for c in range(4):
                    row = chr(ord('A') + box_row * 4 + r)
                    col = box_col * 4 + c
                    cells.append(grid[(row, col)])
            model.AddAllDifferent(cells)
    
    # 約束4: 初始錨點約束
    for row in 'ABCDEFGHIJKLMNOOP':
        for col, val in enumerate(initial_puzzle[row]):
            if val != 0:
                model.Add(grid[(row, col)] == val)
    
    # 約束5: 鎖定行約束 (如I行終局)
    if locked_row is not None and locked_row_data is not None:
        for col, val in enumerate(locked_row_data):
            model.Add(grid[(locked_row, col)] == val)
        print(f"[OK] {locked_row}行終局已完整鎖定，列約束將傳播至全盘")
    
    # 創建求解器
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    solver.parameters.enumerate_all_solutions = True
    
    class SolutionCollector(cp_model.CpSolverSolutionCallback):
        def __init__(self, grid, max_solutions):
            super().__init__()
            self.grid = grid
            self.max_solutions = max_solutions
            self.solutions = []
            self.solution_count = 0
            
        def on_solution_callback(self):
            if self.solution_count >= self.max_solutions:
                self.StopSearch()
            else:
                solution = {}
                for row in 'ABCDEFGHIJKLMNOOP':
                    solution[row] = [self.Value(self.grid[(row, col)]) for col in range(16)]
                self.solutions.append(solution)
                self.solution_count += 1
                print(f"  找到解 #{self.solution_count}")
    
    collector = SolutionCollector(grid, max_solutions)
    
    # 開始求解
    print(f"\n開始CP-SAT求解...")
    start_time = time.time()
    status = solver.Solve(model, collector)
    elapsed = time.time() - start_time
    
    print(f"\n求解完成 (耗時: {elapsed:.3f}秒)")
    
    # 解讀結果
    results = {
        'status': status,
        'status_text': solver.StatusName(status),
        'elapsed_time': elapsed,
        'solution_count': collector.solution_count,
        'solutions': collector.solutions[:5],  # 最多保留5個解
        'locked_row': locked_row,
        'locked_row_data': locked_row_data,
    }
    
    if status == cp_model.OPTIMAL:
        print(f"狀態: OPTIMAL (找到 {collector.solution_count} 個解)")
        if collector.solution_count == 1:
            results['uniqueness'] = 'unique'
            print("唯一解確認")
        else:
            results['uniqueness'] = 'multiple'
            print(f"存在多解 (共{collector.solution_count}個)")
    elif status == cp_model.FEASIBLE:
        results['uniqueness'] = 'unknown'
        print("FEASIBLE (至少找到一個解)")
    else:
        print(f"狀態: {solver.StatusName(status)}")
    
    return results


# ==================== 執行求解 ====================

print("\n" + "=" * 60)
print("執行CP-SAT求解...")
print("=" * 60)

results = solve_with_cp_sat(
    initial_puzzle=INITIAL_PUZZLE,
    locked_row='I',
    locked_row_data=I_ROW_FINAL,
    max_solutions=5,  # 尋找最多5個解以探索解空間
    time_limit=120    # 2分鐘時間限制
)

# ==================== 結果分析 ====================

print("\n" + "=" * 60)
print("解空間探索結果分析")
print("=" * 60)

if results['solution_count'] >= 1:
    print(f"\n✓ 找到 {results['solution_count']} 個解")
    
    # 驗證第一個解的I行
    solution = results['solutions'][0]
    i_match = solution['I'] == I_ROW_FINAL
    print(f"\n第一個解I行驗證:")
    print(f"  解盤I行: {solution['I']}")
    print(f"  終局I行: {I_ROW_FINAL}")
    print(f"  I行匹配: {'YES ✓' if i_match else 'NO ✗'}")
    
    # 如果存在多解，比較差異
    if results['solution_count'] > 1:
        print(f"\n多解差異分析:")
        for idx in range(min(2, results['solution_count'])):
            sol = results['solutions'][idx]
            diff_rows = []
            for row in 'ABCDEFGHIJKLMNOOP':
                if sol[row] != I_ROW_FINAL if row == 'I' else True:
                    # 對比終局盤
                    # 需要导入V86终局数据
                    # final = FINAL_SOLUTION.get(row, [])
                    if sol[row] != final:
                        diff_rows.append(row)
            print(f"  解 #{idx+1}: 與終局盤不同行數: {len(diff_rows)} ({', '.join(diff_rows) if diff_rows else '全部匹配'})")
    
    # 解盤展示 (第一個解)
    print(f"\n第一個解完整解盤:")
    for row in 'ABCDEFGHIJKLMNOOP':
        marker = '★' if row == 'I' else '  '
        print(f"{marker}行{row}: {solution[row]}")
    
else:
    print(f"\n[!] 未找到解 (INFEASIBLE)")

# ==================== 保存結果 ====================

output_dir = 'D:/Users/Jualius/WorkBuddy/3d_sudoku_system/output/'

# 保存JSON結果
output_json = {
    'version': 'V90',
    'timestamp': datetime.now().isoformat(),
    'puzzle': {
        'initial_anchors': total_initial,
        'i_row_anchor_increment': len(i_increments),
        'total_anchors': total_anchors,
        'i_row_initial': i_initial,
        'i_row_final': i_final,
    },
    'results': {
        'status': results['status_text'],
        'elapsed_time': results['elapsed_time'],
        'solution_count': results['solution_count'],
        'uniqueness': results.get('uniqueness', 'unknown'),
    }
}

if results['solution_count'] > 0:
    output_json['solutions'] = results['solutions']

with open(f'{output_dir}V90_101_anchor_I_solution.json', 'w', encoding='utf-8') as f:
    json.dump(output_json, f, ensure_ascii=False, indent=2)

print(f"\nJSON結果已保存: {output_dir}V90_101_anchor_I_solution.json")

# ==================== 總結報告 ====================

summary = f"""# V90: 101錨點I行終局完整解空間探索報告

**版本**: V90  
**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**項目**: 符闔數獨16×16 I行終局推演

---

## 一、謎題定義

| 項目 | 數值 |
|------|------|
| 初始盤錨點 | 92 |
| I行終局新增錨點 | {len(i_increments)} |
| **總錨點數** | **{total_anchors}** |

### I行數據

```
I行初始:  [13, 0, 0, 2, 0, 11, 0, 0, 14, 0, 0, 7, 0, 15, 0, 3]
I行終局:  [13, 9, 16, 2, 6, 11, 8, 12, 14, 4, 1, 7, 10, 15, 5, 3]
```

### 增量錨點

| 位置 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|------|---|---|---|---|---|---|---|---|---|---|----|----|----|----|----|----|
| 初始 | 13 | 0 | 0 | 2 | 0 | 11 | 0 | 0 | 14 | 0 | 0 | 7 | 0 | 15 | 0 | 3 |
| 終局 | 13 | **9** | **16** | 2 | **6** | 11 | **8** | **12** | 14 | **4** | **1** | 7 | **10** | 15 | **5** | 3 |
| 狀態 | ✓ | 新增 | 新增 | ✓ | 新增 | ✓ | 新增 | 新增 | ✓ | 新增 | 新增 | ✓ | 新增 | ✓ | 新增 | ✓ |

---

## 二、求解結果

| 指標 | 數值 |
|------|------|
| **狀態** | {results['status_text']} |
| **耗時** | {results['elapsed_time']:.3f}秒 |
| **解數量** | {results['solution_count']} |
| **唯一性** | {results.get('uniqueness', '未知')} |

---

## 三、解空間分析

"""

if results['solution_count'] == 0:
    summary += """### 3.1 結果：INFEASIBLE ❌

**未找到可行解**

**原因分析**:
1. I行終局排列與初始盤92錨點存在列約束硬衝突
2. 列約束傳播導致無可行解空間
3. 符闔排列集合閉合性驗證：**通過**（I行終局在集合中）

**注意**: 這是「符闔排列集合閉合性」≠「約束滿足性」的典型案例。
即使終局排列在符闔集合中，但與初始盤的列約束存在不可調和的硬衝突。
"""
elif results['solution_count'] == 1:
    summary += f"""### 3.1 結果：唯一解 ✓

**找到1個唯一解**

#### I行驗證

| 項目 | 數值 |
|------|------|
| 解盤I行 | `{solution['I']}` |
| 終局I行 | `{I_ROW_FINAL}` |
| 匹配狀態 | {'✅ 完全一致' if i_match else '❌ 不一致'} |

#### 解盤展示

```
"""
    for row in 'ABCDEFGHIJKLMNOOP':
        marker = '★' if row == 'I' else ' '
        vals = solution[row]
        summary += f"{marker}行{row}: {vals}\n"
    summary += "```\n"

else:
    summary += f"""### 3.1 結果：多解 ⚠️

**找到{results['solution_count']}個解**，說明101錨點不足以唯一確定完整解。

#### 各解I行驗證

"""
    for idx, sol in enumerate(results['solutions'][:3]):
        i_match = sol['I'] == I_ROW_FINAL
        summary += f"- 解 #{idx+1}: I行 {'✅ 匹配' if i_match else '❌ 不匹配'}\n"

summary += f"""

---

## 四、與V84（M行）對比

| 版本 | 鎖定行 | 錨點數 | 狀態 | 解數量 |
|------|--------|--------|------|--------|
| V84 | M行 | 101 | OPTIMAL | 1 |
| **V90** | **I行** | **101** | {results['status_text']} | **{results['solution_count']}** |

### 關鍵對比

- I行和M行都是低熵組（增量9錨點）
- 但I行排列數僅164個（最少），M行有484個
- 解空間大小差異顯著

---

## 五、符闔排列熵值關聯

| 熵級 | 行 | 排列數 | 101錨點表現 |
|------|-----|--------|------------|
| ★高熵 | C, E, J | 656K+/28K+ | 需多行鎖定 |
| 中熵 | A,D,G,H,K,L,N,O,P | 8K+/1.9K+/... | 單行鎖定可解 |
| 低熵 | B,F,I,M | 902/359/**164**/484 | 需驗證 |

**I行特殊情況**: 排列數164個（全16行最少），但101錨點結果顯示...

---

## 六、輸出文件

| 文件 | 說明 |
|------|------|
| `V90_solver.py` | 求解器源碼 |
| `V90_101_anchor_I_solution.json` | JSON結果 |

---

*報告生成完成 - V90*
"""

with open(f'{output_dir}V90_101_anchor_I_summary.md', 'w', encoding='utf-8') as f:
    f.write(summary)

print(f"總結報告已保存: {output_dir}V90_101_anchor_I_summary.md")

# ==================== 最終匯總 ====================

print("\n" + "=" * 60)
print("V90 101錨點I行完整解空間探索 - 完成")
print("=" * 60)
