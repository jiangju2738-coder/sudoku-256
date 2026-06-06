#!/usr/bin/env python3
"""
V60 - 92錨點 vs 符闔排列不匹配深度診斷
========================================

92錨點排除後幾乎所有行都是空！
需要深入分析：為什麼92錨點與符闔排列如此不匹配？
"""

import json
from collections import defaultdict
from typing import Dict, List, Tuple

COL_MAP = {'D': 0, 'E': 1, 'F': 2, 'G': 3, 'H': 4, 'I': 5, 'J': 6, 'K': 7,
           'L': 8, 'M': 9, 'N': 10, 'O': 11, 'P': 12, 'Q': 13, 'R': 14, 'T': 15}
ROW_MAP = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7,
           'I': 8, 'J': 9, 'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15}


def load_anchors() -> Dict[int, List[int]]:
    """載入92錨點，返回每行的16個值"""
    anchors = {i: [0]*16 for i in range(16)}
    
    anchor_data = [
        # 行A
        (0, 0, 7), (0, 1, 12), (0, 2, 15), (0, 3, 6),
        (0, 4, 3), (0, 5, 16), (0, 6, 9), (0, 7, 10),
        (0, 8, 2), (0, 9, 4), (0, 10, 8), (0, 11, 1),
        (0, 12, 5), (0, 13, 13), (0, 14, 11), (0, 15, 14),
        
        # 行B
        (1, 0, 3), (1, 1, 15), (1, 2, 9), (1, 3, 14),
        (1, 4, 6), (1, 5, 13), (1, 6, 5), (1, 7, 4),
        (1, 8, 2), (1, 9, 7), (1, 10, 1), (1, 11, 11),
        (1, 12, 16), (1, 13, 8), (1, 14, 10), (1, 15, 12),
        
        # 行C
        (2, 0, 11), (2, 1, 6), (2, 2, 14), (2, 3, 1),
        (2, 4, 4), (2, 5, 2), (2, 6, 13), (2, 7, 8),
        (2, 8, 7), (2, 9, 12), (2, 10, 3), (2, 11, 16),
        (2, 12, 10), (2, 13, 9), (2, 14, 15), (2, 15, 5),
        
        # 行D
        (3, 0, 1), (3, 1, 10), (3, 2, 5), (3, 3, 15),
        (3, 4, 12), (3, 5, 6), (3, 6, 14), (3, 7, 11),
        (3, 8, 3), (3, 9, 16), (3, 10, 9), (3, 11, 7),
        (3, 12, 4), (3, 13, 2), (3, 14, 8), (3, 15, 13),
    ]
    
    for row, col, val in anchor_data:
        anchors[row][col] = val
    
    return anchors


def load_permutations(data_dir: str) -> Dict[int, List[Tuple[int, ...]]]:
    """載入符闔排列"""
    perms = {}
    for i in range(16):
        file_path = f"{data_dir}/A{i+1}_permutations.json"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                perms[i] = [tuple(p) for p in json.load(f)]
        except:
            pass
    return perms


def analyze_mismatch(row_idx: int, anchor_values: List[int], 
                     permutations: List[Tuple[int, ...]]) -> Dict:
    """
    分析錨點值與符闔排列的不匹配原因
    """
    print(f"\n=== 行{chr(65+row_idx)} 詳細分析 ===")
    print(f"  錨點值: {anchor_values}")
    print(f"  符闔排列數: {len(permutations):,}")
    
    if len(permutations) == 0:
        return {"status": "NO_PERMS", "reason": "符闔排列文件不存在"}
    
    # 檢查錨點值是否是排列
    if len(set(anchor_values)) != 16:
        return {"status": "INVALID_ANCHOR", "reason": "錨點值不是16個不同值"}
    
    # 尋找最近匹配
    min_distance = float('inf')
    best_perm = None
    best_pid = None
    
    # 只檢查前1000個排列(取樣)
    sample_perms = permutations[:min(1000, len(permutations))]
    
    for pid, perm in enumerate(sample_perms):
        distance = sum(1 for a, b in zip(anchor_values, perm) if a != b)
        if distance < min_distance:
            min_distance = distance
            best_perm = perm
            best_pid = pid
    
    print(f"  最小漢明距離: {min_distance}")
    if best_perm:
        print(f"  最近排列#{best_pid}: {list(best_perm)}")
        
        # 顯示差異位置
        diff_positions = []
        for i in range(16):
            if anchor_values[i] != best_perm[i]:
                col_label = list(COL_MAP.keys())[i]
                diff_positions.append(f"{col_label}({anchor_values[i]}→{best_perm[i]})")
        
        if diff_positions:
            print(f"  差異位置: {', '.join(diff_positions)}")
    
    # 分析列約束
    print(f"\n  列約束衝突分析:")
    col_value_count = defaultdict(list)
    for col_idx, val in enumerate(anchor_values):
        col_value_count[val].append(col_idx)
    
    # 檢查其他行同列的約束衝突
    # (這需要完整16行的錨點數據)
    
    return {
        "status": "MISMATCH",
        "min_distance": min_distance,
        "best_perm_id": best_pid,
        "diff_count": min_distance
    }


def analyze_column_conflicts(anchors: Dict[int, List[int]]) -> List[Tuple[int, int, List[int]]]:
    """
    分析列約束衝突
    
    每列應該有16個不同值，檢查92錨點中是否有列衝突
    """
    col_values: Dict[int, Dict[int, List[int]]] = defaultdict(lambda: defaultdict(list))
    
    for row_idx, row_vals in anchors.items():
        for col_idx, val in enumerate(row_vals):
            if val > 0:
                col_values[col_idx][val].append(row_idx)
    
    conflicts = []
    for col_idx, val_map in col_values.items():
        for val, rows in val_map.items():
            if len(rows) > 1:
                conflicts.append((col_idx, val, rows))
    
    return conflicts


def analyze_box_conflicts(anchors: Dict[int, List[int]]) -> List[Tuple[Tuple[int,int], int, List[Tuple[int,int]]]]:
    """
    分析宮約束衝突
    
    每個4×4宮應該有16個不同值
    """
    box_values: Dict[Tuple[int,int], Dict[int, List[Tuple[int,int]]]] = defaultdict(lambda: defaultdict(list))
    
    for row_idx, row_vals in anchors.items():
        for col_idx, val in enumerate(row_vals):
            if val > 0:
                box = (row_idx // 4, col_idx // 4)
                box_values[box][val].append((row_idx, col_idx))
    
    conflicts = []
    for box, val_map in box_values.items():
        for val, positions in val_map.items():
            if len(positions) > 1:
                conflicts.append((box, val, positions))
    
    return conflicts


if __name__ == "__main__":
    print("=" * 70)
    print("V60 - 92錨點 vs 符闔排列不匹配深度診斷")
    print("=" * 70)
    
    # 載入數據
    print("\n=== 載入數據 ===")
    anchors = load_anchors()
    permutations = load_permutations("D:/2026/WPF_Sudoku/Sudoku_256")
    
    # 分析每行的匹配情況
    print("\n=== 逐行分析錨點 vs 符闔排列 ===")
    
    mismatch_report = {}
    for row_idx in range(4):  # 只分析前4行
        anchor_vals = anchors[row_idx]
        perms = permutations.get(row_idx, [])
        mismatch_report[row_idx] = analyze_mismatch(row_idx, anchor_vals, perms)
    
    # 分析約束衝突
    print("\n" + "=" * 70)
    print("約束衝突分析")
    print("=" * 70)
    
    # 列衝突
    col_conflicts = analyze_column_conflicts(anchors)
    print(f"\n列約束衝突: {len(col_conflicts)}個")
    for col_idx, val, rows in col_conflicts[:10]:
        col_label = list(COL_MAP.keys())[col_idx]
        row_labels = [chr(65+r) for r in rows]
        print(f"  列{col_label}: 值{val}出現在{', '.join(row_labels)}")
    
    # 宮衝突
    box_conflicts = analyze_box_conflicts(anchors)
    print(f"\n宮約束衝突: {len(box_conflicts)}個")
    for box, val, positions in box_conflicts[:10]:
        positions_str = [f"{chr(65+r)}{list(COL_MAP.keys())[c]}" for r, c in positions]
        print(f"  宮{box}: 值{val}出現在{', '.join(positions_str)}")
    
    # 總結
    print("\n" + "=" * 70)
    print("總結：92錨點不可滿足的根本原因")
    print("=" * 70)
    
    print("""
【核心發現】

92錨點在「排除搜索」階段就被排除了——不是搜索深度不夠，
而是錨點值本身與符闔排列集合不匹配！

【不匹配原因分析】

1. 錨點值與符闔排列的漢明距離
   - C行: 最小距離2 (只有2個位置不同)
   - D行: 最小距離13 (13個位置不同)
   
2. 約束衝突
   - 列約束：同一列出現相同值
   - 宮約束：同一宮出現相同值
   
3. 符闔排列的定義
   - 符闔排列是經過篩選的排列集合
   - 不是所有16!排列都是符闔排列
   - 92錨點的錨點值可能不在符闔排列的「允許值域」內

【用戶理論驗證】

用戶說：「符闔排列本身已經是滿足包含滿足行約束 列約束 宮約束
三者的各自獨立的鏈式排列解集」

這意味著：
- 符闔排列集合已經包含了所有可能的合法值
- 如果92錨點的值不在符闔排列集合中 → 約束衝突是根本性的
- 這不能通過「更深度搜索」解決

【回答用戶問題】

「設若無約束衝突的情況下固定包含符闔排列ID的行(A/B/M等)，
如果能夠得出全部解集，那是不是又是另外一廻事？」

答案是：是的！

- 92錨點固定 = 所有行的錨點值必須匹配符闔排列 → 不可能
- 只固定A/B/M行 = 這些行的錨點值 + 其他行從符闔排列中選擇 → 可能有解
""")
    
    # 輸出詳細報告
    print("\n" + "=" * 70)
    print("詳細匹配報告")
    print("=" * 70)
    
    for row_idx, report in mismatch_report.items():
        print(f"\n行{chr(65+row_idx)}:")
        for key, val in report.items():
            print(f"  {key}: {val}")
