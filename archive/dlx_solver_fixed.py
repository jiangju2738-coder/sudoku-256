#!/usr/bin/env python3
"""
Run the solver from D:/2026/WPF_Sudoku/Sudoku_256 directory
"""
import os
import sys

# Change to the working directory
working_dir = r"D:/2026/WPF_Sudoku/Sudoku_256"
os.chdir(working_dir)
print(f"Working directory: {os.getcwd()}")

# Now run the solver
try:
    # Read and execute the main solver script
    with open('dlx_solver_core.py', 'r', encoding='utf-8') as f:
        code = f.read()
    exec(code)
except Exception as e:
    import traceback
    print(f"\n❌ 执行出错: {e}")
    traceback.print_exc()
    sys.exit(1)
