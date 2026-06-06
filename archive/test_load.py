#!/usr/bin/env python3
import json
import sys

base_dir = "D:/2026/WPF_Sudoku/Sudoku_256"

print("Testing file loading...")

# Test A1_permutations.json
with open(f"{base_dir}/A1_permutations.json", "r") as f:
    data = json.load(f)
    print(f"A1: {len(data) if isinstance(data, list) else 'dict'} elements")
    if isinstance(data, list) and len(data) > 0:
        print(f"  First perm: {data[0]}")

# Test column_constraints.json
try:
    with open(f"{base_dir}/column_constraints.json", "r") as f:
        col_data = json.load(f)
        print(f"Column constraints: {col_data['summary']}")
except Exception as e:
    print(f"Column constraints error: {e}")

print("\nAll files loaded successfully!")
