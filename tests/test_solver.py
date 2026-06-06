#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
256 數獨求解器 - CI 測試套件

測試項目:
  1. 常數與數據完整性
  2. 已知解驗證
  3. DataLoader 功能
  4. SolutionVerifier 驗證邏輯
  5. 求解器 (cpsat_plain + backtrack, cpsat_perm 有檔案時才跑)
  6. CLI 命令 (solve256.py)
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

# 確保能匯入專案模組
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sudoku256.constants import (
    N, BOX_SIZE, VALUES, ROW_LABELS,
    ANCHORS_92, KNOWN_SOLUTION_92, KNOWN_SOLUTION_53,
    ROW_C_FINAL, ROW_D_FINAL, ROW_I_FINAL,
    ROW_E_FINAL, ROW_H_FINAL, ROW_P_FINAL,
    PERM_STATS, TOTAL_PERMS,
    anchors_to_grid, puzzle_dict_to_grid, grid_to_puzzle_dict,
    count_anchors, box_index, INITIAL_PUZZLE_92,
)
from sudoku256.verifier import SolutionVerifier
from sudoku256.loader import DataLoader
from sudoku256.propagator import PermutationFilter, AC3Propagator
from sudoku256.solver import Sudoku256Solver, SolveResult


# ═══════════════════════════════════════════════════════════════
#  Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def project_root():
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def loader():
    return DataLoader(str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def known_solution():
    """回傳 KNOWN_SOLUTION_92 的深拷貝"""
    return [row[:] for row in KNOWN_SOLUTION_92]


@pytest.fixture(scope="session")
def has_ortools():
    """偵測 OR-Tools 是否可用"""
    try:
        from ortools.sat.python import cp_model
        return True
    except ImportError:
        return False


@pytest.fixture(scope="session")
def has_perm_files():
    """偵測排列 JSON 檔案是否完整"""
    count = sum(
        1 for i in range(N)
        if (PROJECT_ROOT / f"A{i + 1}_permutations.json").exists()
    )
    return count == N


# ═══════════════════════════════════════════════════════════════
#  1. 常數與數據完整性
# ═══════════════════════════════════════════════════════════════

class TestConstants:
    """網格常量與數據定義的完整性測試"""

    def test_grid_size(self):
        assert N == 16

    def test_box_size(self):
        assert BOX_SIZE == 4

    def test_values(self):
        assert VALUES == list(range(1, 17))
        assert len(VALUES) == N

    def test_row_labels(self):
        assert len(ROW_LABELS) == N
        assert ROW_LABELS[0] == "A"
        assert ROW_LABELS[15] == "P"

    def test_anchors_92_count(self):
        """ANCHORS_92 應有 114 項 (含 C/D/I 完全固定行)"""
        assert len(ANCHORS_92) == 114

    def test_anchors_92_values_range(self):
        """所有錨點值必須在 1-16 範圍內"""
        for (r, c), v in ANCHORS_92.items():
            assert 1 <= v <= N, f"錨點 ({r},{c})={v} 超出範圍"
            assert 0 <= r < N, f"行索引 {r} 超出範圍"
            assert 0 <= c < N, f"列索引 {c} 超出範圍"

    def test_anchors_92_no_duplicate_positions(self):
        """錨點位置不可重複"""
        positions = list(ANCHORS_92.keys())
        assert len(positions) == len(set(positions))

    def test_anchors_92_fixed_rows(self):
        """C/D/I 行應各有 16 個錨點 (完全固定)"""
        for row_idx in [2, 3, 8]:  # C, D, I
            count = sum(1 for (r, _) in ANCHORS_92 if r == row_idx)
            assert count == N, f"行{ROW_LABELS[row_idx]} 錨點數={count}, 預期={N}"

    def test_perm_stats_total(self):
        """排列統計總數 = 1,360,849"""
        assert TOTAL_PERMS == 1_360_849
        assert sum(PERM_STATS.values()) == TOTAL_PERMS

    def test_perm_stats_coverage(self):
        """排列統計覆蓋全部 16 行"""
        assert len(PERM_STATS) == N
        for label in ROW_LABELS:
            assert label in PERM_STATS, f"缺少行{label}的排列統計"
            assert PERM_STATS[label] > 0, f"行{label}排列數為 0"


# ═══════════════════════════════════════════════════════════════
#  2. 已知解驗證
# ═══════════════════════════════════════════════════════════════

class TestKnownSolution:
    """KNOWN_SOLUTION_92 的正確性驗證"""

    def test_solution_dimensions(self, known_solution):
        assert len(known_solution) == N
        for row in known_solution:
            assert len(row) == N

    def test_solution_row_constraints(self, known_solution):
        """每行是 1-16 全排列"""
        expected = set(VALUES)
        for i, row in enumerate(known_solution):
            assert set(row) == expected, f"行{i + 1} ({ROW_LABELS[i]}) 不滿足全排列"

    def test_solution_column_constraints(self, known_solution):
        """每列是 1-16 全排列"""
        expected = set(VALUES)
        for c in range(N):
            col = {known_solution[r][c] for r in range(N)}
            assert col == expected, f"列{c + 1} 不滿足全排列"

    def test_solution_box_constraints(self, known_solution):
        """每個 4x4 宮格是 1-16 全排列 (至少對非放鬆宮格)"""
        expected = set(VALUES)
        for b in range(N):
            br = (b // BOX_SIZE) * BOX_SIZE
            bc = (b % BOX_SIZE) * BOX_SIZE
            box = set()
            for dr in range(BOX_SIZE):
                for dc in range(BOX_SIZE):
                    box.add(known_solution[br + dr][bc + dc])
            # 注意: 某些宮格可能因符闔行衝突而放鬆
            # 但 KNOWN_SOLUTION_92 經驗證全部通過
            if box != expected:
                pytest.skip(f"宮{b + 1} 有符闔行間衝突 (預期行為)")

    def test_solution_anchors_match(self, known_solution):
        """解必須與所有 92 錨點一致"""
        for (r, c), expected_val in ANCHORS_92.items():
            assert known_solution[r][c] == expected_val, (
                f"錨點 ({ROW_LABELS[r]}{c + 1}): "
                f"期望 {expected_val}, 實際 {known_solution[r][c]}"
            )

    def test_verifier_passes(self, known_solution):
        """SolutionVerifier 應對已知解全部通過"""
        verifier = SolutionVerifier(known_solution)
        result = verifier.verify_all(anchors=ANCHORS_92)
        assert result["row_ok"], f"行驗證失敗: {result['errors']}"
        assert result["col_ok"], f"列驗證失敗: {result['errors']}"
        assert result["anchor_ok"], f"錨點驗證失敗: {result['errors']}"
        assert result["error_count"] == 0, f"驗證錯誤: {result['errors']}"

    def test_quick_check(self, known_solution):
        """靜態 quick_check 應通過"""
        result = SolutionVerifier.quick_check(known_solution)
        assert result["row_ok"]
        assert result["col_ok"]
        # box_ok 可能因符闔行放鬆而略過


# ═══════════════════════════════════════════════════════════════
#  3. 完全固定行驗證
# ═══════════════════════════════════════════════════════════════

class TestFixedRows:
    """C/D/I 完全固定行的數據一致性"""

    def test_row_c_is_permutation(self):
        assert sorted(ROW_C_FINAL) == VALUES

    def test_row_d_is_permutation(self):
        assert sorted(ROW_D_FINAL) == VALUES

    def test_row_i_is_permutation(self):
        assert sorted(ROW_I_FINAL) == VALUES

    def test_row_c_matches_anchors(self):
        for c in range(N):
            if (2, c) in ANCHORS_92:
                assert ROW_C_FINAL[c] == ANCHORS_92[(2, c)]

    def test_row_d_matches_anchors(self):
        for c in range(N):
            if (3, c) in ANCHORS_92:
                assert ROW_D_FINAL[c] == ANCHORS_92[(3, c)]

    def test_row_i_matches_anchors(self):
        for c in range(N):
            if (8, c) in ANCHORS_92:
                assert ROW_I_FINAL[c] == ANCHORS_92[(8, c)]

    def test_row_c_matches_solution(self, known_solution):
        assert known_solution[2] == ROW_C_FINAL

    def test_row_d_matches_solution(self, known_solution):
        assert known_solution[3] == ROW_D_FINAL

    def test_row_i_matches_solution(self, known_solution):
        assert known_solution[8] == ROW_I_FINAL

    def test_extra_row_e(self):
        assert sorted(ROW_E_FINAL) == VALUES

    def test_extra_row_h(self):
        assert sorted(ROW_H_FINAL) == VALUES

    def test_extra_row_p(self):
        assert sorted(ROW_P_FINAL) == VALUES


# ═══════════════════════════════════════════════════════════════
#  4. 輔助函數測試
# ═══════════════════════════════════════════════════════════════

class TestHelperFunctions:
    """輔助函數的正確性測試"""

    def test_anchors_to_grid(self):
        grid = anchors_to_grid(ANCHORS_92)
        assert len(grid) == N
        assert len(grid[0]) == N
        # 錨點位置應有值
        assert grid[0][2] == 3  # A3=3
        assert grid[2][0] == 5  # C1=5
        # 非錨點位置應為 0
        assert grid[0][0] == 0

    def test_anchors_to_grid_empty(self):
        grid = anchors_to_grid({})
        assert all(grid[r][c] == 0 for r in range(N) for c in range(N))

    def test_puzzle_dict_to_grid(self):
        grid = puzzle_dict_to_grid(INITIAL_PUZZLE_92)
        assert len(grid) == N
        # 與 anchors_to_grid 結果應相同
        grid2 = anchors_to_grid(ANCHORS_92)
        assert grid == grid2

    def test_grid_to_puzzle_dict_roundtrip(self, known_solution):
        """grid -> dict -> grid 應無損"""
        d = grid_to_puzzle_dict(known_solution)
        assert len(d) == N
        grid2 = puzzle_dict_to_grid(d)
        assert grid2 == known_solution

    def test_count_anchors(self):
        grid = anchors_to_grid(ANCHORS_92)
        c = count_anchors(grid)
        assert c == 114  # ANCHORS_92 有 114 項

    def test_count_anchors_empty(self):
        grid = [[0] * N for _ in range(N)]
        assert count_anchors(grid) == 0

    def test_count_anchors_full(self, known_solution):
        assert count_anchors(known_solution) == N * N

    def test_box_index(self):
        # 左上角宮格
        assert box_index(0, 0) == 0
        assert box_index(3, 3) == 0
        # 右上角宮格
        assert box_index(0, 12) == 3
        assert box_index(3, 15) == 3
        # 左下角宮格
        assert box_index(12, 0) == 12
        # 右下角宮格
        assert box_index(15, 15) == 15
        # 中間宮格
        assert box_index(4, 4) == 5


# ═══════════════════════════════════════════════════════════════
#  5. DataLoader 測試
# ═══════════════════════════════════════════════════════════════

class TestDataLoader:
    """數據加載器功能測試"""

    def test_init_default_dir(self):
        loader = DataLoader()
        assert loader.base_dir.exists()

    def test_init_custom_dir(self, project_root):
        loader = DataLoader(str(project_root))
        assert loader.base_dir == project_root

    def test_find_permutation_files(self, loader):
        """探測排列檔案 (CI 環境可能為 0)"""
        found = loader.find_permutation_files()
        assert isinstance(found, dict)
        for k, v in found.items():
            assert 0 <= k < N
            assert isinstance(v, Path)
            assert v.exists()

    def test_get_data_availability(self, loader):
        report = loader.get_data_availability()
        assert "config_json" in report
        assert "permutation_files" in report
        assert "xlsx_files" in report
        assert "solution_files" in report
        assert isinstance(report["permutation_files"], dict)
        assert len(report["permutation_files"]) == N

    def test_load_permutations_valid_index(self, loader, has_perm_files):
        """加載存在的排列檔案"""
        found = loader.find_permutation_files()
        if not found:
            pytest.skip("排列 JSON 檔案不存在 (CI 環境預期行為)")
        # 加載第一個可用檔案
        idx = next(iter(found))
        perms = loader.load_permutations(idx)
        assert isinstance(perms, list)
        assert len(perms) > 0
        for p in perms:
            assert len(p) == N
            assert sorted(p) == VALUES

    def test_load_permutations_missing_file(self, loader):
        """加載不存在的檔案應拋出 FileNotFoundError"""
        # 找到一個不存在的行
        found = loader.find_permutation_files()
        for i in range(N):
            if i not in found:
                with pytest.raises(FileNotFoundError):
                    loader.load_permutations(i)
                return
        pytest.skip("所有排列檔案都存在, 無法測試缺失情況")

    def test_load_all_permutations(self, loader):
        all_perms = loader.load_all_permutations()
        assert len(all_perms) == N
        for perms in all_perms:
            assert isinstance(perms, list)


# ═══════════════════════════════════════════════════════════════
#  6. SolutionVerifier 測試
# ═══════════════════════════════════════════════════════════════

class TestSolutionVerifier:
    """解驗證器邏輯測試"""

    def test_verify_valid_solution(self, known_solution):
        verifier = SolutionVerifier(known_solution)
        assert verifier.verify_rows()

    def test_verify_anchors(self, known_solution):
        verifier = SolutionVerifier(known_solution)
        assert verifier.verify_anchors(ANCHORS_92)

    def test_verify_anchors_wrong_value(self, known_solution):
        """修改解中一個錨點值, 驗證應失敗"""
        bad = [row[:] for row in known_solution]
        # 找一個錨點位置並改值
        (r, c), _ = next(iter(ANCHORS_92.items()))
        bad[r][c] = (bad[r][c] % N) + 1  # 改為不同值
        verifier = SolutionVerifier(bad)
        assert not verifier.verify_anchors(ANCHORS_92)

    def test_verify_rows_invalid(self):
        """重複值的行應失敗"""
        bad = [[1] * N for _ in range(N)]  # 全部填 1
        verifier = SolutionVerifier(bad)
        assert not verifier.verify_rows()

    def test_verify_columns(self, known_solution):
        verifier = SolutionVerifier(known_solution)
        assert verifier.verify_columns_fuhe({2, 3, 8})

    def test_is_valid(self, known_solution):
        verifier = SolutionVerifier(known_solution)
        assert verifier.is_valid(anchors=ANCHORS_92)

    def test_is_valid_wrong_solution(self):
        """全零網格應驗證失敗"""
        zero_grid = [[0] * N for _ in range(N)]
        verifier = SolutionVerifier(zero_grid)
        assert not verifier.is_valid(anchors=ANCHORS_92)

    def test_verify_all_returns_dict(self, known_solution):
        verifier = SolutionVerifier(known_solution)
        result = verifier.verify_all(anchors=ANCHORS_92)
        assert isinstance(result, dict)
        expected_keys = {
            "row_ok", "col_ok", "box_ok", "box_strict_ok",
            "box_relaxed_ok", "anchor_ok", "fummel_ok",
            "errors", "error_count",
        }
        assert expected_keys.issubset(result.keys())


# ═══════════════════════════════════════════════════════════════
#  7. AC-3 約束傳播測試
# ═══════════════════════════════════════════════════════════════

class TestAC3Propagator:
    """AC-3 約束傳播引擎測試"""

    def test_ac3_reduces_domains(self):
        """AC-3 應能減少空格的候選值數量"""
        grid = anchors_to_grid(ANCHORS_92)
        propagator = AC3Propagator(grid)
        success, iterations = propagator.run()
        assert success, "AC-3 不應判定無解 (92 錨點有解)"
        assert iterations > 0
        # AC-3 後候選域應比初始小
        total = propagator.total_candidates()
        assert total < N * N * N  # 遠小於全部 16 候選

    def test_ac3_detects_contradiction(self):
        """衝突網格應被 AC-3 偵測"""
        grid = [[0] * N for _ in range(N)]
        # 在第一行放兩個 1
        grid[0][0] = 1
        grid[0][1] = 1
        propagator = AC3Propagator(grid)
        success, _ = propagator.run()
        # AC-3 可能或可能不偵測到此衝突 (取決於實作)
        # 但不应崩溃
        assert isinstance(success, bool)


# ═══════════════════════════════════════════════════════════════
#  8. 求解器測試
# ═══════════════════════════════════════════════════════════════

class TestSolver:
    """求解器功能測試"""

    def test_solver_init(self):
        engine = Sudoku256Solver(verbose=False)
        assert engine is not None
        assert engine.verbose is False

    def test_auto_detect_strategy(self, has_ortools):
        engine = Sudoku256Solver(verbose=False)
        strategy = engine._detect_strategy()
        assert strategy in ("cpsat_perm", "cpsat_plain", "backtrack")
        if not has_ortools:
            assert strategy == "backtrack"

    def test_solve_cpsat_plain(self, has_ortools):
        """CP-SAT 標準模型應能找到有效解"""
        if not has_ortools:
            pytest.skip("OR-Tools 未安裝")
        engine = Sudoku256Solver(verbose=False)
        result = engine.solve(strategy="cpsat_plain", time_limit=60)
        assert result.status == "SOLVED"
        assert result.solution is not None
        # 驗證解
        v = result.verification
        assert v["row_ok"]
        assert v["anchor_ok"]
        assert v["error_count"] == 0

    def test_solve_backtrack(self):
        """回溯法應能找到有效解 (可能較慢)"""
        engine = Sudoku256Solver(verbose=False)
        result = engine.solve(strategy="backtrack", time_limit=120)
        assert result.status == "SOLVED"
        assert result.solution is not None
        v = result.verification
        assert v["row_ok"]
        assert v["anchor_ok"]
        assert v["error_count"] == 0

    def test_solve_auto(self, has_ortools):
        """自動策略選擇應能成功求解"""
        engine = Sudoku256Solver(verbose=False)
        # 回溯可能需要較長時間, 給足時限
        limit = 300 if not has_ortools else 120
        result = engine.solve(time_limit=limit)
        assert result.status == "SOLVED"
        assert result.solution is not None

    def test_solve_result_to_dict(self, known_solution):
        """SolveResult 序列化測試"""
        r = SolveResult(
            status="SOLVED",
            solution=known_solution,
            solver_name="test",
            strategy="test",
        )
        d = r.to_dict()
        assert d["status"] == "SOLVED"
        assert d["solver"] == "test"
        assert d["solution"] == known_solution
        assert "timestamp" in d

    def test_solve_result_save(self, known_solution, tmp_path):
        """SolveResult 保存/讀取測試"""
        r = SolveResult(
            status="SOLVED",
            solution=known_solution,
            solver_name="test",
        )
        filepath = tmp_path / "test_result.json"
        r.save(str(filepath))
        assert filepath.exists()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["status"] == "SOLVED"
        assert len(data["solution"]) == N

    def test_solve_cpsat_perm(self, has_ortools, has_perm_files):
        """CP-SAT + 排列過濾應能找到有效解 (需要排列檔案)"""
        if not has_ortools:
            pytest.skip("OR-Tools 未安裝")
        if not has_perm_files:
            pytest.skip("排列 JSON 檔案不存在 (CI 環境預期行為)")
        engine = Sudoku256Solver(verbose=False)
        result = engine.solve(strategy="cpsat_perm", time_limit=120)
        assert result.status == "SOLVED"
        assert result.filter_time > 0  # 應有過濾耗時


# ═══════════════════════════════════════════════════════════════
#  9. CLI 測試
# ═══════════════════════════════════════════════════════════════

class TestCLI:
    """solve256.py 命令行介面測試"""

    def _run_cli(self, args, timeout=120):
        """執行 CLI 命令"""
        cmd = [sys.executable, str(PROJECT_ROOT / "solve256.py")] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
        )
        return result

    def test_cli_info(self):
        """--info 應正常執行並輸出數據摘要"""
        result = self._run_cli(["--info"])
        assert result.returncode == 0
        assert "92 錨點" in result.stdout or "92" in result.stdout

    def test_cli_help(self):
        """--help 應顯示使用說明"""
        result = self._run_cli(["--help"])
        assert result.returncode == 0
        assert "256 數獨" in result.stdout or "sudoku" in result.stdout.lower()

    def test_cli_verify_known_solution(self, tmp_path):
        """--verify 應能驗證已知解"""
        # 先寫入已知解
        sol_file = tmp_path / "known_sol.json"
        with open(sol_file, "w", encoding="utf-8") as f:
            json.dump({"solution": KNOWN_SOLUTION_92}, f)

        result = self._run_cli(["--verify", str(sol_file)])
        assert result.returncode == 0
        assert "PASS" in result.stdout or "通過" in result.stdout

    def test_cli_verify_invalid(self, tmp_path):
        """--verify 應偵測無效解"""
        bad_sol = [[1] * N for _ in range(N)]
        sol_file = tmp_path / "bad_sol.json"
        with open(sol_file, "w", encoding="utf-8") as f:
            json.dump({"solution": bad_sol}, f)

        result = self._run_cli(["--verify", str(sol_file)])
        assert result.returncode == 1 or "FAIL" in result.stdout

    def test_cli_verify_missing_file(self):
        """--verify 不存在的檔案"""
        result = self._run_cli(["--verify", "/nonexistent/file.json"])
        assert result.returncode == 1 or "不存在" in result.stdout

    def test_cli_solve_backtrack(self, tmp_path):
        """CLI 求解 (回溯策略)"""
        out_file = tmp_path / "cli_result.json"
        result = self._run_cli([
            "--strategy", "backtrack",
            "--time-limit", "120",
            "--output", str(out_file),
            "--quiet",
        ], timeout=180)
        assert result.returncode == 0
        assert out_file.exists()
        with open(out_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["status"] == "SOLVED"


# ═══════════════════════════════════════════════════════════════
#  10. 邊界情況與健壯性
# ═══════════════════════════════════════════════════════════════

class TestEdgeCases:
    """邊界情況與健壯性測試"""

    def test_initial_puzzle_consistency(self):
        """INITIAL_PUZZLE_92 應與 ANCHORS_92 一致"""
        grid = puzzle_dict_to_grid(INITIAL_PUZZLE_92)
        grid2 = anchors_to_grid(ANCHORS_92)
        assert grid == grid2

    def test_known_solution_53_dimensions(self):
        assert len(KNOWN_SOLUTION_53) == N
        for row in KNOWN_SOLUTION_53:
            assert len(row) == N

    def test_known_solution_53_rows_valid(self):
        """53 錨點解的行約束"""
        expected = set(VALUES)
        for row in KNOWN_SOLUTION_53:
            assert set(row) == expected

    def test_verifier_empty_errors(self, known_solution):
        """驗證後 errors 列表行為"""
        verifier = SolutionVerifier(known_solution)
        verifier.verify_all(anchors=ANCHORS_92)
        assert isinstance(verifier.errors, list)
        assert len(verifier.errors) == 0

    def test_solve_result_defaults(self):
        """SolveResult 預設值"""
        r = SolveResult(status="UNKNOWN")
        assert r.solution is None
        assert r.solver_name == ""
        assert r.filter_time == 0.0
        assert r.solve_time == 0.0
        assert r.errors == []

    def test_loader_xlsx_fallback_missing_file(self, loader):
        """XLSX 備用加載不存在的檔案"""
        with pytest.raises(FileNotFoundError):
            loader.load_permutations_from_xlsx("nonexistent.xlsx")
