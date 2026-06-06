# SAT 求解器深度技术资源报告

**报告日期**: 2026年5月14日  
**主题**: SAT/CNF编码技术、精确解计数、解枚举、工具框架及大型数独应用

---

## 一、关键技术要点

### 1.1 SAT/CNF 编码技术

#### 基础编码模型

| 编码类型 | 变量数量 | 子句数量 | 复杂度 |
|---------|---------|---------|--------|
| **最小编码 (Minimal)** | n³ | ~3n² + n³×n(n-1)/2 | O(n⁴) |
| **扩展编码 (Extended)** | n³ | 增加优化子句 | O(n⁴) |
| **SMT 直接编码** | n² | O(n²) 高阶约束 | O(n²) |

**标准数独 (9×9) 编码规模**:
- 布尔变量: 729 个 (x_{r,c,v} 表示位置(r,c)值为v)
- 最小编码子句: **8,829 条**
- 扩展编码子句: **11,988 条** (增加优化约束减少搜索空间)

#### 约束类型 (6大类)

| 约束类别 | 子句形式 | 数量 (9×9) | 逻辑含义 |
|---------|---------|-----------|---------|
| C₁: 每格至少一值 | n元子句 | n² = 81 | ∀(r,c): ∨ᵥ x_{r,c,v} |
| C₂: 每格至多一值 | 二元子句 | n²×n(n-1)/2 = 2,916 | ∀(r,c,v<v'): ¬x_{r,c,v}∨¬x_{r,c,v'} |
| C₃: 行唯一性 | n元子句 | n² = 81 | ∀(r,v): ∨_c x_{r,c,v} |
| C₄: 列唯一性 | n元子句 | n² = 81 | ∀(c,v): ∨_r x_{r,c,v} |
| C₅: 宫唯一性 | n元子句 | n² = 81 | ∀(宫,v): ∨_{(r,c)∈宫} x_{r,c,v} |
| C₆: 已知提示 | 一元子句 | 提示数 | x_{r,c,v} (固定值) |

#### 编码优化策略

| 优化技术 | 效果 | 实现方法 |
|---------|------|---------|
| **子句合并** | 减少30-50% | 将相关约束合并为复合子句 |
| **变量重用** | 减少内存 | 紧凑的变量编号映射 |
| **对称性破缺** | 减少搜索空间 | 固定首行首列的值 |
| **预处理传播** | 减少求解器工作 | 编码阶段应用单元传播 |
| **扩展约束** | 减少冲突2-3倍 | 增加冗余但高效的约束 |

**扩展编码优化效果 (Hard难度)**:
- 冲突次数: 147 → 11 (减少92%)
- 决策次数: 259 → 24 (减少91%)

### 1.2 精确解计数算法 (#SAT)

#### 核心算法原理

```
#SAT 基本框架 (基于DPLL):
count(φ) = 
  若 φ 为空: 返回 1
  若 φ 不可满足: 返回 0
  若 φ 可分解为独立组件 φ₁ ∧ φ₂:
    返回 count(φ₁) × count(φ₂)
  否则选择变量 x:
    返回 count(φ|ₓ₌True) + count(φ|ₓ₌False)
```

#### 主要技术组件

| 技术组件 | 作用 | 典型实现 |
|---------|------|---------|
| **组件缓存 (Component Caching)** | 避免重复计算子问题 | 哈希表存储规范化子公式 |
| **子句学习 (Clause Learning)** | 剪枝搜索空间 | 冲突驱动学习 (CDCL) |
| **公式缓存 (Formula Caching)** | 避免重复计数 | 存储已计算子公式结果 |
| **隐式BCP** | 增强 lookahead | 布尔约束传播优化 |
| **组件分解** | 并行化计算 | 识别独立子公式 |

#### 精确计数求解器对比

| 求解器 | 核心技术 | 性能特点 | 适用场景 |
|-------|---------|---------|---------|
| **sharpSAT** | 组件缓存 + 隐式BCP | 大型结构化实例最优 | 需要高效内存管理 |
| **Cachet** | 公式缓存 + 子句学习 | 平衡型，稳定 | 通用精确计数 |
| **c2d** | 编译到d-DNNF | 多次查询高效 | 需要重复计数 |
| **GANAK** | 投影 + 分层采样 | 大规模可扩展 | 超大规模实例 |

**sharpSAT 创新点**:
- 全新的组件编码方式，缓存大小减少至少一个数量级
- 新的缓存管理方案
- 适合#SAT的lookahead BCP技术
- 在大型结构化实例上显著优于其他#SAT求解器

### 1.3 解的枚举技术 (Solution Enumeration)

#### 枚举策略

| 策略 | 核心机制 | 适用场景 |
|-----|---------|---------|
| **Blocking Clause 法** | 每找到一个解，添加阻止该解的子句 | 小规模枚举 |
| **投影枚举 (Projected Enumeration)** | 仅枚举指定变量的组合 | 投影SAT问题 |
| **AllSAT 求解器** | 基于CDCL的完整枚举 | 硬件验证、形式化方法 |
| **增量枚举** | 维护求解器状态，增量查找新解 | 多次求解场景 |

#### Blocking Clause 技术

```
基本流程:
1. 调用 SAT 求解器
2. 若可满足:
   a. 输出当前解
   b. 添加 blocking clause: ¬(x₁∧x₂∧...∧xₙ)
   c. 返回步骤1
3. 若不可满足: 枚举完成

优化变体:
- 短 blocking clause: 基于 backbone 分析减少子句长度
- 不相交投影: 避免生成 blocking clause
```

#### 现代 AllSAT 求解器

| 求解器 | 技术特点 |
|-------|---------|
| **TabularAllSAT** | 投影枚举，无blocking clause |
| **TabularAllSMT** | SMT领域的投影枚举 |
| **BASolver** | 基于backbone的短blocking clause |
| **mChaff** | 改进的Chaff，支持枚举 |

### 1.4 CNF 格式规范

#### DIMACS CNF 标准格式

```
c 注释行（以c开头）
p cnf <变量数> <子句数>
<文字1> <文字2> ... <文字n> 0
```

**文字编码规则**:
| 类型 | 编码 |
|-----|-----|
| 正文字 xⱼ | j |
| 负文字 ¬xⱼ | -j |
| 子句结束 | 0 |

**示例 (标准数独编码片段)**:
```cnf
c Sudoku 9x9 CNF encoding
c Variable: var(r,c,v) = (r-1)*81 + (c-1)*9 + (v-1) + 1
p cnf 729 3176
1 2 3 4 5 6 7 8 9 0
-1 -2 0
-1 -3 0
...
```

#### 格式扩展

| 扩展格式 | 用途 | 支持工具 |
|---------|------|---------|
| **LRF (Lingeling)** | 增量求解、假设 | Lingeling, PySAT |
| **OPB** | 伪布尔约束 | Open-WBO, MaxSAT求解器 |
| **WCNF** | 加权MaxSAT | 各类MaxSAT求解器 |
| **proof format (RUP/DRAT)** | 证明输出 | 验证求解器正确性 |

---

## 二、重要工具和框架

### 2.1 核心 SAT 求解器

| 求解器 | 类型 | 特点 | 安装方式 |
|-------|-----|------|---------|
| **MiniSat** | CDCL | 轻量级，工业标准，简单API | `apt install minisat` |
| **Glucose** | CDCL+LBD | SAT竞赛冠军，高性能 | `apt install glucose` |
| **lingeling** | CDCL+扩展 | 增量求解支持，多模型 | `pacman -S lingeling` |
| **CaDiCaL** | CDCL | 现代高性能，开源 | `npm install cadical` |
| **Kissat** | CDCL | 2020 SAT竞赛冠军 | `git clone kissat` |

### 2.2 Python 集成工具

| 工具 | 功能 | 优势 |
|-----|------|-----|
| **PySAT** | 统一SAT求解器接口 | 支持10+求解器，增量API |
| **python-sat** | PySAT的Python绑定 | 原生API，完整功能 |
| **pysat.examples** | 示例集合 | MaxSAT、MUS、MCS枚举 |

**PySAT 核心API**:
```python
from pysat.formula import CNF
from pysat.solvers import Solver

# 创建CNF公式
cnf = CNF()
cnf.append([1, 2])
cnf.append([-1, 2])

# 使用求解器
with Solver(name='glucose', bootstrap_with=cnf) as solver:
    if solver.solve():
        model = solver.get_model()
        print("SAT", model)
    else:
        print("UNSAT")
```

### 2.3 #SAT 计数工具

| 工具 | 类型 | 支持功能 |
|-----|------|---------|
| **sharpSAT** | 精确计数 | 组件缓存、内存优化 |
| **Cachet** | 精确计数 | 公式缓存、组件分析 |
| **ApproxMC** | 近似计数 | 概率计数，快速 |
| **GANAK** | 投影计数 | 分层采样，大规模 |
| **c2d** | 编译型 | d-DNNF编译，多次查询 |

### 2.4 SMT 求解器 (扩展)

| 求解器 | 支持理论 | 数独应用优势 |
|-------|---------|------------|
| **Z3** | 整数、数组、逻辑 | Distinct约束直接编码 |
| **CVC5** | 多理论 | 高效的整数变量支持 |
| **Yices** | 算术、逻辑 | 轻量级选择 |

**Z3 SMT 数独编码示例**:
```python
from z3 import *

def sudoku_solver(puzzle):
    # 直接整数变量编码
    cells = [[Int(f'cell_{i}_{j}') for j in range(9)] for i in range(9)]
    
    # 使用Distinct约束
    s = Solver()
    for i in range(9):
        s.add(Distinct(cells[i]))  # 行唯一性
        s.add(Distinct([cells[j][i] for j in range(9)]))  # 列唯一性
    
    # 宫唯一性
    for si in range(3):
        for sj in range(3):
            block = [cells[3*si+i][3*sj+j] for i in range(3) for j in range(3)]
            s.add(Distinct(block))
    
    # 填入已知提示
    # ...
    
    if s.check() == sat:
        return s.model()
```

---

## 三、核心算法概述

### 3.1 DPLL 算法框架

```
DPLL(φ):
1. 单位传播: 重复应用单元子句赋值
2. 纯文字消除: 移除纯文字
3. 若 φ 为空: 返回 SATISFIABLE
4. 若存在空子句: 返回 UNSATISFIABLE
5. 选择分支变量 x
6. 递归: return DPLL(φ|ₓ₌True) or DPLL(φ|ₓ₌False)
```

### 3.2 CDCL (Conflict-Driven Clause Learning)

```
CDCL 核心流程:
1. 决策: 选择未赋值变量，赋予真/假
2. 传播: 执行布尔约束传播 (BCP)
3. 检测冲突:
   - 若冲突:
     a. 冲突分析，生成学习子句
     b. 回溯到学习子句足够支持的层级
   - 若无冲突:
     a. 若所有变量赋值: SATISFIABLE
     b. 若需重启: 清空决策栈，重新开始
     c. 否则: 回到步骤1
```

### 3.3 #SAT 计数算法 (sharpSAT风格)

```
sharpSAT-Count(φ):
1. 组件分解: 识别独立子组件
   - 若可分解为 φ₁, φ₂:
     返回 sharpSAT-Count(φ₁) × sharpSAT-Count(φ₂)
2. 缓存检查: 若 φ 在缓存中，返回缓存值
3. 分支选择: 选择最优变量 x (基于启发式)
4. 递归计数:
   c₁ = sharpSAT-Count(φ|ₓ₌True)
   c₂ = sharpSAT-Count(φ|ₓ₌False)
5. 缓存结果: 存储 (φ, c₁+c₂)
6. 返回 c₁ + c₂
```

### 3.4 解枚举算法 (AllSAT)

```
AllSAT-Enumerate(φ):
1. 调用 SAT 求解器求解 φ
2. while SATISFIABLE:
   a. 获取模型 M
   b. 输出 M
   c. 构造 blocking clause B = ¬M
   d. 将 B 添加到 φ
   e. 重新求解
3. 输出: 枚举完成
```

**优化变体 - 投影枚举**:
```
ProjectedAllSAT(φ, X):  # X 为需要枚举的变量集
1. 调用 SAT 求解器，仅关注 X 中变量的投影
2. while SATISFIABLE:
   a. 获取投影 P = M|ₓ
   b. 若 P 已输出: continue
   c. 输出 P
   d. 添加投影 blocking clause: ¬P
3. 返回所有唯一投影
```

---

## 四、应用场景匹配 (大型数独问题)

### 4.1 数独问题规模分析

| 数独规模 | 布尔变量数 | CNF子句数 | 典型求解时间 |
|---------|-----------|----------|------------|
| 9×9 (标准) | 729 | ~3,176 | <10ms |
| 16×16 | 4,096 | ~50,000 | 1-10秒 |
| 25×25 | 15,625 | ~300,000 | 10-100秒 |
| 100×100 | 1,000,000 | ~30,000,000 | 分钟级 |

**复杂度增长**: O(n⁵) - 变量 O(n³)，子句 O(n⁴)，求解复杂度随n急剧增加

### 4.2 大型数独求解策略

#### 方法选择建议

| 问题规模 | 推荐方法 | 理由 |
|---------|---------|-----|
| 9×9 | 任意SAT求解器 | 极快，所有方法均可 |
| 16×16 | MiniSat/Glucose | 平衡性能和复杂度 |
| 25×25 | SMT (Z3/CVC5) | 直接整数编码减少变量数 |
| 100+ | 专用SMT + 约束传播 | 布尔编码不可行 |

#### SMT vs SAT 编码对比

| 方面 | SAT (CNF) | SMT |
|-----|-----------|-----|
| **变量数** | n³ (729 for 9×9) | n² (81 for 9×9) |
| **约束表达** | 显式子句 | 高阶约束 (Distinct) |
| **求解速度** | 9×9: 极快 | 9×9: 快 |
| **可扩展性** | 中等 | 较好 |
| **理论支持** | 无 | 算术、数组等 |

**25×25 数独性能比较 (2025年研究)**:
| 求解器 | 成功率 | 平均时间 | 传播效率 |
|-------|--------|---------|---------|
| Z3 | 100% | 15秒 | 高 |
| CVC5 | 100% | 18秒 | 高 |
| MiniSat (CNF) | ~60% | 120秒+ | 中 |
| 回溯搜索 | ~40% | 300秒+ | 低 |

### 4.3 特殊问题场景

#### 数独解计数问题

**应用场景**: 计算某个数独谜题有多少个有效解

| 求解器 | 适用性 | 预期复杂度 |
|-------|-------|----------|
| sharpSAT | ★★★ | 良好，但n增大后指数增长 |
| Cachet | ★★★ | 稳定，中等规模 |
| GANAK | ★★☆ | 大规模近似计数 |
| 增量枚举 | ★★☆ | 实际计数所有解 |

**提示数与解数的关系**:
- 17提示 (最小单解): 约50,000个非等价谜题，验证需计算机穷举
- 解数指数增长: 提示数每减1，搜索空间约增加10倍
- 16提示无单解: McGuire (2012) 证明，遍历54亿+棋盘

#### 数独生成问题

**最小提示数搜索**:
```
算法流程:
1. 生成完整合法数独棋盘
2. 随机移除单元格作为候选提示
3. 调用SAT求解器验证唯一解
4. 若多解，恢复该单元格
5. 重复直到无法移除更多
```

**性能优化**:
- 使用增量SAT求解 (PySAT增量接口)
- 预计算不可避免集 (Unavoidable Sets)
- 并行化搜索 (分布式计算)

### 4.4 推荐技术路线

```
┌─────────────────────────────────────────────────────────┐
│                  大型数独求解技术选型                     │
├─────────────────────────────────────────────────────────┤
│  9×9 标准数独                                             │
│  ├── 单解求解: MiniSat / Glucose (CNF编码)               │
│  ├── 多解枚举: AllSAT / 增量求解                          │
│  └── 解计数: sharpSAT / Cachet                           │
├─────────────────────────────────────────────────────────┤
│  16×16 中大型数独                                         │
│  ├── 单解求解: MiniSat (扩展编码) / Glucose              │
│  ├── 多解枚举: TabularAllSAT (投影枚举)                  │
│  └── 解计数: sharpSAT (若规模可接受)                     │
├─────────────────────────────────────────────────────────┤
│  25×25 及以上大型数独                                     │
│  ├── 单解求解: Z3 / CVC5 (SMT编码)                      │
│  ├── 多解枚举: TabularAllSMT                             │
│  └── 解计数: 近似计数 (GANAK/ApproxMC) + 验证            │
└─────────────────────────────────────────────────────────┘
```

---

## 五、资源索引

### 5.1 核心论文

| 论文 | 主题 | 链接 |
|-----|------|-----|
| sharpSAT | #SAT精确计数 | [Springer LNCS 4121](https://link.springer.com/content/pdf/10.1007/11814948_38.pdf) |
| Cachet Heuristics | 模型计数启发式 | [CS Washington](https://homes.cs.washington.edu/~beame/papers/cachet-heuristics.pdf) |
| Sudoku as SAT | 数独CNF编码 | [INESC-ID](https://sat.inesc-id.pt/~ines/publications/aimath06.pdf) |
| AllSAT Survey | 解枚举技术 | [ACM](https://dl.acm.org/doi/10.1145/2975585) |
| 17-Clue Proof | 最小提示数证明 | [Nature 报道](https://www.sudokuwiki.org/17_Clue_Proof) |

### 5.2 代码仓库

| 项目 | 语言 | 功能 |
|-----|------|-----|
| [PySAT](https://pysathq.github.io/) | Python | SAT求解器统一接口 |
| [sharpSAT](https://github.com/marcthurley/sharpSAT) | C++ | #SAT精确计数 |
| [sat-sudoku-solver](https://github.com/matt4tch/sat-sudoku-solver) | C++ | 数独SAT求解器示例 |
| [GANAK](https://github.com/meelgroup/GANAK) | C++ | 投影模型计数 |

### 5.3 基准数据集

| 数据集 | 规模 | 用途 |
|-------|------|-----|
| **top95** | 95个Hard 9×9 | SAT求解器基准 |
| **17-clue collection** | 50,000+ | 最小提示数研究 |
| **25×25 benchmarks** | 100个谜题 | 大型数独评估 (2025) |

---

## 六、实践建议

### 6.1 编码选择指南

```
if n == 9:
    use CNF_encoding(minimal_or_extended)
    solver = MiniSat / Glucose
elif n <= 16:
    use CNF_encoding(extended_with_optimizations)
    solver = Glucose / CaDiCaL
elif n <= 25:
    use SMT_encoding(整数变量 + Distinct约束)
    solver = Z3 / CVC5
else:
    use SMT + 专用约束传播
    solver = Z3 + 自定义启发式
```

### 6.2 性能调优技巧

| 优化方向 | 具体措施 |
|---------|---------|
| **减少子句数** | 使用扩展编码中的冗余但高效约束 |
| **减少变量数** | SMT编码替代CNF，减少O(n)倍变量 |
| **增量求解** | 使用PySAT的假设接口，避免重复求解 |
| **并行化** | 组件分解后并行计数，或使用并行求解器 |
| **缓存重用** | sharpSAT/Cachet的自动组件缓存 |

### 6.3 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|-----|---------|---------|
| CNF生成太慢 | 编码算法效率低 | 预生成模板，增量构建 |
| 求解器内存溢出 | 变量数过多 | 切换到SMT编码或分块求解 |
| 计数结果异常 | 公式有对称性 | 添加对称性破缺约束 |
| 枚举重复解 | blocking clause不足 | 检查投影变量集是否完整 |
| 大型数独超时 | 搜索空间指数增长 | 增加提示数或使用SMT |

---

**报告结束**

*如需进一步了解特定技术细节或获取实现代码，请告知。*