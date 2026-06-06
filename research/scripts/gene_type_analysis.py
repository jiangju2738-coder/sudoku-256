import json

with open('V77_gene_fingerprint_100D_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取每个盘的关键基因特征
puzzles = data.get('gene_fingerprints', {})

print('=' * 80)
print('基因指纹100D维度 - 标准数独 vs 自由变体分析')
print('=' * 80)
print()

# 分析每个盘的基因特征
for name, genes in puzzles.items():
    print(f'【{name}】')
    
    # 行锚点密度范围
    row_anchors = [genes.get(f'D{i}', {}).get('value', 0) for i in range(1, 17)]
    
    # 提取D91-D100 (三大架构综合指标)
    d91 = genes.get('D91', {}).get('value', 0)  # 综闔博弈均衡度
    d92 = genes.get('D92', {}).get('value', 0)  # 五维点填充率
    d93 = genes.get('D93', {}).get('value', 0)  # 五维线锁定度
    d94 = genes.get('D94', {}).get('value', 0)  # 五维面宫均衡
    d95 = genes.get('D95', {}).get('value', 0)  # 五维体列强度
    d96 = genes.get('D96', {}).get('value', 0)  # 五维球网络度
    d97 = genes.get('D97', {}).get('value', 0)  # 五维时空演进
    d98 = genes.get('D98', {}).get('value', 0)  # 链式环式传递链
    d99 = genes.get('D99', {}).get('value', 0)  # 闭环完整度
    d100 = genes.get('D100', {}).get('value', 0)  # 基因综合评分
    
    print(f'  行锚点范围: {min(row_anchors)} - {max(row_anchors)} (差异: {max(row_anchors)-min(row_anchors)})')
    print(f'  综闔博弈均衡度(D91): {d91:.4f}')
    print(f'  五维点填充率(D92): {d92:.4f}')
    print(f'  五维线锁定度(D93): {d93:.4f}')
    print(f'  基因综合评分(D100): {d100:.4f}')
    
    # 判断标准数独 vs 自由变体特征
    if d91 > 0.5:
        print(f'  [标准数独特征] 综闔博弈均衡度高，无主导行')
    else:
        print(f'  [自由变体特征] 综闔博弈均衡度低，存在主导行')
    
    print()

print()
print('=' * 80)
print('标准数独 vs 自由变体基因指纹判据体系')
print('=' * 80)
print()
print('【判据1】综闔博弈均衡度 (D91)')
print('  - D91 > 0.5  : 标准数独特征，行间约束均衡')
print('  - D91 <= 0.5 : 自由变体特征，存在主导行/约束不均匀')
print()
print('【判据2】五维线锁定度 (D93)')
print('  - D93 = 0    : 标准数独，无额外行列约束')
print('  - D93 > 0    : 自由变体，存在额外行列约束（如X数独对角线）')
print()
print('【判据3】五维面宫均衡 (D94)')
print('  - D94 ≈ 1.0  : 标准数独，宫间约束强度一致')
print('  - D94 < 1.0  : 自由变体，宫间约束存在差异')
print()
print('【判据4】链式环式闭环完整度 (D99)')
print('  - D99 = 0%   : 标准谜题盘，未形成闭环')
print('  - D99 = 100% : 解盘，约束完全闭环')
print()
print('【判据5】基因综合评分 (D100)')
print('  - D100 < 65  : 强约束谜题（如演进谜题）')
print('  - D100 >= 65 : 标准谜题（如初始盘）')
print('  - D100 = 100 : 完全解盘')
print()

# 分类统计
standard_count = 0
variant_count = 0
solution_count = 0

for name, genes in puzzles.items():
    d91 = genes.get('D91', {}).get('value', 0)
    d93 = genes.get('D93', {}).get('value', 0)
    d100 = genes.get('D100', {}).get('value', 0)
    
    if d100 == 100:
        solution_count += 1
    elif d91 > 0.5 and d93 == 0:
        standard_count += 1
    else:
        variant_count += 1

print('=' * 80)
print('8盘分类统计结果')
print('=' * 80)
print(f'  标准数独谜题: {standard_count} 个')
print(f'  自由变体谜题: {variant_count} 个')
print(f'  完全解盘: {solution_count} 个')
print()
print('结论: 符阖排列数独系统包含标准数独特征和自由变体特征')
print('      演进谜题具有典型的自由变体特征（存在主导行）')
