#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V77 符闔數獨基因指紋100D 深度提取系統
======================================

融闔三大架構：
1. 综闔博弈框架 - 博弈参与者、约束强度分析
2. 五维思维框架 - 点线面体球时空六维分析
3. 链式环式原理 - 行/列/宫约束传播分析

基因维度100D：
- D1-D25：单元格特征（每行）
- D26-D50：行特征
- D51-D75：列特征
- D76-D100：宫特征与全局特征

项目对象：
- 初始盘 (92锚点) + 終局盤
- 演进加E盘 (105锚点) + E解盘
- 演进加I盘 (101锚点) + I解盘
- 演进算盘 (V74) + V74解盘

共8个盘进行基因提取
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import numpy as np
from typing import Dict, List, Tuple, Any
from datetime import datetime
from collections import Counter

# ============================================================
# 第一部分：8个盘数据加载
# ============================================================

def load_all_discs() -> Dict[str, Dict]:
    """加载所有8个盘数据"""
    discs = {}
    
    # 1. 初始盘 (92锚点谜题)
    discs['initial_puzzle'] = {
        'name': '初始盘（92锚点）',
        'type': 'puzzle',
        'anchors': 92,
        'data': load_txt_puzzle('超級大數獨_box_size4.txt', 'known')
    }
    
    # 2. 終局盤 (txt终局解盘)
    discs['final_solution'] = {
        'name': '終局盤（txt终局解盘）',
        'type': 'solution',
        'anchors': 113,
        'data': load_txt_puzzle('超級大數獨_box_size4.txt', 'final')
    }
    
    # 3. 演进加E盘谜题 (105锚点)
    with open('V75_evolution_plus_E_solution_105.json', 'r', encoding='utf-8') as f:
        v75_data = json.load(f)
    discs['v75_puzzle'] = {
        'name': '演进加E盘谜题（105锚点）',
        'type': 'puzzle',
        'anchors': 105,
        'data': v75_data['puzzle']
    }
    
    # 4. 演进加E解盘
    discs['v75_solution'] = {
        'name': '演进加E解盘',
        'type': 'solution',
        'anchors': 256,
        'data': convert_solution_to_dict(v75_data['solution'])
    }
    
    # 5. 演进加I盘谜题 (101锚点)
    with open('V76_evolution_plus_I_solution_101.json', 'r', encoding='utf-8') as f:
        v76_data = json.load(f)
    discs['v76_puzzle'] = {
        'name': '演进加I盘谜题（101锚点）',
        'type': 'puzzle',
        'anchors': 101,
        'data': v76_data['puzzle']
    }
    
    # 6. 演进加I解盘
    discs['v76_solution'] = {
        'name': '演进加I解盘',
        'type': 'solution',
        'anchors': 256,
        'data': convert_solution_to_dict(v76_data['solution'])
    }
    
    # 7. V74 演进算盘 (C行锁定)
    with open('V74_evolution_solution.json', 'r', encoding='utf-8') as f:
        v74_data = json.load(f)
    discs['v74_puzzle'] = {
        'name': '演进算盘（C行锁定）',
        'type': 'puzzle',
        'anchors': 108,
        'data': extract_v74_puzzle(v74_data)
    }
    
    # 8. V74 解盘
    discs['v74_solution'] = {
        'name': 'V74解盘',
        'type': 'solution',
        'anchors': 256,
        'data': convert_solution_to_dict(v74_data['solution'])
    }
    
    return discs


def load_txt_puzzle(filepath: str, variant: str) -> Dict[str, List[int]]:
    """从txt文件加载谜题/解盘"""
    # 初始盘92锚点
    if variant == 'known':
        return {
            'A': [0,0,3,0, 0,12,0,5, 0,0,0,14, 0,16,0,8],
            'B': [0,12,0,0, 3,0,9,0, 6,0,5,4, 2,0,1,0],
            'C': [0,0,14,0, 0,2,0,8, 0,0,0,0, 0,0,0,0],
            'D': [0,4,0,13, 7,0,1,0, 0,0,0,11, 0,12,0,0],
            'E': [0,0,0,0, 13,0,0,0, 0,5,0,0, 4,0,0,0],
            'F': [0,8,0,0, 15,0,4,3, 0,9,0,0, 0,13,0,12],
            'G': [14,0,4,6, 0,0,12,0, 2,0,0,0, 0,3,0,0],
            'H': [0,13,0,0, 0,5,0,9, 0,0,14,6, 0,0,16,0],
            'I': [13,0,0,2, 0,11,0,0, 14,0,0,7, 0,15,0,3],
            'J': [0,5,0,0, 0,0,0,0, 0,0,16,0, 8,0,7,0],
            'K': [1,0,6,0, 5,0,0,2, 0,3,0,0, 9,0,0,0],
            'L': [0,0,0,4, 0,16,14,0, 0,0,12,5, 0,0,0,1],
            'M': [15,0,0,0, 12,0,0,0, 5,1,0,3, 0,6,0,7],
            'N': [0,0,9,0, 0,6,0,0, 13,0,0,15, 0,0,3,0],
            'O': [0,1,0,0, 9,0,0,15, 0,0,2,8, 0,5,0,0],
            'P': [0,0,2,0, 0,0,5,0, 0,14,0,0, 1,0,10,15]
        }
    # 終局盤
    elif variant == 'final':
        return {
            'A': [2,6,3,1, 11,12,13,5, 10,7,9,14, 15,16,4,8],
            'B': [16,12,11,8, 3,10,9,14, 6,15,5,4, 2,7,1,13],
            'C': [7,10,14,15, 4,2,16,8, 12,13,3,1, 11,9,6,5],
            'D': [9,4,5,13, 7,15,1,6, 16,2,8,11, 3,12,14,10],
            'E': [11,2,1,9, 13,7,6,16, 3,5,15,12, 4,10,8,14],
            'F': [5,8,7,10, 15,14,4,3, 1,9,11,16, 6,13,2,12],
            'G': [14,16,4,6, 8,1,12,11, 2,10,7,13, 5,3,15,9],
            'H': [12,13,15,3, 2,5,10,9, 4,8,14,6, 7,1,16,11],
            'I': [13,9,16,2, 6,11,8,12, 14,4,1,7, 10,15,5,3],
            'J': [10,5,12,14, 1,9,3,13, 15,11,16,2, 8,4,7,6],
            'K': [1,11,6,7, 5,4,15,2, 8,3,13,10, 9,14,12,16],
            'L': [3,15,8,4, 10,16,14,7, 9,6,12,5, 13,2,11,1],
            'M': [15,14,13,11, 12,8,2,10, 5,1,4,3, 16,6,9,7],
            'N': [4,7,9,5, 14,6,11,1, 13,16,10,15, 12,8,3,2],
            'O': [6,1,10,16, 9,3,7,15, 11,12,2,8, 14,5,13,4],
            'P': [8,3,2,12, 16,13,5,4, 7,14,6,9, 1,11,10,15]
        }
    return {}


def convert_solution_to_dict(solution: List[List[int]]) -> Dict[str, List[int]]:
    """将解盘列表转换为字典格式"""
    result = {}
    for i, row in enumerate('ABCDEFGHIJKLMNOP'):
        result[row] = solution[i]
    return result


def extract_v74_puzzle(v74_data: Dict) -> Dict[str, List[int]]:
    """提取V74演进算盘谜题"""
    # V74是C行完整锁定的演进算盘
    solution = convert_solution_to_dict(v74_data['solution'])
    c_row = solution['C']
    
    # 从解中提取C行+初始锚点构成谜题
    return {
        'A': [0,0,3,0, 11,12,0,5, 0,0,0,14, 0,16,0,8],
        'B': [0,12,0,0, 3,0,9,0, 6,0,5,4, 2,0,1,0],
        'C': c_row,  # C行完整锁定
        'D': [0,4,0,13, 7,0,1,0, 0,0,0,11, 0,12,0,0],
        'E': [0,0,0,0, 13,0,0,0, 0,5,0,0, 4,0,0,0],
        'F': [0,8,0,0, 15,0,4,3, 0,9,0,0, 0,13,0,12],
        'G': [14,0,4,6, 8,0,12,0, 2,0,0,0, 0,3,0,0],
        'H': [0,13,0,0, 2,5,0,9, 0,0,14,6, 0,0,16,0],
        'I': [13,0,0,2, 6,11,0,0, 14,0,0,7, 0,15,0,3],
        'J': [0,5,0,0, 1,0,0,0, 0,0,16,0, 8,0,7,0],
        'K': [1,0,6,0, 5,0,0,2, 0,3,0,0, 9,0,0,0],
        'L': [0,0,0,4, 10,16,14,0, 0,0,12,5, 0,0,0,1],
        'M': [15,0,0,0, 12,0,0,0, 5,1,0,3, 0,6,0,7],
        'N': [0,0,9,0, 14,6,0,0, 13,0,0,15, 0,0,3,0],
        'O': [0,1,0,0, 9,0,0,15, 0,0,2,8, 0,5,0,0],
        'P': [0,0,2,0, 16,0,5,0, 0,14,0,0, 1,0,10,15]
    }


# ============================================================
# 第二部分：100D基因指纹提取
# ============================================================

class GeneFingerprintExtractor:
    """100D基因指纹提取器"""
    
    ROWS = 'ABCDEFGHIJKLMNOP'
    
    def __init__(self, data: Dict[str, List[int]]):
        self.data = data
        self.grid = np.array([data[row] for row in self.ROWS])
        
    def extract_all_genes(self) -> Dict[str, Any]:
        """提取全部100D基因"""
        return {
            # D1-D25: 行特征基因
            **self._extract_row_genes(),
            # D26-D50: 列特征基因
            **self._extract_col_genes(),
            # D51-D75: 宫特征基因
            **self._extract_palace_genes(),
            # D76-D100: 全局特征基因
            **self._extract_global_genes()
        }
    
    def _extract_row_genes(self) -> Dict[str, Any]:
        """提取行特征基因 (D1-D16, D17-D25)"""
        genes = {}
        
        # D1-D16: 每行锚点数（已知数密度）
        for i, row in enumerate(self.ROWS):
            genes[f'D{i+1}'] = {
                'name': f'行{row}_锚点密度',
                'value': sum(1 for v in self.data[row] if v != 0),
                'type': 'anchor_density'
            }
        
        # D17-D25: 行排列复杂度指标
        for i, row in enumerate(self.ROWS):
            known = [v for v in self.data[row] if v != 0]
            genes[f'D{i+17}'] = {
                'name': f'行{row}_排列复杂度',
                'value': self._calc_permutation_complexity(known),
                'type': 'complexity'
            }
        
        return genes
    
    def _extract_col_genes(self) -> Dict[str, Any]:
        """提取列特征基因 (D26-D41, D42-D50)"""
        genes = {}
        
        # D26-D41: 每列锚点数
        for i in range(16):
            col_vals = [self.data[row][i] for row in self.ROWS]
            genes[f'D{i+26}'] = {
                'name': f'列{chr(64+i+1)}_锚点密度',
                'value': sum(1 for v in col_vals if v != 0),
                'type': 'anchor_density'
            }
        
        # D42-D50: 列值分布熵
        for i in range(16):
            col_vals = [self.data[row][i] for row in self.ROWS]
            genes[f'D{i+42}'] = {
                'name': f'列{chr(64+i+1)}_值分布熵',
                'value': self._calc_entropy([v for v in col_vals if v != 0]),
                'type': 'entropy'
            }
        
        return genes
    
    def _extract_palace_genes(self) -> Dict[str, Any]:
        """提取宫特征基因 (D51-D66, D67-D75)"""
        genes = {}
        
        # D51-D66: 每宫锚点数
        for p_row in range(4):
            for p_col in range(4):
                palace_id = p_row * 4 + p_col
                cells = []
                for r in range(4):
                    for c in range(4):
                        cells.append(self.data[self.ROWS[p_row*4 + r]][p_col*4 + c])
                genes[f'D{51+palace_id}'] = {
                    'name': f'宫{palace_id+1}_锚点密度',
                    'value': sum(1 for v in cells if v != 0),
                    'type': 'anchor_density'
                }
        
        # D67-D75: 宫值分布特征
        for p_row in range(4):
            for p_col in range(4):
                palace_id = p_row * 4 + p_col
                cells = []
                for r in range(4):
                    for c in range(4):
                        cells.append(self.data[self.ROWS[p_row*4 + r]][p_col*4 + c])
                genes[f'D{67+palace_id}'] = {
                    'name': f'宫{palace_id+1}_值集中度',
                    'value': self._calc_value_concentration(cells),
                    'type': 'concentration'
                }
        # D75: 宫间关联度
        genes['D75'] = {
            'name': '宫间关联度',
            'value': self._calc_palace_correlation(),
            'type': 'correlation'
        }
        
        return genes
    
    def _extract_global_genes(self) -> Dict[str, Any]:
        """提取全局特征基因 (D76-D100)"""
        genes = {}
        
        # D76-D80: 整体锚点统计
        total_anchors = sum(sum(1 for v in row if v != 0) for row in self.data.values())
        genes['D76'] = {'name': '总锚点数', 'value': total_anchors, 'type': 'count'}
        genes['D77'] = {'name': '空单元格数', 'value': 256 - total_anchors, 'type': 'count'}
        genes['D78'] = {'name': '锚点填充率', 'value': round(total_anchors/256*100, 2), 'type': 'rate'}
        genes['D79'] = {'name': '平均每行锚点', 'value': round(total_anchors/16, 2), 'type': 'avg'}
        genes['D80'] = {'name': '平均每列锚点', 'value': round(total_anchors/16, 2), 'type': 'avg'}
        
        # D81-D90: 行约束强度方差
        row_anchors = [sum(1 for v in row if v != 0) for row in self.data.values()]
        genes['D81'] = {'name': '行锚点方差', 'value': round(np.var(row_anchors), 4), 'type': 'variance'}
        genes['D82'] = {'name': '行锚点标准差', 'value': round(np.std(row_anchors), 4), 'type': 'std'}
        genes['D83'] = {'name': '行锚点极差', 'value': max(row_anchors) - min(row_anchors), 'type': 'range'}
        genes['D84'] = {'name': '最大锚点行', 'value': self.ROWS[np.argmax(row_anchors)], 'type': 'extreme'}
        genes['D85'] = {'name': '最小锚点行', 'value': self.ROWS[np.argmin(row_anchors)], 'type': 'extreme'}
        
        # D86-D90: 数字分布特征
        all_vals = [v for row in self.data.values() for v in row if v != 0]
        val_counter = Counter(all_vals)
        genes['D86'] = {'name': '数字1频次', 'value': val_counter.get(1, 0), 'type': 'frequency'}
        genes['D87'] = {'name': '数字8频次', 'value': val_counter.get(8, 0), 'type': 'frequency'}
        genes['D88'] = {'name': '数字16频次', 'value': val_counter.get(16, 0), 'type': 'frequency'}
        genes['D89'] = {'name': '数字分布均匀度', 'value': round(1 - np.var(list(val_counter.values()))/100, 4), 'type': 'uniformity'}
        genes['D90'] = {'name': '解空间收敛度', 'value': self._calc_convergence(), 'type': 'convergence'}
        
        # D91-D100: 三大架构综合指标
        genes['D91'] = {'name': '综闔博弈均衡度', 'value': self._calc_zhonghe_balance(), 'type': 'framework'}
        genes['D92'] = {'name': '五维点维度密度', 'value': genes['D78']['value'], 'type': 'framework'}
        genes['D93'] = {'name': '五维线维度锁定率', 'value': round(sum(1 for r in row_anchors if r==16)/16*100, 2), 'type': 'framework'}
        genes['D94'] = {'name': '五维体维度平均列约束', 'value': round(np.mean([sum(1 for v in [self.data[r][c] for r in self.ROWS] if v!=0) for c in range(16)])/16*100, 2), 'type': 'framework'}
        genes['D95'] = {'name': '链式传递链数', 'value': self._calc_chain_count(), 'type': 'chain'}
        genes['D96'] = {'name': '环式闭环完整度', 'value': self._calc_loop_completeness(), 'type': 'loop'}
        genes['D97'] = {'name': '时空演进阶段', 'value': self._calc_spacetime_stage(total_anchors), 'type': 'spacetime'}
        genes['D98'] = {'name': '基因指纹唯一性', 'value': self._calc_gene_uniqueness(), 'type': 'uniqueness'}
        genes['D99'] = {'name': '符闔排列匹配度', 'value': self._calc_permutation_match(), 'type': 'permutation'}
        genes['D100'] = {'name': '综合基因评分', 'value': self._calc_overall_score(), 'type': 'overall'}
        
        return genes
    
    def _calc_permutation_complexity(self, known_vals: List[int]) -> float:
        """计算排列复杂度"""
        if len(known_vals) <= 1:
            return 0.0
        diffs = [abs(known_vals[i] - known_vals[i+1]) for i in range(len(known_vals)-1)]
        return round(np.std(diffs) / np.mean(diffs) if np.mean(diffs) > 0 else 0, 4)
    
    def _calc_entropy(self, vals: List[int]) -> float:
        """计算熵"""
        if not vals:
            return 0.0
        counter = Counter(vals)
        probs = [c/len(vals) for c in counter.values()]
        return round(-sum(p * np.log2(p) for p in probs if p > 0), 4)
    
    def _calc_value_concentration(self, cells: List[int]) -> float:
        """计算值集中度"""
        known = [v for v in cells if v != 0]
        if not known:
            return 0.0
        counter = Counter(known)
        return round(max(counter.values()) / len(known), 4)
    
    def _calc_palace_correlation(self) -> float:
        """计算宫间关联度"""
        palace_means = []
        for p_row in range(4):
            for p_col in range(4):
                cells = []
                for r in range(4):
                    for c in range(4):
                        cells.append(self.data[self.ROWS[p_row*4 + r]][p_col*4 + c])
                known = [v for v in cells if v != 0]
                palace_means.append(np.mean(known) if known else 0)
        return round(np.std(palace_means) / np.mean(palace_means) if np.mean(palace_means) > 0 else 0, 4)
    
    def _calc_convergence(self) -> float:
        """计算解空间收敛度"""
        total_anchors = sum(sum(1 for v in row if v != 0) for row in self.data.values())
        # 经验公式：锚点越多，解空间越收敛
        return round(min(total_anchors / 150, 1.0) * 100, 2)
    
    def _calc_zhonghe_balance(self) -> float:
        """计算综闔博弈均衡度"""
        row_anchors = [sum(1 for v in row if v != 0) for row in self.data.values()]
        # 均衡度：各行约束的方差倒数
        variance = np.var(row_anchors)
        return round(1 / (1 + variance), 4)
    
    def _calc_chain_count(self) -> int:
        """计算链式传递链数"""
        total_anchors = sum(sum(1 for v in row if v != 0) for row in self.data.values())
        # 每个锚点通过列传递到15个其他行
        return total_anchors * 15
    
    def _calc_loop_completeness(self) -> float:
        """计算环式闭环完整度"""
        # 检查行/列/宫约束是否形成闭环
        row_complete = sum(1 for row in self.data.values() if sum(1 for v in row if v != 0) == 16)
        return round(row_complete / 16, 4)
    
    def _calc_spacetime_stage(self, total_anchors: int) -> str:
        """计算时空演进阶段"""
        if total_anchors <= 92:
            return '初始态'
        elif total_anchors <= 100:
            return '演进态I'
        elif total_anchors <= 110:
            return '演进态II'
        else:
            return '终局态'
    
    def _calc_gene_uniqueness(self) -> float:
        """计算基因指纹唯一性"""
        # 基于锚点分布的唯一性指标
        row_anchors = [sum(1 for v in row if v != 0) for row in self.data.values()]
        unique_pattern = len(set(row_anchors))
        return round(unique_pattern / 16, 4)
    
    def _calc_permutation_match(self) -> float:
        """计算符闔排列匹配度"""
        # 检查每行是否符合符闔排列特征（简化版）
        matches = 0
        for row in self.ROWS:
            vals = [v for v in self.data[row] if v != 0]
            if len(set(vals)) == len(vals):  # 无重复
                matches += 1
        return round(matches / 16, 4)
    
    def _calc_overall_score(self) -> float:
        """计算综合基因评分"""
        total_anchors = sum(sum(1 for v in row if v != 0) for row in self.data.values())
        score = 0
        
        # 锚点完整性 (40%)
        score += min(total_anchors / 160, 1.0) * 40
        
        # 行约束均衡 (30%)
        row_anchors = [sum(1 for v in row if v != 0) for row in self.data.values()]
        balance = 1 / (1 + np.var(row_anchors))
        score += balance * 30
        
        # 符闔排列符合度 (30%)
        match = self._calc_permutation_match()
        score += match * 30
        
        return round(score, 2)


# ============================================================
# 第三部分：三大架构分析
# ============================================================

class ZhongheGameAnalysis:
    """综闔博弈框架分析"""
    
    def __init__(self, discs: Dict):
        self.discs = discs
    
    def analyze(self) -> Dict:
        """综合分析"""
        results = {}
        for name, disc in self.discs.items():
            row_constraints = {}
            for row in 'ABCDEFGHIJKLMNOP':
                known = sum(1 for v in disc['data'][row] if v != 0)
                row_constraints[row] = {
                    'known': known,
                    'constraint_strength': round(known / 16, 4)
                }
            
            # 博弈参与者识别
            players = []
            for row, info in row_constraints.items():
                if info['constraint_strength'] >= 1.0:
                    players.append({'row': row, 'role': '主导者', 'strength': 1.0})
                elif info['constraint_strength'] >= 0.5:
                    players.append({'row': row, 'role': '影响者', 'strength': info['constraint_strength']})
                elif info['constraint_strength'] > 0:
                    players.append({'row': row, 'role': '参与者', 'strength': info['constraint_strength']})
            
            results[name] = {
                'row_constraints': row_constraints,
                'players': players,
                'dominant_rows': [p['row'] for p in players if p['role'] == '主导者'],
                'avg_constraint': round(np.mean([r['constraint_strength'] for r in row_constraints.values()]), 4)
            }
        
        return results


class FiveDimensionalAnalysis:
    """五维思维框架分析"""
    
    def __init__(self, discs: Dict):
        self.discs = discs
    
    def analyze(self) -> Dict:
        results = {}
        for name, disc in self.discs.items():
            data = disc['data']
            
            # 点维度
            total = 256
            filled = sum(sum(1 for v in row if v != 0) for row in data.values())
            point_dim = {
                'total_cells': total,
                'filled_cells': filled,
                'empty_cells': total - filled,
                'fill_rate': round(filled / total * 100, 2)
            }
            
            # 线维度
            line_dim = {}
            for row in 'ABCDEFGHIJKLMNOP':
                known = sum(1 for v in data[row] if v != 0)
                line_dim[row] = {
                    'known': known,
                    'locked': known == 16,
                    'lock_rate': round(known / 16 * 100, 2)
                }
            
            # 面维度（宫）
            plane_dim = {}
            for p_row in range(4):
                for p_col in range(4):
                    palace_id = f"P{p_row*4+p_col+1}"
                    cells = []
                    for r in range(4):
                        for c in range(4):
                            cells.append(data['ABCDEFGHIJKLMNOP'[p_row*4 + r]][p_col*4 + c])
                    filled = sum(1 for v in cells if v != 0)
                    plane_dim[palace_id] = {
                        'filled': filled,
                        'fill_rate': round(filled / 16 * 100, 2)
                    }
            
            # 体维度（列）
            body_dim = {}
            for col in range(16):
                col_vals = [data[row][col] for row in 'ABCDEFGHIJKLMNOP']
                known = sum(1 for v in col_vals if v != 0)
                body_dim[chr(65+col)] = {
                    'known': known,
                    'constraint_strength': round(known / 16 * 100, 2)
                }
            
            # 球维度
            sphere_dim = {
                'anchor_density': round(filled / total * 100, 2),
                'constraint_network': 'complete' if filled >= 100 else 'partial'
            }
            
            # 时空维度
            spacetime_dim = {
                'stage': self._get_stage(filled),
                'evolution_rate': round(filled / 256 * 100, 2)
            }
            
            results[name] = {
                'point': point_dim,
                'line': line_dim,
                'plane': plane_dim,
                'body': body_dim,
                'sphere': sphere_dim,
                'spacetime': spacetime_dim
            }
        
        return results
    
    def _get_stage(self, filled: int) -> str:
        if filled <= 50:
            return '初始态'
        elif filled <= 100:
            return '演进态'
        elif filled <= 200:
            return '收敛态'
        else:
            return '终局态'


class ChainRingAnalysis:
    """链式环式原理分析"""
    
    def __init__(self, discs: Dict):
        self.discs = discs
    
    def analyze(self) -> Dict:
        results = {}
        for name, disc in self.discs.items():
            data = disc['data']
            
            # 分析每对行之间的链式约束
            chain_links = []
            for i, row1 in enumerate('ABCDEFGHIJKLMNOP'):
                for j, row2 in enumerate('ABCDEFGHIJKLMNOP'):
                    if i < j:
                        # 计算两行通过列约束的关联度
                        common_constrained_cols = 0
                        for col in range(16):
                            if data[row1][col] != 0 and data[row2][col] != 0:
                                common_constrained_cols += 1
                        
                        chain_links.append({
                            'rows': f'{row1}-{row2}',
                            'shared_constraints': common_constrained_cols,
                            'chain_strength': round(common_constrained_cols / 16, 4)
                        })
            
            # 环式闭环检测
            loops = self._detect_loops(data)
            
            results[name] = {
                'chain_links': chain_links,
                'total_chain_count': sum(1 for row in data.values() for v in row if v != 0) * 15,
                'loops': loops,
                'loop_completeness': round(len([l for l in loops if l['complete']]) / max(len(loops), 1), 4)
            }
        
        return results
    
    def _detect_loops(self, data: Dict) -> List[Dict]:
        """检测约束环"""
        loops = []
        # 检测行-列-宫闭环
        for row in 'ABCDEFGHIJKLMNOP':
            known_cols = [i for i, v in enumerate(data[row]) if v != 0]
            if len(known_cols) >= 2:
                loops.append({
                    'type': 'row-col-loop',
                    'row': row,
                    'cols': known_cols,
                    'complete': len(known_cols) == 16
                })
        return loops


# ============================================================
# 第四部分：报告生成
# ============================================================

def generate_gene_report(discs: Dict) -> Dict:
    """生成完整的基因提取报告"""
    print("="*70)
    print("V77 符闔數獨基因指紋100D 深度提取")
    print("="*70)
    print()
    
    # 1. 提取每个盘的100D基因指纹
    print("【步骤1】100D基因指纹提取")
    gene_fingerprints = {}
    for name, disc in discs.items():
        print(f"  提取 {disc['name']} 基因...")
        extractor = GeneFingerprintExtractor(disc['data'])
        gene_fingerprints[name] = extractor.extract_all_genes()
    print("  ✓ 完成")
    print()
    
    # 2. 综闔博弈框架分析
    print("【步骤2】综闔博弈框架分析")
    zhonghe = ZhongheGameAnalysis(discs)
    zhonghe_results = zhonghe.analyze()
    for name, result in zhonghe_results.items():
        dominant = result['dominant_rows']
        print(f"  {discs[name]['name']}:")
        print(f"    主导者: {dominant if dominant else '无'}")
        print(f"    平均约束强度: {result['avg_constraint']:.2%}")
    print()
    
    # 3. 五维思维框架分析
    print("【步骤3】五维思维框架分析")
    five_dim = FiveDimensionalAnalysis(discs)
    five_dim_results = five_dim.analyze()
    for name, result in five_dim_results.items():
        print(f"  {discs[name]['name']}:")
        print(f"    点维度填充率: {result['point']['fill_rate']}%")
        print(f"    线维度锁定行: {sum(1 for r in result['line'].values() if r['locked'])}")
        print(f"    时空阶段: {result['spacetime']['stage']}")
    print()
    
    # 4. 链式环式原理分析
    print("【步骤4】链式环式原理分析")
    chain_ring = ChainRingAnalysis(discs)
    chain_ring_results = chain_ring.analyze()
    for name, result in chain_ring_results.items():
        print(f"  {discs[name]['name']}:")
        print(f"    总传递链数: {result['total_chain_count']}")
        print(f"    闭环完整度: {result['loop_completeness']:.2%}")
    print()
    
    # 5. 基因指纹对比
    print("【步骤5】8盘基因指纹对比")
    comparison = compare_gene_fingerprints(gene_fingerprints)
    print(comparison)
    print()
    
    return {
        'gene_fingerprints': gene_fingerprints,
        'zhonghe_analysis': zhonghe_results,
        'five_dim_analysis': five_dim_results,
        'chain_ring_analysis': chain_ring_results,
        'timestamp': datetime.now().isoformat()
    }


def compare_gene_fingerprints(fingerprints: Dict) -> str:
    """对比基因指纹"""
    lines = []
    lines.append("  盘名" + " " * 20 + "总锚点" + " " * 6 + "综合评分" + " " * 8 + "时空阶段")
    lines.append("  " + "-" * 60)
    
    for name, genes in fingerprints.items():
        anchors = genes['D76']['value']
        score = genes['D100']['value']
        stage = genes['D97']['value']
        lines.append(f"  {name[:25]:<25} {anchors:<10} {score:<15} {stage}")
    
    return "\n".join(lines)


# ============================================================
# 主程序
# ============================================================

def main():
    print("="*70)
    print("V77 符闔數獨基因指紋100D 融闔三大架構深度研究")
    print("="*70)
    print()
    
    # 加载8个盘
    print("【步骤0】加载8个盘数据")
    discs = load_all_discs()
    for name, disc in discs.items():
        print(f"  ✓ {disc['name']}: {disc['anchors']} 锚点")
    print()
    
    # 生成完整报告
    report = generate_gene_report(discs)
    
    # 保存报告
    output_file = 'V77_gene_fingerprint_100D_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"✓ 基因报告已保存: {output_file}")
    print()
    
    # 输出基因指纹摘要
    print("="*70)
    print("基因指纹100D 摘要表")
    print("="*70)
    print()
    
    for name, genes in report['gene_fingerprints'].items():
        print(f"【{discs[name]['name']}】")
        print(f"  D76-D80 (锚点统计): {genes['D76']['value']}锚点, 填充率{genes['D78']['value']}%")
        print(f"  D81-D85 (行约束): 方差{genes['D81']['value']}, 极差{genes['D83']['value']}")
        print(f"  D91-D100 (综合指标): 均衡度{genes['D91']['value']}, 评分{genes['D100']['value']}")
        print()
    
    return report


if __name__ == '__main__':
    main()