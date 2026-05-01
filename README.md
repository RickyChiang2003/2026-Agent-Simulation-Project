# 2026 Agent Simulation Project

### Update Log
- 2026/05/02 3:54 
    - 目前為初始架構，尚未經過任何測試
    - 包含檔案：`TODO.md`、`DESIGN_0502.md`、`Prompt_Assembler.py`、`main.py`、`config.ini`
        - `TODO.md`
            - 助教簡報的 markdown 整合版，包含 TinyTroupe 和 Simulation Case Studies 的說明，適合拿來給 LLM 當作背景知識。但是關於 Assignment 和 API Key 的部分請還是去看[助教簡報](https://docs.google.com/presentation/d/11l7aBdOASB0omz0a5Wgw88LHAyngDkKYppdw8_mDkjo/edit?slide=id.p#slide=id.p)。
        - `DESIGN_0502.md`
            - 包含題目設計大綱，**非常建議閱讀(或丟 LLM 輔助閱讀)**。
        - `Prompt_Assembler.py`
            - 包含初始 prompt ，方便日後組合各種 prompt 。實作上便提供 class `MedicalDilemmaPromptAssembler` 給 `main.py` 呼叫使用。但裡面也有寫 main 函式，可以執行 `python Prompt_Assembler.py` 看看那些 prompt 組合後會長甚麼樣子
        - `main.py`
            - 包含 TinyTroupe 的架構與實驗邏輯，可能有 bug (因為尚未經過測試) 。實際做實驗應該就是 `python main.py`，雖然應該要先 debug 一陣子就是。
        - `config.ini`
            - 設定 API Key 以及要使用的模型。請記得不要把 API Key 推上 github ，雖然 .gitignore 裡面有寫但還是請小心。

