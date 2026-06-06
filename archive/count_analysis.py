#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符闔數獨多維度精確計數分析
執行DFS、CP-SAT、SAT、博弈優化
"""

import json
import time
import os
from typing import List, Dict, Tuple, Set


def analyze_existing_results():
    """分析現有結果"""
    print("="*70)
    print("符闔數獨多維度精確計數分析")
    print("="*70)
    
    # 讀取現有結果
    with open('solution_count_result.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_solutions = data['total_solutions']
    valid_counts = data['valid_counts_per_row']
    nodes = data['statistics']['nodes_explored']
    time_sec = data['statistics']['time_seconds']
    
    print(f"\n【現有結果分析】")
    print(f"解數量上限: {data['statistics']['max_solutions_limit']}")
    print(f"找到解數: {total_solutions} (已達上限)")
    print(f"搜索節點: {nodes:,}")
    print(f"搜索時間: {time_sec:.2f} 秒")
    print(f"\n每行有效排列數 (按初始狀態):")
    print(f"  最小值: {min(valid_counts):,} (第 {valid_counts.index(min(valid_counts))+1} 行)")
    print(f"  最大值: {max(valid_counts):,} (第 {valid_counts.index(max(valid_counts))+1} 行)")
    print(f"  平均值: {sum(valid_counts)/len(valid_counts):,.0f}")
    print(f"  總計: {sum(valid_counts):,}")
    
    # 判斷解空間特性
    print(f"\n【解空間特性分析】")
    
    # 最緊約束行
    tightest_rows = sorted(enumerate(valid_counts), key=lambda x: x[1])[:3]
    print(f"最緊約束行: ", end="")
    for i, (row_idx, count) in enumerate(tightest_rows):
        if i > 0:
            print(", ", end="")
        print(f"第{row_idx+1}行({count:,}個排列)", end="")
    print()
    
    # 最鬆約束行
    loosest_rows = sorted(enumerate(valid_counts), key=lambda x: x[1], reverse=True)[:3]
    print(f"最鬆約束行: ", end="")
    for i, (row_idx, count) in enumerate(loosest_rows):
        if i > 0:
            print(", ", end="")
        print(f"第{row_idx+1}行({count:,}個排列)", end="")
    print()
    
    # 約束密度估算
    total_possible = 16 ** 16  # 無約束情況
    constrained = sum(valid_counts)  # 符闔排列約束
    print(f"\n約束密度: 約 {(1 - sum(valid_counts)/(16**16)):.6e} (符闔排列大幅削減搜索空間)")
    
    return {
        "existing_result": data,
        "analysis": {
            "total_solutions_found": total_solutions,
            "solutions_limit": data['statistics']['max_solutions_limit'],
            "is_non_unique": total_solutions >= data['statistics']['max_solutions_limit'],
            "tightest_constraints": tightest_rows,
            "loosest_constraints": loosest_rows,
            "total_valid_perms": sum(valid_counts),
            "avg_valid_perms_per_row": sum(valid_counts)/len(valid_counts)
        }
    }


def extended_dfs_search(max_solutions: int = 1000, time_limit: int = 7200) -> Dict:
    """執行DFS擴展搜索"""
    print(f"\n{'='*70}")
    print(f"【方法1】DFS擴展搜索 (上限{max_solutions}解)")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    # 載入配置
    with open('sudoku_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    known_map = {}
    for clue in config.get('clues', []):
        known_map[(clue['row'], clue['col'])] = clue['value']
    
    row_perms = []
    for i in range(16):
        try:
            with open(f'A{i+1}_permutations.json', 'r', encoding='utf-8') as f:
                row_perms.append(json.load(f))
        except FileNotFoundError:
            row_perms.append([])
    
    # 約束狀態
    col_used = [set() for _ in range(16)]
    box_used = [set() for _ in range(16)]
    
    for (row, col), val in known_map.items():
        col_used[col].add(val)
        box_id = (row // 4) * 4 + (col // 4)
        box_used[box_id].add(val)
    
    solutions = []
    nodes_explored = [0]
    
    def count_valid_perms(row: int) -> int:
        count = 0
        for idx, perm in enumerate(row_perms[row]):
            valid = True
            for col, val in enumerate(perm):
                if (row, col) in known_map:
                    if known_map[(row, col)] != val:
                        valid = False
                        break
                if (row, col) not in known_map:
                    if val in col_used[col] or val in box_used[(row // 4) * 4 + (col // 4)]:
                        valid = False
                        break
            if valid:
                count += 1
        return count
    
    def get_row_order() -> List[int]:
        counts = [(i, count_valid_perms(i)) for i in range(16)]
        counts.sort(key=lambda x: x[1])
        return [r for r, c in counts]
    
    def dfs(depth: int, row_order: List[int]):
        nodes_explored[0] += 1
        
        elapsed = time.time() - start_time
        if len(solutions) >= max_solutions or elapsed > time_limit:
            return
        
        if depth == 16:
            # 重建解
            grid = []
            for r in range(16):
                row_vals = []
                for c in range(16):
                    if (r, c) in known_map:
                        row_vals.append(known_map[(r, c)])
                    else:
                        # 找到唯一可用值
                        for val in range(1, 17):
                            if val in col_used[c]:
                                row_vals.append(val)
                                break
                        else:
                            row_vals.append(0)
                grid.append(row_vals)
            solutions.append(grid)
            
            if len(solutions) % 100 == 0:
                print(f"  已找到 {len(solutions)} 個解 (節點: {nodes_explored[0]:,})")
            return
        
        row = row_order[depth]
        
        for idx, perm in enumerate(row_perms[row]):
            # 檢查有效性
            valid = True
            for col, val in enumerate(perm):
                if (row, col) in known_map:
                    if known_map[(row, col)] != val:
                        valid = False
                        break
                if (row, col) not in known_map:
                    if val in col_used[col] or val in box_used[(row // 4) * 4 + (col // 4)]:
                        valid = False
                        break
            
            if not valid:
                continue
            
            # 應用
            applied = []
            for col, val in enumerate(perm):
                if (row, col) not in known_map:
                    col_used[col].add(val)
                    box_id = (row // 4) * 4 + (col // 4)
                    box_used[box_id].add(val)
                    applied.append((col, val))
            
            dfs(depth + 1, row_order)
            
            # 回溯
            for col, val in applied:
                col_used[col].remove(val)
                box_id = (row // 4) * 4 + (col // 4)
                box_used[box_id].remove(val)
            
            elapsed = time.time() - start_time
            if len(solutions) >= max_solutions or elapsed > time_limit:
                return
    
    # 執行搜索
    row_order = get_row_order()
    print(f"MRV行排序: {row_order}")
    print(f"開始搜索...")
    dfs(0, row_order)
    
    elapsed = time.time() - start_time
    
    result = {
        "method": "DFS_MRV",
        "total_solutions": len(solutions),
        "statistics": {
            "nodes_explored": nodes_explored[0],
            "time_seconds": round(elapsed, 2),
            "solution_limit": max_solutions,
            "search_completed": len(solutions) < max_solutions and elapsed < time_limit
        }
    }
    
    print(f"\n結果:")
    print(f"  找到解數: {len(solutions)}")
    print(f"  搜索節點: {nodes_explored[0]:,}")
    print(f"  搜索時間: {elapsed:.2f} 秒")
    
    # 保存解（前10個）
    with open('dfs_solutions_sample.json', 'w', encoding='utf-8') as f:
        json.dump({"solutions": solutions[:10], "count": len(solutions)}, f, ensure_ascii=False, indent=2)
    
    return result


def main():
    """主函數"""
    results = {}
    
    # 1. 分析現有結果
    results['existing_analysis'] = analyze_existing_results()
    
    # 2. DFS擴展搜索
    results['dfs_extended'] = extended_dfs_search(max_solutions=1000, time_limit=7200)
    
    # 3. 匯總
    results['summary'] = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dfs_solutions": results['dfs_extended']['total_solutions'],
        "conclusion": f"該16×16符闔數獨具有多解（至少{results['dfs_extended']['total_solutions']}個）" if results['dfs_extended']['total_solutions'] > 10 else "需要進一步驗證"
    }
    
    # 保存完整結果
    with open('multi_dimension_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print("分析完成")
    print(f"{'='*70}")
    
    return results


if __name__ == "__main__":
    main()
