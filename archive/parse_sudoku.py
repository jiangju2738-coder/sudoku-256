# 解析數獨配置
data_str = """
[0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8],
[0,12,0,0, 3,0,9,0, 6,0,5,4, 2,0,1,0],
[0,0,14,0, 0,2,0,8, 0,0,0,0, 0,0,0,0],
[0,4,0,13, 7,0,1,0, 0,0,0,11, 0,12,0,0],
[0,0,0,0, 13,0,0,0, 0,5,0,0, 4,0,0,0],
[0,8,0,0, 15,0,4,3, 0,9,0,0, 0,13,0,12],
[14,0,4,6, 0,0,12,0, 2,0,0,0, 0,3,0,0],
[0,13,0,0, 0,5,0,9, 0,0,14,6, 0,0,16,0],
[13,0,0,2, 0,11,0,0, 14,0,0,7, 0,15,0,3],
[0,5,0,0, 0,0,0,0, 0,0,16,0, 8,0,7,0],
[1,0,6,0, 5,0,0,2, 0,3,0,0, 9,0,0,0],
[0,0,0,4, 0,16,14,0, 0,0,12,5, 0,0,0,1],
[15,0,0,0, 12,0,0,0, 5,1,0,3, 0,6,0,7],
[0,0,9,0, 0,6,0,0, 13,0,0,15, 0,0,3,0],
[0,1,0,0, 9,0,0,15, 0,0,2,8, 0,5,0,0],
[0,0,2,0, 0,0,5,0, 0,14,0,0, 1,0,10,15]
"""

from collections import defaultdict
import json

# 解析矩陣
rows = []
for line in data_str.strip().split('\n'):
    line = line.strip().rstrip(',').strip('[]')
    nums = [int(x.strip()) for x in line.split(',') if x.strip()]
    rows.append(nums)

print('=== 數獨16x16矩陣解析完成 ===')
print(f'總行數: {len(rows)}')
print(f'每行數字個數: {len(rows[0])}')

# 統計已知數字(非0)
known_count = 0
known_positions = []
for r in range(16):
    for c in range(16):
        if rows[r][c] != 0:
            known_count += 1
            known_positions.append({
                'row': r + 1,
                'col': c + 1,
                'cell_num': r * 16 + c + 1,
                'value': rows[r][c],
                'label': f'{r+1}{chr(66+c)}'
            })

print(f'\n已知數字總數: {known_count}')
print(f'未知數字(0)總數: {256 - known_count}')

# 數獨標準數字範圍
print('\n=== 數獨256個宮格數字分佈 ===')
print('第1行: A1, 數字區間 1-16')
print('第2行: A2, 數字區間 17-32')
print('...')
print('第16行: A16, 數字區間 241-256')
print()

# 按行顯示已知數字
for r in range(16):
    known_in_row = [pos for pos in known_positions if pos['row'] == r + 1]
    known_vals = [str(pos['value']) for pos in known_in_row]
    print(f'第{r+1:2d}行 (A{r+1:2d}, 數字{r*16+1:3d}-{r*16+16:3d}): 已知{len(known_in_row):2d}個 -> {" ".join(known_vals) if known_vals else "全未知"}')

# 按已知數值統計出現在哪些行
val_rows = defaultdict(set)
for pos in known_positions:
    val_rows[pos['value']].add(pos['row'])

print('\n=== 單源值分析(每個數值出現在哪些行) ===')
single_source = []
for v in range(1, 17):
    rows_with_v = sorted(val_rows[v])
    if len(rows_with_v) == 1:
        single_source.append({'value': v, 'row': rows_with_v[0]})
    print(f'數值 {v:2d}: 出現在行 {" ".join(f"A{r}" for r in rows_with_v)} ({len(rows_with_v)}行)')

print(f'\n單源值數量: {len(single_source)}')
print('單源值列表:', [(s['value'], s['row']) for s in single_source])

# 保存到JSON
result = {
    'known_count': known_count,
    'known_positions': known_positions,
    'single_source_count': len(single_source),
    'single_source': single_source
}
with open('box_size4_parsed.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print('\n已保存: box_size4_parsed.json')
