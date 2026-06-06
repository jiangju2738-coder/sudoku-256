#!/usr/bin/env python3
"""
重新验证16行符闔排列与初始盘已知数字的对应关系
A列1-16 = 第1-16行
B-Q列 = 第1-16列
"""

import json
import os
from collections import Counter

WORK_DIR = r"D:\2026\WPF_Sudoku\Sudoku_256"

# 初始盘数据 - 92个已知数字
INITIAL_PUZZLE = [
    [0, 0, 3, 0, 0, 12, 0, 5, 0, 0, 0, 14, 0, 16, 0, 8],      # 第1行 A1
    [0, 12, 0, 0, 3, 0, 9, 0, 6, 0, 5, 4, 2, 0, 1, 0],      # 第2行 A2
    [0, 0, 14, 0, 0, 2, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0],      # 第3行 A3
    [0, 4, 0, 13, 7, 0, 1, 0, 0, 0, 0, 11, 0, 12, 0, 0],    # 第4行 A4
    [0, 0, 0, 0, 13, 0, 0, 0, 0, 5, 0, 0, 4, 0, 0, 0],      # 第5行 A5
    [0, 8, 0, 0, 15, 0, 4, 3, 0, 9, 0, 0, 0, 13, 0, 12],    # 第6行 A6
    [14, 0, 4, 6, 0, 0, 12, 0, 2, 0, 0, 0, 0, 3, 0, 0],    # 第7行 A7
    [0, 13, 0, 0, 0, 5, 0, 9, 0, 0, 14, 6, 0, 0, 16, 0],    # 第8行 A8
    [13, 0, 0, 2, 0, 11, 0, 0, 14, 0, 0, 7, 0, 15, 0, 3],    # 第9行 A9
    [0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 8, 0, 7, 0],      # 第10行 A10
    [1, 0, 6, 0, 5, 0, 0, 2, 0, 3, 0, 0, 9, 0, 0, 0],      # 第11行 A11
    [0, 0, 0, 4, 0, 16, 14, 0, 0, 0, 12, 5, 0, 0, 0, 1],    # 第12行 A12
    [15, 0, 0, 0, 12, 0, 0, 0, 5, 1, 0, 3, 0, 6, 0, 7],    # 第13行 A13
    [0, 0, 9, 0, 0, 6, 0, 0, 13, 0, 0, 15, 0, 0, 3, 0],    # 第14行 A14
    [0, 1, 0, 0, 9, 0, 0, 15, 0, 0, 2, 8, 0, 5, 0, 0],    # 第15行 A15
    [0, 0, 2, 0, 0, 0, 5, 0, 0, 14, 0, 0, 1, 0, 10, 15]    # 第16行 A16
]

def count_known_numbers(row):
    """计算每行已知数字的数量和值"""
    known = [v for v in row if v != 0]
    missing = [v for v in range(1, 17) if v not in known]
    return {
        "known_count": len(known),
        "known_values": known,
        "missing_count": len(missing),
        "missing_values": sorted(missing)
    }

def load_permutations(row_num):
    """加载指定行的排列数据"""
    filename = f"A{row_num}_permutations.json"
    filepath = os.path.join(WORK_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_row_match(row_idx, row_data, permutations):
    """验证行数据与排列的匹配情况"""
    known_values = [v for v in row_data if v != 0]
    total_perms = len(permutations)
    
    exact_matches = 0
    partial_matches = []
    
    for perm in permutations:
        match_count = 0
        for pos, val in enumerate(row_data):
            if val != 0 and val == perm[pos]:
                match_count += 1
        
        if match_count == len(known_values):
            exact_matches += 1
        elif match_count > 0:
            partial_matches.append((match_count, perm))
    
    return {
        "total_permutations": total_perms,
        "exact_matches": exact_matches,
        "partial_matches_count": len(partial_matches),
        "best_partial": max(partial_matches, key=lambda x: x[0]) if partial_matches else None
    }

def main():
    print("=" * 80)
    print("16行符闔排列与初始盘已知数字验证报告")
    print("=" * 80)
    print()
    
    # 先统计每行已知数字
    print("【步骤1】每行已知数字统计")
    print("-" * 60)
    for i in range(16):
        stats = count_known_numbers(INITIAL_PUZZLE[i])
        print(f"第{i+1:2d}行 (A{i+1:2d}): {stats['known_count']:2d}个已知数字, "
              f"值: {stats['known_values']}")
        print(f"        缺失: {stats['missing_values']}")
    print()
    
    # 统计已知数字总数
    total_known = sum(count_known_numbers(row)["known_count"] for row in INITIAL_PUZZLE)
    print(f"总计: {total_known}个已知数字 (分布: {[count_known_numbers(row)['known_count'] for row in INITIAL_PUZZLE]})")
    print()
    
    # 验证每行排列匹配
    print("【步骤2】排列匹配验证")
    print("-" * 60)
    
    results = []
    for row_idx in range(16):
        row_num = row_idx + 1
        print(f"\n验证第{row_num}行 (A{row_num})...")
        
        permutations = load_permutations(row_num)
        if permutations is None:
            print(f"  ❌ 文件不存在: A{row_num}_permutations.json")
            results.append({"row": row_num, "status": "file_missing"})
            continue
        
        match_result = verify_row_match(row_idx, INITIAL_PUZZLE[row_idx], permutations)
        
        stats = count_known_numbers(INITIAL_PUZZLE[row_idx])
        status_icon = "✅" if match_result["exact_matches"] > 0 else "❌"
        print(f"  {status_icon} 总排列数: {match_result['total_permutations']:,}")
        print(f"  {status_icon} 完全匹配: {match_result['exact_matches']:,}")
        
        if match_result["partial_matches_count"] > 0:
            best = match_result["best_partial"]
            print(f"  ⚠️  部分匹配: {match_result['partial_matches_count']:,} (最佳: {best[0]}/{len(stats['known_values'])}个数字匹配)")
        
        results.append({
            "row": row_num,
            "status": "match" if match_result["exact_matches"] > 0 else "no_exact_match",
            "total_permutations": match_result["total_permutations"],
            "exact_matches": match_result["exact_matches"],
            "partial_count": match_result["partial_matches_count"]
        })
    
    print("\n" + "=" * 80)
    print("【验证总结】")
    print("-" * 60)
    
    match_rows = [r for r in results if r.get("exact_matches", 0) > 0]
    no_match_rows = [r for r in results if r.get("exact_matches", 0) == 0]
    
    print(f"✅ 完全匹配行数: {len(match_rows)}/16")
    print(f"❌ 无完全匹配行数: {len(no_match_rows)}/16")
    
    if no_match_rows:
        print(f"\n冲突行详情:")
        for r in no_match_rows:
            if r.get("partial_count", 0) > 0:
                print(f"  第{r['row']:2d}行: {r['total_permutations']:,}个排列, 无完全匹配, "
                      f"部分匹配数: {r['partial_count']:,}")
            else:
                print(f"  第{r['row']:2d}行: {r['total_permutations']:,}个排列, 无任何部分匹配")
    
    # 返回JSON供后续分析
    with open(os.path.join(WORK_DIR, "验证行约束匹配结果.json"), 'w', encoding='utf-8') as f:
        json.dump({
            "total_known_numbers": total_known,
            "row_distribution": [count_known_numbers(row)["known_count"] for row in INITIAL_PUZZLE],
            "results": results,
            "summary": {
                "matched_rows": len(match_rows),
                "conflict_rows": len(no_match_rows)
            }
        }, f, indent=2, ensure_ascii=False)
    
    print("\n结果已保存至: 验证行约束匹配结果.json")

if __name__ == "__main__":
    main()
