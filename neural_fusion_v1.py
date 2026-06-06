#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极融合搜索架构 V1 — 五维神经元融阖系统

模块4：六维神经元状态 → 融合决策 → 搜索方向引导
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum


# ======================== 常量定义 ========================

GRID_SIZE = 16


# ======================== 枚举类型 ========================

class NeuronState(Enum):
    """神经元状态"""
    EMPTY = "empty"          # 空
    CANDIDATE = "candidate"  # 候选
    DETERMINED = "determined"  # 确定
    CONFLICT = "conflict"    # 冲突
    PROPAGATED = "propagated"  # 已传播


class FusionPriority(Enum):
    """融合优先级"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


# ======================== 数据类 ========================

@dataclass
class NeuralNode:
    """神经元节点"""
    neuron_id: str           # 神经元ID
    dimension: int           # 维度 (0-5)
    state: NeuronState = NeuronState.EMPTY
    confidence: float = 0.0  # 置信度
    connections: List[str] = field(default_factory=list)
    output: Optional[Dict] = None


@dataclass
class FusionDecision:
    """融合决策"""
    priority_cells: List[Tuple[int, int]]  # 高优先级单元格
    priority_values: Dict[Tuple[int, int], int]  # 优先填充值
    strategy: str = "default"  # 搜索策略
    pruning_rules: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ConstraintUpdate:
    """约束更新"""
    cell: Tuple[int, int]
    old_domain: Set[int]
    new_domain: Set[int]
    constraint_type: str


# ======================== 六维神经元定义 ========================

class PointNeuron:
    """POINT 神经元 (0D) — 单元级"""
    
    def __init__(self):
        self.nodes: Dict[Tuple[int, int], NeuralNode] = {}
    
    def initialize(self, anchors: Dict[Tuple[int, int], int]) -> None:
        """初始化256个单元神经元"""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                is_anchor = (r, c) in anchors
                state = NeuronState.DETERMINED if is_anchor else NeuronState.EMPTY
                confidence = 1.0 if is_anchor else 0.0
                self.nodes[(r, c)] = NeuralNode(
                    neuron_id=f"P_{r}_{c}",
                    dimension=0,
                    state=state,
                    confidence=confidence
                )
    
    def compute_priority(self) -> List[Tuple[int, int, float]]:
        """计算单元格优先级（MRV启发式）"""
        priorities = []
        for (r, c), node in self.nodes.items():
            if node.state == NeuronState.EMPTY:
                # 空单元格优先级
                priorities.append((r, c, 1.0 - node.confidence))
        priorities.sort(key=lambda x: x[2], reverse=True)
        return priorities
    
    def select_next_cell(self) -> Optional[Tuple[int, int]]:
        """选择下一个要填充的单元格（MRV）"""
        priorities = self.compute_priority()
        if priorities:
            return priorities[0][:2]
        return None


class LineNeuron:
    """LINE 神经元 (1D) — 行/列级"""
    
    def __init__(self):
        self.row_nodes: List[NeuralNode] = []
        self.col_nodes: List[NeuralNode] = []
        self.constraint_graph: Dict[str, List[str]] = {}
    
    def initialize(self, num_rows: int = GRID_SIZE, num_cols: int = GRID_SIZE) -> None:
        """初始化行/列神经元"""
        for i in range(num_rows):
            node = NeuralNode(
                neuron_id=f"L_row_{i}",
                dimension=1,
                state=NeuronState.CANDIDATE
            )
            self.row_nodes.append(node)
        
        for i in range(num_cols):
            node = NeuralNode(
                neuron_id=f"L_col_{i}",
                dimension=1,
                state=NeuronState.CANDIDATE
            )
            self.col_nodes.append(node)
    
    def propagate_constraint(self, row_idx: int, col_idx: int, 
                             value: int) -> List[ConstraintUpdate]:
        """传播行/列约束"""
        updates = []
        
        # 行传播：同行其他单元格不能取该值
        for c in range(GRID_SIZE):
            if c != col_idx:
                updates.append(ConstraintUpdate(
                    cell=(row_idx, c),
                    old_domain=set(range(1, GRID_SIZE + 1)),
                    new_domain=set(range(1, GRID_SIZE + 1)) - {value},
                    constraint_type='row'
                ))
        
        # 列传播：同列其他单元格不能取该值
        for r in range(GRID_SIZE):
            if r != row_idx:
                updates.append(ConstraintUpdate(
                    cell=(r, col_idx),
                    old_domain=set(range(1, GRID_SIZE + 1)),
                    new_domain=set(range(1, GRID_SIZE + 1)) - {value},
                    constraint_type='col'
                ))
        
        return updates


class PlaneNeuron:
    """PLANE 神经元 (2D) — 宫级"""
    
    def __init__(self):
        self.box_nodes: List[NeuralNode] = []
        self.num_boxes = (GRID_SIZE // 4) * (GRID_SIZE // 4)  # 16个宫
    
    def initialize(self) -> None:
        """初始化16个宫神经元"""
        for i in range(self.num_boxes):
            node = NeuralNode(
                neuron_id=f"PL_box_{i}",
                dimension=2,
                state=NeuronState.CANDIDATE
            )
            self.box_nodes.append(node)
    
    def get_box_id(self, row: int, col: int) -> int:
        """获取单元格所属宫ID"""
        box_r = row // 4
        box_c = col // 4
        return box_r * 4 + box_c
    
    def propagate_box_constraint(self, row: int, col: int, 
                                  value: int) -> List[ConstraintUpdate]:
        """传播宫约束"""
        box_id = self.get_box_id(row, col)
        updates = []
        
        box_r, box_c = box_id // 4, box_id % 4
        
        for r in range(box_r * 4, (box_r + 1) * 4):
            for c in range(box_c * 4, (box_c + 1) * 4):
                if (r, c) != (row, col):
                    updates.append(ConstraintUpdate(
                        cell=(r, c),
                        old_domain=set(range(1, GRID_SIZE + 1)),
                        new_domain=set(range(1, GRID_SIZE + 1)) - {value},
                        constraint_type='box'
                    ))
        
        return updates


class BodyNeuron:
    """BODY 神经元 (3D) — 全域级"""
    
    def __init__(self):
        self.state = NeuronState.EMPTY
        self.solutions_pool: List[Dict] = []
        self.global_confidence = 0.0
    
    def aggregate_solutions(self, solutions: List[Dict]) -> None:
        """汇聚多解"""
        self.solutions_pool.extend(solutions)
        if solutions:
            self.state = NeuronState.PROPAGATED
            self.global_confidence = len(set(str(s) for s in solutions)) / max(len(solutions), 1)


class SphereNeuron:
    """SPHERE 神经元 (4D) — 解空间级"""
    
    def __init__(self):
        self.topology_map: Dict = {}
        self.clusters: List[List[Dict]] = []
        self.distance_matrix: List[List[float]] = []
    
    def map_topology(self, solutions: List[Dict]) -> None:
        """映射解空间拓扑"""
        # 计算解之间的距离矩阵
        n = len(solutions)
        self.distance_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                # 计算汉明距离
                dist = sum(
                    1 for r in range(GRID_SIZE) 
                    for c in range(GRID_SIZE)
                    if solutions[i].get((r, c)) != solutions[j].get((r, c))
                )
                self.distance_matrix[i][j] = dist
                self.distance_matrix[j][i] = dist
        
        # 简单聚类（基于距离阈值）
        threshold = GRID_SIZE * GRID_SIZE * 0.1  # 10%差异
        visited = [False] * n
        cluster_id = 0
        
        for i in range(n):
            if not visited[i]:
                cluster = [i]
                visited[i] = True
                for j in range(i + 1, n):
                    if not visited[j] and self.distance_matrix[i][j] < threshold:
                        cluster.append(j)
                        visited[j] = True
                self.clusters.append(cluster)
    
    def get_navigation_path(self, 
                            current_solution: Dict,
                            target_density: float = 0.5) -> List[Dict]:
        """获取解空间导航路径"""
        # 基于聚类选择探索方向
        if not self.clusters:
            return []
        
        # 找到当前解所属的簇
        for cluster in self.clusters:
            if 0 in cluster:  # 假设0是当前解
                # 返回簇内其他解作为导航路径
                return [cluster]
        
        return self.clusters


class SpaceTimeNeuron:
    """SPACE-TIME 神经元 (5D) — 演化级"""
    
    def __init__(self):
        self演化轨迹: List[Dict] = []
        self.convergence_trend: float = 0.0
        self.early_stop_decision: bool = False
        self.strategy_adjustment: Dict = {}
    
    def track_evolution(self, iteration: int, 
                        metrics: Dict[str, float]) -> None:
        """记录演化轨迹"""
        self演化轨迹.append({
            'iteration': iteration,
            'metrics': metrics,
            'timestamp': iteration
        })
        
        # 计算收敛趋势
        if len(self演化轨迹) >= 3:
            recent_fitness = [t['metrics'].get('fitness', 0) 
                             for t in self演化轨迹[-3:]]
            if all(recent_fitness[i] >= recent_fitness[i-1] 
                   for i in range(1, len(recent_fitness))):
                self.convergence_trend = 1.0
            else:
                self.convergence_trend = 0.0
    
    def should_early_stop(self, patience: int = 10, 
                          min_improvement: float = 0.01) -> bool:
        """判断是否早停"""
        if len(self演化轨迹) < patience:
            return False
        
        recent = self演化轨迹[-patience:]
        improvements = []
        for i in range(1, len(recent)):
            prev_fitness = recent[i-1]['metrics'].get('fitness', 0)
            curr_fitness = recent[i]['metrics'].get('fitness', 0)
            if curr_fitness > prev_fitness:
                improvements.append(curr_fitness - prev_fitness)
        
        avg_improvement = sum(improvements) / max(len(improvements), 1)
        self.early_stop_decision = avg_improvement < min_improvement
        
        return self.early_stop_decision
    
    def adjust_strategy(self, 
                       current_strategy: str,
                       exploration_ratio: float) -> str:
        """动态调整策略"""
        if exploration_ratio > 0.7:
            # 高探索率：偏向广搜索
            self.strategy_adjustment['weight'] = 0.3
            return 'wave_helix'
        elif exploration_ratio < 0.3:
            # 低探索率：偏向精搜索
            self.strategy_adjustment['weight'] = 0.8
            return 'backtrack'
        else:
            return 'fusion'


# ======================== 五维神经元融阖系统 ========================

class FiveDimensionalNeuralFusion:
    """五维神经元融阖系统
    
    六维神经元逐层传递与融合：
    POINT → LINE → PLANE → BODY → SPHERE → SPACE-TIME
    """
    
    def __init__(self):
        # 初始化六维神经元
        self.point = PointNeuron()
        self.line = LineNeuron()
        self.plane = PlaneNeuron()
        self.body = BodyNeuron()
        self.sphere = SphereNeuron()
        self.spacetime = SpaceTimeNeuron()
        
        self.fusion_history: List[FusionDecision] = []
    
    def initialize(self, anchors: Dict[Tuple[int, int], int]) -> None:
        """初始化所有神经元"""
        self.point.initialize(anchors)
        self.line.initialize()
        self.plane.initialize()
    
    def fuse_point_layer(self, 
                         anchors: Dict[Tuple[int, int], int]) -> Dict:
        """POINT层融合：单元级决策"""
        
        # 根据锚点生成初始置信度
        for (r, c), val in anchors.items():
            node = self.point.nodes.get((r, c))
            if node:
                node.state = NeuronState.DETERMINED
                node.confidence = 1.0
                node.output = {'value': val}
        
        # 计算空单元优先级
        priority_cells = self.point.compute_priority()
        
        return {
            'priority_cells': priority_cells[:10],  # 前10个优先
            'fixed_cells': len(anchors),
            'empty_cells': GRID_SIZE * GRID_SIZE - len(anchors)
        }
    
    def fuse_line_layer(self, 
                        point_output: Dict) -> Dict:
        """LINE层融合：行/列级约束传播"""
        
        # 基于POINT层的输出，传播约束
        propagated = []
        
        for (r, c), val in point_output.get('fixed_cells_info', {}).items():
            updates = self.line.propagate_constraint(r, c, val)
            propagated.extend(updates)
        
        # 检查行/列神经元的状态
        row_states = [node.state for node in self.line.row_nodes]
        col_states = [node.state for node in self.line.col_nodes]
        
        return {
            'propagated_updates': len(propagated),
            'row_satisfied': sum(1 for s in row_states if s == NeuronState.PROPAGATED),
            'col_satisfied': sum(1 for s in col_states if s == NeuronState.PROPAGATED)
        }
    
    def fuse_plane_layer(self, 
                         line_output: Dict) -> Dict:
        """PLANE层融合：宫级约束检查"""
        
        # 检查宫约束
        box_status = []
        for box_id in range(self.plane.num_boxes):
            box_status.append({
                'box_id': box_id,
                'state': NeuronState.CANDIDATE,
                'constraints': 0  # 待更新
            })
        
        return {
            'box_status': box_status,
            'plane_confidence': 0.5  # 初始置信度
        }
    
    def fuse_body_layer(self, 
                        plane_output: Dict,
                        candidate_solutions: List[Dict]) -> Dict:
        """BODY层融合：全域汇聚"""
        
        self.body.aggregate_solutions(candidate_solutions)
        
        return {
            'solutions_count': len(self.body.solutions_pool),
            'global_confidence': self.body.global_confidence,
            'status': self.body.state.value
        }
    
    def fuse_sphere_layer(self, 
                          body_output: Dict,
                          solutions: List[Dict]) -> Dict:
        """SPHERE层融合：解空间拓扑"""
        
        if solutions:
            self.sphere.map_topology(solutions)
        
        return {
            'num_clusters': len(self.sphere.clusters),
            'topology_density': len(self.sphere.clusters) / max(len(solutions), 1),
            'navigation_paths': len(self.sphere.clusters)
        }
    
    def fuse_spacetime_layer(self, 
                             sphere_output: Dict,
                             iteration: int,
                             metrics: Dict[str, float]) -> Dict:
        """SPACE-TIME层融合：演化监控"""
        
        self.spacetime.track_evolution(iteration, metrics)
        
        # 判断策略调整
        new_strategy = self.spacetime.adjust_strategy(
            'fusion',
            sphere_output.get('topology_density', 0.5)
        )
        
        should_stop = self.spacetime.should_early_stop()
        
        return {
            'convergence_trend': self.spacetime.convergence_trend,
            'should_early_stop': should_stop,
            'recommended_strategy': new_strategy,
            'evolution_stage': len(self.spacetime.演化轨迹)
        }
    
    def fuse(self, 
             anchors: Dict[Tuple[int, int], int],
             iteration: int,
             candidate_solutions: List[Dict],
             metrics: Dict[str, float]) -> FusionDecision:
        """六维神经元融阖 → 决策"""
        
        # 逐层传递
        point_output = self.fuse_point_layer(anchors)
        line_output = self.fuse_line_layer(point_output)
        plane_output = self.fuse_plane_layer(line_output)
        body_output = self.fuse_body_layer(plane_output, candidate_solutions)
        sphere_output = self.fuse_sphere_layer(body_output, candidate_solutions)
        spacetime_output = self.fuse_spacetime_layer(
            sphere_output, iteration, metrics
        )
        
        # 生成融合决策
        priority_cells = point_output.get('priority_cells', [])
        
        decision = FusionDecision(
            priority_cells=[(r, c) for r, c, _ in priority_cells[:5]],
            priority_values={},
            strategy=spacetime_output.get('recommended_strategy', 'fusion'),
            pruning_rules=[],
            confidence=point_output.get('fixed_cells', 0) / (GRID_SIZE * GRID_SIZE)
        )
        
        self.fusion_history.append(decision)
        
        return decision


# ======================== 测试 ========================

if __name__ == "__main__":
    # 模拟锚点
    anchors = {(2, 0): 7, (2, 1): 15, (2, 2): 3, (2, 3): 9}
    
    # 初始化融阖系统
    fusion = FiveDimensionalNeuralFusion()
    fusion.initialize(anchors)
    
    # 测试融合
    decision = fusion.fuse(
        anchors=anchors,
        iteration=1,
        candidate_solutions=[],
        metrics={'fitness': 0.5}
    )
    
    print(f"融合决策:")
    print(f"  优先级单元格: {decision.priority_cells[:3]}")
    print(f"  推荐策略: {decision.strategy}")
    print(f"  置信度: {decision.confidence:.2f}")
