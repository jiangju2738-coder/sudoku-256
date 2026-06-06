#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從 XLSX 符闔排列文件提取完整排列數據, 生成 A1-A16_permutations.json。

用法:
    python extract_perms.py              # 提取全部 16 行
    python extract_perms.py --check      # 僅驗證, 不寫入
    python extract_perms.py --row A      # 只提取指定行
"""
import os
import sys
import json
import time
import argparse

# XLSX 文件名映射 (行字母 -> 文件名)
# 注意: XLSX 檔案存放在 xlsx/ 子目錄中
XLSX_MAP = {
    'A': 'A第一行符闔排列.xlsx',
    'B': 'B第二行符闔排列.xlsx',
    'C': 'C第三行符闔排列_補P10R.xlsx',  # 補P10R 有完整 656,777 排列
    'D': 'D第四行符闔排列.xlsx',
    'E': 'E第五行符闔排列.xlsx',
    'F': 'F第六行符闔排列.xlsx',
    'G': 'G第七行符闔排列.xlsx',
    'H': 'H第八行符闔排列.xlsx',
    'I': 'I第九行符闔排列.xlsx',
    'J': 'J第十行符闔排列.xlsx',
    'K': 'K第十一行符闔排列.xlsx',
    'L': 'L第十二行符闔排列.xlsx',
    'M': 'M第十三行符闔排列.xlsx',
    'N': 'N第十四行符闔排列.xlsx',
    'O': 'O第十五行符闔排列.xlsx',
    'P': 'P第十六行符闔排列.xlsx',
}

# PERM_STATS 預期值 (用於驗證)
EXPECTED_STATS = {
    'A': 8731, 'B': 902, 'C': 656777, 'D': 1980,
    'E': 633271, 'F': 359, 'G': 2356, 'H': 4782,
    'I': 164, 'J': 28984, 'K': 2972, 'L': 620,
    'M': 484, 'N': 10668, 'O': 5990, 'P': 1809,
}

ROW_LABELS = "ABCDEFGHIJKLMNOP"


def extract_from_xlsx(filepath, row_label, verbose=True):
    """
    從 XLSX 文件提取排列。
    使用 openpyxl read_only 模式以處理大文件。

    返回: (permutations_list, stats_dict)
    """
    import openpyxl

    perms = []
    skipped = 0
    invalid = 0
    t0 = time.time()

    if verbose:
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print("  Loading %.1f MB ..." % size_mb, end="", flush=True)

    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active

    if verbose:
        print(" reading ...", end="", flush=True)

    for i, row in enumerate(ws.iter_rows(values_only=True)):
        vals = list(row)

        # 需要至少 19 列 (label + index + label + 16 values)
        if len(vals) < 19:
            skipped += 1
            continue

        # 提取排列值 (列索引 3-18)
        try:
            perm = [int(v) for v in vals[3:19]]
        except (TypeError, ValueError):
            skipped += 1
            continue

        # 驗證: 16 個值, 範圍 1-16, 全排列
        if len(perm) == 16 and sorted(perm) == list(range(1, 17)):
            perms.append(perm)
        else:
            invalid += 1

    wb.close()
    elapsed = time.time() - t0

    stats = {
        "file": os.path.basename(filepath),
        "total_rows": i + 1,
        "valid_perms": len(perms),
        "skipped": skipped,
        "invalid": invalid,
        "time_sec": round(elapsed, 2),
    }

    if verbose:
        print(" %d perms in %.1fs" % (len(perms), elapsed))

    return perms, stats


def extract_via_zipfile(filepath, row_label, verbose=True):
    """
    備用方案: 用 zipfile + regex 解析 XLSX (不需 openpyxl)。
    對大文件可能較慢, 但無需額外依賴。
    """
    import zipfile
    import re

    perms = []
    skipped = 0
    invalid = 0
    t0 = time.time()

    if verbose:
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print("  [zipfile] Loading %.1f MB ..." % size_mb, end="", flush=True)

    with zipfile.ZipFile(filepath, 'r') as zf:
        sheet_xml = zf.read('xl/worksheets/sheet1.xml').decode('utf-8')

    if verbose:
        print(" parsing ...", end="", flush=True)

    rows = re.findall(r'<row[^>]*>(.*?)</row>', sheet_xml, re.DOTALL)

    for row_xml in rows:
        vals = re.findall(r'<v>([^<]*)</v>', row_xml)
        if len(vals) < 19:
            skipped += 1
            continue
        try:
            perm = [int(v) for v in vals[3:19]]
        except ValueError:
            skipped += 1
            continue
        if len(perm) == 16 and sorted(perm) == list(range(1, 17)):
            perms.append(perm)
        else:
            invalid += 1

    elapsed = time.time() - t0
    stats = {
        "file": os.path.basename(filepath),
        "total_rows": len(rows),
        "valid_perms": len(perms),
        "skipped": skipped,
        "invalid": invalid,
        "time_sec": round(elapsed, 2),
    }

    if verbose:
        print(" %d perms in %.1fs" % (len(perms), elapsed))

    return perms, stats


def main():
    parser = argparse.ArgumentParser(description="Extract permutations from XLSX")
    parser.add_argument("--check", action="store_true", help="Verify only, don't write")
    parser.add_argument("--row", type=str, default=None, help="Only extract specific row (A-P)")
    parser.add_argument("--zipfile", action="store_true", help="Use zipfile fallback instead of openpyxl")
    parser.add_argument("--base-dir", type=str, default=None, help="Base directory")
    args = parser.parse_args()

    base_dir = args.base_dir or os.path.dirname(os.path.abspath(__file__))
    extract_fn = extract_via_zipfile if args.zipfile else extract_from_xlsx

    rows_to_process = [args.row.upper()] if args.row else list(ROW_LABELS)

    print("=" * 70)
    print("  XLSX -> JSON Permutation Extractor")
    print("  Base dir: %s" % base_dir)
    print("=" * 70)

    all_stats = []
    total_perms = 0
    total_time = 0

    for label in rows_to_process:
        idx = ROW_LABELS.index(label)
        json_name = "A%d_permutations.json" % (idx + 1)
        xlsx_name = XLSX_MAP.get(label)

        if not xlsx_name:
            print("\nRow %s: no XLSX mapping found, skipping" % label)
            continue

        # XLSX 檔案存放在 xlsx/ 子目錄中
        xlsx_dir = os.path.join(base_dir, "xlsx")
        if not os.path.isdir(xlsx_dir):
            xlsx_dir = base_dir  # fallback: 直接在 base_dir 找
        xlsx_path = os.path.join(xlsx_dir, xlsx_name)
        if not os.path.exists(xlsx_path):
            print("\nRow %s: XLSX not found: %s" % (label, xlsx_name))
            continue

        print("\n[Row %s] %s" % (label, xlsx_name))
        perms, stats = extract_fn(xlsx_path, label, verbose=True)
        stats["row"] = label
        stats["json_file"] = json_name

        # Compare with PERM_STATS expected
        expected = EXPECTED_STATS.get(label, None)
        if expected:
            match = "MATCH" if len(perms) == expected else "DIFF (%d vs %d)" % (len(perms), expected)
            stats["expected"] = expected
            stats["match"] = match
            print("  Expected: %d -> %s" % (expected, match))

        # Check existing JSON
        json_path = os.path.join(base_dir, json_name)
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            overlap = len(set(tuple(p) for p in perms) & set(tuple(p) for p in existing))
            stats["existing_count"] = len(existing)
            stats["overlap"] = overlap
            print("  Existing JSON: %d perms, overlap: %d" % (len(existing), overlap))

        # Write output
        if not args.check and perms:
            out_path = os.path.join(base_dir, json_name)
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(perms, f)
            size_kb = os.path.getsize(out_path) / 1024
            print("  Written: %s (%.1f KB)" % (json_name, size_kb))

        all_stats.append(stats)
        total_perms += len(perms)
        total_time += stats["time_sec"]

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print("  %-4s  %-10s  %-10s  %-10s  %-8s  %s" % (
        "Row", "Extracted", "Expected", "Match", "Time", "Overlap"))
    print("  " + "-" * 60)
    for s in all_stats:
        overlap_str = str(s.get("overlap", "-"))
        print("  %-4s  %-10d  %-10s  %-10s  %-6.1fs  %s" % (
            s["row"], s["valid_perms"],
            str(s.get("expected", "-")),
            s.get("match", "-"),
            s["time_sec"],
            overlap_str,
        ))

    print("  " + "-" * 60)
    print("  Total: %d permutations in %.1fs" % (total_perms, total_time))
    print("=" * 70)

    # Save extraction report
    if not args.check:
        report_path = os.path.join(base_dir, "extraction_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_permutations": total_perms,
                "total_time_sec": round(total_time, 2),
                "rows": all_stats,
            }, f, ensure_ascii=False, indent=2)
        print("\nReport saved: %s" % report_path)


if __name__ == "__main__":
    main()
