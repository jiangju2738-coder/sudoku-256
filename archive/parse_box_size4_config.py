#!/usr/bin/env python3
"""
解析 超級大數獨_box_size4.txt 配置文件
完整分析92個已知數字、符闔排列約束、座標系統
"""

import json
from collections import defaultdict
from datetime import datetime

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"


def parse_config_file():
    """解析配置文件"""
    print("="*70)
    print("符闔數獨配置文件解析報告")
    print("="*70)
    print(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 讀取配置文件
    with open(f"{BASE_DIR}/超級大數獨_box_size4.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    print("\n" + "="*70)
    print("第一部分：數獨網格數據（16x16）")
    print("="*70)
    
    # 解析網格數據（第3-21行）
    grid_lines = content.split('\n')[2:22]  # 行號3-21
    grid = []
    for i, line in enumerate(grid_lines):
        # 提取數字序列
        numbers = []
        current = ""
        for ch in line:
            if ch.isdigit():
                current += ch
            else:
                if current:
                    numbers.append(int(current))
                    current = ""
        if current:
            numbers.append(int(current))
        
        if len(numbers) == 16:
            grid.append(numbers)
        elif len(numbers) > 0:
            print(f"  行 {i+1}: 解析到 {len(numbers)} 個數字")
    
    print(f"\n網格尺寸: {len(grid)} 行 × {len(grid[0]) if grid else 0} 列")
    
    # 統計已知數字
    known_digits = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != 0:
                known_digits.append({
                    "row": r + 1,
                    "col": c + 1,
                    "value": grid[r][c]
                })
    
    print(f"\n已知數字總數: {len(known_digits)} 個")
    print(f"空單元格: {256 - len(known_digits)} 個")
    print(f"填滿率: {len(known_digits)/256*100:.1f}%")
    
    print("\n" + "="*70)
    print("第二部分：256個宮格位置分佈")
    print("="*70)
    
    # 解析256個宮格分布說明
    print("\n座標系統說明:")
    print("  - 行號: A1-A16 對應第1-16行")
    print("  - 列號: B-Q 對應第1-16列")
    print("  - 位置標記: [行號][列號] 例如 1B=第1行第1列")
    
    # 解析每個位置的詳細數據
    grid_details = {}
    lines = content.split('\n')
    current_row = None
    current_values = {}
    
    for i, line in enumerate(lines):
        # 匹配行標識
        if line.startswith(f"第{str(current_row)}行") and current_row is not None:
            # 保存上一行的數據
            if current_values:
                grid_details[current_row] = current_values
            current_values = {}
            current_row = None
        
        # 匹配位置數據
        match_pattern = f"A: {current_row}" if current_row else None
        if f"A: {current_row}" in line:
            continue
        
        # 匹配具體單元格: 例如 "1: A1 1B = 0"
        for cell_idx in range(1, 17):
            search_str = f"{cell_idx}: A{current_row} {current_row}B" if current_row else None
        
    # 手動解析256個位置的已知數字
    print("\n256個單元格分佈（按行分組，每行16個）:")
    print("-" * 70)
    
    for row_idx in range(1, 17):
        row_start = (row_idx - 1) * 16 + 1
        row_end = row_idx * 16
        known_in_row = [k for k in known_digits if k["row"] == row_idx]
        
        row_data = [0] * 16
        for k in known_digits:
            row_data[k["col"] - 1] = k["value"]
        
        filled_count = len(known_in_row)
        print(f"\n第{row_idx:2d}行 (單元格 {row_start:3d}-{row_end:3d}): "
              f"已知 {filled_count:2d} 個, 空白 {16-filled_count:2d} 個")
        
        # 顯示本行數據
        display = []
        for c in range(16):
            if row_data[c] != 0:
                display.append(f"{row_data[c]:2d}")
            else:
                display.append(" .")
        print(f"    {' '.join(display)}")
    
    print("\n" + "="*70)
    print("第三部分：符闔排列約束")
    print("="*70)
    
    # 分析每行的符闔排列文件引用
    print("\n符闔排列文件引用:")
    for row_idx in range(1, 17):
        print(f"  第{row_idx:2d}行: A{row_idx}第{row_idx}行符闔排列.xlsx")
    
    print(f"\n總計: 16個符闔排列文件，每個文件定義該行可選的排列集合")
    print(f"每行需從其排列集中選取1個排列填入16個單元格")
    
    print("\n" + "="*70)
    print("第四部分：數值分佈統計")
    print("="*70)
    
    # 統計每個數值的分佈
    val_distribution = defaultdict(list)
    for k in known_digits:
        val_distribution[k["value"]].append(f"A{k['row']}")
    
    print("\n各數值出現的行分佈:")
    print("-" * 70)
    for val in range(1, 17):
        rows = val_distribution[val]
        row_str = " ".join(sorted(set(rows)))
        print(f"  數值 {val:2d}: 出現在行 {row_str} ({len(rows)} 次)")
    
    print("\n" + "="*70)
    print("第五部分：宮格約束驗證")
    print("="*70)
    
    # 驗證4x4宮格約束
    print("\n宮格劃分（4x4=16個宮格）:")
    for box_r in range(4):
        for box_c in range(4):
            box_id = box_r * 4 + box_c
            cells = []
            for dr in range(4):
                for dc in range(4):
                    r = box_r * 4 + dr
                    c = box_c * 4 + dc
                    if r < len(grid) and c < len(grid[0]):
                        val = grid[r][c]
                        if val != 0:
                            cells.append(f"{val}")
                        else:
                            cells.append(".")
            print(f"  宮格 {box_id+1:2d} (行{box_r*4+1}-{box_r*4+4}, 列{box_c*4+1}-{box_c*4+4}): "
                  f"{', '.join(cells)}")
    
    print("\n" + "="*70)
    print("第六部分：約束衝突檢測")
    print("="*70)
    
    # 檢測行內衝突
    print("\n行內衝突檢測:")
    row_conflicts = []
    for r in range(16):
        values = [grid[r][c] for c in range(16) if grid[r][c] != 0]
        if len(values) != len(set(values)):
            conflicts = [v for v in set(values) if values.count(v) > 1]
            row_conflicts.append((r+1, conflicts))
    
    if row_conflicts:
        for r, conflicts in row_conflicts:
            print(f"  ❌ 第{r}行: 數值 {conflicts} 重複出現")
    else:
        print("  ✅ 所有行無衝突")
    
    # 檢測列內衝突
    print("\n列內衝突檢測:")
    col_conflicts = []
    for c in range(16):
        values = [grid[r][c] for r in range(16) if grid[r][c] != 0]
        if len(values) != len(set(values)):
            conflicts = [v for v in set(values) if values.count(v) > 1]
            col_conflicts.append((c+1, conflicts))
    
    if col_conflicts:
        for c, conflicts in col_conflicts:
            print(f"  ❌ 第{c}列: 數值 {conflicts} 重複出現")
    else:
        print("  ✅ 所有列無衝突")
    
    # 檢測宮格衝突
    print("\n宮格衝突檢測:")
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
                conflicts = [v for v in set(values) if values.count(v) > 1]
                box_conflicts.append((box_id+1, conflicts))
    
    if box_conflicts:
        for box_id, conflicts in box_conflicts:
            print(f"  ❌ 宮格 {box_id}: 數值 {conflicts} 重複出現")
    else:
        print("  ✅ 所有宮格無衝突")
    
    print("\n" + "="*70)
    print("第七部分：已知數字座標映射")
    print("="*70)
    
    print("\n座標對照表:")
    print("  行: A1=第1行, A2=第2行, ..., A16=第16行")
    print("  列: B=第1列, C=第2列, ..., Q=第16列")
    print("\n所有已知數字座標列表:")
    for k in sorted(known_digits, key=lambda x: (x["row"], x["col"])):
        col_letter = chr(ord('B') + k["col"] - 1)
        coord = f"{k['row']}{col_letter}"
        print(f"  {coord:4s} = 第{k['row']:2d}行第{k['col']:2d}列 = 值 {k['value']:2d}")
    
    print("\n" + "="*70)
    print("總結")
    print("="*70)
    
    # 保存解析結果
    result = {
        "parse_time": datetime.now().isoformat(),
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
        "conflicts": {
            "row": row_conflicts,
            "col": col_conflicts,
            "box": box_conflicts
        },
        "coordinate_system": {
            "rows": {f"A{i}": i for i in range(1, 17)},
            "columns": {chr(ord('B')+i): i+1 for i in range(16)}
        }
    }
    
    with open(f"{BASE_DIR}/box_size4_config_parsed.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"""
【解析完成】

網格資訊:
  - 尺寸: 16×16 (256單元格)
  - 宮格: 4×4 (16個宮格)
  - 已知數字: {len(known_digits)} 個
  - 填滿率: {len(known_digits)/256*100:.1f}%

座標系統:
  - 行: A1-A16 (第1-16行)
  - 列: B-Q (第1-16列)
  - 位置: 1B=第1行第1列, 16Q=第16行第16列

約束結構:
  - 符闔排列: 每行需從其排列集中選取1個排列
  - 數獨約束: 行/列/宮格均須AllDifferent(1-16)

衝突檢測:
  - 行衝突: {len(row_conflicts)} 個
  - 列衝突: {len(col_conflicts)} 個
  - 宮格衝突: {len(box_conflicts)} 個

結果檔案: box_size4_config_parsed.json
""")
    
    return result


if __name__ == "__main__":
    result = parse_config_file()
