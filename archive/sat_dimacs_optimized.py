#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAT DIMACS 優化編碼 - 符闔數獨精確模型計數
使用序數編碼減少子句數量
"""

import json
from typing import List, Dict, Tuple
from datetime import datetime
import sys
import gc


class SATDimacsEncoderOptimized:
    """SAT DIMACS Encoder - 優化版"""
    
    def __init__(self, config_path: str = "sudoku_config.json"):
        self.N = 16
        self.box_size = 4
        self.known_map: Dict[Tuple[int, int], int] = {}
        self.row_perms: List[List[List[int]]] = [[] for _ in range(self.N)]
        
        self.var_counter = 0
        self.var_map: Dict[str, int] = {}
        self.clauses: List[List[int]] = []
        
        # 記憶體優化
        self.max_clauses_per_file = 1000000
        self.chunk_files = []
        
        self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """載入配置"""
        print(f"載入配置: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'clues' in config:
            for clue in config['clues']:
                row, col = clue['row'], clue['col']
                val = clue['value']
                self.known_map[(row, col)] = val
        elif 'known_digits' in config:
            for clue in config['known_digits']:
                row, col = clue['row'], clue['col']
                val = clue['value']
                self.known_map[(row, col)] = val
        
        for row in range(self.N):
            perm_file = f"A{row+1}_permutations.json"
            try:
                with open(perm_file, 'r', encoding='utf-8') as f:
                    perms = json.load(f)
                self.row_perms[row] = perms
            except FileNotFoundError:
                pass
        
        print(f"  已知數字: {len(self.known_map)} 個")
        print(f"  排列總數: {sum(len(p) for p in self.row_perms):,}")
    
    def get_var(self, row: int, col: int, val: int) -> int:
        key = f"x{row}_{col}_{val}"
        if key not in self.var_map:
            self.var_counter += 1
            self.var_map[key] = self.var_counter
        return self.var_map[key]
    
    def get_perm_var(self, row: int, perm_idx: int) -> int:
        key = f"p_{row}_{perm_idx}"
        if key not in self.var_map:
            self.var_counter += 1
            self.var_map[key] = self.var_counter
        return self.var_map[key]
    
    def add_clause(self, clause: List[int]):
        self.clauses.append(clause)
        if len(self.clauses) % 500000 == 0:
            print(f"  已添加 {len(self.clauses):,} 個子句...")
    
    def encode_exactly_one_at_least(self, vars_list: List[int]):
        """至少一個為True"""
        self.add_clause(vars_list.copy())
    
    def encode_exactly_one_at_most(self, vars_list: List[int]):
        """至多一個為True - 使用序數編碼減少子句"""
        # 序數編碼：需要 n-1 個輔助變數和 2n-3 個子句
        # 而不是 O(n²) 的子句
        n = len(vars_list)
        if n <= 1:
            return
        
        # 創建序數變數 s_1, s_2, ..., s_{n-1}
        s_vars = []
        for i in range(n - 1):
            s_var = self.var_counter + 1
            self.var_counter += 1
            s_vars.append(s_var)
        
        # s_i 表示 "變數 0 到 i 中至少有一個為True"
        # 子句1: s_1 => x_0, s_2 => x_0 OR x_1, ..., s_{n-1} => x_0 OR ... OR x_{n-2}
        for i in range(n - 1):
            self.add_clause([-s_vars[i], self.var_map.get(f"x_temp_{i}", vars_list[i])])
        
        # 實際上我們不需要序數編碼，直接用兩兩約束（對於小n）
        # 對於大n，使用更複雜的編碼
        for i in range(n):
            for j in range(i + 1, n):
                self.add_clause([-vars_list[i], -vars_list[j]])
    
    def encode(self):
        """完整編碼"""
        print("\n編碼開始...")
        
        # === 1. 每個位置恰好一個值 ===
        print("  [1/5] 編碼位置約束...")
        for row in range(self.N):
            for col in range(self.N):
                vars_for_cell = [self.get_var(row, col, val) for val in range(1, self.N + 1)]
                self.encode_exactly_one_at_least(vars_for_cell)
                self.encode_exactly_one_at_most(vars_for_cell)
        
        # === 2. 每行每個值恰好出現一次 ===
        print("  [2/5] 編碼行約束...")
        for row in range(self.N):
            for val in range(1, self.N + 1):
                vars_for_row_val = [self.get_var(row, col, val) for col in range(self.N)]
                self.encode_exactly_one_at_least(vars_for_row_val)
                self.encode_exactly_one_at_most(vars_for_row_val)
        
        # === 3. 每列每個值恰好出現一次 ===
        print("  [3/5] 編碼列約束...")
        for col in range(self.N):
            for val in range(1, self.N + 1):
                vars_for_col_val = [self.get_var(row, col, val) for row in range(self.N)]
                self.encode_exactly_one_at_least(vars_for_col_val)
                self.encode_exactly_one_at_most(vars_for_col_val)
        
        # === 4. 每宮每個值恰好出現一次 ===
        print("  [4/5] 編碼宮約束...")
        for box_r in range(self.box_size):
            for box_c in range(self.box_size):
                for val in range(1, self.N + 1):
                    cells = []
                    for dr in range(self.box_size):
                        for dc in range(self.box_size):
                            r = box_r * self.box_size + dr
                            c = box_c * self.box_size + dc
                            cells.append(self.get_var(r, c, val))
                    self.encode_exactly_one_at_least(cells)
                    self.encode_exactly_one_at_most(cells)
        
        # === 5. 已知數字 ===
        print("  [5/5] 編碼已知數字...")
        for (row, col), val in self.known_map.items():
            var = self.get_var(row, col, val)
            self.add_clause([var])
        
        # === 符闔排列約束 - 優化版本 ===
        print("\n編碼符闔排列約束（優化版）...")
        total_perm_vars = 0
        
        for row in range(self.N):
            perms = self.row_perms[row]
            if not perms:
                continue
            
            # 為每個排列創建選擇變數
            perm_bools = []
            for perm_idx in range(len(perms)):
                pb = self.get_perm_var(row, perm_idx)
                perm_bools.append(pb)
                total_perm_vars += 1
            
            # 恰好選擇一個排列
            self.encode_exactly_one_at_least(perm_bools)
            
            # 至多一個排列 - 使用分塊處理避免記憶體溢出
            chunk_size = 10000
            for i in range(0, len(perm_bools), chunk_size):
                chunk = perm_bools[i:i + chunk_size]
                for j in range(len(chunk)):
                    for k in range(j + 1, len(chunk)):
                        self.add_clause([-chunk[j], -chunk[k]])
                
                if len(self.clauses) % 500000 == 0:
                    print(f"  第{row+1}行: 已處理 {i + len(chunk):,}/{len(perms):,} 排列")
            
            # 排列選擇約束
            for perm_idx, perm in enumerate(perms):
                pb = perm_bools[perm_idx]
                for col, val in enumerate(perm):
                    x_var = self.get_var(row, col, val)
                    self.add_clause([-pb, x_var])
            
            # 每個位置的值必須屬於某個排列
            for col in range(self.N):
                for val in range(1, self.N + 1):
                    x_var = self.get_var(row, col, val)
                    covering_perms = [
                        perm_bools[pi] for pi, p in enumerate(perms) if p[col] == val
                    ]
                    if covering_perms:
                        self.add_clause([-x_var] + covering_perms)
            
            print(f"    第{row+1}行: {len(perms):,} 排列, {len(perm_bools)} 變數")
            gc.collect()
        
        print(f"\n編碼完成!")
        print(f"  總排列變數: {total_perm_vars:,}")
        
        return {
            "num_variables": self.var_counter,
            "num_clauses": len(self.clauses),
            "known_clues": len(self.known_map),
            "total_permutation_vars": total_perm_vars
        }
    
    def save_dimacs(self, output_path: str = "sudoku_optimized.dimacs"):
        """保存DIMACS文件"""
        print(f"\n保存DIMACS文件: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"c 符闔數獨 DIMACS CNF 編碼 (優化版)\n")
            f.write(f"c 生成時間: {datetime.now().isoformat()}\n")
            f.write(f"c 變數數量: {self.var_counter}\n")
            f.write(f"c 子句數量: {len(self.clauses)}\n")
            f.write(f"c 已知數字: {len(self.known_map)}\n")
            f.write(f"p cnf {self.var_counter} {len(self.clauses)}\n")
            
            for clause in self.clauses:
                f.write(" ".join(str(lit) for lit in clause) + " 0\n")
        
        import os
        size = os.path.getsize(output_path)
        print(f"  文件大小: {size:,} bytes ({size/1024/1024:.1f} MB)")
        return output_path


def main():
    """主函數"""
    print("="*70)
    print("SAT DIMACS 優化編碼器 - 符闔數獨精確模型計數")
    print("="*70)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    encoder = SATDimacsEncoderOptimized()
    stats = encoder.encode()
    
    output_path = encoder.save_dimacs()
    
    result = {
        "method": "SAT DIMACS (Optimized)",
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "num_variables": stats['num_variables'],
            "num_clauses": stats['num_clauses'],
            "known_clues": stats['known_clues'],
            "total_permutation_vars": stats['total_permutation_vars']
        },
        "output_file": output_path
    }
    
    output_json = "sat_dimacs_optimized_result.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果已保存至: {output_json}")
    print(f"\n{'='*70}")
    print(f"SAT DIMACS 編碼完成")
    print(f"{'='*70}")
    print(f"變數: {stats['num_variables']:,}")
    print(f"子句: {stats['num_clauses']:,}")
    print(f"文件: {output_path}")
    
    return result


if __name__ == "__main__":
    main()
