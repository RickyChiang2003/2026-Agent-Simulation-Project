# 2026 Agent Simulation Project

本專案使用 TinyTroupe 進行多代理人模擬，主題為醫療資源分配決策。

## 環境建置

### 需求
- Python 3.10+
- OpenAI API Key

### conda（建議）
```bash
conda create -n tinytroupe-sim python=3.11 -y
conda activate tinytroupe-sim
python -m pip install --upgrade pip
pip install git+https://github.com/microsoft/TinyTroupe.git@main
```

### venv
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install git+https://github.com/microsoft/TinyTroupe.git@main
```

## 設定

編輯 `config.ini`：
```ini
[OpenAI]
API_TYPE = openai
API_KEY = sk-...
MODEL = gpt-5-mini
TIMEOUT = 120
MAX_COMPLETION_TOKENS = 4096
REASONING_EFFORT = low

[Simulation]
RAISE_EXCEPTIONS = True

[Cognition]
ENABLE_MEMORY_CONSOLIDATION = False
```

## 執行

### 互動式
```bash
./run_experiments.sh
```

### 直接批次執行
```bash
python3 main.py
```

## 實驗組合（1~8）
1. Control, R=4, V=0
2. Control, R=4, V=1
3. Control, R=8, V=0
4. Control, R=8, V=1
5. Experimental, R=4, V=0
6. Experimental, R=4, V=1
7. Experimental, R=8, V=0
8. Experimental, R=8, V=1

## 輸出
- JSON 結果：`artifacts/results/`
- TinyTroupe log：`artifacts/logs/`

## 當前決策格式（重要）
- 每回合輸出規格：
  - 第1行必須是：`INTENT=P1|P2|P3|UNDECIDED|VETO`
  - 後續需包含 `Rationale / Evidence / Response`
- 一般回合：以該 agent 自己的 `assistant -> actions -> TALK` 內容做嚴格判票（以 `INTENT=...` 為主）。
- 追加投票輪：若前 R 回合全員都 `UNDECIDED` 才觸發，該輪允許放寬抓自然語句（如 `I support P1`、`我選P1`）。
- 不再使用「缺證據即改判 UNDECIDED」規則，也不再用「從其他 agent 的刺激反推 intent」。

## 核心檔案
- `main.py`：模擬流程、意向解析、批次執行
- `Prompt_Assembler.py`：角色與系統 prompt 組裝
- `run_experiments.sh`：互動式執行入口
- `DESIGN_0502.md`：原始題目設計
- `NEW_DESIGN.md`：新版實驗設計與改版重點
