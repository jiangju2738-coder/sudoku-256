#!/usr/bin/env python3
"""
符闔排列重度比對分析
分析92個已知數字約束下的排列過濾情況
檢查是否存在16行A1-A16的數據重疊
"""

import json
import re
from datetime import datetime
from collections import defaultdict

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"


def parse_grid_from_txt():
    """從txt文件解析92個已知數字"""
    with open(f"{BASE_DIR}/超級大數獨_box_size4.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    grid = []
    
    for line in lines[2:]:
        line = line.strip()
        if not line:
            continue
        numbers = re.findall(r'\d+', line)
        numbers = [int(x) for x in numbers]
        if len(numbers) == 16:
            grid.append(numbers)
        if len(grid) >= 16:
            break
    
    known_digits = []
    for r in range(16):
        for c in range(16):
            if grid[r][c] != 0:
                known_digits.append({
                    "row": r+1,
                    "col": c+1,
                    "value": grid[r][c],
                    "cell_num": r*16 + c + 1,
                    "box": (r//4)*4 + (c//4) + 1
                })
    
    return grid, known_digits


def load_fuhe_perms():
    """加載所有符闔排列"""
    perms = {}
    total = 0
    for r in range(1, 17):
        with open(f"{BASE_DIR}/A{r}_permutations.json") as f:
            perms[r] = json.load(f)
        total += len(perms[r])
    return perms, total


def analyze_perm_filtering(known_digits, perms):
    """分析排列過濾過程"""
    print("="*70)
    print("符闔排列重度比對分析")
    print("="*70)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 過濾每行有效排列
    fixed = {(k["row"]-1, k["col"]-1): k["value"] for k in known_digits}
    
    print("\n【第一階段】排列過濾分析")
    print("-"*70)
    
    filtered_perms = {}
    filtering_stats = []
    
    for r in range(1, 17):
        row_num = r
        row_known = [(fc, v) for (fr, fc), v in fixed.items() if fr == r]
        
        total = len(perms.get(row_num, []))
        valid = []
        
        for perm in perms.get(row_num, []):
            ok = all(perm[c] == v for c, v in row_known)
            if ok:
                valid.append(perm)
        
        filtered_perms[r] = valid
        pct = len(valid)/total*100 if total > 0 else 0
        
        filtering_stats.append({
            "row": r,
            "total": total,
            "valid": len(valid),
            "filtered_out": total - len(valid),
            "retention_rate": pct
        })
        
        status = "✓" if len(valid) > 0 else "❌"
        print(f"  行{r:2d}: {total:>8,} → {len(valid):>8,} ({pct:>6.2f}%) {status}")
    
    # 檢查空行
    empty_rows = [s["row"] for s in filtering_stats if s["valid"] == 0]
    
    if empty_rows:
        print(f"\n❌ 嚴重問題: 行 {empty_rows} 無有效排列！")
        print("   這表明92個已知數字與符闔排列存在根本衝突")
    
    # 檢查過度約束
    over_constrained = [s for s in filtering_stats if s["retention_rate"] < 1 and s["total"] > 0]
    if over_constrained:
        print(f"\n⚠️ 過度約束的行 ({len(over_constrained)}個):")
        for s in over_constrained:
            print(f"    行{s['row']}: 只剩{s['valid']}個排列 ({s['retention_rate']:.3f}%)")
    
    return filtered_perms, filtering_stats, empty_rows


def analyze_cross_row_overlap(filtered_perms):
    """分析跨行重疊"""
    print("\n【第二階段】跨行重疊分析")
    print("-"*70)
    
    # 統計每個排列在哪些行出現
    perm_to_rows = defaultdict(set)
    
    for r, perms in filtered_perms.items():
        for perm in perms:
            perm_tuple = tuple(perm)
            perm_to_rows[perm_tuple].add(r)
    
    # 分類排列
    unique_perms = []  # 只出現在一行
    shared_perms = []  # 出現在多行
    
    for perm, rows in perm_to_rows.items():
        if len(rows) == 1:
            unique_perms.append({"perm": list(perm), "row": list(rows)[0]})
        else:
            shared_perms.append({"perm": list(perm), "rows": sorted(rows)})
    
    print(f"\n有效排列總數: {len(perm_to_rows)}")
    print(f"唯一行排列: {len(unique_perms)}")
    print(f"跨行重疊排列: {len(shared_perms)}")
    
    if shared_perms:
        print(f"\n⚠️ 跨行重疊詳情 (前10個):")
        for item in shared_perms[:10]:
            print(f"  排列{item['perm'][:4]}... → 出現在行: {item['rows']}")
    
    if len(unique_perms) == 16:
        print(f"\n✅ 理想狀態: 每行都有唯一符闔排列")
    else:
        print(f"\n⚠️ 非理想: 只有{len(unique_perms)}個唯一行排列")
    
    return {
        "total_unique_permutations": len(perm_to_rows),
        "unique_to_one_row": len(unique_perms),
        "shared_by_multiple_rows": len(shared_perms),
        "shared_details": shared_perms[:20]
    }


def analyze_row_overlap_with_original(filtered_perms, perms):
    """分析求解行與原始符闔排列的重疊"""
    print("\n【第三階段】求解行與原始符闔排列重疊分析")
    print("-"*70)
    
    # 注意：由於DLX求解結果為0解，我們分析的是過濾後的排列集
    # 而非實際求解終盤
    
    print("\n注意: 由於DLX求解結果為0解，以下分析基於過濾後的排列集")
    print("而非實際求解終盤。實際終盤需在有解時進行此分析。")
    
    overlap_analysis = {
        "analysis_type": "filtered_perms",
        "note": "基於排列過濾結果，非實際求解終盤",
        "per_row_overlap": []
    }
    
    for r in range(1, 17):
        valid_count = len(filtered_perms.get(r, []))
        original_count = len(perms.get(r, []))
        
        if valid_count > 0:
            # 檢查有效排列是否都在原始集中
            all_in_original = all(
                perm in perms.get(r, []) 
                for perm in filtered_perms[r]
            )
        else:
            all_in_original = False
        
        overlap_analysis["per_row_overlap"].append({
            "row": r,
            "valid_perms": valid_count,
            "original_perms": original_count,
            "all_in_original": all_in_original,
            "overlap_rate": valid_count/original_count*100 if original_count > 0 else 0
        })
    
    return overlap_analysis


def generate_conclusion(filtering_stats, overlap_result, empty_rows):
    """生成結論"""
    print("\n" + "="*70)
    print("【深度研究結論】")
    print("="*70)
    
    # 約束分析
    total_valid = sum(s["valid"] for s in filtering_stats)
    total_original = sum(s["total"] for s in filtering_stats)
    
    print(f"""
【核心發現】

1. 約束系統狀態: {'❌ 不可滿足 (0解)' if empty_rows else '✓ 可能可滿足'}
   
   {'⚠️ 存在空行，約束衝突'} if empty_rows else '✓ 所有行至少有一個有效排列'

2. 排列過濾統計:
   - 原始排列總數: {total_original:,}
   - 過濾後有效: {total_valid:,}
   - 過濾比例: {(total_original-total_valid)/total_original*100:.2f}%

3. 跨行重疊特徵:
   - 有效唯一排列: {overlap_result['unique_to_one_row']}
   - 跨行共享排列: {overlap_result['shared_by_multiple_rows']}

{'⚠️ 關鍵問題:' if empty_rows else '✓ 系統狀態:'}
""")
    
    if empty_rows:
        print("""
   ❌ 92個已知數字造成過度約束:
      - 某些行的排列選擇空間被完全壓縮至零
      - 列AllDifferent約束與符闔排列約束產生衝突
      - 單源值鎖定鏈形成全局不可滿足結構
   
   💡 優化建議:
      1. 減少已知數字至40-60個（15-23%填滿率）
      2. 重新提取符闔排列，確保約束相容
      3. 分析MIS（不可滿足子集）定位衝突根源
      4. 使用CP-SAT進行可行性預檢
""")
    else:
        print("""
   ✓ 約束系統基本相容，可繼續求解
   
   💡 優化建議:
      1. 繼續使用DLX進行精確計數
      2. 分析多解空間特徵
      3. 開發符闔排列生成算法
""")
    
    print(f"""
【研究方向】

1. 符闔排列理論:
   - 基於約束相容的排列生成算法
   - 排列集設計的最優密度研究
   - 單源值分布的均衡性分析

2. 求解算法優化:
   - DLX+CP-SAT混合求解策略
   - 增量約束求解
   - 多解空間采样

3. 博弈分析:
   - 零和博弈下的解存在性
   - 玩家策略的最優響應
   - 約束密度與解空間的相變

4. 應用擴展:
   - 16×16→25×25擴展
   - 多符闔類型整合
   - 動態約束系統
""")


def main():
    # 解析數據
    grid, known_digits = parse_grid_from_txt()
    perms, total_perms = load_fuhe_perms()
    
    print(f"\n📊 數據概覽:")
    print(f"   已知數字: {len(known_digits)} 個")
    print(f"   符闔排列: {total_perms:,} 個")
    
    # 排列過濾分析
    filtered_perms, filtering_stats, empty_rows = analyze_perm_filtering(known_digits, perms)
    
    # 跨行重疊分析
    overlap_result = analyze_cross_row_overlap(filtered_perms)
    
    # 與原始排列比對
    original_overlap = analyze_row_overlap_with_original(filtered_perms, perms)
    
    # 生成結論
    generate_conclusion(filtering_stats, overlap_result, empty_rows)
    
    # 保存完整報告
    report = {
        "timestamp": datetime.now().isoformat(),
        "sudoku_data": {
            "known_digits_count": len(known_digits),
            "fill_rate": round(len(known_digits)/256*100, 1)
        },
        "fuhe_permutations": {
            "total": total_perms,
            "per_row": {str(r): len(perms[r]) for r in range(1, 17)}
        },
        "filtering_analysis": filtering_stats,
        "cross_row_overlap": overlap_result,
        "original_overlap": original_overlap,
        "empty_rows": empty_rows,
        "conclusion": {
            "status": "infeasible" if empty_rows else "feasible",
            "empty_row_count": len(empty_rows),
            "total_valid_perms": sum(s["valid"] for s in filtering_stats)
        }
    }
    
    with open(f"{BASE_DIR}/perm_overlap_analysis.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n✅ 比對分析報告已保存: perm_overlap_analysis.json")
    
    return report


if __name__ == "__main__":
    result = main()
