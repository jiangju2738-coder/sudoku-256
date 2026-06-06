#!/usr/bin/env python3
"""
基于已知数字重新提取排列，并去除锁定冲突

方法：
1. 对每行，只保留符合已知数字的排列
2. 计算新的单源值
3. 对"过度锁定"的行，放宽约束
"""

import json
from collections import defaultdict

BASE_DIR = "D:/2026/WPF_Sudoku/Sudoku_256"
N = 16


def load_data():
    with open(f"{BASE_DIR}/sudoku_config.json") as f:
        config = json.load(f)
    perms = {}
    for r in range(1, 17):
        with open(f"{BASE_DIR}/A{r}_permutations.json") as f:
            perms[r] = json.load(f)
    return config, perms


def extract_with_known_digits(config, perms):
    """基于已知数字提取排列"""
    refined = {}
    
    for row_num in range(1, 17):
        r = row_num - 1
        
        # 获取该行已知数字
        known = [(k["col"]-1, k["value"]) for k in config["known_digits"] if k["row"] == row_num]
        
        if not known:
            refined[row_num] = perms.get(row_num, [])[:]
            continue
        
        # 筛选排列
        valid = []
        for perm in perms.get(row_num, []):
            if all(perm[c] == v for c, v in known):
                valid.append(perm)
        
        refined[row_num] = valid
    
    return refined


def compute_single_sources(perms):
    """计算单源值"""
    val_col_sources = defaultdict(lambda: defaultdict(set))
    
    for row_num in range(1, 17):
        for perm in perms.get(row_num, []):
            for c in range(N):
                val_col_sources[perm[c]][c].add(row_num - 1)
    
    single_source = {}
    for v in range(1, 17):
        for c in range(N):
            rows = val_col_sources[v][c]
            if len(rows) == 1:
                single_source[(c, v)] = list(rows)[0]
    
    return single_source


def remove_over_locked_rows(perms, single_source, max_ss_per_row=5):
    """去除过度锁定的行"""
    
    # 计算每行的单源值负载
    row_load = defaultdict(list)
    for (c, v), r in single_source.items():
        row_load[r].append((c, v))
    
    # 找出过度锁定的行
    over_locked = [(r, len(ss)) for r, ss in row_load.items() if len(ss) > max_ss_per_row]
    
    print(f"过度锁定的行：{over_locked}")
    
    # 对这些行，放宽单源值约束
    # 方法：从排列集中随机移除一些单源值
    new_single_source = single_source.copy()
    
    for r, count in over_locked:
        row_num = r + 1
        # 移除一些单源值
        to_remove = count - max_ss_per_row
        ss_list = row_load[r]
        
        print(f"\nRow {row_num}: 移除 {to_remove} 个单源值")
        
        for i in range(to_remove):
            c, v = ss_list[i]
            del new_single_source[(c, v)]
            print(f"  移除：Col {c+1}, 值 {v}")
    
    return new_single_source, over_locked


def verify_with_relaxed(perms, single_source):
    """用放松后的约束验证"""
    print("\n【验证放松后的约束】")
    
    # 快速计数
    col_used = [set() for _ in range(16)]
    box_used = [set() for _ in range(16)]
    
    count = 0
    
    def search(r):
        nonlocal count
        if count >= 10:
            return True
        if r == 16:
            count += 1
            return False
        
        for perm in perms.get(r+1, []):
            ok = True
            for c in range(16):
                if perm[c] in col_used[c]:
                    ok = False
                    break
            if not ok:
                continue
            for c in range(16):
                if perm[c] in box_used[r//4*4 + c//4]:
                    ok = False
                    break
            if not ok:
                continue
            
            for c in range(16):
                col_used[c].add(perm[c])
                box_used[r//4*4 + c//4].add(perm[c])
            
            search(r+1)
            
            for c in range(16):
                col_used[c].remove(perm[c])
                box_used[r//4*4 + c//4].remove(perm[c])
            
            if count >= 10:
                return True
        
        return False
    
    search(0)
    return count


def main():
    print("="*70)
    print("重新提取排列并去除锁定冲突")
    print("="*70)
    
    config, perms = load_data()
    
    # 步骤 1: 基于已知数字提取
    print("\n【步骤 1】基于已知数字提取排列...")
    refined = extract_with_known_digits(config, perms)
    
    total_before = sum(len(perms.get(r, [])) for r in range(1, 17))
    total_after = sum(len(refined.get(r, [])) for r in range(1, 17))
    
    print(f"  提取前：{total_before:,} 排列")
    print(f"  提取后：{total_after:,} 排列")
    
    for r in range(1, 17):
        before = len(perms.get(r, []))
        after = len(refined.get(r, []))
        if before != after:
            print(f"  Row {r:2d}: {before:>6,} → {after:>6,}")
    
    # 步骤 2: 计算新单源值
    print("\n【步骤 2】计算新单源值...")
    new_single = compute_single_sources(refined)
    print(f"  新单源值：{len(new_single)} 个")
    
    # 步骤 3: 去除过度锁定
    print("\n【步骤 3】去除过度锁定...")
    relaxed_single, over_locked = remove_over_locked_rows(refined, new_single, max_ss_per_row=5)
    print(f"  放松后单源值：{len(relaxed_single)} 个")
    
    # 步骤 4: 验证
    print("\n【步骤 4】验证放松后的约束...")
    count = verify_with_relaxed(refined, relaxed_single)
    print(f"  找到解数：{count}")
    
    # 保存
    result = {
        "original_total": total_before,
        "refined_total": total_after,
        "original_single_source": len(new_single),
        "relaxed_single_source": len(relaxed_single),
        "solutions_found": count,
        "over_locked_rows": over_locked,
        "removed_single_sources": [(c+1, v, r+1) for (c, v), r in [(k, v) for k, v in new_single.items() if k not in relaxed_single]]
    }
    
    with open(f"{BASE_DIR}/relaxed_result.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n结果已保存：relaxed_result.json")
    
    # 输出放松后的排列统计
    print("\n【放松后的排列统计】")
    for r in range(1, 17):
        cnt = len(refined.get(r, []))
        ss = len([1 for (c, v), row_idx in relaxed_single.items() if row_idx == r-1])
        print(f"  Row {r:2d}: {cnt:>6,} 排列, {ss:2d} 单源值")


if __name__ == "__main__":
    main()
