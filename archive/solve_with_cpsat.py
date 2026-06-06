#!/usr/bin/env python3
"""
Level 2 16x16 Sudoku Solver using OR-Tools CP-SAT
Optimized: Standard Sudoku constraints only (no permutation constraints initially)
"""

import json
import time
from pathlib import Path
from ortools.sat.python import cp_model

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "sudoku_config.json"
PERM_DIR = BASE_DIR


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def load_permutations():
    perms = {}
    for row_num in range(1, 17):
        perm_file = PERM_DIR / f"A{row_num}_permutations.json"
        if perm_file.exists():
            with open(perm_file) as f:
                perms[f"A{row_num}"] = json.load(f)
    return perms


def create_cpsat_model(config, permutations, use_perm_constraints=False):
    """Create CP-SAT model with optional permutation constraints"""
    model = cp_model.CpModel()
    
    grid_size = 16
    box_size = 4
    
    # Create variables: x[row][col] in [1, 16]
    x = {}
    for r in range(grid_size):
        for c in range(grid_size):
            var_name = f"x[{r},{c}]"
            x[r, c] = model.NewIntVar(1, grid_size, var_name)
    
    # --- Standard Sudoku Constraints ---
    
    # Row constraints: all-different in each row
    for r in range(grid_size):
        cells = [x[r, c] for c in range(grid_size)]
        model.AddAllDifferent(cells)
    
    # Column constraints: all-different in each column
    for c in range(grid_size):
        cells = [x[r, c] for r in range(grid_size)]
        model.AddAllDifferent(cells)
    
    # Block constraints: all-different in each 4x4 block
    for br in range(grid_size // box_size):
        for bc in range(grid_size // box_size):
            cells = []
            for dr in range(box_size):
                for dc in range(box_size):
                    r = br * box_size + dr
                    c = bc * box_size + dc
                    cells.append(x[r, c])
            model.AddAllDifferent(cells)
    
    # --- Fixed Values ---
    for known in config.get("known_digits", []):
        r = known["row"] - 1
        c = known["col"] - 1
        v = known["value"]
        model.Add(x[r, c] == v)
    
    # --- Optional Permutation Constraints (符阖排列) ---
    # Use AllowedAssignments instead of ExactlyOne for efficiency
    if use_perm_constraints:
        print("  Adding permutation constraints with AllowedAssignments...")
        for row_idx in range(1, 17):
            row_name = f"A{row_idx}"
            if row_name in permutations:
                perms = permutations[row_name]
                if perms:
                    # Get the cells in this row
                    row_cells = [x[row_idx-1, c] for c in range(grid_size)]
                    # Use AllowedAssignments to constrain the entire row to one of the permutations
                    model.AddAllowedAssignments(row_cells, perms)
                    print(f"    Row {row_idx}: {len(perms)} permutations")
    
    return model, x


def solve(model):
    """Solve the model"""
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 3600
    solver.parameters.log_search_progress = True
    solver.parameters.num_search_workers = 8
    
    print("\n" + "=" * 60)
    print("Starting CP-SAT Solver...")
    print("=" * 60 + "\n")
    
    start_time = time.time()
    status = solver.Solve(model)
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"Solve Time: {elapsed:.2f} seconds")
    print("=" * 60)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"\nStatus: {solver.StatusName(status)}")
        return True, solver
    else:
        print(f"\nStatus: {solver.StatusName(status)}")
        print("No solution found!")
        return False, None


def get_grid(solver, x, grid_size=16):
    grid = []
    for r in range(grid_size):
        row_vals = []
        for c in range(grid_size):
            row_vals.append(solver.Value(x[r, c]))
        grid.append(row_vals)
    return grid


def print_grid(grid):
    for r in range(16):
        row_vals = grid[r]
        formatted = []
        for i, v in enumerate(row_vals):
            formatted.append(f"{v:2d}")
            if (i + 1) % 4 == 0 and i < 15:
                formatted.append("|")
        print(" ".join(formatted))
        if (r + 1) % 4 == 0 and r < 15:
            print("-" * 60)


def verify_solution(solver, x, config, permutations):
    grid_size = 16
    box_size = 4
    
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    
    errors = []
    grid = get_grid(solver, x, grid_size)
    
    # Check rows
    for r in range(grid_size):
        if len(set(grid[r])) != grid_size:
            errors.append(f"Row {r+1}: duplicate values")
    
    # Check columns
    for c in range(grid_size):
        col_vals = [grid[r][c] for r in range(grid_size)]
        if len(set(col_vals)) != grid_size:
            errors.append(f"Col {c+1}: duplicate values")
    
    # Check blocks
    for br in range(grid_size // box_size):
        for bc in range(grid_size // box_size):
            cells = []
            for dr in range(box_size):
                for dc in range(box_size):
                    r = br * box_size + dr
                    c = bc * box_size + dc
                    cells.append(grid[r][c])
            if len(set(cells)) != grid_size:
                errors.append(f"Block ({br},{bc}): duplicate values")
    
    # Check fixed values
    for known in config.get("known_digits", []):
        r = known["row"] - 1
        c = known["col"] - 1
        v = known["value"]
        if grid[r][c] != v:
            errors.append(f"Fixed value mismatch at ({r+1},{c+1}): expected {v}, got {grid[r][c]}")
    
    if errors:
        print(f"❌ Found {len(errors)} errors:")
        for e in errors[:5]:
            print(f"  - {e}")
    else:
        print("✅ All constraints satisfied!")
        print("✅ Rows: 16 unique values each")
        print("✅ Columns: 16 unique values each")
        print("✅ Blocks: 16 unique values each")
        print("✅ Fixed values: all match")


def save_solution(solver, x, config, output_name="solution_cpsat.json"):
    grid = get_grid(solver, x, 16)
    
    result = {
        "puzzle": "Level 2",
        "grid_size": 16,
        "box_size": 4,
        "solution": grid,
        "constraints": {
            "known_digits": config.get("known_digits", [])
        }
    }
    
    output_file = BASE_DIR / output_name
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nSolution saved to: {output_file}")


def main():
    print("=" * 60)
    print("Level 2 16x16 Sudoku - OR-Tools CP-SAT Solver")
    print("=" * 60)
    
    config = load_config()
    print(f"\nConfiguration:")
    print(f"  Grid size: {config['grid_size']}x{config['grid_size']}")
    print(f"  Block size: {config['box_size']}x{config['box_size']}")
    print(f"  Known digits: {len(config['known_digits'])}")
    
    permutations = load_permutations()
    
    # Phase 1: Solve with standard constraints only
    print("\n" + "=" * 60)
    print("Phase 1: Standard Sudoku Constraints Only")
    print("=" * 60)
    
    model1, x1 = create_cpsat_model(config, permutations, use_perm_constraints=False)
    print(f"\nModel Statistics:")
    print(f"  Variables: {len(x1)}")
    
    solved1, solver1 = solve(model1)
    
    if solved1:
        print("\nStandard solution found!")
        print("\n" + "=" * 60)
        print("GRID SOLUTION:")
        print("=" * 60)
        grid1 = get_grid(solver1, x1, 16)
        print_grid(grid1)
        
        verify_solution(solver1, x1, config, permutations)
        save_solution(solver1, x1, config, "solution_standard.json")
        
        # Check if this solution satisfies permutation constraints
        print("\n" + "=" * 60)
        print("Checking Permutation Constraints:")
        print("=" * 60)
        
        perm_violations = 0
        for row_idx in range(1, 17):
            row_name = f"A{row_idx}"
            if row_name in permutations:
                row_vals = grid1[row_idx-1]
                if row_vals not in permutations[row_name]:
                    perm_violations += 1
                    print(f"  Row {row_idx}: VIOLATED - not in allowed permutations")
                else:
                    print(f"  Row {row_idx}: OK")
        
        if perm_violations == 0:
            print("\n✅ Solution satisfies ALL permutation constraints!")
            print("Solution is complete and valid!")
        else:
            print(f"\n❌ {perm_violations} rows violate permutation constraints")
            print("\n" + "=" * 60)
            print("Phase 2: Adding Permutation Constraints")
            print("=" * 60)
            
            model2, x2 = create_cpsat_model(config, permutations, use_perm_constraints=True)
            print(f"\nModel Statistics:")
            print(f"  Variables: {len(x2)}")
            
            solved2, solver2 = solve(model2)
            
            if solved2:
                print("\nSolution with permutation constraints found!")
                grid2 = get_grid(solver2, x2, 16)
                print("\n" + "=" * 60)
                print("FINAL GRID SOLUTION:")
                print("=" * 60)
                print_grid(grid2)
                verify_solution(solver2, x2, config, permutations)
                save_solution(solver2, x2, config, "solution_full.json")
            else:
                print("\nCould not find solution with permutation constraints.")
                print("The puzzle may have no solution, or need more time.")
    else:
        print("\nNo solution found even with standard constraints.")
        print("The puzzle may have conflicting fixed values.")


if __name__ == "__main__":
    main()
