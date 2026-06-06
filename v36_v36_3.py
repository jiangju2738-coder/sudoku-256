#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量化多解空间采样排列生成算法 V36.3 (最终修复版)
"""

import json, time, hashlib, random
from collections import defaultdict, Counter
from typing import List, Dict
from datetime import datetime
from ortools.sat.python import cp_model

GRID_SIZE = 16
BOX_SIZE = 4
SEQUENCE = [7, 15, 3, 9]

def load_anchors_from_config(config_file='sudoku_config.json'):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['known_digits']

class IncrementalCPSATSampler:
    def __init__(self, anchors: List[Dict]):
        self.anchors = anchors
        self.anchors_set = {(a['row']-1, a['col']-1): a['value'] for a in anchors}
        self.non_anchor_cells = [(r,c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                                  if (r,c) not in self.anchors_set]
        self.solutions = []
        self.solution_hashes = set()
        self.x = {}
        
    def _build_model(self):
        model = cp_model.CpModel()
        self.x = {}
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                key = (r, c)
                if key in self.anchors_set:
                    self.x[key] = model.NewConstant(self.anchors_set[key])
                else:
                    self.x[key] = model.NewIntVar(1, GRID_SIZE, f'x_{r}_{c}')
        for r in range(GRID_SIZE):
            model.AddAllDifferent([self.x[(r,c)] for c in range(GRID_SIZE)])
        for c in range(GRID_SIZE):
            model.AddAllDifferent([self.x[(r,c)] for r in range(GRID_SIZE)])
        for br in range(4):
            for bc in range(4):
                box = [self.x[(br*4+dr, bc*4+dc)] for dr in range(4) for dc in range(4)]
                model.AddAllDifferent(box)
        return model

    def _extract_solution(self, solver):
        grid = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
        for (r,c), v in self.anchors_set.items():
            grid[r][c] = v
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if (r,c) not in self.anchors_set:
                    grid[r][c] = solver.Value(self.x[(r,c)])
        return grid
    
    def _get_hash(self, grid):
        flat = tuple(tuple(row) for row in grid)
        return hashlib.sha256(json.dumps(flat).encode()).hexdigest()[:20]
    
    def _hamming(self, g1, g2):
        return sum(1 for r in range(GRID_SIZE) for c in range(GRID_SIZE) if g1[r][c]!=g2[r][c])
    
    def _is_dup(self, grid):
        h = self._get_hash(grid)
        if h in self.solution_hashes: return True
        for sol in self.solutions:
            if self._hamming(grid, sol) < 1: return True
        return False
    
    def _add_anti(self, model, ref_sol, n):
        avail = [p for p in self.non_anchor_cells]
        selected = random.sample(avail, min(n, len(avail)))
        for (r,c) in selected:
            model.Add(self.x[(r,c)] != ref_sol[r][c])
        return selected
    
    def collect(self, target=100, t_per_sol=45.0, t_total=600.0):
        t0 = time.time()
        print('  [Phase 1] 基础解搜索...')
        model = self._build_model()
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = t_per_sol
        s.parameters.num_search_workers = 8
        s.parameters.log_search_progress = True
        st = s.Solve(model)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f'  WARN: 无基础解 (Status={st})')
            return []
        sol1 = self._extract_solution(s)
        self.solutions.append(sol1)
        self.solution_hashes.add(self._get_hash(sol1))
        print(f'  OK: 第1解 ({time.time()-t0:.1f}s)')
        
        for i in range(2, target+1):
            elapsed = time.time()-t0
            if elapsed > t_total:
                print(f'  TIMEOUT: {elapsed:.0f}s')
                break
            if i%5==0: print(f'  PROGRESS: {len(self.solutions)} sols')
            
            ref = random.choice(self.solutions)
            n = 3 if len(self.solutions)<=10 else (5 if len(self.solutions)<=50 else 8)
            
            model = self._build_model()
            self._add_anti(model, ref, n)
            s = cp_model.CpSolver()
            s.parameters.max_time_in_seconds = min(t_per_sol, t_total-elapsed)
            s.parameters.num_search_workers = 8
            s.parameters.log_search_progress = False
            st = s.Solve(model)
            if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                ns = self._extract_solution(s)
                if not self._is_dup(ns):
                    self.solutions.append(ns)
                    self.solution_hashes.add(self._get_hash(ns))
                    print(f'  OK: 第{len(self.solutions)}解')
                else:
                    print(f'  DUP: 第{i}次重复')
            else:
                print(f'  FAIL: 第{i}次无解/超时')
        return self.solutions
    
    def divergence_points(self):
        if len(self.solutions)<2: return []
        ent = defaultdict(float)
        for (r,c) in self.non_anchor_cells:
            vals = [sol[r][c] for sol in self.solutions]
            ent[(r,c)] = len(set(vals))/16.0
        sp = sorted(ent.items(), key=lambda x:-x[1])[:20]
        return [{'pos':f'({r},{c})','entropy':round(e,4),'vals':sorted(set(sol[r][c] for sol in self.solutions))[:8]} 
                for (r,c),e in sp]

def run(anchors, target=100, outfile='v36_v36_3_result.json'):
    print('='*60)
    print('  增量化多解空间采样排列生成算法 V36.3 (最终修复版)')
    print('='*60)
    print(f'  锚点: {len(anchors)} | 目标: {target} | 网格: {GRID_SIZE}x{GRID_SIZE}')
    
    t0 = time.time()
    sam = IncrementalCPSATSampler(anchors)
    sols = sam.collect(target=target, t_per_sol=45.0, t_total=600.0)
    t_tot = time.time()-t0
    div = sam.divergence_points()
    
    res = {'meta':{'ver':'V36.3','time':datetime.now().isoformat(),'anchors':len(anchors),'target':target},
           'sum':{'sols':len(sols),'time_s':round(t_tot,2),'eff':round(len(sols)/max(0.1,t_tot)*60,2)},
           'divergence':div[:10], 'solutions':[]}
    for i,s in enumerate(sols):
        hh = sam._get_hash(s)
        rh = [hashlib.md5(str(tuple(s[r])).encode()).hexdigest()[:6] for r in range(GRID_SIZE)]
        hm = sam._hamming(s, sols[i-1]) if i>0 else None
        res['solutions'].append({'id':i+1,'hash':hh,'row_feat':rh,'hamming':hm})
    
    eff = res['sum']['eff']
    print(f'  总耗时: {t_tot:.1f}s | 解数: {len(sols)} | 效率: {eff:.1f}/min')
    if div:
        print('  分叉点:')
        for d in div[:3]:
            print(f'    {d["pos"]} (熵={d["entropy"]})')
    
    with open(outfile,'w') as f: json.dump(res, f, indent=2)
    print(f'  Saved: {outfile}')
    return res

if __name__=='__main__':
    a = load_anchors_from_config()
    rc = Counter(x['row'] for x in a)
    print(f'加载 {len(a)} 锚点 | C行:{rc.get(3,0)} D行:{rc.get(4,0)}')
    run(a, target=100)
