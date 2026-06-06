# Quick verification: C191620 in backup + CP-SAT search
import json
import sys
sys.path.insert(0, 'C:\\Users\\Jualius\\.workbuddy\\binaries\\python\\versions\\3.13.12\\Lib\\site-packages')

from ortools.sat.python import cp_model

print("=" * 80)
print("验证1: C191620是否在backup_fuyi/C中？")
print("=" * 80)

with open('backup_fuyi/A3_permutations.json', 'r', encoding='utf-8') as f:
    backup_c = [tuple(p) for p in json.load(f)]

FINAL_C = (7, 10, 14, 15, 4, 2, 16, 8, 12, 13, 3, 1, 11, 9, 6, 5)
in_backup = FINAL_C in backup_c
print(f"backup C集合大小: {len(backup_c)}")
print(f"C191620在backup中: {in_backup}")
if not in_backup:
    print("结论: C191620不在backup_fuyi/中，backup是筛选子集")

print("\n" + "=" * 80)
print("搜索2: 用CP-SAT搜索92锚点 + C191620")
print("=" * 80)

anchors = {
    'BR':1, 'DJ':1, 'KD':1, 'LS':1, 'MM':1, 'OE':1, 'PP':1,
    'BP':2, 'CI':2, 'GL':2, 'IG':2, 'KK':2, 'ON':2, 'PF':2,
    'AF':3, 'BH':3, 'FK':3, 'GQ':3, 'IS':3, 'KM':3, 'MO':3, 'NR':3,
    'BO':4, 'DE':4, 'EP':4, 'FJ':4, 'GF':4, 'LG':4,
    'AK':5, 'BN':5, 'EM':5, 'HI':5, 'JE':5, 'KH':5, 'LO':5, 'ML':5, 'OQ':5, 'PJ':5,
    'BL':6, 'GG':6, 'HO':6, 'KF':6, 'MQ':6, 'NI':6,
    'DH':7, 'IO':7, 'JR':7, 'MS':7,
    'AS':8, 'CK':8, 'FE':8, 'JP':8, 'OO':8,
    'BJ':9, 'FM':9, 'HK':9, 'KP':9, 'NF':9, 'OH':9,
    'PR':10,
    'DO':11, 'II':11,
    'AI':12, 'BE':12, 'DQ':12, 'FS':12, 'GJ':12, 'LN':12, 'MH':12,
    'DG':13, 'EH':13, 'FQ':13, 'HE':13, 'ID':13, 'NL':13,
    'AO':14, 'CF':14, 'GD':14, 'HN':14, 'IL':14, 'LJ':14, 'PM':14,
    'FH':15, 'IQ':15, 'MD':15, 'NO':15, 'OK':15, 'PS':15,
    'AQ':16, 'HR':16, 'JN':16, 'LI':16,
}

row_map = {'A':0,'B':1,'C':2,'D':3,'E':4,'F':5,'G':6,'H':7,'I':8,'J':9,'K':10,'L':11,'M':12,'N':13,'O':14,'P':15}
col_map = {'D':0,'E':1,'F':2,'G':3,'H':4,'I':5,'J':6,'K':7,'L':8,'M':9,'N':10,'O':11,'P':12,'Q':13,'R':14,'S':15}

model = cp_model.CpModel()
grid = {(r,c): model.NewIntVar(1,16,f'g{r}{c}') for r in range(16) for c in range(16)}

for r in range(16):
    model.AddAllDifferent([grid[(r,c)] for c in range(16)])
for c in range(16):
    model.AddAllDifferent([grid[(r,c)] for r in range(16)])
for br in range(4):
    for bc in range(4):
        model.AddAllDifferent([grid[(br*4+dr,bc*4+dc)] for dr in range(4) for dc in range(4)])

for coord, val in anchors.items():
    r,c = row_map[coord[0]], col_map[coord[1]]
    model.Add(grid[(r,c)] == val)

for i,val in enumerate(FINAL_C):
    model.Add(grid[(2,i)] == val)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8

print("开始CP-SAT搜索...")
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("找到解！")
    for r in range(16):
        row = [solver.Value(grid[(r,c)]) for c in range(16)]
        print(f"  {chr(65+r)}: {row}")
        if r == 2:
            if tuple(row) == FINAL_C:
                print("    [SAME] 与C191620一致")
            else:
                print("    [DIFF] 与C191620不同！")
else:
    print("无解！")

print("\n" + "=" * 80)
print("关键发现总结")
print("=" * 80)
print(f"1. C191620在backup中: {in_backup}")
print(f"2. CP-SAT搜索92锚点+C191620: {'找到解' if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else '无解'}")
