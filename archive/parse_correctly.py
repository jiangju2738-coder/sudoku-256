#!/usr/bin/env python3
"""
直接解析超級大數獨網格 - 從已知的16行矩陣數據提取
"""

import json
import re
from collections import defaultdict
from datetime import datetime

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"

def main():
    print("="*70)
    print("符闔數獨配置文件解析報告（最終修正版）")
    print("="*70)
    print(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 從sudoku_config.json獲取正確的已知數字
    with open(f"{BASE_DIR}/sudoku_config.json") as f:
        config = json.load(f)
    
    known_digits = config.get("known_digits", [])
    
    # 建構16x16網格
    grid = [[0]*16 for _ in range(16)]
    for k in known_digits:
        r, c, v = k["row"]-1, k["col"]-1, k["value"]
        grid[r][c] = v
    
    print("\n" + "="*70)
    print("第一部分：數獨網格數據（16x16）")
    print("="*70)
    
    print(f"\n✅ 網格尺寸: 16×16 = 256單元格")
    print(f"   宮格尺寸: 4×4 = 16個宮格")
    
    print(f"\n已知數字: {len(known_digits)} 個")
    print(f"空單元格: {256 - len(known_digits)} 個")
    print(f"填滿率: {len(known_digits)/256*100:.1f}%")
    
    print("\n完整網格 (0=空白):")
    print("-" * 70)
    for r in range(16):
        line = []
        for c in range(16):
            if grid[r][c] != 0:
                line.append(f"{grid[r][c]:2d}")
            else:
                line.append(" .")
        print(f"  行{r+1:2d}: {' '.join(line)}")
    
    print("\n" + "="*70)
    print("第二部分：256個宮格位置分佈")
    print("="*70)
    
    col_letters = {i+1: chr(ord('B')+i) for i in range(16)}
    
    print("\n座標系統:")
    print("  行: A1-A16 (第1-16行)")
    print("  列: B-Q (第1-16列)")
    print("  位置標記: [行號][列號]")
    print("  例如: 1B=第1行第1列(單元格1), 16Q=第16行第16列(單元格256)")
    
    print("\n256個單元格分佈（按行分組）:")
    print("-" * 70)
    for r in range(1, 17):
        start = (r-1)*16 + 1
        end = r*16
        known_in_row = [k for k in known_digits if k["row"] == r]
        print(f"第{r:2d}行 (單元格 {start:3d}-{end:3d}): "
              f"已知 {len(known_in_row):2d} 個, 空白 {16-len(known_in_row):2d} 個")
    
    print("\n" + "="*70)
    print("第三部分：符闔排列約束")
    print("="*70)
    
    print("\n每行符闔排列文件:")
    for r in range(1, 17):
        print(f"  第{r:2d}行 → A{r}第{r}行符闔排列.xlsx")
    
    print(f"\n總排列數: 1,111,494 個（從各行排列集合計）")
    print(f"每行約束: 必須從其排列集中選取恰好1個排列")
    
    # 加載各行排列數
    perms_count = {}
    for r in range(1, 17):
        with open(f"{BASE_DIR}/A{r}_permutations.json") as f:
            perms_count[r] = len(json.load(f))
    
    print("\n各行排列數分佈:")
    for r in range(1, 17):
        print(f"  Row {r:2d}: {perms_count[r]:>8,} 個排列")
    
    print("\n" + "="*70)
    print("第四部分：數值分佈統計")
    print("="*70)
    
    val_distribution = defaultdict(list)
    for k in known_digits:
        val_distribution[k["value"]].append(f"A{k['row']}")
    
    print("\n各數值出現的行分佈:")
    print("-" * 70)
    for val in range(1, 17):
        rows = val_distribution[val]
        unique_rows = sorted(set(rows))
        row_str = " ".join(unique_rows)
        print(f"  數值 {val:2d}: 出現在 {row_str} ({len(rows)} 次)")
    
    print("\n" + "="*70)
    print("第五部分：座標映射詳細列表")
    print("="*70)
    
    print("\n所有92個已知數字座標:")
    print("-" * 70)
    for k in sorted(known_digits, key=lambda x: (x["row"], x["col"])):
        coord = f"{k['row']}{col_letters[k['col']]}"
        cell_num = (k['row'] - 1) * 16 + k['col']
        box_r = (k['row'] - 1) // 4
        box_c = (k['col'] - 1) // 4
        box_id = box_r * 4 + box_c + 1
        print(f"  {coord:4s} (單元格{cell_num:3d}, 宮格{box_id:2d}): "
              f"第{k['row']:2d}行第{k['col']:2d}列 = 值 {k['value']:2d}")
    
    print("\n" + "="*70)
    print("第六部分：約束衝突檢測")
    print("="*70)
    
    # 檢查行衝突
    row_conflicts = []
    for r in range(16):
        values = [grid[r][c] for c in range(16) if grid[r][c] != 0]
        if len(values) != len(set(values)):
            dup = [v for v in set(values) if values.count(v) > 1]
            row_conflicts.append((r+1, dup))
    
    # 檢查列衝突
    col_conflicts = []
    for c in range(16):
        values = [grid[r][c] for r in range(16) if grid[r][c] != 0]
        if len(values) != len(set(values)):
            dup = [v for v in set(values) if values.count(v) > 1]
            col_conflicts.append((c+1, dup))
    
    # 檢查宮格衝突
    box_conflicts = []
    for box_r in range(4):
        for box_c in range(4):
            box_id = box_r * 4 + box_c
            values = []
            for dr in range(4):
                for dc in range(4):
                    r = box_r * 4 + dr
                    c = box_c * 4 + dc
                    if grid[r][c] != 0:
                        values.append(grid[r][c])
            if len(values) != len(set(values)):
                dup = [v for v in set(values) if values.count(v) > 1]
                box_conflicts.append((box_id+1, dup))
    
    print("\n行內衝突檢測:")
    if row_conflicts:
        for r, dup in row_conflicts:
            print(f"  ❌ 第{r}行: 數值 {dup} 重複")
    else:
        print("  ✅ 所有行無內部衝突")
    
    print("\n列內衝突檢測:")
    if col_conflicts:
        for c, dup in col_conflicts:
            print(f"  ❌ 第{c}列: 數值 {dup} 重複")
    else:
        print("  ✅ 所有列無內部衝突")
    
    print("\n宮格衝突檢測:")
    if box_conflicts:
        for bid, dup in box_conflicts:
            print(f"  ❌ 宮格{bid}: 數值 {dup} 重複")
    else:
        print("  ✅ 所有宮格無內部衝突")
    
    print("\n" + "="*70)
    print("第七部分：總結")
    print("="*70)
    
    result = {
        "parse_time": datetime.now().isoformat(),
        "grid": grid,
        "grid_size": 16,
        "box_size": 4,
        "total_cells": 256,
        "known_digits_count": len(known_digits),
        "empty_cells": 256 - len(known_digits),
        "fill_rate": round(len(known_digits)/256*100, 1),
        "known_digits": known_digits,
        "row_distribution": {str(r): len([k for k in known_digits if k["row"]==r]) for r in range(1, 17)},
        "col_distribution": {str(c): len([k for k in known_digits if k["col"]==c]) for c in range(1, 17)},
        "value_distribution": {str(v): len(val_distribution[v]) for v in range(1, 17)},
        "perms_per_row": perms_count,
        "total_permutations": sum(perms_count.values()),
        "conflicts": {
            "row": row_conflicts,
            "col": col_conflicts,
            "box": box_conflicts
        },
        "coordinate_system": {
            "rows": {f"A{i}": i for i in range(1, 17)},
            "columns": {chr(ord('B')+i): i+1 for i in range(16)},
            "cell_formula": "cell_num = (row-1)*16 + col"
        }
    }
    
    with open(f"{BASE_DIR}/box_size4_full_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"""
【解析完成總結】

📊 網格資訊:
  - 尺寸: 16×16 (256單元格)
  - 宮格: 4×4 (16個宮格)
  - 已知數字: {len(known_digits)} 個
  - 空白單元格: {256-len(known_digits)} 個
  - 填滿率: {len(known_digits)/256*100:.1f}%

📍 座標系統:
  - 行: A1-A16 (對應第1-16行)
  - 列: B-Q (對應第1-16列)
  - 單元格編號: 1B=單元格1, ..., 16Q=單元格256
  - 公式: cell_num = (row-1)×16 + col

🔢 符闔排列約束:
  - 總排列數: {sum(perms_count.values()):,} 個
  - 每行從其排列集中選取1個排列
  - 每行排列數分布差異顯著 (見上表)

✅ 約束衝突檢測:
  - 行衝突: {len(row_conflicts)} 個
  - 列衝突: {len(col_conflicts)} 個
  - 宮格衝突: {len(box_conflicts)} 個
  {'所有已知數字均無內部衝突 ✓' if not any([row_conflicts, col_conflicts, box_conflicts]) else '⚠️ 存在衝突'}

📄 輸出檔案:
  - box_size4_full_analysis.json (完整分析數據)

""")
    
    return result


if __name__ == "__main__":
    result = main()
