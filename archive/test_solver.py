#!/usr/bin/env python3
import json
import time
from ortools.sat.python import cp_model

print("=" * 60)
print("CP-SAT Solution Test - 55 anchors")
print("=" * 60)

with open('sudoku_config.json', 'r') as f:
    config = json.load(f)

anchors = config['known_digits']
positions = {(a['row']-1, a['col']-1): a['value'] for a in anchors}

print(f"\nAnchors: {len(anchors)}")

# Load permutations
row_perms = {}
for i in range(16):
    letter = chr(65+i)
    try:
        with open(f'A{i+1}_permutations.json', 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                row_perms[letter] = data
    except Exception as e:
        print(f"Warning: Could not load A{i+1}_permutations.json: {e}")

print(f"Permutations loaded: {sum(len(v) for v in row_perms.values())}")

# Unknown rows
unknown = [i for i in range(16) if sum(1 for (r,c) in positions if r==i) < 16]
print(f"Unknown rows: {len(unknown)} - {[chr(65+i) for i in unknown]}")

# Filter permutations for each unknown row
print("\nFiltered permutations:")
for i in unknown:
    letter = chr(65+i)
    if letter in row_perms:
        filtered = [p for p in row_perms[letter] 
                   if all(p[c] == positions.get((i,c), p[c]) for c in range(16) if (i,c) in positions)]
        print(f"  Row {letter}: {len(row_perms[letter])} -> {len(filtered)} valid")
    else:
        print(f"  Row {letter}: No permutation file")

# Build model
model = cp_model.CpModel()
row_vars = {}
row_counts = {}

for i in unknown:
    letter = chr(65+i)
    if letter in row_perms:
        filtered = [p for p in row_perms[letter] 
                   if all(p[c] == positions.get((i,c), p[c]) for c in range(16) if (i,c) in positions)]
        row_counts[i] = len(filtered)
        if len(filtered) > 0:
            row_vars[i] = [model.NewBoolVar(f'r{i}_p{k}') for k in range(len(filtered))]
            model.AddExactlyOne(row_vars[i])
        else:
            print(f"  WARNING: Row {letter} has 0 valid permutations!")

# Column constraints
print("\nBuilding column constraints...")
conflicts = []
for c in range(16):
    for v in range(1, 17):
        exprs = []
        # Known positions
        for (kr, kc), kv in positions.items():
            if kc == c and kv == v:
                exprs.append(1)
        # Unknown rows
        for i in unknown:
            if i in row_vars and chr(65+i) in row_perms:
                filtered = [p for p in row_perms[chr(65+i)] 
                           if all(p[c2] == positions.get((i,c2), p[c2]) for c2 in range(16) if (i,c2) in positions)]
                for k, p in enumerate(filtered):
                    if p[c] == v:
                        exprs.append(row_vars[i][k])
        
        if exprs:
            if any(isinstance(x, int) for x in exprs):
                cnt = sum(1 for x in exprs if isinstance(x, int) and x == 1)
                if cnt > 1:
                    conflicts.append(f"col{c+1}_v{v}")
                    model.Add(False)
            else:
                model.Add(sum(exprs) <= 1)

if conflicts:
    print(f"Direct conflicts found: {conflicts[:5]}")

# Box constraints
print("Building box constraints...")
for box in range(16):
    for v in range(1, 17):
        exprs = []
        for (kr, kc), kv in positions.items():
            if kv == v:
                br, bc = kr // 4, kc // 4
                if br * 4 + bc == box:
                    exprs.append(1)
        for i in unknown:
            if i in row_vars and chr(65+i) in row_perms:
                filtered = [p for p in row_perms[chr(65+i)] 
                           if all(p[c2] == positions.get((i,c2), p[c2]) for c2 in range(16) if (i,c2) in positions)]
                for k, p in enumerate(filtered):
                    for c in range(16):
                        if (i // 4) * 4 + (c // 4) == box and p[c] == v:
                            exprs.append(row_vars[i][k])
        
        if exprs:
            if any(isinstance(x, int) for x in exprs):
                cnt = sum(1 for x in exprs if isinstance(x, int) and x == 1)
                if cnt > 1:
                    model.Add(False)

print("Solving...")
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60
solver.parameters.num_search_workers = 8
solver.parameters.log_search_progress = True

class CB(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        super().__init__()
        self.sols = []
    
    def on_solution_callback(self):
        grid = [[0]*16 for _ in range(16)]
        for (r, c), v in positions.items():
            grid[r][c] = v
        for i in unknown:
            if i in row_vars and chr(65+i) in row_perms:
                filtered = [p for p in row_perms[chr(65+i)] 
                           if all(p[c2] == positions.get((i,c2), p[c2]) for c2 in range(16) if (i,c2) in positions)]
                for k in range(len(filtered)):
                    if self.Value(row_vars[i][k]):
                        grid[i] = filtered[k][:]
                        break
        self.sols.append(grid)

cb = CB()
t0 = time.time()
status = solver.Solve(model, cb)
t1 = time.time()

print("\n" + "=" * 60)
print("Result:")
print("=" * 60)
print(f"Status: {solver.StatusName(status)}")
print(f"Solutions: {len(cb.sols)}")
print(f"Time: {t1-t0:.2f}s")

if cb.sols:
    print(f"\nFound {len(cb.sols)} solution(s)!")
    # Save first solution
    with open('first_solution.json', 'w') as f:
        json.dump(cb.sols[0], f, indent=2)
    print("Saved to first_solution.json")
