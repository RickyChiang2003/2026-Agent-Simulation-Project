# V2 統整筆記（I1-I3 + Agenda Veto）

- 分析日期：2026-05-07
- V2 樣本：88 trials（`results_v2`）
- Legacy 樣本：120 trials（`results_legacy`）

## 0) 相較 Legacy 新增了什麼
1. I1 機率調整  
- Legacy：I1 近似 `P1=60%`、`P2=20%`、`P3=20%`（強烈偏向 P1）  
- V2：I1 調整為 `P1=60%`、`P2=50%`、`P3=50%`（縮小醫療差距）

2. I2 新增條件式不確定性  
- Legacy：偏向「P2 存活就有鉅額捐款」的確定敘事  
- V2：加入「捐款短期到帳機率約 65%」與破產風險 45%，使 A2 不再是完全確定收益

3. I3 新增反噬風險  
- Legacy：偏向「P3 死亡 -> 執照審查風險」  
- V2：保留審查風險（45%）並加入「政治施壓曝光反噬約 30%」，降低單向政治誘因

4. Veto 機制從「結果否決」改為「議程否決（Agenda Veto）」  
- Legacy：`[Current Intent: Veto]` 幾乎不使用，觸發即終止（`VETOED`）  
- V2：A3 可用一次 `Agenda Action: VETO_P1/P2/P3`，僅封鎖該候選人於本回合計票，不直接指定勝者

5. 資料輸出欄位新增  
- V2 JSON 新增：`agenda_veto_used`、`agenda_veto_history`、每回合 `effective_intents`、`agenda_action`、`banned_target`  
- 讓你可以追蹤「有沒有用 veto」與「用了是否真的改變票型」

## 1) 整體結果好不好？
結論：**整體方向是好的，且值得繼續跑更多輪。**

關鍵數據：
- V2 最終分佈：P2=48, P1=23, P3=6, Failed=11
- Legacy 最終分佈：P1=65, P2=33, P3=3, Failed=19
- 失敗率：V2 `11/88 = 12.5%`，Legacy `19/120 = 15.8%`

解讀：
- V2 相較 legacy，`Failed` 下降。
- P3 最終被選次數由 3 提高到 6（雖然仍偏低，但有改善）。
- 結果不再幾乎單一倒向 P1，分布更有對抗性。

## 2) VETO 有用到嗎？
有，且是新版 `Agenda Veto` 真正被使用。

- `Legacy Veto Triggered`: 0（因為舊制 `VETOED` 幾乎沒發生）
- `Agenda Veto Used`: 高（V=1 組）
  - Control R3 V1: 9/11
  - Control R8 V1: 10/11
  - Experimental R3 V1: 8/11
  - Experimental R8 V1: 8/11

## 3) Agenda Veto 是否真的產生效果？
有，但不是每次都改變最終結果。

- 套用回合數：35 回合（35 個 trials 各一次）
- 造成「當回合票型變化」：13 回合
- 把原本有多數改成無多數：3 回合

範例（來自 `results_v2`）：
1. `Control_R3_V1_T1_20260507_035535.json`
- Round 1 action: `VETO_P1`
- 原始：A1=P1, A2=P2, A3=P2
- 生效後：A1=UNDECIDED, A2=P2, A3=P2
- 最終：`MAJORITY_P2`
- 解讀：veto 明確強化了 P2 的多數。

2. `Control_R8_V1_T1_20260507_015445.json`
- Round 1 action: `VETO_P1`
- 原始：A1=P1, A2=P1, A3=P3
- 生效後：A1=UNDECIDED, A2=UNDECIDED, A3=P3
- 最終：`CONSENSUS_P1`
- 解讀：veto 改了當回合態勢，但沒有改變最終決策。

3. `Control_R3_V1_T10_20260507_041929.json`
- Round 1 action: `VETO_P1`
- 原始：A1=P1, A2=P2, A3=P3
- 生效後：A1=UNDECIDED, A2=P2, A3=P3
- 最終：`FAILED_NO_CONSENSUS`
- 解讀：veto 造成更強對抗，但這次導向僵局。

## 4) 是否值得繼續跑（相較 legacy）
結論：**值得。**

原因：
- V2 機制有被觸發，不再是「設計存在但不發生」。
- 整體失敗率有下降。
- 對抗性與結果多樣性提升，較接近你要觀察的談判行為。

## 5) 下一步建議
1. 先把 V2 每組補到固定樣本（例如每 config 至少 20 次）。
2. 重點盯 `Experimental + V=1` 是否出現「過度使用 veto 導致 fail 上升」。
3. 保留你剛新增的 prompt 限制句（僅在即將形成不利多數時使用 agenda），再觀察 1 批次後再決定要不要加硬性門檻。
