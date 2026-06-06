#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據加載器 - 統一處理 JSON / 排列文件 / XLSX 數據源

職責:
    1. 加載 sudoku_config.json (53錨點)
    2. 加載 A1~A16_permutations.json (符闔排列)
    3. 從 XLSX 文件提取排列 (備用)
    4. 自動探測可用數據源
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .constants import N, ROW_LABELS, PERM_STATS


class DataLoader:
    """統一數據加載器"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = Path(base_dir)

    # ─────────────────────────────────────────────
    #  JSON 配置加載
    # ─────────────────────────────────────────────

    def load_config(self, filename: str = "sudoku_config.json") -> dict:
        """加載 sudoku_config.json"""
        path = self.base_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"配置檔案不存在: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_solution(self, filename: str = "solution.json") -> dict:
        """加載已有的解檔案"""
        path = self.base_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"解檔案不存在: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ─────────────────────────────────────────────
    #  符闔排列加載
    # ─────────────────────────────────────────────

    def find_permutation_files(self) -> Dict[int, Path]:
        """
        自動探測 A1~A16_permutations.json 檔案。
        回傳: {row_index (0-15): file_path}
        """
        found = {}
        for i in range(N):
            path = self.base_dir / f"A{i + 1}_permutations.json"
            if path.exists():
                found[i] = path
        return found

    def load_permutations(self, row_index: int) -> List[List[int]]:
        """
        加載指定行的符闔排列集合。
        row_index: 0-15 (對應 A-P 行)
        """
        path = self.base_dir / f"A{row_index + 1}_permutations.json"
        if not path.exists():
            raise FileNotFoundError(
                f"排列檔案不存在: {path}\n"
                f"請確認 A{row_index + 1}_permutations.json 存在於 {self.base_dir}"
            )
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 驗證格式
        if not isinstance(data, list):
            raise ValueError(f"A{row_index + 1}_permutations.json 格式錯誤: 預期 list")
        for perm in data:
            if len(perm) != N:
                raise ValueError(
                    f"A{row_index + 1}_permutations.json 排列長度錯誤: "
                    f"預期 {N}, 實際 {len(perm)}"
                )
        return data

    def load_all_permutations(self) -> List[List[List[int]]]:
        """
        加載全部 16 行的符闔排列。
        回傳: [row0_perms, row1_perms, ..., row15_perms]
        """
        all_perms = []
        for i in range(N):
            try:
                perms = self.load_permutations(i)
                all_perms.append(perms)
            except FileNotFoundError:
                # 若檔案不存在, 用空列表填充
                all_perms.append([])
        return all_perms

    def load_closed_permutations(self, row_index: int) -> List[List[int]]:
        """加載指定行的封閉排列 (約束傳播後唯一解)"""
        path = self.base_dir / f"A{row_index + 1}_closed_permutations.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ─────────────────────────────────────────────
    #  XLSX 備用加載 (使用 zipfile + xml)
    # ─────────────────────────────────────────────

    def load_permutations_from_xlsx(self, xlsx_filename: str) -> List[List[int]]:
        """
        從 XLSX 文件提取排列數據 (備用方案)。
        直接解析 XLSX 內部 XML, 不依賴 openpyxl。
        """
        import zipfile
        import re

        path = self.base_dir / xlsx_filename
        if not path.exists():
            raise FileNotFoundError(f"XLSX 檔案不存在: {path}")

        perms = []
        with zipfile.ZipFile(path, 'r') as zf:
            # 讀取 shared strings
            shared_strings = []
            if 'xl/sharedStrings.xml' in zf.namelist():
                ss_xml = zf.read('xl/sharedStrings.xml').decode('utf-8')
                shared_strings = re.findall(r'<t[^>]*>([^<]*)</t>', ss_xml)

            # 讀取第一個工作表
            sheet_path = 'xl/worksheets/sheet1.xml'
            if sheet_path not in zf.namelist():
                raise ValueError(f"XLSX 中找不到 {sheet_path}")

            sheet_xml = zf.read(sheet_path).decode('utf-8')
            rows = re.findall(r'<row[^>]*>(.*?)</row>', sheet_xml, re.DOTALL)

            for row_xml in rows:
                cells = re.findall(
                    r'<c[^>]*>(?:<v>([^<]*)</v>)?</c>', row_xml
                )
                if len(cells) >= N:
                    try:
                        values = []
                        for cell in cells[:N]:
                            if cell.isdigit():
                                val = int(cell)
                            elif cell and shared_strings:
                                idx = int(cell)
                                val = int(shared_strings[idx])
                            else:
                                continue
                            values.append(val)
                        if len(values) == N and sorted(values) == list(range(1, N + 1)):
                            perms.append(values)
                    except (ValueError, IndexError):
                        continue

        return perms

    # ─────────────────────────────────────────────
    #  數據源探測與統計
    # ─────────────────────────────────────────────

    def get_data_availability(self) -> dict:
        """探測可用數據源, 回傳可用性報告"""
        report = {
            "config_json": (self.base_dir / "sudoku_config.json").exists(),
            "permutation_files": {},
            "xlsx_files": {},
            "solution_files": {},
        }

        # 排列 JSON 文件
        for i in range(N):
            label = ROW_LABELS[i]
            json_path = self.base_dir / f"A{i + 1}_permutations.json"
            report["permutation_files"][label] = json_path.exists()

        # XLSX 文件
        xlsx_pattern = str(self.base_dir / "*符闔排列*.xlsx")
        xlsx_files = glob.glob(xlsx_pattern)
        for xf in xlsx_files:
            name = os.path.basename(xf)
            report["xlsx_files"][name] = True

        # 解檔案
        for sol_file in ["solution.json", "solution_92_anchors.json",
                         "all_solutions_found.json"]:
            report["solution_files"][sol_file] = (
                self.base_dir / sol_file
            ).exists()

        return report

    def print_data_summary(self):
        """打印數據可用性摘要"""
        report = self.get_data_availability()

        perm_count = sum(1 for v in report["permutation_files"].values() if v)
        xlsx_count = len(report["xlsx_files"])
        sol_count = sum(1 for v in report["solution_files"].values() if v)

        print(f"數據目錄: {self.base_dir}")
        print(f"  配置 JSON:       {'有' if report['config_json'] else '無'}")
        print(f"  排列 JSON 文件:  {perm_count}/16 行")
        print(f"  XLSX 文件:       {xlsx_count} 個")
        print(f"  已有解檔案:      {sol_count} 個")

        if perm_count > 0:
            print(f"\n  符闔排列統計:")
            total = 0
            for label in ROW_LABELS:
                if report["permutation_files"].get(label):
                    idx = ROW_LABELS.index(label)
                    count = PERM_STATS.get(label, 0)
                    total += count
                    print(f"    {label}: {count:>10,}")
                else:
                    print(f"    {label}: (檔案缺失)")
            print(f"    總計: {total:>10,}")
