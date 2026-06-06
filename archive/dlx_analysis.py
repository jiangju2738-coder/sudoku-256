#!/usr/bin/env python3
"""
Dancing Links (DLX) 精确求解与冲突分析 - 优化版

使用高效剪枝和增量验证
"""

import json
import time
from collections import defaultdict
from typing import List, Tuple, Set, Dict
import sys

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"
N = 16
N_BOX = 4


def get_box_id(row: int, col: int) -> int:
    return (row // N_BOX) * N_BOX + (col // N_BOX)


def load_data():
    with open(f"{BASE_DIR}/sudoku_config.json") as f:
        config = json.load(f)
    perms = {}
    for r in range(1, 17):
        with open(f"{BASE_DIR}/A{r}_permutations.json") as f:
            perms[r] = json.load(f)
    return config, perms


def count_solutions_fast(config, perms, limit=1000):
    """快速计数解（带剪枝）"""
    print("\n【DLX 精确计数】")
    print("="*50)
    
    count = 0
    solutions = []
    
    # 预处理：为每行建立排列索引
    row_perms = {r: perms.get(r, []) for r in range(1, 17)}
    
    # 预填已知数字
    fixed = {}  # (r, c) -> v
    for k in config.get("known_digits", []):
        fixed[(k["row"]-1, k["col"]-1)] = k["value"]
    
    # 构建每行的约束（哪些排列符合已知数字）
    constrained_perms = {}
    for r in range(16):
        row_num = r + 1
        row_known = [(fc, v) for (fr, fc), v in fixed.items() if fr == r]
        
        valid = []
        for perm in row_perms.get(row_num, []):
            ok = all(perm[c] == v for c, v in row_known)
            if ok:
                valid.append(perm)
        constrained_perms[r] = valid
        print(f"  Row {r+1:2d}: {len(perms.get(row_num, [])):>6,} → {len(valid):>6,}")
    
    # 快速计数：递归 + 剪枝
    col_used = [set() for _ in range(16)]
    box_used = [set() for _ in range(16)]
    
    # 预填已知数字
    for (r, c), v in fixed.items():
        col_used[c].add(v)
        box_used[get_box_id(r, c)].add(v)
    
    def search(r):
        nonlocal count, solutions
        
        if count >= limit:
            return True
        
        if r == 16:
            count += 1
            if len(solutions) < 5:
                solutions.append(1)  # 只计数
            return False
        
        for perm in constrained_perms[r]:
            # 检查列
            ok = True
            for c in range(16):
                if perm[c] in col_used[c]:
                    ok = False
                    break
            if not ok:
                continue
            
            # 检查宫
            for c in range(16):
                if perm[c] in box_used[get_box_id(r, c)]:
                    ok = False
                    break
            if not ok:
                continue
            
            # 放置
            for c in range(16):
                col_used[c].add(perm[c])
                box_used[get_box_id(r, c)].add(perm[c])
            
            if search(r + 1):
                return True
            
            # 回溯
            for c in range(16):
                col_used[c].remove(perm[c])
                box_used[get_box_id(r, c)].remove(perm[c])
        
        return False
    
    start = time.time()
    search(0)
    elapsed = time.time() - start
    
    print(f"\n结果：")
    print(f"  解数：{count}")
    print(f"  时间：{elapsed:.2f}s")
    print(f"  速率：{count/max(elapsed, 0.01):.0f} 解/秒")
    
    return count, solutions


def analyze_single_sources(config, perms):
    """分析单源值"""
    print("\n【单源值冲突分析】")
    print("="*50)
    
    # 值→列→行的映射
    val_col_row = defaultdict(lambda: defaultdict(set))
    
    for row_num in range(1, 17):
        for perm in perms.get(row_num, []):
            for c in range(16):
                val_col_row[perm[c]][c].add(row_num - 1)
    
    single_source = {}
    row_load = defaultdict(list)
    
    for v in range(1, 17):
        for c in range(16):
            rows = val_col_row[v][c]
            if len(rows) == 1:
                r = list(rows)[0]
                single_source[(c, v)] = r
                row_load[r].append((c, v))
    
    print(f"\n单源值总计：{len(single_source)} 个")
    print(f"\n各行单源值数量：")
    for r in range(16):
        cnt = len(row_load[r])
        pct = cnt / len(perms.get(r+1, [])) * 100 if perms.get(r+1) else 0
        print(f"  Row {r+1:2d}: {cnt:3d} ({pct:.1f}%)")
    
    # 找出最严重冲突
    print(f"\n最严重冲突（每列单源值数）：")
    col_load = defaultdict(int)
    for (c, v), r in single_source.items():
        col_load[c] += 1
    
    for c in sorted(col_load.keys(), key=lambda x: -col_load[x])[:5]:
        vals = [(v, single_source[(c, v)]) for v in range(1, 17) if (c, v) in single_source]
        print(f"  Col {c+1:2d}: {col_load[c]} 个单源值")
        for v, r in vals[:3]:
            print(f"      值 {v} ← Row {r+1}")
    
    return single_source, row_load, col_load


def refine_perms_remove_conflicts(config, perms, single_source):
    """重新提取排列，去除冲突"""
    print("\n【重新提取排列（去除冲突）】")
    print("="*50)
    
    # 分析：哪些单源值造成问题
    problem_single = []
    
    for (c, v), r in single_source.items():
        # 检查 Row r 是否有排列在 Col c 位置能放置值 v
        has_support = any(perm[c] == v for perm in perms.get(r+1, []))
        if not has_support:
            problem_single.append((c, v, r))
    
    print(f"\n发现 {len(problem_single)} 个冲突单源值：")
    for c, v, r in problem_single[:10]:
        print(f"  Col {c+1}, 值 {v} ← Row {r+1} (但该行排列不支持)")
    
    # 过滤：移除冲突的单源值
    safe_single = {k: v for k, v in single_source.items() if k not in [(c, v) for c, v, _ in problem_single]}
    
    print(f"\n安全单源值：{len(safe_single)} 个（移除 {len(problem_single)} 个冲突）")
    
    return safe_single, problem_single


def main():
    print("="*70)
    print("符阖排列 16x16 数独 - DLX 精确分析与冲突修复")
    print("="*70)
    
    config, perms = load_data()
    total = sum(len(perms.get(r, [])) for r in range(1, 17))
    print(f"\n数据加载完成：")
    print(f"  已知数字：{len(config.get('known_digits', []))} 个")
    print(f"  排列总数：{total:,} 个")
    
    # 任务 1：计数
    count, solutions = count_solutions_fast(config, perms, limit=100)
    
    # 任务 2：单源值分析
    single_source, row_load, col_load = analyze_single_sources(config, perms)
    
    # 任务 3：重新提取
    safe_single, problems = refine_perms_remove_conflicts(config, perms, single_source)
    
    # 总结
    print("\n" + "="*70)
    print("总结")
    print("="*70)
    
    status = "❌ 无解" if count == 0 else f"✅ 找到 {count} 个解"
    print(f"""
【结果】
  1. 解的数量：{status}
  2. 单源值：{len(single_source)} 个
  3. 冲突单源值：{len(problems)} 个
  4. 安全单源值：{len(safe_single)} 个

【结论】
  {'问题在于约束集本身不可满足' if count == 0 else '约束集可满足，存在解'}

【建议】
  {'- 检查排列提取是否正确' if count == 0 else '- 可继续搜索更多解'}
  {'- 或重新设计 Level 2 的已知数字' if count == 0 else '- 用 DLX 精确计数完整解空间'}
""")
    
    # 保存结果
    result = {
        "solution_count": count,
        "single_source_count": len(single_source),
        "conflict_count": len(problems),
        "safe_single_count": len(safe_single),
        "problems": [(c+1, v, r+1) for c, v, r in problems[:20]]
    }
    
    with open(f"{BASE_DIR}/dlx_result.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"结果已保存：dlx_result.json")


if __name__ == "__main__":
    main()
