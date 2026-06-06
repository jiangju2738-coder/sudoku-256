#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务1: 解析txt文件中所有16行的列约束（256个位置约束）
"""

import json
import re
from collections import Counter

# txt文件第150-255行的约束内容（16行 x 16列 = 256个位置）
TXT_CONSTRAINTS = """
第1行：A第一行符阖排列.xlsx；

1：AD = 0 解集 = 2 6 7 9 10 11
2: AE = 0 解集 = 2 6 7 9 10 11 15
3: AF = 3
4: AG = 0 解集 = 1 7 9 10 11 15
5: AH = 0 解集 = 4 6 10 11 14
6: AI = 12
7: AJ = 0 解集 = 6 10 11 13 15
8: AK = 5
9: AL = 0 解集 = 1 7 9 10 12 15
10: AM = 0 解集 = 2 7 10 12 13 15
11: AN = 0 解集 = 1 7 9 10 13 15
12: AO = 14
13: AP = 0 解集 = 6 7 10 11 13 14 15
14: AQ = 16
15: AR = 0 解集 = 4 6 9 11 13 14 15
16: AS = 8

第2行：B第二行符阖排列.xlsx；

17: BD = 0 解集 = 7 8 10 11 16
18: BE = 12
19: BF = 0 解集 = 1 7 8 10 11 15 16
20: BG = 0 解集 = 7 8 10 11 15 16
21: BH = 3
22: BI = 0 解集 = 10 13 14 15
23: BJ = 9
24: BK = 0 解集 = 10 11 13 14 16
25: BL = 6
26: BM = 0 解集 = 7 8 10 13 15 16
27: BN = 5
28: BO = 4
29: BP = 2
30: BQ = 0 解集 = 7 10 11 14
31: BR = 1
32: BS = 0 解集 = 10 11 13 14 15

第3行：C第三行符阖排列.xlsx；

33: CD = 0 解集 = 5 6 7 9 10 11 16
34: CE = 0 解集 = 6 7 9 10 11 15 16
35: CF = 14
36: CG = 0 解集 = 1 5 7 9 10 11 15 16
37: CH = 0 解集 = 4 6 10 11 16
38: CI = 2
39: CJ = 0 解集 = 6 10 11 13 15 16
40: CK = 8
41: CL = 0 解集 = 1 3 7 9 10 12 15 16
42: CM = 0 解集 = 7 10 12 13 15 16
43: CN = 0 解集 = 1 3 7 9 10 13 15
44: CO = 0 解集 = 1 9 10 12 13 16
45: CP = 0 解集 = 3 5 6 7 10 11 13 15
46: CQ = 0 解集 = 4 7 9 10 11
47: CR = 0 解集 = 4 5 6 9 11 13 15
48: CS = 0 解集 = 4 5 6 9 10 11 13 15

第4行：D第四行符阖排列.xlsx；

49: DD = 0 解集 = 2 5 6 8 9 10 16
50: DE = 4
51: DF = 0 解集 = 5 8 10 15 16
52: DG = 13
53: DH = 7
54: DI = 0 解集 = 10 14 15
55: DJ = 1
56: DK = 0 解集 = 6 10 14 16
57: DL = 0 解集 = 3 8 9 10 15 16
58: DM = 0 解集 = 2 8 10 15 16
59: DN = 0 解集 = 3 8 10 15
60: DO = 11
61: DP = 0 解集 = 3 5 6 10 14 15
62: DQ = 12
63: DR = 0 解集 = 5 6 9 14 15
64: DS = 0 解集 = 5 6 9 10 14 15

第5行：E第五行符阖排列.xlsx；

65: ED = 0 解集 = 2 3 7 9 10 11 12 16
66: EE = 0 解集 = 2 3 7 9 10 11 15 16
67: EF = 0 解集 = 1 7 10 11 12 15 16
68: EG = 0 解集 = 1 3 7 9 10 11 12 15 16
69: EH = 13
70: EI = 0 解集 = 1 7 8 10 14
71: EJ = 0 解集 = 2 6 7 8 10 11 16
72: EK = 0 解集 = 1 6 7 10 11 14 16
73: EL = 0 解集 = 1 3 7 8 10 11 12 13 16
74: EM = 5
75: EN = 0 解集 = 1 3 7 8 9 10 11 15
76: EO = 0 解集 = 1 10 12 16
77: EP = 4
78: EQ = 0 解集 = 1 2 7 8 9 10 11 14
79: ER = 0 解集 = 2 6 8 9 11 14 15
80: ES = 0 解集 = 2 6 9 10 11 14 15

第6行：F第六行符阖排列.xlsx；

81: FD = 0 解集 = 2 5 7 10 11 16
82: FE = 8
83: FF = 0 解集 = 1 5 7 10 11 16
84: FG = 0 解集 = 1 5 7 10 11 16
85: FH = 15
86: FI = 0 解集 = 1 7 10 14
87: FJ = 4 
88: FK = 3
89: FL = 0 解集 = 1 7 10 11 16
90: FM = 9
91: FN = 0 解集 = 1 7 10 11
92: FO = 0 解集 = 1 10 16
93: FP = 0 解集 = 5 6 7 10 11 14
94: FQ = 13
95: FR = 0 解集 = 2 5 6 11 14
96: FS = 12

第7行：G第七行符阖排列.xlsx；

97: GD = 14
98: GE = 0 解集 = 7 9 10 11 15 16
99: GF = 4
100: GG = 6
101: GH = 0 解集 = 1 8 10 11 16
102: GI = 0 解集 = 1 7 8 10
103: GJ = 12
104: GK = 0 解集 = 1 7 10 11 16
105: GL = 2
106: GM = 0 解集 = 7 8 10 11 13 15 16
107: GN = 0 解集 = 1 7 8 10 11 13 15
108: GO = 0 解集 = 1 10 13 16
109: GP = 0 解集 = 5 7 10 11 15
110: GQ = 3
111: GR = 0 解集 = 5 8 9 11 15
112: GS = 0 解集 = 5 9 10 11 15

第8行：H第八行符阖排列.xlsx；

113: HD = 0 解集 = 2 3 7 10 11 12
114: HE = 13
115: HF = 0 解集 = 1 7 10 11 12 15
116: HG = 0 解集 = 1 3 7 10 11 12 15
117: HH = 0 解集 = 1 2 8 10 11
118: HI = 5
119: HJ = 0 解集 = 2 7 8 10 11
120: HK = 9 
121: HL = 0 解集 = 1 3 4 7 8 10 11 12 15
122: HM = 0 解集 = 4 7 8 10 11 12 15
123: HN = 14
124: HO = 6
125: HP = 0 解集 = 7 10 11 15
126: HQ = 0 解集 = 1 2 7 8 10 11
127: HR = 16
128: HS = 0 解集 = 2 10 11 15

第9行：I第八行符阖排列.xlsx；

129: ID = 13
130: IE = 0 解集 = 9 10 16
131: IF = 0 解集 = 8 10 12 16
132: IG = 2
133: IH = 0 解集 = 1 4 6 8 10
134: II = 11
135: IJ = 0 解集 = 6 8 10 15
136: IK = 0 解集 = 1 4 6 10 12
137: IL = 14
138: IM = 0 解集 = 4 6 8 10
139: IN = 0 解集 = 1 4 6 8 9 10
140: IO = 7
141: IP = 0 解集 = 5 6 10 16
142: IQ = 15
143: IR = 0 解集 = 4 5 6 12
144: IS = 3

第10行：J第十行符阖排列.xlsx；

145: JD = 0 解集 = 3 9 10 11 12
146: JE = 5
147: JF = 0 解集 = 10 11 12 15
148: JG = 0 解集 = 3 9 10 11 12 14 15
149: JH = 0 解集 = 1 4 6 10
150: JI = 0 解集 = 1 3 4 9 10 12 13 15
151: JJ = 0 解集 = 3 6 10 13 15
152: JK = 0 解集 = 1 4 6 10 12 13
153: JL = 0 解集 = 1 4 9 10 11 15
154: JM = 0 解集 = 2 4 6 10 11 13 15
155: JN = 16
156: JO = 0 解集 = 1 2 9 10 13
157: JP = 8
158: JQ = 0 解集 = 2 4 10 11 14
159: JR = 7
160: JS = 0 解集 = 2 4 6 10 11 13 14

第11行：K第十一行符阖排列.xlsx；

161: KD = 1
162: KE = 0 解集 = 7 10 11 14 15 16
163: KF = 6
164: KG = 0 解集 = 7 8 10 11 12 14 15 16
165: KH = 5
166: KI = 0 解集 = 4 7 8 10 12 13 15
167: KJ = 0 解集 = 7 8 10 13
168: KK = 2
169: KL = 0 解集 = 4 8 10 11 15
170: KM = 3
171: KN = 0 解集 = 4 8 10 11 13 15
172: KO = 0 解集 = 10 13
173: KP = 9
174: KQ = 0 解集 = 4 10 11 14
175: KR = 0 解集 = 4 11 12 13 14
176: KS = 0 解集 = 4 10 11 13 14 16

第12行：L第十二行符阖排列.xlsx；

177: LD = 0 解集 = 3 7 8 9 10 11
178: LE = 0 解集 = 3 7 9 10 11 15
179: LF = 0 解集 = 7 8 10 11 15
180: LG = 4
181: LH = 0 解集 = 6 8 10
182: LI = 16
183: LJ = 14
184: LK = 0 解集 = 6 7 10 13
185: LL = 0 解集 = 8 9 10 11 15
186: LM = 0 解集 = 2 6 8 10 11 13 15
187: LN = 12
188: LO = 5
189: LP = 0 解集 = 6 10 11 13
190: LQ = 0 解集 = 2 10 11
191: LR = 0 解集 = 2 5 6 11 13
192: LS = 1

第13行：M第十三行符阖排列.xlsx；

193: MD = 15
194: ME = 0 解集 = 10 11 14 16
195: MF = 0 解集 = 8 10 11 13 16
196: MG = 0 解集 = 8 10 11 14 16
197: MH = 12
198: MI = 0 解集 = 4 8 10 13 14
199: MJ = 0 解集 = 2 8 10 11 13 16
200: MK = 0 解集 = 4 10 11 13 14 16
201: ML = 5
202: MM = 1
203: MN = 0 解集 = 4 9 10 11
204: MO = 3
205: MP = 0 解集 = 11 13 14 16
206: MQ = 6
207: MR = 0 解集 = 2 4 8 9 11 13 14
208: MS = 7

第14行：N第十四行符阖排列.xlsx；

209: ND = 0 解集 = 4 5 7 8 10 11 12 16
210: NE = 0 解集 = 7 10 11 14 16
211: NF = 9
212: NG = 0 解集 = 5 7 8 10 11 12 14 16
213: NH = 0 解集 = 1 2 4 8 10 11 14 16
214: NI = 6
215: NJ = 0 解集 = 2 7 8 10 11 16
216: NK = 0 解集 = 1 4 7 10 11 14 16
217: NL = 13
218: NM = 0 解集 = 4 7 10 11 12 16
219: NN = 0 解集 = 4 7 10 11
220: NO = 15
221: NP = 0 解集 = 11 12 14 16
222: NQ = 0 解集 = 2 4 8 11 14
223: NR = 3
224: NS = 0 解集 = 2 4 11 14 16

第15行：O第十五行符阖排列.xlsx；

225: OD = 0 解集 = 3 4 6 7 10 11 12 16
226: OE = 1
227: OF = 0 解集 = 7 10 11 12 13 16
228: OG = 0 解集 = 3 7 10 11 12 14 16
229: OH = 9
230: OI = 0 解集 = 3 4 7 10 13 14
231: OJ = 0 解集 = 3 7 10 11 13 16
232: OK = 15
233: OL = 0 解集 = 4 7 10 11 12 16
234: OM = 0 解集 = 4 6 7 10 11 12 16
235: ON = 2
236: OO = 8
237: OP = 0 解集 = 11 12 13 14 16
238: OQ = 5
239: OR = 0 解集 = 4 11 12 13 14
240: OS = 0 解集 = 4 11 13 14 16

第16行：P第十六行符阖排列.xlsx。

241: PD = 0 解集 = 3 4 6 7 11 12 16
242: PE = 0 解集 = 3 6 7 11 16
243: PF = 2
244: PG = 0 解集 = 3 7 8 11 12 16
245: PH = 0 解集 = 4 8 11 16
246: PI = 0 解集 = 3 4 7 8 13
247: PJ = 5
248: PK = 0 解集 = 4 7 11 13 16
249: PL = 0 解集 = 4 7 9 11 12 16
250: PM = 14
251: PN = 0 解集 = 4 6 7 9 11
252: PO = 0 解集 = 9 12 16
253: PP = 1
254: PQ = 0 解集 = 4 8 9 11
255: PR = 10
256: PS = 15
"""

def parse_constraints(text):
    """解析txt文件中的列约束"""
    row_names = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
    col_names = ['D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']
    
    current_row = None
    result = {}
    
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检测行标题：第1行：A第一行...
        row_match = re.match(r'第(\d+)行：(\w)', line)
        if row_match:
            current_row = row_match.group(2)
            result[current_row] = {}
            continue
        
        if not current_row:
            continue
        
        # 解析约束：序号: XY = 值/0 解集 = v1 v2 ...
        constraint_match = re.match(r'(\d+): (\w)(\w) = (\d+)(.*)', line)
        if constraint_match:
            num = int(constraint_match.group(1))
            row = constraint_match.group(2)
            col = constraint_match.group(3)
            value = int(constraint_match.group(4))
            rest = constraint_match.group(5).strip()
            
            pos = row + col
            
            if '解集' in rest:
                # 解集约束
                set_match = re.search(r'解集\s*=\s*([\d\s]+)', rest)
                if set_match:
                    values_str = set_match.group(1).strip()
                    values = set(int(v) for v in values_str.split() if v)
                    result[row][pos] = {
                        'type': 'set',
                        'value': value,
                        'allowed': values,
                        'size': len(values)
                    }
            else:
                # 固定值约束
                result[row][pos] = {
                    'type': 'fixed',
                    'value': value,
                    'allowed': {value},
                    'size': 1
                }
    
    return result, row_names, col_names

def main():
    print("=" * 80)
    print("TASK 1 COMPLETE: 解析txt文件中所有256个位置约束")
    print("=" * 80)
    
    constraints, row_names, col_names = parse_constraints(TXT_CONSTRAINTS)
    
    # 统计
    total_fixed = 0
    total_set = 0
    constraint_map = {}
    
    for row in row_names:
        for col in col_names:
            pos = row + col
            if pos in constraints.get(row, {}):
                c = constraints[row][pos]
                if c['type'] == 'fixed':
                    total_fixed += 1
                else:
                    total_set += 1
                constraint_map[pos] = c
    
    print(f"\n【统计】")
    print(f"  总位置数: 256")
    print(f"  固定值约束: {total_fixed} 个")
    print(f"  解集约束: {total_set} 个")
    print(f"  已解析: {len(constraint_map)} 个")
    
    # 每行分布
    print(f"\n【每行约束分布】")
    for row in row_names:
        fixed = sum(1 for col in col_names 
                    if constraints.get(row, {}).get(row+col, {}).get('type') == 'fixed')
        sets = sum(1 for col in col_names 
                   if constraints.get(row, {}).get(row+col, {}).get('type') == 'set')
        print(f"  {row}: fixed={fixed}, sets={sets}")
    
    # 解集大小分布
    print(f"\n【解集大小分布】")
    set_sizes = Counter()
    for c in constraint_map.values():
        if c['type'] == 'set':
            set_sizes[c['size']] += 1
    
    for size in sorted(set_sizes.keys()):
        print(f"  解集大小 {size}: {set_sizes[size]} 个位置")
    
    # 示例：行C的约束
    print(f"\n【约束示例 - 行C全部16个位置】")
    for col in col_names:
        pos = 'C' + col
        c = constraints.get('C', {}).get(pos, {})
        if c:
            if c['type'] == 'fixed':
                print(f"  {pos} = {c['value']} [FIXED]")
            else:
                print(f"  {pos} = {sorted(c['allowed'])} [SET size={c['size']}]")
    
    # 保存约束数据
    output = {
        'total_positions': 256,
        'total_fixed': total_fixed,
        'total_set': total_set,
        'row_distribution': {},
        'set_size_distribution': dict(set_sizes),
        'constraints': {}
    }
    
    for row in row_names:
        output['row_distribution'][row] = {
            'fixed': sum(1 for col in col_names 
                        if constraints.get(row, {}).get(row+col, {}).get('type') == 'fixed'),
            'sets': sum(1 for col in col_names 
                       if constraints.get(row, {}).get(row+col, {}).get('type') == 'set')
        }
        def serialize_constraint(c):
    """序列化约束，转换set为list"""
    return {
        'type': c['type'],
        'value': c['value'],
        'allowed': list(c['allowed']),
        'size': c['size']
    }

    # 在main函数中添加：
    output['constraints'][row] = {
        pos: serialize_constraint(constraints[row][pos])
        for pos in constraints.get(row, {})
    }
    
    with open('column_constraints.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n约束数据已保存到: column_constraints.json")
    
    # 输出固定值位置
    print(f"\n【固定值位置（共{total_fixed}个）】")
    for row in row_names:
        for col in col_names:
            pos = row + col
            c = constraints.get(row, {}).get(pos, {})
            if c and c['type'] == 'fixed':
                print(f"  {pos} = {c['value']}")
    
    return constraints, constraint_map

if __name__ == '__main__':
    main()
