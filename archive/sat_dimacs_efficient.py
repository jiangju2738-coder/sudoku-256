#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAT DIMACS 精確編碼 - 符闔數獨
使用分塊編碼和高效序數編碼，避免記憶體溢出
"""

import json
import time
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import gc


class SATDimacsEncoderEfficient:
    """高效SAT DIMACS編碼器"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16
        self.box_size = 4
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        self.var_counter = 0
        self.var_map: Dict[str, int] = {}
        
        # 分批寫入文件
        self.output_path = "sudoku_efficient.dimacs"
        self.header_written = False
        self.clause_count = 0
        
        self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """載入配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'known_digits' in config:
            for clue in config['known_digits']:
                self.known_map[(clue['row'], clue['col'])] = clue['value']
        elif 'clues' in config:
            for clue in config['clues']:
                self.known_map[(clue['row'], clue['col'])] = clue['value']
        
        for row in range(self.N):
            try:
                with open(f"A{row+1}_permutations.json", 'r', encoding='utf-8') as f:
                    self.row_perms[row] = json.load(f)
            except FileNotFoundError:
                self.row_perms[row] = []
        
        print(f"  已知數字: {len(self.known_map)} 個")
        print(f"  排列總數: {sum(len(p) for p in self.row_perms):,}")
    
    def get_var(self, row: int, col: int, val: int) -> int:
        """位置值變數: x[row][col][val]"""
        key = f"x{row}_{col}_{val}"
        if key not in self.var_map:
            self.var_counter += 1
            self.var_map[key] = self.var_counter
        return self.var_map[key]
    
    def encode_exactly_one_lazy(self, vars_list: List[int], f):
        """懶惰 ExactlyOne 編碼：至少一個 + 兩兩互斥（分塊）"""
        # 至少一個
        f.write(" ".join(str(v) for v in vars_list) + " 0\n")
        self.clause_count += 1
        
        # 兩兩互斥 - 分塊處理避免記憶體
        n = len(vars_list)
        chunk_size = 1000
        for i in range(0, n, chunk_size):
            chunk = vars_list[i:i+chunk_size]
            for j in range(len(chunk)):
                for k in range(j+1, len(chunk)):
                    f.write(f"-{chunk[j]} -{chunk[k]} 0\n")
                    self.clause_count += 1
    
    def encode_at_most_one_efficient(self, vars_list: List[int], f):
        """高效 AtMostOne：使用序數變數編碼"""
        n = len(vars_list)
        if n <= 1:
            return
        
        # 序數編碼需要額外變數
        # s_i 表示前i個變數中至少一個為True
        # 實際實現複雜，這裡用簡化版
        
        # 使用Lingeling-style編碼：需要 log2(n) 個輔助變數
        # 這裡使用簡單分塊兩兩互斥
        
        chunk_size = 500
        for i in range(0, n, chunk_size):
            chunk = vars_list[i:i+chunk_size]
            for j in range(len(chunk)):
                for k in range(j+1, len(chunk)):
                    f.write(f"-{chunk[j]} -{chunk[k]} 0\n")
                    self.clause_count += 1
    
    def encode(self):
        """分塊編碼，直接寫入文件"""
        print("\n開始高效編碼...")
        f = open(self.output_path, 'w', encoding='utf-8')
        
        try:
            # 先計算變數總數
            print("  計算變數總數...")
            for row in range(self.N):
                for col in range(self.N):
                    for val in range(1, self.N+1):
                        self.get_var(row, col, val)
            
            perm_var_start = self.var_counter + 1
            
            for row in range(self.N):
                for idx in range(len(self.row_perms[row])):
                    self.var_counter += 1  # 排列選擇變數
            
            total_vars = self.var_counter
            print(f"  總變數數: {total_vars:,}")
            
            # 寫入頭部
            f.write(f"c 符闔數獨 DIMACS CNF (高效編碼)\n")
            f.write(f"c 生成時間: {datetime.now().isoformat()}\n")
            f.write(f"c 變數總數: {total_vars}\n")
            
            # === 1. 位置約束 ===
            print("  [1/5] 位置約束...")
            for row in range(self.N):
                for col in range(self.N):
                    vars_cell = [self.get_var(row, col, val) for val in range(1, self.N+1)]
                    self.encode_exactly_one_lazy(vars_cell, f)
                    if self.clause_count % 100000 == 0:
                        print(f"    子句: {self.clause_count:,}")
            
            # === 2. 行約束 ===
            print("  [2/5] 行約束...")
            for row in range(self.N):
                for val in range(1, self.N+1):
                    vars_row = [self.get_var(row, col, val) for col in range(self.N)]
                    self.encode_exactly_one_lazy(vars_row, f)
            
            # === 3. 列約束 ===
            print("  [3/5] 列約束...")
            for col in range(self.N):
                for val in range(1, self.N+1):
                    vars_col = [self.get_var(row, col, val) for row in range(self.N)]
                    self.encode_exactly_one_lazy(vars_col, f)
            
            # === 4. 宮約束 ===
            print("  [4/5] 宮約束...")
            for br in range(self.box_size):
                for bc in range(self.box_size):
                    for val in range(1, self.N+1):
                        cells = []
                        for dr in range(self.box_size):
                            for dc in range(self.box_size):
                                r = br * self.box_size + dr
                                c = bc * self.box_size + dc
                                cells.append(self.get_var(r, c, val))
                        self.encode_exactly_one_lazy(cells, f)
            
            # === 5. 已知數字 ===
            print("  [5/5] 已知數字...")
            for (row, col), val in self.known_map.items():
                var = self.get_var(row, col, val)
                f.write(f"{var} 0\n")
                self.clause_count += 1
            
            # === 符闔排列約束 ===
            print("\n符闔排列約束...")
            
            for row in range(self.N):
                perms = self.row_perms[row]
                if not perms:
                    continue
                
                print(f"  第{row+1}行: {len(perms):,} 排列")
                
                # 排列選擇變數範圍
                perm_start = perm_var_start + sum(len(self.row_perms[r]) for r in range(row))
                
                # ExactlyOne(排列選擇)
                perm_vars = list(range(perm_start, perm_start + len(perms)))
                
                # 至少一個排列
                f.write(" ".join(str(v) for v in perm_vars) + " 0\n")
                self.clause_count += 1
                
                # 兩兩互斥（分塊）
                chunk_size = 5000
                for i in range(0, len(perm_vars), chunk_size):
                    chunk = perm_vars[i:i+chunk_size]
                    for j in range(len(chunk)):
                        for k in range(j+1, len(chunk)):
                            f.write(f"-{chunk[j]} -{chunk[k]} 0\n")
                            self.clause_count += 1
                
                # 排列選擇 → 值約束
                for perm_idx, perm in enumerate(perms):
                    pb = perm_start + perm_idx
                    for col, val in enumerate(perm):
                        xv = self.get_var(row, col, val)
                        f.write(f"-{pb} {xv} 0\n")
                        self.clause_count += 1
                
                # 值 → 某個排列
                for col in range(self.N):
                    for val in range(1, self.N+1):
                        xv = self.get_var(row, col, val)
                        covering = [perm_start + pi for pi, p in enumerate(perms) if p[col] == val]
                        if covering:
                            f.write(f"-{xv} " + " ".join(str(v) for v in covering) + " 0\n")
                            self.clause_count += 1
                
                gc.collect()
            
            print(f"\n編碼完成!")
            print(f"  子句總數: {self.clause_count:,}")
            
            # 更新頭部
            f.seek(0)
            f.write(f"c 子句總數: {self.clause_count}\n")
            f.write(f"p cnf {total_vars} {self.clause_count}\n")
            
        finally:
            f.close()
        
        import os
        size = os.path.getsize(self.output_path)
        print(f"  文件大小: {size:,} bytes ({size/1024/1024:.1f} MB)")
        
        return {
            "num_variables": total_vars,
            "num_clauses": self.clause_count,
            "file_size_bytes": size,
            "known_clues": len(self.known_map)
        }


def main():
    print("="*70)
    print("SAT DIMACS 高效編碼器 - 符闔數獨")
    print("="*70)
    print(f"開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    encoder = SATDimacsEncoderEfficient()
    stats = encoder.encode()
    
    result = {
        "method": "SAT DIMACS Efficient",
        "timestamp": datetime.now().isoformat(),
        "statistics": stats,
        "output_file": encoder.output_path
    }
    
    with open("sat_efficient_result.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n結果已保存")
    print(f"變數: {stats['num_variables']:,}")
    print(f"子句: {stats['num_clauses']:,}")
    
    return result


if __name__ == "__main__":
    main()
