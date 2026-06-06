#!/usr/bin/env python3
"""
解析 超級大數獨_box_size4.txt 配置文件 - 修正版
正確提取16x16網格和92個已知數字
"""

import json
import re
from collections import defaultdict
from datetime import datetime

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"


def parse_config_file_v2():
    """解析配置文件 - 修正版"""
    print("="*70)
    print("符闔數獨配置文件解析報告（修正版）")
    print("="*70)
    print(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 讀取配置文件
    with open(f"{BASE_DIR}/超級大數獨_box_size4.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    print("\n" + "="*70)
    print("第一部分：數獨網格數據（16x16）")
    print("="*70)
    
    # 解析網格數據（第3-21行，每行是一個16元組）
    lines = content.strip().split('\n')
    grid = []
    
    for line in lines[2:18]:  # 行號3-18（索引2-17）對應16行
        # 用正則匹配數字
        numbers = re.findall(r'\d+', line)
        numbers = [int(n) for n in numbers]
        
        if len(numbers) == 16:
            grid.append(numbers)
        else:
            print(f"  ⚠️ 行解析異常: 找到 {len(numbers)} 個數字")
            print(f"     原始行: {line.strip()}")
    
    if len(grid) != 16:
        print(f"\n❌ 錯誤：只解析到 {len(grid)} 行，期望 16 行")
        return None
    
    print(f"\n✅ 成功解析 16×16 網格")
    
    # 顯示網格
    print("\n完整網格:")
    for r in range(16):
        line = []
        for c in range(16):
            if grid[r][c] != 0:
                line.append(f"{grid[r][c]:2d}")
            else:
                line.append(" .")
        print(f"  行{r+1:2d}: {' '.join(line)}")
    
    # 統計已知數字
    known_digits = []
    for r in range(16):
        for c in range(16):
            if grid[r][c] != 0:
                known_digits.append({
                    "row": r + 1,
                    "col": c + 1,
                    "value": grid[r][c]
                })
    
    print(f"\n已知數字統計:")
    print(f"  總數: {len(known_digits)} 個")
    print(f"  空單元格: {256 - len(known_digits)} 個")
    print(f"  填滿率: {len(known_digits)/256*100:.1f}%")
    
    print("\n" + "="*70)
    print("第二部分：座標系統與256個宮格分佈")
    print("="*70)
    
    print("\n座標系統說明:")
    print("  行: A1-A16 (第1-16行)")
    print("  列: B-Q (第1-16列)")
    print("  標記: [行號][列號] 例如:")
    print("    - 1B = 第1行第1列 = 單元格1")
    print("    - 16Q = 第16行第16列 = 單元格256")
    
    # 座標對照
    col_letters = {i+1: chr(ord('B')+i) for i in range(16)}
    
    print("\n所有已知數字座標列表:")
    print("-" * 50)
    for k in sorted(known_digits, key=lambda x: (x["row"], x["col"])):
        coord = f"{k['row']}{col_letters[k['col']]}"
        cell_num = (k['row'] - 1) * 16 + k['col']
        print(f"  {coord:4s} (單元格{cell_num:3d}): 第{k['row']:2d}行第{k['col']:2d}列 = {k['value']:2d}")
    
    print("\n256個單元格分佈（16行×16列）:")
    for r in range(1, 17):
        start = (r-1)*16 + 1
        end = r*16
        known_count = len([k for k in known_digits if k["row"]==r])
        print(f"  第{r:2d}行 (單元格 {start:3d}-{end:3d}): 已知 {known_count:2d} 個, 空白 {16-known_count:2d} 個")
    
    print("\n" + "="*70)
    print("第三部分：符闔排列約束")
    print("="*70)
    
    print("\n符闔排列文件引用:")
    for r in range(1, 17):
        print(f"  第{r:2d}行: A{r}第{r}行符闔排列.xlsx")
    
    print(f"\n約束解釋:")
    print(f"  - 符闔排列：每行必須從其對應的排列集中選取恰好1個排列")
    print(f"  - 每行16個單元格必須填入該排列的16個值（順序固定）")
    print(f"  - 總排列數：1,111,494 個（分布在16行中）")
    
    print("\n" + "="*70)
    print("第四部分：數值分佈分析")
    print("="*70)
    
    # 每個數值的分佈
    val_rows = defaultdict(list)
    val_positions = defaultdict(list)
    
    for k in known_digits:
        val_rows[k["value"]].append(k["row"])
        val_positions[k["value"]].append(f"{k['row']}{col_letters[k['col']]}")
    
    print("\n各數值出現位置:")
    print("-" * 50)
    for val in range(1, 17):
        rows = val_rows[val]
        positions = val_positions[val]
        row_str = ", ".join([f"A{r}" for r in sorted(set(rows))])
        print(f"  數值 {val:2d}: 出現 {len(positions):2d} 次, 行分布: {row_str}")
    
    print("\n" + "="*70)
    print("第五部分：宮格約束驗證")
    print("="*70)
    
    print("\n4×4宮格劃分:")
    for box_r in range(4):
        for box_c in range(4):
            box_id = box_r * 4 + box_c
            values = []
            for dr in range(4):
                for dc in range(4):
                    r = box_r * 4 + dr
                    c = box_c * 4 + dc
                    if grid[r][c] != 0:
                        values.append(f"{grid[r][c]}")
                    else:
                        values.append(".")
            print(f"  宮格{box_id+1:2d} (R{box_r*4+1}-{box_r*4+4}, C{box_c*4+1}-{box_c*4+4}):")
            print(f"    {' '.join(values[:4])}")
            print(f"    {' '.join(values[4:8])}")
            print(f"    {' '.join(values[8:12])}")
            print(f"    {' '.join(values[12:])}")
    
    print("\n" + "="*70)
    print("第六部分：約束衝突檢測")
    print("="*70)
    
    # 行衝突
    print("\n行內衝突檢測:")
    row_conflicts = []
    for r in range(16):
        values = [grid[r][c] for c in range(16) if grid[r][c] != 0]
        if len(values) != len(set(values)):
            dup = [v for v in set(values) if values.count(v) > 1]
            row_conflicts.append((r+1, dup))
    
    if row_conflicts:
        for r, dup in row_conflicts:
            print(f"  ❌ 第{r}行: 數值 {dup} 重複")
    else:
        print("  ✅ 所有行無內部衝突")
    
    # 列衝突
    print("\n列內衝突檢測:")
    col_conflicts = []
    for c in range(16):
        values = [grid[r][c] for r in range(16) if grid[r][c] != 0]
        if len(values) != len(set(values)):
            dup = [v for v in set(values) if values.count(v) > 1]
            col_conflicts.append((c+1, dup))
    
    if col_conflicts:
        for c, dup in col_conflicts:
            print(f"  ❌ 第{c}列: 數值 {dup} 重複")
    else:
        print("  ✅ 所有列無內部衝突")
    
    # 宮格衝突
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
                dup = [v for v in set(values) if values.count(v) > 1]
                box_conflicts.append((box_id+1, dup))
    
    if box_conflicts:
        for bid, dup in box_conflicts:
            print(f"  ❌ 宮格{bid}: 數值 {dup} 重複")
    else:
        print("  ✅ 所有宮格無內部衝突")
    
    print("\n" + "="*70)
    print("第七部分：數據完整性驗證")
    print("="*70)
    
    # 與 sudoku_config.json 對比
    with open(f"{BASE_DIR}/sudoku_config.json") as f:
        config = json.load(f)
    
    config_known = {(k["row"], k["col"]): k["value"] for k in config.get("known_digits", [])}
    parsed_known = {(k["row"], k["col"]): k["value"] for k in known_digits}
    
    if config_known == parsed_known:
        print(f"\n✅ 解析數據與 sudoku_config.json 完全一致")
        print(f"   已知數字數: {len(known_digits)}")
    else:
        print(f"\n⚠️ 數據不一致!")
        print(f"   sudoku_config.json: {len(config_known)} 個已知數字")
        print(f"   解析結果: {len(parsed_known)} 個已知數字")
    
    # 保存結果
    result = {
        "parse_version": "v2",
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
        "value_distribution": {str(v): len(val_rows[v]) for v in range(1, 17)},
        "conflicts": {
            "row": row_conflicts,
            "col": col_conflicts,
            "box": box_conflicts
        },
        "coordinate_system": {
            "rows": {f"A{i}": i for i in range(1, 17)},
            "columns": {chr(ord('B')+i): i+1 for i in range(16)}
        },
        "validation": {
            "consistent_with_config_json": config_known == parsed_known
        }
    }
    
    with open(f"{BASE_DIR}/box_size4_config_parsed_v2.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print("【解析完成】")
    print("="*70)
    
    return result


if __name__ == "__main__":
    result = parse_config_file_v2()
