"""
92锚点提取与CP-SAT求解
基于超级大数独_box_size4.txt中的92个锚点定义
"""
import json, os, time, sys
from ortools.sat.python import cp_model

BASE_DIR = r'D:\2026\WPF_Sudoku\Sudoku_256'
backup_dir = os.path.join(BASE_DIR, 'backup_fuyi')

sys.stdout.reconfigure(encoding='utf-8')
N = 16; BOX_SIZE = 4

# ─────────────────────────────────────────────
# 第一步：从txt文件中提取92个锚点
# ─────────────────────────────────────────────
# 根据文件内容，提取每个"已知数X"的行列位置
# 注意：txt文件使用符号列名（A-S行，D-S列），需要转换为数字坐标

# 行映射：A=1, B=2, ..., P=16
row_map = {chr(65+i): i+1 for i in range(16)}  # A-P → 1-16
# 列映射：D=1, E=2, ..., S=16
col_map = {chr(68+i): i+1 for i in range(16)}  # D-S → 1-16

# 从文件中提取的92个锚点（数值1-16各自的行列位置）
anchors_by_value = {
    1: "BR DJ KD LS MM OE PP",
    2: "BP CI GL IG KK ON PF",
    3: "AF BH FK GQ IS KM MO NR",
    4: "BO DE EP FJ GF LG",
    5: "AK BN EM HI JE KH LO ML OQ PJ",
    6: "BL GG HO KF MQ NI",
    7: "DH IO JR MS",
    8: "AS CK FE JP OO",
    9: "BJ FM HK KP NF OH",
    10: "PR",
    11: "DO II",
    12: "AI BE DQ FS GJ LN MH",
    13: "DG EH FQ HE ID NL",
    14: "AO CF GD HN IL LJ PM",
    15: "FH IQ MD NO OK PS",
    16: "AQ HR JN LI",
}

# 转换为(行,列,值)三元组
anchors_92 = []
for value, locations in anchors_by_value.items():
    for loc in locations.split():
        row_letter = loc[0]
        col_letter = loc[1:]
        row = row_map[row_letter]
        col = col_map[col_letter]
        anchors_92.append((row, col, value))

print('=' * 65)
print('  第一步：解析92个锚点')
print('=' * 65)
print()
print(f'从92锚点定义中提取的锚点总数: {len(anchors_92)}')

# 检查是否有重复
anchors_set = set(anchors_92)
print(f'去重后锚点数: {len(anchors_set)}')
if len(anchors_92) != len(anchors_set):
    print(f'[警告] 存在重复锚点！')

# 检查每个数值的锚点数量
print()
print('各数值锚点数量分布:')
for v in range(1, 17):
    count = sum(1 for a in anchors_92 if a[2] == v)
    print(f'  已知数{v}: {count}个锚点')

print()
print('完整锚点列表:')
for r, c, v in sorted(anchors_92, key=lambda x: (x[0], x[1])):
    print(f'  row{r:2d}col{c:2d} = {v:2d}  ({chr(64+r)}{chr(67+c)})')

# ─────────────────────────────────────────────
# 第二步：加载原始符阖排列，检查锚点相容性
# ─────────────────────────────────────────────
perm_sets = []
for i in range(N):
    path = os.path.join(backup_dir, f'A{i+1}_permutations.json')
    with open(path, 'r', encoding='utf-8') as f:
        perms = json.load(f)
    perm_sets.append(perms)

print()
print('=' * 65)
print('  第二步：检查92锚点与原始符阖排列的相容性')
print('=' * 65)
print()

compatible = []
incompatible = []

for r, c, v in anchors_92:
    count_v = sum(1 for p in perm_sets[r-1] if p[c-1] == v)
    pct = count_v / len(perm_sets[r-1]) * 100 if len(perm_sets[r-1]) > 0 else 0
    if pct > 0:
        compatible.append((r, c, v, count_v, len(perm_sets[r-1]), pct))
    else:
        incompatible.append((r, c, v, len(perm_sets[r-1])))

print(f'完全相容（出现率>0%）: {len(compatible)} 个')
print(f'完全不相容（出现率=0%）: {len(incompatible)} 个')
print()

if incompatible:
    print('=== 不相容锚点 ===')
    for r, c, v, total in incompatible:
        print(f'  row{r}col{c}={v}: 在行{r}的{total}个符阖排列中从未出现')

# ─────────────────────────────────────────────
# 第三步：用CP-SAT求解（仅使用相容锚点）
# ─────────────────────────────────────────────
if incompatible:
    print()
    print('=' * 65)
    print('  警告：存在不相容锚点，需要决定是否继续')
    print('=' * 65)
    print()
    print('选项：')
    print('  1. 仅使用相容锚点求解')
    print('  2. 使用全部92锚点（可能INFEASIBLE）')
    print('  3. 跳过此步')

use_compatible_only = True  # 先使用相容锚点

if use_compatible_only:
    working_anchors = [(r, c, v) for r, c, v, *_ in compatible]
    print(f'\n使用{len(working_anchors)}个相容锚点求解')
else:
    working_anchors = anchors_92
    print(f'\n使用全部{len(working_anchors)}个锚点求解（可能失败）')

# 构建CP-SAT模型
model = cp_model.CpModel()

# 创建变量：每行选择一个符阖排列
row_choice_vars = []
for r in range(N):
    row_vars = [model.NewBoolVar(f'c_r{r}_k{k}') for k in range(len(perm_sets[r]))]
    row_choice_vars.append(row_vars)
    model.AddExactlyOne(row_vars)

# 锚点约束
for r, c, v in working_anchors:
    r0, c0 = r-1, c-1
    valid_k = [k for k in range(len(perm_sets[r0])) if perm_sets[r0][k][c0] == v]
    if not valid_k:
        print(f'[错误] row{r}col{c}=v{v} 无排列！')
        sys.exit(1)
    model.AddExactlyOne([row_choice_vars[r0][k] for k in valid_k])

# 列 AllDifferent
for c in range(N):
    for val in range(1, N+1):
        cells = [row_choice_vars[r][k] for r in range(N) for k in range(len(perm_sets[r]))
                 if perm_sets[r][k][c] == val]
        if cells:
            model.AddExactlyOne(cells)

# 宫 AllDifferent
for br in range(BOX_SIZE):
    for bc in range(BOX_SIZE):
        for val in range(1, N+1):
            cells = []
            for dr in range(BOX_SIZE):
                for dc in range(BOX_SIZE):
                    r2 = br * BOX_SIZE + dr
                    c2 = bc * BOX_SIZE + dc
                    for k in range(len(perm_sets[r2])):
                        if perm_sets[r2][k][c2] == val:
                            cells.append(row_choice_vars[r2][k])
            if cells:
                model.AddExactlyOne(cells)

print()
print('求解中...')
solver = cp_model.CpSolver()
solver.parameters.num_search_workers = 8
solver.parameters.max_time_in_seconds = 120

t0 = time.time()
status = solver.Solve(model)
elapsed = time.time() - t0

print(f'[CP-SAT结果] 状态: {status} | 耗时: {elapsed:.2f}s')

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # 构造解
    grid = []
    for r in range(N):
        for k in range(len(perm_sets[r])):
            if solver.Value(row_choice_vars[r][k]) == 1:
                grid.append(list(perm_sets[r][k]))
                break

    # 验证
    r_ok = all(set(row) == set(range(1, N+1)) for row in grid)
    c_ok = all(set(grid[r][c] for r in range(N)) == set(range(1, N+1)) for c in range(N))
    b_ok = all(set(grid[br*BOX_SIZE+dr][bc*BOX_SIZE+dc] for dr in range(BOX_SIZE) for dc in range(BOX_SIZE))
               == set(range(1, N+1)) for br in range(BOX_SIZE) for bc in range(BOX_SIZE))

    # 检查锚点
    anchor_fails = []
    for r, c, v in working_anchors:
        if grid[r-1][c-1] != v:
            anchor_fails.append((r, c, v, grid[r-1][c-1]))

    result = {
        'status': 'SOLVED',
        'solver': 'CP-SAT',
        'source': '92锚点（相容子集）',
        'anchor_count': len(working_anchors),
        'anchor_total': len(anchors_92),
        'anchor_incompatible': len(incompatible),
        'solve_time_sec': round(elapsed, 3),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'solution': grid,
        'verification': {
            'row_ok': r_ok,
            'col_ok': c_ok,
            'box_ok': b_ok,
            'fummel_ok': True,
            'anchor_ok': len(anchor_fails) == 0,
            'anchor_fails': anchor_fails
        }
    }

    out_path = os.path.join(BASE_DIR, 'solution_92_anchors.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print()
    print('=' * 65)
    print('  求解结果')
    print('=' * 65)
    print(f'  状态: {result["status"]}')
    print(f'  使用的锚点数: {len(working_anchors)}（原始92个，{len(incompatible)}个不相容）')
    print(f'  耗时: {elapsed:.2f}s')
    print(f'  行约束: {"PASS" if r_ok else "FAIL"}')
    print(f'  列约束: {"PASS" if c_ok else "FAIL"}')
    print(f'  宫约束: {"PASS" if b_ok else "FAIL"}')
    print(f'  符阖排列: PASS')
    print(f'  锚点验证: {"PASS" if len(anchor_fails)==0 else "FAIL"}')

    if anchor_fails:
        print(f'\n  [失败] 锚点不匹配:')
        for r, c, v, actual in anchor_fails:
            print(f'    row{r}col{c}: 期望={v}, 实际={actual}')

    # 显示解（锚点用[ ]标注）
    print()
    print('  解盘（[ ]内为92锚点）:')
    print('    ' + ' '.join(f'C{c+1:02d}' for c in range(16)))
    anchor_set = set(working_anchors)
    for r in range(16):
        row_str = ''
        for c in range(16):
            v = grid[r][c]
            if (r+1, c+1, v) in anchor_set:
                row_str += f'[{v:2d}]'
            else:
                row_str += f' {v:2d} '
        print(f'R{r+1:02d}|{row_str}')
        if r in [3, 7, 11]:
            print('        ' + '-' * 50)

    print()
    print(f'解已保存到: {out_path}')
else:
    print(f'\n无解！92锚点与原始符阖排列/数独约束不相容')
