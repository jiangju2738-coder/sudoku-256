#!/usr/bin/env python3
"""
Run the DLX solver and capture all output
"""
import sys
import os

# Read and execute the main solver script
with open('dlx_solve_full.py', 'r', encoding='utf-8') as f:
    code = f.read()

exec(code)
