#!/usr/bin/env python3
"""
验证V63找到的唯一解是否真的存在于16行符阖排列xlsx文件中
"""

import json
from pathlib import Path
from zipfile import ZipFile
import re

# V63解
with open('solution_compressed_search.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
solution = data.get('solution', [])

row_letters = 'ABCDEFGHIJKLMNOP'

# xlsx文件映射
xlsx_files = {}
base = Path('.')
for f in base.glob('*.xlsx'):
    name = f.name
    if len(name) > 0 and name[0] in row_letters:
        xlsx_files[name[0]] = f

def row_in_xlsx(row_data, letter):
    """检查一个排列是否在对应行的xlsx文件中"""
    if letter not in xlsx_files:
        return False, "文件不存在"
    
    filepath = xlsx_files[letter]
    try:
        with ZipFile(filepath, 'r') as z:
            with z.open('xl/worksheets/sheet1.xml') as wf:
                content = wf.read().decode('utf-8')
            
            # 解析所有行，检查是否有完全匹配的
            rows = re.findall(r'<row[^>]*>(.*?)</row>', content, re.DOTALL)
            
            for row_xml in rows:
                cells = re.findall(r'<c r="([A-Z]+)(\d+)"[^>]*>(.*?)</c>', row_xml)
                xlsx_row = {}
                for ref, _, val_block in cells:
                    val_match = re.search(r'<v>(\d+)</v>', val_block)
                    if val_match:
                        xlsx_row[int(ref[1:]) if len(ref) == 2 else int(ref[1:])] = int(val_match.group(1))
                
                # 检查是否匹配（只检查D-P列，即第4-16列）
                match = True
                for col_idx, val in enumerate(row_data, start=1):
                    if col_idx >= 4 and col_idx <= 16:  # D-P列
                        if col_idx not in xlsx_row or xlsx_row[col_idx] != val:
                            match = False
                            break
                
                if match:
                    return True, None
                    
            return False, f"未找到匹配排列（共检查{len(rows)}个排列）"
    except Exception as e:
        return False, str(e)

print("="*70)
print("V63解各行在xlsx文件中的存在性验证")
print("="*70)
print()

results = {}
for i, letter in enumerate(row_letters):
    row_data = solution[i]
    found, error = row_in_xlsx(row_data, letter)
    status = "FOUND" if found else "NOT FOUND"
    results[letter] = found
    print(f"行{letter}: {status}")
    if error and not found:
        print(f"  错误: {error}")
    print(f"  排列: {row_data}")
    print()

print("="*70)
print("汇总")
print("="*70)

total = len(row_letters)
found_count = sum(1 for k, v in results.items() if v)
print(f"共检查 {total} 行")
print(f"在xlsx中找到: {found_count} 行")
print(f"未在xlsx中找到: {total - found_count} 行")

if found_count == total:
    print()
    print("结论: V63解的所有行都在对应的符阖排列xlsx文件中!")
else:
    print()
    print("结论: V63解的部分行不在xlsx文件中!")
    print("缺失的行:", [k for k, v in results.items() if not v])
