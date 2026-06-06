#!/usr/bin/env python3
from pathlib import Path

solver_path = Path('cosmic_thunder_evolutionary_solver.py')
c = solver_path.read_text(encoding='utf-8')

print(f'cosmic_thunder_evolutionary_solver.py: {len(c)} bytes')
print()

checks = [
    ('適應度權重 0.1/0.5/0.4', 'row_score * 0.1' in c),
    ('repair_with_permutation_swap 方法', 'def repair_with_permutation_swap' in c),
    ('enable_repair 參數', 'enable_repair' in c),
    ('verify_with_solution_limit 方法', 'def verify_with_solution_limit' in c),
    ('QuantumState 枚舉', 'class QuantumState' in c),
    ('CP-SAT solution_limit', 'solution_limit' in c),
]

all_ok = True
for name, found in checks:
    status = '✅' if found else '❌'
    print(f'{status} {name}')
    if not found:
        all_ok = False

print()
if all_ok:
    print('✅ 所有改進已實施完成！')
else:
    print('⚠️ 部分改進缺失')
