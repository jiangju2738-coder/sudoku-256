# Changelog

本專案的所有重要變更記錄於此。格式基於 [Keep a Changelog](https://keepachangelog.com/)。

## [Unreleased]

### Added
- GitHub Actions CI 持續整合 (`.github/workflows/ci.yml`)
  - `test` job: Python 3.11/3.12 矩陣測試，74 項 pytest
  - `smoke` job: CP-SAT plain + 回溯法端到端求解驗證
  - Path-based triggers（含 README.md）
  - pip cache 加速依賴安裝
  - pytest-timeout 防止測試卡死
  - JUnit XML 報告上傳為 artifact
- pytest 測試套件 (`tests/test_solver.py`)
  - 74 項測試，10 大類別：常數驗證、已知解校驗、完全固定行、輔助函數、數據加載、解驗證器、AC-3 約束傳播、三種求解策略、CLI 命令、邊界情況
  - 本地：73 passed / 1 skipped
  - CI：72 passed / 2 skipped（排列 JSON 在 .gitignore 自動跳過）
- `requirements.txt`：pytest、pytest-timeout、ortools
- README CI badge（綠色 passing）
- README CI 測試說明段落：本地執行方式、雙層 job 架構表、測試覆蓋說明
- QoderWork Skills
  - `github-actions-ci`（新建）：CI 最佳實踐
  - `sudoku256-solver`（更新）：加入 CI Testing 段落
  - `xlsx-permutation-extractor`（更新）：加入 gitignore / CI skip 說明
- `docs/retrospective.md`：專案整理經驗與心得（目錄結構、大檔案管理、CI 遞進建立、測試策略、Skills 沉澱、求解 pipeline）

### CI 歷史
| 日期 | Commit | 結果 | 備註 |
|------|--------|------|------|
| 2026-06-07 | `2a389f4` 初始 CI + pytest | failure | 缺 requirements.txt，pip cache 錯誤 |
| 2026-06-07 | `d3cb03c` 添加 requirements.txt | success (54s) | 修復 pip cache |
| 2026-06-07 | `b117f9a` README.md 加入 paths | success (50s) | 文件變更也觸發 CI |

## [2.0.0] - 2026-06-07

### Added
- 統一模块化求解框架 (`sudoku256/` 套件)
- 三種求解策略：CP-SAT + 排列過濾、CP-SAT 標準、回溯 + AC-3
- CLI 入口 (`solve256.py`)：求解、枚舉、驗證、基準測試
- XLSX 符闔排列提取腳本 (`extract_perms.py`)
- 解驗證器（行/列/宮/錨點/符闔五項約束）
- 符闔排列三層預過濾引擎
- MIT License
- 完整 README（繁體中文）
- Git LFS 追蹤 XLSX 原始數據
- 專案目錄整理（469 檔案分類到子目錄）
- 歷史研究檔案歸檔（731 檔案）
