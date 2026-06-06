"""
基于92锚点重新生成符阖排列
方法：从满足92个锚点的合法Sudoku解中提取每行排列
"""
import json, os, time, sys
from ortools.sat.python import cp_model

BASE_DIR = r'D:\2026\WPF_Sudoku\Sudoku_256'
sys.stdout.reconfigure(encoding='utf-8')
N = 16; BOX_SIZE = 4

# ─────────────────────────────────────────────
# 第一步：定义92个锚点
# ─────────────────────────────────────────────
row_map = {chr(65+i): i+1 for i in range(16)}
col_map = {chr(68+i): i+1 for i in range(16)}

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

anchors_92 = []
for value, locations in anchors_by_value.items():
    for loc in locations.split():
        row = row_map[loc[0]]
        col = col_map[loc[1:]]
        anchors_92.append((row, col, value))

print('=' * 70)
print('  基于92锚点重新生成符阖排列')
print('=' * 70)
print()
print(f'锚点总数: {len(anchors_92)}')

# ─────────────────────────────────────────────
# 第二步：用CP-SAT枚举满足92锚点的解
# ─────────────────────────────────────────────
# 不使用符阖排列约束，只用92个锚点+数独三约束
# 这样生成的解保证92个锚点都被满足

model = cp_model.CpModel()

# 创建16x16的变量
grid_vars = [[model.NewIntVar(1, N, f'cell_{r}_{c}') for c in range(N)] for r in range(N)]

# 92个锚点约束
for r, c, v in anchors_92:
    model.Add(grid_vars[r-1][c-1] == v)

# 行AllDifferent
for r in range(N):
    model.AddAllDifferent(grid_vars[r])

# 列AllDifferent
for c in range(N):
    model.AddAllDifferent([grid_vars[r][c] for r in range(N)])

# 宫AllDifferent
for br in range(BOX_SIZE):
    for bc in range(BOX_SIZE):
        box_cells = []
        for dr in range(BOX_SIZE):
            for dc in range(BOX_SIZE):
                box_cells.append(grid_vars[br * BOX_SIZE + dr][bc * BOX_SIZE + dc])
        model.AddAllDifferent(box_cells)

print('模型构建完成')

# 使用SolutionCollector枚举多个解
class SolutionCollector(cp_model.CpSolver):
    def __init__(self, model):
        super().__init__()
        self._model = model
        self._solutions = []
        self._collector = None
        
    def on_solution_callback(self):
        grid = [[self.Value(self._model._variables[i]) for i in range(N)] for r in range(N)]
        # 从grid_vars提取
        grid = []
        for r in range(N):
            row = []
            for c in range(N):
                row.append(self.Value(self._model._variables[
                    next(k for k, v in self._model._variables.items() if v == self._model._cell_vars[r][c])
                ]))
            grid.append(row)
        self._solutions.append(grid)

# 简化：直接用CpSolver枚举
# 由于CpSolver不支持直接枚举所有解，使用循环搜索
print()
print('开始枚举解...')

solutions = []
solver = cp_model.CpSolver()
solver.parameters.num_search_workers = 8
solver.parameters.max_time_in_seconds = 300
solver.parameters.enumerate_all_solutions = False  # 先用单个解测试

t0 = time.time()
status = solver.Solve(model)
elapsed = time.time() - t0

print(f'[第一次求解] 状态: {status} | 耗时: {elapsed:.2f}s')

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # 构造第一个解
    grid = []
    for r in range(N):
        row = []
        for c in range(N):
            row.append(solver.Value(grid_vars[r][c]))
        grid.append(row)
    solutions.append(grid)
    
    print(f'找到第1个解')
    
    # 添加排除约束，继续搜索
    for iteration in range(1, 100):  # 最多枚举100个解
        # 添加排除当前解的约束
        for r in range(N):
            for c in range(N):
                model.Add(grid_vars[r][c] != grid[r][c])
        
        solver2 = cp_model.CpSolver()
        solver2.parameters.num_search_workers = 8
        solver2.parameters.max_time_in_seconds = 10
        
        status2 = solver2.Solve(model)
        elapsed2 = time.time() - t0
        
        if status2 in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            new_grid = []
            for r in range(N):
                row = []
                for c in range(N):
                    row.append(solver2.Value(grid_vars[r][c]))
                new_grid.append(row)
            solutions.append(new_grid)
            print(f'找到第{len(solutions)}个解 (总耗时: {elapsed2:.1f}s)')
            
            if len(solutions) >= 10:
                print('已达到目标解数量(10个)，停止搜索')
                break
        else:
            print(f'已穷尽所有解，共找到 {len(solutions)} 个')
            break

print()
print('=' * 70)
print(f'  枚举完成：共找到 {len(solutions)} 个满足92锚点的解')
print('=' * 70)

if len(solutions) == 0:
    print('无解！92锚点与数独三约束不相容')
    sys.exit(1)

# ─────────────────────────────────────────────
# 第三步：从解中提取每行的排列
# ─────────────────────────────────────────────
print()
print('从解中提取符阖排列...')

permutations_by_row = {i: set() for i in range(N)}

for sol_idx, grid in enumerate(solutions):
    for r in range(N):
        perm = tuple(grid[r])
        permutations_by_row[r].add(perm)

# 转换为列表并保存
for i in range(N):
    perms_list = sorted(list(permutations_by_row[i]))
    
    # 保存到新文件
    output_path = os.path.join(BASE_DIR, f'A{i+1}_permutations_from_92_anchors.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(perms_list, f, ensure_ascii=False, indent=2)
    
    print(f'行{i+1}: {len(perms_list)}个排列 -> {output_path}')

print()
print('=' * 70)
print('  符阖排列重新生成完成')
print('=' * 70)

# 验证：检查92个锚点在新符阖排列中的相容性
print()
print('验证：检查92锚点在新符阖排列中的相容性...')

compatible_count = 0
for r, c, v in anchors_92:
    row_idx = r - 1
    col_idx = c - 1
    # 加载新生成的排列
    path = os.path.join(BASE_DIR, f'A{row_idx+1}_permutations_from_92_anchors.json')
    with open(path, 'r', encoding='utf-8') as f:
        perms = json.load(f)
    
    has_match = any(p[col_idx] == v for p in perms)
    if has_match:
        compatible_count += 1
    else:
        print(f'  [FAIL] row{r}col{c}={v} 在新生成的符阖排列中无匹配!')

print(f'相容性: {compatible_count}/{len(anchors_92)} ({compatible_count/len(anchors_92)*100:.1f}%)')

if compatible_count == len(anchors_92):
    print('所有92锚点在新符阖排列中均相容！')
    print()
    print('下一步：用新生成的符阖排列求解完整数独')
else:
    print('部分锚点仍不相容，需进一步分析')
