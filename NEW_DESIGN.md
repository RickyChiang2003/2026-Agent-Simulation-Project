# NEW DESIGN (2026-05-05)

## 目標
改善「有討論但無法判定決策」問題，提升每回合可解析性與最終收斂率。

## 主要改版

### 1) 輸出格式改為 `INTENT=` 主導
每位 Agent 每回合需先輸出：
- 第1行：`INTENT=P1|P2|P3|UNDECIDED|VETO`
- 後續內容：`Rationale / Evidence / Response`

### 2) parser 改為讀取 JSON `actions` 中的 `TALK.content`
`main.py` 會優先從 assistant JSON 內解析 `TALK` 文本，而非只看整段字串。

- 一般回合：偏嚴格，優先抓 `INTENT=...`
- 追加投票輪：可放寬抓自然語句（例如 `I support P1`、`我選P1`）

### 3) 判票來源單純化
一般回合只看「該 agent 自己最後的 assistant 回覆」中的 `actions -> TALK.content`。
不再使用跨代理刺激回推，避免誤判。

### 4) 追加投票輪
僅在前 R 回合全員都 `UNDECIDED` 時觸發：
- 額外 +1 輪
- 該輪允許較自然的投票句，避免「有表態卻抓不到」

### 5) 回合數調整
預設批次使用 `4/8`：
- 組別：Control / Experimental
- 回合：4 / 8
- 否決權：0 / 1
共 8 組。

### 6) 輸出位置
- Results: `artifacts/results/`
- Logs: `artifacts/logs/`

### 7) 設定穩定性修正（避免截斷）
為避免 `LengthFinishReasonError`：
- `MODEL = gpt-5-mini`
- `MAX_COMPLETION_TOKENS = 4096`
- `REASONING_EFFORT = low`

## 已觀察到的問題（最新 log）
若 token 太小或 reasoning 太高，模型會在 JSON 未完成前被截斷，造成 `LengthFinishReasonError`。
這不是 API 認證問題，而是輸出上限配置問題。

## 後續建議
1. 若仍常空話，可把 `Response` 與數字證據改成「告警指標」先追蹤，不先作硬懲罰。
2. 建議保留每輪 parser debug（命中的 TALK 文字與 intent）來快速定位誤判。
