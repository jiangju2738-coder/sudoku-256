# Sudoku 256 — 16×16 符闔超級數獨求解器

一個針對 **16×16 符闔超級數獨**（256 格、4×4 宮格、值域 1–16）的統一求解框架。支援三種求解策略，內建解驗證器與符闔排列過濾引擎，可從命令行或 Python API 使用。

## 什麼是符闔超級數獨？

符闔超級數獨源自《易經》符闔數理論，在標準 16×16 數獨的基礎上附加一項約束：每一行的排列必須屬於預先計算好的「符闔排列集合」。全部 16 行共有 **1,360,849** 個符闔排列，分佈在 16 個 JSON 文件中（由 XLSX 原始數據提取）。

這項額外約束將求解空間大幅壓縮，使問題從「多解」變為「唯一解」。

## 快速開始

```bash
# 安裝依賴
pip install ortools

# 從 XLSX 提取符闔排列文件（僅首次需要）
python extract_perms.py

# 求解
python solve256.py
```

## 求解策略

求解器會自動偵測環境，按優先級選擇最佳策略：

| 策略 | 需要 | 過濾時間 | 求解時間 | 總耗時 | 符闔驗證 | 結果 |
|------|------|---------|---------|--------|---------|------|
| `cpsat_perm` | OR-Tools + 排列文件 | ~1.5s | ~0.2s | ~4.2s | 通過 | 唯一符闔解 |
| `cpsat_plain` | OR-Tools | — | ~0.18s | ~0.18s | — | 有效數獨解 |
| `backtrack` | 純 Python | — | ~0.17s | ~0.17s | — | 有效數獨解 |

**cpsat_perm**（CP-SAT + 排列過濾）是推薦策略。它先將 1,360,849 個符闔排列透過三層過濾（已知錨點 → 列約束 → 宮約束）壓縮到約 1,400 個候選，再用 Google OR-Tools 的 CP-SAT 求解器建立精確覆蓋模型求解。此策略找到的解同時滿足標準數獨約束和符闔排列約束，與已知解完全一致。

## 命令行用法

```bash
# 自動選擇最佳策略求解
python solve256.py

# 強制指定策略
python solve256.py --strategy cpsat_perm
python solve256.py --strategy cpsat_plain
python solve256.py --strategy backtrack

# 設定時限（秒）
python solve256.py --time-limit 600

# 枚舉多個解
python solve256.py --enumerate 5

# 驗證已有的解
python solve256.py --verify solution.json

# 顯示數據源摘要
python solve256.py --info

# 效能基準測試
python solve256.py --bench

# 指定輸出檔名
python solve256.py --output my_result.json

# 靜默模式
python solve256.py --quiet
```

## Python API

```python
from sudoku256 import Sudoku256Solver, SolutionVerifier

# 求解
engine = Sudoku256Solver(verbose=True)
result = engine.solve(strategy="cpsat_perm")

print(result.status)       # "SOLVED"
print(result.strategy)     # "cpsat_perm"
print(result.total_time)   # 4.2 (秒)
result.save("solution.json")

# 驗證
verifier = SolutionVerifier(result.solution)
report = verifier.verify_all(anchors=ANCHORS_92)
print(report)  # {"row_ok": True, "col_ok": True, "box_ok": True, ...}
```

## 專案結構

```
Sudoku_256/
├── solve256.py                 # CLI 入口
├── extract_perms.py            # XLSX 符闔排列提取腳本
├── sudoku256/                  # 核心套件
│   ├── __init__.py             # 公開 API
│   ├── constants.py            # 單一數據源（錨點、已知行、常量）
│   ├── loader.py               # 數據加載（JSON / XLSX / 排列文件）
│   ├── propagator.py           # 約束傳播（AC-3 + 符闔排列過濾）
│   ├── solver.py               # 統一求解器（三策略自動選擇）
│   └── verifier.py             # 解驗證（行/列/宮/錨點/符闔）
├── A*_permutations.json        # 符闔排列文件（由 extract_perms.py 生成）
├── *.xlsx                      # 符闔排列原始數據
└── .gitignore
```

## 數據說明

### 92 錨點

棋盤上有 114 個已知值（含 C、D、I 三行各 16 個完全固定格），定義在 `constants.py` 的 `ANCHORS_92` 中。這些錨點來自經過驗證的 `KNOWN_SOLUTION_92`，確保行列宮之間零衝突。

### 符闔排列文件

16 個 `A1_permutations.json` ~ `A16_permutations.json` 文件，由 `extract_perms.py` 從 XLSX 原始數據提取。由於文件較大（合計約 1,360,849 條排列），已排除在 Git 追蹤之外。首次使用時需執行：

```bash
python extract_perms.py
```

提取完成後可透過 `extraction_report.json` 查看每行的排列數量統計。

## 依賴

- **Python** ≥ 3.8
- **ortools**（Google OR-Tools）— `cpsat_perm` 和 `cpsat_plain` 策略需要
- **openpyxl** — `extract_perms.py` 提取 XLSX 時需要

`backtrack` 策略為純 Python 實現，無需外部依賴。

## 授權

MIT License
