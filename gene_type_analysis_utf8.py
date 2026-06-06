import json

with open('V77_gene_fingerprint_100D_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

puzzles = data.get('gene_fingerprints', {})

results = []
for name, genes in puzzles.items():
    row_anchors = [genes.get(f'D{i}', {}).get('value', 0) for i in range(1, 17)]
    d91 = genes.get('D91', {}).get('value', 0)
    d92 = genes.get('D92', {}).get('value', 0)
    d93 = genes.get('D93', {}).get('value', 0)
    d100 = genes.get('D100', {}).get('value', 0)
    
    # 判断类型
    if d100 == 100:
        ptype = "解盘"
    elif d91 > 0.5 and d93 == 0:
        ptype = "标准数独"
    else:
        ptype = "自由变体"
    
    results.append({
        'name': name,
        'row_anchor_range': f"{min(row_anchors)}-{max(row_anchors)}",
        'd91': d91,
        'd92': d92,
        'd93': d93,
        'd100': d100,
        'type': ptype
    })

# 打印表格
print("=" * 90)
print("基因指纹100D维度 - 标准数独 vs 自由变体分类结果")
print("=" * 90)
print()
print(f"{'盘名':<25} {'行锚点范围':<12} {'D91均衡度':<12} {'D92填充率':<12} {'D93锁定度':<12} {'D100评分':<10} {'类型':<10}")
print("-" * 90)

for r in results:
    print(f"{r['name']:<25} {r['row_anchor_range']:<12} {r['d91']:<12.4f} {r['d92']:<12.4f} {r['d93']:<12.4f} {r['d100']:<10.4f} {r['type']:<10}")

print()
print("=" * 90)
print("分类统计")
print("=" * 90)

type_counts = {}
for r in results:
    t = r['type']
    type_counts[t] = type_counts.get(t, 0) + 1

for t, count in type_counts.items():
    print(f"  {t}: {count} 个")

print()
print("=" * 90)
print("基因指纹判据体系 - 标准数独 vs 自由变体")
print("=" * 90)
print()
print("[判据1] 综闔博弈均衡度 (D91)")
print("  - D91 > 0.5  : 标准数独特征，行间约束均衡，无主导行")
print("  - D91 <= 0.5 : 自由变体特征，存在主导行，约束不均匀")
print()
print("[判据2] 五维线锁定度 (D93)")
print("  - D93 = 0    : 标准数独，仅行列宫三重约束")
print("  - D93 > 0    : 自由变体，存在额外约束维度（如X数独对角线、Killer数独Cage等）")
print()
print("[判据3] 基因综合评分 (D100)")
print("  - D100 < 65  : 强约束谜题（演进谜题，存在主导行）")
print("  - D100 >= 65 : 标准谜题（初始盘，约束相对均衡）")
print("  - D100 = 100 : 完全解盘（16行全部锁定）")
print()
print("=" * 90)
print("结论")
print("=" * 90)
print("""
1. 符阖排列数独系统同时包含标准数独特征和自由变体特征

2. 初始盘 (initial_puzzle):
   - D91=0.3556, D93=0.0000, D100=63.67
   - 虽D93=0（无额外维度约束），但D91<0.5（存在行约束不均匀）
   - 属于"类标准数独但具有不均匀分布"的过渡态

3. 演进谜题 (v74/v75/v76 puzzle):
   - D91≈0.12, D93=6.25, D100≈60
   - 典型的自由变体特征：
     * 存在主导行（I行/E行/C行 100%约束）
     * 额外锁定维度（行终局排列约束）
     * 属于"行锁定型自由变体"

4. 解盘 (final_solution/v74/v75/v76 solution):
   - D91=1.0, D92=100, D93=100, D100=100
   - 完全闭合格式，所有行16锚点锁定
   - 不属于谜题类别，而是约束满足结果

5. 符阖数独的本质特征：
   - 符阖排列约束是"行级自由变体约束"
   - 每行需从特定的164-656,777个排列中选择
   - 这相当于在标准数独行约束基础上增加了排列集合约束
   - 因此符阖数独本质上是一种"自由变体数独"
""")
