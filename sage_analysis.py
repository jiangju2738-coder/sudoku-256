#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
賽奇（Sage）數據科學分析腳本
超級大數獨 256 宮格文件解析與統計分析
"""

import re
import os
import math

FPATH = "D:/2026/WPF_Sudoku/Sudoku_256/超級大數獨_box_size4.txt"

# ============================================================
# 輔助函數：從行文本中解析 16 個數字
# ============================================================
def parse_row_numbers(line_text):
    """從如 '[0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8]' 中提取16個數字"""
    m = re.search(r'\[([^\]]+)\]', line_text)
    if not m:
        return None
    inner = m.group(1)
    # 替換全形逗號
    inner = inner.replace('，', ',')
    nums = []
    for tok in re.split(r'[,\s]+', inner.strip()):
        tok = tok.strip()
        if tok == '':
            continue
        try:
            nums.append(int(tok))
        except ValueError:
            return None
    if len(nums) == 16:
        return nums
    return None

# ============================================================
# 讀取文件
# ============================================================
with open(FPATH, encoding='utf-8') as f:
    raw = f.read()
    lines = f.readlines() if False else raw.splitlines()

file_size = os.path.getsize(FPATH)
total_lines = len(lines)

print("=" * 60)
print("【Step 1】文件基本信息")
print("=" * 60)
print(f"文件路徑   : {FPATH}")
print(f"文件大小   : {file_size:,} bytes ({file_size/1024:.2f} KB)")
print(f"總行數     : {total_lines}")
print(f"文件編碼   : UTF-8")

# ============================================================
# 解析初始謎盤 / 各盤 / 符闔排列統計
# ============================================================

# --- 1. 初始謎盤（行A-P 含0的盤）
initial_grid = {}
solution_grids = {}     # key: 盤名（初始解盤/更新解盤/終局解盤）
permutation_counts = {} # key: 行號(1-16), value: 排列數

# 狀態標誌
MODE_INIT_PUZZLE    = False
MODE_INIT_SOLUTION  = False
MODE_UPDATE_SOL     = False
MODE_FINAL_SOL      = False
MODE_EVOLVED_PUZZLE = False

ROW_LABELS = list("ABCDEFGHIJKLMNOP")

init_puzzle_rows   = {}
init_sol_rows      = {}
update_sol_rows    = {}
final_sol_rows     = {}
evolved_puzzle_rows= {}

# 行標籤 → 數字行號映射
row_to_num = {r: i+1 for i, r in enumerate(ROW_LABELS)}

for line in lines:
    stripped = line.strip()

    # 判斷區段
    if '初始謎盤' in stripped and '已知題盤' in stripped:
        MODE_INIT_PUZZLE = True
        MODE_INIT_SOLUTION = MODE_UPDATE_SOL = MODE_FINAL_SOL = MODE_EVOLVED_PUZZLE = False
        continue
    if '初始解盤' in stripped and '行A列字母' not in stripped and '初始加' not in stripped:
        MODE_INIT_SOLUTION = True
        MODE_INIT_PUZZLE = MODE_UPDATE_SOL = MODE_FINAL_SOL = MODE_EVOLVED_PUZZLE = False
        continue
    if '更新解盤' in stripped:
        MODE_UPDATE_SOL = True
        MODE_INIT_PUZZLE = MODE_INIT_SOLUTION = MODE_FINAL_SOL = MODE_EVOLVED_PUZZLE = False
        continue
    if '終局解盤' in stripped:
        MODE_FINAL_SOL = True
        MODE_INIT_PUZZLE = MODE_INIT_SOLUTION = MODE_UPDATE_SOL = MODE_EVOLVED_PUZZLE = False
        continue
    if '演進筭盤' in stripped:
        MODE_EVOLVED_PUZZLE = True
        MODE_INIT_PUZZLE = MODE_INIT_SOLUTION = MODE_UPDATE_SOL = MODE_FINAL_SOL = False
        continue

    # 符闔排列統計
    m_perm = re.match(r'第(\d+)行：[A-Z]\d+-[A-Z](\d+)\s', stripped)
    if m_perm:
        row_idx = int(m_perm.group(1))
        count   = int(m_perm.group(2))
        if row_idx not in permutation_counts:
            permutation_counts[row_idx] = count

    # 解析行數據 行X [...]
    m_row = re.match(r'行([A-P])[\d\s]*[\[（]', stripped)
    if m_row:
        lbl = m_row.group(1)
        nums = parse_row_numbers(stripped)
        if nums and len(nums) == 16:
            if MODE_INIT_PUZZLE or (MODE_INIT_PUZZLE is False and MODE_INIT_SOLUTION is False
                and MODE_UPDATE_SOL is False and MODE_FINAL_SOL is False
                and MODE_EVOLVED_PUZZLE is False):
                pass
            if MODE_INIT_PUZZLE:
                init_puzzle_rows[lbl] = nums
            elif MODE_INIT_SOLUTION:
                init_sol_rows[lbl] = nums
            elif MODE_UPDATE_SOL:
                update_sol_rows[lbl] = nums
            elif MODE_FINAL_SOL:
                final_sol_rows[lbl] = nums
            elif MODE_EVOLVED_PUZZLE:
                evolved_puzzle_rows[lbl] = nums

# 回退：直接用正則抓初始謎盤（行A-P 含0）
# 文件中已知題盤區域在第3-22行（索引2-21）
# 直接提取所有含0的謎盤行
init_puzzle_rows_direct = {}
for line in lines[2:25]:
    m = re.match(r'行([A-P])\s*\[([^\]]+)\]', line.strip())
    if m:
        lbl = m.group(1)
        inner = m.group(2).replace('，', ',')
        nums = [int(x.strip()) for x in re.split(r'[,\s]+', inner.strip()) if x.strip().isdigit()]
        if len(nums) == 16:
            init_puzzle_rows_direct[lbl] = nums

# 終局解盤（第103行起）
final_sol_direct = {}
in_final = False
for i, line in enumerate(lines):
    if '終局解盤' in line:
        in_final = True
        continue
    if in_final:
        m = re.match(r'行([A-P])[\d\s]*\[([^\]]+)\]', line.strip())
        if m:
            lbl = m.group(1)
            inner = m.group(2).replace('，', ',')
            nums = [int(x.strip()) for x in re.split(r'[,\s]+', inner.strip()) if x.strip().lstrip('-').isdigit()]
            nums = [abs(n) for n in nums]
            if len(nums) == 16:
                final_sol_direct[lbl] = nums
        if '演進筭盤' in line:
            break

# 演進筭盤（含0）
evolved_direct = {}
in_evolved = False
for i, line in enumerate(lines):
    if '演進筭盤' in line:
        in_evolved = True
        continue
    if in_evolved:
        stripped2 = line.strip()
        m = re.match(r'行([A-P])[\d\s]*\[([^\]]+)\]', stripped2)
        if m:
            lbl = m.group(1)
            inner = m.group(2).replace('，', ',')
            parts = re.split(r'[,\s]+', inner.strip())
            nums2 = []
            for p in parts:
                p = p.strip()
                if p.isdigit():
                    nums2.append(int(p))
            if len(nums2) == 16:
                evolved_direct[lbl] = nums2
        if len(evolved_direct) >= 16:
            break

# ============================================================
# 整合謎盤：優先用 init_puzzle_rows_direct（原始謎盤帶0）
# ============================================================
main_puzzle = init_puzzle_rows_direct if len(init_puzzle_rows_direct) == 16 else evolved_direct
main_solution = final_sol_direct

print()
print("=" * 60)
print("【Step 2】數獨結構分析")
print("=" * 60)

print(f"\n◆ 謎盤解析成功行數 : {len(main_puzzle)} / 16")
print(f"◆ 終局解盤解析行數 : {len(main_solution)} / 16")

# 已知錨點數（非零格）
if main_puzzle:
    total_cells = 16 * 16
    known_counts = {}
    for lbl in ROW_LABELS:
        if lbl in main_puzzle:
            known = sum(1 for v in main_puzzle[lbl] if v != 0)
            known_counts[lbl] = known

    total_known = sum(known_counts.values())
    fill_rate = total_known / total_cells * 100 if total_cells else 0

    print(f"\n◆ 總格數           : {total_cells}")
    print(f"◆ 已知格數（非零）  : {total_known}")
    print(f"◆ 空格數（零）     : {total_cells - total_known}")
    print(f"◆ 平均填充率       : {fill_rate:.2f}%")

    print("\n◆ 各行已知數統計：")
    print(f"  {'行號':<6} {'已知數':<8} {'空格數':<8} {'填充率'}")
    print("  " + "-" * 36)
    for lbl in ROW_LABELS:
        if lbl in known_counts:
            k = known_counts[lbl]
            e = 16 - k
            r = k / 16 * 100
            print(f"  {lbl:<6} {k:<8} {e:<8} {r:.1f}%")

    # 難度分布
    known_vals = list(known_counts.values())
    import statistics
    mean_k  = statistics.mean(known_vals)
    stdev_k = statistics.stdev(known_vals) if len(known_vals) > 1 else 0
    min_k   = min(known_vals)
    max_k   = max(known_vals)
    print(f"\n◆ 難度指標（已知數分布）：")
    print(f"  最小值 = {min_k}, 最大值 = {max_k}, 均值 = {mean_k:.2f}, 標準差 = {stdev_k:.2f}")

# 數字頻率（謎盤中各數字出現次數）
print("\n◆ 謎盤數字頻率（1-16）：")
freq = {i: 0 for i in range(1, 17)}
for lbl in ROW_LABELS:
    if lbl in main_puzzle:
        for v in main_puzzle[lbl]:
            if 1 <= v <= 16:
                freq[v] += 1

print(f"  {'數字':<6} {'出現次數':<10} {'佔已知格比例'}")
print("  " + "-" * 32)
for d in range(1, 17):
    cnt = freq[d]
    pct = cnt / total_known * 100 if total_known > 0 else 0
    print(f"  {d:<6} {cnt:<10} {pct:.1f}%")

# 空格位置密度矩陣（16×16）
print("\n◆ 空格位置密度熱力圖數據（16×16，1=空格，0=已知）：")
density_matrix = []
for lbl in ROW_LABELS:
    if lbl in main_puzzle:
        row = [1 if v == 0 else 0 for v in main_puzzle[lbl]]
    else:
        row = [1] * 16
    density_matrix.append(row)

# 每列空格密度
col_density = [0] * 16
for row in density_matrix:
    for j, v in enumerate(row):
        col_density[j] += v
col_density_pct = [v / 16 * 100 for v in col_density]

print("  列空格密度（%）：")
print("  " + " ".join(f"{v:4.0f}" for v in col_density_pct))
print()
print("  空格矩陣（行=A-P，列=1-16，X=空格，.=已知）：")
for i, (lbl, row) in enumerate(zip(ROW_LABELS, density_matrix)):
    visual = "".join("X" if v == 1 else "." for v in row)
    print(f"  行{lbl}: {visual}")

# ============================================================
# Step 3：約束複雜度分析
# ============================================================
print()
print("=" * 60)
print("【Step 3】約束複雜度分析")
print("=" * 60)

def sudoku_constraints(n, box):
    """
    n×n 數獨（box×box 小宮），計算約束總數
    每個格子有 3 個基礎約束（行、列、宮格），加上唯一性約束
    """
    row_c = n * n          # 行約束（每行每個數字恰好一個）
    col_c = n * n          # 列約束
    box_c = n * n          # 宮格約束（共 n 個宮格，每宮 n 個數字）
    total_c = row_c + col_c + box_c
    cells = n * n
    # 搜索空間（假設每個空格最多 n 種可能）
    empty_typical = int(cells * 0.5)
    search_space = n ** empty_typical
    return row_c, col_c, box_c, total_c, cells, search_space

print("\n◆ 複雜度對比表：")
header = f"  {'規格':<20} {'格數':<8} {'行約束':<8} {'列約束':<8} {'宮格約束':<10} {'總約束':<10} {'搜索空間(對數)'}"
print(header)
print("  " + "-" * 85)

configs = [
    ("9×9 標準數獨",  9, 3),
    ("16×16 數獨",   16, 4),
    ("理論256宮格",  256, 16),  # 假設存在
]
for name, n, box in configs:
    rc, cc, bc, tc, cells, ss = sudoku_constraints(n, box)
    log_ss = math.log10(ss) if ss > 0 else 0
    print(f"  {name:<20} {cells:<8} {rc:<8} {cc:<8} {bc:<10} {tc:<10} 10^{log_ss:.0f}")

# 16×16 詳細計算
n16 = 16
print(f"\n◆ 16×16 數獨精確統計：")
print(f"  總格數        : {n16*n16}")
print(f"  數字範圍      : 1 - {n16}")
print(f"  小宮尺寸      : 4×4")
print(f"  行約束數      : {n16} 行 × {n16} 個數字 = {n16*n16} 個約束")
print(f"  列約束數      : {n16} 列 × {n16} 個數字 = {n16*n16} 個約束")
print(f"  宮格約束數    : {n16} 宮 × {n16} 個數字 = {n16*n16} 個約束")
print(f"  約束總計      : {n16*n16*3} 個")

empty_16 = total_cells - total_known if main_puzzle else int(n16*n16*0.64)
print(f"  本謎題空格數  : {empty_16}")
print(f"  理論搜索空間  : 16^{empty_16} ≈ 10^{empty_16 * math.log10(16):.0f}")

print(f"\n◆ 與標準9×9相比：")
ratio_cells   = (16*16) / (9*9)
ratio_constr  = (16*16*3) / (9*9*3)
ratio_search  = (empty_16 * math.log10(16)) - (41 * math.log10(9))  # 典型9×9空格≈41
print(f"  格數倍率      : {ratio_cells:.1f}× ({n16*n16} vs {81})")
print(f"  約束倍率      : {ratio_constr:.1f}×")
print(f"  搜索空間差    : 額外 10^{ratio_search:.0f} 倍")

# ============================================================
# Step 4：符闔排列統計
# ============================================================
print()
print("=" * 60)
print("【Step 4】各行符闔排列統計")
print("=" * 60)
if permutation_counts:
    print(f"\n  {'行號':<6} {'排列數':<12} {'對數(log10)'}")
    print("  " + "-" * 32)
    total_perms = 1
    for row in sorted(permutation_counts.keys()):
        cnt = permutation_counts[row]
        log_cnt = math.log10(cnt) if cnt > 0 else 0
        print(f"  {row:<6} {cnt:<12,} {log_cnt:.2f}")
        total_perms *= cnt

    print(f"\n  所有行排列數之積（理論上界）：")
    print(f"  log10 = {math.log10(total_perms):.2f}")
    print(f"  (實際解空間遠小於此上界，因列+宮格約束大幅剪枝)")

# ============================================================
# Step 5：代表性謎題樣本
# ============================================================
print()
print("=" * 60)
print("【Step 5】代表性謎題樣本")
print("=" * 60)

print("\n◆ 樣本1：初始謎盤（行A-P，0=未知）")
print(f"  （已知錨點 = {total_known}，空格 = {total_cells - total_known}）")
for lbl in ROW_LABELS:
    if lbl in main_puzzle:
        nums = main_puzzle[lbl]
        # 格式化：每4個一組
        groups = [nums[i:i+4] for i in range(0, 16, 4)]
        formatted = "  ".join(", ".join(f"{v:2d}" for v in g) for g in groups)
        print(f"  行{lbl}: [{formatted}]")

if main_solution and len(main_solution) == 16:
    print(f"\n◆ 樣本2：終局解盤（完整解，16×16，1-16）")
    for lbl in ROW_LABELS:
        if lbl in main_solution:
            nums = main_solution[lbl]
            groups = [nums[i:i+4] for i in range(0, 16, 4)]
            formatted = "  ".join(", ".join(f"{v:2d}" for v in g) for g in groups)
            print(f"  行{lbl}: [{formatted}]")

    # 驗證終局解（每行、列、宮格各包含1-16）
    print(f"\n◆ 終局解驗證：")
    target_set = set(range(1, 17))

    row_ok = True
    for lbl in ROW_LABELS:
        if lbl in main_solution:
            if set(main_solution[lbl]) != target_set:
                row_ok = False
                print(f"  行{lbl} 驗證失敗：{sorted(set(main_solution[lbl]))}")
    print(f"  行約束 : {'[OK] 全部通過' if row_ok else '[FAIL] 存在問題'}")

    # 列驗證
    col_ok = True
    for j in range(16):
        col_vals = [main_solution[lbl][j] for lbl in ROW_LABELS if lbl in main_solution]
        if len(col_vals) == 16 and set(col_vals) != target_set:
            col_ok = False
            print(f"  第{j+1}列驗證失敗")
    print(f"  列約束 : {'[OK] 全部通過' if col_ok else '[FAIL] 存在問題'}")

    # 宮格驗證（4×4 共16個宮格）
    all_rows = [main_solution[lbl] for lbl in ROW_LABELS if lbl in main_solution]
    box_ok = True
    if len(all_rows) == 16:
        for br in range(4):
            for bc_idx in range(4):
                box_vals = []
                for r in range(br*4, br*4+4):
                    for c in range(bc_idx*4, bc_idx*4+4):
                        box_vals.append(all_rows[r][c])
                if set(box_vals) != target_set:
                    box_ok = False
    print(f"  宮格約束: {'[OK] 全部通過' if box_ok else '[FAIL] 存在問題'}")

# ============================================================
# 文件內容摘要
# ============================================================
print()
print("=" * 60)
print("【文件結構摘要】")
print("=" * 60)
sections = [
    ("已知題盤",       "初始謎盤，92個錨點，164個空格"),
    ("已知數列表",     "數字1-16各自的已知位置（行列索引）"),
    ("各數字未知數",   "每個數字在謎盤中的未知格數量"),
    ("初始解盤",       "第一階段解（含行標注序次）"),
    ("更新解盤",       "第二階段更新解"),
    ("終局解盤",       "最終完整解（16×16，1-16）"),
    ("演進筭盤",       "演進版謎盤（調整後的初始盤）"),
    ("初始加*盤",      "按行分析的演進解（16行，附加標注）"),
    ("符闔排列統計",   "每行滿足約束的合法排列數（16行）"),
    ("行號/列號映射",  "A-P→第1-16行，D-S→第1-16列"),
]
for name, desc in sections:
    print(f"  [{name}] {desc}")

print()
print("=" * 60)
print("分析完成！")
print("=" * 60)
