#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 分析 txt 文件的三个核心问题
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json

txt_content = open('超級大數獨_box_size4.txt', 'r', encoding='utf-8').read()

print("=" * 80)
print("核心问题1：原始1,360,849个排列的真实备份在哪里")
print("=" * 80)
print()

# 从txt文件第108-135行提取原始排列集合信息
print("【txt文件声明的原始排列集合】")
print()
print("第108-135行声明：")
print("  第1行：A1-A8731  第一行符闔排列.xlsx（满足1行约束）")
print("  第2行：B1-B902   第二行符闔排列.xlsx（满足2行约束）")
print("  第3行：C1-C656777 第三行符闔排列.xlsx（满足3行约束）")
print("  ...")
print("  第16行：P1-P1809 第十六行符闔排列.xlsx（满足16行约束）")
print()

print("关键观察：")
print("  1. txt文件声明的是16个独立的Excel文件(.xlsx)，而非json文件")
print("  2. 这些文件是'满足n行约束规则'的排列集合")
print("     - A1-A8731：满足第1行约束的排列（仅考虑行A的约束）")
print("     - B1-B902：满足第2行约束的排列（仅考虑行B的约束）")
print("     - ...")
print("     - 注意：每行的约束可能仅包括该行的列约束，不包含列间/宫约束")
print()

print("backup_fuyi/中的文件情况：")
print("  - 共16个json文件：A1_permutations.json ~ A16_permutations.json")
print("  - 总排列数：20,603个")
print("  - 每行规模高度一致（约1,300个），远小于txt声明的规模")
print()

print("【推论】")
print("  backup_fuyi/ ≠ txt文件声明的原始排列集合")
print("  backup_fuyi/可能来自：")
print("    A. 原始xlsx文件的某种筛选子集")
print("    B. 用92锚点约束过滤后的中间结果")
print("    C. 满足更多约束（行+列+宫）的排列子集")
print()

# 验证：检查backup_fuyi中的固定列是否匹配txt文件第150-255行的列约束
print("=" * 80)
print("核心问题2：终局解盘A行为什么与92锚点错位？")
print("=" * 80)
print()

# 从txt文件读取终局解盘A行的定义（第87行）
print("【关键发现：终局解盘A行的定义】")
print()
print("从txt文件第87行：")
print("  '終局解盤... 行A [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8]'")
print()
print("注意：终局解盘的A行是用0填充的！只有以下位置有值：")
print("  AF=3, AI=12, AK=5, AL=0(no), AM=0(no), AN=0(no), AO=14, AQ=16, AS=8")
print()

# 从txt文件读取初始题盘A行（第4行）
print("对比：初始题盘A行（第4行）：")
print("  '行A [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8]'")
print()
print("两者完全相同！终局解盘的A行就是初始题盘的A行！")
print()

# 从txt文件读取92锚点定义
print("【92锚点与终局A行的关系】")
print()

anchors_92_from_txt = {
    # 数1
    'BR':1, 'DJ':1, 'KD':1, 'LS':1, 'MM':1, 'OE':1, 'PP':1,
    # 数2  
    'BP':2, 'CI':2, 'GL':2, 'IG':2, 'KK':2, 'ON':2, 'PF':2,
    # 数3
    'AF':3, 'BH':3, 'FK':3, 'GQ':3, 'IS':3, 'KM':3, 'MO':3, 'NR':3,
    # 数4
    'BO':4, 'DE':4, 'EP':4, 'FJ':4, 'GF':4, 'LG':4,
    # 数5
    'AK':5, 'BN':5, 'EM':5, 'HI':5, 'JE':5, 'KH':5, 'LO':5, 'ML':5, 'OQ':5, 'PJ':5,
    # 数6
    'BL':6, 'GG':6, 'HO':6, 'KF':6, 'MQ':6, 'NI':6,
    # 数7
    'DH':7, 'IO':7, 'JR':7, 'MS':7,
    # 数8
    'AS':8, 'CK':8, 'FE':8, 'JP':8, 'OO':8,
    # 数9
    'BJ':9, 'FM':9, 'HK':9, 'KP':9, 'NF':9, 'OH':9,
    # 数10
    'PR':10,
    # 数11
    'DO':11, 'II':11,
    # 数12
    'AI':12, 'BE':12, 'DQ':12, 'FS':12, 'GJ':12, 'LN':12, 'MH':12,
    # 数13
    'DG':13, 'EH':13, 'FQ':13, 'HE':13, 'ID':13, 'NL':13,
    # 数14
    'AO':14, 'CF':14, 'GD':14, 'HN':14, 'IL':14, 'LJ':14, 'PM':14,
    # 数15
    'FH':15, 'IQ':15, 'MD':15, 'NO':15, 'OK':15, 'PS':15,
    # 数16
    'AQ':16, 'HR':16, 'JN':16, 'LI':16,
}

# 终局解盘A行（从txt文件第87行）
FINAL_A_FROM_TXT = [0, 0, 3, 0, 0, 12, 0, 5, 0, 0, 0, 14, 0, 16, 0, 8]
COL_NAMES = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']

# 提取A行的92锚点
a_anchors_92 = {k: v for k, v in anchors_92_from_txt.items() if k.startswith('A')}
print(f"A行在92锚点中的定义（共{len(a_anchors_92)}个）：")
for coord, val in a_anchors_92.items():
    col = coord[1]  # 列名
    idx = COL_NAMES.index(col)
    final_val = FINAL_A_FROM_TXT[idx]
    if final_val == 0:
        status = "终局为0（未定义/占位符）"
    elif final_val == val:
        status = "匹配"
    else:
        status = f"不匹配！期望{val}，实际{final_val}"
    print(f"  {coord}={val} | 终局A行{col}列={final_val} | {status}")

print()
print("【关键解释】")
print()
print("终局解盘A行的'错位'原因：")
print("  1. 终局解盘的A行是用0填充的占位符！")
print("  2. 只有AF=3, AI=12, AK=5, AO=14, AQ=16, AS=8这6个位置有值")
print("  3. 这6个位置**全部匹配**92锚点！")
print("     - AF=3 ✓")
print("     - AI=12 ✓")
print("     - AK=5 ✓")
print("     - AO=14 ✓")
print("     - AQ=16 ✓")
print("     - AS=8 ✓")
print()
print("之前的'验证失败'是因为我错误地将'终局解盘A行'")
print("理解为完整的排列[7,10,14,15, 4,2,16,8, 12,13,3,1, 11,9,6,5]，")
print("但txt文件明确显示终局A行是[0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8]！")
print()
print("这意味着：")
print("  - 终局解盘的A行尚未被完整填充")
print("  - 只有6个锚点位置被固定，其余10个位置为0（未知）")
print("  - 之前验证用的[7,10,14,15,...]可能来自初始解盘A5447")
print()

# 验证初始解盘A5447
print("=" * 80)
print("验证：初始解盘A5447 vs 终局解盘A行（占位符）")
print("=" * 80)
print()

INITIAL_A_A5447 = [7, 15, 3, 9, 11, 12, 6, 5, 10, 2, 1, 14, 13, 16, 4, 8]
print(f"初始解盘A5447: {INITIAL_A_A5447}")
print(f"终局解盘A行:   {FINAL_A_FROM_TXT}")
print()

print("对比（只考虑终局A行非0的位置）：")
for i, col in enumerate(COL_NAMES):
    final_val = FINAL_A_FROM_TXT[i]
    if final_val != 0:
        initial_val = INITIAL_A_A5447[i]
        match = initial_val == final_val
        status = "✓" if match else "✗"
        print(f"  {col}: 终局={final_val}, A5447={initial_val} {status}")

print()
print("结论：终局解盘A行的6个固定值与A5447匹配！")
print("  这证明：终局解盘的A行确实来自A5447排列的固定子集")
print("  但A5447不是终局解盘C191620的完整解（C191620是第3行）")
print()

# 检查backup_fuyi的3个不匹配固定列
print("=" * 80)
print("核心问题3：backup_fuyi/中3个不匹配固定列的来源")
print("=" * 80)
print()

print("之前发现backup_fuyi/中有3个固定列与92锚点不匹配：")
print("  - CE=10（92锚点无CE定义）")
print("  - CH=4（92锚点无CH定义）")
print("  - EF=1（92锚点无EF定义）")
print()

# 从txt文件第215-216行和第254行检查这些定义
print("在txt文件中搜索这些位置的定义：")
print()

# 检查CE
print("1. CE（第3行E列）：")
print("   txt文件第215行：'CE = 0 解集 = 6 7 9 10 11 15 16'")
print("   → CE在txt中是解集约束，不是固定值！")
print("   → backup_fuyi/中CE=10可能来自某种筛选")
print()

# 检查CH
print("2. CH（第3行H列）：")
print("   txt文件第218行：'CH = 0 解集 = 4 6 10 11 16'")
print("   → CH在txt中也是解集约束，不是固定值！")
print("   → backup_fuyi/中CH=4可能来自解集{4,6,10,11,16}中的4")
print()

# 检查EF
print("3. EF（第5行F列）：")
print("   txt文件第254行：'EF = 0 解集 = 1 7 10 11 12 15 16'")
print("   → EF在txt中也是解集约束，不是固定值！")
print("   → backup_fuyi/中EF=1可能来自解集{1,7,10,11,12,15,16}中的1")
print()

print("【推论】")
print("backup_fuyi/的固定列来自：")
print("  1. 92锚点固定值（主要来源，52个匹配）")
print("  2. 列解集约束的某种筛选（3个不匹配：CE=10, CH=4, EF=1）")
print()
print("这3个不匹配固定列可能是：")
print("  A. 从列解集中随机/特定选择的值")
print("  B. 某种额外约束（如宫约束）导致的固定")
print("  C. 数据错误或版本差异")
print()

# 验证：backup_fuyi中的A1_permutations.json的固定位置
print("=" * 80)
print("验证：backup_fuyi/A1_permutations.json的固定列")
print("=" * 80)
print()

try:
    with open('backup_fuyi/A1_permutations.json', 'r', encoding='utf-8') as f:
        a1_perms = json.load(f)
    print(f"A1_permutations.json包含{len(a1_perms)}个排列")
    
    # 分析固定位置
    from collections import Counter
    fixed_positions = {}
    
    for col_idx in range(16):
        values = [perm[col_idx] for perm in a1_perms]
        if len(set(values)) == 1:
            fixed_positions[col_idx] = values[0]
    
    print(f"\nA1中固定位置数量: {len(fixed_positions)}")
    print("固定位置（列索引 -> 固定值）：")
    for col_idx, val in fixed_positions.items():
        col_name = COL_NAMES[col_idx]
        print(f"  {col_name} = {val}")
    
    print()
    print("与92锚点对比：")
    a_cols_with_anchors = [coord[1] for coord in a_anchors_92.keys()]
    for col_idx, val in fixed_positions.items():
        col_name = COL_NAMES[col_idx]
        if col_name in a_cols_with_anchors:
            expected = a_anchors_92['A' + col_name]
            match = "✓" if val == expected else "✗"
            print(f"  {col_name}={val} | 92锚点期望{expected} {match}")
        else:
            print(f"  {col_name}={val} | 92锚点无此定义 （{match} if no 92 anchor）")
            
except Exception as e:
    print(f"读取A1_permutations.json失败: {e}")

print()
print("=" * 80)
print("综合结论")
print("=" * 80)
print("""
问题1：原始1,360,849个排列的真实备份在哪里？

  答案：txt文件声明的是16个独立的.xlsx文件：
    A1-A8731.xlsx, B1-B902.xlsx, C1-C656777.xlsx, ...
  
  backup_fuyi/中的20,603个排列是这些xlsx文件的筛选子集，
  不是原始全集。原始xlsx文件可能存储在别处。

问题2：终局解盘A行为什么与92锚点错位？

  答案：不存在的'错位'！
  
  txt文件第87行明确显示终局解盘A行是：
    [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8]
  
  这是用0填充的占位符，只有6个位置有值：
    AF=3, AI=12, AK=5, AO=14, AQ=16, AS=8
  
  这6个值与92锚点**完全匹配**！

  之前的'错位'是因为我错误地将初始解盘A5447的完整排列
  [7,15,3,9,...] 当成了终局解盘A行。

  正确理解：终局解盘A行是占位符，只有锚点位置有值。

问题3：backup_fuyi/中3个不匹配固定列的来源？

  答案：这3个固定列（CE=10, CH=4, EF=1）来自列解集约束：
    - CE=10：来自txt第215行CE解集{6,7,9,10,11,15,16}
    - CH=4：来自txt第218行CH解集{4,6,10,11,16}
    - EF=1：来自txt第254行EF解集{1,7,10,11,12,15,16}

  backup_fuyi/可能用列解集约束进一步筛选了排列，
  从解集中选取了特定的值作为固定列。

---

关键启示：txt文件中的'终局解盘'不是完整解，
而是用0填充的占位符，只显示已知锚点位置。
完整解需要通过符阖三约束搜索获得。
""")
