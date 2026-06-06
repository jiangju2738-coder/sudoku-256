# 專案整理經驗與心得

本文記錄 Sudoku 256 專案從研究腳本集合到完整 GitHub repo 的整理過程，涵蓋兩個 session 的工作與反思。

## 從 700 個檔案到有序結構

最初根目錄有 469 個散落檔案，混合了 V19 到 V91 的實驗腳本、分析報告、JSON 數據、HTML 視覺化。用 `git mv` 分類到 7 個子目錄後，不僅 git 歷史保留完整，找檔案的效率也大幅提升。

```
experiments/v30s-v90s/   歷史實驗（按版本分組）
research/scripts/        通用研究腳本
research/data/           JSON 數據與結果
reports/                 研究報告（md/html/pdf）
viz/                     互動式視覺化（HTML/PNG）
xlsx/                    符闔排列 XLSX 原始數據 (Git LFS)
archive/                 早期版本腳本（V19–V31）
```

**教訓：** 研究專案從第一天就該有基本的目錄結構，否則後期整理成本很高。469 個 `git mv` 命令雖然可以批次執行，但後續要逐一確認路徑引用是否正確。

## 大檔案管理的取捨

專案中有兩類大檔案需要特別處理：

**XLSX 原始數據（171MB）**：用 Git LFS 追蹤。LFS 把二進位大檔存在獨立的物件儲存中，git repo 只保留指標檔案。CI 環境 clone 時不會下載 LFS 內容，節省時間和空間。需要注意的是 `git lfs checkout` 必須在 clone 後手動執行，否則工作目錄中的 XLSX 會是純文字的 LFS 指標。

**排列 JSON 檔案（74MB）**：放 `.gitignore`，由 `extract_perms.py` 從 XLSX 本地生成。16 個 JSON 檔案中最大的兩個（A3 36MB、A5 35MB）單獨就超過 GitHub 的建議檔案大小上限。選擇不追蹤意味著每位開發者首次 clone 後需執行一次提取腳本，但換來的是 repo 體積可控、CI 環境乾淨。

這個「大數據本地生成 + CI 自動降級」的模式在數據密集專案中很實用。

## CI 的遞進式建立

CI 設定不是一次到位，而是遞進式建立：

1. **初始版本**（失敗）：寫了 workflow 和測試，但 `cache: pip` 找不到 `requirements.txt`，setup-python 直接報錯
2. **修復 pip cache**：加入 `requirements.txt`，CI 首次成功
3. **加入 README paths**：讓文件變更也觸發 CI，確保 badge 和內容同步
4. **加入 CHANGELOG paths**：同理，變更記錄也該驗證
5. **更新 bench 數據**：README 的策略比較表改用實際跑出來的數字

每一步都有獨立 commit，方便追溯。從失敗中學到的關鍵知識：`actions/setup-python` 的 `cache: pip` 選項**必須**搭配 `requirements.txt` 或 `pyproject.toml`，否則會報 `No file matched` 錯誤。

## 測試策略設計

74 項測試刻意設計為在兩種環境都能跑：

| 環境 | Passed | Skipped | 原因 |
|------|--------|---------|------|
| 本地（有排列 JSON） | 73 | 1 | `test_load_permutations_missing_file` 因為所有檔案都存在而跳過 |
| CI（無排列 JSON） | 72 | 2 | 加上 `test_solve_cpsat_perm` 和 `test_load_permutations_valid_index` 跳過 |

用 session-scoped fixture 偵測環境，再用 `pytest.skip()` 動態跳過，比硬編碼條件更乾淨：

```python
@pytest.fixture(scope="session")
def has_perm_files():
    count = sum(1 for i in range(N)
                if (PROJECT_ROOT / f"A{i+1}_permutations.json").exists())
    return count == N

def test_solve_cpsat_perm(self, has_ortools, has_perm_files):
    if not has_ortools:
        pytest.skip("OR-Tools 未安裝")
    if not has_perm_files:
        pytest.skip("排列 JSON 檔案不存在")
    # ... 實際測試邏輯
```

雙層 job 架構也值得一提：`test` job 用矩陣跑完整 pytest（Python 3.11 + 3.12），`smoke` job 在 `needs: test` 之後做端到端 CLI 驗證。矩陣測試快速給出單元測試結果，smoke test 確認核心功能在乾淨環境下也能正確求解。

## Skills 作為知識沉澱

每次完成一個任務就寫成 QoderWork skill，這次建立了 3 個新 skill、更新了 2 個既有 skill：

- `github-actions-ci`（新建）：CI workflow 範本、path 過濾、pytest 模式、troubleshooting
- `github-repo-deploy`（前次 session）：gh CLI 認證、SSH 設定、LFS 遷移
- `sudoku256-solver`（更新）：加入 CI Testing 段落和測試覆蓋說明
- `xlsx-permutation-extractor`（更新）：加入 gitignore / CI skip 行為說明

Skill 比靜態文件更有用，因為它包含可執行的最佳實踐和具體的 troubleshooting 步驟，下次遇到類似需求可以直接複用。

## 求解 Pipeline 全貌

最終的求解流程：

```
16 個 XLSX (171MB, Git LFS)
    ↓ extract_perms.py
16 個 JSON (1,360,849 排列, .gitignore)
    ↓ PermutationFilter (三層過濾)
~1,400 候選排列
    ↓ CP-SAT 精確覆蓋模型
唯一符闔解 (0.3s)
    ↓ SolutionVerifier
行/列/宮/錨點 全部 PASS
```

74 項測試 + GitHub Actions CI 確保未來改動不會破壞既有功能。

## 數據

| 指標 | 數值 |
|------|------|
| 總 commits | 17 |
| 測試項目 | 74 |
| CI 平均耗時 | ~53s |
| 求解最快 | 0.16s (backtrack) |
| 符闔求解 | 0.3s (cpsat_perm) |
| 排列總數 | 1,360,849 |
| Skills 總數 | 36 |
