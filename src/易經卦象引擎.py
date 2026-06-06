"""
易經卦象引擎 - 符闔排列與六十四卦映射系統
I-Ching Hexagram Engine - Fuhe Permutation & 64-Hexagram Mapping

包含：
- Hexagram: 六十四卦基本單元
- Fuhe_Translator: 符闔轉化器
- Hexagram_Mapper: 卦象映射器
- Trigram_Analyzer: 卦象分析器
- IChingOptimizer: 卦象博弈優化器
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import math


# ============================================================================
# 基礎類型定義
# ============================================================================

GRID_SIZE = 16
NUM_VALUES = 16
YANG = 1  # 陽爻 ⚊
YIN = 0   # 陰爻 ⚋


class Trigram(Enum):
    """八卦（三爻）"""
    QIAN = ("乾", "☰", 0b111, "天", "剛")      # 111
    KUN = ("坤", "☷", 0b000, "地", "柔")        # 000
    ZHEN = ("震", "☳", 0b001, "雷", "動")       # 001
    XUN = ("巽", "☴", 0b110, "風", "入")        # 110
    KAN = ("坎", "☵", 0b010, "水", "陷")        # 010
    LI = ("離", "☲", 0b101, "火", "麗")         # 101
    GEN = ("艮", "☶", 0b100, "山", "止")        # 100
    DUI = ("兌", "☱", 0b011, "澤", "悅")        # 011


class Hexagram(Enum):
    """六十四卦（六爻）"""
    # 上經（1-30卦）
    QIAN = ("乾", "䷀", 0b111111, "天", "元亨利貞")
    KUN = ("坤", "䷁", 0b000000, "地", "元亨牝馬")
    TUN = ("屯", "䷂", 0b000101, "水雷", "元亨利貞")
    MENG = ("蒙", "䷃", 0b100101, "山水", "亨匪我求")
    XU = ("需", "䷄", 0b111010, "水天", "有孚光亨")
    SONG = ("訟", "䷅", 0b101010, "天水", "有孚窒惕")
    SHI = ("師", "䷆", 0b001010, "地水", "貞丈人吉")
    BI = ("比", "䷇", 0b000010, "水地", "吉原筮元永")
    XIAO_CHU = ("小畜", "䷈", 0b111110, "風天", "亨密雲不雨")
    LUI = ("履", "䷉", 0b111011, "天澤", "履虎尾不咥")
    TAI = ("泰", "䷊", 0b000111, "地天", "小往大來")
    PI = ("否", "䷋", 0b111000, "天地", "否之匪人")
    TONG_REN = ("同人", "䷌", 0b111011, "天火", "同人于野")
    DA_YU = ("大有", "䷍", 0b001111, "火天", "元亨")
    XIAN = ("咸", "䷞", 0b011011, "澤山", "亨利貞")
    HENG = ("恆", "䷟", 0b110100, "雷風", "亨無咎")
    XUN = ("巽", "䷸", 0b110110, "風", "小亨利有")
    GEN = ("艮", "䷳", 0b100100, "山", "艮其背不獲")
    
    # 下經（31-64卦）
    JI_JI = ("既濟", "䷾", 0b101010, "水火", "亨小利貞")
    WEI_JI = ("未濟", "䷿", 0b010101, "火水", "亨狐汔濟")
    DA_GUO = ("大過", "䷛", 0b011110, "澤風", "棟撓利有")
    XIAO_GUO = ("小過", "䷽", 0b100100, "雷山", "亨利貞")
    CUI = ("萃", "䷬", 0b011010, "澤地", "亨王假有")
    SHENG = ("升", "䷭", 0b001100, "地風", "元亨用見")
    
    # 更多卦象（簡化表示，完整64卦需擴展）
    # 使用位模式表示，上三爻為外卦，下三爻為內卦
    
    @classmethod
    def from_binary(cls, binary: int) -> Optional['Hexagram']:
        """從二進制值取得卦"""
        for h in cls:
            if h.value[2] == binary:
                return h
        return None
    
    @classmethod
    def get_all(cls) -> List['Hexagram']:
        """取得所有卦象"""
        return list(cls)


# ============================================================================
# 爻與卦的基本結構
# ============================================================================

@dataclass
class Yao:
    """單爻"""
    position: int  # 爻位 (1-6，從下往上)
    yin_yang: int  # 0=陰爻⚋, 1=陽爻⚊
    name: str = ""
    
    def __post_init__(self):
        if self.yin_yang == YANG:
            self.name = "陽"
        else:
            self.name = "陰"
    
    def get_symbol(self) -> str:
        """取得符號"""
        return "⚊" if self.yin_yang == YANG else "⚋"
    
    def get_value(self) -> int:
        """取得數值 (2^(position-1))"""
        return self.yin_yang * (2 ** (self.position - 1))
    
    def __str__(self) -> str:
        return f"{self.name}爻({self.position}){self.get_symbol()}"


@dataclass
class TrigramStructure:
    """三爻卦結構"""
    name: str
    symbol: str
    binary: int
    element: str  # 五行屬性
    attribute: str  # 屬性
    yaos: List[Yao] = field(default_factory=list)
    
    def __post_init__(self):
        """從二進制構造爻"""
        self.yaos = []
        for i in range(3):
            yin_yang = (self.binary >> i) & 1
            self.yaos.append(Yao(position=i+1, yin_yang=yin_yang))
    
    def get_binary_string(self) -> str:
        """取得二進制表示"""
        return bin(self.binary)[2:].zfill(3)
    
    def __str__(self) -> str:
        return f"{self.name}({self.symbol}){self.get_binary_string()}"


@dataclass
class HexagramStructure:
    """六爻卦結構"""
    name: str
    symbol: str
    binary: int
    upper_element: str  # 上卦元素
    lower_element: str  # 下卦元素
    judgment: str  # 卦辭
    image: str = ""
    
    # 上下卦
    upper_trigram: Optional[TrigramStructure] = None
    lower_trigram: Optional[TrigramStructure] = None
    
    yaos: List[Yao] = field(default_factory=list)
    
    def __post_init__(self):
        """從二進制構造爻和上下卦"""
        # 六爻 (從下往上編號 1-6)
        self.yaos = []
        for i in range(6):
            yin_yang = (self.binary >> i) & 1
            self.yaos.append(Yao(position=i+1, yin_yang=yin_yang))
        
        # 下三爻為內卦 (位置 0,1,2 → 爻位 1,2,3)
        lower_binary = self.binary & 0b111
        self.lower_trigram = self._get_trigram(lower_binary)
        
        # 上三爻為外卦 (位置 3,4,5 → 爻位 4,5,6)
        upper_binary = (self.binary >> 3) & 0b111
        self.upper_trigram = self._get_trigram(upper_binary)
    
    def _get_trigram(self, binary: int) -> TrigramStructure:
        """取得對應的三爻卦"""
        trigram_map = {
            0b111: Trigram.QIAN,
            0b000: Trigram.KUN,
            0b001: Trigram.ZHEN,
            0b110: Trigram.XUN,
            0b010: Trigram.KAN,
            0b101: Trigram.LI,
            0b100: Trigram.GEN,
            0b011: Trigram.DUI,
        }
        
        tg = trigram_map.get(binary)
        if tg:
            return TrigramStructure(
                name=tg.value[0],
                symbol=tg.value[1],
                binary=tg.value[2],
                element=tg.value[3],
                attribute=tg.value[4]
            )
        return TrigramStructure(
            name="未知",
            symbol="?",
            binary=binary,
            element="?",
            attribute="?"
        )
    
    def get_binary_string(self) -> str:
        """取得二進制表示"""
        return bin(self.binary)[2:].zfill(6)
    
    def get_yao_sequence(self) -> str:
        """取得爻序表示"""
        return "".join(y.get_symbol() for y in self.yaos)
    
    def get_hexagram_name(self) -> str:
        """取得卦名"""
        return f"{self.name}({self.symbol})"
    
    def __str__(self) -> str:
        return (f"{self.get_hexagram_name()} "
                f"{self.upper_trigram}上{self.lower_trigram}下 "
                f"{self.get_binary_string()}")


# ============================================================================
# 符闔轉化器
# ============================================================================

class FuheTranslator:
    """符闔轉化器：符號 ↔ 爻象 ↔ 約束"""
    
    # 數獨元素到爻象的映射規則
    CONSTRAINT_TO_YAO = {
        'unique': YANG,      # 唯一性 = 陽爻
        'domain': YANG,      # 值域 = 陽爻
        'all_different': YANG,  # 全不同 = 陽爻
        'sum': YANG,         # 和約束 = 陽爻
        'symmetry': YANG,    # 對稱性 = 陽爻
        'empty': YIN,        # 空 = 陰爻
        'pending': YIN,      # 待定 = 陰爻
    }
    
    # 五維到爻位的映射
    DIMENSION_TO_YAO_POSITION = {
        0: 1,   # 點 → 初爻
        1: 2,   # 線 → 二爻
        2: 3,   # 面 → 三爻
        3: 4,   # 體 → 四爻
        4: 5,   # 球 → 五爻
        5: 6,   # 時空 → 上爻
    }
    
    @classmethod
    def constraint_to_yao(cls, constraint_type: str, is_satisfied: bool = True) -> Yao:
        """約束類型轉化為爻"""
        yin_yang = YANG if (is_satisfied and constraint_type in cls.CONSTRAINT_TO_YAO) else YIN
        return Yao(position=0, yin_yang=yin_yang)
    
    @classmethod
    def dimension_to_hexagram(cls, dimension_statuses: Dict[int, bool]) -> HexagramStructure:
        """五維狀態轉化為卦象"""
        binary = 0
        for dim, satisfied in dimension_statuses.items():
            yao_pos = cls.DIMENSION_TO_YAO_POSITION[dim]
            yin_yang = YANG if satisfied else YIN
            binary |= yin_yang * (2 ** (yao_pos - 1))
        
        hexagram = Hexagram.from_binary(binary)
        if hexagram:
            return HexagramStructure(
                name=hexagram.value[0],
                symbol=hexagram.value[1],
                binary=hexagram.value[2],
                upper_element=hexagram.value[3].split('天')[0] if '天' in hexagram.value[3] else hexagram.value[3],
                lower_element=hexagram.value[3].split('天')[-1] if '天' in hexagram.value[3] else hexagram.value[3],
                judgment=hexagram.value[4]
            )
        
        return HexagramStructure(
            name=f"卦{binary}",
            symbol="",
            binary=binary,
            upper_element="?",
            lower_element="?",
            judgment="未定義"
        )
    
    @classmethod
    def fuhe_to_constraint(cls, hexagram: HexagramStructure) -> Dict[str, bool]:
        """卦象轉化為約束狀態"""
        constraints = {}
        for dim, yao_pos in cls.DIMENSION_TO_YAO_POSITION.items():
            yao = hexagram.yaos[yao_pos - 1]  # 爻位從1開始
            constraints[f"dimension_{dim}"] = (yao.yin_yang == YANG)
        return constraints
    
    @classmethod
    def get_fuhe_expression(cls, hexagram: HexagramStructure) -> str:
        """取得符闔表達式"""
        return (f"符闔: {hexagram.name}{hexagram.symbol} "
                f"爻象: {''.join(y.get_symbol() for y in hexagram.yaos)} "
                f"二進制: {hexagram.get_binary_string()} "
                f"上下: {hexagram.upper_trigram.name}上{hexagram.lower_trigram.name}下")


# ============================================================================
# 卦象映射器
# ============================================================================

class HexagramMapper:
    """卦象映射器：數獨 ↔ 卦象"""
    
    # 數獨約束到卦象的預定義映射
    CONSTRAINT_HEXAGRAM_MAP = {
        # 點層約束
        'point_domain': Hexagram.KUN,       # 坤卦 - 空值域
        'point_solved': Hexagram.QIAN,      # 乾卦 - 確定值
        'point_pending': Hexagram.TUN,      # 屯卦 - 初生
        
        # 線層約束
        'line_row': Hexagram.KUN,           # 坤卦 - 地順
        'line_col': Hexagram.QIAN,          # 乾卦 - 天行
        'line_complete': Hexagram.TAI,      # 泰卦 - 天地交
        
        # 面層約束
        'plane_box': Hexagram.XIAN,         # 咸卦 - 感應
        'plane_complete': Hexagram.HENG,    # 恆卦 - 恆久
        
        # 體層約束
        'body_network': Hexagram.XUN,       # 巽卦 - 風入（用風卦代替復卦）
        'body_complete': Hexagram.QIAN,     # 乾卦 - 純陽
        
        # 球層約束
        'sphere_dense': Hexagram.CUI,       # 萃卦 - 聚集
        'sphere_sparse': Hexagram.GEN,      # 艮卦 - 止（用艮卦代替蹇卦）
        
        # 時空約束
        'spacetime_search': Hexagram.WEI_JI, # 未濟卦 - 未成
        'spacetime_solved': Hexagram.JI_JI,  # 既濟卦 - 已成
    }
    
    @classmethod
    def map_constraint_to_hexagram(cls, constraint_type: str, 
                                    dimension: int, 
                                    is_satisfied: bool) -> HexagramStructure:
        """映射約束到卦象"""
        key = f"{cls._get_dimension_name(dimension)}_{constraint_type}"
        
        if is_satisfied:
            hexagram_enum = cls.CONSTRAINT_HEXAGRAM_MAP.get(f"{key}_complete")
        else:
            hexagram_enum = cls.CONSTRAINT_HEXAGRAM_MAP.get(f"{key}", Hexagram.WEI_JI)
        
        if hexagram_enum:
            return HexagramStructure(
                name=hexagram_enum.value[0],
                symbol=hexagram_enum.value[1],
                binary=hexagram_enum.value[2],
                upper_element=hexagram_enum.value[3].split('天')[0],
                lower_element=hexagram_enum.value[3].split('天')[-1],
                judgment=hexagram_enum.value[4]
            )
        
        return HexagramStructure(
            name="未知",
            symbol="",
            binary=0,
            upper_element="?",
            lower_element="?",
            judgment="無映射"
        )
    
    @classmethod
    def _get_dimension_name(cls, dim: int) -> str:
        """取得維度名稱"""
        names = ['point', 'line', 'plane', 'body', 'sphere', 'spacetime']
        return names[dim] if 0 <= dim < 6 else 'unknown'
    
    @classmethod
    def get_hexagram_sequence(cls, constraint_history: List[Tuple[int, str, bool]]) -> List[HexagramStructure]:
        """取得約束演化的卦象序列"""
        return [
            cls.map_constraint_to_hexagram(ct, d, s)
            for d, ct, s in constraint_history
        ]
    
    @classmethod
    def analyze_hexagram_change(cls, hex1: HexagramStructure, 
                                 hex2: HexagramStructure) -> Dict:
        """分析卦象變化"""
        changes = []
        for i, (y1, y2) in enumerate(zip(hex1.yaos, hex2.yaos)):
            if y1.yin_yang != y2.yin_yang:
                change_type = "變陽" if y2.yin_yang == YANG else "變陰"
                changes.append({
                    'position': i + 1,
                    'from': y1.get_symbol(),
                    'to': y2.get_symbol(),
                    'type': change_type
                })
        
        return {
            'from_hex': hex1.name,
            'to_hex': hex2.name,
            'changes': changes,
            'is_mutual': len(changes) == 1  # 一爻變為變卦
        }


# ============================================================================
# 卦象分析器
# ============================================================================

@dataclass
class TrigramAnalysis:
    """卦象分析結果"""
    trigram: TrigramStructure
    element: str
    attribute: str
    strength: float  # 強弱 (0-1)
    direction: str   # 趨勢
    recommendation: str  # 建議


@dataclass
class HexagramAnalysis:
    """六十四卦分析結果"""
    hexagram: HexagramStructure
    upper_analysis: TrigramAnalysis
    lower_analysis: TrigramAnalysis
    overall_meaning: str
    constraint_mapping: Dict[str, bool]
    recommendation: str


class TrigramAnalyzer:
    """卦象分析器"""
    
    # 八卦屬性強度
    ELEMENT_STRENGTH = {
        '天': 1.0, '地': 0.1, '雷': 0.8, '風': 0.6,
        '水': 0.5, '火': 0.7, '山': 0.4, '澤': 0.3
    }
    
    @classmethod
    def analyze(cls, trigram: TrigramStructure) -> TrigramAnalysis:
        """分析單個三爻卦"""
        # 計算強弱（陽爻比例）
        yang_count = sum(1 for y in trigram.yaos if y.yin_yang == YANG)
        strength = yang_count / 3.0
        
        # 判定趨勢
        if strength >= 0.67:
            direction = "上升"
        elif strength >= 0.33:
            direction = "平衡"
        else:
            direction = "下降"
        
        # 建議
        if trigram.name == "乾":
            recommendation = "剛健不息，約束應強"
        elif trigram.name == "坤":
            recommendation = "柔順包容，應留彈性"
        elif trigram.name == "坎":
            recommendation = "險陷之中，需謹慎行"
        elif trigram.name == "離":
            recommendation = "附麗光明，應清晰明"
        else:
            recommendation = "隨勢而變"
        
        return TrigramAnalysis(
            trigram=trigram,
            element=trigram.element,
            attribute=trigram.attribute,
            strength=strength,
            direction=direction,
            recommendation=recommendation
        )


class HexagramAnalyzer:
    """六十四卦分析器"""
    
    @classmethod
    def analyze(cls, hexagram: HexagramStructure) -> HexagramAnalysis:
        """分析六爻卦"""
        upper_analysis = TrigramAnalyzer.analyze(hexagram.upper_trigram)
        lower_analysis = TrigramAnalyzer.analyze(hexagram.lower_trigram)
        
        # 整體含義
        if upper_analysis.strength > lower_analysis.strength:
            overall_meaning = f"{upper_analysis.element}克{lower_analysis.element}，上強下弱"
        elif upper_analysis.strength < lower_analysis.strength:
            overall_meaning = f"{lower_analysis.element}承{upper_analysis.element}，下奉上"
        else:
            overall_meaning = f"{upper_analysis.element}{lower_analysis.element}相應，平衡"
        
        # 約束映射
        constraint_mapping = FuheTranslator.fuhe_to_constraint(hexagram)
        
        # 建議
        if hexagram.name in ["既濟", "乾", "泰"]:
            recommendation = "事已成，可穩進"
        elif hexagram.name in ["未濟", "坤", "否"]:
            recommendation = "事未成，需努力"
        elif hexagram.name in ["屯", "蒙"]:
            recommendation = "初起階段，謹慎探索"
        else:
            recommendation = "依卦辭行事"
        
        return HexagramAnalysis(
            hexagram=hexagram,
            upper_analysis=upper_analysis,
            lower_analysis=lower_analysis,
            overall_meaning=overall_meaning,
            constraint_mapping=constraint_mapping,
            recommendation=recommendation
        )


# ============================================================================
# 卦象博弈優化器
# ============================================================================

class IChingOptimizer:
    """卦象博弈優化器"""
    
    # 卦象到博弈策略的映射
    HEXAGRAM_STRATEGY_MAP = {
        '乾': 'aggressive',    # 乾卦 - 積極進取
        '坤': 'conservative',  # 坤卦 - 保守穩固
        '泰': 'balanced',      # 泰卦 - 平衡策略
        '既濟': 'finalize',    # 既濟 - 收尾策略
        '未濟': 'explore',     # 未濟 - 探索策略
        '屯': 'cautious',      # 屯卦 - 謹慎起步
        '蒙': 'learning',      # 蒙卦 - 學習模式
        '咸': 'cooperative',   # 咸卦 - 合作策略
        '恆': 'consistent',    # 恆卦 - 持續策略
    }
    
    @classmethod
    def get_strategy(cls, hexagram: HexagramStructure) -> str:
        """根據卦象取得策略"""
        return cls.HEXAGRAM_STRATEGY_MAP.get(hexagram.name, 'balanced')
    
    @classmethod
    def get_strategy_params(cls, hexagram: HexagramStructure) -> Dict:
        """取得策略參數"""
        strategy = cls.get_strategy(hexagram)
        
        params = {
            'aggressive': {'backtrack_limit': 100, 'prune_threshold': 0.8},
            'conservative': {'backtrack_limit': 10, 'prune_threshold': 0.5},
            'balanced': {'backtrack_limit': 50, 'prune_threshold': 0.65},
            'finalize': {'backtrack_limit': 5, 'prune_threshold': 0.9},
            'explore': {'backtrack_limit': 200, 'prune_threshold': 0.4},
            'cautious': {'backtrack_limit': 20, 'prune_threshold': 0.7},
            'learning': {'backtrack_limit': 100, 'prune_threshold': 0.5},
            'cooperative': {'backtrack_limit': 30, 'prune_threshold': 0.6},
            'consistent': {'backtrack_limit': 40, 'prune_threshold': 0.65},
        }
        
        return params.get(strategy, params['balanced'])
    
    @classmethod
    def optimize_search(cls, current_hexagram: HexagramStructure,
                        progress: float) -> Dict:
        """優化搜索策略"""
        strategy = cls.get_strategy(current_hexagram)
        params = cls.get_strategy_params(current_hexagram)
        
        # 根據進度調整
        if progress > 0.8:
            params['backtrack_limit'] *= 0.5  # 後期減少回溯
            params['prune_threshold'] *= 1.2  # 提高剪枝閾值
        
        return {
            'strategy': strategy,
            'params': params,
            'hexagram': current_hexagram.name,
            '卦辭': current_hexagram.judgment
        }


# ============================================================================
# 六十四卦完整數據庫（簡化版）
# ============================================================================

def get_all_hexagrams() -> List[HexagramStructure]:
    """取得所有卦象結構"""
    hexagrams = []
    
    # 上經 1-30 卦
    upper_jing = [
        (63, "乾", "䷀", "天", "天", "元亨利貞"),
        (0, "坤", "䷁", "地", "地", "元亨牝馬"),
        (5, "屯", "䷂", "水", "雷", "元亨利貞"),
        (20, "蒙", "䷃", "山", "水", "亨匪我求"),
        (26, "需", "䷄", "水", "天", "有孚光亨"),
        (42, "訟", "䷅", "天", "水", "有孚窒惕"),
        (2, "師", "䷆", "地", "水", "貞丈人吉"),
        (8, "比", "䷇", "水", "地", "吉原筮元永"),
        (30, "小畜", "䷈", "風", "天", "亨密雲不雨"),
        (43, "履", "䷉", "天", "澤", "履虎尾不咥"),
        (11, "泰", "䷊", "地", "天", "小往大來"),
        (12, "否", "䷋", "天", "地", "否之匪人"),
        (13, "同人", "䷌", "天", "火", "同人于野"),
        (14, "大有", "䷍", "火", "天", "元亨"),
        (31, "咸", "䷞", "澤", "山", "亨利貞"),
        (32, "恆", "䷟", "雷", "風", "亨無咎"),
    ]
    
    # 下經 31-64 卦（部分）
    lower_jing = [
        (58, "既濟", "䷾", "水", "火", "亨小利貞"),
        (21, "未濟", "䷿", "火", "水", "亨狐汔濟"),
        (28, "大過", "䷛", "澤", "風", "棟撓利有"),
        (62, "小過", "䷽", "雷", "山", "亨利貞"),
        (45, "萃", "䷬", "澤", "地", "亨王假有"),
        (46, "升", "䷭", "地", "風", "元亨用見"),
    ]
    
    for binary, name, symbol, upper, lower, judgment in upper_jing + lower_jing:
        hexagram = HexagramStructure(
            name=name,
            symbol=symbol,
            binary=binary,
            upper_element=upper,
            lower_element=lower,
            judgment=judgment
        )
        hexagrams.append(hexagram)
    
    return hexagrams


# ============================================================================
# 測試程式碼
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("易經卦象引擎 - 符闔排列與六十四卦映射")
    print("=" * 70)
    
    # 1. 基礎卦象構造
    print("\n📿 1. 基礎卦象構造:")
    
    qian = HexagramStructure(
        name="乾", symbol="䷀", binary=0b111111,
        upper_element="天", lower_element="天",
        judgment="元亨利貞"
    )
    print(f"   {qian}")
    print(f"   爻序: {qian.get_yao_sequence()}")
    print(f"   上卦: {qian.upper_trigram}")
    print(f"   下卦: {qian.lower_trigram}")
    
    kun = HexagramStructure(
        name="坤", symbol="䷁", binary=0b000000,
        upper_element="地", lower_element="地",
        judgment="元亨牝馬"
    )
    print(f"\n   {kun}")
    print(f"   爻序: {kun.get_yao_sequence()}")
    
    # 2. 符闔轉化
    print("\n🔀 2. 符闔轉化:")
    
    # 五維狀態轉卦象
    dim_statuses = {0: True, 1: True, 2: False, 3: True, 4: False, 5: True}
    hexagram = FuheTranslator.dimension_to_hexagram(dim_statuses)
    print(f"   五維狀態 {dim_statuses}")
    print(f"   → 卦象: {hexagram.name}{hexagram.symbol}")
    print(f"   {FuheTranslator.get_fuhe_expression(hexagram)}")
    
    # 3. 卦象分析
    print("\n🔮 3. 卦象分析:")
    
    analysis = HexagramAnalyzer.analyze(qian)
    print(f"   乾卦分析:")
    print(f"   - 上卦: {analysis.upper_analysis.trigram.name} (強度: {analysis.upper_analysis.strength:.2f})")
    print(f"   - 下卦: {analysis.lower_analysis.trigram.name} (強度: {analysis.lower_analysis.strength:.2f})")
    print(f"   - 含義: {analysis.overall_meaning}")
    print(f"   - 建議: {analysis.recommendation}")
    
    # 4. 博弈優化
    print("\n🎮 4. 博弈優化:")
    
    opt_result = IChingOptimizer.optimize_search(qian, progress=0.5)
    print(f"   卦象: {opt_result['hexagram']}")
    print(f"   策略: {opt_result['strategy']}")
    print(f"   參數: {opt_result['params']}")
    print(f"   卦辭: {opt_result['卦辭']}")
    
    # 5. 卦象變化的分析
    print("\n🔄 5. 卦象變化分析:")
    
    change_result = HexagramMapper.analyze_hexagram_change(qian, kun)
    print(f"   從 {change_result['from_hex']} → {change_result['to_hex']}")
    print(f"   變化: {change_result['changes']}")
    print(f"   是否為變卦: {change_result['is_mutual']}")
    
    # 6. 全部卦象列表
    print("\n📚 6. 六十四卦列表:")
    all_hexagrams = get_all_hexagrams()
    print(f"   共 {len(all_hexagrams)} 卦")
    for h in all_hexagrams[:10]:
        print(f"   {h.name}{h.symbol}: {h.upper_element}上{h.lower_element}下")
    
    print("\n✅ 易經卦象引擎初始化完成")
    print("=" * 70)
