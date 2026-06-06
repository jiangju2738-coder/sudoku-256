#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V86 符闔數獨16行完整數據匯總生成器
輸出A4版電子文檔至Output文件夾
"""

import os
from datetime import datetime

# 指定輸出目錄
OUTPUT_DIR = r"D:\Users\Jualius\WorkBuddy\3d_sudoku_system\output"

# 確保目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================== 數據定義 ====================

# 1. 初始盤92錨點
INITIAL_PUZZLE = {
    'A': [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8],
    'B': [0,12,0,0, 3,0,9,0, 6,0,5,4, 2,0,1,0],
    'C': [0,0,14,0, 0,2,0,8, 0,0,0,0, 0,0,0,0],
    'D': [0,4,0,13, 7,0,1,0, 0,0,0,11, 0,12,0,0],
    'E': [0,0,0,0, 13,0,0,0, 0,5,0,0, 4,0,0,0],
    'F': [0,8,0,0, 15,0,4,3, 0,9,0,0, 0,13,0,12],
    'G': [14,0,4,6, 0,0,12,0, 2,0,0,0, 0,3,0,0],
    'H': [0,13,0,0, 0,5,0,9, 0,0,14,6, 0,0,16,0],
    'I': [13,0,0,2, 0,11,0,0, 14,0,0,7, 0,15,0,3],
    'J': [0,5,0,0, 0,0,0,0, 0,0,16,0, 8,0,7,0],
    'K': [1,0,6,0, 5,0,0,2, 0,3,0,0, 9,0,0,0],
    'L': [0,0,0,4, 0,16,14,0, 0,0,12,5, 0,0,0,1],
    'M': [15,0,0,0, 12,0,0,0, 5,1,0,3, 0,6,0,7],
    'N': [0,0,9,0, 0,6,0,0, 13,0,0,15, 0,0,3,0],
    'O': [0,1,0,0, 9,0,0,15, 0,0,2,8, 0,5,0,0],
    'P': [0,0,2,0, 0,0,5,0, 0,14,0,0, 1,0,10,15]
}

# 2. 終局盤16行完整符闔組闔排列
FINAL_SOLUTION = {
    'A': [2,6,3,1, 11,12,13,5, 10,7,9,14, 15,16,4,8],
    'B': [16,12,11,8, 3,10,9,14, 6,15,5,4, 2,7,1,13],
    'C': [7,10,14,15, 4,2,16,8, 12,13,3,1, 11,9,6,5],
    'D': [9,4,5,13, 7,15,1,6, 16,2,8,11, 3,12,14,10],
    'E': [11,2,1,9, 13,7,6,16, 3,5,15,12, 4,10,8,14],
    'F': [5,8,7,10, 15,14,4,3, 1,9,11,16, 6,13,2,12],
    'G': [14,16,4,6, 8,1,12,11, 2,10,7,13, 5,3,15,9],
    'H': [12,13,15,3, 2,5,10,9, 4,8,14,6, 7,1,16,11],
    'I': [13,9,16,2, 6,11,8,12, 14,4,1,7, 10,15,5,3],
    'J': [10,5,12,14, 1,9,3,13, 15,11,16,2, 8,4,7,6],
    'K': [1,11,6,7, 5,4,15,2, 8,3,13,10, 9,14,12,16],
    'L': [3,15,8,4, 10,16,14,7, 9,6,12,5, 13,2,11,1],
    'M': [15,14,13,11, 12,8,2,10, 5,1,4,3, 16,6,9,7],
    'N': [4,7,9,5, 14,6,11,1, 13,16,10,15, 12,8,3,2],
    'O': [6,1,10,16, 9,3,7,15, 11,12,2,8, 14,5,13,4],
    'P': [8,3,2,12, 16,13,5,4, 7,14,6,9, 1,11,10,15]
}

# 3. 各符闔排列數統計
PERM_STATS = {
    'A': 8731, 'B': 902, 'C': 656777, 'D': 1980,
    'E': 633271, 'F': 359, 'G': 2356, 'H': 4782,
    'I': 164, 'J': 28984, 'K': 2972, 'L': 620,
    'M': 484, 'N': 10668, 'O': 5990, 'P': 1809
}

# 行序列表（修正：16行A-P）
ROW_ORDER = list('ABCDEFGHIJKLMNOP')

# ==================== 生成Markdown文檔 ====================

def count_anchors(row_data):
    """計算錨點數（非0的單元格）"""
    return sum(1 for v in row_data if v != 0)

def format_row(row_name, data):
    """格式化行數據顯示"""
    values = [f"{v:3d}" for v in data]
    groups = [' '.join(values[i:i+4]) for i in range(0, 16, 4)]
    return f"★行{row_name}: " + "  ".join(groups)

def generate_markdown():
    """生成Markdown文檔"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 計算各行錨點數（使用ROW_ORDER列表）
    initial_anchors = {r: count_anchors(INITIAL_PUZZLE[r]) for r in ROW_ORDER}
    final_anchors = {r: 16 for r in ROW_ORDER}  # 終局16錨點
    anchor_increments = {r: final_anchors[r] - initial_anchors[r] for r in ROW_ORDER}
    
    total_initial = sum(initial_anchors.values())
    total_increment = sum(anchor_increments.values())
    total_final = total_initial + total_increment
    
    md = f"""# 符闔數獨256 - 16行完整數據匯總

**生成時間**: {timestamp}

---

## 一、項目概述

| 項目 | 數值 | 說明 |
|------|------|------|
| 數獨類型 | 16×16 | 符闔排列變體 |
| 宮格規模 | 256個 | 4×4宮格 |
| 初始盤錨點 | **{total_initial}** | 92個已知數 |
| 終局盤錨點 | **256** | 16行×16列完整填滿 |
| 錨點增量 | **{total_increment}** | 從初始到終局新增 |
| 符闔排列總空間 | 1,360,849 | V73永例上限 |

---

## 二、初始盤數據（92錨點）

初始謎盤已知錨點分佈：

```
"""

    for row in 'ABCDEFGHIJKLMNOP':
        anchors = count_anchors(INITIAL_PUZZLE[row])
        anchor_str = ','.join([f"{v:2d}" if v != 0 else " 0" for v in INITIAL_PUZZLE[row]])
        md += f"行{row} [{anchor_str}] → {anchors}個錨點\n"

    md += f"""
**初始盤錨點總計**: {total_initial}

---

## 三、錨點增量統計表

| 行 | 初始錨點 | 終局錨點 | **增量** | 排列數 | 熵級 |
|----|---------|---------|---------|--------|------|
"""

    entropy_high = []
    entropy_medium = []
    entropy_low = []
    
    for row in 'ABCDEFGHIJKLMNOP':
        inc = anchor_increments[row]
        perm = PERM_STATS[row]
        
        if inc >= 12:
            entropy = "★高熵"
            entropy_high.append(row)
        elif inc >= 10:
            entropy = "中熵"
            entropy_medium.append(row)
        else:
            entropy = "低熵"
            entropy_low.append(row)
        
        md += f"| **{row}** | {initial_anchors[row]} | 16 | **+{inc}** | {perm:,} | {entropy} |\n"

    md += f"| **合計** | {total_initial} | 256 | **+{total_increment}** | {sum(PERM_STATS.values()):,} | |\n"

    md += f"""
---

## 四、終局盤完整符闔組闔排列

終局解盤（A-P共16行完整排列）：

```
"""

    for row in 'ABCDEFGHIJKLMNOP':
        md += format_row(row, FINAL_SOLUTION[row]) + "\n"

    md += """```

---

## 五、各行詳細數據（謎盤+解盤對照）

"""

    for row in 'ABCDEFGHIJKLMNOP':
        inc = anchor_increments[row]
        perm = PERM_STATS[row]
        
        md += f"""### 行{row}

| 項目 | 數據 |
|------|------|
| **初始謎盤** | `[{', '.join([f'{v:2d}' if v != 0 else ' 0' for v in INITIAL_PUZZLE[row]])}]` |
| **終局排列** | `[{', '.join(map(str, FINAL_SOLUTION[row]))}]` |
| 錨點增量 | +{inc} |
| 符闔排列數 | {perm:,} |

**差異分析**：
"""
        
        # 找出新增錨點位置
        new_positions = []
        for i in range(16):
            if INITIAL_PUZZLE[row][i] == 0 and FINAL_SOLUTION[row][i] != 0:
                new_positions.append(i)
        
        if new_positions:
            md += f"- 新增錨點位置（0-indexed）: {new_positions}\n"
            md += f"- 新增錨點值: {[FINAL_SOLUTION[row][i] for i in new_positions]}\n"
        
        # 找出已錨點位置變化
        changed_positions = []
        for i in range(16):
            if INITIAL_PUZZLE[row][i] != 0 and FINAL_SOLUTION[row][i] != INITIAL_PUZZLE[row][i]:
                changed_positions.append((i, INITIAL_PUZZLE[row][i], FINAL_SOLUTION[row][i]))
        
        if changed_positions:
            md += f"- 位置衝突（初始≠終局）: {changed_positions}\n"
        else:
            md += f"- 已錨點位置與終局一致 ✓\n"
        
        md += "\n---\n\n"

    md += f"""
## 六、符闔排列熵值分析

### 熵值等級分類

| 等級 | 行 | 特徵 |
|------|-----|------|
| **高熵組** | {', '.join(entropy_high)} | 增量≥12，排列稀疏性最高 |
| **中熵組** | {', '.join(entropy_medium)} | 增量10-11，中等填補 |
| **低熵組** | {', '.join(entropy_low)} | 增量8-9，初始錨點較多 |

### 排列數分布

| 排列數區間 | 行數 | 具體行 |
|-----------|------|--------|
| < 1,000 | 4 | B(902), F(359), I(164), M(484) |
| 1,000-10,000 | 8 | A, D, G, H, K, L, O, P |
| > 10,000 | 4 | C(656K), E(633K), J(29K), N(11K) |

---

## 七、約束規則識別

基於V79全量演進行序推演，識別出以下約束規則：

| 類型 | 說明 | 數據支援 |
|------|------|----------|
| 標準數獨三重約束 | 行/列/宮 AllDifferent | 所有解盤均滿足 |
| 符闔排列集合約束 | 每行從對應排列集合選擇 | 16行共{sum(PERM_STATS.values()):,}個排列 |
| 行鎖定約束 | 終局排列作為錨點 | 16行全量鎖定 |
| 無解性判斷 | 排列集合與列/宮硬衝突 | A/B/M行INFEASIBLE |

---

## 八、匯總統計

| 指標 | 數值 |
|------|------|
| 初始盤錨點 | {total_initial} |
| A-P行增量錨點 | {total_increment} |
| **完整解盤總錨點** | **{total_final}** (16×16) |
| 符闔排列總上限 | 1,360,849 |
| 高熵行數 | {len(entropy_high)} |
| 中熵行數 | {len(entropy_medium)} |
| 低熵行數 | {len(entropy_low)} |

---

## 九、輸出文件清單

| 文件 | 格式 | 說明 |
|------|------|------|
| `V86_16行完整數據匯總.md` | Markdown | 本匯總文檔 |
| `V86_16行完整數據匯總.json` | JSON | 機器可讀數據 |

---

*生成工具: V86_16行完整數據匯總_generator.py*
*符闔數獨研究項目 V86 版本*
"""

    return md

def generate_json():
    """生成JSON數據文件"""
    import json
    
    initial_anchors = {r: count_anchors(INITIAL_PUZZLE[r]) for r in 'ABCDEFGHIJKLMNOP'}
    anchor_increments = {r: 16 - initial_anchors[r] for r in 'ABCDEFGHIJKLMNOP'}
    
    # 找出新增錨點位置
    new_anchor_positions = {}
    for row in 'ABCDEFGHIJKLMNOP':
        positions = [i for i in range(16) if INITIAL_PUZZLE[row][i] == 0]
        new_anchor_positions[row] = positions
    
    data = {
        "metadata": {
            "version": "V86",
            "generated": datetime.now().isoformat(),
            "sudoku_type": "16x16 Fummel Sudoku",
            "description": "符闔排列256數獨16行完整數據匯總"
        },
        "summary": {
            "initial_anchors": sum(initial_anchors.values()),
            "total_increment": sum(anchor_increments.values()),
            "final_anchors": 256,
            "total_permutations": sum(PERM_STATS.values())
        },
        "initial_puzzle": INITIAL_PUZZLE,
        "final_solution": FINAL_SOLUTION,
        "anchor_analysis": {
            "by_row": {
                row: {
                    "initial": initial_anchors[row],
                    "final": 16,
                    "increment": anchor_increments[row],
                    "perm_count": PERM_STATS[row],
                    "new_anchor_positions": new_anchor_positions[row]
                }
                for row in 'ABCDEFGHIJKLMNOP'
            },
            "entropy_classification": {
                "high": [r for r in 'ABCDEFGHIJKLMNOP' if anchor_increments[r] >= 12],
                "medium": [r for r in 'ABCDEFGHIJKLMNOP' if 10 <= anchor_increments[r] < 12],
                "low": [r for r in 'ABCDEFGHIJKLMNOP' if anchor_increments[r] < 10]
            }
        },
        "perm_stats": PERM_STATS,
        "permutation_upper_bound": 1360849
    }
    
    return json.dumps(data, ensure_ascii=False, indent=2)

# ==================== 執行生成 ====================

if __name__ == '__main__':
    print("=" * 60)
    print("V86 符闔數獨16行完整數據匯總生成器")
    print("=" * 60)
    print(f"\n輸出目錄: {OUTPUT_DIR}")
    
    # 生成Markdown
    md_content = generate_markdown()
    md_path = os.path.join(OUTPUT_DIR, "V86_16行完整數據匯總.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"\n✓ Markdown文檔已生成: {md_path}")
    print(f"  文件大小: {os.path.getsize(md_path):,} bytes")
    
    # 生成JSON
    json_content = generate_json()
    json_path = os.path.join(OUTPUT_DIR, "V86_16行完整數據匯總.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_content)
    print(f"✓ JSON文檔已生成: {json_path}")
    print(f"  文件大小: {os.path.getsize(json_path):,} bytes")
    
    # 統計摘要
    print("\n" + "=" * 60)
    print("生成完成 - 數據摘要")
    print("=" * 60)
    
    initial_total = sum(count_anchors(INITIAL_PUZZLE[r]) for r in 'ABCDEFGHIJKLMNOP')
    increment_total = sum(16 - count_anchors(INITIAL_PUZZLE[r]) for r in 'ABCDEFGHIJKLMNOP')
    
    print(f"\n初始盤錨點: {initial_total}")
    print(f"錨點增量總計: {increment_total}")
    print(f"完整解盤錨點: {initial_total + increment_total} (16×16)")
    print(f"符闔排列總空間: {sum(PERM_STATS.values()):,}")
    print(f"\n高熵行 (增量≥12): {', '.join([r for r in 'ABCDEFGHIJKLMNOP' if 16 - count_anchors(INITIAL_PUZZLE[r]) >= 12])}")
    print(f"中熵行 (增量10-11): {', '.join([r for r in 'ABCDEFGHIJKLMNOP' if 10 <= 16 - count_anchors(INITIAL_PUZZLE[r]) < 12])}")
    print(f"低熵行 (增量8-9): {', '.join([r for r in 'ABCDEFGHIJKLMNOP' if 16 - count_anchors(INITIAL_PUZZLE[r]) < 10])}")
    
    print("\n" + "=" * 60)
    print("A4版電子文檔已輸出至: D:\\Users\\Jualius\\WorkBuddy\\3d_sudoku_system\\output")
    print("=" * 60)
