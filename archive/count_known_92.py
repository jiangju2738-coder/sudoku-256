#!/usr/bin/env python3
"""正確解析超級大數獨_box_size4.txt中的已知數字 - 最終版"""

import json
import re

with open("超級大數獨_box_size4.txt", "r", encoding="utf-8") as f:
    content = f.read()

print("="*60)
print("從超級大數獨_box_size4.txt提取16×16數獨網格")
print("="*60)

lines = content.strip().split('\n')

grid = []
for line in lines[2:]:  # 從第3行開始
    line = line.strip()
    if not line:  # 空行跳過
        continue
    
    # 用正則提取所有數字（包含中文標點前的數字）
    numbers = re.findall(r'\d+', line)
    numbers = [int(x) for x in numbers]
    
    if len(numbers) == 16:
        grid.append(numbers)
        non_zero = sum(1 for x in numbers if x != 0)
        print(f"行{len(grid):2d}: {non_zero:2d} 個已知數字")
    else:
        print(f"⚠️ 解析異常: {len(numbers)} 個數字: {line[:50]}")
    
    if len(grid) >= 16:
        break

print(f"\n✅ 成功解析 {len(grid)} 行 × 16 列")

# 統計所有已知數字
known_positions = []
for r in range(16):
    for c in range(16):
        val = grid[r][c]
        if val != 0:
            col_letter = chr(ord('B') + c)
            cell_num = r * 16 + c + 1
            box_r = r // 4
            box_c = c // 4
            box_id = box_r * 4 + box_c + 1
            known_positions.append({
                "row": r + 1,
                "col": c + 1,
                "value": val,
                "cell_num": cell_num,
                "box": box_id,
                "coord": f"{r+1}{col_letter}"
            })

print(f"\n📊 網格統計:")
print(f"  總單元格: 256")
print(f"  已知數字: {len(known_positions)} 個")
print(f"  空白單元格: {256 - len(known_positions)} 個")
print(f"  填滿率: {len(known_positions)/256*100:.1f}%")

# 與sudoku_config.json對比
print("\n" + "="*60)
print("與sudoku_config.json對比")
print("="*60)

with open("sudoku_config.json") as f:
    config = json.load(f)

config_digits = config.get("known_digits", [])
print(f"sudoku_config.json: {len(config_digits)} 個已知數字")

txt_set = {(k["row"], k["col"]): k["value"] for k in known_positions}
config_set = {(k["row"], k["col"]): k["value"] for k in config_digits}

if txt_set == config_set:
    print("✅ 數據完全一致！")
else:
    print("⚠️ 數據不一致")
    all_keys = set(txt_set.keys()) | set(config_set.keys())
    match = sum(1 for k in all_keys if txt_set.get(k) == config_set.get(k))
    print(f"  匹配: {match}/{len(all_keys)}")

# 完整座標列表
print("\n" + "="*60)
print(f"所有 {len(known_positions)} 個已知數字座標")
print("="*60)

for i, k in enumerate(known_positions, 1):
    print(f"  {i:3d}. {k['coord']:4s} (單元格{k['cell_num']:3d}, 宮格{k['box']:2d}) = 值{k['value']:2d}")

# 按行分佈
print("\n" + "="*60)
print("各行已知數字分佈")
print("="*60)
for r in range(1, 17):
    row_known = [k for k in known_positions if k["row"] == r]
    print(f"  第{r:2d}行 (A{r}): {len(row_known):2d} 個")

# 保存JSON
output = {
    "source": "超級大數獨_box_size4.txt",
    "grid_size": 16,
    "box_size": 4,
    "total_cells": 256,
    "known_digits_count": len(known_positions),
    "empty_cells": 256 - len(known_positions),
    "fill_rate": round(len(known_positions)/256*100, 1),
    "known_digits": known_positions,
    "row_distribution": {str(r): len([k for k in known_positions if k["row"]==r]) for r in range(1, 17)},
    "grid": grid
}

with open("box_size4_grid_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✅ 數據已保存: box_size4_grid_data.json")
