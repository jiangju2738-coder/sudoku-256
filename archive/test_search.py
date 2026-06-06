#!/usr/bin/env python3
"""Test minimal search"""
import json
import time
from copy import deepcopy

N = 16
base_dir = "D:/2026/WPF_Sudoku/Sudoku_256"

print("Loading permutations...")
perms = []
for i in range(1, 17):
    with open(f"{base_dir}/A{i}_permutations.json", "r") as f:
        data = json.load(f)
        perms.append(data if isinstance(data, list) else data["permutations"])

print(f"Total perms: {sum(len(p) for p in perms):,}")

# Sort by constraint tightness
row_order = sorted(range(N), key=lambda r: len(perms[r]))
print(f"Row order: {[(r+1, len(perms[r])) for r in row_order]}")

print("\nStarting search...")
t0 = time.time()

grid = [[0]*N for _ in range(N)]
col_vals = [set() for _ in range(N)]

def backtrack(idx):
    elapsed = time.time() - t0
    if idx >= N:
        print(f"✓ Found solution at {elapsed:.1f}s!")
        return True
    
    row = row_order[idx]
    for perm in perms[row]:
        conflict = False
        for c in range(N):
            if perm[c] in col_vals[c]:
                conflict = True
                break
        if conflict:
            continue
        
        grid[row] = perm[:]
        for c in range(N):
            col_vals[c].add(perm[c])
        
        if backtrack(idx + 1):
            return True
        
        for c in range(N):
            col_vals[c].remove(perm[c])
    
    return False

if backtrack(0):
    print("\nSolution found:")
    for r in range(N):
        print(f"  {grid[r]}")
else:
    print(f"No solution found in {time.time() - t0:.1f}s")
